import unittest

from hummbl import StepType, StructuredToolUse, ToolUseCapture


class ToolUseCaptureTests(unittest.TestCase):
    def setUp(self):
        self.capture = ToolUseCapture()
        self.protocol = StructuredToolUse()

    def test_capture_from_messages_builds_valid_recovery_trace(self):
        messages = [
            {
                "role": "user",
                "content": "Investigate why the feature flag is enabled.",
            },
            {
                "role": "assistant",
                "content": (
                    "<think>I know the feature is active in production. "
                    "I still need the config source, so I will search the "
                    "repository for the flag definition.</think>"
                    "<tool_call>"
                    '{"name":"repo_search","arguments":{"query":"FEATURE_X"}}'
                    "</tool_call>"
                ),
            },
            {
                "role": "user",
                "content": (
                    "<tool_response>"
                    '{"matches":["config.py: FEATURE_X = False"]}'
                    "</tool_response>"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "<think>The result contradicts my assumption about the "
                    "effective value. I should inspect the runtime override "
                    "before finalizing.</think>"
                    "<tool_call>"
                    '{"name":"open_file","arguments":{"path":"env.py"}}'
                    "</tool_call>"
                ),
            },
            {
                "role": "user",
                "content": (
                    "<tool_response>"
                    '{"content":"FEATURE_X = True"}'
                    "</tool_response>"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "<think>The override explains the behavior and confirms "
                    "the root cause.</think>"
                    "<answer>FEATURE_X is overridden in env.py.</answer>"
                ),
            },
        ]

        trace = self.capture.capture_from_messages(messages)

        self.assertEqual(trace.outcome, "finalize")
        self.assertEqual(len(trace.get_steps_by_type(StepType.ACTION)), 2)

        decisions = trace.get_steps_by_type(StepType.DECISION)
        self.assertEqual(
            [step.metadata["status"] for step in decisions],
            ["recover", "finalize"],
        )

        violations = self.protocol.validate_trace(trace)
        self.assertEqual(violations, [])

        summary = self.capture.summary([trace])
        self.assertEqual(summary["tool_calls"], 2)
        self.assertEqual(summary["recoveries"], 1)
        self.assertEqual(summary["finalizations"], 1)

    def test_capture_from_spotagenticcot_row_preserves_context(self):
        row = {
            "id": "spot-row-1",
            "system": "You are an expert analyst that must think before tools.",
            "images": [{"src": "example.jpg"}],
            "conversations": [
                {
                    "from": "human",
                    "value": "<image> Determine the location of this image.",
                },
                {
                    "from": "assistant",
                    "value": (
                        "<think>I see a bridge and coastal shoreline. "
                        "I still need exact coordinates, so I will search "
                        "for the landmark.</think>"
                        "<tool_call>"
                        '{"name":"search_web","arguments":{"query":"coastal bridge landmark coordinates"}}'
                        "</tool_call>"
                    ),
                },
                {
                    "from": "human",
                    "value": (
                        "<tool_response>"
                        '{"result":"The bridge viewpoint is at 55.57, 12.91"}'
                        "</tool_response>"
                    ),
                },
                {
                    "from": "assistant",
                    "value": (
                        "<think>The search result confirms the landmark and "
                        "provides coordinates.</think>"
                        "<answer>{\"latitude\":55.57,\"longitude\":12.91}</answer>"
                    ),
                },
            ],
        }

        trace = self.capture.capture_from_spotagenticcot_row(row)

        self.assertEqual(trace.outcome, "finalize")
        self.assertIn("spotagenticcot", trace.tags)
        self.assertIn("spot-row-1", trace.tags)

        reflections = trace.get_steps_by_type(StepType.REFLECTION)
        self.assertEqual(len(reflections), 1)
        self.assertEqual(reflections[0].metadata["source"], "spotagenticcot")
        self.assertEqual(reflections[0].metadata["row_id"], "spot-row-1")
        self.assertEqual(reflections[0].metadata["image_count"], 1)

        violations = self.protocol.validate_trace(trace)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
