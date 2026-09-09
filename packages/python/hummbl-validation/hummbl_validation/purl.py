"""Package URL (PURL) parsing and identity normalization.

PURL spec: https://github.com/package-url/purl-spec

Format: pkg:type/namespace/name@version?qualifiers#subpath

Normalization rules:
  - type: always lowercased
  - name/namespace: case-folding depends on ecosystem
    - pypi: lowercased (PEP 503)
    - github: lowercased (GitHub org/repo are case-insensitive)
    - npm, cargo, maven, others: case preserved

Identity: the type is ALWAYS part of the identity. pkg:npm/django and
pkg:pypi/django are different packages. This module never silently
equates identities across ecosystems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote, unquote

# Ecosystems where name and namespace are case-insensitive.
_CASE_INSENSITIVE_TYPES = frozenset({"pypi", "github", "composer", "nuget"})


@dataclass(frozen=True)
class PURL:
    """A parsed Package URL.

    Identity is (type, namespace, name, version). Two PURLs are equal
    iff their normalized identity components match. qualifiers and
    subpath are not part of identity.
    """
    type: str
    name: str
    namespace: str | None = None
    version: str | None = None
    qualifiers: dict[str, str] = field(default_factory=dict, compare=False)
    subpath: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if not self.type:
            raise ValueError("PURL type is required")
        if not self.name:
            raise ValueError("PURL name is required")

    @property
    def identity(self) -> str:
        """Canonical identity string: pkg:type/namespace/name@version."""
        ns = f"{self.namespace}/" if self.namespace else ""
        ver = f"@{self.version}" if self.version else ""
        return f"pkg:{self.type}/{ns}{self.name}{ver}"

    def __str__(self) -> str:
        """Full canonical PURL string including qualifiers and subpath."""
        s = self.identity
        if self.qualifiers:
            qs = "&".join(f"{k}={quote(v, safe='')}" for k, v in sorted(self.qualifiers.items()))
            s += f"?{qs}"
        if self.subpath:
            s += f"#{quote(self.subpath, safe='')}"
        return s


def parse(purl_str: str) -> PURL:
    """Parse a PURL string into a PURL object with normalized components.

    Raises ValueError for malformed input.
    """
    if not isinstance(purl_str, str):
        raise TypeError(f"expected str, got {type(purl_str).__name__}")
    s = purl_str.strip()
    if not s:
        raise ValueError("empty PURL string")
    if not s.startswith("pkg:"):
        raise ValueError(f"PURL must start with 'pkg:', got: {s[:20]!r}")

    body = s[4:]

    # Split off subpath
    subpath = None
    if "#" in body:
        body, subpath = body.split("#", 1)
        subpath = unquote(subpath) if subpath else None

    # Split off qualifiers
    qualifiers: dict[str, str] = {}
    if "?" in body:
        body, qs = body.split("?", 1)
        if qs:
            for pair in qs.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    qualifiers[k.lower()] = unquote(v)
                else:
                    qualifiers[pair.lower()] = ""

    # Split off version — the @ must be after the last / (in the name
    # portion), not in the namespace. npm scoped packages use @ in the
    # namespace (e.g. pkg:npm/@babel/core) and that @ is NOT a version
    # separator. Only an @ after the last / is the version separator.
    version = None
    last_slash = body.rfind("/")
    at_pos = body.find("@", last_slash + 1) if last_slash >= 0 else body.find("@")
    if at_pos >= 0:
        version = unquote(body[at_pos + 1:]) if body[at_pos + 1:] else None
        body = body[:at_pos]

    # Now body is type/namespace/name
    if "/" not in body:
        raise ValueError(f"PURL must have type and name, got: {body!r}")

    ptype, rest = body.split("/", 1)
    ptype = unquote(ptype).lower()

    if "/" in rest:
        namespace, name = rest.rsplit("/", 1)
        namespace = unquote(namespace)
    else:
        namespace = None
        name = rest

    name = unquote(name)

    if not ptype:
        raise ValueError("PURL type is empty")
    if not name:
        raise ValueError("PURL name is empty")

    # Normalize case for case-insensitive ecosystems
    if ptype in _CASE_INSENSITIVE_TYPES:
        name = name.lower()
        if namespace:
            namespace = namespace.lower()

    return PURL(
        type=ptype,
        name=name,
        namespace=namespace or None,
        version=version,
        qualifiers=qualifiers,
        subpath=subpath,
    )


def normalize(purl_str: str) -> str:
    """Parse and re-emit a PURL in canonical form.

    Raises ValueError for malformed input.
    """
    return str(parse(purl_str))
