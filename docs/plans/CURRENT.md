# Current Development Index

Status: First Consequential Choice Under Conflicting Information is selected for owner-authorized replacement activation after an exhausted, unaccepted CC-11 slice.

## Runtime Authority

- Authoritative state: [Autonomous Loop State](AUTONOMOUS_LOOP_STATE.json)
- Active autonomous goal: [First Consequential Choice Under Conflicting Information](first-consequential-choice/GOAL.md)
- Owner authorization: standing for the active goal
- Scheduler status: pending activation after the repository activation commit
- Current orchestrator: none
- Current slice: none
- Recovery action: preserve the unaccepted adapter repair for independent validation inside a new frozen slice
- Resolved owner decision: close `cc11-live-day-20260911` as unaccepted after its three-attempt cap and permit a later new bounded CC-11 repair slice without weakening the failed contract

The JSON runtime state is authoritative when this summary and runtime state disagree.
The scheduler remains paused until the replacement activation is committed.
The replacement authorization reactivates only the existing goal and does not itself select a replacement slice.

## Migration Note

The legacy authorization is deliberately not imported by the schema-version-2 migration because the saved automation was paused.
The unchanged legacy goal records remain historical evidence rather than runtime authority.
On 2026-09-11, the owner delegated selection of the next sensible goal and then explicitly instructed continuation after the live Ollama service check.
That instruction selects the unfinished [goal](first-consequential-choice/GOAL.md), grants standing implementation authorization within its existing boundaries, and authorizes activation of the existing scheduler.
The live prerequisite was verified at the owner-provided private Ollama endpoint with the exact required `qwen3:4b-instruct` model before activation.

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

The exhausted CC-11 slice remains closed without acceptance and does not count toward a generation limit.
The owner authorized replacing it with a new bounded CC-11 repair slice rather than weakening its frozen criterion.
The authoritative runtime is ready under standing authorization, the scheduler awaits post-commit activation, and no replacement slice is selected yet.
