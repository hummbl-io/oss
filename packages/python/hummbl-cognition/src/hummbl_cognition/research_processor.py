"""Research Queue Processor -- uses local LLM to process research questions.

Reads a research queue (JSON array of questions), uses qwen3.5:9b on nodezero
to generate findings for each, and ingests results into the Open Brain ledger.

Designed to run on nodezero as a launchd cron (every 2 hours) where Ollama and
the Open Brain server are both local.

Idempotent: tracks processed question hashes in a state file so re-runs skip
already-answered questions. Questions can be refreshed by updating the queue.

Usage:
    python -m hummbl_cognition.research_processor run
    python -m hummbl_cognition.research_processor run --dry-run
    python -m hummbl_cognition.research_processor status
    python -m hummbl_cognition.research_processor list

Dependencies: stdlib only. Ollama accessed via urllib.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_STATE_FILE = "_state/cognition/research_processor_state.json"
DEFAULT_QUEUE_FILE = "_state/cognition/research_queue.json"
DEFAULT_OPEN_BRAIN_URL = "http://127.0.0.1:11435"

# Built-in fallback research queue -- used when the external JSON file is missing.
# The canonical queue lives at _state/cognition/research_queue.json.
# Each question has: id, domain, query, tier (1=highest priority), recurrence.
DEFAULT_QUEUE: list[dict[str, Any]] = [
    {
        "id": "RQ-001",
        "domain": "prompt-engineering",
        "query": (
            "What are the current best practices for structuring system prompts "
            "for multi-agent AI systems? Focus on: role separation, context "
            "injection, tool-use instructions, and avoiding prompt injection. "
            "Provide specific, actionable patterns."
        ),
        "tier": 1,
        "recurrence": "weekly",
    },
    {
        "id": "RQ-002",
        "domain": "agent-coordination",
        "query": (
            "What coordination protocols exist for multi-agent AI systems? "
            "Compare: shared message bus (like our TSV bus), blackboard systems, "
            "contract nets, and stigmergic coordination. What are the failure "
            "modes of each? Which patterns work best for 3-5 agents?"
        ),
        "tier": 1,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-003",
        "domain": "cost-governance",
        "query": (
            "What strategies exist for controlling AI API costs in production? "
            "Cover: token budgeting, model routing (expensive vs cheap models), "
            "caching strategies, circuit breakers for cost, and cost attribution "
            "across multiple agents. Include specific implementation patterns."
        ),
        "tier": 2,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-004",
        "domain": "memory-systems",
        "query": (
            "How do production AI systems implement persistent memory? Compare: "
            "vector databases, BM25 keyword search, knowledge graphs, and hybrid "
            "approaches. What are the trade-offs for a system with 10K-100K "
            "memory entries? Focus on retrieval quality and latency."
        ),
        "tier": 1,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-005",
        "domain": "security",
        "query": (
            "What are the top security risks for AI agent systems that interact "
            "with external APIs and execute code? Cover: prompt injection, tool "
            "misuse, credential exposure, data exfiltration, and privilege "
            "escalation. What mitigations are most effective?"
        ),
        "tier": 2,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-006",
        "domain": "briefing-systems",
        "query": (
            "What makes an effective executive briefing or daily digest? Cover: "
            "information hierarchy, signal-to-noise ratio, actionability of items, "
            "personalization, and delivery timing. What do the best daily briefing "
            "products (Morning Brew, The Skimm, custom enterprise tools) do well?"
        ),
        "tier": 2,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-007",
        "domain": "local-inference",
        "query": (
            "What are the best practices for running local LLM inference in "
            "production? Cover: model selection for different tasks (summarization "
            "vs coding vs analysis), quantization trade-offs, batching strategies, "
            "and monitoring inference quality over time. Focus on 8B-14B parameter "
            "models on Apple Silicon."
        ),
        "tier": 2,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-008",
        "domain": "governance",
        "query": (
            "What governance frameworks exist for AI agent systems? Compare: "
            "NIST AI RMF, EU AI Act requirements, ISO 42001, and custom "
            "frameworks. What minimum governance is needed for a multi-agent "
            "system used by a small team? Focus on practical implementation."
        ),
        "tier": 3,
        "recurrence": "once",
    },
    {
        "id": "RQ-009",
        "domain": "testing",
        "query": (
            "How do teams test AI agent systems effectively? Cover: unit testing "
            "agent logic, integration testing with mocked LLMs, evaluating output "
            "quality, regression testing for prompt changes, and chaos testing for "
            "multi-agent coordination. What test patterns have the highest ROI?"
        ),
        "tier": 2,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-010",
        "domain": "competitive-intelligence",
        "query": (
            "What are the major platforms and tools for AI agent orchestration "
            "as of early 2026? Compare: LangGraph, CrewAI, AutoGen, Semantic "
            "Kernel, and custom solutions. What features differentiate them? "
            "What gaps exist that a governance-first platform could fill?"
        ),
        "tier": 1,
        "recurrence": "weekly",
    },
]

# Backward compatibility alias
RESEARCH_QUEUE = DEFAULT_QUEUE

# Max questions to process per run (avoid hogging Ollama)
MAX_PER_RUN = 3
# Max response length from LLM (tokens)
MAX_PREDICT = 1024


def _resolve_path(rel_path: str) -> Path:
    """Resolve a path relative to git root or cwd."""
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        ).strip()
        if root:
            return Path(root) / rel_path
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return Path(rel_path)


def load_research_queue(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load the research queue from an external JSON file.

    Falls back to DEFAULT_QUEUE if the file does not exist or is corrupt.

    Args:
        path: Path to the JSON file.  When None, resolves
              ``_state/cognition/research_queue.json`` relative to the git
              root (or cwd).

    Returns:
        A list of research-queue item dicts.
    """
    queue_path = _resolve_path(DEFAULT_QUEUE_FILE) if path is None else Path(path)

    if not queue_path.exists():
        logger.debug("Queue file %s not found, using DEFAULT_QUEUE", queue_path)
        return list(DEFAULT_QUEUE)

    try:
        data = json.loads(queue_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            logger.warning("Queue file %s is not a JSON array, using DEFAULT_QUEUE", queue_path)
            return list(DEFAULT_QUEUE)
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load queue file %s: %s, using DEFAULT_QUEUE", queue_path, exc)
        return list(DEFAULT_QUEUE)


def save_research_queue(
    queue: list[dict[str, Any]],
    path: str | Path | None = None,
) -> Path:
    """Write the research queue to a JSON file (crash-safe via temp+rename).

    Args:
        queue: The list of research-queue item dicts to persist.
        path:  Destination file path.  When None, resolves
               ``_state/cognition/research_queue.json`` relative to the git
               root (or cwd).

    Returns:
        The resolved Path that was written to.
    """
    queue_path = _resolve_path(DEFAULT_QUEUE_FILE) if path is None else Path(path)

    queue_path.parent.mkdir(parents=True, exist_ok=True)

    # Crash-safe write: write to a temp file in the same directory, then rename.
    fd, tmp_path = tempfile.mkstemp(
        dir=str(queue_path.parent),
        prefix=".research_queue_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, str(queue_path))
    except BaseException:
        # Clean up temp file on any failure
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise

    return queue_path


def _question_hash(question: dict[str, Any]) -> str:
    """Hash a question for change detection. Includes query text + recurrence."""
    h = hashlib.sha256()
    h.update(question["query"].encode("utf-8"))
    h.update(question.get("recurrence", "once").encode("utf-8"))
    return h.hexdigest()[:16]


def _load_state(state_file: Path) -> dict[str, Any]:
    """Load processor state."""
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"processed": {}, "last_run": None, "total_processed": 0}


def _save_state(state_file: Path, state: dict[str, Any]) -> None:
    """Save processor state."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state["last_run"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state_file.write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _is_kill_switch_engaged() -> bool:
    """Check if the kill switch is engaged."""
    try:
        from hummbl_governance.kill_switch_core import get_kill_switch_core
    except ImportError:
        return False
    try:
        return bool(get_kill_switch_core().engaged)
    except Exception as exc:
        logger.warning("Kill switch check failed; blocking research as fail-closed: %s", exc)
        return True


def _should_reprocess(
    question: dict[str, Any],
    processed: dict[str, Any],
) -> bool:
    """Determine if a question should be (re)processed.

    Returns True if:
    - Never processed before
    - Recurrence period has elapsed (weekly/monthly)
    - Question text changed (hash mismatch)
    """
    qid = question["id"]
    entry = processed.get(qid)
    if not entry:
        return True

    # Check if query changed
    current_hash = _question_hash(question)
    if entry.get("hash") != current_hash:
        return True

    # Check recurrence
    recurrence = question.get("recurrence", "once")
    if recurrence == "once":
        return False

    last_processed = entry.get("last_processed")
    if not last_processed:
        return True

    try:
        last_dt = datetime.strptime(last_processed, "%Y-%m-%dT%H:%M:%SZ")
        last_dt = last_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_elapsed = (now - last_dt).days

        if recurrence == "weekly" and days_elapsed >= 7:
            return True
        if recurrence == "monthly" and days_elapsed >= 30:
            return True
    except (ValueError, TypeError):
        return True

    return False


def _ollama_research(
    question: dict[str, Any],
    *,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
    timeout_s: int = 180,
) -> str | None:
    """Use the local LLM to research a question. Returns findings text."""
    prompt = f"""You are a research analyst for a multi-agent AI orchestration platform.
Answer the following research question with specific, actionable findings.
Structure your response as numbered findings (1-5 key points).
Each finding should be concrete and implementable, not abstract.
Domain: {question['domain']}

Research Question:
{question['query']}

Findings:"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.3,
            "num_predict": MAX_PREDICT,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url=f"{base_url}/api/generate",
        method="POST",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("response", "")
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        logger.warning("Ollama research call failed for %s: %s", question["id"], e)
        return None


def _ingest_finding(
    question: dict[str, Any],
    findings: str,
    *,
    brain_url: str = DEFAULT_OPEN_BRAIN_URL,
) -> dict[str, Any]:
    """Ingest a research finding into the Open Brain server."""
    from http.client import HTTPConnection
    from urllib.parse import urlparse

    from hummbl_cognition.models import LedgerEntry

    content = f"{question['id']}: {question['domain']}\n\n{findings.strip()}"
    # Truncate to LedgerEntry max (4096 chars)
    if len(content) > 4000:
        content = content[:4000] + "\n[truncated]"

    entry = LedgerEntry.create(
        content=content,
        agent="research-processor",
        vendor="local",
        model=DEFAULT_MODEL,
        entry_type="discovery",
        scope="project",
        tags=[
            "research",
            f"domain:{question['domain']}",
            f"rq:{question['id'].lower()}",
            f"tier:{question.get('tier', 3)}",
        ],
        confidence=0.6,  # Local LLM research = moderate confidence
    )

    parsed = urlparse(brain_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 11435

    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }
    token = os.environ.get("OPEN_BRAIN_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    conn = HTTPConnection(host, port, timeout=30)
    try:
        body = json.dumps(
            {"entries": [entry.to_dict()]}, separators=(",", ":"),
        ).encode("utf-8")
        headers["Content-Length"] = str(len(body))
        conn.request("POST", "/ingest", body=body, headers=headers)
        response = conn.getresponse()
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)
    except Exception as e:
        return {"ingested": 0, "errors": [str(e)]}
    finally:
        conn.close()


def run_processor(
    *,
    queue: list[dict[str, Any]] | None = None,
    state_file: str | Path | None = None,
    model: str = DEFAULT_MODEL,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    brain_url: str = DEFAULT_OPEN_BRAIN_URL,
    dry_run: bool = False,
    max_per_run: int = MAX_PER_RUN,
) -> dict[str, Any]:
    """Run one processor pass: pick questions, research, ingest.

    Returns dict with: processed, skipped, errors, questions.
    """
    if _is_kill_switch_engaged():
        logger.warning("Kill switch engaged, skipping research")
        return {"processed": 0, "skipped": 0, "errors": ["kill switch engaged"],
                "questions": []}

    if queue is None:
        queue = load_research_queue()

    state_path = Path(state_file) if state_file else _resolve_path(DEFAULT_STATE_FILE)
    state = _load_state(state_path)
    processed_state = state.get("processed", {})

    # Sort by tier (priority), then filter to those needing processing
    sorted_queue = sorted(queue, key=lambda q: q.get("tier", 99))
    to_process = [
        q for q in sorted_queue
        if _should_reprocess(q, processed_state)
    ]

    # Cap per run
    to_process = to_process[:max_per_run]

    result: dict[str, Any] = {
        "processed": 0,
        "skipped": len(queue) - len(to_process),
        "errors": [],
        "questions": [q["id"] for q in to_process],
    }

    if not to_process:
        logger.info("No questions to process (all up to date)")
        _save_state(state_path, state)
        return result

    for question in to_process:
        if _is_kill_switch_engaged():
            result["errors"].append("kill switch engaged mid-run")
            break

        qid = question["id"]
        logger.info("Researching %s: %s", qid, question["domain"])

        if dry_run:
            logger.info("DRY RUN: Would research %s (%s)", qid, question["query"][:80])
            result["processed"] += 1
            continue

        # Call Ollama
        findings = _ollama_research(
            question, model=model, base_url=ollama_url,
        )
        if not findings:
            result["errors"].append(f"{qid}: Ollama call failed")
            continue

        logger.info("Got findings for %s (%d chars)", qid, len(findings))

        # Ingest into Open Brain
        ingest_result = _ingest_finding(question, findings, brain_url=brain_url)
        if ingest_result.get("ingested", 0) > 0:
            result["processed"] += 1
            processed_state[qid] = {
                "hash": _question_hash(question),
                "last_processed": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "findings_length": len(findings),
            }
            logger.info("Ingested %s into Open Brain", qid)
        else:
            errors = ingest_result.get("errors", [])
            result["errors"].append(f"{qid}: ingest failed: {errors}")

    # Save state
    state["processed"] = processed_state
    state["total_processed"] = state.get("total_processed", 0) + result["processed"]
    _save_state(state_path, state)

    return result


def processor_status(
    *,
    queue: list[dict[str, Any]] | None = None,
    state_file: str | Path | None = None,
) -> dict[str, Any]:
    """Report processor status."""
    if queue is None:
        queue = load_research_queue()
    state_path = Path(state_file) if state_file else _resolve_path(DEFAULT_STATE_FILE)
    state = _load_state(state_path)
    processed = state.get("processed", {})

    pending = [
        q["id"] for q in queue
        if _should_reprocess(q, processed)
    ]
    completed = [
        q["id"] for q in queue
        if not _should_reprocess(q, processed)
    ]

    return {
        "total_questions": len(queue),
        "pending": pending,
        "completed": completed,
        "total_processed": state.get("total_processed", 0),
        "last_run": state.get("last_run"),
    }


def list_queue(
    *,
    queue: list[dict[str, Any]] | None = None,
    state_file: str | Path | None = None,
) -> list[dict[str, Any]]:
    """List all questions with their status."""
    if queue is None:
        queue = load_research_queue()
    state_path = Path(state_file) if state_file else _resolve_path(DEFAULT_STATE_FILE)
    state = _load_state(state_path)
    processed = state.get("processed", {})

    items = []
    for q in queue:
        qid = q["id"]
        p = processed.get(qid, {})
        items.append({
            "id": qid,
            "domain": q["domain"],
            "tier": q.get("tier", 3),
            "recurrence": q.get("recurrence", "once"),
            "status": "pending" if _should_reprocess(q, processed) else "done",
            "last_processed": p.get("last_processed"),
            "query": q["query"][:100],
        })
    return items


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Research Queue Processor -- local LLM research for Open Brain",
    )
    parser.add_argument(
        "--brain-url", default=DEFAULT_OPEN_BRAIN_URL,
        help=f"Open Brain URL (default: {DEFAULT_OPEN_BRAIN_URL})",
    )

    subparsers = parser.add_subparsers(dest="command")

    p_run = subparsers.add_parser("run", help="Process research questions")
    p_run.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    p_run.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    p_run.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama base URL")
    p_run.add_argument("--state-file", help="Override state file")
    p_run.add_argument("--max", type=int, default=MAX_PER_RUN, help=f"Max questions per run (default: {MAX_PER_RUN})")

    p_status = subparsers.add_parser("status", help="Show processor status")
    p_status.add_argument("--state-file", help="Override state file")

    p_list = subparsers.add_parser("list", help="List all research questions")
    p_list.add_argument("--state-file", help="Override state file")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 2

    if args.command == "status":
        s = processor_status(state_file=getattr(args, "state_file", None))
        print(json.dumps(s, indent=2))
        return 0

    if args.command == "list":
        items = list_queue(state_file=getattr(args, "state_file", None))
        for item in items:
            status_marker = "+" if item["status"] == "done" else " "
            last = item.get("last_processed", "never")
            if last and last != "never":
                last = last[:10]
            print(
                f"[{status_marker}] {item['id']} T{item['tier']} "
                f"{item['domain']:25s} {item['recurrence']:8s} "
                f"last={last}"
            )
            print(f"    {item['query']}")
        return 0

    if args.command == "run":
        result = run_processor(
            state_file=args.state_file,
            model=args.model,
            ollama_url=args.ollama_url,
            brain_url=args.brain_url,
            dry_run=args.dry_run,
            max_per_run=args.max,
        )
        print(json.dumps(result, indent=2))
        return 0 if not result["errors"] else 1

    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
