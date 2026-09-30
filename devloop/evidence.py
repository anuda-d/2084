"""Private, durable audit references; historical acceptance is never rewritten."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import uuid
from pathlib import Path


def validate_reference(value):
    if (not isinstance(value, dict) or set(value) != {"id", "path", "classification"}
            or not isinstance(value["id"], str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", value["id"])
            or not isinstance(value["path"], str) or not Path(value["path"]).is_absolute()
            or not isinstance(value["classification"], str)
            or value["classification"] not in {"supporting", "contrary"}):
        raise ValueError("Invalid evidence artifact reference")


class Evidence:
    def __init__(self, config, store):
        self.config, self.store = config, store

    @property
    def directory(self):
        value = self.config.evidence.get("directory")
        return Path(value).expanduser().resolve() if value else None

    @property
    def goal_key(self):
        return hashlib.sha256(str(self.config.goal.relative_to(self.config.root)).encode()
                              + b"\0" + self.config.goal.read_bytes()).hexdigest()

    def records(self):
        return self.store.read().get("artifacts", {}).get(self.goal_key, {})

    def save(self, records):
        goals = self.store.read().get("artifacts", {})
        goals[self.goal_key] = records
        self.store.update(artifacts=goals)

    def prepare(self):
        root = self.directory
        if root is None:
            return
        if root.is_relative_to(self.config.root):
            raise ValueError("Evidence directory must be outside the checkout")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = root.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("Evidence directory must be owner-only (0700)")

    def inspect(self, path):
        # The audit verifier checks every file's permissions, shape and digest.
        from scenarios.autonomous_day_audit import verify_autonomous_day_live_audit
        path = Path(path)
        before = path.lstat()
        if not stat.S_ISDIR(before.st_mode) or before.st_uid != os.getuid():
            raise ValueError("Evidence must be an owned real directory")
        manifest = path / "manifest.json"
        descriptor = os.open(manifest, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            digest = hashlib.sha256(stream.read()).hexdigest()
        verdict = verify_autonomous_day_live_audit(path)
        if verdict["errors"]:
            raise ValueError("Invalid evidence: " + ", ".join(verdict["errors"]))
        after = path.lstat()
        if ((before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                or hashlib.sha256(manifest.read_bytes()).hexdigest() != digest):
            raise ValueError("Evidence changed during verification")
        return dict(manifest_sha256=digest, device=before.st_dev, inode=before.st_ino,
                    verification=verdict)

    def register(self, references):
        if references:
            self.prepare()
        records = self.records()
        for reference in references:
            validate_reference(reference)
            path = Path(reference["path"])
            if self.directory is None or not path.resolve().is_relative_to(self.directory) or path.resolve() == self.directory:
                raise ValueError("Evidence artifact must be beneath the managed directory")
            measured = self.inspect(path)
            row = {**reference, "path":str(path.resolve()), **measured,
                   "goal":str(self.config.goal.relative_to(self.config.root))}
            previous = records.get(row["id"])
            if previous and not previous.get("historical_missing") and previous != row:
                raise ValueError("Evidence identifier already registered; retain it and use a new identifier")
            records[row["id"]] = row
            # Each successfully registered artifact survives a later bad reference.
            self.save(records)

    def report(self):
        records = self.records()
        required = self.config.evidence.get("required_for_completion", [])
        rows = []
        for identifier in sorted(set(records) | set(required)):
            record = records.get(identifier, {})
            row = {**record, "id":identifier, "required":identifier in required,
                   "availability":"missing", "passed":False}
            path = record.get("path")
            if path and os.path.lexists(path):
                try:
                    if self.directory is None or not Path(path).resolve().is_relative_to(self.directory):
                        raise ValueError("Evidence is outside managed storage")
                    measured = self.inspect(path)
                    if any(record.get(key) != measured[key] for key in ("manifest_sha256", "device", "inode")):
                        raise ValueError("Evidence differs from the registered artifact")
                    row.update(availability="available", passed=measured["verification"]["passed"])
                except (OSError, ValueError) as error:
                    row.update(availability="invalid", error=str(error))
            rows.append(row)
        missing = any(r["required"] and (r["availability"] != "available" or not r["passed"]
                                         or r.get("classification") != "supporting") for r in rows)
        historical = self.store.read().get("phase") == "complete"
        summary = ("Previously accepted; original live evidence unavailable." if historical and missing
                   else "Required completion evidence unavailable." if missing
                   else "Registered evidence verified." if rows else "No external evidence required.")
        return {"summary":summary, "required_available":not missing, "artifacts":rows}

    def fingerprint(self, *, require_complete=False):
        report = self.report()
        if require_complete and not report["required_available"]:
            identifiers = ", ".join(r["id"] for r in report["artifacts"] if r["required"])
            raise ValueError("Required evidence unavailable or not supporting: " + identifiers)
        fingerprint = {}
        for row in report["artifacts"]:
            # Required-but-not-yet-created artifacts are allowed during development.
            if "manifest_sha256" not in row:
                if row.get("classification") == "supporting" and not row.get("historical_missing"):
                    raise ValueError("Registered evidence missing: " + row["id"])
                continue
            if row["availability"] != "available":
                raise ValueError("Registered evidence missing or changed: " + row["id"])
            if row["classification"] == "supporting" and not row["passed"]:
                raise ValueError("Supporting evidence failed verification: " + row["id"])
            fingerprint[row["id"]] = {key:row[key] for key in
                                       ("manifest_sha256", "path", "device", "inode", "classification", "passed")}
        return fingerprint

    def migrate(self):
        """Import known legacy bundles, or retain an explicit missing reference."""
        state = self.store.read()
        if state.get("enabled") or state.get("child_pid"):
            raise ValueError("Pause the runner and stop its child before evidence migration")
        self.prepare()
        for identifier, original in self.config.evidence.get("legacy", {}).items():
            previous = self.records().get(identifier)
            if previous and not previous.get("historical_missing"):
                continue
            source = Path(original).expanduser()
            candidates = [source]
            for root in self.config.evidence.get("recovery_roots", []):
                directory = Path(root).expanduser()
                if directory.is_dir():
                    candidates.extend(directory.rglob(source.name))
            recovered = False
            for candidate in dict.fromkeys(candidates):
                try:
                    measured = self.inspect(candidate)
                    if not measured["verification"]["passed"]:
                        continue
                except (OSError, ValueError):
                    continue
                target = self.directory / (identifier + "-recovered-" + uuid.uuid4().hex[:12])
                # Never modify/delete the original or overwrite a previous copy.
                shutil.copytree(candidate, target, symlinks=True)
                copied = self.inspect(target)
                if copied["manifest_sha256"] != measured["manifest_sha256"]:
                    raise ValueError("Recovered evidence copy differs from original")
                self.register([dict(id=identifier, path=str(target), classification="supporting")])
                recovered = True
                break
            if not recovered:
                records = self.records()
                records[identifier] = dict(id=identifier, path=str(source), classification="supporting",
                                           historical_missing=True, goal=str(self.config.goal.relative_to(self.config.root)))
                self.save(records)
        return self.report()
