# Three-Slice Goal-Bounded Autonomous Development Loop

Status: current operating contract.

The loop advances one owner-approved goal through small, independently verified slices.
It is currently stopped and unauthorized.
The previous authorization record is historical evidence and does not activate this contract.

## Architecture

```text
scheduled liveness / recovery trigger
                |
                v
      orchestrator generation
       owns 0..3 accepted slices
                |
       freeze one slice contract
                |
       transfer checkout ownership
                v
         one fresh writer
          sole slice modifier
         /                  \
read-only explorers   fresh read-only reviewer
         \                  /
        implement -> validate -> review -> repair
                |
     accepted evidence and commit
                |
       return ownership and result
                |
       next slice, up to three
                |
       whole-goal alignment
                |
       compact durable handoff
                |
       fresh orchestrator generation
```

The scheduler is only a liveness and recovery trigger.
It does not select a slice, alter a goal, implement code, or create overlapping work.

The orchestrator owns goal interpretation, gap selection, frozen slice contracts, sequential delegation, result acceptance, and whole-goal alignment.
One orchestrator generation may accept at most three slices.
It does not implement product code.

Each slice receives one fresh writer.
That writer is the sole repository modifier from checkout transfer until the accepted commit or terminal handback.
The writer may delegate bounded read-only exploration and must obtain a fresh read-only review after validation.

## Sources of Authority

Read these sources in order:

1. `AGENTS.md`;
2. `docs/plans/CURRENT.md`;
3. `docs/plans/AUTONOMOUS_LOOP_STATE.json`;
4. this contract;
5. the owner-approved active goal and its implementation evidence when authorization is standing;
6. the latest compact handoff when it exists; and
7. only the source and tests required by the frozen slice.

Repository code, committed evidence, and `AUTONOMOUS_LOOP_STATE.json` are authoritative.
A temporary handoff is context only.
It never grants authority, changes a goal, weakens a gate, or queues future work.

## Runtime State Machine

All lifecycle changes use `scripts/autonomous_loop_state.py`.
The CLI validates the complete state before and after mutation, writes atomically, and requires checkout ownership.
Every mutation supplies the expected revision and a unique event identifier.
A retry with the same event identifier is idempotent.
A stale revision or reused event identifier fails closed.

```text
stopped
  -> ready
  -> contracted
  -> implementing
  -> validating
  -> reviewing
       -> repairing -> validating
       -> ready after accepted slice 1 or 2
       -> alignment_required after accepted slice 3
  -> aligning
  -> handoff_ready
  -> fresh generation at ready
```

`blocked` and `needs_owner_decision` are terminal recovery states.
An incomplete slice stays in its exact phase and retains its frozen contract.
It never counts toward the three-slice limit.

## Authorization and Activation

The runtime state is initially `stopped` with no active goal and no authorization.
Historical goal files cannot activate it.

Activation requires all of the following:

- an explicit owner instruction selecting exactly one goal;
- owner confirmation recorded by the administrative activation event;
- synchronized human-readable goal and implementation evidence;
- the exact saved automation updated to active only after repository activation is committed; and
- no conflicting or unreadable owner or runtime state.

Agents may not infer activation from an old goal status, a scheduler trigger, a handoff, or unfinished product evidence.

## Scheduler Contract

The `autonomous-2084-development-loop` automation runs only as a liveness and recovery trigger during the configured window.
On every trigger it validates runtime state and ownership before doing anything else.

The scheduler no-ops when:

- runtime state is stopped or unauthorized;
- the saved automation is paused;
- another valid orchestrator or writer owns the checkout;
- an active actor is non-terminal or awaiting input;
- state or ownership is unreadable or inconsistent;
- a blocker or owner decision is recorded; or
- current time does not permit a new generation and no incomplete slice requires safe recovery.

The scheduler may create a fresh orchestrator only when authorized state is `ready` without an orchestrator or `handoff_ready` after a completed alignment.
It may recover an exact recorded orchestrator or writer only after the exact task is verified `completed`, `failed`, or `interrupted`.
It never creates a second writer or substitutes a different slice.

## Checkout Ownership

Read-only orientation does not require checkout ownership.
Immediately before the first repository write, run `python3 scripts/autonomous_loop_lock.py acquire` with the actor role and generation scope.

The durable lock records task identity, role, generation, optional slice, claim token, and recovery evidence.
The current owner must assert ownership after a resumed turn and immediately before commit.

The orchestrator freezes the slice contract while it owns the checkout.
It then atomically transfers checkout ownership to the named fresh writer with `autonomous_loop_lock.py transfer`.
The orchestrator performs no repository mutations while the writer owns the checkout.

After acceptance and commit, the writer transfers ownership back to the same orchestrator generation.
After alignment, the orchestrator releases ownership before a fresh generation begins.

The unscoped Codex task listing is not an ownership precondition.
Do not call `list_threads` as part of the no-overlap gate.
If acquisition reports another owner, inspect only that exact task with `read_thread`.
Active, unknown, unreadable, or non-terminal owners continue to block recovery.
Lock age never authorizes recovery.

## Orchestrator Generation

An orchestrator generation begins with one fresh orchestrator and an accepted-slice count of zero.
The orchestrator performs these steps sequentially:

1. inspect current goal evidence and identify one smallest unmet gap;
2. define a complete frozen slice contract;
3. create one fresh writer for that slice;
4. record the writer in runtime state;
5. transfer checkout ownership to the writer;
6. wait for a compact accepted or terminal result;
7. verify the result matches runtime state and committed repository evidence;
8. accept another slice only when fewer than three have been accepted; and
9. perform whole-goal alignment immediately after the third accepted slice or earlier at goal completion.

The orchestrator does not preselect later slices or persist a future task queue.
It chooses each next slice from repository evidence after the preceding slice is accepted.

## Frozen Slice Contract

The orchestrator writes the complete contract before delegating the writer.
The state machine stores the contract and its canonical SHA-256 digest.
Any later contract mutation invalidates the state.

Every contract contains exactly:

- one goal criterion;
- one intended observable result;
- one evidence claim;
- an explicit file or subsystem scope;
- one or more `check` and `expect` gates; and
- focused and full validation commands.

The writer may report that a contract is impossible or requires an owner decision.
The writer may not weaken, delete, reinterpret, or replace a gate.

## Writer Slice

The fresh writer begins only after the runtime state names it and checkout ownership has transferred.
The writer owns exactly one slice.

The writer:

1. reads the frozen contract and relevant implementation;
2. may delegate one to three concrete read-only exploration questions;
3. implements only the contracted change;
4. runs every frozen gate and focused validation;
5. runs `./scripts/check.sh`;
6. records factual validation evidence;
7. obtains a fresh read-only reviewer that is neither the writer nor orchestrator;
8. resolves every blocking finding with the same writer;
9. repeats focused and full validation after material correction;
10. obtains another fresh review after material correction;
11. asserts ownership and commits the reviewed coherent implementation;
12. records acceptance only when the supplied accepted commit is the exact current `HEAD`;
13. commits the runtime acceptance transition; and
14. transfers ownership and a compact result back to the orchestrator.

A reviewer inspects the frozen claim, actual diff, test evidence, failure paths, and relevant product invariants.
A reviewer cannot edit, commit, change the contract, select a new slice, or grant product authority.

## Acceptance and Retry Bounds

A slice counts toward the generation only when:

- its contract digest still matches;
- every frozen gate has the stated observable result;
- focused validation passes;
- the complete repository check passes;
- a fresh independent review has no blocking finding;
- every material correction was revalidated and freshly reviewed; and
- the coherent implementation commit exists before the accepted-slice count advances.

The subsequent runtime-state commit records the accepted evidence and exact implementation commit.

Missing evidence is failure, not partial acceptance.
An incomplete or rejected slice contributes zero to the accepted-slice count.

The same writer receives no more than two repair cycles after blocking review.
The exact slice may receive no more than three writer attempts across verified crash recovery.
Exhausting either bound records `blocked` and stops automatic progress.

## Recovery

Recovery first validates state and reads the durable checkout owner.
It then inspects only the exact recorded task.

Recovery requires:

- a latest task state of `completed`, `failed`, or `interrupted`;
- the exact observed task identifier and claim token;
- atomic lock recovery with matching terminal evidence;
- matching actor identity in runtime state;
- matching generation and slice scope; and
- a state revision that has not changed since observation.

After lock recovery, `recover-actor` rebinds only that exact orchestrator or writer.
Writer recovery preserves the frozen contract and phase and increments the writer attempt.
Orchestrator recovery preserves the generation and accepted-slice count and increments its recovery count.
Any mismatch stops at `ACTIVE RUN STATUS UNKNOWN` without repository changes.

## Whole-Goal Alignment and Handoff

Three accepted slices make `alignment_required` mandatory.
No fourth slice may be contracted in that generation.

Whole-goal alignment checks:

- accepted evidence against every goal criterion;
- regressions and affected product invariants;
- accumulated complexity and removal opportunities;
- whether the goal is complete;
- remaining evidence gaps; and
- unresolved risks or owner decisions.

The alignment report records goal status, the three accepted slices, remaining gaps, risks, and an evidence-based recommendation.
The recommendation is not a selected next slice.

After alignment, the orchestrator writes a compact durable handoff, clears itself from active runtime state, releases ownership, and stops.
A new scheduled or relayed task may then begin a fresh generation when authorization remains standing.

## Owner Decision and Terminal Boundaries

Stop at `NEEDS OWNER DECISION` before:

- selecting, replacing, broadening, or reinterpreting a goal;
- deciding a material product, simulation, worldbuilding, privacy, visual, or lasting architecture question;
- weakening a frozen gate or product invariant;
- absorbing overlapping user changes;
- destructive cleanup, publication, deployment, push, or merge; or
- continuing after the owner pauses or stops the loop.

Record the smallest concrete question and preserve exact working state.
Release ownership only when the current task owns it.
Do not relay from a blocked, unsafe, paused, or owner-decision state.

## Product Invariants

Every slice preserves these established boundaries:

- `EventLog` is append-only objective evidence;
- official-record changes never rewrite objective history or automatically deliver observations;
- agents act only from information and access available to them;
- public expression remains an attempted action;
- model output is not automatically truth, memory, or consequence;
- normal presentation remains separate from omniscient inspection; and
- the focal character remains autonomous rather than a player puppet.

## Migration Behavior

Schema version 2 starts stopped, with `goal_id: null` and no authorization.
The prior active-goal wording remains in historical goal and implementation documents for auditability.
It is not imported because the saved automation was paused at migration time.

There is no automatic compatibility bridge from the one-task-per-slice relay.
Old temporary handoffs may inform orientation but cannot populate the new runtime state.
The first activation requires an explicit owner-approved administrative migration.

## Validation

`scripts/check_autonomous_loop_contract.py` verifies the runtime schema, stopped migration state, required contract language, control scripts, canonical automation prompt, and absence of obsolete one-task-per-slice rules in current operating documents.
`tests/test_autonomous_loop_state.py` exercises legal transitions, contract immutability, three-slice alignment, retry bounds, idempotency, compare-and-swap behavior, and exact actor recovery.
`tests/test_autonomous_loop_lock.py` exercises atomic ownership, transfer, stale-owner recovery, and backward-compatible legacy lock records.

Run focused loop checks first:

```sh
python3 -m unittest tests.test_autonomous_loop_state tests.test_autonomous_loop_lock tests.test_autonomous_loop_contract
```

Then run the full repository check:

```sh
./scripts/check.sh
```
