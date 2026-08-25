# Astronomy Discovery Pipeline

Date: 2026-03-27
Status: draft

## Question

What is a realistic discovery pipeline for an individual or small team trying to make real findings from astronomy data?

## Bottom Line

The right target is not "train one model and declare discovery."

The realistic path is:

1. choose an archive with known review bottlenecks
2. generate candidates at scale
3. rank or cluster anomalies
4. perform disciplined human review
5. validate against catalogs and artifacts
6. package evidence for expert follow-up or publication

## Best Near-Term Datasets And Programs

- NEOWISE and WISE-style infrared archive work
- Rubin Observatory alert streams and derived public infrastructure
- Hubble anomaly-mining or archival image triage
- Backyard Worlds and related NASA citizen-science workflows
- HETDEX-style hybrid citizen-science plus ML workflows

Relevant sources:

- NEOWISE variable-object example  
  https://www.smithsonianmag.com/smart-news/high-school-student-discovers-1-5-million-potential-new-astronomical-objects-by-developing-an-ai-algorithm-180986429/
- Rubin Observatory scale and alert volume  
  https://kipac.stanford.edu/research/projects/vera-rubin-observatorys-legacy-survey-space-and-time-lsst  
  https://www.scientificamerican.com/article/rubin-observatory-data-flood-will-let-the-universe-alert-astronomers-10/
- Backyard Worlds  
  https://science.nasa.gov/citizen-science/backyard-worlds-cool-neighbors/  
  https://science.nasa.gov/get-involved/citizen-science/a-solar-neighborhood-census-thanks-to-nasa-citizen-science/
- HETDEX citizen science plus ML  
  https://arxiv.org/abs/2304.07348

## Good Discovery Tasks

- variable-object discovery in time-series data
- transient triage
- brown-dwarf or moving-object detection
- anomaly detection in archival imagery
- catalog cross-match oddball discovery
- rare-event clustering

## Practical Workflow

### Stage 1: Problem Selection

- prefer a narrow scientific question with a known public dataset
- prefer domains where false positives can be reduced using catalogs, metadata, or follow-up literature
- avoid areas that require immediate access to proprietary instruments

### Stage 2: Candidate Generation

- train unsupervised, weakly supervised, or ranking models
- surface rare or unstable patterns rather than only optimizing benchmark accuracy
- preserve enough traceability to explain why a candidate was surfaced

### Stage 3: Human Review

- perform manual triage on top-ranked candidates
- compare AI-autonomous triage with human-guided review
- keep a rejection log so you learn what the model is getting wrong

### Stage 4: Validation

- cross-check against existing catalogs
- eliminate instrumental artifacts and duplicates
- document uncertainty explicitly

### Stage 5: Evidence Package

- image or light-curve snapshots
- ranking rationale
- nearest-known-object comparison
- catalog match or non-match
- confidence and follow-up recommendation

## HUMMBL Relevance

- tuples can represent candidate generation, review decisions, rejection reasons, and validation evidence
- BaseN can encode different reasoning paths for anomaly triage
- HITL and HOTL regimes can be tested directly in candidate review workflows

## Confidence

High on the workflow shape. Medium on which exact archive will be best for a solo start, because that depends on current data access and tooling maturity.
