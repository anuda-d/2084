# First Autonomous 24-Hour Living Day Implementation State

Status: active; AD-1 through AD-12 are open.

This is verified shared state for the owner-approved
[goal](GOAL.md). It records completed evidence only; it is not a task backlog or
implementation sequence.

## Run State

- Incomplete run: none
- Last completed run: AD-7 retained private-record size ceiling (2026-08-23)
- Verified implementation runs since alignment: 3
- Alignment due: yes

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| AD-1 Simulation-owned day | open | No explicit clock, exact 24-hour successor composition, or day-boundary completion exists. |
| AD-2 Deterministic temporal order | open | The existing tick order is deterministic for `first_day_v3`, but no full-day time representation, equal-time contract, or quiet-time advancement has been verified. |
| AD-3 Decision eligibility | open | Every idle policy is currently called every tick, and immediate waits create repeated attempts. |
| AD-4 Ordinary focal rhythm | open | The existing 28-tick authored route does not provide a complete rest, obligation, movement, and private-time day rhythm. |
| AD-5 Independently living world | open | The current supporting policies complete one bounded interaction and then wait; no full-day independent activity is verified. |
| AD-6 Knowledge and consequence | open | Existing observation boundaries are verified only in the bounded scenario, not for an independently advancing full day. |
| AD-7 Bounded model continuity | open | The exact UTF-8 dynamic request size is measured in every private decision record, and the Ollama adapter permits 48 KiB exactly but converts any larger input into explicit safe-failure evidence before transport. Prior attempts and terminal results use an explicit recent-window projection capped at 16 entries each with total and omitted counts. Retained private decision records now use canonical UTF-8 measurement, an enforced 8 MiB ceiling, and inspector-only current and peak sizes. Delivered observations and canonical understanding remain unbounded in the fresh request, and the full-day call-count ceiling is not yet verified. |
| AD-8 Failure behavior | open | Known model failures are explicit in the bounded path, but retry cadence, unexpected runtime failure, and false full-day completion are not covered. |
| AD-9 Offline full-day proof | open | No deterministic 24-hour soak, equality evidence, final-state comparison, or long-run measurement exists. |
| AD-10 Recorded full-day reproduction | open | Recorded decisions reproduce the 28-tick scenario only; no complete-day reproduction exists. |
| AD-11 Watchability and inspection | open | Current output renders every tick and has no compact quiet-span or full-day progress/measurement summary. |
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

## Verified Run Log

### 2026-08-23 — AD-7 retained private-record size ceiling

- Added one canonical compact sorted JSON serializer and exact UTF-8 byte
  measurement for the complete inspector-only decision-record collection.
  Exactly 8 MiB is accepted; a larger candidate raises a typed error containing
  only the attempted and maximum byte counts and does not replace retained
  evidence.
- The engine records current and peak retained bytes, preflights new records
  with a conservative bound derived from the actual action and authored rule
  material, and preflights pending completions against the exact prospective
  resolved record before world mutation. The omniscient inspector reports the
  current, peak, and ceiling; objective history and normal output do not.
- Focused validation passed 23 model-policy tests, including exact-limit and
  one-byte overflow, pending-to-resolved growth, atomic collection replacement,
  a 5,000-byte authored rule-string adversary, and an exact-limit pending travel
  that cannot partially complete or duplicate.
- Full offline validation passed 118 repository tests and 63 historical
  scenario checks; `git diff --check` passed.
- Fresh independent Sol-high review initially found two partial-state overflow
  paths. After fixes, repeated read-only review reproduced both adversarial
  cases and found no remaining blocking issue.
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
