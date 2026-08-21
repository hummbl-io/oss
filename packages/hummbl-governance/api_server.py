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

"""hummbl-governance REST API server.

Lightweight HTTP API wrapping governance primitives. Uses only stdlib
(http.server). Deploy behind a reverse proxy for production.

Endpoints:
    GET  /api/v1/status              - Governance overview
    GET  /api/v1/kill-switch         - Kill switch state
    POST /api/v1/kill-switch/engage  - Engage kill switch
    POST /api/v1/kill-switch/disengage - Disengage
    GET  /api/v1/circuit-breaker     - Circuit breaker state
    GET  /api/v1/cost/check          - Budget status
    POST /api/v1/cost/record         - Record usage
    GET  /api/v1/audit               - Query audit log
    GET  /api/v1/health              - Health check
    GET  /api/v1/score               - Governance score

Usage:
    python3 api_server.py [--port 8090] [--host 127.0.0.1]
"""

import argparse
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hummbl_governance import (
    KillSwitch,
    KillSwitchMode,
    CircuitBreaker,
    CostGovernor,
    AuditLog,
    ReasoningEngine,
)

STATE_DIR = Path(os.environ.get("GOVERNANCE_STATE_DIR", ".governance"))
DB_PATH = STATE_DIR / "costs.db"


def _load_api_token() -> str | None:
    """Return the expected Bearer token from env, or None if auth not configured."""
    env_token = os.environ.get("GOVERNANCE_API_TOKEN", "").strip()
    if env_token:
        return env_token
    token_file = os.environ.get("GOVERNANCE_API_TOKEN_FILE", "").strip()
    if not token_file:
        return None
    try:
        token = Path(token_file).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    return token or None


def _require_api_auth() -> bool:
    """Return True if API auth is required (fail-closed when token not configured).

    Default: True (fail-closed). A server started without GOVERNANCE_API_TOKEN
    will reject all requests with 401. Set GOVERNANCE_API_ALLOW_NO_AUTH=1 to
    bypass (tests/dev only).
    """
    allow = os.environ.get("GOVERNANCE_API_ALLOW_NO_AUTH", "").strip().lower()
    return allow not in ("1", "true", "yes", "on")


def _cors_origin() -> str | None:
    """Return the CORS origin to emit, or None to suppress CORS.

    Default: None (no CORS header — same-origin only). Set
    GOVERNANCE_API_CORS_ORIGIN to a specific origin or '*' for cross-origin
    access. Wildcard is opt-in because it disables the browser same-origin
    protection that gates access to the kill switch endpoint.
    """
    return os.environ.get("GOVERNANCE_API_CORS_ORIGIN", "").strip() or None

# Singletons
_ks = None
_cb = None
_cg = None
_al = None
_re = None


def init_services():
    global _ks, _cb, _cg, _al, _re
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "audit").mkdir(exist_ok=True)
    _ks = KillSwitch(state_dir=STATE_DIR)
    _cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    _cg = CostGovernor(db_path=str(DB_PATH))
    _al = AuditLog(base_dir=str(STATE_DIR / "audit"))
    _re = ReasoningEngine()


def _compute_governance_score():
    """Compute governance posture score (0-100)."""
    score = 0
    if not _ks.engaged:
        score += 25
    if _cb.state.name == "CLOSED":
        score += 25
    budget = _cg.check_budget_status()
    decision = getattr(budget, "decision", None)
    if hasattr(decision, "name") and decision.name == "ALLOW":
        score += 25
    if (STATE_DIR / "policy.json").exists():
        score += 25
    return score


def _score_to_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 95:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "F"


class GovernanceHandler(BaseHTTPRequestHandler):
    _PUBLIC_GET_ROUTES = {"/api/v1/health"}

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        origin = _cors_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def _check_auth(self) -> bool:
        """Return True if the request passes auth, False after sending 401.

        Uses hmac.compare_digest for constant-time comparison.
        """
        token = _load_api_token()
        if token is None:
            if _require_api_auth():
                self._json_response(
                    {"error": "Unauthorized: GOVERNANCE_API_TOKEN not configured"},
                    401,
                )
                return False
            return True
        auth_header = self.headers.get("Authorization", "")
        expected = f"Bearer {token}"
        if not hmac.compare_digest(
            auth_header.encode("utf-8"),
            expected.encode("utf-8"),
        ):
            self._json_response({"error": "Unauthorized"}, 401)
            return False
        return True

    def do_OPTIONS(self):
        self.send_response(204)
        origin = _cors_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _get_status(self, params):
        budget = _cg.check_budget_status()
        self._json_response({
            "kill_switch": {"mode": _ks.mode.name, "engaged": _ks.engaged},
            "circuit_breaker": {"state": _cb.state.name, "failure_count": _cb.failure_count},
            "cost_governor": {
                "daily_spend": getattr(budget, "current_spend", 0),
                "decision": (
                    getattr(budget, "decision", "UNKNOWN").name
                    if hasattr(getattr(budget, "decision", None), "name")
                    else str(getattr(budget, "decision", "UNKNOWN"))
                ),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _get_kill_switch(self, params):
        status = _ks.get_status()
        self._json_response(status)

    def _get_circuit_breaker(self, params):
        self._json_response({
            "state": _cb.state.name,
            "failure_count": _cb.failure_count,
            "success_count": getattr(_cb, "success_count", 0),
        })

    def _get_cost_check(self, params):
        budget = _cg.check_budget_status()
        result = {}
        for attr in ("current_spend", "soft_cap", "hard_cap", "decision", "rationale", "utilization"):
            val = getattr(budget, attr, None)
            if val is not None:
                result[attr] = val.name if hasattr(val, "name") else val
        self._json_response(result)

    def _get_audit(self, params):
        intent_id = params.get("intent_id", [None])[0]
        task_id = params.get("task_id", [None])[0]
        entries = []
        if intent_id:
            entries = list(_al.query_by_intent(intent_id))
        elif task_id:
            entries = list(_al.query_by_task(task_id))
        self._json_response({
            "count": len(entries),
            "entries": [
                {k: str(v) for k, v in (e.__dict__ if hasattr(e, "__dict__") else {"data": str(e)}).items()}
                for e in entries[:50]
            ],
        })

    def _get_health(self, params):
        self._json_response({
            "healthy": not _ks.engaged and _cb.state.name == "CLOSED",
            "kill_switch": _ks.mode.name,
            "circuit_breaker": _cb.state.name,
        })

    def _get_score(self, params):
        score = _compute_governance_score()
        grade = _score_to_grade(score)
        self._json_response({"score": score, "grade": grade})

    # Route table for GET endpoints
    _GET_ROUTES = {
        "/api/v1/status": _get_status,
        "/api/v1/kill-switch": _get_kill_switch,
        "/api/v1/circuit-breaker": _get_circuit_breaker,
        "/api/v1/cost/check": _get_cost_check,
        "/api/v1/audit": _get_audit,
        "/api/v1/health": _get_health,
        "/api/v1/score": _get_score,
    }

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)
        if path not in self._PUBLIC_GET_ROUTES and not self._check_auth():
            return

        handler = self._GET_ROUTES.get(path)
        if handler:
            handler(self, params)
        else:
            self._json_response({"error": f"Not found: {path}"}, 404)

    def do_POST(self):
        if not self._check_auth():
            return
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/v1/kill-switch/engage":
            body = self._read_body()
            mode_name = body.get("mode", "HALT_NONCRITICAL")
            mode_map = {
                "HALT_NONCRITICAL": KillSwitchMode.HALT_NONCRITICAL,
                "HALT_ALL": KillSwitchMode.HALT_ALL,
                "EMERGENCY": KillSwitchMode.EMERGENCY,
            }
            mode = mode_map.get(mode_name)
            if not mode:
                self._json_response({"error": f"Invalid mode: {mode_name}"}, 400)
                return
            if not body.get("confirm"):
                self._json_response({"error": "Must set confirm=true"}, 400)
                return
            _ks.engage(mode=mode, reason=body.get("reason", "API"), triggered_by=body.get("triggered_by", "api-client"))
            self._json_response({"engaged": True, "mode": mode_name})

        elif path == "/api/v1/kill-switch/disengage":
            body = self._read_body()
            if not body.get("confirm"):
                self._json_response(
                    {"error": "Must set confirm=true to disengage the kill switch"},
                    400,
                )
                return
            _ks.disengage(reason=body.get("reason", "API"), triggered_by=body.get("triggered_by", "api-client"))
            self._json_response({"disengaged": True})

        elif path == "/api/v1/cost/record":
            body = self._read_body()
            required = ["provider", "model", "tokens_in", "tokens_out", "cost"]
            missing = [f for f in required if f not in body]
            if missing:
                self._json_response({"error": f"Missing fields: {missing}"}, 400)
                return
            _cg.record_usage(**{k: body[k] for k in required})
            self._json_response({"recorded": True})

        elif path == "/api/v1/apply":
            body = self._read_body()
            model_code = body.get("model")
            if not model_code:
                self._json_response({"error": "Missing model code"}, 400)
                return
            
            model = _re.get_model(model_code)
            if not model:
                self._json_response({"error": f"Unknown model code: {model_code}"}, 404)
                return

            # Check Kill Switch
            if _ks.engaged:
                self._json_response({"error": "Governance Kill Switch ACTIVE", "mode": _ks.mode.name}, 503)
                return

            # Generate Prompt
            prompt = _re.generate_system_prompt(model_code, depth=body.get("depth", 1))
            
            # For now, return the prompt and model metadata.
            # In a real deployment, this would call the LLM adapter.
            self._json_response({
                "ok": True,
                "data": {
                    "model": model.code,
                    "name": model.name,
                    "transformation": model.transformation,
                    "definition": model.definition,
                    "system_prompt": prompt,
                    "status": "prompt_generated_awaiting_adapter"
                }
            })

        else:
            self._json_response({"error": f"Not found: {path}"}, 404)

    def log_message(self, format, *args):
        # Suppress default logging (format and args required by BaseHTTPRequestHandler API)
        _ = format  # Used by parent class signature
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    init_services()
    server = HTTPServer((args.host, args.port), GovernanceHandler)
    print(f"hummbl-governance API | http://{args.host}:{args.port}/api/v1/status")
    print(f"State: {STATE_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown.")


if __name__ == "__main__":
    main()
