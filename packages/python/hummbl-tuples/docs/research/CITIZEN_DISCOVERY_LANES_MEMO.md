# Citizen Discovery Lanes Memo

Date: 2026-03-27
Status: draft

## Question

Given the non-astronomy lanes ranked for fit, which public datasets matter most, which are best for AI-assisted anomaly discovery, and which lane offers the fastest credible path to a first novel result?

## Bottom Line

If the goal is a first credible AI-assisted discovery outside astronomy, the best near-term lane is still:

1. biodiversity and ecology
2. earth observation
3. protein design
4. climate and environmental sensing
5. archaeology and historical archives

For pure anomaly-discovery fit, the top two are biodiversity and earth observation.

For fastest path to a first credible result, biodiversity is the best choice because the data are public, multimodal, large, underreviewed, and still close enough to human intuition for manual validation.

## Ranked Memo

### 1. Biodiversity And Ecology

#### Top Public Datasets

- `GBIF`
  - global biodiversity occurrence backbone
  - open, massive, and research-grade enough for downstream filtering
  - https://www.gbif.org/
- `iNaturalist`
  - image-rich, community-validated observations
  - research-grade observations can flow into GBIF
  - https://www.inaturalist.org/
  - https://www.inaturalist.org/posts/29105-making-sure-your-observations-are-shared-to-gbif
- `eBird`
  - strongest public bird-observation dataset
  - direct download products are available
  - https://ebird.org/about/download-ebird-data-products
- `Movebank`
  - free animal-tracking database
  - strong for movement anomalies, migration, and behavior shifts
  - https://www.movebank.org/

#### Best For AI-Assisted Anomaly Discovery?

Yes. This is probably the best non-astronomy lane for anomaly discovery.

High-value anomaly tasks:

- unusual range shifts
- rare species in unexpected places
- phenology anomalies
- inter-species co-occurrence anomalies
- cryptic or misidentified species clusters
- movement anomalies in tracking data

Why it fits:

- images, metadata, geolocation, and timing all help validation
- community and expert review pathways already exist
- plenty of discovery can start as ranking, clustering, or mismatch detection rather than perfect classification

#### Fastest Credible Path To A First Novel Result?

Best overall.

Why:

- easiest data access
- easiest manual review loop
- strong ecological novelty surface
- many publishable outcomes do not require wet-lab validation

#### Notes

- GBIF has passed the billion-record scale and remains one of the largest open biodiversity infrastructures.  
  https://www.gbif.org/news/5BesWzmwqQ4U84suqWyOQy/big-data-for-biodiversity-gbiforg-surpasses-1-billion-species-occurrences
- eBird explicitly offers public download products and has been described as the largest biodiversity-related citizen science project.  
  https://ebird.org/about/download-ebird-data-products  
  https://ebird.org/news/annual-ebird-update-brings-gbif-to-almost-one-billion-records
- Recent large-scale biodiversity AI datasets derived from iNaturalist show the scale is already in the hundreds of millions of images.  
  https://arxiv.org/abs/2406.17720  
  https://arxiv.org/abs/2505.14707

### 2. Earth Observation

#### Top Public Datasets

- `Landsat`
  - long-running public Earth archive
  - https://science.nasa.gov/mission/landsat/data-overview/
- `Harmonized Landsat Sentinel-2`
  - useful for higher-temporal-frequency land monitoring
  - https://science.nasa.gov/mission/landsat/open-data/
  - https://lpdaac.usgs.gov/documents/1117/HLS_Quick_Guide_v02.pdf
- `Sentinel / Copernicus` public products
- `Microsoft Planetary Computer`
  - practical public access layer for many EO datasets
  - https://planetarycomputer.microsoft.com/

#### Best For AI-Assisted Anomaly Discovery?

Yes. Extremely strong fit.

High-value anomaly tasks:

- deforestation anomalies
- shoreline or wetland shifts
- wildfire burn-pattern anomalies
- illegal mining or land-use change
- crop-health anomalies
- flood extent change

#### Fastest Credible Path To A First Novel Result?

Second-best.

Why:

- data are huge and public
- anomaly detection is natural here
- but validation is harder than biodiversity because many signals are ambiguous without domain context

### 3. Protein Design

#### Top Public Datasets

- `wwPDB`
  - canonical open structural biology archive
  - https://www.wwpdb.org/
- `Foldit`
  - citizen-science protein-design environment with real scientific outputs
  - https://fold.it/
  - https://www.ipd.uw.edu/2019/06/foldit-protein-design/
- `AlphaFold DB`
  - useful as a comparative structural prior rather than a discovery endpoint
  - https://alphafold.ebi.ac.uk/

#### Best For AI-Assisted Anomaly Discovery?

Moderate.

This is better for:

- design search
- structural outlier ranking
- candidate prioritization

It is less attractive for solo anomaly discovery because validation often needs deeper biophysical or experimental grounding.

#### Fastest Credible Path To A First Novel Result?

Third.

Why:

- the scientific upside is high
- but the validation burden is much heavier than ecology or EO

### 4. Climate And Environmental Sensing

#### Top Public Datasets

- `NOAA Climate Data Records`
  - https://www.ncei.noaa.gov/products/climate-data-records
- `NOAA Climate Data Online`
  - https://www.ncdc.noaa.gov/cdo-web/
- `EPA Air Quality System`
  - https://www.epa.gov/aqs
- `AirNow`
  - https://www.airnow.gov/about-airnow

#### Best For AI-Assisted Anomaly Discovery?

Good, especially for:

- local pollution anomalies
- smoke and air-quality events
- unusual sensor divergences
- climate extreme clustering
- cross-sensor inconsistency detection

#### Fastest Credible Path To A First Novel Result?

Fourth.

Why:

- rich public data
- socially meaningful problems
- but signals are noisy and novelty can be harder to separate from routine variability

### 5. Archaeology And Historical Archives

#### Top Public Datasets

- `Library of Congress APIs`
  - https://www.loc.gov/apis/
- `Chronicling America API`
  - https://chroniclingamerica.loc.gov/about/api/
- `Europeana`
  - https://www.europeana.eu/
- `Arachne / iDAI.objects`
  - archaeological objects and image archives
  - https://arachne.dainst.org/

#### Best For AI-Assisted Anomaly Discovery?

Moderate.

Best tasks:

- image-cluster oddities
- overlooked archival patterns
- cross-collection entity resolution
- OCR correction and event mining in historical corpora

#### Fastest Credible Path To A First Novel Result?

Fifth.

Why:

- public data access is good
- but novelty is often interpretive and slower to validate as a real discovery claim

## Best For AI-Assisted Anomaly Discovery

1. biodiversity and ecology
2. earth observation
3. climate and environmental sensing
4. archaeology and historical archives
5. protein design

## Fastest Credible Path To A First Novel Result

1. biodiversity and ecology
2. earth observation
3. protein design
4. climate and environmental sensing
5. archaeology and historical archives

## Recommendation

If you want the fastest realistic path:

- start with `biodiversity`
- use `iNaturalist + GBIF + eBird` first
- focus on anomaly ranking rather than full classification
- pick one question class:
  - range-shift anomaly
  - rare-species resurfacing
  - phenology mismatch
  - cryptic-species confusion cluster

That is the best mix of:

- public data
- human-legible validation
- AI leverage
- and publishable novelty potential

## Confidence

High on biodiversity as the best non-astronomy starting lane. Medium-high on the detailed ranking across the other four lanes.
