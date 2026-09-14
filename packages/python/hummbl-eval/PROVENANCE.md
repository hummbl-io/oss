# PROVENANCE — hummbl-eval

- **Original repo:** https://github.com/hummbl-io/hummbl-eval
- **Original maintainer:** Reuben Bowlby
- **Import date:** 2026-09-09
- **Import mechanism:** File-copy only (no git history imported)
- **Known consumers:** HUMMBL fleet evaluation pipeline
- **Release history:** Not yet published to PyPI
- **Why this package exists:** Provides evidence-governed evaluation contracts for compositional Human-AI systems. Defines Record, Relation, and GateBench primitives for structured evaluation of AI agent outputs with provenance tracking.
- **Gitleaks scan:** 2 hits, both false positives (test fixture `sk-1234567890abcdef` with `# pragma: allowlist secret` in `evals/opencode_quality_checks.py`). No real secrets found.
