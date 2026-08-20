# Core Construct

Status: current product direction.

This document is a living guide to what 2084 is becoming. It describes the current direction without pretending that the setting, systems, or final form are settled.

## Central Idea

2084 follows one autonomous person living inside a broader social simulation shaped by institutions, incentives, limited information, relationships, and pressure.

The focal character is the main human-readable perspective into the world. They act without waiting for approval at every step. The observer watches them move, work, speak, remember, doubt, conform, and experience consequences while other agents and systems continue independently.

The project is not primarily about winning, directing every movement, or presenting aggregate research results. Its central experience is watching a believable life unfold inside a society that no single person fully understands.

## Current Thematic Direction

The world takes inspiration from *Nineteen Eighty-Four*, especially:

- uncertain surveillance and the self-censorship it can create;
- conflict between lived experience, memory, social testimony, and official records;
- public conformity that may not match private belief;
- institutions that are powerful without being omniscient or perfectly coordinated;
- trust, fear, status, scarcity, propaganda, and informing as social pressures;
- doublethink as a practiced way of living with contradictions.

These are starting mechanisms, not a commitment to recreate Oceania or reproduce Orwell's story. The simulation should develop its own people, institutions, history, and outcomes.

## The Focal Character

The focal character should be a genuine participant in the simulation rather than a privileged narrator or disguised player avatar.

They may have:

- needs, responsibilities, personal aims, and tolerances for risk;
- a limited field of perception;
- memories with sources, confidence, and possible errors;
- relationships that influence trust and disclosure;
- private beliefs and public expressions that can diverge;
- uncertainty about other people and institutional reach;
- plans that can fail, change, or be interrupted.

The focal character should not know hidden world state merely because the observer or simulation knows it. Their actions should arise from what is available to them.

## Reality, Claims, and Doublethink

Reality in 2084 should not literally be created by whoever speaks most authoritatively. The simulation preserves what actually occurred. Characters, institutions, records, and interfaces may each represent it differently.

For important claims, the simulation may need to distinguish:

1. what happened in the world;
2. what the character directly experienced;
3. what they remember and how confident they are;
4. what another person told them;
5. what the institution currently declares;
6. what they privately accept or suspect;
7. what they say or perform in public;
8. which version guides them in a particular context.

The doublethink-inspired mechanism should initially be modest. It can model context-dependent recall, confidence erosion, compartmentalization, rationalization, and differences between private and public behavior. It should not claim to reproduce human consciousness or rely on a magical switch that makes contradictions disappear.

Early contradictions should be structured and understandable, such as changing ration figures, revised production claims, altered rules, or conflicting accounts of a past event. Arbitrary language interpretation can wait.

The proposed architecture separates this into four responsibilities. The
**Official Record** owns the institution's mutable current public projection;
**Observation Delivery** determines which version reaches which person and
when; **Agent Understanding** owns source-linked memory, confidence, conflict,
contextual stance, and inspectable suppression; and **Claim and Provenance** may
later hold shared claim semantics once the first two modules provide two real
uses. Objective events remain outside all four in the append-only history. See
[The Lie and Doublethink: Proposed Architecture](../plans/LIE_AND_DOUBLETHINK_ARCHITECTURE.md).

## Institutions

Institutions may observe, broadcast, reward, investigate, ration, revise records, and punish. Their influence should come from rules, roles, resources, incentives, and social reach rather than direct access to private agent state.

A revised official record changes only the institution's controlled public
projection. It does not erase objective events, automatically alter private or
uncontrolled physical records, or instantly grant the revision to every agent.
Suppression and fabrication are therefore institutional operations with
authority, access, processing, time, and evidence—not global edits to the
simulation.

Institutional limits matter. Surveillance can miss events. Reports can be false or delayed. Officials can misunderstand evidence. Processing capacity can become overloaded. Different parts of an institution can act from different information.

A powerful institution with blind spots is more useful than an all-knowing authority because characters can form uncertain beliefs about its reach and adapt in unexpected ways.

## The Private Record

The focal character may possess a private diary or similar physical record. For now, this is a small system rather than a central pillar.

At minimum:

- it exists at a location in the world and can be possessed;
- the focal character can interact with it, including reading and writing;
- writing records the character's perspective at that time, not objective truth;
- entries can preserve an earlier belief or memory after public accounts change;
- using it should occur within simulated time and circumstance.

Discovery, concealment, confiscation, selective sharing, memory reinforcement, and other consequences remain possible later extensions. They should be added only when they create behavior that the simpler record cannot.

## Time and Consequence

Actions consume time. Work, travel, conversations, announcements, inspections, shortages, reports, and relationship changes may proceed without waiting for the focal character.

The simulation does not need to run while no session is active, but it should feel continuous while being observed. Time advancement should update the wider world, not only the focal character.

Consequences should remain connected to understandable world responses. Delayed or hidden consequences are welcome when the underlying chain can still be inspected during development.

## AI

The intended direction is to make the focal character model-backed first. The
model will be the character's decision and expression process: its validated
choices become the focal character's attempted actions, rather than suggestions
for a separate scripted actor.

The persistent character is not reducible to one model call. Identity, body,
location, aims, relationships, delivered observations, source-linked memory,
current plans, and prior outcomes remain explicit simulation state. The model
receives only a restricted character view and chooses what to attempt next.

AI does not automatically know the world, speak truthfully, remain consistent,
or deserve authority over consequences. It may reason, plan, choose, phrase, or
explain behavior, but it may not inspect hidden state, directly mutate the
world, or declare its own success.

World truth, perception, action validity, institutional access, and consequential resolution should remain governed by explicit simulation state and constraints. Simpler decision rules remain valuable wherever they answer the same question more clearly.

Begin with the focal character only. Supporting characters should become
model-backed only after the focal boundary demonstrates limited knowledge,
persistent identity, inspectable decisions, safe failure handling, and recorded
reproduction. Agent Understanding remains the canonical, inspectable substrate
for delivered evidence and structured memory; opaque model conversation history
must not become the character's only memory.

### Current implementation status

The first living slice currently uses transparent deterministic policies, not
AI. Those policies receive restricted agent or institution views and return an
attempted action; the simulation separately validates and resolves the attempt.
Policies receive immutable completed or rejected results, so an unsuccessful
attempt cannot silently advance their plan. This is enough to test knowledge
boundaries and inspectable consequences before adding a less predictable
decision layer.

The implemented belief model is also deliberately narrow. It recognizes one
structured direct-allocation proposition with fixed confidence and can link
incompatible values without erasing either one. Official Record observations
remain retained source-linked observations rather than being folded into that
different physical-allocation belief. It does not yet model memory decay,
reinterpretation, planning, or general language understanding. Public
expression can still respond to an explicit social-pressure threshold without
changing the retained private perspective.

The implemented Official Record experiment has four narrow seams. The institution
can publish one immutable, structured three-packet ration-schedule version under
a stable artifact identity without delivering it, and the focal character can
later consult that current version through configured access at the allocation
office. The consultation is recorded as an attempted and resolved action, with
its version-linked observation delivered separately on the next tick. A later
allocation resolution records the two-unit physical handover as its own
resource-identified objective consequence and delivers that outcome separately;
the handover does not itself change the schedule. A configured, authorized
institutional attempt later appends a two-packet version for the same period and
makes it current while retaining version one and both objective events. That
rewrite does not deliver an observation. A later access-valid consultation can
deliver version two while leaving the earlier version-one observation unchanged.
The autonomous focal path performs that second consultation only after the
partial handover and delivered counter pressure; it does not receive hidden
notice of the rewrite. The clerk separately consults version one through the
same access boundary before using it as evidence for the pressure action. Agent
Understanding, Claim and Provenance, and Observation Delivery remain proposals.
The `first_day_v2` scenario no longer uses the generic scheduled broadcasts;
the focal and supporting policies still contain scenario-specific consultation,
pressure, and diary decisions.

## Observation and Playability

Playability means embodied attention, not necessarily conventional control:

- one person is visibly identifiable and followable;
- their actions and immediate circumstances can be understood;
- the observer can inspect a readable account of beliefs, memories, plans, and uncertainty;
- other people and systems act independently;
- the normal perspective contains only information appropriate to the focal character;
- optional intervention may exist later, but autonomous watching is the default assumption.

An omniscient inspector may be useful for development and replay. It should remain distinct from the normal focal-character experience.

## Working Principle

Prefer the smallest mechanism that creates a meaningful interaction, uncertainty, or consequence. Thematic appeal alone is not enough reason to build a system.

Authored material may seed people, places, pressures, and starting conditions. It should not secretly force the focal character through a predetermined rebellion, betrayal, or collapse and then present that outcome as emergence.

## Still Open

- The focal character's identity, work, household, and initial situation
- The original setting and historical background
- The first small district and supporting population
- Which bounded focal-character model interface, failure policy, and recorded
  reproduction format should implement the approved model-backed direction
- Which interpretations or plans may later be proposed by the model while
  delivered evidence, source provenance, and world consequences remain explicit
- What evidence should be required before supporting characters also become
  model-backed
- Whether the selected public-counter stance and diary-cued resurfacing rule is
  the smallest useful Agent Understanding experiment, or should be removed
  after evaluation
- How much of the focal character's internal state the observer may inspect
- Whether and how the observer can intervene
- Which additional institutional limits, if any, are justified after the
  completed bounded Official Record rewrite
- Whether the first record-operation follow-up explores one suppressed reference or one fabricated artifact
- When Official Record and Agent Understanding provide enough evidence to extract shared Claim and Provenance semantics
- Whether the diary becomes consequential beyond basic physical interaction
- The eventual visual form and level of spatial detail
