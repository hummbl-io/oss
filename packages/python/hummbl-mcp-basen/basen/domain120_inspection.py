# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Experimental, read-only inspection of existing Domain120 artifacts.

This module performs no file, network, model, ledger or cache operations.
Its three named input profiles describe observed historical formats, not a
new canonical Domain120 schema. Parsing and ancestor lookup do not establish
admission, semantic correspondence, permission to generate, or execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re

FAMILIES = ("P", "IN", "CO", "DE", "RE", "SY")
FAMILY_NAMES = dict(zip(FAMILIES, (
    "Perspective", "Inversion", "Composition", "Decomposition", "Recursion", "Systems"
)))
CAPABILITIES = ("inspect", "lookup", "browse")
PROFILES = ("lattice-object-v0", "transformations-2026-06-draft",
            "research-draft-2026-08")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_NAMESPACE = re.compile(r"domain120\.[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*")
_LOCAL_CODE = re.compile(r"[A-Za-z][A-Za-z0-9._:-]*")


class InspectionError(ValueError):
    """Input cannot be interpreted unambiguously under the selected profile."""


class UnsupportedCapability(InspectionError):
    """The prototype supplies no implementation or authority for this action."""


def _text(value, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise InspectionError(f"{field} must be a nonempty, unpadded string")
    if any(ord(char) < 32 for char in value):
        raise InspectionError(f"{field} must not contain control characters")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise InspectionError(f"{field} must contain valid Unicode") from exc
    return value


def _prose(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InspectionError(f"{field} must contain nonempty text")
    if any(ord(char) < 32 and char not in "\r\n\t" for char in value):
        raise InspectionError(f"{field} contains unsupported control characters")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise InspectionError(f"{field} must contain valid Unicode") from exc
    return value


def _sha(value, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise InspectionError(f"{field} must be a lowercase SHA-256 hex digest")
    return value


def _object(value, field: str) -> dict:
    if not isinstance(value, dict):
        raise InspectionError(f"{field} must be an object")
    return value


def _array(value, field: str) -> list:
    if not isinstance(value, list):
        raise InspectionError(f"{field} must be an array")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InspectionError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise InspectionError(f"Non-JSON numeric constant: {value}")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise InspectionError("JSON numeric value exceeds the supported finite range")
    return result


def _json(raw: bytes):
    if not isinstance(raw, bytes):
        raise InspectionError("Artifact input must be immutable bytes")
    try:
        return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_pairs,
                          parse_constant=_constant, parse_float=_float)
    except InspectionError:
        raise
    except (ValueError, RecursionError) as exc:
        raise InspectionError(f"Invalid UTF-8 JSON: {type(exc).__name__}") from exc


@dataclass(frozen=True)
class SourcePin:
    """Caller-supplied locator. Only the supplied content digest is checked here."""
    kind: str
    path: str
    sha256: str
    repository: str | None = None
    revision: str | None = None

    def __post_init__(self):
        _text(self.path, "source path")
        _sha(self.sha256, "source digest")
        if self.kind == "git":
            _text(self.repository, "repository")
            if not isinstance(self.revision, str) or not re.fullmatch(r"[0-9a-f]{40}", self.revision):
                raise InspectionError("Git revision must be an exact 40-character commit ID")
            if self.path.startswith(("/", "\\")) or "\\" in self.path or ":" in self.path:
                raise InspectionError("Git source path must be repository-relative POSIX text")
            if any(part in ("", ".", "..") for part in self.path.split("/")):
                raise InspectionError("Git source path must not contain ambiguous segments")
        elif self.kind == "local-file":
            if self.repository is not None or self.revision is not None:
                raise InspectionError("Local-file source cannot claim a Git repository/revision")
        else:
            raise InspectionError("Source kind must be git or local-file")

    def verify_bytes(self, raw: bytes):
        if not isinstance(raw, bytes):
            raise InspectionError("Artifact input must be immutable bytes")
        if hashlib.sha256(raw).hexdigest() != self.sha256:
            raise InspectionError("Artifact bytes do not match the supplied digest")

    def report(self):
        return {**asdict(self),
                "locator_authentication": "not performed; caller-supplied metadata"}


@dataclass(frozen=True)
class CatalogIdentity:
    namespace: str
    version: str | None
    artifact_sha256: str

    def __post_init__(self):
        if not isinstance(self.namespace, str) or not _NAMESPACE.fullmatch(self.namespace):
            raise InspectionError("An explicit domain120.<namespace> is required")
        if self.version is not None:
            _text(self.version, "catalog version")
        _sha(self.artifact_sha256, "catalog digest")


@dataclass(frozen=True)
class OperatorIdentity:
    catalog: CatalogIdentity
    local_code: str

    def __post_init__(self):
        if not isinstance(self.catalog, CatalogIdentity):
            raise InspectionError("Operator identity requires a qualified catalog identity")
        if not isinstance(self.local_code, str) or not _LOCAL_CODE.fullmatch(self.local_code):
            raise InspectionError("Operator local code must be an unambiguous identifier")


class Base120Index:
    """Comparison registry, pinned independently from each inspected domain set."""

    def __init__(self, raw: bytes, source: SourcePin, registry_version: str):
        source.verify_bytes(raw)
        _text(registry_version, "Base120 registry version")
        rows = _array(_json(raw), "Base120 SDK registry")
        records = {}
        for row in rows:
            _object(row, "Base120 record")
            code = _text(row.get("code"), "Base120 code")
            if code in records:
                raise InspectionError(f"Duplicate Base120 code: {code}")
            family = row.get("transformation")
            if family not in FAMILIES or not re.fullmatch(re.escape(family) + r"(?:[1-9]|1[0-9]|20)", code):
                raise InspectionError(f"Invalid Base120 code/family: {code}")
            _text(row.get("name"), "Base120 name")
            _prose(row.get("definition"), "Base120 definition")
            records[code] = json.dumps(row, ensure_ascii=True)
        expected = {f"{family}{number}" for family in FAMILIES for number in range(1, 21)}
        if set(records) != expected:
            raise InspectionError("Comparison registry must contain the exact 120 Base120 IDs")
        self._raw = raw
        self._source = source
        self._version = registry_version
        self._records = records

    @property
    def version(self):
        return self._version

    def describe(self):
        return {"registry_version": self._version, "source": self._source.report(),
                "registry_version_origin": "caller-supplied comparison label",
                "registry_version_verification": "not derived from or authenticated against registry bytes",
                "source_digest_check": "matched supplied bytes",
                "record_count": len(self._records), "canonical_authority": "not authenticated"}

    def resolve(self, code: str):
        _text(code, "ancestor code")
        if code not in self._records:
            raise InspectionError(f"Ancestor absent from pinned Base120 registry: {code}")
        return {
            "code": code, "registry_version": self._version,
            "registry_version_origin": "caller-supplied comparison label",
            "registry_version_verification": "not derived from or authenticated against registry bytes",
            "source": self._source.report(),
            "source_digest_check": "matched supplied bytes",
            "record": json.loads(self._records[code]),
            "resolution": "ID exists in supplied comparison registry",
            "semantic_correspondence": "not assessed",
            "historical_derivation": "not authenticated",
        }


@dataclass(frozen=True)
class _Operator:
    code: str
    family: str
    name: str
    definition: str
    domain_adaptation: str | None
    ancestor: str
    declared_status: str | None
    pointer: str
    record_json: str
    not_projected: tuple[str, ...]


class CatalogView:
    """Validated inspection profile over retained raw bytes; not a lifecycle gate."""

    def __init__(self, raw: bytes, source: SourcePin, base120: Base120Index, *,
                 profile: str, namespace: str | None = None):
        source.verify_bytes(raw)
        if not isinstance(base120, Base120Index):
            raise InspectionError("An explicit Base120 comparison registry is required")
        if profile not in PROFILES:
            raise InspectionError(f"Unsupported input profile: {profile!r}")
        document = _object(_json(raw), "Domain120 artifact")
        self._raw = raw
        self._source = source
        self._base120 = base120
        self._profile = profile
        domain_key = "lattice_id" if profile == "research-draft-2026-08" else "domain"
        self._domain = _text(document.get(domain_key), domain_key)
        self._field_sources = {
            "domain": "/" + domain_key,
            "declared_set_status": "/status" if "status" in document else None,
            "declared_operator_status": "operator /status" if profile == "lattice-object-v0" else None,
        }
        self._declared_status = document.get("status")
        if self._declared_status is not None:
            _text(self._declared_status, "declared set status")
        self._namespace_origin = "caller-assigned; global uniqueness not authenticated"
        if profile == "lattice-object-v0":
            if "transformations" in document:
                raise InspectionError("Ambiguous mixed lattice/transformations profiles")
            version = _text(document.get("version"), "catalog version")
            self._version_origin = "declared by source /version; release authority not authenticated"
            self._identity = CatalogIdentity(namespace, version, source.sha256)
            self._operators = self._lattice(document)
            consumed = {"domain", "version", "operators"}
            self._base_binding = "Comparison registry supplied for inspection; source has no required raw pin"
        elif profile == "transformations-2026-06-draft":
            if "operators" in document:
                raise InspectionError("Ambiguous mixed transformations/lattice profiles")
            set_id = _text(document.get("set_id"), "set_id")
            match = re.fullmatch(r"(domain120\.([a-z-]+))\.v(\d+\.\d+\.\d+)", set_id)
            if not match or match[2] != self._domain:
                raise InspectionError("Historical set_id must bind domain and declared version")
            if namespace is not None and namespace != match[1]:
                raise InspectionError("Supplied namespace conflicts with source set_id")
            if document.get("family") != "Domain120":
                raise InspectionError("Historical family discriminator must be Domain120")
            self._identity = CatalogIdentity(match[1], match[3], source.sha256)
            self._version_origin = "parsed from source /set_id; release authority not authenticated"
            self._namespace_origin = "declared by source set_id; global uniqueness not authenticated"
            if document.get("base_architecture") != "base120.v" + base120.version:
                raise InspectionError("Source Base120 version declaration differs from caller-supplied comparison label")
            self._operators = self._transformations(document)
            consumed = {"domain", "set_id", "family", "base_architecture", "transformations"}
            self._base_binding = (
                "Source version declaration matches caller-supplied comparison label only; "
                "registry version not authenticated; raw comparison pin supplied for inspection"
            )
        else:
            ambiguous = {"domain", "version", "set_id", "transformations", "status",
                         "composition_matrix", "base_architecture", "family"} & set(document)
            if ambiguous:
                raise InspectionError("Mixed research/other profile fields: " + ", ".join(sorted(ambiguous)))
            self._identity = CatalogIdentity(namespace, None, source.sha256)
            self._version_origin = "absent from source; unknown, not inferred from revision or digest"
            self._field_sources["declared_operator_status"] = "operator /state"
            self._operators = self._research(document)
            consumed = {"lattice_id", "operators", "domain_pillar", "epistemic_pillar",
                        "maturity", "dimensions", "capacity"}
            self._base_binding = "Comparison registry supplied for inspection; source has no required raw pin"
        consumed.update({"status", "schema_version"})
        self._root_not_projected = tuple(sorted(set(document) - consumed))
        self._by_code = {}
        for operator in self._operators:
            if operator.code in self._by_code:
                raise InspectionError(f"Duplicate local operator code: {operator.code}")
            base120.resolve(operator.ancestor)
            self._by_code[operator.code] = operator

    def _operator(self, row, family, pointer, *, historical, status_key="status"):
        _object(row, pointer)
        if family not in FAMILIES:
            raise InspectionError(f"Unknown family at {pointer}")
        code_key = "id" if historical else "code"
        definition_key = "description" if historical else "definition"
        ancestor_key = "base120_source" if historical else "base120_ancestor"
        code = _text(row.get(code_key), pointer + "/" + code_key)
        OperatorIdentity(self._identity, code)
        name = _text(row.get("name"), pointer + "/name")
        definition = _prose(row.get(definition_key), pointer + "/" + definition_key)
        ancestor = _text(row.get(ancestor_key), pointer + "/" + ancestor_key)
        adaptation = None
        declared_status = None
        consumed = {code_key, "name", definition_key, ancestor_key}
        if historical:
            adaptation = _prose(row.get("domain_adaptation"), pointer + "/domain_adaptation")
            consumed.add("domain_adaptation")
        else:
            consumed.add("family")
            if status_key in row:
                declared_status = _text(row[status_key], pointer + "/" + status_key)
                consumed.add(status_key)
        return _Operator(code, family, name, definition, adaptation, ancestor,
                         declared_status, pointer, json.dumps(row, ensure_ascii=True),
                         tuple(sorted(set(row) - consumed)))

    def _lattice(self, document):
        rows = _array(document.get("operators"), "operators")
        operators = tuple(self._operator(row, _object(row, "operator").get("family"),
                                         f"/operators/{index}", historical=False)
                          for index, row in enumerate(rows))
        if "composition_matrix" in document:
            matrix = _object(document["composition_matrix"], "composition_matrix")
            for family, row in matrix.items():
                if family not in FAMILIES:
                    raise InspectionError("Unknown composition row family")
                for target, state in _object(row, "composition row").items():
                    if target not in FAMILIES or state not in ("undefined", "admissible", "inadmissible", "deprecated"):
                        raise InspectionError("Unknown composition family or state")
        if "cross_maps" in document:
            known = {op.code for op in operators}
            seen = set()
            for mapping in _array(document["cross_maps"], "cross_maps"):
                _object(mapping, "cross-map")
                key = tuple(_text(mapping.get(field), "cross-map " + field)
                            for field in ("to", "operator", "cousin"))
                if key[1] not in known:
                    raise InspectionError("Cross-map refers to absent local operator")
                if key in seen:
                    raise InspectionError("Duplicate cross-map")
                seen.add(key)
        return operators

    def _transformations(self, document):
        groups = _object(document.get("transformations"), "transformations")
        if set(groups) != set(FAMILIES):
            raise InspectionError("Historical profile requires exactly six transformation families")
        operators = []
        for family in FAMILIES:
            rows = _array(groups[family], "transformations/" + family)
            if len(rows) > 20:
                raise InspectionError("Historical profile permits at most 20 records per family")
            operators.extend(self._operator(row, family, f"/transformations/{family}/{index}",
                                             historical=True)
                             for index, row in enumerate(rows))
        return tuple(operators)

    def _research(self, document):
        # Observed draft shape only. No lifecycle, cardinality or pillar authority.
        for field in ("domain_pillar", "epistemic_pillar", "maturity"):
            _text(document.get(field), field)
        for dimension in _array(document.get("dimensions"), "dimensions"):
            _text(dimension, "dimension")
        capacity = document.get("capacity")
        if type(capacity) is not int or capacity <= 0:
            raise InspectionError("Declared capacity must be a positive integer")
        operators = []
        for index, row in enumerate(_array(document.get("operators"), "operators")):
            pointer = f"/operators/{index}"
            _object(row, pointer)
            _text(row.get("state"), pointer + "/state")
            if "status" in row:
                raise InspectionError("Mixed research state and lattice status fields")
            operators.append(self._operator(row, row.get("family"), pointer,
                                             historical=False, status_key="state"))
        for mapping in _array(document.get("cross_maps"), "cross_maps"):
            _object(mapping, "research cross-map")
            for field in ("from", "to", "operator"):
                _text(mapping.get(field), "research cross-map " + field)
            _prose(mapping.get("reason"), "research cross-map reason")
        # Endpoints deliberately remain uninterpreted: the historical examples
        # use matching code strings and do not establish direction or semantics.
        return tuple(operators)

    @property
    def identity(self):
        return self._identity

    def source_bytes(self):
        """Return the exact immutable bytes, including unknown fields and whitespace."""
        return self._raw

    def source_document(self):
        """Return a fresh parsed copy. Mutating it cannot change this view."""
        return _json(self._raw)

    def inspect(self):
        document = self.source_document()
        return {
            "schema": "domain120.experimental-inspection.v2",
            "identity": asdict(self._identity), "source": self._source.report(),
            "source_digest_check": "matched supplied bytes",
            "profile": self._profile, "domain": self._domain,
            "namespace_origin": self._namespace_origin,
            "version_origin": self._version_origin,
            "field_sources": dict(self._field_sources),
            "declared_research_metadata": {
                key: document[key]
                for key in ("domain_pillar", "epistemic_pillar", "maturity", "dimensions", "capacity")
                if self._profile == "research-draft-2026-08"
            },
            "research_metadata_authority": "Source declarations only; no ontology, cardinality or lifecycle validation",
            "declared_schema": document.get("schema_version"),
            "declared_set_status": self._declared_status,
            "inspection_status": "parsed",
            "inspection_scope": "Named input shape, identifiers, fields and ancestor-ID existence only",
            "operator_count": len(self._operators),
            "family_counts": {f: sum(op.family == f for op in self._operators) for f in FAMILIES},
            "base120_binding": self._base_binding,
            "base120_comparison": self._base120.describe(),
            "capabilities": list(CAPABILITIES),
            "admission": "not assessed",
            "semantic_validation": "not performed",
            "construction_permission": "not granted",
            "execution_permission": "not granted",
            "projection": {
                "root_fields_not_in_common_view": list(self._root_not_projected),
                "operator_fields_not_in_common_view": [
                    {"pointer": op.pointer, "fields": list(op.not_projected)}
                    for op in self._operators if op.not_projected
                ],
                "retention": "All fields remain in source_bytes/source_document and source records",
                "relations": "Composition/cross-map/review/world-model content retained, not interpreted",
            },
        }

    def lookup(self, local_code: str, *, include_catalog_context: bool = True):
        """Project a record; omit context only when its caller supplies that context."""
        OperatorIdentity(self._identity, local_code)
        if local_code not in self._by_code:
            raise InspectionError(f"Operator absent from this catalog: {local_code}")
        op = self._by_code[local_code]
        return {
            "identity": asdict(OperatorIdentity(self._identity, op.code)),
            **({"catalog_context": self.inspect()} if include_catalog_context else {}),
            "family": op.family, "family_name": FAMILY_NAMES[op.family], "name": op.name,
            "family_name_origin": "Prototype comparison labels, not authenticated source family semantics",
            "family_semantic_equivalence": "not assessed",
            "reasoning": {"definition": op.definition, "domain_adaptation": op.domain_adaptation},
            "declared_operator_status": op.declared_status,
            "ancestor": self._base120.resolve(op.ancestor),
            "source_pointer": op.pointer, "source_record": json.loads(op.record_json),
            "not_projected_fields": list(op.not_projected),
            "admission": "not assessed", "semantic_validation": "not performed",
            "construction_permission": "not granted", "execution_permission": "not granted",
        }

    def operator_codes(self, family: str | None = None):
        """Lightweight selection before an application projects a bounded page."""
        if family is not None and family not in FAMILIES:
            raise InspectionError("Unknown family filter")
        return tuple(op.code for op in self._operators
                     if family is None or op.family == family)

    def browse(self, family: str | None = None):
        if family is not None and family not in FAMILIES:
            raise InspectionError("Unknown family filter")
        return [self.lookup(op.code) for op in self._operators
                if family is None or op.family == family]

    def request(self, capability: str, **arguments):
        if capability not in CAPABILITIES:
            raise UnsupportedCapability(f"Unsupported capability: {capability!r}")
        expected = {"inspect": set(), "lookup": {"local_code"}, "browse": {"family"}}[capability]
        if set(arguments) - expected:
            raise InspectionError("Unsupported request arguments")
        if capability == "inspect":
            return self.inspect()
        if capability == "lookup":
            if "local_code" not in arguments:
                raise InspectionError("lookup requires local_code")
            return self.lookup(arguments["local_code"])
        return self.browse(arguments.get("family"))


class CatalogCollection:
    """Explicit qualified lookup across multiple existing catalogs."""

    def __init__(self, catalogs):
        self._catalogs = {}
        versions = {}
        for catalog in catalogs:
            if not isinstance(catalog, CatalogView):
                raise InspectionError("Collection entries must be inspected catalogs")
            identity = catalog.identity
            version_key = (identity.namespace, identity.version)
            if (identity.version is not None and version_key in versions
                    and versions[version_key] != identity.artifact_sha256):
                raise InspectionError("Conflicting content for the same catalog namespace/version")
            if identity in self._catalogs:
                raise InspectionError("Duplicate qualified catalog identity")
            if identity.version is not None:
                versions[version_key] = identity.artifact_sha256
            self._catalogs[identity] = catalog

    def _catalog(self, identity: CatalogIdentity):
        if not isinstance(identity, CatalogIdentity):
            raise InspectionError("Collection retrieval requires a qualified catalog identity")
        if identity not in self._catalogs:
            raise InspectionError("Qualified catalog identity is absent")
        return self._catalogs[identity]

    def inspect(self, identity: CatalogIdentity):
        return self._catalog(identity).inspect()

    def source_bytes(self, identity: CatalogIdentity):
        return self._catalog(identity).source_bytes()

    def source_document(self, identity: CatalogIdentity):
        return self._catalog(identity).source_document()

    def lookup(self, identity: OperatorIdentity):
        if not isinstance(identity, OperatorIdentity):
            raise InspectionError("Collection lookup requires a qualified operator identity")
        return self._catalog(identity.catalog).lookup(identity.local_code)
