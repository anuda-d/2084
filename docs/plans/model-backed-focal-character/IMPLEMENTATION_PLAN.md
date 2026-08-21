# Model-Backed Focal Character Implementation State

Status: active shared state; no implementation work unit has been selected.

## Run State

- Incomplete run: none
- Last completed run: MF-4A model attempt resolution authority
- Verified implementation runs since alignment: 1
- Alignment due: no

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| MF-1 Actual character decision | met | MF-1A verifies through the deterministic test client that `ModelFocalPolicy` calls the injected chooser once, converts its schema-valid response directly through the strict parser, and records the resulting `wait` attempt where the unchanged scripted mode selects travel. This proves the offline boundary, not live-model behavior. |
| MF-2 Restricted decision envelope | open | MF-2A verifies that the restricted `AgentView` carries each agent's authored display name and role from agent-owned state without adding objective, institutional-private, inspector-only, or other-agent fields. The complete serialized model envelope remains open. |
| MF-3 Structured action contract | open | MF-3A verifies an exact pure parser that derives the actor from the restricted view, accepts only supported action kinds and immutable structured parameters, and rejects prose, missing or extra fields, actor spoofing, malformed containers, cycles, and unsupported values without touching simulation state. Per-action semantic parameter constraints remain open. |
| MF-4 World-owned consequence | met | MF-4A verifies through committed model-path tests that the unchanged resolver alone schedules valid travel, completes it at the configured tick with linked location mutation and an actor-safe result in the next restricted view, or rejects unreachable travel with no movement and a linked actor-safe reason. The client receives no consequence API. |
| MF-5 Decision continuity | open | None yet. |
| MF-6 Explicit failure | open | None yet. |
| MF-7 Decision evidence and privacy | open | None yet. |
| MF-8 Recorded reproduction | open | None yet. |
| MF-9 Bounded behavioral proof | open | None yet. |
| MF-10 Integration | open | The scripted default and observer boundary remain intact and offline checks pass 70 current and 63 historical tests. A usable documented live entry path and explicit live smoke remain open. |

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

None. MF-4A is verified; the next implementation work unit must be selected
from fresh repository evidence.

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

### 2026-08-20 — Alignment after MF-1A

- Fresh Sol-high whole-goal review found no blocker and reopened no criterion.
- MF-1 remains met through the deterministic-client boundary; this does not
  prove live-model behavior. MF-2A and MF-3A remain proportionate partial
  evidence, and MF-2 through MF-10 remain open.
- No hidden world knowledge, institutional authority, other-agent private
  state, canonical model-created memory, provider framework, credential path,
  or direct consequence authority entered the implementation.
- A future persistent client must not make opaque provider conversation state
  the character's canonical memory.
- `AgentView.valid_actions` still lacks agent-safe parameter constraints, and
  the restricted view does not directly serialize canonical memory traces or
  interpreted claims; MF-2 and MF-3 must remain open.
- No code warrants removal. Keep the single narrow client interface. Do not
  grow the recursive generic parameter validator into a parallel semantic
  schema; consolidate it with the eventual per-action contract instead.
- The review selected no later implementation work. Focused tests passed 3;
  full checks passed 70 current and 63 historical tests; `git diff --check`
  passed; the worktree remained clean at reviewed HEAD `73b23c2`.

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

### MF-3A Exact structured choice parser

- Criterion advanced: MF-3 Structured action contract remains open.
- Observed behavior: `structured_choice_to_attempt()` accepts one exact choice
  object, derives the actor from the supplied restricted view, and returns the
  existing immutable `ActionAttempt` without consulting or mutating the world.
- Boundary evidence: Focused tests cover a valid detached choice plus prose,
  missing or extra fields, actor spoofing, unsupported kinds, malformed or
  cyclic parameter containers, unsupported values, nested non-string keys, and
  empty required text; invalid choices leave inspector state and events equal.
- Validation: Two focused tests passed; `./scripts/check.sh` passed 69 current
  and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high re-review found no blockers, independently
  reproduced the full checks, and probed direct and mixed cycles, 3,000-level
  nesting, and nested detachment successfully. It confirmed MF-3 remains open
  because semantic constraints for each action kind are not implemented yet.

### MF-1A Injected model policy decision

- Criterion met: MF-1 Actual character decision.
- Observed behavior: `ModelFocalPolicy` calls its injected decision client once
  and passes the response directly through the strict parser; no scripted focal
  chooser runs inside that path.
- Behavioral evidence: From equal seed-42 opening world state, the legacy mode
  attempts travel while the deterministic model client selects `wait`; the
  objective log records Mara's `wait` and its supplied decision reason, then
  normal resolution produces `wait_completed`.
- Validation: Three focused tests passed; `./scripts/check.sh` passed 70 current
  and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, reproduced the
  checks and runtime behavior, and confirmed the engine still supplies the
  restricted view and owns attempt recording and resolution. This evidence
  proves the fake-client boundary, not live-provider behavior or failure paths.

### MF-4A Model attempt resolution authority

- Criterion met: MF-4 World-owned consequence.
- Observed behavior: Model-selected valid travel stays pending until the
  unchanged resolver completes it at tick 3; unreachable model-selected travel
  is rejected immediately and leaves Mara at home.
- Boundary evidence: Committed tests verify attempt/outcome causal linkage,
  configured timing, location mutation only on completion, skipped client calls
  while pending, and completed or rejected actor-safe results in the restricted
  view. The decision client exposes only `choose(view)` and no consequence API.
- Validation: Five focused tests passed; `./scripts/check.sh` passed 72 current
  and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, reproduced the
  full checks and model-path probes, confirmed complete result linkage and
  tick-2 immobility independently, and approved MF-4 as met without production
  changes to the resolver.
