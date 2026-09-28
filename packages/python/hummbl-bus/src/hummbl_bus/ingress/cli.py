"""bus-ingress runner CLI.

    python -m hummbl_bus.ingress webhook --config channels.json
    python -m hummbl_bus.ingress email   --config channels.json
    python -m hummbl_bus.ingress signal  --config channels.json
    python -m hummbl_bus.ingress fanout  --config channels.json --bus <path>

Config is a local JSON file (uncommitted — holds deployment-specific
address map, env var names, ports). See ``channels.example.json``.
Secrets come from env vars only.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .allowlist import Allowlist
from .normalizer import Normalizer


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalizer(cfg: dict) -> Normalizer:
    b = cfg.get("bridge", {})
    return Normalizer(
        Allowlist(
            cfg.get("allowlist", {}).get("senders", {}),
            unknown_sender=cfg.get("allowlist", {}).get("unknown_sender", "quarantine"),
        ),
        bridge_host=b.get("host", "127.0.0.1"),
        bridge_port=int(b.get("port", 8080)),
        origin_machine=cfg.get("origin_machine"),
        spool_dir=cfg.get("spool_dir"),
    )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="hummbl_bus.ingress")
    ap.add_argument(
        "adapter",
        choices=[
            "webhook",
            "email",
            "signal",
            "fanout",
            "mesh",
            "discord",
            "telegram",
            "ntfy",
            "jmp",
        ],
    )
    ap.add_argument("--config", required=True, help="channels.json path")
    ap.add_argument("--bus", help="local bus mirror path (fanout only)")
    args = ap.parse_args(argv)

    cfg = _load(args.config)
    norm = _normalizer(cfg)

    if args.adapter == "webhook":
        from .webhook import serve

        w = cfg.get("webhook", {})
        serve(
            norm,
            w.get("channel_tokens", {}),
            host=w.get("host", "127.0.0.1"),
            port=int(w.get("port", 18796)),
        )
    elif args.adapter == "email":
        import os

        from .email_imap import IMAPConfig, run_poller

        e = cfg.get("email", {})
        ic = IMAPConfig(
            host=e.get("host", "127.0.0.1"),
            port=int(e.get("port", 1143)),
            user=e.get("user", ""),
            password_env=e.get("password_env", "BUS_INGRESS_IMAP_PASSWORD"),
            mailbox=e.get("mailbox", "INBOX"),
            starttls=bool(e.get("starttls", False)),
            poll_seconds=int(e.get("poll_seconds", 30)),
        )
        pw = os.environ.get(ic.password_env, "")
        if not pw:
            print(f"missing env {ic.password_env}", file=sys.stderr)
            return 2
        run_poller(ic, norm, password=pw)
    elif args.adapter == "signal":
        from .signal_cli import run_daemon

        s = cfg.get("signal", {})
        run_daemon(
            s.get("account", ""),
            norm,
            config_dir=s.get("config_dir"),
            poll_seconds=int(s.get("poll_seconds", 10)),
        )
    elif args.adapter == "fanout":
        from .fanout import run as run_fanout

        bus = args.bus or cfg.get("fanout", {}).get("bus_path")
        if not bus:
            print("fanout needs --bus or config fanout.bus_path", file=sys.stderr)
            return 2
        routes = _load_routes(cfg)
        run_fanout(bus, routes, from_end=cfg.get("fanout", {}).get("from_end", True))
    elif args.adapter == "mesh":
        import shlex

        from .meshtastic import run_serial_relay

        m = cfg.get("mesh", {})
        cmd = shlex.split(m.get("relay_cmd", ""))
        if not cmd:
            print("mesh needs config mesh.relay_cmd", file=sys.stderr)
            return 2
        run_serial_relay(cmd, norm)
    elif args.adapter == "discord":
        import os

        from .discord_poller import run_poller as run_discord

        d = cfg.get("discord", {})
        token_env = d.get("token_env", "DISCORD_BOT_TOKEN")
        token = os.environ.get(token_env, "")
        if not token:
            print(f"missing env {token_env}", file=sys.stderr)
            return 2
        run_discord(
            token,
            d.get("channels", []),
            norm,
            bot_id=d.get("bot_id", ""),
            poll_seconds=int(d.get("poll_seconds", 15)),
            watermark_path=d.get("watermark_path"),
        )
    elif args.adapter == "telegram":
        import os

        from .telegram_poller import run_poller as run_telegram

        t = cfg.get("telegram", {})
        token_env = t.get("token_env", "TELEGRAM_BOT_TOKEN")
        token = os.environ.get(token_env, "")
        if not token:
            print(f"missing env {token_env}", file=sys.stderr)
            return 2
        run_telegram(token, norm, poll_seconds=int(t.get("poll_seconds", 2)))
    elif args.adapter == "ntfy":
        from .ntfy_sub import run_subscriber

        n = cfg.get("ntfy", {})
        run_subscriber(
            n.get("base_url", "https://ntfy.sh"),
            n["topic"],
            norm,
            token_env=n.get("token_env"),
            reconnect_seconds=int(n.get("reconnect_seconds", 10)),
        )
    elif args.adapter == "jmp":
        import os

        from .xmpp_jmp import run_client

        j = cfg.get("jmp", {})
        pw_env = j.get("password_env", "BUS_JMP_PASSWORD")
        pw = os.environ.get(pw_env, "")
        if not pw:
            print(f"missing env {pw_env}", file=sys.stderr)
            return 2
        run_client(
            j["jid"],
            pw,
            norm,
            gateway=j.get("gateway", "cheogram.com"),
            channel=j.get("channel", "jmp"),
            reconnect_seconds=int(j.get("reconnect_seconds", 15)),
        )
    return 0


def _load_routes(cfg: dict):
    """Route spec -> Route objects with subprocess backends."""
    import os

    from .fanout import Route, subprocess_backend

    routes = []
    for r in cfg.get("fanout", {}).get("routes", []):
        target = os.environ.get(r.get("target_env", ""), r.get("target", ""))
        routes.append(
            Route(
                recipients=frozenset(r.get("recipients", ["operator"])),
                channel=r.get("channel", "webhook"),
                backend=subprocess_backend(r["cmd"]),
                urgency=(frozenset(r["urgency"]) if r.get("urgency") else None),
                target_addr=target,
            )
        )
    return routes


if __name__ == "__main__":
    sys.exit(main())
