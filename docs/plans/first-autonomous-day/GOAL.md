# First Autonomous 24-Hour Living Day

Status: complete; owner-approved on 2026-08-23 and completed on 2026-08-27.

Verified completion evidence is recorded in the
[Implementation Plan](IMPLEMENTATION_PLAN.md).

This goal follows the completed
[Model-Backed Focal Character](../model-backed-focal-character/GOAL.md) goal. It
builds the first accelerated full-day simulation around the implemented Mara
boundary without turning the project into an always-running service or a
general society simulator.

## Question

Can model-backed Mara live through one complete accelerated simulated day with
continuous identity, limited knowledge, bounded decision context, and real
world-owned consequences while supporting characters and institutions continue
to act independently?

## Goal Result

Add one successor composition that begins at an explicit simulated time,
advances exactly 24 simulated hours, and stops at the day boundary. The day must
contain a small ordinary rhythm of rest or inactivity, work or obligation,
movement, household or private time, and independently scheduled wider-world
activity. These are opportunities and constraints, not a prescribed dramatic
route.

Mara's live model continues to choose her actual attempted actions from a
restricted view. The simulation continues to own time, eligibility, physical
possibility, observation delivery, action resolution, objective truth, and the
end of the day. Supporting characters and institutions may remain transparent
deterministic policies, but they must have enough independent schedule and
activity to make the world continue while Mara is occupied or unavailable.

The complete day must be runnable offline with deterministic test choices,
reproducible from recorded model choices, and finally exercised through one
explicitly owner-authorized live Ollama run using the existing exact
`qwen3:4b-instruct` integration. The live run proves the full-day boundary and
runtime behavior, not deterministic sampling or a generally believable human.

## Time and Decision Boundary

Simulation time is authoritative and independent of wall-clock time. The goal
must define:

- an explicit start time and exact 24-hour end boundary;
- one documented time representation and ordering rule;
- action duration and scheduled-event semantics in that representation;
- the conditions that make an actor eligible for another decision;
- how quiet intervals advance without fabricating repeated no-op activity;
- how equal-time completions, deliveries, scheduled events, understanding
  updates, and decisions retain a deterministic causal order.

An actor must not be consulted merely because another minute or time quantum
passed. Decision eligibility may arise from initial activation, a completed or
rejected action, a delivered observation, an explicit scheduled wake, or
another equally narrow documented trigger. Rest, inactivity, and safe model
failure must not cause one provider call or one objective `wait` event per time
quantum.

The implementation may retain fixed stepping, add next-due advancement, or
introduce a small scheduling seam. The goal does not authorize a wholesale
runtime rewrite without evidence that the selected criterion requires it.

## Ordinary-Day Boundary

The full-day composition must create watchable opportunity for:

- a meaningful inactive or rest period;
- a work or other ordinary obligation;
- travel or location change under the existing physical-access rules;
- household, private, or diary time;
- at least one supporting-character action outside direct focal interaction;
- at least one institutional or wider-world event while Mara is occupied or
  inactive;
- a later focal encounter with some background consequence only through a
  channel Mara can actually access.

Authored schedules, roles, starting conditions, access, and pressures must be
reported honestly. They may create circumstances but must not encode a required
rebellion, discovery, confrontation, diary route, or other dramatic plot and
then present it as emergence.

The smallest new action or state needed for ordinary rest or inactivity is in
scope. A general needs, health, emotion, relationship, employment, or economy
system is not.

## Long-Run Model Boundary

The full-day model path must preserve the completed focal-character boundary:

- the model receives only Mara-safe current state and affordances;
- a schema-valid choice becomes an attempted action without scripted
  substitution;
- world validation and resolution remain authoritative;
- opaque provider conversation history is not canonical memory;
- live failure remains explicit and never invokes the scripted focal policy;
- private decision evidence stays outside objective history and normal output;
- recorded choices reproduce world behavior without claiming deterministic
  live sampling.

The current full-lifetime decision envelope cannot simply grow for the entire
day. Full objective and private evidence must remain inspectable, but the fresh
model request must use a bounded, explicit continuity projection. The
projection may select current state, unresolved aims, delivered evidence,
canonical understanding, and relevant prior results; it must not silently
discard a fact that still affects behavior or replace canonical state with an
uninspectable summary.

Initial measurable full-day ceilings are:

- no more than 128 focal model decision calls;
- no more than 48 KiB of serialized dynamic restricted decision input at any
  one call;
- no more than 8 MiB of serialized private decision records for the complete
  day.

If evidence shows that one ceiling is incompatible with a necessary boundary,
stop for owner review rather than quietly weakening or gaming the measurement.

## Run and Failure Evidence

The accelerated day must expose enough progress to distinguish useful quiet
time from a stalled run. Normal presentation should show readable simulated
time and summarize quiet spans without revealing hidden activity. The
inspector and final run summary must retain exact ordering and report at least:

- start, current, and end simulated time;
- decision counts by actor and model status;
- event, observation, and action-result counts;
- provider failure counts;
- peak restricted-input and retained private-record sizes;
- whether the day reached its exact completion boundary.

An unexpected policy or provider-adapter exception must not be reported as a
completed day. Runtime failure evidence must identify the last committed
simulation boundary without becoming an objective world event or leaking
private model material. Durable process restart is outside this goal.

## Invariants

- `EventLog` remains append-only objective evidence.
- Official Record changes never rewrite objective history or automatically
  deliver themselves.
- Agents learn only through observations and channels they can access.
- Time advancement never grants hidden knowledge or impossible authority.
- A model choice remains an attempted action, not a declared outcome.
- Supporting policies and institutions receive no focal-private state.
- Normal presentation remains focal-safe; the inspector is explicitly
  omniscient.
- Quiet-time compression or scheduling must not skip due actions, events,
  deliveries, or understanding transitions.
- Equal configuration, seed, and scripted or recorded choices produce equal
  ordered evidence and final objective state.
- The completed `first_day_v3` scenario remains available as a regression and
  comparison rather than being silently redefined as a 24-hour day.

## Completion Criteria

- **AD-1 Simulation-owned day:** A documented offline command advances a
  declared start time to exactly 24 simulated hours later and completes at the
  day boundary independently of the `first_day_v3` plot checklist or wall
  clock.
- **AD-2 Deterministic temporal order:** Actions, scheduled world and
  institutional activity, completions, deliveries, understanding updates, and
  decisions have explicit, tested ordering, including equal-time cases and any
  quiet-time advancement.
- **AD-3 Decision eligibility:** Policies are called only at documented
  decision triggers. A measured inactive interval produces no per-quantum wait
  actions or model calls, and safe failure has bounded retry timing.
- **AD-4 Ordinary focal rhythm:** The successor composition gives autonomous
  Mara real opportunities for rest or inactivity, obligation, movement, and
  household or private activity without a policy or skill encoding one required
  dramatic route.
- **AD-5 Independently living world:** At least one supporting character and
  one institutional or wider-world process act independently during the day,
  including consequential activity while Mara is occupied or inactive.
- **AD-6 Knowledge and consequence:** Mara encounters at least one background
  consequence only through a valid access or observation path. Undelivered
  activity does not enter her model input, understanding, or normal
  presentation.
- **AD-7 Bounded model continuity:** A fresh model request preserves relevant
  explicit continuity without full-lifetime growth, opaque provider memory, or
  hidden-world leakage and remains within the approved decision-count, input,
  and private-record ceilings.
- **AD-8 Failure behavior:** Timeout, unavailable model, malformed response,
  invalid choice, and unexpected runtime failure remain explicit, avoid rapid
  per-quantum provider calls, never use the scripted policy as fallback, and
  cannot produce a false completed-day report.
- **AD-9 Offline full-day proof:** Two complete scripted or deterministic-client
  24-hour runs with equal configuration and seed produce equal ordered events,
  observations, action results, relevant private evidence, run summaries, and
  final state while satisfying all growth ceilings.
- **AD-10 Recorded full-day reproduction:** Recorded focal choices reproduce
  equal ordered full-day world history and final state without a live provider
  call, with mismatch, exhaustion, and tampering remaining explicit failures.
- **AD-11 Watchability and inspection:** Normal output presents readable time,
  meaningful activity, and compact quiet spans without leaks; inspector and
  machine-readable summary reconstruct the exact causal sequence and measured
  long-run evidence.
- **AD-12 Integration and live day:** Existing bounded scenarios and tests
  remain passing offline. One explicit owner-authorized live run through the
  existing private Ollama `qwen3:4b-instruct` connection reaches the full-day
  boundary within the same authority, privacy, cadence, failure, and growth
  limits.

## Out of Scope

- A 24-hour wall-clock run, real-time pacing, closed-session advancement, or an
  always-running daemon
- Durable checkpoint/load, crash recovery, process migration, or distributed
  scheduling
- Graphical UI, intervention controls, service deployment, or production
  operations
- Model-backed supporting characters, general conversation, or multi-agent
  model orchestration
- General hunger, health, emotion, relationships, employment, economy,
  surveillance, or social-network systems
- Memory decay, consciousness claims, arbitrary model-authored canonical
  memory, or general language inference
- A larger district or population added only to make the run appear alive
- General provider routing, automatic model replacement, training, or skill
  rewriting
- Claiming one live day is deterministic, fully believable, or emergent
- Replacing or weakening the completed Official Record, Agent Understanding, or
  Model-Backed Focal Character boundaries

## Specification Routing

This goal is the authoritative bounded specification. After selecting one
smallest useful gap, consult only the relevant implementation and tests plus:

- the implemented loop, time, decision, replay, and current-limit descriptions
  in [Architecture](../../main/ARCHITECTURE.md);
- the ordinary-life, time, AI, and observer direction in
  [Core Construct](../../main/CORE_CONSTRUCT.md);
- the model authority and continuity boundary in the completed
  [Model-Backed Focal Character goal](../model-backed-focal-character/GOAL.md);
- the deferred 24-hour concerns in the completed
  [Mara Model Harness Plan](../MARA_HARNESS_PLAN.md#deferred-architecture).

The broader [Lie and Doublethink proposal](../LIE_AND_DOUBLETHINK_ARCHITECTURE.md)
is optional context, not an implementation checklist. Do not read or modify
`experiments/` unless a later owner-approved goal explicitly targets it.

Provider documentation or a live endpoint is required only for the final
explicit live criterion or a selected adapter-specific defect. Normal
implementation and repository validation remain offline.

## Completion Boundary

Complete AD-1 through AD-12 through fresh single-work-unit runs selected from
verified repository evidence. Each implementation work unit uses the actual
`$unlazy` skill in Solo mode through the autonomous development-loop automation,
records only its current gates, runs focused and full validation, receives fresh
independent review, updates verified state, and commits one coherent change.

Do not create a future task queue. After independent whole-goal review confirms
all criteria and the owner-authorized live day succeeds, mark the goal complete,
commit the final state update, and stop before selecting another goal.
