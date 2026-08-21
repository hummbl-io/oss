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

"""Training Receipt — auto-register model in ModelRegistry after training completes.

Usage:
    from hummbl_governance.kernel.training_receipt import register_training_result

    result = train_lm(..., checkpoint_dir="checkpoints/my_model")
    register_training_result(
        model_id="my-model-v1",
        result=result,
        task="char_lm",
        corpus_id="my_corpus",
        hardware="RTX_3080_Ti",
        framework="JAX_Flax",
        tags=["base", "v1"],
    )
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Try to find hummbl-governance on PYTHONPATH or adjacent to caller
_HUMMBL_ROOT = Path(__file__).parent.parent.parent
if str(_HUMMBL_ROOT) not in sys.path:
    sys.path.insert(0, str(_HUMMBL_ROOT))

try:
    from hummbl_governance.kernel.model_registry import ModelRegistry
except ImportError:
    # Fallback: try direct import if PYTHONPATH is set
    from model_registry import ModelRegistry


def register_training_result(
    model_id: str,
    result: dict[str, Any],
    task: str,
    corpus_id: str = "",
    hardware: str = "",
    framework: str = "",
    tags: list[str] | None = None,
    parent_id: str = "",
    notes: str = "",
    registry_path: str | None = None,
) -> None:
    """Register a training result in the ModelRegistry.

    Args:
        model_id: Unique model identifier.
        result: Dict returned by train_lm() (must contain n_params, best_val_loss,
                checkpoint_path, config, vocab_size, train_tokens, elapsed_sec).
        task: Model task type (e.g. "char_lm", "scaling_sweep").
        corpus_id: ID of the training corpus.
        hardware: Training hardware (e.g. "RTX_3080_Ti").
        framework: Training framework (e.g. "JAX_Flax").
        tags: Optional list of tags.
        parent_id: Optional parent model ID for lineage tracking.
        notes: Optional free-text notes.
    """
    reg = ModelRegistry(registry_path=registry_path)

    metrics: dict[str, float] = {}
    if "best_val_loss" in result and result["best_val_loss"] is not None:
        metrics["val_loss"] = float(result["best_val_loss"])
        metrics["perplexity"] = float(__import__("math").exp(result["best_val_loss"]))
    if "train_tokens" in result:
        metrics["train_tokens"] = float(result["train_tokens"])
    if "elapsed_sec" in result:
        metrics["elapsed_sec"] = float(result["elapsed_sec"])
    if "vocab_size" in result:
        metrics["vocab_size"] = float(result.get("vocab_size", 0))

    params_m = float(result.get("n_params", 0)) / 1e6
    checkpoint = result.get("checkpoint_path", "")
    config = result.get("config", {})

    entry = reg.register(
        model_id=model_id,
        task=task,
        params_m=params_m,
        checkpoint_path=checkpoint,
        metrics=metrics,
        corpus_id=corpus_id,
        config=config,
        hardware=hardware,
        framework=framework,
        tags=tags or [],
        parent_id=parent_id,
        notes=notes,
    )
    print(f"[TrainingReceipt] Registered {entry.model_id} in ModelRegistry.")


def auto_register(
    result: dict[str, Any],
    model_id: str | None = None,
    registry_path: str | None = None,
) -> None:
    """Auto-register a training result with sensible defaults.

    Infers model_id from config if not provided:
        {task}_{embed_dim}d_{num_layers}l_{vocab_size}v
    """
    cfg = result.get("config", {})
    task = "char_lm"  # default; override if known

    if model_id is None:
        embed = cfg.get("embed_dim", "x")
        layers = cfg.get("num_layers", "x")
        vocab = cfg.get("vocab_size", cfg.get("vocab", "x"))
        model_id = f"{task}_{embed}d_{layers}l_{vocab}v"

    register_training_result(
        model_id=model_id,
        result=result,
        task=task,
        hardware="RTX_3080_Ti",  # default; override if known
        framework="JAX_Flax",
        tags=["auto_registered"],
        registry_path=registry_path,
    )
