import unittest

from hummbl_eval.records import Record, Relation
from hummbl_eval.validation import SemanticError, validate_graph


def make_record(record_id: str, record_type: str, sequence: int) -> Record:
    return Record.create(
        record_type=record_type,
        schema_id="hummbl:test",
        schema_version="0.1.0",
        payload={"id": record_id},
        actor_id="actor:test",
        source_id="node:test",
        source_sequence=sequence,
        record_id=record_id,
    )


class RelationValidationTests(unittest.TestCase):
    def test_allows_interface_cycle_but_rejects_containment_cycle(self) -> None:
        a = make_record("urn:uuid:00000000-0000-7000-8000-000000000001", "hummbl:System", 1)
        b = make_record("urn:uuid:00000000-0000-7000-8000-000000000002", "hummbl:System", 2)
        interfaces = [
            Relation.create("hummbl:interfaces_with", a.record_id, b.record_id, "actor:test", 3),
            Relation.create("hummbl:interfaces_with", b.record_id, a.record_id, "actor:test", 4),
        ]
        validate_graph([a, b], interfaces)

        contains = [
            Relation.create("hummbl:contains", a.record_id, b.record_id, "actor:test", 5),
            Relation.create("hummbl:contains", b.record_id, a.record_id, "actor:test", 6),
        ]
        with self.assertRaises(SemanticError):
            validate_graph([a, b], contains)

    def test_rejects_receipt_laundering(self) -> None:
        receipt = make_record("urn:uuid:00000000-0000-7000-8000-000000000003", "hummbl:Receipt", 1)
        claim = make_record("urn:uuid:00000000-0000-7000-8000-000000000004", "hummbl:Claim", 2)
        relation = Relation.create(
            "hummbl:supports", receipt.record_id, claim.record_id, "actor:test", 3
        )
        with self.assertRaisesRegex(SemanticError, "Evidence"):
            validate_graph([receipt, claim], [relation])

    def test_accepts_evidence_support_and_rejects_identity_and_endpoint_errors(self) -> None:
        evidence = make_record(
            "urn:uuid:00000000-0000-7000-8000-000000000005", "hummbl:Evidence", 1
        )
        claim = make_record("urn:uuid:00000000-0000-7000-8000-000000000006", "hummbl:Claim", 2)
        support = Relation.create(
            "hummbl:supports", evidence.record_id, claim.record_id, "actor:test", 3
        )
        validate_graph([evidence, claim], [support])
        with self.assertRaisesRegex(SemanticError, "duplicate record"):
            validate_graph([evidence, evidence], [])
        with self.assertRaisesRegex(SemanticError, "duplicate relation"):
            validate_graph([evidence, claim], [support, support])

        missing = Relation.create(
            "hummbl:contains",
            evidence.record_id,
            "urn:uuid:00000000-0000-7000-8000-000000000099",
            "actor:test",
            4,
        )
        with self.assertRaisesRegex(SemanticError, "endpoint"):
            validate_graph([evidence], [missing])

    def test_relation_type_and_actor_fields_match_schema_constraints(self) -> None:
        record_id = "urn:uuid:00000000-0000-7000-8000-000000000010"
        for relation_type in ("HUMMBL:contains", "hummbl:Contains", "contains"):
            with self.subTest(relation_type=relation_type), self.assertRaises(ValueError):
                Relation.create(relation_type, record_id, record_id, "actor:test", 1)
        with self.assertRaises(ValueError):
            Relation.create("hummbl:contains", record_id, record_id, "", 1)


if __name__ == "__main__":
    unittest.main()
