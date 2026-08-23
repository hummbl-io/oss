# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Cross-repo contract enforcement layer.

This module sits on top of :mod:`hummbl_governance.cross_repo_contract` and the
``$ref``-capable :class:`~hummbl_governance.schema_validator.SchemaValidator`.
It provides a single entry point that:

1. Loads the candidate v0.1 contract and shared-reference schemas.
2. Builds a :class:`RefRegistry` so the contract schema can ``$ref`` into the
   shared definition library instead of inlining equivalent shapes.
3. Validates a contract document (and optional compatibility manifest) through
   both the schema layer and the semantic rules in
   :mod:`hummbl_governance.cross_repo_contract`.

Enforcement establishes declared structural and semantic compatibility only.
It does not establish truth, security, canon status, or deployment authority,
and it does not perform remote URI dereferencing.

Stdlib-only.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from importlib.resources import files  # nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2
from pathlib import Path
from typing import Any

from hummbl_governance.cross_repo_contract import (
    validate_compatibility_manifest,
    validate_contract_document,
)
from hummbl_governance.schema_validator import RefRegistry, SchemaValidator

_CONTRACT_SCHEMA = "cross_repo_contract_v0.1.schema.json"
_COMPATIBILITY_SCHEMA = "cross_repo_compatibility_manifest_v0.1.schema.json"
_SHARED_REFS_SCHEMA = "cross_repo_shared_refs_v0.1.schema.json"


def _load_packaged_schema(name: str) -> dict[str, Any]:
    resource = files("hummbl_governance").joinpath("data", name)
    return json.loads(resource.read_text(encoding="utf-8"))


def build_contract_registry() -> RefRegistry:
    """Build a :class:`RefRegistry` containing the v0.1 shared definitions.

    The shared-refs schema declares an ``$id`` so contract schemas can
    reference definitions such as
    ``https://hummbl.io/schemas/cross-repo-shared-refs-v0.1.schema.json#/$defs/repo_ref``.
    """
    registry = RefRegistry()
    shared = _load_packaged_schema(_SHARED_REFS_SCHEMA)
    registry.register(shared)
    return registry


@dataclass
class EnforcementResult:
    """Outcome of an enforcement check.

    ``errors`` is empty when the document is valid. ``schema_errors`` and
    ``semantic_errors`` partition the failures by source so callers can
    distinguish structural from semantic problems.
    """

    is_valid: bool
    schema_errors: list[str] = field(default_factory=list)
    semantic_errors: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[str]:
        return [*self.schema_errors, *self.semantic_errors]


def enforce_contract(
    contract: dict[str, Any],
    *,
    registry: RefRegistry | None = None,
) -> EnforcementResult:
    """Enforce the v0.1 contract schema and semantic rules on *contract*.

    The schema is validated with ``$ref`` resolution enabled. Semantic rules
    from :mod:`hummbl_governance.cross_repo_contract` are then applied.
    """
    if registry is None:
        registry = build_contract_registry()
    schema = _load_packaged_schema(_CONTRACT_SCHEMA)
    schema_errors = [
        f"schema: {error}"
        for error in SchemaValidator.validate(contract, schema, registry=registry)
    ]
    if schema_errors:
        return EnforcementResult(is_valid=False, schema_errors=schema_errors)
    semantic_errors = validate_contract_document(contract)
    # validate_contract_document re-runs the schema check; strip the duplicate
    # schema-prefixed errors since we already collected them above.
    semantic_errors = [e for e in semantic_errors if not e.startswith("schema:")]
    return EnforcementResult(
        is_valid=not semantic_errors,
        semantic_errors=semantic_errors,
    )


def enforce_compatibility_manifest(
    manifest: dict[str, Any],
    contract: dict[str, Any] | None = None,
    *,
    registry: RefRegistry | None = None,
) -> EnforcementResult:
    """Enforce the v0.1 compatibility manifest schema and semantic rules.

    When *contract* is supplied, the manifest is cross-validated against it.
    """
    if registry is None:
        registry = build_contract_registry()
    schema = _load_packaged_schema(_COMPATIBILITY_SCHEMA)
    schema_errors = [
        f"schema: {error}"
        for error in SchemaValidator.validate(manifest, schema, registry=registry)
    ]
    if schema_errors:
        return EnforcementResult(is_valid=False, schema_errors=schema_errors)
    semantic_errors = validate_compatibility_manifest(manifest, contract)
    semantic_errors = [e for e in semantic_errors if not e.startswith("schema:")]
    # Partition contract-originated errors as schema errors for clarity.
    contract_origin = [e for e in semantic_errors if e.startswith("contract:")]
    pure_semantic = [e for e in semantic_errors if not e.startswith("contract:")]
    return EnforcementResult(
        is_valid=not (contract_origin or pure_semantic),
        schema_errors=contract_origin,
        semantic_errors=pure_semantic,
    )


def enforce_files(
    contract_path: str | Path,
    manifest_path: str | Path | None = None,
    *,
    registry: RefRegistry | None = None,
) -> EnforcementResult:
    """Enforce contract and optional manifest files from disk."""
    contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    if manifest_path is None:
        return enforce_contract(contract, registry=registry)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    return enforce_compatibility_manifest(manifest, contract, registry=registry)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point mirroring ``hummbl_governance.cross_repo_contract``."""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Enforce HUMMBL candidate cross-repo contracts with $ref resolution. "
            "A pass establishes declared structural and semantic compatibility only."
        )
    )
    parser.add_argument("contract", help="Path to a cross-repo contract JSON document")
    parser.add_argument(
        "--manifest",
        help="Optional compatibility manifest JSON document to validate against the contract",
    )
    args = parser.parse_args(argv)

    try:
        result = enforce_files(args.contract, args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not result.is_valid:
        print("INVALID")
        for error in result.errors:
            print(f"- {error}")
        return 1

    print("VALID")
    print(
        "Enforcement establishes declared structural and semantic compatibility only; "
        "it does not establish truth, security, canon status, or deployment authority."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
