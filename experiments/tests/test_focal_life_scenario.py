import inspect
import unittest

from experiments.focal_life_scenario import (
    FOCAL_AGENT_ID,
    AllocationNeed,
    AllocationRequest,
    ObjectiveAllocation,
    choose_allocation_request,
    choose_follow_up_after_allocation,
    resolve_allocation_request,
    resolve_follow_up_choice,
    run_provisional_focal_life_scenario,
)
from experiments.source_linked_history import SourceLinkedHistory


class FocalLifeScenarioTests(unittest.TestCase):
    def test_follow_up_resolution_records_attempt_and_objectively_constrained_outcome(self):
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
        request = AllocationRequest(
            requested_units=2,
            trace=run_provisional_focal_life_scenario().request.trace,
        )
        prior_resolution = resolve_allocation_request(
            history=history,
            request=request,
            objective_allocation=objective,
            tick=2,
        )
        handover = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=prior_resolution.consequence_event.event_id,
            source="direct handover",
            delivery_tick=2,
            details={
                "evidence_kind": "allocation_handover",
                "granted_units": prior_resolution.granted_units,
                "unfilled_units": prior_resolution.unfilled_units,
            },
        )
        need = AllocationNeed(required_units=3, maximum_request_units=3)
        decision = choose_follow_up_after_allocation((handover,), need)

        resolution = resolve_follow_up_choice(
            history=history,
            decision=decision,
            selected_handover=handover,
            prior_resolution=prior_resolution,
            objective_allocation=objective,
            tick=3,
        )

        self.assertEqual(decision.choice, "seek_remaining_allocation")
        self.assertEqual(resolution.attempted_event.details["choice"], decision.choice)
        self.assertEqual(
            resolution.attempted_event.details["selected_observation_id"],
            handover.observation_id,
        )
        self.assertEqual(
            resolution.attempted_event.details["prior_consequence_event_id"],
            prior_resolution.consequence_event.event_id,
        )
        self.assertEqual(
            resolution.outcome_event.details["attempted_event_id"],
            resolution.attempted_event.event_id,
        )
        self.assertEqual(resolution.outcome_event.details["remaining_allocatable_units"], 0)
        self.assertEqual(resolution.granted_units, 0)
        self.assertEqual(resolution.unfilled_units, 2)

    def test_invalid_follow_up_resolution_evidence_fails_before_history_mutation(self):
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
        request = AllocationRequest(
            requested_units=2,
            trace=run_provisional_focal_life_scenario().request.trace,
        )
        prior_resolution = resolve_allocation_request(
            history=history,
            request=request,
            objective_allocation=objective,
            tick=2,
        )
        handover = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=prior_resolution.consequence_event.event_id,
            source="direct handover",
            delivery_tick=2,
            details={
                "evidence_kind": "allocation_handover",
                "granted_units": 1,
                "unfilled_units": 1,
            },
        )
        decision = choose_follow_up_after_allocation(
            (handover,),
            AllocationNeed(required_units=3, maximum_request_units=3),
        )
        object.__setattr__(decision.trace, "observed_granted_units", True)
        events_before_resolution = history.events()

        with self.assertRaisesRegex(ValueError, "observed_granted_units"):
            resolve_follow_up_choice(
                history=history,
                decision=decision,
                selected_handover=handover,
                prior_resolution=prior_resolution,
                objective_allocation=objective,
                tick=3,
            )

        self.assertEqual(history.events(), events_before_resolution)

        object.__setattr__(decision.trace, "observed_granted_units", 1)
        object.__setattr__(
            prior_resolution.attempted_event,
            "details",
            {
                "availability_event_id": availability.event_id,
                "requested_units": 99,
            },
        )
        corrupted_events = history.events()

        with self.assertRaisesRegex(ValueError, "prior resolution evidence"):
            resolve_follow_up_choice(
                history=history,
                decision=decision,
                selected_handover=handover,
                prior_resolution=prior_resolution,
                objective_allocation=objective,
                tick=3,
            )

        self.assertEqual(history.events(), corrupted_events)

    def test_follow_up_choice_changes_with_delivered_grant(self):
        history = SourceLinkedHistory()
        partial_event = history.record_event(
            tick=1,
            kind="provisional_allocation_resolved",
            details={"granted_units": 1},
        )
        partial = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=partial_event.event_id,
            source="direct handover",
            delivery_tick=1,
            details={"evidence_kind": "allocation_handover", "granted_units": 1},
        )
        sufficient_event = history.record_event(
            tick=2,
            kind="provisional_allocation_resolved",
            details={"granted_units": 3},
        )
        sufficient = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=sufficient_event.event_id,
            source="direct handover",
            delivery_tick=2,
            details={"evidence_kind": "allocation_handover", "granted_units": 3},
        )
        need = AllocationNeed(required_units=3, maximum_request_units=3)

        partial_choice = choose_follow_up_after_allocation((partial,), need)
        sufficient_choice = choose_follow_up_after_allocation((sufficient,), need)

        self.assertEqual(partial_choice.choice, "seek_remaining_allocation")
        self.assertEqual(partial_choice.trace.observed_granted_units, 1)
        self.assertEqual(partial_choice.trace.remaining_units, 2)
        self.assertEqual(sufficient_choice.choice, "continue_ordinary_task")
        self.assertEqual(sufficient_choice.trace.observed_granted_units, 3)
        self.assertEqual(sufficient_choice.trace.remaining_units, 0)

    def test_follow_up_waits_when_no_handover_was_delivered(self):
        decision = choose_follow_up_after_allocation(
            (),
            AllocationNeed(required_units=3, maximum_request_units=3),
        )

        self.assertEqual(decision.choice, "wait_for_handover")
        self.assertIsNone(decision.trace.selected_observation_id)
        self.assertIsNone(decision.trace.observed_granted_units)
        self.assertEqual(decision.trace.remaining_units, 3)

    def test_scenario_delivered_handover_drives_later_ordinary_choice(self):
        evidence = run_provisional_focal_life_scenario()
        parameters = tuple(
            inspect.signature(choose_follow_up_after_allocation).parameters
        )
        handover = evidence.follow_up_observations[-1]

        self.assertEqual(parameters, ("observations", "need"))
        self.assertEqual(evidence.follow_up.choice, "seek_remaining_allocation")
        self.assertEqual(
            evidence.follow_up.trace.selected_observation_id,
            handover.observation_id,
        )
        self.assertEqual(
            handover.event_id,
            evidence.resolution.consequence_event.event_id,
        )
        self.assertNotIn("committed_units", handover.details)
        self.assertEqual(evidence.follow_up.trace.observed_granted_units, 1)
        self.assertEqual(evidence.follow_up.trace.remaining_units, 2)
        self.assertEqual(evidence.follow_up.trace.required_units, 3)
        self.assertIn("latest handover", evidence.follow_up.trace.rule)

    def test_scenario_delivers_only_understandable_follow_up_outcome(self):
        evidence = run_provisional_focal_life_scenario()
        handover = evidence.follow_up_observations[-1]
        resolution = evidence.follow_up_resolution
        outcome = evidence.follow_up_outcome_observation

        self.assertEqual(evidence.follow_up.choice, "seek_remaining_allocation")
        self.assertEqual(
            resolution.attempted_event.details["selected_observation_id"],
            handover.observation_id,
        )
        self.assertEqual(
            resolution.attempted_event.details["prior_consequence_event_id"],
            evidence.resolution.consequence_event.event_id,
        )
        self.assertEqual(outcome.event_id, resolution.outcome_event.event_id)
        self.assertEqual(
            outcome.details,
            {
                "evidence_kind": "follow_up_allocation_outcome",
                "granted_units": 0,
                "unfilled_units": 2,
            },
        )
        self.assertNotIn("committed_units", outcome.details)
        self.assertNotIn("shelf_units", outcome.details)
        self.assertNotIn("remaining_allocatable_units", outcome.details)
        self.assertEqual(evidence.focal_observations[-1], outcome)

    def test_follow_up_rejects_invalid_public_inputs(self):
        history = SourceLinkedHistory()
        event = history.record_event(
            tick=1,
            kind="provisional_allocation_resolved",
            details={"granted_units": 1},
        )
        invalid_grant = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=event.event_id,
            source="direct handover",
            delivery_tick=1,
            details={"evidence_kind": "allocation_handover", "granted_units": True},
        )
        need = AllocationNeed(required_units=3, maximum_request_units=3)

        with self.assertRaisesRegex(TypeError, "observations must be a tuple"):
            choose_follow_up_after_allocation([], need)
        with self.assertRaisesRegex(TypeError, "AllocationNeed"):
            choose_follow_up_after_allocation((), None)
        with self.assertRaisesRegex(TypeError, "Observation records"):
            choose_follow_up_after_allocation((object(),), need)
        with self.assertRaisesRegex(ValueError, "observed granted_units"):
            choose_follow_up_after_allocation((invalid_grant,), need)

    def test_scenario_separates_objective_state_claims_and_observations(self):
        evidence = run_provisional_focal_life_scenario()
        (
            availability,
            official_claim,
            attempted,
            consequence,
            follow_up_attempted,
            follow_up_outcome,
        ) = evidence.events
        direct, official, handover, outcome_observation = evidence.focal_observations

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
            (FOCAL_AGENT_ID,) * 4,
        )
        self.assertEqual(attempted.kind, "provisional_allocation_requested")
        self.assertEqual(handover.event_id, consequence.event_id)
        self.assertEqual(follow_up_attempted.kind, "provisional_follow_up_attempted")
        self.assertEqual(follow_up_outcome.kind, "provisional_follow_up_resolved")
        self.assertEqual(outcome_observation.event_id, follow_up_outcome.event_id)

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
        self.assertEqual(len(first.events), 6)
        self.assertEqual(len(first.focal_observations), 4)
        self.assertEqual(
            first.focal_observations[2].details["granted_units"],
            first.resolution.granted_units,
        )
        self.assertEqual(
            first.focal_observations[-1].details["granted_units"],
            first.follow_up_resolution.granted_units,
        )
        self.assertIn("prefer latest direct", first.request.trace.rule)


if __name__ == "__main__":
    unittest.main()
