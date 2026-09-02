# 2084

2084 is a terminal-based social-simulation prototype about following one autonomous person through a world they can only partly understand.

The long-term idea is to watch a life unfold inside a small society shaped by lies, contradictions, institutions, relationships, limited information, and pressure.
The focal character is not a player-controlled puppet and does not know everything the simulation knows.
Other people and institutions continue acting while the observer sees the world mainly through that character's experience.

The project takes thematic inspiration from George Orwell's *Nineteen Eighty-Four*, especially the gap between lived experience, public behavior, and official accounts.
It is not an adaptation of Orwell's plot, characters, or setting.

## What exists today

The repository contains two runnable scenario compositions built on the same explicit world-authority, limited-knowledge, and observer boundaries.

`first_day_v3` follows Mara Vale and two supporting characters through a 28-tick authored workday.
Its deterministic scripted focal policy is the default, while an explicitly selected local model can choose Mara's attempted actions instead.
In the scripted comparison, Mara:

- travels between home, work, and a civic allocation office;
- sees three allocation units but physically receives only two;
- consults an official schedule that initially promises three packets;
- experiences public pressure, encounters the revised two-packet schedule, and repeats that revised entitlement publicly while retaining separate evidence;
- writes the earlier three-packet schedule claim into a physical diary;
- reads that entry later and makes one ordinary trip to recheck the public schedule; and
- finishes the day with one household unit still unmet.

The scripted route is heavily authored, but the characters are not moved directly by a player.
Transparent rule-based policies choose attempted actions from limited information.
In model-backed mode, the local model chooses Mara's attempts instead, while supporting characters remain rule-based.
In both modes the simulation checks each attempt and alone decides what actually happens.

`autonomous_day` is a separate accelerated composition that advances from `Day 0 00:00` to exactly `Day 1 00:00`.
It schedules independent supporting-character work, a transit-service change, observation delivery, bounded Mara decision opportunities, action completion, safe-failure retries, and exact end-of-day handling through explicit causal phases.
The default command is provider-free and makes no Mara model request.
An explicit Ollama mode uses the same restricted Mara decision boundary, and recorded decisions can reproduce the resulting world history without another provider call.

The codebase preserves an important separation across its implemented scenarios and supporting modules:

- **Objective history** records what happened and is append-only.
- **Official records** can gain a new current version without rewriting objective history; the first-day scenario exercises this versioned record path, while the autonomous day uses a separate objective transit-state change.
- **Observations** determine what a particular character actually encounters and when.
  Publishing or revising a record does not automatically tell every character about it.
- **Agent state** can contain source-linked beliefs and memory traces derived from delivered observations.
- **Presentation** keeps the normal view focused on Mara, while separately labelled omniscient inspectors expose sanitized objective and causal evidence appropriate to each scenario.

This is a feasibility prototype, not a finished game or a claim to model human psychology.

## Run the scenarios

The project uses Python's standard library and has no third-party runtime dependencies.
From the repository root, run the authored first-day comparison with:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30
```

The normal output shows only information deliberately admitted to Mara's view.
The scenario completes at tick 28; `--ticks 30` simply gives it enough room to reach that completion condition.

To see the explicitly omniscient development record, run:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect
```

The inspector is intentionally verbose.
It includes objective events, agent-specific observations, action outcomes, official-record versions, physical state, beliefs, Agent Understanding evidence, and inspector-only model decision records when model-backed Mara is used.

Useful first-day options:

```text
--seed N                     Choose the world seed.
--ticks N                    Limit how many ticks may run.
--focal-policy scripted      Use the deterministic default.
--focal-policy ollama        Explicitly use the local model-backed policy.
--ollama-base-url URL        Supply its private numeric-IP HTTP origin.
--ollama-model MODEL         Supply the model selected for this integration.
--inspect                    Show the omniscient development view.
```

The autonomous-day command uses `--focal-policy offline` as its default instead of the first-day command's `scripted` value.
It does not accept `--ticks` because its boundary is always exactly 1,440 simulated minutes.

### Run model-backed Mara

`policies.mara_harness.MaraHarness` is the single public construction point for model-backed Mara.
It is a composition facade over the restricted request, client, parser, safe-failure, and private-record collaborators, not a simulation runtime or persistent mind.
Its complete behavioral boundary is `AgentView -> MaraHarness -> ActionAttempt`; the simulation still decides when to call it and alone validates and resolves the returned attempt.

The live integration uses a local Ollama server and exactly `qwen3:4b-instruct`.
Both the endpoint and model must be supplied at runtime; the repository contains no configured endpoint.
Replace the example private address below with the numeric private-LAN origin that hosts Ollama:

```bash
python3 -m scenarios.first_day \
  --seed 42 \
  --ticks 3 \
  --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct
```

The adapter accepts only a path-free HTTP origin on a private, loopback, or link-local numeric IP address.
It does not use credentials, provider chat history, retries, model pulls, redirects, proxies, or DNS.
Each eligible Mara decision sends one fresh restricted state through `MaraHarness.from_ollama(...)` and requests one structured attempted action.
A provider timeout, unavailable service, malformed response, or invalid choice produces an explicit safe wait; it never invokes the scripted policy.

Normal output shows Mara's concise attributed `Reason:` and the consequence the simulation resolved.
Add `--inspect` to see restricted model input, authored profile and skill identities, non-secret model configuration identity, structured response, attempted action, validation, and outcome links.
The inspector does not retain the endpoint, raw prompt, provider error detail, or hidden provider chain-of-thought.
Mara's requested concise `decision_reason` is retained as an attributed explanation and shown normally.
Live choices may vary even with temperature zero; recorded-decision playback reproduces world behavior, not deterministic model sampling.

### Run the accelerated autonomous day

The autonomous-day composition advances from `Day 0 00:00` to exactly `Day 1 00:00`.
Its default is offline and makes no model request:

```bash
python3 -m scenarios.autonomous_day --seed 42
```

Its live path is separately explicit and uses the same externally configured private-IP Ollama boundary:

```bash
python3 -m scenarios.autonomous_day \
  --seed 42 \
  --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct
```

Replace the example address at runtime.
The repository does not retain the endpoint.
Add `--inspect` for the sanitized omniscient causal record; normal output remains focal-safe.
A zero exit status means the exact day boundary was reached, including when individual model decisions took the documented safe-failure path.
A terminal runtime failure returns nonzero.

To retain one private live-run audit bundle, pass a new directory path that does not already exist:

```bash
python3 -m scenarios.autonomous_day \
  --seed 42 \
  --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct \
  --audit-dir /private/tmp/2084-ad12-live
```

The audit directory is atomically reserved with owner-only permissions before the first provider call and is never overwritten.
One provider-backed run writes the focal-safe transcript, sanitized inspector, canonical private decision records, measured verdict, and manifest of artifact hashes.
The manifest identifies the concrete Ollama adapter and records the source HEAD, working-tree status, and complete tracked-diff hash before and after the run.
Before the live run, the CLI queries `/api/tags` and requires the pinned digest, family, parameter size, and quantization for `qwen3:4b-instruct`.
Injected clients and recorded replays cannot attest as the live Ollama source.
The same recorded choices are replayed offline before the verdict passes; this does not make a second provider call.

The audit fails if the provider never produces a selected decision, any growth ceiling or causal link fails, the exact day boundary is missed, or private configuration appears in either observer view.
The verifier also fails closed for missing, malformed, recursively invalid, linked, permission-changed, or hash-mismatched artifacts.

Recheck an unchanged bundle with:

```bash
python3 -m scenarios.autonomous_day_audit /private/tmp/2084-ad12-live
```

Run the complete test suite with:

```bash
./scripts/check.sh
```

That command checks both the current engine and the older prototypes retained under `experiments/`.

## Implemented foundations

Beyond the initial First Living Slice, four bounded foundations are implemented and retained as regression evidence:

- **Official Record** provides a stable ration-schedule artifact, immutable versions, a current-version pointer, location-gated consultation, and an authorized same-period rewrite that never changes objective history or automatically delivers the new version.
- **Agent Understanding** lets Mara retain two delivered official versions, link their conflict, use the revised version as a public working stance under pressure, and later resurface the earlier version through a physical diary strongly enough to prompt one ordinary public-schedule recheck.
- **Model-Backed Focal Character** provides a versioned Mara profile and decision skill, a restricted decision envelope, a strict shared action contract, explicit safe failures, inspector-only linked decision evidence, recorded-decision reproduction, and the opt-in Ollama command above.
- **First Autonomous 24-Hour Living Day** provides authoritative simulated minutes, explicit causal phases, bounded decision eligibility, independent wider-world activity, exact day completion, long-run growth limits, provider-free reproduction, and an auditable explicit Ollama path.

The deterministic first-day policy and the offline autonomous-day command remain the provider-free defaults.

The evidence remains deliberately inspectable and limited:

- only delivered observations create source-linked memory traces and claims;
- the public and diary stances retain their exact sources and transition history;
- supporting characters and institutions receive no focal-private diary understanding;
- the normal transcript explains encountered behavior without omniscient identifiers; and
- the development inspector exposes the detached causal record.

The older narrow belief model still supplies the `Private belief` line visible in the first-day terminal output.
It represents Mara's direct sight of three physical allocation units.
It remains separate from the official-version conflict and stance system.

The repository also contains a proposed thin-harness/fat-skills direction for later model-backed expansion.
The current code implements only the narrow Mara decision boundary; it does not contain a general skill resolver, tool-using agent runtime, self-modifying skill system, or model-backed supporting cast.

## Known limits

- The scripted comparison remains heavily authored.
  Model-backed Mara uses one bounded decision skill and one local model, while supporting characters and institutions remain deterministic.
  This is not yet a general living society or evidence that the character is believable.
- The first-day route, institutional rewrite timing, public pressure, diary opportunity, autonomous-day schedule, and transit change are authored inputs.
  The results are bounded evidence, not emergent stories.
- Memory decay, forgetting, general language understanding, dynamic personality, relationships, surveillance, punishment, and a broader living society are not implemented.
  Mara has a short authored profile, not a general personality simulation.
- There is no graphical interface, durable save system, user-facing replay command, or player intervention.
  Recorded-decision reproduction exists programmatically and runs while a private live-audit bundle is created; the standalone audit verifier later checks the stored bundle's integrity and verdict rather than replaying it again.
- The inspector is a development tool, not the intended final experience.

These limits are deliberate.
The project is testing small, inspectable mechanisms before adding scale or less predictable behavior.

## Repository guide

```text
scenarios/    Authored worlds and runnable entry points
simulation/   Time, world state, actions, events, records, and understanding
policies/     Scripted rules plus Mara's model request, client, and policy boundary
observer/     The filtered terminal view and omniscient inspector
tests/        Tests for the current engine and scenarios
experiments/  Older prototypes kept as historical evidence
docs/         Product direction, architecture, goals, and verified progress
scripts/      Repository checks
```

The most useful documents are:

- [Core Construct](docs/main/CORE_CONSTRUCT.md) - the intended experience and thematic direction.
- [Architecture](docs/main/ARCHITECTURE.md) - the implemented boundaries between world truth, time, observations, decisions, institutions, and presentation.
- [UI Architecture](docs/main/UI_ARCHITECTURE.md) - implemented terminal surfaces and future interface direction.
- [First Autonomous 24-Hour Living Day Goal](docs/plans/first-autonomous-day/GOAL.md) - the completed full-day behavior contract.
- [First Autonomous 24-Hour Living Day Implementation State](docs/plans/first-autonomous-day/IMPLEMENTATION_PLAN.md) - verified implementation and live-audit evidence.
- [Model-Backed Focal Character Goal](docs/plans/model-backed-focal-character/GOAL.md) - the completed bounded Phase 3B goal.
- [Model-Backed Focal Character Implementation State](docs/plans/model-backed-focal-character/IMPLEMENTATION_PLAN.md) - verified completion evidence for that goal.
- [Agent Understanding Goal](docs/plans/agent-understanding/GOAL.md) - the completed Phase 3A foundation.
- [Verified Implementation State](docs/plans/agent-understanding/IMPLEMENTATION_PLAN.md) - evidence retained from the completed Agent Understanding goal.
- [Design References](docs/main/DESIGN_REFERENCES.md) - transferable reference ideas and explicit boundaries against copying them wholesale.
- [Thin Harness, Fat Skills](docs/main/thin-harness-fat-skills-spec.md) - a proposed general architecture direction, not an implemented general agent runtime.
- [Mara Model Harness Plan](docs/plans/MARA_HARNESS_PLAN.md) - the completed architecture record behind the first live model integration.
