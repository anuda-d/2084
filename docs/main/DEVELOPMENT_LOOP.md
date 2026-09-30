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
There is no hourly work cadence or fixed number of changes per session.

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
Each completed check and review is persisted against the tree, approval identity, and registered evidence fingerprints.
An interrupted check or review restarts; already-completed verification survives pauses and restarts when its inputs are unchanged.
Failing checks normally return work to the same agent for repair.
Sensitive file paths, modification of existing tests, explicit semantic concerns, and whole-goal completion trigger independent read-only review.
Routine passing changes do not require another agent.
Three unsuccessful attempts block the current work; the count survives process restarts.
Outstanding review findings remain mandatory until an independent review resolves them, regardless of later worker flags.

The worker prepares completion documentation together and returns `goal_complete` with its final changes.
Structured results declare `review_scope` as `change` or `goal` and list `artifacts` with `id`, absolute `path`, and `supporting` or `contrary` classification.
A review separately records `goal_criteria_verified` and whether its corrections are `completion_only`.
The runner can check, review, commit, and complete that candidate in one transition.
A commit preserving the same validated tree does not require another whole-goal review.
Corrections within the configured completion-document allowlist receive a focused recheck only when an independent reviewer confirms unchanged behavior, criteria, authored inputs, and evidence.
Otherwise the runner requires a full goal review; changed trees still run all configured repository checks.

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
Goal-file or runner-configuration changes require inspection and a new `enable`, and unfinished work must first be resolved.
The approval identity hashes the entire goal file, so even a documentation-only link edit requires re-enabling after review; it does not renew exhausted live-experiment budgets.

Status contains the active session, phase, remaining gap, latest result, and paths to detailed execution logs.
A time-window pause preserves the session, candidate, and retry count automatically.
The 45-minute per-execution limit uses both monotonic time and an absolute wall deadline, including an overdue process that has already exited on wake.
Logs record phase, start, finish, last output, session elapsed time, and whether work completed, failed, timed out, paused, or crossed the window boundary.
Session elapsed time includes waiting and is not a measure of productive coding time.

## Durable evidence

Private audit bundles live under `~/.local/share/2084/evidence`, outside the checkout, with owner-only permissions.
The runner exposes this location as `DEVLOOP_EVIDENCE_DIR` and grants the worker bounded write access there.
The live CLI requires an audit target beneath that root before constructing a provider during runner-managed work.
Keep every failed or inconclusive attempt and return its artifact reference as contrary evidence.
The registry retains goal association, original manifest digest, filesystem identity, and verification result without overwriting an existing identifier.
Required completion artifacts must be supporting, present, and intact before goal review, verification reuse, and final acceptance.
A generic audit pass does not establish the semantic goal criterion; independent review still assesses the claim.
Status, doctor, and the dashboard show evidence availability separately from historical completion.

With the runner paused, its child stopped, and the service unloaded, recover configured legacy bundles using:

```sh
python3 -m devloop migrate-evidence
```

Migration searches the documented locations and configured recovery roots, copies verified originals into private durable storage, and preserves the originals.
Unrecoverable evidence remains explicitly unavailable while the historical completion verdict stays intact.
Migration does not invent verification receipts, authorize new experiments, reset retries, or enable a goal.

## Terminal dashboard

Run `python3 -m devloop dashboard` for an interactive view of the existing runner.
It uses Python's built-in curses support and needs an interactive terminal at least 52 columns wide and 16 rows tall.
Wider terminals show a sidebar with the operating window, model, service state, and token usage.

| Keys | Action |
| --- | --- |
| `1-4`, `h/l`, arrows, Tab | Switch Activity, Changes, Checks, and Details |
| `j/k`, Ctrl-d/Ctrl-u | Scroll by a line or half a page |
| `g/G` | Top of view or follow newest output |
| `[` / `]` | Older or newer execution log |
| `/`, Esc | Filter the current view or clear the filter |
| `p/r` | Pause or resume with the runner's existing checks |
| `?`, `:help` | Show help |
| `q`, `:q` | Close the dashboard without changing execution |

`:pause` and `:resume` also work.
Views refresh automatically without model calls or Ollama probes; the endpoint in Details is configuration, not a health result.
Activity translates structured events into messages and command output, including bounded tails of older logs.
Changes shows local Git status, tracked diffs, and recent commits; Checks shows recorded validation and current feedback.
Pause/resume never bypass a blocked goal or reset the repair budget.
Opening the dashboard does not start the service, and closing it does not pause the loop.
External notifications are not configured.

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
Their original records remain in Git at migration commit `0e52fc7735a48f06da74805f00c3474d5a012d31`; they are historical evidence, not current instructions.
The existing product goal and accepted implementation evidence remain intact.

```sh
python3 -m unittest tests.test_development_runner
./scripts/check.sh
```

The runner tests exercise real Git commits and child processes with a controlled Codex substitute.
They cover continuous progress, window boundaries, live service pause/resume, review routing, failed checks, preserved work, exclusive ownership, and interrupted commit recovery.
