# Compliance Calendar

Scheduled governance and security review tasks for hummbl-governance.

## Quarterly Reviews

| Task | Schedule | Workflow | Owner | Issue |
|------|----------|----------|-------|-------|
| nosec suppression audit | Q1/Q2/Q3/Q4 (Jan 1, Apr 1, Jul 1, Oct 1) | `.github/workflows/nosec-audit.yml` | security steward | #137 |

## Review Process

### nosec suppression audit

1. **Automated scan**: The `nosec-audit` workflow runs quarterly on schedule, scanning all production `.py` files under `hummbl_governance/` for `# nosec` comments.
2. **Justification check**: Each nosec must have an inline justification (rule code + reason). Unjustified suppressions cause the workflow to fail and auto-create a GitHub issue.
3. **Registry artifact**: The workflow uploads `docs/nosec-registry.json` as a 90-day-retained artifact for audit trail.
4. **Manual review**: The security steward reviews each suppression quarterly to verify:
   - The justification is still valid (code context hasn't changed)
   - The Bandit rule is still a false positive (not a real vulnerability)
   - The suppression cannot be replaced by a Bandit config skip (structural false positives)
5. **Structural skip consideration**: If a rule is suppressed multiple times in the same file for the same reason (e.g., B311 in `statistical_framework.py`), consider adding it to `[tool.bandit]` skips in `pyproject.toml` instead of inline nosec comments.

## Adding New Calendar Entries

To add a new scheduled review:
1. Create a workflow in `.github/workflows/` with a `schedule` trigger
2. Add an entry to the Quarterly Reviews table above
3. Document the review process in this file
4. Reference the governing issue or ADR
