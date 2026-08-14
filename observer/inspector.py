"""Explicitly omniscient development presentation."""

from __future__ import annotations

import json

from simulation.engine import Simulation


def render_inspector(simulation: Simulation) -> str:
    """Expose objective records and provenance only in development mode."""
    beliefs = {
        agent_id: [
            {
                "belief_id": belief.belief_id,
                "proposition": belief.proposition,
                "asserted_value": belief.asserted_value,
                "source_observation_ids": list(belief.source_observation_ids),
                "confidence": belief.confidence,
                "last_updated_tick": belief.last_updated_tick,
                "context": belief.context,
                "conflicts_with": list(belief.conflicts_with),
            }
            for belief in agent.beliefs
        ]
        for agent_id, agent in simulation.world.agents.items()
    }
    payload = {
        "objective_state": simulation.inspector_state(),
        "institution_records": dict(simulation.world.institution.records),
        "beliefs": beliefs,
        "history": simulation.history_data(),
    }
    return (
        "2084 DEVELOPMENT INSPECTOR — OMNISCIENT\n"
        "Not part of the normal observer experience.\n"
        + json.dumps(payload, indent=2, sort_keys=True)
        + "\n"
    )
