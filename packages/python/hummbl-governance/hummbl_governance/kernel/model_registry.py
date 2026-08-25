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

"""Model Registry — append-only JSONL tracking for trained models.

A small library for registering, finding, and comparing model artifacts.
No external dependencies beyond stdlib.

Usage:
    from hummbl_governance.kernel.model_registry import ModelRegistry

    reg = ModelRegistry()
    reg.register(
        model_id="example-char-lm-v1",
        task="char_lm",
        params_m=10.0,
        checkpoint_path="checkpoints/example_char_lm_v1.msgpack",
        metrics={"val_ppl": 18.5, "val_loss": 2.92},
        corpus_id="public_example_corpus",
        config={"embed_dim": 256, "num_layers": 4, "num_heads": 8},
        hardware="local_gpu",
        framework="JAX_Flax",
    )

    models = reg.find(task="char_lm")
    best = reg.best(metrics_key="val_ppl", higher_is_better=False)
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .invariants import KernelInvariant, KernelPanic

logger = logging.getLogger(__name__)


@dataclass
class ModelEntry:
    """A single model registration record."""

    model_id: str
    timestamp: str
    task: str  # e.g. "char_lm", "scaling_sweep", "moe_experiment"
    params_m: float  # millions of parameters
    checkpoint_path: str
    metrics: dict[str, Any] = field(default_factory=dict)
    corpus_id: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    hardware: str = ""
    framework: str = ""
    tags: list[str] = field(default_factory=list)
    parent_id: str = ""  # for lineage tracking (fine-tunes, distilled models)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ModelEntry:
        return cls(**d)


class ModelRegistry:
    """Append-only model registry backed by JSONL."""

    def __init__(self, registry_path: str | None = None) -> None:
        using_default_path = registry_path is None
        if registry_path is None:
            # Runtime model registry state must not append into package source.
            registry_path = str(default_registry_path())
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        seed = package_seed_registry_path()
        if using_default_path and not self.registry_path.exists() and seed.exists():
            tmp_fd, tmp_name = tempfile.mkstemp(
                dir=self.registry_path.parent, suffix=".tmp"
            )
            try:
                with os.fdopen(tmp_fd, "wb") as tmp_f:
                    tmp_f.write(seed.read_bytes())
                os.replace(tmp_name, self.registry_path)
            except FileExistsError:
                if Path(tmp_name).exists():
                    os.unlink(tmp_name)
            except OSError:
                if Path(tmp_name).exists():
                    os.unlink(tmp_name)
                raise

    def register(self, **kwargs: Any) -> ModelEntry:
        """Register a new model. Returns the entry."""
        entry = ModelEntry(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **kwargs,
        )
        with open(self.registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return entry

    def list_models(self) -> list[ModelEntry]:
        """Return all registered models.

        Fail-closed: corrupted model registry lines undermine the integrity
        of the model registry. Silently skipping corrupted entries could
        cause the system to use stale or missing model configurations with
        no observable signal. Raise KernelPanic so operators can investigate.
        """
        entries: list[ModelEntry] = []
        if not self.registry_path.exists():
            return entries
        with open(self.registry_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(ModelEntry.from_dict(json.loads(line)))
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.error(
                        "Corrupted model registry line in %s: %s",
                        self.registry_path, line[:100],
                    )
                    raise KernelPanic(
                        KernelInvariant.INTEGRITY,
                        f"Corrupted model registry line in "
                        f"{self.registry_path}: {line[:100]!r} — "
                        f"refusing to silently drop model entry",
                    ) from exc
        return entries

    def find(
        self,
        task: str | None = None,
        tags: list[str] | None = None,
        min_params_m: float | None = None,
        max_params_m: float | None = None,
        hardware: str | None = None,
        framework: str | None = None,
    ) -> list[ModelEntry]:
        """Find models matching criteria."""
        results = []
        for entry in self.list_models():
            if task is not None and entry.task != task:
                continue
            if tags is not None and not all(t in entry.tags for t in tags):
                continue
            if min_params_m is not None and entry.params_m < min_params_m:
                continue
            if max_params_m is not None and entry.params_m > max_params_m:
                continue
            if hardware is not None and entry.hardware != hardware:
                continue
            if framework is not None and entry.framework != framework:
                continue
            results.append(entry)
        return results

    def best(self, metrics_key: str, higher_is_better: bool = False) -> ModelEntry | None:
        """Return the best model by a metric."""
        entries = self.list_models()
        if not entries:
            return None
        compatible: list[tuple[ModelEntry, int | float | str]] = []
        for e in entries:
            if metrics_key not in e.metrics:
                continue
            metric = e.metrics[metrics_key]
            if isinstance(metric, (int, float)):
                compatible.append((e, float(metric)))
            elif isinstance(metric, str):
                compatible.append((e, metric))
        if not compatible:
            return None

        types = {type(value) for _, value in compatible}
        if len(types) > 1:
            raise TypeError(f"Incompatible metric types for '{metrics_key}': {sorted({t.__name__ for t in types})}")

        valid = compatible
        if not valid:
            return None
        best = (
            max(valid, key=lambda e: e[1]) if higher_is_better else min(valid, key=lambda e: e[1])
        )
        return best[0]

    def get(self, model_id: str) -> ModelEntry | None:
        """Get the latest model by ID."""
        matches = [entry for entry in self.list_models() if entry.model_id == model_id]
        if not matches:
            return None
        return max(matches, key=lambda entry: entry.timestamp)

    def lineage(self, model_id: str) -> list[ModelEntry]:
        """Trace lineage from a model back to ancestors."""
        entries = {e.model_id: e for e in self.list_models()}
        chain: list[ModelEntry] = []
        current = entries.get(model_id)
        while current is not None:
            chain.append(current)
            current = entries.get(current.parent_id) if current.parent_id else None
        return list(reversed(chain))

    def stats(self) -> dict[str, Any]:
        """Return registry statistics."""
        entries = self.list_models()
        if not entries:
            return {"count": 0}
        tasks: dict[str, int] = {}
        for e in entries:
            tasks[e.task] = tasks.get(e.task, 0) + 1
        return {
            "count": len(entries),
            "tasks": tasks,
            "total_params_m": sum(e.params_m for e in entries),
            "latest": max(entries, key=lambda e: e.timestamp).model_id,
        }


def package_seed_registry_path() -> Path:
    """Return the package seed registry path."""
    here = Path(__file__).parent.parent
    return here / "data" / "registry" / "models.jsonl"


def default_registry_path() -> Path:
    """Return the user-state default registry path for runtime writes."""
    configured = os.environ.get("HUMMBL_MODEL_REGISTRY_PATH")
    if configured:
        return Path(configured).expanduser()

    state_dir = os.environ.get("HUMMBL_KERNEL_STATE_DIR")
    if state_dir:
        return Path(state_dir).expanduser() / "model_registry" / "models.jsonl"

    state_root = os.environ.get("XDG_STATE_HOME") or os.environ.get("LOCALAPPDATA")
    if state_root:
        return Path(state_root).expanduser() / "hummbl-governance" / "model_registry" / "models.jsonl"

    return Path.home() / ".local" / "state" / "hummbl-governance" / "model_registry" / "models.jsonl"
