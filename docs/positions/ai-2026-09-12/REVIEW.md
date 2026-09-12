# Review and refresh the proposed baseline

Read the numbered positions first. For a factual clause, resolve its claim ID
through [claims.json](claims.json), then inspect the public source note, exact
model/version, date, evaluator, population and limitations. Publisher statements
remain attributed reports unless independent evidence supports a stronger status.

The public package contains proposed positions, source citations and a commercial
hypothesis. It does not certify AGI/ASI, general RSI, license conformance, legal
compliance, customer ROI, or successful company adoption.

From the repository root, using Python 3.11 or newer:

```bash
python3 tools/validate_ai_positions.py
python3 -m unittest discover -s tools -p test_validate_ai_positions.py
git diff --check
```

These are local consistency checks: references, coverage, dates, links and
illustrative arithmetic. They do not establish source truth or publication of
a changed website. The broader repository CI remains separate from semantic review.

Before adoption, confirm that proposed judgments express the intended company
position. Before reusing volatile factual wording, refresh the primary source.
Preserve claim IDs and record changed scope rather than silently replacing a
forecast or comparing incompatible evaluation versions. A new source may
strengthen, narrow or contradict a position; none of those outcomes is assumed.
