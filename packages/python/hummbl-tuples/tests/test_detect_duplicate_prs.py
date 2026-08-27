#!/usr/bin/env python3
"""Tests for duplicate PR detection branch-name coverage."""

from __future__ import annotations

from scripts.detect_duplicate_prs import (
    classify_branch,
    find_duplicates,
    parse_issue_number,
)


def test_parse_issue_number_supports_docs_and_fix_branches():
    assert parse_issue_number("docs/codex/issue-12-draft-pr") == 12
    assert parse_issue_number("fix/devin/issue-13-claim-collector") == 13
    assert parse_issue_number("feat/devin/issue-14-hash-chain") == 14


def test_parse_issue_number_ignores_non_issue_branches():
    assert parse_issue_number("docs/codex/workflow-update") is None
    assert parse_issue_number("feat/devin/noissue-15-update") is None


def test_classify_branch_uses_issue_naming():
    assert classify_branch("docs/codex/issue-21-draft-pr") == "draft"
    assert classify_branch("fix/devin/issue-21-fix-cascade") == "candidate"
    assert classify_branch("feature/devin/workflow-pass") == "other"


def test_find_duplicates_detects_draft_and_candidate_for_same_issue():
    prs = [
        {"number": 1001, "title": "docs branch", "headRefName": "docs/codex/issue-31-draft-pr"},
        {"number": 1002, "title": "fix branch", "headRefName": "fix/devin/issue-31-fix"},
    ]
    duplicates = find_duplicates(prs)
    assert len(duplicates) == 1
    assert duplicates[0]["issue"] == 31
    assert len(duplicates[0]["draft_prs"]) == 1
    assert duplicates[0]["draft_prs"][0]["number"] == 1001
    assert len(duplicates[0]["feat_prs"]) == 1
    assert duplicates[0]["feat_prs"][0]["number"] == 1002


def test_find_duplicates_flags_multiple_drafts():
    prs = [
        {"number": 1101, "title": "first draft", "headRefName": "fix/devin/issue-32-draft-pr"},
        {"number": 1102, "title": "second draft", "headRefName": "docs/codex/issue-32-draft-pr"},
    ]
    duplicates = find_duplicates(prs)
    assert len(duplicates) == 1
    assert duplicates[0]["issue"] == 32
    assert len(duplicates[0]["draft_prs"]) == 2
    assert len(duplicates[0]["feat_prs"]) == 0


def test_find_duplicates_no_false_positive_on_unrelated_branches():
    prs = [
        {"number": 1201, "title": "plain docs", "headRefName": "docs/codex/workflow-notes"},
        {"number": 1202, "title": "feat branch", "headRefName": "fix/devin/issue-33"},
    ]
    duplicates = find_duplicates(prs)
    assert duplicates == []
