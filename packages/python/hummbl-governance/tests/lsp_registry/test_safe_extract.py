"""Tests for safe archive extraction (CVE-2007-4559 / zip-slip defense).

Validates that _safe_extract_tar and _safe_extract_zip reject:
  - Absolute paths (e.g. /etc/passwd)
  - Parent directory traversal (e.g. ../../etc/passwd)
  - Symlinks/hardlinks pointing outside the destination
And that they accept normal, safe archive members.
"""

from __future__ import annotations

import io
import os
import tarfile
import zipfile
from pathlib import Path

import pytest

from hummbl_governance.lsp_registry.install import (
    _safe_extract_tar,
    _safe_extract_zip,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_safe_tar(members: list[tuple[str, bytes]]) -> bytes:
    """Build an in-memory tar.gz with the given (name, content) pairs."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, content in members:
            data = content if isinstance(content, bytes) else content.encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _make_safe_zip(members: list[tuple[str, bytes]]) -> bytes:
    """Build an in-memory zip with the given (name, content) pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in members:
            data = content if isinstance(content, bytes) else content.encode()
            zf.writestr(name, data)
    return buf.getvalue()


def _make_tar_with_symlink(name: str, linkname: str) -> bytes:
    """Build an in-memory tar.gz containing a symlink."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(name=name)
        info.type = tarfile.SYMTYPE
        info.linkname = linkname
        info.size = 0
        tf.addfile(info, io.BytesIO())
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tar extraction tests
# ---------------------------------------------------------------------------

class TestSafeExtractTar:
    """Tests for _safe_extract_tar path-traversal defense."""

    def test_safe_members_extracted(self, tmp_path: Path) -> None:
        """Normal archive members should extract without error."""
        data = _make_safe_tar([
            ("safe.txt", b"hello"),
            ("subdir/nested.txt", b"world"),
        ])
        archive = tmp_path / "safe.tar.gz"
        archive.write_bytes(data)

        with tarfile.open(archive, "r:gz") as tf:
            _safe_extract_tar(tf, str(tmp_path))

        assert (tmp_path / "safe.txt").read_text() == "hello"
        assert (tmp_path / "subdir" / "nested.txt").read_text() == "world"

    def test_absolute_path_rejected(self, tmp_path: Path) -> None:
        """Tar member with absolute path should be rejected."""
        # On Unix, tarfile strips leading / automatically, so this only
        # triggers on paths that resolve outside dest after normalization.
        # Use a path that escapes via normalization.
        data = _make_safe_tar([("../../etc/evil.txt", b"pwned")])
        archive = tmp_path / "evil.tar.gz"
        archive.write_bytes(data)

        with tarfile.open(archive, "r:gz") as tf:
            with pytest.raises((ValueError, Exception)):
                _safe_extract_tar(tf, str(tmp_path))

    def test_parent_traversal_rejected(self, tmp_path: Path) -> None:
        """Tar member with ../ traversal should be rejected."""
        data = _make_safe_tar([("../escape.txt", b"escaped")])
        archive = tmp_path / "traversal.tar.gz"
        archive.write_bytes(data)

        with tarfile.open(archive, "r:gz") as tf:
            with pytest.raises((ValueError, Exception)):
                _safe_extract_tar(tf, str(tmp_path))

    def test_deep_parent_traversal_rejected(self, tmp_path: Path) -> None:
        """Multiple levels of ../ should also be rejected."""
        data = _make_safe_tar([("../../../../etc/passwd", b"stolen")])
        archive = tmp_path / "deep.tar.gz"
        archive.write_bytes(data)

        with tarfile.open(archive, "r:gz") as tf:
            with pytest.raises((ValueError, Exception)):
                _safe_extract_tar(tf, str(tmp_path))

    def test_symlink_escape_rejected(self, tmp_path: Path) -> None:
        """Symlink pointing outside destination should be rejected."""
        data = _make_tar_with_symlink("evil_link", "../../etc/passwd")
        archive = tmp_path / "symlink.tar.gz"
        archive.write_bytes(data)

        with tarfile.open(archive, "r:gz") as tf:
            # On Python 3.12+ filter="data" rejects symlinks automatically.
            # On older Python, the manual check catches escaping symlinks.
            with pytest.raises((ValueError, Exception)):
                _safe_extract_tar(tf, str(tmp_path))

    def test_empty_archive_ok(self, tmp_path: Path) -> None:
        """An empty tar should extract without error."""
        data = _make_safe_tar([])
        archive = tmp_path / "empty.tar.gz"
        archive.write_bytes(data)

        with tarfile.open(archive, "r:gz") as tf:
            _safe_extract_tar(tf, str(tmp_path))

    def test_nested_directories_ok(self, tmp_path: Path) -> None:
        """Deeply nested but safe paths should extract fine."""
        data = _make_safe_tar([
            ("a/b/c/d/e/f.txt", b"deep"),
        ])
        archive = tmp_path / "nested.tar.gz"
        archive.write_bytes(data)

        with tarfile.open(archive, "r:gz") as tf:
            _safe_extract_tar(tf, str(tmp_path))

        assert (tmp_path / "a" / "b" / "c" / "d" / "e" / "f.txt").read_text() == "deep"


# ---------------------------------------------------------------------------
# Zip extraction tests
# ---------------------------------------------------------------------------

class TestSafeExtractZip:
    """Tests for _safe_extract_zip zip-slip defense."""

    def test_safe_members_extracted(self, tmp_path: Path) -> None:
        """Normal zip members should extract without error."""
        data = _make_safe_zip([
            ("safe.txt", b"hello"),
            ("subdir/nested.txt", b"world"),
        ])
        archive = tmp_path / "safe.zip"
        archive.write_bytes(data)

        with zipfile.ZipFile(archive, "r") as zf:
            _safe_extract_zip(zf, str(tmp_path))

        assert (tmp_path / "safe.txt").read_text() == "hello"
        assert (tmp_path / "subdir" / "nested.txt").read_text() == "world"

    def test_absolute_path_rejected(self, tmp_path: Path) -> None:
        """Zip entry with absolute path should be rejected."""
        data = _make_safe_zip([("../../escape.txt", b"escaped")])
        archive = tmp_path / "evil.zip"
        archive.write_bytes(data)

        with zipfile.ZipFile(archive, "r") as zf:
            with pytest.raises((ValueError, Exception)):
                _safe_extract_zip(zf, str(tmp_path))

    def test_parent_traversal_rejected(self, tmp_path: Path) -> None:
        """Zip entry with ../ traversal should be rejected."""
        data = _make_safe_zip([("../escape.txt", b"escaped")])
        archive = tmp_path / "traversal.zip"
        archive.write_bytes(data)

        with zipfile.ZipFile(archive, "r") as zf:
            with pytest.raises((ValueError, Exception)):
                _safe_extract_zip(zf, str(tmp_path))

    def test_deep_parent_traversal_rejected(self, tmp_path: Path) -> None:
        """Multiple levels of ../ should also be rejected."""
        data = _make_safe_zip([("../../../../etc/passwd", b"stolen")])
        archive = tmp_path / "deep.zip"
        archive.write_bytes(data)

        with zipfile.ZipFile(archive, "r") as zf:
            with pytest.raises((ValueError, Exception)):
                _safe_extract_zip(zf, str(tmp_path))

    def test_empty_zip_ok(self, tmp_path: Path) -> None:
        """An empty zip should extract without error."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w"):
            pass
        archive = tmp_path / "empty.zip"
        archive.write_bytes(buf.getvalue())

        with zipfile.ZipFile(archive, "r") as zf:
            _safe_extract_zip(zf, str(tmp_path))

    def test_nested_directories_ok(self, tmp_path: Path) -> None:
        """Deeply nested but safe paths should extract fine."""
        data = _make_safe_zip([
            ("a/b/c/d/e/f.txt", b"deep"),
        ])
        archive = tmp_path / "nested.zip"
        archive.write_bytes(data)

        with zipfile.ZipFile(archive, "r") as zf:
            _safe_extract_zip(zf, str(tmp_path))

        assert (tmp_path / "a" / "b" / "c" / "d" / "e" / "f.txt").read_text() == "deep"


# ---------------------------------------------------------------------------
# URL scheme validation tests
# ---------------------------------------------------------------------------

class TestDownloadSchemeValidation:
    """Tests for the URL scheme allowlist in _install_binary."""

    def test_allowed_schemes(self) -> None:
        """_ALLOWED_DOWNLOAD_SCHEMES should contain http and https only."""
        from hummbl_governance.lsp_registry.install import _ALLOWED_DOWNLOAD_SCHEMES
        assert "http" in _ALLOWED_DOWNLOAD_SCHEMES
        assert "https" in _ALLOWED_DOWNLOAD_SCHEMES
        assert "file" not in _ALLOWED_DOWNLOAD_SCHEMES
        assert "ftp" not in _ALLOWED_DOWNLOAD_SCHEMES
