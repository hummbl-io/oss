#!/usr/bin/env python3
"""Smoke check: load the Base120 registry and report counts by family.

Run from packages/python/base120:
    PYTHONPATH=. python3 examples/registry_smoke_check.py

Exits 0 if the registry holds exactly 120 operators, 20 per family.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from base120 import Engine

FAMILIES = ["P", "IN", "CO", "DE", "RE", "SY"]

def main() -> int:
    engine = Engine()
    ops = engine.list()
    counts = Counter(op.family for op in ops)
    for fam in FAMILIES:
        print(f"{fam}: {counts.get(fam, 0)}")
    print(f"TOTAL: {len(ops)}")
    ok = len(ops) == 120 and all(counts.get(f, 0) == 20 for f in FAMILIES)
    print("OK" if ok else "MISMATCH")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
