"""Regression test: _parse_yamlish() fallback parser for stdlib-only operation.

Phase 1 P0/P1 fixes (lane=fix/cline/hummbl-governance-phase-1-quality).

Prior bugs:
1. _parse_yamlish() was called in _load_atlas() but never defined --
   AttributeError at runtime whenever PyYAML is unavailable, breaking
   the zero-dependency claim.
2. Two definitions were briefly introduced (one block-list parser,
   one inline-list/scalar parser); Python keeps only the later one,
   silently dropping the block-list parser's support for
   boundary_conditions / related_modules / experiment_receipts.
3. The merged parser initially required ": " (colon-space) to detect
   a key, which missed "key:" (empty value, block list follows) --
   causing block-list items to attach to the WRONG previous key.

This test suite exercises _parse_yamlish() directly (bypassing the
PyYAML import) against the real atlas YAML files and synthetic edge
cases to guard against all three regressions.
"""
from __future__ import annotations

from pathlib import Path

from hummbl_governance.kernel.law_engine import LawEngine


ATLAS_DIR = Path(__file__).resolve().parents[2] / "hummbl_governance" / "data" / "atlas"


class TestParseYamlishExists:
    """Guard against the method being called-but-undefined again."""

    def test_method_exists_and_is_callable(self) -> None:
        engine = LawEngine()
        assert hasattr(engine, "_parse_yamlish")
        assert callable(engine._parse_yamlish)

    def test_empty_input_returns_empty_dict(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish("")
        assert result == {}

    def test_comments_only_returns_empty_dict(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish("# just a comment\n# another\n")
        assert result == {}


class TestParseYamlishScalars:
    """Verify scalar key: value parsing (quoted strings, bool, null)."""

    def test_basic_key_value(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish("id: SL-01\ntitle: Test Law\n")
        assert result["id"] == "SL-01"
        assert result["title"] == "Test Law"

    def test_quoted_string_value(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish('title: "Delegation Chain Scaling"\n')
        assert result["title"] == "Delegation Chain Scaling"

    def test_boolean_true_false(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish("enabled: true\ndisabled: false\n")
        assert result["enabled"] is True
        assert result["disabled"] is False

    def test_null_values(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish("value: null\nother: ~\n")
        assert result["value"] is None
        assert result["other"] is None

    def test_inline_list(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish("tags: [a, b, c]\n")
        assert result["tags"] == ["a", "b", "c"]

    def test_comments_are_skipped(self) -> None:
        engine = LawEngine()
        result = engine._parse_yamlish("# comment\nid: SL-02\n# another\nname: Test\n")
        assert result["id"] == "SL-02"
        assert result["name"] == "Test"


class TestParseYamlishBlockLists:
    """Verify block-list parsing (key: followed by indented '- item' lines).

    This is the exact regression Codex flagged: prior merge attempts
    dropped this capability or attached items to the wrong key.
    """

    def test_block_list_under_bare_key(self) -> None:
        engine = LawEngine()
        yaml_text = (
            "boundary_conditions:\n"
            "  - \"Authority attenuation monotonic\"\n"
            "  - \"Each hop logged\"\n"
            "  - \"Verification cost bounded\"\n"
        )
        result = engine._parse_yamlish(yaml_text)
        assert result["boundary_conditions"] == [
            "Authority attenuation monotonic",
            "Each hop logged",
            "Verification cost bounded",
        ]

    def test_multiple_block_lists_do_not_cross_contaminate(self) -> None:
        engine = LawEngine()
        yaml_text = (
            "id: SL-07\n"
            "experiment_receipts: []\n"
            "boundary_conditions:\n"
            "  - \"Authority attenuation monotonic\"\n"
            "  - \"Each hop logged\"\n"
            "  - \"Verification cost bounded\"\n"
            "related_modules:\n"
            "  - \"delegation_token\"\n"
            "  - \"governance_bus\"\n"
            "  - \"idp\"\n"
        )
        result = engine._parse_yamlish(yaml_text)
        assert result["id"] == "SL-07"
        assert result["boundary_conditions"] == [
            "Authority attenuation monotonic",
            "Each hop logged",
            "Verification cost bounded",
        ]
        assert result["related_modules"] == [
            "delegation_token",
            "governance_bus",
            "idp",
        ]
        # Regression guard: related_modules items must NOT bleed into
        # boundary_conditions, and vice versa.
        assert "delegation_token" not in result["boundary_conditions"]
        assert "Each hop logged" not in result["related_modules"]

    def test_scalar_after_block_list_starts_fresh(self) -> None:
        engine = LawEngine()
        yaml_text = (
            "boundary_conditions:\n"
            "  - \"item one\"\n"
            "  - \"item two\"\n"
            "status: candidate.accepted\n"
        )
        result = engine._parse_yamlish(yaml_text)
        assert result["boundary_conditions"] == ["item one", "item two"]
        assert result["status"] == "candidate.accepted"


class TestParseYamlishRealAtlasFiles:
    """Verify the parser against every real SL-*.yaml atlas file."""

    def test_all_atlas_files_parse_without_error(self) -> None:
        # Note: some atlas files (e.g. SL-EXP004) use record_id/name
        # instead of id/title -- _load_atlas() already handles that
        # fallback (data.get("id") or data.get("record_id") or ...).
        # This test only verifies _parse_yamlish() returns a non-empty
        # dict for every file, not that every file uses id/title.
        engine = LawEngine()
        atlas_files = sorted(ATLAS_DIR.glob("SL-*.yaml"))
        assert len(atlas_files) > 0, "No atlas files found -- check ATLAS_DIR"
        for path in atlas_files:
            result = engine._parse_yamlish(path.read_text(encoding="utf-8"))
            assert result, f"{path.name}: _parse_yamlish returned empty dict"
            has_identifier = result.get("id") or result.get("record_id")
            assert has_identifier, f"{path.name}: missing both 'id' and 'record_id'"

    def test_all_atlas_files_load_via_law_engine(self) -> None:
        """Verify LawEngine._load_atlas() successfully loads every atlas
        file into self.laws, including ones using record_id/name aliases
        (e.g. SL-EXP004 uses record_id/name instead of id/title).
        """
        engine = LawEngine()
        atlas_files = sorted(ATLAS_DIR.glob("SL-*.yaml"))
        loaded_ids = {law.law_id for law in engine.list_laws()}

        assert len(loaded_ids) == len(atlas_files), (
            f"Expected {len(atlas_files)} laws loaded, got {len(loaded_ids)}: "
            f"{loaded_ids}"
        )
        # Every file stem should correspond to exactly one loaded law_id.
        expected_stems = {path.stem for path in atlas_files}
        assert loaded_ids == expected_stems, (
            f"Mismatch between atlas file stems and loaded law_ids. "
            f"Missing: {expected_stems - loaded_ids}, "
            f"Unexpected: {loaded_ids - expected_stems}"
        )

    def test_sl07_boundary_conditions_and_related_modules_preserved(self) -> None:
        """SL-07 has both boundary_conditions and related_modules block
        lists -- the exact scenario from Codex's review finding.
        """
        engine = LawEngine()
        sl07_path = ATLAS_DIR / "SL-07.yaml"
        if not sl07_path.exists():
            import pytest
            pytest.skip("SL-07.yaml not present in this checkout")

        result = engine._parse_yamlish(sl07_path.read_text(encoding="utf-8"))
        assert result["id"] == "SL-07"
        assert result["title"] == "Delegation Chain Scaling"
        assert isinstance(result["boundary_conditions"], list)
        assert len(result["boundary_conditions"]) == 3
        assert isinstance(result["related_modules"], list)
        assert len(result["related_modules"]) == 3
        assert "delegation_token" in result["related_modules"]
        assert "Authority attenuation monotonic" in result["boundary_conditions"]


class TestLawEngineLoadsWithoutPyYAML:
    """Verify LawEngine can load the real atlas via _parse_yamlish alone,
    simulating the PyYAML-unavailable fallback path.
    """

    def test_load_atlas_uses_parse_yamlish_successfully(self, monkeypatch) -> None:
        # Force the ImportError branch by making `import yaml` fail
        # inside _load_atlas, regardless of whether PyYAML is installed
        # in the test environment.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("simulated missing PyYAML")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        engine = LawEngine()
        laws = engine.list_laws()
        assert len(laws) > 0, "Atlas should load via _parse_yamlish fallback"

        sl07 = engine.get_law("SL-07")
        if sl07 is not None:
            assert sl07.name == "Delegation Chain Scaling"
            assert len(sl07.boundary_conditions) == 3
            assert len(sl07.related_modules) == 3
