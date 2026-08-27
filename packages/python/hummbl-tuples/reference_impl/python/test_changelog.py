"""Test the changelog system."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from changelog import Changelog, generate, lattice_init, link, promote

# Create a temp changelog
tmpdir = tempfile.mkdtemp()
cl_path = Path(tmpdir) / "test_changelog.jsonl"

cl = Changelog(cl_path)

# Lattice init
cl.append(lattice_init("Domain120:Architecture", "devin", "P05", ["scale", "function", "material"]))

# Generate 2 operators
cl.append(
    generate(
        "Domain120:Architecture",
        "op-001",
        "devin",
        "DE",
        "Factorize Load Path",
        "Decompose structural system into load paths",
    )
)
cl.append(
    generate(
        "Domain120:Architecture",
        "op-002",
        "devin",
        "IN",
        "Invert Seismic Assumption",
        "Reverse assumed load direction for seismic check",
    )
)

# Promote op-001
cl.append(promote("Domain120:Architecture", "op-001", "devin", "Candidate", "Curated"))

# Link op-001 to op-002
cl.append(link("Domain120:Architecture", "op-001", "op-002", "Domain120:Architecture", "devin"))

# Check version
print(f"Entries: {len(cl)}")
print(f"Version: {cl.version_string()}")
print(f"Last hash: {cl.last_hash[:16]}...")
print(f"Chain valid: {cl.verify_chain()}")

# Reload and verify
cl2 = Changelog(cl_path)
print(f"\nAfter reload: {len(cl2)} entries")
print(f"Version after reload: {cl2.version_string()}")
print(f"Chain valid after reload: {cl2.verify_chain()}")

# Show entries
print("\nEntries:")
for e in cl2.entries():
    op_id = e.operator_id or "(lattice)"
    print(f"  {e.operation:20s} {op_id:12s} hash={e.content_hash()[:12]}")

# Show canonical JSON of first entry
first = cl2.entries().__next__()
print("\nFirst entry canonical JSON:")
print(f"  {first.to_canonical_json()[:120]}...")

# Show the JSONL file content
print(f"\nJSONL file ({cl_path}):")
with open(cl_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        print(f"  line {i}: {line.strip()[:100]}...")

print("\nAll tests passed!")
