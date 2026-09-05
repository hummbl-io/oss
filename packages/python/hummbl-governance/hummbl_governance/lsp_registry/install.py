"""Auto-installation utilities for LSP servers.

Provides cross-platform installation logic for common language servers,
with support for npm, pip, cargo, go install, and direct binary downloads.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("hummbl_governance.lsp_registry.install")

_ALLOWED_DOWNLOAD_SCHEMES = frozenset({"http", "https"})


def _safe_extract_tar(tf: tarfile.TarFile, dest: str) -> None:
    """Extract tar archive with path-traversal protection (tar slip / CVE-2007-4559).

    Rejects members whose resolved path escapes the destination directory.
    On Python 3.12+ delegates to the stdlib ``filter="data"`` parameter.
    """
    if sys.version_info >= (3, 12):
        tf.extractall(dest, filter="data")
        return
    dest_path = os.path.realpath(dest)
    for member in tf.getmembers():
        member_path = os.path.realpath(os.path.join(dest, member.name))
        if not member_path.startswith(dest_path + os.sep) and member_path != dest_path:
            raise ValueError(f"Refusing to extract path outside destination: {member.name}")
    tf.extractall(dest)


def _safe_extract_zip(zf: zipfile.ZipFile, dest: str) -> None:
    """Extract zip archive with path-traversal protection (zip slip).

    Rejects entries whose resolved path escapes the destination directory.
    """
    dest_path = os.path.realpath(dest)
    for name in zf.namelist():
        member_path = os.path.realpath(os.path.join(dest, name))
        if not member_path.startswith(dest_path + os.sep) and member_path != dest_path:
            raise ValueError(f"Refusing to extract path outside destination: {name}")
    zf.extractall(dest)

# ---------------------------------------------------------------------------
# Installation recipes
# ---------------------------------------------------------------------------


@dataclass
class InstallRecipe:
    """Recipe for installing an LSP server."""

    # Package manager to use
    manager: str  # "npm", "pip", "cargo", "go", "binary", "custom"

    # Package name or identifier
    package: str

    # Expected binary name after install
    binary: str

    # Optional version constraint
    version: Optional[str] = None

    # For binary installs: download URL template (with {version} placeholder)
    download_url: Optional[str] = None

    # For binary installs: archive type ("zip", "tar.gz", "tar.xz", "raw")
    archive_type: Optional[str] = None

    # Custom install function name (if manager == "custom")
    custom_func: Optional[str] = None

    # Post-install verification command
    verify_cmd: Optional[str] = None


# Built-in recipes for common servers
RECIPES: dict[str, InstallRecipe] = {
    "pyright": InstallRecipe(
        manager="npm",
        package="pyright",
        binary="pyright-langserver",
    ),
    "typescript-language-server": InstallRecipe(
        manager="npm",
        package="typescript-language-server",
        binary="typescript-language-server",
    ),
    "gopls": InstallRecipe(
        manager="go",
        package="golang.org/x/tools/gopls@latest",
        binary="gopls",
    ),
    "rust-analyzer": InstallRecipe(
        manager="binary",
        package="rust-analyzer",
        binary="rust-analyzer",
        download_url="https://github.com/rust-lang/rust-analyzer/releases/download/{version}/rust-analyzer-{platform}.gz",
        archive_type="gz",
    ),
    "clangd": InstallRecipe(
        manager="binary",
        package="clangd",
        binary="clangd",
        download_url="https://github.com/clangd/clangd/releases/download/{version}/clangd-{platform}.zip",
        archive_type="zip",
    ),
    "bash-language-server": InstallRecipe(
        manager="npm",
        package="bash-language-server",
        binary="bash-language-server",
    ),
    "yaml-language-server": InstallRecipe(
        manager="npm",
        package="yaml-language-server",
        binary="yaml-language-server",
    ),
    "lua-language-server": InstallRecipe(
        manager="binary",
        package="lua-language-server",
        binary="lua-language-server",
        download_url="https://github.com/LuaLS/lua-language-server/releases/download/{version}/lua-language-server-{version}-{platform}.tar.gz",
        archive_type="tar.gz",
    ),
    "vscode-langservers-extracted": InstallRecipe(
        manager="npm",
        package="vscode-langservers-extracted",
        binary="vscode-css-language-server",
    ),
}


def _get_platform_key() -> str:
    """Return a platform key for binary downloads."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        if machine in ("amd64", "x86_64"):
            return "win32-x64"
        return "win32-ia32"
    elif system == "darwin":
        if machine == "arm64":
            return "darwin-arm64"
        return "darwin-x64"
    elif system == "linux":
        if machine in ("x86_64", "amd64"):
            return "linux-x64"
        elif machine in ("aarch64", "arm64"):
            return "linux-arm64"
        return "linux-x64"
    return "unknown"


def _which(bin_name: str) -> Optional[str]:
    """Find binary on PATH."""
    return shutil.which(bin_name)


def _run_install(cmd: list[str], cwd: Optional[str] = None) -> bool:
    """Run an install command, return True on success."""
    try:
        logger.info("Running install: %s", " ".join(cmd))
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error("Install failed: %s", result.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("Install timed out")
        return False
    except Exception as e:
        logger.error("Install error: %s", e)
        return False


def _install_npm(recipe: InstallRecipe) -> bool:
    """Install via npm."""
    pkg = recipe.package
    if recipe.version:
        pkg = f"{pkg}@{recipe.version}"
    return _run_install(["npm", "install", "-g", pkg])


def _install_pip(recipe: InstallRecipe) -> bool:
    """Install via pip."""
    pkg = recipe.package
    if recipe.version:
        pkg = f"{pkg}=={recipe.version}"
    return _run_install([sys.executable, "-m", "pip", "install", pkg])


def _install_cargo(recipe: InstallRecipe) -> bool:
    """Install via cargo."""
    pkg = recipe.package
    if recipe.version:
        pkg = f"{pkg}@{recipe.version}"
    return _run_install(["cargo", "install", pkg])


def _install_go(recipe: InstallRecipe) -> bool:
    """Install via go install."""
    pkg = recipe.package
    if recipe.version and "@" not in pkg:
        pkg = f"{pkg}@{recipe.version}"
    return _run_install(["go", "install", pkg])


def _install_binary(recipe: InstallRecipe) -> bool:
    """Install by downloading a binary archive."""
    if not recipe.download_url:
        logger.error("No download_url for binary recipe: %s", recipe.package)
        return False

    version = recipe.version or "latest"
    platform_key = _get_platform_key()

    url = recipe.download_url.format(version=version, platform=platform_key)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in _ALLOWED_DOWNLOAD_SCHEMES:
        logger.error("Refusing URL with disallowed scheme: %s", parsed.scheme)
        return False
    logger.info("Downloading %s from %s", recipe.package, url)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            archive_path = tmpdir / "download"

            # Download
            urllib.request.urlretrieve(url, archive_path)

            # Extract
            if recipe.archive_type == "zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    _safe_extract_zip(zf, str(tmpdir))
            elif recipe.archive_type in ("tar.gz", "tgz"):
                with tarfile.open(archive_path, "r:gz") as tf:
                    _safe_extract_tar(tf, str(tmpdir))
            elif recipe.archive_type == "tar.xz":
                with tarfile.open(archive_path, "r:xz") as tf:
                    _safe_extract_tar(tf, str(tmpdir))
            elif recipe.archive_type == "gz":
                import gzip
                import shutil

                out_path = tmpdir / recipe.binary
                with gzip.open(archive_path, "rb") as f_in:
                    with open(out_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                out_path.chmod(0o755)
            elif recipe.archive_type == "raw":
                out_path = tmpdir / recipe.binary
                shutil.move(archive_path, out_path)
                out_path.chmod(0o755)
            else:
                logger.error("Unknown archive type: %s", recipe.archive_type)
                return False

            # Find the binary
            bin_path = None
            for root, _dirs, files in os.walk(tmpdir):
                for f in files:
                    if f == recipe.binary or f.startswith(recipe.binary):
                        bin_path = Path(root) / f
                        break
                if bin_path:
                    break

            if not bin_path:
                logger.error("Binary not found in archive: %s", recipe.binary)
                return False

            # Install to user bin directory
            install_dir = Path.home() / ".local" / "bin"
            install_dir.mkdir(parents=True, exist_ok=True)
            dest = install_dir / recipe.binary
            shutil.copy2(bin_path, dest)
            dest.chmod(0o755)

            logger.info("Installed %s to %s", recipe.binary, dest)
            return True

    except Exception as e:
        logger.error("Binary install failed: %s", e)
        return False


# Manager dispatch
_INSTALLERS = {
    "npm": _install_npm,
    "pip": _install_pip,
    "cargo": _install_cargo,
    "go": _install_go,
    "binary": _install_binary,
}


def try_install(server_id: str, strategy: str = "auto") -> Optional[str]:
    """Attempt to install an LSP server.

    Args:
        server_id: The server identifier (must match a recipe key).
        strategy: "auto" (try install), "manual" (check only), "off" (no install).

    Returns:
        Path to the binary if available (installed or already present), else None.
    """
    if strategy == "off":
        return None

    # First check if already available
    recipe = RECIPES.get(server_id)
    if recipe:
        existing = _which(recipe.binary)
        if existing:
            return existing

    if strategy == "manual":
        return None

    # Try to install
    if recipe and recipe.manager in _INSTALLERS:
        installer = _INSTALLERS[recipe.manager]
        if installer(recipe):
            # Verify installation
            existing = _which(recipe.binary)
            if existing:
                return existing
            # Also check user local bin
            user_bin = Path.home() / ".local" / "bin" / recipe.binary
            if user_bin.exists():
                return str(user_bin)

    return None


def verify_install(server_id: str) -> bool:
    """Verify a server is installed and working."""
    recipe = RECIPES.get(server_id)
    if not recipe:
        return False

    bin_path = _which(recipe.binary)
    if not bin_path:
        user_bin = Path.home() / ".local" / "bin" / recipe.binary
        if user_bin.exists():
            bin_path = str(user_bin)
        else:
            return False

    if recipe.verify_cmd:
        try:
            result = subprocess.run(
                recipe.verify_cmd.split(),
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    return True


def list_available_recipes() -> dict[str, InstallRecipe]:
    """Return all known installation recipes."""
    return RECIPES.copy()


__all__ = [
    "InstallRecipe",
    "RECIPES",
    "try_install",
    "verify_install",
    "list_available_recipes",
]
