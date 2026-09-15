"""Tests for hummbl_evidence.evidence_state.

Ported from hummbl-observatory's evidence_state module to verify the
shared primitive preserves the P1 constraint: absence renders as unknown,
never clean.
"""

import pytest

from hummbl_evidence.evidence_state import EvidenceState, render_health


class TestEvidenceState:
    def test_four_values(self):
        assert EvidenceState.SUFFICIENT.value == "sufficient"
        assert EvidenceState.PARTIAL.value == "partial"
        assert EvidenceState.ABSENT.value == "absent"
        assert EvidenceState.CONTRADICTORY.value == "contradictory"

    def test_is_str_enum(self):
        assert isinstance(EvidenceState.SUFFICIENT, str)
        assert EvidenceState.SUFFICIENT == "sufficient"


class TestRenderHealth:
    def test_sufficient_renders_as_supported(self):
        assert render_health(EvidenceState.SUFFICIENT) == "supported"

    def test_partial_renders_as_partial(self):
        assert render_health(EvidenceState.PARTIAL) == "partial"

    def test_absent_renders_as_unknown_never_clean(self):
        """ABSENT must render as 'unknown', never 'clean' or 'healthy'."""
        label = render_health(EvidenceState.ABSENT)
        assert label == "unknown"
        assert label != "clean"
        assert label != "healthy"

    def test_contradictory_renders_as_contested_never_clean(self):
        """CONTRADICTORY must render as 'contested', never 'clean' or 'healthy'."""
        label = render_health(EvidenceState.CONTRADICTORY)
        assert label == "contested"
        assert label != "clean"
        assert label != "healthy"

    def test_non_evidence_state_raises_type_error(self):
        with pytest.raises(TypeError, match="expected EvidenceState"):
            render_health("sufficient")  # type: ignore[arg-type]

    def test_none_raises_type_error(self):
        with pytest.raises(TypeError, match="expected EvidenceState"):
            render_health(None)  # type: ignore[arg-type]
