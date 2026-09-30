"""Continuous goal work with automatic checks, conditional review, and local commits."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .evidence import Evidence
from .protocol import WORK_SCHEMA, REVIEW_SCHEMA, validate_result
from .runtime import Busy, Store, lock, process_alive, run_process, prevent_idle_sleep


class Paused(Exception):
    pass


class Runner:
    def __init__(self, config: Config, *, clock=None, executor=run_process):
        self.config = config
        self.root = config.root
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.executor = executor
        common = Path(self.git("rev-parse", "--path-format=absolute", "--git-common-dir"))
        self.store = Store(common / "development-loop")
        self.evidence = Evidence(config, self.store)
        self.interrupted = False
        self.execution_lock = None
        self.env = os.environ.copy()
        self.env.update({str(k): os.environ.get(str(k), str(v))
                         for k, v in config.data.get("environment", {}).items()})
        self.env["PYTHONUTF8"] = "1"
        self.env.pop("CODEX_THREAD_ID", None)
        self.env.pop("DEVLOOP_EVIDENCE_DIR", None)
        if self.evidence.directory:
            self.env["DEVLOOP_EVIDENCE_DIR"] = str(self.evidence.directory)

    def git(self, *arguments: str) -> str:
        return subprocess.check_output(["git", *arguments], cwd=self.root, text=True, encoding="utf-8").strip()

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    def dirty(self) -> bool:
        return bool(self.git("status", "--porcelain", "--untracked-files=all"))

    def tree(self) -> str:
        self.git("add", "--all")
        return self.git("write-tree")

    def enable(self):
        with lock(self.store.directory / "runner.lock", blocking=False):
            state = self.store.read()
            if process_alive(state.get("child_pid")):
                raise Busy("A previous runner child is still alive; preserve its work")
            if state.get("root") not in (None, str(self.root)):
                raise ValueError("This repository already belongs to a different loop checkout")
            if not state.get("base") and self.dirty():
                raise ValueError("Enable from a clean checkout; commit or isolate existing work first")
            if state.get("base") and self.head() != state["base"] and not state.get("commit_intent"):
                raise ValueError("Checkout HEAD changed outside the runner; inspect before enabling")
            changed_goal = state.get("identity") not in (None, self.config.identity())
            if changed_goal and (state.get("base") or state.get("commit_intent")):
                raise ValueError("Resolve unfinished work before changing the approved goal or runner configuration")
            return self.store.update(enabled=True, phase="ready", reason="", failures=0,
                                     root=str(self.root), identity=self.config.identity(),
                                     goal=str(self.config.goal.relative_to(self.root)),
                                     session_id=None if changed_goal else state.get("session_id"))

    def resume(self):
        state = self.store.read()
        if state.get("root") != str(self.root) or state.get("identity") != self.config.identity():
            raise ValueError("Stop the service and enable the configured goal before resuming")
        if state["phase"] in {"blocked", "complete"}:
            raise ValueError("Inspect the blocking condition or completed goal before enabling again")
        return self.store.update(enabled=True)

    def stop_reason(self, started_at: float, wall_started: float | None = None) -> str | None:
        if not self.store.read().get("enabled"):
            return "owner_pause"
        if self.interrupted:
            return "interrupted"
        if self.config.window.remaining(self.clock()) <= self.config.window.checkpoint:
            return "window_closed"
        if self.deadline_expired(started_at, wall_started):
            return "timeout"
        return None

    def deadline_expired(self, started_at, wall_started):
        limit = self.config.limits["turn_seconds"]
        return (time.monotonic() - started_at >= limit
                or (wall_started is not None and self.clock().timestamp() - wall_started >= limit))

    def stop_requested(self, started_at: float) -> bool:
        return self.stop_reason(started_at) is not None

    def execute(self, command: list[str], name: str, prompt: str | None = None) -> Path:
        run_id = uuid.uuid4().hex[:12]
        log = self.store.directory / "runs" / f"{run_id}-{name}.jsonl"
        started_at = time.monotonic()
        wall_started = self.clock().timestamp()
        if self.stop_requested(started_at):
            raise Paused()
        timing = dict(phase=name, started_at=wall_started, finished_at=None, last_output_at=None,
                      elapsed_seconds=0, stop_reason=None, log=str(log))
        self.store.update(phase=name, last_log=str(log), execution=timing)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(json.dumps({"type":"execution.started", **timing}) + "\n", encoding="utf-8")

        def event(item):
            if item.get("type") == "execution.output":
                timing["last_output_at"] = item["observed_at"]
                self.store.update(execution=timing)
            if name == "working" and item.get("type") == "thread.started":
                self.store.update(session_id=item["thread_id"])
            if item.get("type") == "turn.completed" and "usage" in item:
                previous = self.store.read().get("usage", {})
                for key, value in item["usage"].items():
                    if isinstance(value, int):
                        previous[key] = previous.get(key, 0) + value
                self.store.update(usage=previous)

        code, stopped, reason = None, False, None
        def stop():
            nonlocal reason
            reason = reason or self.stop_reason(started_at, wall_started)
            return reason is not None
        try:
            code, stopped = self.executor(command, cwd=self.root, log=log, input_text=prompt,
                                          env=self.env, stop=stop,
                                          event=event, started=lambda pid: self.store.update(child_pid=pid),
                                          inherited_lock=self.execution_lock)
        finally:
            finished = self.clock().timestamp()
            if self.deadline_expired(started_at, wall_started):
                stopped, reason = True, reason or self.stop_reason(started_at, wall_started)
            reason = reason or (self.stop_reason(started_at, wall_started) if stopped else None)
            timing.update(finished_at=finished, elapsed_seconds=max(0, finished-wall_started),
                          stop_reason=reason or ("completed" if code == 0 else "failure"), exit_code=code)
            with log.open("a", encoding="utf-8") as output:
                output.write("\n" + json.dumps({"type":"execution.finished", **timing}) + "\n")
            self.store.update(execution=timing)
        if stopped:
            if reason == "timeout":
                raise ValueError(f"Execution exceeded the configured turn limit; see {log}")
            raise Paused()
        if code:
            raise ValueError(f"{name} failed with exit {code}; read {log} and repair the cause")
        return log

    def agent(self, prompt: str, *, review: bool = False) -> dict:
        schema = REVIEW_SCHEMA if review else WORK_SCHEMA
        name = "reviewing" if review else "working"
        schema_path = self.store.directory / f"{name}-schema.json"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        result_path = self.store.directory / f"{name}-result.json"
        result_path.unlink(missing_ok=True)
        state = self.store.read()
        command = list(self.config.command) + ["exec"]
        if not review and self.evidence.directory:
            self.evidence.prepare()
            # Parent exec options also apply when resuming a worker session.
            command += ["--add-dir", str(self.evidence.directory)]
        if not review and state.get("session_id"):
            command += ["resume", state["session_id"]]
        model = self.config.agent["review_model" if review else "model"]
        sandbox = "read-only" if review else self.config.agent["sandbox"]
        command += ["--json", "--output-schema", str(schema_path), "-o", str(result_path),
                    "-m", model, "-c", f'model_reasoning_effort="{self.config.agent["reasoning"]}"',
                    "-c", f'sandbox_mode="{sandbox}"', "-c", 'approval_policy="never"',
                    "-c", f'sandbox_workspace_write.network_access={str(self.config.agent.get("network_access", False)).lower()}', "-"]
        self.execute(command, name, prompt)
        if not result_path.exists():
            raise ValueError("Codex exited without the required structured result")
        return validate_result(json.loads(result_path.read_text(encoding="utf-8")), schema)

    def work_prompt(self) -> str:
        state = self.store.read()
        _, end = self.config.window.bounds(self.clock())
        paths = [self.config.skill, self.config.goal, *self.config.context]
        return (
            f"Advance only the approved {self.config.project} goal. Read: "
            + ", ".join(str(p.relative_to(self.root)) for p in paths)
            + ". Follow the goal-development skill. You are the sole implementation agent. "
            "Choose and finish the next smallest coherent responsibility, or continue unfinished work. "
            "Do not create task contracts, lifecycle records, orchestrators, or mandatory explorer/reviewer agents. "
            "The external runner owns review dispatch, staging, commits, and operational state. "
            "Do not change Git HEAD, push, merge, deploy, alter the runner or its configuration, or weaken the approved goal. "
            "Run focused validation and report concrete behavioral evidence; the runner runs repository checks. "
            "For live experiments use OLLAMA_BASE_URL and OLLAMA_MODEL from the environment, passing them explicitly to the scenario CLI. "
            "A useful experiment may produce a concise durable evidence artifact instead of a source-code change. "
            "Store every live audit, including failed/inconclusive attempts, in a new directory under DEVLOOP_EVIDENCE_DIR. "
            "Return artifact references with stable unique id, absolute path, and supporting or contrary classification. "
            "Never overwrite prior evidence; use the configured required identifiers only for supporting completion evidence. "
            "Use review_required for semantic risks or weak coverage. For missing product direction return blocked with one concrete question. "
            "An inconclusive experiment is evidence, not goal completion. Do not repeat live runs to select a preferred result. "
            f"The window closes at {end.isoformat()}; pause before then. "
            "Return change_ready only when a meaningful change is ready for validation and commit. "
            "Prepare all completion documentation together, then return goal_complete with the final changes and evidence for every criterion. "
            "Do not create a separate change_ready handoff solely to record already-achieved completion. "
            "Use review_scope=goal when requesting verification of all criteria, otherwise change. "
            "Return checkpoint when interrupted work needs another turn, with the exact remaining gap. "
            f"Prior result: {state.get('summary', '')}\nRemaining: {state.get('remaining', '')}\n"
            f"Feedback: {state.get('feedback', '')}\n"
            f"Required artifacts: {json.dumps(self.config.evidence.get('required_for_completion', []))}\n"
        )

    def review_reasons(self, result: dict) -> list[str]:
        reasons = []
        if result["review_required"]:
            reasons.append(result["review_reason"] or "Worker identified a semantic risk")
        if result["outcome"] == "goal_complete" or result.get("review_scope") == "goal":
            reasons.append("Independent verification of whole-goal completion")
        paths = self.git("diff", "--cached", "--name-only", "HEAD").splitlines()
        for path in paths:
            if any(fnmatch.fnmatchcase(path, p) for p in self.config.review.get("paths", [])):
                reasons.append(f"Sensitive boundary: {path}")
            if any(fnmatch.fnmatchcase(path, p) for p in self.config.review.get("test_paths", [])):
                patch = self.git("diff", "--cached", "--unified=0", "HEAD", "--", path)
                if any(line.startswith("-") and not line.startswith("---") for line in patch.splitlines()):
                    reasons.append(f"Existing test behavior changed: {path}")
                if any(line.startswith("+") and any(token in line for token in ("@skip", "skipTest", "expectedFailure", "xfail")) for line in patch.splitlines()):
                    reasons.append(f"Test suppression added: {path}")
        return reasons

    def required_review_scope(self, result):
        pending = self.store.read().get("review_obligation")
        return "goal" if (result["outcome"] == "goal_complete" or result["review_scope"] == "goal"
                          or (pending and pending["scope"] == "goal")) else "change"

    def verification_key(self, tree: str, result: dict) -> dict:
        return {"tree":tree, "identity":self.config.identity(),
                "evidence":self.evidence.fingerprint(require_complete=self.required_review_scope(result) == "goal")}

    def validate_candidate(self, result: dict, candidate_tree: str):
        key = self.verification_key(candidate_tree, result)
        receipt = self.store.read().get("verification")
        if not receipt or receipt["key"] != key:
            receipt = {"key":key, "checks":[], "review":None}
            self.store.update(verification=receipt)
        commands = self.config.check_commands()
        # A stored prefix must match the configured check order exactly.
        if [c["command"] for c in receipt["checks"]] != commands[:len(receipt["checks"])]:
            raise ValueError("Stored validation does not match configured checks")
        for command in commands[len(receipt["checks"]):]:
            log = self.execute(command, "checking")
            if self.tree() != candidate_tree or self.verification_key(candidate_tree, result) != key:
                raise ValueError("Validation changed repository content or evidence; revalidate the final change")
            receipt["checks"].append({"command":command, "log":str(log), "exit_code":0})
            self.store.update(verification=receipt, checks=receipt["checks"])
        reasons = self.review_reasons(result)
        pending = self.store.read().get("review_obligation")
        if pending:
            reasons.append("Unresolved independent review: " + pending["result"]["findings"])
        scope = self.required_review_scope(result)
        cached = receipt.get("review")
        baseline = self.store.read().get("goal_review")
        if scope == "goal" and baseline and baseline["key"] == key:
            cached = baseline
        if reasons and not (cached and (cached["scope"] == "goal" or scope == "change")):
            requested_scope = scope
            if scope == "goal" and baseline and all(baseline["key"][k] == key[k] for k in ("identity", "evidence")):
                paths = self.git("diff", "--name-only", baseline["key"]["tree"], candidate_tree).splitlines()
                if paths and set(paths) <= set(self.config.review.get("completion_paths", [])):
                    requested_scope = "completion_correction"
            while True:
                prompt = (
                    f"Independently review the candidate for {self.config.project}. Review scope: {requested_scope}. "
                    f"Read {self.config.goal.relative_to(self.root)} and relevant source/tests. "
                    "The external runner owns lifecycle state. Do not modify files, commit, or create agents. "
                    "Check behavior, failure paths, product invariants and whether evidence supports the claim. "
                    "For goal scope, verify every criterion, including required live evidence. "
                    "Return goal_criteria_verified=true only when all criteria have supporting evidence. "
                    "Report all concrete inconsistencies in one pass, not stylistic paperwork. "
                    "For completion_correction, inspect the entire diff from the prior reviewed tree. "
                    "Reuse its verified goal coverage; do not repeat the whole-goal audit unless the diff changes its basis. "
                    "Use the runner's passed checks rather than rerunning them without a concrete verification concern. "
                    "Set completion_only=true only if all changes and outstanding repairs are completion wording/evidence links "
                    "and preserve behavior, criteria, authored inputs, and evidence. Otherwise set it false to request full review. "
                    "A repair may retain verified goal coverage only when every remaining finding is completion-only. "
                    f"Prior goal coverage: {json.dumps(baseline)}\n"
                    f"Previous findings: {self.store.read().get('feedback', '')}\n"
                    f"Review triggers: {json.dumps(reasons)}\nClaim: {json.dumps(result)}\n"
                    f"Candidate: {json.dumps(key)}\nConfigured checks: {json.dumps(receipt['checks'])}\n"
                    "Return pass or repair with concise actionable findings and both coverage booleans."
                )
                decision = validate_result(self.agent(prompt, review=True), REVIEW_SCHEMA)
                if self.tree() != candidate_tree or self.head() != self.store.read()["base"]:
                    self.store.update(phase="blocked", reason="Repository changed during read-only review")
                    raise ValueError("Repository changed during read-only review")
                if self.verification_key(candidate_tree, result) != key:
                    raise ValueError("Evidence changed during review")
                if requested_scope == "completion_correction" and not decision["completion_only"]:
                    requested_scope = "goal"
                    continue
                cached = {"key":key, "scope":scope, "result":decision,
                          "requested_scope":requested_scope, "log":self.store.read().get("last_log")}
                receipt["review"] = cached
                resolved = decision["verdict"] == "pass" and (scope != "goal" or decision["goal_criteria_verified"])
                updates = dict(verification=receipt, review=decision, review_reasons=reasons,
                               review_obligation=None if resolved else cached)
                if scope == "goal":
                    covered = decision["goal_criteria_verified"] and (
                        decision["verdict"] == "pass" or decision["completion_only"])
                    updates["goal_review"] = cached if covered else None
                self.store.update(**updates)
                break
        if reasons:
            decision = cached["result"]
            if decision["verdict"] != "pass":
                raise ValueError("Review requests repair: " + decision["findings"])
            if scope == "goal" and not decision["goal_criteria_verified"]:
                raise ValueError("Whole-goal review did not verify every criterion")
            receipt["review"] = cached
            self.store.update(review=decision)
        self.store.update(verification=receipt, checks=receipt["checks"], review_reasons=reasons)
        return key

    def status(self):
        state = self.store.read()
        state["window_open"] = self.config.window.remaining(self.clock()) > self.config.window.checkpoint
        state["evidence_status"] = self.evidence.report()
        return state

    def failure(self, detail: str):
        count = self.store.read().get("failures", 0) + 1
        blocked = count >= self.config.limits["failed_attempts"] or self.store.read().get("phase") == "blocked"
        self.store.update(failures=count, phase="blocked" if blocked else "ready", feedback=detail,
                          reason=detail if blocked else "", candidate=None,
                          retry_after=time.time() + self.config.limits["retry_seconds"])

    def accept_commit(self):
        state = self.store.read()
        intent = state["commit_intent"]
        if intent.get("verification_key") != self.verification_key(intent["tree"], intent["result"]):
            raise ValueError("Commit evidence no longer matches validation; inspect before accepting")
        if self.head() == intent["base"]:
            if self.stop_requested(time.monotonic()):
                raise Paused()
            if self.tree() != intent["tree"]:
                raise ValueError("Validated content changed before commit")
            self.execute(["git", "commit", "-m", intent["message"]], "committing")
        if (self.git("rev-parse", "HEAD^") != intent["base"]
                or self.git("rev-parse", "HEAD^{tree}") != intent["tree"] or self.dirty()):
            raise ValueError("Commit recovery does not match the validated change; inspect the checkout")
        if intent["verification_key"] != self.verification_key(intent["tree"], intent["result"]):
            raise ValueError("Evidence changed during commit; completion is not accepted")
        self.finish(intent["result"], self.head())

    def finish(self, result: dict, commit: str):
        complete = result["outcome"] == "goal_complete"
        self.store.update(phase="complete" if complete else "ready", summary=result["summary"],
                          remaining=result["remaining"], evidence=result["evidence"], last_commit=commit,
                          base=None, candidate=None, commit_intent=None, failures=0, feedback="", reason="")
        print(json.dumps({"project": self.config.project, "phase": "complete" if complete else "accepted",
                          "summary": result["summary"], "commit": commit, "remaining": result["remaining"]}), flush=True)

    def step(self) -> str:
        """One stateful unit; successive units need no timer or new session."""
        state = self.store.read()
        if not state.get("enabled") or state["phase"] in {"blocked", "complete"}:
            return state["phase"] if state.get("enabled") else "paused"
        if self.config.window.remaining(self.clock()) <= self.config.window.checkpoint:
            return "outside_window"
        if state.get("identity") != self.config.identity():
            self.store.update(phase="blocked", reason="Goal or runner configuration changed; inspect and explicitly enable again")
            return "blocked"
        if state.get("retry_after", 0) > time.time():
            return "retry_wait"
        try:
            if state.get("commit_intent"):
                self.accept_commit()
                return self.store.read()["phase"]
            if state.get("base"):
                if self.head() != state["base"]:
                    self.store.update(phase="blocked", reason="Git HEAD changed outside runner acceptance")
                    return "blocked"
            else:
                if self.dirty():
                    self.store.update(phase="blocked", reason="Unowned checkout changes; inspect before continuing")
                    return "blocked"
                self.store.update(base=self.head())
            result = validate_result(state.get("candidate") or self.agent(self.work_prompt()), WORK_SCHEMA)
            if self.head() != self.store.read()["base"]:
                self.store.update(phase="blocked", reason="Worker changed Git HEAD; inspect before continuing")
                return "blocked"
            self.store.update(summary=result["summary"], remaining=result["remaining"])
            self.evidence.register(result["artifacts"])
            if result["outcome"] == "blocked":
                self.store.update(phase="blocked", reason=result["remaining"] or result["summary"])
                return "blocked"
            if result["outcome"] == "checkpoint":
                self.failure("Continue the unfinished responsibility: " + result["remaining"])
                return self.store.read()["phase"]
            if not result["summary"].strip() or not result["evidence"].strip():
                raise ValueError("A completion claim needs a concrete result and behavioral evidence")
            changed = self.dirty()
            if not changed and result["outcome"] != "goal_complete":
                raise ValueError("No repository change supports this claimed implementation; close a concrete goal gap")
            if self.config.identity() != self.store.read()["identity"]:
                self.store.update(phase="blocked", reason="Worker changed the approved goal or runner configuration")
                return "blocked"
            candidate_tree = self.tree()
            self.store.update(candidate=result)
            key = self.validate_candidate(result, candidate_tree)
            if changed:
                if not result["commit_message"].strip():
                    raise ValueError("A ready change needs a concise commit message")
                self.store.update(commit_intent={"base": self.store.read()["base"], "tree": candidate_tree,
                                                "message": result["commit_message"], "result": result,
                                                "verification_key":key})
                self.accept_commit()
            else:
                if self.verification_key(candidate_tree, result) != key or self.tree() != candidate_tree:
                    raise ValueError("Validated content or evidence changed before completion")
                self.finish(result, self.head())
        except Paused:
            self.store.update(phase="ready", reason="Execution paused; unfinished work is preserved")
            return "paused"
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            self.failure(str(error))
        return self.store.read()["phase"]

    def run(self, *, service: bool = False) -> int:
        with lock(self.store.directory / "runner.lock", blocking=False) as handle:
            self.execution_lock = handle
            state = self.store.read()
            if state.get("root") not in (None, str(self.root)):
                raise ValueError("The active loop belongs to another checkout")
            if process_alive(state.get("child_pid")):
                raise Busy("A previous runner child is still alive; preserve its work")
            self.store.update(runner_pid=os.getpid(), child_pid=None)
            try:
                while not self.interrupted:
                    state = self.store.read()
                    active = (state.get("enabled") and state["phase"] not in {"complete", "blocked"}
                              and self.config.window.remaining(self.clock()) > self.config.window.checkpoint)
                    with prevent_idle_sleep(bool(active), self.config.window.remaining(self.clock())):
                        result = self.step()
                    if result in {"complete", "blocked"} and not service:
                        return 0 if result == "complete" else 2
                    if result in {"outside_window", "paused", "retry_wait", "complete", "blocked"}:
                        # Cheap code waits. No model call or hourly boundary is involved.
                        for _ in range(20):
                            if self.interrupted:
                                break
                            time.sleep(0.25)
                return 0
            finally:
                self.store.update(runner_pid=None)
                self.execution_lock = None


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("development-loop.toml"))
    parser.add_argument("command", choices=("run", "status", "enable", "pause", "resume", "doctor", "dashboard", "migrate-evidence"))
    parser.add_argument("--service", action="store_true", help="Stay available while blocked or complete, without model calls")
    args = parser.parse_args(arguments)
    try:
        runner = Runner(Config(args.config))
        if args.command == "dashboard":
            from .dashboard import open_dashboard
            return open_dashboard(runner)
        elif args.command == "status":
            print(json.dumps(runner.status(), indent=2))
        elif args.command == "migrate-evidence":
            with lock(runner.store.directory / "runner.lock", blocking=False):
                if process_alive(runner.store.read().get("child_pid")):
                    raise Busy("A runner child is still alive")
                print(json.dumps(runner.evidence.migrate(), indent=2))
        elif args.command == "enable":
            print(json.dumps(runner.enable(), indent=2))
        elif args.command == "resume":
            print(json.dumps(runner.resume(), indent=2))
        elif args.command == "pause":
            print(json.dumps(runner.store.update(enabled=False), indent=2))
        elif args.command == "doctor":
            command = runner.config.command[0]
            if not shutil.which(command):
                raise ValueError(f"Executable not found: {command}")
            print(json.dumps({"project": runner.config.project, "python": sys.version.split()[0],
                              "agent": shutil.which(command), "goal": str(runner.config.goal),
                              "state": str(runner.store.path), "dirty": runner.dirty(),
                              "evidence_status":runner.evidence.report()}))
        else:
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, lambda *_: setattr(runner, "interrupted", True))
            return runner.run(service=args.service)
        return 0
    except (OSError, ValueError, Busy, subprocess.CalledProcessError) as error:
        print(f"Development loop: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
