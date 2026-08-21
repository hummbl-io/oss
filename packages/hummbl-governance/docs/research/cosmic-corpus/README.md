# Cosmic Corpus Doctrine

**Status:** PROPOSED — requires human review before canonical promotion
**Origin:** hummbl-io/hummbl-governance#82
**Steward:** HUMMBL Research Institute

---

## 1. Purpose

The governance research lane needs a scalable Cosmic Corpus: bibliographies and dossiers that can scale from continents to planets, moons, star systems, galaxies, archives, surveys, and citizen-science novelty quests.

Space research and space governance require provenance, dataset passports, observation receipts, crossmatch gates, novelty claim discipline, and governance context for treaties, planetary protection, heritage, debris, scientific credit, and resource use.

---

## 2. Non-Negotiable Invariants

1. **No discovery claim without provenance** — every observation must trace to its source
2. **No novelty claim without negation** — every novelty claim must include what it is NOT
3. **No dataset without governance context** — every dataset must declare its governance posture

---

## 3. Primitives

### AstroBib

A bibliography entry for astronomical/space sources.

```yaml
bib_id: "astrobib-001"
title: "Source name"
type: "survey"  # survey, archive, catalog, mission, telescope
url: "https://..."
access: "public"  # public, restricted, proprietary
governance_context: "NASA public domain"
provenance: "NASA/ESA"
```

### CelestialDossier

A dossier for a celestial object or region.

```yaml
dossier_id: "celestial-001"
object_name: "Mars"
object_type: "planet"  # planet, moon, asteroid, star, exoplanet, galaxy
coordinates: "RA 14h 15m, Dec -15° 12'"
datasets:
  - "MGS MOLA topography"
  - "MRO HiRISE imagery"
governance_context:
  treaties: ["Outer Space Treaty 1967"]
  planetary_protection: "COSPAR Category IV"
  heritage: "None designated"
novelty_quests:
  - "subsurface water detection"
  - "atmospheric methane anomalies"
```

### DatasetPassport

A governance passport for a dataset.

```yaml
passport_id: "passport-001"
dataset_name: "MGS MOLA"
source: "NASA"
access_policy: "public"
provenance_chain:
  - "MGS spacecraft → MOLA instrument → PDS archive"
license: "NASA public domain"
governance_context: "Planetary data — no export restrictions"
receipt_required: true
```

### ObservationReceipt

A receipt for an observation or measurement.

```yaml
receipt_id: "obs-001"
observer: "agent-id"
target: "Mars crater X"
instrument: "HiRISE"
timestamp: "2026-06-23T12:00:00Z"
result: "crater depth measured"
provenance: "MRO orbit 12345"
```

### NoveltyQuest

A structured novelty search across cosmic datasets.

```yaml
quest_id: "quest-001"
target: "Mars atmospheric methane"
hypothesis: "Seasonal methane variations indicate subsurface processes"
datasets:
  - "MAVEN data"
  - "TGO NOMAD data"
crossmatch_gates:
  - "seasonal filtering"
  - "instrument calibration check"
  - "prior-art comparison"
lifecycle: "candidate"  # candidate, crossmatched, reviewed, rejected, promoted, published
```

### CrossmatchGate

A validation gate for crossmatching datasets.

```yaml
gate_id: "gate-001"
name: "coordinate match"
type: "spatial"
tolerance: "1 arcsec"
required: true
```

### SpaceGovernanceEnvelope

Governance context for space activities.

```yaml
envelope_id: "envelope-001"
scope: "Mars surface"
treaties:
  - "Outer Space Treaty 1967"
  - "Artemis Accords"
planetary_protection: "COSPAR Category IV"
heritage_sites: []
debris_policy: "IADC guidelines"
scientific_credit: "first publication rights"
resource_use: "not authorized"
```

---

## 4. Novelty Quest Lifecycle

```
candidate → crossmatched → reviewed → promoted → published/submitted
                                    ↓
                                 rejected
```

| Stage | Meaning |
|-------|---------|
| `candidate` | Hypothesis formulated, datasets identified |
| `crossmatched` | Datasets crossmatched through all gates |
| `reviewed` | Human + Arbiter review completed |
| `rejected` | Prior art explains the result or methodology flawed |
| `promoted` | Confirmed as novel — ready for publication |
| `published/submitted` | Submitted to journal or published |

---

## 5. Bibliography Directory Layout

```
docs/research/cosmic-corpus/
  README.md                    — this doctrine
  TEMPLATE.md                  — celestial dossier template
  governance/
    README.md                  — space governance bibliography
  archives/
    README.md                  — survey/archive bibliography
  solar-system/
    README.md                  — solar system bibliography
  moons/
    README.md                  — moon bibliography
  exoplanets/
    README.md                  — exoplanet bibliography
  galaxies/
    README.md                  — galaxy bibliography
  citizen-science/
    README.md                  — citizen science platforms
  surveys/
    README.md                  — survey missions
```

---

## 6. Cross-References

- **Government Corpus doctrine:** hummbl-governance#81
- **Simulation-governance prior-art corpus:** hummbl-governance#1018
- **Arbiter novelty rubric:** arbiter#88
- **Simulation Affordance template:** hummbl-governance#83

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Approval required:** Human review before canonical promotion
