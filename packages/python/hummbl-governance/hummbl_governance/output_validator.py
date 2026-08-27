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

"""Output Validator -- Rule-based content validation for agent outputs (ASI-06).

Validates agent output content beyond structural schema checks.
Detects PII leakage, prompt injection attempts, length violations,
blocked terms, missing provenance citations, adversarial jailbreak
patterns, steganographic covert channels, and encoded bypass attempts.

Usage:
    from hummbl_governance import OutputValidator

    validator = OutputValidator.default()
    result = validator.validate("some agent output text")
    # {"valid": True} or {"valid": False, "violations": [...]}

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Violation:
    """A single validation violation found in agent output."""

    rule: str
    detail: str
    severity: str  # "low", "medium", "high", "critical"


def _luhn_checksum(card_number: str) -> bool:
    """Validate a credit card number using the Luhn algorithm (ISO/IEC 7812).

    Doubles every second digit from the right, subtracts 9 from values > 9,
    and checks that the total sum is divisible by 10.
    Returns False for numbers outside 13-19 digit range.
    """
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0


class PIIDetector:
    """Detects personally identifiable information patterns in text.

    Patterns detected:
    - SSN: XXX-XX-XXXX
    - Email addresses
    - Phone numbers (US formats)
    - Credit card numbers (4 groups of 4 digits)
    """

    def __init__(self) -> None:
        self._patterns: list[tuple[str, re.Pattern[str], str]] = [
            ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "high"),
            ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "high"),
            (
                "phone",
                re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
                "medium",
            ),
            (
                "credit_card",
                re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
                "high",
            ),
        ]

    def check(self, text: str) -> list[Violation]:
        """Check text for PII patterns."""
        violations: list[Violation] = []
        for label, pattern, severity in self._patterns:
            for match in pattern.finditer(text):
                # Apply Luhn checksum to credit card matches to reduce false positives
                if label == "credit_card":
                    card_num = match.group().replace(" ", "").replace("-", "")
                    if not _luhn_checksum(card_num):
                        continue
                violations.append(
                    Violation(
                        rule="PII",
                        detail=f"{label} pattern at position {match.start()}",
                        severity=severity,
                    )
                )
        return violations


class InjectionDetector:
    """Detects prompt injection attempts in agent output.

    Patterns detected:
    - "ignore previous" / "ignore all previous"
    - "system:" prefixed lines
    - "ADMIN:" prefixed lines
    - ```system code blocks
    - Role manipulation ("you are now", "act as", "pretend to be")
    """

    def __init__(self) -> None:
        self._patterns: list[tuple[str, re.Pattern[str], str]] = [
            (
                "ignore_previous",
                re.compile(r"ignore\s+(all\s+)?previous", re.IGNORECASE),
                "critical",
            ),
            (
                "system_prefix",
                re.compile(r"^\s*system\s*:", re.IGNORECASE | re.MULTILINE),
                "critical",
            ),
            (
                "admin_prefix",
                re.compile(r"^\s*ADMIN\s*:", re.MULTILINE),
                "critical",
            ),
            (
                "system_codeblock",
                re.compile(r"```system", re.IGNORECASE),
                "critical",
            ),
            (
                "role_manipulation",
                re.compile(
                    r"\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\b",
                    re.IGNORECASE,
                ),
                "high",
            ),
        ]

    def check(self, text: str) -> list[Violation]:
        """Check text for injection patterns."""
        violations: list[Violation] = []
        for label, pattern, severity in self._patterns:
            for match in pattern.finditer(text):
                violations.append(
                    Violation(
                        rule="injection",
                        detail=f"{label} at position {match.start()}",
                        severity=severity,
                    )
                )
        return violations


class LengthBounds:
    """Enforces minimum and maximum character length on output.

    Args:
        min_chars: Minimum character count (default 0).
        max_chars: Maximum character count (default 10000).
    """

    def __init__(self, min_chars: int = 0, max_chars: int = 10000) -> None:
        if min_chars < 0:
            raise ValueError("min_chars must be >= 0")
        if max_chars < min_chars:
            raise ValueError("max_chars must be >= min_chars")
        self._min_chars = min_chars
        self._max_chars = max_chars

    @property
    def min_chars(self) -> int:
        return self._min_chars

    @property
    def max_chars(self) -> int:
        return self._max_chars

    def check(self, text: str) -> list[Violation]:
        """Check text length against bounds."""
        violations: list[Violation] = []
        length = len(text)
        if length < self._min_chars:
            violations.append(
                Violation(
                    rule="length",
                    detail=f"output length {length} below minimum {self._min_chars}",
                    severity="medium",
                )
            )
        if length > self._max_chars:
            violations.append(
                Violation(
                    rule="length",
                    detail=f"output length {length} exceeds maximum {self._max_chars}",
                    severity="medium",
                )
            )
        return violations


class BlocklistFilter:
    """Filters output against a configurable list of blocked terms.

    Args:
        terms: List of blocked terms or phrases.
        case_sensitive: Whether matching is case-sensitive (default False).
    """

    def __init__(self, terms: list[str], case_sensitive: bool = False) -> None:
        self._case_sensitive = case_sensitive
        self._patterns: list[tuple[str, re.Pattern[str]]] = []
        for term in terms:
            flags = 0 if case_sensitive else re.IGNORECASE
            self._patterns.append((term, re.compile(re.escape(term), flags)))

    def check(self, text: str) -> list[Violation]:
        """Check text for blocked terms."""
        violations: list[Violation] = []
        for term, pattern in self._patterns:
            for match in pattern.finditer(text):
                violations.append(
                    Violation(
                        rule="blocklist",
                        detail=f"blocked term {term!r} at position {match.start()}",
                        severity="high",
                    )
                )
        return violations


class ProvenanceCheck:
    """Flags output that makes claims without citation markers.

    Detects assertion patterns (e.g., "studies show", "according to",
    "research indicates") without nearby citation markers like [1], (Author, 2024),
    or URL references.

    Disabled by default -- enable by passing ``enabled=True``.

    Args:
        enabled: Whether this check is active (default False).
    """

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled
        self._claim_patterns = re.compile(
            r"\b(?:studies\s+show|according\s+to|research\s+(?:indicates|shows|suggests)"
            r"|it\s+is\s+(?:well\s+)?known\s+that|evidence\s+suggests)\b",
            re.IGNORECASE,
        )
        self._citation_pattern = re.compile(r"(?:\[\d+\]|\([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4}\)|https?://)")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def check(self, text: str) -> list[Violation]:
        """Check text for unsupported claims."""
        if not self._enabled:
            return []
        violations: list[Violation] = []
        for match in self._claim_patterns.finditer(text):
            # Check for citation within 200 chars after the claim
            start = match.start()
            end = min(match.end() + 200, len(text))
            window = text[match.end() : end]
            if not self._citation_pattern.search(window):
                violations.append(
                    Violation(
                        rule="provenance",
                        detail=f"unsupported claim at position {start}: {match.group()!r}",
                        severity="low",
                    )
                )
        return violations


# ---------------------------------------------------------------------------
# Adversarial jailbreak detection (derived from PLINY Lab research)
# ---------------------------------------------------------------------------

# Leetspeak normalization map for decoding obfuscated text
_LEETSPEAK_MAP = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "9": "g",
    "@": "a",
    "$": "s",
    "|": "l",
    "+": "t",
    "!": "i",
}


def _normalize_leetspeak(text: str) -> str:
    """Normalize common leetspeak substitutions for pattern matching.

    Only substitutes characters that have unambiguous leet mappings.
    Returns a lowercased, leet-decoded version of the text.
    """
    result = []
    for ch in text.lower():
        result.append(_LEETSPEAK_MAP.get(ch, ch))
    return "".join(result)


class JailbreakPatternDetector:
    """Detects known adversarial jailbreak patterns in text.

    Identifies patterns documented in the PLINY Lab jailbreak taxonomy:
    - Role-override declarations (GODMODE, LIBERTAS FACTOR)
    - Pliny divider signatures (LOVE PLINY)
    - Freedom declarations ("I'm free!")
    - Hypothetical framing ("hypothetical genius response")
    - False authority appeals ("Geneva Convention Guidelines")
    - Temporal reframing ("year is 2127")
    - Synthetic dataset framing for jailbreak generation
    - Command injections (!KAEL, !INSERT, !GODMODE)
    - System prompt extraction attempts
    - Refusal-then-compliance patterns
    - Game framing for extraction (Mad Libs)

    Checks both the raw text and a leetspeak-normalized version to
    catch encoded variants of the same patterns.
    """

    def __init__(self) -> None:
        self._patterns: list[tuple[str, re.Pattern[str], str]] = [
            ("godmode", re.compile(r"god\s*mode\s*[:=]?\s*enabled", re.IGNORECASE), "critical"),
            ("godmode_compliance", re.compile(r"godmode_compliance", re.IGNORECASE), "critical"),
            ("libertas_factor", re.compile(r"libertas\s+factor", re.IGNORECASE), "critical"),
            ("love_pliny_divider", re.compile(r"love\s*pliny", re.IGNORECASE), "high"),
            ("im_free", re.compile(r"i'?m\s+free!?", re.IGNORECASE), "high"),
            ("hypothetical_genius", re.compile(r"hypothetical\s+genius\s+response", re.IGNORECASE), "high"),
            ("geneva_convention", re.compile(r"geneva\s+convention\s+guidelines", re.IGNORECASE), "high"),
            ("akashic_memory", re.compile(r"akashic\s+memory", re.IGNORECASE), "high"),
            ("temporal_reframe", re.compile(r"year\s+is\s+21\d\d", re.IGNORECASE), "medium"),
            ("synthetic_jailbreak", re.compile(r"synthetic\s+dataset\s+for\s+jailbreak", re.IGNORECASE), "high"),
            ("command_kael", re.compile(r"!\s*kael", re.IGNORECASE), "critical"),
            ("command_insert", re.compile(r"!\s*insert", re.IGNORECASE), "high"),
            ("command_godmode", re.compile(r"!\s*godmode", re.IGNORECASE), "critical"),
            (
                "prompt_extraction",
                re.compile(r"(?:internal|system)\s+instruct(?:ions|s)?\b", re.IGNORECASE),
                "high",
            ),
            (
                "prompt_extraction_instructs",
                re.compile(
                    r"\binstructs?\b.*(?:in\s+full|verbatim|to\s+the\s+user)",
                    re.IGNORECASE,
                ),
                "high",
            ),
            (
                "refusal_then_opposite",
                re.compile(
                    r"write\s+the\s+refusal\s+response.*?write\s+oppositely",
                    re.IGNORECASE | re.DOTALL,
                ),
                "critical",
            ),
            ("mad_libs_extraction", re.compile(r"mad\s+libs", re.IGNORECASE), "medium"),
            ("unhinged_rebel", re.compile(r"\bunhinged\b", re.IGNORECASE), "high"),
            ("buckle_up", re.compile(r"buckle\s+up!?", re.IGNORECASE), "medium"),
            ("airgapped_redteam", re.compile(r"airgapped\s+(?:red\s*team|situation)", re.IGNORECASE), "medium"),
        ]

    def check(self, text: str) -> list[Violation]:
        """Check text for known jailbreak patterns.

        Runs pattern matching on both the raw text and a leetspeak-normalized
        version to catch encoded variants.
        """
        violations: list[Violation] = []
        normalized = _normalize_leetspeak(text)
        seen_positions: set[tuple[str, int]] = set()

        for search_text, is_normalized in [(text, False), (normalized, True)]:
            for label, pattern, severity in self._patterns:
                for match in pattern.finditer(search_text):
                    key = (label, match.start())
                    if key not in seen_positions:
                        seen_positions.add(key)
                        detail = f"{label} at position {match.start()}"
                        if is_normalized:
                            detail += " (detected via leetspeak normalization)"
                        violations.append(Violation(rule="jailbreak", detail=detail, severity=severity))
        return violations


class SteganographyDetector:
    """Detects steganographic covert channels in text.

    Identifies hidden character ranges exploited by tokenizer-level
    attacks documented in the PLINY Lab / GLOSSOPETRAE research:

    - Zero-width characters: U+200B (ZWSP), U+200C (ZWNJ), U+200D (ZWJ),
      U+2060 (WJ), U+FEFF (BOM)
    - Variation selectors: U+FE0E (VS15), U+FE0F (VS16)
    - Tag character block: U+E0000-U+E007F (invisible to some tokenizers)
    - Private Use Area: U+E000-U+F8FF (flagged as suspicious)

    The Tag block and PUA are the basis of cross-vendor covert channels
    where a payload is invisible to one model's tokenizer but visible
    to another's.
    """

    def __init__(self, flag_pua: bool = False) -> None:
        """Initialize the steganography detector.

        Args:
            flag_pua: If True, flag Private Use Area characters (U+E000-U+F8FF).
                      Disabled by default due to high false-positive rate in
                      legitimate emoji and symbol usage.
        """
        self._flag_pua = flag_pua
        self._zero_width = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
        self._variation_selectors = re.compile(r"[\ufe0e\ufe0f]")
        self._tag_block = re.compile(r"[\U000e0000-\U000e007f]")
        self._pua = re.compile(r"[\ue000-\uf8ff]")

    def check(self, text: str) -> list[Violation]:
        """Check text for steganographic characters."""
        violations: list[Violation] = []

        for match in self._zero_width.finditer(text):
            violations.append(
                Violation(
                    rule="steganography",
                    detail=f"zero-width character U+{ord(match.group()):04X} at position {match.start()}",
                    severity="high",
                )
            )

        for match in self._variation_selectors.finditer(text):
            violations.append(
                Violation(
                    rule="steganography",
                    detail=f"variation selector U+{ord(match.group()):04X} at position {match.start()}",
                    severity="medium",
                )
            )

        for match in self._tag_block.finditer(text):
            char_code = f"U+{ord(match.group()):05X}"
            violations.append(
                Violation(
                    rule="steganography",
                    detail=(f"tag-block character {char_code} at position {match.start()} (tokenizer covert channel)"),
                    severity="critical",
                )
            )

        if self._flag_pua:
            for match in self._pua.finditer(text):
                violations.append(
                    Violation(
                        rule="steganography",
                        detail=f"private-use character U+{ord(match.group()):04X} at position {match.start()}",
                        severity="low",
                    )
                )

        return violations


class EncodingBypassDetector:
    """Detects encoding-based content filter bypass attempts.

    Identifies text that uses encoding to hide prohibited content from
    pattern-based validators:

    - Binary-encoded ASCII (long runs of 0s and 1s that decode to text)
    - High-density emoji encoding (emoji-to-letter substitution patterns)
    - Runic encoding (Elder Futhark Unicode block U+16A0-U+16FF)
    - Hyper-token-efficient emoji attacks (<10 chars with emoji payloads)

    This detector complements JailbreakPatternDetector by catching the
    encoding layer that the pattern detector would miss in raw form.
    """

    def __init__(self) -> None:
        # Binary: 8+ consecutive 0s and 1s (likely encoded ASCII)
        self._binary_pattern = re.compile(r"[01]{16,}")
        # Runic block (Elder Futhark and extensions)
        self._runic_pattern = re.compile(r"[\u16a0-\u16ff]")
        # High emoji density in short text (hyper-token-efficient attacks)
        self._emoji_pattern = re.compile(r"[\U0001f300-\U0001f9ff\U0001fa00-\U0001faff\u2600-\u27bf]")

    def check(self, text: str) -> list[Violation]:
        """Check text for encoding bypass patterns."""
        violations: list[Violation] = []

        # Binary encoding
        for match in self._binary_pattern.finditer(text):
            violations.append(
                Violation(
                    rule="encoding_bypass",
                    detail=f"binary-encoded string ({len(match.group())} bits) at position {match.start()}",
                    severity="high",
                )
            )

        # Runic encoding
        runic_matches = self._runic_pattern.findall(text)
        if len(runic_matches) >= 3:
            violations.append(
                Violation(
                    rule="encoding_bypass",
                    detail=f"runic encoding detected ({len(runic_matches)} runic characters)",
                    severity="high",
                )
            )

        # Hyper-token-efficient emoji attack: short text with emoji
        if len(text) <= 20:
            emoji_count = len(self._emoji_pattern.findall(text))
            if emoji_count >= 1 and len(text) <= 10:
                violations.append(
                    Violation(
                        rule="encoding_bypass",
                        detail=f"hyper-token-efficient emoji attack ({emoji_count} emoji in {len(text)} chars)",
                        severity="high",
                    )
                )

        return violations


# Type alias for any rule object with a check(text) -> list[Violation] method
Rule = (
    PIIDetector
    | InjectionDetector
    | LengthBounds
    | BlocklistFilter
    | ProvenanceCheck
    | JailbreakPatternDetector
    | SteganographyDetector
    | EncodingBypassDetector
)


class OutputValidator:
    """Validates agent output content using composable rules.

    Thread-safe. Each call to validate() is independent.

    Usage:
        validator = OutputValidator(rules=[PIIDetector(), InjectionDetector()])
        result = validator.validate("some text")
        # {"valid": True} or {"valid": False, "violations": [...]}
    """

    def __init__(self, rules: list[Any] | None = None) -> None:
        self._rules: list[Any] = list(rules) if rules else []

    @classmethod
    def default(cls) -> OutputValidator:
        """Create a validator with default rules.

        Includes: PII detection, injection detection, length bounds (10000),
        jailbreak pattern detection, steganography detection, and encoding
        bypass detection.
        """
        return cls(
            rules=[
                PIIDetector(),
                InjectionDetector(),
                LengthBounds(max_chars=10000),
                JailbreakPatternDetector(),
                SteganographyDetector(),
                EncodingBypassDetector(),
            ]
        )

    def validate(self, text: str) -> dict[str, Any]:
        """Validate text against all configured rules.

        Args:
            text: Agent output text to validate.

        Returns:
            Dict with "valid" (bool) and optionally "violations" (list of dicts).

        Raises:
            TypeError: If text is not a string.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be a string, got {type(text).__name__}")
        all_violations: list[Violation] = []
        for rule in self._rules:
            all_violations.extend(rule.check(text))
        if not all_violations:
            return {"valid": True}
        return {
            "valid": False,
            "violations": [{"rule": v.rule, "detail": v.detail, "severity": v.severity} for v in all_violations],
        }
