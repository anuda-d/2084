# Agent Understanding Implementation Plan

Status: active shared state.

## Run State

- Active task: the sole task marked `next` below
- Last completed task: none
- Incomplete run: none
- Implementation runs since alignment review: 0
- Consecutive runs on one criterion: 0
- Next alignment review: AR-01 after AU-03

## Iteration Contract

One Codex run completes at most one task below. A run reads the goal, this file,
and only the specification linked by the active task. It finds implementation
code just in time with repository search. It validates, obtains fresh read-only
review, updates this file, commits one coherent change, and exits.

Task descriptions name behavior rather than permanent file ownership. If one
task cannot fit comfortably in a fresh context, split it before implementation
and record the split here. Do not combine adjacent tasks to increase throughput.

## Ordered Tasks

| ID | Status | Criterion | One-iteration outcome | Read | Focused evidence |
| --- | --- | --- | --- | --- | --- |
| AU-01 | next | AU-1 | Represent delivered direct-resource evidence as one immutable memory trace. | [Memory Traces](specs/MEMORY_TRACES.md) | Focused trace unit test |
| AU-02 | pending | AU-1 | Interpret one delivered official schedule version as one immutable memory trace. | [Memory Traces](specs/MEMORY_TRACES.md) | Focused official-trace unit test |
| AU-03 | pending | AU-1 | Create focal traces only during delivered-observation processing. | [Memory Traces](specs/MEMORY_TRACES.md) | Delivery integration comparison |
| AR-01 | pending | alignment | Review goal alignment after AU-03. | Goal plus verified task log | Recorded no-code review |
| AU-04 | pending | AU-1 | Reuse one interpreted claim across repeated version-two deliveries. | [Memory Traces](specs/MEMORY_TRACES.md) | Repeated-delivery test |
| AU-05 | pending | AU-2 | Link incompatible same-period official claims as one reciprocal conflict. | [Official-Version Conflict](specs/CONFLICTS.md) | Focused conflict test |
| AU-06 | pending | AU-2 | Keep the direct-resource claim outside the official-version conflict. | [Official-Version Conflict](specs/CONFLICTS.md) | Proposition-boundary test |
| AR-02 | pending | alignment | Review goal alignment after AU-06. | Goal plus verified task log | Recorded no-code review |
| AU-07 | pending | AU-3 | Expose a restricted Agent Understanding snapshot to focal policy. | [Public-Counter Stance](specs/PUBLIC_STANCE.md) | Restricted-view test |
| AU-08 | pending | AU-3 | Create the public-counter stance from version two under sufficient local pressure. | [Public-Counter Stance](specs/PUBLIC_STANCE.md) | Threshold comparison |
| AU-09 | pending | AU-3 | End the public-counter stance outside its valid location. | [Public-Counter Stance](specs/PUBLIC_STANCE.md) | Location comparison |
| AR-03 | pending | alignment | Review goal alignment after AU-09. | Goal plus verified task log | Recorded no-code review |
| AU-10 | pending | AU-4 | Select the revised speech attempt from the supplied public stance. | [Public-Counter Stance](specs/PUBLIC_STANCE.md) | Policy counterfactual test |
| AU-11 | pending | AU-4 | Preserve understanding when the revised speech attempt is rejected. | [Public-Counter Stance](specs/PUBLIC_STANCE.md) | Rejection integration test |
| AU-12 | pending | AU-5 | Write the earlier official schedule claim into the physical diary. | [Diary Resurfacing](specs/DIARY_RESURFACING.md) | Diary source test |
| AR-04 | pending | alignment | Review goal alignment after AU-12. | Goal plus verified task log | Recorded no-code review |
| AU-13 | pending | AU-6 | Create the private-diary stance from one delivered diary read. | [Diary Resurfacing](specs/DIARY_RESURFACING.md) | Delivered-read comparison |
| AU-14 | pending | AU-7 | Select the first archive-bound travel step from the private stance. | [Diary Resurfacing](specs/DIARY_RESURFACING.md) | Policy counterfactual test |
| AU-15 | pending | AU-7 | Stop the recheck intention after one post-diary consultation. | [Diary Resurfacing](specs/DIARY_RESURFACING.md) | Single-recheck integration test |
| AR-05 | pending | alignment | Review goal alignment after AU-15. | Goal plus verified task log | Recorded no-code review |
| AU-16 | pending | AU-8 | Prove focal-private understanding stays absent from other actors' inputs. | [Knowledge Boundaries](specs/KNOWLEDGE_BOUNDARIES.md) | Restricted-input regression test |
| AU-17 | pending | AU-8 | Prove stance transitions create no observations or world consequences. | [Knowledge Boundaries](specs/KNOWLEDGE_BOUNDARIES.md) | Side-effect regression test |
| AU-18 | pending | AU-9 | Render the focal explanation from explicit understanding projection data. | [Understanding Presentation](specs/PRESENTATION.md) | Normal-output test |
| AR-06 | pending | alignment | Review goal alignment after AU-18. | Goal plus verified task log | Recorded no-code review |
| AU-19 | pending | AU-9 | Render omniscient understanding evidence in the inspector. | [Understanding Presentation](specs/PRESENTATION.md) | Inspector evidence test |
| AU-20 | pending | AU-9 | Complete the authored `first_day_v3` Agent Understanding path. | [Understanding Presentation](specs/PRESENTATION.md) | End-to-end scenario test |
| AU-21 | pending | AU-10 | Reproduce equal detached `first_day_v3` histories. | [Reproduction](specs/REPRODUCTION.md) | Complete-run equality test |
| AR-07 | pending | alignment | Review goal alignment after AU-21. | Goal plus verified task log | Recorded no-code review |
| AU-22 | pending | AU-10 | Close the goal from complete validated evidence. | [Reproduction](specs/REPRODUCTION.md) | Full check plus completion review |

## Task Update Rules

- At run start, change the active task from `next` to `in_progress`.
- After validation and review, change it to `complete`.
- Mark exactly one following task `next`.
- Record concise observed evidence in the log below; repository history records
  the commit identifier.
- Alignment tasks use orchestrator self-review, update this file, commit the
  review record, and exit without implementation.
- If implementation reveals a larger task, restore its status to `pending`,
  insert smaller ordered tasks before it, and exit without a partial commit.
- If the task needs owner authority, leave code unchanged and record the
  decision needed.

## Verified Task Log

No implementation task has been completed for this goal.
