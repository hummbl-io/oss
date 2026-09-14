"""Tests for scripts/ecosystem_contracts canonical contract values."""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
# Standalone runner (python tests/test_ecosystem_contracts.py) needs both
# scripts/ and ROOT on sys.path; under pytest, conftest.py handles this.
for _p in (str(SCRIPTS), str(ROOT), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ecosystem_contracts as ec  # noqa: E402
import print_ecosystem_manifest as pem  # noqa: E402


def test_paideia_axes_order():
    assert ec.PAIDEIA_AXES == ("M", "D", "E", "V", "C", "L", "S", "P", "A", "Em")
    assert ec.PAIDEIA_AXIS_NAMES["Em"] == "EMOTION"
    assert ec.PAIDEIA_VERSION == "v0.2-draft"
    assert ec.PAIDEIA_AXES_V0_1 == ("M", "D", "E", "V", "C", "L", "S", "P", "A")
    assert set(ec.PAIDEIA_INTENT_VALUES) == {"required", "deliberate_absent", "n_a"}
    assert ec.PAIDEIA_DEFAULT_INTENT == "required"


def test_praxis_and_poiesis_counts():
    assert len(ec.PRAXIS_ARCHETYPES) == 11
    assert len(ec.POIESIS_STAGES) == 5


def test_sibling_modules_have_contract_metadata():
    assert set(ec.SIBLING_NAMES) == {
        "NOMOS", "EVIDENCE", "RELEASE", "LINGUA", "SYNTHESIS", "CANON",
    }
    assert len(ec.SIBLING_NAMES) == 6


def _load_contract_module(sibling: str) -> types.ModuleType:
    contract_path = ROOT / sibling / "contracts.py"
    assert contract_path.exists(), f"missing contract module: {contract_path}"
    spec = importlib.util.spec_from_file_location(f"arcana_sibling_{sibling.lower()}", contract_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_sibling_contract_files_and_headers():
    for sibling in ec.SIBLING_NAMES:
        module = _load_contract_module(sibling)
        assert hasattr(module, "MODULE_NAME")
        assert module.MODULE_NAME == sibling
        assert isinstance(module.MODULE_VERSION, str)
        assert module.MODULE_VERSION.startswith("v")
        expected = ec.sibling_contract_spec(sibling)
        assert module.MODULE_VERSION == expected["version"]
        assert hasattr(module, "MODULE_STATUS")
        assert module.MODULE_STATUS == expected["status"]
        assert hasattr(module, "MODULE_PURPOSE")
        assert isinstance(module.MODULE_PURPOSE, str)
        assert module.MODULE_PURPOSE == expected["purpose"]
        assert hasattr(module, "MODULE_SURFACE")
        assert module.MODULE_SURFACE == sibling
        assert hasattr(module, "MODULE_BOUNDARY")
        assert isinstance(module.MODULE_BOUNDARY, str)
        assert module.MODULE_BOUNDARY == expected["boundary"]
        assert hasattr(module, "MODULE_CONTRACT_TERMS")
        assert module.MODULE_CONTRACT_TERMS == expected["terms"]


def test_sibling_packages_import_contracts():
    for sibling in ec.SIBLING_NAMES:
        module = importlib.import_module(f"{sibling}.contracts")
        assert module.MODULE_NAME == sibling


def test_sibling_readmes_reference_contracts():
    for sibling in ec.SIBLING_NAMES:
        expected = ec.sibling_contract_spec(sibling)
        readme_path = ROOT / sibling / "README.md"
        assert readme_path.exists(), f"missing README: {readme_path}"
        text = readme_path.read_text(encoding="utf-8")
        assert f"# {sibling}" in text
        assert f"**Status**: {expected['status']}" in text
        assert f"- Version: `{expected['version']}`" in text
        assert f"- Surface: `{sibling}/contracts.py`" in text


def test_sibling_manifest_is_json_serializable():
    manifest = ec.sibling_contract_manifest()
    assert tuple(manifest) == ec.SIBLING_NAMES
    for sibling, entry in manifest.items():
        assert entry["name"] == sibling
        assert entry["contract_path"] == f"{sibling}/contracts.py"
        assert entry["import_name"] == f"{sibling}.contracts"
        assert entry["terms"] == ec.sibling_contract_spec(sibling)["terms"]
    json.dumps(manifest)


def test_docs_index_links_platform_and_roadmap():
    docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "[platform-set.md](platform-set.md)" in docs_index
    assert "[ecosystem-roadmap.md](ecosystem-roadmap.md)" in docs_index
    assert "[review-packet-ecosystem-contracts.md](review-packet-ecosystem-contracts.md)" in docs_index


def test_platform_set_lists_manifest_and_release_gate():
    platform_set = (ROOT / "docs" / "platform-set.md").read_text(encoding="utf-8")
    assert "`scripts/print_ecosystem_manifest.py`" in platform_set
    assert "`RELEASE/gate.py`" in platform_set


def test_roadmap_mentions_all_siblings():
    roadmap = (ROOT / "docs" / "ecosystem-roadmap.md").read_text(encoding="utf-8")
    for sibling in ec.SIBLING_NAMES:
        assert sibling in roadmap


def test_manifest_cli_uses_canonical_manifest():
    manifest = pem.build_manifest()
    assert manifest["schema_version"] == "arcana-ecosystem-manifest-v0.1"
    assert manifest["sibling_modules"] == ec.sibling_contract_manifest()


def test_praxis_version_matches_version_shape():
    assert ec.PRAXIS_VERSION.startswith("v")
    assert ec.POIESIS_VERSION.startswith("v")


def test_paideia_signature_order_and_shape():
    vec = {axis: idx for idx, axis in enumerate(ec.PAIDEIA_AXES, start=1)}
    assert ec.paideia_signature(vec) == "1-2-3-4-5-6-7-8-9-10"
    # v0.1 legacy signature helper preserves the 9-axis order
    vec_v01 = {axis: idx for idx, axis in enumerate(ec.PAIDEIA_AXES_V0_1, start=1)}
    assert ec.paideia_signature_v0_1(vec_v01) == "1-2-3-4-5-6-7-8-9"


def test_canonical_notes_include_keys():
    praxis_note = ec.canonical_praxis_note()
    poiesis_note = ec.canonical_poiesis_note()
    for name in ec.PRAXIS_ARCHETYPES:
        assert name in praxis_note
    for name in ec.POIESIS_STAGES:
        assert name in poiesis_note


def test_prawn_stage_count_and_order():
    assert len(ec.PRAWN_STAGES) == 5
    # Canonical order matters — it's a cycle, not a set
    assert tuple(ec.PRAWN_STAGES.keys()) == (
        "perceive", "reason", "account", "work", "notate",
    )


def test_prawn_version_shape():
    assert ec.PRAWN_VERSION.startswith("v")


def test_prawn_account_shapes():
    # checkpoint is the default (Ostrom); gate is the exception (high-irreversibility)
    assert tuple(ec.PRAWN_ACCOUNT_SHAPES.keys()) == ("checkpoint", "gate")
    # gate maps to HITL, checkpoint maps to HOTL (per models.py oversight modes)
    assert "HITL" in ec.PRAWN_ACCOUNT_SHAPES["gate"]
    assert "HOTL" in ec.PRAWN_ACCOUNT_SHAPES["checkpoint"]
    # pressure-test finding: account must include material stake, not narration alone
    assert "stake" in ec.PRAWN_STAGES["account"].lower()


def test_prawn_canonical_notes_include_keys():
    prawn_note = ec.canonical_prawn_note()
    account_note = ec.canonical_prawn_account_note()
    for name in ec.PRAWN_STAGES:
        assert name in prawn_note
    for name in ec.PRAWN_ACCOUNT_SHAPES:
        assert name in account_note


def test_prawn_pressure_test_amendments_present():
    """Guard against silent regression of the 5 pressure-test amendments
    (docs/pressure-test-prawn-account.md). Each amendment is earned by a
    specific ARCANA lens pressure-testing the account stage."""
    account_desc = ec.PRAWN_STAGES["account"].lower()
    checkpoint_desc = ec.PRAWN_ACCOUNT_SHAPES["checkpoint"].lower()
    gate_desc = ec.PRAWN_ACCOUNT_SHAPES["gate"].lower()

    # 1. Foucault: theater detection — account must mention blocking/suspicion
    assert "suspect" in account_desc or "blocked" in account_desc, (
        "Foucault amendment missing: account stage must mention theater detection"
    )

    # 2. Yarvin: material stake — account must require a forfeited stake
    assert "stake" in account_desc, (
        "Yarvin amendment missing: account stage must require material stake"
    )
    assert "forfeit" in account_desc, (
        "Yarvin amendment missing: stake must be forfeited on misaccounting"
    )

    # 3. Schmitt: sovereign decision — the contract comment must disclose the
    #    EMERGENCY bypass asymmetry. Check the module source for the disclosure.
    import inspect
    source = inspect.getsource(ec)
    assert "sovereign" in source.lower(), (
        "Schmitt amendment missing: contract must disclose sovereign decision for EMERGENCY bypass"
    )

    # 4. Ostrom: checkpoint is the default — must be first in the ordering
    assert next(iter(ec.PRAWN_ACCOUNT_SHAPES.keys())) == "checkpoint", (
        "Ostrom amendment missing: checkpoint must be the default (first) shape"
    )
    assert "default" in checkpoint_desc, (
        "Ostrom amendment missing: checkpoint must be labeled as default"
    )
    assert "exception" in gate_desc, (
        "Ostrom amendment missing: gate must be labeled as exception"
    )

    # 5. Ashby: variety gap / tunable sensitivity — gate must mention tunability
    assert "tunable" in gate_desc or "sensitivity" in gate_desc, (
        "Ashby amendment missing: gate must disclose tunable sensitivity / variety gap"
    )


def test_prawn_work_pressure_test_amendments_present():
    """Guard against silent regression of the 3 work-stage pressure-test
    amendments (docs/pressure-test-prawn-work.md)."""
    work_desc = ec.PRAWN_STAGES["work"].lower()
    notate_desc = ec.PRAWN_STAGES["notate"].lower()

    # 1. Schneier: internal privilege separation (write-authorization vs write-execution)
    assert "authorization" in work_desc, (
        "Schneier amendment missing: work must mention write-authorization"
    )
    assert "execution" in work_desc, (
        "Schneier amendment missing: work must mention write-execution"
    )

    # 2. Ashby: variety deficit + feedback loop as recovery mechanism
    assert "variety" in work_desc, (
        "Ashby amendment missing: work must disclose variety deficit"
    )
    assert "feedback" in work_desc, (
        "Ashby amendment missing: work must name feedback loop as variety-recovery"
    )
    assert "latency" in work_desc, (
        "Ashby amendment missing: work must mention feedback latency vs irreversibility"
    )

    # 3. Illich: refrain-path — notate must record refrain-decisions
    assert "refrain" in notate_desc, (
        "Illich amendment missing: notate must mention refrain-decisions"
    )
    assert "complete" in notate_desc, (
        "Illich amendment missing: notate must mark refrain as a complete cycle"
    )


def _run_standalone():
    import inspect

    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
            if "tmp_path" in inspect.signature(fn).parameters:
                # no tmp_path fixtures needed today
                fn()
            else:
                fn()
            print(f"OK    {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
