# Current Development Index

Status: active.

## Active Work

- Goal: [Agent Understanding](agent-understanding/GOAL.md)
- Shared plan: [Implementation Plan](agent-understanding/IMPLEMENTATION_PLAN.md)
- Active work: the sole task marked `next`, or the required alignment run
- Task specification: the document linked from the active task
- Run boundary: exactly one current task or alignment review
- Model routing: Terra high implements; Sol high reviews and aligns; no Luna
- Incomplete run: none

## Required Read Order

1. `AGENTS.md`
2. this file
3. the active goal
4. the shared implementation plan
5. for implementation, only the specification linked by the active task
6. relevant implementation and tests located with `rg`

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
- Select only the active task; if alignment is due, plan the next batch without
  implementation.
- For implementation, state one criterion, one behavior, and one evidence claim
  before editing.
- Load code just in time; the plan does not prescribe permanent file paths.
- Run focused validation before the full check.
- Use a fresh Sol-high read-only reviewer after implementation and during
  no-code alignment.
- Update `IMPLEMENTATION_PLAN.md` with status and evidence.
- Commit one coherent work unit.
- Exit after the commit; do not start another work unit in this chat.

## Stop Conditions

- Active project work exists.
- Baseline state is unsafe.
- The task exceeds one fresh context window.
- Owner authority is required.
- No justified change advances the active task.
- The goal is complete.
