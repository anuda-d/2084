# 2084: First Living Simulation Slice

> Historical implementation brief. The completed reusable engine was later
> promoted from `experiments/` to `twenty_eighty_four/`; use the commands in the
> root `README.md` rather than the paths recorded below.

## Codex implementation goal

Build the first reusable, deterministic, autonomous simulation loop for **2084** from the existing experimental implementation. The result should simulate one focal character completing a small ordinary sequence inside a partially observable authoritarian social world.

The implementation must preserve the project's established distinctions between:

- objective world state;
- events that actually occurred;
- observations delivered to particular agents;
- memories and private beliefs derived from those observations;
- public expressions and attempted actions;
- world resolution and consequences;
- the restricted focal-character presentation;
- the omniscient development inspector.

This is an engine and feasibility milestone. It is not a graphical game, a complete society, or an LLM-agent demonstration.

---

## 1. Repository and starting-point recovery

Repository: `anuda-d/2084`

Before changing code, read these documents in full:

1. `README.md`
2. `CORE_CONSTRUCT.md`
3. `ARCHITECTURE.md`
4. `UI_ARCHITECTURE.md`
5. `DESIGN_REFERENCES.md`
6. `AGENTS.md`

Treat those documents as the source of product direction. Do not silently revise their core boundaries while implementing this goal.

### Existing implementation

The visible `main` branch may contain only the initial design documents. Prior pull requests contain an experimental Python implementation, including source-linked history, deterministic scenario behavior, a terminal observer, a physical diary, and an extensive test suite.

Recover the latest implementation before starting over. Prefer the head of PR #3:

```bash
git fetch origin pull/3/head:recover-agent-loop
git switch recover-agent-loop
```

If the pull-request reference is unavailable, try the recorded head commit:

```bash
git fetch origin 869069a0968efbbb5404119a56730e1b67ad3612
git switch -c recover-agent-loop FETCH_HEAD
```

Run the existing validation command if present:

```bash
./scripts/check.sh
```

If the recovered code and tests cannot be obtained, document that fact before recreating only the minimum implementation required by this goal.

### Recovery acceptance criteria

- The recovered implementation is placed on a normal branch.
- Existing tests are executed before refactoring.
- Any initially failing tests are recorded separately from failures introduced by new work.
- No working implementation is discarded merely because its structure is provisional.
- The recovery branch is not force-pushed over `main`.

---

## 2. Problem statement

The existing experiment appears to prove several important concepts, but much of the behavior is composed inside a large fixed scenario. It is closer to a deterministic demonstration than a reusable living simulation.

The next step is to extract a small engine that can repeatedly advance time, update relevant world systems, deliver limited observations, allow agents to select actions, resolve those actions against objective state, and present an appropriately filtered view.

The engine should make it possible to define a scenario as initial state and configured pressures rather than as one long prescribed sequence of function calls.

The implementation must still be small. Generalization is useful only where it supports the first living slice.

---

## 3. Product outcome

Provide a runnable terminal simulation in which one focal character autonomously experiences an ordinary resource-allocation contradiction over approximately 20 to 30 ticks.

During the run:

1. The character begins at home with an ordinary need and responsibility.
2. The character moves through a small world containing a home, workplace, and allocation office.
3. The character directly observes one resource amount.
4. An institution later broadcasts a contradictory official amount.
5. The character forms or retains a private belief grounded in delivered evidence.
6. The character requests resources based only on available observations, beliefs, needs, and constraints.
7. The world resolves the request using objective state that the character may not know.
8. A supporting character independently performs at least one relevant scheduled or reactive action.
9. Under sufficient public or institutional pressure, the focal character may publicly repeat a claim that differs from their private belief.
10. The focal character can write their limited perspective into a physical diary when time and access permit.
11. The terminal observer explains the visible sequence without leaking hidden world or institutional state.
12. A separate development inspector can expose objective records for debugging.

The interesting behavior must result from state, observations, schedules, and explicit decision policies. Do not hardcode a required rebellion, betrayal, arrest, or predetermined dramatic ending.

---

## 4. First-slice scope

### Required world

- One focal character.
- Two supporting characters.
- Three locations:
  - home;
  - workplace;
  - allocation office.
- One institution that can:
  - broadcast an official claim;
  - possess objective or institutional records;
  - receive only observations or reports available to it;
  - operate with bounded information.
- One resource pressure, such as a ration or household allocation.
- One structured contradiction between direct experience and an official claim.
- One physical diary object.

Names, quantities, and exact setting details should remain clearly provisional unless already established in project documentation.

### Minimum action vocabulary

Implement only the actions needed for the slice:

- `travel`
- `work`
- `request_allocation`
- `speak`
- `write_diary`
- `read_diary`
- `wait`

An action is an attempt. Selecting an action must not automatically make it succeed.

### Minimum agent state

Each relevant agent should have only the state needed by the slice:

- identity;
- current location;
- current aim or need;
- schedule or immediate obligation;
- observations received;
- a small set of structured beliefs;
- relationships or pressure values only if they affect a decision;
- current plan or next intended action;
- physical possession when relevant.

Avoid generic personality matrices, emotional simulations, full natural-language memory, or broad theory-of-mind systems.

---

## 5. Required architecture boundaries

The exact filenames may vary, but responsibilities must be separated clearly. A reasonable target structure is:

```text
experiments/
    core/
        events.py
        world.py
        observations.py
        beliefs.py
        agents.py
        actions.py
        simulation.py
    policies/
        focal_policy.py
        supporting_policy.py
        institution_policy.py
    scenarios/
        first_day.py
    observer/
        terminal.py
        inspector.py
    tests/
```

Do not perform a mechanical file split merely to match this tree. Extract responsibilities gradually while preserving behavior and tests.

### 5.1 Objective world state

Owns facts that are true inside the simulation, including:

- tick and simulation seed;
- locations and permitted travel;
- physical objects and possession;
- actual resource quantities and commitments;
- agent locations;
- recorded events;
- institutional operations and records.

An official claim must never overwrite objective history. A correction or revision is a new event.

### 5.2 Events and append-only history

Every consequential occurrence should create an immutable event with at least:

- stable event identifier;
- tick;
- event kind;
- actor or responsible system when applicable;
- structured details;
- links to the attempted action or prior event when applicable.

The run must retain enough information to inspect causal order and replay surprising behavior.

### 5.3 Observations

Observations are agent-specific deliveries derived from events. Each observation should retain:

- stable observation identifier;
- receiving agent;
- source event;
- source or channel;
- delivery tick;
- structured perceived details.

An agent must never query global history or objective state through its decision policy.

### 5.4 Memory and beliefs

Use structured claims for the first contradiction. A belief should minimally record:

- proposition;
- asserted value;
- source observation or observations;
- confidence;
- last updated tick;
- context if the accepted or expressed version varies by context;
- explicit conflict links where known.

Confidence updates should use small, inspectable rules. Do not ask an AI model to infer every contradiction from prose.

### 5.5 Decision policies

A decision policy may inspect only information available to that agent:

- location and physical access;
- delivered observations;
- memories and beliefs;
- needs and obligations;
- perceived pressure and relationships;
- available action definitions;
- current tick and schedule information the agent knows.

It returns an attempted action and a concise explanation artifact. It cannot mutate world state, invent observations, or declare success.

### 5.6 Action resolution

The world resolver validates attempts and applies consequences. It should:

- verify location, possession, time, and resource requirements;
- reject impossible actions without corrupting state;
- advance time or schedule completion appropriately;
- resolve against objective world state;
- create linked outcome events;
- deliver resulting observations only to eligible agents;
- remain deterministic under the same configuration and seed.

### 5.7 Observer projection

The normal terminal observer may show only:

- the focal character's location and visible surroundings;
- their current or recently attempted action;
- observations actually delivered to them;
- an intentionally readable summary of their current aim, beliefs, uncertainty, and decision explanation;
- public events they could perceive;
- diary entries they can physically access.

It must not expose:

- hidden resource commitments;
- unseen NPC actions;
- private NPC beliefs;
- unprocessed institutional reports;
- objective truth merely because it exists in the engine.

The development inspector may expose those details, but it must be a separate command, mode, or clearly labelled output.

---

## 6. Simulation loop

Implement a reusable step operation with an order similar to:

```text
1. Start tick
2. Apply scheduled world and institutional events
3. Complete actions whose duration has elapsed
4. Generate eligible perceptions and deliver observations
5. Update affected beliefs
6. Ask idle agents to choose one valid attempted action
7. Validate and begin or immediately resolve those attempts
8. Record events and queue resulting observations
9. Produce focal-character presentation
10. End tick
```

The exact order may change if tests show a clearer model, but it must be explicit and consistent. Avoid accidental same-tick omniscience, such as an agent responding to an event before its observation is delivered.

The public API should support at least:

```python
simulation = build_first_day(seed=42)
snapshot = simulation.step()
simulation.run(max_ticks=30)
```

The engine should also expose a completion condition so a scenario does not depend only on arbitrary process termination.

---

## 7. Determinism and replay

The first slice must be deterministic.

- All randomness comes from a run-scoped seeded generator.
- Do not use global random state.
- Record the configuration and seed.
- Stable input plus stable seed must produce the same ordered event history.
- Different seeds may change bounded choices if randomness is actually used.
- A replay or serialization format may remain simple, but event history must be serializable to JSON-compatible data.

Do not introduce distributed execution, background workers, real-time clocks, or an always-running server.

---

## 8. Terminal experience

Provide one documented command, preferably:

```bash
python3 -m experiments.scenarios.first_day
```

Accept useful optional flags if they remain simple:

```bash
python3 -m experiments.scenarios.first_day --seed 42 --ticks 30
python3 -m experiments.scenarios.first_day --seed 42 --ticks 30 --inspect
```

Normal output should prioritize watchability. For each meaningful tick, show a compact record such as:

- current time and location;
- visible situation;
- focal character's current aim;
- selected or completed action;
- concise reason based on available information;
- newly delivered observation or consequence;
- important belief uncertainty when it changes.

Do not print raw object dumps or hidden development data in the normal view.

The inspector output should make debugging possible by showing event identifiers, observation provenance, objective resource state, action attempts, resolution links, and belief transitions.

---

## 9. Implementation phases

### Phase 0: Recover and baseline

- Recover the latest PR implementation.
- Run all tests.
- Identify existing modules and responsibilities.
- Record the current runnable commands.
- Write a short baseline note describing what is fixed-script behavior versus reusable behavior.

Completion condition: existing behavior is understood and protected by tests.

### Phase 1: Introduce a reusable simulation container

- Add explicit run configuration, tick, seed, world state, agent registry, event history, and observation delivery.
- Implement `step()` without changing scenario behavior more than necessary.
- Move the existing fixed scenario through the step boundary incrementally.

Completion condition: at least one existing decision and resolution occurs through `Simulation.step()`.

### Phase 2: Add spatial and temporal constraints

- Represent the three locations and permitted travel.
- Make travel consume ticks.
- Add small schedules or obligations.
- Ensure diary access depends on location or possession.

Completion condition: an impossible remote action is rejected, and agents can move to gain access.

### Phase 3: Convert the allocation contradiction

- Represent objective allocation, direct observation, official claim, private belief, and public expression as distinct records.
- Ensure the focal policy chooses from delivered evidence only.
- Resolve requests against objective supply.
- Preserve causal links among attempt, resolution, and delivered outcome.

Completion condition: the contradiction changes understandable behavior without changing objective history.

### Phase 4: Add supporting autonomy

- Give two supporting characters minimal schedules or policies.
- Require at least one supporting action to occur without being directly invoked by the focal character.
- Allow only observable supporting actions to enter the focal view.

Completion condition: the wider world visibly advances while hidden NPC state remains private.

### Phase 5: Integrate the diary

- Preserve the existing physical diary mechanics where possible.
- Require access and simulated time for reading and writing.
- Record the focal character's perspective, not objective truth.
- Permit a diary entry to preserve an earlier belief after an official revision.

Completion condition: a later read returns the same immutable perspective-bound entry.

### Phase 6: Terminal observer and inspector

- Render a concise focal-character transcript.
- Add a clearly separate inspector mode.
- Verify normal output does not depend on hidden fields.

Completion condition: a person can understand the main behavioral sequence from the normal transcript, while a developer can audit causality through the inspector.

### Phase 7: Cleanup and documentation

- Remove dead provisional paths only after equivalent behavior is protected.
- Update the experiment README with commands and limitations.
- Document the tick order and state boundaries.
- Record unresolved questions rather than silently choosing permanent answers.

Completion condition: the slice is runnable, tested, and understandable without reading one giant scenario function.

---

## 10. Testing requirements

Preserve existing tests and add focused tests for the reusable engine.

### Determinism

- Same configuration and seed produce identical ordered events.
- Event and observation identifiers remain stable for identical runs.
- Running tests in a different order does not affect results.

### Knowledge boundaries

- A decision policy cannot access objective allocation state.
- An undelivered observation cannot affect a decision.
- A supporting character's private belief does not appear in the focal view.
- Institutional action cannot use a private diary entry unless a valid observation or report path exists.

### Action and resolution separation

- Selecting an action does not mutate the world.
- Impossible actions fail without partial mutation.
- Resolved actions link to their attempted action.
- Resource resolution uses objective state rather than the requesting agent's belief.

### Time and location

- Travel consumes time.
- Reading or writing the diary requires physical access.
- Writing cannot complete before it begins.
- Agents do not respond to an observation before its delivery tick.

### Contradictions and belief

- Direct experience and official claims can coexist as conflicting claims.
- Official revision does not overwrite objective history.
- Public expression may differ from private belief under explicit conditions.
- The difference is traceable to pressure and evidence, not a hardcoded story beat.

### Presentation privacy

- Normal transcript contains no hidden allocations or commitments.
- Normal transcript contains no unseen events.
- Inspector mode contains the necessary provenance and resolution evidence.
- User-facing decision explanations summarize factors but do not expose raw model reasoning.

### Diary

- Non-possessors cannot write or read.
- Writing consumes time.
- An entry retains the author's perspective at writing time.
- Reading returns the same immutable entry.
- Diary content does not become institutional knowledge automatically.

---

## 11. End-to-end acceptance scenario

A default run with seed `42` should demonstrate all of the following, without requiring exact prose:

1. The focal character starts at home with an ordinary allocation need.
2. At least one supporting character advances independently.
3. The focal character travels to or attends an appropriate location.
4. They directly observe a structured resource claim.
5. An institution later issues an incompatible structured claim.
6. Both claims retain source and time provenance.
7. The focal character attempts an allocation request using only delivered evidence.
8. The resolver grants or denies resources using hidden objective commitments.
9. The result is delivered back as an observation.
10. The focal character chooses a follow-up action based on that delivered result.
11. Their private belief and public statement can diverge for an explicit, inspectable reason.
12. They write their perspective into a physically accessible diary.
13. A later diary read returns that earlier perspective even if official claims changed.
14. The normal terminal view shows a coherent life sequence without hidden-state leakage.
15. Inspector mode can reconstruct the causal chain.
16. Repeating the run with seed `42` produces the same ordered event history.

The end-to-end test should assert structured facts and event relationships, not exact decorative narration.

---

## 12. Definition of done

The goal is complete when:

- Existing implementation history has been recovered or its absence documented.
- Existing tests still pass, except for explicitly justified replacements.
- A reusable `Simulation.step()` boundary exists.
- The first-day scenario is expressed primarily as configured initial state, schedules, policies, and events rather than one prescribed function sequence.
- One focal character and two supporting characters act over 20 to 30 ticks.
- Three locations constrain behavior.
- The required action vocabulary is supported.
- Objective truth, observation, belief, public expression, and resolution remain distinct.
- At least one meaningful private/public contradiction affects behavior.
- The diary remains physical, perspective-bound, and time-constrained.
- The normal terminal view is filtered correctly.
- A separate inspector exposes causal evidence.
- Same-seed replay is deterministic.
- The documented run command works from a clean checkout.
- Tests cover the acceptance criteria.
- Documentation explains current limitations and does not overclaim human realism or emergence.

---

## 13. Explicit non-goals

Do not include these in this goal:

- Graphical UI, map, animation, or game engine integration.
- Web application or API deployment.
- LLM-based autonomous decision-making.
- Generated dialogue as a prerequisite for simulation behavior.
- Vector databases or semantic memory.
- Hundreds or thousands of agents.
- A full economy, political system, surveillance network, or language-control system.
- Always-running simulation time while the program is closed.
- Multiplayer features.
- Observer intervention or direct character control.
- Complex diary concealment, confiscation, discovery, or evidence mechanics.
- Claims that the simulation reproduces consciousness or accurately predicts human behavior.
- Recreating Orwell's characters, plot, institutions, or exact world.

If an implementation choice begins pulling in one of these areas, stop and reduce scope.

---

## 14. LLM integration boundary for later work

Do not integrate an LLM in this milestone. Preserve an interface that could later allow a model to recommend an action or phrase dialogue.

Any later model integration must follow these constraints:

- Input contains only the agent's allowed observations, memories, beliefs, aims, and currently valid actions.
- Output uses a validated structured schema.
- The model can recommend an attempted action, not resolve it.
- The model cannot create world facts, observations, inventory, permissions, or outcomes.
- Invalid output falls back to a deterministic policy.
- Consequential simulation state remains owned by explicit engine code.
- Model-generated prose is presentation, not evidence of an event.

---

## 15. Engineering principles

- Prefer the smallest mechanism that produces visible behavior.
- Preserve existing behavior before refactoring it.
- Add one abstraction only when two or more concrete behaviors require it.
- Keep authored starting conditions separate from engine rules.
- Keep scenario drama out of core mechanisms.
- Treat every important statement as a sourced claim rather than automatic truth.
- Make temporal order explicit.
- Fail closed when an action lacks authority, knowledge, location, or resources.
- Retain provenance for important decisions and consequences.
- Test hidden-information boundaries as seriously as successful behavior.
- Explain assumptions that materially affect the simulated behavior.

---

## 16. Required delivery report

At completion, provide:

1. A concise description of the implemented simulation.
2. The branch and commit used as the recovered starting point.
3. A summary of architectural changes.
4. Exact commands to run the simulation, inspector, and tests.
5. Test results.
6. A short example transcript.
7. Known limitations.
8. Any state-boundary or product-direction decisions that require owner review.
9. A list of tempting follow-up features that were intentionally excluded.

Do not claim that behavior is emergent merely because it was not manually selected during the run. State exactly which rules, schedules, starting conditions, and seeded choices produced it.
