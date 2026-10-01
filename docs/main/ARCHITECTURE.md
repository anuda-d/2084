# Architecture

Status: implemented contracts and known limits for the first-day and accelerated-day prototypes.
[Core Construct](CORE_CONSTRUCT.md) defines product direction; the [consequential-choice specification](../plans/first-consequential-choice/GOAL.md) records the completed scenario's scope and acceptance criteria.

## Implementation map

| Module | Responsibility |
| --- | --- |
| `scenarios/first_day.py` | Authored `first_day_v3` composition and CLI |
| `scenarios/autonomous_day.py` | Exact-day composition, social/transit options, ordinary resolution, and presentation |
| `scenarios/autonomous_day_audit.py` | Private live bundle creation, replay comparison, and standalone integrity verification |
| `simulation/engine.py` | First-day scheduling, validation, resolution, delivery, understanding updates, and focal snapshots |
| `simulation/world.py`, `simulation/events.py` | Mutable objective state and immutable append-only evidence |
| `simulation/official_record.py` | Ration revisions and current pointer, plus separately retained finite transit notices |
| `simulation/agents.py`, `simulation/understanding.py`, `simulation/beliefs.py` | Agent state, restricted views, actor-safe results, sourced claims, and stance transitions |
| `simulation/actions.py` | Attempt/result types and shared parameter contracts |
| `simulation/time.py`, `simulation/scheduling.py` | Whole-minute time and deterministic causal-phase agenda |
| `simulation/day_runtime.py`, `simulation/decision_eligibility.py` | Exact-day execution, explicit decision triggers, budgets, and terminal evidence |
| `policies/mara_harness.py`, `policies/model_focal_policy.py` | Public Mara facade, restricted serialization, strict choice parsing, safe failure, and recorded decisions |
| `policies/mara_decision_request.py`, `policies/ollama_client.py` | Authored request layers, response schema, and one stateless local provider request |
| `observer/terminal.py`, `observer/inspector.py` | First-day focal snapshots and separate omniscient inspection |

## Authority and source evidence

`WorldState` owns time, locations, physical objects, holdings, and consequential conditions.
`EventLog` retains what occurred; official revision never rewrites objective history.
Observations identify their recipient, arrival time, and source.
An event, record publication, statement attempt, delivered observation, understanding update, and later action remain separate causal facts.
Policies receive restricted views, not objective history, institutional secrets, or other actors' private state.

An attempted action never resolves itself.
The world validates parameters, authority, access, resources, and time, then schedules or resolves the consequence and supplies actor-safe results.
A schema-valid but physically invalid model choice may be rejected by ordinary world rules.
Normal presentation cannot turn inspector evidence into actor knowledge.

## Official records and understanding

The first-day record publishes an immutable three-packet entitlement under a stable artifact identity.
Access-valid consultation delivers a version-linked observation later; publication alone delivers nothing.
The two-packet physical handover is a separate resource consequence and does not alter entitlement.
An authorized same-period rewrite appends a two-packet version, retains lineage, and changes the current pointer.
Unauthorized or stale-target revisions leave that projection unchanged.
Later consultation can deliver the new version without erasing the earlier observation.
Transit notices likewise assert finite route/interval/status claims independently of actual service and delivery.

Delivered evidence creates focal-owned traces linked to interpreted claims.
Repeated delivery may create another trace for the same claim; undelivered versions create none.
Official claims conflict only across compatible referents with incompatible values; the physical allocation proposition is separate from official entitlement.
The transit conflict requires the same route and service interval, not merely different statuses at different times.
Canonical source evidence survives conflict.

At the allocation office, a delivered pressure signal above the configured threshold permits a `public_counter` stance sourced from the revised official claim.
Pressure determines the context, not the stance's asserted value; departure clears that context.
The policy uses the supplied stance to attempt speech, and rejection cannot rewrite understanding.
A physically completed diary write preserves the earlier official claim and source.
Only a delivered read of that entry creates the `private_diary` stance; a rejected read creates no resurfacing.
The supplied private stance prompts one ordinary archive recheck, then clears after consultation, without changing confidence or deleting traces/conflicts.
Supporting agents and institutions receive no focal-private stance or diary material.

Transition logic remains in `Simulation` and the autonomous-day composition.
There is no general claim language, memory decay, model-authored canonical understanding, standalone delivery module, or implemented official suppression/fabrication.

## Time and decisions

The first-day `Simulation.step()` order is institutional processing, due completions, completion perceptions and queued results, understanding updates, idle policy choices, action resolution, then focal snapshots.
The legacy generic broadcast path delivers during institutional processing; `first_day_v3` does not configure it.
Its tick-based 28-tick completion remains a separate regression from the accelerated day.

The accelerated day uses non-negative whole simulated minutes with a start and exact end at start plus 1440.
`TemporalAgenda` advances directly to due work or the endpoint without inventing activity during quiet spans.
Equal-time phases are scheduled world/institution work, action completion, observation delivery, understanding update, then decision.
Stable work identity breaks remaining ties.
A released phase cannot accept new work in that or an earlier same-minute phase; earlier work may schedule a later phase before it is released.

Handlers receive a restricted scheduling context and cannot advance the clock or re-enter execution through it.
The composition synchronizes `WorldState.tick` when time advances.
Five decision causes are supported: initial activation, terminal action result, delivered observation, explicit scheduled wake, and safe-failure retry.
Causes coalesce per actor and minute; time passage alone never asks a policy or model to decide.
Decision eligibility uses `[start, end)`; scheduled work and completions may still commit exactly at the closed end.
Otherwise available duration-bearing Mara attempts that would complete after the end are rejected before pending work is created.

Pending actions remain non-interruptible.
Delivered information may be retained while Mara is busy and become usable at her next legitimate decision.
The safe-failure cadence permits one authority-bound retry chain delayed by 30 simulated minutes, with no retry at or beyond the endpoint.
Marked model-backed actors allow 128 decision-handler invocations; a would-be 129th fails before the handler runs.
Deterministic supporting actors are not automatically assigned Mara's model-call budget.

Unexpected dispatch failure records sanitized terminal evidence and freezes further execution and registration.
This is not rollback: append-only effects from a failed handler can remain in an explicitly uncommitted tail.
The legacy engine likewise records a failed tick and last committed snapshot and rejects later steps after terminal failure.
Neither path may report false completion.

## Model boundary and continuity

`MaraHarness` exposes `AgentView -> ActionAttempt` and private decision evidence; the simulation decides when to invoke it.
Requests contain stable boundary instructions, the versioned Mara profile, the reusable choice skill, and fresh restricted JSON.
Profiles and skills cannot include hidden facts, future events, or a prescribed scenario route.
Provider history is not a fourth memory channel.
The world owns canonical state and consequence; judgment belongs in the authored skill/model, while validation and repeatable execution remain deterministic.

The first-day policy supports eight action kinds; the autonomous day exposes travel, work, household, and wait.
Shared parameter contracts enforce required, optional, forbidden, typed, bounded, and coupled fields before attempts are created.
The Ollama response schema is copied per request; scalar enums use only disclosed affordance options and do not mutate caller-owned state.
The local parser and world resolver remain authoritative over provider output.
Timeout, unavailable service, malformed response, and invalid choice yield an explicit safe wait, never a scripted policy fallback.

Dynamic restricted JSON is measured in UTF-8 and capped at 48 KiB before transport.
Recent action history uses a 16-entry window plus latest attempts and completed/rejected results by finite kind.
Delivered observations and source-linked understanding collections use 64-entry recent projections with total, included, and omitted counts.
A request requires complete relevant continuity and source closure for every retained belief, trace, claim, and stance.
Missing closure produces a safe failure before any provider call; canonical evidence is not discarded to make the request fit.
Private decision records use canonical compact JSON measurement and cannot exceed 8 MiB.

The autonomous-day world classifies persistent effects for every accepted action kind.
Travel is explained by location/reachability; wait/rest has no persistent consequence; first work/household completion fulfills a named obligation.
Up to eight world-owned continuity requirements can retain an exact actor-safe attempt/result pair, source identities, canonical consequence, and clearing lifecycle.
A fulfilled obligation's pair survives safe failures until a selected decision receives it while the obligation remains fulfilled.
Missing, substituted, mismatched, duplicate, or excess requirements fail before transport.
Voluntary repeats add no requirement; the model cannot author or clear them.

## Scenario-specific causality

The default accelerated composition schedules Ilan's workplace shift from minute 480 to 600 and an independent transit change at 510.
Only workplace-terminal access delivers the source to Ilan.
His immutable decision view contains his delivered evidence, current trigger, actor-safe state, valid actions, and world-supplied addressability.
His deterministic policy chooses a cited statement or ordinary wait.
The world requires the exact triggering Ilan-owned observation, valid source/channel/parameters, and matching finite claim.
An accepted statement schedules next-minute testimony; delivery independently rechecks workplace co-location before Mara gains an observation.
Committed delivery precedes understanding and an eligible Mara decision.
A home-bulletin path at minute 660 separately requires physical receiver access.

Mara's ordinary world-owned opportunities include travel, 120-minute work, 60-minute household activity, and a scheduled-home wait resolved as 60-minute rest.
The consequential-choice scenario's opt-in notice, tradeoff deadlines, service-dependent travel, access-gated timing, and information counterfactuals are documented in the [implementation record](../plans/first-consequential-choice/IMPLEMENTATION_PLAN.md).
Those authored options preserve the option-absent regressions and are retained in replay configuration.
They create opportunities, not a required dramatic or live-model outcome.

## Presentation and evidence

Normal first-day output receives only focal snapshots; accelerated output shows admitted encounters, attempts, consequences, and compact quiet spans.
Official accounts remain attributed claims, diary entries remain earlier perspectives, and scripted decisions are labelled as authored.
A concise attributed decision reason may be public; prompts, endpoint details, raw failures, private records, and hidden reasoning may not enter objective history or normal output.
The separate inspector is explicitly omniscient.
Accelerated inspection reconstructs committed dispatch/phase order, observations, understanding, attempts/results, model status, budgets, and any uncommitted failed-dispatch tail.

Detached `history_data()` preserves JSON-compatible objective evidence.
Recorded decisions pass through the same parser and world resolver without another provider call and require matching restricted inputs, seed, and authored configuration.
`MaraHarness.from_recorded_archive(...)` verifies a private HMAC-sealed archive against a caller-held key before replay.
This detects edits while the key remains trusted; it is not proof against someone who controls the key or a durable save/checkpoint format.
Live-bundle creation runs a replay comparison; standalone verification checks stored schemas, provenance, permissions, hashes, and verdict without replaying again.

## Regression coverage and limits

| Boundary | Existing test modules |
| --- | --- |
| First-day truth, access, records, stance, diary, and presentation | `test_living_simulation`, `test_official_record`, `test_agent_understanding`, `test_first_day_cli` |
| Restricted choices, authored inputs, provider failure/privacy, and replay | `test_model_focal_policy`, `test_mara_harness`, `test_mara_decision_request`, `test_ollama_client` |
| Time, ordering, eligibility, exact-day failure, and budgets | `test_simulated_time`, `test_temporal_agenda`, `test_day_runtime`, `test_decision_eligibility`, `test_day_decision_runtime`, `test_day_decision_budget` |
| Social/transit causality, obligations, CLI, private audit, and replay | `test_supporting_policy`, `test_autonomous_day_world`, `test_autonomous_day_cli`, `test_autonomous_day_audit` |

The scenario inputs, schedules, pressures, and scripted choices are authored.
Equal deterministic or recorded choices prove reproduction; equal live settings do not guarantee equal sampling or believable behavior.
The engine remains a large coordinator, payloads use immutable mappings, and holdings are simple integer quantities.
There is no general economy, supporting-agent cognition, broad social model, graphical UI, durable save system, or user-facing replay command.
