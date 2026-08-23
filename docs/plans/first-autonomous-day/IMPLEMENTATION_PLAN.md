# First Autonomous 24-Hour Living Day Implementation State

Status: active; AD-1 through AD-12 are open.

This is verified shared state for the owner-approved
[goal](GOAL.md). It records completed evidence only; it is not a task backlog or
implementation sequence.

## Run State

- Incomplete run: none
- Last completed run: AD-1/AD-2 authoritative simulated-day clock primitive (2026-08-23)
- Verified implementation runs since alignment: 1
- Alignment due: no

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| AD-1 Simulation-owned day | open | An isolated `SimulatedDayClock` now owns an explicit start, current time, and exact start-plus-1,440-minute boundary with readable day/time projection. It is not wired into a successor composition or offline full-day command. |
| AD-2 Deterministic temporal order | open | Non-negative integer simulated minutes now define total time ordering, and the clock accepts equal/forward movement while rejecting backward/beyond-boundary advancement. The existing tick order remains deterministic for successful `first_day_v3` runs, and a failed advancement is terminal with a named last committed snapshot. No full-day event ordering or quiet-time advancement is verified. |
| AD-3 Decision eligibility | open | Every idle policy is currently called every tick, and immediate waits create repeated attempts. |
| AD-4 Ordinary focal rhythm | open | The existing 28-tick authored route does not provide a complete rest, obligation, movement, and private-time day rhythm. |
| AD-5 Independently living world | open | A coworker and institution act independently in the bounded scenario, but the supporting policies complete one bounded interaction and then wait; no sustained full-day activity while Mara is inactive is verified. |
| AD-6 Knowledge and consequence | open | Existing observation boundaries are verified only in the bounded scenario, not for an independently advancing full day. |
| AD-7 Bounded model continuity | open | The exact UTF-8 dynamic request size is measured in every private decision record, and the Ollama adapter permits 48 KiB exactly but converts any larger input into explicit safe-failure evidence before transport. Prior attempts and terminal results use an explicit recent-window projection capped at 16 entries each with total and omitted counts. Retained private decision records use canonical UTF-8 measurement, an enforced 8 MiB ceiling, and inspector-only current and peak sizes. The recent window plus omission counts does not yet prove preservation of every behaviorally relevant older result. Delivered observations and canonical understanding remain unbounded in the fresh request, and the full-day call-count ceiling is not verified. |
| AD-8 Failure behavior | open | Known model failures are explicit in the bounded path. An unexpected `Simulation.step()` exception now creates sanitized inspector-only evidence naming the failed tick and last committed snapshot, makes completion false, and prevents any retry from mutating the partial append-only tail. Safe-failure retry cadence and false-completion behavior in a full-day runner are not covered. |
| AD-9 Offline full-day proof | open | No deterministic 24-hour soak, equality evidence, final-state comparison, or long-run measurement exists. |
| AD-10 Recorded full-day reproduction | open | Recorded decisions reproduce the 28-tick scenario only; no complete-day reproduction exists. |
| AD-11 Watchability and inspection | open | Inspector-only evidence now includes restricted-input bytes, current and peak private-record bytes, and sanitized runtime-failure boundaries. Current normal output still renders every tick and has no readable full-day clock, compact quiet spans, or complete progress/measurement summary. |
| AD-12 Integration and live day | open | Existing regressions pass and the bounded live adapter worked previously, but no owner-authorized full-day live run exists. |

## Per-Run Selection

Each fresh implementation work unit:

1. reads the active goal and this shared state;
2. confirms the repository and no-overlap gate are safe;
3. locates only enough implementation and tests to select the smallest useful
   gap for one open criterion;
4. invokes the actual `$unlazy` skill in Solo mode and writes gates only for
   that selected work unit before editing;
5. records the same bounded work unit under `Current Run` and `Incomplete run`;
6. states the intended behavior and focused evidence;
7. implements the complete bounded change;
8. runs and re-verifies the approved focused gates, `./scripts/check.sh`, and
   `git diff --check`;
9. obtains fresh independent read-only Sol-high review, resolves blocking
   findings, and re-verifies affected gates;
10. records verified evidence here, commits one coherent change, and exits or
    begins the next Continuous Goal work unit from fresh repository state.

Do not select or record future work. Criteria order does not prescribe task
order. If no honest work unit advances the goal, make no implementation change.

Read-only alignment and no-overlap terminal runs do not create an `unlazy`
ledger because they do not implement a work unit.

## Current Run

None. The last selected work unit is complete.

## Completion Rules

- Clear `Current Run` and `Incomplete run` only after validation, independent
  review, evidence recording, and commit preparation are complete.
- Mark a criterion met only when proportionate verified evidence satisfies its
  full boundary.
- Treat `unlazy` gate evidence as work-unit proof, not as a substitute for this
  shared goal-level state.
- Do not weaken the model-call, input-size, or private-record ceilings without
  owner approval.
- Keep routine validation offline and free of credentials or live provider
  requirements.
- A deterministic fake proves the runtime boundary, not live-model behavior.
- Recorded choices prove reproduction of resulting world behavior, not
  deterministic live sampling.
- The final live run remains explicitly owner-authorized. If the private Ollama
  endpoint or exact model is unavailable, leave AD-12 open and record the owner
  blocker rather than changing providers or silently using scripted Mara.
- If the selected change would require checkpointing, a daemon, a general needs
  system, model-backed supporting characters, or another out-of-scope system,
  stop for owner review.

## Alignment

After several verified work units, or whenever implementation evidence changes
the apparent boundary, perform a fresh whole-goal alignment review. A fresh
Sol-high read-only reviewer compares the goal, verified evidence, implementation,
tests, and retained boundaries. Resolve blocking findings and record removal or
simplification recommendations.

Alignment may close evidence gaps but must not select a future task. Reset the
implementation-run counter after recording the reviewed state.

### 2026-08-23 — First whole-goal alignment

- Fresh independent Sol-high review compared all AD-1 through AD-12 criteria
  with implementation and tests. Every criterion remains open; the goal remains
  coherent, owner-authorized, and within its existing scope.
- The review confirmed the three AD-7 mechanisms and their privacy boundaries,
  but corrected two overstatements: a recent-history window does not by itself
  prove relevance preservation, and private-record overflow was initially safe
  only for Mara's target mutation rather than the complete failed advancement.
- `Simulation.step()` now records a sanitized terminal failure boundary with
  the failed tick, last committed snapshot, and evidence counts. Partial
  append-only failed-tick evidence remains inspectable, `is_complete` is false,
  and every retry fails before mutation. This is terminal failure evidence, not
  rollback or restart.
- Re-review reproduced new-record and pending-completion overflow, an arbitrary
  private exception marker, complete-scenario and tick-limit preconditions, and
  retry refusal with no remaining blocking finding or leak.
- Focused validation passed 40 model-policy and adapter tests. Full offline
  validation passed 119 repository tests and 63 historical scenario checks;
  `git diff --check` passed.
- No mechanism was removed or expanded. The alignment counter resets to zero;
  no future implementation task was selected or recorded.

## Verified Run Log

### 2026-08-23 — AD-1/AD-2 authoritative simulated-day clock primitive

- Added one wall-clock-independent `SimulatedTime` whose non-negative integer
  minute value is the sole ordering source and whose readable `Day N HH:MM`
  form is only a projection.
- Added a `SimulatedDayClock` with explicit start, current, and exact
  start-plus-1,440-minute end. Equal-time and forward advancement through the
  boundary are valid; backward and beyond-boundary changes are rejected before
  mutation.
- Focused validation passed four boundary tests covering conversion, total
  order, non-midnight rollover, exact completion, invalid values, and failed
  advancement. Full offline validation passed 123 repository tests and 63
  historical scenario checks; `git diff --check` passed.
- Fresh independent Sol-high review found no blocking issues and separately
  exercised five days of conversions, detached serialization, boundary
  mutation safety, and absence of wall-clock dependencies.
- Scope limit: AD-1 and AD-2 remain open. The primitive is deliberately not
  connected to `Simulation.step()`, an event scheduler, quiet-time advancement,
  a successor composition, or a runnable full-day completion boundary.

### 2026-08-23 — AD-7 retained private-record size ceiling

- Added one canonical compact sorted JSON serializer and exact UTF-8 byte
  measurement for the complete inspector-only decision-record collection.
  Exactly 8 MiB is accepted; a larger candidate raises a typed error containing
  only the attempted and maximum byte counts and does not replace retained
  evidence.
- The engine records current and peak retained bytes, preflights new records
  with a conservative bound derived from the actual action and authored rule
  material, and preflights pending completions against the exact prospective
  resolved record before the focal mutation. The omniscient inspector reports
  the current, peak, and ceiling; objective history and normal output do not.
- Focused validation passed 23 model-policy tests, including exact-limit and
  one-byte overflow, pending-to-resolved growth, atomic collection replacement,
  a 5,000-byte authored rule-string adversary, and an exact-limit pending travel
  that cannot partially complete or duplicate.
- Full offline validation passed 118 repository tests and 63 historical
  scenario checks; `git diff --check` passed.
- Work-unit review initially found and resolved two focal partial-state overflow
  paths. Later whole-goal alignment found that earlier same-tick supporting or
  institutional evidence could still form a partial tail; terminal runtime
  failure evidence and retry refusal now make the last committed snapshot
  explicit without rewriting that append-only evidence.
- Scope limit: AD-7 remains open. Delivered observations and source-linked
  understanding still lack a bounded fresh-request projection, and the
  complete-day 128-call ceiling has not been exercised.

### 2026-08-23 — AD-7 bounded decision-history continuity projection

- Replaced full-lifetime prior attempts and terminal results in each fresh Mara
  request with a deterministic recent window capped at 16 entries per
  collection. Projection metadata reports the kind, limits, lifetime totals,
  and omitted counts instead of silently hiding older evidence.
- The latest attempt remains explicit, retained attempts and results preserve
  their causal order, and current state, delivered evidence, canonical
  understanding, and world resolution remain unchanged.
- Focused validation passed 20 model-policy tests, including exact-window
  retention, visible omissions, fixed collection cardinality after 96 lifetime
  entries, later completed and rejected outcome use, privacy, and replay.
- Full offline validation passed 115 repository tests and 63 historical
  scenario checks; `git diff --check` passed.
- Fresh independent Sol-high review found no blocking issues and independently
  confirmed the bounded cardinality claim, restricted-view privacy, canonical
  state preservation, and equal recorded world-history reproduction.
- Scope limit: AD-7 remains open. Delivered observations and source-linked
  understanding still lack a bounded fresh-request projection, and retained
  full-day private decision records have no verified 8 MiB ceiling.

### 2026-08-23 — AD-7 restricted-input size boundary

- Added one canonical serializer and UTF-8 byte measurement for the dynamic
  restricted decision-state JSON actually embedded in the Ollama prompt.
- The Ollama adapter accepts an input of exactly 49,152 bytes and refuses any
  larger input before transport. `ModelFocalPolicy` turns that refusal into the
  existing safe wait while recording `restricted_input_too_large`, the failure
  type, and the independently recomputable input size in private evidence.
- Focused validation passed 34 model-policy and Ollama adapter tests, including
  the exact boundary, one-byte overflow, multibyte measurement, unchanged normal
  selection, and zero transport calls for oversized input.
- Full offline validation passed 113 repository tests and 63 historical
  scenario checks; `git diff --check` passed.
- Fresh independent Sol-high review found no blocking issues and separately
  confirmed exact measurement, pre-transport refusal, privacy, and equal replayed
  world history for an oversized-input safe failure.
- Scope limit: AD-7 remains open. This work enforces one approved ceiling but
  does not bound continuity selection or complete-day private-record retention.
