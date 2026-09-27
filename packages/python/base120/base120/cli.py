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

"""Base120 CLI.

Commands:
  base120 list                    — list all 120 operators
  base120 list --family DE        — list operators for one family
  base120 get P6                  — show one operator's details
  base120 prompt P6 "problem"     — generate a system prompt
  base120 families                — list the 6 families with descriptions
  base120 verify-docs             — check README.md and llms.txt against registry
  base120 run program.b120        — execute a .b120 reasoning program
  base120 glyph render            — render the ledger as a glyph image (SVG/PNG)
  base120 glyph decode glyph.png  — read the ledger back out of a glyph image

Signing: ``glyph render --sign`` and ``glyph decode --verify`` read the
HMAC key from the BASE120_SIGNING_SECRET environment variable (>= 32 bytes).

Stdlib only. Zero third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from base120.engine import FAMILY_NAMES, Engine
from base120.glyph import DEFAULT_MAX_DRIFT, MIN_KEY_BYTES, GlyphError, decode, encode
from base120.ledger import Ledger

SIGNING_SECRET_ENV = "BASE120_SIGNING_SECRET"


def _cmd_list(engine: Engine, args: argparse.Namespace) -> int:
    family: str | None = args.family
    ops = engine.list(family=family)
    if not ops:
        print(f"No operators found for family {family!r}.", file=sys.stderr)
        return 1
    if family:
        fname = FAMILY_NAMES.get(family.upper(), family.upper())
        print(f"{fname} ({family.upper()}) — {len(ops)} operators\n")
    for op in ops:
        print(f"  {op.code:<6}  {op.name}")
    return 0


def _cmd_get(engine: Engine, args: argparse.Namespace) -> int:
    op = engine.get(args.code)
    if op is None:
        print(f"Unknown operator code: {args.code!r}", file=sys.stderr)
        return 1
    fname = FAMILY_NAMES.get(op.transformation, op.transformation)
    print(f"{op.code}: {op.name}")
    print(f"  Family:     {op.transformation} — {fname}")
    print(f"  Definition: {op.definition}")
    return 0


def _cmd_prompt(engine: Engine, args: argparse.Namespace) -> int:
    try:
        prompt = engine.prompt(args.code, args.problem)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(prompt)
    return 0


def _cmd_families(engine: Engine, _args: argparse.Namespace) -> int:
    for fam in engine.families():
        name = FAMILY_NAMES.get(fam, fam)
        ops = engine.list(family=fam)
        print(f"  {fam:<4}  {name:<16}  {len(ops)} operators")
    return 0


def _cmd_verify_docs(engine: Engine, _args: argparse.Namespace) -> int:
    """Check README.md and llms.txt operator names against the canonical registry."""
    root = Path(__file__).resolve().parents[1]
    canonical = {op.code: op.name for op in engine.list()}
    errors: list[str] = []

    for relative in ("README.md", "llms.txt"):
        path = root / relative
        if not path.exists():
            errors.append(f"{relative}: file not found")
            continue
        text = path.read_text(encoding="utf-8")

        # Check every operator appears with its canonical name
        missing: list[str] = []
        wrong: list[str] = []
        for code, name in sorted(canonical.items()):
            if relative == "llms.txt":
                expected = f"- {code} {name}"
            else:
                expected = f"{code} {name}"
            if expected not in text:
                # Check if code appears with a different name
                if relative == "llms.txt":
                    m = re.search(rf"^- {re.escape(code)}\s+(.+)$", text, re.MULTILINE)
                else:
                    m = re.search(
                        rf"\b{re.escape(code)}\s+(\S+(?:\s+\S+)*?)(?:\s*[|\n]|$)",
                        text,
                    )
                if m:
                    found = m.group(1).strip().rstrip(".")
                    if found.lower() != name.lower():
                        wrong.append(f'  {code}: found "{found}", expected "{name}"')
                missing.append(code)

        if missing:
            errors.append(f"{relative}: {len(missing)} operators missing: {missing[:5]}...")
        if wrong:
            errors.append(f"{relative}: {len(wrong)} misnamed operators:")
            errors.extend(wrong)

        # Check for phantom operator codes
        found_codes = set(re.findall(r"\b([PICDRS][A-Z]\d{1,2})\b", text))
        phantom = {
            c for c in found_codes if c not in canonical and re.match(r"^(P|IN|CO|DE|RE|SY)\d+$", c)
        }
        if phantom:
            errors.append(f"{relative}: {len(phantom)} phantom codes: {sorted(phantom)}")

    if errors:
        print(f"FAIL: {len(errors)} issue(s) found\n")
        for err in errors:
            print(f"  {err}")
        return 1

    print("OK: all 120 operators verified in README.md and llms.txt")
    return 0


def _cmd_run(engine: Engine, args: argparse.Namespace) -> int:
    """Execute a .b120 reasoning program."""
    try:
        from base120lang.interpreter import (
            BudgetExceededError,
            Interpreter,
            SchemaValidationError,
        )
        from base120lang.loader import LoadError, load_program
        from base120lang.mock_runner import MockRunner
    except ImportError:
        print(
            "base120lang is not installed. Install with: pip install -e .[lang]",
            file=sys.stderr,
        )
        return 1

    path = args.file
    try:
        program = load_program(path)
    except LoadError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    runner = MockRunner()
    interpreter = Interpreter(runner=runner)

    try:
        record = interpreter.run(program)
    except BudgetExceededError as e:
        print(f"Budget exceeded: {e}", file=sys.stderr)
        return 1
    except SchemaValidationError as e:
        print(f"Schema validation failed: {e}", file=sys.stderr)
        return 1

    # Print results
    print(f"Program: {record.program_name}")
    print(f"Input: {record.input}")
    print(f"Runner: {record.runner} v{record.runner_version}")
    print(f"Program hash: {record.program_hash[:16]}...")
    print()
    print(f"Steps ({len(record.steps)}):")
    for step in record.steps:
        conf = f"{step.confidence:.2f}" if step.confidence is not None else "N/A"
        print(f"  [{step.step_index}] {step.operator_code}: {step.status} (confidence={conf})")
    print()
    if record.recommendation is not None:
        print(f"Decision: {record.recommendation}")
    if record.confidence is not None:
        print(f"Confidence: {record.confidence:.2f}")
    print(f"Ledger entries: {len(record.ledger_trail)}")
    print(f"Started: {record.started_at}")
    print(f"Completed: {record.completed_at}")
    return 0


def _signing_key() -> bytes:
    raw = os.environ.get(SIGNING_SECRET_ENV)
    if not raw:
        raise GlyphError(f"{SIGNING_SECRET_ENV} is not set")
    key = raw.encode("utf-8")
    if len(key) < MIN_KEY_BYTES:
        raise GlyphError(f"{SIGNING_SECRET_ENV} must be at least {MIN_KEY_BYTES} bytes, got {len(key)}")
    return key


def _cmd_glyph_render(engine: Engine, args: argparse.Namespace) -> int:
    try:
        key = _signing_key() if args.sign else None
        ledger = Ledger(args.ledger) if args.ledger else Ledger()
        entries = ledger.project(args.last)
        glyph = encode(entries, max_drift=args.max_drift, key=key)
        if args.format == "png":
            data = glyph.to_png(scale=args.scale)
        else:
            data = glyph.to_svg().encode("utf-8")
    except (GlyphError, ValueError, OSError) as exc:
        print(f"glyph render failed: {exc}", file=sys.stderr)
        return 1
    if args.output:
        Path(args.output).write_bytes(data)
    else:
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
    return 0


def _cmd_glyph_decode(engine: Engine, args: argparse.Namespace) -> int:
    try:
        key = _signing_key() if args.verify else None
        glyph = decode(Path(args.file).read_bytes(), key=key)
    except (GlyphError, OSError, UnicodeDecodeError) as exc:
        print(f"glyph decode failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(glyph.payload, sort_keys=True, indent=2))
    else:
        verified = "n/a" if glyph.verified is None else str(glyph.verified).lower()
        print(f"entries:   {len(glyph.entries)}")
        print(f"max_drift: {glyph.max_drift}")
        print(f"signed:    {str(glyph.signed).lower()}")
        print(f"verified:  {verified}")
        print(f"flagged:   {', '.join(sorted(glyph.flagged)) or '-'}")
        for e in glyph.entries:
            print(f"  {e.id:<5} {e.time}  drift={e.drift}")
    if args.verify and glyph.verified is not True:
        return 2
    return 0


def _cmd_glyph(engine: Engine, args: argparse.Namespace) -> int:
    if args.glyph_command == "render":
        return _cmd_glyph_render(engine, args)
    if args.glyph_command == "decode":
        return _cmd_glyph_decode(engine, args)
    print("usage: base120 glyph {render,decode}", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="base120",
        description="Base120 — 120 reasoning operators for structured thinking.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # list
    p_list = sub.add_parser("list", help="List operators")
    p_list.add_argument(
        "--family",
        metavar="FAMILY",
        help="Filter by family: P, IN, CO, DE, RE, SY",
    )

    # get
    p_get = sub.add_parser("get", help="Show operator details")
    p_get.add_argument("code", help="Operator code, e.g. P6 or DE1")

    # prompt
    p_prompt = sub.add_parser("prompt", help="Generate a system prompt")
    p_prompt.add_argument("code", help="Operator code, e.g. P6")
    p_prompt.add_argument("problem", help="Problem statement to reason about")

    # families
    sub.add_parser("families", help="List the 6 operator families")

    # verify-docs
    sub.add_parser(
        "verify-docs",
        help="Check README.md and llms.txt operator names against the registry",
    )

    # run
    p_run = sub.add_parser("run", help="Execute a .b120 reasoning program")
    p_run.add_argument("file", help="Path to .b120 program file")

    # glyph
    p_glyph = sub.add_parser("glyph", help="Encode the ledger as an image, or decode one")
    glyph_sub = p_glyph.add_subparsers(dest="glyph_command", metavar="subcommand")
    glyph_sub.required = True

    p_render = glyph_sub.add_parser("render", help="Render ledger entries as a glyph image")
    p_render.add_argument("--ledger", metavar="PATH", help="Ledger JSONL path (default: ~/.base120/ledger.jsonl)")
    p_render.add_argument("--last", type=int, metavar="N", help="Only the last N entries")
    p_render.add_argument(
        "--max-drift",
        type=float,
        default=DEFAULT_MAX_DRIFT,
        metavar="F",
        help=f"cut() threshold for ring marks (default {DEFAULT_MAX_DRIFT})",
    )
    p_render.add_argument("--format", choices=("svg", "png"), default="svg", help="Output format (default svg)")
    p_render.add_argument("--scale", type=int, default=12, metavar="PX", help="PNG pixels per grid cell (default 12)")
    p_render.add_argument("--sign", action="store_true", help=f"HMAC-sign the payload with ${SIGNING_SECRET_ENV}")
    p_render.add_argument("-o", "--output", metavar="FILE", help="Write to FILE instead of stdout")

    p_decode = glyph_sub.add_parser("decode", help="Read the ledger back out of a glyph image")
    p_decode.add_argument("file", help="Glyph .svg or .png")
    p_decode.add_argument(
        "--verify", action="store_true", help=f"Verify the signature with ${SIGNING_SECRET_ENV}; exit 2 on failure"
    )
    p_decode.add_argument("--json", action="store_true", help="Print the raw payload as JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    engine = Engine()

    dispatch = {
        "list": _cmd_list,
        "get": _cmd_get,
        "prompt": _cmd_prompt,
        "families": _cmd_families,
        "verify-docs": _cmd_verify_docs,
        "run": _cmd_run,
        "glyph": _cmd_glyph,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(engine, args)


if __name__ == "__main__":
    sys.exit(main())
