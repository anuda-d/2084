import json
import unittest
from dataclasses import FrozenInstanceError

from observer.inspector import render_inspector
from scenarios.first_day import (
    FOCAL_AGENT_ID,
    RATION_SCHEDULE_ARTIFACT_ID,
    RATION_SCHEDULE_PERIOD_ID,
    RATION_SCHEDULE_VERSION_ONE_ID,
    build_first_day,
)
from simulation.actions import ActionAttempt


class OfficialRecordTests(unittest.TestCase):
    def test_initial_publication_sets_current_three_packet_weekly_version(self):
        simulation = build_first_day(seed=42)

        self.assertEqual(simulation.world.institution.official_record.versions, ())

        simulation.step()

        record = simulation.world.institution.official_record
        version = record.current_version
        self.assertIsNotNone(version)
        self.assertEqual(record.artifact_id, RATION_SCHEDULE_ARTIFACT_ID)
        self.assertEqual(record.current_version_id, RATION_SCHEDULE_VERSION_ONE_ID)
        self.assertEqual(record.versions, (version,))
        self.assertEqual(version.artifact_id, RATION_SCHEDULE_ARTIFACT_ID)
        self.assertEqual(version.version_id, RATION_SCHEDULE_VERSION_ONE_ID)
        self.assertEqual(version.period_id, RATION_SCHEDULE_PERIOD_ID)
        self.assertEqual(version.entitlement_packets, 3)
        self.assertIsNone(version.previous_version_id)

        publication = next(
            event
            for event in simulation.events
            if event.kind == "official_record_published"
        )
        self.assertEqual(publication.actor_id, "civic-allocation-office")
        self.assertEqual(publication.tick, 1)
        self.assertEqual(
            dict(publication.details),
            {
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                "period_id": RATION_SCHEDULE_PERIOD_ID,
                "entitlement_packets": 3,
                "previous_version_id": None,
            },
        )
        history = simulation.history_data()
        self.assertFalse(
            any(
                observation["event_id"] == publication.event_id
                for observation in history["observations"]
            )
        )

        detached = record.to_data()
        self.assertEqual(history["official_record"], detached)
        inspector_lines = render_inspector(simulation).splitlines()
        inspector_payload = json.loads("\n".join(inspector_lines[2:]))
        self.assertEqual(inspector_payload["official_record"], detached)

        with self.assertRaises(FrozenInstanceError):
            version.entitlement_packets = 99
        with self.assertRaises(AttributeError):
            record.artifact_id = "replacement-artifact"
        detached["versions"][0]["entitlement_packets"] = 99
        self.assertEqual(record.current_version.entitlement_packets, 3)

    def test_focal_character_consults_version_one_through_configured_access(self):
        simulation = build_first_day(seed=42)

        first_tick = simulation.step()
        publication = next(
            event
            for event in simulation.events
            if event.kind == "official_record_published"
        )
        self.assertFalse(
            any(
                observation.event_id == publication.event_id
                for observation in first_tick.new_observations
            )
        )

        for _ in range(6):
            consultation_tick = simulation.step()

        self.assertEqual(
            consultation_tick.current_action, "consult the weekly ration schedule"
        )
        attempt = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted"
            and event.actor_id == FOCAL_AGENT_ID
            and event.details["action_kind"] == "consult_official_record"
        )
        consultation = next(
            event
            for event in simulation.events
            if event.kind == "official_record_consulted"
        )
        self.assertEqual(attempt.details["artifact_id"], RATION_SCHEDULE_ARTIFACT_ID)
        self.assertEqual(
            consultation.caused_by, (attempt.event_id, publication.event_id)
        )
        self.assertFalse(
            any(
                observation.details.get("evidence_kind") == "official_record_version"
                for observation in consultation_tick.new_observations
            )
        )

        delivery_tick = simulation.step()

        delivered = next(
            observation
            for observation in delivery_tick.new_observations
            if observation.details.get("evidence_kind") == "official_record_version"
        )
        self.assertEqual(delivered.agent_id, FOCAL_AGENT_ID)
        self.assertEqual(delivered.event_id, consultation.event_id)
        self.assertEqual(delivered.delivery_tick, 8)
        self.assertEqual(delivered.source, "Civic Allocation Office public record")
        self.assertEqual(
            dict(delivered.details),
            {
                "evidence_kind": "official_record_version",
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                "period_id": RATION_SCHEDULE_PERIOD_ID,
                "proposition": "weekly_household_ration_entitlement_packets",
                "asserted_value": 3,
                "previous_version_id": None,
                "publication_event_id": publication.event_id,
            },
        )
        self.assertEqual(
            simulation.agent_view(FOCAL_AGENT_ID).consultable_official_record_ids,
            (RATION_SCHEDULE_ARTIFACT_ID,),
        )

    def test_official_record_consultation_is_rejected_away_from_access_location(self):
        simulation = build_first_day(seed=42)
        observations_before = simulation.observations_for(FOCAL_AGENT_ID)

        attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="consult_official_record",
                parameters={"artifact_id": RATION_SCHEDULE_ARTIFACT_ID},
                explanation="consult the weekly ration schedule from home",
            )
        )

        rejection = simulation.events[-1]
        self.assertEqual(rejection.kind, "action_rejected")
        self.assertEqual(rejection.action_id, attempt.action_id)
        self.assertIn("allocation_office", rejection.details["reason"])
        self.assertEqual(
            simulation.observations_for(FOCAL_AGENT_ID), observations_before
        )
        self.assertEqual(
            simulation.agent_view(FOCAL_AGENT_ID).consultable_official_record_ids,
            (),
        )


if __name__ == "__main__":
    unittest.main()
