# arcana

HUMMBL multi-lens governance and political-philosophy analysis workspace.

Turns a topic into a structured article family (canonical `article.md`,
agent-optimized `article.llm.md`, `meta.json`, `schema.jsonld`) with
PAIDEIA-9 reflection scoring.

## Modules

- `api_client` — LLM API client with lens registry loading
- `cli` — Command-line interface
- `models` — Data models
- `ollama_client` — Ollama local LLM client
- `pipeline` — Analysis pipeline (governance, renderer, models)
- `CANON` — Canonical source contracts
- `EVIDENCE` — Evidence contracts
- `LINGUA` — Language contracts
- `NOMOS` — Governance law contracts
- `POIESIS` — Production stage contracts
- `PRAXIS` — Execution pipeline contracts
- `RELEASE` — Release gate contracts
- `SYNTHESIS` — Synthesis runtime and contracts
- `sources` — Source adapters

## Setup

```bash
pip install -e ".[test]"
```

## Testing

```bash
python -m pytest tests/ -v
```

## License

Apache-2.0
