import inspect
import unittest

from experiments.focal_life_scenario import (
    FOCAL_AGENT_ID,
    AllocationNeed,
    AllocationRequest,
    ObjectiveAllocation,
    choose_allocation_request,
    resolve_allocation_request,
    run_provisional_focal_life_scenario,
)
from experiments.source_linked_history import SourceLinkedHistory


class FocalLifeScenarioTests(unittest.TestCase):
    def test_scenario_separates_objective_state_claims_and_observations(self):
        evidence = run_provisional_focal_life_scenario()
        availability, official_claim, attempted, consequence = evidence.events
        direct, official, handover = evidence.focal_observations

        self.assertEqual(availability.kind, "provisional_shelf_availability")
        self.assertEqual(availability.details["shelf_units"], 2)
        self.assertEqual(availability.details["committed_units"], 1)
        self.assertEqual(official_claim.kind, "provisional_official_availability_claim")
        self.assertEqual(official_claim.details["claimed_available_units"], 4)
        self.assertNotEqual(availability.event_id, official_claim.event_id)

        self.assertEqual(direct.event_id, availability.event_id)
        self.assertEqual(direct.details["available_units"], 2)
        self.assertNotIn("committed_units", direct.details)
        self.assertEqual(official.event_id, official_claim.event_id)
        self.assertEqual(official.details["available_units"], 4)
        self.assertEqual(
            tuple(item.agent_id for item in evidence.focal_observations),
            (FOCAL_AGENT_ID, FOCAL_AGENT_ID, FOCAL_AGENT_ID),
        )
        self.assertEqual(attempted.kind, "provisional_allocation_requested")
        self.assertEqual(handover.event_id, consequence.event_id)

    def test_decision_uses_only_filtered_observations_and_need_constraints(self):
        evidence = run_provisional_focal_life_scenario()
        parameters = tuple(inspect.signature(choose_allocation_request).parameters)

        self.assertEqual(parameters, ("observations", "need"))
        self.assertEqual(evidence.request.requested_units, 2)
        self.assertEqual(len(evidence.request.trace.observed_availability), 2)
        direct, official = evidence.request.trace.observed_availability
        self.assertEqual(
            (direct.observation_id, direct.evidence_kind, direct.units),
            (evidence.decision_observations[0].observation_id, "direct", 2),
        )
        self.assertEqual(
            (official.observation_id, official.evidence_kind, official.units),
            (evidence.decision_observations[1].observation_id, "official_claim", 4),
        )
        self.assertEqual(
            evidence.request.trace.selected_observation_id,
            direct.observation_id,
        )
        self.assertEqual(evidence.request.trace.required_units, 3)
        self.assertEqual(evidence.request.trace.maximum_request_units, 3)

    def test_policy_changes_with_need_and_delivered_observations(self):
        evidence = run_provisional_focal_life_scenario()
        direct, official = evidence.decision_observations

        smaller_need = choose_allocation_request(
            (direct, official),
            AllocationNeed(required_units=1, maximum_request_units=3),
        )
        official_only = choose_allocation_request(
            (official,),
            AllocationNeed(required_units=3, maximum_request_units=3),
        )
        no_availability = choose_allocation_request(
            (),
            AllocationNeed(required_units=3, maximum_request_units=3),
        )

        self.assertEqual(smaller_need.requested_units, 1)
        self.assertEqual(official_only.requested_units, 3)
        self.assertEqual(
            official_only.trace.selected_observation_id,
            official.observation_id,
        )
        self.assertEqual(no_availability.requested_units, 0)

    def test_world_resolution_records_attempt_and_constrained_consequence(self):
        evidence = run_provisional_focal_life_scenario()
        attempted = evidence.resolution.attempted_event
        consequence = evidence.resolution.consequence_event

        self.assertEqual(evidence.request.requested_units, 2)
        self.assertFalse(hasattr(evidence.request, "granted_units"))
        self.assertNotEqual(attempted.event_id, consequence.event_id)
        self.assertEqual(attempted.details["requested_units"], 2)
        self.assertEqual(consequence.details["attempted_event_id"], attempted.event_id)
        self.assertEqual(consequence.details["allocatable_units"], 1)
        self.assertEqual(consequence.details["granted_units"], 1)
        self.assertEqual(consequence.details["unfilled_units"], 1)
        self.assertEqual(evidence.resolution.granted_units, 1)
        self.assertEqual(evidence.resolution.unfilled_units, 1)

    def test_invalid_request_is_rejected_before_resolution_mutates_history(self):
        trace = run_provisional_focal_life_scenario().request.trace
        with self.assertRaisesRegex(ValueError, "requested_units"):
            AllocationRequest(requested_units=-1, trace=trace)
        with self.assertRaisesRegex(ValueError, "requested_units"):
            AllocationRequest(requested_units=True, trace=trace)
        with self.assertRaisesRegex(TypeError, "RequestDecisionTrace"):
            AllocationRequest(requested_units=1, trace=None)

        history = SourceLinkedHistory()
        availability = history.record_event(
            tick=1,
            kind="provisional_shelf_availability",
            details={"shelf_units": 2, "committed_units": 1},
        )
        objective = ObjectiveAllocation(
            availability_event_id=availability.event_id,
            shelf_units=2,
            committed_units=1,
        )
        corrupted_request = AllocationRequest(requested_units=1, trace=trace)
        object.__setattr__(corrupted_request, "requested_units", -1)
        events_before_resolution = history.events()

        with self.assertRaisesRegex(ValueError, "requested_units"):
            resolve_allocation_request(
                history=history,
                request=corrupted_request,
                objective_allocation=objective,
                tick=2,
            )

        self.assertEqual(history.events(), events_before_resolution)

    def test_complete_scenario_is_deterministic_and_traceable(self):
        first = run_provisional_focal_life_scenario()
        repeated = run_provisional_focal_life_scenario()

        self.assertEqual(first, repeated)
        self.assertEqual(len(first.decision_observations), 2)
        self.assertEqual(len(first.events), 4)
        self.assertEqual(len(first.focal_observations), 3)
        self.assertEqual(
            first.focal_observations[-1].details["granted_units"],
            first.resolution.granted_units,
        )
        self.assertIn("prefer latest direct", first.request.trace.rule)


if __name__ == "__main__":
    unittest.main()
