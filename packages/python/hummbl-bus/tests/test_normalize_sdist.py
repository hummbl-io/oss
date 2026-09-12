from __future__ import annotations

import gzip
import hashlib
import io
import subprocess
import sys
import tarfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = PROJECT_ROOT / "scripts" / "release" / "normalize_sdist.py"


def _write_sdist_fixture(path: Path, *, archive_mtime: int, member_mtime: int) -> None:
    entries = {
        "example-1.0": None,
        "example-1.0/PKG-INFO": b"Metadata-Version: 2.2\nName: example\nVersion: 1.0\n",
        "example-1.0/pyproject.toml": b"[build-system]\nrequires = []\n",
        "example-1.0/src/example.py": b"VALUE = 1\n",
    }

    with path.open("wb") as raw:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, mtime=archive_mtime
        ) as compressed:
            with tarfile.open(
                fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT
            ) as archive:
                for name, content in entries.items():
                    info = tarfile.TarInfo(name)
                    info.mtime = member_mtime
                    if content is None:
                        info.type = tarfile.DIRTYPE
                        info.mode = 0o755
                        archive.addfile(info)
                    else:
                        info.mode = 0o644
                        info.size = len(content)
                        archive.addfile(info, io.BytesIO(content))


def _normalize(source: Path, output: Path, *, epoch: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(NORMALIZER),
            str(source),
            str(output),
            "--epoch",
            str(epoch),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_normalized_sdists_are_byte_identical(tmp_path: Path) -> None:
    first_source = tmp_path / "first.tar.gz"
    second_source = tmp_path / "second.tar.gz"
    first_output = tmp_path / "first-normalized.tar.gz"
    second_output = tmp_path / "second-normalized.tar.gz"
    epoch = 1_700_000_000

    _write_sdist_fixture(first_source, archive_mtime=100, member_mtime=200)
    _write_sdist_fixture(second_source, archive_mtime=300, member_mtime=400)

    first = _normalize(first_source, first_output, epoch=epoch)
    second = _normalize(second_source, second_output, epoch=epoch)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert hashlib.sha256(first_output.read_bytes()).digest() == hashlib.sha256(
        second_output.read_bytes()
    ).digest()

    with tarfile.open(first_output, "r:gz") as archive:
        members = archive.getmembers()
        assert all(member.mtime == epoch for member in members)
        assert all(member.uid == 0 and member.gid == 0 for member in members)
        payload = archive.extractfile("example-1.0/src/example.py")
        assert payload is not None
        assert payload.read() == b"VALUE = 1\n"


def test_normalizer_rejects_unsafe_member_paths(tmp_path: Path) -> None:
    source = tmp_path / "unsafe.tar.gz"
    output = tmp_path / "normalized.tar.gz"

    with tarfile.open(source, "w:gz") as archive:
        info = tarfile.TarInfo("../escape")
        info.size = 1
        archive.addfile(info, io.BytesIO(b"x"))

    result = _normalize(source, output, epoch=1_700_000_000)

    assert result.returncode != 0
    assert "unsafe archive member" in result.stderr
    assert not output.exists()
