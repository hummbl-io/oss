"""Caveman-ponytail translator for bus messages.

Reads bus tail, compresses each message prose caveman-ponytail style:
drop articles, filler, hedging, pleasantries. Keep technical identifiers
(correlation_id, host=, machine=, paths, code, agent names, message types).

Stdlib-only. Read-only. Never writes to bus.

CLI:
    python -m hummbl_bus.bus_translate [N] [--bus PATH] [--raw]
    hummbl-bus-translate [N] [--bus PATH] [--raw]

N = number of tail entries (default 20). --raw = skip compression, print verbatim.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DEFAULT_BUS_PATH = "_state/coordination/messages.tsv"
DEFAULT_TAIL = 20

# Words to drop entirely (word-boundary, case-insensitive).
# Articles, filler, hedging, pleasantries. Never drop technical terms.
_DROP_WORDS = {
    # articles
    "a", "an", "the",
    # filler
    "just", "really", "basically", "actually", "simply", "literally",
    "quite", "rather", "somewhat", "fairly", "pretty",
    # pleasantries
    "please", "kindly", "sure", "certainly", "obviously", "of course",
    "happy to", "glad to", "unfortunately", "luckily",
    # hedging
    "maybe", "perhaps", "possibly", "probably", "apparently",
    "seemingly", "allegedly", "supposedly",
}

# Phrases to drop (multi-word, applied before single-word pass).
_DROP_PHRASES = [
    r"\bI think\b",
    r"\bI believe\b",
    r"\bI feel\b",
    r"\bI guess\b",
    r"\bit seems\b",
    r"\bit appears\b",
    r"\bit looks like\b",
    r"\bthere seems\b",
    r"\bthere appears\b",
    r"\bgoing to\b",
    r"\bgoing ahead\b",
    r"\bin order to\b",
    r"\bso as to\b",
    r"\bas well\b",
    r"\bright now\b",
    r"\bat this point\b",
    r"\bat this time\b",
    r"\bfor now\b",
    r"\bfor the time being\b",
    r"\bneed to\b",
    r"\bwant to\b",
    r"\bgoing forward\b",
    r"\bthat said\b",
    r"\bwith that said\b",
    r"\bthat being said\b",
    r"\bneedless to say\b",
    r"\bit should be noted\b",
    r"\bit is worth noting\b",
    r"\bfor what it['']?s worth\b",
    r"\bby the way\b",
    r"\bin terms of\b",
    r"\bwhen it comes to\b",
    r"\bthe fact that\b",
    r"\bdue to the fact\b",
    r"\bin light of\b",
    r"\bon the other hand\b",
    r"\bon one hand\b",
    r"\bthat having been said\b",
]

# Contraction expansions (normalize before drop pass).
_CONTRACTIONS = {
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "won't": "will not",
    "can't": "cannot",
    "couldn't": "could not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
    "it's": "it is",
    "that's": "that is",
    "there's": "there is",
    "here's": "here is",
    "we're": "we are",
    "they're": "they are",
    "you're": "you are",
    "we've": "we have",
    "they've": "they have",
    "you've": "you have",
    "we'll": "we will",
    "they'll": "they will",
    "you'll": "you will",
    "we'd": "we would",
    "they'd": "they would",
    "you'd": "you would",
    "i'm": "I am",
    "i've": "I have",
    "i'll": "I will",
    "i'd": "I would",
}

_PHRASE_RE = re.compile("|".join(_DROP_PHRASES), re.IGNORECASE)
_WORD_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in _DROP_WORDS if " " not in w) + r")\b", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def _expand_contractions(text: str) -> str:
    """Expand contractions to full form. Case-insensitive on lowercase ones."""
    for contraction, expansion in _CONTRACTIONS.items():
        text = re.sub(re.escape(contraction), expansion, text, flags=re.IGNORECASE)
    return text


def compress_message(text: str) -> str:
    """Compress a single bus message prose caveman-ponytail style.

    Drops articles, filler, hedging, pleasantries. Keeps technical
    identifiers (paths, correlation_id, host=, code, agent names, types).
    Fragments OK. Never drops content inside backticks, quotes, brackets,
    or key=value tokens.

    Args:
        text: Raw message body.

    Returns:
        Compressed message string. Empty input returns empty string.
    """
    if not text or not text.strip():
        return ""

    # Escape any literal null bytes in input so they cannot collide with
    # placeholder markers. Restored at the end.
    text = text.replace("\x00", "\x01NULL\x01")

    # Protect technical tokens: key=value, paths, code in backticks, quoted strings.
    # Replace with placeholders, compress prose, restore.
    placeholders: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"\x00{len(placeholders) - 1}\x00"

    # Protect backtick code spans.
    protected = re.sub(r"`[^`]*`", _stash, text)
    # Protect key=value tokens (host=delta, correlation_id=foo, machine=anvil).
    protected = re.sub(r"\b[\w.-]+=[^\s,)]+", _stash, protected)
    # Protect paths (forward and backward slash, with extensions or dirs).
    protected = re.sub(r"[A-Za-z]:[\\/][\w\\/.-]+", _stash, protected)
    protected = re.sub(r"(?<![A-Za-z:])/(?:[\w.-]+/)+[\w.-]*", _stash, protected)
    # Protect double-quoted strings.
    protected = re.sub(r'"[^"]*"', _stash, protected)
    # Protect bracketed tokens [skill=...], [mode=...].
    protected = re.sub(r"\[[^\]]*\]", _stash, protected)
    # Protect parenthetical citations (BIS 90 FR 4617, PR #1234, §14).
    protected = re.sub(r"\([^)]*\)", _stash, protected)
    # Protect standalone §references and PR/issue numbers.
    protected = re.sub(r"§[\w.-]+", _stash, protected)
    protected = re.sub(r"\bPR #\d+\b", _stash, protected, flags=re.IGNORECASE)
    protected = re.sub(r"\bissue #\d+\b", _stash, protected, flags=re.IGNORECASE)

    # Expand contractions.
    protected = _expand_contractions(protected)

    # Drop phrases first (multi-word).
    protected = _PHRASE_RE.sub("", protected)

    # Drop single words.
    protected = _WORD_RE.sub("", protected)

    # Collapse whitespace.
    protected = _WS_RE.sub(" ", protected).strip()

    # Strip leading punctuation left by drops (e.g., ", " at start).
    protected = re.sub(r"^[\s,;:]+", "", protected).strip()

    # Restore placeholders. Bounds-checked to avoid IndexError on
    # stray null-surrounded digits in input (shouldn't happen after
    # escaping, but defensive).
    def _restore(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        if 0 <= idx < len(placeholders):
            return placeholders[idx]
        return match.group(0)

    protected = re.sub(r"\x00(\d+)\x00", _restore, protected)

    # Final whitespace collapse after restore.
    protected = _WS_RE.sub(" ", protected).strip()
    # Restore escaped null bytes.
    protected = protected.replace("\x01NULL\x01", "\x00")
    return protected


def read_tail(bus_path: str | Path, n: int = DEFAULT_TAIL) -> list[dict[str, str]]:
    """Read last N bus entries. Read-only.

    Args:
        bus_path: Path to messages.tsv.
        n: Number of tail entries to return.

    Returns:
        List of dicts: timestamp, from, to, type, message.
        Empty list if file missing or unreadable.
    """
    path = Path(bus_path)
    if not path.exists():
        return []

    entries: list[dict[str, str]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []

    # Guard against N<=0: lines[-0:] returns entire list (Python slicing
    # quirk). Negative N is nonsensical for tail. Return empty.
    if n <= 0:
        return []

    for line in lines[-n:]:
        line = line.rstrip("\n\r")
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        ts, from_id, to_id, msg_type, message = parts
        entries.append(
            {
                "timestamp": ts,
                "from": from_id,
                "to": to_id,
                "type": msg_type,
                "message": message,
            }
        )
    return entries


def format_entry(entry: dict[str, str], compressed: bool = True) -> str:
    """Format a bus entry for display.

    Args:
        entry: Dict from read_tail.
        compressed: If True, compress message prose. If False, verbatim.

    Returns:
        Single-line formatted string. Tabs/newlines in message replaced
        with spaces to prevent TSV injection in downstream piping.
    """
    msg = compress_message(entry["message"]) if compressed else entry["message"]
    # Sanitize: no tabs or newlines in message column (TSV injection prevention).
    msg = msg.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    return f"{entry['timestamp']}\t{entry['from']}\t{entry['to']}\t{entry['type']}\t{msg}"


def _resolve_bus_path(override: str | None) -> Path:
    if override:
        return Path(override)
    env = Path(DEFAULT_BUS_PATH)
    if env.exists():
        return env
    # Fallback: common locations on Delta/Anvil.
    candidates = [
        Path.home() / "Projects" / "founder-mode" / "_state" / "coordination" / "messages.tsv",
        Path("C:/FM/founder-mode/founder_model/_state/coordination/messages.tsv"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return env


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for caveman-ponytail bus translation.

    Usage:
        python -m hummbl_bus.bus_translate [N] [--bus PATH] [--raw]

    Args:
        N: Number of tail entries (default 20).
        --bus PATH: Override bus file path.
        --raw: Skip compression, print verbatim entries.

    Returns:
        0 on success, 1 on read error, 2 on usage error.
    """
    args = argv if argv is not None else sys.argv[1:]

    bus_override: str | None = None
    raw = False
    n = DEFAULT_TAIL

    positional: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--bus" and i + 1 < len(args):
            bus_override = args[i + 1]
            i += 2
        elif args[i] == "--raw":
            raw = True
            i += 1
        elif args[i].lstrip("-").isdigit() and not args[i].startswith("--"):
            positional.append(args[i])
            i += 1
        elif args[i] == "--help" or args[i] == "-h":
            print(
                "Usage: hummbl-bus-translate [N] [--bus PATH] [--raw]\n"
                "  N       tail entry count (default 20)\n"
                "  --bus   override bus file path\n"
                "  --raw   skip compression, print verbatim",
                file=sys.stderr,
            )
            return 0
        else:
            print(f"Unknown argument: {args[i]}", file=sys.stderr)
            return 2

    if positional:
        try:
            n = int(positional[0])
        except ValueError:
            print(f"ERROR: N must be integer, got {positional[0]!r}", file=sys.stderr)
            return 2

    bus_path = _resolve_bus_path(bus_override)
    entries = read_tail(bus_path, n)

    if not entries:
        print(f"(no entries in {bus_path})", file=sys.stderr)
        return 1

    for entry in entries:
        print(format_entry(entry, compressed=not raw))

    return 0


if __name__ == "__main__":
    sys.exit(main())
