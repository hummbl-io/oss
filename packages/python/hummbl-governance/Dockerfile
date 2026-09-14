# Multi-stage Dockerfile for hummbl-governance CI reproduction
#
# Usage:
#   docker build -t hummbl-governance-ci packages/python/hummbl-governance/
#   docker run hummbl-governance-ci
#
# Reproduces the oss monorepo CI test suite for hummbl-governance locally.
# Zero runtime dependencies (stdlib only); test extras: pytest, pytest-cov,
# ruff, cryptography, build.

# ---- Builder: install test deps into a venv ----
FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml .

# Create venv and install test deps (cryptography ships wheels, no gcc needed)
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir ".[test]"

# ---- Runtime: venv + source, no build tools ----
FROM python:3.13-slim

WORKDIR /app

# ca-certificates for HTTPS; git for tests that init temp repos
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Copy source (filtered by .dockerignore)
COPY . .

# Install package in editable mode (uses venv deps, links to /app source)
RUN pip install -e . --no-deps --no-cache-dir

# Run as non-root so file permission tests (chmod 0o444) behave correctly
RUN useradd -m -u 1000 ci && chown -R ci:ci /app /venv
USER ci

CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=hummbl_governance", "--cov-report=term", "--cov-fail-under=80"]
