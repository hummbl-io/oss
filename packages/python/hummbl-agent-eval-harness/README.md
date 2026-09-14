# hummbl-agent-eval-harness

Evaluate text against required and forbidden regular expressions. The result
contains rule counts, a percentage score, and the failed rule descriptions.
Runtime code uses only the Python standard library. Python 3.11+ is required.

Status: Alpha, available from this source tree. This import does not publish
a PyPI release. The distribution name is `hummbl-agent-eval-harness`; the
existing Python namespace `agent_eval_harness` and `agent-eval` command are
preserved.

## Install from this repository

From the monorepo root:

```bash
python -m pip install './packages/python/hummbl-agent-eval-harness[test]'
```

## Python API

```python
from agent_eval_harness import AgentEvalHarness

harness = AgentEvalHarness()
harness.add_regex_constraint("status", r"\bPASS\b", "Include a status")
harness.add_regex_constraint(
    "secret", r"\bSECRET_KEY\b", "Omit the forbidden marker", must_not_match=True
)
result = harness.evaluate("Status: PASS")
assert result.passed_rules == 2
assert result.score == 100.0
```

## Command line

```bash
agent-eval 'Status: PASS' --require '\bPASS\b' --forbid '\bSECRET_KEY\b'
```

The command returns `0` when every rule passes, `1` when a rule fails, and
`2` for invalid arguments, invalid regular expressions, or no supplied rules.
This exit behavior supports a CI check of the specific constraints supplied.

## Scope

The built-in rules use Python `re.search`. They check textual matches; they
do not establish factual accuracy, semantic adherence, general model quality,
or absence of secrets. There is no built-in AST analysis or model connection.
Use trusted regex patterns and bounded inputs: Python's regex engine can
take excessive time on pathological patterns. The library retains its
existing score of 100 for an empty rule set; inspect `total_rules` before
interpreting a library result. The CLI requires at least one rule.

## Tests and provenance

Run `python -m pytest tests/ -q` from this package directory.
See [NOTICE](NOTICE) for the source commit and import changes, and
[LICENSE](LICENSE) for the retained MIT OR Apache-2.0 licensing.
