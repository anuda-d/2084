# Model-Backed Focal Character Implementation State

Status: active shared state; no implementation work unit has been selected.

## Run State

- Incomplete run: none
- Last completed run: MF-2A restricted focal identity projection
- Verified implementation runs since alignment: 1
- Alignment due: no

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| MF-1 Actual character decision | open | None yet. |
| MF-2 Restricted decision envelope | open | MF-2A verifies that the restricted `AgentView` carries each agent's authored display name and role from agent-owned state without adding objective, institutional-private, inspector-only, or other-agent fields. The complete serialized model envelope remains open. |
| MF-3 Structured action contract | open | None yet. |
| MF-4 World-owned consequence | open | None yet. |
| MF-5 Decision continuity | open | None yet. |
| MF-6 Explicit failure | open | None yet. |
| MF-7 Decision evidence and privacy | open | None yet. |
| MF-8 Recorded reproduction | open | None yet. |
| MF-9 Bounded behavioral proof | open | None yet. |
| MF-10 Integration | open | None yet. |

This table records only verified goal evidence. It is not a task backlog or an
implementation sequence.

## Per-Run Selection

Each fresh implementation run:

1. reads the active goal and this shared state;
2. confirms the repository and no-overlap gate are safe;
3. locates only enough current implementation and tests to select the smallest
   useful gap for one open criterion;
4. records one bounded work unit under `Current Run` and `Incomplete run` before
   changing implementation;
5. states the intended behavior and focused evidence;
6. implements, validates, obtains fresh independent review, records verified
   evidence, commits, and exits or begins the next continuous-goal work unit
   from fresh repository state.

Do not select or record future work. Criteria order does not prescribe task
order. If no honest work unit advances the goal, make no implementation change.

## Current Run

None. MF-2A is verified; the next work unit must be selected from fresh
repository evidence.

## Completion Rules

- Clear `Current Run` and `Incomplete run` only after validation, independent
  review, evidence recording, and commit preparation are complete.
- Mark a criterion met only when proportionate verified evidence satisfies it.
- Keep live model calls opt-in; automated repository validation stays offline.
- Never record or commit credentials, authorization headers, or secret-bearing
  environment values.
- A deterministic fake proves the boundary, not live-model behavior.
- A recorded decision proves reproducibility of resulting world behavior, not
  deterministic model sampling.
- If credentials or an owner decision block a live adapter or smoke test, leave
  the affected criterion open and record the exact blocker.

## Alignment

After several verified work units, or whenever implementation evidence changes
the apparent boundary, perform a fresh whole-goal alignment review. Alignment
may close evidence gaps or recommend removal and simplification, but it must not
select a future task.

## Verified Run Log

### MF-2A Restricted focal identity projection

- Criterion advanced: MF-2 Restricted decision envelope remains open.
- Observed behavior: `Simulation.agent_view()` exposes the requested agent's
  authored display name and role alongside the existing restricted state.
- Boundary evidence: The focused policy-view test asserts Mara's identity,
  retains the explicit forbidden-field checks, and confirms policy selection
  does not mutate objective or event state.
- Validation: Focused test passed; `./scripts/check.sh` passed 67 current and 63
  historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high re-review found no blocking issue and
  independently reproduced the focused test, full checks, and diff check. It
  confirmed the fields come from the requested agent's own state and add no
  hidden authority; supporting-agent identity has only a generic-path runtime
  check, so MF-2 remains open.
