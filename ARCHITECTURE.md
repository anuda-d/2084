# Architecture

This document describes conceptual boundaries for 2084. It is not yet a technical specification.

## Possible Simulation Loop

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

The observer normally watches this loop through one focal character. Autoplay can repeatedly advance it, but the simulation should remain step-based and replayable underneath.

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

## Candidate First Slice

A small first slice could contain:

- one focal character;
- a small supporting cast with schedules and relationships;
- a home, workplace, and one shared social location;
- one institution capable of broadcasting claims and limited observation;
- one ordinary obligation or resource pressure;
- one official claim that contradicts experience or an earlier record;
- a basic physical diary;
- autonomous time advancement and a filtered focal-character view.

This is a feasibility target, not a fixed scenario. It should be reduced further if any component prevents the character's behavior from being understood.

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
