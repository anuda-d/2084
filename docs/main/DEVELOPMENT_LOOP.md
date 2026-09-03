# Goal-Bounded Autonomous Development Loop

Status: current operating contract for scheduled development against one
owner-approved goal.

This loop advances one approved 2084 goal through small, independently
validated work units in successive fresh tasks.
It operates only when `docs/plans/CURRENT.md` records exactly one active goal
with standing owner authorization and the `autonomous-2084-development-loop`
automation is active.
Routine implementation, acceptance, local commit, handoff, and relay inside
the approved goal do not wait for owner review.

The owner remains the authority for a new goal and for unresolved material
product, worldbuilding, simulation, privacy, or lasting architecture decisions.
Standing authorization never broadens or reinterprets the active goal.

An explicit owner request may authorize a bounded administrative change while
no product goal is active.
That authority covers only the requested maintenance and never starts the
implementation loop, activates the scheduler, or selects product behavior.

## Scheduled Operating Window

When standing authorization is active, the loop may start new units daily from
18:00 until 23:00 in `America/Toronto`.
The recurring scheduler starts a fresh recovery task once per hour at 18:00,
19:00, 20:00, 21:00, and 22:00.
Before selecting a new unit, inspect the exact
`autonomous-2084-development-loop` automation and fail closed unless its status
is active.

An accepted unit that finishes before 23:00 creates one fresh successor task in
the same saved local project after writing its handoff.
That relay provides back-to-back progress without allowing one task to own two
units.
At or after 23:00, the active task finishes its current unit safely, writes the
handoff, and does not create a successor.

The hourly starts are recovery opportunities, not permission for overlap.
Every scheduled or relayed task first inspects repository run state and
performs any useful read-only orientation without checkout ownership.
It atomically claims the durable checkout-ownership record immediately before
the first repository write.
If another durable owner is active, the new task exits without changing the
repository.
If no recorded owner exists and `Current run` and `Incomplete run` agree on one
unfinished unit, the fresh task resumes exactly that unit instead of selecting
a replacement.
If the run fields conflict, the ownership record is unreadable, or the recorded
owner's state cannot be verified, stop safely without changes.

Outside the scheduled window, a task may finish an already-recorded unit safely
but may not select a new unit or relay a successor.
An explicit owner instruction may perform bounded administrative work outside
the window but does not silently start an implementation unit.

## Goal and Work-Unit Boundary

The active goal defines the outcome, invariants, authorized scope, validation
standard, and completion condition.
A work unit is the smallest coherent change that creates evidence for one unmet
criterion.
One implementation task owns at most one work unit.

Standing authorization permits successive bounded units only inside the active
goal.
The loop selects each unit from current repository evidence after the prior
unit is accepted and committed.
It never records a future task queue.

Each work unit:

1. selects one smallest justified goal gap;
2. obtains one to three independent read-only explorations;
3. states one criterion, intended result, and evidence claim;
4. implements one coherent change through the sole-writer orchestrator;
5. runs focused checks and the full repository check;
6. records candidate evidence;
7. receives a fresh independent read-only review;
8. resolves every blocking finding and repeats validation and fresh review after
   a material correction;
9. records accepted evidence and creates one local commit;
10. writes the compact temporary handoff with `No next unit selected`;
11. creates one fresh successor before 23:00 when relay remains authorized; and
12. stops without selecting another unit.

## Fresh-Task Handoff Contract

Every implementation unit begins in a newly created fresh task.
The first unit reads the active goal and implementation state without requiring
a prior handoff.
Every later unit reads the latest temporary handoff before selecting or
continuing work.

A task may orient, select or continue one unit, explore, implement, validate,
review, correct, accept, commit, hand off, and relay.
It may not select or implement a second unit.

At every accepted, paused, blocked, or owner-decision terminal state, write a
compact redacted handoff in the operating system temporary directory.
Use `2084-<active-goal-id>-handoff.md` and capture the goal id before a
completion transition clears it.

The handoff contains only:

- active goal id and exact terminal state;
- accepted commit or exact incomplete working-tree state;
- criterion and evidence status;
- focused, full, scenario, inspector, and independent-review results as
  applicable;
- alignment count or checkpoint state;
- risks and unresolved owner decisions;
- `No next unit selected`; and
- suggested skills for the next task.

The handoff is context, not authority, accepted evidence, or a future task
queue.
If it is unavailable, the fresh task reconstructs factual state from the
repository and does not infer missing decisions or discard work.

## Fresh-Task Relay

After an accepted local commit and handoff, read the current local time in
`America/Toronto`.
Inspect the exact `autonomous-2084-development-loop` automation again.
If it is before 23:00, standing authorization remains active, and that
automation's status is active:

1. use the Codex project tools to identify the exact saved local project;
2. assert and release checkout ownership, then enter handoff-only state and
   perform no more repository work;
3. create one fresh local task in that project with `gpt-5.6-terra` and high
   reasoning;
4. give it the active automation prompt and tell it to begin with the
   authoritative read order;
5. wait once, briefly, only to confirm dispatch; and
6. stop the current task.

Do not relay after a blocked, paused, owner-decision, unsafe-baseline,
overlapping-run, or goal-complete terminal state.
Do not relay at or after 23:00.
Do not interpret failure to create a successor as permission to keep working in
the current task.
The next hourly recovery start may resume from repository state and the
handoff.

## No-Overlap Gate

Read-only work does not require checkout ownership.
This includes orientation, exploration, independent review, and checks that do
not alter tracked files.

Immediately before the first repository write, run
`python3 scripts/autonomous_loop_lock.py acquire`.
The command obtains the current task ID from `CODEX_THREAD_ID` and atomically
creates the durable local ownership record.

If acquisition reports `HELD_BY <owner-id>`, inspect that exact task with
`read_thread`.
Stop at **ACTIVE RUN EXISTS** when the recorded owner is queued, active, or owns
a non-terminal latest turn.
An owner whose latest turn is non-terminal, including an idle owner awaiting
input, continues to own the checkout.
If `read_thread` verifies that the exact recorded owner's latest turn is
`completed`, `failed`, or `interrupted`, recover with
`python3 scripts/autonomous_loop_lock.py recover --expected-task-id <owner-id>
--expected-claim-token <token> --verified-terminal-state <state>`.
Use the claim token returned with `HELD_BY` when the owner was inspected.
Each successful resumed-owner assertion rotates that token.
The recovery command atomically replaces only that expected owner.
It fails closed if the recorded owner or claim token changed, the record is
missing or unreadable, or the supplied state is not terminal.
If exact-owner inspection fails or the exact-owner state is active,
non-terminal, or unknown, stop at **ACTIVE RUN STATUS UNKNOWN**.
Lock age is diagnostic only and never authorizes recovery.

The unscoped Codex task listing is not an ownership precondition because it can
hang, cannot filter by project, and cannot reliably classify idle historical
tasks.
Do not call `list_threads` as part of the no-overlap gate.
The atomic ownership record is the decisive single-writer proof for every task
governed by this repository.

Assert ownership after any resumed turn and immediately before commit by
running `python3 scripts/autonomous_loop_lock.py assert-owner`.
A mismatch stops all further repository work.
Release ownership at completion and every other non-relaying terminal state
only when the current task owns the record, by running
`python3 scripts/autonomous_loop_lock.py release`.
For a relay, assert and release ownership immediately before creating the
successor, enter handoff-only state, and perform no more repository work.
The successor must acquire ownership for itself.

The recorded `Current run` and `Incomplete run` must also agree.
A fresh task continues a recorded incomplete unit instead of selecting a
replacement.

## Owner Decision Boundary

Routine work-unit evidence is accepted under standing authorization after
focused and full validation plus clean fresh independent review.
The owner is not a routine unit reviewer.

Stop at **NEEDS OWNER DECISION** before acting when continuation requires:

- selecting, replacing, broadening, or reinterpreting a goal;
- a material product, worldbuilding, simulation, visual, scope, privacy, or
  lasting architecture choice not already settled by authoritative documents;
- resolving an open question that materially affects behavior;
- destructive cleanup, disposal of user work, deployment, publication, push,
  merge, or another external side effect;
- authority to absorb overlapping unrelated changes; or
- direction after the owner pauses or stops the loop.

When a decision is required, record the smallest concrete question, set `Run
status` to `needs owner decision`, write the handoff, release ownership if the
current task owns the record, and do not relay.

## Model Routing

- The sole-writer orchestrator uses `gpt-5.6-terra` with high reasoning.
- Read-only explorer agents use `gpt-5.6-terra` with high reasoning.
- Every independent implementation and alignment review uses a fresh
  `gpt-5.6-sol` agent with high reasoning.
- Reviewers are read-only and may not edit, commit, choose product direction,
  or determine a new goal.

These development models are separate from any model used inside the 2084
simulation.

## Sources of Authority

Read these in order before repository work:

1. `AGENTS.md`;
2. `docs/plans/CURRENT.md`;
3. the active goal linked from `CURRENT.md`;
4. the linked implementation state;
5. the latest temporary handoff when available;
6. relevant implementation and tests located at selection time; and
7. only the product specification relevant to the selected unit.

Read the README, Core Construct, Architecture, UI Architecture, Design
References, broader proposals, and completed goals only when the active
specification routes there or an invariant is otherwise unclear.
A proposal is not an implementation checklist.

If authoritative sources conflict in a way that changes product direction,
worldbuilding, simulation behavior, scope, privacy, or lasting architecture,
stop at **NEEDS OWNER DECISION**.

## Standing Authority

While the active goal has `Owner authorization: standing`, the loop may:

- select successive bounded units during the scheduled window;
- implement one coherent change per unit;
- add or update focused tests and quality gates;
- update implementation-state evidence;
- simplify or remove loop-owned code when it is the safest bounded solution;
- use read-only explorers and reviewers;
- accept clean reviewed evidence;
- create local commits;
- create the required temporary handoff; and
- create one fresh successor task before 23:00.

Standing authority does not permit the loop to:

- select or invent a new goal;
- broaden or reinterpret the active goal;
- decide an unresolved owner question;
- weaken tests, validation, simulation boundaries, or privacy rules;
- absorb, overwrite, discard, or commit unrelated user work;
- push, merge, deploy, publish, or create unrelated external side effects;
- use destructive cleanup to make a unit pass; or
- treat a reviewer as a product decision-maker.

## Preconditions

Before selecting or continuing a unit, confirm that:

- the task has not completed another unit;
- current time permits new selection, or an incomplete unit is being finished;
- exactly one active owner-approved goal is linked;
- owner authorization is standing;
- no owner decision is pending;
- when alignment is due, this task is the alignment unit rather than an
  implementation unit;
- no overlapping task or recorded run exists;
- a current unit, if any, matches the incomplete unit;
- the work is authorized by the active goal;
- no future task queue is recorded;
- the checkout contains no unsafe overlapping user changes; and
- the repository check passes, or a pre-existing unrelated failure is recorded.

If unrelated changes overlap the unit, stop at **BASELINE BLOCKED**.
Never reset or discard them without direction.

## One Work-Unit Run

### 1. Orient

Read the sources of authority, latest handoff, run fields, accepted evidence,
and repository state.
Confirm this is a fresh task and perform read-only no-overlap checks.
If `Alignment due: yes`, select only whole-goal alignment and do not select an
implementation unit.

### 2. Select One Task

Choose the smallest unmet goal gap that can create direct evidence in one task.
Immediately before recording the selected run, acquire durable checkout
ownership.
Record only that task under `Current run` and `Incomplete run` in both the
compact index and active implementation state.
State:

> This work unit advances criterion X by producing result Y, verified by
> evidence Z.

Do not record later tasks.
If no honest gap advances the goal, stop at **NO JUSTIFIED CHANGE**.

### 3. Explore

Use one to three read-only explorer agents for concrete independent questions.
Wait for all explorers before editing.
The orchestrator remains the sole writer.

### 4. Implement

Make the smallest coherent change that can satisfy the claim.
Do not add speculative extension points or future-feature seams.

Preserve these invariants:

- `EventLog` is append-only objective evidence;
- official-record changes do not rewrite history or automatically deliver an
  observation;
- agents act only from information and access actually available to them;
- public expression remains an attempted action;
- model output is not automatically truth, memory, or consequence;
- normal presentation and the omniscient inspector remain separate; and
- the focal character remains autonomous rather than a player puppet.

### 5. Validate

Run focused checks first and then `./scripts/check.sh`.
When observable simulation behavior changes, also run the normal scenario and
inspector.
Inspect the owned diff and verify the intended behavior or architecture claim
directly.

Review the diff for:

- impossible knowledge or authority;
- accidental history mutation or observation delivery;
- forced outcomes described as emergence;
- tests changed beyond the intended behavior;
- normal-view privacy leaks;
- complexity that does not improve the active question; and
- stale or contradictory documentation.

### 6. Record and Review

Before review, record the criterion, claim, exact diff, observed evidence,
validation, risks, and proposed accepted evidence.

Use a fresh read-only `gpt-5.6-sol` high-reasoning reviewer.
Provide the goal, relevant rules, actual diff, evidence claim, validation, and
known risks.
Resolve every blocker.
A material correction repeats focused and full validation and uses a new fresh
reviewer.

### 7. Accept, Commit, Hand Off, Relay, and Stop

After validation passes and review is clean:

1. record the factual review result;
2. mark only supported criteria accepted;
3. append the accepted run record;
4. update alignment or checkpoint fields when applicable;
5. clear `Current run` and `Incomplete run`;
6. set `Run status` to `awaiting scheduled fresh task` unless the goal is
   complete;
7. synchronize `CURRENT.md`;
8. stage only the coherent unit;
9. assert checkout ownership and create one local commit;
10. write the temporary handoff with `No next unit selected`;
11. assert checkout ownership, release checkout ownership, and enter
    handoff-only state;
12. before 23:00, create one fresh successor when every relay precondition
    remains true; and
13. stop at **UNIT COMMITTED - HANDOFF READY**.

The current task never selects the successor's unit.

## Alignment and Saturation

- A criterion with verified evidence is closed unless a regression or affected
  invariant justifies reopening it.
- After at most three implementation work units, perform a separate whole-goal
  alignment before another implementation unit.
- Alignment reviews evidence, complexity, removals, and completion.
  It does not choose later work.
- Two infrastructure-only units must not occur without focused behavioral
  evidence unless the owner-approved goal explicitly authorizes architecture
  work.
- A no-change result is valid when no justified change advances the goal.

## Blocked Units

Do not silently replace a non-viable selected unit.

- Resolve a technical blocker safely inside the same claim when possible.
- For a required owner decision, record it, hand off, and stop without relay.
- For an unsafe baseline or overlap, preserve exact state, hand off when
  appropriate, and stop without relay.
- Never remove work merely because a unit is blocked.
- If the current task owns checkout ownership, release it after writing the
  blocked handoff and before stopping.

## Owner Pause or Stop

The owner may pause or stop the loop at any time.
On pause, set owner authorization, cadence, relay, and run status to paused in
both operational files, preserve any active unit, write a handoff, and stop.
If the current task owns checkout ownership, release it after writing the
handoff and before stopping.
The scheduler must no-op while authorization is paused.

Administrative state changes explicitly requested by the owner remain allowed.
Resuming requires an explicit owner instruction and synchronized standing
state.
The activation or resume change must set the
`autonomous-2084-development-loop` automation to active before scheduled work
can begin.

## Goal Completion

The active goal is complete only when every criterion has accepted evidence,
the final repository check and required end-to-end behavior checks pass, and a
final fresh independent review is clean.

At completion:

1. record final evidence and review;
2. mark every criterion accepted;
3. set the goal and implementation state to their canonical completed status;
4. clear current and incomplete runs and pending decisions;
5. set `Active goal id` to `none`, owner authorization to `pending`, cadence to
   `stopped`, relay to `stopped`, and standing authority to `none`;
6. synchronize `CURRENT.md` and any owner-facing status document;
7. run the final repository check;
8. assert checkout ownership and create the final local commit;
9. write the final handoff using the captured completing goal id;
10. pause the `autonomous-2084-development-loop` automation so it does not
    create later no-op recovery tasks;
11. release checkout ownership;
12. do not relay; and
13. stop at **GOAL COMPLETE** without selecting another goal.

## Terminal States

- **UNIT COMMITTED - HANDOFF READY**
- **ALIGNMENT COMMITTED - HANDOFF READY**
- **NEEDS OWNER DECISION - HANDOFF READY**
- **OWNER AUTHORIZATION REQUIRED OR PAUSED**
- **ACTIVE RUN EXISTS**
- **ACTIVE RUN STATUS UNKNOWN**
- **NO JUSTIFIED CHANGE**
- **WORK UNIT BLOCKED - HANDOFF READY**
- **BASELINE BLOCKED - HANDOFF READY**
- **GOAL COMPLETE**

## Accepted Run Record

For every committed unit retain:

1. criterion and claim;
2. observed evidence and interpretation separately;
3. exact files and local commit;
4. focused and full validation plus applicable end-to-end evidence;
5. explorer partition and fresh review result;
6. risks and unresolved assumptions;
7. acceptance basis under standing owner authorization; and
8. confirmation that the handoff records `No next unit selected`.
