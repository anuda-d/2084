# Repeated-step seed contract comparison

This note is a bounded design exercise for a possible repeated-step experiment.
It compares two contracts for supplying the existing single-transition seam with
an integer seed. It does not select a contract, define a derivation algorithm,
or authorize repeated stepping. `apply_transition` remains unchanged and still
accepts one explicit integer seed for one transition.

## Common boundary

Under either contract, a replay must retain the immutable initial state, the
complete immutable transition configuration, and the ordered objective events
used to verify the result. Every transition also needs an explicit step identity
and randomness-stream identity. A step identity identifies the logical
transition, not merely the current event-list length. A stream identity keeps
independent uses of randomness distinct if later experiments add more than one
use per step.

The retained metadata described below is part of the complete replay input. It
must be validated before any history mutation. Transition events or adjacent
diagnostic records must expose the effective seed and the inputs that selected
or derived it, so a mismatch can be localized to a particular transition.

## Contract A: explicit seed per transition

Retained inputs are the initial state, transition configuration, and an ordered
transition-input sequence. Each item in that sequence contains exactly a step
identity, stream identity, and integer seed. Replay uses those retained values
directly; it does not infer a seed from position, time, process state, or prior
pseudo-random-number-generator state.

- **Deterministic replay:** A fresh replay supplies the recorded seed for each
  matching step and stream. Complete equal inputs should produce equal ordered
  objective events.
- **Prefix and suffix resume:** A resumable prefix must retain its resulting
  state and objective history plus the unused suffix of transition inputs. The
  first resumed item must still carry its original step, stream, and seed; list
  renumbering must not change it.
- **Branching:** A branch can copy a prefix and then retain a different explicit
  seed sequence for its suffix. Equal prefix inputs remain directly comparable,
  while the first differing item identifies where the branches separate.
- **Inspectability:** The effective integer seed is already present for every
  transition, alongside its step and stream identities. No derivation needs to
  be reconstructed.
- **Mismatch and failure diagnosis:** Missing, duplicate, reordered, or changed
  transition items are metadata errors. If valid metadata produces a different
  event, diagnostics can report the step and stream, supplied seed, and the
  recorded and reproduced events.

This contract retains more per-transition data and requires callers to own seed
allocation. That allocation policy would remain a separate open design question.

## Contract B: deterministic seed derivation

Retained inputs are the initial state, transition configuration, one integer run
seed, a derivation-contract version, and the ordered transition identity
sequence. Each identity item contains exactly a step identity and stream
identity. Replay derives the effective integer seed from the retained run seed,
derivation version, step identity, and stream identity, then passes that integer
to the unchanged single-transition seam.

The derivation must be a stable, explicitly versioned contract whose results do
not vary by language runtime, process, platform, or library upgrade. This note
does not choose its algorithm or encoding. Runtime-specific or unstable hashing,
including default language object/string hashes, is not acceptable. Neither is
an unspecified PRNG state advanced by call order. Encoding, integer bounds, and
version behavior would have to be fixed before this contract could be
implemented.

- **Deterministic replay:** A fresh replay derives each effective seed from the
  same complete retained inputs. Complete equal inputs should produce equal
  ordered objective events.
- **Prefix and suffix resume:** A resumable prefix must retain its resulting
  state and objective history plus the original run seed, derivation version,
  and unused ordered identity suffix. Resuming at an identity must derive the
  same effective seed without consuming or reconstructing hidden generator
  state.
- **Branching:** A branch can copy a prefix and use a different explicit step or
  stream identity in its suffix. Whether a future design needs a separate branch
  identity is unresolved; it must not be smuggled into process-local state or
  call order.
- **Inspectability:** Each transition must expose the run seed, derivation
  version, step identity, stream identity, and resulting effective integer seed.
  A version label alone is not enough to diagnose a result.
- **Mismatch and failure diagnosis:** Missing, duplicate, reordered, changed, or
  unsupported identity/version metadata are errors. If valid metadata derives a
  different seed or event, diagnostics can identify the exact derivation inputs,
  effective seed, and recorded and reproduced events.

This contract retains less seed data per transition but makes the derivation
algorithm, encoding, versioning, and identity scheme part of the replay contract.

## Observable acceptance tests for either contract

Any future repeated-step seed contract must demonstrate all of the following:

1. The same complete inputs produce an identical ordered sequence of objective
   events when executed against a fresh history.
2. Changed seed metadata is detected rather than silently accepted. For the
   derived contract, seed metadata includes the run seed, derivation version,
   step identity, and stream identity.
3. Replaying a prefix and then resuming produces the same suffix as uninterrupted
   execution from the same complete inputs.
4. Unrelated consumers of randomness cannot perturb transition results.
5. The effective seed and all selection or derivation inputs for every
   transition are inspectable.
6. No result depends on hidden entropy, wall-clock time, process identity,
   runtime hash randomization, or implicit mutable generator state.
7. Missing, malformed, duplicated, unsupported, or inconsistent seed metadata
   fails before objective history is mutated.

These tests describe observable evidence, not a preference between the
contracts. The choice remains unresolved. A later repeated-step experiment must
first specify its identity and resume semantics and can then test one contract
without changing the existing single-transition boundary.
