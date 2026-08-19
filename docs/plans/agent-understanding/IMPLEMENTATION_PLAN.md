# Agent Understanding Rolling Plan

Status: active shared state.

## Run State

- Active work: the sole task marked `next` below
- Current batch: 1
- Last completed task: none
- Incomplete run: none
- Verified implementation tasks since alignment: 0
- Alignment due: after the current three-task batch

## Planning Contract

The goal and its completion criteria define the destination. This file plans
only the next small batch from current evidence; it is not a full implementation
blueprint.

One Codex run completes at most one task below. A run reads the goal, this file,
and only the specification linked by the active task. It locates implementation
code just in time, validates the result, obtains fresh read-only review, updates
this file, commits one coherent change, and exits.

After the batch, a separate alignment run evaluates observed behavior against
the whole goal and plans at most three new tasks. It may revise assumptions,
remove unnecessary work, or close criteria. It does not implement a task.

## Current Batch

| ID | Status | Criterion | One-iteration outcome | Read | Focused evidence |
| --- | --- | --- | --- | --- | --- |
| AU-01 | next | AU-1 | Represent delivered direct-resource evidence as one immutable memory trace. | [Memory Traces](specs/MEMORY_TRACES.md) | Focused trace unit test |
| AU-02 | pending | AU-1 | Interpret one delivered official schedule version as one immutable memory trace. | [Memory Traces](specs/MEMORY_TRACES.md) | Focused official-trace unit test |
| AU-03 | pending | AU-1 | Create focal traces only during delivered-observation processing. | [Memory Traces](specs/MEMORY_TRACES.md) | Delivery integration comparison |

No later implementation tasks are planned yet. The remaining AU criteria are
goal-level requirements, not a predetermined execution sequence.

## Task Update Rules

- At run start, change the active task from `next` to `in_progress`.
- After validation and review, change it to `complete`.
- If another task remains in the current batch, mark exactly one `next`.
- After the final batch task, set `Alignment due` to `now`; do not invent the
  next task in the same run.
- Record concise observed evidence below; repository history records commits.
- If a task is too large, split only that task before implementation and exit.
- If evidence invalidates a later batch task, set `Alignment due` to `now` and
  leave that task unstarted.
- If owner authority is required, leave code unchanged and record the decision.

## Alignment Rules

When alignment is due, use one fresh run to:

1. compare verified behavior with every open goal criterion;
2. identify the smallest next evidence-producing gap;
3. plan no more than three one-context tasks;
4. link each task to one relevant specification and focused evidence;
5. mark exactly one task `next`, reset the counter, commit, and exit.

Do not implement during alignment. Do not pre-plan the rest of the goal.

## Verified Task Log

No implementation task has been completed for this goal.
