"""Rendering helpers for ARCANA article objects."""

from __future__ import annotations

from models import ARCANAArticle


def render_article(article: ARCANAArticle) -> str:
    """Render an `ARCANAArticle` as human-readable Markdown."""
    lines = [f"# {article.title}", ""]
    lines.append(f"**Article ID:** {article.receipt.article_id}")
    lines.append(f"**Topic:** {article.title}")
    lines.append(f"**Generated:** {article.receipt.generated_at}")
    lines.append(f"**Oversight mode:** {article.receipt.oversight_mode}")
    lines.append(f"**Review status:** {article.receipt.human_review_status}")
    if article.summary:
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(article.summary)
    lines.append("")
    if article.convergences:
        lines.append("## Convergences")
        lines.append("")
        lines.extend(f"- {item}" for item in article.convergences)
        lines.append("")
    if article.divergences:
        lines.append("## Divergences")
        lines.append("")
        lines.extend(f"- {item}" for item in article.divergences)
        lines.append("")
    lines.append("## Synthesis")
    lines.append("")
    lines.append(article.synthesis or "(empty)")
    lines.append("")
    if article.live_questions:
        lines.append("## Live Questions")
        lines.append("")
        lines.extend(f"- {item}" for item in article.live_questions)
        lines.append("")
    if article.perspectives:
        lines.append("## Perspectives")
        lines.append("")
        for p in article.perspectives:
            lines.append(f"### {p.agent_name} ({p.lens})")
            lines.append("")
            lines.append(p.perspective)
            lines.append("")
            lines.append("**Key claims**")
            lines.extend(f"- {c}" for c in p.key_claims)
            lines.append("")
            lines.append(f"**Blind spots:** {p.blind_spots}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_index(articles) -> str:
    """Render a compact index of articles."""
    lines = ["# ARCANA Index", ""]
    for article in sorted(articles, key=lambda item: item.receipt.generated_at, reverse=True):
        lines.append(f"- {article.title} (`{article.receipt.article_id}`)")
    return "\n".join(lines).strip() + "\n"
