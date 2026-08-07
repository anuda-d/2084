import unittest

from experiments.deterministic_transition import GenericIntegerState
from experiments.replay_record import ReplayRecord
from experiments.single_transition_replay import (
    SingleTransitionReplay,
    SingleTransitionReplayInputError,
    SingleTransitionReplayMismatchError,
)
from experiments.source_linked_history import SourceLinkedHistory


class SingleTransitionReplayTests(unittest.TestCase):
    def test_known_record_reproduces_one_transition_and_exact_objective_event(self):
        recorded_history = SourceLinkedHistory()
        expected_event = recorded_history.record_event(
            tick=8,
            kind="integer_changed",
            details={
                "before_value": 20,
                "selected_delta": 5,
                "after_value": 25,
            },
        )
        record = ReplayRecord.capture(
            seed=1,
            configuration={
                "deltas": [-2, 5, 11],
                "event_kind": "integer_changed",
            },
            history=recorded_history,
        )
        replay = SingleTransitionReplay.capture(
            initial_state=GenericIntegerState(tick=7, value=20),
            record=record,
        )

        result = replay.reproduce()

        self.assertEqual(result.next_state, GenericIntegerState(tick=8, value=25))
        self.assertEqual(result.event, expected_event)
        self.assertEqual(record.events, (expected_event,))
        self.assertEqual(record.observations, ())

    def test_mismatched_initial_state_is_explicit_and_does_not_mutate_inputs(self):
        recorded_history = SourceLinkedHistory()
        recorded_history.record_event(
            tick=8,
            kind="integer_changed",
            details={
                "before_value": 20,
                "selected_delta": 5,
                "after_value": 25,
            },
        )
        record = ReplayRecord.capture(
            seed=1,
            configuration={
                "deltas": [-2, 5, 11],
                "event_kind": "integer_changed",
            },
            history=recorded_history,
        )
        caller_state = GenericIntegerState(tick=7, value=999)
        replay = SingleTransitionReplay.capture(
            initial_state=caller_state,
            record=record,
        )
        history_before = recorded_history.events()
        record_before = record.to_data()

        with self.assertRaisesRegex(
            SingleTransitionReplayMismatchError,
            "objective history",
        ):
            replay.reproduce()

        self.assertEqual(caller_state, GenericIntegerState(tick=7, value=999))
        self.assertIsNot(replay.initial_state, caller_state)
        self.assertEqual(record.to_data(), record_before)
        self.assertEqual(recorded_history.events(), history_before)

    def test_invalid_transition_configuration_is_rejected_at_capture(self):
        recorded_history = SourceLinkedHistory()
        recorded_history.record_event(
            tick=8,
            kind="integer_changed",
            details={
                "before_value": 20,
                "selected_delta": 5,
                "after_value": 25,
            },
        )
        record = ReplayRecord.capture(
            seed=1,
            configuration={"deltas": [-2, 5, 11]},
            history=recorded_history,
        )
        record_before = record.to_data()
        history_before = recorded_history.events()

        with self.assertRaisesRegex(
            SingleTransitionReplayInputError,
            "configuration fields",
        ):
            SingleTransitionReplay.capture(
                initial_state=GenericIntegerState(tick=7, value=20),
                record=record,
            )

        self.assertEqual(record.to_data(), record_before)
        self.assertEqual(recorded_history.events(), history_before)

    def test_record_must_contain_exactly_one_objective_event(self):
        for event_count in (0, 2):
            with self.subTest(event_count=event_count):
                recorded_history = SourceLinkedHistory()
                for index in range(event_count):
                    recorded_history.record_event(
                        tick=index + 1,
                        kind="integer_changed",
                        details={
                            "before_value": index,
                            "selected_delta": 1,
                            "after_value": index + 1,
                        },
                    )
                record = ReplayRecord.capture(
                    seed=0,
                    configuration={
                        "deltas": [1],
                        "event_kind": "integer_changed",
                    },
                    history=recorded_history,
                )
                history_before = recorded_history.events()

                with self.assertRaisesRegex(
                    SingleTransitionReplayInputError,
                    "exactly one objective event",
                ):
                    SingleTransitionReplay.capture(
                        initial_state=GenericIntegerState(tick=0, value=0),
                        record=record,
                    )

                self.assertEqual(recorded_history.events(), history_before)

    def test_configuration_and_history_mismatches_report_both_event_sequences(self):
        cases = (
            (
                "configuration",
                {"deltas": [-2, 6, 11], "event_kind": "integer_changed"},
                {
                    "before_value": 20,
                    "selected_delta": 5,
                    "after_value": 25,
                },
                26,
            ),
            (
                "history",
                {"deltas": [-2, 5, 11], "event_kind": "integer_changed"},
                {
                    "before_value": 20,
                    "selected_delta": 5,
                    "after_value": 999,
                },
                25,
            ),
        )

        for label, configuration, recorded_details, reproduced_after in cases:
            with self.subTest(label=label):
                recorded_history = SourceLinkedHistory()
                recorded_history.record_event(
                    tick=8,
                    kind="integer_changed",
                    details=recorded_details,
                )
                record = ReplayRecord.capture(
                    seed=1,
                    configuration=configuration,
                    history=recorded_history,
                )
                replay = SingleTransitionReplay.capture(
                    initial_state=GenericIntegerState(tick=7, value=20),
                    record=record,
                )
                record_before = record.to_data()
                history_before = recorded_history.events()

                with self.assertRaises(
                    SingleTransitionReplayMismatchError
                ) as caught:
                    replay.reproduce()

                self.assertEqual(caught.exception.recorded_events, record.events)
                self.assertEqual(
                    caught.exception.reproduced_events[0].details["after_value"],
                    reproduced_after,
                )
                self.assertEqual(record.to_data(), record_before)
                self.assertEqual(recorded_history.events(), history_before)


if __name__ == "__main__":
    unittest.main()
