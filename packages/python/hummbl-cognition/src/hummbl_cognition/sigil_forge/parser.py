"""Parser for the Sigil Forge prompt DSL.

Supported syntax:

    RETRIEVE(k=5) -> GENERATE(role=oracle, depth=high)
    LOOP(2) { REFINE(role=synthesizer) }
    IF(score < 0.8) { REFINE(iter=2) } ELSE { FORMAT(type=markdown) }

The parser intentionally stays small and stdlib-only. It accepts both ASCII
``->`` and the Unicode arrow used in transcripts.
"""

from __future__ import annotations

import re
from typing import Any

from hummbl_cognition.sigil_forge.ir import Condition, Program

_OPERATORS = {
    "CRITIQUE",
    "FILTER",
    "FORMAT",
    "GENERATE",
    "POLICY_CHECK",
    "REFINE",
    "RETRIEVE",
    "STORE",
    "TRANSFORM",
    "CONTEXT_RESET",
}
_CONDITION_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(<=|>=|==|!=|<|>)\s*(.+?)\s*$")


class ParseError(ValueError):
    """Raised when DSL text cannot be parsed."""


class DSLParser:
    """Parse Sigil Forge source into a structured AST."""

    def parse(self, text: str) -> tuple[Program, ...]:
        source = strip_comments(text).replace("→", "->").strip()
        if not source:
            raise ParseError("DSL source is empty")
        parser = _Parser(source)
        program = parser.parse_program(stop_on_closing_brace=False)
        parser.skip_separators()
        if not parser.at_end():
            raise ParseError(f"Unexpected trailing input near: {parser.remaining()!r}")
        return tuple(program)


class _Parser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0

    def at_end(self) -> bool:
        return self.pos >= len(self.source)

    def remaining(self) -> str:
        return self.source[self.pos : self.pos + 40]

    def parse_program(self, *, stop_on_closing_brace: bool) -> list[Program]:
        statements: list[Program] = []
        while not self.at_end():
            self.skip_separators()
            if stop_on_closing_brace and self.peek() == "}":
                break
            if self.at_end():
                break
            statements.append(self.parse_statement())
            self.skip_separators()
        if not statements:
            raise ParseError("Expected at least one statement")
        return statements

    def parse_statement(self) -> Program:
        name = self.parse_identifier().upper()
        if name == "LOOP":
            count = self.parse_loop_count()
            body = self.parse_block()
            return Program(kind="loop", params={"count": count}, body=tuple(body))
        if name == "IF":
            condition = self.parse_condition()
            body = self.parse_block()
            else_body: tuple[Program, ...] = ()
            self.skip_separators()
            if self.match_word("ELSE"):
                else_body = tuple(self.parse_block())
            return Program(kind="if", condition=condition, body=tuple(body), else_body=else_body)
        if name not in _OPERATORS:
            raise ParseError(f"Unknown operator: {name}")
        params = self.parse_params()
        return Program(kind="node", operator=name.lower(), params=params, body=(), condition=None)

    def parse_identifier(self) -> str:
        self.skip_ws()
        start = self.pos
        while not self.at_end() and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
            self.pos += 1
        if start == self.pos:
            raise ParseError(f"Expected identifier near: {self.remaining()!r}")
        return self.source[start : self.pos]

    def parse_params(self) -> dict[str, Any]:
        self.skip_ws()
        if self.peek() != "(":
            return {}
        content = self.read_parenthesized()
        if not content.strip():
            return {}
        params: dict[str, Any] = {}
        for item in self.split_top_level(content, ","):
            if "=" not in item:
                raise ParseError(f"Expected key=value argument, got: {item!r}")
            key, value = item.split("=", 1)
            key = key.strip()
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                raise ParseError(f"Invalid argument name: {key!r}")
            params[key] = parse_value(value.strip())
        return params

    def parse_loop_count(self) -> int:
        content = self.read_parenthesized().strip()
        if not content:
            raise ParseError("LOOP requires an iteration count")
        if "=" in content:
            key, value = content.split("=", 1)
            if key.strip() not in {"n", "count", "iter"}:
                raise ParseError("LOOP count argument must be n, count, or iter")
            content = value.strip()
        count = parse_value(content)
        if not isinstance(count, int) or count < 1:
            raise ParseError("LOOP count must be a positive integer")
        return count

    def parse_condition(self) -> Condition:
        content = self.read_parenthesized()
        match = _CONDITION_RE.match(content)
        if not match:
            raise ParseError(f"Invalid IF condition: {content!r}")
        metric, operator, raw_value = match.groups()
        return Condition(metric=metric, operator=operator, value=parse_value(raw_value.strip()))

    def parse_block(self) -> list[Program]:
        self.skip_ws()
        if self.peek() != "{":
            raise ParseError(f"Expected block near: {self.remaining()!r}")
        self.pos += 1
        body = self.parse_program(stop_on_closing_brace=True)
        self.skip_separators()
        if self.peek() != "}":
            raise ParseError("Unclosed block")
        self.pos += 1
        return body

    def read_parenthesized(self) -> str:
        self.skip_ws()
        if self.peek() != "(":
            raise ParseError(f"Expected '(' near: {self.remaining()!r}")
        self.pos += 1
        start = self.pos
        depth = 1
        in_quote: str | None = None
        while not self.at_end():
            char = self.source[self.pos]
            if in_quote:
                if char == in_quote:
                    in_quote = None
            elif char in {"'", '"'}:
                in_quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    content = self.source[start : self.pos]
                    self.pos += 1
                    return content
            self.pos += 1
        raise ParseError("Unclosed parenthesized expression")

    def split_top_level(self, text: str, delimiter: str) -> list[str]:
        parts: list[str] = []
        start = 0
        in_quote: str | None = None
        for index, char in enumerate(text):
            if in_quote:
                if char == in_quote:
                    in_quote = None
            elif char in {"'", '"'}:
                in_quote = char
            elif char == delimiter:
                parts.append(text[start:index].strip())
                start = index + 1
        parts.append(text[start:].strip())
        return [part for part in parts if part]

    def match_word(self, word: str) -> bool:
        self.skip_ws()
        end = self.pos + len(word)
        if self.source[self.pos:end].upper() != word:
            return False
        if end < len(self.source) and (self.source[end].isalnum() or self.source[end] == "_"):
            return False
        self.pos = end
        return True

    def skip_separators(self) -> None:
        while True:
            self.skip_ws()
            if self.source.startswith("->", self.pos):
                self.pos += 2
                continue
            if self.peek() == ";":
                self.pos += 1
                continue
            break

    def skip_ws(self) -> None:
        while not self.at_end() and self.source[self.pos].isspace():
            self.pos += 1

    def peek(self) -> str:
        if self.at_end():
            return ""
        return self.source[self.pos]


def parse_value(raw: str) -> Any:
    if not raw:
        raise ParseError("Parameter value cannot be empty")
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def strip_comments(text: str) -> str:
    """Remove hash comments outside quotes."""
    lines: list[str] = []
    for line in text.splitlines():
        in_quote: str | None = None
        kept: list[str] = []
        for char in line:
            if in_quote:
                kept.append(char)
                if char == in_quote:
                    in_quote = None
                continue
            if char in {"'", '"'}:
                in_quote = char
                kept.append(char)
                continue
            if char == "#":
                break
            kept.append(char)
        lines.append("".join(kept))
    return "\n".join(lines)
