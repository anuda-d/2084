# Current Development Index

Status: First Accelerated-Day Social Thread is active and owner-approved as of
2026-09-01. Implementation is in progress.

## Active Work

- Active goal:
  [First Accelerated-Day Social Thread](first-accelerated-day-social-thread/GOAL.md)
- Shared implementation state:
  [Implementation Plan](first-accelerated-day-social-thread/IMPLEMENTATION_PLAN.md)
- Most recently completed goal:
  [First Autonomous 24-Hour Living Day](first-autonomous-day/GOAL.md)
- Most recent completion evidence:
  [Implementation Plan](first-autonomous-day/IMPLEMENTATION_PLAN.md)
- Earlier completed goal:
  [Model-Backed Focal Character](model-backed-focal-character/GOAL.md)
- Earlier completion evidence:
  [Implementation Plan](model-backed-focal-character/IMPLEMENTATION_PLAN.md)
- Active work: Continuous Goal mode selects one run-scoped work unit at a time
  from the active goal and verified implementation state, but the app-level
  loop is active only after Goal activation is verified

## Required Read Order

1. this file
2. `AGENTS.md`
3. if one exists, the owner-approved active goal
4. its shared implementation state
5. relevant implementation and tests located with `rg` for task selection
6. only the specification relevant to the selected task

If this index reports no active goal, stop after reading it.
Do not turn a completed goal, open question, or improvement idea into active
work.

Do not preload completed-goal records, historical experiments, the broader
architecture proposal, or unrelated specifications. Read a main architecture
document only when the active specification routes to it or an invariant is
unclear.

## Commands

- Autonomous-day offline run: `python3 -m scenarios.autonomous_day --seed 42`
- Full check: `./scripts/check.sh`
- Normal run: `python3 -m scenarios.first_day --seed 42 --ticks 30`
- Inspector: `python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect`
- Repository state: `git status --short`
- Diff review: `git diff --check`

## Run Contract

- Continuous Goal requires a real app-level Goal; the repository goal does not activate it.
  When the owner explicitly asks to start the continuous implementation loop, call `get_goal` before repository work.
  If it reports no Goal or a completed Goal, call `create_goal` with the owner-approved objective and verifiable stop condition, then call `get_goal` again.
  The `create_goal` objective must state that the same task continues automatically across turns until the verifiable whole-goal stop condition.
  It must not direct continuation to a new agent, task, chat, or handoff.
  It must not release the repository lock between work units.
  Continue only when `get_goal` reports `status: active` and the objective covers the requested work.
  Perform this verification before task listing or lock acquisition.
  If the Goal is paused, blocked, otherwise non-active, or has a different objective, stop at **GOAL MODE NOT ACTIVE** and ask the owner to resume, clear, or resolve it.
  Treat an objective that requests transfer after a work unit as different even when its product scope is unchanged, and do not record that mismatch as repository handoff state.
  For that objective conflict, ask the owner to `clear` the conflicting Goal and start once with the corrected same-task objective; resuming cannot repair its text.
  Never claim Continuous Goal mode from commentary, repository state, or an earlier turn alone.
  Continuous Goal does not use `create_thread`; fresh successor threads belong only to scheduled relay.
- On every automatically continued Goal turn, call `get_goal` before repository work, then assert durable lock ownership.
  A normal Goal turn boundary is not terminal while that app-level Goal remains active.
  If a continued turn observes any non-active status, perform no repository work except releasing a lock it owns, then stop at **GOAL MODE NOT ACTIVE**.
  When the objective is genuinely complete, commit the verified completion state, release the lock, and call `update_goal` with `status: complete`.
- Confirm the no-overlap gate before repository work.
- Inspect returned task activity for visible other active or queued 2084 work,
  then claim durable local ownership before repository work with
  `python3 scripts/autonomous_loop_lock.py acquire --task-id <current-id>`.
  A full task-list page is not itself terminal: recover a held lock only after
  `read_thread` reports its exact owner `idle` or `notLoaded` with a terminal
  `completed`, `failed`, or `interrupted` latest turn, then
  `takeover --expected-task-id <owner-id> --verified-inactive` succeeds. Before
  each later repository-working turn, `assert-owner --task-id <current-id>`
  must still succeed.
- If alignment is due, review goal evidence without selecting later work.
- Otherwise select one smallest useful gap from the goal and current evidence.
- For implementation, state one criterion, one behavior, and one evidence claim
  before editing.
- For implementation, invoke the installed `$unlazy` skill in Solo mode and
  write run-scoped gates for only that selected work unit before editing.
- Load code just in time; the state file prescribes no task sequence or paths.
- Run focused validation before the full check.
- Use a fresh Sol-high read-only reviewer after implementation and during
  no-code alignment.
- Update `IMPLEMENTATION_PLAN.md` with verified status and evidence only.
  Never record app Goal, task, lock, automation, relay, handoff, or chat state there.
- Commit one coherent work unit.
- In continuous Goal mode, begin the next work unit only after the commit and
  from the updated repository state.
- In the current scheduled relay window, each Codex task completes at most one
  work unit. After `TASK COMPLETE` or `ALIGNMENT COMPLETE`, a task finishing
  before 23:00 `America/Toronto` starts exactly one fresh Terra-high task in
  this saved project's local checkout after verifying the exact saved project
  through the project listing, releases its durable local ownership record,
  embeds its own task ID as the authorized handoff-only predecessor, and then
  does no more repository work. If either ID cannot be resolved unambiguously,
  the handoff fails safely without creating a successor and releases its lock.
  After creation, the predecessor waits for one bounded progress snapshot to
  confirm dispatch, never creates a duplicate if that result is unclear, and
  exits. The successor rereads this index from fresh repository state and,
  before any repository work, stops without change if its start time is at or
  after 23:00 `America/Toronto`.
- The current external triggers at 18:00, 19:00, 20:00, 21:00, and 22:00 are
  recovery starts. They make no repository change when a cycle already owns the
  checkout. At or after 23:00, or after any other terminal state, do not create
  a successor. A cycle started before cutoff still finishes and commits its one
  work unit safely. A manual one-shot exits after its commit and never relays.

## Stop Conditions

- Active project work exists, except for the exact handoff-only predecessor ID
  carried by a scheduled relay successor.
- Baseline state is unsafe.
- A scheduled or manual task exceeds one fresh context window.
- Owner authority is required.
- No justified task advances the active goal.
- The goal is complete.
