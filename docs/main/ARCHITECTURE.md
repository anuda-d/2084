# Architecture

Status: current description of the implemented boundaries and known limits.

This document describes the conceptual boundaries for 2084 and how the current
first living slice implements them. The implementation is a working feasibility
slice, not a settled production specification.

## Implemented Simulation Loop

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
5. Update structured beliefs from newly delivered claim observations.
6. Ask each idle policy for one attempted action using a restricted view.
7. Validate and resolve or schedule each attempt.
8. Retain a focal-character snapshot containing only admitted information.

`Simulation.run()` repeatedly calls this boundary. The terminal command advances
the loop automatically, but the engine remains discrete and deterministic. The
current run can reproduce identical history data from the same configuration
and seed; it cannot yet load a durable save and resume or replay a complete run.

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
- `simulation/actions.py` defines immutable action attempts, pending
  actions, and actor-safe terminal results.
- `policies/` selects attempts without receiving objective world
  resources, hidden history, or private state belonging to other agents.
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
active bounded goal has begun with the initial-publication, narrow public
consultation, and authorized rewrite seams described above.

- **Official Record** would own the institution's mutable current public
  projection and bounded rewrite, suppression, and fabrication operations.
- **Agent Understanding** would own source-linked memory traces, interpreted
  claims, confidence, known conflicts, contextual stance, retrieval
  accessibility, and inspectable suppression or resurfacing.
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

A later Agent Understanding module may make a memory less accessible or inhibit
a contradiction from guiding one contextual stance. That transition must not
delete its provenance from development evidence. Public expression remains a
separate attempted action rather than a belief field silently overwritten by
the institution.

### Public expression and action

What an agent says, performs, or attempts. This may differ from private belief because of fear, habit, strategy, social pressure, or uncertainty.

An attempted action does not create its own outcome. The world resolves whether it is possible and what follows.

### Institutional knowledge and official records

Reports, sensor observations, evidence, suspicions, queues, decisions, and public claims available to institutions.

Institutions act only on information they can access and process. Their official records may contradict world truth, private memory, or one another without gaining special authority over objective state.

The institution's current public projection may stop showing an earlier
official version, suppress references in controlled artifacts, or introduce an
artifact attributed to the past. Each accepted operation is still a new
objective event. Uncontrolled physical copies, private records, observations,
and agent memories change only through valid world actions or delivery paths.

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

Possible later changes include contextual stance, retrieval accessibility,
repetition effects, motivated reinterpretation, compartmentalization,
inhibition, resurfacing, memory decay, and cognitive strain. These should be
introduced one at a time, retained as inspectable transitions, and tied to
visible behavior. A conflict must not trigger automatic memory deletion.

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
change does not itself broadcast the result. Observation Delivery separately
determines who encounters the new projection.

## Physical Objects and the Diary

Physical objects should have only the properties required for current interactions: identity, type, location, possession, and relevant state.

The initial diary can be one such object. Its minimum supported actions are reading and writing. An entry should record time, content or structured claims, and the focal character's perspective when written. Writing should advance time and require physical access to the object.

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
observations, and belief transitions through `history_data()`. Equal configured
runs produce identical ordered records. This is replay evidence, not yet a
portable persistence format, checkpoint system, or full-run replay executor.

## Implemented First Slice

The current scenario contains:

- one focal character;
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

- The decision layer uses deterministic rules, not AI.
- The focal policy is tailored to this first day rather than driven by a general
  planner, need system, or schedule model.
- `Simulation` is a single large coordinator whose action-specific resolution
  branches will need separation if the action vocabulary grows.
- Action and observation payloads use immutable structured mappings rather than
  action-specific schemas.
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
- There is no deep Agent Understanding module: cognitive transitions remain split
  between the belief helper, simulation coordinator, focal policy, and observer.
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
- Which single Agent Understanding transition changes observable behavior without pretending to model full human cognition?
- Which authority, access, time, and capacity limits belong in the first Official Record rewrite?
- Should the first follow-up operation explore one suppressed reference or one fabricated artifact?
- When do Official Record and Agent Understanding justify extracting Claim and Provenance?
- Which delivery channel first needs stale or missed official versions?
- How much independent NPC behavior is required to make the world feel alive?
- What should the readable decision explanation expose?
- How should pauses, playback speed, and optional intervention affect time?
- What needs to be deterministic or seeded for replay?
- When should a new mechanism be removed rather than expanded?
- Which responsibilities should leave `Simulation` first as additional actions
  and world systems are introduced?
- When does history need durable persistence or executable replay rather than
  deterministic in-memory evidence?
