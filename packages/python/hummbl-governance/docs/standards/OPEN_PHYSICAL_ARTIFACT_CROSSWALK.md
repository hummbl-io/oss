# Candidate Open Physical Artifact Governance Crosswalk

Status: candidate crosswalk for issue #171.
Last verified: 2026-07-03.

This document is public-safe governance analysis. It is not canon, legal advice,
a license recommendation, a safety certification, manufacturing validation, or a
freedom-to-operate finding. Every new term in this document is candidate until a
separate namespace and governance review promotes it.

## Purpose

Open-source software intuition does not transfer directly to physical
artifacts. Physical artifacts have supply chains, build conditions, hazards,
tooling assumptions, modification lineage, and trademark boundaries that do not
exist in ordinary source-code review.

This crosswalk gives HUMMBL agents a draft checklist for reasoning about open
hardware, open physical artifacts, and open-source-inspired manufacturing work
without collapsing those artifacts into normal software repositories.

## Reviewed Source Anchors

All source anchors were retrieved on 2026-07-03. They are evidence anchors, not
HUMMBL canon.

| Anchor | URL | Bounded use in this document |
|---|---|---|
| OSHWA Open Source Hardware Definition | https://oshwa.org/resources/open-source-hardware-definition/ | Baseline for public design files, preferred editable source formats, scope declaration, necessary software, derivative works, redistribution, attribution, and non-discrimination. |
| OSHWA Certification Basics | https://certification.oshwa.org/basics.html | Separates hardware, software, documentation, and branding; reinforces that certification is a specific representation, not a generic marketing label. |
| CERN Open Hardware Licence | https://cern-ohl.web.cern.ch/ | Shows that hardware design licenses need variants and terms distinct from normal software license defaults. |
| Open Source Ecology GVCS | https://wiki.opensourceecology.org/wiki/Global_Village_Construction_Set | Example of a broad open physical systems ambition with machines, tooling, and production claims that require evidence separation. |
| RepRap wiki | https://reprap.org/wiki/RepRap | Example of an open hardware community surface with machine designs, build history, and evolved variants. |
| Towards FAIR Principles for Open Hardware | https://arxiv.org/abs/2109.06045 | Research basis for treating open hardware reuse as findability, accessibility, interoperability, and reusability work with different constraints from FOSS. |
| Standardisation of practices in Open Source Hardware | https://arxiv.org/abs/2004.07143 | Research basis for standardization, documentation formats, discoverability, modularity, and open toolchain concerns. |
| A Lot of Moving Parts | https://arxiv.org/abs/2406.12801 | Research basis for collaboration challenges in open-source hardware design communities. |

## Candidate Claim Taxonomy

Use the narrowest claim that the evidence supports:

| Claim | Minimum evidence | Do not infer |
|---|---|---|
| `open-source-inspired` | Design intent or process resembles open-source practice. | Source files, license permissions, safety, reproducibility, or third-party buildability. |
| `docs-published` | Build, assembly, or explanatory documentation is public. | Editable source completeness or permission to modify, manufacture, or sell. |
| `source-available-physical-artifact` | Native design files, schematics, firmware, or BOMs are public. | Open hardware license compatibility or reproducible builds. |
| `candidate-open-hardware` | Scope, license stack, editable sources, BOM, and necessary software are declared. | OSHWA certification, safety validation, or market readiness. |
| `candidate-certified-open-hardware` | Current certification record and matching public docs are identified for namespace review. | Safety, quality, endorsement, or freedom to use trademarks. |
| `candidate-verified-reproducible-open-artifact` | Independent build or reproduction receipt confirms artifact construction from the declared evidence packet for governance review. | Regulatory approval, production quality, or unrestricted commercial use. |

## Crosswalk

| OSS intuition | Physical-artifact translation | Required governance question |
|---|---|---|
| Source repository | Native CAD, schematics, PCB files, firmware, BOM, drawings, build instructions, calibration notes, test fixtures. | Can a competent third party inspect and modify the preferred editable sources, not only rendered exports? |
| Package dependency graph | Material, supplier, component, firmware, toolchain, jig, process, and calibration dependency graph. | Are substitutions declared and are critical tolerances or safety effects documented? |
| License file | License stack across software, firmware, documentation, hardware design files, trademarks, and produced objects. | Which rights apply to which layer, and where are trademark or brand rights excluded? |
| CI status | Build, assembly, inspection, calibration, test, failure, and field-use receipts. | Has anyone reproduced the artifact from the declared packet under documented conditions? |
| Fork or derivative | Modification lineage across design files, materials, tooling, manufacturing process, firmware, and field changes. | Can a derivative preserve provenance without implying original endorsement? |
| Release notes | Versioned design release with source hashes, BOM revision, tolerance changes, known hazards, maintenance notes, and validation scope. | What changed physically, and what tests or hazard analyses were repeated? |
| Security advisory | Safety, misuse, defect, recall, field failure, supply-chain, and firmware vulnerability advisory. | Does the advisory route to human expert review before agents recommend build or use actions? |

## Candidate Evidence Packet

A minimal open physical artifact evidence packet should include:

- artifact identity, version, maintainer, and repository or publication URL;
- scope statement identifying which layers are open and which are excluded;
- native editable design files, not only images, PDFs, screenshots, or exports;
- bill of materials with supplier assumptions and acceptable substitutions;
- mechanical drawings, schematics, PCB layouts, firmware source, and interface
  documentation where applicable;
- tooling, calibration, fabrication, assembly, and maintenance instructions;
- license stack for software, firmware, documentation, hardware design files,
  brand assets, and produced artifacts;
- trademark and endorsement boundary;
- hazard inventory, misuse notes, required PPE, and regulated-use warnings;
- build, assembly, inspection, calibration, test, failure, field-use, and
  reproduction receipts;
- derivative lineage record for substitutions, remixes, forks, repairs, and
  field modifications;
- validation limits stating what has not been tested or certified.

## Negative Examples

These claims must remain unpromoted until the missing evidence is supplied:

- `open` marketing page with only product photos and no editable design source;
- public STL or PDF with no native CAD, BOM, license, or modification rights;
- schematic dump with no firmware source for required embedded behavior;
- BOM without supplier substitutions, tolerances, or safety-critical part notes;
- build video without reproducible instructions, calibration steps, or tests;
- open design files paired with a trademark claim that implies endorsement of
  derivatives;
- third-party fork that changes materials or tolerances without hazard or test
  receipts;
- certified-looking badge with no current certification record or documentation
  match;
- agent-generated build recommendation for a regulated or hazardous artifact
  without human expert review.

## Escalation Boundaries

Agents must escalate before recommending construction, sale, field deployment,
or modification when an artifact touches:

- medical devices, implants, diagnostics, health monitoring, or clinical use;
- vehicles, aircraft, drones, pressure vessels, lifting equipment, tools,
  structural components, or other injury-producing systems;
- RF/radio devices, batteries, power electronics, lasers, weapons, defense,
  surveillance, or dual-use systems;
- regulated goods, child-safety contexts, food/water contact, environmental
  controls, or critical infrastructure;
- any case where component substitution can change safety behavior;
- any case where licensing, patents, export controls, trademarks, or product
  liability would materially affect a recommendation.

Escalation means a human expert or appropriate governance reviewer must approve
the next action. A public source file or model card is not enough.

## Candidate Admission Gate

Before a physical artifact claim is admitted into HUMMBL governance, the reviewer
should record:

1. claim text and requested label;
2. evidence packet path or URL;
3. source retrieval date;
4. license stack summary and unresolved license questions;
5. source-completeness gaps;
6. reproduction or validation receipts;
7. safety and regulated-use classification;
8. trademark or endorsement boundary;
9. derivative lineage status;
10. reviewer decision: reject, hold, candidate, or promote for governance review.

## Review Notes

- This document does not choose a default open hardware license.
- This document does not assert that OSHWA, CERN OHL, OSE, RepRap, or any cited
  paper makes a third-party project safe, compliant, reproducible, or
  commercially viable.
- Public openness does not remove the need for safety, legal, manufacturing,
  regulatory, or field-use review.
- Candidate names here should not be reused in product copy until namespace and
  claim review are complete.
