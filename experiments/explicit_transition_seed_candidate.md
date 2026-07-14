# Explicit per-transition seed candidate proposal

This proposal makes Contract A from
[the repeated-step seed contract comparison](repeated_step_seed_contracts.md)
testable in one later, bounded experiment. It is not an implementation, a
selection of the project's seed contract, or permanent replay, identity, or
branch architecture. Contract B remains open. The local choices below may be
discarded after the candidate is tested.

The candidate would only coordinate repeated calls to the unchanged
`apply_transition`. It would not change that function, the replay record's
shape or version, source-linked history, dependencies, commands, or runtime
behavior. It would add no product scenario or agent-facing behavior.

## Candidate-local vocabulary

One **transition input** has exactly these conceptual fields:

- `step_id`: a nonnegative integer. In a complete candidate run, step
  identities are `0, 1, ..., n - 1` in that order. They identify logical calls
  to `apply_transition`; they are not state ticks, event identifiers, event-list
  positions, or values inferred from any of those.
- `stream_id`: the exact string `transition`. The candidate has only the one
  existing seed-consuming transition seam. Keeping this field explicit tests
  the stream boundary without inventing a multi-stream design.
- `seed`: an integer accepted by the existing transition seam. A Boolean is not
  an integer for this purpose.

The **ordered transition inputs** are an immutable, nonempty sequence of those
items. The sequence order is authoritative, but each item's explicit identity
must also agree with its position. Reordering therefore fails validation rather
than silently changing the meaning of a position. A repeated-step acceptance
example should contain at least two items even though the vocabulary also
describes a one-item boundary case.

These are deliberately narrow experiment rules. In particular, zero-based
integer steps and the literal stream name do not settle how a later simulation
would identify actions, simultaneous transitions, subsystems, or persisted
records.

## Fresh execution and retained evidence

A fresh candidate execution would receive an immutable initial
`GenericIntegerState`, one immutable `TransitionConfiguration`, and the complete
ordered transition-input sequence. It would start with a fresh
`SourceLinkedHistory`, validate all inputs, and then call `apply_transition`
once per item, passing only that item's integer seed through the existing seam.
The next state from one call becomes the state for the next call.

The candidate would retain or return an immutable **transition trace** adjacent
to, but not inside, objective history. Each trace item contains the `step_id`,
`stream_id`, effective `seed`, and the exact objective event returned by that
call. This is experiment diagnostic evidence, not an observation available to
an agent and not a proposed change to `ReplayRecord` or `WorldEvent`.

For reproduction, the retained initial state, configuration, ordered inputs,
objective events, and trace items are the complete comparison evidence. A
reproduction succeeds only when its complete resulting state, ordered objective
events, and transition traces equal the retained evidence. Exact trace
comparison detects changed seed metadata even when two integer seeds happen to
select the same configured delta.

No seed allocation policy is part of the candidate. The caller supplies every
seed, and the coordinator must not consult hidden entropy, time, process state,
runtime hashing, or mutable generator state.

## Prefix and suffix resume

For a split after `k` successful transitions, where `0 <= k <= n`, a resumable
prefix consists of:

- the resulting immutable state;
- the complete objective history after the prefix;
- the `k` immutable trace items for steps `0` through `k - 1`; and
- the unused original transition-input suffix beginning with step `k`.

The suffix keeps its original step identities. It is never renumbered to start
at zero. Before a resumed call mutates history, candidate validation checks the
whole retained boundary: the prefix trace identities are exactly `0` through
`k - 1`, each prefix trace event equals the objective event at the same prefix
position, the resulting state's tick and value agree with the last prefix
event when the prefix is nonempty, and suffix identities are exactly `k`
through `n - 1`. The zero-length prefix uses the original initial state and an
empty history and trace; an empty suffix is an already-complete resume.

After validation, resume applies the suffix items in order to the retained
state and history. Its final state, complete history, and appended trace suffix
must equal uninterrupted execution from the same complete inputs. Resume does
not reconstruct or advance any implicit randomness state.

This is an in-memory experiment boundary, not a checkpoint file or portable
resume schema. It does not resolve how a future durable record should encode
initial state or diagnostics.

## Validation and diagnostics

Validation is a distinct preflight phase over the complete candidate input or
resume boundary. No call to `apply_transition` and no objective-history append
may occur until preflight succeeds. At minimum, preflight rejects:

- a missing required field, an extra field, a non-sequence input collection,
  or an empty fresh-run collection;
- a Boolean or other non-integer step or seed, a negative step, or an empty or
  non-string stream;
- a duplicated, skipped, or reordered step identity;
- any stream identity other than the candidate's supported `transition`
  stream;
- reproduction inputs whose step, stream, or seed metadata disagrees with the
  same-position retained trace item;
- a prefix trace whose metadata or event disagrees with its matching input or
  objective event; and
- a resume state, prefix length, or suffix boundary inconsistent with the
  retained prefix evidence.

An input error should identify the collection index when available, the
offending field, the supplied value, and the expected candidate rule. A valid
reproduction that differs from retained evidence should identify the first
different step and stream and expose the supplied seed plus immutable recorded
and reproduced event and trace evidence. These diagnostics are development
inspection data; they grant no agent access to omniscient history.

The candidate is not tamper-proof storage. Its consistency checks localize
accidental or test-induced metadata changes; they do not authenticate a record
whose inputs and comparison evidence were all rewritten together.

## Branch boundary

No branch identity is needed to test explicit seeds. A candidate branch is a
separate execution that copies an exact validated prefix and supplies a
different explicit suffix. Shared prefix items and traces remain equal; the
first different suffix item identifies the branch point. Step identities and
the `transition` stream identity keep their original meanings on both runs.

This local rule must not be generalized silently. Whether durable replay needs
a branch identity, and whether equal step and stream identities in different
runs name the same logical transition, remain open questions.

## Evidence required from a future experiment

The seven shared acceptance tests in the comparison note map to the following
concrete evidence for this candidate:

1. **Equal complete inputs:** execute the same initial state, configuration,
   and ordered inputs twice against fresh histories; assert equal final states,
   complete ordered objective-event tuples, and complete trace tuples.
2. **Changed seed metadata:** change the seed in one copied input item while
   leaving its retained trace evidence unchanged; assert rejection before any
   event append, including when the changed seed selects the same delta. Also
   exercise changed, reordered, and duplicated step or stream metadata.
3. **Prefix resume:** for at least one interior split `k`, compare uninterrupted
   execution with prefix execution followed by resume; assert equal final
   states, complete histories, and trace suffixes, with the first resumed item
   still identified as step `k`.
4. **Randomness isolation:** perform unrelated standard-library randomness
   calls before and between candidate transitions; assert that the final state,
   events, and traces remain equal because every transition receives its own
   retained integer seed.
5. **Inspectability:** for every objective event, assert that the same-position
   trace exposes the exact step, `transition` stream, effective seed, and event
   returned by `apply_transition`.
6. **No hidden inputs:** make entropy and wall-clock access fail if called,
   perturb process-global random state, and run with differing hash seeds;
   assert unchanged results and no attempted hidden-input access. Source
   inspection should also show direct use of retained seeds with no generator
   state carried between calls.
7. **Failure before mutation:** separately supply missing, malformed,
   duplicated, unsupported, and prefix/suffix-inconsistent metadata; for every
   case assert the pre-existing objective-event tuple is exactly equal before
   and after the failed call and that the diagnostic locates the field or
   boundary.

Passing these tests would show only that this explicit-seed candidate satisfies
the bounded contract. It would not prove that Contract A is preferable to
deterministic derivation or that these identity and resume semantics belong in
the permanent architecture.

## Questions intentionally left open

- Should the project ultimately retain explicit per-transition seeds or adopt
  a stable, versioned derivation contract?
- What step and stream identity vocabulary could represent real simulation
  actions or multiple random consumers?
- Does durable branching require a branch or run identity, and what should
  identity equality mean across branches?
- How should a portable replay represent initial state, resume checkpoints, and
  diagnostics without making this generic integer experiment permanent?
- Which application boundary may inspect complete traces and objective history?
