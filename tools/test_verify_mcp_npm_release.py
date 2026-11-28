import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from verify_mcp_npm_release import PACKAGE, REPOSITORY_URL, verify_package, verify_release


class ReleaseHandoffTests(unittest.TestCase):
    def setUp(self):
        self.actor = "release-fixture[bot]"
        self.receipt = {"version": "1.2.4-beta.1", "source_commit": "1" * 40, "npm_sha256": "a" * 64}
        self.release = {
            "tag_name": "mcp-server/v1.2.4-beta.1", "author": {"login": self.actor},
            "draft": False, "prerelease": True, "body": json.dumps(self.receipt),
            "assets": [{"name": "npm.tgz", "id": 42, "state": "uploaded", "digest": "sha256:" + "a" * 64}],
        }

    def test_receipt_binds_actor_tag_asset_and_channel(self):
        result = verify_release(self.release, self.actor)
        self.assertEqual((result["asset_id"], result["dist_tag"]), (42, "beta"))
        for change in (
            {"tag_name": "v1.2.4"}, {"draft": True}, {"prerelease": False}, {"assets": []},
            {"author": {"login": "other"}}, {"body": json.dumps({**self.receipt, "npm_sha256": "b" * 64})},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify_release({**self.release, **change}, self.actor)

    def test_archive_identity_and_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "npm.tgz"
            manifest = {"name": PACKAGE, "version": "1.2.4", "repository": {"url": REPOSITORY_URL}}
            with tarfile.open(path, "w:gz") as archive:
                for name, raw in (("package/package.json", json.dumps(manifest).encode()), ("package/dist/index.js", b"")):
                    entry = tarfile.TarInfo(name)
                    entry.size = len(raw)
                    archive.addfile(entry, io.BytesIO(raw))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            verify_package(path, digest, "1.2.4")
            for expected, version in ((digest, "1.2.5"), ("0" * 64, "1.2.4")):
                with self.assertRaises(ValueError):
                    verify_package(path, expected, version)


if __name__ == "__main__":
    unittest.main()
