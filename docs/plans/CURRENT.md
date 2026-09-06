# Current Development Index

Status: First Consequential Choice Under Conflicting Information is active under standing scheduled authorization.
Owner-approved on 2026-09-06.

## Active Work

- Goal: [First Consequential Choice Under Conflicting Information](first-consequential-choice/GOAL.md)
- Shared implementation state: [Implementation State](first-consequential-choice/IMPLEMENTATION_PLAN.md)
- Active work: none selected
- Most recently completed goal:
  [First Accelerated-Day Social Thread](first-accelerated-day-social-thread/GOAL.md)
- Most recent completion evidence:
  [Implementation Plan](first-accelerated-day-social-thread/IMPLEMENTATION_PLAN.md)
- Earlier completed goal:
  [First Autonomous 24-Hour Living Day](first-autonomous-day/GOAL.md)
- Earlier completion evidence:
  [Implementation Plan](first-autonomous-day/IMPLEMENTATION_PLAN.md)
- Earlier completed goal:
  [Model-Backed Focal Character](model-backed-focal-character/GOAL.md)
- Earlier completion evidence:
  [Implementation Plan](model-backed-focal-character/IMPLEMENTATION_PLAN.md)

## Run State Snapshot

- Active goal id: first-consequential-choice
- Owner authorization: standing
- Authorization scope: active goal
- Authorization source: owner
- Loop cadence: scheduled autonomous relay
- Current run: none
- Incomplete run: none
- Run status: awaiting scheduled fresh task
- Pending owner decision: none
- Scheduled window: daily 18:00-23:00 America/Toronto
- Fresh-task relay: active
- Alignment due: no
- Standing implementation authority: active

## Goal Boundary

Exactly one product goal is active: First Consequential Choice Under Conflicting Information.
Standing owner authorization covers only the linked goal's outcome, invariants, scope, and completion criteria.
Do not turn a completed goal, open question, proposal, or improvement idea into additional active work.
The owner must approve any replacement or expansion of the goal.
This activation selects no implementation unit and does not change the development-loop architecture.

## Scheduled Autonomy

The linked goal has standing scheduled authorization under the existing development-loop contract.
Its implementation state and this index must agree on the active goal id, authorization, current run, incomplete run, run status, scheduled window, relay status, alignment status, and standing authority.
Scheduled work may begin only when the existing `autonomous-2084-development-loop` automation is verified active and targets the saved local 2084 project at `/Users/anuda/Desktop/2084`.

During an authorized window, each fresh task owns at most one bounded work unit.
Before selecting that unit and again before relay, inspect the exact
`autonomous-2084-development-loop` automation and stop unless its status is
active.
After a clean accepted commit before 23:00, that task writes the required
temporary handoff and may create one fresh successor task in the same saved
local project.
At or after 23:00, it finishes an already-started unit safely, writes the
handoff, and does not create a successor.

Hourly scheduled starts are recovery opportunities.
They may perform read-only orientation without the durable checkout lock.
They atomically claim it immediately before the first repository write and
no-op when another active task owns it.
The unscoped Codex task listing is not an ownership precondition because it can
hang and cannot reliably classify idle historical tasks.
Do not call `list_threads` as part of the no-overlap gate.
A recorded owner may be replaced only through the guarded stale-lock recovery
procedure after its exact terminal latest turn is verified.

## Required Read Order

1. `AGENTS.md`;
2. this file;
3. the active goal when one exists;
4. its shared implementation state;
5. the latest temporary handoff when one exists;
6. current time and durable checkout ownership;
7. only enough relevant implementation and tests to select or resume one unit;
8. only the specification relevant to that unit.

If this index reports no active goal, stop after reading it unless the owner
explicitly requested a bounded administrative change.

Do not preload completed-goal records, the broader architecture proposal, or
unrelated specifications.
Read a main architecture document only when the active specification routes to
it or an invariant is unclear.

## Fresh-Task Boundary

One implementation task owns at most one work unit.
Every terminal unit state writes `2084-<active-goal-id>-handoff.md` in the
operating system temporary directory and records `No next unit selected`.
The current task never selects a second unit.
When relay is allowed, it creates a fresh task whose first action is to read
authoritative repository state and select or resume exactly one unit.

## Run Contract

- Read-only work does not require checkout ownership.
- Immediately before the first repository write, run
  `python3 scripts/autonomous_loop_lock.py acquire`.
  The command uses `CODEX_THREAD_ID` automatically.
- If the lock is held, inspect only the exact recorded owner with `read_thread`.
  An idle owner that asked for input still owns the checkout.
  If its latest turn is verified as `completed`, `failed`, or `interrupted`, use
  `recover --expected-task-id <owner-id> --expected-claim-token <token>
  --verified-terminal-state <state>`.
  Any owner mismatch or active, non-terminal, unreadable, or unknown state fails
  closed.
- Assert ownership after any resumed turn and immediately before commit by
  running
  `python3 scripts/autonomous_loop_lock.py assert-owner`.
- Release ownership at completion, at every other non-relaying terminal state,
  or immediately before creating a relay successor.
- Select or resume only one smallest useful goal gap.
  Record the same value under `Current run` and `Incomplete run` before editing.
- If `Alignment due: yes`, select only whole-goal alignment and do not select an
  implementation unit.
- State one criterion, intended result, and evidence claim.
- Use one to three read-only `gpt-5.6-terra` high-reasoning explorers before
  implementation.
  The orchestrator is the sole writer.
- Run focused validation before `./scripts/check.sh`.
- Record candidate evidence before a fresh read-only `gpt-5.6-sol`
  high-reasoning review.
- Resolve every blocker.
  After a material correction, repeat validation and use a new fresh reviewer.
- Update implementation state with verified facts only.
  Never record a future task queue.
- Commit one coherent work unit.
- Write the compact redacted temporary handoff with `No next unit selected`.
- Before 23:00, a clean authorized scheduled task may assert and release its
  lock only after verifying that the exact automation is still active, enter
  handoff-only state, create exactly one fresh Terra-high successor in this
  saved local project, wait once briefly to confirm dispatch, and stop.
- At or after 23:00, after any other terminal state, or while no goal has
  standing authorization, do not create a successor.
- Never push, merge, deploy, publish, destructively clean, or absorb unrelated
  user work without explicit direction.

## Commands

- Autonomous-day offline run: `python3 -m scenarios.autonomous_day --seed 42`
- Full check: `./scripts/check.sh`
- Normal run: `python3 -m scenarios.first_day --seed 42 --ticks 30`
- Inspector: `python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect`
- Repository state: `git status --short`
- Diff review: `git diff --check`

## Stop Condition

The repository is awaiting a scheduled fresh task for the sole active goal.
No next unit selected.
Stop without implementation or relay when authorization is paused, the exact automation is not active, state conflicts, or the development-loop contract requires an owner decision.
When the goal is complete, synchronize completed state, pause the existing automation, release ownership, and stop without selecting another goal.
