"""Tests for review coverage matrix."""

from __future__ import annotations

import json
from pathlib import Path

from hummbl_gitops.remote.coverage_matrix import ReviewCoverage, get_coverage, record_review


class TestReviewCoverage:
    def test_empty_coverage(self) -> None:
        cov = ReviewCoverage(pr_number=1)
        assert len(cov.reviews) == 0
        assert len(cov.covered_aspects) == 0
        assert len(cov.uncovered_aspects) == 8

    def test_add_review(self) -> None:
        cov = ReviewCoverage(pr_number=1)
        cov.add_review(agent="devin", aspect="security")
        assert "security" in cov.covered_aspects
        assert "security" not in cov.uncovered_aspects

    def test_summary_shows_uncovered(self) -> None:
        cov = ReviewCoverage(pr_number=1)
        cov.add_review(agent="devin", aspect="security")
        summary = cov.summary()
        assert "security: devin" in summary
        assert "Uncovered" in summary

    def test_summary_all_covered(self) -> None:
        cov = ReviewCoverage(pr_number=1)
        for aspect in ["security", "logic", "tests", "docs", "style", "ci", "performance", "breaking"]:
            cov.add_review(agent="devin", aspect=aspect)
        summary = cov.summary()
        assert "All aspects covered" in summary

    def test_json_roundtrip(self) -> None:
        cov = ReviewCoverage(pr_number=42)
        cov.add_review(agent="devin", aspect="security", timestamp="2026-09-01T12:00:00Z")
        json_str = cov.to_json()
        restored = ReviewCoverage.from_json(json_str)
        assert restored.pr_number == 42
        assert len(restored.reviews) == 1
        assert restored.reviews[0]["aspect"] == "security"
