"""Rewrite a Python source distribution with deterministic archive metadata."""

from __future__ import annotations

import argparse
import copy
import gzip
import os
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


def _validated_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    roots: set[str] = set()
    names: set[str] = set()

    for member in members:
        name = member.name.rstrip("/")
        path = PurePosixPath(name)
        unsafe = (
            not name
            or "\\" in name
            or path.is_absolute()
            or ".." in path.parts
            or not (member.isfile() or member.isdir())
        )
        if unsafe:
            raise ValueError(f"unsafe archive member: {member.name!r}")
        if name in names:
            raise ValueError(f"duplicate archive member: {member.name!r}")
        names.add(name)
        roots.add(path.parts[0])

    if len(roots) != 1:
        raise ValueError("sdist must contain exactly one top-level directory")

    root = next(iter(roots))
    required = {f"{root}/PKG-INFO", f"{root}/pyproject.toml"}
    missing = required - names
    if missing:
        raise ValueError(f"sdist is missing required members: {sorted(missing)!r}")

    return sorted(members, key=lambda member: member.name)


def normalize_sdist(source: Path, output: Path, *, epoch: int) -> None:
    """Write *output* with canonical tar and gzip metadata from *source*."""
    if epoch < 0:
        raise ValueError("epoch must be non-negative")
    if not output.parent.is_dir():
        raise ValueError(f"output directory does not exist: {output.parent}")

    temporary_path: Path | None = None
    try:
        with tarfile.open(source, "r:gz") as source_archive:
            members = _validated_members(source_archive)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=output.parent,
                prefix=f".{output.name}.",
                suffix=".tmp",
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)

            with temporary_path.open("wb") as raw_output:
                with gzip.GzipFile(
                    filename="",
                    mode="wb",
                    fileobj=raw_output,
                    compresslevel=9,
                    mtime=epoch,
                ) as compressed:
                    with tarfile.open(
                        fileobj=compressed,
                        mode="w",
                        format=tarfile.PAX_FORMAT,
                    ) as output_archive:
                        for member in members:
                            normalized = copy.copy(member)
                            normalized.mtime = epoch
                            normalized.uid = 0
                            normalized.gid = 0
                            normalized.uname = ""
                            normalized.gname = ""
                            normalized.mode = (
                                0o755
                                if member.isdir() or member.mode & 0o100
                                else 0o644
                            )
                            normalized.pax_headers = {}
                            payload = (
                                source_archive.extractfile(member)
                                if member.isfile()
                                else None
                            )
                            output_archive.addfile(normalized, payload)

        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _parse_epoch(parser: argparse.ArgumentParser, value: int | None) -> int:
    if value is not None:
        return value
    environment_value = os.environ.get("SOURCE_DATE_EPOCH")
    if environment_value is None:
        parser.error("provide --epoch or set SOURCE_DATE_EPOCH")
    try:
        return int(environment_value)
    except ValueError:
        parser.error("SOURCE_DATE_EPOCH must be an integer")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--epoch", type=int)
    args = parser.parse_args(argv)

    try:
        normalize_sdist(args.source, args.output, epoch=_parse_epoch(parser, args.epoch))
    except (OSError, tarfile.TarError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
