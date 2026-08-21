# Scientific Grounding Coordination Matrix

- **Status:** planning artifact
- **Date:** 2026-06-25
- **Owner:** Reuben Bowlby
- **Purpose:** sequence the Scientific Grounding issue set before any
  cross-repo implementation

## Scope

This matrix coordinates the current Scientific Grounding issue set across the
primary evidence, research, doctrine, theory, and tuple-interface repos:

- `hummbl-bibliography#71`
- `hummbl-research#39`
- `hummbl-doctrine#10`
- `hummbl-theory#15`
- `hummbl-tuples#22`

It assumes three boundary constraints:

1. Empirical evidence is upstream of theory and tuple encoding.
2. Doctrine must not be mistaken for empirical proof.
3. Tuple/schema work should follow, not lead, the evidence contract.

## Coordination matrix

| Issue | Repo | Governed interface surface | Upstream dependencies | Downstream dependents | Required acceptance gates | Expected receipt artifacts | Residual risk if implemented out of order |
|------|------|-----------------------------|-----------------------|-----------------------|---------------------------|----------------------------|-------------------------------------------|
| `#71` | `hummbl-bibliography` | Canonical empirical evidence contract, bibliography keys, source metadata, machine-readable evidence map | none | `hummbl-research#39`, `hummbl-theory#15`, `hummbl-doctrine#10`, `hummbl-tuples#22` | Human-readable grounding contract exists; machine-readable evidence map exists or is fully specified; missing DOI/ISBN/arXiv metadata tracked; validation commands documented and passing | grounding contract doc, evidence-map artifact spec/export, metadata debt receipt, validation receipt | Downstream repos invent duplicate source records, inconsistent keys, and unverifiable evidence tiers |
| `#39` | `hummbl-research` | Research claim traceability from local validation artifacts or bibliography keys | `hummbl-bibliography#71` | `hummbl-theory#15`, public research claims, future product claims | Material claims tagged with source, validation artifact, or research-alpha status; examples and README claims do not overstate validation; documented review/check gate exists | research grounding manifest/section, claim inventory receipt, validation receipt | Research claims harden around unstable labels and leak into theory or public messaging as if externally validated |
| `#10` | `hummbl-doctrine` | Doctrine/evidence boundary and operator-doctrine classification | `hummbl-bibliography#71` | `hummbl-theory#15`, `hummbl-tuples#22`, fleet agent prompts | Doctrine-vs-science boundary documented; external-source claims classified; unsourced scientific-looking claims tracked as debt | doctrine boundary note, classification receipt, debt ledger | Agents treat operator doctrine or intellectual lineage as empirical proof |
| `#15` | `hummbl-theory` | Theory claim-strength rubric and evidence/status tagging | `hummbl-bibliography#71`, `hummbl-research#39`, `hummbl-doctrine#10` | publication-ready theory outputs, `hummbl-tuples#22` examples | Core theory claims carry bibliography key, research note path, implementation evidence path, or explicit status tag; no speculative claim presented as validated | theory claim audit, claim-strength rubric, research-debt receipt | Theory canon overstates support, and later tuple/receipt layers preserve misleading confidence |
| `#22` | `hummbl-tuples` | Tuple-backed representation for scientific grounding evidence and attestation boundaries | `hummbl-bibliography#71`, `hummbl-doctrine#10`, `hummbl-theory#15` | any downstream tuple consumers, receipt tooling, promotion gates | Documented tuple pattern exists; examples separate grounding from attestation/promotion receipts; schema gaps identified before schema edits | tuple pattern doc, example tuples, schema-gap receipt, validation receipt | Tuple interface overfits provisional assumptions and collapses evidence, attestation, and promotion into one ambiguous primitive |

## Recommended implementation sequence

1. **`hummbl-bibliography#71` first**
   The fleet needs a canonical evidence contract before any downstream claim,
   doctrine, or tuple layer can normalize around it.

2. **`hummbl-research#39` and `hummbl-doctrine#10` second**
   These can proceed in parallel only after the bibliography contract is clear.
   Research clarifies empirical/validation posture; doctrine clarifies
   non-empirical operator posture.

3. **`hummbl-theory#15` third**
   Theory needs both the evidence contract and the doctrine boundary to avoid
   mixing synthesis with proof.

4. **`hummbl-tuples#22` last**
   Tuple encoding should represent the settled interface, not invent it.

## Decision gates before implementation

The following gates should be satisfied before cross-repo code/schema work:

1. `G-SG-1`: bibliography evidence contract defined
2. `G-SG-2`: doctrine/evidence boundary documented
3. `G-SG-3`: research claim-status tagging model documented
4. `G-SG-4`: theory claim-strength rubric documented
5. `G-SG-5`: tuple evidence pattern drafted only after the first four are
   concrete

## Deferred work

- No cross-repo schema unification in this planning artifact
- No canon/publication promotion
- No marketing/public-facing claim expansion
- No automatic repo creation or naming exception inference

## Related governance surfaces

- Naming/boundary gate: `hummbl-governance#134`
- Whether system boundary gate: `whether-book#73`
- This matrix is sequencing-only and does not grant implementation authority by
  itself
