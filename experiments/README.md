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

### Explicit limitations

The single integer transition is not a repeated simulation loop, decision or
action model, belief update, institution, diary behavior, scenario or setting,
UI, AI behavior, persistence format, replay file, or production package. Its
seed is a deterministic selector, not a claim about a future randomness
strategy. The transition records at the prior state tick plus one; this local
choice does not impose repository-wide monotonic event chronology.

The replay record replays recorded history; it does not reproduce decisions or
transitions from their inputs. Its structured-data shape is not a permanent
schema. Event and observation identifiers remain deterministic in-memory
counters, and details and configuration accept only scalar, mapping, and
sequence values that can be copied into immutable containers. Replay does not
settle authorization for omniscient history and projections.
