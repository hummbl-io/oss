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

"""CLI for ModelRegistry.

Usage:
    python -m hummbl_governance.kernel.model_registry_cli list
    python -m hummbl_governance.kernel.model_registry_cli find --task char_lm
    python -m hummbl_governance.kernel.model_registry_cli best --metric val_ppl
    python -m hummbl_governance.kernel.model_registry_cli get example-char-lm-v1
    python -m hummbl_governance.kernel.model_registry_cli stats
"""
from __future__ import annotations

import argparse
import json
import sys

from .model_registry import ModelRegistry


def list_command(args: argparse.Namespace) -> None:
    reg = ModelRegistry()
    entries = reg.list_models()
    print(f"Models: {len(entries)}")
    for e in entries:
        metrics = ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in e.metrics.items())
        print(f"  {e.model_id:30} {e.task:15} {e.params_m:6.1f}M  {metrics}")


def find_command(args: argparse.Namespace) -> None:
    reg = ModelRegistry()
    results = reg.find(
        task=args.task,
        tags=args.tags.split(",") if args.tags else None,
        min_params_m=args.min_params,
        max_params_m=args.max_params,
        hardware=args.hardware,
        framework=args.framework,
    )
    print(f"Found: {len(results)}")
    for e in results:
        print(f"  {e.model_id} ({e.task}, {e.params_m}M, {e.hardware})")


def best_command(args: argparse.Namespace) -> None:
    reg = ModelRegistry()
    entry = reg.best(args.metric, higher_is_better=args.higher)
    if entry is None:
        print("No models found.")
        sys.exit(1)
    print(f"Best by {args.metric}:")
    print(f"  ID: {entry.model_id}")
    print(f"  Value: {entry.metrics[args.metric]}")
    print(f"  Task: {entry.task}")
    print(f"  Params: {entry.params_m}M")


def get_command(args: argparse.Namespace) -> None:
    reg = ModelRegistry()
    entry = reg.get(args.model_id)
    if entry is None:
        print(f"Model '{args.model_id}' not found.")
        sys.exit(1)
    print(json.dumps(entry.to_dict(), indent=2))


def stats_command(args: argparse.Namespace) -> None:
    reg = ModelRegistry()
    s = reg.stats()
    print(json.dumps(s, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Model Registry CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all models")

    find_parser = subparsers.add_parser("find", help="Find models by criteria")
    find_parser.add_argument("--task", type=str)
    find_parser.add_argument("--tags", type=str)
    find_parser.add_argument("--min-params", type=float)
    find_parser.add_argument("--max-params", type=float)
    find_parser.add_argument("--hardware", type=str)
    find_parser.add_argument("--framework", type=str)

    best_parser = subparsers.add_parser("best", help="Best model by metric")
    best_parser.add_argument("--metric", type=str, required=True)
    best_parser.add_argument("--higher", action="store_true", default=False)

    get_parser = subparsers.add_parser("get", help="Get model by ID")
    get_parser.add_argument("model_id", type=str)

    subparsers.add_parser("stats", help="Registry statistics")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    {
        "list": list_command,
        "find": find_command,
        "best": best_command,
        "get": get_command,
        "stats": stats_command,
    }[args.command](args)


if __name__ == "__main__":
    main()
