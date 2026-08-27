# First Autonomous 24-Hour Living Day Implementation State

Status: active; AD-1 through AD-11 are met. AD-12 is open.

This is verified shared state for the owner-approved
[goal](GOAL.md). It records completed evidence only; it is not a task backlog or
implementation sequence.

## Run State

- Incomplete run: none
- Last completed run: AD-12 exact-boundary completion regression (2026-08-27)
- Verified implementation runs since alignment: 3
- Alignment due: yes

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| AD-1 Simulation-owned day | met | `python3 -m scenarios.autonomous_day --seed 42` runs the successor world offline from declared `Day 0 00:00` through exact `Day 1 00:00`, independently of wall-clock time and the legacy plot checklist. It returns success only when the runtime reaches the complete 1,440-minute boundary. |
| AD-2 Deterministic temporal order | met | Non-negative integer minutes, stable identities, and an explicit phase order deterministically dispatch actions, scheduled world work, completions, deliveries, understanding updates, and decisions. Tests cover equal-time ordering, dynamic registration into a later same-minute phase, and quiet-time advancement to the exact boundary. This is the successor ordering rule; the legacy generic broadcast path remains a separate regression. |
| AD-3 Decision eligibility | met | The successor runtime owns five explicit eligibility causes, coalesces simultaneous pre-release causes per actor, and does not call Mara during an empty quiet interval. Its Mara seam is reached only by a scheduled wake, delivered observation, completed action result, or consumed safe-failure retry as configured; retries are actor-bound, delayed 30 minutes, and limited to one pending chain. Legacy idle policies remain outside this successor proof. |
| AD-4 Ordinary focal rhythm | met | Model-selected choices give Mara world-owned opportunities for a 60-minute rest, travel, 120-minute workplace work, and 60-minute household activity. Each is an attempted action resolved by the world, with no required dramatic route or scripted focal substitution. This establishes the goal's basic ordinary rhythm, not a general needs or employment system. |
| AD-5 Independently living world | met | Ilan independently starts and completes one authored two-hour workplace action, and the transit authority independently changes objective service state while Mara is inactive. Both are scheduled without focal interaction and retain append-only evidence. This proves authored schedule independence, not supporting policy choice, broad autonomy, or a society simulation. |
| AD-6 Knowledge and consequence | met | The objective transit change grants Mara no knowledge itself. Only the authored home bulletin delivers its source-linked consequence; that delivery creates canonical understanding before an optional restricted decision view. Inaccessible locations produce no delivery, understanding, callback, or model input. This proves one concrete access path, not general inference or conflict handling. |
| AD-7 Bounded model continuity | met | The Ollama request remains capped at 48 KiB, retained private records at 8 MiB, and marked actor decision handling at exactly 128 invocations. Recent 16-entry history is supplemented by the latest attempt and latest completed/rejected result per finite kind. The autonomous-day world can additionally retain up to eight typed requirements that freeze one exact actor-safe attempt/result pair, its source identities, the canonical consequence it explains, and its selected-decision clearing lifecycle. Missing, substituted, mismatched, duplicate, or over-cap sources fail before a provider call. A scenario-owned classification table covers exactly the four accepted successor kinds: travel is explained by canonical location/reachability, wait/rest has no persistent consequence, rejection changes no canonical state, and the first work or household completion retains its fulfilled-obligation pair through failures until a selected decision receives it; voluntary repeats add nothing. Two equal complete days retain equal bounded inputs and finish with no unresolved requirements. Source-linked belief, trace, stance, diary, and observation closure remains bounded and fail-closed without hidden-world or model-authored relevance. |
| AD-8 Failure behavior | met | The exact harness boundary handles timeout, unavailable, malformed, and invalid-choice failures as explicit safe waits without scripted focal fallback. The successor limits each actor to one authority-bound, 30-minute retry chain and rejects stale or forged requests. Sanitized terminal runtime evidence stops execution and the command returns nonzero with focal-safe incomplete status, including at the exact end time. This is terminal failure evidence, not rollback; legacy per-tick policy cadence remains outside the successor proof. |
| AD-9 Offline full-day proof | met | Two equal-seed, equal-configuration deterministic-harness runs reach minute 1,440 and retain equal ordered events, observations, action results, private decision records, summaries, and inspector final-state evidence. The paired proof measures five focal calls, every restricted input, and the peak retained private-record footprint against the approved ceilings. This proves offline deterministic reproduction of one scripted choice sequence, not live-model determinism or the other goal criteria. |
| AD-10 Recorded full-day reproduction | met | Complete deterministic-harness days, including one timeout and retry, replay equal summaries, ordered objective history, results, inspector state, and restricted inputs through minute 1,440 without a source-client call. A private HMAC-sealed archive binds every retained record to a caller-held verification key; a self-consistent selected-record edit fails before replay can apply it. This detects modification while that key remains trusted; it is not a provenance claim against a party that controls the key or a claim of live-model determinism. |
| AD-11 Watchability and inspection | met | The successor command presents readable start/end time, compact quiet intervals, Mara's accessible bulletin, and world-confirmed completed activity with fixed focal-safe labels. The inspector reconstructs committed runtime work, objective history/state, observations, action results in append-only objective event order across actors, source-linked understanding transitions, ordered consumed decision-trigger provenance, and the exact objective tail of an uncommitted failed dispatch through a pre-dispatch checkpoint plus safe temporal ordering metadata. Each committed event, observation, action result, and understanding transition links to the exact successful runtime dispatch sequence and causal phase that produced it; uncommitted failure-tail artifacts remain explicitly unlinked. Its ordered sanitized model-decision status sequence is privacy-safe, and `provider_failure_count` excludes a `restricted_input_too_large` rejection that the Ollama adapter raises before transport, preserving the provider-call boundary required by this criterion. |
| AD-12 Integration and live day | open | Existing regressions pass and one owner-authorized exact-model live attempt produced 19 selected decisions with zero provider failures, but an unnecessary decision dispatched at the closed minute-1,440 boundary after the final action completion and made the audited verdict fail. The retained failed bundle is anchored below; no successful owner-authorized live day exists yet. |

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

None.

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

### 2026-08-27 - AD-12 exact-boundary completion regression

- Decision eligibility now uses the half-open `[start, end)` interval. A cause
  delivered at minute 1,440 creates no new decision, and a safe-failure retry
  landing at or beyond that instant is omitted. The general agenda still
  commits authored scheduled work and action completions exactly at the end.
- A deterministic model-backed reproduction repeated selected 60-minute
  household actions through the final boundary. Before the fix it reproduced
  the live `ValueError` twice in 0.1 seconds; after the fix the final result
  commits at minute 1,440, the runtime completes, and no boundary model request
  or private decision record exists.
- A provider-free local replay of the first 18 retained live choices reached
  the corrected exact boundary with equal objective state, executed work, and
  committed event, observation, result, and understanding histories. The
  failed audit bundle remains unchanged and retains its unnecessary nineteenth
  boundary decision as historical evidence.
- Solo gates were verified with 5 met, 0 unmet, and 0 abandoned. Eighty-one
  focused tests, 232 current tests, 63 historical tests, and whitespace
  validation passed. A fresh independent Sol-high review found no blocker in
  code, API typing, tests, architecture, or the failed-live evidence record.
- Scope limit: AD-12 remains open. The one authorized live attempt failed and
  has not been retried; another provider-backed execution requires explicit
  owner authorization.

### 2026-08-27 - AD-12 first owner-authorized live audit attempt

- One exact `qwen3:4b-instruct` execution used the validated Ollama adapter and
  retained an immutable private audit bundle outside the repository. Its
  manifest SHA-256 is
  `08f2001b38640fc396822d52bd869ffbab3f74b737bee33c3978ede31acbbc86`.
- The source remained unchanged during execution. Exact model identity,
  adapter provenance, public-view privacy, both growth ceilings, and decision
  count checks passed. All 19 provider calls returned selected decisions and
  `provider_failure_count` was zero.
- The final action completion committed at minute 1,440, then its result
  incorrectly created one more decision at the closed boundary. That decision
  selected an action whose consequence would exceed the day, producing a
  sanitized terminal `ValueError`, one uncommitted objective tail, incomplete
  causal dispatch evidence, and a failed recorded-replay comparison.
- The audit verifier reports a structurally intact bundle with `passed: false`.
  AD-12 remains open, and this attempt must not be relabeled as a completed live
  day or silently retried.

### 2026-08-27 - AD-12 single-run live audit bundle

- The owner-authorized command can now reserve one new private directory before
  provider use and write a focal-safe transcript, sanitized inspector,
  canonical private decisions, measured verdict, artifact hashes, and a
  provider-free replay comparison from exactly one live execution.
- The live preflight pins the exact `qwen3:4b-instruct` tag, digest, family,
  parameter size, and quantization through `/api/tags`. The manifest records
  equal pre-run and post-run source revision, status, and tracked-diff evidence,
  and it rejects injected clients and recorded replays as live provenance.
- The writer keeps the reserved directory descriptor open, binds every private
  exclusive write to its device and inode, and fails path replacement. The
  verifier rejects linked files, extra or missing files, unsafe permissions,
  malformed or recursive JSON, invalid provenance and verdict schemas, and
  artifact size or hash mismatches without following symlinks.
- Solo gates were verified with 4 met, 0 unmet, and 0 abandoned. Twenty-two
  focused tests, 231 current tests, 63 historical tests, and whitespace
  validation passed. A fresh independent Sol-high review found no remaining
  blocker after adversarial filesystem, provenance, source-change, model,
  replay, and negative-seed cases were resolved.
- Scope limit: AD-12 remains open. This work makes the one live run auditable;
  it does not claim the live run has occurred or that a locally stored bundle
  alone is an external authenticity proof.

### 2026-08-27 - AD-12 explicit autonomous-day Ollama CLI

- The successor command now keeps its no-model offline default while exposing
  one explicit live selection that requires an external private origin and the
  exact `qwen3:4b-instruct` model. It constructs the existing `MaraHarness` and
  changes no runtime scheduling, world validation, resolution, knowledge, or
  presentation authority.
- Missing paired configuration, live arguments in offline mode, a wrong model,
  and an invalid origin fail as controlled command errors before provider use.
  A fake client through the public entry point completes the full day within
  the model-call and growth ceilings; normal and inspector output retain no
  endpoint or configuration identity.
- Solo gates were verified with 4 met, 0 unmet, and 0 abandoned. Ten focused
  CLI tests, 219 current tests, 63 historical tests, and whitespace validation
  passed. A fresh independent Sol-high read-only review found no blocker.
- Scope limit: AD-12 remains open. This proves the live command composition
  offline; it does not claim that the owner-authorized live full day occurred
  or that a zero exit status alone distinguishes selected decisions from safe
  provider failures.

### 2026-08-26 — AD-7 explicit action continuity completion

- World-owned continuity requirements replace the earlier raw result-ID
  markers. Each bounded row freezes the exact actor-safe attempt and result,
  source identities, explained canonical obligation transition, and
  `through_selected_decision` lifecycle. The generic model projection verifies
  the whole pair and refuses a provider call for a missing, substituted,
  rejected, mismatched, duplicate, or over-cap source.
- The autonomous-day composition owns the meanings rather than the generic
  policy. Its independently declared four-kind resolver vocabulary has an
  exhaustive classification: travel persists through current location and
  reachability, wait/rest has no lasting consequence, and only the first work
  or household fulfillment creates a temporary exact-pair requirement. A
  failure retains that row for retry; a selected decision clears only the rows
  in the view it received while the obligation remains fulfilled.
- Focused tests force the exact pair outside ordinary windows, exercise forged
  same-kind attempts, forged completed results, rejected and duplicate source
  identities, a valid nine-row over-cap boundary, both obligation lifecycles,
  voluntary repeats, and classification-set equality. Two equal deterministic
  complete days retain equal bounded evidence and end with no unresolved row.
  The complete offline check passes 213 current and 63 historical tests, and
  whitespace validation is clean.
- Two independent Sol-high reviews found no remaining blocker after exact
  attempt/result snapshots, registration identity checks, and the
  scenario-owned exhaustive classification were added. This closes AD-7 only;
  AD-12 remains open for the separately owner-authorized live Ollama day.

### 2026-08-26 — AD-7 bounded obligation-result relevance lifecycle

- The successor snapshots the world-owned fulfillment-result marker IDs placed
  in a restricted Mara view. A failed model decision retains those IDs for its
  delayed retry; the first `selected` decision consumes only the snapshot it
  received. The changed obligation state remains canonical after that marker is
  cleared, and no private policy state can author or clear it.
- Focused deterministic work and household sequences prove the first
  fulfillment result is explicitly included in the following request, while a
  repeated voluntary action does not create or preserve a marker. The timeout
  sequence proves both the failed request and its retry report exactly one
  requested and included explicit relevant result before the successful retry
  clears it.
- Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned: five focused
  lifecycle tests, the complete offline repository check, and whitespace
  validation all passed. A fresh Sol-high reviewer found the first retry test
  could pass through the ordinary recent-history window; after explicit-marker
  assertions corrected that gap, a second fresh Sol-high review found no
  blocker.
- Scope limit: AD-7 remains open. This gives two authored obligation outcomes a
  bounded, inspectable lifecycle; it does not establish semantic relevance or
  clearing for older attempts, other results, or general future state changes.

### 2026-08-26 — AD-11 pre-transport provider-call provenance

- `ModelFocalPolicy` now records `RestrictedInputTooLargeError` as a safe
  pre-transport failure (`provider_call_attempted: false`). The Ollama adapter
  rejects the restricted decision input before its transport's `post_json`, so
  the retained status now names the actual boundary rather than treating a
  local adapter rejection as provider work.
- Focused policy coverage verifies the retained false flag. A full configured
  autonomous day uses a transport sentinel that fails if touched; it reaches
  the exact end boundary, retains sanitized oversized-input failures, and its
  inspector reports zero provider failures. Existing recorded replay coverage
  preserves the false marker without a transport call.
- Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned: the focused
  policy and successor tests, the complete offline repository check, and
  whitespace validation. A fresh independent Sol-high review found no
  blocker; the small follow-up test hardening was reverified and received a
  second fresh Sol-high closure review with no blocker.
- AD-11 is met. This corrects model-path provenance; it does not close AD-7's
  semantic relevance gap or authorize the owner-required live day for AD-12.

### 2026-08-26 — Tenth whole-goal alignment

- A fresh independent Sol-high read-only review and the main alignment review
  compared AD-1 through AD-12 with the active goal, the successor composition,
  recent explicit-result continuity changes, focused coverage, normal output,
  and omniscient inspector evidence. AD-1 through AD-6 and AD-8 through AD-10
  remain met within their recorded narrow limits. AD-7, AD-11, and AD-12 are
  open.
- The recent work and household completion markers are bounded, world-owned,
  and private-state safe, but AD-7 remains open: they do not establish a general
  relevance or clearing lifecycle for older unmarked behaviorally relevant
  attempts and results. Do not treat more latest-by-kind retention heuristics
  as a substitute for such a lifecycle.
- AD-11 reopens. `OllamaDecisionClient` rejects an oversized restricted input
  before attempting transport, while `ModelFocalPolicy` currently records that
  failure as provider-called; the inspector consequently counts it as a
  provider failure. The current aggregate is not an honest provider-call
  measure. This alignment records the blocker without selecting or implementing
  its repair.
- AD-12 remains open: the autonomous-day CLI remains offline-only, and this
  loop authorization is not owner authorization for the required exact-model
  live day. No alternate provider or scripted fallback is authorized.
- Fresh main validation passed 210 current and 63 historical offline tests;
  normal and inspector seed-42 runs both reached exact `Day 1 00:00`; and
  `git diff --check` and the worktree were clean. The independent review found
  no hidden-knowledge grant, private-state leak, impossible authority, scope
  expansion, or removal candidate. No future implementation task is selected.

### 2026-08-26 — AD-7 household result relevance

- The successor now treats the first completed authored household-time action
  as a canonical consequence: it removes the fulfilled `household time`
  obligation and appends that exact world-created household-result ID to Mara's
  bounded relevance closure before the resulting decision is eligible. A later
  physically valid household action does not append a marker because it changes
  no obligation.
- Focused successor-world coverage proves the obligation update, exact result
  identity, next restricted-input inclusion, and the repeated-household guard.
  Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned: focused
  coverage, the default autonomous-day boundary, the complete offline
  repository check, and whitespace validation all passed.
- A fresh independent Sol-high read-only review found no blocker in canonical
  state, bounded growth, hidden knowledge, model authorship, or the repeated
  marker guard.
- Scope limit: AD-7 remains open. This adds one concrete world-owned result
  relevance lifecycle; it does not establish a general semantic relevance or
  clearing policy, preserve every older behaviorally relevant action attempt,
  or authorize the required live day.

### 2026-08-26 — AD-7 workplace result relevance

- The successor now treats the first completed authored workplace shift as a
  canonical consequence: it removes the fulfilled `workplace shift` obligation
  and appends that exact world-created work-result ID to Mara's bounded
  relevance closure before the resulting decision is eligible. A later
  physically valid voluntary work action does not append a marker because it
  changes no obligation.
- Focused successor-world coverage proves the obligation update, exact result
  identity, next restricted-input inclusion, and the repeated-work guard. Solo
  gates were reverified with 3 met, 0 unmet, and 0 abandoned. The offline check
  passed 208 current and 63 historical tests; `git diff --check` passed; the
  default autonomous-day command again reached exact `Day 1 00:00`.
- The first fresh Sol-high review found that repeated work could exhaust the
  relevance closure without changing canonical state. The guard and regression
  resolved it, all gates were reverified, and a fresh Sol-high closure review
  found no blocker.
- Scope limit: AD-7 remains open. This proves one concrete world-owned result
  relevance lifecycle; it does not establish a general semantic relevance or
  clearing policy, preserve every older behaviorally relevant action attempt,
  or authorize the required live day.

### 2026-08-26 — AD-7 explicit relevant action-result continuity

- `AgentState` now owns an optional ordered closure of action-result IDs that
  are explicitly relevant to current canonical state. Both generic simulation
  views and the successor-day Mara view copy this closure; model choices cannot
  author it. The decision-history projection retains up to eight distinct
  marked actor-local results alongside its existing windows, preserving causal
  order.
- An unknown, malformed, or over-cap marker makes the decision-history
  projection incomplete. `ModelFocalPolicy` uses the existing explicit safe
  continuity failure before a provider call rather than silently omitting a
  required result. Recorded replay still compares the complete restricted
  input, including the projection metadata.
- Focused tests prove an old marked `work` result survives while an unmarked
  old same-kind result remains omitted, the fail-closed provider boundary, and
  propagation through the successor Mara view. Solo gates were reverified with
  4 met, 0 unmet, and 0 abandoned. `./scripts/check.sh` passed 206 current and
  63 historical offline tests; `git diff --check` passed.
- A fresh independent Sol-high read-only review found no blocker in bounded
  growth, hidden knowledge, model authorship, stale-marker failure, replay, or
  deterministic compatibility.
- Scope limit: AD-7 remains open. The ordinary-day composition does not yet
  create or clear a real action-result relevance marker, and the mechanism does
  not preserve older action attempts. This is a bounded result-continuity seam,
  not proof that every behaviorally relevant historical fact is represented.

### 2026-08-26 — Ninth whole-goal alignment

- A fresh independent Sol-high read-only review and the main alignment review
  compared AD-1 through AD-12 with the active goal, the successor composition,
  focused coverage, the normal observer output, and omniscient inspector
  evidence. AD-1 through AD-6 and AD-8 through AD-10 remain met within their
  recorded narrow limits.
- AD-11 is now met narrowly. The normal command shows readable simulated time,
  compact quiet spans, and focal-safe confirmed activity. The inspector joins
  ordered runtime work, objective artifacts, causal dispatch provenance,
  sanitized model-decision status, provider-call failures, and growth measures
  without exposing restricted decision material. A seed-42 inspector run
  confirms the causal sequence and exact `Day 1 00:00` boundary.
- AD-7 remains open: the finite decision-history projection still omits older
  same-kind attempts or results without an explicit canonical relevance marker.
  Do not extend latest-by-kind retention heuristics as if that closed the
  semantic gap. AD-12 remains open pending the owner-authorized full-day live
  run with the exact required model; no alternate provider or scripted fallback
  is authorized.
- Fresh validation passed 202 current and 63 historical offline tests,
  `python3 -m scenarios.autonomous_day --seed 42` through the exact boundary,
  and `git diff --check` with a clean worktree. No privacy leak, hidden
  knowledge grant, impossible authority, scope expansion, or removal candidate
  was found. No future implementation task is selected.

### 2026-08-26 — AD-11 committed model-decision dispatch links

- Every configured Mara decision-status entry in the omniscient inspector now
  carries a detached dispatch sequence and named causal phase only after the
  runtime commits its matching decision work. The link is keyed internally by
  the private record identity but exposes neither that identity nor any
  restricted input, response, attempted-action payload, configuration identity,
  or exception detail.
- A forced exception after a retained private decision record proves that the
  inspector reports its dispatch as `null`; it does not falsely describe the
  failed decision work as committed. A deterministic timeout/retry day proves
  every committed status link exactly matches ordered
  `decision_eligibility` work and the `decision` phase.
- Solo gates were met with 3 met, 0 unmet, and 0 abandoned: the focused status
  sequence regression, the autonomous-day world suite, and the complete
  offline check with whitespace validation. A fresh independent Sol-high
  read-only review found no blocker, including for mutable returned data,
  privacy, or failure-boundary handling.
- Scope limit: AD-11 remains open. This makes model-decision invocation
  provenance reconstructable alongside objective artifact provenance; it does
  not complete the full watchability and inspection criterion, resolve the
  explicit AD-7 continuity gap, or authorize the owner-required live day.

### 2026-08-26 — AD-11 committed inspector-dispatch linkage

- The accelerated-day runtime now invokes an optional observer only after it
  records successful work and any consumed-decision evidence. If that observer
  itself fails, the runtime stops with the work counted as committed and no
  false failed-dispatch marker.
- The successor uses that boundary to attach only a runtime dispatch sequence
  and named causal phase to each committed event, observation, action result,
  and understanding transition. The inspector leaves artifacts from the exact
  objective tail of a failed dispatch unlinked, preserving their distinct
  uncommitted status and not exposing private work identity or exception text.
- Focused validation passed 27 autonomous-day world tests and 9 runtime tests.
  The complete offline repository check and `git diff --check` passed. The Solo
  gates were reverified after the review fix with 3 met, 0 unmet, and 0
  abandoned.
- A fresh Sol-high reviewer initially found that the observer was called before
  the runtime committed the dispatch. The callback moved after commitment, a
  failure-boundary regression was added, and the reviewer rechecked the final
  change with no remaining findings. The reviewer also verified each seed-42
  inspector artifact links to an existing runtime dispatch with the same phase.
- Scope limit: AD-11 remains open. This makes committed causal provenance
  explicit for the inspector; it does not complete all normal watchability or
  inspection evidence, the open AD-7 continuity gap, or the owner-required
  live-day run.

### 2026-08-26 — AD-11 explicit normal-output causal tie ordering

- Same-minute focal updates now sort explicitly by the successor's existing
  causal phases—action completion before observation delivery—and then by the
  append-only objective event or observation order within that phase. The
  renderer derives those phase ranks from `TemporalPhase`; it does not expose
  phase values, event IDs, private decision reasons, or supporting activity.
- Focused coverage puts an observation before a completion in its input and
  gives it the lower source-order value, proving that causal phase rather than
  incidental stable-sort input order produces the completion-first result. An
  end-to-end deterministic day separately keeps Mara's 11:00 household result
  before her accessible transit bulletin.
- Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned: focused
  ordering coverage, the complete offline repository check, and whitespace
  validation. A fresh Sol-high read-only closure review found no blockers. The
  normal offline command still reaches the exact `Day 1 00:00` boundary with
  the same focal-safe labels.
- Scope limit: AD-11 remains open. This makes one presentation tie explicit;
  it does not close the full watchability and inspection criterion, the
  documented AD-7 continuity gap, or the owner-required live-day run.

### 2026-08-26 — AD-11 sanitized model-decision inspector sequence

- The omniscient inspector now emits an ordered `decision_status_sequence` for
  a configured Mara harness. Every entry carries only its decision tick,
  selected-or-failed status, safe failure kind, whether the restricted decision
  client was reached, and world-owned validation and resolution status/timing.
  It deliberately omits restricted input, structured response, attempted-action
  payload, configuration identity, authorship identity, and exception detail.
- Focused coverage exercises a client-reached timeout followed by selected
  decisions and a pre-client continuity-projection failure. It proves the
  sequence is chronological, has the exact sanitized field set, distinguishes
  the two failure boundaries, and does not itself contain private response or
  exception text. The unconfigured offline inspector continues to report no
  model sequence.
- Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned: focused
  sequence coverage, the complete offline repository check, and whitespace
  validation. A fresh Sol-high read-only review found no blocking issue. The
  full check passed 199 current and 63 historical tests; the normal offline
  command reached the exact `Day 1 00:00` boundary.
- Scope limit: AD-11 remains open. This closes the missing ordered sanitized
  decision-status evidence; it does not make the inspector focal-safe, prove
  all watchability requirements, close the documented AD-7 continuity gap, or
  authorize the owner-required live day.

### 2026-08-26 — Eighth whole-goal alignment

- A fresh independent Sol-high read-only review and the main alignment review
  compared AD-1 through AD-12 with the active goal, current successor runtime,
  focal-policy boundary, focused tests, and offline validation. AD-1 through
  AD-6 and AD-8 through AD-10 remain met within their recorded limits. AD-7,
  AD-11, and AD-12 remain open.
- The review found one concrete AD-11 blocker: `provider_failure_count` treats
  a `restricted_input_too_large` safe failure as a provider failure even though
  the Ollama adapter rejects that input before transport. The marker is set at
  the model-policy boundary and is therefore not yet an honest provider-call
  aggregate. AD-11 was already open, so this records a correction to its
  evidence rather than changing any criterion status or selecting a fix.
- AD-11 also remains incomplete because its inspector reports aggregates, not
  an ordered sanitized model-decision status sequence. AD-7 remains open for
  the documented older same-kind relevance gap, and AD-12 remains blocked on
  the owner-authorized exact-model live run.
- No privacy leak, hidden-knowledge grant, impossible authority, scope
  expansion, or runtime mechanism warranting removal was found. The architecture
  overview still overstates completion by listing only the continuity and live
  limits while omitting open AD-11; this is recorded drift, not a documentation
  repair selected by this alignment.
- Validation passed the full offline check with 198 current and 63 historical
  tests, the default autonomous-day command through exact `Day 1 00:00`, and
  `git diff --check`; the worktree was clean. The independent review separately
  passed 102 focused successor/model tests and reached the same exact boundary.
  The implementation-run counter resets to zero; no future work is selected or
  recorded.

### 2026-08-26 — AD-11 chronological inspector action results

- Inspector action results now follow their append-only outcome-event order
  across actors instead of the previous actor grouping. This makes equal-time
  ordering inherit the objective log's already-recorded causal order without
  mutating that log or introducing new world state.
- A focused deterministic-harness regression produces interleaved Mara and
  Ilan outcomes and proves the inspector reports Mara, Mara, Ilan, Mara in
  outcome-event order. Normal focal-safe rendering remains unchanged.
- Solo gates passed with 3 met, 0 unmet, and 0 abandoned: the focused inspector
  regression, the complete offline repository check, and whitespace validation.
  A fresh Sol-high read-only review found no blocking issue.
- Scope limit: AD-11 remains open. This closes one causal-order presentation
  gap; it does not claim complete watchability evidence or authorize the
  owner-required live run.

### 2026-08-26 — AD-7 same-kind result continuity

- Restricted decision history now retains the newest completed and newest
  rejected result for each finite supported action kind after the recent
  16-result window. The explicit two-status-per-kind rule is bounded and keeps
  causal order; an older duplicate of either terminal status remains omitted.
- A focused regression displaces two completed and two rejected `work` results
  behind later `wait` results. It proves the newer completed and rejected work
  results survive, both older duplicates remain omitted, and the declared
  finite result bound still holds. This preserves only supplied Mara history;
  it grants no hidden state, changes no objective history, and does not infer
  a general relevance rule.
- The Solo gates were reverified after the independent review corrected the
  duplicate-rejection coverage: focused regression, complete offline
  repository check, and whitespace validation. A fresh Sol-high closure review
  found no blocker.
- Scope limit: AD-7 remains open. This covers one explicit terminal-outcome
  distinction, not every older same-kind attempt or outcome that could matter.

### 2026-08-26 — AD-11 provider-failure aggregate

- Private model-decision records now retain whether the restricted decision
  client was reached. The inspector's `provider_failure_count` counts only
  failed records with that marker; it excludes a
  `continuity_projection_incomplete` safe failure that is stopped before any
  client call, while still reporting it in `decision_status_counts`.
- Focused coverage proves a timeout after a client call counts once and that a
  complete deterministic pre-client failure/replay sequence makes no client
  call and reports zero provider failures. The marker remains private evidence:
  it appears in neither objective history nor normal focal-safe output.
- The three Solo gates were reverified after the replay coverage addition: the
  focused aggregate regression, the complete offline repository check, and
  whitespace validation. A fresh independent Sol-high review found no
  blockers; its replay-coverage observation was incorporated before the final
  revalidation.
- Scope limit: AD-11 remains open. This makes one required aggregate honest;
  it does not by itself prove the complete watchability and inspection
  criterion or authorize the owner-required live day.

### 2026-08-25 — Seventh whole-goal alignment

- A fresh independent Sol-high read-only review and the main alignment review
  compared AD-1 through AD-12 against the goal, current successor
  implementation, focused tests, and full offline validation. AD-1 through
  AD-6, AD-8, AD-9, and AD-10 remain met within their recorded limits; AD-7
  and AD-12 remain open for their stated continuity and owner-authorized-live
  evidence gaps.
- The review reopens AD-11. The inspector's `provider_failure_count` counts
  every failed retained decision record, including a
  `continuity_projection_incomplete` failure that is explicitly stopped before
  any provider call. The current metric is therefore a model-decision failure
  aggregate, not the required provider-failure aggregate. No implementation
  task is selected by this state-only alignment record.
- AD-10 remains met narrowly. Full-day replay covers equal summaries,
  objective history/state, observations, results, restricted inputs, and the
  selected timeout/retry failure fields without a source-provider call; the
  caller-held HMAC seal rejects a self-consistent selected-record edit. Replay
  does not prove byte-for-byte equality of every retained private decision
  record because its configuration identity differs, and this record makes no
  such claim.
- Validation in this review passed 62 focused successor/model tests, the full
  offline check with 196 current and 63 historical tests, the default
  autonomous-day command through exact `Day 1 00:00`, and `git diff --check`.
  The worktree was clean. No privacy leak, hidden-knowledge grant, scope
  expansion, architecture-document drift, or mechanism that warrants removal
  was found. The alignment counter resets to zero; no future work is selected
  or recorded.

### 2026-08-25 — AD-7 latest-action-attempt continuity

- The restricted decision history now retains its recent 16 attempts and also
  the latest attempt for each supported action kind that has fallen outside
  that window. Retained attempts preserve their original causal order, and the
  total cannot exceed the recent window plus the finite supported-kind count.
- A focused regression uses two displaced valid `work` attempts followed by
  later `wait` attempts. It proves only the newer work attempt survives,
  confirms older displaced waits remain omitted, and checks the declared bound.
  This does not infer an outcome, deliver knowledge, or add objective history.
- Three Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned: the
  focused continuity regression, the full offline check, and whitespace
  validation. The first fresh Sol-high review found the latest-only test gap;
  after its correction and complete gate re-verification, a fresh Sol-high
  closure review found no blockers.
- Scope limit: AD-7 remains open. This is a finite relevance rule for distinct
  action kinds, not proof that an older same-kind attempted action or result is
  always behaviorally represented.

### 2026-08-25 — AD-10 sealed recorded replay integrity

- Recorded full-day replay now uses `RecordedDecisionArchive`, which computes
  an HMAC over the canonical private decision-record collection. Its
  verification key remains caller-held and stays outside objective history,
  normal presentation, and inspector output. The public Mara replay facade
  verifies the archive before it constructs a replay client.
- Complete deterministic source/replay coverage still proves equal day
  summaries, objective history, observations, results, restricted inputs, and
  selected timeout/retry failure fields without another source-client call. A
  separate full-day regression changes both the selected structured response
  and matching attempted action, then proves the original seal rejects that
  self-consistent alteration before a replay world exists.
- Three Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned: the
  focused autonomous-day suite, the complete offline repository check, and
  whitespace validation. A fresh independent Sol-high review found no
  blockers.
- Scope limit: this is integrity while the caller retains a trusted key; it is
  not a portable persistence format, durable key-management system, or proof
  of provenance against someone who controls the key. It does not prove
  live-model determinism.

### 2026-08-25 — Sixth whole-goal alignment

- A fresh independent Sol-high read-only review and the main alignment review
  compared every AD-1 through AD-12 criterion with the current successor
  implementation, focused tests, and retained boundaries. The goal remains
  owner-approved, coherent, and within its stated scope; no privacy leak,
  hidden-knowledge grant, or mechanism that warrants removal was found.
- AD-1 through AD-6, AD-8, AD-9, and AD-11 remain met narrowly. AD-7 remains
  open because the source-closed 64-entry delivered-evidence projection does
  not retain older behaviorally relevant action or result evidence beyond its
  recent-16 window. AD-12 remains open because no owner-authorized full-day
  live `qwen3:4b-instruct` run has occurred.
- The review reopens AD-10. Replay rejects altered restricted input and
  exhausted records, but it accepts a self-consistent altered selected record
  and reproduces a changed objective history. Until an integrity boundary is
  implemented or the owner explicitly narrows the criterion, the previous
  claim that tampered records fail explicitly is too broad.
- A valid action selected at minute 1,440 can schedule completion beyond the
  day boundary, making the run fail explicitly rather than falsely report
  completion. This preserves the current failure-reporting boundary but is a
  live-day completion risk that remains within the already-open AD-12 work;
  no implementation task is selected by this alignment record.
- Offline validation passed 193 current and 63 historical tests. The default
  autonomous-day command reached the exact Day 1 00:00 boundary, and
  `git diff --check` passed. Its unconfigured default model path remains
  evidence for the offline composition, not for a model-backed live day.
- `docs/main/ARCHITECTURE.md` still describes the earlier narrow successor
  state as lacking focal-policy, restricted-view, understanding, and full-day
  proof integration. That overview materially lags current verified behavior;
  record the drift without treating documentation repair as this state-only
  alignment work unit. The alignment counter resets to zero; no future work is
  selected or recorded.

### 2026-08-25 — Fifth whole-goal alignment

- A fresh independent Sol-high read-only review compared all AD-1 through
  AD-12 criteria with the goal, current successor implementation, tests, and
  retained boundaries. It found AD-2, AD-3, AD-4, AD-6, AD-8, and AD-10 now
  meet their stated boundaries, alongside AD-1, AD-5, and AD-9. AD-7, AD-11,
  and AD-12 remain open.
- The review corrected the AD-11 record: configured-harness inspector output
  already reports numeric growth, decision-status, and provider-failure
  aggregates. It remains incomplete because consumed decision provenance and
  understanding transitions are absent, and failed-handler objective tails are
  not part of its committed-work trace.
- AD-7 remains open because delivered observations and canonical understanding
  are unbounded and the recent-16 action window does not prove retention of
  older behaviorally relevant continuity. AD-12 remains open: no
  owner-authorized full-day live `qwen3:4b-instruct` run has occurred.
- Focused temporal/runtime/autonomous-day coverage passed 90 tests; the full
  offline check passed 187 current and 63 historical tests. The default
  autonomous-day command reached minute 1,440, and `git diff --check` passed.
- No runtime mechanism warrants removal. Broader general behavior beyond the
  stated criteria remains a scope limit, not a blocker. `ARCHITECTURE.md`
  materially lags the verified successor state; this alignment records the
  drift without expanding a state-only work unit. The alignment counter resets
  to zero; no future implementation task was selected or recorded.

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

### 2026-08-25 — AD-7 latest-action-result continuity

- Each restricted Mara decision input still retains the most recent 16 action
  results, and now also retains the newest result for each supported action
  kind when that result is older than the recent window. This is an explicit,
  bounded relevance rule: retained results keep their original causal order,
  and the result collection cannot exceed the recent 16 plus the finite
  supported action-kind count.
- A focused regression proves an early completed `work` result remains visible
  after later `wait` results displace it from the recent window, while the
  projection reports omitted results and remains within its declared maximum.
  The complete offline repository check and whitespace validation passed on
  re-verification; the three Solo gates are 3 met, 0 unmet, and 0 abandoned.
- A fresh independent Sol-high review found no blocker, hidden-knowledge
  grant, privacy leak, objective-history mutation, or unbounded growth. Scope
  limit: this does not complete AD-7. Older same-kind results and older
  attempted actions can still be behaviorally relevant beyond their windows.

### 2026-08-25 — Autonomous-day architecture refresh

- Refreshed the overview to describe the verified full-day successor rather
  than its earlier scaffold: restricted Mara decisions, world-owned action
  resolution, independent supporting and institutional activity, access-gated
  delivery and understanding, offline replay, focal-safe normal output, and
  omniscient inspection. This is documentation-only and changes no product
  behavior or goal criterion.
- Review corrections preserve the precise boundaries: Mara selects a `wait`
  attempt while the world may resolve a scheduled home wait as rest; the
  unconfigured command renders only its boundary, quiet spans, and bulletin;
  and an inspector tail exists only when terminal failure occurs during a
  dispatch. AD-7 remains open for older behaviorally relevant attempted-action
  or result selection, and AD-12 remains open for the owner-authorized live
  Ollama run.
- Three Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned: direct
  architecture assertions, the full offline repository check, and whitespace
  validation. Independent review found and corrected the three initial wording
  issues plus one dispatch-boundary edge case; a fresh final Sol-high closure
  review found no blockers.

### 2026-08-25 — AD-7 source-closed relevant continuity projection

- A restricted input now keeps older delivered observations when they source a
  retained belief, memory trace, contextual stance, or accessible diary entry,
  then fills only remaining capacity with newer context. The 64-entry cap still
  applies to every projected evidence collection, including accessible diary
  entries; a missing source or any required closure that exceeds that cap takes
  the explicit safe-failure path before a provider call.
- Focused regressions prove that an old belief source survives otherwise
  irrelevant observation growth, an oversized required observation closure is
  capped and fails before provider use, and an accessible diary entry cannot
  introduce an undelivered fact. Recorded safe-failure replay remains exact.
- Three Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned: the
  focused policy suite (30 tests), the full offline check (191 current and 63
  historical tests), and whitespace validation. A fresh Sol-high review found
  two cap/source-closure defects; both were fixed, reverified, and a second
  fresh Sol-high closure review found no blockers.
- Scope limit: AD-7 remains open. This defines and proves source-linked
  relevance for delivered evidence and accessible diary entries, but does not
  prove that every older behaviorally relevant attempted action or result is
  selected within the bounded continuity projection.

### 2026-08-25 — AD-7 bounded delivered-evidence continuity projection

- Each fresh restricted input now caps delivered observations, beliefs, memory
  traces, and interpreted claims at 64 entries and records exact total,
  included, and omitted counts. It also verifies source closure for retained
  beliefs, traces, claims, and contextual stance.
- A request with omitted evidence or broken source closure takes the explicit
  safe-failure path before a live provider call. Canonical agent evidence is
  not changed. Recorded replay validates and consumes the matching private
  safe-failure record; a recorded selected choice at that same incomplete input
  remains an explicit error rather than bypassing the boundary.
- Four Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned: the
  focused bounded-projection and replay regression, complete-view regression,
  full offline check (191 current and 63 historical tests), and whitespace
  validation. The first fresh Sol-high review found the replay-consumption
  issue; the correction was reverified, and a fresh Sol-high closure review
  found no code blocker.
- Scope limit: AD-7 remains open. This prevents a model from acting on silently
  incomplete continuity, but it does not prove that an older behaviorally
  relevant fact can always be represented within a continuing full-day path.

### 2026-08-25 — AD-11 failed-dispatch objective-tail inspection

- Before every autonomous-day dispatch, the composition captures the existing
  objective event, observation, and action-result identities. If that dispatch
  fails after mutation, the explicit inspector reports only its safe time,
  phase, and sequence position, then derives the uncommitted objective tail
  from the pre-dispatch checkpoint. Arbitrary scheduled-work IDs, kinds, and
  exception material remain absent.
- The regression places a successful and a failing handler in the same phase
  and minute. It verifies that the committed event stays outside the failed
  tail, the appended failed-handler event is identified exactly, and the failed
  dispatch is sequence two. A runtime regression independently proves the
  sequence-two ordering evidence.
- Four Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned: the
  focused runtime module, the autonomous-day tail regression, the full offline
  check (190 current and 63 historical tests), and whitespace validation. The
  first fresh Sol-high review found the missing tail boundary; after this fix,
  a second fresh Sol-high closure review found no blockers.
- This completes AD-11's explicit watchability and inspection boundary for the
  successor. It does not add recovery or rollback, expose private model
  material, or claim that arbitrary handler side effects are reversible.

### 2026-08-25 — AD-11 inspector causal provenance

- The explicit omniscient inspector now reports each successfully committed
  decision dispatch with its ordered coalesced trigger kind/source pair and
  reports Mara's source-linked transit understanding transition. The exported
  transition data is detached, so mutating an inspector payload cannot modify
  retained run evidence.
- A deterministic harness regression verifies the three exercised decision
  causes (scheduled wake, completed action result, and delivered observation),
  the understanding transition's observation/event links, and the absence of
  model input or private decision records from inspector output. Normal
  focal-safe rendering remains unchanged.
- Three Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned: the
  focused causal-inspection regression, the full offline check (188 current
  and 63 historical tests), and whitespace validation. A fresh Sol-high review
  found the original mutable-payload leak, the fix was reverified, and a fresh
  closure review found no blockers.
- Scope limit: AD-11 remains open. This reconstructs successful decision
  provenance and one understanding transition, but failed-handler objective
  tails remain outside the runtime's committed-work evidence.

### 2026-08-25 — AD-10 recorded safe-failure replay

- A recorded timeout now re-enters the policy boundary as the same explicit
  safe failure rather than being silently replayed as a selected wait. It
  creates the same safe wait, source-linked delayed retry, runtime summary,
  ordered objective events, observations, action results, and inspector
  objective state through minute 1,440, without calling the source client.
- Focused evidence asserts the preserved private failure tuple
  `failed`/`timeout`/`TimeoutError`, exact replayed restricted inputs, and
  aggregate inspector failure counts. The replay keeps its own recorded
  configuration identity and does not expose private evidence in objective
  history or normal output.
- Three Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned:
  the focused timeout/retry reproduction, the full offline check (187 current
  and 63 historical tests), and `git diff --check`. Fresh independent reviews
  corrected two evidence gaps before a final Sol-high closure review found no
  blockers.
- Scope limit: AD-10 remains open. This proves one recorded timeout/retry
  route, not every failure or tampering form, durable or user-facing replay,
  provenance authenticity for caller-provided failure metadata, or live-model
  determinism.

### 2026-08-25 — AD-8 safe-failure retry authority

- The successor runtime now gives an active decision handler an expiring,
  actor-bound retry capability. Scheduled work, retained stale contexts,
  mismatched actors, and direct generic attempts to forge a
  `SAFE_FAILURE_RETRY` trigger are rejected. Mara's active failed decision
  still creates the existing one-pending, 30-minute retry chain.
- Focused runtime coverage exercises all authority failures plus the allowed
  retry. The three Solo gates were reverified with 3 met, 0 unmet, and 0
  abandoned: focused runtime tests, the full offline check (186 current and 63
  historical tests), and whitespace validation.
- Fresh independent review identified the initial stale-context/public and
  generic-trigger bypasses; both were corrected and a subsequent fresh
  closure review found no blockers.
- Scope limit: AD-8 remains open. The capability limits who may report a
  failure retry; it does not independently establish whether a provider
  failure occurred or replace the legacy per-tick failure path.

### 2026-08-25 — AD-11 inspector model-status counts

- The explicit omniscient inspector now reports deterministic aggregate counts
  for retained Mara decision-record statuses. The unconfigured path states that
  this aggregate is unavailable; injected harness coverage proves both an
  all-selected run and a run containing one safe-failed decision.
- The status aggregate contains only status names and integer counts. Focused
  assertions confirm the model-path output excludes model inputs and private
  decision records, while normal focal-safe output remains unchanged.
- The four Solo gates were reverified with 4 met, 0 unmet, and 0 abandoned:
  autonomous-day world tests, CLI tests, the full offline check (185 current
  and 63 historical tests), and the manual privacy review. `git diff --check`
  passed. Fresh independent Sol-high review found no blockers.
- Scope limit: AD-11 remains open. These are counts of retained Mara records in
  the explicit inspector, not runtime-wide model-status counts; an exception
  before a private record is retained may make runtime decision totals differ.

### 2026-08-25 — AD-11 numeric model-context measurements

- The explicit omniscient inspector now reports numeric peak counts for the
  restricted decision-history projection, delivered observations, and
  understanding categories supplied across an injected Mara harness run. It
  derives them from retained private records but does not emit model inputs,
  observation material, or private records themselves.
- The deterministic harness regression verifies the exact aggregate shape for
  its complete day while normal focal-safe rendering remains unchanged.
- Focused autonomous-day world validation, the full offline check, and
  whitespace validation passed. The three Solo gates were reverified with 3
  met, 0 unmet, and 0 abandoned. Fresh independent Sol-high review found no
  blockers: the measurements are deterministic, do not alter state or policy
  behavior, and preserve the existing privacy boundary.
- Scope limit: AD-11 remains open. This makes context shape inspectable for the
  exercised harness path; it neither bounds unbounded observation or
  understanding collections nor proves full long-run continuity relevance.

### 2026-08-25 — AD-8/AD-11 sanitized failed-day presentation

- The autonomous-day command now catches only exceptions for which the runtime
  has already recorded sanitized terminal evidence. It returns nonzero and
  renders a focal-safe line saying the day stopped without completing, rather
  than letting a provider or replay exception escape as normal command output.
- A recorded-choice mismatch regression verifies the normal output omits the
  exception type and detailed mismatch text while inspector JSON retains the
  failure type, last committed time, failed time, and work counts. A separate
  exact-end failure regression confirms `Day 1 00:00` is described truthfully
  as incomplete, not as a failure before the boundary.
- The three Solo gates were reverified with 3 met, 0 unmet, and 0 abandoned:
  focused autonomous-day/CLI tests, the full offline check, and `git diff
  --check`. Fresh independent Sol-high review found and corrected the initial
  CLI escape and exact-end wording issues; fresh closure review found no
  blockers.
- Scope limit: AD-8 and AD-11 remain open. This reports runtime-recorded
  failure honestly; it does not add rollback, recovery, generic failure
  handling outside the runtime boundary, or reconstruction of uncommitted
  objective tails.

### 2026-08-24 — AD-2/AD-6 source-linked transit understanding

- The authored minute-660 home transit bulletin now schedules one
  `UNDERSTANDING_UPDATE` after its observation delivery and before a resulting
  decision. That update creates Mara's canonical trace and claim only from the
  delivered observation, preserving links to its immutable source event and
  delivery identity.
- Focused evidence confirms that the later same-minute restricted view contains
  the source-linked trace and claim. The existing inaccessible-location path
  still creates no observation, understanding, callback, or decision.
- Focused validation passed 18 autonomous-day world tests; the full offline
  validation passed 185 repository tests and 63 historical checks after the
  inspector's executed-work expectation was updated. `git diff --check` passed.
  The two Solo gates were reverified with 2 met, 0 unmet, and 0 abandoned.
- Fresh independent Sol-high review found no blockers. It confirmed causal
  delivery-to-understanding-to-decision ordering, the absence of objective
  institutional state from Mara's view, and deterministic equal-seed traces.
- Scope limit: AD-2 and AD-6 remain open. This is one static transit-status
  interpretation, not general inference, conflict handling, bounded continuity,
  or full knowledge-and-consequence coverage.

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
