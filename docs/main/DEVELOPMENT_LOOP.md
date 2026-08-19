# Agentic Development Loop

Status: current operating contract for scheduled autonomous development.

This loop advances one owner-approved 2084 goal through small, independently
validated tasks. Each Codex run completes at most one current task, records the
verified result, commits the coherent change, and exits. Each run selects its
task from the active goal and current verified evidence; it does not plan later
tasks. The repository is the durable state between fresh runs. The loop does
not choose project direction or authorize its own next goal.

## Schedule and Run Boundary

The loop is launched by standalone scheduled tasks at 6:00 PM, 7:00 PM, and
8:00 PM in `America/Toronto`. Each task works in the main 2084 checkout, handles
one self-selected implementation task or one alignment review, and exits. If an
earlier run is still active, the next trigger performs no repository work. The
repository carries durable context; prior task conversation does not.

The owner may request a manual run in chat at any time. A manual run follows the
same one-task, authority, validation, independent-review, and no-overlap rules.
The scheduled time boundary does not apply unless the manual request supplies
one.

### Model routing

The scheduled orchestrator uses `gpt-5.6-terra` with high reasoning for
implementation and integration. Every independent implementation reviewer and
goal-alignment reviewer uses a fresh `gpt-5.6-sol` agent with high reasoning.
Luna is not authorized for this loop.

### No-overlap gate

Before reading or changing repository state, a run must inspect the Codex task
activity for this project. Ignore the just-started task itself. If any other
2084 task is queued or running—including a manual run, an earlier scheduled
orchestrator, or any subagent—stop at **ACTIVE RUN EXISTS** without touching the
repository. If task activity cannot be inspected reliably, stop at
**ACTIVE RUN STATUS UNKNOWN** rather than risk concurrent work.

The application may still create a scheduled run at the trigger time; this gate
defines whether that run may begin work. Do not assume the scheduler suppresses
overlapping runs because that behavior is not part of the documented contract.
An orchestrator must not finish while one of its subagents remains active: wait
for it, ask it to return, or stop it before reporting a terminal state. This
keeps the active orchestrator visible to the next trigger for the full lifetime
of its agent tree.

At the start of each scheduled run, read the compact index in `CURRENT.md` and
the just-in-time authority sources it routes. The 8:00 PM run must not begin an
implementation that cannot be finished, validated, reviewed, documented, and
committed by 9:00 PM.

The scheduled task uses this instruction:

> Complete exactly one current work unit from the autonomous 2084 development
> loop. If alignment is due, review verified goal evidence without selecting
> future work. Otherwise select the smallest useful task from the active goal
> and current evidence; do not use or create a future task queue.
> Before touching the repository, inspect Codex task activity for this project.
> If any other 2084 task, loop orchestrator, or subagent is active, make this run
> a no-op as required by the contract.
> Start with `docs/plans/CURRENT.md`. Read its active goal and implementation
> state. Locate only enough code and tests to select one bounded task, then read
> only its relevant specification. Implement, validate, obtain fresh
> independent `gpt-5.6-sol` high-reasoning review, update the shared state,
> commit one coherent task, and exit. For alignment, use a fresh
> `gpt-5.6-sol` high-reasoning reviewer, update verified goal state, commit, and
> exit without implementation or task selection. Do not begin another work
> unit, select a new goal, push, merge, publish, or disturb unrelated user work.
> Do not use Luna.

## Sources of Authority

Read these in order before changing the repository:

1. `AGENTS.md` — project-wide working constraints.
2. `docs/plans/CURRENT.md` — compact index and current run boundary.
3. The active goal linked from `CURRENT.md` — authorized outcome and invariants.
4. The linked implementation state — verified progress and incomplete work.
5. Relevant code and tests found just in time to select one task.
6. Only the specification relevant to the selected task — detailed behavior.

Read `README.md`, Core Construct, Architecture, UI Architecture, Design
References, broader proposals, completed goals, and historical experiments only
when the active specification routes to them or an invariant cannot otherwise
be resolved. The active goal narrows higher-level documents but does not
override their invariants.

If the sources conflict in a way that changes product direction or lasting
architecture, stop at **NEEDS OWNER DECISION**. Autonomy removes routine review,
not the boundary around owner authority.

## Authority

The autonomous loop may:

- implement one coherent change that advances one unmet active-goal criterion;
- add or change tests that prove the new behavior or protect an affected
  invariant;
- update factual implementation-status documentation affected by the change;
- simplify or remove code when that is the smallest way to satisfy the goal;
- partition bounded independent implementation work and delegate investigation
  or verification as described below;
- mark a criterion met when proportionate evidence passes validation and
  independent review;
- commit each complete task, including its tests and progress update.

The autonomous loop may not:

- select, broaden, or replace the active goal;
- settle an open product, worldbuilding, or lasting architecture decision;
- make conceptual changes to the Core Construct or Architecture without an
  owner decision;
- continue into an adjacent feature after the active goal is complete;
- modify `experiments/` unless the active goal explicitly targets it;
- push, merge, publish, or discard user work;
- weaken a test merely because intended behavior is difficult to implement.

The orchestrator owns the final integration and completion decision, but it may
not be the only reviewer of its implementation result. The owner remains the
authority for goal and product-direction decisions.

## Preconditions

Before implementation, confirm that:

- `CURRENT.md` links exactly one active, owner-approved goal;
- the linked implementation state contains no future task queue;
- the active goal authorizes the proposed behavior;
- no incomplete run is recorded in the implementation state;
- the working checkout contains no unrelated unfinished changes;
- the baseline repository check passes, or any pre-existing failure is recorded
  and clearly unrelated to the proposed change.

If the checkout contains unrelated user changes, do not edit, stage, commit, or
discard them. Stop at **BASELINE BLOCKED** and report the exact paths. If another
precondition is not met, make no implementation change and report the specific
condition.

## One Task Run

### 1. Orient

Read the compact index, goal, and implementation state. If alignment is due,
perform section 7 without loading implementation or starting a task. Otherwise,
locate only enough relevant implementation and tests to select one task.

### 2. Select one task

Choose the smallest unmet goal gap whose implementation can create new
behavioral evidence in one fresh context. Record that single task in the
implementation state, then read only its relevant specification. Do not select
or record later work. If it cannot fit comfortably, replace it with a smaller
task before editing. State a progress claim:

> This task advances criterion X by producing behavior Y, verified by evidence
> Z.

If no honest progress claim can be made, do not change code.

### 3. Partition and delegate bounded work

Use subagents to keep exploration, implementation details, test output, and
review evidence out of the orchestrator's context when the work divides
cleanly. Suitable parallel work includes repository exploration, invariant
analysis, independent components, and independent test suites.

- Use no more than two implementation or investigation subagents concurrently
  by default.
- Give each subagent one bounded outcome, relevant constraints, exclusive file
  or module ownership, and a concise return format.
- Parallel writers are allowed only when their interfaces are agreed first,
  their owned files do not overlap, and neither needs to edit shared mutable
  state such as central schemas, registries, configuration, or the same tests.
- Use one writer when steps depend on one another, boundaries are uncertain, or
  integration would require frequent coordination.
- Prefer parallel read-only work when a clean write partition is unavailable.
- Do not delegate the active-goal choice, progress claim, or completion
  decision.
- Require each subagent to return a distilled result instead of raw logs or
  exploration transcripts.
- Skip delegation when coordination would cost more than the context or time it
  saves.

### 4. Implement one coherent change

Make the smallest change that can satisfy the progress claim. Wait for all
implementation subagents, inspect their results, and integrate them into one
coherent change. No two agents may edit the same file concurrently. If a
supposedly independent partition reveals a shared dependency, stop parallel
writes and integrate that boundary sequentially.

Infrastructure-only work is allowed only when it is necessary for a named
criterion and identifies the immediate behavioral use it unlocks. Do not add
speculative extension points for later goals.

### 5. Validate proportionately

Run focused checks first, then the repository check. When observable simulation
behavior changes, also run the normal focal view and the omniscient inspector.
Review the diff for:

- hidden knowledge or impossible authority;
- accidental coupling of official publication and observation delivery;
- mutation of append-only objective evidence;
- forced outcomes described as emergence;
- tests changed beyond the intended behavior;
- complexity that does not help answer the active question.

### 6. Obtain independent review, record, and commit

After integration and validation, spawn a fresh read-only reviewer subagent for
every implementation task. Give it the active goal, relevant project rules,
the resulting diff, and validation results, but do not give it the
implementer's reasoning or ask it to confirm the chosen approach. It must look
for goal mismatch, impossible knowledge or authority, broken invariants,
missing behavioral evidence, test gaps, and unnecessary complexity. The
reviewer must use `gpt-5.6-sol` with high reasoning, including for a
documentation-only or no-change alignment task.

The orchestrator must resolve every blocking finding and repeat independent
review after any material correction. Separate observed behavior from
interpretation. Mark the task complete only when the evidence is proportionate,
the focused and full checks pass, and independent review finds no unresolved
blocking violation. Update `IMPLEMENTATION_PLAN.md` in the same run, including
verified criterion status, counters, evidence, and any alignment requirement.
Clear the current-run record during commit preparation; do not record a next
task.

Review the final staged diff, then create one commit containing the coherent
implementation, validation evidence encoded in tests, and progress update. Do
not include unrelated files. If validation or review fails, fix the task or
restore only the loop's own incomplete changes before moving on; never commit a
known failing or partial result as verified progress.

### 7. Apply progress and saturation gates

- A criterion with verified proportionate evidence is closed. Do not harden it
  further without a regression, an affected invariant, or owner direction.
- After at most three verified implementation tasks, perform a goal-level
  alignment review in a separate run before the next implementation task.
- Never plan, suggest, or record a future implementation task.
- Do not complete two infrastructure-only tasks without focused behavioral
  evidence.
- It is valid for a run to make no code change.

The goal-level alignment review asks what observable behavior changed, which
criteria are proven, whether complexity grew faster than explanatory value,
and whether anything should be removed. It updates only verified state and
recommendations about existing implementation. Reset the alignment counter only
after recording and committing that review. Do not implement or select a later
task during alignment.

## Terminal States

After the one-task run, choose exactly one state:

- **TASK COMPLETE** — the task is validated, recorded, and committed; exit
  without selecting another task.
- **ALIGNMENT COMPLETE** — verified goal evidence was reviewed and recorded;
  no implementation task was selected.
- **ACTIVE RUN EXISTS** — another project task, orchestrator, or subagent is
  active, so this trigger performed no repository work.
- **ACTIVE RUN STATUS UNKNOWN** — task activity could not be inspected reliably,
  so this trigger performed no repository work.
- **TIME WINDOW COMPLETE** — the current coherent task is safely finished and
  the run has reached its daily stopping boundary.
- **NEEDS OWNER DECISION** — continuing requires a product, worldbuilding,
  architecture, scope, or authority choice absent from the active goal.
- **GOAL COMPLETE** — every criterion has proportionate verified evidence. Mark
  the goal complete, commit the final progress update, and do not select or
  begin another goal.
- **NO JUSTIFIED CHANGE** — no change would honestly advance the active goal.
- **BASELINE BLOCKED** — existing repository state prevents a safe autonomous
  task.

For each committed task, retain a concise report in the scheduled task run:

1. criterion advanced and the progress claim;
2. observed behavior and interpretation kept separate;
3. files changed and commit created;
4. focused and full validation results;
5. implementation partition, subagents used, and independent-review findings;
6. forced outcomes, special cases, risks, and unresolved assumptions;
7. whether alignment is due; do not name a future implementation task.

At a terminal state, report why work stopped and the exact repository state.
Routine implementation results do not wait for owner review.
