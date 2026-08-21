# Receipts

Status: public boundary
Last updated: 2026-07-03

Receipts are durable evidence for public claims, changes, reviews, and
promotion decisions.

## Receipt Types

Useful receipt types include:

- command output;
- CI run URL;
- commit SHA;
- release tag;
- PyPI release page;
- package build artifact;
- test summary;
- source URL and verification date;
- security scan result;
- link check result;
- public/private boundary review;
- issue or PR review;
- operator approval.

## Minimum Receipt Fields

Each receipt should preserve:

- subject;
- date;
- source;
- command or URL;
- artifact path or commit SHA;
- result;
- limitations;
- reviewer or author;
- next action when incomplete.

## Public Claim Receipts

Public claims must be backed by receipts or explicitly marked as planned,
draft, pending, or removed.

Claims that depend on private systems, other repos, production usage, security
posture, compliance posture, or benchmark comparisons need especially careful
receipts.

## What Receipts Are Not

Receipts are not marketing language. They do not create certification,
attestation, warranty, support, uptime, or compliance commitments unless a
separate written agreement says so.
