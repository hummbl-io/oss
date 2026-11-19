# POINTER — canonical home moved

This in-tree copy of **governed-compression** is the **origin record**, not the
source of truth.

- **Canonical home:** `hummbl-io/governed-compression` (standalone GitHub repo)
- **Ruled:** 2026-11-14 (C1, governed-compression repo room) — the standalone
  repo is canonical because all recent PR/CI activity and the PyPI publish
  workflow live there; this tree originated the package and is retained as
  its pre-move record.
- **License of record:** the split statement in the canonical repo's
  `LICENSE` (engine/formats dual MIT OR Apache-2.0; future methods
  proprietary per `PROPRIETARY-METHODS.md`).
- This tree's `PROVENANCE.md` is the origin statement of record; its text is
  carried into the canonical repo's `PROVENANCE.md` with provenance noted.
- Do not develop against this copy. Changes made here will diverge silently —
  the two trees already diverged once (dependency pins and package metadata,
  recorded 2026-11-14).
