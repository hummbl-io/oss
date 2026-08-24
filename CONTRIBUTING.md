# Contributing to hummbl-io/oss

This monorepo publishes HUMMBL packages to public registries (PyPI, npm,
crates.io, Go proxy, Maven Central, Nix, arXiv/Zenodo). Public visibility
raises the stakes on two things: workflow correctness (broken CI blocks
every release) and inventory accuracy (false ownership claims confuse
users and can look like name-squatting). This document covers both.

For the full monorepo architecture, directory structure, and per-language
publishing workflows, see [`docs/MONOREPO-DESIGN.md`](./docs/MONOREPO-DESIGN.md).
For the package inventory, see [`docs/PACKAGES.md`](./docs/PACKAGES.md).

---

## 1. Workflow authoring rules

**These rules are mandatory on this repo.** They were learned from debugging
4 consecutive `startup_failure` runs during the `hummbl-governance` 1.4.1
publish (2026-08-21). Ignore them and the workflow fails before any job
starts -- with no logs.

### 1.1 SHA-pin every action

The repo has `sha_pinning_required: true` (verify:
`gh api repos/hummbl-io/oss/actions/permissions`). Tag refs (`@v4`, `@v5`,
`@stable`, `@main`) cause `startup_failure`. Always pin to the full 40-char
commit SHA:

```yaml
# WRONG -- will fail with startup_failure
- uses: actions/checkout@v4

# RIGHT
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
```

Resolve a tag to its SHA:

```bash
gh api repos/<owner>/<repo>/commits/<tag> --jq '.sha'
```

### 1.2 ASCII only

No em-dashes, smart quotes, or non-ASCII characters anywhere in
`.github/workflows/*.yml` -- including comments. Use `--` and straight
quotes. A single em-dash (`\u2014`) in a comment caused a `startup_failure`
on this repo.

### 1.3 LF line endings

CRLF causes `startup_failure`. The repo's `.gitattributes` enforces LF on
workflow YAML. If you edit workflows on Windows, ensure your editor writes
LF, not CRLF.

### 1.4 Create environments before referencing them

GitHub Actions fails at startup if a job references an environment that
doesn't exist. Create each environment first:

```bash
gh api repos/hummbl-io/oss/environments/<name> -X PUT
```

Existing environments on this repo: `pypi` (created 2026-08-21). Create
`npm`, `crates`, `maven`, `nix` before their first publish workflow runs.

### 1.5 Quote the `on:` key

YAML 1.1 treats `on` as a boolean. Write `"on":` (quoted) to avoid parse
ambiguity:

```yaml
# WRONG -- may parse as boolean
on:
  push:
    tags: ["python/*/v*"]

# RIGHT
"on":
  push:
    tags: ["python/*/v*"]
```

### 1.6 Reference

Full workflow examples for all 8 registries (with SHA-pinned actions) are
in [`docs/MONOREPO-DESIGN.md`](./docs/MONOREPO-DESIGN.md) section 4.

---

## 2. Registry inventory verification protocol

**Any "live" claim in `docs/PACKAGES.md` MUST be backed by verification of
the `author`, `repository`, and `maintainers` fields on the registry.**
Name-existence-on-registry is NOT proof of ownership.

### 2.1 Why this rule exists

In the initial PACKAGES.md (2026-08-21), 11 of 20 "live" packages were
**name collisions** -- unrelated packages by other authors that happened to
share common-word names. The inventory author looked up package names on
PyPI and npm, found packages with those names, and assumed they were
HUMMBL's without checking the author/repository/maintainers fields.

| Name | Claimed as HUMMBL's | Actual owner |
|------|---------------------|--------------|
| `arbiter` (PyPI) | Yes | R.A. Stern (`rastern/arbiter`) |
| `arcana` (PyPI) | Yes | `arcana.readthedocs.io` |
| `crab` (PyPI) | Yes | Graham Bell (`grahambell/crab`) |
| `randy` (PyPI) | Yes | Francis Horsman (Bitbucket `sys-git/randy`) |
| `hermes-agent` (PyPI) | Yes | Nous Research |
| `mcp-server` (npm) | Yes | Melvin Carvalho (`sandy-mount/mcp-server`) |
| `hermes-agent` (npm) | Yes | `wrtensi/hermes-agent-npm` |
| `arbiter` (npm) | Yes | skbolton (`skbolton/Arbiter`) |
| `arcana` (npm) | Yes | flipactual (`flipactual/arcana`) |
| `crab` (npm) | Yes | kossnocorp (`kossnocorp/crab`) |
| `randy` (npm) | Yes | deestan (`deestan/randy`) |

All 11 were unprefixed common-word names. HUMMBL's actual packages use the
`hummbl-*` prefix on PyPI and the `@hummbl/*` scope on npm, which avoids
this collision class.

### 2.2 Verification commands

Before adding a package to any "Live" table in PACKAGES.md, run the
registry lookup and record the author/repository/maintainers:

**PyPI:**
```powershell
$r = Invoke-WebRequest "https://pypi.org/pypi/<name>/json"
$j = $r.Content | ConvertFrom-Json
$j.info.author           # author field
$j.info.project_urls     # Repository, Homepage, Issues
```

**npm:**
```powershell
$r = Invoke-WebRequest "https://registry.npmjs.org/<name>"
$j = $r.Content | ConvertFrom-Json
$j.maintainers           # maintainer names
$j.versions.($j.'dist-tags'.latest).repository  # repository URL
```

For scoped npm packages, URL-encode the slash: `@hummbl%2Fmcp-server`.

### 2.3 PACKAGES.md "Live" table format

Every "Live" table must include an "Ownership verified" column that
records the verification date and method (e.g. "2026-08-21 (naming + repo
match)" or "2026-08-21 (operator-confirmed)"). Do not add a package to a
"Live" table without having run the registry lookup and confirmed the
author/repository/maintainers fields match HUMMBL.

### 2.4 Collision-prone names

Common-word package names (e.g. `arbiter`, `crab`, `randy`, `arcana`,
`mcp-server`, `hermes-agent`) are inherently collision-prone. If a HUMMBL
package uses an unprefixed common-word name, verify extra carefully and
consider whether the package should be renamed to `hummbl-*` (PyPI) or
`@hummbl/*` (npm) to avoid future confusion.

---

## 3. PII and redaction

This is a **public** repo. Before pushing anything, scan for:

- Internal host paths: `PROJECTS/`, `hosts/<fleet-node>`,
  `C:\Users`, `/opt/<org>`
- Machine names in path context: `<fleet-node-1>`, `<fleet-node-2>`,
  `<fleet-vps>`, `<fleet-gateway>` (machine names as **public** GitHub
  repo names are fine -- they're already public; **private** repo names
  are still internal and must not be enumerated in public docs)
- Private repo names with sensitive descriptions (e.g. "vault / Secrets",
  "meeting-archive / Private transcripts") -- do not publish categorized
  inventories of non-public infrastructure
- Operator personal name
- 1Password item IDs (format: `id=<20-char alphanumeric>`)
- Tailscale topology details
- Bus URLs and internal service paths

**Scan scope: every file in the PR diff, not just the primary artifact.**
Docs, configs, and inventory files can contain internal paths even when
the primary artifact is clean. Enumerate files with:

```bash
git diff --name-only main...<branch>
```

Scan each file, not just the ones you authored.

### 3.1 False-positive patterns

The following are NOT PII and should not block a publish:
- Common words that overlap with internal codenames (e.g. a Greek
  letter used as a mathematical variable, not a machine name)
- Common English words used as idioms (e.g. "clean slate")
- `OPENAI_API_KEY=os.getenv(...)` calls (env var references, not hardcoded
  secrets)
- Placeholder webhook URLs (`hooks.slack.com/services/T/B/X` patterns)
- Test fixture secrets (`my-secret-key`, `shared-key`, `sk-abcdefgh`)
- `private key` regex patterns in detection code (not actual keys)

---

## 4. Migration from private repos

When migrating a package from a private `hummbl-io/*` repo into this
public monorepo, use a **clean snapshot (no git history)** with a PII scan
before copy. Private repo git history may contain hostnames, internal
paths, credentials, or personal data that must not enter the public
monorepo.

Never `git mv` from a private repo into this public monorepo without
scanning the full history for PII first. `git mv` is only safe for packages
already in a public repo.

See [`docs/MONOREPO-DESIGN.md`](./docs/MONOREPO-DESIGN.md) section 1 for
the full migration method.

---

## 5. Package deprecation policy (Revival Hijack defense)

**Never delete a published package from PyPI, npm, or crates.io.**

When a PyPI maintainer deletes a project, the package name immediately
becomes re-registerable. An attacker can register the same name and
publish a malicious version -- any existing user who runs
`pip install <name>` or has it in a `requirements.txt` without a pinned
version will receive the malicious package. JFrog (2024) identified
**22,000 PyPI packages** vulnerable to this "Revival Hijack" attack
class. npm and crates.io have analogous risks.

**To deprecate a HUMMBL package:**

1. **Yank specific versions** (`pip download <name>==<version>` no longer
   finds it, but `pip install <name>==<version>` still works for users
   who pinned it) -- do NOT delete the project
2. **Publish a final empty/deprecated release** with a deprecation notice
   in the description and README
3. **Keep the project owned by `hummbl-io`** to prevent name re-registration
4. **Document the deprecation** in `docs/PACKAGES.md` with the date and
   reason

This policy applies to PyPI, npm, and crates.io. Maven Central is fully
immutable (no deletion possible). Go module proxy tags are immutable once
pushed (delete the tag in git, but the proxy caches the version forever).

---

## 6. License

All packages in this monorepo are Apache-2.0. See [`LICENSE`](./LICENSE).
