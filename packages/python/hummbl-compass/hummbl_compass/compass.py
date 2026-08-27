"""hummbl-compass - Decision router for the hummbl-* repo ecosystem.

stdlib-only. Loads hummbl-topology.json and provides:
- Natural-language task routing
- Base120 transformation lookup
- Layer-based filtering
- Bridge traversal
- Gap reporting

Usage::

    from compass import Compass
    c = Compass()
    result = c.route("benchmark a kernel on Metal")
    print(result.repo.name, result.confidence)

CLI::

    python -m compass "benchmark a kernel on Metal"
    python -m compass --by-base120 SY20
    python -m compass --gaps
    python -m compass --bridges hummbl-governance
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TOPOLOGY_PATH = Path(__file__).parent / "hummbl-topology.json"

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "P": [
        "perspective", "viewpoint", "frame", "lens", "stakeholder", "narrative",
        "assumption", "identity", "context", "role", "empathy", "worldview",
        "cultural", "temporal", "spatial", "story", "positioning",
    ],
    "IN": [
        "invert", "reverse", "backwards", "opposite", "failure", "prevent", "avoid",
        "premortem", "subtraction", "constraint", "negate", "worst case",
        "red team", "adversarial", "anti", "kill", "stop", "harm", "risk",
    ],
    "CO": [
        "combine", "synergy", "integrate", "collaborate", "compose", "merge",
        "hybrid", "synthesis", "coalition", "network", "complement", "bundle",
        "platform", "pipeline", "orchestrate", "emerge", "pattern", "interdisciplinary",
    ],
    "DE": [
        "decompose", "break down", "root cause", "component", "layer", "hierarchy",
        "module", "diagnose", "separate", "tree", "analysis", "why", "cause",
        "taxonomy", "classify", "factor", "reduce", "dimension", "isolate",
    ],
    "RE": [
        "recursion", "iterate", "improve", "refine", "feedback", "loop", "repeat",
        "kaizen", "spiral", "self-similar", "cycle", "increment", "continuous",
        "learn", "calibrate", "compound", "bootstrap", "version", "diff",
    ],
    "SY": [
        "system", "leverage", "emergent", "dynamics", "flow", "stock", "complex",
        "network", "interdependence", "holistic", "interconnect", "feedback loop",
        "govern", "compliance", "resilience", "homeostasis", "ecosystem", "protocol",
    ],
}

LAYER_KEYWORDS: dict[str, list[str]] = {
    "L0": ["meta", "cross-cutting", "shared", "library", "topology", "taxonomy", "intelligence"],
    "L1": ["governance", "compliance", "legal", "risk", "safety", "adversarial", "security", "contract"],
    "L2": ["ml", "ai", "kernel", "gpu", "metal", "cuda", "benchmark", "model", "train", "inference", "alignment"],
    "L3": ["bus", "mesh", "coordination", "agent", "orchestration", "sync", "memory", "ledger"],
    "L4": ["strategy", "intel", "research", "positioning", "partnership", "category", "evidence"],
    "L5": ["human", "belonging", "cognition", "founder", "health", "wellbeing", "identity", "narrative"],
    "L6": ["production", "deploy", "live", "runtime", "ops", "service", "tool", "pipeline"],
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Repo:
    """A single hummbl-* repository from the topology."""

    name: str
    primary_base120: str
    secondary_base120s: tuple[str, ...]
    layer: str
    layer_name: str
    description: str
    bridges: tuple[str, ...]
    status: str
    size_category: str
    git_host: str = "github"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Repo:
        return cls(
            name=d["name"],
            primary_base120=d["primary_base120"],
            secondary_base120s=tuple(d.get("secondary_base120s", [])),
            layer=d["layer"],
            layer_name=d["layer_name"],
            description=d["description"],
            bridges=tuple(d.get("bridges", [])),
            status=d["status"],
            size_category=d["size_category"],
            git_host=d.get("git_host", "github"),
        )


@dataclass
class RouteResult:
    """Result of a task routing query."""

    repo: Repo
    confidence: float
    reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Topology loader
# ---------------------------------------------------------------------------

def _load_topology(path: Path | None = None) -> dict[str, Any]:
    p = path or _TOPOLOGY_PATH
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Compass
# ---------------------------------------------------------------------------

class Compass:
    """Decision router for the hummbl-* ecosystem."""

    def __init__(self, topology_path: Path | None = None) -> None:
        data = _load_topology(topology_path)
        self.version: str = data.get("schema_version", "unknown")
        self.repos: list[Repo] = [Repo.from_dict(r) for r in data["repos"]]
        self.gaps: list[dict[str, Any]] = data.get("gaps", [])
        self.cross_cutting: list[dict[str, Any]] = data.get("cross_cutting_concerns", [])
        self._by_name: dict[str, Repo] = {r.name: r for r in self.repos}
        self._by_layer: dict[str, list[Repo]] = {}
        self._by_base120: dict[str, list[Repo]] = {}
        for r in self.repos:
            self._by_layer.setdefault(r.layer, []).append(r)
            self._by_base120.setdefault(r.primary_base120, []).append(r)
            for s in r.secondary_base120s:
                self._by_base120.setdefault(s, []).append(r)

    # ------------------------------------------------------------------
    # Core routing
    # ------------------------------------------------------------------

    def route(self, query: str, top_k: int = 3) -> list[RouteResult]:
        """Route a natural-language task to the best repos."""
        q = query.lower()
        scores: dict[str, float] = {}
        reasons: dict[str, list[str]] = {}

        for repo in self.repos:
            s = 0.0
            rsn: list[str] = []

            # Keyword match against repo name and description
            name_words = set(repo.name.replace("hummbl-", "").split("-"))
            desc_words = set(repo.description.lower().split())
            query_words = set(re.findall(r"[a-z]+", q))

            name_overlap = len(name_words & query_words)
            desc_overlap = len(desc_words & query_words)
            s += name_overlap * 3.0 + desc_overlap * 1.5
            if name_overlap:
                rsn.append(f"name keyword match ({name_overlap})")
            if desc_overlap:
                rsn.append(f"description keyword match ({desc_overlap})")

            # Base120 domain keyword match
            domain = repo.primary_base120[:2] if len(repo.primary_base120) >= 2 else repo.primary_base120
            keywords = DOMAIN_KEYWORDS.get(domain, [])
            for kw in keywords:
                if kw in q:
                    s += 2.0
                    rsn.append(f"Base120 domain keyword '{kw}'")
                    break

            # Layer keyword match
            layer_kws = LAYER_KEYWORDS.get(repo.layer, [])
            for kw in layer_kws:
                if kw in q:
                    s += 1.5
                    rsn.append(f"layer keyword '{kw}'")
                    break

            # Secondary base120 match
            for sec in repo.secondary_base120s:
                sec_domain = sec[:2] if len(sec) >= 2 else sec
                sec_kws = DOMAIN_KEYWORDS.get(sec_domain, [])
                for kw in sec_kws:
                    if kw in q:
                        s += 1.0
                        rsn.append(f"secondary domain keyword '{kw}'")
                        break

            if s > 0:
                scores[repo.name] = s
                reasons[repo.name] = rsn

        # Normalize to confidence 0-1
        if scores:
            max_score = max(scores.values())
            for name in scores:
                scores[name] = scores[name] / max_score if max_score > 0 else 0.0

        # Sort and return top_k
        sorted_names = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]
        results: list[RouteResult] = []
        for name in sorted_names[:top_k]:
            results.append(
                RouteResult(
                    repo=self._by_name[name],
                    confidence=round(scores[name], 3),
                    reasons=reasons[name],
                )
            )
        return results

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def by_layer(self, layer: str) -> list[Repo]:
        """Return all repos in a given layer (e.g., 'L5')."""
        return list(self._by_layer.get(layer, []))

    def by_base120(self, code: str) -> list[Repo]:
        """Return all repos matching a Base120 code (primary or secondary)."""
        return list(self._by_base120.get(code, []))

    def bridges(self, repo_name: str) -> list[Repo]:
        """Return the repos that a given repo bridges to."""
        repo = self._by_name.get(repo_name)
        if repo is None:
            return []
        return [self._by_name[b] for b in repo.bridges if b in self._by_name]

    def report_gaps(self) -> list[dict[str, Any]]:
        """Return proposed repos for under-represented Base120 models."""
        return list(self.gaps)

    def stats(self) -> dict[str, Any]:
        """Return ecosystem statistics."""
        return {
            "total_repos": len(self.repos),
            "by_layer": {layer: len(repos) for layer, repos in self._by_layer.items()},
            "by_base120_domain": self._domain_counts(),
        }

    def _domain_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.repos:
            # Extract domain prefix by stripping trailing digits
            code = r.primary_base120
            prefix = code.rstrip("0123456789")
            counts[prefix] = counts.get(prefix, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fmt_repo(repo: Repo) -> str:
    return f"  {repo.name:<30} [{repo.layer} {repo.layer_name:<12}] {repo.primary_base120} - {repo.description}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="hummbl-compass - route tasks to the right hummbl-* repo")
    parser.add_argument("query", nargs="?", help="Natural-language task to route")
    parser.add_argument("--by-base120", metavar="CODE", help="List repos by Base120 code (e.g., SY20)")
    parser.add_argument("--by-layer", metavar="LAYER", help="List repos by layer (e.g., L5)")
    parser.add_argument("--bridges", metavar="REPO", help="Show bridge connections for a repo")
    parser.add_argument("--gaps", action="store_true", help="Show recommended new repos (gaps)")
    parser.add_argument("--stats", action="store_true", help="Show ecosystem statistics")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to show (default: 3)")
    parser.add_argument("--topology", type=Path, default=None, help="Path to custom topology JSON")
    args = parser.parse_args(argv)

    compass = Compass(topology_path=args.topology)

    if args.stats:
        stats = compass.stats()
        print("Ecosystem Statistics")
        print("=" * 40)
        print(f"Total repos: {stats['total_repos']}")
        print("\nBy layer:")
        for layer, count in sorted(stats["by_layer"].items()):
            print(f"  {layer}: {count}")
        print("\nBy Base120 domain:")
        for domain, count in sorted(stats["by_base120_domain"].items()):
            print(f"  {domain}: {count}")
        return 0

    if args.gaps:
        gaps = compass.report_gaps()
        if not gaps:
            print("No gaps defined in topology.")
            return 0
        print("Gap Analysis -- Proposed New Repos")
        print("=" * 50)
        for g in sorted(gaps, key=lambda x: x.get("priority", 99)):
            try:
                prio = g.get("priority", "?")
                print(f"\n  {g['repo_name']:<25} [P{prio}] {g['primary_base120']} ({g['layer']})")
                print(f"    {g['description']}")
                print(f"    Why: {g['justification']}")
            except Exception as e:
                print(f"    ERROR printing gap: {e}")
        return 0

    if args.by_base120:
        repos = compass.by_base120(args.by_base120)
        print(f"Repos matching Base120 {args.by_base120}: {len(repos)}")
        for r in repos:
            print(_fmt_repo(r))
        return 0

    if args.by_layer:
        repos = compass.by_layer(args.by_layer)
        print(f"Repos in layer {args.by_layer}: {len(repos)}")
        for r in repos:
            print(_fmt_repo(r))
        return 0

    if args.bridges:
        repos = compass.bridges(args.bridges)
        if not repos:
            print(f"No bridges found for {args.bridges}")
            return 1
        print(f"{args.bridges} bridges to {len(repos)} repos:")
        for r in repos:
            print(_fmt_repo(r))
        return 0

    if args.query:
        results = compass.route(args.query, top_k=args.top_k)
        if not results:
            print("No matching repos found.")
            return 1
        print(f"Top {len(results)} matches for: '{args.query}'")
        print("=" * 50)
        for i, res in enumerate(results, 1):
            print(f"\n{i}. {res.repo.name} (confidence: {res.confidence})")
            print(f"   [{res.repo.layer} {res.repo.layer_name}] {res.repo.primary_base120}")
            print(f"   {res.repo.description}")
            for reason in res.reasons:
                print(f"   * {reason}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
