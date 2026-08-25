"""Seed the model registry with public scaling-law example artifacts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hummbl_governance.kernel.model_registry import ModelRegistry


def main() -> None:
    reg = ModelRegistry()

    # Check if already seeded
    existing = reg.list_models()
    if existing:
        print(f"Registry already has {len(existing)} entries. Skipping seed.")
        return

    # SL-EXP003 — CPU scaling sweep
    reg.register(
        model_id="SL-EXP003",
        task="scaling_sweep",
        params_m=0.0,  # N/A for sweep
        checkpoint_path="tiny-jax-transformer/results/exp003_scaling_analysis.json",
        metrics={"alpha": 0.367, "beta": 0.128, "r_squared": 0.962},
        corpus_id="tinyshakespeare_65_vocab",
        config={
            "platform": "CPU",
            "framework": "JAX_CPU",
            "sizes": ["33K", "167K", "628K", "1.8M", "3.2M"],
            "token_budgets": [250000, 500000, 1000000, 2000000, 4000000],
        },
        hardware="AMD_Ryzen_5800X",
        framework="JAX_CPU",
        tags=["scaling_law", "chinchilla", "cpu", "dense"],
        notes="Chinchilla TinyShakespeare reconstruction on CPU. 25 configs.",
    )

    # SL-EXP004 — GPU scaling sweep
    reg.register(
        model_id="SL-EXP004",
        task="scaling_sweep",
        params_m=0.0,
        checkpoint_path="tiny-jax-transformer/sweep_gpu_20260618_000936/scaling_analysis.json",
        metrics={"alpha": 0.432, "beta": 0.381, "r_squared": 0.865},
        corpus_id="tinyshakespeare_65_vocab",
        config={
            "platform": "GPU",
            "framework": "JAX_CUDA12",
            "sizes": ["33K", "167K", "628K", "1.8M", "3.2M"],
            "token_budgets": [250000, 500000, 1000000, 2000000, 4000000],
            "batch_size": 64,
            "eval_every": 250,
        },
        hardware="RTX_3080_Ti",
        framework="JAX_CUDA12",
        tags=["scaling_law", "chinchilla", "gpu", "dense"],
        notes="Chinchilla TinyShakespeare reconstruction on GPU via WSL2. 25 configs.",
    )

    stats = reg.stats()
    print(f"Seeded registry with {stats['count']} entries:")
    for entry in reg.list_models():
        print(f"  - {entry.model_id} ({entry.task}, {entry.params_m}M params)")


if __name__ == "__main__":
    main()
