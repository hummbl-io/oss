"""Shared ruff lint configuration for the HUMMBL fleet."""

from __future__ import annotations

from pathlib import Path

__all__ = ["get_ruff_config_path", "get_ruff_config_text"]


def get_ruff_config_path() -> Path:
    """Return the absolute path to the packaged ruff.toml configuration."""
    return Path(__file__).resolve().parent / "ruff.toml"


def get_ruff_config_text() -> str:
    """Return the content of the packaged ruff.toml configuration."""
    return get_ruff_config_path().read_text(encoding="utf-8")
