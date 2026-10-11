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

"""base120 — 120 reasoning operators for structured thinking.

Version 2 of the base120 Python SDK. Stdlib-only. Zero third-party runtime
dependencies. Tuple-native output aligned to the Krineia governance model.

Quick start::

    from base120 import Engine

    engine = Engine()

    # Discover operators
    op = engine.get("P6")           # Operator(code='P6', name='Point-of-View Anchoring', ...)
    ops = engine.list(family="DE")  # 20 Decomposition operators

    # Generate a system prompt for any LLM
    prompt = engine.prompt("P6", "How should we price the certification tier?")

    # Record an application as a governance artifact
    result = engine.record("P6", "How should...", "Anchor to compliance officer POV", 0.85)
    t = result.to_tuple()  # OperatorTuple(id='P6', time='...Z', state='...', drift=0.15)
    # Append to the Krineia audit ledger
    from base120 import Ledger
    ledger = Ledger()
    ledger.append(t)                  # ~/.base120/ledger.jsonl
    high_drift = ledger.cut(0.5)      # entries with drift > 0.5

Krineia alignment:
  to_tuple() fields map to the 4 Krineia node fields:
    id    → who/what (operator code)
    time  → when     (UTC ISO-8601)
    state → current condition (recommendation)
    drift → deviation from setpoint (1.0 - confidence)

CLI::

    base120 list
    base120 list --family DE
    base120 get P6
    base120 prompt P6 "your problem here"
    base120 families
    base120 glyph render --format png -o ledger.png
    base120 glyph decode ledger.png

Glyph::

    from base120 import Ledger, encode_glyph, decode_glyph
    glyph = encode_glyph(Ledger().project(), max_drift=0.5)
    png = glyph.to_png()                 # 6x20 grid + order strip + payload
    assert decode_glyph(png).entries == glyph.entries

Apache 2.0. Copyright 2026 HUMMBL, LLC.
"""

from __future__ import annotations

from base120.engine import FAMILIES, FAMILY_NAMES, Engine
from base120.glyph import Glyph, GlyphError
from base120.glyph import decode as decode_glyph
from base120.glyph import encode as encode_glyph
from base120.ledger import Ledger
from base120.models import ApplyResult, Operator, OperatorTuple

__version__ = "3.1.0"

__all__ = [
    "FAMILIES",
    "FAMILY_NAMES",
    "ApplyResult",
    "Engine",
    "Glyph",
    "GlyphError",
    "Ledger",
    "Operator",
    "OperatorTuple",
    "__version__",
    "decode_glyph",
    "encode_glyph",
]
