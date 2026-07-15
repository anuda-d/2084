import dataclasses
import os
from pathlib import Path
import random
import subprocess
import sys
import textwrap
import time
import unittest
from unittest import mock

from experiments.deterministic_transition import (
    GenericIntegerState,
    TransitionConfiguration,
)
from experiments.explicit_transition_seed_run import (
    ExplicitTransitionInputError,
    ExplicitTransitionMismatchError,
    TransitionInput,
    TransitionTrace,
    empty_explicit_transition_prefix,
    execute_explicit_transitions,
    reproduce_explicit_transitions,
    resume_explicit_transitions,
)
from experiments.source_linked_history import SourceLinkedHistory, WorldEvent


class ExplicitTransitionSeedRunTests(unittest.TestCase):
    DEFAULT_INPUTS = object()

    def setUp(self):
        self.initial_state = GenericIntegerState(tick=4, value=20)
        self.configuration = TransitionConfiguration(
            deltas=(-2, 5, 11), event_kind="integer_changed"
        )
        self.inputs = tuple(
            TransitionInput(step_id=index, stream_id="transition", seed=seed)
            for index, seed in enumerate((1, 5, -2, 8))
        )

    def execute(self, inputs=DEFAULT_INPUTS):
        return execute_explicit_transitions(
            initial_state=self.initial_state,
            configuration=self.configuration,
            transition_inputs=self.inputs if inputs is self.DEFAULT_INPUTS else inputs,
        )

    # Evidence 1: equal complete inputs.
    def test_equal_complete_inputs_have_equal_state_events_and_traces(self):
        first = self.execute()
        second = self.execute()

        self.assertEqual(first.final_state, second.final_state)
        self.assertEqual(first.events, second.events)
        self.assertEqual(first.traces, second.traces)
        self.assertEqual(first.final_state, GenericIntegerState(tick=8, value=52))
        self.assertIsInstance(first.events, tuple)
        self.assertIsInstance(first.traces, tuple)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.traces[0].seed = 99
        with self.assertRaises(TypeError):
            first.events[0].details["after_value"] = 999

    # Evidence 2: changed metadata, including modulo-collision seeds.
    def test_changed_metadata_is_rejected_before_reproduction(self):
        retained = self.execute()
        collision = list(self.inputs)
        collision[1] = dataclasses.replace(collision[1], seed=2)  # 5 % 3 == 2 % 3

        with mock.patch(
            "experiments.explicit_transition_seed_run.apply_transition"
        ) as apply:
            with self.assertRaisesRegex(
                ExplicitTransitionInputError,
                r"transition_inputs\[1\] metadata.*supplied.*expected retained",
            ):
                reproduce_explicit_transitions(
                    retained=retained, transition_inputs=tuple(collision)
                )
            apply.assert_not_called()

        invalid_metadata = (
            (1, dataclasses.replace(self.inputs[1], step_id=0), r"step_id.*expected 1"),
            (1, dataclasses.replace(self.inputs[1], step_id=2), r"step_id.*expected 1"),
            (1, dataclasses.replace(self.inputs[1], stream_id="decision"), r"stream_id.*decision.*transition"),
        )
        for index, replacement, message in invalid_metadata:
            with self.subTest(replacement=replacement):
                changed = list(self.inputs)
                changed[index] = replacement
                with self.assertRaisesRegex(ExplicitTransitionInputError, message):
                    reproduce_explicit_transitions(
                        retained=retained, transition_inputs=tuple(changed)
                    )

    # Evidence 3: prefix resume.
    def test_interior_prefix_resume_preserves_original_steps_and_matches_full_run(self):
        uninterrupted = self.execute()
        prefix = self.execute(self.inputs[:2])
        resumed = resume_explicit_transitions(
            prefix=prefix, suffix_inputs=self.inputs[2:]
        )

        self.assertEqual(resumed.final_state, uninterrupted.final_state)
        self.assertEqual(resumed.events, uninterrupted.events)
        self.assertEqual(resumed.traces, uninterrupted.traces)
        self.assertEqual(resumed.traces[2].step_id, 2)
        self.assertEqual(resumed.transition_inputs, self.inputs)

        empty_prefix = empty_explicit_transition_prefix(
            initial_state=self.initial_state, configuration=self.configuration
        )
        self.assertEqual(
            resume_explicit_transitions(
                prefix=empty_prefix, suffix_inputs=self.inputs
            ),
            uninterrupted,
        )
        self.assertEqual(
            resume_explicit_transitions(prefix=uninterrupted, suffix_inputs=()),
            uninterrupted,
        )

    # Evidence 4: unrelated randomness cannot perturb results.
    def test_unrelated_randomness_before_and_between_steps_is_isolated(self):
        expected = self.execute()
        random.seed(918273)
        _ = [random.random() for _ in range(20)]
        prefix = self.execute(self.inputs[:2])
        _ = random.randbytes(64)
        random.seed(1)
        _ = random.getrandbits(512)
        resumed = resume_explicit_transitions(
            prefix=prefix, suffix_inputs=self.inputs[2:]
        )

        self.assertEqual(resumed.final_state, expected.final_state)
        self.assertEqual(resumed.events, expected.events)
        self.assertEqual(resumed.traces, expected.traces)

    # Evidence 5: every transition is inspectable.
    def test_trace_exposes_exact_identity_seed_and_event_for_each_step(self):
        result = self.execute()

        self.assertEqual(len(result.traces), len(result.events))
        for item, event, trace in zip(
            self.inputs, result.events, result.traces
        ):
            self.assertEqual(trace.step_id, item.step_id)
            self.assertEqual(trace.stream_id, "transition")
            self.assertEqual(trace.seed, item.seed)
            self.assertIs(trace.event, event)

    # Evidence 6: no hidden inputs.
    def test_entropy_clock_global_random_and_hash_seed_are_not_inputs(self):
        random.seed(111)
        expected = self.execute()
        random.seed(999999)
        with mock.patch.object(os, "urandom", side_effect=AssertionError("entropy")), mock.patch.object(
            time, "time", side_effect=AssertionError("clock")
        ), mock.patch.object(
            random, "SystemRandom", side_effect=AssertionError("system random")
        ):
            actual = self.execute()
        self.assertEqual(actual, expected)

        program = textwrap.dedent(
            """
            from experiments.deterministic_transition import GenericIntegerState, TransitionConfiguration
            from experiments.explicit_transition_seed_run import TransitionInput, execute_explicit_transitions
            inputs = tuple(TransitionInput(i, "transition", seed) for i, seed in enumerate((1, 5, -2, 8)))
            result = execute_explicit_transitions(
                initial_state=GenericIntegerState(tick=4, value=20),
                configuration=TransitionConfiguration(deltas=(-2, 5, 11), event_kind="integer_changed"),
                transition_inputs=inputs,
            )
            print(result.final_state.tick, result.final_state.value)
            print(tuple((t.step_id, t.stream_id, t.seed, t.event.tick, t.event.details["after_value"]) for t in result.traces))
            """
        )
        outputs = []
        for hash_seed in ("1", "8675309"):
            environment = os.environ.copy()
            environment["PYTHONHASHSEED"] = hash_seed
            outputs.append(
                subprocess.run(
                    [sys.executable, "-c", program],
                    cwd=Path(__file__).parents[2],
                    env=environment,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
            )
        self.assertEqual(outputs[0], outputs[1])

        source = Path("experiments/explicit_transition_seed_run.py").read_text()
        self.assertIn("seed=item.seed", source)
        self.assertNotIn("import random", source)
        self.assertNotIn("import time", source)

    # Evidence 7: every invalid boundary fails before mutation.
    def test_invalid_collections_and_boundaries_fail_before_any_mutation(self):
        invalid_fresh = (
            (None, r"expected an immutable tuple"),
            ([], r"expected an immutable tuple"),
            ((), r"expected at least one"),
            (({"step_id": 0, "stream_id": "transition"},), r"fields: missing \['seed'\]"),
            (({"step_id": 0, "stream_id": "transition", "seed": 1, "extra": 2},), r"extra \['extra'\]"),
            (({"step_id": True, "stream_id": "transition", "seed": 1},), r"step_id.*not Boolean"),
            (({"step_id": 0, "stream_id": "", "seed": 1},), r"stream_id.*nonempty"),
            (({"step_id": 0, "stream_id": "transition", "seed": False},), r"seed.*not Boolean"),
            ((TransitionInput(0, "transition", 1), TransitionInput(0, "transition", 2)), r"step_id.*expected 1"),
            ((TransitionInput(0, "transition", 1), TransitionInput(2, "transition", 2)), r"step_id.*expected 1"),
            ((TransitionInput(1, "transition", 1), TransitionInput(0, "transition", 2)), r"step_id.*expected 0"),
            ((TransitionInput(0, "observation", 1),), r"only supported stream"),
        )
        for supplied, message in invalid_fresh:
            with self.subTest(supplied=supplied):
                with mock.patch(
                    "experiments.explicit_transition_seed_run.apply_transition"
                ) as apply:
                    with self.assertRaisesRegex(ExplicitTransitionInputError, message):
                        self.execute(supplied)
                    apply.assert_not_called()

        prefix = self.execute(self.inputs[:2])
        bad_event = WorldEvent(
            event_id=prefix.events[1].event_id,
            tick=prefix.events[1].tick,
            kind=prefix.events[1].kind,
            details={**prefix.events[1].details, "after_value": 999},
        )
        inconsistent_prefixes = (
            dataclasses.replace(prefix, final_state=GenericIntegerState(tick=6, value=999)),
            dataclasses.replace(prefix, events=(prefix.events[0], bad_event)),
            dataclasses.replace(
                prefix,
                traces=(
                    prefix.traces[0],
                    dataclasses.replace(prefix.traces[1], seed=999),
                ),
            ),
        )
        for bad_prefix in inconsistent_prefixes:
            with self.subTest(bad_prefix=bad_prefix):
                before = prefix.events
                with mock.patch.object(
                    SourceLinkedHistory,
                    "record_event",
                    side_effect=AssertionError("history mutated"),
                ), mock.patch(
                    "experiments.explicit_transition_seed_run.apply_transition"
                ) as apply:
                    with self.assertRaises(ExplicitTransitionInputError):
                        resume_explicit_transitions(
                            prefix=bad_prefix, suffix_inputs=self.inputs[2:]
                        )
                    apply.assert_not_called()
                self.assertEqual(prefix.events, before)

        with mock.patch.object(
            SourceLinkedHistory,
            "record_event",
            side_effect=AssertionError("history mutated"),
        ):
            with self.assertRaisesRegex(
                ExplicitTransitionInputError, r"suffix_inputs\[0\].step_id.*expected 2"
            ):
                resume_explicit_transitions(
                    prefix=prefix,
                    suffix_inputs=(TransitionInput(0, "transition", 7),),
                )

    def test_valid_reproduction_compares_state_events_and_traces(self):
        retained = self.execute()
        self.assertEqual(
            reproduce_explicit_transitions(
                retained=retained, transition_inputs=self.inputs
            ),
            retained,
        )

        original_apply = __import__(
            "experiments.explicit_transition_seed_run", fromlist=["apply_transition"]
        ).apply_transition

        def changed_apply(*, state, seed, configuration, history):
            return original_apply(
                state=state,
                seed=seed + 1,
                configuration=configuration,
                history=history,
            )

        with mock.patch(
            "experiments.explicit_transition_seed_run.apply_transition",
            side_effect=changed_apply,
        ):
            with self.assertRaises(ExplicitTransitionMismatchError) as caught:
                reproduce_explicit_transitions(
                    retained=retained, transition_inputs=self.inputs
                )
        self.assertEqual(caught.exception.step_id, 0)
        self.assertEqual(caught.exception.stream_id, "transition")
        self.assertEqual(caught.exception.seed, 1)
        self.assertNotEqual(
            caught.exception.recorded_event, caught.exception.reproduced_event
        )
        self.assertNotEqual(
            caught.exception.recorded_trace, caught.exception.reproduced_trace
        )


if __name__ == "__main__":
    unittest.main()
