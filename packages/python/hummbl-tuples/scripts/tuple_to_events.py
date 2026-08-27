#!/usr/bin/env python3
"""Convert tuple traces to structured event log formats.

Supports CloudEvents (https://cloudevents.io) and NDJSON output.

Usage:
    python scripts/tuple_to_events.py --input trace.json --format cloudevents --output events.json
    python scripts/tuple_to_events.py --input trace.json --format ndjson --output events.ndjson
    python scripts/tuple_to_events.py --input trace.json --format cloudevents

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def tuple_to_cloudevent(tuple_dict: dict[str, Any]) -> dict[str, Any]:
    """Convert a single HUMMBL tuple to a CloudEvent 1.0 dict.

    Mapping:
    - specversion: "1.0" (constant)
    - id: tuple id
    - time: tuple time
    - type: "hummbl.tuple.<tuple_type>.<state>" (e.g., hummbl.tuple.CONTRACT.ok)
    - source: "/hummbl/tuples/<agent>"
    - subject: intent_id (if present)
    - datacontenttype: "application/json"
    - data: the full tuple dict

    Extension attributes:
    - hummbltuple_type: original tuple_type
    - hummblstate: state (if present)
    - hummbldriftdrift: drift (if present)
    - hummbltier: tier (if present)
    - hummbltool: tool (if present)
    """
    tuple_type = tuple_dict.get("tuple_type", "UNKNOWN")
    state = tuple_dict.get("state", "")
    agent = tuple_dict.get("agent", "unknown")
    intent_id = tuple_dict.get("intent_id", "")

    event_type = f"hummbl.tuple.{tuple_type}"
    if state:
        event_type += f".{state}"

    event: dict[str, Any] = {
        "specversion": "1.0",
        "id": tuple_dict.get("id", ""),
        "time": tuple_dict.get("time", ""),
        "type": event_type,
        "source": f"/hummbl/tuples/{agent}",
        "datacontenttype": "application/json",
        "data": tuple_dict,
    }

    if intent_id:
        event["subject"] = intent_id

    # Extension attributes (HUMMBL-specific)
    event["hummbltuple_type"] = tuple_type
    if state:
        event["hummblstate"] = state
    if "drift" in tuple_dict:
        event["hummblrift"] = tuple_dict["drift"]
    if "tier" in tuple_dict:
        event["hummbltier"] = tuple_dict["tier"]
    if "tool" in tuple_dict:
        event["hummbltool"] = tuple_dict["tool"]

    return event


def tuple_to_ndjson(tuple_dict: dict[str, Any]) -> str:
    """Convert a single tuple to an NDJSON line (just JSON + newline)."""
    return json.dumps(tuple_dict, ensure_ascii=False, sort_keys=True)


def convert_trace(
    trace: list[dict[str, Any]],
    fmt: str,
) -> Any:
    """Convert a trace (list of tuples) to the target format.

    Args:
        trace: List of tuple dicts
        fmt: "cloudevents" or "ndjson"

    Returns:
        For cloudevents: list of CloudEvent dicts
        For ndjson: string of newline-delimited JSON
    """
    if fmt == "cloudevents":
        return [tuple_to_cloudevent(t) for t in trace]
    elif fmt == "ndjson":
        return "\n".join(tuple_to_ndjson(t) for t in trace) + "\n"
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input trace file (JSON array)")
    parser.add_argument("--output", help="Output file")
    parser.add_argument(
        "--format", required=True, choices=["cloudevents", "ndjson"], help="Output format"
    )
    args = parser.parse_args(argv)

    with Path(args.input).open("r", encoding="utf-8") as f:
        trace = json.load(f)

    if not isinstance(trace, list):
        raise ValueError(f"Input file {args.input} must contain a JSON array")

    result = convert_trace(trace, args.format)

    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as f:
            if isinstance(result, str):
                f.write(result)
            else:
                json.dump(result, f, indent=2, ensure_ascii=False)
                f.write("\n")
        print(f"Wrote {len(trace)} events to {args.output}")
    else:
        if isinstance(result, str):
            print(result, end="")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
