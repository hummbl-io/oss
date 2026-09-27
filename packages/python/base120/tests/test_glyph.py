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

"""Tests for base120.glyph — round-trip image encoding of a ledger."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path
from xml.etree import ElementTree

import pytest
from base120.cli import main
from base120.glyph import (
    FAMILY_COLORS,
    GLYPH_FORMAT,
    Glyph,
    GlyphError,
    _iter_chunks,
    decode,
    encode,
)
from base120.models import OperatorTuple

from base120 import Engine, Ledger, decode_glyph, encode_glyph

KEY = b"k" * 32
OTHER_KEY = b"j" * 32


def _entries() -> list[OperatorTuple]:
    return [
        OperatorTuple("P6", "2026-09-27T00:00:00Z", "anchor to the buyer", 0.1),
        OperatorTuple("DE1", "2026-09-27T00:00:01Z", 'split ]]> <x> "q" é →', 0.7),
        OperatorTuple("P6", "2026-09-27T00:00:02Z", "anchor again", 0.55),
        OperatorTuple("SY20", "2026-09-27T00:00:03Z", "close the loop", 0.0),
    ]


# ---------------------------------------------------------------------------
# Encode
# ---------------------------------------------------------------------------


class TestEncode:
    def test_counts_and_flags(self):
        g = encode(_entries(), max_drift=0.5)
        assert g.counts == {"P6": 2, "DE1": 1, "SY20": 1}
        assert g.flagged == {"P6", "DE1"}
        assert g.peak_drift["P6"] == 0.55

    def test_cut_threshold_is_strict(self):
        g = encode([OperatorTuple("P1", "t", "s", 0.5)], max_drift=0.5)
        assert g.flagged == frozenset()

    def test_unsigned_by_default(self):
        g = encode(_entries())
        assert g.signed is False
        assert g.signature is None
        assert g.payload["signed"] is False
        assert g.payload["alg"] is None

    def test_signed_with_key(self):
        g = encode(_entries(), key=KEY)
        assert g.signed is True
        assert g.verify(KEY) is True
        assert g.verify(OTHER_KEY) is False
        assert g.payload["alg"] == "HMAC-SHA256"

    def test_short_key_rejected(self):
        with pytest.raises(GlyphError, match="at least 32 bytes"):
            encode(_entries(), key=b"short")

    def test_unknown_code_rejected(self):
        with pytest.raises(GlyphError, match="Not a Base120 operator code"):
            encode([OperatorTuple("X1", "t", "s", 0.1)])

    @pytest.mark.parametrize("code", ["P0", "P21", "p6", "IN 1", "SY020", ""])
    def test_off_range_codes_rejected(self, code):
        with pytest.raises(GlyphError):
            encode([OperatorTuple(code, "t", "s", 0.1)])

    def test_bad_max_drift_rejected(self):
        with pytest.raises(GlyphError):
            encode(_entries(), max_drift=1.5)
        with pytest.raises(GlyphError):
            encode(_entries(), max_drift="0.5")  # type: ignore[arg-type]

    def test_empty_ledger_is_valid(self):
        g = encode([])
        assert g.counts == {}
        assert decode(g.to_svg()).entries == ()
        assert decode(g.to_png()).entries == ()

    def test_canonical_bytes_are_ascii_and_sorted(self):
        g = encode(_entries())
        raw = g.canonical
        raw.decode("ascii")
        obj = json.loads(raw)
        assert list(obj) == sorted(obj)
        assert obj["format"] == GLYPH_FORMAT

    def test_every_registry_code_places_on_the_grid(self):
        engine = Engine()
        entries = [OperatorTuple(op.code, "t", "s", 0.0) for op in engine.list()]
        g = encode(entries)
        assert len(g.counts) == 120
        assert set(g.counts) == {op.code for op in engine.list()}


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_svg_round_trip_exact(self):
        g = encode(_entries(), max_drift=0.5, key=KEY)
        svg = g.to_svg()
        d = decode(svg, key=KEY)
        assert d.entries == g.entries
        assert d.max_drift == g.max_drift
        assert d.signature == g.signature
        assert d.verified is True
        assert d.to_svg() == svg

    def test_png_round_trip_exact(self):
        g = encode(_entries(), max_drift=0.5, key=KEY)
        png = g.to_png()
        d = decode(png, key=KEY)
        assert d.entries == g.entries
        assert d.verified is True
        assert d.to_png() == png

    def test_svg_bytes_accepted(self):
        g = encode(_entries())
        assert decode(g.to_svg().encode("utf-8")).entries == g.entries

    def test_decode_without_key_leaves_verified_none(self):
        g = encode(_entries(), key=KEY)
        d = decode(g.to_svg())
        assert d.signed is True
        assert d.verified is None

    def test_decode_with_wrong_key_is_false(self):
        g = encode(_entries(), key=KEY)
        assert decode(g.to_png(), key=OTHER_KEY).verified is False

    def test_unsigned_glyph_with_key_is_false_not_error(self):
        g = encode(_entries())
        d = decode(g.to_svg(), key=KEY)
        assert d.signed is False
        assert d.verified is False

    def test_tampered_payload_fails_verification(self):
        g = encode(_entries(), key=KEY)
        tampered = g.to_svg().replace('"drift":0.7', '"drift":0.1')
        assert tampered != g.to_svg()
        assert decode(tampered, key=KEY).verified is False

    def test_visual_layer_regenerates_from_payload(self):
        g = encode(_entries(), key=KEY)
        d = decode(g.to_png(), key=KEY)
        assert Glyph(d.entries, d.max_drift, d.signature, None).to_svg() == g.to_svg()

    def test_digest_differs_between_different_ledgers(self):
        a = encode(_entries())
        b = encode(_entries()[:-1])
        assert a.digest != b.digest
        assert a.to_svg() != b.to_svg()

    def test_order_matters(self):
        es = _entries()
        a = encode(es)
        b = encode(list(reversed(es)))
        assert a.counts == b.counts
        assert a.to_svg() != b.to_svg()
        assert a.canonical != b.canonical


# ---------------------------------------------------------------------------
# Container formats
# ---------------------------------------------------------------------------


class TestContainers:
    def test_svg_is_well_formed_xml_with_metadata(self):
        g = encode(_entries())
        root = ElementTree.fromstring(g.to_svg())
        assert root.tag.endswith("svg")
        meta = [el for el in root.iter() if el.tag.endswith("metadata")]
        assert len(meta) == 1
        assert json.loads(meta[0].text)["format"] == GLYPH_FORMAT

    def test_png_structure_and_crcs(self):
        g = encode(_entries())
        png = g.to_png(scale=4)
        kinds = [k for k, _ in _iter_chunks(png)]
        assert kinds[0] == b"IHDR"
        assert kinds[-1] == b"IEND"
        assert b"iTXt" in kinds
        assert b"IDAT" in kinds
        ihdr = next(b for k, b in _iter_chunks(png) if k == b"IHDR")
        w, h, depth, ctype = struct.unpack(">IIBB", ihdr[:10])
        assert depth == 8 and ctype == 2
        idat = b"".join(b for k, b in _iter_chunks(png) if k == b"IDAT")
        raw = zlib.decompress(idat)
        assert len(raw) == h * (1 + w * 3)

    def test_png_scale_changes_dimensions_not_payload(self):
        g = encode(_entries())
        small = decode(g.to_png(scale=2))
        big = decode(g.to_png(scale=20))
        assert small.entries == big.entries == g.entries
        assert len(g.to_png(scale=2)) < len(g.to_png(scale=20))

    def test_png_zero_scale_rejected(self):
        with pytest.raises(GlyphError):
            encode(_entries()).to_png(scale=0)

    def test_corrupt_png_crc_detected(self):
        png = bytearray(encode(_entries()).to_png())
        idx = png.find(b"iTXt") + 4 + 10
        png[idx] ^= 0xFF
        with pytest.raises(GlyphError, match="CRC"):
            decode(bytes(png))

    def test_png_without_payload(self):
        png = encode(_entries()).to_png()
        chunks = [(k, b) for k, b in _iter_chunks(png) if k != b"iTXt"]
        out = bytearray(b"\x89PNG\r\n\x1a\n")
        for k, b in chunks:
            out += struct.pack(">I", len(b)) + k + b + struct.pack(">I", zlib.crc32(k + b) & 0xFFFFFFFF)
        with pytest.raises(GlyphError, match="No glyph payload"):
            decode(bytes(out))

    def test_svg_without_payload(self):
        with pytest.raises(GlyphError, match="No glyph payload"):
            decode('<svg xmlns="http://www.w3.org/2000/svg"/>')

    def test_not_svg_not_png(self):
        with pytest.raises(GlyphError):
            decode("definitely not xml <")

    def test_wrong_format_marker(self):
        bad = '<svg xmlns="http://www.w3.org/2000/svg"><metadata id="base120-glyph">{"format":"x"}</metadata></svg>'
        with pytest.raises(GlyphError, match="format marker"):
            decode(bad)

    def test_wrong_version(self):
        bad = (
            '<svg xmlns="http://www.w3.org/2000/svg"><metadata id="base120-glyph">'
            '{"format":"base120-glyph","version":99,"entries":[],"max_drift":0.5}</metadata></svg>'
        )
        with pytest.raises(GlyphError, match="version"):
            decode(bad)

    def test_entry_missing_field(self):
        bad = (
            '<svg xmlns="http://www.w3.org/2000/svg"><metadata id="base120-glyph">'
            '{"format":"base120-glyph","version":1,"entries":[{"id":"P1"}],"max_drift":0.5}</metadata></svg>'
        )
        with pytest.raises(GlyphError, match="missing fields"):
            decode(bad)


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------


class TestPalette:
    def test_six_families_have_hex_colors(self):
        assert set(FAMILY_COLORS) == {"P", "IN", "CO", "DE", "RE", "SY"}
        for hx in FAMILY_COLORS.values():
            assert len(hx) == 7 and hx.startswith("#")
            int(hx[1:], 16)

    def test_mirrors_design_tokens_when_present(self):
        tokens = Path(__file__).resolve().parents[3] / ("hummbl-design-tokens/hummbl_design_tokens/data/tokens.json")
        if not tokens.exists():
            pytest.skip("design tokens not in this checkout")
        block = json.loads(tokens.read_text(encoding="utf-8"))["base120_families"]
        mirrored = {k: v["hex"] for k, v in block.items() if not k.startswith("_")}
        assert mirrored == FAMILY_COLORS


# ---------------------------------------------------------------------------
# Package surface and CLI
# ---------------------------------------------------------------------------


class TestSurface:
    def test_package_exports(self):
        import base120

        assert base120.encode_glyph is encode
        assert base120.decode_glyph is decode
        assert "Glyph" in base120.__all__
        assert "GlyphError" in base120.__all__

    def test_public_helpers_roundtrip(self):
        g = encode_glyph(_entries())
        assert decode_glyph(g.to_svg()).entries == g.entries


class TestCli:
    def _ledger(self, tmp_path: Path) -> Path:
        led = tmp_path / "ledger.jsonl"
        ledger = Ledger(led)
        for e in _entries():
            ledger.append(e)
        return led

    def test_render_svg_to_file_and_decode(self, tmp_path, capsys):
        led = self._ledger(tmp_path)
        out = tmp_path / "g.svg"
        assert main(["glyph", "render", "--ledger", str(led), "-o", str(out)]) == 0
        assert decode(out.read_text()).entries == tuple(_entries())
        assert main(["glyph", "decode", str(out)]) == 0
        text = capsys.readouterr().out
        assert "entries:   4" in text
        assert "signed:    false" in text
        assert "P6, DE1" in text or "DE1, P6" in text

    def test_render_png_last_n(self, tmp_path):
        led = self._ledger(tmp_path)
        out = tmp_path / "g.png"
        assert main(["glyph", "render", "--ledger", str(led), "--format", "png", "--last", "2", "-o", str(out)]) == 0
        d = decode(out.read_bytes())
        assert [e.id for e in d.entries] == ["P6", "SY20"]

    def test_render_to_stdout(self, tmp_path, capsysbinary):
        led = self._ledger(tmp_path)
        assert main(["glyph", "render", "--ledger", str(led)]) == 0
        data = capsysbinary.readouterr().out
        assert decode(data).entries == tuple(_entries())

    def test_sign_and_verify_via_env(self, tmp_path, monkeypatch, capsys):
        led = self._ledger(tmp_path)
        out = tmp_path / "g.png"
        monkeypatch.setenv("BASE120_SIGNING_SECRET", "s" * 32)
        assert main(["glyph", "render", "--ledger", str(led), "--format", "png", "--sign", "-o", str(out)]) == 0
        assert main(["glyph", "decode", str(out), "--verify"]) == 0
        assert "verified:  true" in capsys.readouterr().out
        monkeypatch.setenv("BASE120_SIGNING_SECRET", "t" * 32)
        assert main(["glyph", "decode", str(out), "--verify"]) == 2
        assert "verified:  false" in capsys.readouterr().out

    def test_sign_without_secret_fails(self, tmp_path, monkeypatch, capsys):
        led = self._ledger(tmp_path)
        monkeypatch.delenv("BASE120_SIGNING_SECRET", raising=False)
        assert main(["glyph", "render", "--ledger", str(led), "--sign"]) == 1
        assert "BASE120_SIGNING_SECRET" in capsys.readouterr().err

    def test_short_secret_fails(self, tmp_path, monkeypatch, capsys):
        led = self._ledger(tmp_path)
        monkeypatch.setenv("BASE120_SIGNING_SECRET", "short")
        assert main(["glyph", "render", "--ledger", str(led), "--sign"]) == 1
        assert "at least 32 bytes" in capsys.readouterr().err

    def test_decode_json(self, tmp_path, capsys):
        led = self._ledger(tmp_path)
        out = tmp_path / "g.svg"
        main(["glyph", "render", "--ledger", str(led), "-o", str(out)])
        assert main(["glyph", "decode", str(out), "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["format"] == GLYPH_FORMAT
        assert len(payload["entries"]) == 4

    def test_decode_missing_file(self, tmp_path, capsys):
        assert main(["glyph", "decode", str(tmp_path / "nope.png")]) == 1
        assert "glyph decode failed" in capsys.readouterr().err

    def test_render_missing_ledger_is_empty_glyph(self, tmp_path):
        out = tmp_path / "g.svg"
        assert main(["glyph", "render", "--ledger", str(tmp_path / "none.jsonl"), "-o", str(out)]) == 0
        assert decode(out.read_text()).entries == ()

    def test_digest_is_sha256_of_canonical(self):
        g = encode(_entries())
        assert g.digest == hashlib.sha256(g.canonical).digest()
