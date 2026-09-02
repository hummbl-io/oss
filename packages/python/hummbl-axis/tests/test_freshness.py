"""Tests for the Atlas freshness checker."""

import os
import time
from pathlib import Path

from hummbl_axis.atlas_reader import (
    FRESHNESS_WINDOWS,
    FreshnessResult,
    check_freshness,
    scan_freshness,
)


class TestCheckFreshness:
    def test_fresh_file_not_stale(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-test.md"
        path.write_text("test", encoding="utf-8")
        now = time.time()
        result = check_freshness(path, "metadata", now=now)
        assert result.is_stale is False
        assert result.age_days < 1
        assert result.max_age_days == 30
        assert result.category == "metadata"

    def test_old_file_is_stale(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-old.md"
        path.write_text("test", encoding="utf-8")
        # Set mtime to 45 days ago
        old_time = time.time() - (45 * 86400)
        os.utime(path, (old_time, old_time))
        result = check_freshness(path, "metadata")
        assert result.is_stale is True
        assert result.age_days > 30

    def test_dependency_window_14_days(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-deps.md"
        path.write_text("test", encoding="utf-8")
        # Set mtime to 20 days ago
        old_time = time.time() - (20 * 86400)
        os.utime(path, (old_time, old_time))
        result = check_freshness(path, "dependency")
        assert result.is_stale is True
        assert result.max_age_days == 14

    def test_security_window_7_days(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-sec.md"
        path.write_text("test", encoding="utf-8")
        # Set mtime to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(path, (old_time, old_time))
        result = check_freshness(path, "security")
        assert result.is_stale is True
        assert result.max_age_days == 7

    def test_nonexistent_file(self, tmp_path: Path):
        path = tmp_path / "nonexistent.md"
        result = check_freshness(path, "metadata")
        assert result.is_stale is True
        assert result.last_modified == 0.0

    def test_to_dict(self, tmp_path: Path):
        path = tmp_path / "test.md"
        path.write_text("test", encoding="utf-8")
        result = check_freshness(path, "metadata")
        d = result.to_dict()
        assert d["category"] == "metadata"
        assert d["max_age_days"] == 30
        assert "is_stale" in d

    def test_freshness_windows_constant(self):
        assert FRESHNESS_WINDOWS["metadata"] == 30
        assert FRESHNESS_WINDOWS["dependency"] == 14
        assert FRESHNESS_WINDOWS["security"] == 7


class TestScanFreshness:
    def test_scans_directory(self, tmp_path: Path):
        # Create 3 files with different ages
        for i, days_ago in enumerate([5, 40, 10]):
            p = tmp_path / f"hummbl-atlas-{i}.md"
            p.write_text("test", encoding="utf-8")
            old_time = time.time() - (days_ago * 86400)
            os.utime(p, (old_time, old_time))

        results = scan_freshness(tmp_path, "hummbl-atlas-*.md", "metadata")
        assert len(results) == 3
        # Sorted oldest first
        assert results[0].age_days > results[1].age_days
        # The 40-day-old one is stale
        stale = [r for r in results if r.is_stale]
        assert len(stale) == 1

    def test_empty_directory(self, tmp_path: Path):
        results = scan_freshness(tmp_path, "hummbl-atlas-*.md")
        assert results == []

    def test_non_matching_pattern(self, tmp_path: Path):
        (tmp_path / "other.txt").write_text("test", encoding="utf-8")
        results = scan_freshness(tmp_path, "hummbl-atlas-*.md")
        assert results == []
