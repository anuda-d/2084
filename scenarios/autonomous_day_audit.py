"""Private one-run evidence bundle for the owner-authorized live day."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from http.client import HTTPConnection, HTTPException
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
from typing import Callable, Mapping
from urllib.parse import urlsplit

from policies.mara_harness import MaraHarness
from policies.model_focal_policy import RecordedDecisionArchive
from policies.ollama_client import OLLAMA_MAX_RESPONSE_BYTES, OllamaDecisionClient
from scenarios.autonomous_day import (
    AD12_OLLAMA_MODEL,
    MARA_ID,
    AutonomousDay,
    autonomous_day_inspector_data,
    build_autonomous_day,
    render_autonomous_day,
)
from simulation.agents import serialize_private_decision_records
from simulation.day_runtime import DayRunSummary, MAX_MODEL_DECISION_CALLS_PER_DAY


AUDIT_SCHEMA_VERSION = 1
AD12_OLLAMA_MODEL_DIGEST = (
    "0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0"
)
AUDIT_DIRECTORY_MODE = 0o700
AUDIT_FILE_MODE = 0o600
AUDIT_ARTIFACT_NAMES = (
    "normal.txt",
    "inspector.json",
    "private-decisions.json",
    "verdict.json",
)
AUDIT_CHECK_NAMES = frozenset(
    {
        "exact_boundary_reached",
        "no_terminal_runtime_failure",
        "model_configured",
        "model_exercised",
        "provider_adapter_is_ollama",
        "exact_model_identity_verified",
        "source_unchanged_during_run",
        "provider_call_attempted",
        "provider_selected_at_least_once",
        "decision_count_within_limit",
        "decision_count_matches_runtime",
        "restricted_input_within_limit",
        "private_records_within_limit",
        "committed_causal_links_complete",
        "model_decision_dispatches_complete",
        "no_uncommitted_objective_tail",
        "normal_and_inspector_privacy_safe",
        "recorded_replay_equal",
    }
)
AUDIT_MEASUREMENT_NAMES = frozenset(
    {
        "decision_count",
        "provider_call_attempt_count",
        "provider_selected_count",
        "provider_failure_count",
        "peak_restricted_input_bytes",
        "maximum_restricted_input_bytes",
        "peak_retained_private_record_bytes",
        "maximum_retained_private_record_bytes",
    }
)


@dataclass(frozen=True)
class LiveAuditResult:
    directory: Path
    passed: bool
    verdict: Mapping[str, object]


@dataclass(frozen=True)
class LiveAuditReservation:
    path: Path
    device: int
    inode: int


def fetch_ollama_model_identity(
    *,
    base_url: str,
    model: str,
    timeout_seconds: float = 10,
    connection_factory: Callable[..., HTTPConnection] = HTTPConnection,
) -> dict[str, object]:
    """Read and validate exact model metadata without making a model call."""

    OllamaDecisionClient(
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    parsed = urlsplit(base_url.strip())
    connection = connection_factory(
        parsed.hostname,
        port=parsed.port,
        timeout=timeout_seconds,
    )
    try:
        connection.request("GET", "/api/tags", headers={"Accept": "application/json"})
        response = connection.getresponse()
        body = response.read(OLLAMA_MAX_RESPONSE_BYTES + 1)
    except (HTTPException, OSError, TimeoutError) as error:
        raise RuntimeError("Ollama model identity preflight failed") from error
    finally:
        connection.close()
    if response.status != 200 or len(body) > OLLAMA_MAX_RESPONSE_BYTES:
        raise RuntimeError("Ollama model identity preflight failed")
    try:
        document = json.loads(body.decode("utf-8"))
        models = document["models"]
    except (KeyError, RecursionError, TypeError, UnicodeDecodeError, ValueError) as error:
        raise RuntimeError("Ollama model identity preflight failed") from error
    if not isinstance(models, list):
        raise RuntimeError("Ollama model identity preflight failed")
    matches = [
        entry
        for entry in models
        if isinstance(entry, Mapping)
        and (entry.get("name") == model or entry.get("model") == model)
    ]
    if len(matches) != 1:
        raise RuntimeError("exact Ollama model is not uniquely available")
    entry = matches[0]
    details = entry.get("details")
    if not isinstance(details, Mapping):
        raise RuntimeError("Ollama model identity details are unavailable")
    identity = {
        "source": "ollama_api_tags",
        "model": model,
        "digest": entry.get("digest"),
        "family": details.get("family"),
        "parameter_size": details.get("parameter_size"),
        "quantization_level": details.get("quantization_level"),
    }
    if identity["digest"] != AD12_OLLAMA_MODEL_DIGEST:
        raise RuntimeError("Ollama model digest does not match AD-12")
    if identity["family"] != "qwen3":
        raise RuntimeError("Ollama model family does not match AD-12")
    if identity["parameter_size"] not in {"4.0B", "4.02B"}:
        raise RuntimeError("Ollama model parameter size does not match AD-12")
    if identity["quantization_level"] != "Q4_K_M":
        raise RuntimeError("Ollama model quantization does not match AD-12")
    return identity


def reserve_live_audit_directory(
    directory: str | os.PathLike[str],
) -> LiveAuditReservation:
    """Atomically reserve an owner-only empty directory before provider use."""

    path = Path(directory)
    repository = Path(__file__).resolve().parents[1]
    resolved_target = path.parent.resolve() / path.name
    if resolved_target == repository or repository in resolved_target.parents:
        raise ValueError("audit directory must be outside the repository")
    if os.path.lexists(path):
        raise FileExistsError(f"audit directory already exists: {path}")
    if not path.parent.is_dir():
        raise FileNotFoundError(f"audit directory parent does not exist: {path.parent}")
    os.mkdir(path, AUDIT_DIRECTORY_MODE)
    os.chmod(path, AUDIT_DIRECTORY_MODE)
    metadata = path.lstat()
    return LiveAuditReservation(
        path=path,
        device=metadata.st_dev,
        inode=metadata.st_ino,
    )


def _open_validated_reservation(reservation: LiveAuditReservation) -> int:
    """Open the reserved inode so later writes cannot be redirected by rename."""

    path = reservation.path
    descriptor = os.open(
        path,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError("audit reservation is no longer a real directory")
        if (metadata.st_dev, metadata.st_ino) != (
            reservation.device,
            reservation.inode,
        ):
            raise RuntimeError("audit reservation identity changed")
        if stat.S_IMODE(metadata.st_mode) != AUDIT_DIRECTORY_MODE:
            raise PermissionError("audit reservation has unsafe permissions")
        if os.listdir(descriptor):
            raise FileExistsError("audit reservation is not empty")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _reservation_path_matches(reservation: LiveAuditReservation) -> bool:
    try:
        descriptor = os.open(
            reservation.path,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
    except OSError:
        return False
    try:
        metadata = os.fstat(descriptor)
        return (metadata.st_dev, metadata.st_ino) == (
            reservation.device,
            reservation.inode,
        )
    finally:
        os.close(descriptor)


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_private_file(
    directory_descriptor: int,
    name: str,
    content: bytes,
) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        AUDIT_FILE_MODE,
        dir_fd=directory_descriptor,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def capture_live_audit_source_state() -> dict[str, object]:
    """Fingerprint repository state at one side of the live execution."""

    repository = Path(__file__).resolve().parents[1]
    revision_result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        cwd=repository,
        text=True,
    )
    revision = revision_result.stdout.strip()
    if len(revision) != 40 or any(
        character not in "0123456789abcdef" for character in revision
    ):
        raise RuntimeError("git did not return a full lowercase source revision")
    status_result = subprocess.run(
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
        check=True,
        capture_output=True,
        cwd=repository,
        text=True,
    )
    diff_result = subprocess.run(
        ("git", "diff", "--binary", "HEAD"),
        check=True,
        capture_output=True,
        cwd=repository,
    )
    return {
        "revision": revision,
        "clean": not status_result.stdout,
        "status_lines": status_result.stdout.splitlines(),
        "working_diff_sha256": sha256(diff_result.stdout).hexdigest(),
        "working_diff_bytes": len(diff_result.stdout),
    }


def _replay_matches(day: AutonomousDay, summary: DayRunSummary) -> bool:
    if not day.private_decision_records:
        return False
    integrity_key = secrets.token_bytes(32)
    archive = RecordedDecisionArchive.seal(
        day.private_decision_records,
        integrity_key=integrity_key,
    )
    replay = build_autonomous_day(
        seed=day.world.seed,
        mara_harness=MaraHarness.from_recorded_archive(
            archive,
            integrity_key=integrity_key,
        ),
    )
    replay_summary = replay.run()
    source_inspector = autonomous_day_inspector_data(day, summary)
    replay_inspector = autonomous_day_inspector_data(replay, replay_summary)
    comparable_fields = ("runtime", "counts", "objective_state", "history")
    return all(
        replay_inspector[field] == source_inspector[field]
        for field in comparable_fields
    )


def _all_committed_artifacts_have_dispatches(
    inspector: Mapping[str, object],
) -> bool:
    history = inspector["history"]
    if not isinstance(history, Mapping):
        raise RuntimeError("inspector history is not a mapping")
    collections = (
        history["events"],
        history["observations"],
        history["action_results"],
        history["understanding_transitions"],
    )
    return all(
        isinstance(artifact, Mapping) and artifact.get("dispatch") is not None
        for collection in collections
        for artifact in collection
    )


def write_autonomous_day_live_audit(
    *,
    day: AutonomousDay,
    summary: DayRunSummary,
    directory: str | os.PathLike[str],
    ollama_base_url: str,
    ollama_model: str,
    source_before: Mapping[str, object],
    model_identity: Mapping[str, object],
    reservation: LiveAuditReservation | None = None,
) -> LiveAuditResult:
    """Write and verify one non-overwriting private bundle from one live run."""

    if not day.mara_harness_configured:
        raise ValueError("live audit requires a configured Mara harness")
    if ollama_model != AD12_OLLAMA_MODEL:
        raise ValueError(f"live audit requires exact model {AD12_OLLAMA_MODEL}")
    if reservation is None:
        reservation = reserve_live_audit_directory(directory)
    elif Path(directory) != reservation.path:
        raise ValueError("audit directory does not match its reservation")
    directory_descriptor = _open_validated_reservation(reservation)
    try:
        return _write_live_audit_to_reserved_directory(
            day=day,
            summary=summary,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            source_before=source_before,
            model_identity=model_identity,
            reservation=reservation,
            directory_descriptor=directory_descriptor,
        )
    finally:
        os.close(directory_descriptor)


def _write_live_audit_to_reserved_directory(
    *,
    day: AutonomousDay,
    summary: DayRunSummary,
    ollama_base_url: str,
    ollama_model: str,
    source_before: Mapping[str, object],
    model_identity: Mapping[str, object],
    reservation: LiveAuditReservation,
    directory_descriptor: int,
) -> LiveAuditResult:
    audit_path = reservation.path
    source_after = capture_live_audit_source_state()
    source_unchanged = dict(source_before) == source_after
    model_identity_valid = dict(model_identity) == {
        "source": "ollama_api_tags",
        "model": AD12_OLLAMA_MODEL,
        "digest": AD12_OLLAMA_MODEL_DIGEST,
        "family": "qwen3",
        "parameter_size": model_identity.get("parameter_size"),
        "quantization_level": "Q4_K_M",
    } and model_identity.get("parameter_size") in {"4.0B", "4.02B"}

    inspector = autonomous_day_inspector_data(day, summary)
    normal_bytes = render_autonomous_day(day, summary).encode("utf-8")
    inspector_bytes = _json_bytes(inspector)
    private_bytes = (
        serialize_private_decision_records(day.private_decision_records) + "\n"
    ).encode("utf-8")
    private_fragments = {
        ollama_base_url,
        ollama_model,
        *(record.configuration_id for record in day.private_decision_records),
    }
    public_material = normal_bytes + inspector_bytes
    privacy_safe = all(
        fragment.encode("utf-8") not in public_material
        for fragment in private_fragments
        if fragment
    )

    replay_equal = False
    replay_failure_type = None
    try:
        replay_equal = _replay_matches(day, summary)
    except Exception as error:
        replay_failure_type = type(error).__name__

    model_path = inspector["model_path"]
    if not isinstance(model_path, Mapping):
        raise RuntimeError("inspector model path is not a mapping")
    growth = model_path["growth"]
    if not isinstance(growth, Mapping):
        raise RuntimeError("inspector growth evidence is not a mapping")
    selected_live_decision_count = sum(
        record.status == "selected" and record.provider_call_attempted
        for record in day.private_decision_records
    )
    provider_call_attempt_count = sum(
        record.provider_call_attempted
        for record in day.private_decision_records
    )
    runtime = inspector["runtime"]
    if not isinstance(runtime, Mapping):
        raise RuntimeError("inspector runtime is not a mapping")
    decision_counts = runtime["decision_counts_by_actor"]
    if not isinstance(decision_counts, Mapping):
        raise RuntimeError("runtime decision counts are not a mapping")
    model_decision_sequence = model_path["decision_status_sequence"]
    if not isinstance(model_decision_sequence, list):
        raise RuntimeError("model decision status sequence is not a list")
    checks = {
        "exact_boundary_reached": summary.reached_end_boundary,
        "no_terminal_runtime_failure": summary.runtime_failure is None,
        "model_configured": model_path["configured"] is True,
        "model_exercised": model_path["exercised"] is True,
        "provider_adapter_is_ollama": day.mara_provider_kind == "ollama",
        "exact_model_identity_verified": model_identity_valid,
        "source_unchanged_during_run": source_unchanged,
        "provider_call_attempted": provider_call_attempt_count > 0,
        "provider_selected_at_least_once": selected_live_decision_count > 0,
        "decision_count_within_limit": (
            len(day.private_decision_records) <= MAX_MODEL_DECISION_CALLS_PER_DAY
        ),
        "decision_count_matches_runtime": (
            decision_counts.get(MARA_ID) == len(day.private_decision_records)
        ),
        "restricted_input_within_limit": (
            growth["peak_restricted_input_bytes"]
            <= growth["maximum_restricted_input_bytes"]
        ),
        "private_records_within_limit": (
            growth["peak_retained_private_record_bytes"]
            <= growth["maximum_retained_private_record_bytes"]
        ),
        "committed_causal_links_complete": (
            _all_committed_artifacts_have_dispatches(inspector)
        ),
        "model_decision_dispatches_complete": all(
            isinstance(decision, Mapping) and decision.get("dispatch") is not None
            for decision in model_decision_sequence
        ),
        "no_uncommitted_objective_tail": (
            inspector["history"]["uncommitted_objective_tail"] is None
        ),
        "normal_and_inspector_privacy_safe": privacy_safe,
        "recorded_replay_equal": replay_equal,
    }
    verdict = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "passed": all(checks.values()),
        "checks": checks,
        "measurements": {
            "decision_count": len(day.private_decision_records),
            "provider_call_attempt_count": provider_call_attempt_count,
            "provider_selected_count": selected_live_decision_count,
            "provider_failure_count": model_path["provider_failure_count"],
            "peak_restricted_input_bytes": growth["peak_restricted_input_bytes"],
            "maximum_restricted_input_bytes": growth[
                "maximum_restricted_input_bytes"
            ],
            "peak_retained_private_record_bytes": growth[
                "peak_retained_private_record_bytes"
            ],
            "maximum_retained_private_record_bytes": growth[
                "maximum_retained_private_record_bytes"
            ],
        },
        "replay_failure_type": replay_failure_type,
    }

    initial_artifacts = {
        "normal.txt": normal_bytes,
        "inspector.json": inspector_bytes,
        "private-decisions.json": private_bytes,
        "verdict.json": _json_bytes(verdict),
    }
    for name, content in initial_artifacts.items():
        _write_private_file(directory_descriptor, name, content)

    manifest = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "source": {
            "before": dict(source_before),
            "after": source_after,
            "unchanged_during_run": source_unchanged,
        },
        "seed": day.world.seed,
        "model": ollama_model,
        "model_identity": dict(model_identity),
        "provider_adapter": day.mara_provider_kind,
        "artifacts": {
            name: {
                "sha256": sha256(content).hexdigest(),
                "bytes": len(content),
            }
            for name, content in initial_artifacts.items()
        },
    }
    _write_private_file(
        directory_descriptor,
        "manifest.json",
        _json_bytes(manifest),
    )
    verification = _verify_live_audit_descriptor(directory_descriptor)
    path_stable = _reservation_path_matches(reservation)
    return LiveAuditResult(
        directory=audit_path,
        passed=(
            verdict["passed"] is True
            and verification["passed"] is True
            and path_stable
        ),
        verdict=verdict,
    )


def _read_audit_file(directory_descriptor: int, name: str) -> bytes:
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_NOFOLLOW,
        dir_fd=directory_descriptor,
    )
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise OSError("audit artifact is not one private regular file")
        if stat.S_IMODE(metadata.st_mode) != AUDIT_FILE_MODE:
            raise PermissionError("audit artifact has unsafe permissions")
        with os.fdopen(descriptor, "rb") as stream:
            return stream.read()
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _is_hex_digest(value: object, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_source_state(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != {
        "revision",
        "clean",
        "status_lines",
        "working_diff_sha256",
        "working_diff_bytes",
    }:
        return False
    status_lines = value["status_lines"]
    return (
        _is_hex_digest(value["revision"], 40)
        and isinstance(value["clean"], bool)
        and isinstance(status_lines, list)
        and all(isinstance(line, str) for line in status_lines)
        and value["clean"] is (not status_lines)
        and _is_hex_digest(value["working_diff_sha256"], 64)
        and _is_nonnegative_int(value["working_diff_bytes"])
    )


def _valid_manifest_provenance(manifest: Mapping[str, object]) -> bool:
    if set(manifest) != {
        "schema_version",
        "source",
        "seed",
        "model",
        "model_identity",
        "provider_adapter",
        "artifacts",
    }:
        return False
    source = manifest["source"]
    identity = manifest["model_identity"]
    if not isinstance(source, Mapping) or set(source) != {
        "before",
        "after",
        "unchanged_during_run",
    }:
        return False
    if not isinstance(identity, Mapping) or set(identity) != {
        "source",
        "model",
        "digest",
        "family",
        "parameter_size",
        "quantization_level",
    }:
        return False
    return (
        manifest["schema_version"] == AUDIT_SCHEMA_VERSION
        and _is_int(manifest["seed"])
        and manifest["model"] == AD12_OLLAMA_MODEL
        and manifest["provider_adapter"] == "ollama"
        and _valid_source_state(source["before"])
        and _valid_source_state(source["after"])
        and source["before"] == source["after"]
        and source["unchanged_during_run"] is True
        and identity["source"] == "ollama_api_tags"
        and identity["model"] == AD12_OLLAMA_MODEL
        and identity["digest"] == AD12_OLLAMA_MODEL_DIGEST
        and identity["family"] == "qwen3"
        and identity["parameter_size"] in {"4.0B", "4.02B"}
        and identity["quantization_level"] == "Q4_K_M"
    )


def _valid_verdict(verdict: object) -> bool:
    if not isinstance(verdict, Mapping) or set(verdict) != {
        "schema_version",
        "passed",
        "checks",
        "measurements",
        "replay_failure_type",
    }:
        return False
    checks = verdict["checks"]
    measurements = verdict["measurements"]
    if (
        not isinstance(checks, Mapping)
        or set(checks) != AUDIT_CHECK_NAMES
        or not all(isinstance(value, bool) for value in checks.values())
        or not isinstance(measurements, Mapping)
        or set(measurements) != AUDIT_MEASUREMENT_NAMES
        or not all(_is_nonnegative_int(value) for value in measurements.values())
    ):
        return False
    return (
        verdict["schema_version"] == AUDIT_SCHEMA_VERSION
        and isinstance(verdict["passed"], bool)
        and verdict["passed"] is all(checks.values())
        and (
            verdict["replay_failure_type"] is None
            or isinstance(verdict["replay_failure_type"], str)
        )
        and measurements["decision_count"] <= MAX_MODEL_DECISION_CALLS_PER_DAY
        and measurements["provider_selected_count"]
        <= measurements["provider_call_attempt_count"]
        <= measurements["decision_count"]
        and measurements["peak_restricted_input_bytes"]
        <= measurements["maximum_restricted_input_bytes"]
        and measurements["peak_retained_private_record_bytes"]
        <= measurements["maximum_retained_private_record_bytes"]
    )


def _verify_live_audit_descriptor(
    directory_descriptor: int,
) -> dict[str, object]:
    """Verify one already-open audit directory without pathname races."""

    errors: list[str] = []
    directory_metadata = os.fstat(directory_descriptor)
    if not stat.S_ISDIR(directory_metadata.st_mode):
        return {"passed": False, "errors": ["audit_directory_unreadable"]}
    if stat.S_IMODE(directory_metadata.st_mode) != AUDIT_DIRECTORY_MODE:
        errors.append("audit_directory_permissions")
    expected_names = {*AUDIT_ARTIFACT_NAMES, "manifest.json"}
    if set(os.listdir(directory_descriptor)) != expected_names:
        errors.append("audit_directory_contents")
    try:
        manifest = json.loads(
            _read_audit_file(
                directory_descriptor,
                "manifest.json",
            ).decode("utf-8")
        )
        if not isinstance(manifest, Mapping):
            raise TypeError("manifest must be a mapping")
        if not _valid_manifest_provenance(manifest):
            errors.append("manifest_provenance")
        manifest_artifacts = manifest["artifacts"]
        if (
            not isinstance(manifest_artifacts, Mapping)
            or set(manifest_artifacts) != set(AUDIT_ARTIFACT_NAMES)
        ):
            raise TypeError("manifest artifacts must be complete")
    except (
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
    ):
        return {"passed": False, "errors": [*errors, "manifest_unreadable"]}
    contents: dict[str, bytes] = {}
    for name in AUDIT_ARTIFACT_NAMES:
        try:
            content = _read_audit_file(directory_descriptor, name)
            contents[name] = content
            expected = manifest_artifacts[name]
            if (
                not isinstance(expected, Mapping)
                or set(expected) != {"sha256", "bytes"}
                or not _is_hex_digest(expected["sha256"], 64)
                or not _is_nonnegative_int(expected["bytes"])
            ):
                raise TypeError("artifact metadata must be exact")
            if len(content) != expected["bytes"]:
                errors.append(f"size:{name}")
            if sha256(content).hexdigest() != expected["sha256"]:
                errors.append(f"sha256:{name}")
        except (KeyError, OSError, TypeError):
            errors.append(f"unreadable:{name}")
    try:
        verdict = json.loads(contents["verdict.json"].decode("utf-8"))
        if not _valid_verdict(verdict):
            raise TypeError("verdict must have the exact measured schema")
    except (
        KeyError,
        RecursionError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
    ):
        errors.append("verdict_unreadable")
        verdict = {}
    try:
        inspector = json.loads(contents["inspector.json"].decode("utf-8"))
        private_records = json.loads(
            contents["private-decisions.json"].decode("utf-8")
        )
        contents["normal.txt"].decode("utf-8")
        if not isinstance(inspector, Mapping) or not isinstance(
            private_records,
            list,
        ):
            raise TypeError("audit JSON artifact has the wrong shape")
    except (
        KeyError,
        RecursionError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
    ):
        errors.append("artifact_content_unreadable")
    return {
        "passed": not errors and verdict.get("passed") is True,
        "errors": errors,
    }


def verify_autonomous_day_live_audit(
    directory: str | os.PathLike[str],
) -> dict[str, object]:
    """Recompute artifact integrity and private filesystem permissions."""

    try:
        directory_descriptor = os.open(
            Path(directory),
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
    except OSError:
        return {"passed": False, "errors": ["audit_directory_unreadable"]}
    try:
        return _verify_live_audit_descriptor(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify one AD-12 live audit bundle")
    parser.add_argument("directory")
    args = parser.parse_args(argv)
    result = verify_autonomous_day_live_audit(args.directory)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
