#!/usr/bin/env python3
"""Check that v40.02r02 target fields do not leak into raw D.E.C. rows."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual-2" / "data"
FORBIDDEN_RAW_TOKENS = {
    "pubchem", "rdkit", "uniprot", "pdb", "alphafold",
    "rna", "dna", "protein", "fold", "contact_map", "distance_matrix",
}


def header_tokens(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])
    return {h.lower() for h in header}


def main() -> int:
    for path in DATA.rglob("raw_dec_trace*.csv"):
        bad = {tok for tok in FORBIDDEN_RAW_TOKENS for h in header_tokens(path) if tok in h}
        if bad:
            raise ValueError(f"target leakage tokens {sorted(bad)} in raw D.E.C. header {path}")
    guard = DATA / "protein" / "protein_target_leakage_guard.csv"
    if not guard.exists():
        raise FileNotFoundError(guard)
    with guard.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or {r["guard_status"] for r in rows} != {"active"}:
        raise ValueError("protein leakage guard rows must be active")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
