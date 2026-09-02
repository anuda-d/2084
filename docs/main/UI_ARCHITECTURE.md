# UI Architecture

Status: current interface direction; most described surfaces are not implemented.

The interface should make an autonomous social simulation watchable through one focal character.
It is not primarily a control panel, statistical dashboard, or conventional game HUD.

## Observer Role

The observer is attached to the focal character's life without necessarily playing as them.

The default experience should allow the simulation to advance autonomously while the observer:

- follows the focal character in the world;
- sees what they are doing now and what immediately preceded it;
- inspects a readable summary of plans, memories, beliefs, and uncertainty;
- looks at visible people, places, and objects;
- pauses, changes playback speed, or revisits recent events;
- optionally uses bounded intervention if that becomes valuable later.

Manual steering is an open possibility, not a requirement for the project to feel playable.

### Current implemented surfaces

The first living slice has a read-only terminal observer.
Each tick shows the focal character's location, aim, selected or ongoing action, concise decision explanation, newly delivered observations, action rejections, a held-versus-needed resource summary, and a small belief summary.
It receives only focal snapshots and cannot inspect the objective world or event history.
In explicit model mode, the same surface shows Mara's attributed concise decision reason and the consequence admitted by the simulation; it does not show the restricted request, model configuration, or private decision record.

The autonomous-day composition has a second focal-safe terminal surface based on readable simulated time rather than legacy ticks.
It shows the start and exact end boundary, compact quiet intervals, delivered transit information, and any completed Mara travel, work, household, or rest activity admitted by the world.
The offline default therefore remains intentionally quiet when no Mara policy is configured, while injected, recorded, or explicit Ollama decisions can create additional focal-visible activity through the same renderer.

Both scenarios can render a separately labelled omniscient inspector.
The first-day inspector contains objective state, institutional and official records, all beliefs, source-linked history, and linked model-decision evidence when present.
The autonomous-day inspector adds simulated-time execution, causal phase order, committed dispatch provenance, decision cadence, growth ceilings, continuity-requirement counts, and terminal-failure evidence.
Private live-run audit bundles retain the focal transcript, sanitized inspector, canonical decision records, verdict, and artifact hashes outside the normal observer view.
This separation is implemented and tested, although it is not yet a graphical interface boundary.

There is currently no graphical or spatial view, pause/resume control, playback speed, selectable people or objects, intervention, or durable history browser.
The surfaces below remain design directions unless identified above as already implemented.

## Main Perspective

The focal character should remain easy to find and follow.
A spatial view may eventually show their movement through a small district, but the first interface can be simpler if it still conveys place, time, and proximity.

The normal perspective should reveal only what the focal character can directly observe, reasonably remember, or currently infer.
It should not expose hidden NPC motives, unseen reports, institutional queues, or objective truth by accident.

## Possible Surfaces

### Living world

Where is the focal character, who is nearby, what are they doing, and how is time advancing?

### Current thread

A concise narrative rail may show the current action, immediate aim, recent event, conversation, consequence, and next uncertainty.
It should be grounded in simulation records rather than inventing connective story.

### Character understanding

A readable decision artifact may summarize:

- current aim;
- chosen or attempted action;
- relevant pressures and constraints;
- what the character currently believes;
- confidence and unresolved uncertainty;
- which remembered claim is currently accessible or guiding this context;
- alternatives they considered at an appropriate level;
- what they expect to learn or check next.

This is a user-facing explanation, not raw hidden model reasoning.

The first-day terminal implements the concise attributed decision reason and selected or ongoing action.
The autonomous-day normal view emphasizes admitted completed activity and compact time spans instead of displaying private decision input.
Alternatives considered, expectations, and a dedicated understanding surface remain proposed.

### People and relationships

The observer may inspect what the focal character knows or believes about another person: past interactions, trust, suspicion, obligations, and unresolved questions.
Unknown private state must remain unknown.

### Official reality

Broadcasts, notices, public records, rules, and institutional claims should appear as claims from identifiable sources.
The interface must not silently present them as objective world truth.

This surface should show the version of an official artifact that the focal character can currently access, not the complete Official Record or its hidden revision lineage.
A changed central record does not automatically replace an earlier observation or a stale physical copy.
The character must encounter the new version through an actual delivery or access path.

### Private record

The diary should initially appear as a physical object the focal character can read or write.
Its view shows recorded entries, not a complete memory database or omniscient event log.

Entries may expose earlier beliefs and contradictions, but the interface should make clear that they were written from the character's limited perspective.

### Development inspector

A separate surface already exposes objective events, hidden state, Official Record operations and versions, delivered-observation history, Agent Understanding transitions, and institutional state.
The first-day inspector can include linked private decision traces, while the autonomous-day inspector exposes sanitized decision status, cadence, dispatch, and growth evidence without canonical private decision records or restricted model input.
It exists for debugging, programmatic reproduction, audit verification, and explaining surprising behavior.
A durable replay browser and graphical inspector remain unimplemented.

This inspector must be visually and conceptually distinct from the normal main-character perspective.

## Showing Contradictions

The interface should let contradictions become experienced rather than reducing them immediately to a warning badge or score.

For example, the observer might see:

- an earlier diary entry;
- a newly encountered official artifact or announcement;
- the focal character publicly repeating the new account;
- a private confidence, accessibility, or contextual-stance change;
- another person's incompatible recollection.

The UI may later help compare these sources, but it should preserve their provenance and avoid declaring which one the character ought to believe.

## Autonomy and Intervention

Autonomous playback should be the default design assumption.
The simulation advances the focal character's plan and the wider world after visible events have had time to be understood.

Useful observer controls may include:

- pause and resume;
- playback speed;
- follow or free camera movement;
- selecting visible people and objects;
- opening recent history or the diary;
- temporarily enabling a bounded steering mode.

Any intervention should enter the simulation as an explicit input.
It should not silently replace the focal character's agency or grant them impossible knowledge.

## Working Principle

The interface should reveal the simulation without becoming a second source of truth.
Important statements should remain connected to actual events, official artifacts, delivered observations, memory traces, contextual stances, or claims.

Visual polish is valuable when it strengthens embodied attention or makes causality clearer.
It should not conceal an unclear simulation.

## Open Questions

- Does the first slice need a spatial map, or can place be conveyed more simply?
- How much of the focal character's private state should the observer see?
- Should the observer know when the character is rationalizing, or infer it from behavior?
- How are confidence, accessibility, contextual stance, and contradictions shown without turning them into game meters?
- How does the official-record surface distinguish a current artifact from a stale physical copy without revealing hidden revision history?
- When should the diary surface appear, and should writing be visibly animated?
- Is bounded steering useful, or does it weaken the observational experience?
- How much recent history is necessary to understand delayed consequences?
