#!/usr/bin/env python3
"""Trace replay debugger for governance simulation traces.

Allows stepping through events, inspecting agent state transitions,
and replaying from checkpoints.

Usage:
    python scripts/trace_replay.py --input trace.json
    python scripts/trace_replay.py --input trace.json --step
    python scripts/trace_replay.py --input trace.json --goto 5
    python scripts/trace_replay.py --input trace.json --list-agents
    python scripts/trace_replay.py --input trace.json --filter-agent agent-alpha
    python scripts/trace_replay.py --input trace.json --checkpoint 3 --output checkpoint.json

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_trace(path: str) -> list[dict[str, Any]]:
    """Load a trace file (JSON array of tuples)."""
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Trace file {path} must contain a JSON array")
    return data


class TraceReplay:
    """Replay debugger for governance simulation traces."""

    def __init__(self, trace: list[dict[str, Any]]):
        self.trace = trace
        self.cursor = 0

    @property
    def current(self) -> dict[str, Any] | None:
        """Return the event at the current cursor position."""
        if 0 <= self.cursor < len(self.trace):
            return self.trace[self.cursor]
        return None

    @property
    def is_at_start(self) -> bool:
        return self.cursor == 0

    @property
    def is_at_end(self) -> bool:
        return self.cursor >= len(self.trace) - 1

    def step_forward(self) -> dict[str, Any] | None:
        """Move cursor forward by one event."""
        if self.cursor < len(self.trace) - 1:
            self.cursor += 1
        return self.current

    def step_backward(self) -> dict[str, Any] | None:
        """Move cursor backward by one event."""
        if self.cursor > 0:
            self.cursor -= 1
        return self.current

    def goto(self, index: int) -> dict[str, Any] | None:
        """Jump to a specific event index."""
        if 0 <= index < len(self.trace):
            self.cursor = index
        return self.current

    def reset(self) -> None:
        """Reset cursor to the beginning."""
        self.cursor = 0

    def list_agents(self) -> list[str]:
        """Return unique agent IDs in the trace."""
        agents = set()
        for t in self.trace:
            agent = t.get("agent", "")
            if agent:
                agents.add(agent)
        return sorted(agents)

    def filter_by_agent(self, agent_id: str) -> list[dict[str, Any]]:
        """Return events for a specific agent."""
        return [t for t in self.trace if t.get("agent") == agent_id]

    def get_state_at(self, index: int) -> dict[str, Any]:
        """Reconstruct agent state at a given index.

        Aggregates all events up to and including the given index,
        grouped by agent.
        """
        if index < 0 or index >= len(self.trace):
            return {}
        states: dict[str, dict[str, Any]] = {}
        for i in range(index + 1):
            t = self.trace[i]
            agent = t.get("agent", "unknown")
            if agent not in states:
                states[agent] = {
                    "agent": agent,
                    "events": [],
                    "states_seen": set(),
                    "tools_used": set(),
                    "tuple_types": set(),
                }
            states[agent]["events"].append({
                "index": i,
                "id": t.get("id", ""),
                "tuple_type": t.get("tuple_type", ""),
                "state": t.get("state", ""),
                "time": t.get("time", ""),
            })
            if t.get("state"):
                states[agent]["states_seen"].add(t["state"])
            if t.get("tool"):
                states[agent]["tools_used"].add(t["tool"])
            if t.get("tuple_type"):
                states[agent]["tuple_types"].add(t["tuple_type"])
        # Convert sets to sorted lists for JSON serialization
        for s in states.values():
            s["states_seen"] = sorted(s["states_seen"])
            s["tools_used"] = sorted(s["tools_used"])
            s["tuple_types"] = sorted(s["tuple_types"])
            s["event_count"] = len(s["events"])
        return states

    def checkpoint(self, index: int) -> dict[str, Any]:
        """Create a checkpoint at a given index.

        A checkpoint captures the cursor position and reconstructed state.
        """
        return {
            "checkpoint_index": index,
            "total_events": len(self.trace),
            "state_at_checkpoint": self.get_state_at(index),
            "event_at_checkpoint": self.trace[index] if 0 <= index < len(self.trace) else None,
        }

    def summary(self) -> dict[str, Any]:
        """Return a summary of the trace."""
        agents = self.list_agents()
        tuple_types = set()
        states = set()
        for t in self.trace:
            if t.get("tuple_type"):
                tuple_types.add(t["tuple_type"])
            if t.get("state"):
                states.add(t["state"])
        return {
            "total_events": len(self.trace),
            "agents": agents,
            "tuple_types": sorted(tuple_types),
            "states": sorted(states),
            "cursor": self.cursor,
        }

    def format_event(self, event: dict[str, Any], index: int) -> str:
        """Format a single event for display."""
        tt = event.get("tuple_type", "?")
        eid = event.get("id", "?")
        state = event.get("state", "?")
        agent = event.get("agent", "?")
        time = event.get("time", "?")
        return f"[{index:4d}] {tt:12s} | {eid:20s} | state={state:8s} | agent={agent:15s} | time={time}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input trace file (JSON array)")
    parser.add_argument("--step", action="store_true", help="Step through events one at a time")
    parser.add_argument("--goto", type=int, help="Jump to a specific event index")
    parser.add_argument("--list-agents", action="store_true", help="List unique agents in the trace")
    parser.add_argument("--filter-agent", help="Filter events by agent ID")
    parser.add_argument("--checkpoint", type=int, help="Create a checkpoint at the given index")
    parser.add_argument("--output", help="Output file for checkpoint or filtered results")
    parser.add_argument("--summary", action="store_true", help="Print trace summary")
    args = parser.parse_args(argv)

    trace = load_trace(args.input)
    replay = TraceReplay(trace)

    if args.summary:
        s = replay.summary()
        print(f"Trace Summary")
        print(f"  Total events: {s['total_events']}")
        print(f"  Agents: {', '.join(s['agents'])}")
        print(f"  Tuple types: {', '.join(s['tuple_types'])}")
        print(f"  States: {', '.join(s['states'])}")
        return 0

    if args.list_agents:
        agents = replay.list_agents()
        print(f"Agents in trace ({len(agents)}):")
        for a in agents:
            count = len(replay.filter_by_agent(a))
            print(f"  {a}: {count} events")
        return 0

    if args.filter_agent:
        events = replay.filter_by_agent(args.filter_agent)
        print(f"Events for agent '{args.filter_agent}' ({len(events)}):")
        for i, e in enumerate(events):
            idx = trace.index(e)
            print(replay.format_event(e, idx))
        if args.output:
            with Path(args.output).open("w", encoding="utf-8") as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"Wrote {len(events)} events to {args.output}")
        return 0

    if args.checkpoint is not None:
        cp = replay.checkpoint(args.checkpoint)
        output = json.dumps(cp, indent=2, ensure_ascii=False)
        if args.output:
            with Path(args.output).open("w", encoding="utf-8") as f:
                f.write(output)
                f.write("\n")
            print(f"Wrote checkpoint to {args.output}")
        else:
            print(output)
        return 0

    if args.goto is not None:
        event = replay.goto(args.goto)
        if event:
            print(replay.format_event(event, args.goto))
        else:
            print(f"Index {args.goto} out of range (0-{len(trace)-1})")
        return 0

    if args.step:
        replay.reset()
        while not replay.is_at_end:
            event = replay.current
            if event:
                print(replay.format_event(event, replay.cursor))
            replay.step_forward()
        # Print last event
        if replay.current:
            print(replay.format_event(replay.current, replay.cursor))
        return 0

    # Default: print current event and summary
    s = replay.summary()
    print(f"Trace: {s['total_events']} events, {len(s['agents'])} agents")
    if replay.current:
        print(replay.format_event(replay.current, replay.cursor))
    print(f"\nUse --step, --goto N, --list-agents, --filter-agent ID, --checkpoint N, or --summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
