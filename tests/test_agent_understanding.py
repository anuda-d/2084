import unittest
from dataclasses import FrozenInstanceError

from scenarios.first_day import CLERK_ID, CO_WORKER_ID, FOCAL_AGENT_ID, build_first_day
from simulation.events import Observation, freeze_mapping
from simulation.understanding import trace_from_delivered_observation


class AgentUnderstandingTests(unittest.TestCase):
    def test_supported_deliveries_create_immutable_source_linked_traces(self):
        simulation = build_first_day(seed=42)
        for _ in range(8):
            simulation.step()

        focal = simulation.world.agents[FOCAL_AGENT_ID]
        traces = focal.memory_traces
        claims = focal.interpreted_claims

        self.assertEqual(
            [trace.evidence_kind for trace in traces],
            ["direct_resource_claim", "official_record_version"],
        )
        self.assertEqual(len(claims), 2)
        observations = {
            observation.observation_id: observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
        }
        for trace in traces:
            source = observations[trace.source_observation_id]
            claim = next(
                claim
                for claim in claims
                if claim.claim_id == trace.interpreted_claim_id
            )
            self.assertEqual(trace.source_event_id, source.event_id)
            self.assertEqual(trace.source, source.source)
            self.assertEqual(trace.delivery_tick, source.delivery_tick)
            self.assertEqual(trace.proposition, claim.proposition)
            self.assertEqual(trace.asserted_value, claim.asserted_value)
            self.assertEqual(trace.period_id, claim.period_id)
        self.assertIsNone(traces[0].period_id)
        self.assertEqual(traces[1].period_id, "first-day-week")
        for supporting_agent_id in (CO_WORKER_ID, CLERK_ID):
            supporting_agent = simulation.world.agents[supporting_agent_id]
            self.assertEqual(supporting_agent.memory_traces, ())
            self.assertEqual(supporting_agent.interpreted_claims, ())
        with self.assertRaises(FrozenInstanceError):
            traces[0].asserted_value = 99

    def test_rewrite_without_delivery_creates_no_trace(self):
        simulation = build_first_day(seed=42)
        for _ in range(9):
            simulation.step()
        traces_before_rewrite = simulation.world.agents[FOCAL_AGENT_ID].memory_traces

        simulation.step()

        focal = simulation.world.agents[FOCAL_AGENT_ID]
        self.assertEqual(focal.memory_traces, traces_before_rewrite)
        self.assertEqual(
            simulation.world.institution.official_record.current_version.version_id,
            "weekly-household-ration-schedule-v2",
        )
        self.assertFalse(
            any(trace.asserted_value == 2 for trace in focal.memory_traces)
        )

    def test_delivered_official_versions_form_one_reciprocal_conflict(self):
        simulation = build_first_day(seed=42)
        simulation.run(max_ticks=12)

        focal = simulation.world.agents[FOCAL_AGENT_ID]
        direct_claim = next(
            claim
            for claim in focal.interpreted_claims
            if claim.proposition == "daily_allocation_units"
        )
        official_claims = [
            claim
            for claim in focal.interpreted_claims
            if claim.proposition == "weekly_household_ration_entitlement_packets"
        ]
        self.assertEqual([claim.asserted_value for claim in official_claims], [3, 2])
        self.assertEqual(
            official_claims[0].conflicts_with,
            (official_claims[1].claim_id,),
        )
        self.assertEqual(
            official_claims[1].conflicts_with,
            (official_claims[0].claim_id,),
        )
        self.assertEqual(direct_claim.conflicts_with, ())

        official_observations = [
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "official_record_version"
        ]
        self.assertEqual(
            [observation.details["asserted_value"] for observation in official_observations],
            [3, 2],
        )
        record = simulation.world.institution.official_record
        self.assertEqual(
            [version.version_id for version in record.versions],
            [
                "weekly-household-ration-schedule-v1",
                "weekly-household-ration-schedule-v2",
            ],
        )

    def test_undelivered_official_version_cannot_form_a_conflict(self):
        simulation = build_first_day(seed=42)
        simulation.run(max_ticks=10)

        focal = simulation.world.agents[FOCAL_AGENT_ID]
        official_claims = [
            claim
            for claim in focal.interpreted_claims
            if claim.proposition == "weekly_household_ration_entitlement_packets"
        ]
        self.assertEqual(len(official_claims), 1)
        self.assertEqual(official_claims[0].conflicts_with, ())
        self.assertEqual(
            simulation.world.institution.official_record.current_version.version_id,
            "weekly-household-ration-schedule-v2",
        )

    def test_repeated_delivery_reuses_the_interpreted_claim(self):
        details = freeze_mapping(
            {
                "evidence_kind": "official_record_version",
                "period_id": "first-day-week",
                "proposition": "weekly_household_ration_entitlement_packets",
                "asserted_value": 2,
            }
        )
        first_observation = Observation(
            observation_id="observation-0001",
            agent_id=FOCAL_AGENT_ID,
            event_id="event-0001",
            source="Civic Allocation Office public record",
            delivery_tick=12,
            details=details,
        )
        second_observation = Observation(
            observation_id="observation-0002",
            agent_id=FOCAL_AGENT_ID,
            event_id="event-0002",
            source="Civic Allocation Office public record",
            delivery_tick=13,
            details=details,
        )

        first_trace, claim = trace_from_delivered_observation(
            first_observation,
            trace_id="memory-trace-mara-vale-001",
            claim_id="interpreted-claim-mara-vale-001",
            existing_claims=(),
        )
        second_trace, duplicate_claim = trace_from_delivered_observation(
            second_observation,
            trace_id="memory-trace-mara-vale-002",
            claim_id="interpreted-claim-mara-vale-002",
            existing_claims=(claim,),
        )

        self.assertNotEqual(first_trace.trace_id, second_trace.trace_id)
        self.assertEqual(
            first_trace.interpreted_claim_id,
            second_trace.interpreted_claim_id,
        )
        self.assertIsNone(duplicate_claim)

    def test_history_export_is_deterministic_and_detached(self):
        first = build_first_day(seed=42)
        second = build_first_day(seed=42)
        first.run(max_ticks=12)
        second.run(max_ticks=12)

        history = first.history_data()
        self.assertEqual(history, second.history_data())
        focal_history = history["agent_understanding"][FOCAL_AGENT_ID]
        self.assertEqual(len(focal_history["memory_traces"]), 3)
        focal_history["memory_traces"][0]["asserted_value"] = 99
        self.assertEqual(
            first.history_data()["agent_understanding"][FOCAL_AGENT_ID][
                "memory_traces"
            ][0]["asserted_value"],
            3,
        )


if __name__ == "__main__":
    unittest.main()
