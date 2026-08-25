# First Autonomous 24-Hour Living Day Implementation State

Status: active; AD-1, AD-5, and AD-9 are met. AD-2 through AD-4, AD-6 through AD-8, and AD-10 through AD-12 are open.

This is verified shared state for the owner-approved
[goal](GOAL.md). It records completed evidence only; it is not a task backlog or
implementation sequence.

## Run State

- Incomplete run: none
- Last completed run: AD-9 paired deterministic-harness offline proof (2026-08-24)
- Verified implementation runs since alignment: 15
- Alignment due: no

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| AD-1 Simulation-owned day | met | `python3 -m scenarios.autonomous_day --seed 42` runs the successor world offline from declared `Day 0 00:00` through exact `Day 1 00:00`, independently of wall-clock time and the legacy plot checklist. It returns success only when the runtime reaches the complete 1,440-minute boundary. |
| AD-2 Deterministic temporal order | open | Non-negative integer minutes, the chosen causal phases, and stable identities order successor work. One authored supporting action now starts in scheduled-world phase and dynamically registers its later completion; an institutional event dynamically registers a later observation-phase delivery. Focal travel and scheduled-home rest completions now use action-completion ordering before later same-minute decisions; no understanding runtime uses the order yet. |
| AD-3 Decision eligibility | open | The accelerated-day runtime owns explicit eligibility for five documented causes, coalesces pre-release simultaneous causes per actor, dispatches one dedicated handler, and creates no call from an otherwise empty quiet interval. Same-minute causes after decision-phase release are rejected. One actor has at most one pending safe-failure retry chain; it can continue only after consumption. In the successor composition, an explicitly configured Mara callback or injected `MaraHarness` receives one restricted scheduled-wake decision at minute 420; an accessible transit bulletin can later trigger one decision after observation delivery, while an inaccessible bulletin does not add one. A completed model-selected travel action or scheduled-home rest requests one `ACTION_RESULT` decision in the later same-minute decision phase, linked to its append-only completion event; immediate waits, rejections, and safe-failure waits do not do so. Retry provenance remains caller-asserted. Every idle legacy policy is still called every tick. |
| AD-4 Ordinary focal rhythm | open | At the explicit minute-420 home wake, a model-selected `wait` can become a world-owned 60-minute rest. It retains an attempted-action record, completes at minute 480, and can create a later action-result decision; safe-failure waits remain immediate rather than being misrepresented as rest. After a model-selected travel reaches the workplace, Mara's restricted view exposes `work`; a selected work attempt then completes under world authority after 120 minutes and creates a later action-result decision. This provides narrow rest and workplace-obligation opportunities, not a complete rest, obligation, movement, or private-time day rhythm. |
| AD-5 Independently living world | met | Ilan independently starts and completes one authored two-hour workplace action, and the transit authority independently changes objective service state while Mara is inactive. Both are scheduled without focal interaction and retain append-only evidence. This proves authored schedule independence, not supporting policy choice, broad autonomy, or a society simulation. |
| AD-6 Knowledge and consequence | open | The successor transit change grants no knowledge by itself. A distinct observation-phase bulletin at minute 660 links the immutable source event to Mara only at the authored home receiver; workplace and transit-stop locations retain no observation. When the composition is given an explicit Mara callback or injected `MaraHarness`, the accessible bulletin enters its restricted `AgentView` and can therefore enter detached model input; an inaccessible bulletin creates neither a callback nor a decision. Canonical understanding remains unconfigured. |
| AD-7 Bounded model continuity | open | The Ollama boundary enforces 48 KiB input, private records enforce 8 MiB retention, and attempts/results use a recent window of 16 each. The successor runtime enforces exactly 128 dedicated decision-handler invocations for every marked model-bounded actor: call 128 is valid and call 129 is terminal before invocation. An injected successor `MaraHarness` now receives only the composition's restricted `AgentView`; its private records are retained, linked to the resulting action attempt and outcome, and excluded from objective history and normal output. Observations/understanding remain unbounded and older relevance remains unproven. |
| AD-8 Failure behavior | open | Known model failures are explicit in the bounded path. An unexpected legacy step exception creates sanitized terminal evidence. The successor runtime records sanitized handler/dispatch failure evidence and freezes subsequent execution and registration; handler side effects and append-only events before an exception are not rolled back or fully represented by its committed-work trace. Each requested safe-failure retry is delayed 30 minutes, and only one pending retry chain can exist per actor; any work handler can still assert a retry for any actor. The optional successor harness now resolves its failed private record as an immediate safe wait, then requests a source-linked retry through the runtime; the legacy path still retries every tick. |
| AD-9 Offline full-day proof | met | Two equal-seed, equal-configuration deterministic-harness runs reach minute 1,440 and retain equal ordered events, observations, action results, private decision records, summaries, and inspector final-state evidence. The paired proof measures five focal calls, every restricted input, and the peak retained private-record footprint against the approved ceilings. This proves offline deterministic reproduction of one scripted choice sequence, not live-model determinism or the other goal criteria. |
| AD-10 Recorded full-day reproduction | open | Recorded choices from one complete deterministic-harness autonomous-day run now reproduce equal runtime summary, ordered objective events and observations, inspector objective state, and restricted inputs through minute 1,440 without invoking the source client. Altered input or exhausted records cause an explicit `RecordedDecisionError`, preserve terminal runtime failure evidence, and never report day completion. This remains one narrow deterministic composition rather than complete recorded-choice coverage or a live-provider claim. |
| AD-11 Watchability and inspection | open | The successor command presents readable start/end time, compact quiet intervals, Mara's accessible bulletin, and world-confirmed completed Mara activity using fixed focal-safe labels. Equal-time updates retain causal action-completion-before-observation order without raw event details, hidden activity, or private model material. Explicit `--inspect` JSON reconstructs successful runtime work, quiet spans, objective events/state, observations, action results, and independently derived counts; it distinguishes the default unconfigured path from an injected/exercised harness and counts recorded provider failures without exposing private records. Private model-growth measurements are absent, and failed-handler objective tails remain outside the committed-work trace. |
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

### 2026-08-23 — Fourth whole-goal alignment

- Fresh independent Sol-high review compared all AD-1 through AD-12 criteria
  after the model call ceiling and first concrete successor-world composition.
  AD-5 is now met narrowly: Ilan's authored work and the transit authority's
  objective service change are independently scheduled while Mara is inactive.
  AD-1 through AD-4 and AD-6 through AD-12 remain open.
- The review found that `WorldState.tick` was synchronized only after the day
  returned. The runtime now invokes a composition-owned time observer before
  every due handler and at the final boundary; focused tests observe matching
  world and event or delivery minutes at 480, 510, 600, and 660, then minute
  1,440.
- The review corrected two overstatements. Successor terminal failure freezes
  subsequent execution and registration but is not rollback; a failed handler
  may leave objective state or append-only events outside the successful
  committed-work trace. The composition also marks Mara as model-bounded for
  accounting but does not configure or exercise a model policy.
- Focused validation passed ten runtime and composition tests. Full offline
  validation passed 154 repository tests and 63 historical checks; the legacy
  normal and omniscient runs still reached tick 28 with no runtime failure, and
  `git diff --check` passed.
- Fresh independent re-review found no blockers and additionally verified
  same-minute multi-phase synchronization plus sanitized terminal behavior for
  time-observer failure during due work and at the exact end boundary.
- No agenda, eligibility, observation, or budget mechanism warrants removal.
  The alignment counter resets to zero; no future implementation task was
  selected or recorded.

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

### 2026-08-23 — Second whole-goal alignment

- Fresh independent Sol-high review compared all AD-1 through AD-12 criteria
  after the simulated clock and temporal agenda work. Every criterion remains
  open; the isolated primitives do not yet constitute a successor runtime or
  full-day command.
- The review corrected one temporal overstatement. The agenda defines a chosen
  successor phase order; it does not exactly preserve the legacy generic
  broadcast path, which delivers a broadcast during institutional processing
  before same-tick completions. `first_day_v3` does not use that generic path.
- The review also measured the existing safe-failure cadence rather than
  leaving it unspecified: five timeout ticks produced five provider calls,
  five private failure records, and five focal wait attempts. AD-8 therefore
  remains open partly because the current path retries once per tick.
- Full offline validation passed 130 repository tests and 63 historical
  scenario checks. Eleven focused clock and agenda tests and 42 model-policy
  and Ollama boundary tests passed. The scripted regression reached tick 28
  with 150 events, 24 observations, 73 action results, and no runtime failure.
- No mechanism warrants removal. Temporal wording was simplified to state the
  successor order directly and retain the legacy generic-broadcast exception.
  The alignment counter resets to zero; no future implementation task was
  selected or recorded.

### 2026-08-23 — Third whole-goal alignment

- Fresh independent Sol-high review compared all AD-1 through AD-12 criteria
  after the isolated accelerated-day executor and decision-trigger integration.
  Every criterion remains open; there is still no successor agent/world
  composition, offline full-day command, or integrated model path.
- The review corrected one retry overstatement. A single chain produced 49
  decisions at minutes 0, 30, through the exact end at 1,440, but 30 overlapping
  valid wake/retry chains produced 1,441 decisions—one per minute—and still
  completed. Each retry request is delayed 30 minutes; aggregate cadence,
  retry-chain suppression, and the 128-call ceiling are not enforced.
- A world-work handler could also assert a retry for an unrelated actor. This
  is consistent with the recorded caller-asserted provenance limit, not proof
  of integrated failure authority.
- Full offline validation passed 146 repository tests and 63 historical
  checks. Twenty-seven successor clock, agenda, eligibility, and runtime tests
  and 42 model-policy/Ollama boundary tests passed. `first_day_v3` reproduced at
  tick 28 with 150 events, 24 observations, 73 action results, and no runtime
  failure.
- Existing append-only history, Official Record, observation, attempted-action,
  policy privacy, normal/inspector, and legacy scenario boundaries remain
  intact. No mechanism warrants removal. The alignment counter resets to zero;
  no future implementation task was selected or recorded.

## Verified Run Log

### 2026-08-24 — AD-9 paired deterministic-harness offline proof

- Two separate equal-seed, equal-configuration deterministic harnesses now run
  the complete successor day to minute 1,440 with the same selected travel,
  work, return-home, household, and wait sequence. The regression compares
  their ordered objective history, observations, action results, complete
  private records, runtime summaries, and inspector final-state projection.
- The proof measures five focal calls against the 128-call ceiling, every
  retained restricted input against the 48 KiB ceiling, and peak retained
  private-record bytes against the 8 MiB ceiling. It does not make private
  records part of objective history or normal output.
- Focused validation passed the paired regression and all 17 autonomous-day
  world tests. Full offline validation passed 184 repository tests and 63
  historical checks; `git diff --check` passed. The two Solo gates were
  reverified with 2 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found no blockers. It confirmed that the
  scripted client supplies attempted choices only; time, scheduling, action
  resolution, observation delivery, and the measured limits remain world-owned.
- Scope limit: AD-9 is met for the required offline deterministic proof. This
  does not prove deterministic live sampling, complete continuity relevance,
  full failure coverage, or the owner-authorized live day.

### 2026-08-24 — AD-10 recorded autonomous-day reproduction

- Private records from a complete deterministic-harness day now replay through
  the existing recorded-client boundary. The replay reaches the exact minute
  1,440 boundary with the same runtime summary, ordered objective events,
  observations, inspector objective state, and restricted model inputs, while
  making no additional source-client call.
- Altering a recorded restricted input or exhausting the record sequence raises
  an explicit `RecordedDecisionError`; the runtime remains incomplete and
  retains terminal failure evidence rather than reporting a completed day.
- Focused validation passed two replay and failure-path tests. Full offline
  validation passed 183 repository tests and 63 historical checks; `git diff
  --check` passed. The two Solo gates were reverified with 2 met, 0 unmet, and
  0 abandoned.
- Fresh independent Sol-high review found no blockers. It confirmed that replay
  constructs only the recorded-client boundary and that this test does not add
  private decision material to normal output or objective history.
- Scope limit: AD-10 remains open. This proves one deterministic full-day
  recording and its strict failure paths, not coverage of every choice route,
  complete-day recorded-choice interfaces, or deterministic live-model output.

### 2026-08-24 — AD-11 focal-safe normal activity rendering

- Normal autonomous-day output now renders Mara's completed household, rest,
  travel, and workplace activities from world-confirmed action results using
  fixed readable labels. It excludes immediate waits, private decision records,
  raw event identifiers/details, and supporting-character activity.
- Same-minute focal updates retain the runtime's causal order: Mara's action
  completion is shown before an observation delivery at the same simulated
  minute. Quiet-span rendering remains compact and creates no zero-length
  interval between tied updates.
- Focused validation passed 14 autonomous-day world tests; full offline
  validation passed 181 repository tests and 63 historical checks. `git diff
  --check` passed. The two Solo gates were reverified with 2 met, 0 unmet, and
  0 abandoned.
- Fresh independent Sol-high review found and the implementation fixed the
  same-minute ordering issue; closure review found no remaining blocker.
- Scope limit: AD-11 remains open. This improves normal focal-safe watchability
  only; it does not configure a default model path, expose private evidence, or
  replace the inspector's exact causal record.

### 2026-08-24 — AD-4 basic home household opportunity

- At home, Mara's successor-only restricted view offers one parameter-free
  `household` attempted action. World authority completes it after 60 minutes
  with append-only `household_time_completed` evidence, resolves the linked
  private decision record, and requests one source-linked `ACTION_RESULT`
  decision in the later same-minute phase.
- Focused evidence selects household time at minute 420, completes it at minute
  480, and verifies the home-only contract, duration, attempted/completed
  evidence, terminal result, and later decision trigger. The default
  no-harness command remains unchanged.
- The action is intentionally successor-only: legacy restricted model input
  does not advertise it, and direct legacy resolution records a deterministic
  rejection with its source-linked `ActionResult` rather than leaving an
  orphaned attempt.
- Focused validation passed 13 autonomous-day tests and 97 affected
  cross-boundary tests. Full offline validation passed 180 repository tests and
  63 historical checks; `git diff --check` passed. The two Solo gates were
  reverified with 2 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found and corrected the legacy action
  boundary; a final fresh Sol-high closure review found no blockers.
- Scope limit: AD-4 remains open. This adds one basic home/private opportunity
  without prescribing a route, changing the legacy composition, or adding a
  general household, needs, diary-consequence, or employment system.

### 2026-08-24 — AD-4 workplace obligation resolution

- Once a model-selected travel action has placed Mara at the workplace, her
  restricted decision view offers `work` alongside reachable travel and wait.
  A selected work attempt remains append-only objective evidence, completes
  under successor-world authority after 120 minutes, and then requests one
  source-linked `ACTION_RESULT` decision in the later same-minute phase.
- Focused evidence follows travel at minute 420, workplace work at minute 450,
  and `work_completed` at minute 570. It verifies the workplace-only action
  contract, the completed action history, and the later decision trigger.
- Focused validation passed the new regression and all 12 autonomous-day world
  tests. Full offline validation passed 177 repository tests and 63 historical
  checks; the default autonomous-day command reached `Day 1 00:00`, and
  `git diff --check` passed. The two Solo gates were reverified with 2 met,
  0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found no blockers, including on restricted
  input, world-owned resolution, deterministic pending-action handling, and
  private-record isolation.
- Scope limit: AD-4 remains open. This adds one authored workplace opportunity
  after Mara chooses to travel there; it does not prescribe that route, add
  household or private activity, create a general employment system, or
  complete the full ordinary-day rhythm.

### 2026-08-24 — AD-3/AD-8 safe-failure retry cadence

- A failed configured `MaraHarness` decision now resolves to the existing immediate safe wait and, only after that private record and objective result are resolved, requests the runtime's single 30-minute `SAFE_FAILURE_RETRY`. The retry is sourced by the private decision ID and is not exposed in objective history or normal output.
- Focused evidence exercises a timeout at minute 420, one retry at minute 450, and the separate accessible-bulletin decision at minute 660. It proves three total calls rather than per-minute polling, a retry trigger sourced by `model-decision-mara-vale-0420`, and no fabricated `rest_completed` event.
- Focused validation passed the retry regression and all 11 autonomous-day world tests. Full offline validation passed 176 repository tests and 63 historical checks; `git diff --check` passed. The two Solo gates were reverified with 2 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found no blockers. It noted only that the focused test does not separately assert private decision-ID absence from normal or inspector output; the selected runtime behavior does not serialize these records, and this change adds no presentation path.
- Scope limit: AD-8 remains open. This configures only Mara's successor-harness retry cadence; it does not provide retry authority provenance beyond the configured caller, change the legacy per-tick path, prove all provider failure modes through a full-day composition, or establish final live-day behavior.

### 2026-08-24 — AD-3/AD-4 scheduled-home rest completion

- A model-selected `wait` at Mara's explicit minute-420 scheduled home wake
  now becomes a world-owned 60-minute rest. Its append-only attempt remains
  objective evidence; the `rest_completed` result occurs at minute 480 and
  creates one later same-minute `ACTION_RESULT` eligibility item. At that
  minute, independently scheduled world work still precedes rest completion,
  which precedes the resulting decision.
- A safe-failure fallback wait never becomes rest. It completes immediately,
  creates no extra action-result decision, and remains a failed private model
  record rather than a fabricated ordinary activity.
- Focused validation passed the two rest and safe-failure regressions and all
  11 autonomous-day world tests. Full offline validation passed 176 repository
  tests and 63 historical checks; `git diff --check` passed. All three Solo
  gates were reverified with 3 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found and the implementation fixed the
  safe-failure classification issue. A fresh re-review found no code blocker
  and corrected the AD-2 evidence wording to distinguish exercised focal
  completion ordering from still-unexercised understanding ordering.
- Scope limit: AD-3 and AD-4 remain open. This is one configured rest
  opportunity only; it does not establish an obligation, movement, household
  or private-time rhythm, generic rest behavior, a required route, or a
  model-owned failure retry.

### 2026-08-24 — AD-3 travel-completion action-result eligibility

- A model-chosen Mara travel attempt now completes under world authority at
  minute 450 and then creates one same-minute `ACTION_RESULT` eligibility item
  for the later decision phase. Its trigger is linked to the append-only
  `travel_completed` event; the next harness request receives only the updated
  restricted workplace view, not the event log or scheduling authority.
- This work deliberately excludes synchronous waits and rejected choices, which
  resolve during decision handling and cannot safely create another
  same-minute decision. It therefore does not add a quiet-time polling path.
- Focused validation passed the causal trigger test; the full offline check
  passed 175 repository tests and 63 historical checks. All three Solo gates
  were reverified with 3 met, 0 unmet, and 0 abandoned; `git diff --check`
  passed.
- Fresh independent Sol-high review initially requested direct trigger/source
  evidence. The revised test captures the dispatched decision and confirms its
  sole trigger is `ACTION_RESULT` sourced by the minute-450 travel completion;
  the re-review found no remaining blocker.
- Scope limit: AD-3 remains open. This covers only completed travel in the
  configured successor harness and does not add wait or rejection eligibility,
  safe-failure retry authority, full-day focal cadence, or ordinary-day rhythm.

### 2026-08-24 — AD-7/AD-11 omniscient model-growth measurements

- The explicit autonomous-day inspector now reports aggregate-only model-growth
  evidence when a `MaraHarness` is configured: the peak restricted-input byte
  count, retained private-record count, peak retained private-record footprint,
  and their existing ceilings. It does not serialize a private record, model
  input, or provider conversation into this summary. An unconfigured model path
  reports `growth: null` rather than invented zero measurements.
- Retained private-evidence measurements sample the empty collection and every
  accepted record append, linkage replacement, and resolution replacement, so
  the reported peak is not inferred solely from final state. Restricted-input
  peak derives from canonical per-record byte measurements.
- Focused successor-world and CLI validation passed 13 tests. The full offline
  check passed 174 repository tests and 63 historical checks; `git diff --check`
  passed. All four Solo gates were reverified with 4 met, 0 unmet, and 0
  abandoned.
- Fresh independent Sol-high review found no blockers and confirmed aggregate
  privacy, mutation-time peak sampling, deterministic measurements, and
  focal-safe normal output.
- Scope limit: AD-7 and AD-11 remain open. This adds inspector measurement
  evidence only; it does not prove continuity relevance, full-day focal action
  cadence, recorded reproduction, or a live day.

### 2026-08-24 — AD-3/AD-7 Mara harness decision seam

- `build_autonomous_day` now accepts an explicitly injected `MaraHarness` as an alternative to the callback-only seam. At the existing scheduled-wake and access-gated bulletin triggers, the harness receives only Mara's restricted view. Its choice becomes one append-only action attempt, while the successor world owns validation and resolution: wait completes at the current minute, a reachable travel completes 30 simulated minutes later, and other choices are recorded then rejected without scripted focal substitution.
- The harness's private model decision record is retained separately, linked to the action attempt and terminal result, and remains outside objective history and normal output. Inspector metadata accurately identifies a configured/exercised harness and counts its recorded provider failures without exposing the records themselves.
- Focused validation passed nine successor-world tests and four CLI tests. Full offline validation passed 174 repository tests and 63 historical checks; all four Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned. `git diff --check` passed.
- Fresh independent Sol-high review found two blockers: it corrected Mara's restricted affordances to the resolver-supported travel/wait set and added the private-record resolution reserve before any objective or actor-state mutation. A fresh re-review found no remaining blockers.
- Scope limit: AD-3 and AD-7 remain open. This introduces only two resolved successor actions and does not make terminal actions eligible for another choice, integrate safe-failure retries with a model decision, prove full-day continuity relevance, provide recorded full-day reproduction, or configure the default command or a live provider.

### 2026-08-24 — AD-3 scheduled focal wake eligibility

- The successor composition now requests one `SCHEDULED_WAKE` decision for
  Mara at minute 420 only when an explicit decision callback is supplied. The
  runtime dispatches it in the later decision phase with the authoritative
  world clock at minute 420, a restricted home `AgentView`, no delivered
  observations, and no world or institution reference. The existing accessible
  bulletin remains a later, separately observation-gated decision.
- The default no-callback composition still produces zero Mara decisions and
  unchanged focal-safe output; it does not create or disclose the wake.
- Focused validation passed seven successor-world tests and four CLI tests.
  Full offline validation passed 172 repository tests and 63 historical
  checks; all four Solo gates were reverified with 4 met, 0 unmet, and 0
  abandoned. `git diff --check` passed.
- Fresh independent Sol-high review found no blockers. It confirmed the
  decision-phase order, restricted view, inaccessible-bulletin behavior, and
  unchanged default composition.
- Scope limit: AD-3 remains open. This is a callback-only scheduled trigger,
  not a configured model policy, focal attempted-action resolver, safe-failure
  integration, or complete ordinary-day rhythm.

### 2026-08-24 — AD-3/AD-6 access-gated decision callback

- The autonomous-day composition can now receive an explicitly injected Mara
  decision callback. An accessible home transit bulletin first appends its
  source-linked observation, then requests one same-minute
  `OBSERVATION_DELIVERED` decision; the runtime releases that callback in the
  later decision phase. A workplace Mara receives no bulletin, callback, or
  decision count.
- The callback receives only the eligibility evidence and a frozen, Mara-safe
  `AgentView`. Its detached model input contains the delivered bulletin but no
  institution record, event log, world object, or scheduling authority.
- Focused validation passed two access-and-callback boundary tests. Full
  offline validation passed 169 repository tests and 63 historical checks; all
  four Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found no blockers and confirmed the phase
  order, restricted callback authority, inaccessible-path suppression, and
  compatibility of the no-callback command.
- Scope limit: AD-3 and AD-6 remain open. This is a callback/input bridge, not
  a configured model policy, an attempted-action resolver, or canonical
  understanding.

### 2026-08-24 — AD-3/AD-8 safe-failure retry-chain suppression

- The successor eligibility seam now retains at most one pending safe-failure
  retry per actor. A later failure reuses that pending retry rather than
  scheduling an adjacent chain; after the retry is consumed, a later failure
  may start its next 30-minute link. A valid pending retry remains visible even
  when a newer failure is too close to the day boundary to create one itself.
- Focused validation passed 14 eligibility and runtime tests. Full offline
  validation passed 169 repository tests and 63 historical checks; all three
  Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review identified the boundary-ordering case,
  which was fixed and revalidated. A fresh re-review found no blockers and
  confirmed the overlap suppression, boundary preservation, and next-link
  behavior.
- Scope limit: AD-3 and AD-8 remain open. Retry provenance is still asserted
  by callers, no actual focal policy uses the successor eligibility path, and
  this does not alter the legacy per-tick retry path.

### 2026-08-24 — AD-11 focal-safe normal quiet intervals

- Normal autonomous-day output now shows the two intervals without a
  Mara-visible update: `Day 0 00:00` through the accessible bulletin at `Day 0
  11:00`, and from that bulletin through `Day 1 00:00`. The renderer derives
  those intervals only from the declared runtime boundary and the observations
  it already presents; it does not expose the hidden supporting or
  institutional schedule.
- Focused CLI validation passed four tests, including the two interval lines
  and the existing supporting/institutional non-leak assertions. Full offline
  validation passed 158 repository tests and 63 historical checks; all three
  approved gates were reverified with 3 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found no blockers. It confirmed that the
  normal output has no visible boundary at the hidden minute-480, -510, or
  -600 activity, and that this remains a narrow AD-11 slice rather than a
  complete watchability claim.
- Scope limit: AD-11 remains open. Private model-growth measurements and
  reconstruction of partial objective tails after failed handlers are still
  absent.

### 2026-08-23 — AD-11 autonomous-day inspector

- Added explicit `--inspect` mode to the autonomous-day command. It replaces
  focal-safe output with deterministic omniscient JSON containing successful
  runtime work order, five quiet spans, objective history and state, delivered
  observations, action results, and derived evidence counts.
- The inspector reconstructs four work items, three events, one observation,
  and one action result with exact causal identifiers through minute 1,440. It
  states that the model path is unconfigured and unexercised and reports
  provider failure count as unavailable rather than an unsupported zero.
- Focused validation passed four command tests. Full offline validation passed
  158 repository tests and 63 historical checks; all three approved gates were
  reverified with 3 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review initially rejected the unsupported hard-coded
  provider-failure zero. After correction, re-review found no blockers and
  verified cross-process determinism, detached JSON, exact quiet duration,
  causal reconstruction, failure-tail qualification, and unchanged focal-safe
  default output.
- Scope limit: AD-11 remains open. Normal output does not summarize focal-safe
  quiet spans; private model-growth measurements are absent; and partial
  failed-handler objective tails are not reconstructable from committed-work
  evidence.

### 2026-08-23 — AD-1 offline autonomous-day command

- Added the documented offline command
  `python3 -m scenarios.autonomous_day --seed 42`. It runs the successor from
  `Day 0 00:00` through exact `Day 1 00:00` and returns zero only when the
  runtime reports the complete 1,440-minute boundary.
- Normal output contains only readable boundary information, Mara's location,
  and her delivered home transit bulletin. It omits Ilan, objective event kinds,
  stable identifiers, and omniscient runtime work evidence.
- Focused validation passed three module-command, equality, and controlled
  argument-error tests. Full offline validation passed 157 repository tests and
  63 historical checks; all three approved gates were reverified with 3 met, 0
  unmet, and 0 abandoned.
- Fresh independent Sol-high review found no behavioral blockers and verified
  offline and wall-clock independence, cross-process byte equality, incomplete
  exit 1, unexpected-failure non-success, controlled unknown arguments, and no
  normal-output leak. Its initial stale-state findings were corrected before
  commit.
- AD-1 is met. Scope limit: the command has no inspector mode, quiet-span
  presentation, focal decisions, general action resolution, or complete
  ordinary-day claim; AD-6 and AD-11 remain open on those narrower boundaries.

### 2026-08-23 — AD-6 access-gated background consequence

- Added a distinct observation-phase delivery at minute 660 for the transit
  authority's minute-510 service change. The delivery links the immutable source
  event and reports its recorded status rather than rereading later mutable
  institutional state.
- Mara retains the bulletin only while physically at the authored home receiver.
  Moving her to the workplace or transit stop leaves the same three-event
  objective history and reduced service state intact but creates no observation.
  Delivery itself appends no objective event and causes no decision or model
  access.
- Focused validation passed three positive, negative, and equality tests. Full
  offline validation passed 152 repository tests and 63 historical scenario
  checks; all three approved gates were reverified with 3 met, 0 unmet, and 0
  abandoned.
- Fresh independent Sol-high review found no blockers and additionally verified
  both inaccessible locations, immutable source linkage, exact observation
  phase, repeat-run idempotence, and honest terminal failure for a missing
  delivery target.
- Scope limit: AD-6 remains open. The delivered observation does not yet enter
  decision eligibility, model input, canonical understanding, or normal
  presentation. This third implementation unit makes whole-goal alignment due
  before another implementation task is selected.

### 2026-08-23 — AD-5 independent successor-world activity

- Added the first concrete world composition hosted by the accelerated-day
  runtime. An authored schedule makes Ilan attempt ordinary workplace work at
  minute 480 and complete it at minute 600; the district transit authority
  changes objective tram-service state at minute 510 while Mara remains home
  and inactive.
- The action attempt and completion update Ilan's explicit action state and
  append causally linked objective events. The institutional change updates
  objective institutional state and appends its own event without automatically
  delivering anything to Mara. The world clock reaches exactly minute 1,440.
- Equal-seed compositions produce equal ordered events, runtime summaries,
  institutional state, and supporting results. Focused validation passed two
  tests; full offline validation passed 151 repository tests and 63 historical
  scenario checks.
- Fresh independent Sol-high review found no blockers and additionally verified
  exact quiet spans and phase order, repeat-run idempotence, pending-action
  cleanup, zero focal decisions or observations, and an honest terminal failure
  when the authored workplace precondition is violated. All three approved
  gates were reverified: 3 met, 0 unmet, and 0 abandoned.
- Scope limit: AD-5 and the other criteria remain open. The supporting action
  validates only its authored workplace condition; there is no general
  successor action resolver, focal policy, observation delivery, normal
  presenter, or offline command yet.

### 2026-08-23 — AD-7 full-day model decision-call ceiling

- Added explicit model-backed actor configuration to the successor runtime and
  enforced the approved maximum of 128 dedicated decision-handler invocations
  per configured actor. Call 128 remains valid; a would-be call 129 becomes a
  sanitized terminal failure before handler invocation and cannot complete the
  day.
- Runtime summaries now report deterministic decision counts by actor. Every
  configured model actor appears even at zero with its bounded status, while an
  active unmarked supporting actor is reported without silently inheriting
  Mara's ceiling.
- Focused validation passed three exact-boundary and actor-scope tests. Full
  offline validation passed 149 repository tests and 63 historical scenario
  checks; staged and unstaged `git diff --check` passed.
- Fresh independent Sol-high review initially found that zero-call configured
  actors were omitted from the summary. After correction, re-review found no
  blockers and verified two bounded zero-call actors, mixed supporting counts,
  exact 128-call success, pre-handler refusal at 129, and no false completion.
- Scope limit: AD-7 and AD-11 remain open. This counts dedicated runtime
  decision-handler invocations; no successor composition yet configures Mara or
  connects those invocations to the existing model policy/provider boundary.

### 2026-08-23 — AD-3 runtime decision-trigger dispatch

- Connected the explicit eligibility registry to the accelerated-day runtime.
  Valid causes now produce coalesced `EligibleDecision` records for one
  dedicated handler; quiet advancement produces no handler call.
- The restricted handler context can request another documented trigger or one
  safe-failure retry exactly 30 simulated minutes later. Repeated failures may
  therefore form a 30-minute chain through the exact boundary, and no individual
  retry is placed beyond the day. Overlapping chains are not suppressed and can
  still produce aggregate per-minute decisions.
- Preserved the agenda's causal phase invariant: simultaneous causes coalesce
  only before the decision phase is released. A decision handler cannot add a
  same-minute cause to either a pending or already consumed actor record.
- Focused validation passed five decision-runtime tests. Full offline
  validation passed 146 repository tests and 63 historical scenario checks;
  staged and unstaged `git diff --check` passed.
- Fresh independent Sol-high review initially found an actor-order-dependent
  late-merge bypass. After correction, re-review found no blockers, reproduced
  both directions as terminal without admitting the late cause, and verified
  16 focused/relevant tests plus the full suite.
- Scope limit: AD-3 and AD-8 remain open. Trigger provenance is asserted by the
  simulation-owned caller, and no AgentView, existing policy call, attempted
  action, result, or observation delivery is connected yet.

### 2026-08-23 — AD-1/AD-2 accelerated-day agenda runtime

- Added a one-shot executor that dispatches registered work through the
  temporal agenda until exactly start plus 1,440 minutes. Work due at the end
  executes before the agenda closes against further registration.
- Handlers receive only immutable current/end time and validated scheduling
  authority. Dynamically caused later-phase and future work re-enters the same
  ordered agenda; handlers cannot advance time, release work, close the agenda,
  or re-enter the runtime through their context.
- The runtime summary retains exact committed-work order and compact quiet
  spans. An unexpected handler or dispatch exception records only sanitized
  boundary counts and types, makes completion false, and freezes both rerun and
  further registration without claiming rollback.
- Focused validation passed five runtime tests. Full offline validation passed
  141 repository tests and 63 historical scenario checks; staged and unstaged
  `git diff --check` passed.
- Fresh independent Sol-high review initially found and reproduced handler
  over-authority and post-failure mutation. After correction, re-review found
  no blocking defects and passed four adversarial groups, including an
  all-five-phase exact-end chain and both original reproductions.
- Scope limit: AD-1, AD-2, AD-8, and AD-11 remain open. This runtime has no
  agent/world composition, policy call, action resolution, observation path,
  normal presenter, or user command.

### 2026-08-23 — AD-3 explicit decision-trigger eligibility

- Added an isolated successor seam for exactly five decision causes: initial
  activation, terminal action result, delivered observation, scheduled wake,
  and safe-failure retry. Time passage alone creates no eligibility work.
- Multiple causes for one actor at one minute coalesce into one deterministic
  eligibility record. Different minutes retain separate agenda identities, and
  a record can be consumed only once, after release and at its due minute.
- Defined the initial safe-failure cadence as one retry exactly 30 simulated
  minutes later. Stale or future failure instants are rejected, an exact-end
  retry is allowed, and a retry crossing the end boundary is omitted.
- Focused validation passed six eligibility tests. Full offline validation
  passed 136 repository tests and 63 historical scenario checks; staged and
  unstaged `git diff --check` passed.
- Fresh independent Sol-high review and re-review found no blocking defects and
  separately exercised all trigger kinds, actor isolation, stale and future
  failure rejection, exact-boundary retry and consumption, and release timing.
- Scope limit: AD-3 and AD-8 remain open. Trigger provenance is caller-asserted,
  and no successor runtime yet connects deliveries, action results, policy
  calls, waits, or failures to this seam. The legacy path is unchanged.

### 2026-08-23 — AD-2 monotonic equal-time phase dispatch

- Changed the pure agenda to release only the earliest causal phase at a due
  minute, retaining later phases so work caused by a completion or delivery can
  enter the correct place before an already pending decision.
- Once a phase is released for one minute, a new item in that phase or an
  earlier phase is rejected before its stable identity is consumed. Rejected
  identities remain usable for valid future work.
- Focused validation passed seven agenda tests. Full offline validation passed
  130 repository tests and 63 historical scenario checks; staged and unstaged
  `git diff --check` passed.
- Fresh independent Sol-high review found no blocking defects and separately
  exercised multiple minutes, dynamically caused delivery and understanding
  work, backward and same-phase rejection, identity reuse, within-phase order,
  per-minute isolation, and exact-end dispatch.
- Scope limit: AD-2 remains open because no successor runtime executes the
  agenda. Registration closure after reaching the end boundary also remains a
  runner-level decision.

### 2026-08-23 — AD-2 deterministic temporal agenda

- Added one pure temporal agenda that registers uniquely identified work only
  within the remaining simulated day and orders it by authoritative minute,
  explicit causal phase, and stable item identity.
- Equal-time phases use the chosen successor order: scheduled world and
  institutional work, action completions, observation deliveries,
  understanding updates, then decisions. The agenda returns due work without
  executing it or fabricating activity during quiet spans.
- Next-due advancement jumps the day clock directly to pending work or the
  exact end boundary. Duplicate identities, past work, beyond-boundary work,
  and an externally skipped pending instant are rejected without consuming the
  pending item.
- Focused validation passed five agenda tests. Full offline validation passed
  128 repository tests and 63 historical scenario checks; staged and unstaged
  `git diff --check` passed.
- Fresh independent Sol-high review found no blocking defects and separately
  probed multiple distinct instants, future-work retention, exact-boundary
  work, failed-schedule atomicity, and repeated completion advancement.
- Scope limit: AD-2 remains open. The agenda is not wired into a successor
  runtime and does not yet define interleaving for same-minute work created
  while another returned batch executes or when end-boundary registration
  closes.

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
