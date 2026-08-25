# Public Intelligence Source Receipts

Status: candidate registry support for hummbl-production#565.

This directory stores source receipts referenced by
`docs/research/public-intelligence/sources.registry.yaml`.

Receipt rules:

- Record source URL, retrieval date, authority claim, and access-mode notes.
- Do not record credentials, bearer strings, passwords, tokens, cookies, or
  account-specific headers.
- Treat video, newsletter, social, and blog leads as lead-only until an
  official source or primary authority is linked.
- Keep bulk ingestion blocked unless storage, license, privacy, rate-limit,
  and cost gates are all present and passing.
