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

At the start of each scheduled run, read this contract and the authority sources
below. At 8:30 PM, do not begin another implementation change. Use the remaining
time to finish, validate, document, and commit the current coherent cycle. Stop
by 9:00 PM even when the active goal is unfinished; the next scheduled run
continues from repository state.

The scheduled task uses this instruction:

> Run the autonomous 2084 development loop until 9:00 PM America/Toronto.
> Follow `AGENTS.md` and `docs/main/DEVELOPMENT_LOOP.md`, using the active goal
> in `docs/plans/CURRENT.md`. Complete as many coherent, validated cycles as the
> contract permits. Self-review and commit each completed cycle. Do not select
> a new goal, push, merge, publish, or disturb unrelated user work. Stop early
> only at a contract terminal state.

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
- delegate bounded independent investigation or verification as described
  below;
- mark a criterion met when proportionate evidence passes validation and
  self-review;
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

The main agent is the final technical reviewer of routine implementation
results inside the active goal. The owner remains the authority for goal and
product-direction decisions.

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

### 3. Delegate only bounded work

Use subagents when two or more independent read-heavy questions would
materially improve speed or confidence. Suitable work includes repository
exploration, invariant review, focused test analysis, and inspection of the
resulting diff.

- Use no more than two subagents by default.
- Give each subagent one bounded question and request a concise evidence-backed
  summary.
- Prefer read-only assignments. The main agent remains the sole writer and owns
  all integration and final judgment.
- Do not delegate the active-goal choice, progress claim, or completion
  decision.
- Skip delegation when coordination would cost more than the task warrants.

### 4. Implement one coherent change

Make the smallest change that can satisfy the progress claim.
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

### 6. Self-review, record, and commit

Separate observed behavior from interpretation. Mark the criterion met only
when the evidence is proportionate, the focused and full checks pass, and the
diff review finds no unresolved violation. Update `CURRENT.md` in the same
cycle, including counters and any next alignment requirement.

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
5. subagents used, if any, and what they established;
6. forced outcomes, special cases, risks, and unresolved assumptions;
7. the next candidate criterion, if the run will continue.

At a terminal state, report why work stopped and the exact repository state.
Routine implementation results do not wait for owner review.
