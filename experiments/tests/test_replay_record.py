import copy
import unittest
from dataclasses import FrozenInstanceError

from experiments.replay_record import ReplayRecord
from experiments.source_linked_history import SourceLinkedHistory


class ReplayRecordTests(unittest.TestCase):
    def make_history(self):
        history = SourceLinkedHistory()
        first = history.record_event(
            tick=3,
            kind="ration_posted",
            details={
                "amount": 20,
                "labels": ["morning", {"language": "newspeak"}],
                "notice": b"A-20",
            },
        )
        second = history.record_event(
            tick=8,
            kind="official_claim_broadcast",
            details={"claimed_amount": 25, "audible": True},
        )
        history.deliver_observation(
            agent_id="agent-a",
            event_id=second.event_id,
            source="hallway speaker",
            delivery_tick=9,
            details={"clarity": 0.75},
        )
        history.deliver_observation(
            agent_id="agent-b",
            event_id=first.event_id,
            source="direct sight",
            delivery_tick=10,
            details={"remembered": None},
        )
        return history

    def test_round_trip_restores_equivalent_ordered_immutable_history(self):
        configuration = {
            "district": "north",
            "rates": [1, 2.5],
            "switches": {"announcements": True},
        }
        record = ReplayRecord.capture(
            seed=2084,
            configuration=configuration,
            history=self.make_history(),
        )

        data = record.to_data()
        round_tripped = ReplayRecord.from_data(data)
        restored = round_tripped.restore_history()

        self.assertEqual(round_tripped, record)
        self.assertEqual(round_tripped.to_data(), data)
        self.assertEqual(restored.events(), record.events)
        self.assertEqual(restored.observations(), record.observations)
        self.assertEqual(round_tripped.seed, 2084)
        self.assertEqual(round_tripped.configuration["rates"], (1, 2.5))
        self.assertEqual(
            [item.agent_id for item in restored.observations()],
            ["agent-a", "agent-b"],
        )

        configuration["rates"].append(99)
        data["configuration"]["switches"]["announcements"] = False
        data["events"][0]["details"]["labels"].append("rewritten")
        self.assertEqual(round_tripped.configuration["rates"], (1, 2.5))
        self.assertTrue(
            round_tripped.configuration["switches"]["announcements"]
        )
        self.assertEqual(len(round_tripped.events[0].details["labels"]), 2)

        with self.assertRaises(TypeError):
            round_tripped.configuration["district"] = "south"
        with self.assertRaises(TypeError):
            round_tripped.events[0].details["amount"] = 25
        with self.assertRaises(FrozenInstanceError):
            round_tripped.observations[0].source = "rewritten"

    def test_malformed_input_is_rejected_without_mutating_caller_data(self):
        valid = ReplayRecord.capture(
            seed=2084,
            configuration={"mode": "experiment"},
            history=self.make_history(),
        ).to_data()

        cases = (
            ("noninteger version", lambda data: data.update(version=1.0)),
            ("unknown event", lambda data: data["observations"][0].update(event_id="event-9999")),
            ("delivery before event", lambda data: data["observations"][0].update(delivery_tick=1)),
            ("noncanonical event identifier", lambda data: data["events"][0].update(event_id="custom")),
            ("unsupported nested value", lambda data: data["events"][0]["details"].update(bad={1, 2})),
            ("missing field", lambda data: data["observations"][0].pop("source")),
        )

        for label, corrupt in cases:
            with self.subTest(label=label):
                malformed = copy.deepcopy(valid)
                corrupt(malformed)
                before = copy.deepcopy(malformed)
                with self.assertRaises((TypeError, ValueError)):
                    ReplayRecord.from_data(malformed)
                self.assertEqual(malformed, before)


if __name__ == "__main__":
    unittest.main()
