"""Optional page-local context references preserve the existing inspection data."""
import io
import json
import unittest
from dataclasses import asdict
from unittest.mock import patch

from basen import domain120_catalogs as catalogs
from basen import mcp_server as server
from basen.domain120_inspection import Base120Index, CatalogView
from tests.test_domain120_inspection import (
    BASE120_RAW,
    BASE_PIN,
    encode,
    historical_document,
    lattice_document,
    local_pin,
    research_document,
)


class SharedContextTests(unittest.TestCase):
    def setUp(self):
        base = Base120Index(BASE120_RAW, BASE_PIN, "1.0.0")
        self.views = []
        for profile, builder in (("lattice-object-v0", lattice_document),
                                 ("transformations-2026-06-draft", historical_document),
                                 ("research-draft-2026-08", research_document)):
            doc = builder()
            doc.update(license="fixture-only", visibility="private-fixture")
            if "operators" in doc:
                doc["operators"].append(dict(doc["operators"][0], code="IN01", family="IN",
                                             base120_ancestor="IN1"))
            raw = encode(doc)
            self.views.append(CatalogView(raw, local_pin(raw), base, profile=profile,
                                          namespace=None if "transformations" in doc
                                          else "domain120." + profile))
        self.service = catalogs.CatalogService(self.views, "a" * 64)

    def wire(self, operation="browse", **arguments):
        with patch.object(server, "_DOMAIN120_SERVICE", self.service):
            result = server.handle_request("tools/call", {
                "name": catalogs.PREFIX + operation, "arguments": arguments})
        stream = io.StringIO()
        with patch.object(server.sys, "stdout", stream):
            server._write_response(server._success_obj(1, result))
        return stream.getvalue().encode("utf-8")

    def page(self, **arguments):
        return json.loads(json.loads(self.wire(**arguments))["result"]["content"][0]["text"])

    def test_default_and_explicit_per_operator_have_identical_wire_bytes(self):
        for view in self.views:
            for selection in ({}, {"limit": 1}, {"offset": 1, "limit": 1},
                              {"family": "P"}, {"family": "RE"}, {"offset": 100}):
                with self.subTest(profile=view.inspect()["profile"], selection=selection):
                    args = {"catalog": asdict(view.identity), **selection}
                    self.assertEqual(self.wire(**args), self.wire(**args, context_mode="per_operator"))
                    self.assertNotIn("context_mode", self.page(**args))

    def test_shared_references_preserve_all_context_and_operator_fields(self):
        for view in self.views:
            for selection in ({}, {"limit": 1}, {"offset": 1, "limit": 1},
                              {"family": "P"}, {"family": "RE"}, {"offset": 100}):
                with self.subTest(profile=view.inspect()["profile"], selection=selection):
                    args = {"catalog": asdict(view.identity), **selection}
                    default, shared = self.page(**args), self.page(**args, context_mode="shared")
                    self.assertEqual(shared.pop("context_mode"), "shared")
                    shared_rows, default_rows = shared.pop("operators"), default.pop("operators")
                    self.assertEqual(shared, default)
                    context = shared["catalog_context"]
                    self.assertEqual(context["source_distribution_declarations"],
                                     {"license": "fixture-only", "visibility": "private-fixture"})
                    self.assertEqual(len(shared_rows), len(default_rows))
                    for actual, expected in zip(shared_rows, default_rows, strict=True):
                        ref = actual.pop("catalog_context_ref")
                        self.assertEqual(ref, "/catalog_context")
                        self.assertIs(shared[ref[1:]], context)
                        self.assertEqual(actual["identity"]["catalog"], context["identity"])
                        old_context = expected.pop("catalog_context")
                        self.assertEqual({key: context[key] for key in old_context}, old_context)
                        self.assertEqual(actual, expected)

    def test_shared_page_constructs_context_once_without_per_record_full_parses(self):
        view = self.views[-1]
        with patch.object(self.service, "_context", wraps=self.service._context) as context, \
                patch.object(view, "inspect", wraps=view.inspect) as inspect, \
                patch.object(view, "source_document", wraps=view.source_document) as source, \
                patch.object(view, "lookup", wraps=view.lookup) as lookup:
            page = self.page(catalog=asdict(view.identity), context_mode="shared")
            self.assertEqual(len(page["operators"]), 2)
            self.assertEqual(context.call_count, 1)
            self.assertEqual(inspect.call_count, 1)
            # Context inspection plus source distribution declarations. Per-record
            # and ancestor JSON decoding still occurs and is necessary.
            self.assertEqual(source.call_count, 2)
            self.assertEqual(lookup.call_count, 2)
            self.assertTrue(all(call.kwargs == {"include_catalog_context": False}
                                for call in lookup.call_args_list))

    def test_invalid_modes_and_other_read_tools_reject_mode(self):
        identity = asdict(self.views[0].identity)
        for mode in (None, False, True, 0, 1, "", "SHARED", "other", [], {}, ["shared"]):
            with self.subTest(mode=mode), self.assertRaises(server.JsonRpcError) as caught:
                self.wire(catalog=identity, context_mode=mode)
            self.assertEqual(caught.exception.code, server.INVALID_PARAMS)
        for operation in ("catalogs", "inspect", "lookup", "relations", "source"):
            args = {} if operation == "catalogs" else {"catalog": identity}
            if operation == "lookup":
                args["local_code"] = "P01"
            with self.subTest(operation=operation), self.assertRaises(server.JsonRpcError) as caught:
                self.wire(operation, **args, context_mode="shared")
            self.assertEqual(caught.exception.code, server.INVALID_PARAMS)

    def test_standalone_lookup_stays_self_contained_and_source_is_unchanged(self):
        for view in self.views:
            raw = view.source_bytes()
            code = view.operator_codes()[0]
            expected = view.lookup(code)
            self.page(catalog=asdict(view.identity), context_mode="shared")
            self.assertEqual(view.lookup(code), expected)
            self.assertEqual(expected["catalog_context"], view.inspect())
            self.assertEqual(view.source_bytes(), raw)

    def test_discovery_offers_exact_opt_in_enum_only_on_browse(self):
        for tool in catalogs.tool_definitions():
            properties = tool["inputSchema"]["properties"]
            if tool["name"] == catalogs.PREFIX + "browse":
                self.assertEqual(properties["context_mode"], {
                    "type": "string", "enum": ["per_operator", "shared"], "default": "per_operator"})
                self.assertNotIn("context_mode", tool["inputSchema"]["required"])
            else:
                self.assertNotIn("context_mode", properties)
