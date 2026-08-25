# Tuple-to-Events Mapping Document

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #38 (B6: Build a converter from tuple traces to structured event log formats)
- **Date:** 2026-07-01

## Summary

This document describes the mapping from HUMMBL tuples to CloudEvents 1.0 format, including mapping decisions, constraints, and lossy conversions.

## CloudEvents 1.0 Mapping

### Core attributes

| CloudEvent attribute | HUMMBL tuple field | Notes |
|---------------------|--------------------|-------|
| specversion | (constant) | Always "1.0" |
| id | id | Direct mapping |
| time | time | Direct mapping (ISO 8601) |
| type | tuple_type + state | "hummbl.tuple.<tuple_type>.<state>" |
| source | agent | "/hummbl/tuples/<agent>" |
| subject | intent_id | Optional, only if present |
| datacontenttype | (constant) | Always "application/json" |
| data | (full tuple) | The complete tuple dict is embedded |

### Extension attributes (HUMMBL-specific)

| Extension | Tuple field | Notes |
|-----------|-------------|-------|
| hummbltuple_type | tuple_type | Redundant with type but preserved for querying |
| hummblstate | state | Governance state (ok/blocked/error) |
| hummblrift | drift | Governance drift value |
| hummbltier | tier | Governance tier |
| hummbltool | tool | Tool that produced the tuple |

## Mapping decisions

### 1. type attribute includes state

The CloudEvents `type` attribute combines `tuple_type` and `state` (e.g., `hummbl.tuple.CONTRACT.ok`). This allows event filtering by both tuple class and governance state.

**Alternative considered**: type as just `hummbl.tuple.<tuple_type>` with state as an extension. Rejected because state is a primary filter dimension for governance events.

### 2. source uses agent, not tool

The `source` attribute maps to `agent` (the AI agent that produced the tuple), not `tool`. This is because in HUMMBL, the agent is the accountable entity, while the tool is the mechanism.

### 3. Full tuple in data

The complete tuple dict is embedded in the `data` field. This is lossless — no information is lost in the conversion to CloudEvents.

### 4. subject is optional

The `subject` attribute is only set when `intent_id` is present. Research tuples (BaseN, Nodezero) do not have `intent_id` and thus have no `subject`.

## Lossy conversions

### CloudEvents → HUMMBL tuples

Converting from CloudEvents back to HUMMBL tuples is lossless if the full tuple is in `data`. However, if a consumer only reads the CloudEvents attributes (not `data`), they lose:
- `tuple_data` (the domain-specific payload)
- `task_id`
- `previous_hash` (if present)
- All Layer 3 domain fields

### NDJSON format

NDJSON output is the simplest format — each line is a JSON object of the original tuple. This is lossless but does not add CloudEvents metadata. Useful for log aggregation systems that expect newline-delimited JSON.

## Constraints

1. CloudEvents `id` must be unique within a source. HUMMBL tuple IDs are unique within a trace but may not be globally unique. Consumers should use `source + id` for uniqueness.

2. CloudEvents `time` must be RFC 3339. HUMMBL tuple `time` is ISO 8601, which is a superset of RFC 3339. Most HUMMBL timestamps are RFC 3339 compatible.

3. CloudEvents `type` should follow a reverse-DNS convention. We use `hummbl.tuple.<type>.<state>` which is a simplified convention.

## Do Not Infer

- Do not infer that CloudEvents conversion makes tuples interoperable with all event systems (CloudEvents is a specification, not a protocol).
- Do not infer that the extension attributes are standard (they are HUMMBL-specific).
- Do not infer that NDJSON output preserves CloudEvents metadata (it does not — it's just the raw tuple).
- Do not infer that this converter supports all CloudEvents bindings (it produces the JSON event format only).

## Non-goals

- Not a CloudEvents SDK
- Not a protocol gateway
- Not a bidirectional converter (tuple → events only)
- Not an event router or broker
