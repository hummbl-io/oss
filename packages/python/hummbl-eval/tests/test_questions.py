import unittest

from hummbl_eval.lifecycle import LifecycleError, QuestionEvent, replay_question


class QuestionLifecycleTests(unittest.TestCase):
    def test_preserves_original_and_reopens_answer(self) -> None:
        events = [
            QuestionEvent("CREATED", "What is the first pilot?"),
            QuestionEvent("PARTIAL_ANSWER", answer_ref="record:partial"),
            QuestionEvent("ANSWERED", answer_ref="record:answer"),
            QuestionEvent("REOPENED", reason="evidence expired"),
        ]
        state = replay_question("Q-024", events)
        self.assertEqual(state.original_text, "What is the first pilot?")
        self.assertEqual(state.status, "open")
        self.assertEqual(len(state.events), 4)

    def test_rejects_answer_without_reference(self) -> None:
        with self.assertRaises(LifecycleError):
            replay_question(
                "Q-001",
                [QuestionEvent("CREATED", "Question"), QuestionEvent("ANSWERED")],
            )

    def test_rephrase_defer_and_invalid_transitions(self) -> None:
        state = replay_question(
            "Q-002",
            [
                QuestionEvent("CREATED", "Original"),
                QuestionEvent("REPHRASED", "Current"),
                QuestionEvent("DEFERRED", reason="operator gate"),
                QuestionEvent("REOPENED", reason="approved"),
            ],
        )
        self.assertEqual(
            (state.original_text, state.current_text, state.status), ("Original", "Current", "open")
        )

        invalid = [
            [],
            [QuestionEvent("CREATED", "Question"), QuestionEvent("REPHRASED")],
            [QuestionEvent("CREATED", "Question"), QuestionEvent("PARTIAL_ANSWER")],
            [QuestionEvent("CREATED", "Question"), QuestionEvent("REOPENED")],
            [QuestionEvent("CREATED", "Question"), QuestionEvent("DEFERRED")],
            [QuestionEvent("CREATED", "Question"), QuestionEvent("UNKNOWN")],
        ]
        for events in invalid:
            with self.subTest(events=events), self.assertRaises(LifecycleError):
                replay_question("Q-X", events)


if __name__ == "__main__":
    unittest.main()
