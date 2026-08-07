# Architecture

This document describes the conceptual boundaries for 2084 and how the current
first living slice implements them. The package is a working feasibility slice,
not a settled production specification.

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
2. Apply scheduled institutional claims and deliver their broadcasts.
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

- `twenty_eighty_four/scenarios/first_day.py` is the composition boundary. It creates
  the world, policies, rules, schedules, and completion conditions.
- `twenty_eighty_four/core/world.py` contains mutable objective state.
- `twenty_eighty_four/core/events.py` contains immutable append-only events and
  agent-specific observations with source links.
- `twenty_eighty_four/core/agents.py` separates mutable agent state from the immutable
  restricted view supplied to a policy.
- `twenty_eighty_four/core/beliefs.py` derives the currently supported structured
  beliefs and contradiction links.
- `twenty_eighty_four/core/actions.py` defines immutable action attempts, pending
  actions, and actor-safe terminal results.
- `twenty_eighty_four/policies/` selects attempts without receiving objective world
  resources, hidden history, or private state belonging to other agents.
- `twenty_eighty_four/core/simulation.py` currently centralizes scheduling,
  validation, resolution, perception delivery, belief updates, history export,
  completion, and focal projection.
- `twenty_eighty_four/observer/terminal.py` accepts only focal snapshots. The separate
  `twenty_eighty_four/observer/inspector.py` accepts the full simulation and is
  explicitly omniscient.

## State Boundaries to Preserve

### Objective world state

Facts that are true in the simulation: time, locations, physical objects, resource quantities, actions that occurred, institutional operations, and other consequential conditions.

Objective history should not be overwritten when an official record changes. A revised public account is a new world event, not a retroactive mutation of the simulation's actual past.

### Observations

Information delivered to a particular agent through perception, conversation, broadcasts, documents, or other channels.

An observation should have a source and arrival time. Being present near an event does not necessarily mean an agent noticed or understood it.

### Memory and belief

What an agent currently retains or concludes. Memories and beliefs may have confidence, provenance, age, and context. They can be wrong without changing the world state.

For initially supported contradictions, beliefs should use structured claims whose conflict is explicit. The system should not depend on an AI reliably discovering every contradiction in arbitrary prose.

### Public expression and action

What an agent says, performs, or attempts. This may differ from private belief because of fear, habit, strategy, social pressure, or uncertainty.

An attempted action does not create its own outcome. The world resolves whether it is possible and what follows.

### Institutional knowledge and official records

Reports, sensor observations, evidence, suspicions, queues, decisions, and public claims available to institutions.

Institutions act only on information they can access and process. Their official records may contradict world truth, private memory, or one another without gaining special authority over objective state.

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

A small doublethink-inspired system can begin with a claim record containing:

- the proposition or subject;
- the asserted value;
- the source;
- when it was observed or asserted;
- the agent's confidence;
- the context in which it is accepted, repeated, or acted upon;
- explicit links to known conflicting claims.

This permits an agent to remember one ration amount, repeat another at work, and remain uncertain in private without collapsing all three into a single loyalty score.

Possible later changes include memory decay, repetition effects, motivated reinterpretation, compartmentalization, and cognitive strain. These should be introduced one at a time and tied to visible behavior.

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
- one institution with scheduled broadcasts and a small public record;
- a workplace obligation and a three-unit household allocation need;
- official five-unit and later one-unit claims that contradict direct sight of
  three units;
- a basic physical diary;
- autonomous step advancement, action durations, and a filtered focal view.

The scenario is a feasibility result rather than a general social simulation.
Its starting need, route, claim schedule, hidden resource commitment, pressure
value, conformity threshold, policy priorities, and action durations are
authored. The policies choose from delivered information, but the resulting day
should not be presented as an emergent plot.

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
  but the current institution only emits scheduled broadcasts. Those broadcasts
  reach every agent.
- A simulation-owned seeded random generator exists, but the current path makes
  no random choice.
- The normal observer is terminal-only and read-only. There is no graphical UI,
  pause control, intervention, service layer, or always-running world.

## Open Architecture Questions

- Which state must update every step, and which can update only when relevant?
- What is the smallest useful action vocabulary?
- How should agents update confidence without pretending to model full human cognition?
- Which institutional limits belong in the first slice?
- How much independent NPC behavior is required to make the world feel alive?
- What should the readable decision explanation expose?
- How should pauses, playback speed, and optional intervention affect time?
- What needs to be deterministic or seeded for replay?
- When should a new mechanism be removed rather than expanded?
- Which responsibilities should leave `Simulation` first as additional actions
  and world systems are introduced?
- When does history need durable persistence or executable replay rather than
  deterministic in-memory evidence?
