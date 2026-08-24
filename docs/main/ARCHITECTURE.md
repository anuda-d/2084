# Architecture

Status: current description of the implemented boundaries and known limits.

This document describes the conceptual boundaries for 2084 and how the current
first living slice implements them. The implementation is a working feasibility
slice, not a settled production specification.

The bounded Official Record, Agent Understanding, and Model-Backed Focal
Character goals are complete. The owner-approved
[First Autonomous 24-Hour Living Day](../plans/first-autonomous-day/GOAL.md)
goal is active and targets one accelerated model-backed day with explicit time,
decision eligibility, a minimally living wider world, bounded model continuity,
offline reproduction, and one final owner-authorized live run. Its initial
bounded-model work now enforces restricted-input and retained-private-record
byte ceilings and projects prior decisions through a finite recent window. The
24-hour clock and a pure deterministic temporal agenda now exist as isolated
successor-runtime primitives, with a small agenda executor around them.
Ordinary-day composition, agent and action scheduling, full-day proofs, and the
live run are not implemented. The separate
thin-harness/fat-skills documents
describe a possible generalization of the completed Mara boundary, not an
implemented general agent runtime.

## Implemented Simulation Loop

### Simulated-time primitive for the 24-hour successor

The active full-day work defines authoritative time as a non-negative integer
count of whole simulated minutes. That integer is the sole ordering value;
readable `Day N HH:MM` text is a projection and wall-clock time has no role.
One `SimulatedDayClock` owns an explicit start, current time, and end at exactly
start plus 1,440 minutes. It permits equal-time or forward advancement through
that boundary and rejects backward or beyond-boundary movement.

This primitive is not yet wired into `Simulation.step()` or a successor
composition. A `TemporalAgenda` can register uniquely identified work within
the remaining day, order it by simulated minute, explicit causal phase, and
stable identity, then move the day clock directly to the next due instant or
the exact end boundary. The chosen successor equal-time order is scheduled
world and institutional work, action completions, observation deliveries,
understanding updates, then decisions. It releases only one phase at a time, so
work caused by an earlier phase can enter a later phase before already-pending
decisions are released. Once a phase has been released at a minute, inserting
that phase or an earlier one is rejected. This seam returns due work; it does
not execute it or fabricate intervening events.

This chosen order is not an exact copy of every legacy path. In the legacy
generic-broadcast path, institutional processing also delivers its broadcast
before same-tick action completions. `first_day_v3` does not use that generic
broadcast path. The successor agenda separates scheduled activity from
observation delivery so those causal phases can remain explicit.

The existing `first_day_v3` tick remains unchanged as regression evidence, and
no successor composition, agent/action event schedule, full-day command, or
scenario-level day-completion claim exists yet.

An isolated `DecisionEligibility` seam can place only five documented causes
into the agenda's decision phase: initial activation, a terminal action result,
a delivered observation, an explicit scheduled wake, or a safe-failure retry.
Causes for one actor at one minute coalesce into one eligibility record. Time
passage alone creates no record. The initial safe-failure cadence is one retry
30 simulated minutes later, with no retry if that instant would cross the day
boundary. The seam does not call policies or execute actions, and the legacy
tick loop does not use it yet.

An `AcceleratedDayRuntime` now provides the first isolated executor for these
temporal seams. A composition registers handlers by authored work kind, and the
runtime dispatches due batches through the agenda's causal phases. Handlers
receive only current/end time and a validated scheduling method; they cannot
advance time, release work, close registration, or re-enter the runtime through
that interface. The runtime retains exact
committed-work order and compact quiet spans, processes work due exactly at the
end boundary, then closes the agenda against further registration. An
unexpected handler or dispatch exception creates sanitized terminal evidence
and freezes both execution and registration to prevent false completion or
retry mutation.

This executor is still infrastructure rather than a successor simulation. No
agent, policy, action resolver, observation delivery, ordinary-day composition,
normal presenter, or command uses it yet.

```text
The world and its systems advance
        ↓
Agents receive limited observations
        ↓
Agents update memories, beliefs, and plans
        ↓
Agents attempt available actions
        ↓
World rules resolve actions and conflicts
        ↓
Consequences affect people, institutions, and records
        ↓
The focal-character view presents only an appropriate projection
```

`Simulation.step()` currently performs this loop in a stable order:

1. Increment the world tick.
2. Apply a scheduled initial official-record publication, authorized record
   rewrite, then scheduled institutional claims and their broadcasts. Publication
   and rewrite create objective evidence but no observation.
3. Complete actions whose duration has elapsed.
4. Deliver completion perceptions and queued prior-action outcomes.
5. Update structured beliefs, source-linked understanding, and Mara's bounded
   contextual stance from newly delivered evidence.
6. Ask each idle policy for one attempted action using a restricted view.
7. Validate and resolve or schedule each attempt, linking any model decision
   evidence to validation and eventual outcome outside objective history.
8. Retain a focal-character snapshot containing only admitted information.

`Simulation.run()` repeatedly calls this boundary. The terminal command advances
the loop automatically, while the engine remains discrete and world resolution
remains deterministic for equal attempts. Scripted runs reproduce equal history
from equal configuration and seed. Live model choices are not assumed
deterministic; detached recorded decisions can be replayed through the same
parser and resolver to reproduce world history without another provider call.
There is no durable save/checkpoint format or user-facing replay command.

## Current Implementation Map

- `scenarios/first_day.py` is the composition boundary. It creates
  the world, policies, rules, schedules, and completion conditions.
- `simulation/world.py` contains mutable objective state.
- `simulation/events.py` contains immutable append-only events and
  agent-specific observations with source links.
- `simulation/official_record.py` currently owns one ration schedule's stable
  artifact identity, immutable versions, same-period revision lineage, and
  current-version pointer.
- `simulation/agents.py` separates mutable agent state from the immutable
  restricted view supplied to a policy.
- `simulation/beliefs.py` derives the currently supported structured
  beliefs and contradiction links.
- `simulation/understanding.py` defines source-linked memory traces,
  interpreted claims, contextual stance, and inspectable stance transitions;
  the engine currently coordinates their updates.
- `simulation/actions.py` defines immutable action attempts, pending
  actions, actor-safe terminal results, and the shared model action-parameter
  contract.
- `policies/` selects attempts without receiving objective world resources,
  hidden history, or private state belonging to other agents. The scripted
  focal policy remains the default; an explicit model-backed policy can use the
  single local Ollama adapter or detached recorded decisions.
- `characters/mara/` contains the versioned authored profile and reusable
  choose-next-action skill used by the model-backed policy.
- `policies/mara_decision_request.py`, `policies/model_focal_policy.py`, and
  `policies/ollama_client.py` compose the restricted request, enforce the
  structured choice boundary, record or replay decisions, and make the one
  supported live provider call.
- `simulation/engine.py` currently centralizes scheduling,
  validation, resolution, perception delivery, belief updates, history export,
  completion, and focal projection.
- `observer/terminal.py` accepts only focal snapshots. The separate
  `observer/inspector.py` accepts the full simulation and is
  explicitly omniscient.

## Proposed Deepening Direction

The possible deeper architecture is described in detail in
[The Lie and Doublethink: Proposed Architecture](../plans/LIE_AND_DOUBLETHINK_ARCHITECTURE.md).
It is a proposal, not a description of currently implemented modules. The
completed bounded Official Record goal established the initial-publication,
narrow public-consultation, and authorized rewrite seams described above. The
completed bounded Agent Understanding goal added source-linked memory traces,
explicit official-version conflict, one contextual public stance, and one
diary-cued resurfacing transition. The completed Model-Backed Focal Character
goal connected only Mara to a model while preserving those state boundaries.

- **Official Record** currently owns the institution's narrow mutable public
  projection and authorized rewrite; broader suppression and fabrication remain
  proposed operations.
- **Agent Understanding** currently owns the bounded source-linked memory,
  interpreted-claim conflict, contextual stance, and resurfacing evidence;
  confidence change, inhibition, and decay remain proposed deepening.
- **Claim and Provenance** may be extracted only after Official Record and Agent
  Understanding create two real uses for shared claim identity, comparison, and
  lineage.
- **Observation Delivery** would own channel, reach, access, delay, recipients,
  and source attribution when events or official artifacts become agent-specific
  observations.

`EventLog` remains the append-only evidence of what actually occurred. Official
Record sits beside it; it never replaces or edits it.

## State Boundaries to Preserve

### Objective world state

Facts that are true in the simulation: time, locations, physical objects, resource quantities, actions that occurred, institutional operations, and other consequential conditions.

Objective history should not be overwritten when an official record changes. A revised public account is a new world event, not a retroactive mutation of the simulation's actual past.

### Observations

Information delivered to a particular agent through perception, conversation, broadcasts, documents, or other channels.

An observation should have a source and arrival time. Being present near an event does not necessarily mean an agent noticed or understood it.

### Agent understanding

What an agent currently retains or concludes. Memories and beliefs may have confidence, provenance, age, and context. They can be wrong without changing the world state.

For initially supported contradictions, beliefs should use structured claims whose conflict is explicit. The system should not depend on an AI reliably discovering every contradiction in arbitrary prose.

The bounded Agent Understanding path can select a context-specific public
stance and later resurface an earlier claim through accessible diary evidence.
Those transitions retain provenance in development evidence. More general
inhibition, graded accessibility, and decay remain future work. Public
expression remains a separate attempted action rather than a belief field
silently overwritten by the institution.

### Public expression and action

What an agent says, performs, or attempts. This may differ from private belief because of fear, habit, strategy, social pressure, or uncertainty.

An attempted action does not create its own outcome. The world resolves whether it is possible and what follows.

### Institutional knowledge and official records

Reports, sensor observations, evidence, suspicions, queues, decisions, and public claims available to institutions.

Institutions act only on information they can access and process. Their official records may contradict world truth, private memory, or one another without gaining special authority over objective state.

The implemented institution's current public projection may move from one
immutable version to a later one. Possible future suppression or fabrication
operations would still need to create new objective events rather than edit
history. Uncontrolled physical copies, private records, observations, and
agent memories may change only through valid world actions or delivery paths.

### Observer presentation

The projection shown to the person watching the simulation. The normal projection should be centered on the focal character and should not leak hidden NPC state, unseen events, or institutional secrets.

A separate omniscient inspector may expose underlying state for development, explanation, and replay. It should be visibly distinct from the normal experience.

## Focal Character and Wider World

The focal character uses the same basic world rules as other agents. Their special role is presentational: the observer follows them more closely and may inspect a readable summary of their state.

Time advancement should also update:

- other agents' locations, schedules, and actions;
- institutional broadcasts and operations;
- reports, investigations, and processing delays;
- relationships, rumors, resources, and pressures;
- events that can occur or resolve without the focal character.

The world does not need unlimited background simulation. Only systems capable of affecting decisions or consequences need to advance.

## Decisions and Resolution

Decision-making and world resolution should remain separate responsibilities.

A decision process may consider:

- current needs and aims;
- available legal or physically possible actions;
- observations, memories, beliefs, and confidence;
- relationships and perceived risk;
- time, location, resources, and current pressures;
- public expectations and private preferences.

The decision process may recommend an action and give a concise, user-facing explanation. It may not invent observations, alter hidden state, or declare success.

Resolution validates the attempt, applies costs and time, handles conflicts, and produces consequences. Important resolutions should preserve enough evidence to explain what happened.

### Model-backed focal policy

The implemented AI boundary begins with the focal character. In explicit model
mode, a versioned Mara profile, one reusable decision skill, and a fresh
restricted state are sent to one local Ollama model. Its valid structured output
becomes Mara's attempted action, rather than commentary on a choice made
elsewhere. The scripted focal policy remains a separate default and is never a
failure fallback.

Persistent identity, embodied state, delivered observations, source-linked
understanding, aims, obligations, holdings, accessible objects, and prior
outcomes remain explicit agent or world state. The model receives only the
restricted agent view. It
cannot inspect the development inspector or hidden state, mutate the world, or
declare success; existing world resolution remains authoritative.

Live model output is not assumed deterministic. Inspector-only decision records
therefore retain the restricted input, profile/skill identities, non-secret
model configuration identity, sanitized structured response, attempted action,
validation, and resolved outcome. Recorded-decision playback applies those
choices through the same parser and resolver without another live call. Prompt
text, endpoint addressing, raw provider failures, and hidden provider
chain-of-thought stay out of objective history and normal presentation. Mara's
concise `decision_reason` is intentionally retained as an attributed action
explanation and rendered in the normal `Reason:` line.

The active 24-hour goal has added three long-run guardrails to this boundary.
The dynamic restricted JSON is measured exactly in UTF-8 and the Ollama adapter
refuses inputs above 48 KiB before transport. Prior attempts and results use a
16-entry recent window with explicit total and omitted counts. The complete
private decision-record collection uses canonical compact JSON measurement,
cannot retain more than 8 MiB, and reports current and peak sizes only in the
omniscient inspector. These mechanisms do not yet bound delivered observations
or canonical understanding, prove that older behaviorally relevant results are
always represented elsewhere, or establish a complete-day call ceiling.

An exception during `Simulation.step()` creates sanitized inspector-only
runtime-failure evidence naming the failed tick and last committed snapshot.
The append-only log may retain a partial failed-tick tail; the simulation is
then terminal, cannot report completion, and rejects every later step before
mutation. This is an explicit failure boundary, not rollback or restart.

## Contradictory Reality

A small doublethink-inspired system can begin with a source-linked claim and
memory trace containing:

- the proposition or subject;
- the asserted value;
- the source;
- when it was observed or asserted;
- the agent's confidence;
- the context in which it is accepted, repeated, or acted upon;
- explicit links to known conflicting claims.

This permits an agent to remember one ration amount, repeat another at work, and remain uncertain in private without collapsing all three into a single loyalty score.

The bounded slice already records one contextual public stance, explicit
retrieval accessibility, and one diary-cued resurfacing transition. Possible
deeper changes include graded accessibility, repetition effects, motivated
reinterpretation, compartmentalization, inhibition, memory decay, and cognitive
strain. These should be introduced one at a time, retained as inspectable
transitions, and tied to visible behavior. A conflict must not trigger automatic
memory deletion.

## Bounded Institutions

Surveillance and enforcement should be modeled as processes rather than omniscient powers. A possible path is:

1. an action occurs;
2. a sensor or person may observe it;
3. an observation may become a report;
4. the institution receives incomplete evidence;
5. limited capacity determines what is processed;
6. an authorized response may follow;
7. other agents observe some version of that response and update their beliefs.

Not every step needs to exist in the first implementation. The invariant is that institutions cannot act from private state or information they never obtained.

Official-record operations follow the same rule: a role must have authority and
access to a known target, processing may consume time or capacity, and a record
change does not itself broadcast the result. The current delivery logic in
`Simulation` separately determines who encounters the new projection; a
standalone Observation Delivery module has not been extracted.

## Physical Objects and the Diary

Physical objects should have only the properties required for current interactions: identity, type, location, possession, and relevant state.

The current diary is one such object. Reading and writing require physical
access and consume their configured simulation duration. Entries preserve a
structured claim, its source observations, and start and completion ticks from
Mara's limited perspective.

The diary does not need discovery AI, hiding mechanics, evidence rules, memory bonuses, or complex editing initially. Its object identity leaves room for those consequences if later behavior justifies them.

## Records, Replay, and Explanation

The normal experience need not look like a study dashboard, but the simulation should retain:

- a configuration and random seed for each run;
- an append-only event history;
- observation deliveries and their sources;
- belief or confidence changes that affect decisions;
- attempted actions and resolved outcomes;
- institutional inputs and decisions;
- enough state to reproduce or inspect a surprising sequence.

These records are development infrastructure. They help distinguish emergence from scripting and detect impossible knowledge, inconsistent state, or fabricated consequences.

The current slice exports detached JSON-compatible configuration, events,
observations, and belief transitions through `history_data()`. Equal scripted
runs produce identical ordered history. Separately, `RecordedDecisionClient`
can consume detached private decision records and reproduce equal ordered world
history through the same policy, parser, and resolver without another model
call. This is programmatic full-run reproduction, not a portable persistence
format, checkpoint system, user-facing replay command, or claim that equal live
configuration produces equal samples.

## Implemented First Slice

The current scenario contains:

- one focal character with a deterministic scripted default and an explicit
  local model-backed decision mode;
- two supporting characters with small deterministic policies;
- a home, workplace, and allocation office connected by a travel graph;
- one institution with a structured initial ration-schedule publication,
  one authored authorized rewrite, and no scheduled generic broadcast in the
  current scenario;
- a workplace obligation and a three-unit household allocation need;
- a three-packet published entitlement, a separate two-packet physical handover,
  and a later two-packet published entitlement encountered through reconsultation;
- a basic physical diary;
- autonomous step advancement, action durations, and a filtered focal view.

The scenario is a feasibility result rather than a general social simulation.
Its starting need, route, publication and rewrite timing, hidden resource
commitment, pressure value, conformity threshold, policy priorities, and action
durations are authored. The policies choose from delivered information, but the
resulting day should not be presented as an emergent plot.

## Current Technical Limits

- The first model integration is deliberately narrow: only Mara can use one
  explicitly selected `qwen3:4b-instruct` model through one local Ollama adapter
  and one structured decision skill. Supporting agents and institutions remain
  deterministic, and there is no provider framework, tool loop, generic skill
  resolver, or opaque provider memory.
- Live model sampling may vary. Offline deterministic-client tests and
  recorded-decision playback prove the boundary and resulting world history,
  not deterministic or believable live behavior.
- The scripted focal comparison is tailored to this first day. The model skill
  does not encode that route, but it is still bounded to Mara and the current
  eight-action vocabulary rather than a general planner, need system, or
  schedule model.
- `Simulation` is a single large coordinator whose action-specific resolution
  branches will need separation if the action vocabulary grows.
- Model-selected action parameters have shared per-kind shape contracts, while
  action, event, and observation payloads still use generic immutable mappings
  rather than dedicated data types for every kind.
- The world has one resource model with simple per-agent integer holdings, one
  institution, three locations, three agents, and one diary. It does not yet
  model physical resource lots, transfer logistics, use, or storage.
- Belief creation recognizes one structured allocation proposition with fixed
  confidence values. There is no memory decay or general inference.
- Institutional reports and processing capacity are represented conceptually,
  but the current institution only applies the scheduled initial publication and
  one authored authorized rewrite. The generic engine broadcast path remains,
  but the current scenario does not configure it.
- Official Record currently supports one structured initial ration-schedule
  publication, a location-gated consultation of version one, and an authorized
  same-period rewrite that retains lineage and moves the current pointer to
  version two. The consultation resolver recognizes accepted rewrite evidence,
  and the autonomous focal path later reconsults through configured access to
  receive version two without changing the retained version-one observation.
  Focused evidence also covers unauthorized and stale-target rejection without
  changing the current projection.
- The allocation resolver records the two-unit physical handover as a separate,
  resource-identified objective consequence. Its later delivered outcome updates
  focal holdings without changing the published ration schedule.
- Agent Understanding is deliberately bounded. Its data types live in
  `simulation/understanding.py`, but transition logic remains coordinated by the
  large `Simulation` class and there is no memory decay, general inference, or
  model-authored canonical understanding.
- Claim and Provenance has not been extracted, and observation payloads still
  repeat proposition, value, source, and revision fields as mappings.
- There is no Observation Delivery module: reach, delay, co-location, and
  recipient selection remain centralized in `Simulation`.
- A simulation-owned seeded random generator exists, but the current path makes
  no random choice.
- The normal observer is terminal-only and read-only. There is no graphical UI,
  pause control, intervention, service layer, or always-running world.

## Open Architecture Questions

- Which state must update every step, and which can update only when relevant?
- What is the smallest useful action vocabulary?
- Which authority, access, time, or capacity limit would justify a later
  Official Record experiment beyond the completed rewrite?
- Should the first follow-up operation explore one suppressed reference or one fabricated artifact?
- When do Official Record and Agent Understanding justify extracting Claim and Provenance?
- Which delivery channel first needs stale or missed official versions?
- How much independent NPC behavior is required to make the world feel alive?
- What additional explanation evidence, if any, would remain agent-safe as the
  action vocabulary grows beyond the current concise attributed reason?
- How should pauses, playback speed, and optional intervention affect time?
- What needs to be deterministic or seeded for replay?
- When should a new mechanism be removed rather than expanded?
- Which responsibilities should leave `Simulation` first as additional actions
  and world systems are introduced?
- When does history need durable persistence or executable replay rather than
  deterministic in-memory evidence?
