"""Regression tests for authenticated review identity and registry updates."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import time

import pytest

import wags
from wags import WagsWorkspace


@pytest.fixture
def workspace(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("original target", encoding="utf-8")
    ws = WagsWorkspace(tmp_path / "workspace")
    ws.init_review(target, review_id="original")
    return ws, target


def test_keyed_verification_rejects_removed_signature(workspace):
    ws, _ = workspace
    ws.register_reviewer("original", "reviewer", secret_key="test-key")
    entry = ws.submit_entry("original", "reviewer", verdict="block", secret_key="test-key")
    entry.verdict = "approve"
    entry.sign(None)  # An attacker can recompute the public hash, but not the HMAC.
    stream = ws.reviews_dir / "original" / "reviewer.jsonl"
    stream.write_text(json.dumps(entry.to_dict()) + "\n", encoding="utf-8")
    assert not ws.verify_review("original", keys={"reviewer": "test-key"})["valid"]
    assert ws.converge_review("original", keys={"reviewer": "test-key"})["overall_verdict"] == "BLOCK"


def test_signed_stream_cannot_be_replayed_into_another_review(workspace):
    ws, target = workspace
    ws.init_review(target, review_id="other")
    for rid in ("original", "other"):
        ws.register_reviewer(rid, "reviewer", secret_key="test-key")
    ws.submit_entry("original", "reviewer", verdict="approve", secret_key="test-key")
    source = ws.reviews_dir / "original" / "reviewer.jsonl"
    (ws.reviews_dir / "other" / "reviewer.jsonl").write_bytes(source.read_bytes())
    assert not ws.verify_review("other", keys={"reviewer": "test-key"})["valid"]
    assert ws.converge_review("other", keys={"reviewer": "test-key"})["overall_verdict"] == "BLOCK"


def test_reinitialization_does_not_rebind_existing_approval(workspace):
    ws, target = workspace
    ws.register_reviewer("original", "reviewer", secret_key="test-key")
    ws.submit_entry("original", "reviewer", verdict="approve", secret_key="test-key")
    review_dir = ws.reviews_dir / "original"
    before = {p.name: p.read_bytes() for p in review_dir.iterdir()}
    target.write_text("different, unreviewed target", encoding="utf-8")
    with pytest.raises(FileExistsError):
        ws.init_review(target, review_id="original")
    assert {p.name: p.read_bytes() for p in review_dir.iterdir()} == before


def test_concurrent_registration_keeps_every_reviewer(workspace, monkeypatch):
    ws, _ = workspace
    original_write = wags._atomic_write_json

    def slow_write(path, data):
        if Path(path).name == "reviewers.json":
            time.sleep(0.03)  # Expose stale read-modify-write snapshots.
        original_write(path, data)

    monkeypatch.setattr(wags, "_atomic_write_json", slow_write)
    names = [f"reviewer-{i}" for i in range(12)]
    start = threading.Barrier(len(names))

    def register(name):
        start.wait(timeout=5)
        return ws.register_reviewer("original", name)

    with ThreadPoolExecutor(max_workers=len(names)) as pool:
        list(pool.map(register, names))
    registry = json.loads((ws.reviews_dir / "original" / "reviewers.json").read_text())
    assert set(registry) == set(names)
    assert all((ws.reviews_dir / "original" / f"{name}.jsonl").exists() for name in names)


def test_bad_registry_is_not_silently_replaced(workspace):
    ws, _ = workspace
    registry = ws.reviews_dir / "original" / "reviewers.json"
    registry.write_text("broken JSON", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        ws.register_reviewer("original", "reviewer")
    assert registry.read_text() == "broken JSON"
