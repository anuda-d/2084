# Current Development Index

Status: no active owner-approved goal as of 2026-08-22. Model-Backed Focal
Character is complete.

## Active Work

- Active goal: none
- Most recently completed goal:
  [Model-Backed Focal Character](model-backed-focal-character/GOAL.md)
- Most recent completion evidence:
  [Implementation Plan](model-backed-focal-character/IMPLEMENTATION_PLAN.md)
- Earlier completed goal: [Agent Understanding](agent-understanding/GOAL.md)
- Earlier completion evidence:
  [Agent Understanding Implementation State](agent-understanding/IMPLEMENTATION_PLAN.md)
- Active work: none; stop after reading this index until the owner approves a
  new goal

## Required Read Order

1. `AGENTS.md`
2. this file
3. if one exists, the owner-approved active goal
4. its shared implementation state
5. relevant implementation and tests located with `rg` for task selection
6. only the specification relevant to the selected task

If this index reports no active goal, stop after reading it. Do not turn a
completed goal, open question, or improvement idea into active work.

Do not preload completed-goal records, historical experiments, the broader
architecture proposal, or unrelated specifications. Read a main architecture
document only when the active specification routes to it or an invariant is
unclear.

## Commands

- Full check: `./scripts/check.sh`
- Normal run: `python3 -m scenarios.first_day --seed 42 --ticks 30`
- Inspector: `python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect`
- Repository state: `git status --short`
- Diff review: `git diff --check`

## Run Contract

- Confirm the no-overlap gate before repository work.
- If alignment is due, review goal evidence without selecting later work.
- Otherwise select one smallest useful gap from the goal and current evidence.
- For implementation, state one criterion, one behavior, and one evidence claim
  before editing.
- Load code just in time; the state file prescribes no task sequence or paths.
- Run focused validation before the full check.
- Use a fresh Sol-high read-only reviewer after implementation and during
  no-code alignment.
- Update `IMPLEMENTATION_PLAN.md` with verified status and evidence only.
- Commit one coherent work unit.
- In continuous Goal mode, begin the next work unit only after the commit and
  from the updated repository state. In a one-shot run, exit after the commit.

## Stop Conditions

- Active project work exists.
- Baseline state is unsafe.
- The task exceeds one fresh context window.
- Owner authority is required.
- No justified task advances the active goal.
- The goal is complete.
