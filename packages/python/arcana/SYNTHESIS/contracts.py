"""Contracts for the SYNTHESIS sibling module.

SYNTHESIS is the runtime orchestration surface for ARCANA run pipelines: it
selects lenses, sequences stages, routes work, and assembles receipt bundles.
It does not generate content, score artifacts, or publish -- those belong to
ARCANA/POIESIS, PAIDEIA, and RELEASE respectively.

Status: RUNTIME-DEBUT. The first executable workflow (paideia-review) has
landed in SYNTHESIS/runtime.py; broader orchestration (lens/stage
selection, parallel dispatch, run-state monitoring) remains ROADMAP
(docs/platform-set.md §8). These contracts are the versioned boundary for
the module.
"""

MODULE_NAME = "SYNTHESIS"
MODULE_SURFACE = "SYNTHESIS"
MODULE_VERSION = "v0.1-draft"
MODULE_STATUS = "RUNTIME-DEBUT"
MODULE_ROLE = "runtime-orchestration"
MODULE_PURPOSE = (
    "Runtime orchestration surface for ARCANA run pipelines: lens/stage "
    "selection, sequencing, and receipt assembly. First executable "
    "workflow (paideia-review) landed in SYNTHESIS/runtime.py; broader "
    "orchestration still ROADMAP."
)
MODULE_BOUNDARY = (
    "SYNTHESIS orchestrates the run pipeline and routes work; it does not "
    "generate content, score artifacts, or publish."
)
MODULE_CONTRACT_FOCUS = (
    "run orchestration, lens/stage dispatch, run-state monitoring, and "
    "receipt bundle assembly across sibling modules."
)
MODULE_CONTRACT_TERMS = (
    "run-orchestration",
    "stage-dispatch",
    "receipt-assembly",
)

# Canonical orchestration roles. Each is a runnable lens persona in
# scripts/lenses.json (school 'SYNTHESIS / ...'). Drift between this roster
# and lenses.json is caught by test_synthesis_roles_have_prompts.
SYNTHESIS_ROLES = {
    "conductor": (
        "Orchestrates the full run: selects lenses, sequences stages, and "
        "assembles the article family from per-lens outputs."
    ),
    "dispatcher": (
        "Routes sub-tasks to the right lens or stage and manages "
        "parallelism, dependencies, and the reason-act separation."
    ),
    "monitor": (
        "Tracks run state, surfaces drift between plan and execution, and "
        "emits per-step receipts for EVIDENCE."
    ),
}
