import unittest
from dataclasses import FrozenInstanceError

from experiments.deterministic_transition import (
    GenericIntegerState,
    TransitionConfiguration,
    apply_transition,
)
from experiments.source_linked_history import SourceLinkedHistory


class DeterministicTransitionTests(unittest.TestCase):
    def test_known_seed_advances_state_and_records_one_objective_event(self):
        history = SourceLinkedHistory()
        configuration = TransitionConfiguration(
            deltas=(-2, 5, 11),
            event_kind="integer_changed",
        )

        result = apply_transition(
            state=GenericIntegerState(tick=7, value=20),
            seed=1,
            configuration=configuration,
            history=history,
        )

        self.assertEqual(result.next_state, GenericIntegerState(tick=8, value=25))
        self.assertEqual(result.event.tick, 8)
        self.assertEqual(result.event.kind, "integer_changed")
        self.assertEqual(
            dict(result.event.details),
            {"before_value": 20, "selected_delta": 5, "after_value": 25},
        )
        self.assertEqual(history.events(), (result.event,))
        self.assertEqual(history.observations(), ())

    def test_fixed_seeds_choose_known_deltas_and_replay_identically(self):
        configuration = TransitionConfiguration(
            deltas=(-2, 5, 11),
            event_kind="integer_changed",
        )

        first_history = SourceLinkedHistory()
        first = apply_transition(
            state=GenericIntegerState(tick=0, value=10),
            seed=5,
            configuration=configuration,
            history=first_history,
        )
        repeated_history = SourceLinkedHistory()
        repeated = apply_transition(
            state=GenericIntegerState(tick=0, value=10),
            seed=5,
            configuration=configuration,
            history=repeated_history,
        )
        zero_seed = apply_transition(
            state=GenericIntegerState(tick=3, value=10),
            seed=0,
            configuration=configuration,
            history=SourceLinkedHistory(),
        )

        self.assertEqual(first.next_state, GenericIntegerState(tick=1, value=21))
        self.assertEqual(first.event.details["selected_delta"], 11)
        self.assertEqual(repeated, first)
        self.assertEqual(repeated_history.events(), first_history.events())
        self.assertEqual(zero_seed.next_state, GenericIntegerState(tick=4, value=8))
        self.assertEqual(zero_seed.event.details["selected_delta"], -2)

    def test_configuration_state_result_and_event_details_are_immutable(self):
        caller_deltas = [3, 9]
        configuration = TransitionConfiguration(
            deltas=caller_deltas,
            event_kind="integer_changed",
        )
        caller_deltas[0] = 100

        result = apply_transition(
            state=GenericIntegerState(tick=2, value=4),
            seed=0,
            configuration=configuration,
            history=SourceLinkedHistory(),
        )

        self.assertEqual(configuration.deltas, (3, 9))
        self.assertEqual(result.next_state.value, 7)
        with self.assertRaises(FrozenInstanceError):
            configuration.event_kind = "rewritten"
        with self.assertRaises(FrozenInstanceError):
            result.next_state.value = 100
        with self.assertRaises(FrozenInstanceError):
            result.event = None
        with self.assertRaises(TypeError):
            result.event.details["after_value"] = 100

    def test_invalid_transition_inputs_do_not_mutate_history(self):
        state = GenericIntegerState(tick=1, value=6)
        configuration = TransitionConfiguration(
            deltas=(2,),
            event_kind="integer_changed",
        )
        invalid_cases = (
            ("state", object(), TypeError),
            ("seed", True, ValueError),
            ("configuration", object(), TypeError),
        )

        for field_name, invalid_value, error_type in invalid_cases:
            with self.subTest(field_name=field_name):
                history = SourceLinkedHistory()
                existing = history.record_event(tick=1, kind="existing_event")
                history.deliver_observation(
                    agent_id="agent-a",
                    event_id=existing.event_id,
                    source="direct sight",
                    delivery_tick=1,
                )
                events_before = history.events()
                observations_before = history.observations()
                arguments = {
                    "state": state,
                    "seed": 0,
                    "configuration": configuration,
                    "history": history,
                }
                arguments[field_name] = invalid_value

                with self.assertRaises(error_type):
                    apply_transition(**arguments)

                self.assertEqual(history.events(), events_before)
                self.assertEqual(history.observations(), observations_before)

        with self.assertRaises(TypeError):
            apply_transition(
                state=state,
                seed=0,
                configuration=configuration,
                history=object(),
            )

    def test_public_records_reject_representative_invalid_values(self):
        invalid_constructors = (
            lambda: GenericIntegerState(tick=True, value=0),
            lambda: GenericIntegerState(tick=-1, value=0),
            lambda: GenericIntegerState(tick=0, value=False),
            lambda: TransitionConfiguration(deltas=(), event_kind="changed"),
            lambda: TransitionConfiguration(deltas=(1, True), event_kind="changed"),
            lambda: TransitionConfiguration(deltas=(1,), event_kind="  "),
        )

        for construct in invalid_constructors:
            with self.subTest(construct=construct):
                with self.assertRaises(ValueError):
                    construct()


if __name__ == "__main__":
    unittest.main()
