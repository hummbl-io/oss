PYTHON ?= python3

.PHONY: validate validate-basen validate-experiments test simulate test-simulation ci-local check-case-collisions check-pr-claims check-duplicate-prs

validate:
	$(PYTHON) reference_impl/validate_examples.py
	$(PYTHON) novelty_quest/experiments/behavior_spec_candidate_phase0/scripts/validate_candidate_specs.py
	$(PYTHON) novelty_quest/experiments/agent_skill_behaviorspec_phase0/scripts/validate_agent_skill_specs.py

## ci-local: run all checks that CI will run, locally before pushing.
## Includes schema/example validation, case-collision guard, and tests.
ci-local: validate check-case-collisions
	$(PYTHON) -m pytest tests/ -v

## check-case-collisions: detect tracked paths that differ only by letter case.
## Prevents silent Windows/macOS divergence that breaks Linux CI.
check-case-collisions:
	$(PYTHON) scripts/check_case_collisions.py --strict

## check-pr-claims: verify file references in a PR body exist in the repo.
## Usage: gh pr view <N> --json body --jq '.body' | make check-pr-claims
check-pr-claims:
	$(PYTHON) scripts/check_pr_body_claims.py

## check-duplicate-prs: detect open PRs that duplicate the same issue.
check-duplicate-prs:
	$(PYTHON) scripts/detect_duplicate_prs.py

validate-experiments:
	$(PYTHON) novelty_quest/experiments/behavior_spec_candidate_phase0/scripts/validate_candidate_specs.py
	$(PYTHON) novelty_quest/experiments/agent_skill_behaviorspec_phase0/scripts/validate_agent_skill_specs.py

validate-basen:
	@echo "Usage: make validate-basen CORPUS=path/to/corpus.jsonl"
	@test -n "$(CORPUS)" || (echo "CORPUS is required" && exit 1)
	$(PYTHON) reference_impl/validate_basen_corpus.py "$(CORPUS)"

test:
	$(PYTHON) -m pytest tests/ -v

simulate:
	$(PYTHON) -m hummbl_tuples.simulation --summary

test-simulation:
	$(PYTHON) -m pytest tests/test_simulation.py -v
