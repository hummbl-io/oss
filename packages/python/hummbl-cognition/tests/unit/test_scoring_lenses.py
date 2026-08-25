"""Tests for the scoring lenses module.

Tests cover: ScoringLens validation, TSV loading, data summarization,
finding parsing/normalization, lens registry, run_lens (with mocked Ollama),
CLI entry points, and ledger entry conversion.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from hummbl_cognition.scoring_lenses import (
    BUILTIN_LENSES,
    ScoringLens,
    _clamp_float,
    _normalize_effort,
    findings_to_ledger_entries,
    get_lens,
    list_lenses,
    load_results_tsv,
    main,
    parse_findings,
    register_lens,
    run_lens,
    summarize_data,
)

# ---------------------------------------------------------------------------
# Sample TSV data
# ---------------------------------------------------------------------------

SAMPLE_TSV = (
    "commit\tval_bpb\tmemory_gb\tstatus\tdescription\n"
    "abc1234\t1.82\t14.2\tpass\tbaseline config\n"
    "def5678\t1.75\t16.8\tpass\tincreased context\n"
    "ghi9012\t1.91\t12.1\tfail\treduced batch size\n"
    "jkl3456\t1.68\t22.4\tpass\tlarger model\n"
)


def _write_tsv(tmp_path: Path, content: str = SAMPLE_TSV) -> Path:
    p = tmp_path / "results.tsv"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# ScoringLens dataclass
# ---------------------------------------------------------------------------

class TestScoringLens:
    def test_valid_creation(self):
        lens = ScoringLens(
            name="test",
            description="A test lens",
            system_prompt="Analyze this",
        )
        assert lens.name == "test"
        assert lens.temperature == 0.3
        assert lens.output_format == "findings_json"
        assert lens.tags == ()

    def test_name_with_hyphens_and_underscores(self):
        lens = ScoringLens(
            name="my-test_lens",
            description="test",
            system_prompt="test",
        )
        assert lens.name == "my-test_lens"

    def test_invalid_name_empty(self):
        with pytest.raises(ValueError, match="Lens name"):
            ScoringLens(name="", description="x", system_prompt="x")

    def test_invalid_name_special_chars(self):
        with pytest.raises(ValueError, match="Lens name"):
            ScoringLens(name="bad name!", description="x", system_prompt="x")

    def test_invalid_temperature_low(self):
        with pytest.raises(ValueError, match="Temperature"):
            ScoringLens(name="t", description="x", system_prompt="x", temperature=-0.1)

    def test_invalid_temperature_high(self):
        with pytest.raises(ValueError, match="Temperature"):
            ScoringLens(name="t", description="x", system_prompt="x", temperature=2.5)

    def test_empty_system_prompt(self):
        with pytest.raises(ValueError, match="system_prompt"):
            ScoringLens(name="t", description="x", system_prompt="")

    def test_frozen(self):
        lens = ScoringLens(name="t", description="x", system_prompt="x")
        with pytest.raises(AttributeError):
            lens.name = "changed"  # type: ignore[misc]

    def test_custom_tags(self):
        lens = ScoringLens(
            name="t", description="x", system_prompt="x",
            tags=("a", "b"),
        )
        assert lens.tags == ("a", "b")


# ---------------------------------------------------------------------------
# Built-in lenses
# ---------------------------------------------------------------------------

class TestBuiltinLenses:
    def test_four_builtin_lenses(self):
        assert len(BUILTIN_LENSES) >= 4
        for name in ("convergence", "efficiency", "risk", "transfer"):
            assert name in BUILTIN_LENSES

    def test_get_lens_valid(self):
        lens = get_lens("convergence")
        assert lens.name == "convergence"
        assert "convergence" in lens.description.lower()

    def test_get_lens_unknown(self):
        with pytest.raises(KeyError, match="Unknown lens"):
            get_lens("nonexistent")

    def test_list_lenses(self):
        result = list_lenses()
        assert len(result) >= 4
        names = {l["name"] for l in result}
        assert "convergence" in names
        assert "efficiency" in names
        assert "risk" in names
        assert "transfer" in names
        # Verify structure
        for item in result:
            assert "name" in item
            assert "description" in item
            assert "temperature" in item
            assert "tags" in item

    def test_all_lenses_have_tags(self):
        for name, lens in BUILTIN_LENSES.items():
            assert len(lens.tags) > 0, f"Lens {name} has no tags"
            assert "mlx" in lens.tags, f"Lens {name} missing 'mlx' tag"


# ---------------------------------------------------------------------------
# Lens registration
# ---------------------------------------------------------------------------

class TestLensRegistration:
    def test_register_custom_lens(self):
        custom = ScoringLens(
            name="custom-test",
            description="A custom test lens",
            system_prompt="Custom analysis",
            tags=("custom",),
        )
        register_lens(custom)
        try:
            assert get_lens("custom-test") is custom
        finally:
            # Clean up to avoid polluting other tests
            BUILTIN_LENSES.pop("custom-test", None)

    def test_register_overwrites(self):
        original = ScoringLens(
            name="overwrite-test",
            description="original",
            system_prompt="original",
        )
        replacement = ScoringLens(
            name="overwrite-test",
            description="replaced",
            system_prompt="replaced",
        )
        register_lens(original)
        register_lens(replacement)
        try:
            assert get_lens("overwrite-test").description == "replaced"
        finally:
            BUILTIN_LENSES.pop("overwrite-test", None)


# ---------------------------------------------------------------------------
# TSV loading
# ---------------------------------------------------------------------------

class TestLoadResultsTsv:
    def test_load_valid_tsv(self, tmp_path):
        p = _write_tsv(tmp_path)
        rows = load_results_tsv(p)
        assert len(rows) == 4
        assert rows[0]["commit"] == "abc1234"
        assert rows[0]["val_bpb"] == "1.82"
        assert rows[2]["status"] == "fail"

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_results_tsv(tmp_path / "missing.tsv")

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.tsv"
        p.write_text("")
        with pytest.raises(ValueError, match="empty"):
            load_results_tsv(p)

    def test_header_only(self, tmp_path):
        p = tmp_path / "header.tsv"
        p.write_text("commit\tval_bpb\n")
        with pytest.raises(ValueError, match="at least a header and one data row"):
            load_results_tsv(p)

    def test_mismatched_columns(self, tmp_path):
        p = tmp_path / "short.tsv"
        p.write_text("a\tb\tc\n1\t2\n")
        rows = load_results_tsv(p)
        assert len(rows) == 1
        assert rows[0]["a"] == "1"
        assert rows[0]["b"] == "2"
        assert rows[0]["c"] == ""  # padded

    def test_blank_lines_skipped(self, tmp_path):
        p = tmp_path / "blanks.tsv"
        p.write_text("a\tb\n1\t2\n\n3\t4\n\n")
        rows = load_results_tsv(p)
        assert len(rows) == 2

    def test_accepts_string_path(self, tmp_path):
        p = _write_tsv(tmp_path)
        rows = load_results_tsv(str(p))
        assert len(rows) == 4


# ---------------------------------------------------------------------------
# Data summarization
# ---------------------------------------------------------------------------

class TestSummarizeData:
    def test_empty_data(self):
        assert summarize_data([]) == "(no data)"

    def test_basic_summary(self, tmp_path):
        p = _write_tsv(tmp_path)
        rows = load_results_tsv(p)
        summary = summarize_data(rows)
        assert "commit" in summary
        assert "abc1234" in summary
        assert summary.count("\n") == 4  # header + 4 data rows

    def test_max_rows_truncation(self, tmp_path):
        p = _write_tsv(tmp_path)
        rows = load_results_tsv(p)
        summary = summarize_data(rows, max_rows=2)
        assert "2 more rows omitted" in summary
        # Should have header + 2 data rows + truncation note
        lines = summary.strip().split("\n")
        assert len(lines) == 4


# ---------------------------------------------------------------------------
# Finding parsing
# ---------------------------------------------------------------------------

class TestParseFindings:
    def test_valid_json_array(self):
        raw = json.dumps([
            {"id": "F-001", "claim": "Test claim", "confidence": 0.8,
             "actionable": True, "target": "config", "effort": "low"},
        ])
        findings = parse_findings(raw, "test")
        assert len(findings) == 1
        assert findings[0]["id"] == "F-001"
        assert findings[0]["category"] == "test"

    def test_markdown_fenced_json(self):
        raw = "```json\n" + json.dumps([
            {"id": "F-001", "claim": "X", "confidence": 0.7}
        ]) + "\n```"
        findings = parse_findings(raw, "test")
        assert len(findings) == 1

    def test_wrapped_in_findings_key(self):
        raw = json.dumps({
            "findings": [
                {"id": "F-001", "claim": "X"},
                {"id": "F-002", "claim": "Y"},
            ]
        })
        findings = parse_findings(raw, "test")
        assert len(findings) == 2

    def test_single_finding_object(self):
        raw = json.dumps({"id": "F-001", "claim": "X"})
        findings = parse_findings(raw, "test")
        assert len(findings) == 1

    def test_embedded_json_in_text(self):
        raw = "Here are the findings:\n" + json.dumps([
            {"id": "F-001", "claim": "X"}
        ]) + "\nEnd of analysis."
        findings = parse_findings(raw, "test")
        assert len(findings) == 1

    def test_empty_response(self):
        assert parse_findings("", "test") == []
        assert parse_findings(None, "test") == []  # type: ignore[arg-type]

    def test_invalid_json(self):
        assert parse_findings("this is not json at all", "test") == []

    def test_confidence_clamping(self):
        raw = json.dumps([
            {"claim": "X", "confidence": 1.5},
            {"claim": "Y", "confidence": -0.3},
        ])
        findings = parse_findings(raw, "test")
        assert findings[0]["confidence"] == 1.0
        assert findings[1]["confidence"] == 0.0

    def test_effort_normalization(self):
        raw = json.dumps([
            {"claim": "A", "effort": "Low"},
            {"claim": "B", "effort": "HIGH"},
            {"claim": "C", "effort": "trivial"},
            {"claim": "D", "effort": "significant"},
            {"claim": "E", "effort": "whatever"},
        ])
        findings = parse_findings(raw, "test")
        assert findings[0]["effort"] == "low"
        assert findings[1]["effort"] == "high"
        assert findings[2]["effort"] == "low"
        assert findings[3]["effort"] == "high"
        assert findings[4]["effort"] == "medium"

    def test_claim_truncation(self):
        raw = json.dumps([{"claim": "x" * 300}])
        findings = parse_findings(raw, "test")
        assert len(findings[0]["claim"]) == 200

    def test_auto_generated_ids(self):
        raw = json.dumps([{"claim": "A"}, {"claim": "B"}])
        findings = parse_findings(raw, "test")
        assert findings[0]["id"] == "SL-001"
        assert findings[1]["id"] == "SL-002"

    def test_non_dict_items_skipped(self):
        raw = json.dumps([{"claim": "A"}, "not a dict", 42, {"claim": "B"}])
        findings = parse_findings(raw, "test")
        assert len(findings) == 2

    def test_defaults_for_missing_fields(self):
        raw = json.dumps([{"claim": "minimal"}])
        findings = parse_findings(raw, "test")
        f = findings[0]
        assert f["confidence"] == 0.5
        assert f["actionable"] is True
        assert f["target"] == "unknown"
        assert f["effort"] == "medium"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_clamp_float_normal(self):
        assert _clamp_float(0.5, 0.0, 1.0) == 0.5

    def test_clamp_float_high(self):
        assert _clamp_float(2.0, 0.0, 1.0) == 1.0

    def test_clamp_float_low(self):
        assert _clamp_float(-1.0, 0.0, 1.0) == 0.0

    def test_clamp_float_string(self):
        assert _clamp_float("0.7", 0.0, 1.0) == 0.7

    def test_clamp_float_invalid(self):
        assert _clamp_float("not-a-number", 0.0, 1.0) == 0.5

    def test_normalize_effort_variants(self):
        assert _normalize_effort("low") == "low"
        assert _normalize_effort("L") == "low"
        assert _normalize_effort("easy") == "low"
        assert _normalize_effort("HIGH") == "high"
        assert _normalize_effort("hard") == "high"
        assert _normalize_effort("medium") == "medium"
        assert _normalize_effort("something else") == "medium"
        assert _normalize_effort(42) == "medium"


# ---------------------------------------------------------------------------
# run_lens (with mocked Ollama)
# ---------------------------------------------------------------------------

class TestRunLens:
    def test_dry_run(self, tmp_path):
        p = _write_tsv(tmp_path)
        result = run_lens(p, "convergence", dry_run=True)
        assert result["lens"] == "convergence"
        assert result["row_count"] == 4
        assert result["findings"] == []
        assert result["error"] is None
        assert "prompt" in result
        assert "system" in result["prompt"]
        assert "user" in result["prompt"]
        assert "convergence" in result["prompt"]["user"]

    def test_unknown_lens(self, tmp_path):
        p = _write_tsv(tmp_path)
        with pytest.raises(KeyError, match="Unknown lens"):
            run_lens(p, "nonexistent")

    def test_missing_data_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            run_lens(tmp_path / "missing.tsv", "convergence")

    @patch("hummbl_cognition.scoring_lenses._call_ollama")
    def test_successful_run(self, mock_ollama, tmp_path):
        mock_ollama.return_value = json.dumps([
            {"id": "F-001", "claim": "Convergence is fast", "confidence": 0.85,
             "actionable": True, "target": "training", "effort": "low"},
            {"id": "F-002", "claim": "Plateau at 1.75", "confidence": 0.7,
             "actionable": False, "target": "config", "effort": "medium"},
        ])
        p = _write_tsv(tmp_path)
        result = run_lens(p, "convergence")
        assert result["error"] is None
        assert len(result["findings"]) == 2
        assert result["findings"][0]["category"] == "convergence"
        mock_ollama.assert_called_once()

    @patch("hummbl_cognition.scoring_lenses._call_ollama")
    def test_ollama_failure(self, mock_ollama, tmp_path):
        mock_ollama.return_value = None
        p = _write_tsv(tmp_path)
        result = run_lens(p, "risk")
        assert result["error"] is not None
        assert "Ollama" in result["error"]
        assert result["findings"] == []

    @patch("hummbl_cognition.scoring_lenses._call_ollama")
    def test_ollama_bad_json(self, mock_ollama, tmp_path):
        mock_ollama.return_value = "This is not JSON"
        p = _write_tsv(tmp_path)
        result = run_lens(p, "efficiency")
        assert result["findings"] == []
        assert result["error"] is None  # parse failure is not an error, just empty

    @patch("hummbl_cognition.scoring_lenses._call_ollama")
    def test_uses_correct_temperature(self, mock_ollama, tmp_path):
        mock_ollama.return_value = "[]"
        p = _write_tsv(tmp_path)
        run_lens(p, "risk")
        _, kwargs = mock_ollama.call_args
        assert kwargs["temperature"] == 0.4  # risk lens temperature

    def test_timestamp_in_result(self, tmp_path):
        p = _write_tsv(tmp_path)
        result = run_lens(p, "convergence", dry_run=True)
        assert "timestamp" in result
        assert result["timestamp"].endswith("Z")


# ---------------------------------------------------------------------------
# Ledger entry conversion
# ---------------------------------------------------------------------------

class TestFindingsToLedgerEntries:
    def test_converts_findings(self):
        findings = [
            {"id": "F-001", "claim": "Test claim", "confidence": 0.8,
             "actionable": True, "target": "config", "effort": "low",
             "category": "convergence"},
        ]
        entries = findings_to_ledger_entries(findings, "convergence")
        assert len(entries) == 1
        entry = entries[0]
        assert entry["agent"] == "scoring-lenses"
        assert entry["vendor"] == "local"
        assert entry["type"] == "discovery"
        assert entry["scope"] == "project"
        assert entry["confidence"] == 0.8
        assert "convergence" in entry["content"]
        assert "Test claim" in entry["content"]
        assert "scoring-lens" in entry["tags"]
        assert "lens:convergence" in entry["tags"]

    def test_empty_findings(self):
        entries = findings_to_ledger_entries([], "test")
        assert entries == []

    def test_multiple_findings(self):
        findings = [
            {"claim": "A", "confidence": 0.6},
            {"claim": "B", "confidence": 0.9},
        ]
        entries = findings_to_ledger_entries(findings, "efficiency")
        assert len(entries) == 2
        # Each should have unique IDs
        ids = {e["id"] for e in entries}
        assert len(ids) == 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_no_command(self, capsys):
        ret = main([])
        assert ret == 2

    def test_list_command(self, capsys):
        ret = main(["list"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "convergence" in out
        assert "efficiency" in out
        assert "risk" in out
        assert "transfer" in out

    def test_run_dry_run(self, tmp_path, capsys):
        p = _write_tsv(tmp_path)
        ret = main(["run", "--lens", "convergence", "--data", str(p), "--dry-run"])
        assert ret == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["lens"] == "convergence"
        assert "prompt" in parsed

    def test_run_missing_file(self, tmp_path, capsys):
        ret = main(["run", "--lens", "convergence", "--data", str(tmp_path / "nope.tsv")])
        assert ret == 1

    def test_run_bad_lens(self, tmp_path, capsys):
        p = _write_tsv(tmp_path)
        ret = main(["run", "--lens", "nonexistent", "--data", str(p)])
        assert ret == 1

    @patch("hummbl_cognition.scoring_lenses._call_ollama")
    def test_run_with_findings(self, mock_ollama, tmp_path, capsys):
        mock_ollama.return_value = json.dumps([
            {"id": "F-001", "claim": "Good result", "confidence": 0.9}
        ])
        p = _write_tsv(tmp_path)
        ret = main(["run", "--lens", "efficiency", "--data", str(p)])
        assert ret == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert len(parsed["findings"]) == 1

    @patch("hummbl_cognition.scoring_lenses._call_ollama")
    def test_run_ollama_failure_returns_1(self, mock_ollama, tmp_path, capsys):
        mock_ollama.return_value = None
        p = _write_tsv(tmp_path)
        ret = main(["run", "--lens", "risk", "--data", str(p)])
        assert ret == 1
