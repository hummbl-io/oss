"""Unit tests for research schemas (Proposals 2 & 3).

Validates claim.schema.json (Atomic Claims & D1->D5 evidence distance tags)
and scep.schema.json (Self-Contained Execution Packets) using
hummbl_cognition.schema_validator.
"""

import json
from pathlib import Path
import pytest

from hummbl_cognition.schema_validator import validate, validate_file

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "src" / "hummbl_cognition" / "schemas"
CLAIM_SCHEMA_PATH = SCHEMAS_DIR / "claim.schema.json"
SCEP_SCHEMA_PATH = SCHEMAS_DIR / "scep.schema.json"


@pytest.fixture
def claim_schema() -> dict:
    return json.loads(CLAIM_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def scep_schema() -> dict:
    return json.loads(SCEP_SCHEMA_PATH.read_text(encoding="utf-8"))


class TestClaimSchemaValidation:
    """Test claim.schema.json validation for Atomic Claims and D1-D5 evidence distance tags."""

    def test_schema_file_exists(self):
        assert CLAIM_SCHEMA_PATH.exists()

    @pytest.mark.parametrize("distance", ["D1", "D2", "D3", "D4", "D5"])
    @pytest.mark.parametrize("risk", ["R0", "R1", "R2", "R3", "R4"])
    def test_valid_claim_all_tags(self, claim_schema: dict, distance: str, risk: str):
        instance = {
            "claim_id": "clm-a1b2c3d4",
            "statement": f"Valid atomic claim under distance {distance} and risk {risk}",
            "evidence_distance": distance,
            "risk_level": risk,
            "assurance_level": "VERIFIED",
            "tags": ["just_meat", "ccl"],
            "rehydration_source": "https://hummbl.dev/evidence/clm-a1b2c3d4",
            "created_at": "2026-07-23T18:00:00Z",
        }
        errors = validate(instance, claim_schema)
        assert errors == []

    def test_invalid_claim_distance(self, claim_schema: dict):
        instance = {
            "claim_id": "clm-a1b2c3d4",
            "statement": "Invalid distance tag claim",
            "evidence_distance": "D6",  # Invalid! Must be D1..D5
            "risk_level": "R1",
        }
        errors = validate(instance, claim_schema)
        assert len(errors) > 0

    def test_invalid_claim_id_pattern(self, claim_schema: dict):
        instance = {
            "claim_id": "invalid-prefix-123",  # Invalid pattern
            "statement": "Bad claim ID prefix",
            "evidence_distance": "D1",
            "risk_level": "R0",
        }
        errors = validate(instance, claim_schema)
        assert len(errors) > 0

    def test_missing_required_fields(self, claim_schema: dict):
        instance = {
            "claim_id": "clm-a1b2c3d4",
            "statement": "Missing distance and risk level",
        }
        errors = validate(instance, claim_schema)
        assert len(errors) > 0


class TestScepSchemaValidation:
    """Test scep.schema.json validation for Self-Contained Execution Packets."""

    def test_schema_file_exists(self):
        assert SCEP_SCHEMA_PATH.exists()

    @pytest.mark.parametrize(
        "regime",
        ["HUMAN", "SUPERVISED", "SEMI_AUTONOMOUS", "LATENCY_TOLERANT", "AI_AUTONOMOUS"],
    )
    def test_valid_scep_control_regimes(self, scep_schema: dict, regime: str):
        instance = {
            "packet_id": "scep-f1e2d3c4",
            "control_regime": regime,
            "agent_id": "gemini",
            "target_environment": "anvil-node-1",
            "latency_budget_ms": 500,
            "payload": {
                "command": "run_probe",
                "arguments": {"probe_id": "p001"},
                "nonce": "n98765",
                "checksum": "sha256:abc123def456",
            },
            "fail_closed_interlock": True,
            "timeout_seconds": 30,
            "created_at": "2026-07-23T18:10:00Z",
        }
        errors = validate(instance, scep_schema)
        assert errors == []

    def test_invalid_scep_control_regime(self, scep_schema: dict):
        instance = {
            "packet_id": "scep-f1e2d3c4",
            "control_regime": "UNGOVERNED",  # Invalid regime
            "agent_id": "gemini",
            "target_environment": "mars-colony-alpha",
            "payload": {"command": "execute"},
            "fail_closed_interlock": True,
        }
        errors = validate(instance, scep_schema)
        assert len(errors) > 0

    def test_scep_missing_interlock(self, scep_schema: dict):
        instance = {
            "packet_id": "scep-f1e2d3c4",
            "control_regime": "LATENCY_TOLERANT",
            "agent_id": "gemini",
            "target_environment": "mars-colony-alpha",
            "payload": {"command": "execute"},
            # Missing fail_closed_interlock!
        }
        errors = validate(instance, scep_schema)
        assert len(errors) > 0


class TestSchemaValidatorFileIntegration:
    """Test file-level schema validation using validate_file helper."""

    def test_validate_file_valid_claim(self, tmp_path: Path):
        claim_file = tmp_path / "valid_claim.json"
        claim_data = {
            "claim_id": "clm-99887766",
            "statement": "File integration test atomic claim",
            "evidence_distance": "D1",
            "risk_level": "R1",
        }
        claim_file.write_text(json.dumps(claim_data), encoding="utf-8")

        is_valid, errors = validate_file(claim_file, CLAIM_SCHEMA_PATH)
        assert is_valid is True
        assert errors == []

    def test_validate_file_valid_scep(self, tmp_path: Path):
        scep_file = tmp_path / "valid_scep.json"
        scep_data = {
            "packet_id": "scep-11223344",
            "control_regime": "AI_AUTONOMOUS",
            "agent_id": "gemini",
            "target_environment": "anvil-node-1",
            "payload": {"command": "ping"},
            "fail_closed_interlock": True,
        }
        scep_file.write_text(json.dumps(scep_data), encoding="utf-8")

        is_valid, errors = validate_file(scep_file, SCEP_SCHEMA_PATH)
        assert is_valid is True
        assert errors == []
