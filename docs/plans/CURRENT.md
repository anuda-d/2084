# Current Development Index

Status: autonomous development is stopped and requires explicit owner activation.

## Runtime Authority

- Authoritative state: [Autonomous Loop State](AUTONOMOUS_LOOP_STATE.json)
- Active autonomous goal: none
- Owner authorization: none
- Scheduler status: paused
- Current orchestrator: none
- Current slice: none
- Recovery action: none

The JSON runtime state is authoritative when this summary and runtime state disagree.
The scheduler must no-op while the state is stopped or unauthorized.

## Migration Note

The previous loop recorded First Consequential Choice Under Conflicting Information as active under standing authorization.
Its [goal](first-consequential-choice/GOAL.md) and [implementation evidence](first-consequential-choice/IMPLEMENTATION_PLAN.md) remain unchanged as historical evidence.
That legacy authorization is deliberately not imported into schema version 2 because the saved automation was paused during migration.
No product work may resume until the owner explicitly selects a goal, authorizes it, and activates the scheduler under the new contract.

## New Loop Shape

One orchestrator generation owns direction for no more than three sequential accepted slices.
Each slice is implemented by one fresh writer that temporarily owns the checkout and is the sole repository modifier for that slice.
The writer may delegate read-only exploration and must obtain a fresh read-only review.
After three accepted slices, the orchestrator performs whole-goal alignment, writes a compact durable handoff, releases ownership, and stops.
A fresh orchestrator starts the next generation from repository evidence and the guarded runtime state.

## Required Read Order

1. `AGENTS.md`;
2. this file;
3. `docs/plans/AUTONOMOUS_LOOP_STATE.json`;
4. `docs/main/DEVELOPMENT_LOOP.md`;
5. the active goal and implementation evidence only when runtime authorization is standing;
6. the latest compact handoff when one exists; and
7. only the implementation and tests relevant to the current frozen slice.

## Safety Boundary

Read-only orientation does not require checkout ownership.
Immediately before the first repository write, acquire or recover the exact durable owner with `python3 scripts/autonomous_loop_lock.py`.
Use `python3 scripts/autonomous_loop_state.py validate` before interpreting lifecycle state.
Use revision and event identifiers for every state transition.
Do not call `list_threads` as part of the no-overlap gate.
Inspect only the exact recorded owner with `read_thread` when recovery is needed.
Unknown, active, or non-terminal ownership blocks recovery.

## Commands

- State validation: `python3 scripts/autonomous_loop_state.py validate`
- State summary: `python3 scripts/autonomous_loop_state.py status`
- Ownership summary: `python3 scripts/autonomous_loop_lock.py status`
- Full check: `./scripts/check.sh`
- Repository state: `git status`
- Diff validation: `git diff --check`

## Stop Condition

The loop is stopped, has no active autonomous goal, and has no standing authorization.
No next slice is selected.
Do not start an orchestrator, writer, relay, or product change without a new explicit owner activation.
