"""Package entrypoint shim for `python -m pipeline.cli`."""

from __future__ import annotations

from cli import main  # type: ignore


def _main() -> None:
    main()


if __name__ == "__main__":
    _main()
