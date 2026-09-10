import unittest
import uuid

from hummbl_eval.records import Record, RecordError, new_urn_uuid7


class RecordTests(unittest.TestCase):
    def test_uuid7_urn_and_immutable_payload(self) -> None:
        record_id = new_urn_uuid7()
        self.assertEqual(uuid.UUID(record_id.removeprefix("urn:uuid:")).version, 7)

        source = {"value": [1, 2]}
        record = Record.create(
            record_type="hummbl:Claim",
            schema_id="hummbl:claim",
            schema_version="0.1.0",
            payload=source,
            actor_id="actor:tester",
            source_id="node:test",
            source_sequence=1,
        )
        source["value"].append(3)
        self.assertEqual(record.payload, {"value": [1, 2]})
        self.assertTrue(record.payload_digest.startswith("sha256:"))

    def test_rejects_invalid_type_and_sequence(self) -> None:
        with self.assertRaises(RecordError):
            Record.create("Claim", "schema", "1", {}, "actor", "source", -1)

    def test_rejects_invalid_ids_required_fields_and_uuid_time(self) -> None:
        with self.assertRaises(RecordError):
            new_urn_uuid7(timestamp_ms=-1)
        with self.assertRaises(RecordError):
            Record.create("hummbl:Claim", "", "1", {}, "actor", "source", 1)
        with self.assertRaises(RecordError):
            Record.create(
                "hummbl:Claim",
                "schema",
                "1",
                {},
                "actor",
                "source",
                1,
                record_id="not-a-urn",
            )
        with self.assertRaises(RecordError):
            Record.create(
                "hummbl:Claim",
                "schema",
                "1",
                {},
                "actor",
                "source",
                1,
                record_id="urn:uuid:not-a-uuid",
            )

    def test_runtime_fields_match_record_schema_constraints(self) -> None:
        valid = dict(
            record_type="hummbl:Claim",
            schema_id="hummbl:claim",
            schema_version="0.1.0",
            payload={},
            actor_id="actor:tester",
            source_id="node:test",
            source_sequence=0,
        )
        invalid = [
            {**valid, "record_type": "HUMMBL:Claim"},
            {**valid, "created_at": "not-a-date"},
            {**valid, "maturity": "unknown"},
            {**valid, "confidentiality": "secret"},
            {**valid, "actor_id": ""},
            {**valid, "source_sequence": "0"},
            {**valid, "maturity": ["candidate"]},
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(RecordError):
                Record.create(**values)


if __name__ == "__main__":
    unittest.main()
