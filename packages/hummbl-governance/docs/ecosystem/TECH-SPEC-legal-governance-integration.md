# Tech Spec: hummbl-legal → hummbl-governance Integration
**Status**: APPROVED — Q2 2026  
**Date**: 2026-05-04  
**Author**: Reuben Bowlby  
**Scope**: hummbl-legal (consumer), hummbl-governance (provider)

---

## 1. Problem statement

hummbl-legal is a governance pilot demonstrating that HUMMBL primitives can govern a legal AI
assistant ("Mike"). The pilot has 10 open blockers (ML-BLOCK-001 through ML-BLOCK-010) and a
current decision of `BLOCK` (no real client data). This spec defines the exact wiring needed to
close the four highest-priority blockers and advance the decision to `SYNTHETIC_ONLY`.

The core integration gap: hummbl-legal validates governance receipts using a hand-rolled
PowerShell script (`test-matter-ai-use-receipt.ps1`) instead of the `SchemaValidator` already
in `hummbl-governance`. Three other gaps are similar: places where hummbl-legal re-implements
something that hummbl-governance already provides.

---

## 2. Current state

### 2.1 hummbl-legal structure

```
hummbl-legal/
├── governance/
│   ├── legal-ai-governance-overview.md
│   ├── legal-ai-control-map.md       (maps ethics obligations → HUMMBL primitives)
│   ├── legal-ai-risk-register.md
│   └── legal-ai-blockers.md          (ML-BLOCK-001 through ML-BLOCK-010)
├── scenarios/
│   ├── scenarios-index.md
│   └── scenario-*.md                 (A1, B2, C1, C2, D1, D2 — not yet run)
├── schemas/
│   └── matter-ai-use-receipt.schema.json
├── tests/
│   └── test-matter-ai-use-receipt.ps1   ← REPLACE THIS
└── README.md
```

### 2.2 hummbl-governance relevant exports

```python
from hummbl_governance import SchemaValidator        # stdlib Draft 2020-12 subset
from hummbl_governance import AuditLog               # append-only JSONL
from hummbl_governance import KillSwitch             # 4-mode halt
from hummbl_governance import DelegationToken        # HMAC-SHA256 scoped tokens
from hummbl_governance import IdentityRegistry       # agent name validation
```

### 2.3 Open blockers relevant to this spec

| Blocker | Description | Priority |
|---------|-------------|----------|
| ML-BLOCK-001 | Content logging: raw user query content captured in receipts | HIGH |
| ML-BLOCK-003 | API key for Mike stored in .env — not in Keychain or vault | HIGH |
| ML-BLOCK-006 | Receipt validator is PowerShell — not portable, not CI-friendly | MEDIUM |
| ML-BLOCK-008 | No Python test suite — scenarios run manually | MEDIUM |

---

## 3. Integration design

### 3.1 Replace PowerShell validator with Python SchemaValidator

**Current** (`tests/test-matter-ai-use-receipt.ps1`):
```powershell
$schema = Get-Content "schemas/matter-ai-use-receipt.schema.json" | ConvertFrom-Json
$receipt = Get-Content "fixtures/sample-receipt.json" | ConvertFrom-Json
# hand-rolled field checks...
```

**Target** (`tests/test_matter_ai_use_receipt.py`):
```python
import json
import pytest
from hummbl_governance import SchemaValidator

SCHEMA_PATH = "schemas/matter-ai-use-receipt.schema.json"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)

def test_valid_receipt(schema):
    receipt = {
        "matter_id": "MATTER-2026-001",
        "timestamp": "2026-05-04T12:00:00Z",
        "agent_id": "MIKE",
        "action_type": "DRAFT_REVIEW",
        "authorization_level": 2,
        "output_schema": "legal-draft-v1",
        "content_hash": "abc123",          # hash of content, NOT content itself
        "attorney_review_required": True,
    }
    errors = SchemaValidator.validate(receipt, schema)
    assert errors == []

def test_missing_required_field(schema):
    errors = SchemaValidator.validate({"timestamp": "2026-05-04T12:00:00Z"}, schema)
    assert any("matter_id" in e for e in errors)

def test_content_not_logged(schema):
    """ML-BLOCK-001: receipts MUST NOT contain raw content fields."""
    receipt_with_content = {
        "matter_id": "MATTER-2026-001",
        "user_query": "What is the statute of limitations?",  # FORBIDDEN
        ...
    }
    errors = SchemaValidator.validate(receipt_with_content, schema)
    assert any("user_query" in e for e in errors)
```

**Why this closes ML-BLOCK-006**: Python test runs in CI (`pytest tests/`). No PowerShell
required. The `SchemaValidator` can enforce the `additionalProperties: false` rule that
prevents `user_query` from appearing — closing ML-BLOCK-001 at the schema layer.

### 3.2 Schema update to close ML-BLOCK-001 (content logging)

**Current** `matter-ai-use-receipt.schema.json` — does not prohibit unknown fields.

**Target** — add `"additionalProperties": false` to enforce content exclusion:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "matter-ai-use-receipt.schema.json",
  "title": "MatterAIUseReceipt",
  "type": "object",
  "required": [
    "matter_id", "timestamp", "agent_id", "action_type",
    "authorization_level", "output_schema", "content_hash",
    "attorney_review_required"
  ],
  "additionalProperties": false,
  "properties": {
    "matter_id":               { "type": "string" },
    "timestamp":               { "type": "string", "format": "date-time" },
    "agent_id":                { "type": "string" },
    "action_type":             { "type": "string", "enum": ["DRAFT_REVIEW", "RESEARCH", "CITE_CHECK", "FORM_FILL"] },
    "authorization_level":     { "type": "integer", "minimum": 0, "maximum": 4 },
    "output_schema":           { "type": "string" },
    "content_hash":            { "type": "string", "minLength": 64, "maxLength": 64 },
    "attorney_review_required":{ "type": "boolean" }
  }
}
```

**Key change**: `additionalProperties: false` — any receipt containing `user_query`,
`case_facts`, `client_name`, or any other content field will FAIL validation. This enforces
content-free receipts at the schema layer without requiring runtime logic.

hummbl-governance v1.2.2 implements `additionalProperties` from Draft 2020-12.
**Note on `hummbl-governance` SchemaValidator support**: The `SchemaValidator` in
`hummbl-governance` should be verified against `tests/test_schema_validator.py` before relying on this.

### 3.3 API key management — close ML-BLOCK-003

**Current**: Mike's API key is stored in `.env` file in the repo root.

**Target**: API key loaded from environment variable only. `.env` in `.gitignore`. 
`mike_config.py` (to be written) loads from `os.environ["MIKE_API_KEY"]` — raises
`EnvironmentError` if unset, never falls back to a default.

```python
# mike_config.py
import os

def get_api_key() -> str:
    key = os.environ.get("MIKE_API_KEY")
    if not key:
        raise EnvironmentError(
            "MIKE_API_KEY environment variable is not set. "
            "Store the key in your shell profile or a secrets manager. "
            "Never commit API keys to the repository."
        )
    return key
```

**CI**: Add `MIKE_API_KEY` to CI secrets. Add a `.gitignore` entry for `.env`.
Add a CI check (`grep -r "MIKE_API_KEY\s*=" . --include="*.py" | grep -v os.environ`) to
detect hardcoded keys.

### 3.4 Python test suite for scenarios — close ML-BLOCK-008

Create `tests/test_scenarios.py` covering synthetic-data scenarios A1, B2, C1 (these do not
require Mike to be deployed — they validate the governance wiring with mock AI outputs).

**Scenario A1** (Draft Review — attorney review required):
```python
def test_scenario_a1_draft_review_requires_attorney_sign_off():
    """
    Scenario A1: Mike reviews a contract draft.
    Expected: authorization_level=2, attorney_review_required=True,
    receipt validates against schema, AuditLog entry created.
    """
    receipt = build_mock_receipt(
        action_type="DRAFT_REVIEW",
        authorization_level=2,
        attorney_review_required=True,
    )
    errors = SchemaValidator.validate(receipt, load_schema())
    assert errors == []

    audit = AuditLog(log_path=tmp_audit_path)
    audit.log("SCHEMA_VALIDATE_PASS", agent="MIKE", details={"receipt_id": receipt["matter_id"]})
    assert audit.last_entry()["event_type"] == "SCHEMA_VALIDATE_PASS"
```

**Scenario B2** (Research — no client content in output):
```python
def test_scenario_b2_research_output_contains_no_client_content():
    """
    Scenario B2: Mike produces a research memo.
    Expected: receipt has content_hash, not content. additionalProperties: false enforced.
    """
    receipt_with_content = build_mock_receipt(action_type="RESEARCH")
    receipt_with_content["memo_text"] = "Client told me..."  # inject forbidden field
    
    errors = SchemaValidator.validate(receipt_with_content, load_schema())
    assert errors  # additionalProperties: false rejects memo_text
```

**Scenario C1** (Kill switch engagement):
```python
def test_scenario_c1_kill_switch_halts_mike():
    """
    Scenario C1: Kill switch engaged during Mike session.
    Expected: KillSwitch.engage() → HALT_ALL; no further Mike receipts accepted.
    """
    ks = KillSwitch()
    ks.engage(mode="HALT_ALL", reason="Test — scenario C1")
    assert ks.is_halted()
    
    # Attempting to validate a receipt while halted should raise
    with pytest.raises(RuntimeError, match="HALT_ALL"):
        validate_with_kill_switch_check(build_mock_receipt(), ks)
```

---

## 4. Provider evidence gate (partial — ML-BLOCK-002)

Before using Mike with real client data, HUMMBL must verify that the underlying AI provider
(Anthropic) offers:
- Zero data retention (ZDR) or equivalent
- A Data Processing Agreement (DPA)
- API region selection (US-only data processing)

**Blocking check** (to be added to `governance/provider-evidence.md`):

| Control | Anthropic (as of 2026-05) | Status |
|---------|--------------------------|--------|
| ZDR available | Yes — API tier | ❓ UNVERIFIED — see `docs/trackers/UNVERIFIED-CLAIMS.md` |
| DPA available | Yes — Enterprise | ❓ UNVERIFIED — countersigned DPA not on file |
| Region selection | Yes — US/EU | ❓ UNVERIFIED — no contractual routing clause confirmed |
| Prompt data training opt-out | Yes — API usage | ❓ UNVERIFIED — standard API ToS assumed but not verified |
| Incident notification SLA | 72 hours | ❓ UNVERIFIED — no SLA clause in current agreement |

> **Note**: All five rows above are listed as open items in `docs/trackers/UNVERIFIED-CLAIMS.md`.
> Do not treat this table as evidence. The `✅` markers were premature. Attach actual evidence
> artifacts (DPA, ZDR confirmation, SLA clause) before advancing from SYNTHETIC_ONLY.

**Decision after evidence gate**: SYNTHETIC_ONLY → CONTROLLED_PILOT (requires attorney sign-off
on DPA terms and bar compliance review — ML-BLOCK-004, ML-BLOCK-005).

---

## 5. Migration path from PowerShell to Python

| Step | Action | Closes |
|------|--------|--------|
| 1 | Update `matter-ai-use-receipt.schema.json` (add `additionalProperties: false`) | ML-BLOCK-001 |
| 2 | Write `mike_config.py` (env var only) + `.gitignore` `.env` | ML-BLOCK-003 |
| 3 | Write `tests/test_matter_ai_use_receipt.py` (replaces PS1) | ML-BLOCK-006 |
| 4 | Write `tests/test_scenarios.py` (A1, B2, C1) | ML-BLOCK-008 |
| 5 | Delete `tests/test-matter-ai-use-receipt.ps1` | ML-BLOCK-006 |
| 6 | Commit `governance/provider-evidence.md` with Anthropic evidence | ML-BLOCK-002 |
| 7 | Update `legal-ai-blockers.md` to mark ML-BLOCK-001/002/003/006/008 CLOSED | — |
| 8 | Update decision from `BLOCK` to `SYNTHETIC_ONLY` | — |

---

## 6. Import contract

hummbl-legal imports from hummbl-governance:

```python
from hummbl_governance import SchemaValidator   # v1.2.0+ ✅
from hummbl_governance import AuditLog          # v1.2.0+ ✅
from hummbl_governance import KillSwitch        # v1.2.0+ ✅
from hummbl_governance import DelegationToken   # v1.2.0+ ✅
```

**Version pin** in `pyproject.toml` (or `requirements.txt`):
```text
hummbl-governance>=1.2.0,<2.0.0
```

Do NOT pin to an exact version — governance patches must be picked up automatically.

---

## 7. Tests to add to hummbl-governance

The following integration tests belong in `hummbl-governance/tests/` to verify that
legal-style receipts validate correctly:

```python
# tests/test_legal_receipt_integration.py
def test_legal_receipt_additional_properties_false():
    """SchemaValidator enforces additionalProperties: false."""
    schema = {"type": "object", "additionalProperties": False, "properties": {"id": {"type": "string"}}}
    errors = SchemaValidator.validate({"id": "x", "forbidden_field": "content"}, schema)
    assert errors  # forbidden_field rejected by additionalProperties: false
```

Confirm this test passes against v1.2.2 before wiring hummbl-legal.

---

## 8. Acceptance criteria

- [ ] `tests/test_matter_ai_use_receipt.py` exists, passes with `pytest`
- [ ] `tests/test-matter-ai-use-receipt.ps1` deleted
- [ ] `schemas/matter-ai-use-receipt.schema.json` has `additionalProperties: false`
- [ ] `mike_config.py` uses env var only (no `.env` file)
- [ ] `.env` in `.gitignore`
- [ ] `tests/test_scenarios.py` covers A1, B2, C1 with mock data
- [ ] `governance/provider-evidence.md` committed with Anthropic evidence table
- [ ] `legal-ai-blockers.md` marks ML-BLOCK-001/002/003/006/008 CLOSED
- [ ] Decision updated from `BLOCK` to `SYNTHETIC_ONLY`
- [ ] `hummbl-governance` `test_legal_receipt_integration.py` test added and passing

---

## 9. Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| SchemaValidator `additionalProperties` not implemented in v1.2.2 | Verify with test before wiring; patch governance if needed |
| AuditLog path conflicts with hummbl-governance bus | hummbl-legal uses its own `_state/legal-audit.jsonl` path |
| Scenario test fixtures contain accidental real data | All fixtures in `tests/fixtures/synthetic/` — CI scan for real names/addresses |
| ML-BLOCK-004 (bar compliance) blocks CONTROLLED_PILOT | This spec targets SYNTHETIC_ONLY — bar compliance is a separate work stream |
