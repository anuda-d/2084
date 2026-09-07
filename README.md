# 2084

> Watch one autonomous agent as it navigates a world built on lies, contradiction, and power.

**2084** is a terminal-based social simulation about the interval between what instituitions say happened, what actually happened, what a person learns, and what they can safely express.

Mara Vale acts from limited information while other people, institutions, and the world continue without waiting for her.

The project takes thematic inspiration from George Orwell's *Nineteen Eighty-Four*, especially its treatment of lived experience, public behavior, and official accounts.
It does not adapt Orwell's plot, characters, or setting.

This is a feasibility prototype, not a finished game.

## Start here

There are no third-party runtime dependencies.
From the repository root:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30
```

This runs a deterministic 28-tick day through Mara's limited point of view.
She sees three ration units, receives two, encounters two incompatible versions of the official schedule, and carries the contradiction into her public behavior and private diary.

To expose the objective and causal record behind that same run:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect
```

Normal output is intentionally incomplete.
The inspector is intentionally omniscient and explicitly labelled as a development tool.

## Boundaries

The simulation keeps truth, knowledge, decisions, and presentation separate.

| Layer | Guarantee |
| --- | --- |
| Objective history | Records what happened and never rewrites earlier events |
| Official records | Can publish a new current version without changing objective history |
| Observations | Deliver only what a character can physically or socially encounter |
| Agent understanding | Retains claims, sources, contradictions, confidence, and contextual stance |
| Attempted actions | Express what an agent tries to do, not what automatically succeeds |
| Presentation | Separates Mara's view from sanitized development evidence |

Publishing a record does not automatically inform every character.
Knowing something does not grant authority to change the world.
Attempting something does not guarantee its outcome.

## Choose a scenario

| Scenario | Simulated span | Best for |
| --- | ---: | --- |
| `scenarios.first_day` | 28 ticks | The clearest introduction to official revision, contradiction, public stance, and a physical diary |
| `scenarios.autonomous_day` | 24 hours | Time, independent activity, bounded decisions, social testimony, safe failures, and exact day completion |

### First living slice

The default policy is deterministic and provider-free:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30
```

Useful options:

```text
--seed N                     Choose the world seed
--ticks N                    Limit the available ticks
--focal-policy scripted      Use the deterministic default
--focal-policy ollama        Use the explicit local model policy
--ollama-base-url URL        Supply a private numeric-IP Ollama origin
--ollama-model MODEL         Supply the required local model
--inspect                    Show the omniscient development view
```

The normal transcript contains only information admitted to Mara's view.
The inspector adds objective events, observations, action outcomes, record versions, physical state, beliefs, and sanitized model-decision evidence.

### Accelerated autonomous day

The quiet default advances from `Day 0 00:00` to exactly `Day 1 00:00` without making a model request:

```bash
python3 -m scenarios.autonomous_day --seed 42
```

The provider-free social comparison adds an authored opportunity for Ilan to encounter a transit change, tell Mara in person, and affect her next bounded decision:

```bash
python3 -m scenarios.autonomous_day \
  --seed 42 \
  --focal-policy scripted
```

The transcript identifies this decision source as deterministic and authored.
It does not present the comparison as live or emergent behavior.

The complete provider-free consequential-choice comparison keeps the same
single-day world but exposes both delivered transit accounts for one explicit
service interval, Mara's authored ordinary choice, its world-resolved travel
and obligation consequence, and a later follow-up decision through the normal
focal-safe transcript:

```bash
python3 -m scenarios.autonomous_day \
  --seed 42 \
  --focal-policy scripted \
  --consequential-choice
```

This command uses a deterministic authored decision sequence rather than a
live model.
It is evidence for the observable composition, not a claim that Mara chose the
branch autonomously.
`--consequential-choice` also supports the explicit Ollama policy for the
separate reviewed live-day criterion, but it rejects the inert offline policy.

The opt-in `build_autonomous_day(include_conflicting_transit_accounts=True)` configuration preserves the completed default day while adding one finite official transit notice and a conflicting source-linked Ilan testimony for the same workplace-home service interval.
The official notice is published through the transit authority's Official Record and reaches Mara only at the workplace notice board.

The opt-in `include_deadline_governed_obligation_outcomes=True` configuration adds authored 10:31 workplace and 10:30 household deadlines.
It records a fulfilled or missed objective outcome only from matching completed activity at the required location, with an exact-deadline completion counted as missed.
A fulfilled outcome retains the existing actor-safe completed-action result and continuity requirement for Mara's next selected decision.
A missed outcome remains inspector-only unless
`include_obligation_outcome_delivery=True` is also configured.
That opt-in delivers only Mara's own missed-obligation result through her
personal obligation schedule, requests a later decision only when she is not
busy, and never reveals objective transit state.

The separate opt-in `include_consequential_choice_tradeoff_timing=True` profile requires deadline outcomes and exposes Mara's finite, authored obligation schedule in her restricted input.
It sets both deadlines to 10:32, so a deterministic authored comparison can choose either post-testimony workplace work or homeward travel followed by household activity without changing the existing physical-transit profile.
The schedule identifies only Mara's own obligation, required ordinary activity and location, and deadline - never actual transit status or a predicted outcome.

The opt-in `include_service_dependent_travel=True` configuration samples the objective `normal` or `reduced` service state when Mara's travel attempt is accepted, using the authored 30- or 60-minute duration for that trip.
`homeward_travel_service_recovery_minute` may record one objective recovery after the source observation without automatically delivering it to Mara.
The accepted travel is not retimed if that recovery happens while it is pending.
This preserves an ordinary comparison in which Mara retains the same conflicting accounts and action path while normal service permits household completion before its deadline and reduced service does not.

Add `--inspect` to reconstruct the complete causal chain, including source observation, statement validation, testimony delivery, Mara's attempt, and world resolution.

## Local model mode

Model-backed Mara is optional and explicit.
Both scenarios use the same narrow boundary:

```text
AgentView -> MaraHarness -> ActionAttempt -> world validation
```

`MaraHarness` receives only Mara's restricted state and returns one attempted action.
The simulation still decides when to ask, which actions are valid, and what actually happens.

<details>
<summary><strong>Run with Ollama</strong></summary>

The live integration accepts exactly `qwen3:4b-instruct` through a local Ollama server.
Replace the example address with the numeric private-LAN origin that hosts Ollama.

```bash
python3 -m scenarios.autonomous_day \
  --seed 42 \
  --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct
```

The adapter accepts only a path-free HTTP origin on a private, loopback, or link-local numeric IP address.
It uses no credentials, provider history, retries, model pulls, redirects, proxies, or DNS.

A timeout, unavailable service, malformed response, or invalid choice becomes an explicit safe wait.
The simulation never substitutes the scripted policy after a provider failure.

Live choices may vary even at temperature zero.
Recorded decisions reproduce world behavior without making another provider call.
Replay requires the same seed and authored scenario configuration because an archive seals decisions, not scenario inputs.

### Create a private audit bundle

Pass a new directory path that does not already exist:

```bash
python3 -m scenarios.autonomous_day \
  --seed 42 \
  --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct \
  --audit-dir /private/tmp/2084-ad12-live
```

The run reserves the directory with owner-only permissions and writes a focal-safe transcript, sanitized inspector, private decision records, measured verdict, and artifact manifest.
The verifier checks source identity, model identity, causal links, privacy boundaries, growth limits, replay equality, permissions, hashes, and the exact 24-hour boundary.

Recheck an unchanged bundle with:

```bash
python3 -m scenarios.autonomous_day_audit /private/tmp/2084-ad12-live
```

</details>

## What exists

- Versioned official records whose current projection can change without rewriting objective history.
- Source-linked memories that preserve conflicting claims instead of erasing inconvenient evidence.
- Contextual public and private stances with inspectable inhibition and resurfacing.
- One bounded local-model decision path for Mara with explicit safe failures and private evidence handling.
- An exact 24-hour runtime with scheduled independent activity, decision eligibility, action completion, and bounded retries.
- One deterministic supporting-character choice that can produce evidence-bound testimony and a consequence for Mara.

## What does not exist

- A general living society or model-backed supporting cast.
- A persistent mind, general language understanding, or a claim of believable human psychology.
- Dynamic personality, relationships, surveillance, punishment, memory decay, or forgetting.
- A graphical interface, durable save system, or user-facing replay command.
- Player control over Mara or privileged access to truth in the normal experience.

The authored route, institutional timing, transit change, and decision opportunities are test inputs.
The results demonstrate bounded mechanisms, not emergent stories.

## Repository map

```text
scenarios/    Runnable worlds and their command-line entry points
simulation/   Time, world state, actions, events, records, and understanding
policies/     Deterministic rules and Mara's restricted model boundary
observer/     The focal-safe terminal view and omniscient inspector
tests/        Regression, boundary, privacy, replay, and audit evidence
docs/         Product direction, architecture, goals, and verified progress
scripts/      Repository checks and development-loop safeguards
```

Run every repository check with:

```bash
./scripts/check.sh
```

## Read next

- [Core Construct](docs/main/CORE_CONSTRUCT.md) defines the intended experience and thematic boundaries.
- [Architecture](docs/main/ARCHITECTURE.md) explains the implemented separation between world truth, observations, decisions, institutions, and presentation.
- [UI Architecture](docs/main/UI_ARCHITECTURE.md) records the terminal surfaces and future interface direction.
- [Current Development Index](docs/plans/CURRENT.md) is the compact source of truth for goal and implementation status.
- [Design References](docs/main/DESIGN_REFERENCES.md) documents transferable ideas and the boundaries against copying them wholesale.
