"""
ARCANA CLI — Command-line interface for article lifecycle management.

Usage:
    python -m pipeline.cli generate --topic "..." --agents yarvin,gramsci,foucault,synthesist --mode HOTL
    python -m pipeline.cli list [--dir articles/]
    python -m pipeline.cli approve <article_id> [--reviewer dan]
    python -m pipeline.cli reject <article_id> --reason "..." [--reviewer dan]
    python -m pipeline.cli show <article_id> [--dir articles/]
    python -m pipeline.cli index [--dir articles/]

Options:
    --dir       Directory for article storage (default: ./articles)
    --mode      HITL or HOTL (default: HOTL)
    --agents    Comma-separated agent names (default: yarvin,gramsci,foucault,synthesist)
    --reviewer  Reviewer identifier for approve/reject (default: "cli-user")
    --reason    Rejection reason (required for reject)
    --model     LLM model name (default: claude-sonnet-4-6)
    --confidence Synthesist confidence score 0.0-1.0 (default: 0.75)
    --stub      Use StubAPIClient (no real API calls)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python -m pipeline.cli` from any working directory
_HERE = Path(__file__).parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from pipeline.api_client import (  # noqa: E402
    AgentGenerationRequest,
    StubAPIClient,
    SynthesisRequest,
    build_article_from_results,
    get_system_prompt,
)
from pipeline.governance import (  # noqa: E402
    approve_receipt,
    generate_receipt,
    reject_receipt,
    validate_receipt,
)
from pipeline.models import ARCANAArticle, make_article_id  # noqa: E402
from pipeline.renderer import render_article, render_index  # noqa: E402

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _article_path(articles_dir: Path, article_id: str) -> Path:
    return articles_dir / f"{article_id}.json"


def _save_article(articles_dir: Path, article: ARCANAArticle) -> Path:
    articles_dir.mkdir(parents=True, exist_ok=True)
    path = _article_path(articles_dir, article.receipt.article_id)
    path.write_text(article.to_json(indent=2), encoding="utf-8")
    return path


def _load_article(articles_dir: Path, article_id: str) -> ARCANAArticle:
    path = _article_path(articles_dir, article_id)
    if not path.exists():
        _die(f"Article not found: {article_id}\n  (looked in {path})")
    return ARCANAArticle.from_json(path.read_text(encoding="utf-8"))


def _list_articles(articles_dir: Path) -> list[ARCANAArticle]:
    if not articles_dir.exists():
        return []
    articles = []
    for p in sorted(articles_dir.glob("*.json")):
        try:
            articles.append(ARCANAArticle.from_json(p.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"  [warn] Could not load {p.name}: {exc}", file=sys.stderr)
    return articles


def _die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_generate(args: argparse.Namespace) -> None:
    topic: str = args.topic
    agent_names: list[str] = [a.strip() for a in args.agents.split(",") if a.strip()]
    mode: str = args.mode.upper()
    articles_dir = Path(args.dir)
    model: str = args.model
    confidence: float = float(args.confidence)
    use_stub: bool = args.stub

    if mode not in {"HITL", "HOTL"}:
        _die(f"--mode must be HITL or HOTL; got '{mode}'")
    if not (0.0 <= confidence <= 1.0):
        _die(f"--confidence must be in [0.0, 1.0]; got {confidence}")
    if len(agent_names) < 2:
        _die("At least 2 agents are required (final agent is treated as synthesist)")

    # Separate non-synthesist agents from the synthesist
    # Convention: "synthesist" is always the meta-agent; if not in list, last agent is used
    if "synthesist" in agent_names:
        perspective_agents = [a for a in agent_names if a != "synthesist"]
        synthesist_name = "synthesist"
    else:
        perspective_agents = agent_names[:-1]
        synthesist_name = agent_names[-1]

    print("ARCANA Generate")
    print(f"  Topic   : {topic}")
    print(f"  Agents  : {', '.join(perspective_agents)} + synthesist={synthesist_name}")
    print(f"  Mode    : {mode}")
    print(f"  Model   : {model}")
    print(f"  Stub    : {use_stub}")
    print()

    if use_stub:
        client = StubAPIClient()
    else:
        from pipeline.ollama_client import OllamaAPIClient
        client = OllamaAPIClient(model_name=model)

    article_id = make_article_id()

    # 1. Generate perspective for each non-synthesist agent
    agent_results = []
    for agent_name in perspective_agents:
        lens, system_prompt = get_system_prompt(agent_name)
        print(f"  Generating: {agent_name} ({lens}) ...", end="", flush=True)
        request = AgentGenerationRequest(
            topic=topic,
            agent_name=agent_name,
            lens=lens,
            system_prompt=system_prompt,
            model=model,
        )
        result = client.generate_perspective(request)
        agent_results.append((agent_name, result))
        print(" done")

    # 2. Generate synthesis
    from pipeline.models import AgentPerspective
    # Build perspective objects for the synthesis request
    temp_perspectives = []
    for agent_name, result in agent_results:
        lens, _ = get_system_prompt(agent_name)
        try:
            data = json.loads(result.content)
        except json.JSONDecodeError:
            data = {"perspective": result.content, "key_claims": ["N/A", "N/A", "N/A"], "blind_spots": ""}
        temp_perspectives.append(
            AgentPerspective(
                agent_name=agent_name,
                lens=data.get("lens", lens),
                perspective=data.get("perspective", ""),
                key_claims=data.get("key_claims", ["N/A", "N/A", "N/A"]),
                blind_spots=data.get("blind_spots", ""),
            )
        )

    _synth_lens, synth_prompt = get_system_prompt(synthesist_name)
    print(f"  Synthesising ({synthesist_name}) ...", end="", flush=True)
    synth_request = SynthesisRequest(
        topic=topic,
        perspectives=temp_perspectives,
        system_prompt=synth_prompt,
        model=model,
    )
    synthesis_result = client.generate_synthesis(synth_request)
    print(" done")

    # 3. Assemble article
    article = build_article_from_results(
        topic=topic,
        agent_results=agent_results,
        synthesis_result=synthesis_result,
        mode=mode,
        article_id=article_id,
    )

    # 4. Run governance check and update receipt
    updated_receipt = generate_receipt(
        article,
        mode,
        model=model,
        confidence_score=confidence,
    )
    article.receipt = updated_receipt

    # 5. Save
    path = _save_article(articles_dir, article)
    md_path = articles_dir / f"{article.slug}.md"
    md_path.write_text(render_article(article), encoding="utf-8")

    print()
    print("Article generated:")
    print(f"  ID       : {article.receipt.article_id}")
    print(f"  Title    : {article.title}")
    print(f"  Slug     : {article.slug}")
    print(f"  JSON     : {path}")
    print(f"  Markdown : {md_path}")
    print(f"  Warnings : {len(updated_receipt.content_warnings)}")
    if updated_receipt.content_warnings:
        for w in updated_receipt.content_warnings:
            print(f"    - {w}")
    print(f"  Status   : {updated_receipt.human_review_status} ({mode})")
    if mode == "HITL":
        print("\n  [HITL] Human review required before publication.")
        print(f"  Run: python -m pipeline.cli approve {article.receipt.article_id}")


def cmd_list(args: argparse.Namespace) -> None:
    articles_dir = Path(args.dir)
    articles = _list_articles(articles_dir)

    if not articles:
        print(f"No articles found in {articles_dir}")
        return

    print(f"ARCANA Articles ({len(articles)} total)\n")
    fmt = "{:<36}  {:<10}  {:<8}  {:<10}  {}"
    print(fmt.format("ID", "Date", "Status", "Mode", "Title"))
    print("-" * 100)
    for art in articles:
        r = art.receipt
        date = r.generated_at[:10]
        title_short = art.title[:50] + ("..." if len(art.title) > 50 else "")
        print(fmt.format(r.article_id, date, r.human_review_status, r.oversight_mode, title_short))


def cmd_approve(args: argparse.Namespace) -> None:
    articles_dir = Path(args.dir)
    article_id: str = args.article_id
    reviewer: str = getattr(args, "reviewer", "cli-user") or "cli-user"

    article = _load_article(articles_dir, article_id)
    if article.receipt.human_review_status == "approved":
        print(f"Article {article_id} is already approved.")
        return

    updated_receipt = approve_receipt(article.receipt, reviewer=reviewer)
    if not validate_receipt(updated_receipt):
        _die("Receipt validation failed after approve — this is a bug, please report.")

    article.receipt = updated_receipt
    _save_article(articles_dir, article)

    # Re-render Markdown
    md_path = articles_dir / f"{article.slug}.md"
    md_path.write_text(render_article(article), encoding="utf-8")

    print(f"Approved: {article_id}")
    print(f"  Reviewer   : {reviewer}")
    print(f"  Reviewed at: {updated_receipt.reviewed_at}")
    print(f"  Title      : {article.title}")


def cmd_reject(args: argparse.Namespace) -> None:
    articles_dir = Path(args.dir)
    article_id: str = args.article_id
    reason: str = args.reason
    reviewer: str = getattr(args, "reviewer", "cli-user") or "cli-user"

    if not reason or not reason.strip():
        _die("--reason is required for reject")

    article = _load_article(articles_dir, article_id)
    if article.receipt.human_review_status == "rejected":
        print(f"Article {article_id} is already rejected.")
        return

    updated_receipt = reject_receipt(article.receipt, reviewer=reviewer, reason=reason)
    if not validate_receipt(updated_receipt):
        _die("Receipt validation failed after reject — this is a bug, please report.")

    article.receipt = updated_receipt
    _save_article(articles_dir, article)

    # Re-render Markdown
    md_path = articles_dir / f"{article.slug}.md"
    md_path.write_text(render_article(article), encoding="utf-8")

    print(f"Rejected: {article_id}")
    print(f"  Reviewer   : {reviewer}")
    print(f"  Reason     : {reason}")
    print(f"  Reviewed at: {updated_receipt.reviewed_at}")


def cmd_show(args: argparse.Namespace) -> None:
    articles_dir = Path(args.dir)
    article_id: str = args.article_id
    article = _load_article(articles_dir, article_id)
    print(render_article(article))


def cmd_index(args: argparse.Namespace) -> None:
    articles_dir = Path(args.dir)
    articles = _list_articles(articles_dir)
    print(render_index(articles))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.cli",
        description="ARCANA — Multi-agent governed article pipeline",
    )
    parser.add_argument(
        "--dir",
        default="articles",
        help="Article storage directory (default: ./articles)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # generate
    gen = sub.add_parser("generate", help="Generate a new governed article")
    gen.add_argument("--topic", required=True, help="Article topic / question")
    gen.add_argument(
        "--agents",
        default="yarvin,gramsci,foucault,synthesist",
        help="Comma-separated agent names (last is synthesist if 'synthesist' not in list)",
    )
    gen.add_argument("--mode", default="HOTL", choices=["HITL", "HOTL"],
                     help="Oversight mode (default: HOTL)")
    gen.add_argument("--model", default="claude-sonnet-4-6",
                     help="LLM model identifier")
    gen.add_argument("--confidence", default="0.75",
                     help="Synthesist confidence score 0.0-1.0 (default: 0.75)")
    gen.add_argument("--stub", action="store_true",
                     help="Use StubAPIClient (no real LLM calls)")

    # list
    sub.add_parser("list", help="List all articles in the storage directory")

    # approve
    apv = sub.add_parser("approve", help="Approve an article for publication")
    apv.add_argument("article_id", help="Article UUID to approve")
    apv.add_argument("--reviewer", default="cli-user", help="Reviewer identifier")

    # reject
    rej = sub.add_parser("reject", help="Reject an article")
    rej.add_argument("article_id", help="Article UUID to reject")
    rej.add_argument("--reason", required=True, help="Rejection reason")
    rej.add_argument("--reviewer", default="cli-user", help="Reviewer identifier")

    # show
    shw = sub.add_parser("show", help="Print rendered Markdown for an article")
    shw.add_argument("article_id", help="Article UUID to show")

    # index
    sub.add_parser("index", help="Print the article index / table of contents")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "generate": cmd_generate,
        "list": cmd_list,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "show": cmd_show,
        "index": cmd_index,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
