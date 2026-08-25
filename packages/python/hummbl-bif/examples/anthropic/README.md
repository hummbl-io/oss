# Anthropic Ecosystem Ingestion — Project Overview
> Domain: Anthropic (Claude API, MCP, Claude Code, Safety)
> Completed: 2026-03-24
> Local files present: 2 core files plus living CPN map
> Session time: ~4 hours

## Objective

Build a comprehensive developer knowledge base covering the full Anthropic ecosystem — from the core Messages API through MCP server development, Claude Code CLI, safety frameworks, and production best practices. Target use: accelerate development of HUMMBL governance tooling and support Anthropic Academy coursework.

## Target Domain Profile

| Field | Value |
|-------|-------|
| Company/Product | Anthropic / Claude |
| Primary documentation URL | https://docs.anthropic.com/ |
| `llms.txt` available? | Yes — https://docs.anthropic.com/llms.txt |
| Documentation format | Docs site (docs.anthropic.com) + GitHub |
| Estimated total doc size | Massive (1000+ pages) |
| Rate of change | Rapidly evolving (new models, features monthly) |
| SDK/API involved? | Yes — Python + TypeScript SDKs |
| Code repos to analyze? | github.com/anthropics/anthropic-sdk-python, github.com/anthropics/anthropic-cookbook, github.com/modelcontextprotocol |
| Certification/exam involved? | No (Anthropic Academy coursework) |
| Competitive alternatives | OpenAI GPT-4o, Google Gemini 1.5 Pro, Mistral |

## Source Inventory

| # | Source | URL | Type | Phase |
|---|--------|-----|------|-------|
| 1 | Anthropic llms.txt | https://docs.anthropic.com/llms.txt | LLM-optimized | 1 |
| 2 | Messages API reference | https://docs.anthropic.com/en/api/messages | API Ref | 1 |
| 3 | Models overview | https://docs.anthropic.com/en/docs/about-claude/models | Docs | 1 |
| 4 | Release notes | https://docs.anthropic.com/en/release-notes | Changelog | 1 |
| 5 | MCP specification | https://modelcontextprotocol.io/docs | Spec | 2 |
| 6 | Claude Code docs | https://docs.anthropic.com/en/docs/claude-code | Docs | 2-3 |
| 7 | Python SDK | https://github.com/anthropics/anthropic-sdk-python | Repo | 2-3 |
| 8 | Prompt engineering guide | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering | Docs | 5 |
| 9 | Production guardrails | https://docs.anthropic.com/en/docs/build-with-claude/guardrails | Docs | 6 |
| 10 | Engineering blog | https://www.anthropic.com/engineering | Blog | 7 |
| 11 | System prompts (leaked/published) | https://docs.anthropic.com/en/docs/system-prompts | Docs | 8 |
| 12 | Anthropic cookbook | https://github.com/anthropics/anthropic-cookbook | Repo | 9 |
| 13 | Model cards + research | https://www.anthropic.com/research | Papers | 10 |

## Batch Plan

| Batch | Phase | Name | Status |
|-------|-------|------|--------|
| 01 | Foundation | Core Reference | COMPLETE |
| 02 | Foundation | Protocol / Architecture | PLANNED |
| 03 | Foundation | Tooling Docs (SDK + Claude Code) | PLANNED |
| 04 | Foundation | Delta Document | COMPLETE |
| 05 | Technique | Prompt Engineering Best Practices | PLANNED |
| 06 | Technique | Production Hardening (Guardrails + Rate Limits) | PLANNED |
| 07 | Technique | Engineering Blog + Thought Leadership | PLANNED |
| 08 | Source | System Prompts + Default Configs | PLANNED |
| 09 | Source | Code Repos (SDK + Cookbook) | PLANNED |
| 10 | Source | Research + Safety Philosophy | PLANNED |

## Outcomes

When all 10 batches are completed:

- Can build and deploy MCP servers from scratch using the official Python/TypeScript SDK
- Can use the Claude Messages API with streaming, tool use, vision, and extended thinking
- Understand the full model family: when to use Haiku vs Sonnet vs Opus
- Know the current API surface: all parameters, stop sequences, beta headers
- Can implement production-quality prompt engineering using Anthropic's official techniques
- Can apply guardrails, content filtering, and rate limit strategies to production deployments
- Understand the research and safety philosophy behind Claude's design decisions
- Can navigate the anthropic-cookbook for working code examples on any use case

## Knowledge File Index

| File | Batch | Content |
|------|-------|---------|
| `01_Claude_API_Core_Reference.md` | 01 | Messages API, models, authentication, site map |
| `04_Delta_Document.md` | 04 | What changed since March 2026 — new models, deprecations |
| `CPN_COURSE_COMPLETION_MAP.md` | living | Claude Partner Network course evidence and BIF update routing |

Planned or missing local files:

| Planned file | Intended content |
|---|---|
| `02_Architecture_and_MCP.md` | MCP protocol, tool use architecture, streaming |
| `03_SDK_and_Claude_Code.md` | Python SDK, Claude Code CLI, TypeScript SDK |
| `05_Prompt_Engineering.md` | Prompting techniques, chain-of-thought, few-shot |
| `06_Production_Hardening.md` | Rate limits, error handling, content filtering |
| `07_Engineering_Blog.md` | Interpretability, Constitutional AI, key papers |
| `08_System_Prompts.md` | Published system prompts, recommended configs |
| `09_Code_Repos.md` | Cookbook structure, key examples, patterns to clone |
| `10_Research_and_Safety.md` | Alignment approach, safety frameworks, model cards |

## Maintenance Plan

| Trigger | Action |
|---------|--------|
| New Claude model released | Re-run Batch 4 (Delta), update model table in Batch 1 |
| Major API change | Update Batch 1 (API reference), note in Delta |
| New MCP features | Update Batch 2 (architecture) |
| CPN course badge added | Update `CPN_COURSE_COMPLETION_MAP.md`, then route exact deltas to the matching batch |
| Quarterly review | Check release notes, refresh stale pricing/limits |
