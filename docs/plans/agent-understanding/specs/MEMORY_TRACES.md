# Memory Traces

## Topic

Represent delivered evidence as agent-owned, source-linked memory traces.

## Required behavior

- The existing direct-resource observation creates one focal memory trace.
- Each delivered official schedule observation creates one focal memory trace.
- An undelivered Official Record version creates no trace.
- Each trace retains its source observation, interpreted proposition, asserted
  value, delivery tick, and period when applicable.
- Repeated delivery creates another trace linked to the existing interpreted
  claim.
- Repeated delivery does not duplicate the interpreted claim.

## Ownership

Agent Understanding owns traces and interpreted claims. Observation delivery
continues to own which observations reach the agent. Objective events and the
Official Record remain outside this state.

## Evidence

- Focused tests create traces from delivered observations.
- Focused tests withhold delivery and observe no trace.
- Focused tests repeat version-two delivery and retain two traces for one
  interpreted claim.
- History export remains deterministic and detached.

## Exclusions

- Confidence changes
- Memory decay
- General language interpretation
- Shared Claim and Provenance extraction
