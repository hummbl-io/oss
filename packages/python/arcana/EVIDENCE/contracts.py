"""Contracts for the EVIDENCE sibling module."""

MODULE_NAME = "EVIDENCE"
MODULE_SURFACE = "EVIDENCE"
MODULE_VERSION = "v0.1"
MODULE_STATUS = "AUTHORIZED"
MODULE_PURPOSE = "Capture, retain, and audit evidence from generation and scoring."
MODULE_BOUNDARY = (
    "EVIDENCE owns telemetry and quality records only; it does not alter "
    "content generation or release gate decisions."
)
MODULE_CONTRACT_TERMS = (
    "quality-telemetry",
    "drift-detection",
    "audit-packaging",
)
