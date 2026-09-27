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

"""Base120 glyph: a round-trippable image encoding of a ledger.

A glyph is a two-layer image built from Krineia ledger entries:

  Visual layer   6 x 20 grid, one row per family, one cell per operator.
                 Cell intensity  = how many times the operator was applied.
                 Amber ring      = at least one application exceeded the
                                   cut() threshold (drift > max_drift).
                 Order strip     = one column per ledger entry, in insertion
                                   order, colored by family. Composition is
                                   non-commutative, so sequence is preserved.
                 Digest strip    = 16 greyscale cells from SHA-256 of the
                                   machine layer, so two glyphs that differ
                                   look different at a glance.
  Machine layer  Canonical JSON payload embedded in the image (SVG
                 <metadata> or PNG iTXt chunk). Carries every entry
                 byte-exact plus an optional HMAC-SHA256 signature.

The encoder is external analysis over Ledger.project() and Ledger.cut().
It never writes to a ledger and the Engine never calls it, which keeps the
Krineia no-self-reference invariant intact.

Round-trip contract::

    g = encode(entries, max_drift=0.5, key=secret)
    d = decode(g.to_png(), key=secret)
    assert d.entries == g.entries          # byte-exact machine layer
    assert d.verified is True              # signature checks out
    assert d.to_svg() == g.to_svg()        # visual layer regenerates

Signing follows the fleet convention: the key is injected as bytes, is
optional, and must be at least 32 bytes when present. An unsigned glyph is
still decodable; its payload says ``"signed": false`` so absence reads as
unknown rather than clean.

Stdlib only. Zero third-party dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import struct
import zlib
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from base120.engine import FAMILIES
from base120.models import OperatorTuple

__all__ = [
    "DEFAULT_MAX_DRIFT",
    "FAMILY_COLORS",
    "GLYPH_FORMAT",
    "GLYPH_VERSION",
    "MIN_KEY_BYTES",
    "Glyph",
    "GlyphError",
    "decode",
    "encode",
]

GLYPH_FORMAT = "base120-glyph"
GLYPH_VERSION = 1
DEFAULT_MAX_DRIFT = 0.5
MIN_KEY_BYTES = 32

#: PNG iTXt keyword and SVG <metadata> id that carry the machine layer.
PAYLOAD_KEY = GLYPH_FORMAT

#: Family hues. Validated against the fleet design-token floors: every pair
#: clears CIEDE2000 >= 10 and every hue clears 4.5:1 contrast on SURFACE.
FAMILY_COLORS: dict[str, str] = {
    "P": "#4C8DFF",
    "IN": "#3FB950",
    "CO": "#B07CFF",
    "DE": "#F0883E",
    "RE": "#FF7EB6",
    "SY": "#2DD4BF",
}

#: Canonical dark surface from the fleet design tokens.
SURFACE = "#0F0F12"
#: Empty cell fill (an operator never applied).
EMPTY_CELL = "#1C1C22"
#: Ring color for cells surfaced by cut(): the fleet DEGRADED status hue.
RING = "#F59E0B"

_CODE_RE = re.compile(r"^(P|IN|CO|DE|RE|SY)(20|1[0-9]|[1-9])$")

# Layout in abstract units. One grid cell is 1.0 unit; scale sets pixels.
_COLS = 20
_ROWS = len(FAMILIES)
_GAP = 0.2
_MARGIN = 1.0
_STRIP_GAP = 0.6
_STRIP_H = 1.0
_DIGEST_CELLS = 16
_RING_W = 0.15
_MIN_T = 0.35  # minimum blend toward the family hue for a lit cell

_GRID_W = _COLS * (1 + _GAP) - _GAP
_GRID_H = _ROWS * (1 + _GAP) - _GAP
_ORDER_Y = _MARGIN + _GRID_H + _STRIP_GAP
_DIGEST_Y = _ORDER_Y + _STRIP_H + _STRIP_GAP
_WIDTH = _MARGIN * 2 + _GRID_W
_HEIGHT = _DIGEST_Y + _STRIP_H + _MARGIN


class GlyphError(ValueError):
    """Raised when a glyph cannot be encoded or decoded."""


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _mix(a: str, b: str, t: float) -> str:
    """Linear blend from color ``a`` toward color ``b`` by ``t`` in [0, 1]."""
    ra, ga, ba = _hex_to_rgb(a)
    rb, gb, bb = _hex_to_rgb(b)
    return _rgb_to_hex(
        (
            round(ra + (rb - ra) * t),
            round(ga + (gb - ga) * t),
            round(ba + (bb - ba) * t),
        )
    )


def _family_of(code: str) -> str:
    m = _CODE_RE.match(code)
    if m is None:
        raise GlyphError(f"Not a Base120 operator code: {code!r}")
    return m.group(1)


def _cell_of(code: str) -> tuple[int, int]:
    """Return (row, col) for an operator code."""
    m = _CODE_RE.match(code)
    if m is None:
        raise GlyphError(f"Not a Base120 operator code: {code!r}")
    return FAMILIES.index(m.group(1)), int(m.group(2)) - 1


# ---------------------------------------------------------------------------
# Machine layer
# ---------------------------------------------------------------------------


def _canonical_body(entries: tuple[OperatorTuple, ...], max_drift: float) -> dict[str, Any]:
    return {
        "format": GLYPH_FORMAT,
        "version": GLYPH_VERSION,
        "max_drift": max_drift,
        "entries": [{"id": e.id, "time": e.time, "state": e.state, "drift": e.drift} for e in entries],
    }


def _canonical_bytes(body: dict[str, Any]) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _check_key(key: bytes | None) -> None:
    if key is None:
        return
    if not isinstance(key, (bytes, bytearray)):
        raise GlyphError("Signing key must be bytes")
    if len(key) < MIN_KEY_BYTES:
        raise GlyphError(f"Signing key must be at least {MIN_KEY_BYTES} bytes, got {len(key)}")


def _sign(canonical: bytes, key: bytes) -> str:
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Glyph
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Glyph:
    """An encoded ledger: machine-layer payload plus visual-layer renderers.

    Attributes:
        entries:   Ledger entries in insertion order (the order strip).
        max_drift: cut() threshold used for ring marks.
        signature: HMAC-SHA256 hex over the canonical payload, or None.
        verified:  None when decoded without a key or freshly encoded;
                   True/False when decoded with a key.
    """

    entries: tuple[OperatorTuple, ...]
    max_drift: float
    signature: str | None
    verified: bool | None

    # -- derived views -----------------------------------------------------

    @property
    def signed(self) -> bool:
        return self.signature is not None

    @property
    def counts(self) -> dict[str, int]:
        """Applications per operator code, insertion order of first appearance."""
        out: dict[str, int] = {}
        for e in self.entries:
            out[e.id] = out.get(e.id, 0) + 1
        return out

    @property
    def peak_drift(self) -> dict[str, float]:
        """Maximum drift observed per operator code."""
        out: dict[str, float] = {}
        for e in self.entries:
            out[e.id] = max(out.get(e.id, 0.0), e.drift)
        return out

    @property
    def flagged(self) -> frozenset[str]:
        """Codes with at least one entry surfaced by cut(max_drift)."""
        return frozenset(e.id for e in self.entries if e.drift > self.max_drift)

    @property
    def body(self) -> dict[str, Any]:
        return _canonical_body(self.entries, self.max_drift)

    @property
    def canonical(self) -> bytes:
        """Canonical payload bytes. This is what the signature covers."""
        return _canonical_bytes(self.body)

    @property
    def digest(self) -> bytes:
        return hashlib.sha256(self.canonical).digest()

    @property
    def payload(self) -> dict[str, Any]:
        env = dict(self.body)
        env["signed"] = self.signed
        env["signature"] = self.signature
        env["alg"] = "HMAC-SHA256" if self.signed else None
        return env

    @property
    def payload_text(self) -> str:
        return json.dumps(self.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    # -- visual layer ------------------------------------------------------

    def _cell_fill(self, code: str, max_count: int) -> str:
        n = self.counts.get(code, 0)
        if n == 0:
            return EMPTY_CELL
        t = _MIN_T + (1.0 - _MIN_T) * (n / max_count)
        return _mix(SURFACE, FAMILY_COLORS[_family_of(code)], t)

    def _cells(self) -> list[tuple[float, float, str, bool]]:
        """Grid cells as (x, y, fill, ringed) in unit coordinates."""
        max_count = max(self.counts.values(), default=0)
        flagged = self.flagged
        cells = []
        for row, fam in enumerate(FAMILIES):
            for col in range(_COLS):
                code = f"{fam}{col + 1}"
                x = _MARGIN + col * (1 + _GAP)
                y = _MARGIN + row * (1 + _GAP)
                cells.append((x, y, self._cell_fill(code, max_count), code in flagged))
        return cells

    def to_svg(self) -> str:
        """Render the glyph as an SVG document with the payload in <metadata>."""
        out = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_WIDTH:g} {_HEIGHT:g}" '
            f'width="{_WIDTH * 12:g}" height="{_HEIGHT * 12:g}" '
            f'data-format="{GLYPH_FORMAT}" data-version="{GLYPH_VERSION}">',
            f'<metadata id="{PAYLOAD_KEY}">{escape(self.payload_text)}</metadata>',
            f'<rect width="{_WIDTH:g}" height="{_HEIGHT:g}" fill="{SURFACE}"/>',
        ]
        for x, y, fill, ringed in self._cells():
            out.append(f'<rect x="{x:g}" y="{y:g}" width="1" height="1" fill="{fill}"/>')
            if ringed:
                half = _RING_W / 2
                out.append(
                    f'<rect x="{x + half:g}" y="{y + half:g}" '
                    f'width="{1 - _RING_W:g}" height="{1 - _RING_W:g}" '
                    f'fill="none" stroke="{RING}" stroke-width="{_RING_W:g}"/>'
                )
        n = len(self.entries)
        if n:
            w = _GRID_W / n
            for i, e in enumerate(self.entries):
                x = _MARGIN + i * w
                fill = FAMILY_COLORS[_family_of(e.id)]
                out.append(f'<rect x="{x:g}" y="{_ORDER_Y:g}" width="{w:g}" height="{_STRIP_H:g}" fill="{fill}"/>')
                if e.drift > self.max_drift:
                    out.append(f'<rect x="{x:g}" y="{_ORDER_Y:g}" width="{w:g}" height="{_RING_W:g}" fill="{RING}"/>')
        else:
            out.append(
                f'<rect x="{_MARGIN:g}" y="{_ORDER_Y:g}" width="{_GRID_W:g}" '
                f'height="{_STRIP_H:g}" fill="{EMPTY_CELL}"/>'
            )
        dw = _GRID_W / _DIGEST_CELLS
        for i, b in enumerate(self.digest[:_DIGEST_CELLS]):
            x = _MARGIN + i * dw
            out.append(
                f'<rect x="{x:g}" y="{_DIGEST_Y:g}" width="{dw:g}" height="{_STRIP_H:g}" '
                f'fill="{_mix(SURFACE, "#FFFFFF", b / 255)}"/>'
            )
        out.append("</svg>")
        return "\n".join(out) + "\n"

    def to_png(self, scale: int = 12) -> bytes:
        """Render the glyph as an RGB PNG with the payload in an iTXt chunk."""
        if scale < 1:
            raise GlyphError("scale must be >= 1")
        w = round(_WIDTH * scale)
        h = round(_HEIGHT * scale)
        canvas = _Raster(w, h, SURFACE)
        s = scale

        for x, y, fill, ringed in self._cells():
            px, py = round(x * s), round(y * s)
            canvas.fill(px, py, s, s, fill)
            if ringed:
                canvas.stroke(px, py, s, s, max(1, round(_RING_W * s)), RING)

        n = len(self.entries)
        x0 = round(_MARGIN * s)
        x1 = round((_MARGIN + _GRID_W) * s)
        oy = round(_ORDER_Y * s)
        oh = round(_STRIP_H * s)
        if n:
            span = x1 - x0
            for i, e in enumerate(self.entries):
                a = x0 + (i * span) // n
                b = x0 + ((i + 1) * span) // n
                if b <= a:
                    continue
                canvas.fill(a, oy, b - a, oh, FAMILY_COLORS[_family_of(e.id)])
                if e.drift > self.max_drift:
                    canvas.fill(a, oy, b - a, max(1, round(_RING_W * s)), RING)
        else:
            canvas.fill(x0, oy, x1 - x0, oh, EMPTY_CELL)

        dy = round(_DIGEST_Y * s)
        span = x1 - x0
        for i, byte in enumerate(self.digest[:_DIGEST_CELLS]):
            a = x0 + (i * span) // _DIGEST_CELLS
            b = x0 + ((i + 1) * span) // _DIGEST_CELLS
            canvas.fill(a, dy, b - a, oh, _mix(SURFACE, "#FFFFFF", byte / 255))

        return canvas.to_png(text={PAYLOAD_KEY: self.payload_text})

    def verify(self, key: bytes) -> bool:
        """Return True if ``key`` reproduces this glyph's signature."""
        _check_key(key)
        if self.signature is None:
            return False
        return hmac.compare_digest(_sign(self.canonical, key), self.signature)


# ---------------------------------------------------------------------------
# Encode / decode
# ---------------------------------------------------------------------------


def encode(
    entries: list[OperatorTuple] | tuple[OperatorTuple, ...],
    *,
    max_drift: float = DEFAULT_MAX_DRIFT,
    key: bytes | None = None,
) -> Glyph:
    """Encode ledger entries into a Glyph.

    Args:
        entries:   Output of Ledger.project(). Order is preserved.
        max_drift: Threshold for ring marks, same semantics as Ledger.cut().
        key:       Optional HMAC-SHA256 key, >= 32 bytes. None leaves the
                   glyph unsigned and the payload says so.

    Raises:
        GlyphError: On an unknown operator code, a short key, or a bad drift.
    """
    _check_key(key)
    if not isinstance(max_drift, (int, float)) or isinstance(max_drift, bool):
        raise GlyphError("max_drift must be a number")
    if not 0.0 <= max_drift <= 1.0:
        raise GlyphError(f"max_drift must be within [0, 1], got {max_drift}")
    fixed = tuple(OperatorTuple(id=e.id, time=e.time, state=e.state, drift=e.drift) for e in entries)
    for e in fixed:
        _family_of(e.id)
        if not isinstance(e.drift, (int, float)) or isinstance(e.drift, bool):
            raise GlyphError(f"drift must be a number for {e.id}, got {e.drift!r}")
    body = _canonical_body(fixed, float(max_drift))
    signature = _sign(_canonical_bytes(body), key) if key is not None else None
    return Glyph(entries=fixed, max_drift=float(max_drift), signature=signature, verified=None)


def decode(data: bytes | str, *, key: bytes | None = None) -> Glyph:
    """Decode a glyph from SVG text or PNG bytes.

    Args:
        data: SVG document (str or bytes) or PNG bytes.
        key:  Optional key. When given, ``verified`` is True or False.
              When omitted, ``verified`` is None and the signature is
              carried through untested.

    Raises:
        GlyphError: If no payload is found or the payload is malformed.
    """
    _check_key(key)
    if isinstance(data, str):
        text = _payload_from_svg(data)
    elif data[:8] == _PNG_SIG:
        text = _payload_from_png(data)
    else:
        text = _payload_from_svg(data.decode("utf-8", errors="strict"))
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GlyphError(f"Glyph payload is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("format") != GLYPH_FORMAT:
        raise GlyphError("Glyph payload has the wrong format marker")
    if payload.get("version") != GLYPH_VERSION:
        raise GlyphError(f"Unsupported glyph version: {payload.get('version')!r}")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        raise GlyphError("Glyph payload entries must be a list")
    entries = []
    for i, obj in enumerate(raw_entries):
        if not isinstance(obj, dict):
            raise GlyphError(f"Glyph entry {i} is not an object")
        missing = {"id", "time", "state", "drift"} - obj.keys()
        if missing:
            raise GlyphError(f"Glyph entry {i} missing fields {sorted(missing)}")
        entries.append(OperatorTuple(id=obj["id"], time=obj["time"], state=obj["state"], drift=obj["drift"]))
    max_drift = payload.get("max_drift")
    signature = payload.get("signature")
    if signature is not None and not isinstance(signature, str):
        raise GlyphError("Glyph signature must be a string or null")
    glyph = encode(entries, max_drift=max_drift)
    glyph = Glyph(entries=glyph.entries, max_drift=glyph.max_drift, signature=signature, verified=None)
    if key is not None:
        glyph = Glyph(
            entries=glyph.entries,
            max_drift=glyph.max_drift,
            signature=signature,
            verified=glyph.verify(key),
        )
    return glyph


def _payload_from_svg(text: str) -> str:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise GlyphError(f"Not a valid SVG document: {exc}") from exc
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] == "metadata" and el.get("id") == PAYLOAD_KEY:
            return el.text or ""
    raise GlyphError("No glyph payload found in SVG <metadata>")


# ---------------------------------------------------------------------------
# Minimal PNG writer / reader
# ---------------------------------------------------------------------------

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


class _Raster:
    """Tiny RGB raster with rectangle fill and stroke. Row-major bytearray."""

    def __init__(self, width: int, height: int, background: str) -> None:
        self.w = width
        self.h = height
        r, g, b = _hex_to_rgb(background)
        self.buf = bytearray(bytes((r, g, b)) * (width * height))

    def fill(self, x: int, y: int, w: int, h: int, color: str) -> None:
        if w <= 0 or h <= 0:
            return
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(_hex_to_rgb(color)) * (x1 - x0)
        for yy in range(y0, y1):
            start = (yy * self.w + x0) * 3
            self.buf[start : start + len(row)] = row

    def stroke(self, x: int, y: int, w: int, h: int, t: int, color: str) -> None:
        self.fill(x, y, w, t, color)
        self.fill(x, y + h - t, w, t, color)
        self.fill(x, y, t, h, color)
        self.fill(x + w - t, y, t, h, color)

    def to_png(self, text: dict[str, str] | None = None) -> bytes:
        stride = self.w * 3
        raw = bytearray()
        for yy in range(self.h):
            raw.append(0)  # filter type None
            raw.extend(self.buf[yy * stride : (yy + 1) * stride])
        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        out = bytearray(_PNG_SIG)
        out += _chunk(b"IHDR", ihdr)
        for kw, val in (text or {}).items():
            body = kw.encode("latin-1") + b"\x00" + b"\x00\x00" + b"\x00" + b"\x00" + val.encode("utf-8")
            out += _chunk(b"iTXt", body)
        out += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        out += _chunk(b"IEND", b"")
        return bytes(out)


def _iter_chunks(data: bytes):
    if data[:8] != _PNG_SIG:
        raise GlyphError("Not a PNG file")
    pos = 8
    n = len(data)
    while pos + 8 <= n:
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        crc = data[pos + 8 + length : pos + 12 + length]
        if len(body) != length or len(crc) != 4:
            raise GlyphError("Truncated PNG chunk")
        if struct.unpack(">I", crc)[0] != (zlib.crc32(kind + body) & 0xFFFFFFFF):
            raise GlyphError(f"PNG chunk {kind!r} failed CRC")
        yield kind, body
        pos += 12 + length
        if kind == b"IEND":
            return


def _payload_from_png(data: bytes) -> str:
    for kind, body in _iter_chunks(data):
        if kind != b"iTXt":
            continue
        kw, _, rest = body.partition(b"\x00")
        if kw.decode("latin-1") != PAYLOAD_KEY or len(rest) < 2:
            continue
        compressed = rest[0]
        rest = rest[2:]  # compression flag + method
        _, _, rest = rest.partition(b"\x00")  # language tag
        _, _, rest = rest.partition(b"\x00")  # translated keyword
        if compressed:
            rest = zlib.decompress(rest)
        return rest.decode("utf-8")
    raise GlyphError("No glyph payload found in PNG iTXt")
