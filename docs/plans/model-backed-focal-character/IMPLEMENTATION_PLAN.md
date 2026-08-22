# Model-Backed Focal Character Implementation State

Status: active shared state; no implementation work unit has been selected.

## Run State

- Incomplete run: none
- Last completed run: MF-10C authored decision identity
- Verified implementation runs since alignment: 3
- Alignment due: yes

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| MF-1 Actual character decision | met | MF-1A verifies through the deterministic test client that `ModelFocalPolicy` calls the injected chooser once, converts its schema-valid response directly through the strict parser, and records the resulting `wait` attempt where the unchanged scripted mode selects travel. This proves the offline boundary, not live-model behavior. |
| MF-2 Restricted decision envelope | met | MF-2A verifies agent-owned focal identity; MF-2B verifies detached restricted serialization; MF-2C verifies current applicability plus agent-safe direct destinations, accessible artifacts and diary entries, request guidance, grounded claim/evidence/private-belief combinations, delivered pressure pairs, and the serialized cross-field rule without hidden-state leakage. |
| MF-3 Structured action contract | met | MF-3A verifies the exact pure outer parser. MF-3B verifies one shared contract for all eight supported kinds, with required, optional, forbidden, typed, bounded, and coupled parameter shapes enforced before attempt creation; world-dependent semantics remain resolver-owned. Whitespace-only list identifiers remain a resolver rejection rather than a parser error. |
| MF-4 World-owned consequence | met | MF-4A verifies through committed model-path tests that the unchanged resolver alone schedules valid travel, completes it at the configured tick with linked location mutation and an actor-safe result in the next restricted view, or rejects unreachable travel with no movement and a linked actor-safe reason. The client receives no consequence API. |
| MF-5 Decision continuity | met | MF-5A verifies that later deterministic-client decisions use only fresh serialized restricted input: a completed travel result plus workplace location leads to work, while a rejected travel result plus actor-safe reason leads to wait. Attempts and results remain explicit simulation state; no opaque client history determines the choices. This proves the offline boundary, not live-provider statelessness. |
| MF-6 Explicit failure | met | MF-6A verifies that explicit timeout and unavailable-model signals plus malformed responses and structurally invalid attempts produce one sanitized inspector-only failure record linked to one safe `wait` attempt, never the scripted policy. Schema-valid but world-invalid parameters still reach ordinary resolver rejection. |
| MF-7 Decision evidence and privacy | met | MF-7A verifies one inspector-only record per valid or failed selection with the exact detached pre-client input, explicit non-secret configuration identity, sanitized valid response, attempted action, attempt/action links, validation status, and immediate or eventual outcome link; raw failures, client credentials/config, and private records remain absent from AgentView, normal output, EventLog, and `history_data()`. |
| MF-8 Recorded reproduction | met | MF-8A verifies that an offline recorded-decision client consumes frozen private records in order, requires exact restricted-input equality, and replays detached valid choices or the exact generated safe failure wait through `ModelFocalPolicy`. A complete 18-decision first-day replay reaches tick 28 with equal ordered world history and event identity, no further source-client calls, and explicit mismatch, invalid-record, tampering, and exhaustion failures. This proves recorded world reproduction, not deterministic live sampling. |
| MF-9 Bounded behavioral proof | met | MF-9A verifies two seed-42 model-backed runs with equal opening inspector state and equal first serialized restricted inputs: valid `wait` versus travel choices become causally linked normal outcomes and leave Mara home versus at the workplace by tick 3. This is bounded deterministic-client evidence, not live-model determinism. |
| MF-10 Integration | open | MF-10A provides separate authored profile/skill inputs and a deterministic four-layer request. MF-10B provides the native Ollama adapter with exact offline request, extraction, timeout, failure, privacy, and no-retry evidence. MF-10C records the exact decision-contract, profile, and skill identities separately from restricted input and model configuration. The scripted default remains intact and offline checks pass 105 current and 63 historical tests. A usable documented live entry path and the explicit live smoke remain open. |

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

None. MF-10C is complete; whole-goal alignment is due before another
implementation work unit is selected.

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

### 2026-08-20 — Alignment after MF-9A

- Fresh Sol-high whole-goal review found no blocker and reopened no criterion.
  MF-1, MF-4, MF-5, and MF-9 remain met at their explicitly bounded offline
  evidence levels; MF-2, MF-3, MF-6, MF-7, MF-8, and MF-10 remain open.
- Tests-only work for MF-4, MF-5, and MF-9 is sufficient because it exercises
  the real model policy, restricted view, step loop, and unchanged resolver
  rather than recreating production behavior in fakes.
- A future live adapter must not use opaque provider history as canonical
  memory. The current deterministic-client evidence does not prove live
  provider statelessness or sampling determinism.
- Model-generated `decision_reason` currently enters the objective attempted-
  action event and normal focal explanation. It must remain attributed decision
  explanation or expression, never be presented as world truth or hidden
  private reasoning.
- The global action-kind list is not an agent-safe semantic affordance contract,
  and model-mode normal/inspector privacy remains unproven until detached
  decision evidence exists.
- The opt-in live smoke remains an eventual external-credential completion
  dependency, but is not yet an active blocker because no live adapter exists.
- No production or test code warrants removal. Keep the narrow client interface
  and focused evidence; do not grow generic parameter validation or test-client
  helpers into general frameworks without real duplication.
- The review selected no later implementation work. Focused tests passed 8;
  full checks passed 75 current and 63 historical tests; `git diff --check`
  passed; the worktree remained clean at reviewed HEAD `73e5178`.

### 2026-08-20 — Alignment after MF-3B

- Fresh Sol-high whole-goal review found no blocker, reopened no criterion, and
  closed no additional criterion. MF-1, MF-3, MF-4, MF-5, MF-6, and MF-9 remain
  met at their recorded offline boundaries; MF-2, MF-7, MF-8, and MF-10 remain
  open, so the goal is active and incomplete.
- The detached serialized input contains focal-owned state, delivered evidence,
  source-linked understanding, accessible objects, and action shapes without
  supporting-agent private aims or hidden objective and institutional state.
  Delivered visible supporting-character references remain actor-safe evidence.
- MF-2 remains open because the client is not given reachable destinations,
  location-applicable actions, actor-owned evidence/value combinations, or the
  `pressure`/`pressure_reason` cross-field rule. Whitespace-only identifiers in
  list-shaped parameters pass the parser shape check and are rejected by world
  validation; this caveat does not reopen MF-3.
- MF-6 remains met. Failure evidence stores sanitized category/type data outside
  objective history, links to the safe attempted action, appears only in the
  inspector, and retains no raw exception message or malformed response.
- MF-7 remains open because successful decisions lack records and neither
  restricted input, configuration identity, structured response, validation,
  nor resolved-outcome linkage is captured. MF-8 has no recorded-decision
  playback. MF-10 has no live adapter, external configuration entry path,
  current usage documentation, or opt-in live smoke.
- Model `decision_reason` remains an attributed character/model explanation in
  the attempted-action event and normal focal presentation; it must never be
  treated as objective world truth or hidden private reasoning. A future live
  adapter must not use opaque provider history as canonical memory.
- No code warrants removal. Evolve the existing failure-only
  `PolicyDecisionRecord` instead of adding a parallel evidence system, keep the
  client narrow, and do not turn parameter validation into a second resolver.
- The review selected no later implementation work. Focused tests passed 13;
  full checks passed 80 current and 63 historical tests; `git diff --check`
  passed; the worktree remained clean at reviewed HEAD `a7abcd7`.

### 2026-08-20 — Alignment after MF-8A

- Fresh Sol-high whole-goal review found no blocker and reopened no criterion.
  MF-1 through MF-9 remain met at their recorded offline boundaries. MF-10 is
  the sole open criterion, so the goal remains active and incomplete.
- The restricted input remains detached, agent-owned, source-linked, and
  affordance-bounded. It excludes objective resources, full topology,
  undelivered history, inspector and institution-private data, provider
  configuration, credentials, and unobserved supporting-agent private state.
- The unchanged resolver retains action validation, timing, mutation,
  rejection, and consequence authority. Explicit state and actor-safe outcomes
  support later decisions without opaque provider conversation memory.
- Decision evidence remains immutable, inspector-only, configuration-labelled,
  and causally linked through eventual resolution. Recorded playback uses the
  same policy, parser, and resolver boundary and proves world reproduction, not
  deterministic live sampling.
- MF-10 remains open because the runnable CLI still constructs only the
  scripted policy, no live provider adapter or external configuration path
  exists, provider errors are not translated at a live seam, and there is no
  explicitly opt-in credentialed smoke.
- Public documentation is stale: `README.md` still calls the model boundary
  unimplemented and replay nonexistent; `docs/main/ARCHITECTURE.md` still calls
  the policy planned and omits failure evidence and replay; and
  `docs/main/CORE_CONSTRUCT.md` retains outdated implementation questions.
- Credentials are not yet an owner blocker because there is no usable live
  path to test. Any live adapter must keep the narrow client interface, remain
  stateless with respect to canonical character memory, use only a non-secret
  configuration label, keep credentials external, and avoid a provider
  framework. No current production system warrants removal.
- The unused replay-validator `index` argument is a trivial cleanup opportunity,
  not a goal blocker. The review selected no later implementation work.
  Focused tests passed 20; full checks passed 87 current and 63 historical
  tests; scripted normal and inspector runs each produced 150 events;
  `git diff --check` passed; the worktree remained clean at reviewed HEAD
  `d131f36`.

## Verified Run Log

### MF-10A Authored decision request

- Criterion advanced: MF-10 Integration remains open.
- Observed behavior: separate Mara Profile v0 and `choose-next-action` v0
  Markdown artifacts load with stable human-readable identities and
  deterministic SHA-256 content identities. A pure composer places stable
  boundary instructions, the profile, the skill, and one fresh detached
  restricted decision state in four explicit ordered layers and derives a JSON
  Schema from the canonical supported action contracts.
- Boundary evidence: focused tests verify exact artifact loading, repeated
  identity, stable-before-dynamic ordering, explicit treatment of dynamic
  strings as untrusted data, JSON delimiting, later-input-mutation detachment,
  all eight schema branches, exact outer fields, and the existing conditional
  pressure rule. No scenario completion, provider configuration, credential,
  endpoint, hidden state, desired route, or private reasoning is introduced.
- Parser authority caveat: JSON Schema numeric semantics accept `1.0` as an
  integer, while the strict Python action contract rejects the decoded float.
  This difference is documented and tested; provider constraint never replaces
  the existing local parser.
- Validation: Four focused request tests and the combined 24 model-boundary
  tests passed; `./scripts/check.sh` passed 91 current and 63 historical tests;
  scripted normal and inspector runs completed; `git diff --check` passed.
- Independent review: The first fresh Sol-high review found the numeric-schema
  precision caveat above and no blocker. After it was documented and covered by
  a local-parser regression assertion, a second fresh Sol-high review found no
  findings, independently reproduced the checks and detachment/schema probes,
  and approved MF-10A for finalization. Live Ollama schema acceptance,
  profile/skill identity in decision records, and end-to-end live privacy remain
  outside this cycle's evidence.

### MF-10B Native Ollama adapter

- Criterion advanced: MF-10 Integration remains open.
- Observed behavior: one `OllamaDecisionClient.choose(model_input)` call composes
  fresh two-message Mara context, sends one native `POST /api/chat` with
  `stream: false`, `think: false`, the exact JSON Schema in `format`,
  temperature 0, 256 predicted tokens, and a 16K context, then extracts only
  the assistant `message.content` JSON as the candidate structured choice.
- Transport boundary: the standard-library client accepts only external
  cleartext private, loopback, or link-local numeric-IP origins, bypasses DNS,
  proxies, redirects, and provider history, permits no credentials in the URL,
  uses one exact request with no retry or model pull, enforces a whole-request
  deadline, and caps success and error responses at 1 MiB. Configuration
  identity records the exact model and material generation/timeout settings but
  not the endpoint.
- Failure evidence: focused fake and loopback tests cover socket and nested
  timeout, connection refusal and route errors, HTTP 404/500, close before
  status, malformed HTTP status and truncated response, model-label mismatch,
  invalid UTF-8/JSON/envelope/content, deep JSON recursion, oversized integer
  decoding, oversized and slow-drip bodies, malformed structured choice, and a
  schema-valid world-invalid attempt. These become the existing sanitized
  timeout, unavailable-model, malformed-response, invalid-attempt, or ordinary
  resolver-rejection paths without raw provider, endpoint, or thinking text.
- Authority and continuity evidence: a valid extracted choice passes unchanged
  through `ModelFocalPolicy` and the strict parser; the simulation alone owns
  attempt validity and outcome. Every call builds only the current profile,
  skill, and restricted state; no provider chat is retained and the scripted
  policy is never invoked as fallback.
- Validation: Thirty-eight focused request/adapter/policy tests passed;
  `./scripts/check.sh` passed 105 current and 63 historical tests; scripted
  normal and inspector runs completed; `git diff --check` passed.
- Independent review: successive fresh Sol-high transport reviews exposed and
  drove fixes for HTTP protocol exception escapes, response-model mismatch,
  recursive and oversized-number JSON, non-finite timeout values, automatic
  redirects, malformed URL suffixes and ports, environment proxy inheritance,
  unbounded slow/large responses, numeric-IP name resolution, scoped IPv6,
  public cleartext origins, lossy timeout identity, and close-before-status
  classification. The final fresh review found no findings, independently
  reproduced the focused/full checks and targeted socket probes, and approved
  MF-10B. Live Ollama behavior and profile/skill identity in decision evidence
  remain outside this cycle's evidence.

### MF-10C Authored decision identity

- Criterion advanced: MF-10 Integration remains open.
- Observed behavior: the Ollama client loads one immutable profile and skill for
  its lifetime and exposes a typed identity with decision-contract version,
  stable authored names, and exact SHA-256 content identities. A caller can
  supply that typed identity to `ModelFocalPolicy`, which records a detached
  plain-data copy on both selected and failed private decisions separately from
  restricted input and model configuration.
- Exact content evidence: independent recomputation matched profile
  `sha256:7a4e22b7f545c983b9c5cc0ead28abf5c2deb2c60c806295621dea0970fea678`
  and skill
  `sha256:23e37f6d1615539d2d89c876775676c6c3ab99a947f67d89a1f8fd0aedd5f0ed`
  to the UTF-8 text actually held by the client and embedded in its request.
- Privacy and compatibility evidence: identity/version/hash data appears only
  in inspector decision evidence. Authored prompt text, endpoint, provider
  thinking and errors remain absent from the record, normal view, and world
  history. Generic deterministic clients retain `authorship_identity=None`,
  exported-data mutation does not affect records, import order remains acyclic,
  and recorded-decision replay and tamper rejection remain functional.
- Validation: Thirty-eight focused request/adapter/policy tests passed;
  `./scripts/check.sh` passed 105 current and 63 historical tests; scripted
  normal and inspector runs completed; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no findings and independently
  reproduced hash-to-prompt correspondence, success and every failure category,
  detachment, inspector-only privacy, generic-client compatibility, equal-world
  recorded replay, tamper rejection, and import-order behavior. MF-10 remains
  open for the documented entry path and live smoke.

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

### MF-5A Explicit-state decision continuity

- Criterion met: MF-5 Decision continuity.
- Observed behavior: A deterministic client chooses travel from the initial
  restricted view, then chooses work from a completed travel result plus the
  new workplace location, or wait from a rejected travel result plus its
  actor-safe reason.
- Boundary evidence: Committed tests verify both later model-selected actions,
  their decision explanations, current location, linked result status, and the
  presence of explicit last-attempt and action-history state. Branch selection
  uses the result and location or reason; it does not consult captured prior
  views or opaque conversation history.
- Validation: Seven focused tests passed; `./scripts/check.sh` passed 74 current
  and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, reproduced all
  checks, and cleared the client's test-only captured-view list after the first
  choice; the same completion and rejection follow-ups still occurred. It
  approved MF-5 as met at the offline boundary without claiming live-provider
  statelessness.

### MF-9A Same-input divergent model behavior

- Criterion met: MF-9 Bounded behavioral proof.
- Observed behavior: Two seed-42 model-backed simulations receive equal first
  restricted views; valid wait versus travel choices produce distinct first
  attempts and, through normal resolution, home versus workplace locations at
  tick 3.
- Boundary evidence: The paired test verifies equal opening inspector state and
  full first serialized restricted input, distinct model-selected kinds, causal
  links from each first attempt to its normal completion event, and final
  location divergence.
  Clients receive no simulation, resolver, inspector, institution, or
  other-agent private state.
- Validation: Eight focused tests passed; `./scripts/check.sh` passed 75 current
  and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, reproduced all
  checks, confirmed same-builder and equal-view evidence is proportionate, and
  approved MF-9 as met only at the deterministic fake-client boundary.

### MF-6A Explicit model-decision failure

- Criterion met: MF-6 Explicit failure.
- Observed behavior: explicit timeout and unavailable-model exceptions plus
  malformed responses and structurally invalid attempted actions produce a
  sanitized private failure record and a safe model-policy `wait`; the legacy
  focal policy is never called.
- Boundary evidence: the simulation links each failure record to the ordinary
  attempted-action event and action id outside objective history. Raw response
  values and exception messages are not retained. Schema-valid but world-invalid
  parameters still become model-selected attempts and are rejected by the
  unchanged resolver rather than reclassified as selection failures.
- Privacy evidence: inspector output includes the detached failure records;
  normal focal output, `history_data()`, action history, and failure records do
  not expose raw responses or exception text. MF-7 remains open because valid
  decision input, model configuration identity, structured response, and
  resolved-outcome linkage are not yet recorded.
- Validation: Ten focused tests passed; `./scripts/check.sh` passed 77 current
  and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, reproduced the
  focused and full checks, independently probed structurally invalid and
  world-invalid parameters, verified the privacy boundary, and approved MF-6
  as met while keeping MF-7 open.

### MF-2B Serialized restricted model input

- Criterion advanced: MF-2 Restricted decision envelope remains open.
- Observed behavior: `ModelFocalPolicy` now supplies its client a fresh plain
  mapping/list/scalar serialization instead of `AgentView`. The input includes
  focal identity, embodied and goal state, prior attempts/results, delivered
  observations, beliefs, canonical memory traces and interpreted claims,
  contextual stance, accessible diary and public-record references, and the
  supported action kinds.
- Boundary evidence: focused tests JSON-round-trip the input, mutate nested
  identity, holdings, and action-kind containers without changing the view,
  simulation, or EventLog, and verify source-linked understanding is empty
  before delivery and later refers only to supplied delivered observations.
- Privacy evidence: forbidden objective, event-history, institution-private,
  provider, credential, and other-agent-private fields are absent. A delivered
  visible actor reference may still appear as actor-safe evidence.
- Validation: Twelve focused tests passed; `./scripts/check.sh` passed 79 current
  and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, JSON-encoded the
  input across every deterministic tick including diary and contextual-stance
  states, reproduced mutation and privacy probes, and confirmed no met
  criterion reopens. MF-2 remains open because the action contract still lacks
  agent-safe parameter-level affordances.

### MF-3B Per-action parameter contract

- Criterion met: MF-3 Structured action contract.
- Observed behavior: a shared immutable contract covers every supported action
  kind with required and optional fields. The pure parser rejects missing,
  unexpected, incorrectly typed, empty, out-of-range, and structurally coupled
  parameter errors before constructing an attempt.
- Boundary evidence: the serialized input receives a detached copy of the same
  contract, and the engine reuses its allowed fields. Reachability, location,
  physical access, delivered-evidence membership and uniqueness, understanding
  matches, and consequences remain ordinary resolver concerns.
- Focused evidence: all eight action kinds have valid parser cases plus bounded
  invalid cases; parser errors preserve inspector and EventLog state, while a
  shape-valid nonexistent destination becomes an attempted travel action and a
  normal linked rejection.
- Validation: Thirteen focused tests passed; `./scripts/check.sh` passed 80
  current and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, reproduced the
  checks, and probed contract coverage, booleans-as-integers, non-finite and
  out-of-range pressure, pressure/reason coupling, empty and duplicate evidence,
  unexpected nesting, cycles, deep nesting, and world-invalid travel. It
  approved MF-3 as met without reopening another met criterion. MF-2 remains
  open because agent-safe value options and the serialized pressure/reason
  cross-field rule are not yet supplied to the client.

### MF-2C Agent-safe action affordances

- Criterion met: MF-2 Restricted decision envelope.
- Observed behavior: the model input now identifies currently applicable kinds
  and supplies agent-safe value guidance for direct travel, accessible public
  artifacts and diary entries, allocation requests, grounded expressions and
  diary claims, delivered evidence, and delivered pressure/reason pairs. The
  shared pressure/reason relationship is serialized with the shape contract.
- Boundary evidence: immediate destinations reveal no full route graph; request
  guidance uses Mara's unmet requirement rather than hidden stock; claim and
  pressure options derive only from delivered observations and retained
  understanding; diary pairs require current physical access.
- Privacy evidence: focused and independent all-tick scans found no objective
  resource availability or commitments, hidden event history, full topology,
  institutional or other-agent private state, provider configuration, or
  credentials. Delivered visible-actor references remain actor-safe evidence.
- Authority evidence: affordances are detached guidance. Nested client mutation
  cannot affect the view, world, EventLog, or shared contract, and a shape-valid
  nonexistent destination still becomes an ordinary attempted action followed
  by resolver rejection.
- Validation: Fourteen focused tests passed; `./scripts/check.sh` passed 81
  current and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, scanned all 29
  deterministic states through tick 28, reproduced nested mutation and privacy
  probes, and approved MF-2 as met at the restricted offline envelope boundary
  without reopening MF-3 or another met criterion.

### MF-7A Linked private decision evidence

- Criterion met: MF-7 Decision evidence and privacy.
- Observed behavior: every valid or failed model selection produces exactly one
  immutable private record. It captures the pre-client restricted input, an
  explicit caller-supplied configuration identity, a structured response only
  after successful validation, the resulting attempted action, and linked world
  validation and terminal resolution fields.
- Causal evidence: immediate completion and rejection records link during the
  same step; accepted pending travel begins without a terminal status and is
  immutably updated with the tick-3 completion event when normal resolution
  finishes. Attempt, action, and outcome identifiers match objective events.
- Privacy evidence: records stay outside `EventLog` and `history_data()` and are
  rendered only by the development inspector. Raw malformed output, exception
  messages, client credential-like attributes and provider configuration are
  never retained. Normal output keeps only the existing attributed character
  decision explanation, not the private record or configuration identity.
- Detachment evidence: input is frozen before the client call, valid response
  and attempted action are detached, post-call nested mutation does not change
  records, and record data strictly JSON-encodes in tested paths. Callers must
  continue supplying a non-secret configuration label rather than credentials.
- Validation: Seventeen focused tests passed; `./scripts/check.sh` passed 84
  current and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, reproduced a
  seven-path matrix covering immediate, pending, rejected, malformed,
  shape-invalid, timeout, and unavailable decisions, and approved MF-7 as met
  without reopening another criterion. MF-8 remains open because no playback
  client or equal-history recorded-decision proof exists.

### MF-8A Recorded-decision reproduction

- Criterion met: MF-8 Recorded reproduction.
- Observed behavior: a recorded-decision client freezes exported private
  records, consumes them in order only when the current restricted input
  exactly matches, and returns detached structured choices through the same
  `ModelFocalPolicy` and resolver path without retaining or calling a provider.
- Reproduction evidence: a full deterministic-client first-day capture replays
  all 18 decisions, completes at tick 28, and produces the same ordered 150
  events, 24 observations, 73 action results, `history_data()`, and event ids
  with no additional source-client call and no record left unconsumed.
- Integrity evidence: reordered, missing, perturbed, inconsistent, invalid, or
  exhausted records fail explicitly without inappropriate consumption. Failed
  decision records can replay only the exact generated safe wait; tampered
  action, actor, kind, or reason data is rejected.
- Contract correction: full replay exposed that the existing scripted policy
  legitimately supplies `pressure_reason` without `pressure`. The shared model
  shape contract now matches the unchanged resolver's one-way rule: pressure
  requires a reason, while a reason alone remains valid.
- Validation: Twenty focused tests passed; `./scripts/check.sh` passed 87
  current and 63 historical tests; `git diff --check` passed.
- Independent review: Fresh Sol-high review found no blockers, independently
  replayed the tick-28 history, exercised mismatch, truncation, detachment, and
  safe-failure tampering, and approved MF-8 as met without reopening MF-2 or
  MF-3. This evidence proves offline recorded world reproduction, not
  deterministic live-model sampling. MF-10 remains open.
