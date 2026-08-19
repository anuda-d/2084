# Reproduction

## Topic

Reproduce the complete Agent Understanding experiment from equal configured
runs.

## Required behavior

- The scenario identifier becomes `first_day_v3`.
- Equal configurations produce equal ordered objective events.
- Equal configurations produce equal ordered observations.
- Equal configurations produce equal memory traces and understanding
  transitions.
- Equal configurations produce equal attempted actions and terminal results.
- Detached history remains JSON-compatible.
- The full run stops at one documented completion boundary.

## Evidence

- A complete-run equality test compares detached history.
- The repository check passes.
- Both documented observer commands complete.

## Exclusions

- Durable saves
- Executable replay
- Cross-language portability
- A permanent randomness contract
