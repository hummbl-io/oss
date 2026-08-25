# Tuple Schema Registry Specification v0.1

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #37 (B5: Design tuple schema registry for ecosystem scaling)
- **Date:** 2026-07-01

## Purpose

If tuples are to be reused across organizations, consumers need a way to find and validate schemas. This document specifies a minimal registry design with two reference implementations (static and dynamic).

## Architecture

### Static Registry

A static registry is a versioned directory of schema files with a manifest. Consumers download or clone the registry and validate locally.

```
registry/
  manifest.json          # index of all schemas with versions
  schemas/
    contract.schema.json
    evidence.schema.json
    ...
```

**Pros**: Simple, offline-capable, no server needed, easy to audit
**Cons**: No real-time updates, manual sync required, no discovery API

### Dynamic Registry

A dynamic registry is an HTTP server that provides schema discovery and retrieval via a REST API.

```
GET /registry/manifest           # list all schemas
GET /registry/schemas/{id}       # get a specific schema
GET /registry/schemas/{id}/versions  # list versions
GET /registry/search?q=...       # search schemas
```

**Pros**: Real-time updates, searchable, version negotiation
**Cons**: Requires server infrastructure, network dependency, more complex

## Discovery Mechanism

### URL Pattern

Schemas are identified by URL:

```
https://hummbl.dev/schemas/tuples/{schema_name}
```

The `$id` field in each schema follows this pattern. Consumers can resolve schemas by fetching the URL (dynamic) or looking up the local copy (static).

### Manifest Format

```json
{
  "registry_version": "0.1.0",
  "updated_at": "2026-07-01T00:00:00Z",
  "schemas": [
    {
      "schema_id": "contract.schema.json",
      "url": "https://hummbl.dev/schemas/tuples/contract.schema.json",
      "version": "0.2.0",
      "title": "HUMMBL CONTRACT Tuple",
      "tuple_type": "CONTRACT"
    }
  ]
}
```

## Mock Implementations

### 1. Static Registry (`scripts/static_registry.py`)

A Python script that generates a manifest from a local `schemas/` directory. Consumers can use this to create their own static registry.

### 2. Dynamic Registry (`scripts/dynamic_registry.py`)

A stdlib-only HTTP server that serves schemas and a manifest. Consumers can run this locally or deploy it.

## Trade-offs

| Dimension | Static | Dynamic |
|-----------|--------|---------|
| Setup cost | Low (clone repo) | Medium (run server) |
| Update latency | Manual sync | Real-time |
| Offline use | Yes | No |
| Search | No | Yes |
| Version negotiation | Manual | API-supported |
| Audit trail | Git history | Server logs |
| Trust model | Repo trust | Server trust + TLS |

## Do Not Infer

- Do not infer that the registry is a schema validation service (it only provides schemas)
- Do not infer that the dynamic registry is production-ready (it's a mock)
- Do not infer that the URL pattern implies a live HTTP endpoint (it's an identifier)
- Do not infer that the registry solves schema evolution (see SCHEMA_VERSIONING.md)

## Non-goals

- Not a schema validation service
- Not a package manager (like npm or Maven)
- Not a schema authoring tool
- Not a production deployment guide
