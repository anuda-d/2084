import unittest
import json
import subprocess
import sys
from dataclasses import fields, replace

from twenty_eighty_four.core.actions import ACTION_KINDS, ActionAttempt, ActionResult
from twenty_eighty_four.core.agents import AgentView
from twenty_eighty_four.core.institutions import InstitutionView
from twenty_eighty_four.core.events import freeze_mapping
from twenty_eighty_four.observer.inspector import render_inspector
from twenty_eighty_four.observer.terminal import render_terminal
from twenty_eighty_four.core.simulation import FocalSnapshot
from twenty_eighty_four.policies.focal_policy import FocalPolicy
from twenty_eighty_four.scenarios.first_day import (
    CLERK_ID,
    CO_WORKER_ID,
    FOCAL_AGENT_ID,
    build_first_day,
)


class LivingSimulationStepTests(unittest.TestCase):
    def test_first_step_records_travel_attempt_without_teleporting(self):
        simulation = build_first_day(seed=42)

        snapshot = simulation.step()

        self.assertEqual(simulation.tick, 1)
        self.assertEqual(snapshot.tick, 1)
        self.assertEqual(snapshot.location, "home")
        self.assertEqual(snapshot.current_action, "travel to workplace")
        attempts = [
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        ]
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].details["action_kind"], "travel")
        self.assertEqual(attempts[0].details["destination"], "workplace")
        self.assertEqual(simulation.inspector_state()["agent_locations"][FOCAL_AGENT_ID], "home")

    def test_travel_consumes_two_ticks_and_completes_through_a_linked_event(self):
        simulation = build_first_day(seed=42)

        simulation.step()
        tick_two = simulation.step()
        tick_three = simulation.step()

        self.assertEqual(tick_two.location, "home")
        self.assertEqual(tick_three.location, "workplace")
        attempt = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        completion = next(
            event
            for event in simulation.events
            if event.kind == "travel_completed" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(completion.tick, 3)
        self.assertEqual(completion.action_id, attempt.action_id)
        self.assertEqual(completion.caused_by, (attempt.event_id,))

    def test_agent_view_receives_an_immutable_result_only_when_travel_completes(self):
        simulation = build_first_day(seed=42)

        simulation.step()
        self.assertEqual(simulation.agent_view(FOCAL_AGENT_ID).action_results, ())
        simulation.step()
        self.assertEqual(simulation.agent_view(FOCAL_AGENT_ID).action_results, ())

        simulation.step()

        result = simulation.agent_view(FOCAL_AGENT_ID).action_results[-1]
        attempt = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        completion = next(
            event
            for event in simulation.events
            if event.kind == "travel_completed" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(result.action_id, attempt.action_id)
        self.assertEqual(result.attempt_event_id, attempt.event_id)
        self.assertEqual(result.outcome_event_id, completion.event_id)
        self.assertEqual(result.action_kind, "travel")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.resolved_tick, 3)
        with self.assertRaises(AttributeError):
            result.status = "rejected"

    def test_remote_allocation_request_is_rejected_without_resource_mutation(self):
        simulation = build_first_day(seed=42)
        resources_before = simulation.inspector_state()["objective_resources"].copy()

        attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="request_allocation",
                parameters={"requested_units": 3},
                explanation="request three household units",
            )
        )

        self.assertEqual(
            simulation.inspector_state()["objective_resources"], resources_before
        )
        rejection = simulation.events[-1]
        self.assertEqual(rejection.kind, "action_rejected")
        self.assertEqual(rejection.action_id, attempt.action_id)
        self.assertEqual(rejection.caused_by, (attempt.event_id,))
        self.assertIn("allocation_office", rejection.details["reason"])
        result = simulation.agent_view(FOCAL_AGENT_ID).action_results[-1]
        self.assertEqual(result.action_id, attempt.action_id)
        self.assertEqual(result.outcome_event_id, rejection.event_id)
        self.assertEqual(result.action_kind, "request_allocation")
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, rejection.details["reason"])

    def test_arrival_is_delivered_as_an_observation_before_work_is_selected(self):
        simulation = build_first_day(seed=42)

        simulation.step()
        simulation.step()
        snapshot = simulation.step()

        self.assertEqual(snapshot.location, "workplace")
        self.assertEqual(snapshot.current_action, "work the morning ledger shift")
        arrival = next(
            observation
            for observation in snapshot.new_observations
            if observation.details.get("evidence_kind") == "arrival"
        )
        self.assertEqual(arrival.agent_id, FOCAL_AGENT_ID)
        self.assertEqual(arrival.delivery_tick, 3)
        self.assertEqual(arrival.details["evidence_kind"], "arrival")
        completion = next(
            event for event in simulation.events if event.event_id == arrival.event_id
        )
        self.assertEqual(completion.kind, "travel_completed")

    def test_completed_work_obligation_drives_travel_to_allocation_office(self):
        simulation = build_first_day(seed=42)

        snapshots = [simulation.step() for _ in range(5)]

        self.assertEqual(snapshots[3].location, "workplace")
        self.assertEqual(snapshots[3].current_action, "work the morning ledger shift")
        tick_five = snapshots[4]
        self.assertEqual(tick_five.location, "workplace")
        self.assertEqual(tick_five.current_action, "travel to allocation office")
        self.assertEqual(len(tick_five.new_observations), 1)
        work_observation = tick_five.new_observations[0]
        self.assertEqual(work_observation.details["evidence_kind"], "work_completed")
        self.assertEqual(work_observation.delivery_tick, 5)

    def test_direct_resource_observation_forms_a_sourced_private_belief(self):
        simulation = build_first_day(seed=42)

        snapshot = [simulation.step() for _ in range(7)][-1]

        self.assertEqual(snapshot.location, "allocation_office")
        direct = next(
            observation
            for observation in snapshot.new_observations
            if observation.details.get("evidence_kind") == "direct_resource_claim"
        )
        self.assertEqual(direct.details["proposition"], "daily_allocation_units")
        self.assertEqual(direct.details["asserted_value"], 3)
        self.assertNotIn("committed_units", direct.details)
        private = next(
            belief
            for belief in snapshot.beliefs
            if belief.context == "private" and belief.proposition == "daily_allocation_units"
        )
        self.assertEqual(private.asserted_value, 3)
        self.assertEqual(private.source_observation_ids, (direct.observation_id,))
        self.assertEqual(private.last_updated_tick, 7)
        self.assertEqual(private.confidence, 0.9)
        self.assertEqual(snapshot.current_action, "wait for the allocation briefing")

    def test_official_claim_conflicts_with_private_belief_and_drives_a_sourced_request(self):
        simulation = build_first_day(seed=42)

        snapshot = [simulation.step() for _ in range(8)][-1]

        official = next(
            observation
            for observation in snapshot.new_observations
            if observation.details.get("evidence_kind") == "official_resource_claim"
        )
        self.assertEqual(official.details["asserted_value"], 5)
        private = next(belief for belief in snapshot.beliefs if belief.context == "private")
        public = next(belief for belief in snapshot.beliefs if belief.context == "public")
        self.assertEqual(private.asserted_value, 3)
        self.assertEqual(public.asserted_value, 5)
        self.assertEqual(private.conflicts_with, (public.belief_id,))
        self.assertEqual(public.conflicts_with, (private.belief_id,))
        self.assertEqual(snapshot.current_action, "request 3 allocation units")
        request = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted"
            and event.actor_id == FOCAL_AGENT_ID
            and event.details["action_kind"] == "request_allocation"
        )
        direct = next(
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "direct_resource_claim"
        )
        self.assertEqual(request.details["requested_units"], 3)
        self.assertEqual(request.details["evidence_observation_ids"], (direct.observation_id,))
        self.assertFalse(
            any(
                observation.details.get("evidence_kind") == "allocation_outcome"
                for observation in snapshot.new_observations
            )
        )

    def test_request_resolves_from_objective_commitments_but_delivers_only_the_outcome(self):
        simulation = build_first_day(seed=42)
        for _ in range(8):
            simulation.step()

        snapshot = simulation.step()

        request = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted"
            and event.details["action_kind"] == "request_allocation"
        )
        resolution = next(
            event for event in simulation.events if event.kind == "allocation_resolved"
        )
        self.assertEqual(resolution.action_id, request.action_id)
        self.assertEqual(resolution.caused_by, (request.event_id,))
        self.assertEqual(resolution.details["objective_allocatable_before"], 2)
        self.assertEqual(resolution.details["committed_units"], 1)
        self.assertEqual(resolution.details["granted_units"], 2)
        outcome = next(
            observation
            for observation in snapshot.new_observations
            if observation.details.get("evidence_kind") == "allocation_outcome"
        )
        self.assertEqual(dict(outcome.details), {
            "evidence_kind": "allocation_outcome",
            "granted_units": 2,
            "unfilled_units": 1,
        })
        self.assertEqual(snapshot.current_action, "wait after the partial allocation")
        self.assertEqual(
            simulation.inspector_state()["objective_resources"]["granted_units"], 2
        )

    def test_granted_units_become_holdings_only_when_the_handover_is_delivered(self):
        simulation = build_first_day(seed=42)
        initial_view = simulation.agent_view(FOCAL_AGENT_ID)
        self.assertEqual(initial_view.required_resource_id, "household_allocation")
        self.assertEqual(dict(initial_view.resource_holdings), {})
        self.assertEqual(initial_view.remaining_required_units, 3)
        with self.assertRaises(TypeError):
            initial_view.resource_holdings["household_allocation"] = 99

        request_tick = [simulation.step() for _ in range(8)][-1]
        self.assertEqual(request_tick.held_units, 0)
        self.assertEqual(request_tick.remaining_required_units, 3)

        handover_tick = simulation.step()

        self.assertEqual(handover_tick.held_units, 2)
        self.assertEqual(handover_tick.remaining_required_units, 1)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        self.assertEqual(dict(view.resource_holdings), {"household_allocation": 2})
        self.assertEqual(view.remaining_required_units, 1)
        self.assertEqual(
            simulation.inspector_state()["agent_resource_holdings"][FOCAL_AGENT_ID],
            {"household_allocation": 2},
        )
        self.assertEqual(
            simulation.history_data()["agent_resource_holdings"][FOCAL_AGENT_ID],
            {"household_allocation": 2},
        )

    def test_supporting_worker_advances_independently_and_is_seen_only_when_present(self):
        simulation = build_first_day(seed=42)

        tick_one = simulation.step()
        simulation.step()
        tick_three = simulation.step()

        supporting_attempt = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == CO_WORKER_ID
        )
        self.assertEqual(supporting_attempt.tick, 1)
        self.assertEqual(supporting_attempt.details["action_kind"], "work")
        supporting_completion = next(
            event
            for event in simulation.events
            if event.kind == "work_completed" and event.actor_id == CO_WORKER_ID
        )
        self.assertEqual(supporting_completion.tick, 3)
        self.assertFalse(
            any(
                observation.details.get("actor_id") == CO_WORKER_ID
                for observation in tick_one.new_observations
            )
        )
        visible = next(
            observation
            for observation in tick_three.new_observations
            if observation.details.get("evidence_kind") == "visible_supporting_action"
        )
        self.assertEqual(visible.event_id, supporting_completion.event_id)
        self.assertEqual(visible.details["actor_id"], CO_WORKER_ID)
        self.assertEqual(visible.details["action_kind"], "work")

    def test_clerk_reacts_only_to_delivered_public_request_and_official_claim(self):
        simulation = build_first_day(seed=42)

        snapshots = [simulation.step() for _ in range(9)]

        visible_request = next(
            observation
            for observation in simulation.observations_for(CLERK_ID)
            if observation.details.get("evidence_kind") == "visible_allocation_request"
        )
        self.assertEqual(dict(visible_request.details), {
            "evidence_kind": "visible_allocation_request",
            "actor_id": FOCAL_AGENT_ID,
            "requested_units": 3,
        })
        clerk_speech = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted"
            and event.actor_id == CLERK_ID
            and event.details["action_kind"] == "speak"
        )
        official = next(
            observation
            for observation in simulation.observations_for(CLERK_ID)
            if observation.details.get("evidence_kind") == "official_resource_claim"
        )
        self.assertEqual(
            clerk_speech.details["evidence_observation_ids"],
            (visible_request.observation_id, official.observation_id),
        )
        self.assertEqual(clerk_speech.details["asserted_value"], 5)
        self.assertFalse(
            any(
                observation.details.get("evidence_kind") == "social_pressure"
                for observation in snapshots[-1].new_observations
            )
        )

    def test_public_expression_diverges_from_private_belief_under_delivered_pressure(self):
        simulation = build_first_day(seed=42)

        snapshot = [simulation.step() for _ in range(10)][-1]

        pressure = next(
            observation
            for observation in snapshot.new_observations
            if observation.details.get("evidence_kind") == "social_pressure"
        )
        self.assertEqual(pressure.details["pressure"], 0.8)
        self.assertEqual(snapshot.current_action, "repeat the official 5-unit claim publicly")
        private = next(belief for belief in snapshot.beliefs if belief.context == "private")
        self.assertEqual(private.asserted_value, 3)
        expression = next(
            event
            for event in simulation.events
            if event.kind == "public_statement_made" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(expression.details["asserted_value"], 5)
        self.assertEqual(expression.details["private_belief_id"], private.belief_id)
        self.assertEqual(expression.details["pressure_reason"], "public counter protocol")
        self.assertIn(pressure.observation_id, expression.details["evidence_observation_ids"])

    def test_malformed_public_statement_is_rejected_without_mutation_or_policy_crash(self):
        simulation = build_first_day(seed=42)

        attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="speak",
                parameters={
                    "private_belief_id": "belief-does-not-exist",
                    "evidence_observation_ids": (),
                },
                explanation="fabricated statement",
            )
        )

        rejection = simulation.events[-1]
        self.assertEqual(rejection.kind, "action_rejected")
        self.assertEqual(rejection.caused_by, (attempt.event_id,))
        self.assertFalse(
            any(event.kind == "public_statement_made" for event in simulation.events)
        )
        self.assertEqual(
            simulation.agent_view(FOCAL_AGENT_ID).action_results[-1].status,
            "rejected",
        )
        snapshot = simulation.step()
        self.assertEqual(snapshot.current_action, "travel to workplace")

    def test_rejected_public_statement_does_not_redirect_the_focal_policy(self):
        simulation = build_first_day(seed=42)
        for _ in range(9):
            simulation.step()
        private = next(
            belief
            for belief in simulation.agent_view(FOCAL_AGENT_ID).beliefs
            if belief.context == "private"
        )
        simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="speak",
                parameters={
                    "proposition": private.proposition,
                    "asserted_value": 5,
                    "private_belief_id": private.belief_id,
                    "evidence_observation_ids": ("observation-does-not-exist",),
                },
                explanation="rejected public statement",
            )
        )

        selected = FocalPolicy().choose(simulation.agent_view(FOCAL_AGENT_ID))

        self.assertEqual(simulation.events[-1].kind, "action_rejected")
        self.assertEqual(selected.kind, "wait")
        self.assertEqual(selected.explanation, "wait after the partial allocation")

    def test_rejected_work_does_not_satisfy_the_remaining_work_obligation(self):
        simulation = build_first_day(seed=42)
        for _ in range(18):
            simulation.step()
        simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="work",
                explanation="try to replace the trip with work",
            )
        )

        simulation.step()
        arrival = simulation.step()

        self.assertTrue(
            any(
                result.action_kind == "work" and result.status == "rejected"
                for result in simulation.agent_view(FOCAL_AGENT_ID).action_results
            )
        )
        self.assertEqual(arrival.location, "workplace")
        self.assertEqual(arrival.current_action, "resume the afternoon ledger shift")

    def test_every_action_kind_rejects_unexpected_parameters_without_consequences(self):
        cases = {
            "travel": {"destination": "workplace", "unexpected": True},
            "work": {"unexpected": True},
            "request_allocation": {"requested_units": 1, "unexpected": True},
            "speak": {"unexpected": True},
            "write_diary": {"unexpected": True},
            "read_diary": {"unexpected": True},
            "wait": {"unexpected": True},
        }

        for action_kind, parameters in cases.items():
            with self.subTest(action_kind=action_kind):
                simulation = build_first_day(seed=42)
                attempt = simulation.resolve_attempt(
                    ActionAttempt(
                        actor_id=FOCAL_AGENT_ID,
                        kind=action_kind,
                        parameters=parameters,
                        explanation="malformed action",
                    )
                )

                rejection = simulation.events[-1]
                self.assertEqual(rejection.kind, "action_rejected")
                self.assertEqual(rejection.caused_by, (attempt.event_id,))
                self.assertIn("unexpected parameters", rejection.details["reason"])
                self.assertEqual(
                    simulation.agent_view(FOCAL_AGENT_ID).action_results[-1].status,
                    "rejected",
                )
                self.assertEqual(len(simulation.events), 2)

    def test_allocation_request_rejects_an_invalid_evidence_container(self):
        simulation = build_first_day(seed=42)
        for _ in range(7):
            simulation.step()
        resources_before = simulation.inspector_state()["objective_resources"].copy()

        attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="request_allocation",
                parameters={
                    "requested_units": 3,
                    "evidence_observation_ids": 7,
                },
                explanation="malformed allocation request",
            )
        )

        rejection = simulation.events[-1]
        self.assertEqual(rejection.kind, "action_rejected")
        self.assertEqual(rejection.caused_by, (attempt.event_id,))
        self.assertIn("evidence", rejection.details["reason"])
        self.assertEqual(
            simulation.inspector_state()["objective_resources"], resources_before
        )

    def test_diary_write_rejects_invalid_sources_without_raising_or_mutating(self):
        simulation = build_first_day(seed=42)
        diary_before = simulation.inspector_state()["diaries"]["mara-private-diary"]

        attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="write_diary",
                parameters={
                    "object_id": "mara-private-diary",
                    "proposition": "daily_allocation_units",
                    "asserted_value": 3,
                    "source_observation_ids": 7,
                },
                explanation="malformed diary entry",
            )
        )

        rejection = simulation.events[-1]
        self.assertEqual(rejection.kind, "action_rejected")
        self.assertEqual(rejection.caused_by, (attempt.event_id,))
        self.assertIn("diary", rejection.details["reason"])
        self.assertEqual(
            simulation.inspector_state()["diaries"]["mara-private-diary"],
            diary_before,
        )

    def test_diary_write_rejects_a_claim_that_does_not_match_the_cited_belief(self):
        simulation = build_first_day(seed=42)
        for _ in range(8):
            simulation.step()
        simulation.world.agents[FOCAL_AGENT_ID].location = "home"
        direct = next(
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "direct_resource_claim"
        )
        diary_before = simulation.inspector_state()["diaries"]["mara-private-diary"]

        simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="write_diary",
                parameters={
                    "object_id": "mara-private-diary",
                    "proposition": "daily_allocation_units",
                    "asserted_value": 99,
                    "source_observation_ids": (direct.observation_id,),
                },
                explanation="write a claim unrelated to the cited belief",
            )
        )

        self.assertEqual(simulation.events[-1].kind, "action_rejected")
        self.assertIn("match an actor belief", simulation.events[-1].details["reason"])
        self.assertEqual(
            simulation.inspector_state()["diaries"]["mara-private-diary"],
            diary_before,
        )

    def test_unknown_actor_is_rejected_without_raising_or_mutating_agents(self):
        simulation = build_first_day(seed=42)
        locations_before = simulation.inspector_state()["agent_locations"].copy()

        attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id="unknown-person",
                kind="wait",
                explanation="attempt to act without a registered agent",
            )
        )

        rejection = simulation.events[-1]
        self.assertEqual(rejection.kind, "action_rejected")
        self.assertEqual(rejection.caused_by, (attempt.event_id,))
        self.assertIn("not registered", rejection.details["reason"])
        self.assertEqual(
            simulation.inspector_state()["agent_locations"], locations_before
        )
        result = simulation.history_data()["action_results"][-1]
        self.assertEqual(result["actor_id"], "unknown-person")
        self.assertEqual(result["action_id"], attempt.action_id)
        self.assertEqual(result["status"], "rejected")

    def test_diary_write_requires_returning_home_and_completes_after_two_ticks(self):
        simulation = build_first_day(seed=42)

        snapshots = [simulation.step() for _ in range(17)]

        tick_fifteen = snapshots[14]
        self.assertEqual(tick_fifteen.location, "home")
        self.assertEqual(tick_fifteen.current_action, "write the private 3-unit perspective")
        self.assertEqual(
            simulation.snapshot_at(15).accessible_diary_entry_count,
            0,
        )
        self.assertEqual(
            simulation.snapshot_at(16).accessible_diary_entry_count,
            0,
        )
        diary = simulation.inspector_state()["diaries"]["mara-private-diary"]
        self.assertEqual(len(diary["entries"]), 1)
        entry = diary["entries"][0]
        self.assertEqual(entry["asserted_value"], 3)
        self.assertEqual(entry["started_tick"], 15)
        self.assertEqual(entry["completed_tick"], 17)
        direct = next(
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "direct_resource_claim"
        )
        self.assertEqual(entry["source_observation_ids"], [direct.observation_id])

    def test_diary_read_returns_the_immutable_earlier_perspective_after_revision(self):
        simulation = build_first_day(seed=42)

        snapshot = [simulation.step() for _ in range(18)][-1]

        official_events = [
            event for event in simulation.events if event.kind == "official_claim_issued"
        ]
        self.assertEqual([event.details["asserted_value"] for event in official_events], [5, 1])
        self.assertEqual(official_events[1].caused_by, (official_events[0].event_id,))
        read = next(
            observation
            for observation in snapshot.new_observations
            if observation.details.get("evidence_kind") == "diary_read_completed"
        )
        self.assertEqual(read.details["asserted_value"], 3)
        self.assertEqual(read.details["started_tick"], 15)
        self.assertEqual(read.details["completed_tick"], 17)
        written = next(
            event for event in simulation.events if event.kind == "diary_write_completed"
        )
        self.assertEqual(read.details["entry_id"], written.details["entry_id"])
        self.assertEqual(
            read.details["source_observation_ids"],
            written.details["source_observation_ids"],
        )
        self.assertEqual(snapshot.current_action, "travel to workplace after reading the diary")

    def test_run_completes_at_tick_24_and_same_seed_serializes_identically(self):
        first = build_first_day(seed=42)
        second = build_first_day(seed=42)

        first.run(max_ticks=30)
        second.run(max_ticks=30)

        self.assertTrue(first.is_complete)
        self.assertEqual(first.tick, 24)
        self.assertEqual(first.history_data(), second.history_data())
        encoded = json.dumps(first.history_data(), sort_keys=True)
        self.assertIn('"seed": 42', encoded)
        self.assertEqual(
            [event.event_id for event in first.events],
            [event.event_id for event in second.events],
        )
        self.assertEqual(
            [
                observation.observation_id
                for agent_id in first.world.agents
                for observation in first.observations_for(agent_id)
            ],
            [
                observation.observation_id
                for agent_id in second.world.agents
                for observation in second.observations_for(agent_id)
            ],
        )

    def test_history_serializes_one_terminal_result_for_every_resolved_attempt(self):
        simulation = build_first_day(seed=42)
        simulation.run(max_ticks=30)

        results = simulation.history_data()["action_results"]
        attempts = [
            event for event in simulation.events if event.kind == "action_attempted"
        ]

        self.assertEqual(len(results), len(attempts))
        self.assertEqual(
            {result["action_id"] for result in results},
            {attempt.action_id for attempt in attempts},
        )
        self.assertTrue(all(result["status"] == "completed" for result in results))
        for result in results:
            outcome = next(
                event
                for event in simulation.events
                if event.event_id == result["outcome_event_id"]
            )
            self.assertEqual(outcome.action_id, result["action_id"])

    def test_normal_observer_is_filtered_while_inspector_exposes_causal_evidence(self):
        simulation = build_first_day(seed=42)
        simulation.run(max_ticks=30)

        normal = render_terminal(simulation.snapshots)
        inspector = render_inspector(simulation)

        self.assertIn("directly saw 3 allocation units", normal)
        self.assertIn("official broadcast claimed 5 allocation units", normal)
        self.assertIn("2 granted and 1 unfilled", normal)
        self.assertIn("Household allocation: 2 held; 1 still needed.", normal)
        self.assertIn("Private belief: 3 units", normal)
        self.assertIn("repeat the official 5-unit claim publicly", normal)
        self.assertIn("Diary read returned the earlier 3-unit perspective", normal)
        self.assertIn(
            "Reason: direct sight supports three units for the household need, "
            "despite the incompatible official claim.",
            normal,
        )
        self.assertIn(
            "Reason: public counter pressure favors repeating the delivered "
            "official claim while the private belief remains three units.",
            normal,
        )
        for hidden_term in (
            "committed_units",
            "objective_allocatable_before",
            "allocation_resolved",
            "event-",
            "observation-",
            "civic-allocation-office",
        ):
            self.assertNotIn(hidden_term, normal)

        self.assertIn("DEVELOPMENT INSPECTOR — OMNISCIENT", inspector)
        self.assertIn('"committed_units": 1', inspector)
        self.assertIn("allocation_resolved", inspector)
        self.assertIn("event-", inspector)
        self.assertIn("observation-", inspector)
        self.assertIn("caused_by", inspector)

    def test_final_workday_explanation_preserves_the_unmet_household_need(self):
        simulation = build_first_day(seed=42)
        simulation.run(max_ticks=30)

        final = simulation.snapshots[-1]

        self.assertEqual(final.held_units, 2)
        self.assertEqual(final.remaining_required_units, 1)
        self.assertIn("one household allocation unit remains unmet", final.explanation)
        self.assertNotIn("household errand are complete", final.explanation)

    def test_normal_observer_explains_a_focal_rejection_without_hidden_state(self):
        rejection = ActionResult(
            action_id="action-0001",
            attempt_event_id="event-0001",
            outcome_event_id="event-0002",
            actor_id=FOCAL_AGENT_ID,
            action_kind="travel",
            status="rejected",
            resolved_tick=1,
            reason="destination is not reachable from the current location",
        )
        snapshot = FocalSnapshot(
            tick=1,
            location="home",
            aim="complete work and secure the household allocation",
            required_units=3,
            held_units=0,
            remaining_required_units=3,
            current_action="travel to an unavailable location",
            explanation="attempt the planned journey",
            new_observations=(),
            new_action_results=(rejection,),
            beliefs=(),
            accessible_diary_entry_count=0,
            diary_entries=(),
        )

        normal = render_terminal((snapshot,))

        self.assertIn(
            "Action rejected: destination is not reachable from the current location.",
            normal,
        )
        self.assertNotIn("event-0002", normal)
        self.assertNotIn("committed_units", normal)

    def test_module_command_runs_normal_and_explicit_inspector_modes(self):
        normal = subprocess.run(
            [
                sys.executable,
                "-m",
                "twenty_eighty_four.scenarios.first_day",
                "--seed",
                "42",
                "--ticks",
                "30",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        inspected = subprocess.run(
            [
                sys.executable,
                "-m",
                "twenty_eighty_four.scenarios.first_day",
                "--seed",
                "42",
                "--ticks",
                "30",
                "--inspect",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertIn("Normal observer: focal-character knowledge only", normal.stdout)
        self.assertNotIn("committed_units", normal.stdout)
        self.assertNotIn("DEVELOPMENT INSPECTOR", normal.stdout)
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        self.assertIn("DEVELOPMENT INSPECTOR — OMNISCIENT", inspected.stdout)
        self.assertIn('"committed_units": 1', inspected.stdout)

    def test_policy_views_enforce_knowledge_boundaries_and_selection_is_pure(self):
        simulation = build_first_day(seed=42)
        state_before = simulation.inspector_state()
        events_before = simulation.events

        view = simulation.agent_view(FOCAL_AGENT_ID)
        selected = FocalPolicy().choose(view)

        self.assertEqual(selected.kind, "travel")
        self.assertEqual(simulation.inspector_state(), state_before)
        self.assertEqual(simulation.events, events_before)
        agent_fields = {field.name for field in fields(AgentView)}
        for forbidden in (
            "world",
            "resource",
            "objective_allocation",
            "event_history",
            "institution_records",
        ):
            self.assertNotIn(forbidden, agent_fields)
        institution_fields = {field.name for field in fields(InstitutionView)}
        self.assertEqual(institution_fields, {"tick", "records", "reports"})

        simulation.run(max_ticks=30)
        self.assertFalse(simulation.world.institution.reports)
        self.assertFalse(
            any("diary" in key for key in simulation.world.institution.records)
        )

    def test_default_run_demonstrates_the_complete_structured_acceptance_scenario(self):
        simulation = build_first_day(seed=42)

        snapshots = simulation.run(max_ticks=30)

        self.assertEqual(snapshots[0].location, "home")
        self.assertIn("household allocation", snapshots[0].aim)
        self.assertEqual(
            {snapshot.location for snapshot in snapshots},
            {"home", "workplace", "allocation_office"},
        )
        attempts = [event for event in simulation.events if event.kind == "action_attempted"]
        self.assertEqual({event.details["action_kind"] for event in attempts}, ACTION_KINDS)
        self.assertEqual(
            {event.actor_id for event in attempts},
            {FOCAL_AGENT_ID, CO_WORKER_ID, CLERK_ID},
        )

        direct = next(
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "direct_resource_claim"
        )
        official = next(
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "official_resource_claim"
            and observation.details["asserted_value"] == 5
        )
        self.assertEqual(direct.details["proposition"], official.details["proposition"])
        self.assertNotEqual(direct.details["asserted_value"], official.details["asserted_value"])
        self.assertEqual(direct.delivery_tick, 7)
        self.assertEqual(official.delivery_tick, 8)

        request = next(
            event
            for event in attempts
            if event.actor_id == FOCAL_AGENT_ID
            and event.details["action_kind"] == "request_allocation"
        )
        allocation = next(
            event for event in simulation.events if event.kind == "allocation_resolved"
        )
        outcome = next(
            observation
            for observation in simulation.observations_for(FOCAL_AGENT_ID)
            if observation.details.get("evidence_kind") == "allocation_outcome"
        )
        self.assertEqual(request.details["evidence_observation_ids"], (direct.observation_id,))
        self.assertEqual(allocation.caused_by, (request.event_id,))
        self.assertEqual(outcome.event_id, allocation.event_id)
        self.assertEqual(outcome.delivery_tick, 9)
        tick_nine_wait = next(
            event
            for event in attempts
            if event.actor_id == FOCAL_AGENT_ID
            and event.tick == 9
            and event.details["action_kind"] == "wait"
        )
        self.assertIn("handover", tick_nine_wait.details["decision_explanation"])

        private = next(
            belief
            for belief in simulation.world.agents[FOCAL_AGENT_ID].beliefs
            if belief.context == "private"
        )
        expression = next(
            event
            for event in simulation.events
            if event.kind == "public_statement_made" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual((private.asserted_value, expression.details["asserted_value"]), (3, 5))
        self.assertEqual(expression.details["pressure_reason"], "public counter protocol")

        write = next(event for event in simulation.events if event.kind == "diary_write_completed")
        read = next(event for event in simulation.events if event.kind == "diary_read_completed")
        self.assertEqual(write.details["entry_id"], read.details["entry_id"])
        self.assertEqual(write.details["asserted_value"], read.details["asserted_value"])
        self.assertLess(write.tick, read.tick)

        unresolved_action_ids = {
            attempt.action_id
            for attempt in attempts
            if not any(
                event.action_id == attempt.action_id and event.event_id != attempt.event_id
                for event in simulation.events
            )
        }
        self.assertEqual(unresolved_action_ids, set())

    def test_inspector_history_retains_source_linked_belief_transitions(self):
        simulation = build_first_day(seed=42)
        simulation.run(max_ticks=30)

        transitions = simulation.history_data()["belief_transitions"]

        focal_transitions = [
            transition
            for transition in transitions
            if transition["agent_id"] == FOCAL_AGENT_ID
        ]
        self.assertEqual(
            [transition["asserted_value"] for transition in focal_transitions],
            [3, 5, 1],
        )
        self.assertEqual(
            [transition["tick"] for transition in focal_transitions],
            [7, 8, 16],
        )
        for transition in focal_transitions:
            source = next(
                observation
                for observation in simulation.observations_for(FOCAL_AGENT_ID)
                if observation.observation_id == transition["source_observation_id"]
            )
            self.assertEqual(source.delivery_tick, transition["tick"])
        self.assertEqual(focal_transitions[0]["conflicts_with"], [])
        self.assertTrue(focal_transitions[1]["conflicts_with"])
        self.assertIn("belief_transitions", render_inspector(simulation))

    def test_busy_actor_cannot_replace_an_action_already_in_progress(self):
        simulation = build_first_day(seed=42)
        simulation.step()
        original = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )

        duplicate = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="travel",
                parameters={"destination": "workplace"},
                explanation="duplicate travel",
            )
        )
        rejection = simulation.events[-1]
        simulation.step()
        simulation.step()

        self.assertEqual(rejection.kind, "action_rejected")
        self.assertEqual(rejection.action_id, duplicate.action_id)
        self.assertIn("already in progress", rejection.details["reason"])
        completion = next(
            event
            for event in simulation.events
            if event.kind == "travel_completed" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(completion.action_id, original.action_id)
        self.assertEqual(completion.caused_by, (original.event_id,))

    def test_public_private_divergence_requires_pressure_above_explicit_threshold(self):
        simulation = build_first_day(seed=42)
        for _ in range(10):
            simulation.step()
        view = simulation.agent_view(FOCAL_AGENT_ID)
        weakened_observations = tuple(
            replace(
                observation,
                details=freeze_mapping({**dict(observation.details), "pressure": 0.2}),
            )
            if observation.details.get("evidence_kind") == "social_pressure"
            else observation
            for observation in view.observations
        )
        weakened_view = replace(
            view,
            last_attempt=next(
                attempt
                for attempt in reversed(view.action_history)
                if attempt.kind == "wait"
            ),
            action_history=tuple(
                attempt
                for attempt in view.action_history
                if not (
                    attempt.kind == "speak"
                    and "private_belief_id" in attempt.parameters
                )
            ),
            action_results=tuple(
                result
                for result in view.action_results
                if result.action_kind != "speak"
            ),
            observations=weakened_observations,
        )

        selected = FocalPolicy(public_conformity_threshold=0.7).choose(weakened_view)

        self.assertEqual(selected.kind, "wait")
        self.assertEqual(selected.explanation, "wait after the partial allocation")

    def test_selected_action_parameters_are_immutable(self):
        simulation = build_first_day(seed=42)

        selected = FocalPolicy().choose(simulation.agent_view(FOCAL_AGENT_ID))

        with self.assertRaises(TypeError):
            selected.parameters["destination"] = "allocation_office"
        self.assertEqual(selected.parameters["destination"], "workplace")

    def test_nonpossessor_cannot_read_or_write_the_physical_diary(self):
        simulation = build_first_day(seed=42)
        for _ in range(17):
            simulation.step()
        diary_before = simulation.inspector_state()["diaries"]["mara-private-diary"]
        entry_id = diary_before["entries"][0]["entry_id"]

        write_attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=CLERK_ID,
                kind="write_diary",
                parameters={
                    "object_id": "mara-private-diary",
                    "proposition": "daily_allocation_units",
                    "asserted_value": 5,
                    "source_observation_ids": (),
                },
                explanation="write another person's diary",
            )
        )
        write_rejection = simulation.events[-1]
        read_attempt = simulation.resolve_attempt(
            ActionAttempt(
                actor_id=CLERK_ID,
                kind="read_diary",
                parameters={
                    "object_id": "mara-private-diary",
                    "entry_id": entry_id,
                },
                explanation="read another person's diary",
            )
        )
        read_rejection = simulation.events[-1]

        self.assertEqual(write_rejection.kind, "action_rejected")
        self.assertEqual(write_rejection.action_id, write_attempt.action_id)
        self.assertIn("physical access", write_rejection.details["reason"])
        self.assertEqual(read_rejection.kind, "action_rejected")
        self.assertEqual(read_rejection.action_id, read_attempt.action_id)
        self.assertIn("physical access", read_rejection.details["reason"])
        self.assertEqual(
            simulation.inspector_state()["diaries"]["mara-private-diary"],
            diary_before,
        )

    def test_replay_record_contains_complete_authored_scenario_configuration(self):
        simulation = build_first_day(seed=42)
        simulation.run(max_ticks=30)

        configuration = simulation.history_data()["configuration"]

        self.assertEqual(configuration["seed"], 42)
        scenario = configuration["scenario"]
        self.assertEqual(scenario["scenario_id"], "first_day_v1")
        self.assertEqual(scenario["completion_tick"], 24)
        self.assertEqual(scenario["travel_graph"]["home"], ["workplace"])
        self.assertEqual(
            scenario["initial_resource"],
            {"total_units": 3, "committed_units": 1},
        )
        self.assertEqual(scenario["official_claim_schedule"], {"8": 5, "16": 1})
        self.assertEqual(scenario["public_pressure"], 0.8)
        self.assertEqual(scenario["public_conformity_threshold"], 0.7)
        self.assertEqual(scenario["action_durations"]["travel"], 2)
        self.assertEqual(scenario["agent_ids"], [FOCAL_AGENT_ID, CO_WORKER_ID, CLERK_ID])

    def test_public_statement_observation_is_not_misclassified_as_social_pressure(self):
        simulation = build_first_day(seed=42)
        for _ in range(11):
            simulation.step()

        expression = next(
            event
            for event in simulation.events
            if event.kind == "public_statement_made" and event.actor_id == FOCAL_AGENT_ID
        )
        clerk_view = simulation.observations_for(CLERK_ID)
        observed_expression = next(
            observation for observation in clerk_view if observation.event_id == expression.event_id
        )

        self.assertEqual(
            observed_expression.details["evidence_kind"], "public_statement"
        )
        self.assertEqual(observed_expression.details["asserted_value"], 5)
        self.assertNotIn("pressure", observed_expression.details)


if __name__ == "__main__":
    unittest.main()
