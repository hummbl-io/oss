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
# SPDX-License-Identifier: Apache-2.0

"""Pure comparison for a bounded source-to-pull-mirror Git deployment probe.

The evaluator accepts already-normalized, allowlisted observations. It has no
transport, filesystem, subprocess, credential, synchronization, or publishing
capability. A successful receipt records only that caller-supplied required refs
matched their expected full object IDs in both declarations. It does not prove
provider truth, privacy, full mirror parity, freshness, object availability, or
collector honesty.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit


PROBE_CONTRACT_VERSION = "0.1.0"
PROBE_COMPARISON_PROFILE = "gitops-bounded-required-refs-v0"

_ALIAS_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*$")
_HOST_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
_NUMERIC_HOST_PATTERN = re.compile(r"^(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+)){0,3}$")
_PATH_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_HEX_PATTERN = re.compile(r"^[0-9a-f]+$")
_RESERVED_ALIAS_NAMESPACES = frozenset({"file", "ftp", "git", "http", "https", "sftp", "ssh"})
_OBJECT_ID_LENGTH = {"sha1": 40, "sha256": 64}
_MAX_JSON_DEPTH = 32
_MAX_COLLECTION_ITEMS = 4096
_MAX_STRING_LENGTH = 8192
_MAX_ALIAS_LENGTH = 256
_MAX_REPOSITORY_IDENTITY_LENGTH = 2048
_MAX_REF_LENGTH = 1024
_MAX_JCS_INTEGER = (1 << 53) - 1

_EXPECTED_FIELDS = frozenset(
    {
        "comparison_profile",
        "contract_version",
        "expectation_id",
        "mirror_alias",
        "mirror_repository_identity",
        "object_format",
        "required_refs",
        "source_alias",
        "source_repository_identity",
    }
)
_OBSERVED_FIELDS = frozenset({"mirror", "source"})
_SOURCE_FIELDS = frozenset(
    {
        "alias",
        "object_format",
        "observation_complete",
        "private",
        "refs",
        "repository_identity",
        "role",
    }
)
_MIRROR_FIELDS = frozenset(
    {
        "alias",
        "object_format",
        "observation_complete",
        "private",
        "push_mirror",
        "refs",
        "repository_identity",
        "role",
        "upstream_repository_identity",
    }
)

PROBE_ERROR_CODES = frozenset(
    {
        "ALIASES_NOT_DISTINCT",
        "COMPARISON_PROFILE_INVALID",
        "CONTRACT_VERSION_INVALID",
        "EXPECTED_FIELDS_INVALID",
        "EXPECTED_JSON_INVALID",
        "EXPECTED_NOT_OBJECT",
        "EXPECTATION_ID_INVALID",
        "MIRROR_ALIAS_INVALID",
        "MIRROR_ALIAS_MISMATCH",
        "MIRROR_FIELDS_INVALID",
        "MIRROR_NOT_OBJECT",
        "MIRROR_NOT_PRIVATE",
        "MIRROR_OBJECT_FORMAT_INVALID",
        "MIRROR_OBJECT_FORMAT_MISMATCH",
        "MIRROR_OBSERVATION_INCOMPLETE",
        "MIRROR_REFS_INVALID",
        "MIRROR_REPOSITORY_IDENTITY_INVALID",
        "MIRROR_REPOSITORY_IDENTITY_MISMATCH",
        "MIRROR_REQUIRED_REF_MISMATCH",
        "MIRROR_REQUIRED_REF_MISSING",
        "MIRROR_ROLE_INVALID",
        "OBJECT_FORMAT_INVALID",
        "OBSERVED_FIELDS_INVALID",
        "OBSERVED_JSON_INVALID",
        "OBSERVED_NOT_OBJECT",
        "PUSH_MIRROR_FORBIDDEN",
        "REPOSITORY_IDENTITIES_NOT_DISTINCT",
        "REQUIRED_REFS_INVALID",
        "SOURCE_ALIAS_INVALID",
        "SOURCE_ALIAS_MISMATCH",
        "SOURCE_FIELDS_INVALID",
        "SOURCE_NOT_OBJECT",
        "SOURCE_NOT_PRIVATE",
        "SOURCE_OBJECT_FORMAT_INVALID",
        "SOURCE_OBJECT_FORMAT_MISMATCH",
        "SOURCE_OBSERVATION_INCOMPLETE",
        "SOURCE_REFS_INVALID",
        "SOURCE_REPOSITORY_IDENTITY_INVALID",
        "SOURCE_REPOSITORY_IDENTITY_MISMATCH",
        "SOURCE_REQUIRED_REF_MISMATCH",
        "SOURCE_REQUIRED_REF_MISSING",
        "SOURCE_ROLE_INVALID",
        "UPSTREAM_REPOSITORY_IDENTITY_INVALID",
        "UPSTREAM_REPOSITORY_IDENTITY_MISMATCH",
    }
)

__all__ = [
    "PROBE_COMPARISON_PROFILE",
    "PROBE_CONTRACT_VERSION",
    "PROBE_ERROR_CODES",
    "evaluate_repository_deployment_probe",
]


def _json_shape_valid(value: Any, depth: int = 0) -> bool:
    if depth > _MAX_JSON_DEPTH:
        return False
    if value is None or type(value) is bool:
        return True
    if type(value) is int:
        return abs(value) <= _MAX_JCS_INTEGER
    if isinstance(value, float):
        return False
    if type(value) is str:
        if len(value) > _MAX_STRING_LENGTH:
            return False
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            return False
        return True
    if type(value) is list:
        return len(value) <= _MAX_COLLECTION_ITEMS and all(_json_shape_valid(item, depth + 1) for item in value)
    if type(value) is dict:
        return (
            len(value) <= _MAX_COLLECTION_ITEMS
            and all(type(key) is str for key in value)
            and all(_json_shape_valid(key, depth + 1) for key in value)
            and all(_json_shape_valid(item, depth + 1) for item in value.values())
        )
    return False


def _alias_valid(value: Any, namespace: str) -> bool:
    if type(value) is not str or len(value) > _MAX_ALIAS_LENGTH:
        return False
    if value != value.casefold() or _ALIAS_PATTERN.fullmatch(value) is None:
        return False
    actual_namespace = value.partition(":")[0]
    return actual_namespace == namespace and actual_namespace not in _RESERVED_ALIAS_NAMESPACES


def _repository_identity_valid(value: Any) -> bool:
    if type(value) is not str or not value or len(value) > _MAX_REPOSITORY_IDENTITY_LENGTH:
        return False
    if any(delimiter in value for delimiter in ("%", "\\", "@", "?", "#")):
        return False
    if any(ord(character) <= 32 or ord(character) == 127 for character in value):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or port == 443
        or (port is not None and port < 1)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return False
    host = parsed.hostname
    if (
        host != host.casefold()
        or _HOST_PATTERN.fullmatch(host) is None
        or _NUMERIC_HOST_PATTERN.fullmatch(host) is not None
    ):
        return False
    expected_netloc = host if port is None else f"{host}:{port}"
    canonical_identity = f"https://{expected_netloc}{parsed.path}"
    if parsed.netloc != expected_netloc or value != canonical_identity:
        return False
    segments = parsed.path.removeprefix("/").split("/")
    return (
        parsed.path.startswith("/")
        and len(segments) >= 2
        and all(
            segment not in {"", ".", ".."} and _PATH_SEGMENT_PATTERN.fullmatch(segment) is not None
            for segment in segments
        )
        and segments[-1].endswith(".git")
        and len(segments[-1]) > len(".git")
    )


def _ref_valid(value: Any) -> bool:
    if type(value) is not str or not value or len(value) > _MAX_REF_LENGTH:
        return False
    if not value.startswith(("refs/heads/", "refs/tags/")):
        return False
    if any(ord(character) <= 32 or ord(character) == 127 for character in value):
        return False
    if any(token in value for token in ("..", "//", "@{")):
        return False
    if any(character in value for character in ("\\", "~", "^", ":", "?", "*", "[")):
        return False
    if value.endswith("/"):
        return False
    return all(
        component and not component.startswith(".") and not component.endswith((".", ".lock"))
        for component in value.split("/")
    )


def _object_format_valid(value: Any) -> bool:
    return type(value) is str and value in _OBJECT_ID_LENGTH


def _oid_valid(value: Any, object_format: Any) -> bool:
    if not _object_format_valid(object_format):
        return False
    length = _OBJECT_ID_LENGTH[object_format]
    return (
        type(value) is str
        and len(value) == length
        and _HEX_PATTERN.fullmatch(value) is not None
        and value != "0" * length
    )


def _refs_valid(value: Any, object_format: Any, *, require_nonempty: bool) -> bool:
    return (
        isinstance(value, dict)
        and len(value) <= _MAX_COLLECTION_ITEMS
        and (bool(value) or not require_nonempty)
        and all(_ref_valid(ref) and _oid_valid(oid, object_format) for ref, oid in value.items())
    )


def _checked_object(value: Any, *, json_error: str, object_error: str) -> tuple[dict[str, Any], set[str]]:
    errors: set[str] = set()
    if type(value) is not dict:
        errors.add(object_error)
        return {}, errors
    if not _json_shape_valid(value):
        errors.add(json_error)
        return {}, errors
    return value, errors


def evaluate_repository_deployment_probe(
    expected: Any,
    observed: Any,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Compare caller-supplied refs across designated source and mirror declarations.

    Inputs must already be sanitized and strictly decoded. The function is
    total for finite Python values: failures return ``(None, fixed_codes)`` and
    never include source-controlled values in the error channel.
    """
    expected_data, errors = _checked_object(
        expected,
        json_error="EXPECTED_JSON_INVALID",
        object_error="EXPECTED_NOT_OBJECT",
    )
    observed_data, observed_errors = _checked_object(
        observed,
        json_error="OBSERVED_JSON_INVALID",
        object_error="OBSERVED_NOT_OBJECT",
    )
    errors.update(observed_errors)

    if expected_data and set(expected_data) != _EXPECTED_FIELDS:
        errors.add("EXPECTED_FIELDS_INVALID")
    if observed_data and set(observed_data) != _OBSERVED_FIELDS:
        errors.add("OBSERVED_FIELDS_INVALID")

    contract_version = expected_data.get("contract_version")
    comparison_profile = expected_data.get("comparison_profile")
    expectation_id = expected_data.get("expectation_id")
    source_alias = expected_data.get("source_alias")
    mirror_alias = expected_data.get("mirror_alias")
    source_identity = expected_data.get("source_repository_identity")
    mirror_identity = expected_data.get("mirror_repository_identity")
    object_format = expected_data.get("object_format")
    required_refs = expected_data.get("required_refs")

    if contract_version != PROBE_CONTRACT_VERSION:
        errors.add("CONTRACT_VERSION_INVALID")
    if comparison_profile != PROBE_COMPARISON_PROFILE:
        errors.add("COMPARISON_PROFILE_INVALID")
    if not _alias_valid(expectation_id, "expectation"):
        errors.add("EXPECTATION_ID_INVALID")
    if not _alias_valid(source_alias, "repo"):
        errors.add("SOURCE_ALIAS_INVALID")
    if not _alias_valid(mirror_alias, "repo"):
        errors.add("MIRROR_ALIAS_INVALID")
    if isinstance(source_alias, str) and source_alias == mirror_alias:
        errors.add("ALIASES_NOT_DISTINCT")
    if not _repository_identity_valid(source_identity):
        errors.add("SOURCE_REPOSITORY_IDENTITY_INVALID")
    if not _repository_identity_valid(mirror_identity):
        errors.add("MIRROR_REPOSITORY_IDENTITY_INVALID")
    if isinstance(source_identity, str) and source_identity == mirror_identity:
        errors.add("REPOSITORY_IDENTITIES_NOT_DISTINCT")
    if not _object_format_valid(object_format):
        errors.add("OBJECT_FORMAT_INVALID")

    required_refs_valid = _refs_valid(required_refs, object_format, require_nonempty=True)
    required_ref_map: dict[str, str] = required_refs if isinstance(required_refs, dict) else {}
    if not required_refs_valid:
        errors.add("REQUIRED_REFS_INVALID")

    source_value = observed_data.get("source")
    mirror_value = observed_data.get("mirror")
    source, source_errors = _checked_object(
        source_value,
        json_error="OBSERVED_JSON_INVALID",
        object_error="SOURCE_NOT_OBJECT",
    )
    mirror, mirror_errors = _checked_object(
        mirror_value,
        json_error="OBSERVED_JSON_INVALID",
        object_error="MIRROR_NOT_OBJECT",
    )
    errors.update(source_errors)
    errors.update(mirror_errors)

    if source and set(source) != _SOURCE_FIELDS:
        errors.add("SOURCE_FIELDS_INVALID")
    if mirror and set(mirror) != _MIRROR_FIELDS:
        errors.add("MIRROR_FIELDS_INVALID")

    if not _alias_valid(source.get("alias"), "repo"):
        errors.add("SOURCE_ALIAS_INVALID")
    elif source.get("alias") != source_alias:
        errors.add("SOURCE_ALIAS_MISMATCH")
    if not _alias_valid(mirror.get("alias"), "repo"):
        errors.add("MIRROR_ALIAS_INVALID")
    elif mirror.get("alias") != mirror_alias:
        errors.add("MIRROR_ALIAS_MISMATCH")

    observed_source_identity = source.get("repository_identity")
    observed_mirror_identity = mirror.get("repository_identity")
    upstream_identity = mirror.get("upstream_repository_identity")
    if not _repository_identity_valid(observed_source_identity):
        errors.add("SOURCE_REPOSITORY_IDENTITY_INVALID")
    elif observed_source_identity != source_identity:
        errors.add("SOURCE_REPOSITORY_IDENTITY_MISMATCH")
    if not _repository_identity_valid(observed_mirror_identity):
        errors.add("MIRROR_REPOSITORY_IDENTITY_INVALID")
    elif observed_mirror_identity != mirror_identity:
        errors.add("MIRROR_REPOSITORY_IDENTITY_MISMATCH")
    if not _repository_identity_valid(upstream_identity):
        errors.add("UPSTREAM_REPOSITORY_IDENTITY_INVALID")
    elif upstream_identity != source_identity:
        errors.add("UPSTREAM_REPOSITORY_IDENTITY_MISMATCH")

    if source.get("role") != "source":
        errors.add("SOURCE_ROLE_INVALID")
    if mirror.get("role") != "pull_mirror":
        errors.add("MIRROR_ROLE_INVALID")
    if source.get("private") is not True:
        errors.add("SOURCE_NOT_PRIVATE")
    if mirror.get("private") is not True:
        errors.add("MIRROR_NOT_PRIVATE")
    if source.get("observation_complete") is not True:
        errors.add("SOURCE_OBSERVATION_INCOMPLETE")
    if mirror.get("observation_complete") is not True:
        errors.add("MIRROR_OBSERVATION_INCOMPLETE")
    if mirror.get("push_mirror") is not False:
        errors.add("PUSH_MIRROR_FORBIDDEN")

    source_format = source.get("object_format")
    mirror_format = mirror.get("object_format")
    if not _object_format_valid(source_format):
        errors.add("SOURCE_OBJECT_FORMAT_INVALID")
    elif source_format != object_format:
        errors.add("SOURCE_OBJECT_FORMAT_MISMATCH")
    if not _object_format_valid(mirror_format):
        errors.add("MIRROR_OBJECT_FORMAT_INVALID")
    elif mirror_format != object_format:
        errors.add("MIRROR_OBJECT_FORMAT_MISMATCH")

    source_refs = source.get("refs")
    mirror_refs = mirror.get("refs")
    source_refs_valid = _refs_valid(source_refs, source_format, require_nonempty=False)
    mirror_refs_valid = _refs_valid(mirror_refs, mirror_format, require_nonempty=False)
    source_ref_map: dict[str, str] = source_refs if isinstance(source_refs, dict) else {}
    mirror_ref_map: dict[str, str] = mirror_refs if isinstance(mirror_refs, dict) else {}
    if not source_refs_valid:
        errors.add("SOURCE_REFS_INVALID")
    if not mirror_refs_valid:
        errors.add("MIRROR_REFS_INVALID")

    if required_refs_valid and source_refs_valid:
        for ref, expected_oid in required_ref_map.items():
            if ref not in source_ref_map:
                errors.add("SOURCE_REQUIRED_REF_MISSING")
            elif source_ref_map[ref] != expected_oid:
                errors.add("SOURCE_REQUIRED_REF_MISMATCH")
    if required_refs_valid and mirror_refs_valid:
        for ref, expected_oid in required_ref_map.items():
            if ref not in mirror_ref_map:
                errors.add("MIRROR_REQUIRED_REF_MISSING")
            elif mirror_ref_map[ref] != expected_oid:
                errors.add("MIRROR_REQUIRED_REF_MISMATCH")

    if errors:
        return None, sorted(errors)

    matched_refs = [{"ref": ref, "oid": oid} for ref, oid in sorted(required_ref_map.items())]
    return (
        {
            "comparison_profile": comparison_profile,
            "contract_version": contract_version,
            "expectation_id": expectation_id,
            "matched_refs": matched_refs,
            "mirror_alias": mirror_alias,
            "object_format": object_format,
            "record_type": "repository_deployment_probe_receipt",
            "result": "bounded_required_refs_match",
            "source_alias": source_alias,
        },
        [],
    )
