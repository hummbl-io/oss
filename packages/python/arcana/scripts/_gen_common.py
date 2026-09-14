"""Shared utilities for the generator family.

Every generate_*.py script uses the same scaffold:
- read endpoints.json to pick an Ollama endpoint
- call /api/generate with format=json + think=false
- validate each result, dedup, append to a per-generator TSV log
- optionally merge into a master config file

This module centralizes that so each generator only needs:
- a prompt (versioned)
- a validator function
- an optional merger

Public surface (keep stable — downstream generators depend on these):
  PROMPT_VERSION (per-generator, used in log rows)
  load_endpoint(name) -> dict
  ollama_generate(endpoint, system, user, seed, think=False) -> {parsed, elapsed_s, ...}
  self_review(endpoint, draft, schema_hint, seed) -> reviewed_draft   [optional, opt-in]
  TsvLog(path, header) — append-only logger with atomic header write
  validate_required_string_fields(obj, fields, min_len_map) -> (ok, reason)
  snake_case_ok(s) -> bool
  dedup_preserve_order(items, keyfn) -> list
  standard_argparse() -> argparse.ArgumentParser  # base flags every generator shares
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import string as _string
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENDPOINTS_PATH = HERE / "endpoints.json"
ENDPOINTS_EXAMPLE_PATH = HERE / "endpoints.example.json"
PROMPTS_DIR = HERE / "prompts"

ENV_ENDPOINTS_PATH = "ARCANA_ENDPOINTS_PATH"
ENV_OLLAMA_URL = "ARCANA_OLLAMA_URL"


def _safe_urlopen(req, timeout=None):
    """urlopen wrapper that restricts URL schemes to http/https (bandit B310)."""
    url = req.full_url if hasattr(req, "full_url") else str(req)
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Blocked non-http(s) URL scheme: {url}")
    if timeout is not None:
        return urllib.request.urlopen(req, timeout=timeout)
    return urllib.request.urlopen(req)


ENV_OLLAMA_NAME = "ARCANA_OLLAMA_NAME"
ENV_OLLAMA_MODEL = "ARCANA_OLLAMA_MODEL"
ENV_OLLAMA_MAX_PARALLEL = "ARCANA_OLLAMA_MAX_PARALLEL"

# Bump when a schema-affecting change is made to a prompt or validator.
# Individual generators override with their own module-level PROMPT_VERSION.
COMMON_VERSION = "common-v1"

# ------------------------------- endpoints ------------------------------- #

def _coerce_max_parallel(value: str | None) -> int:
    if value is None:
        return 1
    try:
        parsed = int(value)
    except ValueError:
        raise SystemExit(
            f"{ENV_OLLAMA_MAX_PARALLEL} must be an integer, got {value!r}")
    if parsed <= 0:
        raise SystemExit(
            f"{ENV_OLLAMA_MAX_PARALLEL} must be > 0, got {parsed}")
    return parsed


def _endpoint_from_env() -> dict | None:
    url = os.getenv(ENV_OLLAMA_URL)
    if not url:
        return None
    return {
        "name": os.getenv(ENV_OLLAMA_NAME, "env"),
        "url": url,
        "model": os.getenv(ENV_OLLAMA_MODEL, "qwen3.5:9b"),
        "max_parallel": _coerce_max_parallel(os.getenv(ENV_OLLAMA_MAX_PARALLEL)),
    }


def _load_endpoints_payload(path: Path | None = None) -> dict:
    # Runtime override: direct endpoint URL (lowest-friction local-only mode)
    override = _endpoint_from_env()
    if override:
        return {"endpoints": [override]}

    searched: list[Path] = []
    if path is not None:
        searched.append(path)

    env_path = os.getenv(ENV_ENDPOINTS_PATH)
    if env_path:
        searched.append(Path(env_path))

    # Defaults keep local-only behavior portable for non-canonical hosts.
    searched.extend([ENDPOINTS_PATH, ENDPOINTS_EXAMPLE_PATH])

    for candidate in searched:
        if not candidate.exists():
            continue
        data = json.loads(candidate.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(
                f"endpoint payload must be an object: {candidate}")
        if not isinstance(data.get("endpoints"), list):
            raise SystemExit(
                f"endpoint payload missing/invalid 'endpoints': {candidate}")
        return data

    if searched:
        raise SystemExit(
            "no endpoints configured; set ARCANA_OLLAMA_URL or create a file at "
            f"{ENDPOINTS_PATH} / {ENDPOINTS_EXAMPLE_PATH}")
    raise SystemExit(
        "no endpoints configured; set ARCANA_OLLAMA_URL first")


def load_endpoints(path: Path | None = None) -> list[dict]:
    """Load all configured endpoints as a list of dicts."""
    payload = _load_endpoints_payload(path)
    return payload["endpoints"]


def load_endpoint(name: str | None = None) -> dict:
    enabled = [e for e in load_endpoints() if e.get("enabled", True)]
    if not enabled:
        raise SystemExit("no endpoints enabled")
    if name:
        match = [e for e in enabled if e["name"] == name]
        if not match:
            raise SystemExit(
                f"endpoint '{name}' not enabled or not found. "
                f"available: {[e['name'] for e in enabled]}")
        return match[0]
    return enabled[0]


# ----------------------------- Ollama call ------------------------------- #

@dataclass
class OllamaResult:
    """Structured result of a single Ollama /api/generate call."""
    parsed: dict | list | None    # JSON-parsed body.response (or .thinking fallback)
    raw: str                      # untouched string
    elapsed_s: float
    prompt_tokens: int
    completion_tokens: int
    model: str
    endpoint_name: str
    parse_error: str | None = None

    def ok(self) -> bool:
        return self.parse_error is None and self.parsed is not None


def ollama_generate(endpoint: dict, system: str, user: str,
                    seed: int | None = None, think: bool = False,
                    timeout: int = 600,
                    extra_options: dict | None = None) -> OllamaResult:
    """Call Ollama /api/generate in JSON mode. Returns OllamaResult.

    Catches TimeoutError/OSError/URLError and returns an OllamaResult with
    parse_error set — callers should not have to try/except around this.
    """
    import time as _time
    payload: dict = {
        "model": endpoint["model"],
        "system": system,
        "prompt": user,
        "stream": False,
        "format": "json",
        "think": think,
    }
    if seed is not None or extra_options:
        payload["options"] = {}
        if seed is not None:
            payload["options"]["seed"] = seed
        if extra_options:
            payload["options"].update(extra_options)

    url = endpoint["url"].rstrip("/") + "/api/generate"
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    t0 = _time.time()
    try:
        with _safe_urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return OllamaResult(
            parsed=None, raw="", elapsed_s=_time.time() - t0,
            prompt_tokens=0, completion_tokens=0,
            model=endpoint["model"], endpoint_name=endpoint["name"],
            parse_error=f"{type(e).__name__}: {e}")

    elapsed = _time.time() - t0
    raw = body.get("response", "") or body.get("thinking", "")
    try:
        parsed = json.loads(raw)
        parse_error = None
    except json.JSONDecodeError as e:
        parsed = None
        parse_error = f"JSONDecodeError: {e}"
    return OllamaResult(
        parsed=parsed, raw=raw, elapsed_s=round(elapsed, 2),
        prompt_tokens=body.get("prompt_eval_count", 0),
        completion_tokens=body.get("eval_count", 0),
        model=endpoint["model"], endpoint_name=endpoint["name"],
        parse_error=parse_error)


# ------------------------- self-review (opt-in) -------------------------- #

def self_review(endpoint: dict, draft: dict | list, schema_hint: str,
                seed: int | None = None, timeout: int = 600) -> OllamaResult:
    """Ask the model to review its own draft and return a corrected version.

    Used by generators via --self-review to improve hit rate before validation.
    The review prompt asks the model to identify items likely to fail validation
    and return only a polished set. Same schema shape as the original.
    """
    system = (
        "You are a strict reviewer of LLM-generated structured output. "
        "Given a draft and a schema description, remove weak or malformed "
        "items and return only the ones that meet the schema cleanly. "
        "Return valid JSON only; preserve the top-level shape of the draft."
    )
    user = (
        f"Schema hint:\n{schema_hint}\n\n"
        f"Draft to review:\n{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
        f"Return the polished version with the same top-level JSON shape."
    )
    return ollama_generate(endpoint, system, user, seed=seed,
                           think=False, timeout=timeout)


# --------------------------- TSV logging -------------------------------- #

class TsvLog:
    """Append-only TSV writer with idempotent header.

    Each row is a dict; columns come from the header list passed at
    construction. Values are _tsv_cleaned before write.
    """
    def __init__(self, path: Path, columns: list[str]):
        self.path = path
        self.columns = columns
        self.header_line = "\t".join(columns) + "\n"

    def append(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = (not self.path.exists()
                        or self.path.stat().st_size == 0)
        with self.path.open("a", encoding="utf-8", newline="") as f:
            if write_header:
                f.write(self.header_line)
            for row in rows:
                fields = [_tsv_clean(str(row.get(col, ""))) for col in self.columns]
                f.write("\t".join(fields) + "\n")
        return len(rows)


def _tsv_clean(s: str) -> str:
    """Strip tabs/newlines so each TSV row stays on one line."""
    return s.replace("\t", " ").replace("\n", " ").replace("\r", " ")


# ---------------------- validator building blocks ----------------------- #

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def snake_case_ok(s: str) -> bool:
    return bool(SNAKE_CASE_RE.match(s))


def validate_required_string_fields(
        obj: dict, fields: tuple[str, ...],
        min_len: dict[str, int] | None = None) -> tuple[bool, str]:
    """Common validation: every required field is a non-empty string, with
    optional per-field minimum length. Returns (ok, reason_if_not_ok)."""
    min_len = min_len or {}
    for field in fields:
        if field not in obj or not isinstance(obj[field], str):
            return False, f"missing or non-string field: {field}"
        if not obj[field].strip():
            return False, f"empty field: {field}"
        lo = min_len.get(field)
        if lo and len(obj[field]) < lo:
            return False, (f"field '{field}' too short "
                           f"({len(obj[field])} < {lo} chars)")
    return True, ""


def dedup_preserve_order(items: list, keyfn) -> list:
    """Dedup keeping first occurrence. `keyfn(item) -> hashable`."""
    seen = set()
    out = []
    for item in items:
        k = keyfn(item)
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


# ------------------------ shared argparse base --------------------------- #

def standard_argparse(description: str) -> argparse.ArgumentParser:
    """Base argparse with the flags every generator shares.

    Generators call this, add their own args, then parse_args.
    Shared flags: --model, --endpoint, --seed, --output, --dry-run,
                  --self-review, --prompt-version (read-only info)
    """
    p = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default=None,
                   help="override endpoint model")
    p.add_argument("--endpoint", default=None,
                   help="endpoint name (default: first enabled)")
    p.add_argument("--seed", type=int, default=None,
                   help="deterministic seed passed to Ollama options.seed")
    p.add_argument("--output", default=None,
                   help="output path (generator-specific default)")
    p.add_argument("--dry-run", action="store_true",
                   help="print to stdout, do not write files or log")
    p.add_argument("--self-review", action="store_true",
                   help="run a second LLM pass to polish the draft before validation")
    p.add_argument("--min-accepted", type=int, default=0,
                   help="if positive, retry the brainstorm up to --max-retries "
                        "times (with seed bumped per attempt) until this many "
                        "valid items have accumulated")
    p.add_argument("--max-retries", type=int, default=0,
                   help="additional attempts after the first (only used when "
                        "--min-accepted is set)")
    p.add_argument("--preview-merge", action="store_true",
                   help="when used with --merge, print the diff and skip "
                        "the target file write (use to vet a merge before "
                        "committing it)")
    return p


# ------------------------- provenance helpers --------------------------- #

def now_utc_iso() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_prompt(name: str, version: str) -> tuple[str, _string.Template]:
    """Load a versioned prompt from prompts/{name}_{version}.txt.

    File format (newline-separated sections):
        ---SYSTEM---
        <system prompt text>
        ---USER---
        <user prompt template with $var placeholders>

    Returns (system_text, user_template) where user_template is a
    string.Template; call .safe_substitute(**vars) to render. $-escapes
    are standard Python string.Template rules: $name or ${name} are
    placeholders, $$ is a literal $.

    Versioned file naming means bumping a prompt creates a new file
    (prompts/topics_v2.txt) rather than silently editing v1. PROMPT_VERSION
    in the calling module should match the file's version suffix.
    """
    path = PROMPTS_DIR / f"{name}_{version}.txt"
    if not path.exists():
        raise SystemExit(f"prompt file not found: {path}")
    content = path.read_text(encoding="utf-8")
    if "---USER---" not in content:
        raise SystemExit(f"malformed prompt file {path}: missing ---USER--- marker")
    system_section, user_section = content.split("---USER---", 1)
    # Strip optional ---SYSTEM--- marker from the system section
    if "---SYSTEM---" in system_section:
        system_section = system_section.split("---SYSTEM---", 1)[1]
    return system_section.strip(), _string.Template(user_section.strip())


def retry_until_full(attempt_fn, min_accepted: int, max_retries: int = 0,
                     log_fn=print) -> tuple[list, list]:
    """Keep calling attempt_fn(attempt_idx) -> (accepted, rejected) until the
    cumulative accepted count >= min_accepted, or retries are exhausted.

    The caller is responsible for:
    - Seeding each attempt differently (usually base_seed + attempt_idx)
    - Deduplicating across attempts (items accepted in attempt N must not
      re-appear as "new" in attempt N+1; use a seen_keys set)

    Returns (all_accepted, all_rejected). Never raises; exceptions from
    attempt_fn are caught and recorded as rejection rows with a reason
    of 'attempt_error: <cls>: <msg>'.

    If min_accepted == 0, runs exactly one attempt (no retries).
    """
    all_accepted: list = []
    all_rejected: list = []
    # min_accepted == 0 means: run exactly once (no retry loop)
    max_attempts = 1 if min_accepted <= 0 else max(1, max_retries + 1)
    for attempt in range(max_attempts):
        if min_accepted > 0 and len(all_accepted) >= min_accepted:
            break
        log_fn(f"[retry] attempt {attempt + 1}/{max_attempts} "
               f"(accepted so far: {len(all_accepted)})")
        try:
            accepted, rejected = attempt_fn(attempt)
        except Exception as e:
            log_fn(f"[retry] attempt {attempt + 1} raised "
                   f"{type(e).__name__}: {e}")
            all_rejected.append(({}, f"attempt_error: {type(e).__name__}: {e}"))
            continue
        all_accepted.extend(accepted)
        all_rejected.extend(rejected)
    return all_accepted, all_rejected


def run_brainstorm(
    *,
    endpoint: dict,
    build_prompt,
    list_key: str,
    item_validator,
    base_seed: int | None,
    self_review: bool,
    schema_hint: str = "",
    timeout: int = 600,
    min_accepted: int = 0,
    max_retries: int = 0,
    log_fn=print,
    ollama_fn=None,
    self_review_fn=None,
) -> tuple[list, list, OllamaResult | None]:
    """Run one brainstorm-and-validate pass with optional retry.

    Encapsulates the pattern shared across generate_agents, generate_pairings,
    generate_synthesis_variants, and generate_scenarios:

      1. Build prompt -> ollama_generate -> parse JSON response.
      2. Optionally self-review the draft (uses schema_hint).
      3. Extract parsed[list_key]; reject if not a list.
      4. For each item: skip non-dicts, then call item_validator(item).
      5. If min_accepted > 0, retry with bumped seeds until target hit
         or retries exhausted.

    Caller responsibilities:

    - build_prompt: zero-arg callable returning (system, user) text. Caller
      closes over varying inputs (theme, count, exclusions, etc.).
    - item_validator: callable (item: dict) -> (ok: bool, reason: str). May
      update cross-item state (seen-id sets, dedup frozensets) via closure.
      Caller must add accepted-item keys to its own seen-set when ok is True.
    - log_fn: progress reporter (default print; production passes a stderr
      lambda).

    Returns (accepted, rejected, last_result). last_result is the OllamaResult
    from the most recent attempt (None only if every attempt raised before
    setting it). The caller uses last_result for provenance + error logging.

    The ollama_fn / self_review_fn parameters are dependency-injection points
    for testing; production callers leave them None to use the module defaults.
    """
    if ollama_fn is None:
        ollama_fn = ollama_generate
    if self_review_fn is None:
        self_review_fn = self_review
    state: dict = {"last_result": None}

    def attempt(attempt_idx: int) -> tuple[list, list]:
        seed = None if base_seed is None else base_seed + attempt_idx
        system, user = build_prompt()
        result = ollama_fn(endpoint, system, user, seed=seed,
                           think=False, timeout=timeout)
        state["last_result"] = result
        if not result.ok():
            return [], [({}, f"ollama: {result.parse_error}")]
        if self_review:
            review = self_review_fn(endpoint, result.parsed, schema_hint,
                                    seed=seed)
            parsed = review.parsed if review.ok() else result.parsed
        else:
            parsed = result.parsed
        raw = (parsed or {}).get(list_key) or []
        if not isinstance(raw, list):
            return [], [({}, f"not a {list_key}-list: got {type(raw).__name__}")]
        accepted: list = []
        rejected: list = []
        for item in raw:
            if not isinstance(item, dict):
                rejected.append((item, "not a dict"))
                continue
            ok, reason = item_validator(item)
            if ok:
                accepted.append(item)
            else:
                rejected.append((item, reason))
        return accepted, rejected

    if min_accepted > 0:
        accepted, rejected = retry_until_full(
            attempt, min_accepted=min_accepted, max_retries=max_retries,
            log_fn=log_fn)
    else:
        accepted, rejected = attempt(0)
    return accepted, rejected, state["last_result"]


def provenance_row(*, source: str, theme: str, model: str,
                   seed: int | None, prompt_version: str) -> dict:
    """Standard provenance fields for a TSV log row."""
    return {
        "timestamp_utc": now_utc_iso(),
        "source": source,
        "theme": theme,
        "model": model,
        "seed": str(seed) if seed is not None else "",
        "prompt_version": prompt_version,
    }
