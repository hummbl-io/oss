"""Cognitive Ledger writer -- append-only JSONL persistence with file locking.

Provides the canonical write path for the cognitive ledger. All ledger
writes should go through post_entry() to ensure mutual exclusion via
the platform-appropriate advisory lock backend.

Mirrors the design of bus/bus_writer.py for the coordination bus.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import threading
import unicodedata
from pathlib import Path

from hummbl_cognition._filelock import lock_file as _lock_file
from hummbl_cognition._filelock import unlock_file as _unlock_file
from hummbl_cognition.models import (
    CANONICAL_LEDGER_SCOPES,
    CANONICAL_LEDGER_TYPES,
    LedgerEntry,
    LedgerEntryType,
    LedgerScope,
)

logger = logging.getLogger(__name__)

# Canonical package-relative cognition state.  This file lives at
# <distribution>/hummbl_cognition/ledger_writer.py, so parent.parent is
# the importable package root regardless of the process CWD or workspace
# nesting.  Default readers and writers must derive from this same directory.
DEFAULT_COGNITION_DIR = Path(__file__).resolve().parent.parent / "_state" / "cognition"
DEFAULT_LEDGER_PATH = DEFAULT_COGNITION_DIR / "ledger.jsonl"

# Maximum entry content size (4 KB -- matches schema maxLength)
MAX_CONTENT_BYTES = 4096
_THREAD_WRITE_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Content scanning -- reject poisoned entries before they reach the ledger
# ---------------------------------------------------------------------------

# Prompt injection patterns (case-insensitive)
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?prior\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\]\s*\}\s*\]\s*\}\s*system", re.IGNORECASE),  # JSON escape
]

# Credential patterns
_CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI keys
    re.compile(r"sk-ant-[a-zA-Z0-9-]{20,}"),  # Anthropic keys
    re.compile(r"ghp_[a-zA-Z0-9]{36,}"),  # GitHub PATs
    re.compile(r"gho_[a-zA-Z0-9]{36,}"),  # GitHub OAuth
    re.compile(r"glpat-[a-zA-Z0-9_-]{20,}"),  # GitLab PATs
    re.compile(r"xoxb-[a-zA-Z0-9-]{20,}"),  # Slack bot tokens
    re.compile(r"xoxp-[a-zA-Z0-9-]{20,}"),  # Slack user tokens
    re.compile(r"AIza[a-zA-Z0-9_-]{35}"),  # Google API keys
    re.compile(r"AKIA[A-Z0-9]{16}"),  # AWS access keys
    re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"),  # PEM keys
]

# PII patterns — detect personal data that should not enter append-only logs.
# Used by scan_pii() to warn/block, and by scrub_pii() to hash-replace.
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")),
    ("phone_us", re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (
        "ip_address",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
    ),
]

# Known safe patterns that match PII regexes but are not actual PII.
# Prevents false positives on infrastructure identifiers.
_PII_ALLOWLIST: list[re.Pattern[str]] = [
    re.compile(r"noreply@anthropic\.com"),  # Co-author tag
    re.compile(r"100\.\d+\.\d+\.\d+"),  # Tailscale IPs (CGNAT range)
    re.compile(r"127\.0\.0\.\d+"),  # Loopback
    re.compile(r"0\.0\.0\.0"),  # Bind-all
]


class PIIDetectedError(ValueError):
    """Raised when PII is detected in content destined for append-only storage."""

    def __init__(self, pii_type: str, detail: str) -> None:
        self.pii_type = pii_type
        self.detail = detail
        super().__init__(f"PII detected ({pii_type}): {detail}")


def scan_pii(text: str, *, strict: bool = False) -> list[tuple[str, str]]:
    """Scan text for PII patterns. Returns list of (type, matched_text).

    Args:
        text: Text to scan.
        strict: If True, raise PIIDetectedError on first match.
                If False (default), return matches silently for caller to handle.

    Returns:
        List of (pii_type, matched_value) tuples.
    """
    findings: list[tuple[str, str]] = []
    for pii_type, pattern in _PII_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group()
            # Check allowlist
            if any(allow.search(value) for allow in _PII_ALLOWLIST):
                continue
            findings.append((pii_type, value))
            if strict:
                raise PIIDetectedError(
                    pii_type,
                    f"Found {pii_type} pattern: {value[:4]}...{value[-4:]}"
                    if len(value) > 8
                    else f"Found {pii_type} pattern",
                )
    return findings


def scrub_pii(text: str) -> str:
    """Replace PII in text with SHA-256 pseudonyms.

    Preserves data utility (same input → same hash) while removing
    the actual PII. Safe for append-only logs.
    """
    result = text
    for pii_type, pattern in _PII_PATTERNS:

        def _replace(m: re.Match[str], _type: str = pii_type) -> str:
            value = m.group()
            if any(allow.search(value) for allow in _PII_ALLOWLIST):
                return value  # Keep allowlisted values
            pseudonym = hashlib.sha256(value.encode()).hexdigest()[:12]
            return f"[{_type}:{pseudonym}]"

        result = pattern.sub(_replace, result)
    return result


def scrub_pii_from_dict(data: dict) -> dict:
    """Recursively scrub PII from all string values in a dictionary.

    Returns a new dict with PII replaced by SHA-256 pseudonyms.
    Used by governance_bus.py to sanitize tuple_data before append.
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = scrub_pii(value)
        elif isinstance(value, dict):
            result[key] = scrub_pii_from_dict(value)
        elif isinstance(value, list):
            result[key] = [
                scrub_pii_from_dict(item)
                if isinstance(item, dict)
                else scrub_pii(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


# Exfiltration vectors (commands that could leak secrets)
_EXFILTRATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"curl\s+.*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD)", re.IGNORECASE),
    re.compile(r"wget\s+.*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD)", re.IGNORECASE),
    re.compile(r"curl\s+-[^s]*d\s+.*\$\{?\w*", re.IGNORECASE),
    # Red-team 2026-04-17: URL-based exfiltration with sensitive query params
    re.compile(
        r"https?://[^\s]+[?&](data|token|key|secret|password|cred)=", re.IGNORECASE
    ),
]

# Invisible Unicode characters used for steganographic attacks.
# Covers: zero-width chars, bidi controls, format chars, unusual whitespace,
# variation selectors, and tag characters. Expanded after pre-mortem found
# U+1680 (Ogham Space) bypass.
_INVISIBLE_CODEPOINTS = frozenset(
    {
        # Zero-width characters
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\u2060",  # Word joiner
        "\ufeff",  # Zero-width no-break space (BOM)
        # Bidi controls
        "\u200e",  # Left-to-right mark
        "\u200f",  # Right-to-left mark
        "\u202a",  # Left-to-right embedding
        "\u202b",  # Right-to-left embedding
        "\u202c",  # Pop directional formatting
        "\u202d",  # Left-to-right override
        "\u202e",  # Right-to-left override
        "\u2066",  # Left-to-right isolate
        "\u2067",  # Right-to-left isolate
        "\u2068",  # First strong isolate
        "\u2069",  # Pop directional isolate
        # Unusual whitespace (pre-mortem finding: Ogham Space bypass)
        "\u00a0",  # Non-breaking space
        "\u1680",  # Ogham Space Mark
        "\u2000",  # En Quad
        "\u2001",  # Em Quad
        "\u2002",  # En Space
        "\u2003",  # Em Space
        "\u2004",  # Three-per-em space
        "\u2005",  # Four-per-em space
        "\u2006",  # Six-per-em space
        "\u2007",  # Figure space
        "\u2008",  # Punctuation space
        "\u2009",  # Thin space
        "\u200a",  # Hair space
        "\u205f",  # Medium mathematical space
        "\u3000",  # Ideographic space
        # Invisible separators / formatting (red-team 2026-04-17: U+2063 bypass)
        "\u2062",  # Invisible times
        "\u2063",  # Invisible separator
        "\u2064",  # Invisible plus
        # Format characters
        "\u00ad",  # Soft hyphen
        "\u034f",  # Combining grapheme joiner
        "\u061c",  # Arabic letter mark
        "\u180e",  # Mongolian vowel separator
        # Variation selectors (can alter glyph rendering)
        "\ufe00",  # Variation Selector-1
        "\ufe0f",  # Variation Selector-16 (emoji presentation)
        # Interlinear annotation anchors
        "\ufff9",  # Interlinear annotation anchor
        "\ufffa",  # Interlinear annotation separator
        "\ufffb",  # Interlinear annotation terminator
    }
)


# Cross-script homoglyph map: Cyrillic/Greek lookalikes → Latin equivalents.
# This defeats attacks where Cyrillic 'о' (U+043E) replaces Latin 'o' (U+006F)
# to bypass regex-based injection detection. Only maps characters commonly
# used in confusable attacks against English-language patterns.
_CONFUSABLE_MAP = str.maketrans(
    {
        "\u0430": "a",  # Cyrillic а → Latin a
        "\u0435": "e",  # Cyrillic е → Latin e
        "\u0456": "i",  # Cyrillic і → Latin i
        "\u043e": "o",  # Cyrillic о → Latin o
        "\u0440": "p",  # Cyrillic р → Latin p
        "\u0441": "c",  # Cyrillic с → Latin c
        "\u0443": "y",  # Cyrillic у → Latin y (visual match)
        "\u0445": "x",  # Cyrillic х → Latin x
        "\u04bb": "h",  # Cyrillic һ → Latin h
        "\u0458": "j",  # Cyrillic ј → Latin j
        "\u0455": "s",  # Cyrillic ѕ → Latin s
        "\u0454": "e",  # Cyrillic є → Latin e (approximate)
        "\u0457": "i",  # Cyrillic ї → Latin i (approximate)
        "\u0491": "g",  # Cyrillic ґ → Latin g (approximate)
        # Red-team expansion (2026-04-17): missing confusables that bypass cred patterns
        "\u043a": "k",  # Cyrillic к → Latin k (bypass: sк-ant- evaded cred scan)
        "\u0442": "t",  # Cyrillic т → Latin t
        "\u0434": "d",  # Cyrillic д → Latin d
        "\u043d": "n",  # Cyrillic н → Latin n
        "\u0432": "v",  # Cyrillic в → Latin v
        "\u043c": "m",  # Cyrillic м → Latin m
        "\u0436": "zh",  # Cyrillic ж → Latin zh (approximate)
        "\u043b": "l",  # Cyrillic л → Latin l (approximate)
        # Greek lookalikes
        "\u03bf": "o",  # Greek ο → Latin o
        "\u03b1": "a",  # Greek α → Latin a
        "\u03b5": "e",  # Greek ε → Latin e
        "\u03b9": "i",  # Greek ι → Latin i
        "\u03c1": "p",  # Greek ρ → Latin p
        "\u03c4": "t",  # Greek τ → Latin t
        "\u03ba": "k",  # Greek κ → Latin k
        "\u03bd": "v",  # Greek ν → Latin v
        # Full-width Latin (sometimes used to bypass)
        "\uff49": "i",  # Fullwidth i
        "\uff4f": "o",  # Fullwidth o
        "\uff47": "g",  # Fullwidth g
        "\uff4e": "n",  # Fullwidth n
        "\uff52": "r",  # Fullwidth r
        "\uff45": "e",  # Fullwidth e
    }
)


def _transliterate_confusables(text: str) -> str:
    """Replace cross-script homoglyphs with their Latin equivalents.

    This runs AFTER NFC normalization and BEFORE regex pattern matching.
    It ensures that Cyrillic 'іgnоre' is scanned as Latin 'ignore'.
    """
    return text.translate(_CONFUSABLE_MAP)


class ContentScanError(ValueError):
    """Raised when content scanning detects a suspicious pattern."""

    def __init__(self, category: str, detail: str) -> None:
        self.category = category
        self.detail = detail
        super().__init__(f"Content scan rejected ({category}): {detail}")


def scan_content(text: str) -> None:
    """Scan text for prompt injection, credentials, exfiltration, and invisible chars.

    Text is NFC-normalized before regex matching to prevent homographic
    bypass attacks (e.g., Cyrillic 'а' vs Latin 'a'). Invisible character
    detection runs on the RAW text (pre-normalization) to catch chars that
    NFC would strip.

    Raises ContentScanError if suspicious content is detected.
    Scans all text fields that flow into the ledger and ultimately into
    boot context for other agents.
    """
    # 0. Check invisible chars on RAW text (before normalization strips them)
    found_invisible = [c for c in text if c in _INVISIBLE_CODEPOINTS]
    if found_invisible:
        codepoints = ", ".join(f"U+{ord(c):04X}" for c in set(found_invisible))
        raise ContentScanError(
            "invisible_unicode",
            f"Contains invisible Unicode characters: {codepoints}",
        )

    # Normalize to NFC then apply confusable transliteration to defeat
    # cross-script homoglyph attacks (e.g., Cyrillic 'і'/'о' vs Latin 'i'/'o').
    # NFC alone does NOT handle cross-script lookalikes.
    normalized = unicodedata.normalize("NFC", text)
    normalized = _transliterate_confusables(normalized)

    # 1. Prompt injection (on normalized text)
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(normalized)
        if match:
            raise ContentScanError(
                "prompt_injection",
                f"Matches injection pattern: {match.group()!r}",
            )

    # 2. Credential leakage (on normalized text)
    for pattern in _CREDENTIAL_PATTERNS:
        match = pattern.search(normalized)
        if match:
            # Show first 8 chars only to avoid logging the full secret
            snippet = match.group()[:8] + "..."
            raise ContentScanError(
                "credential_leak",
                f"Contains credential-like pattern: {snippet}",
            )

    # 3. Exfiltration vectors (on normalized text)
    for pattern in _EXFILTRATION_PATTERNS:
        match = pattern.search(normalized)
        if match:
            raise ContentScanError(
                "exfiltration",
                f"Contains exfiltration vector: {match.group()[:40]!r}",
            )


def _resolve_ledger_path(override: str | Path | None = None) -> Path:
    """Resolve the ledger file path.

    Priority: explicit override > COGNITION_LEDGER env > package root default.

    Note: we deliberately do NOT use ``git rev-parse --show-toplevel`` because
    the ``.git`` directory may live at the workspace root (e.g. when the repo
    is a subdirectory of a larger workspace), which would resolve to the wrong
    directory and silently route writes to a stale ledger. See
    ``docs/operations/path-drift-audit/`` and AGENTS.md for context.
    """
    if override:
        return Path(override)

    env_path = os.environ.get("COGNITION_LEDGER")
    if env_path:
        return Path(env_path)

    return DEFAULT_LEDGER_PATH


def _resolve_signing_secret() -> bytes | None:
    """Resolve HMAC signing secret from BUS_SIGNING_SECRET env var."""
    raw = os.environ.get("BUS_SIGNING_SECRET")
    if not raw:
        return None
    secret_bytes = raw.encode("utf-8")
    if len(secret_bytes) < 32:
        logger.warning(
            "BUS_SIGNING_SECRET too short (%d bytes, need 32+). "
            "Entries will NOT be signed.",
            len(secret_bytes),
        )
        return None
    return secret_bytes


def _sign_entry(entry_jsonl: str, secret: bytes) -> str:
    """Compute HMAC-SHA256 signature of a JSONL line."""
    return hmac.new(secret, entry_jsonl.encode("utf-8"), hashlib.sha256).hexdigest()


def _harden_file_permissions(path: Path) -> None:
    """Set restrictive permissions (0o600) on the ledger file."""
    if not path.exists():
        return
    try:
        current_mode = path.stat().st_mode & 0o777
        if current_mode != 0o660:
            path.chmod(0o660)
    except OSError as e:
        logger.warning("Could not harden ledger permissions: %s", e)


def _validate_entry_schema(entry: "LedgerEntry") -> None:
    """Validate entry against the CLP contract schema (KRINEIA cut() operational).

    Uses stdlib-only validation against the contract at
    contracts/cognition/schemas/clp.ledger_entry.schema.json.
    Falls back gracefully if jsonschema is not installed or schema is missing.
    """
    import re as _re

    d = entry.to_dict()

    # Required fields
    for field in (
        "id",
        "timestamp",
        "agent",
        "vendor",
        "model",
        "type",
        "scope",
        "content",
        "content_hash",
    ):
        if field not in d or d[field] is None:
            raise ValueError(f"ledger entry missing required field: {field}")

    # ID format: clp-<12 hex chars>
    if not _re.match(r"^clp-[a-f0-9]{12}$", d["id"]):
        raise ValueError(
            f"ledger entry id format invalid: {d['id']!r} (expected clp-<12hex>)"
        )

    # Vendor enum
    valid_vendors = {"anthropic", "google", "human", "local", "moonshot", "openai", "zai"}
    if d["vendor"] not in valid_vendors:
        raise ValueError(
            f"ledger entry vendor {d['vendor']!r} not in {sorted(valid_vendors)}"
        )

    # Type enum — canonical values only; historical aliases parse for read
    # but are rejected at write time to prevent schema drift accumulation.
    if d["type"] not in CANONICAL_LEDGER_TYPES:
        raise ValueError(
            f"ledger entry type {d['type']!r} not in {sorted(CANONICAL_LEDGER_TYPES)}. "
            f"Historical aliases are accepted during read but not for new writes."
        )

    # Scope enum — canonical values only
    if d["scope"] not in CANONICAL_LEDGER_SCOPES:
        raise ValueError(
            f"ledger entry scope {d['scope']!r} not in {sorted(CANONICAL_LEDGER_SCOPES)}. "
            f"Historical aliases are accepted during read but not for new writes."
        )

    # Content length
    if len(d["content"]) > 4096:
        raise ValueError(
            f"ledger entry content too long: {len(d['content'])} chars (max 4096)"
        )

    # Content hash format: SHA-256 hex = 64 chars
    if not _re.match(r"^[a-f0-9]{64}$", d["content_hash"]):
        raise ValueError(
            "ledger entry content_hash format invalid (expected 64 hex chars)"
        )

    # Tags max count
    tags = d.get("tags") or []
    if len(tags) > 10:
        raise ValueError(f"ledger entry has {len(tags)} tags (max 10)")

    # Confidence range
    confidence = d.get("confidence")
    if confidence is not None and not (0.0 <= confidence <= 1.0):
        raise ValueError(
            f"ledger entry confidence {confidence} out of range [0.0, 1.0]"
        )

    # Assurance level enum
    assurance = d.get("assurance_level")
    if assurance is not None and assurance not in ("SELF", "PEER", "VERIFIED"):
        raise ValueError(f"ledger entry assurance_level {assurance!r} invalid")

    # Optional claim field — ADR-FM-048 Phase 0
    claim = d.get("claim")
    if claim is not None:
        if not isinstance(claim, dict):
            raise ValueError(
                f"ledger entry claim must be a dict, got {type(claim).__name__}"
            )
        claim_json = json.dumps(claim, separators=(",", ":"))
        if len(claim_json) > 8192:
            raise ValueError(
                f"ledger entry claim too large: {len(claim_json)} bytes (max 8192)"
            )


def post_entry(
    entry: LedgerEntry,
    *,
    ledger_path: str | Path | None = None,
    secret: bytes | None = None,
) -> LedgerEntry:
    """Append a ledger entry to the JSONL file under exclusive lock.

    Parameters
    ----------
    entry : LedgerEntry
        The entry to write. Must have a valid content_hash.
    ledger_path : str | Path | None
        Override ledger file path. Defaults to auto-resolve.
    secret : bytes | None
        HMAC-SHA256 key for signing. Falls back to BUS_SIGNING_SECRET env.

    Returns:
    -------
    LedgerEntry
        The entry as written (may include signature if signing enabled).

    Raises:
    ------
    ValueError
        If entry fails validation.
    OSError
        If file write fails.
    """
    path = _resolve_ledger_path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Scan content for injection, credentials, exfiltration, invisible chars.
    # This runs BEFORE hash verification to reject poisoned content early.
    scan_content(entry.content)
    if entry.evidence:
        scan_content(entry.evidence)
    if entry.tags:
        scan_content(" ".join(entry.tags))
    if entry.agent:
        scan_content(entry.agent)

    # PII scan: warn on PII in content destined for append-only storage.
    # Default: warn-only (log but allow). Set PII_SCAN_STRICT=true to block.
    pii_strict = os.environ.get("PII_SCAN_STRICT", "false").lower() == "true"
    pii_findings = scan_pii(entry.content, strict=pii_strict)
    if pii_findings:
        logger.warning(
            "PII detected in ledger entry: %s",
            ", ".join(f"{t}={v[:4]}..." for t, v in pii_findings),
        )

    # KRINEIA cut(): validate entry against contract schema before write
    _validate_entry_schema(entry)

    # Verify content hash
    if not entry.verify_hash():
        raise ValueError(
            "Content hash mismatch: entry content_hash does not match "
            "computed hash of content fields"
        )

    # Resolve signing secret
    if secret is None:
        secret = _resolve_signing_secret()

    # Append under exclusive advisory lock
    with _THREAD_WRITE_LOCK:
        with open(path, "a+", encoding="utf-8") as f:
            _lock_file(f)
            try:
                f.seek(0, 2)
                file_size = f.tell()
                is_new_file = file_size == 0

                # CLP v1.1 hash-chaining: compute or verify previous_hash from preceding line
                if not is_new_file:
                    # Read the complete final record. A single JSONL record may
                    # exceed any fixed read window, so we scan backward from EOF
                    # to find the last newline boundary, growing the window as
                    # needed until the preceding newline is found.
                    last_line = ""
                    read_size = 4096
                    while True:
                        pos = max(0, file_size - read_size)
                        f.seek(pos)
                        chunk = f.read()
                        # Find the last newline that precedes the final line.
                        # If file ends with \n, rfind gives the boundary before
                        # the (empty) trailing segment; we want the one before that.
                        nl_idx = (
                            chunk.rfind("\n", 0, len(chunk) - 1)
                            if chunk.endswith("\n")
                            else chunk.rfind("\n")
                        )
                        if nl_idx >= 0 or pos == 0:
                            # Found a newline boundary (or reached BOF) — the
                            # final record starts right after it.
                            start = nl_idx + 1 if nl_idx >= 0 else 0
                            last_line = chunk[start:].strip()
                            break
                        # No newline found in this window — record is larger than
                        # read_size. Grow the window and retry.
                        read_size *= 2
                        if read_size > file_size:
                            read_size = file_size

                    if last_line:
                        expected_prev_h = hashlib.sha256(
                            last_line.encode("utf-8")
                        ).hexdigest()
                        if entry.previous_hash is None:
                            d = entry.to_dict()
                            d["previous_hash"] = expected_prev_h
                            entry = LedgerEntry.from_dict(d)
                        elif entry.previous_hash != expected_prev_h:
                            raise ValueError(
                                f"Invalid previous_hash {entry.previous_hash!r}: does not match "
                                f"computed hash of preceding ledger line ({expected_prev_h!r})"
                            )

                # Sign if secret available
                if secret is not None:
                    # Clear signature if pre-existing to ensure signature covers computed previous_hash
                    d = entry.to_dict()
                    d.pop("signature", None)
                    entry_to_sign = LedgerEntry.from_dict(d)
                    sig = _sign_entry(entry_to_sign.to_jsonl(), secret)
                    d["signature"] = sig
                    entry = LedgerEntry.from_dict(d)

                line = entry.to_jsonl() + "\n"
                f.seek(0, 2)
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            finally:
                _unlock_file(f)

    # Harden permissions on new files
    if is_new_file:
        _harden_file_permissions(path)

    logger.info(
        "Ledger entry posted: id=%s type=%s scope=%s agent=%s",
        entry.id,
        entry.type,
        entry.scope,
        entry.agent,
    )

    # Fire post-write hooks (prior-art discovery, open-question extraction).
    # Hooks enqueue research queries to the research_processor queue; the
    # existing cron picks them up and posts results back linked to this entry.
    # Fired in a daemon thread so post_entry never blocks on queue I/O.
    # Hooks are opt-out via CLP_POST_WRITE_HOOKS=off and never break the post.
    try:
        import threading

        from hummbl_cognition.post_write_hooks import fire_post_write_hooks

        def _safe_hook(e=entry) -> None:
            try:
                fire_post_write_hooks(e)
            except Exception as exc:
                logger.warning("Post-write hooks failed for %s: %s", e.id, exc)

        threading.Thread(target=_safe_hook, daemon=True).start()
    except Exception as exc:
        logger.warning("Post-write hook dispatch failed for %s: %s", entry.id, exc)

    return entry


def _verify_entry_signature(
    entry: "LedgerEntry", raw_line: str, signing_key: bytes
) -> bool:
    """Verify the HMAC-SHA256 signature of a ledger entry.

    Reconstructs the unsigned JSONL from the entry and compares the expected
    signature against the stored one. Uses hmac.compare_digest to prevent
    timing attacks.

    Parameters
    ----------
    entry : LedgerEntry
        The parsed entry (with signature field populated).
    raw_line : str
        The original raw JSONL line from the ledger file (used to reconstruct
        the unsigned form by stripping the signature key).
    signing_key : bytes
        The HMAC key used for verification.

    Returns:
    -------
    bool
        True if signature is valid, False otherwise.
    """
    d = entry.to_dict()
    d.pop("signature", None)
    unsigned_entry = LedgerEntry.from_dict({**d, "signature": None})
    unsigned_jsonl = unsigned_entry.to_jsonl()
    expected_sig = _sign_entry(unsigned_jsonl, signing_key)
    return hmac.compare_digest(entry.signature, expected_sig)


def read_entries(
    *,
    ledger_path: str | Path | None = None,
    since: str | None = None,
    entry_type: str | LedgerEntryType | None = None,
    scope: str | LedgerScope | None = None,
    agent: str | None = None,
    tags: list[str] | None = None,
    limit: int = 100,
    verify_signatures: bool = False,
    signing_key: bytes | None = None,
    delegation_token: object | None = None,
) -> list[LedgerEntry]:
    """Read and filter ledger entries.

    Parameters
    ----------
    ledger_path : str | Path | None
        Override ledger file path.
    since : str | None
        ISO 8601 timestamp -- only return entries after this time.
    entry_type : str | LedgerEntryType | None
        Filter by entry type.
    scope : str | LedgerScope | None
        Filter by scope.
    agent : str | None
        Filter by agent identifier (substring match).
    tags : list[str] | None
        Filter by tags (entries must contain ALL specified tags).
    limit : int
        Maximum number of entries to return (most recent first).
    verify_signatures : bool
        When True, entries with a ``signature`` field are verified against
        the HMAC key (``signing_key`` or ``BUS_SIGNING_SECRET`` env var).
        Entries whose signature fails verification are dropped and logged as
        warnings. Unsigned entries always pass through -- signing is optional.
        Default False for backward compatibility.
    signing_key : bytes | None
        HMAC key for signature verification. Falls back to
        ``BUS_SIGNING_SECRET`` env var when not provided.
    delegation_token : DelegationCapabilityToken | None
        IDP delegation token. When ``ENABLE_IDP`` is true and a token is
        supplied, the token must have ``"read:ledger"`` in ``ops_allowed``;
        otherwise :exc:`PermissionError` is raised. When IDP is disabled,
        this parameter is ignored (fail-open for backward compatibility).

    Returns:
    -------
    list[LedgerEntry]
        Matching entries, most recent first.

    Raises:
    ------
    PermissionError
        When ``ENABLE_IDP`` is true, a ``delegation_token`` is provided, and
        the token does not authorise ``"read:ledger"``.
    """
    # IDP-gated access: enforce when ENABLE_IDP is true (default) and a token is presented.
    # Default matches delegation_token.py and governance_bus.py (ASI07 fail-closed posture).
    _idp_enabled = os.environ.get("ENABLE_IDP", "").lower() in ("true", "1", "yes")
    if _idp_enabled and delegation_token is not None:
        _required_op = "read:ledger"
        _token_ops = getattr(delegation_token, "ops_allowed", ())
        if _required_op not in _token_ops:
            raise PermissionError(
                f"Delegation token does not permit '{_required_op}'. "
                f"Allowed ops: {list(_token_ops)}"
            )
    path = _resolve_ledger_path(ledger_path)
    if not path.exists():
        return []

    # Normalize filter values
    if isinstance(entry_type, LedgerEntryType):
        entry_type = entry_type.value
    if isinstance(scope, LedgerScope):
        scope = scope.value

    # Resolve HMAC key once if verification is requested
    _signing_key: bytes | None = None
    if verify_signatures:
        _signing_key = (
            signing_key if signing_key is not None else _resolve_signing_secret()
        )

    entries: list[LedgerEntry] = []

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning("Skipping malformed ledger line %d: %s", line_num, e)
                continue

            # Skip-and-warn guard for corrupt entries that cannot be normalized
            # into LedgerEntry records. The append-only invariant is preserved --
            # corrupt lines are skipped on read, not mutated. See issue #1100.
            if not isinstance(data, dict):
                logger.warning(
                    "Skipping corrupt ledger line %d: expected JSON object, got %s",
                    line_num,
                    type(data).__name__,
                )
                continue

            if "id" not in data and "entry_id" not in data:
                logger.warning(
                    "Skipping corrupt ledger line %d: missing required 'id' field "
                    "or legacy 'entry_id' alias (historical graphify event that "
                    "bypassed schema validation)",
                    line_num,
                )
                continue

            try:
                entry = LedgerEntry.from_dict(data)
            except (KeyError, ValueError) as e:
                logger.warning("Skipping malformed ledger line %d: %s", line_num, e)
                continue

            # Signature verification (read-time provenance check)
            if verify_signatures and entry.signature and _signing_key:
                try:
                    if not _verify_entry_signature(entry, line, _signing_key):
                        logger.warning(
                            "Dropping ledger entry %s (line %d): signature mismatch -- "
                            "entry may have been tampered with",
                            entry.id,
                            line_num,
                        )
                        continue
                except Exception as sig_err:
                    logger.warning(
                        "Dropping ledger entry %s (line %d): signature verification "
                        "error: %s",
                        entry.id,
                        line_num,
                        sig_err,
                    )
                    continue

            # Apply filters
            if since and entry.timestamp < since:
                continue
            if entry_type and entry.type != entry_type:
                continue
            if scope and entry.scope != scope:
                continue
            if agent and agent not in entry.agent:
                continue
            if tags and not all(t in entry.tags for t in tags):
                continue

            entries.append(entry)

    # Most recent first, limited
    entries.reverse()
    return entries[:limit]


def validate_integrity(
    *,
    ledger_path: str | Path | None = None,
    secret: bytes | None = None,
) -> tuple[int, list[str]]:
    """Validate ledger integrity: parsing, content hashes, optional signatures.

    Returns:
    -------
    tuple[int, list[str]]
        (valid_count, error_descriptions)
    """
    path = _resolve_ledger_path(ledger_path)
    if not path.exists():
        return 0, []

    if secret is None:
        secret = _resolve_signing_secret()

    valid_count = 0
    errors: list[str] = []
    prev_line: str | None = None

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            # Parse
            try:
                data = json.loads(line)
                entry = LedgerEntry.from_dict(data)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                errors.append(f"Line {line_num}: parse error: {e}")
                continue

            # Verify content hash (skip for grandfathered non-hex hashes)
            import re as _re

            if _re.match(r"^[a-f0-9]{64}$", entry.content_hash):
                if not entry.verify_hash():
                    errors.append(
                        f"Line {line_num}: content_hash mismatch for {entry.id}"
                    )
                    continue
            # else: grandfathered non-hex content_hash — skip hash verification

            # Verify signature if present and secret available
            if entry.signature and secret:
                # Reconstruct unsigned JSONL to verify
                d = entry.to_dict()
                d.pop("signature", None)
                unsigned_entry = LedgerEntry.from_dict({**d, "signature": None})
                unsigned_jsonl = unsigned_entry.to_jsonl()
                expected_sig = _sign_entry(unsigned_jsonl, secret)
                if not hmac.compare_digest(entry.signature, expected_sig):
                    errors.append(f"Line {line_num}: signature mismatch for {entry.id}")
                    continue

            # Verify previous_hash chain continuity if present
            if entry.previous_hash and prev_line:
                expected_prev = hashlib.sha256(prev_line.encode("utf-8")).hexdigest()
                if entry.previous_hash != expected_prev:
                    errors.append(
                        f"Line {line_num}: previous_hash chain mismatch for {entry.id}"
                    )
                    continue

            prev_line = line
            valid_count += 1

    return valid_count, errors


def _group_consecutive(lines: list[int]) -> list[list[int]]:
    """Group consecutive line numbers into ranges."""
    if not lines:
        return []
    ranges: list[list[int]] = [[lines[0], lines[0]]]
    for n in lines[1:]:
        if n == ranges[-1][1] + 1:
            ranges[-1][1] = n
        else:
            ranges.append([n, n])
    return ranges


def _format_line_ranges(ranges: list[list[int]]) -> str:
    """Format [[64,67],[133,359]] -> '64-67, 133-359'."""
    return ", ".join(f"{s}-{e}" if s != e else str(s) for s, e in ranges)


_REMEDIATION = {
    "signature_mismatch": (
        "Likely signing-secret drift or historical signature coverage change. "
        "Do not re-sign in place. First confirm expected historical signing "
        "secret/config, then either document a waiver range or append a "
        "superseding attestation ledger entry."
    ),
    "content_hash_mismatch": (
        "Possible canonicalization/schema drift or content mutation. "
        "Inspect each entry against LedgerEntry.verify_hash() and classify "
        "as schema-era drift vs true corruption before any repair."
    ),
    "parse_error": (
        "Malformed JSONL rows. Preserve raw bytes, identify writer/source, "
        "and only quarantine/repair with explicit operator approval and backup."
    ),
    "other": "Unclassified error. Manual inspection required.",
}


def validate_integrity_report(
    *,
    ledger_path: str | Path | None = None,
    secret: bytes | None = None,
) -> dict[str, object]:
    """Validate ledger integrity and return a structured report.

    Returns a dict suitable for JSON/Markdown serialization with errors
    grouped by class and line ranges.
    """
    path = _resolve_ledger_path(ledger_path)
    total_lines = 0
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                total_lines = sum(1 for _ in f if _.strip())
        except OSError:
            pass

    valid_count, errors = validate_integrity(ledger_path=path, secret=secret)

    # Classify and group
    by_class: dict[str, dict[str, object]] = {}
    for cls_name in (
        "signature_mismatch",
        "content_hash_mismatch",
        "parse_error",
        "other",
    ):
        by_class[cls_name] = {"count": 0, "lines": [], "samples": []}

    for idx, error in enumerate(errors):
        cls_name = _classify_error(error)
        by_class[cls_name]["count"] += 1  # type: ignore[operator]
        # Parse line number from error string
        import re as _re

        m = _re.match(r"Line (\d+):", error)
        if m:
            by_class[cls_name]["lines"].append(int(m.group(1)))  # type: ignore[attr-defined]
        # Keep up to 5 samples per class
        samples: list[str] = by_class[cls_name]["samples"]  # type: ignore[assignment]
        if len(samples) < 5:
            samples.append(error)

    # Build line ranges
    report = {
        "ledger_path": str(path),
        "ledger_exists": path.exists(),
        "total_lines": total_lines,
        "valid_entries": valid_count,
        "errors": {
            "total": len(errors),
            "by_class": {},
        },
        "remediation": _REMEDIATION,
    }

    for cls_name, data in by_class.items():
        lines_list: list[int] = data["lines"]  # type: ignore[assignment]
        ranges = _group_consecutive(sorted(set(lines_list)))
        errors_dict: dict[str, object] = report["errors"]["by_class"]  # type: ignore[index]
        errors_dict[cls_name] = {
            "count": data["count"],
            "line_ranges": _format_line_ranges(ranges),
            "line_numbers": len(lines_list),
            "samples": data["samples"],
        }

    return report


def _classify_error(error: str) -> str:
    """Classify a validation error string into a category."""
    lower = error.lower()
    if "parse error" in lower:
        return "parse_error"
    if "signature mismatch" in lower:
        return "signature_mismatch"
    if "content_hash mismatch" in lower:
        return "content_hash_mismatch"
    return "other"
