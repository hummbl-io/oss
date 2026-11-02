# hummbl-bif

**Batch Ingestion Framework** — a repeatable methodology for building a
comprehensive knowledge base on a company, product, service, or technical
domain, using an AI assistant.

The core idea: structured consumption in priority order, where each batch builds
on the last, produces layered understanding that unordered reading does not.
Work proceeds in four phases (Foundation, then progressively deeper batches),
with each batch validated before the next begins.

- Apache-2.0
- Python >= 3.11, stdlib only

## Install

```bash
pip install hummbl-bif
```

## CLI

```bash
bif start <domain>        # start a new ingestion session
bif status                # show session progress
bif template <phase> <batch> # print the prompt for a phase/batch
bif validate <file.md>    # validate a completed batch file
bif templates             # list available domain templates
```

The source checkout includes domain templates in `templates/`: `ai-ml-platform`,
`cloud-platform`, `programming-framework`, and `saas-evaluation`. To use those
source assets, install from the monorepo root with
`python -m pip install -e packages/python/hummbl-bif`.

## MCP server

`mcp_server.py` exposes the same operations to an MCP-capable assistant:
`bif_start_session`, `bif_get_template`, `bif_validate_batch`,
`bif_session_status`, `bif_list_templates`.

## Documentation

| File | Contents |
|---|---|
| [`FRAMEWORK.md`](FRAMEWORK.md) | The methodology in full — phases, batch structure, validation criteria |
| [`USE_CASES.md`](USE_CASES.md) | Worked applications |
| [`MOBILE_USE_CASES.md`](MOBILE_USE_CASES.md) | Running an ingestion from a phone |
| [`examples/`](examples/) | A complete worked ingestion |

## History

BIF previously lived in a standalone repository. Its source is now maintained
here in the `hummbl-io/oss` monorepo; version 1.0.1 is available on
[PyPI](https://pypi.org/project/hummbl-bif/1.0.1/).
