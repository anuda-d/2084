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
from .runtime import Busy, Store, lock, process_alive, run_process, prevent_idle_sleep


WORK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "outcome": {"type": "string", "enum": ["change_ready", "goal_complete", "blocked", "checkpoint"]},
        "summary": {"type": "string"}, "evidence": {"type": "string"},
        "remaining": {"type": "string"}, "commit_message": {"type": "string"},
        "review_required": {"type": "boolean"}, "review_reason": {"type": "string"},
    },
    "required": ["outcome", "summary", "evidence", "remaining", "commit_message", "review_required", "review_reason"],
}
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"verdict": {"type": "string", "enum": ["pass", "repair"]}, "findings": {"type": "string"}},
    "required": ["verdict", "findings"],
}


class Paused(Exception):
    pass


def validate_result(value: object, schema: dict) -> dict:
    if not isinstance(value, dict) or set(value) != set(schema["required"]):
        raise ValueError("Agent result is missing fields or has unexpected fields")
    for name, rule in schema["properties"].items():
        expected = bool if rule["type"] == "boolean" else str
        if not isinstance(value[name], expected) or ("enum" in rule and value[name] not in rule["enum"]):
            raise ValueError(f"Invalid agent result field: {name}")
    return value


class Runner:
    def __init__(self, config: Config, *, clock=None, executor=run_process):
        self.config = config
        self.root = config.root
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.executor = executor
        common = Path(self.git("rev-parse", "--path-format=absolute", "--git-common-dir"))
        self.store = Store(common / "development-loop")
        self.interrupted = False
        self.execution_lock = None
        self.env = os.environ.copy()
        self.env.update({str(k): os.environ.get(str(k), str(v))
                         for k, v in config.data.get("environment", {}).items()})
        self.env["PYTHONUTF8"] = "1"
        self.env.pop("CODEX_THREAD_ID", None)

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

    def stop_requested(self, started_at: float) -> bool:
        return (self.interrupted or not self.store.read().get("enabled")
                or self.config.window.remaining(self.clock()) <= self.config.window.checkpoint
                or time.monotonic() - started_at >= self.config.limits["turn_seconds"])

    def execute(self, command: list[str], name: str, prompt: str | None = None) -> Path:
        run_id = uuid.uuid4().hex[:12]
        log = self.store.directory / "runs" / f"{run_id}-{name}.jsonl"
        started_at = time.monotonic()
        if self.stop_requested(started_at):
            raise Paused()
        self.store.update(phase=name, last_log=str(log))

        def event(item):
            if name == "working" and item.get("type") == "thread.started":
                self.store.update(session_id=item["thread_id"])
            if item.get("type") == "turn.completed" and "usage" in item:
                previous = self.store.read().get("usage", {})
                for key, value in item["usage"].items():
                    if isinstance(value, int):
                        previous[key] = previous.get(key, 0) + value
                self.store.update(usage=previous)

        code, stopped = self.executor(command, cwd=self.root, log=log, input_text=prompt,
                                      env=self.env, stop=lambda: self.stop_requested(started_at),
                                      event=event, started=lambda pid: self.store.update(child_pid=pid),
                                      inherited_lock=self.execution_lock)
        if stopped:
            if time.monotonic() - started_at >= self.config.limits["turn_seconds"]:
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
            "Use review_required for semantic risks or weak coverage. For missing product direction return blocked with one concrete question. "
            "An inconclusive experiment is evidence, not goal completion. Do not repeat live runs to select a preferred result. "
            f"The window closes at {end.isoformat()}; pause before then. "
            "Return change_ready only when a meaningful change is ready for validation and commit. "
            "Return goal_complete only with evidence for every goal criterion. "
            "Return checkpoint when interrupted work needs another turn, with the exact remaining gap. "
            f"Prior result: {state.get('summary', '')}\nRemaining: {state.get('remaining', '')}\n"
            f"Feedback: {state.get('feedback', '')}\n"
        )

    def review_reasons(self, result: dict) -> list[str]:
        reasons = []
        if result["review_required"]:
            reasons.append(result["review_reason"] or "Worker identified a semantic risk")
        if result["outcome"] == "goal_complete":
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

    def failure(self, detail: str):
        count = self.store.read().get("failures", 0) + 1
        blocked = count >= self.config.limits["failed_attempts"]
        self.store.update(failures=count, phase="blocked" if blocked else "ready", feedback=detail,
                          reason=detail if blocked else "", candidate=None,
                          retry_after=time.time() + self.config.limits["retry_seconds"])

    def accept_commit(self):
        state = self.store.read()
        intent = state["commit_intent"]
        if self.head() == intent["base"]:
            if self.stop_requested(time.monotonic()):
                raise Paused()
            if self.tree() != intent["tree"]:
                raise ValueError("Validated content changed before commit")
            self.execute(["git", "commit", "-m", intent["message"]], "committing")
        if (self.git("rev-parse", "HEAD^") != intent["base"]
                or self.git("rev-parse", "HEAD^{tree}") != intent["tree"] or self.dirty()):
            raise ValueError("Commit recovery does not match the validated change; inspect the checkout")
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
            result = state.get("candidate") or self.agent(self.work_prompt())
            if self.head() != self.store.read()["base"]:
                self.store.update(phase="blocked", reason="Worker changed Git HEAD; inspect before continuing")
                return "blocked"
            self.store.update(summary=result["summary"], remaining=result["remaining"])
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
            checks = []
            for command in self.config.check_commands():
                log = self.execute(command, "checking")
                checks.append({"command": command, "log": str(log), "exit_code": 0})
            if self.tree() != candidate_tree:
                raise ValueError("Validation changed repository content; inspect and revalidate the final change")
            reasons = self.review_reasons(result)
            review = None
            if reasons:
                prompt = (
                    f"Independently review the staged change and the completion claim for {self.config.project}. "
                    f"Read {self.config.goal.relative_to(self.root)} and relevant source/tests. "
                    "The external runner owns lifecycle state. Do not invoke the retired loop, modify files, commit, or create agents. "
                    "Check actual behavior, relevant failure paths, product invariants, and whether evidence supports the claimed result. "
                    "For goal_complete, verify every goal criterion, including live evidence where required. "
                    "Block on concrete correctness, scope, or unsupported-evidence findings; avoid stylistic paperwork findings. "
                    f"Review triggers: {json.dumps(reasons)}\nClaim: {json.dumps(result)}\n"
                    f"Configured checks: {json.dumps(checks)}\nReturn pass or repair with concise actionable findings."
                )
                review = self.agent(prompt, review=True)
                if self.tree() != candidate_tree or self.head() != self.store.read()["base"]:
                    self.store.update(phase="blocked", reason="Repository changed during read-only review")
                    return "blocked"
                if review["verdict"] != "pass":
                    raise ValueError("Review requests repair: " + review["findings"])
            self.store.update(checks=checks, review=review, review_reasons=reasons)
            if changed:
                if not result["commit_message"].strip():
                    raise ValueError("A ready change needs a concise commit message")
                self.store.update(commit_intent={"base": self.store.read()["base"], "tree": candidate_tree,
                                                "message": result["commit_message"], "result": result})
                self.accept_commit()
            else:
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
    parser.add_argument("command", choices=("run", "status", "enable", "pause", "resume", "doctor", "dashboard"))
    parser.add_argument("--service", action="store_true", help="Stay available while blocked or complete, without model calls")
    args = parser.parse_args(arguments)
    try:
        runner = Runner(Config(args.config))
        if args.command == "dashboard":
            from .dashboard import open_dashboard
            return open_dashboard(runner)
        elif args.command == "status":
            status = runner.store.read()
            status["window_open"] = runner.config.window.remaining(runner.clock()) > runner.config.window.checkpoint
            print(json.dumps(status, indent=2))
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
                              "state": str(runner.store.path), "dirty": runner.dirty()}))
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
