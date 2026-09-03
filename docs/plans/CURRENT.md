# Current Development Index

Status: no active goal.
First Accelerated-Day Social Thread completed on 2026-09-02.

## Active Work

- Active goal: none
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

- Active goal id: none
- Owner authorization: pending
- Authorization scope: none
- Authorization source: none
- Loop cadence: stopped
- Current run: none
- Incomplete run: none
- Run status: none
- Pending owner decision: none
- Scheduled window: daily 18:00-23:00 America/Toronto
- Fresh-task relay: stopped
- Alignment due: no
- Standing implementation authority: none

## Goal Boundary

No product goal is active.
Do not turn a completed goal, open question, proposal, or improvement idea into
active work.
The owner must approve exactly one new goal and set `Owner authorization:
standing` before implementation can begin.
The same activation change must set the
`autonomous-2084-development-loop` automation to active and verify its saved
2084 project target before scheduled work can begin.

An explicit owner request may authorize one bounded administrative change while
this index has no active product goal.
That request does not activate product implementation, standing authority, or
the scheduler.

## Scheduled Autonomy

The scheduled relay is stopped because no goal has standing authorization.
When a future goal is activated, its repository state and this index must agree
on the active goal id, authorization, current run, incomplete run, run status,
scheduled window, relay status, alignment status, and standing authority.
The activation is incomplete until the existing paused
`autonomous-2084-development-loop` automation is updated to active.

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
They atomically claim the durable checkout lock and no-op when another task owns
it.
The unscoped Codex task listing is not an ownership precondition because it can
hang and cannot reliably classify idle historical tasks.
Do not call `list_threads` as part of the no-overlap gate.
Ownership is never taken over or force-released by another task.

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

Do not preload completed-goal records, historical experiments, the broader
architecture proposal, or unrelated specifications.
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

- Before any subagent spawn or repository change, run
  `python3 scripts/autonomous_loop_lock.py acquire`.
  The command uses `CODEX_THREAD_ID` automatically.
- If the lock is held, inspect only the exact recorded owner with `read_thread`.
  An idle owner that asked for input still owns the checkout.
  Wake the same owner when its exact terminal state permits recovery, then stop
  the recovery task.
- Before every later mutation phase or resumed turn, run
  `python3 scripts/autonomous_loop_lock.py assert-owner`.
- Release ownership at every non-relaying terminal state or immediately before
  creating a relay successor.
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
- Never push, merge, deploy, publish, destructively clean, modify `experiments/`,
  or absorb unrelated user work without explicit direction.

## Commands

- Autonomous-day offline run: `python3 -m scenarios.autonomous_day --seed 42`
- Full check: `./scripts/check.sh`
- Normal run: `python3 -m scenarios.first_day --seed 42 --ticks 30`
- Inspector: `python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect`
- Repository state: `git status --short`
- Diff review: `git diff --check`

## Stop Condition

The repository is at **NO ACTIVE GOAL - LOOP STOPPED**.
The paused automation must not start implementation or create successor tasks.
