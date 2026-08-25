# Evidence Packet: IL4/IL5 and Air-Gap Public Claim Boundary

Status: draft source packet for issue `#594`
Scope: evidence and wording boundary only
Public copy changed: no
Last reviewed: 2026-07-03

## Objective

This packet source-packs the public claim family around `IL4/IL5`, `air-gap capable`, and adjacent defense/federal deployment language. It does not claim HUMMBL is authorized for IL4 or IL5 workloads, FedRAMP authorized, CMMC certified, or approved by a government assessor.

## Current Public Claim Locations

The exact bundled phrase `IL4/IL5 air-gap capable` was not present in `origin/main` during this review. A deployed-surface spot check on 2026-07-03 also did not find that exact bundled phrase on the checked production URLs listed below.

The claim family remains live in these repo-local source locations:

1. `web/solutions/defense-federal.html:114`
   `Sovereign, air-gap-ready AI governance primitives for federal and defense deployments. Stdlib-only Python, no cloud dependencies, NIST SP 800-53 aligned.`
2. `web/solutions/defense-federal.html:132`
   FAQ heading: `Why is HUMMBL suitable for air-gapped federal AI deployments?`
3. `web/solutions/defense-federal.html:135`
   `HUMMBL's governance primitives are stdlib-only Python with zero third-party runtime dependencies. There are no external API calls, no telemetry, and no cloud dependencies - suitable for classified and air-gapped environments.`
4. `web/method.html:402`
   `The regulated buyer cannot deploy a SaaS governance dashboard into IL4/IL5... They can deploy a stdlib-only Python package anywhere.`
5. `web/primitives/index.html:239`
   `deployable in air-gapped or regulated environments.`
6. `web/primitives/governance-bus.html:296`
   `Your agents run in air-gapped or regulated environments where SaaS...`
7. `web/solutions/regulated-industries.html:250`
   `Air-gap capable - deploys into your existing...`

The defense/federal page also includes useful boundary language at `web/solutions/defense-federal.html:409-413`: HUMMBL does not claim FedRAMP authorization, SAM registration, UEI, CAGE code, GSA schedule status, CMMC certification, or government approval; customer authorization-boundary controls determine where primitives may be deployed.

## Surface Verification Sweep

Review date: 2026-07-03

Repo-local sweep:

- Command family: case-insensitive search for `IL4`, `IL5`, `air-gap`, `airgapped`, `DIBCAC`, `CMMC`, `FedRAMP`, and `classified` across `web`, `docs`, `scripts`, and `operator`.
- The exact bundled phrase `IL4/IL5 air-gap capable` was not found outside this evidence packet.
- Residual `IL4` / `IL5` source references remain in `web/method.html`, `scripts/validate_public_release_state.py`, `docs/reports/public-surface-remediation-closeout-2026-07-02.md`, this evidence packet, and the artifact manifest entry for this packet.
- Residual air-gap language remains in public/source surfaces including `web/solutions/defense-federal.html`, `web/solutions/regulated-industries.html`, `web/primitives/index.html`, `web/primitives/governance-bus.html`, `web/docs/quickstart.html`, `web/docs/hummbl-base120.html`, `web/docs/hummbl-governance.html`, `web/llms-full.txt`, `web/about.html`, and `operator/site` content.
- Residual DIBCAC/CMMC/FedRAMP language remains in source, but the defense/federal page also carries explicit no-authorization / no-certification boundary language.

Deployed production spot check:

- `https://hummbl.io/solutions/defense-federal.html`: HTTP 200; residual `air-gap-ready`, `air-gapped`, `classified`, `CMMC`, and `FedRAMP` terms present; explicit no-FedRAMP/no-CMMC/no-government-approval boundary language present.
- `https://hummbl.io/method.html`: HTTP 200; residual `DIBCAC assessor` wording present.
- `https://hummbl.io/primitives/`: HTTP 200; residual `air-gapped or regulated environments` wording present.
- `https://hummbl.io/primitives/governance-bus.html`: HTTP 200; residual `air-gapped or regulated environments` wording present.
- `https://hummbl.io/solutions/regulated-industries.html`: HTTP 200; residual `Air-gap capable` wording present.

Conclusion: the original bundled `IL4/IL5 air-gap capable` phrase appears retired from the checked source/deployed surfaces, but adjacent air-gap, classified-environment, DIBCAC/CMMC, and federal suitability language remains live. Closeout should therefore record the bundled claim as retired or split, not fully source-supported.

## External Source Basis

Primary and government sources checked for the meaning of the public claim context:

- GSA Cloud Information Center, `Cloud Security`: the DoD CC SRG defines DoD cloud security requirements and Impact Levels. It identifies IL4 as CUI or non-CUI/non-critical mission information on non-National Security Systems, IL5 as higher-sensitivity CUI, mission-critical information, and National Security Systems, and IL6 as classified SECRET/NSS.
  Source: https://cic.gsa.gov/basics/cloud-security
- DoD CIO, `Cloud Security Playbook Volume 1`: Impact Levels are based on information sensitivity and the potential impact of loss of confidentiality, integrity, or availability. The playbook summarizes IL4 as Controlled Unclassified Information and IL5 as CUI requiring additional protection, including Unclassified National Security Systems.
  Source: https://dodcio.defense.gov/Portals/0/Documents/Library/CloudSecurityPlaybookVol1.pdf
- DoD CIO, `Cloud Security Playbook Volume 1`: Mission Owners should select a Cloud Service Offering with the appropriate Impact Level, and should not host higher-IL data or code in a lower-IL service.
  Source: https://dodcio.defense.gov/Portals/0/Documents/Library/CloudSecurityPlaybookVol1.pdf
- DoD CIO, `Cloud Security Playbook Volume 1`: DoD Mission Owners must use CSOs with a DoD Provisional Authorization or an Authorization to Operate for the selected impact level; a DoD PA is granted to a specific CSO, not to a provider generally.
  Source: https://dodcio.defense.gov/Portals/0/Documents/Library/CloudSecurityPlaybookVol1.pdf
- DoD CIO, `Cloud Security Playbook Volume 1`: commercial cloud services used for IL4 or higher have network-access requirements involving DISN/CAP/BCAP paths, not generic internet connectivity.
  Source: https://dodcio.defense.gov/Portals/0/Documents/Library/CloudSecurityPlaybookVol1.pdf
- eCFR, `32 CFR Part 170`: the CMMC Program is designed to ensure defense contractors safeguard FCI and CUI processed, stored, or transmitted on contractor information systems.
  Source: https://www.ecfr.gov/current/title-32/subtitle-A/chapter-I/subchapter-G/part-170

## Claim Decomposition

The public copy currently combines multiple claim types that need separate evidence:

1. Implementation claim: HUMMBL primitives are stdlib-only and have no third-party runtime dependency.
2. Deployment-shape claim: a customer can deploy primitives without a required HUMMBL SaaS control plane.
3. Artifact-portability claim: receipts/logs/evidence can be reviewed or transferred in isolated environments.
4. Environment-fit claim: the primitives are suitable for air-gapped or classified environments.
5. Program-impact-level claim: the primitives are usable in or relevant to IL4/IL5 contexts.
6. Assessment claim: the output is useful to DIBCAC/CMMC/assessor workflows.

Only the first three are supportable from current public repo and site evidence without additional proof. Items 4-6 require explicit architecture evidence, customer-boundary qualifiers, and owner-reviewed source packets before stronger public use.

## Evidence Currently Available

Current repo/public materials support these narrower claims:

- stdlib-only primitives are represented repeatedly in public copy;
- public copy states there are no required external API calls, telemetry, or cloud dependencies for the relevant governance primitives;
- the defense/federal page already includes authorization-boundary disclaimers;
- the site describes append-only, grep-friendly, portable evidence artifacts.

Current evidence does not establish:

- a completed IL4 or IL5 deployment;
- a DoD Provisional Authorization, agency ATO, FedRAMP authorization, CMMC certification, DIBCAC assessment, or government approval;
- a public offline test receipt proving fully disconnected operation for the exact federal/defense use case;
- a public architecture packet mapping HUMMBL components to an IL4/IL5 Mission Owner authorization boundary;
- suitability for classified environments beyond design intent.

## Minimum Evidence Required Before Stronger Public Wording

For `air-gap capable`:

1. Architecture packet showing the exact runtime path without required outbound network calls, SaaS dependency, telemetry, or managed HUMMBL control plane.
2. Software bill of materials or equivalent dependency receipt for the package/runtime path being claimed.
3. Offline execution receipt showing local generation, inspection, and transfer of logs/receipts/evidence.
4. Scope boundary separating primitive/library use from optional web, dashboard, API, analytics, or Cloudflare surfaces.

For `IL4/IL5`:

1. Definition that `IL4/IL5` refers only to a customer environment and information-impact context, not HUMMBL authorization status.
2. Mapping from each claimed primitive to customer-operated control evidence.
3. Statement of what is implemented today versus planned design intent.
4. Statement of what has been tested offline versus not tested.
5. Reviewable boundary language saying customer Mission Owner/AO/assessor decisions determine applicability.

For assessor-readiness wording:

1. Assessor-facing evidence index.
2. Control crosswalk limited to mapping support, not certification.
3. Source-linked examples of receipts, logs, and evidence artifacts.

## Recommendation

Recommendation: split and narrow.

Record the original bundled `IL4/IL5 air-gap capable` phrase as retired from checked source/deployed surfaces. Do not retain or reintroduce it as one bundled public claim unless a dedicated public architecture and evidence packet exists.

Retain, with normal claim-provenance handling:

- `Stdlib-only Python with zero third-party runtime dependencies.`
- `Customer-controlled deployment without a required HUMMBL cloud runtime.`
- `Portable append-only evidence suitable for offline review and transfer.`

Narrow before future promotion:

- Replace broad air-gap/classified/IL4/IL5 phrasing with:
  `Designed for customer-controlled, isolated, and air-gap-constrained environments; customer authorization boundary, information-impact level, and assessor review determine applicability.`

Reserve for a later evidence-backed packet:

- direct `IL4/IL5` capability wording;
- `classified environment` suitability;
- DIBCAC or assessor-readiness implications beyond source inspection and evidence portability.

## Proposed Public Citation Target

This file can be the internal source packet for issue `#594`. A later public link target should be a shorter architecture note, reviewed separately, that:

- cites official DoD/GSA impact-level sources;
- states no HUMMBL authorization/certification/government-approval claim;
- explains the specific primitive/runtime scope;
- links to offline execution and dependency receipts if they become publishable.

## Open Questions

1. Which exact package or primitive set is in scope for the public isolation claim: `hummbl-governance` only, Base120/governance-bus primitives, or additional public demo surfaces?
2. Is there an existing offline test or enclave-simulation receipt that can be published without exposing private evidence?
3. Should `classified` wording be removed from JSON-LD/FAQ copy unless a separate evidence packet supports it?
4. Should every future `IL4/IL5` reference be qualified as customer-environment context only, with no HUMMBL authorization implication?

## Do Not Infer

- This packet does not prove the current public claim is false.
- This packet does not prove the current public claim is fully supported.
- This packet does not authorize a public copy edit by itself.
- This packet does not establish federal readiness, classified-workload readiness, CMMC certification, FedRAMP authorization, or DoD IL4/IL5 authorization.
