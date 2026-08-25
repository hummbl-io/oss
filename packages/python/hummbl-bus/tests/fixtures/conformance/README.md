# Bus v0.2 conformance corpus

All records are synthetic and contain no production message content.

- `wire-v1.tsv` fixes the byte-level UTF-8/LF five-column contract, including
  plain text, Unicode, escaped controls, and a legacy signed envelope.
- `hmac-v1.json` fixes the shared HMAC-SHA256 canonicalization contract.
- `historical-read-v1.tsv` represents compatibility classes observed in the
  live corpus: offset timestamps and the legacy `host` envelope extension.
- `structured-events-v1.json` is prospective dual-read coverage for both
  existing schema IDs; neither schema was prevalent in the measured corpus.
- `malformed-wire-v1.tsv` contains deliberately invalid column counts.

These fixtures are immutable compatibility inputs. Add a new versioned fixture
instead of silently rewriting an established contract.
