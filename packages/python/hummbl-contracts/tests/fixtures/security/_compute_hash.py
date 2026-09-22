"""Throwaway helper: prints the config_sha256 for agent-lock.example.json.

JCS (RFC 8785) canonicalization for this document (ASCII strings, integers,
and floats only) reduces to sorted keys + compact separators, so stdlib
json.dumps suffices. Delete after use or keep for fixture regeneration.
"""
import hashlib
import json
from pathlib import Path

p = Path(__file__).with_name("agent-lock.example.json")
doc = json.loads(p.read_text())
doc.pop("provenance")
canon = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
print(hashlib.sha256(canon.encode()).hexdigest())
