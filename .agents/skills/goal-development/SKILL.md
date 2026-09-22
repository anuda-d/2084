---
name: goal-development
description: Advance one approved development goal through coherent implementation and behavioral verification. Use when the development runner asks for the next useful change or continuation of unfinished work.
---

# Goal development

Select the smallest coherent change that meaningfully advances the approved goal.
Carry it through implementation and verification, and judge completion against observable behavior.

Read the approved goal, the project's current index, and the relevant implementation before choosing work.
State the concrete missing behavior or guarantee and how you will establish it in a few lines.
Continue unfinished work before selecting another responsibility.
Do not create task contracts, future task queues, ledgers, or repeated operational summaries.

Investigate before committing to an approach.
Exercise relevant existing behavior and reproduce reported bugs through the closest practical user flow.
Revise the implementation plan when evidence contradicts it.
Make routine engineering decisions independently within the goal.
Ask only when missing product direction or a consequential change to agreed constraints requires the owner.

Complete the selected responsibility through its necessary code, integration, failure paths, compatibility, and validation.
Reuse existing capabilities, remove superseded paths, and introduce abstractions for demonstrated needs.
A file move or helper extraction counts only when it closes a concrete acceptance gap or indispensable blocker.
An enforceable internal guarantee can be observable progress even when presentation stays unchanged.

Use focused checks during implementation and establish that they exercise the outcome being claimed.
The runner performs the configured repository checks and records operational evidence.
Request independent review for semantic risks, weakly covered behavior, or consequential changes to boundaries, even if automatic path checks miss them.
Do not weaken checks or goal criteria to obtain acceptance.

Keep durable module interfaces and invariants in types, executable tests, and relevant documentation.
Change them with the implementation when authorized and necessary.
Do not regenerate them every task.

Return the requested compact result: what changed, the behavioral evidence, any review concern, and the remaining gap.
The runner owns Git staging, commits, review dispatch, and runtime records.
Do not commit, push, merge, deploy, change the runner configuration, or manipulate its state.
A time limit is a pause, not completion; preserve unfinished work and state the next concrete step.
Declare the goal complete only when every approved criterion has supporting evidence.

Load project-specific examples and constraints from the context files named in the runner prompt.
