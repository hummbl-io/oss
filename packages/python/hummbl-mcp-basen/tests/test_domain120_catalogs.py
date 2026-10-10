"""Snapshot loading and actual BaseN dispatch boundaries, using parser fixtures."""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import asdict
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from basen import domain120_catalogs as catalogs
from basen import mcp_server as server
from basen.domain120_inspection import InspectionError
from tests.test_domain120_inspection import (
    BASE120_RAW, BUNDLED, encode, historical_document, lattice_document, research_document,
)

PACKAGE = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="domain120-inspection-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.manifest = self.root / "inspection.json"
        self.config = {
            "schema": catalogs.SCHEMA,
            "base120": {**self.input("comparison.json", BASE120_RAW), "registry_version": "1.0.0"},
            "catalogs": [
                {**self.input("a.json", encode(lattice_document())),
                 "profile": "lattice-object-v0", "namespace": "domain120.first"},
                {**self.input("b.json", encode(research_document())),
                 "profile": "research-draft-2026-08", "namespace": "domain120.second"},
                {**self.input("c.json", encode(historical_document())),
                 "profile": "transformations-2026-06-draft"},
            ],
        }

    def input(self, name, raw):
        (self.root / name).write_bytes(raw)
        return {"local_path": name,
                "source": {"kind": "local-file", "path": "synthetic-" + name, "sha256": digest(raw)}}

    def save(self):
        raw = encode(self.config)
        self.manifest.write_bytes(raw)
        return digest(raw)

    def load(self):
        return catalogs.load_catalogs(self.manifest, self.save())

    def call(self, service, operation, **args):
        with patch.object(server, "_DOMAIN120_SERVICE", service):
            result = server.handle_request("tools/call", {"name": catalogs.PREFIX + operation, "arguments": args})
        return json.loads(result["content"][0]["text"])

    def identity(self, service, index=0):
        return self.call(service, "catalogs")["catalogs"][index]["identity"]

    def run_stdio(self, requests, expected_sha, *, console=False):
        env = {key: value for key, value in os.environ.items() if not key.startswith("BASEN_")}
        env.update({"BASEN_DOMAIN120_MANIFEST": str(self.manifest),
                    "BASEN_DOMAIN120_MANIFEST_SHA256": expected_sha,
                    "PYTHONDONTWRITEBYTECODE": "1"})
        command = ([sys.executable, "-B", "-c", "from basen.mcp_server import main; main()"] if console
                   else [sys.executable, "-B", "-m", "basen.mcp_server"])
        wire = "".join(json.dumps(request) + "\n" for request in requests)
        return subprocess.run(command, cwd=PACKAGE, env=env, input=wire, text=True,
                              capture_output=True, timeout=15)

    def test_default_surface_and_base120_lookup_stay_separate(self):
        with patch.object(server, "_DOMAIN120_SERVICE", None), patch.object(server, "_REGISTRY_CACHE", {"base120": BUNDLED}):
            self.assertEqual([x["name"] for x in server.handle_request("tools/list", {})["tools"]],
                             [x.name for x in server.MCP_TOOLS])
            result = server.handle_request("tools/call", {"name": "basen_operator_lookup", "arguments": {"operator_id": "P1"}})
            self.assertEqual(json.loads(result["content"][0]["text"])["operator"]["id"], "P1")
            with self.assertRaises(server.JsonRpcError) as caught:
                server.handle_request("tools/call", {"name": "basen_domain120_catalogs", "arguments": {}})
            self.assertEqual(caught.exception.code, server.TOOL_NOT_FOUND)
            with self.assertRaises(server.JsonRpcError):
                server.handle_request("tools/call", {"name": "basen_operator_lookup", "arguments": {"operator_id": "P01", "variant": "domain120.first"}})

    def test_explicit_snapshot_exposes_three_profiles_and_qualified_identity(self):
        service = self.load()
        result = self.call(service, "catalogs")
        self.assertEqual(result["catalog_count"], 3)
        self.assertEqual([x["operator_count"] for x in result["catalogs"]], [1, 1, 1])
        first, second = self.identity(service), self.identity(service, 1)
        self.assertIsNone(second["version"])
        self.assertNotEqual(self.call(service, "lookup", catalog=first, local_code="P01")["operator"]["identity"],
                            self.call(service, "lookup", catalog=second, local_code="P01")["operator"]["identity"])
        with patch.object(server, "_DOMAIN120_SERVICE", service):
            names = [x["name"] for x in server.handle_request("tools/list", {})["tools"]]
        self.assertEqual(names, [x.name for x in server.MCP_TOOLS] + [catalogs.PREFIX + x for x in catalogs.OPERATIONS])

    def test_retained_source_relations_and_distribution_remain_uninterpreted(self):
        doc = lattice_document()
        doc.update({"license": "fixture-only", "visibility": "private-fixture",
                    "unfamiliar_relation": {"text": "retained without inferred semantics"}})
        self.config["catalogs"][0].update(self.input("a.json", encode(doc)))
        service = self.load()
        identity = self.identity(service)
        result = self.call(service, "relations", catalog=identity)
        pointers = {x["source_pointer"]: x["declaration"] for x in result["declarations"]}
        self.assertEqual(pointers["/composition_matrix"], doc["composition_matrix"])
        self.assertEqual(pointers["/operators/0/base120_ancestor"], "P1")
        self.assertFalse(result["projection_scope"]["complete_relation_ontology"])
        context = result["catalog_context"]
        self.assertEqual(context["source_distribution_declarations"], {"license": "fixture-only", "visibility": "private-fixture"})
        self.assertEqual(context["distribution_permission"], "not assessed")
        self.assertEqual(self.call(service, "source", catalog=identity)["source_document"], doc)
        result["declarations"][0]["declaration"] = "mutated copy"
        self.assertEqual(self.call(service, "source", catalog=identity)["source_document"], doc)
        june = self.call(service, "relations", catalog=self.identity(service, 2))
        self.assertEqual(june["declarations"][0]["source_pointer"], "/transformations/P/0/base120_source")

    def test_family_pagination_keeps_catalog_context_and_stable_count(self):
        doc = lattice_document()
        second = dict(doc["operators"][0], code="IN01", family="IN", base120_ancestor="IN1")
        doc["operators"].append(second)
        self.config["catalogs"][0].update(self.input("a.json", encode(doc)))
        service = self.load()
        identity = self.identity(service)
        first = self.call(service, "browse", catalog=identity, limit=1)
        following = self.call(service, "browse", catalog=identity, offset=first["next_offset"], limit=1)
        self.assertEqual(first["matching_count"], 2)
        self.assertEqual(following["operators"][0]["family"], "IN")
        self.assertIsNone(following["next_offset"])
        filtered = self.call(service, "browse", catalog=identity, family="P")
        self.assertEqual(filtered["matching_count"], 1)
        self.assertEqual(filtered["catalog_context"]["identity"], identity)

    def test_new_calls_reject_falsey_malformed_arguments_before_legacy_coercion(self):
        service = self.load()
        with patch.object(server, "_DOMAIN120_SERVICE", service):
            for value in ([], False, 0, None, ""):
                with self.subTest(value=value), self.assertRaises(server.JsonRpcError) as caught:
                    server.handle_request("tools/call", {"name": "basen_domain120_catalogs", "arguments": value})
                self.assertEqual(caught.exception.code, server.INVALID_PARAMS)
            self.assertFalse(server.handle_request("tools/call", {"name": "basen_domain120_catalogs"})["isError"])

    def test_page_projects_only_requested_records_and_relations_need_no_lookups(self):
        doc = lattice_document()
        fixture = doc["operators"][0]
        # Repeated parser records measure projection work, not useful operators.
        doc["operators"] = [dict(fixture, code=f"T{index}") for index in range(120)]
        self.config["catalogs"][0].update(self.input("a.json", encode(doc)))
        service = self.load()
        identity = self.identity(service)
        view = service._views[catalogs._identity(identity)]
        with patch.object(view, "lookup", wraps=view.lookup) as projection:
            page = self.call(service, "browse", catalog=identity, offset=119, limit=1)
            self.assertEqual([row["identity"]["local_code"] for row in page["operators"]], ["T119"])
            self.assertEqual(projection.call_count, 1)
            projection.reset_mock()
            self.assertEqual(self.call(service, "browse", catalog=identity, offset=500, limit=1)["operators"], [])
            self.assertEqual(projection.call_count, 0)
            relations = self.call(service, "relations", catalog=identity)
            self.assertEqual(len(relations["declarations"]), 122)
            self.assertEqual(projection.call_count, 0)

    def test_missing_unqualified_wrong_digest_and_extra_fields_fail(self):
        service = self.load()
        identity = self.identity(service)
        bad = [None, "domain120.first", {}, {**identity, "artifact_sha256": "f" * 64},
               {key: value for key, value in identity.items() if key != "version"},
               {**identity, "path": "should-not-be-read"}]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(server.JsonRpcError):
                self.call(service, "lookup", catalog=value, local_code="P01")
        for args in ({"limit": True}, {"offset": False}, {"limit": 0}, {"limit": 51},
                     {"offset": -1}, {"family": None}, {"family": []}, {"execute": True}):
            with self.subTest(args=args), self.assertRaises(server.JsonRpcError):
                self.call(service, "browse", catalog=identity, **args)

    def test_declared_ratification_cannot_enable_actions(self):
        doc = lattice_document()
        doc["status"] = "ratified"
        self.config["catalogs"][0].update(self.input("a.json", encode(doc)))
        service = self.load()
        result = self.call(service, "inspect", catalog=self.identity(service))
        self.assertEqual(result["catalog_context"]["declared_set_status"], "ratified")
        self.assertEqual(result["admission"], "not assessed")
        self.assertEqual(result["construction_permission"], "not granted")
        self.assertEqual(result["execution_permission"], "not granted")
        for action in ("apply", "recommend", "generate", "promote", "close", "publish"):
            with self.subTest(action=action), self.assertRaises(server.JsonRpcError) as caught:
                self.call(service, action, catalog=self.identity(service))
            self.assertEqual(caught.exception.code, server.TOOL_NOT_FOUND)

    def test_loaded_snapshot_survives_file_change_without_silent_reload(self):
        service = self.load()
        identity = self.identity(service)
        (self.root / "a.json").write_text("changed file", encoding="utf-8")
        self.assertEqual(self.call(service, "source", catalog=identity)["source_document"], lattice_document())
        with self.assertRaises(InspectionError):
            catalogs.load_catalogs(self.manifest, digest(self.manifest.read_bytes()))

    def test_manifest_digest_and_source_digest_checked_independently(self):
        correct = self.save()
        with self.assertRaises(InspectionError):
            catalogs.load_catalogs(self.manifest, "0" * 64)
        self.config["catalogs"][0]["source"]["sha256"] = "f" * 64
        with self.assertRaises(InspectionError):
            self.load()
        self.assertNotEqual(correct, digest(self.manifest.read_bytes()))

    def test_unmapped_basen_registry_shape_is_rejected(self):
        self.config["base120"].update(self.input("comparison.json", encode(BUNDLED)))
        with self.assertRaises(InspectionError):
            self.load()

    def test_duplicate_and_conflicting_catalog_identity_fail(self):
        self.config["catalogs"].append(dict(self.config["catalogs"][0]))
        with self.assertRaises(InspectionError):
            self.load()
        new = lattice_document()
        new["domain"] = "changed content at same version"
        self.config["catalogs"][-1].update(self.input("conflict.json", encode(new)))
        with self.assertRaises(InspectionError):
            self.load()

    def test_relative_path_escape_and_ambiguous_paths_rejected(self):
        for path in ("../a.json", "/a.json", "a/../a.json", "a//b.json", "./a.json",
                     "C:/a.json", "a\\b.json", "a.json:alternate", "a.json/"):
            with self.subTest(path=path):
                self.config["catalogs"][0]["local_path"] = path
                with self.assertRaises(InspectionError):
                    self.load()

    def test_resolved_link_cannot_escape_directory(self):
        with tempfile.TemporaryDirectory(prefix="domain120-outside-test-") as directory:
            outside = Path(directory).resolve() / "outside.json"
            outside.write_bytes(encode(lattice_document()))
            link = self.root / "link.json"
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest("Platform does not permit unprivileged symlink creation: " + type(exc).__name__)
            self.config["catalogs"][0]["local_path"] = link.name
            with self.assertRaisesRegex(InspectionError, "escapes"):
                self.load()

    def test_manifest_shape_strict_json_and_input_limits(self):
        self.config["unknown"] = True
        with self.assertRaises(InspectionError):
            self.load()
        del self.config["unknown"]
        raw = b'{"schema":"x","schema":"y"}'
        self.manifest.write_bytes(raw)
        with self.assertRaises(InspectionError):
            catalogs.load_catalogs(self.manifest, digest(raw))
        self.save()
        with patch.object(catalogs, "MAX_MANIFEST_BYTES", 1), self.assertRaises(InspectionError):
            catalogs.load_catalogs(self.manifest, digest(self.manifest.read_bytes()))
        with patch.object(catalogs, "MAX_ARTIFACT_BYTES", 1), self.assertRaises(InspectionError):
            self.load()
        with patch.object(catalogs, "MAX_TOTAL_BYTES", len(BASE120_RAW)), self.assertRaises(InspectionError):
            self.load()

    def test_startup_atomicity_and_partial_environment_fail_closed(self):
        service = self.load()
        self.config["catalogs"][1]["source"]["sha256"] = "0" * 64
        sha = self.save()
        with patch.object(server, "_DOMAIN120_SERVICE", service), patch.dict(os.environ, {
            "BASEN_DOMAIN120_MANIFEST": str(self.manifest), "BASEN_DOMAIN120_MANIFEST_SHA256": sha,
        }, clear=True):
            with self.assertRaises(InspectionError):
                server._configure_domain120()
            self.assertIsNone(server._DOMAIN120_SERVICE)
            self.assertEqual(len(server.handle_request("tools/list", {})["tools"]), 4)
        for env in ({"BASEN_DOMAIN120_MANIFEST": str(self.manifest)},
                    {"BASEN_DOMAIN120_MANIFEST_SHA256": sha}):
            with patch.dict(os.environ, env, clear=True), self.assertRaises(InspectionError):
                server._configure_domain120()

    def test_new_request_errors_do_not_expose_exception_or_source_content(self):
        service = self.load()
        marker = "PRIVATE_SOURCE_AND_PATH_MARKER"
        for error in (InspectionError(marker), RuntimeError(marker)):
            with patch.object(service, "call", side_effect=error), patch.object(server, "_DOMAIN120_SERVICE", service):
                with self.assertRaises(server.JsonRpcError) as caught:
                    server.handle_request("tools/call", {"name": "basen_domain120_catalogs", "arguments": {}})
                self.assertNotIn(marker, json.dumps(caught.exception.to_dict()))
        with patch.object(service, "call", return_value=object()), patch.object(server, "_DOMAIN120_SERVICE", service):
            with self.assertRaises(server.JsonRpcError) as caught:
                server.handle_request("tools/call", {"name": "basen_domain120_catalogs", "arguments": {}})
            self.assertEqual(caught.exception.message, "Domain120 inspection failed")

    def test_loading_uses_no_network_and_requests_use_no_external_io(self):
        sha = self.save()
        with ExitStack() as guards:
            for target in ("socket.socket", "urllib.request.urlopen", "subprocess.Popen"):
                guards.enter_context(patch(target, side_effect=AssertionError("Unexpected external activity")))
            service = catalogs.load_catalogs(self.manifest, sha)
        identity = self.identity(service)
        with ExitStack() as guards:
            for target in ("builtins.open", "io.open", "os.open", "os.mkdir", "socket.socket",
                           "urllib.request.urlopen", "subprocess.Popen"):
                guards.enter_context(patch(target, side_effect=AssertionError("Unexpected I/O")))
            for operation in catalogs.OPERATIONS:
                args = {} if operation == "catalogs" else {"catalog": identity}
                if operation == "lookup":
                    args["local_code"] = "P01"
                self.assertEqual(self.call(service, operation, **args)["admission"], "not assessed")

    def test_both_stdio_launch_paths_discover_and_lookup_then_reject_bad_arguments(self):
        service = self.load()
        identity = self.identity(service)
        sha = digest(self.manifest.read_bytes())
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "basen_domain120_lookup", "arguments": {"catalog": identity, "local_code": "P01"}}},
        ]
        for index, value in enumerate(([], False, 0, None, ""), 4):
            requests.append({"jsonrpc": "2.0", "id": index, "method": "tools/call",
                             "params": {"name": "basen_domain120_catalogs", "arguments": value}})
        for console in (False, True):
            with self.subTest(console_entry_function=console):
                run = self.run_stdio(requests, sha, console=console)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stderr, "")
                responses = [json.loads(line) for line in run.stdout.splitlines()]
                self.assertEqual(len(responses[1]["result"]["tools"]), 10)
                result = json.loads(responses[2]["result"]["content"][0]["text"])
                self.assertEqual(result["operator"]["identity"]["catalog"], identity)
                self.assertEqual(result["execution_permission"], "not granted")
                for response in responses[3:]:
                    self.assertEqual(response["error"]["code"], server.INVALID_PARAMS)

    def test_bad_configuration_exits_before_protocol_or_partial_tool_discovery(self):
        raw = b'{"PRIVATE_SOURCE_AND_PATH_MARKER": true}'
        self.manifest.write_bytes(raw)
        requests = [{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}]
        for console in (False, True):
            with self.subTest(console_entry_function=console):
                run = self.run_stdio(requests, digest(raw), console=console)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, "")
                self.assertEqual(run.stderr, "Domain120 inspection configuration rejected.\n")


if __name__ == "__main__":
    unittest.main()
