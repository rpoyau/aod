#!/usr/bin/env python3
"""Validate v40.02r02 target-packet scaffold integrity."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual-2" / "data"
REQUIRED = {
    "target_packet_id", "lane", "source", "source_accession",
    "source_release_or_snapshot", "source_record_url_or_path",
    "acquisition_utc", "raw_sha256", "normalized_sha256",
    "normalizer_script", "normalizer_version", "license_or_terms_ref",
    "target_status", "leakage_role", "release_status",
}

FILES = [
    DATA / "molecular" / "pubchem_compound_target_packets.csv",
    DATA / "protein" / "uniprot_target_packets.csv",
    DATA / "protein" / "pdb_structure_target_packets.csv",
    DATA / "protein" / "alphafold_structure_target_packets.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    for path in FILES:
        if not path.exists():
            raise FileNotFoundError(path)
        data = rows(path)
        if not data:
            raise ValueError(f"empty target-packet file: {path}")
        missing = REQUIRED - set(data[0])
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        ids = [r["target_packet_id"] for r in data]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate target_packet_id in {path}")
        for row in data:
            if row["leakage_role"] not in {"target_only", "comparison_only", "allowed_input"}:
                raise ValueError(f"invalid leakage_role in {path}: {row}")
            if not row["raw_sha256"] or not row["normalized_sha256"]:
                raise ValueError(f"missing checksum in {path}: {row}")
    json.loads((DATA / "molecular" / "molecular_target_manifest.json").read_text(encoding="utf-8"))
    json.loads((DATA / "protein" / "protein_target_manifest.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
