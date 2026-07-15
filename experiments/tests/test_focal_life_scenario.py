import inspect
import unittest
from dataclasses import replace

from experiments.focal_life_scenario import (
    FOCAL_AGENT_ID,
    SUPPORTING_AGENT_ID,
    AllocationNeed,
    AllocationRequest,
    PhysicalDiary,
    PrivateAvailabilityBelief,
    ObjectiveAllocation,
    choose_allocation_request,
    choose_after_follow_up_outcome,
    choose_follow_up_after_allocation,
    choose_public_availability_expression,
    choose_supporting_action,
    read_private_diary,
    resolve_allocation_request,
    resolve_follow_up_choice,
    resolve_public_expression,
    resolve_supporting_action,
    run_provisional_focal_life_scenario,
    write_private_diary,
)
from experiments.source_linked_history import SourceLinkedHistory


class FocalLifeScenarioTests(unittest.TestCase):
    def test_fixed_scenario_writes_then_reads_one_possessed_private_diary(self):
        evidence = run_provisional_focal_life_scenario()
        repeated = run_provisional_focal_life_scenario()

        self.assertEqual(evidence.diary.object_id, "provisional-private-diary")
        self.assertEqual(evidence.diary.possessor_id, FOCAL_AGENT_ID)
        self.assertEqual(evidence.diary.location, "carried by provisional-focal")
        self.assertEqual(
            evidence.public_expression_resolution.expression_event.tick,
            5,
        )
        self.assertEqual(
            (evidence.diary_write.started_tick, evidence.diary_write.completed_tick),
            (6, 7),
        )
        self.assertGreater(
            evidence.diary_write.started_tick,
            evidence.public_expression_resolution.expression_event.tick,
        )
        self.assertEqual(evidence.diary_read.read_tick, 8)
        self.assertIs(evidence.diary_read.entry, evidence.diary_write.entry)
        self.assertEqual(evidence.diary.entries, (evidence.diary_write.entry,))
        self.assertEqual(evidence.diary_write, repeated.diary_write)
        self.assertEqual(evidence.diary_read, repeated.diary_read)

    def test_diary_write_requires_physical_possession_before_mutation(self):
        history = SourceLinkedHistory()
        diary = PhysicalDiary(
            object_id="provisional-private-diary",
            location="carried by provisional-focal",
            possessor_id=FOCAL_AGENT_ID,
        )
        perspective = PrivateAvailabilityBelief(
            proposition="available_units",
            units=2,
            source_observation_id="observation-0001",
            source_event_id="event-0001",
        )
        events_before = history.events()

        with self.assertRaisesRegex(ValueError, "must possess the diary"):
            write_private_diary(
                history=history,
                diary=diary,
                actor_id=SUPPORTING_AGENT_ID,
                perspective=perspective,
                start_tick=6,
                duration_ticks=1,
            )

        self.assertEqual(history.events(), events_before)
        self.assertEqual(diary.entries, ())

    def test_diary_write_retains_private_perspective_and_advances_time(self):
        history = SourceLinkedHistory()
        availability = history.record_event(
            tick=1,
            kind="provisional_shelf_availability",
            details={"shelf_units": 2, "committed_units": 1},
        )
        direct = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=availability.event_id,
            source="direct sight",
            delivery_tick=1,
            details={"evidence_kind": "direct", "available_units": 2},
        )
        perspective = PrivateAvailabilityBelief(
            proposition="available_units",
            units=2,
            source_observation_id=direct.observation_id,
            source_event_id=availability.event_id,
        )
        diary = PhysicalDiary(
            object_id="provisional-private-diary",
            location="carried by provisional-focal",
            possessor_id=FOCAL_AGENT_ID,
        )

        result = write_private_diary(
            history=history,
            diary=diary,
            actor_id=FOCAL_AGENT_ID,
            perspective=perspective,
            start_tick=6,
            duration_ticks=1,
        )

        self.assertEqual((result.started_tick, result.completed_tick), (6, 7))
        self.assertGreater(result.completed_tick, result.started_tick)
        self.assertEqual(result.write_event.tick, 7)
        self.assertEqual(result.diary.entries, (result.entry,))
        self.assertEqual(result.entry.perspective_label, "private perspective")
        self.assertEqual(result.entry.proposition, "available_units")
        self.assertEqual(result.entry.units, 2)
        self.assertEqual(
            availability.details["shelf_units"]
            - availability.details["committed_units"],
            1,
        )
        self.assertNotEqual(result.entry.units, 1)
        self.assertEqual(result.entry.source_observation_id, direct.observation_id)
        self.assertNotIn(
            "objective_allocation",
            inspect.signature(write_private_diary).parameters,
        )
        retained_fields = vars(result.entry)
        for forbidden in (
            "shelf_units",
            "committed_units",
            "allocatable_units",
            "objective_availability",
            "raw_events",
            "source_event_id",
        ):
            self.assertNotIn(forbidden, retained_fields)

    def test_physically_accessible_diary_returns_the_exact_retained_entry(self):
        history = SourceLinkedHistory()
        availability = history.record_event(
            tick=1,
            kind="provisional_shelf_availability",
            details={"shelf_units": 2, "committed_units": 1},
        )
        direct = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=availability.event_id,
            source="direct sight",
            delivery_tick=1,
            details={"evidence_kind": "direct", "available_units": 2},
        )
        written = write_private_diary(
            history=history,
            diary=PhysicalDiary(
                object_id="provisional-private-diary",
                location="carried by provisional-focal",
                possessor_id=FOCAL_AGENT_ID,
            ),
            actor_id=FOCAL_AGENT_ID,
            perspective=PrivateAvailabilityBelief(
                proposition="available_units",
                units=2,
                source_observation_id=direct.observation_id,
                source_event_id=availability.event_id,
            ),
            start_tick=6,
            duration_ticks=1,
        )

        read = read_private_diary(
            history=history,
            diary=written.diary,
            actor_id=FOCAL_AGENT_ID,
            entry_id=written.entry.entry_id,
            tick=8,
        )

        self.assertIs(read.entry, written.entry)
        self.assertEqual(read.entry, written.entry)
        self.assertEqual(read.read_tick, 8)
        self.assertEqual(read.read_event.tick, 8)

    def test_pressure_separates_private_belief_public_expression_and_objective_event(self):
        pressured = run_provisional_focal_life_scenario()
        without_pressure = run_provisional_focal_life_scenario(
            include_public_pressure=False
        )
        direct, official = pressured.decision_observations
        objective_event = pressured.events[0]
        objective = pressured.objective_availability_evidence
        private = pressured.private_availability_belief
        public_event = pressured.public_expression_resolution.expression_event

        self.assertEqual(objective.proposition, "available_units")
        self.assertEqual(objective.units, 2)
        self.assertEqual(objective.source_event_id, objective_event.event_id)
        self.assertEqual(private.proposition, "available_units")
        self.assertEqual(private.units, 2)
        self.assertEqual(private.source_observation_id, direct.observation_id)
        self.assertEqual(private.source_event_id, objective_event.event_id)
        self.assertEqual(public_event.kind, "provisional_public_availability_expression")
        self.assertEqual(public_event.details["proposition"], "available_units")
        self.assertEqual(public_event.details["expressed_units"], 4)
        self.assertEqual(
            public_event.details["private_source_observation_id"],
            direct.observation_id,
        )
        self.assertEqual(
            public_event.details["official_source_observation_id"],
            official.observation_id,
        )
        self.assertEqual(
            public_event.details["pressure_observation_id"],
            pressured.focal_pressure_observation.observation_id,
        )
        self.assertEqual(
            public_event.details["objective_availability_event_id"],
            objective_event.event_id,
        )
        self.assertEqual(objective_event.details, {"shelf_units": 2, "committed_units": 1})
        self.assertEqual(
            without_pressure.private_availability_belief.units,
            private.units,
        )
        self.assertEqual(
            without_pressure.public_expression_resolution.expression_event.details[
                "expressed_units"
            ],
            2,
        )
        self.assertIsNone(
            without_pressure.public_expression.trace.selected_pressure_observation_id
        )
        self.assertEqual(
            without_pressure.events[0].details,
            objective_event.details,
        )

    def test_public_expression_resolver_rejects_corrupt_decision_before_mutation(self):
        history = SourceLinkedHistory()
        availability = history.record_event(
            tick=1,
            kind="provisional_shelf_availability",
            details={"shelf_units": 2, "committed_units": 1},
        )
        direct = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=availability.event_id,
            source="direct sight",
            delivery_tick=1,
            details={"evidence_kind": "direct", "available_units": 2},
        )
        official_event = history.record_event(
            tick=2,
            kind="provisional_official_availability_claim",
            details={"claimed_available_units": 4},
        )
        official = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=official_event.event_id,
            source="official notice",
            delivery_tick=2,
            details={"evidence_kind": "official_claim", "available_units": 4},
        )
        pressure_event = history.record_event(
            tick=3,
            kind="provisional_supporting_action",
            details={
                "actor_id": SUPPORTING_AGENT_ID,
                "action": "urge_public_agreement",
            },
        )
        pressure = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=pressure_event.event_id,
            source="supporting person",
            delivery_tick=3,
            details={
                "evidence_kind": "social_pressure",
                "actor_id": SUPPORTING_AGENT_ID,
                "action": "urge_public_agreement",
            },
        )
        decision = choose_public_availability_expression((direct, official, pressure))
        corrupt = replace(decision, expressed_units=3)
        events_before = history.events()

        with self.assertRaisesRegex(ValueError, "public expression decision"):
            resolve_public_expression(
                history=history,
                decision=corrupt,
                selected_private_observation=direct,
                selected_official_observation=official,
                selected_pressure_observation=pressure,
                tick=4,
            )

        self.assertEqual(history.events(), events_before)

        wrong_actor_pressure = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=pressure_event.event_id,
            source="supporting person",
            delivery_tick=3,
            details={
                "evidence_kind": "social_pressure",
                "actor_id": "unrelated-person",
                "action": "urge_public_agreement",
            },
        )
        wrong_source_decision = choose_public_availability_expression(
            (direct, official, wrong_actor_pressure)
        )

        with self.assertRaisesRegex(ValueError, "public pressure evidence"):
            resolve_public_expression(
                history=history,
                decision=wrong_source_decision,
                selected_private_observation=direct,
                selected_official_observation=official,
                selected_pressure_observation=wrong_actor_pressure,
                tick=4,
            )

        self.assertEqual(history.events(), events_before)

    def test_supporting_action_is_recorded_separately_from_its_decision(self):
        history = SourceLinkedHistory()
        request_event = history.record_event(
            tick=1,
            kind="provisional_allocation_requested",
            details={"requested_units": 2},
        )
        visible_request = history.deliver_observation(
            agent_id=SUPPORTING_AGENT_ID,
            event_id=request_event.event_id,
            source="direct sight",
            delivery_tick=1,
            details={
                "evidence_kind": "visible_allocation_request",
                "requested_units": 2,
            },
        )
        decision = choose_supporting_action((visible_request,))

        resolution = resolve_supporting_action(
            history=history,
            decision=decision,
            selected_observation=visible_request,
            tick=2,
        )

        self.assertFalse(hasattr(decision, "event_id"))
        self.assertEqual(resolution.action_event.kind, "provisional_supporting_action")
        self.assertEqual(resolution.action_event.details["action"], decision.action)
        self.assertEqual(
            resolution.action_event.details["selected_observation_id"],
            visible_request.observation_id,
        )
        self.assertEqual(
            resolution.action_event.details["visible_request_event_id"],
            request_event.event_id,
        )

    def test_invalid_supporting_evidence_fails_before_history_mutation(self):
        history = SourceLinkedHistory()
        request_event = history.record_event(
            tick=1,
            kind="provisional_allocation_requested",
            details={"requested_units": 2},
        )
        inconsistent = history.deliver_observation(
            agent_id=SUPPORTING_AGENT_ID,
            event_id=request_event.event_id,
            source="direct sight",
            delivery_tick=1,
            details={
                "evidence_kind": "visible_allocation_request",
                "requested_units": 3,
            },
        )
        decision = choose_supporting_action((inconsistent,))
        events_before = history.events()

        with self.assertRaisesRegex(ValueError, "supporting evidence"):
            resolve_supporting_action(
                history=history,
                decision=decision,
                selected_observation=inconsistent,
                tick=2,
            )

        self.assertEqual(history.events(), events_before)

    def test_supporting_person_acts_only_from_a_delivered_visible_request(self):
        evidence = run_provisional_focal_life_scenario()
        visible_request = evidence.supporting_observations[0]

        acted = choose_supporting_action((visible_request,))
        absent = choose_supporting_action(())

        self.assertEqual(
            tuple(inspect.signature(choose_supporting_action).parameters),
            ("observations",),
        )
        self.assertEqual(visible_request.agent_id, SUPPORTING_AGENT_ID)
        self.assertEqual(
            visible_request.details,
            {"evidence_kind": "visible_allocation_request", "requested_units": 2},
        )
        self.assertEqual(acted.action, "urge_public_agreement")
        self.assertEqual(
            acted.trace.selected_observation_id,
            visible_request.observation_id,
        )
        self.assertEqual(acted.trace.observed_requested_units, 2)
        self.assertIn("visible allocation request", acted.trace.rule)
        self.assertEqual(absent.action, "take_no_social_action")
        self.assertIsNone(absent.trace.selected_observation_id)
        self.assertNotEqual(acted.action, absent.action)
        for hidden_field in (
            "required_units",
            "granted_units",
            "unfilled_units",
            "shelf_units",
            "committed_units",
        ):
            self.assertNotIn(hidden_field, visible_request.details)

    def test_delivered_follow_up_outcome_changes_remaining_constraint_and_choice(self):
        history = SourceLinkedHistory()
        unresolved_event = history.record_event(
            tick=1,
            kind="provisional_follow_up_resolved",
            details={"granted_units": 0, "unfilled_units": 2},
        )
        unresolved = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=unresolved_event.event_id,
            source="direct allocation outcome",
            delivery_tick=1,
            details={
                "evidence_kind": "follow_up_allocation_outcome",
                "granted_units": 0,
                "unfilled_units": 2,
            },
        )
        sufficient_event = history.record_event(
            tick=2,
            kind="provisional_follow_up_resolved",
            details={"granted_units": 2, "unfilled_units": 0},
        )
        sufficient = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=sufficient_event.event_id,
            source="direct allocation outcome",
            delivery_tick=2,
            details={
                "evidence_kind": "follow_up_allocation_outcome",
                "granted_units": 2,
                "unfilled_units": 0,
            },
        )

        absent_choice = choose_after_follow_up_outcome(())
        unresolved_choice = choose_after_follow_up_outcome((unresolved,))
        sufficient_choice = choose_after_follow_up_outcome((sufficient, unresolved))

        self.assertEqual(absent_choice.choice, "wait_for_follow_up_outcome")
        self.assertIsNone(absent_choice.trace.remaining_need_units)
        self.assertEqual(unresolved_choice.choice, "wait_for_changed_conditions")
        self.assertEqual(unresolved_choice.trace.remaining_need_units, 2)
        self.assertEqual(sufficient_choice.choice, "continue_ordinary_task")
        self.assertEqual(sufficient_choice.trace.remaining_need_units, 0)
        self.assertEqual(
            sufficient_choice.trace.selected_observation_id,
            sufficient.observation_id,
        )
        self.assertNotEqual(unresolved_choice.choice, sufficient_choice.choice)

    def test_same_shortfall_changes_later_choice_when_social_pressure_is_delivered(self):
        evidence = run_provisional_focal_life_scenario()
        outcome = evidence.follow_up_outcome_observation
        pressure = evidence.focal_pressure_observation

        without_pressure = choose_after_follow_up_outcome((outcome,))
        with_pressure = choose_after_follow_up_outcome((outcome, pressure))

        self.assertEqual(outcome.details["granted_units"], 0)
        self.assertEqual(outcome.details["unfilled_units"], 2)
        self.assertEqual(without_pressure.choice, "wait_for_changed_conditions")
        self.assertEqual(with_pressure.choice, "seek_alternative_source")
        self.assertEqual(
            with_pressure.trace.selected_observation_id,
            outcome.observation_id,
        )
        self.assertEqual(
            with_pressure.trace.selected_pressure_observation_id,
            pressure.observation_id,
        )
        self.assertNotEqual(without_pressure.choice, with_pressure.choice)

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
        self.assertEqual(evidence.focal_observations[-2], outcome)

    def test_scenario_outcome_and_pressure_constrain_third_autonomous_choice(self):
        evidence = run_provisional_focal_life_scenario()
        outcome = evidence.follow_up_outcome_observation
        pressure = evidence.focal_pressure_observation
        parameters = tuple(inspect.signature(choose_after_follow_up_outcome).parameters)

        self.assertEqual(parameters, ("observations",))
        self.assertEqual(evidence.third_choice.choice, "seek_alternative_source")
        self.assertEqual(
            evidence.third_choice.trace.selected_observation_id,
            outcome.observation_id,
        )
        self.assertEqual(
            evidence.third_choice.trace.selected_pressure_observation_id,
            pressure.observation_id,
        )
        self.assertEqual(
            evidence.third_choice.trace.observed_pressure_action,
            "urge_public_agreement",
        )
        self.assertEqual(
            pressure.details,
            {
                "evidence_kind": "social_pressure",
                "actor_id": SUPPORTING_AGENT_ID,
                "action": "urge_public_agreement",
            },
        )
        self.assertEqual(evidence.third_choice.trace.observed_granted_units, 0)
        self.assertEqual(evidence.third_choice.trace.observed_unfilled_units, 2)
        self.assertEqual(evidence.third_choice.trace.remaining_need_units, 2)
        self.assertIn("latest outcome shortfall", evidence.third_choice.trace.rule)
        self.assertEqual(evidence.third_choice_observations[-2], outcome)
        self.assertEqual(evidence.third_choice_observations[-1], pressure)
        for observation in evidence.third_choice_observations:
            for hidden_field in (
                "shelf_units",
                "committed_units",
                "remaining_allocatable_units",
                "visible_request_event_id",
                "selected_observation_id",
                "observed_requested_units",
                "requested_units",
                "rule",
            ):
                self.assertNotIn(hidden_field, observation.details)

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
            supporting_action,
            follow_up_attempted,
            follow_up_outcome,
            public_expression,
            diary_written,
            diary_read,
        ) = evidence.events
        direct, official, handover, outcome_observation, pressure = (
            evidence.focal_observations
        )

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
            (FOCAL_AGENT_ID,) * 5,
        )
        self.assertEqual(attempted.kind, "provisional_allocation_requested")
        self.assertEqual(handover.event_id, consequence.event_id)
        self.assertEqual(supporting_action.kind, "provisional_supporting_action")
        self.assertEqual(pressure.event_id, supporting_action.event_id)
        self.assertEqual(follow_up_attempted.kind, "provisional_follow_up_attempted")
        self.assertEqual(follow_up_outcome.kind, "provisional_follow_up_resolved")
        self.assertEqual(outcome_observation.event_id, follow_up_outcome.event_id)
        self.assertEqual(
            public_expression.kind,
            "provisional_public_availability_expression",
        )
        self.assertEqual(diary_written.kind, "provisional_private_diary_written")
        self.assertEqual(diary_read.kind, "provisional_private_diary_read")

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
        self.assertEqual(len(first.events), 10)
        self.assertEqual(len(first.focal_observations), 5)
        self.assertEqual(
            first.focal_observations[2].details["granted_units"],
            first.resolution.granted_units,
        )
        self.assertEqual(
            first.focal_observations[-2].details["granted_units"],
            first.follow_up_resolution.granted_units,
        )
        self.assertIn("prefer latest direct", first.request.trace.rule)


if __name__ == "__main__":
    unittest.main()
