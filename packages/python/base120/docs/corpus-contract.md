# Base120 Golden Corpus Contract

The files in `tests/corpus` define the authoritative behavior of Base120
contract artifact validation. Any implementation is correct **if and only if**
it produces byte-for-byte identical error outputs for all corpus inputs.

## Canonical Path

The executable corpus lives in this repository under:

- `tests/corpus/valid/*.json` - artifacts that MUST produce `[]`
- `tests/corpus/invalid/*.json` - artifacts that MUST produce the matching
  expected errors
- `tests/corpus/expected/*.errs.json` - byte-for-byte expected error arrays for
  invalid artifacts

The current Python package is registry-focused, so CI validates the corpus
directory contract with `tests/test_corpus_contract.py`: JSON parseability,
non-empty valid/invalid sets, and one expected-error manifest per invalid
artifact. Full artifact-validator mirrors MUST still use the expected-error
arrays as the behavioral source of truth.
