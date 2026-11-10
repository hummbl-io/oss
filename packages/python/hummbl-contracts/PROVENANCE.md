# PROVENANCE — hummbl-contracts

- **Original repo:** In-tree (originated in hummbl-io/oss)
- **Maintainer:** Reuben Bowlby
- **Version:** 0.1.0
- **Description:** HUMMBL contract schemas and stdlib-only JSON Schema validator
- **License:** MIT OR Apache-2.0 (dual-license, see LICENSE files)

## External Imports

### JSON Schema Test Suite Fixtures
- **Record:** [`provenance/json-schema-test-suite.import.json`](provenance/json-schema-test-suite.import.json)
- **Schema:** [`schemas/public/external-import-record-v1.schema.json`](../../schemas/public/external-import-record-v1.schema.json)
- **Upstream Repository:** `https://github.com/json-schema-org/JSON-Schema-Test-Suite`
- **Immutable Source Revision:** `f6fd52a0a95472e079cbfc6ef7f089702b80e045` (committed 2026-09-06T23:55:31Z)
- **Dialect:** Draft 2020-12
- **Corpus:** 16 keyword fixture files (`tests/draft2020-12/{additionalProperties,anyOf,const,enum,items,maximum,maxItems,maxLength,minimum,minItems,minLength,oneOf,pattern,properties,required,type}.json`) + upstream `LICENSE`
- **Local Location:** [`tests/fixtures/json-schema-test-suite/`](tests/fixtures/json-schema-test-suite/)
- **Upstream License:** MIT License, Copyright (c) 2012 Julian Berman (see [`tests/fixtures/json-schema-test-suite/LICENSE`](tests/fixtures/json-schema-test-suite/LICENSE))
- **Transformations:** None; byte-for-byte exact copies verified against upstream git blob SHAs.
- **Intended Reuse:** Test fixtures only (`zero_runtime` dependency, excluded from package distribution wheel/sdist).
