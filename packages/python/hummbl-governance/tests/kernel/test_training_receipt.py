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

"""Tests for training_receipt module."""
from __future__ import annotations

import math
import tempfile


from hummbl_governance.kernel.model_registry import ModelRegistry
from hummbl_governance.kernel.training_receipt import register_training_result


class TestTrainingReceipt:
    def test_register_training_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = ModelRegistry(registry_path=f"{tmp}/models.jsonl")

            result = {
                "n_params": 10_000_000,
                "best_val_loss": 2.5,
                "train_tokens": 5_000_000,
                "elapsed_sec": 3600.0,
                "checkpoint_path": f"{tmp}/params.msgpack",
                "config": {"embed_dim": 256, "num_layers": 4, "vocab_size": 256},
                "vocab_size": 256,
            }

            register_training_result(
                model_id="test-model-01",
                result=result,
                task="char_lm",
                corpus_id="test_corpus",
                hardware="RTX_3080_Ti",
                framework="JAX_Flax",
                tags=["test", "auto"],
                notes="Unit test registration.",
                registry_path=f"{tmp}/models.jsonl",
            )

            entry = reg.get("test-model-01")
            assert entry is not None
            assert entry.model_id == "test-model-01"
            assert entry.task == "char_lm"
            assert entry.params_m == 10.0
            assert entry.checkpoint_path == f"{tmp}/params.msgpack"
            assert "val_loss" in entry.metrics
            assert abs(entry.metrics["val_loss"] - 2.5) < 1e-9
            assert "perplexity" in entry.metrics
            assert abs(entry.metrics["perplexity"] - math.exp(2.5)) < 1e-6
            assert entry.corpus_id == "test_corpus"
            assert entry.hardware == "RTX_3080_Ti"
            assert entry.framework == "JAX_Flax"
            assert "test" in entry.tags
            assert entry.notes == "Unit test registration."

    def test_auto_register(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = ModelRegistry(registry_path=f"{tmp}/models.jsonl")

            result = {
                "n_params": 5_000_000,
                "best_val_loss": 3.0,
                "train_tokens": 1_000_000,
                "elapsed_sec": 600.0,
                "config": {"embed_dim": 128, "num_layers": 3, "vocab_size": 65},
                "vocab_size": 65,
            }

            from hummbl_governance.kernel.training_receipt import auto_register
            auto_register(result, registry_path=f"{tmp}/models.jsonl")

            # Should infer model_id: char_lm_128d_3l_65v
            entry = reg.get("char_lm_128d_3l_65v")
            assert entry is not None
            assert entry.params_m == 5.0
