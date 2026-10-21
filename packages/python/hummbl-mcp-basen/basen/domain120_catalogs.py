# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Explicit local snapshots and read handlers for Domain120 inspection.

Only load_catalogs() reads files. CatalogService methods operate on the retained
snapshot. Supplied digests bind bytes, not source authority or admission.
"""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

from .domain120_inspection import (
    Base120Index, CatalogCollection, CatalogIdentity, CatalogView, FAMILIES,
    InspectionError, OperatorIdentity, PROFILES, SourcePin, _json, _sha, _text,
)

SCHEMA = "hummbl.domain120-inspection-config.v1"
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_CATALOGS = 64
PREFIX = "basen_domain120_"
OPERATIONS = ("catalogs", "inspect", "lookup", "browse", "relations", "source")
TOOL_NAMES = frozenset(PREFIX + operation for operation in OPERATIONS)


def _fields(value, required, optional=(), *, label="object"):
    if not isinstance(value, dict):
        raise InspectionError(f"{label} must be an object")
    if set(value) - set(required) - set(optional) or set(required) - set(value):
        raise InspectionError(f"{label} has missing or unsupported fields")
    return value


def _pin(value):
    _fields(value, ("kind", "path", "sha256"), ("repository", "revision"), label="source")
    return SourcePin(**value)


def _read_limited(path: Path, limit: int) -> bytes:
    try:
        if not path.is_file():
            raise InspectionError("Configured input must be a regular file")
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except OSError as exc:
        raise InspectionError("Configured local input could not be read") from exc
    if len(raw) > limit:
        raise InspectionError("Configured input exceeds the byte limit")
    return raw


def _local_input(root: Path, relative) -> Path:
    _text(relative, "local_path")
    parts = relative.split("/")
    if ("\\" in relative or ":" in relative or PurePosixPath(relative).is_absolute()
            or any(part in ("", ".", "..") for part in parts)):
        raise InspectionError("local_path must be an unambiguous relative POSIX path")
    try:
        resolved = root.joinpath(*parts).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InspectionError("Configured local input could not be resolved") from exc
    if not resolved.is_relative_to(root):
        raise InspectionError("Configured local input escapes the manifest directory")
    return resolved


def load_catalogs(manifest_path, expected_sha256: str) -> "CatalogService":
    """Read one explicitly selected snapshot; never fetch source locators.

    Local configuration is trusted to select data for this process/client.
    Containment and digest checks are not an OS sandbox or an admission gate.
    """
    _sha(expected_sha256, "manifest digest")
    try:
        manifest = Path(manifest_path).resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as exc:
        raise InspectionError("Inspection manifest could not be resolved") from exc
    raw = _read_limited(manifest, MAX_MANIFEST_BYTES)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise InspectionError("Inspection manifest digest mismatch")
    config = _fields(_json(raw), ("schema", "base120", "catalogs"), label="manifest")
    if config["schema"] != SCHEMA:
        raise InspectionError("Unsupported inspection manifest schema")
    base = _fields(config["base120"], ("local_path", "source", "registry_version"),
                   label="base120 input")
    entries = config["catalogs"]
    if not isinstance(entries, list) or len(entries) > MAX_CATALOGS:
        raise InspectionError("catalogs must be an array within the catalog limit")
    root = manifest.parent
    total_bytes = 0

    def read_entry(entry):
        nonlocal total_bytes
        source = _pin(entry["source"])
        input_path = _local_input(root, entry["local_path"])
        content = _read_limited(input_path, MAX_ARTIFACT_BYTES)
        total_bytes += len(content)
        if total_bytes > MAX_TOTAL_BYTES:
            raise InspectionError("Inspection snapshot exceeds the total byte limit")
        source.verify_bytes(content)
        return content, source

    base_raw, base_pin = read_entry(base)
    comparison = Base120Index(base_raw, base_pin, base["registry_version"])
    catalogs = []
    for entry in entries:
        _fields(entry, ("local_path", "source", "profile"), ("namespace",), label="catalog input")
        if entry["profile"] not in PROFILES:
            raise InspectionError("Unsupported catalog input profile")
        content, source = read_entry(entry)
        catalogs.append(CatalogView(content, source, comparison,
                                    profile=entry["profile"], namespace=entry.get("namespace")))
    return CatalogService(catalogs, expected_sha256)


def _identity(value):
    _fields(value, ("namespace", "version", "artifact_sha256"), label="catalog identity")
    return CatalogIdentity(**value)


class CatalogService:
    """Immutable-byte catalog snapshot; returned structures are fresh values."""

    def __init__(self, catalogs, manifest_sha256):
        _sha(manifest_sha256, "manifest digest")
        views = tuple(catalogs)
        self._collection = CatalogCollection(views)
        self._views = {view.identity: view for view in views}
        self._manifest_sha256 = manifest_sha256

    def _context(self, identity):
        report = self._collection.inspect(identity)
        source = self._collection.source_document(identity)
        report["source_distribution_declarations"] = {
            key: source[key] for key in ("license", "visibility") if key in source
        }
        report["distribution_permission"] = "not assessed"
        return report

    def _envelope(self):
        return {
            "schema": "hummbl.domain120-inspection-response.v1",
            "snapshot_manifest_sha256": self._manifest_sha256,
            "snapshot_policy": "Pinned at process startup; source changes require explicit reload/restart",
            "admission": "not assessed", "semantic_validation": "not performed",
            "construction_permission": "not granted", "execution_permission": "not granted",
            "distribution_permission": "not assessed",
        }

    def call(self, name, arguments):
        if not isinstance(name, str) or name not in TOOL_NAMES:
            raise InspectionError("Unsupported Domain120 inspection tool")
        operation = name[len(PREFIX):]
        required = () if operation == "catalogs" else ("catalog",)
        if operation == "lookup":
            required += ("local_code",)
        optional = ("family", "offset", "limit", "context_mode") if operation == "browse" else ()
        _fields(arguments, required, optional, label="tool arguments")
        output = self._envelope()
        if operation == "catalogs":
            output["catalogs"] = [self._context(identity) for identity in self._views]
            output["catalog_count"] = len(self._views)
            return output

        identity = _identity(arguments["catalog"])
        context = self._context(identity)  # Reject absent/ambiguous identity before any projection.
        view = self._views[identity]
        output["catalog_context"] = context
        if operation == "inspect":
            return output
        if operation == "lookup":
            output["operator"] = self._collection.lookup(OperatorIdentity(identity, arguments["local_code"]))
        elif operation == "browse":
            context_mode = arguments.get("context_mode", "per_operator")
            if not isinstance(context_mode, str) or context_mode not in ("per_operator", "shared"):
                raise InspectionError("context_mode must be per_operator or shared")
            family = arguments.get("family")
            if "family" in arguments and (not isinstance(family, str) or family not in FAMILIES):
                raise InspectionError("Unknown family filter")
            offset, limit = arguments.get("offset", 0), arguments.get("limit", 10)
            if type(offset) is not int or offset < 0:
                raise InspectionError("offset must be a nonnegative integer")
            if type(limit) is not int or not 1 <= limit <= 50:
                raise InspectionError("limit must be an integer from 1 to 50")
            codes = view.operator_codes(family)
            shared = context_mode == "shared"
            operators = [view.lookup(code, include_catalog_context=not shared)
                         for code in codes[offset:offset + limit]]
            if shared:
                output["context_mode"] = "shared"
                for operator in operators:
                    operator["catalog_context_ref"] = "/catalog_context"
            output.update({"operators": operators,
                           "matching_count": len(codes), "offset": offset, "limit": limit,
                           "next_offset": offset + limit if offset + limit < len(codes) else None})
        elif operation == "source":
            output["source_document"] = self._collection.source_document(identity)
            output["representation"] = "Parsed source document; exact raw bytes retained in the snapshot"
        elif operation == "relations":
            source = self._collection.source_document(identity)
            declarations = []
            fields = ("composition_matrix", "cross_maps", "parent_map", "parent_core", "world_model")
            for field in fields:
                if field in source:
                    declarations.append({"source_pointer": "/" + field,
                                         "field": field, "declaration": source[field],
                                         "interpretation": "not performed"})
            ancestor_field = ("base120_source" if context["profile"] == "transformations-2026-06-draft"
                              else "base120_ancestor")
            if context["profile"] == "transformations-2026-06-draft":
                records = ((f"/transformations/{family}/{index}", record)
                           for family, rows in source["transformations"].items()
                           for index, record in enumerate(rows))
            else:
                records = ((f"/operators/{index}", record)
                           for index, record in enumerate(source["operators"]))
            for pointer, record in records:
                declarations.append({"source_pointer": pointer + "/" + ancestor_field,
                                     "field": ancestor_field,
                                     "declaration": record[ancestor_field],
                                     "interpretation": "Ancestor ID exists in comparison registry; semantic derivation not assessed"})
            output["declarations"] = declarations
            output["projection_scope"] = {
                "root_fields": list(fields), "operator_field": ancestor_field,
                "complete_relation_ontology": False,
                "full_source_tool": PREFIX + "source",
            }
        return output


def tool_definitions():
    """MCP tool descriptions; returned dictionaries are not shared mutable state."""
    catalog = {
        "type": "object", "additionalProperties": False,
        "properties": {"namespace": {"type": "string"},
                       "version": {"type": ["string", "null"]},
                       "artifact_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}},
        "required": ["namespace", "version", "artifact_sha256"],
    }
    descriptions = {
        "catalogs": "List explicitly configured historical catalog snapshots and their source/authority limits.",
        "inspect": "Inspect one exact catalog snapshot; count and source declarations do not confer admission.",
        "lookup": "Look up a domain-local operator using qualified catalog identity; retain its separate Base120 ancestor.",
        "browse": "Browse a bounded page of operators in one exact catalog, optionally filtered by family code. Opt-in shared context uses references within the decoded tool-result document.",
        "relations": "Read known source relation declarations and pointers without interpreting composition, reuse or closure.",
        "source": "Read the retained source document for one exact catalog, including fields omitted by common projections.",
    }
    results = []
    for operation in OPERATIONS:
        properties = {} if operation == "catalogs" else {"catalog": catalog}
        required = [] if operation == "catalogs" else ["catalog"]
        if operation == "lookup":
            properties["local_code"] = {"type": "string"}
            required.append("local_code")
        if operation == "browse":
            properties.update({"family": {"type": "string", "enum": list(FAMILIES)},
                               "offset": {"type": "integer", "minimum": 0, "default": 0},
                               "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                               "context_mode": {"type": "string", "enum": ["per_operator", "shared"],
                                                "default": "per_operator"}})
        results.append({"name": PREFIX + operation,
                        "description": descriptions[operation] + " Local snapshot read only; no generation, application or promotion.",
                        "inputSchema": {"type": "object", "properties": properties,
                                        "required": required, "additionalProperties": False}})
    return results
