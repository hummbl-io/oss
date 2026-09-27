"""The base120_families block must clear the fleet accessibility floors."""

from __future__ import annotations

import itertools

from hummbl_design_tokens.color import contrast_ratio, delta_e2000
from hummbl_design_tokens.loader import load_tokens

FAMILIES = ("P", "IN", "CO", "DE", "RE", "SY")


def _block() -> dict[str, str]:
    tokens = load_tokens()
    block = tokens["base120_families"]
    return {k: v["hex"] for k, v in block.items() if not k.startswith("_")}


def test_six_families_in_canonical_order():
    assert tuple(_block()) == FAMILIES


def test_pairwise_de2000_clears_floor():
    tokens = load_tokens()
    floor = tokens["accessibility"]["min_de2000_agent_colors"]
    block = _block()
    for a, b in itertools.combinations(FAMILIES, 2):
        assert delta_e2000(block[a], block[b]) >= floor, (a, b)


def test_contrast_on_canonical_surface():
    tokens = load_tokens()
    surface = tokens["meta"]["canonical_surface"]
    for fam, hx in _block().items():
        assert contrast_ratio(hx, surface) >= 4.5, fam
