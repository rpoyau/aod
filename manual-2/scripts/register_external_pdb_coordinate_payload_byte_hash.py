#!/usr/bin/env python3
"""Register an external PDB coordinate byte-payload SHA-256 from a local file.

This utility is intentionally offline. It does not download PDB/mmCIF data and
it does not derive residue or contact rows. It only hashes a caller-supplied
coordinate byte payload and emits a registration row suitable for a later gate.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import sys

DEFAULT_URI = "https://files.rcsb.org/download/1CRN.cif"
FIELDS = [
    "byte_hash_registration_id",
    "source_database",
    "source_accession",
    "chain_id",
    "coordinate_payload_path",
    "local_payload_path",
    "coordinate_payload_sha256",
    "coordinate_payload_byte_count",
    "coordinate_payload_storage_policy",
    "coordinate_payload_license_or_terms_ref",
    "registration_status",
    "derivation_status_after_registration",
]


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def write_row(path: Path | None, row: dict[str, str]) -> None:
    if path is None:
        w = csv.DictWriter(sys.stdout, fieldnames=FIELDS)
        w.writeheader()
        w.writerow(row)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True, help="local coordinate byte-payload path, e.g. a downloaded 1CRN.cif")
    ap.add_argument("--out", help="optional CSV output path; defaults to stdout")
    ap.add_argument("--source-database", default="RCSB_PDB")
    ap.add_argument("--source-accession", default="1CRN")
    ap.add_argument("--chain-id", default="A")
    ap.add_argument("--coordinate-payload-path", default=DEFAULT_URI)
    ap.add_argument("--storage-policy", default="external_payload_hash_registered_bytes_not_redistributed_by_default")
    ap.add_argument("--terms-ref", default="RCSB_PDB_terms_coordinate_payload")
    args = ap.parse_args()

    payload = Path(args.payload)
    if not payload.is_file():
        raise FileNotFoundError(f"coordinate payload not found: {payload}")
    digest, size = sha256_file(payload)
    row = {
        "byte_hash_registration_id": f"pdb_external_coordinate_payload_byte_hash_{args.source_accession}_{args.chain_id}",
        "source_database": args.source_database,
        "source_accession": args.source_accession,
        "chain_id": args.chain_id,
        "coordinate_payload_path": args.coordinate_payload_path,
        "local_payload_path": str(payload),
        "coordinate_payload_sha256": digest,
        "coordinate_payload_byte_count": str(size),
        "coordinate_payload_storage_policy": args.storage_policy,
        "coordinate_payload_license_or_terms_ref": args.terms_ref,
        "registration_status": "byte_payload_sha256_registered_from_local_file",
        "derivation_status_after_registration": "residue_table_still_requires_explicit_next_gate",
    }
    write_row(Path(args.out) if args.out else None, row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
