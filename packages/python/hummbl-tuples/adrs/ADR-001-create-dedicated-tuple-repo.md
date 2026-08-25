# ADR-001: Create Dedicated Tuple Repo

Date: 2026-03-27
Status: accepted

## Context

Tuple artifacts are currently scattered across HUMMBL repos and local operational state. That makes publication, external review, and standards-oriented development harder than necessary.

## Decision

Create a dedicated repo for tuple semantics, schemas, examples, comparisons, and research notes.

## Consequences

- clearer public story
- easier to publish and cite
- cleaner separation between canonical tuple ideas and repo-specific adapters
- requires explicit synchronization with implementation repos
