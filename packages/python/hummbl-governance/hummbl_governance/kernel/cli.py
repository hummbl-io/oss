#!/usr/bin/env python3
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

"""Kernel CLI — boot, status, inspect, health, model-registry.

Usage:
    python -m hummbl_governance.kernel boot
    python -m hummbl_governance.kernel status
    python -m hummbl_governance.kernel health
    python -m hummbl_governance.kernel inspect <agent_id>
    python -m hummbl_governance.kernel laws
    python -m hummbl_governance.kernel roles
    python -m hummbl_governance.kernel model-registry list
    python -m hummbl_governance.kernel model-registry find --task char_lm
    python -m hummbl_governance.kernel model-registry best --metric val_ppl
    python -m hummbl_governance.kernel model-registry get <model_id>
    python -m hummbl_governance.kernel model-registry stats

__dissect__
-----------
- surface: CLI (kernel administration)
- dependencies: kernel (all engines)
- receipts: KERNEL_CLI_COMMAND
- telemetry: command history
- imports-stdlib: argparse, json, sys
- imports-internal: kernel (all engines)
- imports-third-party: none
- mutable-state: none
- feature-flags: none
- side-effects: reads/writes kernel state directory
- thread-safe: yes (read-only operations)
- async: no
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .kernel import DEFAULT_STATE_DIR, Kernel
from .model_registry import ModelRegistry


def cmd_boot(args: argparse.Namespace) -> int:
    """Boot the Kernel."""
    try:
        kernel = Kernel.boot(state_dir=Path(args.state_dir))
        health = kernel.health()
        print(json.dumps(health, indent=2, default=str))
        print(f"\nKernel booted successfully. Boot receipt: {kernel.boot_receipt_id}")
        return 0
    except Exception as e:
        print(f"Kernel boot failed: {e}", file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show Kernel status."""
    try:
        kernel = Kernel(state_dir=Path(args.state_dir))
        health = kernel.health()
        print(json.dumps(health, indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Kernel status check failed: {e}", file=sys.stderr)
        return 1


def cmd_health(args: argparse.Namespace) -> int:
    """Show detailed health for all engines."""
    try:
        kernel = Kernel(state_dir=Path(args.state_dir))
        health = kernel.health()
        identities = kernel.identity.list_identities()

        # Add engine-specific details
        health["receipts_total"] = sum(
            1 for f in kernel.receipt.receipts_dir.glob("*.jsonl")
            for _ in f.read_text().strip().split("\n") if _
        ) if kernel.receipt.receipts_dir.exists() else 0

        health["laws"] = [law.law_id for law in kernel.law.list_laws()]
        health["identities"] = list(identities.keys())
        health["schedules"] = [
            {"role_id": s.role_id, "cadence": s.cadence, "last_run": s.last_run}
            for s in kernel.schedule.list_schedules()
        ]

        print(json.dumps(health, indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Kernel health check failed: {e}", file=sys.stderr)
        return 1


def cmd_inspect(args: argparse.Namespace) -> int:
    """Inspect an agent identity."""
    try:
        kernel = Kernel(state_dir=Path(args.state_dir))
        identity = kernel.identity.resolve(args.agent_id)
        if not identity:
            print(f"Agent '{args.agent_id}' not found", file=sys.stderr)
            return 1

        print(json.dumps(identity.__dict__, indent=2, default=str))

        # Show recent receipts
        receipts = kernel.receipt.list_for_agent(args.agent_id)
        print(f"\nRecent receipts ({len(receipts)} total):")
        for r in receipts[-5:]:
            print(f"  {r.receipt_id}: {r.action_type} ({r.timestamp})")

        # Show role claims
        roles = kernel.identity.list_roles(args.agent_id)
        if roles:
            print("\nRole claims:")
            for role in roles:
                print(f"  {role['role_id']}: {role['state']} (score: {role.get('metric_score', 0):.2f})")

        return 0
    except Exception as e:
        print(f"Inspection failed: {e}", file=sys.stderr)
        return 1


def cmd_laws(args: argparse.Namespace) -> int:
    """List all loaded scaling laws."""
    try:
        kernel = Kernel(state_dir=Path(args.state_dir))
        laws = kernel.law.list_laws()
        print(f"Loaded {len(laws)} scaling law(s):")
        for law in laws:
            status_icon = "✓" if law.status == "empirically.tested" else "○"
            print(f"  {status_icon} {law.law_id}: {law.name} [{law.status}]")
        return 0
    except Exception as e:
        print(f"Law listing failed: {e}", file=sys.stderr)
        return 1


def cmd_roles(args: argparse.Namespace) -> int:
    """List all registered roles and their claimants."""
    try:
        kernel = Kernel(state_dir=Path(args.state_dir))
        role_claims = kernel.identity.list_role_claims()
        identities = kernel.identity.list_identities()
        print("Active roles:")
        for agent_id, identity in identities.items():
            if identity.active_roles:
                print(f"  {agent_id}: {', '.join(identity.active_roles)}")

        print("\nAll role claims:")
        seen_roles: dict[str, list[str]] = {}
        for key, claim in role_claims.items():
            role_id = claim["role_id"]
            if role_id not in seen_roles:
                seen_roles[role_id] = []
            seen_roles[role_id].append(f"{claim['agent_id']} ({claim['state']})")

        for role_id, claimants in seen_roles.items():
            print(f"  {role_id}: {', '.join(claimants)}")

        return 0
    except Exception as e:
        print(f"Role listing failed: {e}", file=sys.stderr)
        return 1


def cmd_model_registry(args: argparse.Namespace) -> int:
    """Model registry subcommands."""
    sub = args.mr_subcommand
    reg = ModelRegistry()
    if sub == "list":
        entries = reg.list_models()
        print(f"Models: {len(entries)}")
        for e in entries:
            metrics = ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in e.metrics.items())
            print(f"  {e.model_id:30} {e.task:15} {e.params_m:6.1f}M  {metrics}")
        return 0
    elif sub == "find":
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
        return 0
    elif sub == "best":
        entry = reg.best(args.metric, higher_is_better=args.higher)
        if entry is None:
            print("No models found.")
            return 1
        print(f"Best by {args.metric}:")
        print(f"  ID: {entry.model_id}")
        print(f"  Value: {entry.metrics[args.metric]}")
        print(f"  Task: {entry.task}")
        print(f"  Params: {entry.params_m}M")
        return 0
    elif sub == "get":
        entry = reg.get(args.model_id)
        if entry is None:
            print(f"Model '{args.model_id}' not found.")
            return 1
        print(json.dumps(entry.to_dict(), indent=2))
        return 0
    elif sub == "stats":
        s = reg.stats()
        print(json.dumps(s, indent=2))
        return 0
    else:
        print(f"Unknown model-registry subcommand: {sub}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="HUMMBL Governance Kernel CLI")
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR), help="Kernel state directory")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("boot", help="Boot the Kernel")
    subparsers.add_parser("status", help="Show Kernel status")
    subparsers.add_parser("health", help="Show detailed health")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect an agent")
    inspect_parser.add_argument("agent_id", help="Agent identity to inspect")

    subparsers.add_parser("laws", help="List scaling laws")
    subparsers.add_parser("roles", help="List registered roles")

    # model-registry subcommand group
    mr_parser = subparsers.add_parser("model-registry", help="Model registry operations")
    mr_sub = mr_parser.add_subparsers(dest="mr_subcommand", help="Model registry subcommands")
    mr_sub.add_parser("list", help="List all models")

    mr_find = mr_sub.add_parser("find", help="Find models by criteria")
    mr_find.add_argument("--task", type=str)
    mr_find.add_argument("--tags", type=str)
    mr_find.add_argument("--min-params", type=float)
    mr_find.add_argument("--max-params", type=float)
    mr_find.add_argument("--hardware", type=str)
    mr_find.add_argument("--framework", type=str)

    mr_best = mr_sub.add_parser("best", help="Best model by metric")
    mr_best.add_argument("--metric", type=str, required=True)
    mr_best.add_argument("--higher", action="store_true", default=False)

    mr_get = mr_sub.add_parser("get", help="Get model by ID")
    mr_get.add_argument("model_id", type=str)

    mr_sub.add_parser("stats", help="Registry statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "boot": cmd_boot,
        "status": cmd_status,
        "health": cmd_health,
        "inspect": cmd_inspect,
        "laws": cmd_laws,
        "roles": cmd_roles,
        "model-registry": cmd_model_registry,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
