import unittest
from dataclasses import FrozenInstanceError, fields

from policies.supporting_policy import TransitStatementPolicy, TransitStatementView
from simulation.decision_eligibility import DecisionTrigger, DecisionTriggerKind
from simulation.events import EventLog


class TransitStatementPolicyTests(unittest.TestCase):
    def setUp(self):
        event_log = EventLog()
        changed = event_log.record(
            tick=510,
            kind="transit_service_changed",
            actor_id="district-transit-authority",
        )
        self.observation = event_log.deliver(
            agent_id="ilan-reed",
            event_id=changed.event_id,
            source="workplace transit service terminal",
            delivery_tick=510,
            details={
                "evidence_kind": "transit_service_status",
                "route": "workplace-home",
                "current_status": "reduced",
                "proposition": "workplace-home tram service is reduced",
                "asserted_value": 1,
            },
        )
        self.trigger = DecisionTrigger(
            kind=DecisionTriggerKind.OBSERVATION_DELIVERED,
            source_id=self.observation.observation_id,
        )
        self.policy = TransitStatementPolicy(recipient_id="mara-vale")

    def view(self, *, addressable_actor_ids=("mara-vale",)):
        return TransitStatementView(
            tick=510,
            agent_id="ilan-reed",
            location="workplace",
            observations=(self.observation,),
            action_results=(),
            triggers=(self.trigger,),
            addressable_actor_ids=addressable_actor_ids,
            valid_actions=("speak", "wait"),
        )

    def test_restricted_view_is_frozen_and_excludes_hidden_authority(self):
        view = self.view()

        self.assertEqual(
            {field.name for field in fields(view)},
            {
                "tick",
                "agent_id",
                "location",
                "observations",
                "action_results",
                "triggers",
                "addressable_actor_ids",
                "valid_actions",
            },
        )
        for hidden in (
            "world",
            "institution",
            "objective_events",
            "mara_private_state",
            "model_records",
        ):
            self.assertFalse(hasattr(view, hidden))
        with self.assertRaises(FrozenInstanceError):
            view.location = "home"

    def test_addressable_recipient_yields_one_evidence_bound_statement(self):
        attempt = self.policy.choose(self.view())

        self.assertEqual(attempt.actor_id, "ilan-reed")
        self.assertEqual(attempt.kind, "speak")
        self.assertEqual(
            dict(attempt.parameters),
            {
                "proposition": "workplace-home tram service is reduced",
                "asserted_value": 1,
                "evidence_observation_ids": (self.observation.observation_id,),
            },
        )

    def test_missing_addressability_yields_ordinary_wait(self):
        attempt = self.policy.choose(self.view(addressable_actor_ids=()))

        self.assertEqual(attempt.actor_id, "ilan-reed")
        self.assertEqual(attempt.kind, "wait")
        self.assertEqual(dict(attempt.parameters), {})


if __name__ == "__main__":
    unittest.main()
