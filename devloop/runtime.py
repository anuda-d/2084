"""Local persistence, exclusive execution, and bounded child processes."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

import fcntl

from .protocol import validate_verification_state


class Busy(RuntimeError):
    pass


@contextlib.contextmanager
def lock(path: Path, *, blocking: bool = True, timeout: float | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        deadline = time.monotonic() + timeout if timeout is not None else None
        while True:
            try:
                flags = 0 if blocking and deadline is None else fcntl.LOCK_NB
                fcntl.flock(handle, fcntl.LOCK_EX | flags)
                break
            except BlockingIOError as error:
                if not blocking or (deadline is not None and time.monotonic() >= deadline):
                    raise Busy("Another runner owns this checkout") from error
                time.sleep(0.05)
        try:
            yield handle
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        self.path = directory / "state.json"

    def read(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "enabled": False, "phase": "paused", "failures": 0}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or data.get("version") != 1
                or type(data.get("enabled")) is not bool
                or type(data.get("failures")) is not int or data["failures"] < 0
                or data.get("phase") not in {"paused", "ready", "working", "checking", "reviewing", "committing", "blocked", "complete"}):
            raise ValueError("Unsupported or corrupt runner state")
        try:
            validate_verification_state(data)
        except (TypeError, KeyError) as error:
            raise ValueError("Corrupt verification or evidence state") from error
        return data

    def update(self, **changes) -> dict:
        with lock(self.directory / "state.lock"):
            data = self.read()
            data.update(changes)
            data["updated_at"] = time.time()
            temporary = self.path.with_suffix(".tmp")
            with temporary.open("w", encoding="utf-8") as output:
                json.dump(data, output, indent=2, ensure_ascii=False)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            return data


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


@contextlib.contextmanager
def prevent_idle_sleep(active: bool, remaining: float):
    """Keep the Mac awake during work, with a window deadline and parent lifetime."""
    process = None
    if active and sys.platform == "darwin":
        process = subprocess.Popen(["/usr/bin/caffeinate", "-i", "-w", str(os.getpid()),
                                    "-t", str(max(1, int(remaining)))],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        yield
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)


def stop_process(process: subprocess.Popen):
    # A completed CLI can leave tool children alive; clean up its process group too.
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        process.wait()
        return
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=10)


def run_process(
    command: list[str], *, cwd: Path, log: Path, input_text: str | None,
    env: dict[str, str], stop: Callable[[], bool], event: Callable[[dict], None],
    started: Callable[[int | None], None], inherited_lock=None,
) -> tuple[int, bool]:
    """Persist output before consuming it; stop the whole process group on pause."""
    log.parent.mkdir(parents=True, exist_ok=True)
    options = {
        "start_new_session": True,
        "pass_fds": (inherited_lock.fileno(),) if inherited_lock else (),
    }
    interrupted = False
    with log.open("a", encoding="utf-8") as output, tempfile.TemporaryFile(mode="w+", encoding="utf-8") as input_file:
        input_file.write(input_text or "")
        input_file.seek(0)
        initial_offset = output.tell()
        process = subprocess.Popen(command, cwd=cwd, env=env, stdin=input_file,
                                   stdout=output, stderr=subprocess.STDOUT, text=True,
                                   encoding="utf-8", **options)
        try:
            started(process.pid)
            with log.open(encoding="utf-8", errors="replace") as stream:
                stream.seek(initial_offset)
                pending = ""
                while True:
                    chunk = stream.read()
                    if chunk:
                        event({"type":"execution.output", "observed_at":time.time()})
                    pending += chunk
                    lines = pending.split("\n")
                    pending = lines.pop()
                    for line in lines:
                        try:
                            value = json.loads(line)
                        except ValueError:
                            continue
                        if isinstance(value, dict):
                            event(value)
                    if process.poll() is not None:
                        # The file may have grown after the read and before poll.
                        tail = stream.read()
                        if tail:
                            event({"type":"execution.output", "observed_at":time.time()})
                        for line in (pending + tail).splitlines():
                            try:
                                value = json.loads(line)
                                if isinstance(value, dict):
                                    event(value)
                            except ValueError:
                                pass
                        break
                    if stop():
                        interrupted = True
                        stop_process(process)
                    time.sleep(0.1)
            return process.returncode, interrupted
        finally:
            stop_process(process)
            started(None)
