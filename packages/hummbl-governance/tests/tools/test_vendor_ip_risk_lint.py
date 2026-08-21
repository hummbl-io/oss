from tools.vendor_ip_risk_lint import lint_markdown, parse_vendor_rows


REGISTER = "\n".join(
    [
        "# AI Vendor IP Risk Register",
        "",
        "## Vendor register",
        "",
        "| Vendor | Product / tier | Risk | Output ownership | Training default | "
        "Human review / retention | Allowed tiers | Source URLs | Last reviewed | Notes |",
        "|--------|----------------|------|------------------|------------------|"
        "--------------------------|---------------|-------------|---------------|-------|",
        "| Example | Paid API | YELLOW | customer owns output | not trained by default | "
        "bounded | T0,T1; T2/T3 owner approval only | https://example.com/terms | "
        "2026-06-30 | Use paid tier. |",
        "| BadFree | Free tier | RED | unclear | trains by default | unknown | T0,T1 | "
        "REVIEW_REQUIRED | 2026-06-30 | Default RED. |",
        "",
        "## Minimum review fields",
    ]
)


def test_parse_vendor_rows():
    rows = parse_vendor_rows(REGISTER)

    assert len(rows) == 2
    assert rows[0].vendor == "Example"
    assert rows[0].risk == "YELLOW"


def test_valid_register_passes():
    assert lint_markdown(REGISTER) == []


def test_blocks_red_vendor_allowed_for_sensitive_tier():
    markdown = REGISTER.replace("| T0,T1 | REVIEW_REQUIRED |", "| T0,T1,T2 | REVIEW_REQUIRED |")

    findings = lint_markdown(markdown)

    assert [finding.rule for finding in findings] == ["red-sensitive-tier"]


def test_blocks_yellow_sensitive_tier_without_owner_approval():
    markdown = REGISTER.replace("T0,T1; T2/T3 owner approval only", "T0,T1,T2")

    findings = lint_markdown(markdown)

    assert [finding.rule for finding in findings] == [
        "yellow-sensitive-without-approval"
    ]


def test_blocks_missing_source_url():
    markdown = REGISTER.replace("https://example.com/terms", "")

    findings = lint_markdown(markdown)

    assert [finding.rule for finding in findings] == ["missing-source"]


def test_blocks_invalid_review_date():
    markdown = REGISTER.replace("2026-06-30", "2026-99-99", 1)

    findings = lint_markdown(markdown)

    assert [finding.rule for finding in findings] == ["invalid-date"]
