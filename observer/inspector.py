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
        "private_decision_records": [
            record.to_data() for record in simulation.decision_records
        ],
        "private_decision_record_storage": {
            "retained_bytes": simulation.private_decision_records_bytes,
            "peak_retained_bytes": simulation.peak_private_decision_records_bytes,
            "maximum_bytes": simulation.maximum_private_decision_records_bytes,
        },
        "institution_records": dict(simulation.world.institution.records),
        "official_record": simulation.world.institution.official_record.to_data(),
        "beliefs": beliefs,
        "history": simulation.history_data(),
    }
    return (
        "2084 DEVELOPMENT INSPECTOR — OMNISCIENT\n"
        "Not part of the normal observer experience.\n"
        + json.dumps(payload, indent=2, sort_keys=True)
        + "\n"
    )
