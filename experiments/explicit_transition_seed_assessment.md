# Explicit per-transition seed candidate assessment

This is a bounded post-experiment assessment of Contract A from the
[repeated-step seed contract comparison](repeated_step_seed_contracts.md). It
uses only the candidate implementation and tests already in this repository.
It does not select a permanent seed contract, define Contract B, or authorize
changes to replay, persistence, repeated product behavior, or identity design.

## Repository observations

The following are direct observations from the current files:

- [`explicit_transition_seed_run.py`](explicit_transition_seed_run.py) accepts
  an immutable sequence of explicit `step_id`, `stream_id`, and integer `seed`
  values, validates them, passes each retained seed directly to the unchanged
  `apply_transition`, and returns immutable state, objective events, and
  adjacent traces.
- The same module validates retained run boundaries before reproduction or
  resume, rebuilds a validated prefix through `SourceLinkedHistory`, preserves
  original suffix step identities, and distinguishes invalid input from a
  valid reproduction mismatch.
- [`test_explicit_transition_seed_run.py`](tests/test_explicit_transition_seed_run.py)
  contains named tests for each of the seven shared acceptance categories in
  the comparison note. These tests run under the repository's existing
  standard-library test command and `scripts/check.sh`.
- [`repeated_step_seed_contracts.md`](repeated_step_seed_contracts.md) describes
  the inputs and observable requirements for Contract B, but explicitly does
  not choose a derivation algorithm or encoding.
- There is no Contract B candidate proposal, derivation-contract version,
  fixed input encoding, integer-range rule, seed-derivation implementation, or
  Contract B acceptance-test suite in the repository.

### Shared acceptance-test evidence

1. **Equal complete inputs produce equal ordered objective events.**

   - Contract A implementation evidence: `execute_explicit_transitions`
     validates the full input tuple, creates a fresh `SourceLinkedHistory`, and
     uses `_execute_validated` to return the final state, ordered events, and
     traces.
   - Contract A test evidence:
     `test_equal_complete_inputs_have_equal_state_events_and_traces` executes
     equal complete inputs twice and compares final state, events, and traces.
   - Contract B status: the comparison states the required retained inputs and
     outcome, but no derivation implementation or fresh-run test exists.

2. **Changed seed metadata is detected rather than silently accepted.**

   - Contract A implementation evidence: `_normalize_item` and
     `_normalize_inputs` validate step, stream, and seed fields;
     `reproduce_explicit_transitions` compares every supplied metadata tuple
     with the retained trace before executing the reproduction.
   - Contract A test evidence:
     `test_changed_metadata_is_rejected_before_reproduction` covers changed
     seeds even when modulo selection would produce the same delta, plus
     duplicated, skipped, and changed step or stream metadata.
   - Contract B status: the comparison says a run seed, derivation version,
     step identity, and stream identity are seed metadata, but none can be
     validated because there is no concrete version or implementation.

3. **Prefix replay followed by resume matches uninterrupted execution.**

   - Contract A implementation evidence: `_validate_run_boundary` checks the
     retained prefix; `resume_explicit_transitions` requires the suffix to
     begin at the original next step, rebuilds the prefix history, and appends
     traces without renumbering.
   - Contract A test evidence:
     `test_interior_prefix_resume_preserves_original_steps_and_matches_full_run`
     compares an interior resume with an uninterrupted run and also covers
     empty-prefix and empty-suffix boundaries.
   - Contract B status: resume requirements are described, but there is no
     derivation function proving that a resumed identity yields the same seed
     without hidden generator state.

4. **Unrelated randomness consumers cannot perturb transition results.**

   - Contract A implementation evidence: `_execute_validated` passes
     `item.seed` directly to each `apply_transition` call and carries no random
     generator state.
   - Contract A test evidence:
     `test_unrelated_randomness_before_and_between_steps_is_isolated` perturbs
     Python's global random state before and between prefix and suffix work,
     then compares state, events, and traces.
   - Contract B status: the comparison rejects call-order-dependent generator
     state, but no derivation algorithm exists to test for isolation.

5. **The effective seed and its selection or derivation inputs are inspectable.**

   - Contract A implementation evidence: immutable `TransitionInput` and
     `TransitionTrace` values expose the step identity, stream identity, and
     effective integer seed; each trace also retains the matching event.
   - Contract A test evidence:
     `test_trace_exposes_exact_identity_seed_and_event_for_each_step` checks
     those fields for every objective event.
   - Contract B status: the required run seed, version, identities, and
     effective seed are listed in the comparison, but no trace or diagnostic
     representation implements them.

6. **Results do not depend on hidden environmental or mutable inputs.**

   - Contract A implementation evidence: the candidate module imports neither
     `random` nor `time`; the execution path uses the retained seed directly.
   - Contract A test evidence:
     `test_entropy_clock_global_random_and_hash_seed_are_not_inputs` changes
     global random and Python hash seeds, makes selected entropy and clock
     access fail if called, compares outputs, and checks direct seed use in the
     candidate source.
   - Contract B status: unstable hashes, hidden entropy, and implicit generator
     state are prohibited by the comparison, but no algorithm, canonical
     encoding, or version behavior exists to demonstrate platform-stable
     derivation.

7. **Invalid seed metadata fails before objective history is mutated.**

   - Contract A implementation evidence: fresh execution normalizes all inputs
     before creating history; reproduction validates the retained boundary and
     supplied metadata before executing; resume validates the complete prefix
     and suffix before rebuilding or appending history.
   - Contract A test evidence:
     `test_invalid_collections_and_boundaries_fail_before_any_mutation` covers
     missing and extra fields, malformed values, duplicate, skipped, reordered,
     and unsupported identities, and inconsistent state, event, trace, and
     suffix boundaries while asserting that transition or history mutation is
     not reached.
   - Contract B status: required failures are named in the comparison, but
     there is no supported version, metadata validator, derivation path, or
     history-boundary test against which to observe them.

## Interpretation

Contract A has bounded candidate evidence for all seven shared acceptance
categories. That evidence supports the narrower statement that an explicit
seed per transition can coordinate this generic in-memory experiment while
preserving the existing transition and objective-history boundaries.

The evidence is not comparative. Contract B currently has requirements, not a
candidate whose behavior can be measured against the same tests. In
particular, the repository has no algorithm, canonical encoding, version
contract, implementation, or executable evidence for deterministic
derivation. The repository therefore is **not ready to select a project-wide
seed contract**. Contract A's passing candidate evidence is not evidence that
it is preferable to an unimplemented alternative.

## Limitations

- The candidate uses a generic integer state, one literal `transition` stream,
  zero-based sequential step identities, and in-memory evidence. Those are
  reversible experiment choices, not settled product vocabulary or schema.
- The tests exercise the current Python implementation and selected sources of
  hidden input. They do not prove portability across runtimes or establish a
  durable replay format.
- No seed-allocation policy, branch or run identity, durable checkpoint,
  multi-stream behavior, storage-cost comparison, or product action semantics
  is assessed.
- Contract B cannot receive a pass or fail result until its algorithm,
  encoding, integer bounds, version behavior, and candidate-local identity and
  resume rules are concrete enough to test.

## Smallest safe recommended next objective

Write a bounded Contract B candidate proposal, analogous in scope to the
Contract A proposal, that specifies one reversible derivation algorithm,
canonical input encoding, output integer bounds, derivation version behavior,
and candidate-local step, stream, and resume rules. Map that proposal to the
same seven acceptance tests, but do not implement it or select it as permanent
architecture in that objective. Product identity, branching, persistence, and
the eventual project-wide seed choice should remain open.
