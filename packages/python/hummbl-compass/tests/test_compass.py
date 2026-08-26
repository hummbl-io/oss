"""Tests for hummbl-compass.

Run: pytest tests/test_compass.py -v
"""

from pathlib import Path

import pytest

from compass import Compass, Repo

# Path to topology relative to repo root
_TOPOLOGY = Path(__file__).parent.parent / "hummbl-topology.json"


@pytest.fixture
def compass() -> Compass:
    return Compass(topology_path=_TOPOLOGY)


class TestLoad:
    def test_version(self, compass: Compass) -> None:
        assert compass.version == "1.1.0"

    def test_repo_count(self, compass: Compass) -> None:
        assert len(compass.repos) == 41

    def test_all_repos_have_required_fields(self, compass: Compass) -> None:
        for repo in compass.repos:
            assert repo.name.startswith("hummbl-")
            assert repo.primary_base120
            assert repo.layer
            assert repo.description
            assert repo.status in ("active", "experimental", "stale", "deprecated", "archived")


class TestByLayer:
    def test_l5_human_layer(self, compass: Compass) -> None:
        repos = compass.by_layer("L5")
        names = {r.name for r in repos}
        assert "hummbl-bki" in names
        assert "hummbl-hrsi" in names
        assert "hummbl-professor" in names

    def test_l2_technical_layer(self, compass: Compass) -> None:
        repos = compass.by_layer("L2")
        names = {r.name for r in repos}
        assert "hummbl-kernel-forge" in names
        assert "hummbl-agi" in names


class TestByBase120:
    def test_sy20_coordination(self, compass: Compass) -> None:
        repos = compass.by_base120("SY20")
        names = {r.name for r in repos}
        assert "hummbl-bus" in names
        assert "hummbl-mesh" in names

    def test_p3_identity(self, compass: Compass) -> None:
        repos = compass.by_base120("P3")
        names = {r.name for r in repos}
        assert "hummbl-bki" in names


class TestRoute:
    def test_route_kernel_benchmark(self, compass: Compass) -> None:
        results = compass.route("benchmark a kernel on Metal", top_k=3)
        assert len(results) > 0
        names = [r.repo.name for r in results]
        assert "hummbl-kernel-forge" in names

    def test_route_governance(self, compass: Compass) -> None:
        results = compass.route("design a governance control catalog", top_k=3)
        assert len(results) > 0
        names = [r.repo.name for r in results]
        assert "hummbl-governance" in names

    def test_route_belonging(self, compass: Compass) -> None:
        results = compass.route("check my belonging baseline", top_k=3)
        assert len(results) > 0
        names = [r.repo.name for r in results]
        assert "hummbl-hrsi" in names or "hummbl-bki" in names

    def test_confidence_range(self, compass: Compass) -> None:
        results = compass.route("something about ML", top_k=3)
        for r in results:
            assert 0.0 <= r.confidence <= 1.0


class TestBridges:
    def test_bki_bridges(self, compass: Compass) -> None:
        repos = compass.bridges("hummbl-bki")
        names = {r.name for r in repos}
        assert "hummbl-hrsi" in names
        assert "hummbl-professor" in names

    def test_unknown_repo(self, compass: Compass) -> None:
        assert compass.bridges("hummbl-xyz") == []


class TestGaps:
    def test_gaps_exist(self, compass: Compass) -> None:
        gaps = compass.report_gaps()
        assert len(gaps) > 0
        names = {g["repo_name"] for g in gaps}
        # Built repos should no longer appear as gaps
        assert "hummbl-compass" not in names
        assert "hummbl-premortem" not in names
        assert "hummbl-worstcase" not in names
        assert "hummbl-telemetry" not in names


class TestStats:
    def test_stats_structure(self, compass: Compass) -> None:
        stats = compass.stats()
        assert stats["total_repos"] == 41
        assert "by_layer" in stats
        assert "by_base120_domain" in stats
        assert sum(stats["by_layer"].values()) == 41
