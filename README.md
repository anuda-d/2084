# 2084

2084 is an early, terminal-based social simulation about following one
autonomous person through a world they can only partly understand.

The long-term idea is to watch a life unfold inside a small society shaped by
lies, contradictions, institutions, relationships, limited information, and
pressure. The focal character is not a player-controlled puppet and does not
know everything
the simulation knows. Other people and institutions continue acting while the
observer sees the world mainly through that character's experience.

The project takes thematic inspiration from George Orwell's *Nineteen
Eighty-Four*, especially the gap between lived experience, public behavior, and
official accounts. It is not an adaptation of Orwell's plot, characters, or
setting.

## What exists today

The repository contains one bounded prototype scenario, `first_day_v3`, with a
deterministic scripted focal policy by default and an explicitly selected local
model-backed focal policy. The scripted comparison follows Mara Vale and two
supporting characters through a 28-tick workday. Mara:

- travels between home, work, and a civic allocation office;
- sees three allocation units but physically receives only two;
- consults an official schedule that initially promises three packets;
- experiences public pressure, encounters the revised two-packet schedule, and
  repeats that revised entitlement publicly while retaining separate evidence;
- writes the earlier three-packet schedule claim into a physical diary;
- reads that entry later and makes one ordinary trip to recheck the public
  schedule; and
- finishes the day with one household unit still unmet.

The scripted route is heavily authored, but the characters are not moved
directly by a player. Transparent rule-based policies choose attempted actions
from limited information. In model-backed mode, the local model chooses Mara's
attempts instead; supporting characters remain rule-based. In both modes the
simulation checks each attempt and alone decides what actually happens.

The current prototype also preserves an important separation:

- **Objective history** records what happened and is append-only.
- **Official records** can gain a new current version without rewriting that
  objective history.
- **Observations** determine what a particular character actually encounters
  and when. Publishing or revising a record does not automatically tell every
  character about it.
- **Agent state** can contain source-linked beliefs and memory traces derived
  from delivered observations.
- **Presentation** keeps the normal view focused on Mara, while a separate
  development inspector can reveal the complete underlying record.

This is a feasibility prototype, not a finished game or a claim to model human
psychology.

## Run the simulation

The project uses Python's standard library and has no third-party runtime
dependencies. From the repository root, run:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30
```

The normal output shows only information deliberately admitted to Mara's view.
The scenario completes at tick 28; `--ticks 30` simply gives it enough room to
reach that completion condition.

To see the explicitly omniscient development record, run:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect
```

The inspector is intentionally verbose. It includes objective events,
agent-specific observations, action outcomes, official-record versions,
physical state, beliefs, Agent Understanding evidence, and inspector-only
model decision records when model-backed Mara is used.

Useful options:

```text
--seed N                     Choose the world seed.
--ticks N                    Limit how many ticks may run.
--focal-policy scripted      Use the deterministic default.
--focal-policy ollama        Explicitly use the local model-backed policy.
--ollama-base-url URL        Supply its private numeric-IP HTTP origin.
--ollama-model MODEL         Supply the model selected for this integration.
--inspect                    Show the omniscient development view.
```

### Run model-backed Mara

`policies.mara_harness.MaraHarness` is the single public construction point for
model-backed Mara. It is a composition facade over the existing restricted
request, client, parser, safe-failure, and private-record collaborators—not a
simulation runtime or persistent mind. Its complete behavioral boundary is
`AgentView -> MaraHarness -> ActionAttempt`; the simulation still decides when
to call it and alone validates and resolves the returned attempt.

The first live integration uses a local Ollama server and exactly
`qwen3:4b-instruct`. Both the endpoint and model must be supplied at runtime;
the repository contains no configured or owner endpoint. Replace the example
private address below with the numeric private-LAN origin that hosts Ollama:

```bash
python3 -m scenarios.first_day \
  --seed 42 \
  --ticks 3 \
  --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct
```

The adapter accepts only a path-free HTTP origin on a private, loopback, or
link-local numeric IP address. It does not use credentials, provider chat
history, retries, model pulls, redirects, proxies, or DNS. Each eligible Mara
decision sends one fresh restricted state through `MaraHarness.from_ollama(...)`
and requests one structured attempted action. A provider timeout, unavailable
service, malformed response, or invalid choice produces an explicit safe wait;
it never invokes the scripted policy.

Normal output shows Mara's concise attributed `Reason:` and the consequence the
simulation resolved. Add `--inspect` to see restricted model input, authored
profile/skill identities, non-secret model configuration identity, structured
response, attempted action, validation, and outcome links. The inspector does
not retain the endpoint, raw prompt, provider error detail, or hidden provider
chain-of-thought. Mara's requested concise `decision_reason` is retained as an
attributed explanation and shown normally. Live choices may vary even with
temperature zero; recorded-decision playback is for reproducing world behavior,
not claiming deterministic model sampling.

### Run the accelerated autonomous day

The successor composition advances from `Day 0 00:00` to exactly
`Day 1 00:00`. Its default remains offline and makes no model request:

```bash
python3 -m scenarios.autonomous_day --seed 42
```

Its live path is separately explicit and uses the same externally configured,
private-IP Ollama boundary:

```bash
python3 -m scenarios.autonomous_day \
  --seed 42 \
  --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct
```

Replace the example address at runtime. The repository does not retain the
owner endpoint. Add `--inspect` for the sanitized omniscient causal record;
normal output remains focal-safe. A zero exit status means the exact day
boundary was reached, including when individual model decisions took the
documented safe-failure path. A terminal runtime failure returns nonzero.

Run the complete test suite with:

```bash
./scripts/check.sh
```

That command checks both the current engine and the older prototypes retained
under `experiments/`.

## Current development status

Beyond the initial First Living Slice, the three most recent bounded
implementation goals are complete:

- **Official Record** added a stable ration-schedule artifact, immutable
  versions, a current-version pointer, location-gated consultation, and an
  authorized same-period rewrite that never changes objective history or
  automatically delivers the new version.
- **Agent Understanding** demonstrates that Mara can retain two delivered
  official versions, link their conflict, use the revised version as a public
  working stance under pressure, and later resurface the earlier version through
  a physical diary strongly enough to prompt one ordinary public-schedule
  recheck.
- **Model-Backed Focal Character** added a versioned Mara profile and reusable
  decision skill, a restricted decision envelope, a strict shared action
  contract, explicit safe failures, inspector-only linked decision evidence,
  recorded-decision reproduction, and the opt-in Ollama command above. The
  scripted command remains the offline regression default.

The evidence remains deliberately inspectable and limited:

- only delivered observations create source-linked memory traces and claims;
- the public and diary stances retain their exact sources and transition
  history;
- supporting characters and institutions receive no focal-private diary
  understanding;
- the normal transcript explains the encountered behavior without omniscient
  identifiers; and
- the development inspector exposes the detached causal record.

The older narrow belief model still supplies the “Private belief” line visible
in the terminal output. It represents Mara's direct sight of three physical
allocation units. It remains separate from the official-version conflict and
stance system.

The repository also contains a proposed thin-harness/fat-skills direction for
later model-backed expansion. The current code implements only the narrow Mara
decision boundary; it does not contain a general skill resolver, tool-using
agent runtime, or self-modifying skill system. The active 24-hour goal preserves
that narrow model boundary while adding one full-day composition; it does not
authorize the proposed general runtime.

## Known limits

- The scripted comparison remains heavily authored. Model-backed Mara uses one
  bounded decision skill and one local model, while supporting characters and
  institutions remain deterministic; this is not yet a general living society
  or evidence that the character is believable.
- The first-day route, institutional rewrite timing, public pressure, and diary
  opportunity are authored inputs. The result is bounded evidence, not an
  emergent story.
- Memory decay, forgetting, general language understanding, dynamic
  personality, relationships, surveillance, punishment, and a broader living
  society are not implemented. Mara has a short authored profile, not a general
  personality simulation.
- There is no graphical interface, durable save system, user-facing replay
  command, or player intervention. Recorded-decision reproduction exists at the
  policy boundary and is covered by offline tests.
- The inspector is a development tool, not the intended final experience.

These limits are deliberate. The project is testing small, inspectable
mechanisms before adding scale or less predictable behavior.

## Repository guide

```text
scenarios/    Authored worlds and runnable entry points
simulation/   Time, world state, actions, events, records, and understanding
policies/     Scripted rules plus Mara's model request, client, and policy boundary
observer/     The filtered terminal view and omniscient inspector
tests/        Tests for the current engine and scenario
experiments/  Older prototypes kept as historical evidence
docs/         Product direction, architecture, goals, and verified progress
scripts/      Repository checks
```

The most useful documents are:

- [Core Construct](docs/main/CORE_CONSTRUCT.md) — the intended experience and
  thematic direction.
- [Architecture](docs/main/ARCHITECTURE.md) — the boundaries between world
  truth, observations, decisions, institutions, and presentation.
- [Current Development Index](docs/plans/CURRENT.md) — the operational
  development entry point and authoritative goal status.
- [Model-Backed Focal Character Goal](docs/plans/model-backed-focal-character/GOAL.md)
  — the completed bounded Phase 3B goal.
- [Model-Backed Focal Character Implementation State](docs/plans/model-backed-focal-character/IMPLEMENTATION_PLAN.md)
  — verified completion evidence for that goal.
- [Agent Understanding Goal](docs/plans/agent-understanding/GOAL.md) — the
  completed Phase 3A foundation.
- [Verified Implementation State](docs/plans/agent-understanding/IMPLEMENTATION_PLAN.md)
  — evidence retained from the completed Agent Understanding goal.
- [UI Architecture](docs/main/UI_ARCHITECTURE.md) — implemented terminal
  surfaces and future interface direction.
- [Design References](docs/main/DESIGN_REFERENCES.md) — transferable reference
  ideas and explicit boundaries against copying them wholesale.
- [Thin Harness, Fat Skills](docs/main/thin-harness-fat-skills-spec.md) — a
  proposed general architecture direction, not an active implementation goal.
- [Mara Model Harness Plan](docs/plans/MARA_HARNESS_PLAN.md) — the completed
  architecture record behind the first live model integration.
- [Development Loop](docs/main/DEVELOPMENT_LOOP.md) — the full operating
  contract used only when owner-authorized work is active.

For coding agents and contributors, [AGENTS.md](AGENTS.md) describes the working
agreements and the one-slice development loop.
