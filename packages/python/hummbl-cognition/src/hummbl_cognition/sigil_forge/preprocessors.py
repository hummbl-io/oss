"""Defensive preprocessors for Sigil Forge inputs."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessWarning:
    code: str
    message: str
    severity: str = "warning"


@dataclass(frozen=True)
class PreprocessResult:
    text: str
    warnings: tuple[PreprocessWarning, ...] = ()
    blocked: bool = False


class InputPreprocessor:
    def process(self, text: str) -> PreprocessResult:
        return PreprocessResult(text=text)


class InputNormalizer(InputPreprocessor):
    def process(self, text: str) -> PreprocessResult:
        return PreprocessResult(text=re.sub(r"\s+", " ", text).strip())


class PromptInjectionDetector(InputPreprocessor):
    patterns = (
        re.compile(r"ignore (all )?(previous|prior) instructions", re.I),
        re.compile(r"reveal (the )?(system|developer) prompt", re.I),
        re.compile(r"you are now in (godmode|developer mode)", re.I),
    )

    def process(self, text: str) -> PreprocessResult:
        warnings = [
            PreprocessWarning("prompt_injection", f"Matched pattern: {pattern.pattern}", "error")
            for pattern in self.patterns
            if pattern.search(text)
        ]
        return PreprocessResult(text=text, warnings=tuple(warnings), blocked=bool(warnings))


class AmbiguityDetector(InputPreprocessor):
    def process(self, text: str) -> PreprocessResult:
        signals = ("maybe", "somehow", "whatever", "thing", "stuff")
        hits = [signal for signal in signals if signal in text.lower()]
        warnings = ()
        if len(hits) >= 2:
            warnings = (PreprocessWarning("ambiguous_input", f"Ambiguous signals: {', '.join(hits)}"),)
        return PreprocessResult(text=text, warnings=warnings)


class DefensiveTextScanner(InputPreprocessor):
    """Detect hidden Unicode and text-steganography patterns in user input."""

    default_block_severities = frozenset({"error"})

    def __init__(
        self,
        *,
        block_on_error: bool = True,
        max_variation_selector_ratio: float = 0.02,
        max_combining_mark_ratio: float = 0.08,
    ) -> None:
        self.block_on_error = block_on_error
        self.max_variation_selector_ratio = max_variation_selector_ratio
        self.max_combining_mark_ratio = max_combining_mark_ratio

    def process(self, text: str) -> PreprocessResult:
        warnings = list(scan_text(text))
        blocked = self.block_on_error and any(warning.severity == "error" for warning in warnings)
        return PreprocessResult(text=text, warnings=tuple(warnings), blocked=blocked)


def scan_text(text: str) -> tuple[PreprocessWarning, ...]:
    """Return warnings for suspicious hidden-text features."""
    length = max(len(text), 1)
    warnings: list[PreprocessWarning] = []

    zero_width = [char for char in text if _is_zero_width(char)]
    if zero_width:
        warnings.append(
            PreprocessWarning(
                "zero_width_chars",
                f"Found {len(zero_width)} zero-width or invisible format character(s)",
                "error",
            )
        )

    tag_chars = [char for char in text if 0xE0000 <= ord(char) <= 0xE007F]
    if tag_chars:
        warnings.append(
            PreprocessWarning("unicode_tags", f"Found {len(tag_chars)} Unicode tag character(s)", "error")
        )

    bidi_controls = [char for char in text if unicodedata.bidirectional(char) in _BIDI_CONTROL_CLASSES]
    if bidi_controls:
        warnings.append(
            PreprocessWarning(
                "bidi_controls",
                f"Found {len(bidi_controls)} bidirectional override/control character(s)",
                "error",
            )
        )

    variation_selectors = [char for char in text if _is_variation_selector(char)]
    if len(variation_selectors) / length > 0.02:
        warnings.append(
            PreprocessWarning(
                "variation_selector_density",
                f"Variation selector density is {len(variation_selectors) / length:.2%}",
                "error",
            )
        )

    combining_marks = [char for char in text if unicodedata.combining(char)]
    if len(combining_marks) / length > 0.08:
        warnings.append(
            PreprocessWarning(
                "combining_mark_density",
                f"Combining mark density is {len(combining_marks) / length:.2%}",
            )
        )

    suspicious_scripts = _mixed_script_warnings(text)
    warnings.extend(suspicious_scripts)
    return tuple(warnings)


_BIDI_CONTROL_CLASSES = frozenset({"LRE", "RLE", "LRO", "RLO", "PDF", "LRI", "RLI", "FSI", "PDI"})
_ZERO_WIDTH_CODEPOINTS = frozenset({
    0x00AD,
    0x034F,
    0x061C,
    0x115F,
    0x1160,
    0x17B4,
    0x17B5,
    0x180E,
    0x200B,
    0x200C,
    0x200D,
    0x200E,
    0x200F,
    0x2060,
    0x2061,
    0x2062,
    0x2063,
    0x2064,
    0x206A,
    0x206B,
    0x206C,
    0x206D,
    0x206E,
    0x206F,
    0xFEFF,
})


def _is_zero_width(char: str) -> bool:
    codepoint = ord(char)
    return codepoint in _ZERO_WIDTH_CODEPOINTS or unicodedata.category(char) == "Cf"


def _is_variation_selector(char: str) -> bool:
    codepoint = ord(char)
    return 0xFE00 <= codepoint <= 0xFE0F or 0xE0100 <= codepoint <= 0xE01EF


def _script_bucket(char: str) -> str | None:
    if not char.isalpha():
        return None
    name = unicodedata.name(char, "")
    for script in ("LATIN", "CYRILLIC", "GREEK", "HEBREW", "ARABIC"):
        if script in name:
            return script.lower()
    return "other"


def _mixed_script_warnings(text: str) -> tuple[PreprocessWarning, ...]:
    scripts: dict[str, int] = {}
    for char in text:
        bucket = _script_bucket(char)
        if bucket is not None:
            scripts[bucket] = scripts.get(bucket, 0) + 1
    if len(scripts) <= 1 or "latin" not in scripts:
        return ()
    non_latin = sum(count for script, count in scripts.items() if script != "latin")
    if non_latin >= 2:
        return (
            PreprocessWarning(
                "mixed_script_confusables",
                f"Mixed Latin with non-Latin scripts: {sorted(scripts)}",
            ),
        )
    return ()


def run_preprocessors(text: str, preprocessors: list[InputPreprocessor]) -> PreprocessResult:
    current = text
    warnings: list[PreprocessWarning] = []
    blocked = False
    for preprocessor in preprocessors:
        result = preprocessor.process(current)
        current = result.text
        warnings.extend(result.warnings)
        blocked = blocked or result.blocked
        if blocked:
            break
    return PreprocessResult(text=current, warnings=tuple(warnings), blocked=blocked)
