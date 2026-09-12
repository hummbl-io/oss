from __future__ import annotations

from pathlib import Path

import pytest

from hummbl_bus import bus_writer_cli


def test_legacy_sign_flag_fails_closed_without_external_key_manager(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bus_path = tmp_path / "messages.tsv"

    result = bus_writer_cli.main(
        [
            "codex",
            "all",
            "STATUS",
            "host=anvil test",
            "--bus",
            str(bus_path),
            "--sign",
        ]
    )

    assert result == 2
    assert "--sign is unavailable" in capsys.readouterr().err
    assert not bus_path.exists()
