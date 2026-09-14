"""Contracts for the CANON sibling module.

CANON is the public artifact registry and policy baseline mirror: the
canonical record of published artifacts and the normative baseline they are
measured against. It indexes and mirrors; it does not generate, score, or
gate publication (those belong to ARCANA/POIESIS, PAIDEIA, and RELEASE).

Status: ROADMAP (docs/platform-set.md §8 -- intentionally out of scope this
phase). These contracts are the scaffold so the module has a versioned
boundary before any registry behavior lands.
"""

MODULE_NAME = "CANON"
MODULE_SURFACE = "CANON"
MODULE_VERSION = "v0.1-draft"
MODULE_STATUS = "ROADMAP"
MODULE_ROLE = "artifact-registry"
MODULE_PURPOSE = (
    "Public artifact registry and policy baseline mirror: the canonical "
    "record of published artifacts and the normative baseline."
)
MODULE_BOUNDARY = (
    "CANON indexes and mirrors; it does not generate content, score "
    "artifacts, or gate publication (that is RELEASE)."
)
MODULE_CONTRACT_FOCUS = (
    "artifact registration and indexing, policy baseline mirroring, and "
    "provenance/lineage tracking for published artifacts."
)
MODULE_CONTRACT_TERMS = (
    "artifact-registry",
    "baseline-mirror",
    "provenance-tracking",
)

# Canonical registry stages. Each is a runnable lens persona in
# scripts/lenses.json (school 'CANON / ...'). Drift between this roster
# and lenses.json is caught by test_canon_stages_have_prompts.
CANON_STAGES = {
    "registrar": (
        "Indexes and registers published artifacts as the canonical, "
        "deduplicated record."
    ),
    "baseline": (
        "Mirrors the policy baseline (NOMOS standards, PAIDEIA rubrics) as "
        "the normative reference artifacts are measured against."
    ),
    "provenance": (
        "Tracks lineage and provenance of artifacts: what generated what, "
        "from which inputs, under which contract version."
    ),
}
