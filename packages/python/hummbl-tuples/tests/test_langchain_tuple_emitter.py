import json
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from reference_impl.langchain_tuple_emitter import LangChainTupleEmitter, emit_langchain_event
from reference_impl.validate_examples import _validate

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"


def validate_tuple(record):
    schema_name = {
        "SYSTEM": "system.schema.json",
        "EVIDENCE": "evidence.schema.json",
    }[record["tuple_type"]]
    schema = json.loads((SCHEMAS_DIR / schema_name).read_text(encoding="utf-8"))
    _validate(record, schema)


class LangChainTupleEmitterTests(unittest.TestCase):
    def test_start_event_emits_system_tuple(self):
        record = emit_langchain_event(
            {
                "event": "on_chain_start",
                "name": "auditability_experiment_chain",
                "run_id": "lc-run-001",
                "parent_ids": [],
                "tags": ["basen"],
                "metadata": {"control_mode": "AI_AUTONOMOUS"},
                "data": {"input": {"task": "compare traces"}},
            },
            intent_id="intent-portable-interface-demo",
            task_id="task-langchain-emitter-demo",
            time="2026-05-03T15:50:00Z",
        )

        self.assertEqual(record["tuple_type"], "SYSTEM")
        self.assertEqual(record["tuple_data"]["adapter"], "langchain")
        self.assertEqual(record["tuple_data"]["source_run_id"], "lc-run-001")
        validate_tuple(record)

    def test_end_event_emits_evidence_tuple(self):
        emitter = LangChainTupleEmitter(
            intent_id="intent-portable-interface-demo",
            task_id="task-langchain-emitter-demo",
        )
        record = emitter.emit(
            {
                "event": "on_chain_end",
                "name": "auditability_experiment_chain",
                "run_id": "lc-run-001",
                "data": {"output": {"result": "experiment defined"}},
            },
            time="2026-05-03T15:50:08Z",
        )

        self.assertEqual(record["tuple_type"], "EVIDENCE")
        self.assertEqual(record["tuple_data"]["event"], "on_chain_end")
        validate_tuple(record)

    def test_id_is_stable_for_same_event(self):
        event = {"event": "on_tool_start", "name": "search", "run_id": "lc-run-002"}
        first = emit_langchain_event(
            event,
            intent_id="intent-portable-interface-demo",
            task_id="task-langchain-emitter-demo",
            time="2026-05-03T15:51:00Z",
        )
        second = emit_langchain_event(
            event,
            intent_id="intent-portable-interface-demo",
            task_id="task-langchain-emitter-demo",
            time="2026-05-03T15:52:00Z",
        )

        self.assertEqual(first["id"], second["id"])

    def test_non_json_native_values_have_canonical_encodings(self):
        event = {
            "event": "on_tool_start",
            "name": "search",
            "run_id": "lc-run-003",
            "data": {
                "payload": b"same-bytes",
                "started": datetime(2026, 5, 13, 20, 30, tzinfo=timezone.utc),
                "day": date(2026, 5, 13),
                "labels": {"zeta", "alpha"},
            },
        }

        first = emit_langchain_event(
            event,
            intent_id="intent-portable-interface-demo",
            task_id="task-langchain-emitter-demo",
            time="2026-05-03T15:51:00Z",
        )
        second = emit_langchain_event(
            {**event, "data": {**event["data"], "labels": {"alpha", "zeta"}}},
            intent_id="intent-portable-interface-demo",
            task_id="task-langchain-emitter-demo",
            time="2026-05-03T15:52:00Z",
        )

        encoded = first["tuple_data"]["data"]
        self.assertEqual(
            encoded["payload"],
            {"__type": "bytes", "base64": "c2FtZS1ieXRlcw=="},
        )
        self.assertEqual(
            encoded["started"],
            {"__type": "datetime", "iso": "2026-05-13T20:30:00+00:00"},
        )
        self.assertEqual(encoded["day"], {"__type": "date", "iso": "2026-05-13"})
        self.assertEqual(encoded["labels"], {"__type": "set", "items": ["alpha", "zeta"]})
        self.assertEqual(first["id"], second["id"])

    def test_unknown_non_json_native_values_fail_loudly(self):
        class OpaqueValue:
            pass

        with self.assertRaisesRegex(TypeError, "Unsupported non-JSON-native value"):
            emit_langchain_event(
                {
                    "event": "on_tool_start",
                    "name": "search",
                    "run_id": "lc-run-004",
                    "data": {"opaque": OpaqueValue()},
                },
                intent_id="intent-portable-interface-demo",
                task_id="task-langchain-emitter-demo",
            )

    def test_missing_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-empty string 'event'"):
            emit_langchain_event(
                {"name": "missing_event"},
                intent_id="intent-portable-interface-demo",
                task_id="task-langchain-emitter-demo",
            )


if __name__ == "__main__":
    unittest.main()
