# Agentic Development Loop

Status: current operating contract for scheduled development runs.

This loop advances one owner-approved 2084 goal through small, reviewable
changes. It does not choose the project's direction, authorize its own next
goal, or require a code change every time it runs.

## Sources of Authority

Read these in order before changing the repository:

1. `AGENTS.md` — project-wide working constraints.
2. `README.md` and `docs/main/CORE_CONSTRUCT.md` — current product direction.
3. `docs/main/ARCHITECTURE.md` — implemented boundaries and known limits.
4. `docs/plans/CURRENT.md` — the single active goal and accepted progress.
5. The active goal linked from `CURRENT.md` — authorized scope, invariants,
   completion criteria, and stop conditions.

The active goal narrows the higher-level documents; it does not override their
invariants. If the sources conflict in a way that changes product direction or
architecture, stop and request owner review.

Broader proposals are optional context unless the active goal explicitly
requires them. They are not backlogs or implementation checklists.

## Authority

A scheduled run may:

- implement one coherent change that advances one unmet active-goal criterion;
- add or change tests that prove the new behavior or protect an affected
  invariant;
- update factual implementation-status documentation affected by the change;
- simplify or remove code when that is the smallest way to satisfy the goal;
- delegate bounded independent investigation or verification as described
  below.

A scheduled run may not:

- select, broaden, or replace the active goal;
- settle an open product, worldbuilding, or lasting architecture decision;
- make conceptual changes to the Core Construct or Architecture without owner
  review;
- continue into an adjacent feature after the active goal is complete;
- modify `experiments/` unless the active goal explicitly targets it;
- commit, push, merge, publish, or discard user work;
- weaken a test merely because intended behavior is difficult to implement.

The owner is the final reviewer of every implementation result.

## Preconditions

Before implementation, confirm that:

- `CURRENT.md` links exactly one active, owner-approved goal;
- the active goal authorizes the proposed behavior;
- no earlier development-loop result in this task is awaiting owner review;
- the working checkout contains no unrelated unfinished changes;
- the baseline repository check passes, or any pre-existing failure is recorded
  and clearly unrelated to the proposed change.

If a precondition is not met, make no implementation change and report the
specific condition.

## One Scheduled Run

### 1. Orient

Read the authority sources, inspect the relevant implementation and tests, and
compare current behavior with the active goal's completion criteria. Do not
turn every technical limit or broad proposal into work.

### 2. Select one gap

Choose the smallest unmet criterion whose implementation would create new
goal-level behavioral evidence. Before editing, state a progress claim:

> This run advances criterion X by producing behavior Y, verified by evidence Z.

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
- Do not delegate the active-goal choice, progress claim, or completion decision.
- Skip delegation when coordination would cost more than the task warrants.

### 4. Implement one coherent change

Make the smallest change that can satisfy the progress claim. Infrastructure-only
work is allowed only when it is necessary for a named criterion and identifies
the immediate behavioral use it unlocks. Do not add speculative extension
points for later goals.

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

### 6. Apply progress and saturation gates

- A criterion with accepted proportionate evidence is closed. Do not harden it
  further without a regression, an affected invariant, or owner direction.
- After two consecutive implementation runs on the same criterion, the next
  run must move to another criterion, demonstrate end-to-end behavior, or stop
  for owner review.
- After three accepted implementation runs, perform a goal-level alignment
  review before another implementation run.
- Do not perform two consecutive infrastructure-only runs.
- It is valid for a run to make no code change.

The goal-level alignment review asks what observable behavior changed, which
criteria are proven, whether complexity grew faster than explanatory value,
and whether anything should be removed.

## Review Gate

Finish every run with exactly one of these states:

- **READY FOR OWNER REVIEW** — one bounded change is implemented and validated.
- **NO CHANGE — PREVIOUS RESULT AWAITS REVIEW** — do not begin more work.
- **NEEDS OWNER DECISION** — a meaningful choice is not authorized.
- **NO CHANGE — GOAL COMPLETE** — all criteria have proportionate evidence;
  only the owner may accept completion or select another goal.
- **NO JUSTIFIED CHANGE** — no change would honestly advance the active goal.
- **BASELINE BLOCKED** — existing repository state prevents a safe run.

For a reviewable change, report:

1. criterion advanced and the progress claim;
2. observed behavior and interpretation kept separate;
3. files changed;
4. focused and full validation results;
5. subagents used, if any, and what they established;
6. forced outcomes, special cases, risks, and unresolved assumptions;
7. the next candidate criterion without beginning it.

Leave the changes in the working checkout for review. Do not start the next
implementation run until the owner accepts, rejects, or redirects the result.
