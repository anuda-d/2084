# Continuous goal development

One working agent advances the approved goal through coherent changes, with deterministic checks and conditional independent review.
The shared runner is configured by `development-loop.toml`; implementation guidance lives in `.agents/skills/goal-development/SKILL.md`.

## Execution

The Mac hosts the repository, Codex CLI, development runner, and tests.
The Windows PC only runs Ollama for the simulation's `qwen3:4b-instruct` model.
The Mac connects to its private LAN endpoint through `OLLAMA_BASE_URL`.
The configured address, `http://10.0.0.160:11434`, comes from the previously verified live setup; an environment value overrides it.
The PC must be reachable for live experiments, while provider-free implementation and checks can run without it.

The daily window is 18:00-23:00 America/Toronto.
During that window the runner immediately continues after accepted work, using the same Codex session.
Starting at 20:37 works just as starting at 18:00 does.
Outside the window it waits without invoking a model.
The final two minutes are reserved for stopping child processes and preserving unfinished work.
There is no hourly work cadence or fixed number of changes per generation.

The Mac must be awake to work.
During active work the runner uses `caffeinate` to prevent idle sleep, bounded by the window's end and the runner's lifetime.
It allows idle sleep while paused, blocked, complete, or outside the window.
It does not wake a powered-off Mac or override lid-close sleep.
Codex uses the Mac's existing CLI sign-in; the desktop app does not need to remain open.

## Working procedure

The approved goal defines direction and constraints.
The working agent chooses a concrete remaining gap, investigates relevant behavior, implements a coherent responsibility, and performs focused verification.
It returns a brief result and remaining uncertainty.
Useful experiments may produce concise evidence artifacts; inconclusive outcomes never count as a satisfied goal criterion.

The runner stages the candidate, runs configured repository checks, and binds acceptance to that Git tree.
Changed content invalidates prior validation.
Failing checks normally return work to the same agent for repair.
Sensitive file paths, modification of existing tests, explicit semantic concerns, and whole-goal completion trigger independent read-only review.
Routine passing changes do not require another agent.
Three unsuccessful attempts block the current work; the count survives process restarts.

After acceptance the runner commits the tested and reviewed tree locally.
It immediately proceeds to the next meaningful gap while time remains.
It never automatically pushes, merges, deploys, chooses a new goal, or changes its own configuration.

## State and control

Runtime state, raw execution logs, check results, and review results live under the repository's Git common directory in `development-loop/`.
They are not repository commits or documents maintained by the agent.
Only one runner may own a repository, including across its worktrees.
Use a checkout reserved for the loop; pause and stop its child before manual edits.
Unrelated dirty work blocks startup, while interrupted runner-owned changes remain available for continuation.
An interrupted commit is reconciled against its exact parent and validated tree before another change starts.

For a foreground run from a clean checkout:

```sh
python3 -m devloop doctor
python3 -m devloop enable
python3 -m devloop run
```

For status and control from another terminal:

```sh
python3 -m devloop status
python3 -m devloop pause
python3 -m devloop resume
```

`pause` stops the child and preserves unfinished work.
Wait until status reports no `child_pid` before editing the checkout.
`resume` continues the same configured goal without resetting failures or bypassing a block.
`enable` authorizes the configured goal or resets an inspected blocking condition; stop the background service before using it.
Do not use it blindly to cycle through failures.
Goal or runner-configuration changes require inspection and a new `enable`, and unfinished work must first be resolved.

Status contains the active session, phase, remaining gap, latest result, and paths to detailed execution logs.
This CLI is the initial control interface; external notifications are not configured.
A time-window pause preserves the session, candidate, and retry count automatically.

## Mac background service

The Mac needs Python 3.11 or later, Git with an author identity, and an authenticated Codex CLI.
Run the repository checks before installation.
Installation registers a per-user `launchd` service and leaves execution paused:

```sh
./scripts/check.sh
python3 scripts/install_development_loop.py install
python3 -m devloop resume
```

`launchd` keeps the lightweight runner available while the user is logged in and restarts it after a crash or next login.
The runner itself controls the window and continuous work.
After the Mac wakes, the runner checks the current time and continues if eligible.
No model calls occur while paused, outside the window, blocked, or complete.
The foreground `run` command exits on completion or a block; the background service stays available for control commands.

To stop and remove the service while preserving work and state:

```sh
python3 -m devloop pause
python3 scripts/install_development_loop.py remove
```

The default service label on a new installation is `local.devloop.2084`.
Use `--label` to replace an existing service under another label; the installer remembers it for later installation and removal commands.
Keep the retired `autonomous-2084-development-loop` Codex automation paused and remove any superseded scheduled launcher before enabling this one.

## Migration and verification

The previous per-slice contracts, generation transfers, and manually synchronized runtime summaries are retired.
Their original state is preserved in `docs/archive/development-loop-20260916.json`, with the prior human-readable snapshot beside it.
Those files are historical evidence and cannot activate this runner.
The existing product goal and accepted implementation evidence remain intact.

```sh
python3 -m unittest tests.test_development_runner
./scripts/check.sh
```

The runner tests exercise real Git commits and child processes with a controlled Codex substitute.
They cover continuous progress, window boundaries, live service pause/resume, review routing, failed checks, preserved work, exclusive ownership, and interrupted commit recovery.
