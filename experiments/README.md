# Provisional experiments

Experiments in this directory test one uncertain concept at a time. They are not
production packages or settled architecture.

## Source-linked history

`source_linked_history.py` tests the existing architectural boundary between
objective world events and observations delivered to particular agents. Its
in-memory history only appends events. A later official claim is recorded as a
new event and cannot revise an earlier record. Observations must point to an
existing event, include a source and delivery tick, and cannot arrive before the
event. Observation queries are scoped to one agent.

Run its deterministic standard-library tests from the repository root:

```bash
python3 -m unittest discover -s experiments/tests -p 'test_*.py'
```

The repository-wide `scripts/check.sh` command runs the same suite. Python 3 is
required; no third-party test runner or package installation is needed.

## Replay record

`replay_record.py` adds a provisional in-memory record around source-linked
history. It captures an integer run seed, recursively immutable configuration,
objective events, and all source-linked observations. Its public structured-data
round-trip validates identifiers, provenance, ordering, and delivery timing by
rebuilding a fresh `SourceLinkedHistory` through that experiment's public
methods. Invalid input never mutates an existing history or the caller's data.

The complete observation sequence is exposed only for this omniscient
development use. It does not authorize an agent or normal observer to read that
sequence.

## Deterministic integer transition

`deterministic_transition.py` tests one provisional transition seam over a
deliberately generic integer state. `apply_transition` accepts an immutable
state, an explicit integer seed, immutable configuration, and a
`SourceLinkedHistory`. It advances the state tick once and records exactly one
objective event containing the before value, selected delta, and after value.
It does not create an observation.

The configured deltas are an ordered nonempty sequence. Selection is the
transparent rule `seed % len(deltas)`, with that index used to select the delta.
This avoids depending on Python's pseudo-random-number implementation. The
configuration copies caller-owned delta sequences into an immutable tuple, and
the state, result, event, and event details exposed by the public seam are
immutable.

The standard-library test command above includes fixed examples of seed
selection, deterministic repetition on fresh histories, validation before
history mutation, and returned-data immutability. No additional command or
dependency is required.

## Single-transition replay

`single_transition_replay.py` provisionally composes the existing replay record
and deterministic integer transition. `SingleTransitionReplay.capture` retains
a detached immutable copy of the initial `GenericIntegerState` alongside an
unchanged `ReplayRecord`. The record configuration must contain exactly
`deltas` and `event_kind`, and the record must contain exactly one objective
event.

`reproduce` reconstructs `TransitionConfiguration` from the record, invokes the
existing `apply_transition` with the retained seed and state against a fresh
`SourceLinkedHistory`, and returns the transition result only when that fresh
history's complete objective event sequence exactly equals the record's event
sequence. Invalid retained inputs raise `SingleTransitionReplayInputError`.
Valid inputs that produce a different event raise
`SingleTransitionReplayMismatchError`, which exposes immutable recorded and
reproduced event tuples for diagnosis. Neither path mutates the caller's state,
the replay record, or the history from which the record was captured. The
standard-library command above exercises the worked example and mismatch paths;
no command or dependency changes are required.

### Explicit limitations

The single integer transition is not a repeated simulation loop, decision or
action model, belief update, institution, diary behavior, scenario or setting,
UI, AI behavior, persistence format, replay file, or production package. Its
seed is a deterministic selector, not a claim about a future randomness
strategy. The transition records at the prior state tick plus one; this local
choice does not impose repository-wide monotonic event chronology.

The replay record itself still only rebuilds recorded history. The composed
single-transition seam reproduces exactly one generic integer transition; it is
not repeated stepping, seed evolution, decision replay, portable persistence,
or a permanent state/schema design. The retained initial state is in-memory and
does not alter the replay record's version or structured-data shape. The seam
compares objective events only: any observations already retained by the record
remain untouched and are neither recreated nor treated as agent knowledge.
Event and observation identifiers remain deterministic in-memory counters, and
details and configuration accept only scalar, mapping, and sequence values that
can be copied into immutable containers. Replay does not settle authorization
for omniscient history and projections.

## Repeated-step seed contract comparison

[Repeated-step seed contract comparison](repeated_step_seed_contracts.md)
compares explicit per-transition seeds with a stable, versioned deterministic
derivation from a run seed plus explicit step and stream identities. It defines
retained inputs, resume and branching implications, inspectability and failure
expectations, and observable acceptance tests for either possible contract.

This is a design note, not an implementation or decision. It rejects
runtime-specific hashing, hidden entropy, and unspecified mutable PRNG state,
but deliberately leaves the seed contract and any derivation algorithm
unresolved. The existing seam remains a single transition with one explicit
integer seed.

## Explicit per-transition seed candidate

[Explicit per-transition seed candidate proposal](explicit_transition_seed_candidate.md)
makes Contract A locally testable. `explicit_transition_seed_run.py` implements
that bounded candidate by coordinating repeated calls to the unchanged
`apply_transition` against `SourceLinkedHistory`. Fresh execution validates a
complete immutable input tuple before creating history, directly supplies each
retained integer seed, chains immutable states, and returns complete immutable
events and adjacent traces containing the exact step, `transition` stream,
seed, and event.

The candidate also validates reproduction metadata before execution and checks
the resulting final state, events, and traces. A validated in-memory prefix can
be rebuilt and resumed with an original, unrenumbered suffix; inconsistent
prefix state, history, trace, or suffix metadata fails before rebuilding or
appending history. Standard-library tests cover the proposal's seven evidence
categories, including modulo-collision seeds, unrelated randomness, differing
Python hash seeds, and failure-before-mutation cases.

This remains a reversible candidate-local experiment, not a project-wide seed
decision or production simulation loop. It does not change `apply_transition`,
`SourceLinkedHistory`, replay record data, commands, dependencies, or the open
choice between explicit seeds and stable versioned derivation.

## Post-experiment seed assessment

[Explicit per-transition seed candidate assessment](explicit_transition_seed_assessment.md)
maps all seven shared acceptance tests to the candidate implementation and its
tests, then records the corresponding Contract B evidence status. Contract A
has bounded evidence for this generic in-memory experiment. The assessment
records that Contract B had no concrete candidate at that point, so it does not
select a project-wide seed contract.

The assessment's recommended documentation-only follow-up is now the candidate
proposal indexed below. Contract B still has no implementation or executable
evidence.

## Deterministic transition seed candidate

[Deterministic transition seed candidate proposal](deterministic_transition_seed_candidate.md)
makes one Contract B candidate precise enough for a later bounded experiment.
It defines candidate-local unsigned 64-bit run seeds and zero-based steps, the
single `transition` stream, derivation version 1, a byte-for-byte canonical
encoding, and a platform-stable SHA-256 derivation whose first eight digest
bytes become the effective unsigned 64-bit seed. It also specifies retained
diagnostic evidence, validation-before-mutation, prefix/suffix resume rules, and
concrete evidence for the same seven shared acceptance tests.

This is a provisional, reversible, documentation-only candidate. It does not
implement derivation, authorize repeated stepping, select Contract B, or change
runtime code, tests, commands, dependencies, product behavior or identities,
branching, persistence, replay schema, core philosophy, or the existing
transition and history seams.
