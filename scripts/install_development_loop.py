#!/usr/bin/env python3
"""Install or remove the Mac background service without enabling goal execution."""

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from devloop.config import Config
from devloop.runner import Runner
from devloop.runtime import lock


def service_definition(config: Config, label: str, logs: Path) -> dict:
    executable = shutil.which(config.command[0])
    if executable is None:
        raise ValueError(f"Executable not found: {config.command[0]}")
    return {
        "Label": label,
        "ProgramArguments": [sys.executable, "-m", "devloop", "--config", str(config.path), "run", "--service"],
        "WorkingDirectory": str(config.root),
        "EnvironmentVariables": {
            "PATH": os.pathsep.join([str(Path(executable).parent), str(Path(sys.executable).parent),
                                     os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")]),
            "PYTHONUNBUFFERED": "1",
            **{key: os.environ.get(key, str(value)) for key, value in config.data.get("environment", {}).items()},
        },
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 30,
        "ExitTimeOut": 15,
        "StandardOutPath": str(logs / "service.log"),
        "StandardErrorPath": str(logs / "service-errors.log"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("install", "remove"))
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "development-loop.toml")
    parser.add_argument("--label", help="Reuse an existing launchd label during migration")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("This installer runs on macOS")
    config = Config(args.config)
    runner = Runner(config)
    args.label = args.label or runner.store.read().get("service_label", f"local.devloop.{config.project}")
    if not args.label or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-" for c in args.label):
        parser.error("Use a plain launchd service label")
    plist = Path.home() / "Library" / "LaunchAgents" / (args.label + ".plist")
    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{args.label}"
    # Build and validate everything before replacing an existing service.
    definition = service_definition(config, args.label, runner.store.directory) if args.command == "install" else None
    if args.command == "install":
        subprocess.run(config.command + ["login", "status"], check=True, cwd=config.root)
        runner.git("var", "GIT_AUTHOR_IDENT")
        if runner.store.read().get("enabled"):
            raise ValueError("Pause the loop before replacing its background service")
    loaded = subprocess.run(["launchctl", "print", service], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if loaded.returncode == 0:
        subprocess.run(["launchctl", "bootout", service], check=True)
    # bootout returns before SIGTERM cleanup has necessarily released ownership.
    with lock(runner.store.directory / "runner.lock", timeout=15):
        if args.command == "remove":
            runner.store.update(enabled=False)
            plist.unlink(missing_ok=True)
            print("Background service removed; repository and runner state preserved.")
            return
        state = runner.store.read()
        if state.get("enabled"):
            raise ValueError("Pause the loop before replacing its background service")
        if state.get("root") not in (None, str(config.root)):
            raise ValueError("This repository already belongs to another loop checkout")
        if not state.get("identity"):
            runner.store.update(root=str(config.root), identity=config.identity(),
                                goal=str(config.goal.relative_to(config.root)))
        runner.store.update(service_label=args.label)
        plist.parent.mkdir(parents=True, exist_ok=True)
        if plist.exists():
            backup = runner.store.directory / (args.label + ".previous.plist")
            if not backup.exists():
                shutil.copy2(plist, backup)
        temporary = plist.with_suffix(".tmp")
        temporary.write_bytes(plistlib.dumps(definition))
        temporary.replace(plist)
    subprocess.run(["launchctl", "bootstrap", domain, str(plist)], check=True)
    print(f"Installed {plist}; goal execution remains paused.")
    print(f"From {config.root}, use python3 -m devloop resume when ready.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Development loop installation: {error}")
