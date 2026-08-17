# Agentic Development Loop

Status: current operating contract for scheduled autonomous development.

This loop advances one owner-approved 2084 goal through small, independently
validated changes. It is autonomous inside that goal: it selects the next gap,
implements it, reviews the evidence, records verified progress, and commits the
coherent result without waiting for owner acceptance after each cycle. It does
not choose the project's direction or authorize its own next goal.

## Schedule and Run Boundary

The loop is launched by one standalone scheduled task every day at 6:00 PM in
`America/Toronto`. The task works in the main 2084 checkout and may run
consecutive cycles until 9:00 PM. The repository carries durable context
between scheduled runs; prior task conversation does not.

The owner may also request one or more cycles in chat at any time. A manual run
follows the same authority, validation, independent-review, and no-overlap
rules. The 6:00–9:00 PM boundary applies only to the scheduled run unless the
manual request supplies its own time boundary.

### No-overlap gate

Before reading or changing repository state, a run must inspect the Codex task
activity for this project. Ignore the just-started task itself. If any other
2084 task is queued or running—including a manual cycle, an earlier scheduled
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

At the start of each scheduled run, read this contract and the authority sources
below. At 8:30 PM, do not begin another implementation change. Use the remaining
time to finish, validate, document, and commit the current coherent cycle. Stop
by 9:00 PM even when the active goal is unfinished; the next scheduled run
continues from repository state.

The scheduled task uses this instruction:

> Run the autonomous 2084 development loop until 9:00 PM America/Toronto.
> Before touching the repository, inspect Codex task activity for this project.
> If any other 2084 task, loop orchestrator, or subagent is active, make this run
> a no-op as required by the contract.
> Follow `AGENTS.md` and `docs/main/DEVELOPMENT_LOOP.md`, using the active goal
> in `docs/plans/CURRENT.md`. Complete as many coherent, validated cycles as the
> contract permits. Partition only genuinely independent work, obtain fresh
> independent review, and commit each completed cycle. Do not select a new
> goal, push, merge, publish, or disturb unrelated user work. Stop early only
> at a contract terminal state.

## Sources of Authority

Read these in order before changing the repository:

1. `AGENTS.md` — project-wide working constraints.
2. `README.md` and `docs/main/CORE_CONSTRUCT.md` — current product direction.
3. `docs/main/ARCHITECTURE.md` — implemented boundaries and known limits.
4. `docs/plans/CURRENT.md` — the single active goal and verified progress.
5. The active goal linked from `CURRENT.md` — authorized scope, invariants,
   completion criteria, and stop conditions.

The active goal narrows the higher-level documents; it does not override their
invariants. Broader proposals are optional context unless the active goal
explicitly requires them. They are not backlogs or implementation checklists.

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
- commit each complete cycle, including its tests and progress update.

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
- the active goal authorizes the proposed behavior;
- no incomplete cycle is recorded in `CURRENT.md`;
- the working checkout contains no unrelated unfinished changes;
- the baseline repository check passes, or any pre-existing failure is recorded
  and clearly unrelated to the proposed change.

If the checkout contains unrelated user changes, do not edit, stage, commit, or
discard them. Stop at **BASELINE BLOCKED** and report the exact paths. If another
precondition is not met, make no implementation change and report the specific
condition.

## One Development Cycle

### 1. Orient

Read the authority sources, inspect the relevant implementation and tests, and
compare current behavior with the active goal's completion criteria. Perform a
required goal-level alignment review before implementation when `CURRENT.md`
says one is due. Record its conclusions in `CURRENT.md`; it may legitimately
end without a code change.

### 2. Select one gap

Choose the smallest unmet criterion whose implementation would create new
goal-level behavioral evidence. Before editing, state a progress claim:

> This cycle advances criterion X by producing behavior Y, verified by evidence
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
every implementation cycle. Give it the active goal, relevant project rules,
the resulting diff, and validation results, but do not give it the
implementer's reasoning or ask it to confirm the chosen approach. It must look
for goal mismatch, impossible knowledge or authority, broken invariants,
missing behavioral evidence, test gaps, and unnecessary complexity. A
documentation-only or no-change alignment cycle may use orchestrator
self-review.

The orchestrator must resolve every blocking finding and repeat independent
review after any material correction. Separate observed behavior from
interpretation. Mark the criterion met only when the evidence is proportionate,
the focused and full checks pass, and independent review finds no unresolved
blocking violation. Update `CURRENT.md` in the same cycle, including counters
and any next alignment requirement.

Review the final staged diff, then create one commit containing the coherent
implementation, validation evidence encoded in tests, and progress update. Do
not include unrelated files. If validation or review fails, fix the cycle or
restore only the loop's own incomplete changes before moving on; never commit a
known failing or partial result as verified progress.

### 7. Apply progress and saturation gates

- A criterion with verified proportionate evidence is closed. Do not harden it
  further without a regression, an affected invariant, or owner direction.
- After two consecutive implementation cycles on the same criterion, the next
  cycle must move to another criterion, demonstrate end-to-end behavior, or
  stop with **NO JUSTIFIED CHANGE**.
- After three verified implementation cycles, perform a goal-level alignment
  review before another implementation change.
- Do not perform two consecutive infrastructure-only cycles.
- It is valid for a cycle to make no code change.

The goal-level alignment review asks what observable behavior changed, which
criteria are proven, whether complexity grew faster than explanatory value,
and whether anything should be removed. Reset the alignment counter only after
recording that review.

## Terminal States

After each cycle, choose exactly one state:

- **CONTINUE** — the cycle is validated, recorded, and committed; enough time
  remains for another justified cycle.
- **ACTIVE RUN EXISTS** — another project task, orchestrator, or subagent is
  active, so this trigger performed no repository work.
- **ACTIVE RUN STATUS UNKNOWN** — task activity could not be inspected reliably,
  so this trigger performed no repository work.
- **TIME WINDOW COMPLETE** — the current coherent cycle is safely finished and
  the run has reached its daily stopping boundary.
- **NEEDS OWNER DECISION** — continuing requires a product, worldbuilding,
  architecture, scope, or authority choice absent from the active goal.
- **GOAL COMPLETE** — every criterion has proportionate verified evidence. Mark
  the goal complete, commit the final progress update, and do not select or
  begin another goal.
- **NO JUSTIFIED CHANGE** — no change would honestly advance the active goal.
- **BASELINE BLOCKED** — existing repository state prevents a safe autonomous
  cycle.

For each committed cycle, retain a concise report in the scheduled task run:

1. criterion advanced and the progress claim;
2. observed behavior and interpretation kept separate;
3. files changed and commit created;
4. focused and full validation results;
5. implementation partition, subagents used, and independent-review findings;
6. forced outcomes, special cases, risks, and unresolved assumptions;
7. the next candidate criterion, if the run will continue.

At a terminal state, report why work stopped and the exact repository state.
Routine implementation results do not wait for owner review.
