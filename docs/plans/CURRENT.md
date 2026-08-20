# Current Development Index

Status: active.

## Active Work

- Goal: [Agent Understanding](agent-understanding/GOAL.md)
- Shared state: [Implementation State](agent-understanding/IMPLEMENTATION_PLAN.md)
- Active work: select one smallest useful goal gap, or run required alignment
- Task specification: selected just in time after the goal gap is identified
- Work-unit boundary: exactly one selected task or alignment review at a time
- Loop mode: an active owner-started Goal continues with the next work unit
  after each commit; scheduled and manual one-shot runs exit after one unit
- Model routing: Terra high orchestrates and implements; Sol high reviews and
  aligns; no Luna

## Required Read Order

1. `AGENTS.md`
2. this file
3. the active goal
4. the shared implementation state
5. relevant implementation and tests located with `rg` for task selection
6. only the specification relevant to the selected task

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
