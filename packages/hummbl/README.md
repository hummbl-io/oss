# hummbl

**Structured reasoning framework for AI agents.**

hummbl turns plans, hypotheses, observations, evaluations, decisions, and reflections into durable, inspectable artifacts. It provides reasoning primitives, protocols (scientific method, structured tool use), capture from existing artifacts or live runtime hooks, planning, local analysis, scoring, and visualization.

Python 3.10+, zero runtime dependencies (stdlib-only).

## Install

```bash
pip install hummbl
```

For development:

```bash
git clone https://github.com/hummbl-io/oss.git
cd oss/packages/hummbl
pip install -e ".[test]"
```

No runtime dependencies are required. The `test` extra installs `pytest>=9,<10`.

## Usage

hummbl provides core modules for reasoning capture and analysis:

- `reasoning.py` — reasoning primitives
- `protocols.py` — scientific method and structured tool use protocols
- `planner.py` — planning primitives
- `capture.py` — capture from existing artifacts or live runtime hooks
- `analyzer.py` — local analysis of reasoning traces
- `scoring.py` — scoring reasoning artifacts
- `visualize.py` — visualization of reasoning traces
- `cli.py` — command-line interface
- `hummbl_tuples/` — typed tuple primitives for contracts, delegation, evidence, and attestation

Reasoning traces are stored in `traces/`. Documentation (PRD, evals, roadmap, repo map) lives in `docs/`.

## Testing

```bash
pytest
```

The test suite covers protocols, reasoning, scoring, and tool-use capture (`tests/test_protocols.py`, `test_reasoning.py`, `test_scoring.py`, `test_tool_use_capture.py`).

## License

Apache License 2.0. See [LICENSE](LICENSE).
