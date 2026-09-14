"""Print the canonical ARCANA sibling contract manifest as JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ecosystem_contracts as ec


def build_manifest() -> dict[str, object]:
    """Return the full ecosystem manifest for tooling and review packets."""
    return {
        "schema_version": "arcana-ecosystem-manifest-v0.1",
        "sibling_modules": ec.sibling_contract_manifest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true",
                        help="print compact JSON")
    args = parser.parse_args(argv)
    indent = None if args.compact else 2
    print(json.dumps(build_manifest(), indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
