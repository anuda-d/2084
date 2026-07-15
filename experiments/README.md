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

## Provisional focal-life scenario

`focal_life_scenario.py` composes source-linked history into one deterministic,
ordinary allocation example. A provisional focal character directly sees two
units while an official notice claims four are available. The objective record
also retains one prior commitment that is not delivered to the character. A
transparent rule prefers direct availability evidence, then caps a request by
the observed value, the character's need, and its request limit. The decision
accepts only the character's filtered observations and those need constraints;
its trace retains the observation identifiers and values it used.

World resolution is separate from request selection. It records the attempted
request, limits the grant using objective shelf and commitment values, records
the resulting grant and shortfall, and delivers the handover result to the
focal character. Invalid or Boolean request quantities are rejected before any
resolution event is recorded. A second public decision then uses only the
character's filtered observations and the same need. Its provisional local rule
waits when no handover was delivered, seeks the remaining allocation after a
partial handover, and otherwise continues an ordinary task. The decision trace
retains the selected handover observation, observed grant, need, remaining
amount, and rule; it does not declare that the later choice succeeds. A public
follow-up resolver separately records the selected attempt and its outcome. It
links the attempt to the selected handover and prior consequence, then computes
remaining allocatable supply from the original objective allocation minus the
prior grant. In the fixed example, the first grant exhausted that supply, so
the later request receives zero units and leaves two unfilled.

The focal character receives a source-linked follow-up outcome containing only
the understandable grant and shortfall. Objective shelf, commitment, and
remaining-allocation values remain in omniscient event evidence rather than in
the delivered observation. The resolver validates its public inputs and all
linked allocation, prior-resolution, handover, and decision evidence before it
appends either follow-up event; corrupt or inconsistent evidence therefore
cannot leave a partial attempt in history.

One provisional supporting person separately receives only a source-linked view
that the focal character visibly requested two units. This view omits the focal
need, both allocation outcomes, objective supply, commitment, and hidden focal
state. The supporting decision's local rule urges public agreement after a
positive visible request and takes no social action when that observation is
absent. The supporting person does not need to know what the official notice
claimed. A separate resolver validates the decision against its recorded
observation and source event before recording the action; inconsistent evidence
fails before history mutation. Only the understandable generic action is then
delivered to the focal character as social pressure, not the supporter's
observation or reasoning trace.

A third public decision carries the delivered outcome and any delivered social
pressure forward without reading objective allocation state. Its immutable
trace retains both selected observation identifiers, the understandable grant,
shortfall and pressure action, the
resulting constraint, and its local rule. Under the same zero-unit grant and
two-unit shortfall, absence of pressure yields `wait_for_changed_conditions`,
while delivered pressure yields `seek_alternative_source`. A delivered
sufficient outcome instead produces no remaining constraint and
`continue_ordinary_task`.

The pressured fixed run resolves `seek_alternative_source` separately from that
decision. A local, explicitly provisional objective event limits this worked
alternative source to one available unit. Before mutation, the public resolver
validates the decision, its selected delivered follow-up outcome and matching
social pressure, and the recorded objective constraint. It then records the
two-unit attempt and a separate consequence granting one unit and leaving one
unfilled. Corrupt or inconsistent inputs append neither event. The focal
character receives only a source-linked result observation containing that
grant and shortfall; the source constraint, its event identity, allocation
inputs, selected observation identifiers, and decision trace remain hidden.
Without delivered pressure, the third choice remains
`wait_for_changed_conditions` and no alternative-source attempt or outcome is
recorded. The names, quantity, source limit, and rule are one reversible worked
example rather than permanent worldbuilding or a general source model.

The fixed scenario then records one same-proposition comparison. Narrow
immutable objective evidence says that two units were available and links to
the original allocation event. A separate private belief retains the two-unit
value and links only to the focal character's delivered direct observation. A
public-expression decision receives only the focal character's delivered
observations: with delivered pressure it repeats the delivered four-unit
official claim while preserving the private belief; without pressure it
expresses the private two-unit value. The public runner exposes this comparison
through `run_provisional_focal_life_scenario(include_public_pressure=False)`.

The decision cannot append its own expression event. A separate resolver checks
the recorded direct, official, and pressure observations against their source
events, checks the decision against that exact evidence, and validates timing
before mutation. The resulting event retains links to the private source,
official source, pressure, and underlying objective availability event. Corrupt
or inconsistent input fails before an expression is recorded. The objective
allocation event is unchanged by either the pressured or unpressured run.

After the tick-5 public expression, the focal character writes the retained
two-unit private belief into one diary physically carried by that character.
The public write action requires possession, starts at tick 6, completes at
tick 7, and rejects invalid or inconsistent delivered perspective evidence
before recording an event. The immutable entry retains only its private-
perspective label, proposition, value, source observation, author, and writing
times; it does not copy shelf, commitment, allocatable-supply, raw-event, or
objective-record fields. A later public read action also requires physical
access and returns that exact retained entry at tick 8. The diary itself has
only a stable provisional object identifier, one location/possessor fact, and
its entry tuple; this is deliberately not a general object or inventory model.

Tests independently vary delivered partial, sufficient, and absent handovers to
show that the later choice changes with perceived consequences rather than a
prescribed story. They also exercise invalid public inputs. Run the
standard-library test command above, or just this scenario's tests:

```bash
python3 -m unittest experiments.tests.test_focal_life_scenario
```

A bounded normal-perspective transcript makes the fixed sequence watchable from
the repository root:

```bash
python3 -m experiments.focal_life_observer
```

The transcript shows the focal need and request limit, source-linked direct and
official observations, all focal choices, all three delivered allocation
outcomes, the focal-visible social pressure and its effects, retained private
belief, and public expression. It then shows private-perspective diary writing with time
advancing and the later read returning the same retained entry. After that read,
the fixed scenario appends a tick-9 official claim revising the earlier official
four-unit claim to one unit. The new claim explicitly links to the earlier claim
event, and the focal character receives it only through a source-linked official
revision observation. The earlier claim, objective shelf event, private belief,
public expression, and diary entry remain unchanged and separately inspectable.
The transcript presents the revised value as a claim received from its official
source rather than as objective truth. The normal perspective does not expose
objective truth or event identifiers, the
supporter's source observation or local rule, objective commitment or
allocatable-supply values, the raw omniscient event stream, or why the delivered
supply was constrained. The separate objective availability record and its
provenance remain available only through the scenario's returned development
evidence and tests. This boundary is covered through the public transcript
renderer and runnable module command using only the Python standard library.

The character, location vocabulary, quantities, commitment, evidence priority,
allocation rule, supporting person, social action, public-expression rule,
follow-up choices, and responses are all provisional. This is one fixed scenario
with five decisions, three resolved allocation attempts, one resolved social
action, one resolved public expression, one diary write, and one diary read. It
is not a repeated loop, general belief or memory update, confidence or decay
model, institution model, object/inventory system, diary lifecycle, discovery,
concealment, confiscation, sharing, entry editing, UI, AI behavior,
persistence/replay format, permanent setting, or claim that a human mind is
being simulated. The later revision does not trigger reconsideration, and the
private belief does not update. The local pressure and
alternative-source rules demonstrate one divergence and outcome; they do not
prescribe resistance or any other story. The transcript is not a general
observer interface, authorization boundary, interactive view, or graphical UI.

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
