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

"""Schema Validator -- Stdlib-only JSON Schema validator (Draft 2020-12 subset).

Supported keywords:
    type, required, properties, enum, pattern, minimum, maximum,
    minLength, maxLength, minItems, maxItems, items, additionalProperties,
    const, oneOf, anyOf, $ref, $defs, $id

``$ref`` resolution:
    Local document references of the form ``#/$defs/<name>`` and arbitrary
    JSON-pointer fragments (``#/path/to/def``) are resolved against the root
    schema. Cross-document references are resolved through an optional
    :class:`RefRegistry` keyed by document ``$id`` (or an explicit alias).
    Cycles are detected and reported; resolution never fetches remote URIs.

Usage:
    from hummbl_governance import SchemaValidator

    validator = SchemaValidator()
    errors = validator.validate({"name": "test"}, {"type": "object", "required": ["name"]})
    # errors == []  (valid)

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# JSON Schema type name -> Python type(s)
_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
    "null": (type(None),),
}


class ValidationError(Exception):
    """Raised when a value fails schema validation."""

    def __init__(self, message: str, path: str = "") -> None:
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


class RefResolutionError(Exception):
    """Raised when a ``$ref`` cannot be resolved."""


class RefRegistry:
    """Registry of schemas addressable by ``$id`` or an explicit alias.

    The registry holds parsed schema documents. A schema's ``$id`` (when
    present) is used as its canonical key; callers may also register aliases.
    The registry performs no remote fetching -- every document must be loaded
    explicitly by the caller.
    """

    def __init__(self) -> None:
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(self, schema: dict[str, Any], alias: str | None = None) -> str:
        """Register *schema* and return the key it is addressable by.

        If *schema* declares a top-level ``$id``, that value is the canonical
        key. *alias* registers an additional addressable name. At least one of
        ``$id`` or *alias* must be available.
        """
        key = schema.get("$id") or alias
        if not key:
            raise RefResolutionError(
                "schema has no $id and no alias was supplied; cannot register"
            )
        self._schemas[key] = schema
        if alias and alias != key:
            self._schemas[alias] = schema
        return key

    def get(self, key: str) -> dict[str, Any] | None:
        return self._schemas.get(key)

    def __contains__(self, key: object) -> bool:
        return key in self._schemas

    def __len__(self) -> int:
        return len(self._schemas)


class _Resolver:
    """Resolves ``$ref`` values against a root schema and optional registry.

    Resolution rules (Draft 2020-12 subset):

    * ``#`` -> the root document.
    * ``#/<json-pointer>`` -> a node within the root document.
    * ``<uri>#`` or ``<uri>#/<json-pointer>`` -> a registered document (matched
      by ``$id`` or alias) followed by an optional fragment pointer.

    Remote URIs are never fetched; an unregistered document reference raises
    :class:`RefResolutionError`.
    """

    def __init__(
        self,
        root: dict[str, Any],
        registry: RefRegistry | None = None,
    ) -> None:
        self.root = root
        self.registry = registry
        # Resolve the root document's own $id so absolute refs can be normalized.
        self.base_id = root.get("$id") if isinstance(root, dict) else None

    def resolve(self, ref: str) -> dict[str, Any]:
        if not isinstance(ref, str):
            raise RefResolutionError(f"$ref must be a string, got {type(ref).__name__}")

        if ref.startswith("#"):
            return self._resolve_fragment(self.root, ref[1:])

        # Split into document part and fragment.
        fragment_index = ref.find("#")
        if fragment_index == -1:
            document_part, fragment = ref, ""
        else:
            document_part, fragment = ref[:fragment_index], ref[fragment_index + 1 :]

        if document_part == "":
            return self._resolve_fragment(self.root, fragment)

        if self.registry is None:
            raise RefResolutionError(
                f"$ref {ref!r} targets another document but no registry was provided"
            )
        document = self.registry.get(document_part)
        if document is None:
            raise RefResolutionError(
                f"$ref {ref!r} targets unregistered document {document_part!r}"
            )
        return self._resolve_fragment(document, fragment)

    @staticmethod
    def _resolve_fragment(document: dict[str, Any], fragment: str) -> dict[str, Any]:
        if fragment == "" or fragment == "/":
            return document
        if not fragment.startswith("/"):
            raise RefResolutionError(f"unsupported fragment {fragment!r}; expected a JSON pointer")
        node: Any = document
        for token in fragment.split("/")[1:]:
            token = token.replace("~1", "/").replace("~0", "~")
            if isinstance(node, list):
                try:
                    node = node[int(token)]
                except (ValueError, IndexError) as exc:
                    raise RefResolutionError(
                        f"fragment token {token!r} is not a valid array index"
                    ) from exc
            elif isinstance(node, dict):
                if token not in node:
                    raise RefResolutionError(f"fragment token {token!r} not found in document")
                node = node[token]
            else:
                raise RefResolutionError(
                    f"fragment token {token!r} cannot descend into {type(node).__name__}"
                )
        if not isinstance(node, dict):
            raise RefResolutionError("$ref target must be a schema object")
        return node


class SchemaValidator:
    """JSON Schema validator using only Python stdlib.

    Supports a subset of Draft 2020-12 sufficient for validating
    structured governance data, including ``$ref`` resolution against the
    root document and an optional :class:`RefRegistry`.
    """

    @staticmethod
    def validate(
        instance: Any,
        schema: dict[str, Any],
        path: str = "",
        registry: RefRegistry | None = None,
    ) -> list[str]:
        """Validate *instance* against *schema*.

        Returns a list of error strings (empty = valid).
        """
        resolver = _Resolver(schema, registry)
        return _validate(instance, schema, path, resolver=resolver)

    @staticmethod
    def validate_file(
        instance_path: str | Path,
        schema_path: str | Path,
        registry: RefRegistry | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate a JSON file against a JSON Schema file.

        Returns (is_valid, errors).  JSON decode errors in either file are
        reported as validation errors rather than raised.
        """
        try:
            instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, [f"instance file {instance_path!s}: invalid JSON: {exc}"]
        except OSError as exc:
            return False, [f"instance file {instance_path!s}: {exc}"]
        try:
            schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, [f"schema file {schema_path!s}: invalid JSON: {exc}"]
        except OSError as exc:
            return False, [f"schema file {schema_path!s}: {exc}"]
        errors = SchemaValidator.validate(instance, schema, registry=registry)
        return len(errors) == 0, errors

    @staticmethod
    def validate_dict(
        entry: dict[str, Any],
        schema: dict[str, Any],
        registry: RefRegistry | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate a dictionary against a schema.

        Returns (is_valid, errors).
        """
        errors = SchemaValidator.validate(entry, schema, registry=registry)
        return len(errors) == 0, errors


def _check_type(instance: Any, schema: dict[str, Any], path: str) -> str | None:
    """Check type constraint. Returns error string or None."""
    if "type" not in schema:
        return None
    type_name = schema["type"]
    if isinstance(type_name, list):
        expected = tuple(t for name in type_name for t in _TYPE_MAP.get(name, ()))
    else:
        expected = _TYPE_MAP.get(type_name, ())
    if expected and not isinstance(instance, expected):
        return f"{path}: expected type {type_name!r}, got {type(instance).__name__}"
    return None


def _validate(
    instance: Any,
    schema: dict[str, Any],
    path: str = "",
    depth: int = 0,
    max_depth: int = 50,
    resolver: _Resolver | None = None,
    ref_stack: tuple[str, ...] = (),
) -> list[str]:
    """Core validation logic -- dispatches to type-specific validators."""
    if depth > max_depth:
        return [f"{path}: schema depth exceeds max_depth {max_depth}"]

    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object, got {type(schema).__name__}"]

    # $ref resolution (Draft 2020-12: $ref may appear alongside other keywords).
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in ref_stack:
            return [f"{path}: circular $ref {ref!r} detected"]
        if resolver is None:
            return [f"{path}: $ref {ref!r} present but no resolver was provided"]
        try:
            target = resolver.resolve(ref)
        except RefResolutionError as exc:
            return [f"{path}: {exc}"]
        # Validate against the resolved target, then apply sibling keywords
        # present on the referring schema (Draft 2020-12 behavior).
        errors = _validate(
            instance,
            target,
            path,
            depth=depth,
            max_depth=max_depth,
            resolver=resolver,
            ref_stack=ref_stack + (ref,),
        )
        sibling = {k: v for k, v in schema.items() if k != "$ref"}
        if sibling:
            errors.extend(
                _validate(
                    instance,
                    sibling,
                    path,
                    depth=depth,
                    max_depth=max_depth,
                    resolver=resolver,
                    ref_stack=ref_stack,
                )
            )
        return errors

    # const (early return)
    if "const" in schema and instance != schema["const"]:
        return [f"{path}: expected const {schema['const']!r}, got {instance!r}"]

    # type check (early return on mismatch)
    type_error = _check_type(instance, schema, path)
    if type_error:
        return [type_error]

    errors: list[str] = []

    # enum
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")

    # type-specific validation
    next_depth = depth + 1
    if isinstance(instance, str):
        errors.extend(_validate_string(instance, schema, path))
    elif isinstance(instance, (int, float)):
        errors.extend(_validate_number(instance, schema, path))
    elif isinstance(instance, dict):
        errors.extend(_validate_object(instance, schema, path, next_depth, max_depth, resolver, ref_stack))
    elif isinstance(instance, list):
        errors.extend(_validate_array(instance, schema, path, next_depth, max_depth, resolver, ref_stack))

    # composition keywords
    errors.extend(_validate_composition(instance, schema, path, next_depth, max_depth, resolver, ref_stack))

    return errors


def _validate_string(instance: str, schema: dict[str, Any], path: str) -> list[str]:
    """Validate string-specific keywords: pattern, minLength, maxLength."""
    errors: list[str] = []
    if "pattern" in schema:
        try:
            if not re.search(schema["pattern"], instance):
                errors.append(f"{path}: {instance!r} does not match pattern {schema['pattern']!r}")
        except re.error as e:
            errors.append(f"{path}: invalid regex pattern {schema['pattern']!r}: {e}")
    if "minLength" in schema and len(instance) < schema["minLength"]:
        errors.append(f"{path}: string length {len(instance)} < minLength {schema['minLength']}")
    if "maxLength" in schema and len(instance) > schema["maxLength"]:
        errors.append(f"{path}: string length {len(instance)} > maxLength {schema['maxLength']}")
    return errors


def _validate_number(instance: int | float, schema: dict[str, Any], path: str) -> list[str]:
    """Validate number-specific keywords: minimum, maximum."""
    errors: list[str] = []
    if "minimum" in schema and instance < schema["minimum"]:
        errors.append(f"{path}: {instance} < minimum {schema['minimum']}")
    if "maximum" in schema and instance > schema["maximum"]:
        errors.append(f"{path}: {instance} > maximum {schema['maximum']}")
    return errors


def _validate_object(
    instance: dict,
    schema: dict[str, Any],
    path: str,
    depth: int,
    max_depth: int,
    resolver: _Resolver | None = None,
    ref_stack: tuple[str, ...] = (),
) -> list[str]:
    """Validate object-specific keywords: required, properties, additionalProperties."""
    errors: list[str] = []
    for req in schema.get("required", []):
        if req not in instance:
            errors.append(f"{path}: missing required property {req!r}")

    props = schema.get("properties", {})
    for key, prop_schema in props.items():
        if key in instance:
            sub_path = f"{path}.{key}" if path else key
            errors.extend(
                _validate(
                    instance[key],
                    prop_schema,
                    sub_path,
                    depth,
                    max_depth,
                    resolver=resolver,
                    ref_stack=ref_stack,
                )
            )

    if "additionalProperties" in schema:
        errors.extend(
            _validate_additional_props(
                instance, schema["additionalProperties"], props, path, depth, max_depth, resolver, ref_stack
            )
        )
    return errors


def _validate_additional_props(
    instance: dict,
    ap: bool | dict,
    known_props: dict[str, Any],
    path: str,
    depth: int,
    max_depth: int,
    resolver: _Resolver | None = None,
    ref_stack: tuple[str, ...] = (),
) -> list[str]:
    """Validate additionalProperties constraint."""
    errors: list[str] = []
    known_keys = set(known_props.keys())
    for key in instance:
        if key not in known_keys:
            if ap is False:
                errors.append(f"{path}: unexpected property {key!r}")
            elif isinstance(ap, dict):
                sub_path = f"{path}.{key}" if path else key
                errors.extend(
                    _validate(
                        instance[key],
                        ap,
                        sub_path,
                        depth,
                        max_depth,
                        resolver=resolver,
                        ref_stack=ref_stack,
                    )
                )
    return errors


def _validate_array(
    instance: list,
    schema: dict[str, Any],
    path: str,
    depth: int,
    max_depth: int,
    resolver: _Resolver | None = None,
    ref_stack: tuple[str, ...] = (),
) -> list[str]:
    """Validate array-specific keywords: minItems, maxItems, items."""
    errors: list[str] = []
    if "minItems" in schema and len(instance) < schema["minItems"]:
        errors.append(f"{path}: array length {len(instance)} < minItems {schema['minItems']}")
    if "maxItems" in schema and len(instance) > schema["maxItems"]:
        errors.append(f"{path}: array length {len(instance)} > maxItems {schema['maxItems']}")
    if "items" in schema:
        for i, item in enumerate(instance):
            errors.extend(
                _validate(
                    item,
                    schema["items"],
                    f"{path}[{i}]",
                    depth,
                    max_depth,
                    resolver=resolver,
                    ref_stack=ref_stack,
                )
            )
    return errors


def _validate_composition(
    instance: Any,
    schema: dict[str, Any],
    path: str,
    depth: int,
    max_depth: int,
    resolver: _Resolver | None = None,
    ref_stack: tuple[str, ...] = (),
) -> list[str]:
    """Validate composition keywords: oneOf, anyOf."""
    errors: list[str] = []
    if "oneOf" in schema:
        match_count = sum(
            1
            for s in schema["oneOf"]
            if not _validate(instance, s, path, depth, max_depth, resolver=resolver, ref_stack=ref_stack)
        )
        if match_count != 1:
            errors.append(f"{path}: expected exactly one of oneOf to match, got {match_count}")
    if "anyOf" in schema and not any(
        not _validate(instance, s, path, depth, max_depth, resolver=resolver, ref_stack=ref_stack)
        for s in schema["anyOf"]
    ):
        errors.append(f"{path}: none of anyOf schemas matched")
    return errors
