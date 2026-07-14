# Design References

This document records what 2084 is learning from its current references. It is not a requirement to reproduce them. Each idea still has to justify itself inside 2084's own central experience and scope.

## George Orwell's *Nineteen Eighty-Four*

Primary reference: [Orwell Foundation authorized text](https://www.orwellfoundation.com/wp-content/uploads/2010/09/Nineteen-Eighty-Four.pdf).

Useful inspiration includes:

- surveillance whose actual frequency is unknown, producing habitual self-censorship;
- social observation through coworkers, neighbors, relatives, patrols, and informants;
- institutions with specialized roles, labor, incentives, and operational limits;
- official records that are revised to match current claims;
- conflict among material experience, memory, testimony, artifacts, and official history;
- public performance that differs from private belief;
- unequal privacy, resources, credibility, and enforcement across social status;
- scarcity, rationing, favors, illicit exchange, trust, and selective punishment;
- restricted language as pressure on expression and coordination rather than a magic rewrite of thought;
- doublethink as active adaptation to contradiction, not ordinary accidental inconsistency.

The strongest transfer is not an omniscient state. It is a feedback system in which incomplete but credible surveillance, mutable public reality, and social pressure affect what people say, remember, and dare to do.

Supporting commentary:

- [Orwell Foundation overview](https://www.orwellfoundation.com/the-orwell-foundation/orwell/books-by-orwell/nineteen-eighty-four/)
- [Open University on surveillance](https://www.open.edu/openlearn/society-politics-law/george-orwell-and-nineteen-eighty-four/content-section-6.1)
- [Open University on doublethink and post-truth](https://www.open.edu/openlearn/society-politics-law/george-orwell-and-nineteen-eighty-four/content-section-6.3)
- [Orwell, “Politics and the English Language”](https://www.orwellfoundation.com/the-orwell-foundation/orwell/essays-and-other-%20works/politics-and-the-english-language/)

### Boundaries

2084 should not recreate Winston, Julia, O'Brien, Big Brother, Oceania's exact ministries, the novel's plot, or its terminal punishment arc. It should not hardcode rebellion, betrayal, or institutional victory and then describe the result as emergent.

Graphic torture, global superstates, war-front simulation, and a full language-control system are out of scope for an early version. The private diary may echo the novel, but it should earn its place through simulation behavior rather than recognition alone.

## *Agentic World Modeling: Foundations, Capabilities, Laws, and Beyond*

Reference: [arXiv v1](https://arxiv.org/html/2604.22748v1#S1).

The paper is a broad survey and position paper, not evidence that AI societies accurately reproduce human behavior. Its useful contributions are architectural and evaluative:

- separate hidden world state, observations, and agent beliefs;
- treat social worlds as partially observable and reflexive;
- keep structured social state separate from generated dialogue;
- keep an agent's decision policy separate from world transition and resolution;
- prefer explicit, testable constraints over persuasive surface realism;
- check long-horizon coherence, response to interventions, and constraint consistency;
- preserve versioned configurations, seeds, traces, failures, and replay;
- instrument the simulation before increasing sophistication.

### Boundaries

The paper does not justify thousands of LLM agents, claims of human fidelity, autonomous self-revising social models, full theory-of-mind systems, or “digital twin” language for 2084.

The normal experience should not become a formal evaluation dashboard. The paper's discipline belongs underneath the focal-character simulation, where it helps prevent impossible knowledge, state drift, and unexplained consequences.

## Reference Simulation: `/Users/anuda/Desktop/sim`

The local reference project demonstrates a useful interaction model. Its current direction is described in the [reference README](../sim/README.md) and [Core Construct](../sim/CORE_CONSTRUCT.md).

The key transferable idea is **watchable agency**:

- one autonomous character is the main perspective into a larger world;
- autoplay is the normal mode;
- the observer follows the character rather than approving every action;
- time and place constrain what can happen;
- other people, schedules, problems, and events advance independently;
- a compact narrative view explains current and recent behavior;
- notebooks, people, and events can be inspected without exposing all hidden state;
- optional steering may exist without becoming the central experience;
- the simulation owns truth and consequences while a planner recommends actions.

The reference is not an always-running server world when closed. Its clock advances through commands, while autoplay makes this feel continuous during observation. Its current manual control is also more bounded than some aspirational documentation suggests. These are useful reminders to distinguish the actual interaction from the imagined final form.

### Boundaries

2084 should borrow conceptual patterns, not copy the reference project's code, character, scenario, interface, or authored objectives. The focal character should belong to 2084's world and pressures.

The reference project's diary and Orwell's secret diary make a private physical record an appealing convergence. That does not automatically make it a core pillar. The first version should keep it to possession, reading, writing, time, location, and perspective-bound entries; deeper consequences must justify their scope.

## Applied Direction for 2084

Together, the references suggest:

> Follow one autonomous person through a small authoritarian social world. Let the wider society continue beyond their attention. Preserve the difference between what happened, what they experienced, what they remember, what the institution claims, what they say publicly, and what the observer is allowed to see.

The simulation should be rigorous underneath and experiential on the surface. Its interest should come from watching pressure, limited knowledge, relationships, and contradiction alter a life—not from a victory condition, a prescribed plot, or a graph claiming to prove how people behave.

## Scope Test

Before adding a system, ask:

1. Does it change a decision, interaction, uncertainty, or consequence the observer can understand?
2. Does it support the focal-character experience rather than merely expanding the setting?
3. Can it be represented more simply?
4. Does it preserve world truth, limited knowledge, and bounded authority?
5. Would removing it make the first slice clearer?

If an idea is thematically attractive but cannot yet answer these questions, keep it provisional.
