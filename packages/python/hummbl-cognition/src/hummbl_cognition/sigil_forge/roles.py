"""Cognitive role registry for Sigil Forge execution."""

from __future__ import annotations

from dataclasses import dataclass

ROLES = {
    "critic": "Find contradictions, missing evidence, and fragile assumptions.",
    "default": "Complete the task using the provided constraints.",
    "librarian": "Retrieve and ground relevant context before synthesis.",
    "machine": "Produce strict, schema-friendly output.",
    "operative": "Execute procedural steps and preserve operational details.",
    "oracle": "Generate candidate answers and hypotheses.",
    "synthesizer": "Integrate critique into a concise final answer.",
}


def role_instruction(role: str) -> str:
    return ROLES.get(role, ROLES["default"])


class RolePolicyViolationError(ValueError):
    """Raised when a program uses an invalid role transition."""


RolePolicyViolation = RolePolicyViolationError


@dataclass(frozen=True)
class RolePolicy:
    allowed_transitions: frozenset[tuple[str, str]] = frozenset({
        ("default", "oracle"),
        ("default", "operative"),
        ("default", "librarian"),
        ("librarian", "oracle"),
        ("librarian", "critic"),
        ("oracle", "critic"),
        ("oracle", "synthesizer"),
        ("critic", "synthesizer"),
        ("synthesizer", "critic"),
        ("synthesizer", "machine"),
        ("operative", "critic"),
        ("operative", "machine"),
        ("machine", "critic"),
    })

    def validate_sequence(self, roles: list[str]) -> None:
        previous = "default"
        for role in roles:
            if role not in ROLES:
                raise RolePolicyViolation(f"Unknown role: {role}")
            if role == previous:
                continue
            if (previous, role) not in self.allowed_transitions:
                raise RolePolicyViolation(f"Role transition not allowed: {previous} -> {role}")
            previous = role
