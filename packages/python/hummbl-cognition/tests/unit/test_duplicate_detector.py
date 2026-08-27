"""Tests for duplicate_detector module."""

import pytest
from hummbl_cognition.duplicate_detector import (
    DEFAULT_THRESHOLD,
    DetectionResult,
    DuplicateDetector,
    DuplicateMatch,
    detect_duplicates,
)


class TestSimilarityScoring:
    """Tests for title similarity scoring."""

    def test_identical_titles(self):
        detector = DuplicateDetector()
        score = detector.score_similarity("fix: bug in parser", "fix: bug in parser")
        assert score == 1.0

    def test_completely_different(self):
        detector = DuplicateDetector()
        score = detector.score_similarity(
            "fix: bug in parser", "feat: add new dashboard"
        )
        assert score < 0.5

    def test_near_duplicate(self):
        detector = DuplicateDetector()
        score = detector.score_similarity(
            "security: align reporting contacts with org policy",
            "security: align vulnerability reporting contact and SLA with org policy",
        )
        assert score > 0.7

    def test_case_insensitive(self):
        detector = DuplicateDetector()
        score = detector.score_similarity("Fix Bug", "fix bug")
        assert score == 1.0

    def test_empty_string(self):
        detector = DuplicateDetector()
        assert detector.score_similarity("", "test") == 0.0
        assert detector.score_similarity("test", "") == 0.0
        assert detector.score_similarity("", "") == 0.0


class TestCheckCandidate:
    """Tests for single candidate checking."""

    def test_exact_match(self):
        detector = DuplicateDetector()
        existing = [{"number": 100, "title": "fix: bug in parser"}]
        result = detector.check_candidate("fix: bug in parser", existing)
        assert result.is_duplicate is True
        assert len(result.matches) == 1
        assert result.matches[0].match_type == "exact"
        assert result.best_similarity == 1.0

    def test_near_match(self):
        detector = DuplicateDetector(threshold=0.7)
        existing = [{"number": 50, "title": "docs: reconcile README test count"}]
        result = detector.check_candidate(
            "docs: reconcile README test-count claims", existing
        )
        assert result.is_duplicate is True
        # With keyword overlap scoring, high-overlap titles classify as "keyword"
        # rather than "near". These titles share 3 of 4 meaningful keywords.
        assert result.matches[0].match_type in ("near", "keyword")

    def test_keyword_match(self):
        detector = DuplicateDetector(threshold=0.55, keyword_threshold=0.50)
        existing = [
            {
                "number": 77,
                "title": "governed filename lexicon schema checker",
                "state": "closed",
                "url": "https://github.com/example/repo/issues/77",
            }
        ]

        result = detector.check_candidate(
            "filename checker schema lexicon governance",
            existing,
        )

        assert result.is_duplicate is True
        assert result.matches[0].match_type == "keyword"
        assert result.matches[0].issue_state == "closed"
        assert (
            result.matches[0].issue_url == "https://github.com/example/repo/issues/77"
        )

    def test_no_match(self):
        detector = DuplicateDetector()
        existing = [{"number": 1, "title": "completely different title"}]
        result = detector.check_candidate("fix: bug in parser", existing)
        assert result.is_duplicate is False
        assert len(result.matches) == 0

    def test_empty_existing(self):
        detector = DuplicateDetector()
        result = detector.check_candidate("any title", [])
        assert result.is_duplicate is False

    def test_multiple_matches_sorted(self):
        detector = DuplicateDetector(threshold=0.5)
        existing = [
            {"number": 1, "title": "fix: parser bug"},
            {"number": 2, "title": "fix: parser bug in core"},
            {"number": 3, "title": "unrelated feature"},
        ]
        result = detector.check_candidate("fix: parser bug", existing)
        assert result.is_duplicate is True
        assert len(result.matches) == 2
        assert result.matches[0].similarity >= result.matches[1].similarity


class TestFilterCandidates:
    """Tests for batch filtering."""

    def test_filter_with_provided_issues(self):
        existing = [
            {"number": 10, "title": "fix: existing bug"},
            {"number": 11, "title": "feat: existing feature"},
        ]
        candidates = [
            {"title": "fix: existing bug", "repo": "test/repo"},  # duplicate
            {"title": "docs: new documentation", "repo": "test/repo"},  # unique
        ]
        unique, duplicates = detect_duplicates(
            candidates, "test/repo", existing_issues=existing
        )
        assert len(unique) == 1
        assert len(duplicates) == 1
        assert unique[0]["title"] == "docs: new documentation"
        assert duplicates[0]["_duplicate_match"]["is_duplicate"] is True

    def test_filter_all_unique(self):
        existing = [{"number": 1, "title": "old issue"}]
        candidates = [
            {"title": "new issue 1", "repo": "test/repo"},
            {"title": "new issue 2", "repo": "test/repo"},
        ]
        unique, duplicates = detect_duplicates(
            candidates, "test/repo", existing_issues=existing
        )
        assert len(unique) == 2
        assert len(duplicates) == 0

    def test_filter_all_duplicates(self):
        existing = [
            {"number": 1, "title": "fix: bug"},
            {"number": 2, "title": "feat: feature"},
        ]
        candidates = [
            {"title": "fix: bug", "repo": "test/repo"},
            {"title": "feat: feature", "repo": "test/repo"},
        ]
        unique, duplicates = detect_duplicates(
            candidates, "test/repo", existing_issues=existing
        )
        assert len(unique) == 0
        assert len(duplicates) == 2

    def test_filter_empty_candidates(self):
        unique, duplicates = detect_duplicates([], "test/repo", existing_issues=[])
        assert len(unique) == 0
        assert len(duplicates) == 0


class TestIssueFetching:
    """Tests for issue state handling."""

    def test_fetch_open_issues_forces_open_state(self):
        calls = []

        def runner(repo, state="all"):
            calls.append((repo, state))
            return []

        detector = DuplicateDetector(gh_runner=runner)
        detector.fetch_open_issues("test/repo")

        assert calls == [("test/repo", "open")]

    def test_fetch_issues_passes_state_to_custom_runner(self):
        calls = []

        def runner(repo, state="all"):
            calls.append((repo, state))
            return [
                {"number": 1, "title": "closed issue", "state": "closed", "url": "u"}
            ]

        detector = DuplicateDetector(gh_runner=runner)
        issues = detector.fetch_issues("test/repo", state="closed")

        assert calls == [("test/repo", "closed")]
        assert issues[0]["state"] == "closed"
        assert issues[0]["url"] == "u"

    def test_fetch_issues_rejects_invalid_state(self):
        detector = DuplicateDetector(gh_runner=lambda repo, state="all": [])

        with pytest.raises(ValueError, match="state must be one of"):
            detector.fetch_issues("test/repo", state="merged")


class TestThresholdValidation:
    """Tests for threshold validation."""

    def test_threshold_zero_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            DuplicateDetector(threshold=0.0)

    def test_threshold_negative_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            DuplicateDetector(threshold=-0.5)

    def test_threshold_over_one_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            DuplicateDetector(threshold=1.5)

    def test_threshold_one_works(self):
        detector = DuplicateDetector(threshold=1.0)
        existing = [{"number": 1, "title": "exact match"}]
        result = detector.check_candidate("exact match", existing)
        assert result.is_duplicate is True

    def test_default_threshold(self):
        assert DEFAULT_THRESHOLD == 0.80


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_to_dict(self):
        result = DetectionResult(
            candidate_title="test",
            is_duplicate=True,
            matches=[
                DuplicateMatch(
                    issue_number=1,
                    issue_title="test",
                    similarity=0.95,
                    match_type="near",
                )
            ],
            best_similarity=0.95,
        )
        d = result.to_dict()
        assert d["is_duplicate"] is True
        assert d["best_similarity"] == 0.95
        assert len(d["matches"]) == 1
        assert d["matches"][0]["issue_number"] == 1
