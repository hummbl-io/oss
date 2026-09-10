# PROVENANCE — hummbl-gitops

- **Original repo:** https://github.com/hummbl-io/hummbl-gitops
- **Original maintainer:** Reuben Bowlby
- **Import date:** 2026-09-09
- **Import mechanism:** File-copy only (no git history imported)
- **Known consumers:** HUMMBL fleet GitOps loop
- **Release history:** Not yet published to PyPI (was v0.0.1 in standalone)
- **Why this package exists:** Closes the loop between local GitOps and remote GitOps with bidirectional multi-agent peer-review. Forward (local to remote): local CI contract runner, agent pre-review, pre-PR gate. Remote: review coverage matrix, meta-review, adaptive CI contract. Return (remote to local): CI watcher, main-moved detector, receipt sync, auto-rebase.
- **Gitleaks scan:** Clean (0 hits across 6 commits).
