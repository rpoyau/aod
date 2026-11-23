"""Module entry point for ``python3 -B [-O] -m manual.engine``."""
from __future__ import annotations

from manual.engine.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
