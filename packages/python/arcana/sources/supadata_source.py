"""
ARCANA Supadata Source — enrich topics with web content and video transcripts.

Stdlib-only. Reads SUPADATA_API_KEY from environment.

Usage:
    from sources.supadata_source import enrich_topic, fetch_source_urls

    # Enrich a topic with sources from URLs
    enriched = enrich_topic("AI governance frameworks", urls=[
        "https://www.nist.gov/itl/ai-risk-management-framework",
        "https://eur-lex.europa.eu/eli/reg/2024/1689",
    ])

    # Or pass enriched topic directly to ARCANA agent generation
    from pipeline.api_client import AgentGenerationRequest
    req = AgentGenerationRequest(topic=enriched, agent_name="foucault", ...)
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE = "https://api.supadata.ai/v1"
API_KEY = os.environ.get("SUPADATA_API_KEY", "")

HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; ARCANA-SupadataSource/1.0; +https://github.com/hummbl-dev)",
}

LAST_CALL = 0.0
SOURCE_CHAR_LIMIT = 8000  # cap per source to avoid overwhelming agent context


def _rate_limit() -> None:
    global LAST_CALL
    elapsed = time.time() - LAST_CALL
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    LAST_CALL = time.time()


def _request(endpoint: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    url = f"{BASE}{endpoint}"
    if params:
        qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items() if v is not None)
        url = f"{url}?{qs}"
    _rate_limit()
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
        msg = str(getattr(e, "reason", e))
        return {"error": f"Supadata fetch failed: {msg}"}


# ---------------------------------------------------------------------------
# Source fetching
# ---------------------------------------------------------------------------

@dataclass
class Source:
    url: str
    source_type: str  # "web" | "transcript" | "metadata"
    title: str = ""
    content: str = ""
    error: str = ""


def fetch_web_source(url: str) -> Source:
    data = _request("/web/scrape", {"url": url})
    if "error" in data:
        return Source(url=url, source_type="web", error=data["error"])
    content = data.get("content", "")
    return Source(
        url=url,
        source_type="web",
        title=data.get("title", "") or url,
        content=content[:SOURCE_CHAR_LIMIT],
    )


def fetch_transcript(url: str, lang: str = "en") -> Source:
    data = _request("/youtube/transcript", {"url": url, "lang": lang, "text": "true"})
    if "error" in data:
        return Source(url=url, source_type="transcript", error=data["error"])
    segments = data.get("content", [])
    if isinstance(segments, str):
        text = segments.strip()
    elif segments and isinstance(segments[0], str):
        text = " ".join(str(s).strip() for s in segments)
    elif segments and isinstance(segments[0], dict):
        text = " ".join(s.get("text", "").strip() for s in segments if isinstance(s, dict))
    else:
        text = ""
    return Source(
        url=url,
        source_type="transcript",
        title=data.get("title", "") or url,
        content=text[:SOURCE_CHAR_LIMIT],
    )


def fetch_metadata(url: str) -> Source:
    data = _request("/metadata", {"url": url})
    if "error" in data:
        return Source(url=url, source_type="metadata", error=data["error"])
    md = []
    for field in ("title", "author", "platform", "published_at", "description"):
        val = data.get(field, "")
        if val:
            md.append(f"{field}: {val}")
    return Source(
        url=url,
        source_type="metadata",
        title=data.get("title", "") or url,
        content="\n".join(md),
    )


def _guess_source_type(url: str) -> str:
    video_domains = {"youtube.com", "youtu.be", "tiktok.com", "instagram.com", "x.com", "twitter.com"}
    for d in video_domains:
        if d in url.lower():
            return "transcript"
    return "web"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_source_urls(urls: list[str]) -> list[Source]:
    """Fetch all sources. Returns list of Source objects (including failures)."""
    sources: list[Source] = []
    for url in urls:
        stype = _guess_source_type(url)
        if stype == "transcript":
            sources.append(fetch_transcript(url))
        else:
            sources.append(fetch_web_source(url))
    return sources


def enrich_topic(topic: str, urls: list[str] | None = None) -> str:
    """
    Enrich an ARCANA topic with source material from web pages and video transcripts.

    Returns the original topic plus appended source content, suitable for passing
    as the `topic` argument to AgentGenerationRequest.

    If the API key is not set, returns the topic unchanged.
    """
    if not API_KEY:
        return topic

    if not urls:
        return topic

    sources = fetch_source_urls(urls)
    valid = [s for s in sources if s.content and not s.error]

    if not valid:
        return topic

    blocks = [f"TOPIC: {topic}\n"]
    blocks.append("--- SOURCE MATERIALS (fetched via Supadata) ---\n")
    for i, src in enumerate(valid, 1):
        stype_label = {"web": "Web Page", "transcript": "Video Transcript", "metadata": "Metadata"}
        label = stype_label.get(src.source_type, src.source_type)
        blocks.append(f"[SOURCE {i}] {label}: {src.title}")
        blocks.append(f"[SOURCE {i}] URL: {src.url}")
        blocks.append(f"[SOURCE {i}] Content:\n{src.content}\n")

    enriched = "\n".join(blocks)
    if len(enriched) > 50000:
        enriched = enriched[:50000] + "\n[...source material truncated at 50K chars]"
    return enriched
