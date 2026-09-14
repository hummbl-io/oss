"""Tests for the rights/distribution invariant check."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_rights_distribution as checker


class RightsDistributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return name

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def init_repo(self):
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    def add_and_commit(self, *names):
        for name in names:
            self.git("add", name)
        self.git("commit", "-q", "-m", "test")

    def manifest(self, content_id, policy, authority_path=None):
        m = {
            "$schema": "https://raw.githubusercontent.com/hummbl-io/oss/main/schemas/public/product-admission-v1.schema.json",
            "schema_version": "hummbl.product.v1",
            "product_id": "test-product",
            "display_name": "Test Product",
            "distribution": "@test/product",
            "lifecycle": "technical-canary",
            "public_launch": False,
            "admission": {"decision": "hold", "blockers": ["test-blocker"]},
            "canonical_source": {"repository": "hummbl-io/oss", "path": "packages/test"},
            "content_authorities": [],
            "rights": {
                "package_license": "UNLICENSED",
                "software_license": "Apache-2.0",
                "embedded_content": [
                    {
                        "content_id": content_id,
                        "license": "Proprietary",
                        "distribution_policy": policy,
                    }
                ],
            },
            "contract": {
                "version": "test.v1",
                "protocol_versions": ["2026-01-01"],
                "tools": ["test_tool"],
                "mutations": False,
            },
            "local_mode": {"network_egress": False, "telemetry": False, "durable_writes": False},
            "excluded": ["test-exclusion"],
        }
        if authority_path:
            m["content_authorities"] = [
                {"content_id": content_id, "repository": "hummbl-io/oss", "path": authority_path}
            ]
        return m

    # --- Manifest contradiction tests ---

    def test_restrictive_policy_with_content_in_tree_fails(self):
        self.init_repo()
        self.write("packages/test/data/operators.json", '{"test": true}')
        self.write(
            "packages/test/product.json",
            json.dumps(self.manifest("test-corpus", "no-new-public-redistribution",
                                     "packages/test/data/operators.json")),
        )
        self.add_and_commit("packages/test/data/operators.json", "packages/test/product.json")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 1)
        self.assertTrue(any("rights-contradiction" in r for _, r in result.findings))

    def test_private_only_policy_with_content_in_tree_fails(self):
        self.init_repo()
        self.write("packages/test/data/secret.yaml", "key: value")
        self.write(
            "packages/test/product.json",
            json.dumps(self.manifest("test-corpus", "private-only",
                                     "packages/test/data/secret.yaml")),
        )
        self.add_and_commit("packages/test/data/secret.yaml", "packages/test/product.json")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 1)

    def test_restrictive_policy_without_content_in_tree_passes(self):
        self.init_repo()
        self.write(
            "packages/test/product.json",
            json.dumps(self.manifest("test-corpus", "no-new-public-redistribution",
                                     "packages/other/data/not-committed.json")),
        )
        self.add_and_commit("packages/test/product.json")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 0)

    def test_approved_policy_with_content_in_tree_passes(self):
        self.init_repo()
        self.write("packages/test/data/operators.json", '{"test": true}')
        m = self.manifest("test-corpus", "public-redistribution-approved",
                          "packages/test/data/operators.json")
        self.write("packages/test/product.json", json.dumps(m))
        self.add_and_commit("packages/test/data/operators.json", "packages/test/product.json")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 0)

    def test_restrictive_policy_without_authority_is_incomplete(self):
        self.init_repo()
        self.write(
            "packages/test/product.json",
            json.dumps(self.manifest("test-corpus", "no-new-public-redistribution")),
        )
        self.add_and_commit("packages/test/product.json")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 2)
        self.assertTrue(any("missing-content-authority" in r for _, r in result.incomplete))

    def test_non_product_schema_manifest_is_skipped(self):
        self.init_repo()
        self.write("packages/test/data/operators.json", '{"test": true}')
        m = self.manifest("test-corpus", "no-new-public-redistribution",
                          "packages/test/data/operators.json")
        m["schema_version"] = "something.else.v1"
        self.write("packages/test/product.json", json.dumps(m))
        self.add_and_commit("packages/test/data/operators.json", "packages/test/product.json")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 0)

    def test_malformed_manifest_is_incomplete(self):
        self.init_repo()
        self.write("packages/test/product.json", "{not valid json")
        self.add_and_commit("packages/test/product.json")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 2)
        self.assertTrue(any("manifest-parse-failed" in r for _, r in result.incomplete))

    # --- NOTICE trade-secret tests ---

    def test_notice_with_trade_secret_for_tracked_file_fails(self):
        self.init_repo()
        self.write("packages/test/data/operators.json", '{"test": true}')
        self.write(
            "packages/test/NOTICE",
            "The file packages/test/data/operators.json is a trade secret.\n"
            "A separate commercial license is required.\n",
        )
        self.add_and_commit("packages/test/data/operators.json", "packages/test/NOTICE")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 1)
        self.assertTrue(any("trade-secret-claim" in r for _, r in result.findings))

    def test_notice_without_trade_secret_passes(self):
        self.init_repo()
        self.write("packages/test/data/operators.json", '{"test": true}')
        self.write(
            "packages/test/NOTICE",
            "Those files are published. They are not a trade secret.\n"
            "Licensed under Apache-2.0.\n",
        )
        self.add_and_commit("packages/test/data/operators.json", "packages/test/NOTICE")
        # "not a trade secret" contains "trade secret" but the context is
        # a negation. This test verifies the current heuristic flags it —
        # the check is conservative (fail-closed) on any trade-secret mention
        # near tracked files. The operator can adjust if false positives arise.
        result = checker.scan(self.root)
        # The NOTICE mentions operators.json? No — it says "Those files"
        # without naming a tracked path. So no tracked file is referenced.
        self.assertEqual(result.exit_code, 0)

    def test_notice_with_trade_secret_no_tracked_file_references_passes(self):
        self.init_repo()
        self.write(
            "packages/test/NOTICE",
            "Some unrelated material is a trade secret.\n"
            "No file paths mentioned here.\n",
        )
        self.add_and_commit("packages/test/NOTICE")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 0)

    # --- Edge cases ---

    def test_no_manifests_or_notices_is_clean(self):
        self.init_repo()
        self.write("README.md", "public content")
        self.add_and_commit("README.md")
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 0)

    def test_empty_repo_is_incomplete(self):
        self.init_repo()
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 2)

    def test_non_git_repo_is_incomplete(self):
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 2)

    def test_multiple_manifests_checked_independently(self):
        self.init_repo()
        # First manifest: contradiction
        self.write("packages/a/data/corpus.json", '{"a": true}')
        self.write(
            "packages/a/product.json",
            json.dumps(self.manifest("corpus-a", "no-new-public-redistribution",
                                     "packages/a/data/corpus.json")),
        )
        # Second manifest: clean
        self.write(
            "packages/b/product.json",
            json.dumps(self.manifest("corpus-b", "public-redistribution-approved",
                                     "packages/b/data/corpus.json")),
        )
        self.add_and_commit(
            "packages/a/data/corpus.json", "packages/a/product.json", "packages/b/product.json"
        )
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(len([r for _, r in result.findings if "rights-contradiction" in r]), 1)
        # The contradiction should be in packages/a/product.json, not b
        self.assertTrue(any("packages/a/product.json" in n for n, r in result.findings))


if __name__ == "__main__":
    unittest.main()
