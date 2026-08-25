from tools.provenance_lint import lint_identity_text, lint_text


def test_allows_normal_commit_message():
    assert lint_text("docs: update governance standard\n\nHuman-authored note.") == []


def test_blocks_ai_coauthor_trailer():
    findings = lint_text(
        "docs: update standard\n\nCo-authored-by: Codex <codex@example.com>"
    )

    assert [finding.rule for finding in findings] == ["ai-coauthor-trailer"]


def test_blocks_generated_by_trailer():
    findings = lint_text("docs: update standard\n\nGenerated-by: Claude")

    assert [finding.rule for finding in findings] == ["generated-by-trailer"]


def test_blocks_ai_credit_line():
    findings = lint_text("docs: update standard\n\nImplemented by Devin")

    assert [finding.rule for finding in findings] == ["ai-credit-line"]


def test_blocks_ai_author_identity():
    findings = lint_identity_text(
        "Claude (agent) <claude@agents.hummbl.io> 1782843919 -0400",
        label="author",
    )

    # Blocklist catches the AI name; allowlist also catches it (not allowlisted).
    rules = [finding.rule for finding in findings]
    assert "ai-author-identity" in rules
    assert "identity-not-allowlisted-author" in rules


def test_allows_hummbl_io_identity():
    findings = lint_identity_text(
        "hummbl-io <noreply@hummbl.io> 1782843919 -0400",
        label="author",
    )

    assert findings == []


def test_allows_hummbl_dev_identity():
    findings = lint_identity_text(
        "hummbl-io <noreply@hummbl.io> 1782843919 -0400",
        label="author",
    )

    assert findings == []


def test_allows_hummbl_email_domain():
    findings = lint_identity_text(
        "Reuben Bowlby <reuben@hummbl.io> 1782843919 -0400",
        label="author",
    )

    assert findings == []


def test_blocks_non_hummbl_identity():
    """A human identity outside the HUMMBL org is still caught by
    the allowlist (deterministic, closed by default)."""
    findings = lint_identity_text(
        "Contributor <contributor@example.com> 1782843919 -0400",
        label="committer",
    )

    rules = [finding.rule for finding in findings]
    assert "identity-not-allowlisted-committer" in rules
