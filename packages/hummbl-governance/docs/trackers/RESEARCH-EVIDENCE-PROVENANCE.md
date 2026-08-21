# Research Evidence Provenance Log

For volatile research artifacts (model catalogs, benchmark results, API counts, pricing data):
fetch UTC, source URL, parser command, raw count outputs, checksum where practical.

**Purpose**: Make research PRDs reproducible. Without this, "34 free-tier models" is
illustrative, not auditable. Every volatile claim should trace to an entry here.

---

## Standard entry format

```
### <artifact name>
- **Fetched**: <ISO 8601 UTC timestamp>
- **Source URL**: <exact URL fetched>
- **Parser**: <command or script used to produce the count/table>
- **Raw output**: <pasted or linked>
- **Checksum**: <sha256 of raw response, if practical>
- **Used in**: <doc path, PR number>
- **Claim**: <exact claim this evidence supports>
- **Expiry**: <date after which this evidence should be re-fetched>
```

---

## Entries

### OpenRouter free-tier model count
- **Fetched**: UNKNOWN — not recorded
- **Source URL**: UNKNOWN — not recorded
- **Parser**: UNKNOWN — not recorded
- **Raw output**: not saved
- **Checksum**: not computed
- **Used in**: PR #625 research brief
- **Claim**: "34 free-tier models available on OpenRouter"
- **Expiry**: model catalogs change weekly; should be re-fetched before any external use
- **Status**: ⚠️ UNVERIFIED — see UNVERIFIED-CLAIMS.md. Do not use this count in
  external-facing materials until re-fetched with provenance recorded.
- **Notes**: Unclear whether count includes `:free` suffix variants, `$0/$0` pricing rows,
  or excludes OpenRouter pseudo-models. Count method must be documented alongside re-fetch.

---

## Protocol for new entries

1. Before committing any research brief with a volatile count or table, run the fetch and
   record the entry above.
2. If the data source is an API, save the raw JSON response alongside the doc
   (or link to a private gist/file).
3. Include the fetch timestamp in the doc itself (e.g. "as of 2026-05-04T14:32Z").
4. Add an expiry date. For model catalogs: 7 days. For pricing: 14 days. For regulatory
   text: 90 days.
