# Deterministic transition seed candidate proposal

This proposal makes Contract B from
[the repeated-step seed contract comparison](repeated_step_seed_contracts.md)
concrete enough for one later, bounded experiment. It is provisional,
reversible, and documentation-only. It does not implement deterministic seed
derivation, authorize repeated stepping, select Contract B, or establish a
project-wide seed, replay, identity, persistence, or branching contract. The
candidate choices below may be discarded after an experiment measures them.

The candidate would only derive an integer passed to the unchanged
`apply_transition` seam. It leaves `apply_transition`,
`SourceLinkedHistory`, `ReplayRecord`, runtime code, tests, commands,
dependencies, product behavior, product identities and branching, persistence,
the replay schema, core philosophy, and the eventual Contract A/Contract B
choice unchanged.

## Candidate-local inputs and bounds

A complete candidate run has these retained inputs in addition to the unchanged
initial `GenericIntegerState` and `TransitionConfiguration`:

- `run_seed`: an integer in the inclusive range `0` through
  `18_446_744_073_709_551_615` (`2^64 - 1`). A Boolean is not an integer for
  this purpose.
- `derivation_version`: the integer `1`. Booleans, numeric strings, and every
  other integer are unsupported rather than coerced or treated as aliases.
- `identities`: an immutable, nonempty ordered sequence. Each item has exactly
  `step_id` and `stream_id`.

Each `step_id` is an integer in the same unsigned 64-bit range, excluding
Booleans. In a complete run, step identities are exactly `0, 1, ..., n - 1` in
that order. They name candidate-local logical calls to `apply_transition`; they
are not state ticks, event identifiers, event positions, implicit call counts,
or product action identities.

Each `stream_id` is the exact ten-ASCII-byte string `transition`. The candidate
has one seed-consuming seam, so other strings and other Unicode values are
unsupported. Keeping the stream explicit tests separation from a possible
future randomness consumer without proposing a product-wide stream vocabulary.

The maximum step bound makes every field's byte representation total even
though no practical in-memory candidate run could approach that many steps.
These bounds and identities belong only to derivation version 1 of this
candidate.

## Exact version 1 derivation

Version 1 derives one seed independently for each retained identity. Its
canonical input is the following byte concatenation, in exactly this order:

1. The 20 ASCII bytes `2084.seed-derivation`, followed by one zero byte. The
   resulting 21-byte domain prefix in hexadecimal is
   `323038342e736565642d64657269766174696f6e00`.
2. `derivation_version`, encoded as exactly 4 bytes, unsigned, big-endian. For
   version 1 these bytes are `00000001` in hexadecimal.
3. `run_seed`, encoded as exactly 8 bytes, unsigned, big-endian.
4. `step_id`, encoded as exactly 8 bytes, unsigned, big-endian.
5. The byte length of `stream_id`, encoded as exactly 2 bytes, unsigned,
   big-endian. For `transition` these bytes are `000a`.
6. `stream_id`, encoded as strict ASCII. For `transition` these bytes are
   `7472616e736974696f6e` in hexadecimal.

There are no separators, terminators, whitespace, JSON, locale-sensitive
numbers, native-endian values, Unicode normalization, or optional fields beyond
the bytes specified above. Thus every valid version 1 derivation input is
exactly 53 bytes.

Compute SHA-256 over those 53 bytes. The effective transition seed is the first
8 digest bytes, interpreted as one unsigned, big-endian integer. Its inclusive
output range is therefore `0` through `2^64 - 1`. The remaining 24 digest bytes
are ignored. The candidate passes that integer directly to the existing
`apply_transition` seed parameter.

For a fixed version 1 vector with `run_seed = 0`, `step_id = 0`, and
`stream_id = "transition"`, the canonical input, full SHA-256 digest, first
eight digest bytes, and effective seed are respectively:

```text
323038342e736565642d64657269766174696f6e000000000100000000000000000000000000000000000a7472616e736974696f6e
063df7b7b36108532c94ff2752fc84615281b1321b1cbfe657c5edf31d9c74bb
063df7b7b3610853
449787906167474259
```

SHA-256 is selected only because its digest is defined over bytes, is stable
across platforms, and is available in Python's standard library. This proposal
does not rely on collision resistance for metadata validation and does not
claim that SHA-256 or a 64-bit output should become permanent architecture.

The version number selects the complete algorithm, domain prefix, encoding,
bounds, and output rule as one indivisible contract. An implementation supports
only version 1. It must reject an absent or unsupported version before deriving
or mutating history; it must not fall back to the newest version. A future
version would require a separate explicit specification and retained version
value. It must not reinterpret records labelled version 1.

## Fresh execution and retained diagnostic evidence

A fresh candidate execution would validate the complete initial state,
configuration, run seed, version, and ordered identity sequence before creating
or appending objective history. It would then derive each effective seed solely
from the retained metadata for that item, call `apply_transition` once, and
chain the returned immutable state into the next call.

The candidate would retain immutable run metadata and an immutable transition
trace adjacent to, but not inside, objective history. Every trace item exposes:

- the exact `run_seed` and `derivation_version`;
- the exact `step_id` and `stream_id`;
- the derived effective unsigned 64-bit seed; and
- the exact objective event returned by `apply_transition`.

This is development diagnostic evidence, not an agent observation and not a
proposed `ReplayRecord` or `WorldEvent` field. Reproduction compares retained
metadata exactly before execution, then compares final state, complete ordered
objective events, and complete trace items. Metadata equality is not inferred
from effective-seed or transition-result equality. Consequently, changing the
run seed or another metadata field is detected even if a derived seed happens
to select the same configured delta, and even in the theoretical case that two
different derivation inputs have the same 64-bit output.

No hidden entropy, wall-clock value, process identity, runtime string or object
hash, platform byte order, mutable pseudo-random-generator state, or prior
derivation call is an input. Each identity can be derived alone in any order.

## Prefix and suffix resume

For a split after `k` completed transitions, where `0 <= k <= n`, a resumable
candidate boundary retains:

- the original run seed, derivation version, initial state, and configuration;
- the original complete ordered identity sequence;
- the resulting immutable state and complete objective history for steps before
  `k`; and
- the `k` immutable trace items for the prefix.

The unused suffix begins with its original step `k` and is never renumbered.
Before mutation, resume validates the entire retained boundary: version and
bounds, complete identity order, prefix length, every prefix trace's exact
metadata and re-derived effective seed, trace-to-event equality, and agreement
between the prefix result state and its final event. Validation also checks that
the suffix is exactly the unused portion of the original identity sequence.

After preflight, each suffix seed is derived directly from the original run
seed, version, and unchanged identity. Resume does not reconstruct, skip, or
advance hidden generator state. The zero-length prefix uses the original state
with empty history and traces; an empty suffix is an already-complete resume.
The resulting final state, complete history, and traces must equal
uninterrupted execution from the same complete inputs.

These are in-memory candidate rules. They do not define checkpoint storage,
portable persistence, branch identity, or equality across product runs.

## Validation before mutation

All candidate inputs and retained resume or reproduction evidence are validated
in a distinct preflight phase. Structural metadata validation occurs before any
derivation. Re-derivation needed to validate retained seed evidence remains part
of preflight. No `apply_transition` call, history construction, or
objective-event append may occur until the entire preflight succeeds. At
minimum, preflight rejects:

- missing or extra fields, wrong collection shapes, or an empty fresh identity
  sequence;
- a Boolean, non-integer, negative, or out-of-range run seed or step identity;
- a missing, non-integer, or unsupported derivation version;
- a non-string or unsupported stream identity;
- duplicated, skipped, or reordered steps;
- supplied metadata that differs from same-position retained metadata or trace
  evidence, without consulting derived behavior;
- a retained effective seed that differs from version 1 re-derivation; and
- inconsistent prefix length, result state, objective history, trace, or suffix
  evidence.

Diagnostics should identify the failing collection index or resume boundary,
field, supplied value, and expected candidate rule. A valid execution that
differs from retained result evidence should identify the first different step
and stream and expose immutable recorded and reproduced inputs, effective seed,
event, and trace evidence. These diagnostics grant no agent access to
omniscient history and do not authenticate jointly rewritten records.

## Mapping to the seven shared acceptance tests

One later implementation would need to demonstrate the same seven observable
tests from the comparison note:

1. **Equal complete inputs:** execute equal initial state, configuration, run
   seed, version, and identities against fresh histories; assert equal final
   states, ordered objective events, effective seeds, and traces. Include fixed
   byte-vector and digest-prefix examples so encoding errors cannot pass merely
   through self-consistency.
2. **Changed seed metadata:** alter each of run seed, version, step, and stream
   metadata against unchanged retained evidence and assert rejection before
   execution. Include a changed run seed whose effective transition behavior
   collides under `seed % len(deltas)`; exact metadata comparison must still
   reject it. Unsupported versions and streams are validation errors.
3. **Prefix resume:** compare uninterrupted execution with an interior prefix
   plus resume, as well as empty-prefix and empty-suffix cases. Assert unchanged
   original step identities and equal suffix seeds, states, histories, and
   traces.
4. **Randomness isolation:** add unrelated standard-library randomness calls
   before and between derivations and derive identities in a different order;
   assert unchanged per-identity effective seeds and transition results.
5. **Inspectability:** for every event, assert that the same-position trace
   exposes the exact run seed, version, step, stream, derived seed, and returned
   event, and that the seed matches independent canonical-byte derivation.
6. **No hidden inputs:** vary hash randomization and global random state, make
   entropy, clock, and process-identity access fail if called, and compare fixed
   vectors across supported platforms; results must depend only on the 53
   canonical bytes.
7. **Failure before mutation:** exercise missing, malformed, duplicated,
   unsupported, out-of-range, changed, and prefix/suffix-inconsistent metadata;
   assert for every case that no transition call occurs and the pre-existing
   objective-event tuple remains unchanged. Structurally invalid metadata must
   also fail before derivation; retained-seed inconsistency may be found by
   re-derivation but must still fail before transition or history mutation.

Passing those tests would give this candidate bounded Contract B evidence. It
would not select Contract B over Contract A, prove a permanent identity or
branch model, or authorize changes to replay or product behavior.

## Questions intentionally left open

- Should the project ultimately retain explicit per-transition seeds or adopt
  any stable, versioned derivation contract?
- Would a permanent contract use this algorithm, encoding, version vocabulary,
  or integer range?
- What product step, stream, run, and branch identities would represent real
  actions and multiple randomness consumers?
- How should durable replay retain initial state, checkpoints, derivation
  evidence, and authorization for omniscient diagnostics?
