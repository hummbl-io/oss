# hummbl-mcp-basen

MCP server exposing the Base120 + BaseN governance surface: operator lookup,
family browse, embedding-backed recommendations, and tiered apply modes.

## What it provides

- **4 parameterized tools:**
  - `basen_operator_lookup(operator_id, variant)` — lookup by ID, such as `P1` or `SY20`
  - `basen_family_browse(family, variant)` — list operators in a family, such as `P`, `IN`, `CO`, `DE`, `RE`, or `SY`
  - `basen_recommend(problem_description, variant, top_k)` — embedding-backed recommendations with keyword fallback
  - `basen_apply(operator_id, input, mode)` — apply an operator with `advisory`, `analytic`, or `empirical` mode
- **127 URI-addressable resources:**
  - `basen://base120/operator/{P1..SY20}` — 120 operators
  - `basen://base120/family/{P|IN|CO|DE|RE|SY}` — 6 families
  - `basen://base120/manifest` — full catalog manifest
- **3 starter prompts:**
  - `basen-recon` — apply BaseN to recon a problem
  - `basen-spec` — convert intent into a spec
  - `basen-audit` — audit an artifact with BaseN

Tier 1 calls emit and persist a governance record shaped like a `BaseNTuple`
unless disabled with `BASEN_PERSIST_TUPLES=0`. `basen_apply` is mode-sensitive:
`advisory` is a Tier 0 descriptive read, while `analytic` and `empirical` are
Tier 1 calls.

## Install from source

From the root of a checkout of
[hummbl-io/oss](https://github.com/hummbl-io/oss):

```bash
python -m pip install ./packages/python/hummbl-mcp-basen
```

For an editable development install, from the same repository root:

```bash
python -m pip install -e ./packages/python/hummbl-mcp-basen
```

## Run

```bash
hummbl-mcp-basen
```

Or via Python module:

```bash
python -m basen.mcp_server
```

Then write newline-delimited JSON-RPC requests to stdin:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"basen_operator_lookup","arguments":{"operator_id":"IN2"}}}
{"jsonrpc":"2.0","id":4,"method":"resources/read","params":{"uri":"basen://base120/family/IN"}}
{"jsonrpc":"2.0","id":5,"method":"prompts/get","params":{"name":"basen-recon","arguments":{"input":"Plan a migration."}}}
```

## Wiring into Claude Code / Devin

```json
{
  "mcpServers": {
    "basen": {
      "command": "hummbl-mcp-basen",
      "env": {
        "BASEN_MCP_AGENT": "basen-mcp"
      }
    }
  }
}
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BASEN_REGISTRY_PATH` | bundled `data/base120_registry.json` | Override registry path |
| `BASEN_MCP_AGENT` | `basen-mcp` | Emitted agent identity in tuples |
| `BASEN_TUPLE_LOG` | `_state/governance/tuples.jsonl` | JSONL tuple log path |
| `BASEN_PERSIST_TUPLES` | `1` | Set to `0` to disable tuple persistence |
| `BASEN_EMBED_URL` | `http://127.0.0.1:11434/api/embeddings` | Ollama embeddings endpoint |
| `BASEN_EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `BASEN_EMBED_TIMEOUT` | `5.0` | Embedding request timeout (seconds) |
| `BASEN_EMBED_CACHE_DIR` | `_state/basen` | Embedding cache directory |
| `BASEN_CHAT_URL` | `http://127.0.0.1:11434/api/chat` | Ollama chat endpoint |
| `BASEN_CHAT_MODEL` | `qwen3.5:9b` | Chat model for empirical apply mode |
| `BASEN_CHAT_TIMEOUT` | `30.0` | Chat request timeout (seconds) |
| `BASEN_DOMAIN120_MANIFEST` | unset | Explicit local Domain120 inspection snapshot manifest; requires its hash |
| `BASEN_DOMAIN120_MANIFEST_SHA256` | unset | Expected lowercase SHA-256 of that manifest's exact bytes |

## Optional Domain120 snapshot inspection

With both Domain120 variables unset, the existing four tools remain the default.
Setting both opts this process into six additional experimental read tools:

| Tool | Input and result |
|---|---|
| `basen_domain120_catalogs` | No arguments; lists configured catalog identities and source/authority context |
| `basen_domain120_inspect` | Exact `catalog` identity; returns inspection context |
| `basen_domain120_lookup` | Exact `catalog` and `local_code`; returns the retained operator record and separate Base120 ancestor |
| `basen_domain120_browse` | Exact `catalog`, optional `family`, `offset`, `limit` and `context_mode`; returns a page, matching count and next offset |
| `basen_domain120_relations` | Exact `catalog`; returns known source relation declarations and pointers, without interpreting composition or reuse |
| `basen_domain120_source` | Exact `catalog`; returns the retained source document, including fields omitted by other projections |

Copy the structured `catalog` identity from the listing: `namespace`, `version`
(a string or explicit JSON `null`) and `artifact_sha256`. All three fields are
required. A bare operator code cannot select a domain catalog. Browse defaults
to ten records and accepts limits from one to fifty; omit `family` to browse all
families. No Domain120 recommendation, application, generation, admission,
promotion, publication or BaseX operation is exposed. Existing Base120 variants,
resources and prompts keep their separate meanings.

Browse defaults to `context_mode="per_operator"`, retaining a complete catalog
context in each operator. Set `context_mode="shared"` to retain the complete
context once at the page's `catalog_context` and replace each operator's copy
with `catalog_context_ref="/catalog_context"`. That JSON Pointer resolves within
the decoded tool-result document, not the outer JSON-RPC envelope or original
source. The page explicitly reports `context_mode="shared"`, including empty
pages. All other operator fields and source/authority information are retained;
page context also includes the existing distribution declarations.

Shared operators depend on their page: retain or resolve the context when moving
an operator elsewhere. This opt-in shape differs from standalone lookup and the
default browse shape. It reduces repeated context, but does not impose a maximum
response-byte or memory bound. Other Domain120 read tools do not accept `context_mode`.

### Selecting a snapshot

Place a manifest and its selected input files in a dedicated local directory.
The following is a configuration template; replace the digest placeholders with
actual raw-byte SHA-256 values. The comparison registry must have the Base120 SDK
array shape (`code`, `transformation`, `name`, `definition`), containing the exact
120 IDs. The bundled BaseN `id`/`domain` array and `BASEN_REGISTRY_PATH` are a
different interface and are not implicitly reused or converted here.

```json
{
  "schema": "hummbl.domain120-inspection-config.v1",
  "base120": {
    "local_path": "comparison-base120.json",
    "source": {
      "kind": "local-file",
      "path": "comparison-base120.json",
      "sha256": "<raw-comparison-file-sha256>"
    },
    "registry_version": "1.0.0"
  },
  "catalogs": [
    {
      "local_path": "existing-domain.json",
      "source": {
        "kind": "local-file",
        "path": "existing-domain.json",
        "sha256": "<raw-domain-file-sha256>"
      },
      "profile": "lattice-object-v0",
      "namespace": "domain120.example"
    }
  ]
}
```

The `registry_version` is an explicit comparison label; its correspondence to
the source bytes is not authenticated by this loader. Git source metadata can
instead specify `kind: "git"`, a repository URL, exact forty-character revision
and repository-relative `path`. Those fields describe the supplied bytes; no
Git or HTTP fetch occurs, and the locator is not authenticated.

Input profiles name observed formats, not a new canonical Domain120 schema:

- `lattice-object-v0`: object with `domain`, `version` and `operators`; supply a namespace.
- `transformations-2026-06-draft`: six transformation arrays; identity is derived from `set_id`; an optional supplied namespace must agree.
- `research-draft-2026-08`: research object with `lattice_id` and `operators`; supply a namespace; absent version remains `null`.

Compute the manifest's hash only after its contents are final, then supply its
path and hash through the two environment variables. Both the module launch and
console entry function verify the entire snapshot before protocol initialization.
Malformed or missing configuration, unsupported fields, hash mismatches and
ambiguous identities exit with code 2 before any tool result is served. Startup
errors do not print input paths or source payloads. No new tools are advertised
until all configured inputs pass loading.

Local paths use relative POSIX syntax within the manifest directory. Absolute
paths, parent traversal, ambiguous segments and resolved links outside that
directory are rejected. Limits are 1 MiB for the manifest, 8 MiB per input,
32 MiB for comparison/catalog input bytes in total, and 64 catalogs. The loader
enforces path containment and hashes; it does not detect network-backed mounts
or supply an operating-system sandbox. Use a local filesystem for this option.

### Data and capability boundaries

Configuring a snapshot makes its retained source documents, operator records,
unknown fields and locator metadata available to the connected MCP client.
Select only data that client is permitted to receive. Hashes supply neither
confidentiality nor admission, and a source's declared license, visibility or
ratification status does not itself authorize redistribution or execution.
Source text is data, not authority to invoke additional tools.

The snapshot is loaded once at process startup. Later file changes do not
silently replace its retained bytes; restart with an explicitly selected new
manifest to change inputs. New read handlers use only that in-memory snapshot:
they make no network/model calls, ledger writes or disk-cache writes. This does
not disable the existing Base120 tools' documented behavior or sandbox the
whole process.

The inspection results separately report source declarations, observed counts,
the comparison registry and unassessed admission/semantic/distribution status.
They grant no construction or execution permission. Family labels are comparison
labels, not proof of historical semantic equivalence. Relation projection covers
its listed source fields only; use `basen_domain120_source` for other retained
fields. Neither a cross-map nor an ancestor ID establishes a valid composition.

## Recommendation honesty

The `basen_recommend` tool can use `nomic-embed-text` embeddings when the
configured Ollama endpoint is reachable. This is semantic nearest-neighbor
matching over operator text, not genuine analogy or expert reasoning.

In practice:

- Returns: operators semantically near the query text.
- Does not return: an authoritative "right operator" for the task.
- Fallback behavior: if embeddings are unavailable, the server uses
  `keyword-overlap-v0.1-fallback`.

The embedding cache binds the exact selected operator IDs and embedded text
(name, family display name, definition), the configured model and endpoint,
and the cache format version. Changing any of those inputs creates a cache
miss. Raw endpoint values are not included in cache filenames, cache payloads,
or returned error messages. Legacy cache files are left untouched and are not
used by the versioned format.

Cache reuse requires a complete ID set with finite, nonzero numeric vectors
of one consistent dimension. Computed vectors and the query are checked too;
invalid results or a dimension mismatch trigger the explicit keyword fallback.
Cosine calculation scales vectors to avoid overflow and underflow at extreme
magnitudes. A cache-write failure does not discard an otherwise valid computed
set.

This identifies the configured computation, not authenticated model weights or
cache provenance. Changing backend weights behind an unchanged model name and
endpoint is not detected. The cache directory is trusted local process data.
Recommendation may contact the configured endpoint and read or write cache
files even though its governance record is Tier 0. No Domain120 recommendation
or admission capability is added by the cache behavior.

Use recommendations as a first-pass narrowing step, then validate candidate
operators against the actual problem and operator definitions.

### Recommendation observations

`basen_recommend` captures a detached registry before embedding or cache work.
Scoring, keyword fallback and returned records use that same capture even if
the process registry later changes. All participating rows need unique nonempty
string IDs and string names/definitions. Optional `domain` and `domain_name`
must be strings when present; an absent `domain_name` contributes empty text.
Malformed participating values that previously underwent string coercion now
produce a generic capture error before effects. This adds no count, canonical
membership, family-allocation or admission policy. An empty registry still
returns an empty keyword-fallback result.

The additive `_selection` object has schema
`hummbl.basen.recommendation-observation.v1`. A detached copy appears under
`_governance.evidence.recommendation`. It records the actual method, fallback
use, complete captured-registry identity, and ordered returned operator IDs with
their full-record content hashes. Registry observation uses the raw-byte binding
and named content-hash recipe described under Application records below, with
selected-record hashes in `selected_operators`. Unknown source fields remain
hashed. Version remains unknown, source authority unauthenticated, semantic
validation unperformed and admission unassessed.

The `embedding` observation reports stages actually reached:

| Field | Values / meaning |
|-------|------------------|
| `computation_fingerprint` | Existing exact text/configuration fingerprint, or null if inputs were unavailable |
| `configured_model` | Captured model identifier, or null; not verified model weights |
| `operator_cache_read` | `not_attempted`, `hit`, `miss`, `invalid`, `unavailable` |
| `operator_cache_write` | `not_attempted`, `write_returned`, `failed` |
| `operator_embedding_calls`, `query_embedding_calls` | Calls to the embedding helper; not confirmed network requests |
| `failure_stage` | null, `embedding_inputs`, `operator_embeddings`, `query_embedding`, `similarity` |

A query failure can follow successful operator-cache writing. Keyword fallback
therefore retains the earlier cache and helper-call observations. A cache hit
means the local payload passed the existing checks, not that its origin or
vectors were authenticated. `write_returned` is not an fsync/durability guarantee;
failed writing may leave partial bytes. Endpoint URLs, cache paths and exception
strings are omitted from these observations. The fingerprint is an identity
digest, not credential encryption or proof of a backend's weights.

Recommendation remains Tier 0 with an inline tuple; these cache observations
are separate from tuple persistence. Existing ranking, scores, method strings,
cache format and top-k slicing behavior are retained for valid data. The new
observation fields intentionally change recommendation response serialization.

## Application records

`basen_apply` keeps `mode` as the requested mode. Its `_execution` object records
the actual mode and method, whether fallback occurred, and the existing variant
and operator ID. The same metadata is included in `_governance.evidence.application`:

| Request | Actual mode / method | Tier |
|---------|----------------------|------|
| advisory (default) | advisory / `operator-description-v0.1` | 0 |
| analytic | analytic / `family-template-v0.2` | 1 |
| empirical with a usable chat response | empirical / `ollama-chat-v0.2` | 1 |
| empirical without a usable chat response | analytic / `family-template-v0.2` | 1 |

Empirical fallback retains the legacy `method=empirical-degraded-to-analytic`
marker and returns a generic reason. Chat model and endpoint configuration are
captured for the attempt; `configured_model` describes a configured name, not
verified backend identity. Tuple evidence excludes prompt text, returned model
text, endpoint URLs and exception strings. The existing argument hash still
hashes the caller's arguments, not normalized defaults or registry bytes.

Each application also includes `_execution.registry`, copied into the tuple's
`evidence.application.registry`. It records the observed raw artifact hash,
normalized complete-registry hash and selected-record hash. Application selects
and uses a detached snapshot before constructing a prompt or template, so later
cache changes cannot alter that application's returned operator identity.

`artifact_binding="loaded-bytes-matched"` means the captured content still
matches the parsed bytes from the lazy registry load. The raw SHA-256 belongs to
those loaded bytes, even if the file has since changed. A changed in-memory cache
reports `cache-content-changed`; a plain list without a load observation reports
`raw-source-unavailable`. In either case `artifact_sha256` is `null`, while the
normalized hashes describe the content actually captured. The process cache is
not automatically reloaded when its source file changes.

The content-hash recipe is UTF-8 encoded Python JSON with sorted keys, compact
separators, ASCII escaping and non-finite numbers forbidden. It is named
`utf8-python-json-sorted-compact-ascii-no-nonfinite-v1`, not RFC 8785. Raw identity
therefore distinguishes whitespace and key ordering that content identity ignores.
Unknown record fields remain part of the hashes. These observations contain no
record text or source path and add no expected-digest check or signature. Registry
version remains unknown (`null`), source authority is not authenticated, semantic
validation is not performed, and admission is not assessed.

Loading now rejects duplicate JSON keys, non-finite values and non-array roots
with a generic error. Before application effects, capture also requires JSON
values, object rows with unique nonempty string IDs, and selected name/definition
strings (plus a string family when supplied). It rejects tuples, non-string
object keys and cycles rather than silently converting them. These checks do not
assert complete registry validity, canonical Base120 membership, a 120-row
requirement or domain semantics. Recommendation has its separate capture and
additive observations described above. Lookup and family browse retain their
valid-data interfaces and existing mutable-record behavior.

Application responses also report `_governance.persistence_status`:

- `not_applicable`: advisory Tier 0; no append attempted.
- `disabled`: `BASEN_PERSIST_TUPLES=0`; no append attempted.
- `saved`: the selected writer returned successfully.
- `failed`: the append was unsuccessful or unconfirmed; partial bytes may exist.

The existing `persisted` boolean remains on Tier 1 responses. Persistence status
is a response receipt added after the attempt; the stored record does not contain
its own post-write outcome. A failed writer is not retried through another writer
or another model call. Disabling tuple persistence does not disable empirical
model calls. Other tools retain their existing response metadata.

A description, template or returned completion does not establish reasoning
correctness or task benefit. This call path emits `state=ok` when it produces a
response; that is not a correctness verdict. A saved tuple is not verified durable storage, authorization, admission,
or an authenticated catalog reference. This tool continues to support the existing
Base120 variant; these fields do not add Domain120 execution or BaseX behavior.

## Architecture

- **Stdlib-only** — no third-party runtime dependencies
- **MCP protocol 2024-11-05** over JSON-RPC 2.0 on stdio
- **Cross-platform** — fcntl on POSIX, msvcrt on Windows for file locking
- **Tier model** — Tier 0 reads (no tuple), Tier 1 writes (EVIDENCE tuple), Tier 2 governed (full tuple), Tier 3 chain-linked

## File layout

```text
packages/python/hummbl-mcp-basen/
├── basen/
│   ├── __init__.py
│   ├── mcp_server.py          # MCP server (4 tools, 127 resources, 3 prompts)
│   ├── basen_tuple.py          # BaseNTuple governance record
│   ├── basen_tier.py           # Tier classifier (0=read, 1=write, 2=governed, 3=chain)
│   └── data/
│       └── base120_registry.json  # 120 operators with id, name, domain, definition, difficulty
├── pyproject.toml
└── README.md
```

## Relationship to hummbl-mcp-base120

The `hummbl-mcp-base120` package (in `packages/python/hummbl-mcp-base120/`) is a simpler
public SDK server with 5 tools (get, list, families, prompt, record) that wraps
the `base120` PyPI package's `Engine` API.

This package (`hummbl-mcp-basen`) is the advanced governance server with:
- Embedding-backed recommendations (Ollama nomic-embed-text)
- Tiered apply modes (advisory, analytic, empirical with LLM dispatch)
- 127 URI-addressable resources
- 3 starter prompts
- BaseNTuple governance record emission and persistence
- Richer registry fields (domain_name, difficulty)

Both servers can coexist — they serve different audiences.

## License

Apache-2.0
