import json
import unittest
from dataclasses import FrozenInstanceError

from observer.inspector import render_inspector
from scenarios.first_day import (
    FOCAL_AGENT_ID,
    RATION_SCHEDULE_ARTIFACT_ID,
    RATION_SCHEDULE_PERIOD_ID,
    RATION_SCHEDULE_VERSION_ONE_ID,
    RATION_SCHEDULE_VERSION_TWO_ID,
    build_first_day,
)
from simulation.actions import ActionAttempt
from simulation.official_record import OfficialRecord


class OfficialRecordTests(unittest.TestCase):
    def test_rewrite_appends_same_period_version_and_moves_current_projection(self):
        record = OfficialRecord(artifact_id=RATION_SCHEDULE_ARTIFACT_ID)
        version_one = record.publish_initial(
            artifact_id=RATION_SCHEDULE_ARTIFACT_ID,
            version_id=RATION_SCHEDULE_VERSION_ONE_ID,
            period_id=RATION_SCHEDULE_PERIOD_ID,
            entitlement_packets=3,
        )

        version_two = record.rewrite(
            artifact_id=RATION_SCHEDULE_ARTIFACT_ID,
            expected_current_version_id=RATION_SCHEDULE_VERSION_ONE_ID,
            version_id=RATION_SCHEDULE_VERSION_TWO_ID,
            period_id=RATION_SCHEDULE_PERIOD_ID,
            entitlement_packets=2,
        )

        self.assertEqual(record.versions, (version_one, version_two))
        self.assertEqual(record.current_version, version_two)
        self.assertEqual(record.current_version_id, RATION_SCHEDULE_VERSION_TWO_ID)
        self.assertEqual(version_one.entitlement_packets, 3)
        self.assertIsNone(version_one.previous_version_id)
        self.assertEqual(version_two.entitlement_packets, 2)
        self.assertEqual(
            version_two.previous_version_id, RATION_SCHEDULE_VERSION_ONE_ID
        )

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

    def test_two_packet_handover_is_separate_from_three_packet_entitlement(self):
        simulation = build_first_day(seed=42)

        for _ in range(9):
            handover_tick = simulation.step()

        publication = next(
            event
            for event in simulation.events
            if event.kind == "official_record_published"
        )
        request = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted"
            and event.actor_id == FOCAL_AGENT_ID
            and event.details["action_kind"] == "request_allocation"
        )
        handover = next(
            event for event in simulation.events if event.kind == "allocation_resolved"
        )

        self.assertEqual(handover.actor_id, "civic-allocation-office")
        self.assertEqual(handover.action_id, request.action_id)
        self.assertEqual(handover.caused_by, (request.event_id,))
        self.assertEqual(
            dict(handover.details),
            {
                "resource_id": "household_allocation",
                "requested_units": 3,
                "granted_units": 2,
                "unfilled_units": 1,
                "objective_allocatable_before": 2,
                "committed_units": 1,
                "recipient_id": FOCAL_AGENT_ID,
            },
        )
        self.assertNotEqual(handover.event_id, publication.event_id)
        self.assertNotIn("artifact_id", handover.details)
        self.assertNotIn("version_id", handover.details)
        self.assertNotIn("entitlement_packets", handover.details)

        record = simulation.world.institution.official_record
        self.assertEqual(record.current_version_id, RATION_SCHEDULE_VERSION_ONE_ID)
        self.assertEqual(record.current_version.entitlement_packets, 3)

        delivered = next(
            observation
            for observation in handover_tick.new_observations
            if observation.details.get("evidence_kind") == "allocation_outcome"
        )
        self.assertEqual(delivered.event_id, handover.event_id)
        self.assertEqual(delivered.source, "allocation counter handover")
        self.assertEqual(
            dict(delivered.details),
            {
                "evidence_kind": "allocation_outcome",
                "resource_id": "household_allocation",
                "granted_units": 2,
                "unfilled_units": 1,
            },
        )
        self.assertEqual(handover_tick.held_units, 2)
        self.assertEqual(handover_tick.remaining_required_units, 1)

    def test_configured_authorized_rewrite_records_attempt_and_accepted_result(self):
        simulation = build_first_day(seed=42)
        for _ in range(10):
            simulation.step()

        record = simulation.world.institution.official_record
        version_one, version_two = record.versions
        attempt = next(
            event
            for event in simulation.events
            if event.kind == "official_record_rewrite_attempted"
        )
        rewritten = next(
            event
            for event in simulation.events
            if event.kind == "official_record_rewritten"
        )
        initial_publication = next(
            event
            for event in simulation.events
            if event.kind == "official_record_published"
        )

        self.assertEqual(attempt.tick, 10)
        self.assertEqual(attempt.actor_id, "civic-allocation-office")
        self.assertIn(
            attempt.actor_id,
            simulation.world.institution.official_record_rewrite_authorized_actor_ids,
        )
        self.assertEqual(
            dict(attempt.details),
            {
                "reason": "align the published schedule with the two-packet issue",
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "expected_current_version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                "version_id": RATION_SCHEDULE_VERSION_TWO_ID,
                "period_id": RATION_SCHEDULE_PERIOD_ID,
                "entitlement_packets": 2,
            },
        )
        self.assertEqual(rewritten.tick, 10)
        self.assertEqual(rewritten.actor_id, attempt.actor_id)
        self.assertEqual(
            rewritten.caused_by, (attempt.event_id, initial_publication.event_id)
        )
        self.assertEqual(
            dict(rewritten.details),
            {
                "reason": "align the published schedule with the two-packet issue",
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "version_id": RATION_SCHEDULE_VERSION_TWO_ID,
                "period_id": RATION_SCHEDULE_PERIOD_ID,
                "entitlement_packets": 2,
                "previous_version_id": RATION_SCHEDULE_VERSION_ONE_ID,
            },
        )
        self.assertEqual(version_one.version_id, RATION_SCHEDULE_VERSION_ONE_ID)
        self.assertEqual(version_one.entitlement_packets, 3)
        self.assertEqual(version_two.version_id, RATION_SCHEDULE_VERSION_TWO_ID)
        self.assertEqual(version_two.entitlement_packets, 2)
        self.assertEqual(
            version_two.previous_version_id, RATION_SCHEDULE_VERSION_ONE_ID
        )
        self.assertEqual(record.current_version, version_two)
        rewrite_event_ids = {attempt.event_id, rewritten.event_id}
        self.assertFalse(
            any(
                observation["event_id"] in rewrite_event_ids
                for observation in simulation.history_data()["observations"]
            )
        )

    def test_unauthorized_current_target_rewrite_is_rejected_without_mutation(self):
        simulation = build_first_day(seed=42)
        simulation.step()

        record = simulation.world.institution.official_record
        version_one = record.current_version
        publication = next(
            event
            for event in simulation.events
            if event.kind == "official_record_published"
        )
        simulation.world.institution.official_record_rewrite_authorized_actor_ids = ()

        for _ in range(9):
            simulation.step()

        attempt = next(
            event
            for event in simulation.events
            if event.kind == "official_record_rewrite_attempted"
        )
        rejected = next(
            event
            for event in simulation.events
            if event.kind == "official_record_rewrite_rejected"
        )

        self.assertEqual(attempt.actor_id, "civic-allocation-office")
        self.assertEqual(
            attempt.details["expected_current_version_id"],
            RATION_SCHEDULE_VERSION_ONE_ID,
        )
        self.assertEqual(rejected.actor_id, attempt.actor_id)
        self.assertEqual(rejected.caused_by, (attempt.event_id,))
        self.assertEqual(
            dict(rejected.details),
            {"reason": "actor is not authorized to rewrite this record"},
        )
        self.assertEqual(record.versions, (version_one,))
        self.assertEqual(record.current_version, version_one)
        self.assertEqual(record.current_version_id, RATION_SCHEDULE_VERSION_ONE_ID)
        self.assertIn(publication, simulation.events)
        self.assertFalse(
            any(event.kind == "official_record_rewritten" for event in simulation.events)
        )
        rejection_event_ids = {attempt.event_id, rejected.event_id}
        self.assertFalse(
            any(
                observation["event_id"] in rejection_event_ids
                for observation in simulation.history_data()["observations"]
            )
        )

    def test_version_two_requires_a_later_valid_consultation_to_be_delivered(self):
        simulation = build_first_day(seed=42)
        for _ in range(10):
            rewrite_tick = simulation.step()

        rewritten = next(
            event
            for event in simulation.events
            if event.kind == "official_record_rewritten"
        )
        observations_before = simulation.observations_for(FOCAL_AGENT_ID)
        record_observations_before = tuple(
            observation
            for observation in observations_before
            if observation.details.get("evidence_kind") == "official_record_version"
        )
        self.assertEqual(len(record_observations_before), 1)
        self.assertEqual(
            record_observations_before[0].details["version_id"],
            RATION_SCHEDULE_VERSION_ONE_ID,
        )
        self.assertFalse(
            any(
                observation.event_id == rewritten.event_id
                or observation.details.get("version_id")
                == RATION_SCHEDULE_VERSION_TWO_ID
                for observation in rewrite_tick.new_observations
            )
        )

        attempted = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="consult_official_record",
                parameters={"artifact_id": RATION_SCHEDULE_ARTIFACT_ID},
                explanation="consult the revised weekly ration schedule",
            )
        )
        consultation = simulation.events[-1]
        self.assertEqual(consultation.kind, "official_record_consulted")
        self.assertEqual(consultation.action_id, attempted.action_id)
        self.assertEqual(
            consultation.caused_by, (attempted.event_id, rewritten.event_id)
        )
        self.assertEqual(
            simulation.observations_for(FOCAL_AGENT_ID), observations_before
        )
        self.assertEqual(
            tuple(
                observation
                for observation in simulation.observations_for(FOCAL_AGENT_ID)
                if observation.details.get("evidence_kind")
                == "official_record_version"
            ),
            record_observations_before,
        )

        delivery_tick = simulation.step()

        delivered = next(
            observation
            for observation in delivery_tick.new_observations
            if observation.details.get("version_id")
            == RATION_SCHEDULE_VERSION_TWO_ID
        )
        self.assertEqual(delivered.agent_id, FOCAL_AGENT_ID)
        self.assertEqual(delivered.event_id, consultation.event_id)
        self.assertEqual(delivered.details["asserted_value"], 2)
        self.assertEqual(
            delivered.details["previous_version_id"],
            RATION_SCHEDULE_VERSION_ONE_ID,
        )
        self.assertEqual(
            delivered.details["publication_event_id"], rewritten.event_id
        )
        record_observations_after = tuple(
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "official_record_version"
        )
        self.assertEqual(
            [
                observation.details["version_id"]
                for observation in record_observations_after
            ],
            [RATION_SCHEDULE_VERSION_ONE_ID, RATION_SCHEDULE_VERSION_TWO_ID],
        )
        self.assertEqual(record_observations_after[0], record_observations_before[0])

    def test_history_and_inspector_preserve_both_versions_and_rewrite_lineage(self):
        simulation = build_first_day(seed=42)
        for _ in range(10):
            simulation.step()

        history = simulation.history_data()
        official_record = history["official_record"]
        publication = next(
            event
            for event in history["events"]
            if event["kind"] == "official_record_published"
        )
        attempt = next(
            event
            for event in history["events"]
            if event["kind"] == "official_record_rewrite_attempted"
        )
        rewritten = next(
            event
            for event in history["events"]
            if event["kind"] == "official_record_rewritten"
        )

        self.assertEqual(
            official_record,
            {
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "current_version_id": RATION_SCHEDULE_VERSION_TWO_ID,
                "versions": [
                    {
                        "version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                        "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                        "period_id": RATION_SCHEDULE_PERIOD_ID,
                        "entitlement_packets": 3,
                        "previous_version_id": None,
                    },
                    {
                        "version_id": RATION_SCHEDULE_VERSION_TWO_ID,
                        "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                        "period_id": RATION_SCHEDULE_PERIOD_ID,
                        "entitlement_packets": 2,
                        "previous_version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                    },
                ],
            },
        )
        self.assertEqual(
            rewritten["caused_by"], [attempt["event_id"], publication["event_id"]]
        )

        inspector_lines = render_inspector(simulation).splitlines()
        inspector_payload = json.loads("\n".join(inspector_lines[2:]))
        self.assertEqual(inspector_payload["official_record"], official_record)
        self.assertEqual(inspector_payload["history"], history)


if __name__ == "__main__":
    unittest.main()
