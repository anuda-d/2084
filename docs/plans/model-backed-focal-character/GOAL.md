# Model-Backed Focal Character

Status: active; owner-approved on 2026-08-19.

This is the bounded Phase 3B implementation goal described in
[The Lie and Doublethink architecture](../LIE_AND_DOUBLETHINK_ARCHITECTURE.md).
It begins with the focal character only.

## Question

Can Mara's actual decisions and expressions be produced by an AI model from
only her restricted character state, while the simulation retains authority
over knowledge, physical possibility, action resolution, and objective truth?

## Goal Result

Add one model-backed focal-character mode to the existing living simulation.
When this mode is active, a valid structured model choice becomes Mara's
attempted action. No hidden hand-written policy may replace or reinterpret a
valid model choice before world resolution.

Mara remains a persistent simulation character rather than a disposable prompt.
Her identity, embodied state, delivered observations, source-linked
understanding, accessible objects, aims, prior attempts, and resolved outcomes
remain explicit state. The model receives a restricted projection of that state
and supplies her next attempted action and, where appropriate, expression.

The existing deterministic focal policy remains available as a regression and
comparison mode. It is not a silent fallback for model-backed Mara.

## Model-Character Boundary

The model-backed focal policy owns:

- adapting the focal character's restricted decision view into model input;
- presenting a small, authored focal identity and current agent-owned state;
- asking for exactly one structured attempted action at a decision point;
- interpreting a schema-valid response into the existing action-attempt form;
- recording enough detached decision evidence for inspection and reproduction;
- producing an explicit safe failure result when no valid model decision is
  available.

It does not own:

- objective world state or event history;
- observation recipient selection or delivery;
- canonical memory provenance, claim conflict, or stance transitions;
- another character's private state;
- physical access, action validity, duration, success, or consequence;
- official-record or institutional mutation;
- direct mutation of character state;
- normal-observer access to hidden prompts or private inspector evidence.

## Character Continuity

The focal model input must contain only explicit, agent-safe material needed for
the current choice. At minimum, it must distinguish:

- stable authored identity and role;
- current aims and obligations;
- current location, holdings, and accessible objects;
- delivered observations and retained understanding available to Mara;
- prior attempted actions and completed or rejected results relevant to the
  bounded run;
- available action kinds and enough agent-safe parameter constraints to propose
  a valid attempt.

Opaque provider conversation history must not become Mara's only memory. A
model may reason and plan from supplied state, but persistent facts that affect
later simulation decisions must remain inspectable simulation state or an
explicitly recorded decision artifact.

## Live, Test, and Recorded Modes

The implementation may use one narrow model-client interface with one initial
live adapter. Do not build a general multi-provider framework without a second
real adapter.

- **Live model mode** calls the configured model and records its decision
  envelope. Credentials remain external configuration and must never enter
  prompts, events, history exports, fixtures, or committed files.
- **Test model mode** uses a deterministic fake through the same boundary. The
  repository check must not require network access, credentials, or paid calls.
- **Recorded-decision mode** reuses previously recorded structured choices
  without calling a model. It exists to reproduce world behavior, not to claim
  that live model sampling is deterministic.

A timeout, unavailable model, malformed response, unsupported action, or
invalid parameter set must be recorded explicitly. It may yield a safe `wait`
attempt or actor-safe rejection, but it must not secretly invoke the legacy
scripted focal policy.

## Invariants

- `EventLog` remains append-only objective evidence.
- A model receives no objective, undelivered, inspector-only, institutional
  private, or other-agent private state.
- Prompt text and model output do not become observations or objective facts
  merely because the model produced them.
- A valid model choice creates an attempted action, not a successful outcome.
- Existing world validation and resolution remain authoritative.
- Rejected and completed outcomes return through the existing actor-safe result
  boundary before they can affect a later decision.
- Model-backed execution does not mutate Agent Understanding except through an
  already valid delivered-observation or explicit future mechanism outside this
  goal.
- Normal focal presentation does not expose hidden model configuration, raw
  prompts, private decision records, or credentials.
- The inspector can distinguish model input, model response, attempted action,
  validation, and resolved consequence.
- Live model variability is described honestly; deterministic tests and
  recorded-decision reproduction do not imply deterministic live sampling.

## Completion Criteria

- **MF-1 Actual character decision:** In model-backed mode, Mara's schema-valid
  model choice becomes her attempted action without a scripted chooser
  substituting a different action.
- **MF-2 Restricted decision envelope:** The model input contains a stable focal
  identity, relevant agent-owned state, and agent-safe action affordances while
  excluding hidden world, inspector, institution, and other-agent private data.
- **MF-3 Structured action contract:** The model can choose only a supported
  attempted action with validated parameter shapes; prose alone cannot mutate
  or advance the simulation.
- **MF-4 World-owned consequence:** Existing resolution accepts, schedules, or
  rejects model-selected attempts and returns actor-safe results without giving
  the model direct authority over consequences.
- **MF-5 Decision continuity:** A later focal decision can respond to relevant
  completed or rejected results and persistent character state without relying
  on opaque provider chat history as canonical memory.
- **MF-6 Explicit failure:** Timeout, unavailable-model, malformed-response, and
  invalid-attempt paths are inspectable and never fall through to the scripted
  focal policy.
- **MF-7 Decision evidence and privacy:** Inspector-only detached records link
  the restricted input, model configuration identity, structured response,
  attempted action, and resolution while excluding credentials and normal-view
  leaks.
- **MF-8 Recorded reproduction:** A recorded-decision run can reproduce equal
  ordered world history without a live model call; deterministic fake-model
  tests cover the same boundary without network access.
- **MF-9 Bounded behavioral proof:** One focal decision point demonstrates that
  changing the model's valid structured choice changes Mara's attempted action
  and subsequent resolved world behavior without changing the supplied world
  state or granting hidden knowledge.
- **MF-10 Integration:** The existing deterministic `first_day` behavior remains
  available as a regression comparison, the documented model-backed entry path
  is usable with external credentials, normal and inspector projections retain
  their boundary, and the full repository check passes offline.

## Out of Scope

- Model-backed supporting characters or institutions
- General multi-agent conversation or a new dialogue system
- Confidence change, inhibition, memory decay, emotion, or theory of mind
- Letting a model create canonical memories or claims from arbitrary prose
- New action kinds solely to make a model demonstration more dramatic
- Claim and Provenance or Observation Delivery extraction
- Official Record suppression or fabrication
- A general multi-provider framework, model router, training, or fine-tuning
- Graphical UI, production deployment, billing systems, or account management
- Treating live model output as deterministic
- Forcing the existing first-day plot and presenting it as emergence

## Specification Routing

This goal is the authoritative bounded specification. After selecting one
smallest useful gap, consult only the relevant implementation and tests plus:

- the [Phase 3B boundary](../LIE_AND_DOUBLETHINK_ARCHITECTURE.md#phase-3b-embody-the-focal-character-with-a-model);
- the AI direction in [Core Construct](../../main/CORE_CONSTRUCT.md#ai);
- the decision and resolution boundary in
  [Architecture](../../main/ARCHITECTURE.md#decisions-and-resolution).

Provider-specific documentation is required only when implementing the one live
adapter. Provider selection, credentials, and account setup must not leak into
the general character or world interfaces.

## Completion Boundary

Complete MF-1 through MF-10 through fresh, single-work-unit runs selected from
verified repository evidence. Do not create a future task queue. Goal completion
requires proportionate offline evidence for every criterion and one successful,
explicitly opt-in live-model smoke test using external credentials. If live
credentials are unavailable, record that as an owner blocker rather than
weakening the criterion or committing a secret.

After an independent whole-goal review confirms the boundary, evidence, and
documentation, mark the goal complete, commit the final state update, and stop
before selecting another goal.
