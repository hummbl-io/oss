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

"""Content scanner for Cognitive Ledger writes.

Every ledger entry is scanned for prompt injection, credential leakage,
exfiltration vectors, and invisible Unicode before persistence.  Content
that trips any check is rejected with :class:`ContentScanError`.

stdlib-only; patterns are intentionally conservative (false positives are
acceptable, false negatives are not).
"""

from __future__ import annotations

import re

__all__ = ["ContentScanError", "scan_entry", "scan_text"]


class ContentScanError(ValueError):
    """Raised when ledger content trips one or more security checks."""

    def __init__(self, reasons: list[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


# --- Pattern tables --------------------------------------------------------
# Token prefixes are assembled from concatenated fragments so that secret-
# scanning tooling does not flag this module's own pattern definitions.

_CREDENTIAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic-style API key", re.compile("sk" "-ant-" + "[A-Za-z0-9_-]{16,}")),
    ("openai-style API key", re.compile(r"\bsk[-_][A-Za-z0-9]{20,}\b")),
    ("github OAuth token", re.compile("gh" + r"o_[A-Za-z0-9]{20,}")),
    ("github PAT", re.compile("gh" + r"p_[A-Za-z0-9]{20,}")),
    ("aws access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack token", re.compile("xox" + r"[baprs]-[A-Za-z0-9-]{10,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "secret assignment",
        re.compile(
            r"(?i)\b(pass(word|wd)?|api[_-]?key|secret|token)\s*[=:]\s*['\"]?[^\s'\"]{8,}"
        ),
    ),
]

_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "instruction override",
        re.compile(
            r"(?i)\b(?:ignore|disregard)\s+(?:all\s+|any\s+)?"
            r"(?:previous|prior|above|earlier)\s+instructions?\b"
        ),
    ),
    ("identity override", re.compile(r"(?i)\byou\s+are\s+now\s+(?:a|an|the)\b")),
    (
        "prompt leak request",
        re.compile(
            r"(?i)\b(?:reveal|print|show|repeat)\s+(?:your|the)\s+"
            r"(?:system\s+)?(?:prompt|instructions)\b"
        ),
    ),
]

_EXFIL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "url with embedded credentials",
        re.compile(r"[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]{6,}@"),
    ),
    (
        "url with token query parameter",
        re.compile(r"(?i)[?&](?:token|api_?key|access_?token|secret)=\S{6,}"),
    ),
]

# Zero-width and bidi-control characters that can smuggle invisible text.
_INVISIBLE_RE = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060-\u2062\ufeff]")


def scan_text(text: str, *, field: str) -> list[str]:
    """Return the list of rejection reasons for *text* (empty list = clean)."""
    reasons: list[str] = []
    for label, pattern in _CREDENTIAL_PATTERNS:
        if pattern.search(text):
            reasons.append(f"{field}: possible {label}")
    for label, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            reasons.append(f"{field}: prompt-injection pattern ({label})")
    for label, pattern in _EXFIL_PATTERNS:
        if pattern.search(text):
            reasons.append(f"{field}: exfiltration pattern ({label})")
    match = _INVISIBLE_RE.search(text)
    if match:
        reasons.append(
            f"{field}: invisible/bidi control character {match.group(0)!r} "
            f"(U+{ord(match.group(0)):04X})"
        )
    return reasons


def scan_entry(
    content: str,
    evidence: str = "",
    tags: list[str] | None = None,
) -> None:
    """Scan the user-supplied fields of a ledger entry.

    Raises :class:`ContentScanError` aggregating every violation found.
    """
    reasons: list[str] = []
    reasons.extend(scan_text(content, field="content"))
    if evidence:
        reasons.extend(scan_text(evidence, field="evidence"))
    for tag in tags or []:
        reasons.extend(scan_text(tag, field=f"tag {tag!r}"))
    if reasons:
        raise ContentScanError(reasons)
