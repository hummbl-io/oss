# Base120 Specification v1.0.0

This document defines the frozen Base120 v1.0.0 substrate.
This version is immutable.

## Scope

This repository governs the **Base120 Artifact Validator**: the deterministic validation pipeline that processes JSON artifacts against the Base120 schema, maps subclasses to Failure Modes, and resolves those Failure Modes to error codes. All validator behavior, registries, and test corpus semantics defined herein are authoritative.

Validation of the **Base120 model corpus itself**—the collection of 120 mental models that constitute the Base120 framework—is explicitly **out of scope** for this specification. The validator validates *artifacts describing or referencing models*; it does not validate the models themselves.

Corpus-level validation (e.g., integrity checks, provenance verification, or semantic correctness of the model collection) is reserved for a separate system and will be governed under its own specification when defined.
