import unittest
from dataclasses import FrozenInstanceError

from experiments.source_linked_history import SourceLinkedHistory


class SourceLinkedHistoryTests(unittest.TestCase):
    def test_later_official_claim_does_not_rewrite_earlier_event(self):
        history = SourceLinkedHistory()
        experienced = history.record_event(
            tick=3,
            kind="ration_posted",
            details={"amount": 20},
        )

        official_claim = history.record_event(
            tick=8,
            kind="official_claim_broadcast",
            details={"claimed_amount": 25},
        )

        self.assertEqual(
            history.events(),
            (experienced, official_claim),
        )
        self.assertEqual(experienced.details["amount"], 20)
        self.assertEqual(experienced.tick, 3)

    def test_observation_requires_existing_event_source_and_valid_delivery_tick(self):
        history = SourceLinkedHistory()
        event = history.record_event(tick=5, kind="door_opened")

        with self.assertRaisesRegex(ValueError, "unknown event_id"):
            history.deliver_observation(
                agent_id="agent-a",
                event_id="event-9999",
                source="direct sight",
                delivery_tick=5,
            )
        with self.assertRaisesRegex(ValueError, "source must be a nonempty string"):
            history.deliver_observation(
                agent_id="agent-a",
                event_id=event.event_id,
                source="  ",
                delivery_tick=5,
            )
        with self.assertRaisesRegex(ValueError, "before its event"):
            history.deliver_observation(
                agent_id="agent-a",
                event_id=event.event_id,
                source="direct sight",
                delivery_tick=4,
            )

        observation = history.deliver_observation(
            agent_id="agent-a",
            event_id=event.event_id,
            source="direct sight",
            delivery_tick=5,
        )
        self.assertEqual(observation.event_id, event.event_id)
        self.assertEqual(observation.source, "direct sight")
        self.assertEqual(observation.delivery_tick, 5)

    def test_agents_only_receive_their_own_observations(self):
        history = SourceLinkedHistory()
        event = history.record_event(tick=1, kind="bell_rang")
        for agent_id in ("agent-a", "agent-b", "agent-a"):
            history.deliver_observation(
                agent_id=agent_id,
                event_id=event.event_id,
                source="hallway speaker",
                delivery_tick=2,
            )

        agent_a_observations = history.observations_for("agent-a")
        agent_b_observations = history.observations_for("agent-b")

        self.assertEqual(len(agent_a_observations), 2)
        self.assertTrue(
            all(item.agent_id == "agent-a" for item in agent_a_observations)
        )
        self.assertEqual(len(agent_b_observations), 1)
        self.assertEqual(agent_b_observations[0].agent_id, "agent-b")

    def test_returned_records_and_input_aliases_cannot_mutate_history(self):
        history = SourceLinkedHistory()
        caller_details = {
            "amount": 20,
            "witnesses": ["agent-a"],
            "nested": {"location": "canteen"},
        }
        event = history.record_event(
            tick=3,
            kind="ration_posted",
            details=caller_details,
        )
        observation = history.deliver_observation(
            agent_id="agent-a",
            event_id=event.event_id,
            source="notice board",
            delivery_tick=4,
            details={"legibility": "clear"},
        )

        caller_details["amount"] = 99
        caller_details["witnesses"].append("agent-b")
        caller_details["nested"]["location"] = "archive"
        self.assertEqual(event.details["amount"], 20)
        self.assertEqual(event.details["witnesses"], ("agent-a",))
        self.assertEqual(event.details["nested"]["location"], "canteen")

        with self.assertRaises(TypeError):
            event.details["amount"] = 99
        with self.assertRaises(TypeError):
            event.details["nested"]["location"] = "archive"
        with self.assertRaises(FrozenInstanceError):
            observation.source = "rewritten source"
        with self.assertRaises(TypeError):
            observation.details["legibility"] = "rewritten"
        with self.assertRaises(AttributeError):
            history.events().append(event)

        self.assertEqual(history.events()[0].details["amount"], 20)
        self.assertEqual(
            history.observations_for("agent-a")[0].source,
            "notice board",
        )


if __name__ == "__main__":
    unittest.main()
