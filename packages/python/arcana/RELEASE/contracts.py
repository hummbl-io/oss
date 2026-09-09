"""Contracts for the RELEASE sibling module."""

MODULE_NAME = "RELEASE"
MODULE_SURFACE = "RELEASE"
MODULE_VERSION = "v0.1"
MODULE_STATUS = "AUTHORIZED"
MODULE_PURPOSE = "Governed rollout and publication gate control."
MODULE_BOUNDARY = (
    "RELEASE manages outbound distribution permissions and receipts; it does not "
    "perform content synthesis."
)
MODULE_CONTRACT_TERMS = (
    "pre-release-gates",
    "publication-receipts",
    "rollback-conditions",
)
