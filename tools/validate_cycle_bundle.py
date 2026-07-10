#!/usr/bin/env python3
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_complete_bundle import main
if __name__ == '__main__':
    raise SystemExit(main())
