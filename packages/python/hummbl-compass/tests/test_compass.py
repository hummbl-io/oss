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
        assert compass.version == "2.0.0"

    def test_repo_count(self, compass: Compass) -> None:
        # 14 public packages in the oss monorepo
        assert len(compass.repos) == 14

    def test_all_repos_have_required_fields(self, compass: Compass) -> None:
        valid_prefixes = ("hummbl", "base120", "governed-")
        for repo in compass.repos:
            assert any(repo.name.startswith(p) for p in valid_prefixes), f"unexpected name: {repo.name}"
            assert repo.primary_base120
            assert repo.layer
            assert repo.description
            assert repo.status in ("active", "experimental", "stale", "deprecated", "archived")

    def test_no_git_host_leaked(self, compass: Compass) -> None:
        """Public topology must not expose git_host (private infra detail)."""
        for repo in compass.repos:
            assert repo.git_host == "github"


class TestByLayer:
    def test_l1_safety_layer(self, compass: Compass) -> None:
        repos = compass.by_layer("L1")
        names = {r.name for r in repos}
        assert "hummbl-governance" in names
        assert "hummbl-tuples" in names

    def test_l2_technical_layer(self, compass: Compass) -> None:
        repos = compass.by_layer("L2")
        names = {r.name for r in repos}
        assert "hummbl-kernel" in names
        assert "hummbl" in names


class TestByBase120:
    def test_co14_coordination(self, compass: Compass) -> None:
        repos = compass.by_base120("CO14")
        names = {r.name for r in repos}
        assert "hummbl-kernel" in names
        assert "hummbl-bus" in names

    def test_go1_governance(self, compass: Compass) -> None:
        repos = compass.by_base120("GO1")
        names = {r.name for r in repos}
        assert "hummbl-governance" in names


class TestRoute:
    def test_route_kernel(self, compass: Compass) -> None:
        results = compass.route("benchmark a kernel on Metal", top_k=3)
        assert len(results) > 0
        names = [r.repo.name for r in results]
        assert "hummbl-kernel" in names

    def test_route_governance(self, compass: Compass) -> None:
        results = compass.route("design a governance control catalog", top_k=3)
        assert len(results) > 0
        names = [r.repo.name for r in results]
        assert "hummbl-governance" in names

    def test_route_bus(self, compass: Compass) -> None:
        results = compass.route("send a message on the coordination bus", top_k=3)
        assert len(results) > 0
        names = [r.repo.name for r in results]
        assert "hummbl-bus" in names

    def test_confidence_range(self, compass: Compass) -> None:
        results = compass.route("something about ML", top_k=3)
        for r in results:
            assert 0.0 <= r.confidence <= 1.0


class TestBridges:
    def test_governance_bridges(self, compass: Compass) -> None:
        repos = compass.bridges("hummbl-governance")
        names = {r.name for r in repos}
        assert "hummbl-kernel" in names
        assert "hummbl-bus" in names

    def test_unknown_repo(self, compass: Compass) -> None:
        assert compass.bridges("hummbl-xyz") == []


class TestStats:
    def test_stats_structure(self, compass: Compass) -> None:
        stats = compass.stats()
        assert stats["total_repos"] == 14
        assert "by_layer" in stats
        assert "by_base120_domain" in stats
        assert sum(stats["by_layer"].values()) == 14
