# Thin Harness, Fat Skills

Status: proposed architecture direction, not an active implementation goal.

This document generalizes lessons from the completed model-backed Mara boundary.
The current repository has one versioned Mara profile, one authored
`choose-next-action` skill, a narrow request composer and Ollama adapter, a
strict structured-choice parser, and a deterministic simulation that alone
changes world state. It does not yet have a generic skill catalog or resolver,
model tools, a reusable agent harness, automatic skill improvement, or a
model-backed supporting cast.

Any broader implementation requires a new owner-approved goal. The current
factual architecture remains defined by [Architecture](ARCHITECTURE.md); the
completed first application is recorded in the
[Model-Backed Focal Character evidence](../plans/model-backed-focal-character/IMPLEMENTATION_PLAN.md).

## Objective

Guide later agent systems toward three layers:

1. **Skills** contain reusable procedures, domain judgment, and decision logic.
2. **Harness** runs the model and coordinates execution while staying small.
3. **Application tools** perform deterministic operations against real systems and data.

The model should handle interpretation and judgment. Code should handle repeatable execution, validation, calculations, and state changes.

## Core Architecture

### 1. Skills

A skill is a reusable Markdown procedure that defines **how** an agent performs a class of tasks.

Each skill should include:

- A clear purpose and activation description
- Required inputs or parameters
- Ordered execution steps
- Decision rules and domain constraints
- Required tools or context
- Expected output format
- Validation and failure conditions

Task-specific values belong in the invocation, not the skill. One skill should support multiple tasks by accepting different parameters.

Example interface:

```text
Skill: investigate
Inputs: target, question, dataset
Output: evidence-backed findings with citations
```

### 2. Harness

The harness is the program that operates the agent. It should only:

- Run the model and manage its execution loop
- Load relevant context
- Expose file and tool access
- Track session state or memory
- Enforce permissions and safety constraints
- Route tasks to the correct skills and tools

Keep the harness thin. Do not embed domain workflows, large instruction sets, or application-specific logic directly in it.

Preferred interface:

```text
JSON input -> thin harness -> model + selected skills/tools -> structured output
```

Start with a CLI. Add MCP or other integrations only when a real consumer requires them.

### 3. Deterministic Application Tools

Application tools provide reliable operations such as:

- Database queries
- File reads and writes
- Search and retrieval
- API calls
- Calculations and aggregation
- Validation and health checks
- State changes

Tools should be narrow, composable, testable, and read-only by default. Prefer a small CLI or library over exposing every API endpoint as a separate model tool.

## Context Routing

Use a resolver to decide what context or skill to load for a task.

A resolver maps intent to required context:

```text
task type -> skill or document to load
```

Requirements:

- Skill descriptions must clearly state when the skill applies.
- Load only the context needed for the current task.
- Keep global agent instructions short and use pointers to detailed documents.
- Load required validation rules before allowing the agent to complete a change.
- Avoid placing all project knowledge in one permanent context file.

## Work Allocation Rules

Classify every operation as either **latent** or **deterministic**.

| Use the model or a skill when the operation requires | Use code or a tool when the operation requires |
| --- | --- |
| Interpretation | Exact calculation |
| Judgment | Repeatable transformation |
| Synthesis across sources | Lookup or status retrieval |
| Handling ambiguity | Validation against explicit rules |
| Adapting to conversation or environment | Reliable state changes |
| Asking clarifying questions | Identical output for identical input |

Rule of thumb:

> If the agent must think, adapt, or ask questions, use a skill. If the same input should always produce the same output, use code.

Do not use the model for large-scale assignment, counting, validation, or calculation when a deterministic algorithm can perform the operation correctly.

## Diarization Pattern

Diarization converts many source documents into one structured profile containing judgment, conflicts, and changes over time.

Use it when the agent must:

- Read multiple sources about one subject
- Reconcile conflicting claims
- Compare stated intent with observed evidence
- Identify changes over time
- Produce a compact, structured assessment

Minimum workflow:

1. Retrieve all relevant sources.
2. Record source identity and time.
3. Extract claims, events, and evidence.
4. Identify agreements, contradictions, and changes.
5. Produce a structured profile with source references.

## Learning Loop

For repeatable workflows, prefer improving a reviewed skill rather than adding
complexity to the harness.

1. Run the workflow on real examples.
2. Collect outcomes and user feedback.
3. Analyze failures and mediocre results.
4. Convert recurring lessons into explicit skill rules.
5. Validate the revised skill against prior examples.
6. Reuse the updated skill on future runs.

Skill changes must be owner-authorized, reviewable, version-controlled, and
evaluated against prior behavior. Do not allow an agent to silently rewrite
production instructions based on a single result. No automatic skill-rewriting
loop exists in 2084 today.

## Implementation Constraints

- Keep the harness small and domain-agnostic.
- Put reusable reasoning procedures in Markdown skills.
- Put exact operations in deterministic code.
- Minimize the number and size of exposed tools.
- Avoid broad tools that combine unrelated actions.
- Prefer local, fast operations where possible.
- Use structured inputs and outputs at component boundaries.
- Load context on demand instead of keeping everything in the model context.
- Make write operations explicit and permission-controlled.
- Log tool calls, inputs, outputs, errors, and skill versions.
- Add deterministic validation for important outputs.
- Test tools independently from model behavior.
- Evaluate skill changes on representative cases before release.

## Anti-Patterns

Avoid:

- A large harness containing domain-specific workflows
- Dozens of redundant or low-level model tools
- Wrapping every REST endpoint as a separate tool
- One global instruction file containing all project knowledge
- Using an LLM for exact calculations or large deterministic assignments
- Allowing the model to mutate data without explicit tools and permissions
- Encoding task-specific values inside reusable skills
- Treating retrieval alone as synthesis or judgment
- Automatically changing production skills without review and evaluation

## Agent Build Checklist

Before implementing a feature:

1. Define the task inputs, outputs, and success criteria.
2. Separate judgment steps from deterministic steps.
3. Put reusable judgment and procedure in a skill.
4. Put repeatable operations in code or a CLI tool.
5. Add a resolver rule or precise skill description.
6. Specify required context and load it only when needed.
7. Default tools to read-only access.
8. Add validation, logging, permissions, and failure handling.
9. Test deterministic tools separately.
10. Evaluate the complete workflow on representative examples.

## Component Boundary Summary

| Component | Owns | Must not own |
| --- | --- | --- |
| Skill | Procedure, judgment, domain rules, output expectations | Direct system implementation |
| Harness | Model loop, routing, context, permissions, session state | Domain-specific business logic |
| Tool or application | Exact execution, data access, validation, state changes | Open-ended reasoning |
| Resolver | Intent-to-context routing | Full task execution |

The target design is a thin coordination layer, rich reusable skills, and deterministic tools underneath.
