"""Inspection boundaries using a derived comparison fixture and synthetic parser records."""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import asdict, replace
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import types
import unittest
from unittest.mock import patch
import urllib.request

from basen import domain120_inspection as inspection
from basen.domain120_inspection import (
    Base120Index, CatalogCollection, CatalogIdentity, CatalogView, InspectionError,
    OperatorIdentity, SourcePin, UnsupportedCapability,
)

HERE = Path(__file__).resolve().parent
# Map the package's bundled comparison data into the explicitly supported
# SDK record shape. This is a test input, not authenticated canonical provenance.
BUNDLED = json.loads((HERE.parent / "basen/data/base120_registry.json").read_bytes())
BASE120_RAW = json.dumps([
    {"code": row["id"], "name": row["name"], "definition": row["definition"],
     "transformation": row["domain"]} for row in BUNDLED
], ensure_ascii=True).encode("utf-8")
BASE120_SHA = hashlib.sha256(BASE120_RAW).hexdigest()
BASE_PIN = SourcePin("local-file", "normalized-test-comparison-registry.json", BASE120_SHA)


def encode(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True).encode("utf-8")


def local_pin(raw):
    return SourcePin("local-file", "synthetic-parser-fixture.json",
                     hashlib.sha256(raw).hexdigest())


def lattice_document():
    # One parser record, not a generated domain set or admission fixture.
    return {
        "domain": "Parser fixture", "version": "0.1.0",
        "operators": [{
            "code": "P01", "family": "P", "name": "Parser fixture operator",
            "definition": "Existing-format text used solely to exercise a parser.",
            "base120_ancestor": "P1", "status": "candidate",
        }],
        "composition_matrix": {"P": {"IN": "undefined"}},
        "cross_maps": [],
    }


def historical_document():
    # Synthetic shape only; the real historical candidate is exercised by the demo.
    return {
        "set_id": "domain120.parser-fixture.v0.1.0", "family": "Domain120",
        "domain": "parser-fixture", "status": "candidate",
        "base_architecture": "base120.v1.0.0",
        "transformations": {
            **{family: [] for family in inspection.FAMILIES},
            "P": [{"id": "P1", "name": "Parser fixture",
                   "description": "Description kept separate from adaptation.",
                   "base120_source": "P1", "domain_adaptation": "Adaptation fixture.",
                   "examples": ["Not a domain construction"], "receipts": []}],
        },
        "validation": {"receipts": []},
    }


def research_document():
    row = lattice_document()["operators"][0]
    row["state"] = row.pop("status")
    return {
        "lattice_id": "Domain120:Parser Fixture", "domain_pillar": "P05",
        "epistemic_pillar": "Parser fixture", "maturity": "CONVERGING",
        "dimensions": ["fixture dimension"], "capacity": 120,
        "operators": [row], "cross_maps": [],
    }


class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.base = Base120Index(BASE120_RAW, BASE_PIN, "1.0.0")

    def view(self, value=None, namespace="domain120.parser-fixture", raw=None):
        raw = raw if raw is not None else encode(value if value is not None else lattice_document())
        return CatalogView(raw, local_pin(raw), self.base,
                           profile="lattice-object-v0", namespace=namespace)

    def historic(self, value=None):
        raw = encode(value if value is not None else historical_document())
        return CatalogView(raw, local_pin(raw), self.base,
                           profile="transformations-2026-06-draft")

    def research(self, value=None, namespace="domain120.parser-fixture"):
        raw = encode(value if value is not None else research_document())
        return CatalogView(raw, local_pin(raw), self.base,
                           profile="research-draft-2026-08", namespace=namespace)

    def test_research_unknown_version_and_declared_metadata_are_explicit(self):
        document = research_document()
        document["operators"][0]["state"] = "Ratified"
        view = self.research(document)
        result = view.lookup("P01")
        report = result["catalog_context"]
        self.assertIsNone(view.identity.version)
        self.assertIsNone(result["identity"]["catalog"]["version"])
        self.assertIn("absent from source", report["version_origin"])
        self.assertIn("caller-assigned", report["namespace_origin"])
        self.assertEqual(report["domain"], document["lattice_id"])
        self.assertEqual(report["field_sources"]["domain"], "/lattice_id")
        self.assertEqual(report["field_sources"]["declared_operator_status"], "operator /state")
        self.assertIsNone(report["declared_set_status"])
        for field in ("domain_pillar", "epistemic_pillar", "maturity", "dimensions", "capacity"):
            self.assertEqual(report["declared_research_metadata"][field], document[field])
            self.assertNotIn(field, report["projection"]["root_fields_not_in_common_view"])
        self.assertEqual(result["declared_operator_status"], "Ratified")
        self.assertEqual(result["admission"], "not assessed")
        self.assertEqual(result["construction_permission"], "not granted")
        self.assertEqual(result["family_semantic_equivalence"], "not assessed")
        self.assertIn("not authenticated source", result["family_name_origin"])
        self.assertEqual(view.source_document(), document)
        report["declared_research_metadata"]["dimensions"].clear()
        self.assertEqual(view.inspect()["declared_research_metadata"]["dimensions"], ["fixture dimension"])

    def test_unversioned_research_snapshots_coexist_only_with_exact_digest_lookup(self):
        first = self.research()
        doc = research_document()
        doc["operators"][0]["name"] = "Changed parser fixture"
        second = self.research(doc)
        collection = CatalogCollection([first, second])
        for view in (first, second):
            self.assertEqual(collection.lookup(OperatorIdentity(view.identity, "P01")), view.lookup("P01"))
            self.assertEqual(collection.source_bytes(view.identity), view.source_bytes())
        with self.assertRaises(InspectionError):
            CatalogCollection([first, first])
        with self.assertRaises(InspectionError):
            collection.lookup(OperatorIdentity(replace(first.identity, artifact_sha256="0" * 64), "P01"))
        for version in ("", " ", False, 1):
            with self.subTest(version=version), self.assertRaises(InspectionError):
                replace(first.identity, version=version)

    def test_research_cross_maps_keep_unresolved_asymmetric_endpoints(self):
        doc = research_document()
        mapping = {"from": "UNRESOLVED-A", "to": "Domain120:Unknown target",
                   "operator": "UNRESOLVED-B", "reason": "Parser fixture with deliberately asymmetric fields.",
                   "extra": {"source claim": "retained"}}
        doc["cross_maps"] = [mapping]
        view = self.research(doc)
        self.assertEqual(view.source_document()["cross_maps"], [mapping])
        self.assertIn("cross_maps", view.inspect()["projection"]["root_fields_not_in_common_view"])
        self.assertIn("not interpreted", view.inspect()["projection"]["relations"])
        self.assertEqual(view.lookup("P01")["source_record"], doc["operators"][0])
        # This acceptance preserves uncertain data; it does not resolve either code.

    def test_research_shape_and_mixed_profile_fields_fail(self):
        with self.assertRaises(InspectionError):
            self.research(namespace=None)
        for field, value in (("domain", "fixture"), ("version", "0.1.0"),
                             ("set_id", "fixture"), ("transformations", {}),
                             ("status", "candidate"), ("composition_matrix", {})):
            doc = research_document()
            doc[field] = value
            with self.subTest(field=field), self.assertRaises(InspectionError):
                self.research(doc)
        for field, value in (("capacity", True), ("capacity", 0), ("capacity", 1.5),
                             ("dimensions", "fixture"), ("dimensions", [False]),
                             ("maturity", None), ("domain_pillar", []), ("cross_maps", {})):
            doc = research_document()
            doc[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(InspectionError):
                self.research(doc)
        for change in ("missing_state", "mixed_status", "invalid_state"):
            doc = research_document()
            row = doc["operators"][0]
            if change == "missing_state":
                row.pop("state")
            elif change == "mixed_status":
                row["status"] = "candidate"
            else:
                row["state"] = 1
            with self.subTest(change=change), self.assertRaises(InspectionError):
                self.research(doc)

    def test_oss_serializer_shape_accepts_shared_lattice_id_metadata(self):
        # Exact OSS 5e9b9ae7 hummbl_lattice/models.py Lattice.to_dict emits
        # lattice_id alongside domain/version/author/language. It is not an
        # August-only discriminator. This is a parser record, not a new catalog.
        doc = lattice_document()
        doc.update(lattice_id="parser-fixture", author="", language="en")
        view = self.view(doc)
        self.assertEqual(view.lookup("P01")["source_record"], doc["operators"][0])
        self.assertEqual(view.source_document(), doc)
        self.assertIn("lattice_id", view.inspect()["projection"]["root_fields_not_in_common_view"])
        self.assertEqual(view.identity.version, "0.1.0")
        historical = historical_document()
        historical["lattice_id"] = "Additional retained metadata"
        self.assertEqual(self.historic(historical).source_document(), historical)

    def test_research_capacity_and_maturity_remain_source_claims(self):
        doc = research_document()
        doc["capacity"] = 1
        doc["maturity"] = "UNRECOGNIZED SOURCE LABEL"
        second = dict(doc["operators"][0], code="P02")
        doc["operators"].append(second)
        report = self.research(doc).inspect()
        self.assertEqual(report["operator_count"], 2)
        self.assertEqual(report["declared_research_metadata"]["capacity"], 1)
        self.assertIn("no ontology, cardinality or lifecycle validation", report["research_metadata_authority"])
        self.assertEqual(report["admission"], "not assessed")

    def test_pinned_registry_resolves_without_semantic_authority(self):
        result = self.base.resolve("P1")
        self.assertEqual(result["record"]["name"], "First Principles Framing")
        self.assertEqual(result["source"]["sha256"], BASE120_SHA)
        self.assertEqual(result["semantic_correspondence"], "not assessed")
        self.assertNotIn("digest_checked", BASE_PIN.report())
        self.assertEqual(result["source_digest_check"], "matched supplied bytes")

    def test_domain_and_ancestor_identities_remain_distinct(self):
        result = self.view().lookup("P01")
        self.assertEqual(result["identity"]["local_code"], "P01")
        self.assertEqual(result["ancestor"]["code"], "P1")
        self.assertEqual(result["identity"]["catalog"]["namespace"], "domain120.parser-fixture")
        self.assertEqual(result["ancestor"]["registry_version"], "1.0.0")

    def test_caller_version_label_is_explicitly_unverified(self):
        relabeled = Base120Index(BASE120_RAW, BASE_PIN, "9.9.9")
        doc = historical_document()
        doc["base_architecture"] = "base120.v9.9.9"
        raw = encode(doc)
        view = CatalogView(raw, local_pin(raw), relabeled,
                           profile="transformations-2026-06-draft")
        report = view.inspect()
        self.assertIn("caller-supplied comparison label only", report["base120_binding"])
        for item in (relabeled.describe(), view.lookup("P1")["ancestor"]):
            self.assertEqual(item["registry_version"], "9.9.9")
            self.assertEqual(item["registry_version_origin"], "caller-supplied comparison label")
            self.assertIn("not derived", item["registry_version_verification"])

    def test_lookup_keeps_catalog_context_and_qualified_source_access(self):
        doc = historical_document()
        doc.update(license="source-available", visibility="internal",
                   provenance={"method": "synthetic parser fixture"})
        view = self.historic(doc)
        collection = CatalogCollection([view])
        result = collection.lookup(OperatorIdentity(view.identity, "P1"))
        context = result["catalog_context"]
        self.assertEqual(context, collection.inspect(view.identity))
        self.assertEqual(context, view.browse()[0]["catalog_context"])
        self.assertEqual(context["declared_set_status"], "candidate")
        self.assertEqual(context["profile"], "transformations-2026-06-draft")
        self.assertEqual(context["source"]["sha256"], view.identity.artifact_sha256)
        omitted = context["projection"]["root_fields_not_in_common_view"]
        for field in ("license", "visibility", "validation", "provenance"):
            self.assertIn(field, omitted)
        self.assertEqual(collection.source_document(view.identity), doc)
        self.assertEqual(collection.source_bytes(view.identity), encode(doc))
        context["projection"]["root_fields_not_in_common_view"].clear()
        collection.source_document(view.identity)["visibility"] = "mutated"
        self.assertEqual(collection.source_document(view.identity)["visibility"], "internal")
        self.assertIn("visibility", collection.inspect(view.identity)["projection"]["root_fields_not_in_common_view"])
        for method in (collection.inspect, collection.source_document, collection.source_bytes):
            with self.subTest(method=method.__name__), self.assertRaises(InspectionError):
                method("domain120.parser-fixture")
            with self.subTest(method=method.__name__), self.assertRaises(InspectionError):
                method(replace(view.identity, artifact_sha256="0" * 64))

    def test_two_catalogs_same_local_code_are_qualified(self):
        left = self.view(namespace="domain120.fixture-a")
        right = self.view(namespace="domain120.fixture-b")
        collection = CatalogCollection([left, right])
        results = [collection.lookup(OperatorIdentity(view.identity, "P01"))
                   for view in (left, right)]
        self.assertNotEqual(results[0]["identity"], results[1]["identity"])
        with self.assertRaisesRegex(InspectionError, "qualified"):
            collection.lookup("P01")

    def test_same_namespace_version_with_conflicting_bytes_is_rejected(self):
        left = self.view()
        doc = lattice_document()
        doc["comment"] = "different raw artifact"
        right = self.view(doc)
        with self.assertRaisesRegex(InspectionError, "Conflicting content"):
            CatalogCollection([left, right])
        with self.assertRaisesRegex(InspectionError, "Duplicate qualified"):
            CatalogCollection([left, left])

    def test_new_version_can_coexist_but_wrong_digest_cannot_resolve(self):
        old = self.view()
        doc = lattice_document()
        doc["version"] = "0.2.0"
        new = self.view(doc)
        collection = CatalogCollection([old, new])
        self.assertEqual(collection.lookup(OperatorIdentity(new.identity, "P01"))["identity"]["catalog"]["version"], "0.2.0")
        wrong = replace(new.identity, artifact_sha256="0" * 64)
        with self.assertRaisesRegex(InspectionError, "absent"):
            collection.lookup(OperatorIdentity(wrong, "P01"))

    def test_hash_checks_exact_bytes_and_retains_whitespace(self):
        raw = encode(lattice_document())
        view = self.view(raw=raw)
        self.assertEqual(view.source_bytes(), raw)
        spaced = self.view(raw=raw + b"\n")
        self.assertNotEqual(view.identity.artifact_sha256, spaced.identity.artifact_sha256)
        self.assertEqual(view.source_document(), spaced.source_document())
        with self.assertRaisesRegex(InspectionError, "digest"):
            CatalogView(raw + b"\n", local_pin(raw), self.base,
                        profile="lattice-object-v0", namespace="domain120.parser-fixture")

    def test_unknown_fields_are_preserved_and_reported(self):
        doc = lattice_document()
        doc["world_model"] = {"status": "ratified", "unsupported_claim": "unverified"}
        doc["operators"][0]["review"] = {"verdict": "PASS"}
        raw = encode(doc)
        view = self.view(raw=raw)
        self.assertEqual(view.source_bytes(), raw)
        self.assertEqual(view.source_document(), doc)
        result = view.lookup("P01")
        self.assertEqual(result["source_record"]["review"], doc["operators"][0]["review"])
        self.assertIn("review", result["not_projected_fields"])
        report = view.inspect()
        self.assertIn("world_model", report["projection"]["root_fields_not_in_common_view"])
        self.assertEqual(report["admission"], "not assessed")

    def test_mutating_returned_documents_and_records_does_not_change_view(self):
        view = self.view()
        before = view.source_bytes()
        doc = view.source_document()
        doc["operators"][0]["name"] = "mutated"
        result = view.lookup("P01")
        result["source_record"]["name"] = "mutated"
        result["ancestor"]["record"]["name"] = "mutated"
        self.assertEqual(view.source_bytes(), before)
        self.assertEqual(view.lookup("P01")["name"], "Parser fixture operator")
        self.assertEqual(view.lookup("P01")["ancestor"]["record"]["name"], "First Principles Framing")

    def test_claimed_ratification_cannot_enable_capabilities(self):
        doc = lattice_document()
        doc["status"] = "ratified"
        doc["operators"][0]["status"] = "ratified"
        view = self.view(doc)
        report = view.inspect()
        self.assertEqual(report["declared_set_status"], "ratified")
        self.assertEqual(report["admission"], "not assessed")
        self.assertEqual(report["construction_permission"], "not granted")
        self.assertEqual(report["execution_permission"], "not granted")
        for operation in ("recommend", "apply", "generate", "ratify", "promote", "basex", "execute"):
            with self.subTest(operation=operation), self.assertRaises(UnsupportedCapability):
                view.request(operation)

    def test_historical_adaptation_and_source_status_are_separate(self):
        view = self.historic()
        result = view.lookup("P1")
        self.assertEqual(result["reasoning"]["definition"], "Description kept separate from adaptation.")
        self.assertEqual(result["reasoning"]["domain_adaptation"], "Adaptation fixture.")
        self.assertIsNone(result["declared_operator_status"])
        self.assertEqual(view.inspect()["declared_set_status"], "candidate")
        self.assertIn("examples", result["not_projected_fields"])
        self.assertEqual(view.identity.namespace, "domain120.parser-fixture")
        self.assertEqual(view.identity.version, "0.1.0")
        self.assertEqual(result["source_pointer"], "/transformations/P/0")

    def test_historical_identity_and_base_version_mismatches_fail(self):
        mutations = [
            ("domain", "other"), ("family", "Base120"),
            ("set_id", "domain120.parser-fixture.v0.2"),
            ("base_architecture", "base120.v9.9.9"),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                doc = historical_document()
                doc[key] = value
                with self.assertRaises(InspectionError):
                    self.historic(doc)
        raw = encode(historical_document())
        with self.assertRaisesRegex(InspectionError, "conflicts"):
            CatalogView(raw, local_pin(raw), self.base, profile="transformations-2026-06-draft",
                        namespace="domain120.other")

    def test_missing_or_ambiguous_profile_identity_fails(self):
        raw = encode(lattice_document())
        for profile, namespace in (("unknown", "domain120.test"),
                                   ("lattice-object-v0", None),
                                   ("lattice-object-v0", "Base120")):
            with self.subTest(profile=profile, namespace=namespace), self.assertRaises(InspectionError):
                CatalogView(raw, local_pin(raw), self.base, profile=profile, namespace=namespace)
        doc = lattice_document()
        doc["transformations"] = {}
        with self.assertRaisesRegex(InspectionError, "mixed"):
            self.view(doc)

    def test_malformed_operator_fields_and_unknown_ancestors_fail(self):
        for key, value in (("code", ""), ("code", " P01"), ("code", []),
                           ("family", "ZZ"), ("family", []), ("name", None),
                           ("definition", ""), ("base120_ancestor", "P999")):
            with self.subTest(key=key, value=value):
                doc = lattice_document()
                doc["operators"][0][key] = value
                with self.assertRaises(InspectionError):
                    self.view(doc)
        doc = lattice_document()
        doc["operators"].append(dict(doc["operators"][0]))
        with self.assertRaisesRegex(InspectionError, "Duplicate local"):
            self.view(doc)

    def test_malformed_known_relation_shapes_fail_without_interpreting_targets(self):
        cases = [
            ("composition_matrix", []), ("composition_matrix", {"P": []}),
            ("composition_matrix", {"ZZ": {}}), ("composition_matrix", {"P": {"IN": "yes"}}),
            ("cross_maps", {}), ("cross_maps", [None]),
            ("cross_maps", [{"to": "Other", "operator": "MISSING", "cousin": "P01"}]),
            ("cross_maps", [{"to": " Other", "operator": "P01", "cousin": "P01"}]),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                doc = lattice_document()
                doc[key] = value
                with self.assertRaises(InspectionError):
                    self.view(doc)
        doc = lattice_document()
        mapping = {"to": "Unresolved target", "operator": "P01", "cousin": "P99"}
        doc["cross_maps"] = [mapping]
        view = self.view(doc)
        self.assertIn("cross_maps", view.inspect()["projection"]["root_fields_not_in_common_view"])
        self.assertIn("not interpreted", view.inspect()["projection"]["relations"])
        doc["cross_maps"].append(dict(mapping))
        with self.assertRaisesRegex(InspectionError, "Duplicate cross-map"):
            self.view(doc)

    def test_malformed_historical_family_shapes_fail(self):
        for groups in ({}, [], {"P": []}):
            with self.subTest(groups=groups):
                doc = historical_document()
                doc["transformations"] = groups
                with self.assertRaises(InspectionError):
                    self.historic(doc)
        doc = historical_document()
        doc["transformations"]["P"] *= 21
        with self.assertRaisesRegex(InspectionError, "at most 20"):
            self.historic(doc)

    def test_registry_digest_shape_duplicates_and_field_conflicts_fail(self):
        with self.assertRaisesRegex(InspectionError, "digest"):
            Base120Index(BASE120_RAW + b" ", BASE_PIN, "1.0.0")
        cases = []
        original = json.loads(BASE120_RAW)
        cases.append(original[:-1])
        cases.append(original + [dict(original[0])])
        changed = json.loads(BASE120_RAW)
        changed[0]["transformation"] = "IN"
        cases.append(changed)
        for records in cases:
            raw = encode(records)
            with self.subTest(size=len(records)), self.assertRaises(InspectionError):
                Base120Index(raw, local_pin(raw), "1.0.0")
        for code in ("P999", None, []):
            with self.subTest(code=code), self.assertRaises(InspectionError):
                self.base.resolve(code)

    def test_strict_json_rejects_duplicate_keys_nonfinite_and_bad_encoding(self):
        cases = [b'{"domain":"a","domain":"b"}', b'{"x":NaN}', b'{"x":Infinity}',
                 b'{"x":1e999}', b"\xff", b"[]", b"null"]
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(InspectionError):
                self.view(raw=raw)
        with self.assertRaisesRegex(InspectionError, "immutable bytes"):
            CatalogView(bytearray(encode(lattice_document())), local_pin(b""),
                        self.base, profile="lattice-object-v0", namespace="domain120.test")

    def test_integer_limit_failure_is_normalized_without_changing_runtime_limit(self):
        if not hasattr(sys, "get_int_max_str_digits") or sys.get_int_max_str_digits() == 0:
            self.skipTest("Python integer string limit is disabled")
        digit_count = sys.get_int_max_str_digits() + 1
        raw = b'{"unknown_numeric_field":' + b"1" * digit_count + b"}"
        with self.assertRaises(InspectionError) as caught:
            self.view(raw=raw)
        self.assertIsInstance(caught.exception.__cause__, ValueError)
        self.assertEqual(sys.get_int_max_str_digits(), digit_count - 1)

    def test_multiline_description_is_preserved(self):
        doc = lattice_document()
        doc["operators"][0]["definition"] = "First line.\nSecond line.\tA tab."
        self.assertEqual(self.view(doc).lookup("P01")["reasoning"]["definition"],
                         doc["operators"][0]["definition"])

    def test_browse_and_request_have_explicit_arguments(self):
        view = self.view()
        self.assertEqual(len(view.request("browse")), 1)
        self.assertEqual(view.request("browse", family="IN"), [])
        self.assertEqual(view.request("lookup", local_code="P01"), view.lookup("P01"))
        for operation, args in (("inspect", {"execute": True}), ("lookup", {}),
                                ("browse", {"family": "ZZ"})):
            with self.subTest(operation=operation), self.assertRaises(InspectionError):
                view.request(operation, **args)

    def test_locator_metadata_is_not_authentication(self):
        raw = encode(lattice_document())
        pin = SourcePin("git", "candidate.json", hashlib.sha256(raw).hexdigest(),
                        "https://example.invalid/unverified", "a" * 40)
        report = CatalogView(raw, pin, self.base, profile="lattice-object-v0",
                             namespace="domain120.test").inspect()
        self.assertIn("caller-supplied", report["source"]["locator_authentication"])
        for path in ("../candidate.json", "/candidate.json", "a\\candidate.json"):
            with self.subTest(path=path), self.assertRaises(InspectionError):
                SourcePin("git", path, pin.sha256, pin.repository, pin.revision)

    def test_module_initialization_and_operations_use_no_external_io(self):
        # Load source and fixture bytes before installing traps. This checks the
        # module body and operations, not Python's own module-file discovery.
        source = Path(inspection.__file__).read_text(encoding="utf-8")
        code = compile(source, "inspection_probe.py", "exec")
        probe = types.ModuleType("inspection_probe")
        raw = encode(lattice_document())
        research_raw = encode(research_document())
        with patch.dict(sys.modules, {"inspection_probe": probe}), ExitStack() as guards:
            for target in ("builtins.open", "io.open", "os.open", "os.mkdir",
                           "socket.socket", "subprocess.Popen", "urllib.request.urlopen"):
                guards.enter_context(patch(target, side_effect=AssertionError("Unexpected I/O: " + target)))
            exec(code, probe.__dict__)
            base_pin = probe.SourcePin(**asdict(BASE_PIN))
            base = probe.Base120Index(BASE120_RAW, base_pin, "1.0.0")
            pin = probe.SourcePin(**asdict(local_pin(raw)))
            view = probe.CatalogView(raw, pin, base, profile="lattice-object-v0",
                                     namespace="domain120.parser-fixture")
            self.assertEqual(view.inspect()["operator_count"], 1)
            self.assertEqual(len(view.browse()), 1)
            self.assertEqual(view.lookup("P01")["family"], "P")
            collection = probe.CatalogCollection([view])
            self.assertEqual(collection.lookup(probe.OperatorIdentity(view.identity, "P01"))["family"], "P")
            self.assertEqual(collection.inspect(view.identity), view.inspect())
            self.assertEqual(collection.source_bytes(view.identity), raw)
            self.assertEqual(collection.source_document(view.identity), view.source_document())
            research_pin = probe.SourcePin(**asdict(local_pin(research_raw)))
            research = probe.CatalogView(research_raw, research_pin, base,
                                         profile="research-draft-2026-08",
                                         namespace="domain120.research-parser-fixture")
            collection = probe.CatalogCollection([view, research])
            self.assertIsNone(collection.inspect(research.identity)["identity"]["version"])
            self.assertEqual(collection.lookup(probe.OperatorIdentity(research.identity, "P01"))["family"], "P")
            self.assertEqual(len(research.browse()), 1)
            self.assertEqual(collection.source_bytes(research.identity), research_raw)


if __name__ == "__main__":
    unittest.main()
