# Official Record Rewrite

Status: active; approved by the owner.

This is the bounded implementation goal for the next 2084 experiment. It is
narrower than the broader
[Lie and Doublethink architecture proposal](../LIE_AND_DOUBLETHINK_ARCHITECTURE.md).
That proposal provides context and possible later directions; it is not a
checklist for this goal.

## Question

Can an institution replace the currently published version of an earlier ration
schedule without rewriting objective history or automatically changing what an
agent knows?

The experiment is working when the focal character validly encounters a
three-packet promise, physically receives two packets, and later finds that the
official schedule now says the entitlement was two packets all along. The
development inspector must still be able to reconstruct the complete sequence.

## Why This Matters

2084 needs to distinguish:

1. what objectively happened;
2. what the institution currently publishes;
3. what a person encountered and retains;
4. what the person later says or does.

This experiment tests only the first seam between objective history, official
publication, and delivered knowledge. It does not attempt to implement the
complete lie and doublethink architecture.

## Concrete Terms

For this experiment:

- one ration unit is one sealed one-kilogram staple-grain packet issued for
  household consumption;
- a packet is the scenario meaning of one existing integer resource unit; this
  goal does not introduce packet objects, lots, weights, or a new inventory
  model;
- the packet, quantity, institution, and period names are provisional
  worldbuilding;
- the official claim is narrowly structured as: the weekly household ration
  entitlement for a particular period is a particular number of packets;
- the physical handover is a separate objective fact: this household received a
  particular number of packets.

The entitlement and the handover must not be treated as the same proposition.
The direct official contradiction is between two versions of the same schedule
for the same period: three packets in the original version and two packets in
the revised version.

This experiment intentionally evolves `scenarios/first_day.py` rather than
adding a second fixed demonstration scenario. Preserve its movement, work,
allocation, pressure, and diary structure; replace the generic five-to-one
broadcast sequence with the structured three-to-two Official Record rewrite,
retain the separate two-packet handover, and change the scenario identifier
from `first_day_v1` to `first_day_v2`. Update current tests and current
documentation where the intended behavior changes. Keep the version-one
delivery report unchanged as historical evidence.

## Authored Experiment Sequence

1. The institution publishes version one of a weekly ration schedule. It
   promises three packets per household.
2. The focal character encounters version one by performing the narrow public
   record consultation authorized by this goal. Their observation remains
   source-linked to that version.
3. At the allocation office, world resolution grants the focal character two
   physical packets. This is recorded separately from the schedule claim.
4. A configured institutional actor attempts to rewrite the schedule. The
   reason and timing of this first attempt are authored scenario inputs, not an
   emergent institutional strategy.
5. A narrow institutional operation resolver checks the actor's configured
   authority. A valid attempt creates version two, which says the entitlement
   for the same period was two packets from the beginning.
6. Version two becomes the schedule's current published version. Version one is
   no longer returned by the current public projection.
7. The rewrite itself creates no agent observation and performs no broadcast.
   The focal character must perform a later public record consultation to
   encounter version two.
8. The inspector can show the original publication, the focal character's
   delivery, the physical handover, the rewrite attempt and result, both
   official versions, and which version is currently published.

The focal character may retain the earlier observation through the existing
observation or belief boundary. This goal does not require new memory,
suppression, resurfacing, or diary mechanics.

## Narrow Interaction Seams

This goal authorizes two small additions without selecting a general future
architecture:

- a public record consultation attempt that checks configured access, reads the
  artifact's current published version, and delivers one source-linked
  observation to the consulting agent;
- an institutional rewrite attempt and resolver that records the attempt,
  validates configured authority and the expected current version, and produces
  an accepted or actor-safe rejected result.

The consultation path is not a new Observation Delivery module. The
institutional operation may remain separate from the character action
vocabulary if that keeps the responsibilities clearer. Both paths must preserve
the existing separation between attempts, world resolution, consequences, and
delivered knowledge.

## Official Record Responsibility

For this experiment, Official Record owns only:

- a stable identity for the ration-schedule artifact;
- immutable, narrowly structured versions of that artifact;
- the identity of the currently published version;
- validation that a requested rewrite targets an existing artifact and expected
  current version;
- revision lineage from version two to version one;
- detached data needed by the inspector and deterministic history export.

Official Record does not own:

- objective world history or `EventLog`;
- why the institution chooses to rewrite something;
- actor authority, access, processing queues, or institutional capacity;
- recipient selection, archive access, broadcasts, or observation delivery;
- agent memory, belief, confidence, contextual stance, or action choice;
- diaries, stale physical copies, or other uncontrolled records;
- observer prose or a general rendering system;
- suppression, fabrication, restoration, or replacement operations;
- a general claim language or document system.

The action or institutional resolver checks actor authority before applying an
Official Record rewrite. Official Record validates its own artifact and version
invariants; it does not decide who is politically authorized.

## Invariants

- `EventLog` remains append-only objective evidence.
- Publishing version two never edits or removes the event that published
  version one.
- The earlier agent observation is not mutated when the official projection
  changes.
- The rewrite creates no observation by itself.
- Policies receive no hidden official versions or objective history.
- An attempted rewrite remains separate from its accepted or rejected result.
- An unauthorized or stale-target rewrite cannot change the current published
  version.
- Equal configured runs produce equal ordered evidence.
- Public presentation must not expose inspector-only history.

## Completion Criteria

- **OR-1 — Initial publication:** Version one publishes a three-packet weekly
  entitlement through a stable artifact identity.
- **OR-2 — Valid delivery:** The focal character receives a source-linked
  observation of version one through an existing allowed path.
- **OR-3 — Separate physical result:** The two-packet handover is recorded as a
  resolved world consequence, not as another version of the entitlement claim.
- **OR-4 — Authorized rewrite:** A configured authorized attempt creates version
  two with a two-packet entitlement for the same period and makes it current.
- **OR-5 — Preserved evidence:** Version one, version two, their lineage, and the
  objective publication and rewrite evidence remain inspectable.
- **OR-6 — No magical knowledge:** The rewrite alone creates no observation.
  Encountering version two requires a later valid delivery action.
- **OR-7 — Unauthorized rewrite rejected:** An unauthorized attempt targeting
  the current version leaves it unchanged and produces an actor-safe rejected
  result.
- **OR-8 — Stale-target rewrite rejected:** An authorized attempt targeting a
  stale version leaves the current version unchanged and produces an actor-safe
  rejected result.
- **OR-9 — Understandable run:** The focal projection shows only what the focal
  character encountered, while the inspector can reconstruct the full causal
  chain.
- **OR-10 — Reproduction:** The repository checks pass and equal configured runs
  retain equal ordered history data.

## Minimum Validation

Add only tests needed to prove the completion criteria and protect invariants
affected by the implementation:

1. a focused Official Record test for initial publication, rewrite, current
   version, and lineage;
2. focused rejection evidence showing that neither an unauthorized current-target
   rewrite nor an authorized stale-target rewrite mutates the projection;
3. an integration test showing that the accepted rewrite produces objective
   evidence but no automatic observation;
4. one end-to-end scenario test covering the three-packet promise, two-packet
   handover, two-packet revised schedule, focal knowledge boundary, and inspector
   evidence;
5. the existing repository check command.

Do not add fabrication, suppression, queue, capacity, rendering, generalized
claim, generalized document, or exhaustive invalid-input tests under this goal.
A new test must prove new behavior, protect an affected invariant, or reproduce
an observed defect.

## Explicitly Out of Scope

- claiming that the institution autonomously chose the rewrite;
- portraying the rewrite as an emergent story outcome;
- announcing that two packets are an increase over a fabricated lower baseline;
- general propaganda or arbitrary text rewriting;
- suppression, fabrication, restoration, or unperson behavior;
- processing queues, capacity simulation, and institutional bureaucracy;
- a new Observation Delivery module;
- a new Agent Understanding module;
- confidence erosion, contextual stance, inhibition, or resurfacing;
- new diary, stale-copy, concealment, or discovery mechanics;
- a shared Claim and Provenance module;
- AI-driven institutional or character decisions;
- permanent ration economics or settled worldbuilding;
- a second fixed demonstration scenario alongside `first_day`.

The chocolate-ration-style maneuver in which a prior warning is fabricated and
the reduced amount is announced as an increase is a possible later experiment.
It is not part of this goal.

## Stop and Review Conditions

Stop implementation and request owner review when:

- satisfying a criterion appears to require a new deep module listed as out of
  scope;
- the implementation needs a product or worldbuilding decision not made here;
- two consecutive implementation runs focus on the same criterion without
  producing new goal-level behavioral evidence;
- another round would only add edge cases or hardening to an already proven
  criterion;
- the simplest working implementation conflicts with a current architectural
  invariant;
- all completion criteria are satisfied.

It is valid to finish a run without changing code when the goal is complete,
blocked, awaiting review, or has no justified next change.

## Completion Boundary

This goal is complete when OR-1 through OR-10 have proportionate evidence and the
owner accepts the resulting behavior and changes.

Completion does not authorize the next operation. The development loop must not
continue automatically into suppression, fabrication, richer delivery, or
deeper cognition. It may recommend a next experiment, but the owner chooses and
approves the next active goal.
