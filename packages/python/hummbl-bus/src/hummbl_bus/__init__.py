"""hummbl-bus: Secure append-only TSV coordination bus.

Extracted from founder-mode/founder_mode/bus/.

Provides TSV-based message bus with injection protection through
base64 encoding of payloads.

Canonical write path: ``post_message()`` (re-exported from bus_writer).
Security policy: ``get_bus_policy()`` (configurable via BUS_SECURITY_POLICY env).
Integrity audit: ``audit_bus()`` (read-only bus scanner).
"""

from importlib import import_module

from .bus_policy import BusSecurityPolicy, get_bus_policy
from .secure_tsv import (
    BusMessage,
    SecureTSVDecoder,
    SecureTSVEncoder,
    TSVInjectionError,
)

_LAZY_BUS_VERIFIER_EXPORTS = {
    "BusAuditReport",
    "audit_bus",
}

_LAZY_BUS_WRITER_EXPORTS = {
    "harden_bus_file_permissions",
    "is_signed_message",
    "post_message",
    "read_verified_messages",
    "verify_bus_message",
}

_LAZY_BUS_TRANSLATE_EXPORTS = {
    "compress_message",
    "format_entry",
    "read_tail",
}


def __getattr__(name: str):
    if name in _LAZY_BUS_VERIFIER_EXPORTS:
        module = import_module(".bus_verifier", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_BUS_WRITER_EXPORTS:
        module = import_module(".bus_writer", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_BUS_TRANSLATE_EXPORTS:
        module = import_module(".bus_translate", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BusAuditReport",
    "BusMessage",
    "BusSecurityPolicy",
    "SecureTSVDecoder",
    "SecureTSVEncoder",
    "TSVInjectionError",
    "audit_bus",
    "compress_message",
    "format_entry",
    "get_bus_policy",
    "harden_bus_file_permissions",
    "is_signed_message",
    "post_message",
    "read_tail",
    "read_verified_messages",
    "verify_bus_message",
]
