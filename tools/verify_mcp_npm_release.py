"""Validate the public MCP release handoff without executing package contents."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile

PACKAGE = "@hummbl/mcp-server"
REPOSITORY_URL = "https://github.com/hummbl-io/oss.git"
VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?")


def verify_release(release, actor):
    if not actor or release["author"]["login"] != actor or release["draft"]:
        raise ValueError("Unexpected release creator or draft state")
    receipt = json.loads(release["body"])
    version = receipt["version"]
    match = VERSION.fullmatch(version)
    if not match or release["tag_name"] != f"mcp-server/v{version}":
        raise ValueError("Release tag and package version must agree")
    channel = match.group(1)
    if channel and any(re.fullmatch(r"0\d+", part) for part in channel.split(".")):
        raise ValueError("Invalid numeric prerelease identifier")
    if bool(channel) != release["prerelease"]:
        raise ValueError("Prerelease flag and version disagree")
    digest = receipt["npm_sha256"]
    if not re.fullmatch(r"[a-f0-9]{64}", digest) or not re.fullmatch(r"[a-f0-9]{40}", receipt["source_commit"]):
        raise ValueError("Invalid release digest or source commit")
    assets = release["assets"]
    if len(assets) != 1:
        raise ValueError("Expected a single release asset")
    asset = assets[0]
    if (asset["name"] != "npm.tgz" or asset["state"] != "uploaded" or asset["digest"] != "sha256:" + digest
            or type(asset["id"]) is not int or asset["id"] < 1):
        raise ValueError("The uploaded asset must match the private build digest")
    dist_tag = channel.split(".")[0] if channel else "latest"
    if channel and dist_tag not in ("alpha", "beta"):
        dist_tag = "next"
    return {"asset_id": asset["id"], "sha256": digest, "version": version, "dist_tag": dist_tag}


def verify_package(filename, digest, version):
    with Path(filename).open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
            raise ValueError("Downloaded tarball digest mismatch")
    names = set()
    with tarfile.open(filename, "r:gz") as archive:
        for member in archive:
            name = member.name
            path = PurePosixPath(name)
            if (not member.isfile() or name in names or path.as_posix() != name or ".." in path.parts
                    or not name.startswith("package/")):
                raise ValueError("Invalid archive entry")
            names.add(name)
            if name == "package/package.json":
                manifest = json.load(archive.extractfile(member))
                if (manifest["name"] != PACKAGE or manifest["version"] != version or manifest.get("private")
                        or manifest["repository"]["url"] != REPOSITORY_URL):
                    raise ValueError("Unexpected npm package identity")
    if not {"package/package.json", "package/dist/index.js"}.issubset(names):
        raise ValueError("Incomplete npm package")


if __name__ == "__main__":
    if sys.argv[1] == "release":
        result = verify_release(json.loads(Path(sys.argv[2]).read_text()), os.environ["RELAY_LOGIN"])
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            for key, value in result.items():
                print(f"{key}={value}", file=out)
    elif sys.argv[1] == "package":
        verify_package(*sys.argv[2:])
    else:
        raise SystemExit("Expected release or package")
