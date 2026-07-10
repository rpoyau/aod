#!/usr/bin/env python3
"""Derive PDBx/mmCIF coordinate-payload contact-map target rows.

This v40.02r07 generator is offline and deterministic. It ingests committed
PDBx/mmCIF-style coordinate payload fixtures, extracts atom-site rows, derives
CA-pair distance/contact target rows, and writes target-normalization manifests.
It does not read AOD prediction packets and does not score any AOD-vs-PDB row.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
PAYLOAD_DIR = PROT / "pdb_mmcif_payloads"
VERSION = "v40.02r07"
THRESHOLD = 8.0
MIN_SEQUENCE_SEPARATION = 2

MM_CIF_FIXTURES: dict[str, str] = {
    "manual_seed_GAS_pdbx_mmcif_payload_fixture.cif": """data_manual_seed_GAS_pdbx_mmcif_payload_fixture
#
_entry.id manual_seed_GAS_pdbx_mmcif_payload_fixture
_struct.title 'Manual II PDBx/mmCIF coordinate-payload fixture for GAS contact-map derivation gate'
_exptl.method 'manual coordinate fixture; schema gate only'
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
ATOM 1 N N GLY A 1 -1.200 0.000 0.000 1.00 10.00
ATOM 2 C CA GLY A 1 0.000 0.000 0.000 1.00 10.00
ATOM 3 C C GLY A 1 1.300 0.000 0.000 1.00 10.00
ATOM 4 N N ALA A 2 2.500 0.000 0.000 1.00 10.00
ATOM 5 C CA ALA A 2 3.800 0.000 0.000 1.00 10.00
ATOM 6 C CB ALA A 2 3.800 1.500 0.000 1.00 10.00
ATOM 7 C C ALA A 2 5.100 0.000 0.000 1.00 10.00
ATOM 8 N N SER A 3 6.300 0.000 0.000 1.00 10.00
ATOM 9 C CA SER A 3 7.600 0.000 0.000 1.00 10.00
ATOM 10 C CB SER A 3 7.600 1.500 0.000 1.00 10.00
ATOM 11 O OG SER A 3 7.600 2.900 0.000 1.00 10.00
ATOM 12 C C SER A 3 8.900 0.000 0.000 1.00 10.00
#
"""
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(prefix: str, payload: object) -> str:
    text = json.dumps({"prefix": prefix, "payload": payload}, sort_keys=True, separators=(",", ":"))
    return sha256_text(text)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ensure_payload_fixtures() -> None:
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in MM_CIF_FIXTURES.items():
        (PAYLOAD_DIR / name).write_text(text, encoding="utf-8")


def parse_atom_site_loop(path: Path) -> list[dict[str, str]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    rows: list[dict[str, str]] = []
    i = 0
    while i < len(lines):
        if lines[i] != "loop_":
            i += 1
            continue
        i += 1
        headers: list[str] = []
        while i < len(lines) and lines[i].startswith("_atom_site."):
            headers.append(lines[i])
            i += 1
        if not headers:
            continue
        while i < len(lines) and lines[i] and not lines[i].startswith("#") and not lines[i].startswith("loop_"):
            parts = lines[i].split()
            if len(parts) != len(headers):
                raise ValueError(f"atom_site row in {path.name} has {len(parts)} values for {len(headers)} headers: {lines[i]!r}")
            rows.append({h.removeprefix("_atom_site."): v for h, v in zip(headers, parts)})
            i += 1
    if not rows:
        raise ValueError(f"no _atom_site loop parsed from {path}")
    return rows


def dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def fmt_float(x: float) -> str:
    return f"{x:.3f}".rstrip("0").rstrip(".")


def build() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    ensure_payload_fixtures()
    registry: list[dict[str, object]] = []
    atom_extract: list[dict[str, object]] = []
    residue_rows: list[dict[str, object]] = []
    contact_rows: list[dict[str, object]] = []
    distance_rows: list[dict[str, object]] = []

    for path in sorted(PAYLOAD_DIR.glob("*.cif")):
        payload_text = path.read_text(encoding="utf-8")
        payload_sha = sha256_file(path)
        payload_id = path.stem
        protein_id = "manual_seed_GAS"
        structure_target_id = f"{payload_id}_structure_target"
        source_accession = "manual_seed_GAS_pdbx_mmcif_payload_fixture"
        atom_rows = parse_atom_site_loop(path)
        registry.append({
            "payload_id": payload_id,
            "protein_id": protein_id,
            "structure_target_id": structure_target_id,
            "source": "manual_fixture_pdbx_mmcif",
            "source_accession": source_accession,
            "payload_file": f"manual-2/data/protein/pdb_mmcif_payloads/{path.name}",
            "payload_sha256": payload_sha,
            "payload_format": "PDBx/mmCIF_atom_site_loop_fixture",
            "coordinate_payload_status": "committed_fixture_payload_not_external_pdb_validation",
            "residue_count": "3",
            "atom_site_count": str(len(atom_rows)),
            "contact_threshold_angstrom": f"{THRESHOLD:.1f}",
            "min_sequence_separation": str(MIN_SEQUENCE_SEPARATION),
            "leakage_role": "target_only",
            "prediction_premise_status": "forbidden_as_prediction_premise",
            "score_status": "not_scored_in_v40.02r07",
            "release_status": "v40.02r07_pdb_mmcif_coordinate_payload_ingest",
        })
        ca_by_residue: dict[int, tuple[float, float, float]] = {}
        cb_by_residue: dict[int, tuple[float, float, float]] = {}
        resname_by_residue: dict[int, str] = {}
        atom_index = 1
        for atom in atom_rows:
            seq = int(atom["label_seq_id"])
            atom_name = atom["label_atom_id"]
            coord = (float(atom["Cartn_x"]), float(atom["Cartn_y"]), float(atom["Cartn_z"]))
            resname_by_residue[seq] = atom["label_comp_id"]
            if atom_name == "CA":
                ca_by_residue[seq] = coord
            if atom_name == "CB":
                cb_by_residue[seq] = coord
            atom_extract.append({
                "atom_extract_id": f"atom_site_{atom_index:03d}",
                "payload_id": payload_id,
                "protein_id": protein_id,
                "structure_target_id": structure_target_id,
                "model_num": "1",
                "chain_id": atom["label_asym_id"],
                "residue_index": str(seq),
                "residue_name": atom["label_comp_id"],
                "atom_name": atom_name,
                "x": fmt_float(coord[0]),
                "y": fmt_float(coord[1]),
                "z": fmt_float(coord[2]),
                "occupancy": atom["occupancy"],
                "b_iso_or_equiv": atom["B_iso_or_equiv"],
                "extract_status": "parsed_from_committed_pdbx_mmcif_fixture",
                "leakage_role": "target_only",
                "score_status": "not_scored_in_v40.02r07",
                "release_status": "v40.02r07_pdb_mmcif_coordinate_payload_ingest",
            })
            atom_index += 1
        for seq in sorted(resname_by_residue):
            ca = ca_by_residue.get(seq)
            cb = cb_by_residue.get(seq)
            residue_rows.append({
                "residue_coord_id": f"{payload_id}_residue_{seq:03d}",
                "payload_id": payload_id,
                "protein_id": protein_id,
                "structure_target_id": structure_target_id,
                "chain_id": "A",
                "residue_index": str(seq),
                "residue_name": resname_by_residue[seq],
                "ca_x": fmt_float(ca[0]) if ca else "missing",
                "ca_y": fmt_float(ca[1]) if ca else "missing",
                "ca_z": fmt_float(ca[2]) if ca else "missing",
                "cb_x": fmt_float(cb[0]) if cb else "missing_glycine_or_absent",
                "cb_y": fmt_float(cb[1]) if cb else "missing_glycine_or_absent",
                "cb_z": fmt_float(cb[2]) if cb else "missing_glycine_or_absent",
                "ca_coordinate_status": "present" if ca else "missing",
                "cb_coordinate_status": "present" if cb else "missing_glycine_or_absent",
                "residue_coordinate_status": "target_coordinate_payload_extracted_not_prediction_input",
                "leakage_role": "target_only",
                "score_status": "not_scored_in_v40.02r07",
                "release_status": "v40.02r07_pdb_mmcif_coordinate_payload_ingest",
            })
        pairs_payload: list[dict[str, object]] = []
        contact_pairs: list[str] = []
        residues = sorted(ca_by_residue)
        for i_idx, i in enumerate(residues):
            for j in residues[i_idx + 1:]:
                d = dist(ca_by_residue[i], ca_by_residue[j])
                sep = j - i
                in_scope = sep >= MIN_SEQUENCE_SEPARATION
                contact = in_scope and d <= THRESHOLD
                if contact:
                    contact_pairs.append(f"{i}-{j}")
                pairs_payload.append({
                    "residue_i": i,
                    "residue_j": j,
                    "pair_separation": sep,
                    "ca_distance_angstrom": round(d, 6),
                    "in_scope": in_scope,
                    "contact": contact,
                })
        contact_map_hash = stable_hash(f"{payload_id}_contact_map", pairs_payload)
        distance_matrix_hash = stable_hash(f"{payload_id}_distance_matrix", pairs_payload)
        for pair_idx, pair_payload in enumerate(pairs_payload, 1):
            i = int(pair_payload["residue_i"])
            j = int(pair_payload["residue_j"])
            sep = int(pair_payload["pair_separation"])
            d = float(pair_payload["ca_distance_angstrom"])
            in_scope = bool(pair_payload["in_scope"])
            contact = bool(pair_payload["contact"])
            pair = f"{i}-{j}"
            distance_rows.append({
                "distance_row_id": f"{payload_id}_distance_{pair_idx:03d}",
                "payload_id": payload_id,
                "protein_id": protein_id,
                "structure_target_id": structure_target_id,
                "chain_id": "A",
                "residue_i": str(i),
                "residue_j": str(j),
                "pair_separation": str(sep),
                "ca_distance_angstrom": fmt_float(d),
                "distance_basis": "CA_pairwise_from_committed_pdbx_mmcif_fixture",
                "distance_matrix_hash": distance_matrix_hash,
                "leakage_role": "target_only",
                "score_status": "not_scored_in_v40.02r07",
                "release_status": "v40.02r07_pdb_mmcif_contact_derivation_gate",
            })
            contact_rows.append({
                "derived_contact_id": f"{payload_id}_contact_{pair_idx:03d}",
                "payload_id": payload_id,
                "protein_id": protein_id,
                "structure_target_id": structure_target_id,
                "chain_id": "A",
                "residue_i": str(i),
                "residue_j": str(j),
                "pair_separation": str(sep),
                "contact_threshold_angstrom": f"{THRESHOLD:.1f}",
                "min_sequence_separation": str(MIN_SEQUENCE_SEPARATION),
                "ca_distance_angstrom": fmt_float(d),
                "derived_contact": "1" if contact else "0",
                "contact_scope_status": "in_scope" if in_scope else "below_min_sequence_separation_not_in_scope",
                "contact_map_hash": contact_map_hash,
                "derivation_status": "derived_from_committed_coordinate_payload_fixture",
                "leakage_role": "target_only",
                "score_status": "not_scored_in_v40.02r07",
                "release_status": "v40.02r07_pdb_mmcif_contact_derivation_gate",
            })
        # Add a compact row-level contact map hash to the registry after derivation.
        registry[-1]["derived_contact_pairs"] = ";".join(contact_pairs)
        registry[-1]["derived_contact_count"] = str(len(contact_pairs))
        registry[-1]["contact_map_hash"] = contact_map_hash
        registry[-1]["distance_matrix_hash"] = distance_matrix_hash
    return registry, atom_extract, residue_rows, contact_rows, distance_rows


def main() -> int:
    registry, atom_extract, residue_rows, contact_rows, distance_rows = build()
    write_csv(PROT / "pdb_mmcif_coordinate_payload_registry.csv", registry, [
        "payload_id", "protein_id", "structure_target_id", "source", "source_accession", "payload_file", "payload_sha256", "payload_format", "coordinate_payload_status", "residue_count", "atom_site_count", "contact_threshold_angstrom", "min_sequence_separation", "derived_contact_pairs", "derived_contact_count", "contact_map_hash", "distance_matrix_hash", "leakage_role", "prediction_premise_status", "score_status", "release_status",
    ])
    write_csv(PROT / "pdb_mmcif_atom_site_extract.csv", atom_extract, [
        "atom_extract_id", "payload_id", "protein_id", "structure_target_id", "model_num", "chain_id", "residue_index", "residue_name", "atom_name", "x", "y", "z", "occupancy", "b_iso_or_equiv", "extract_status", "leakage_role", "score_status", "release_status",
    ])
    write_csv(PROT / "pdb_mmcif_residue_coordinate_table.csv", residue_rows, [
        "residue_coord_id", "payload_id", "protein_id", "structure_target_id", "chain_id", "residue_index", "residue_name", "ca_x", "ca_y", "ca_z", "cb_x", "cb_y", "cb_z", "ca_coordinate_status", "cb_coordinate_status", "residue_coordinate_status", "leakage_role", "score_status", "release_status",
    ])
    write_csv(PROT / "pdb_mmcif_contact_map_derived.csv", contact_rows, [
        "derived_contact_id", "payload_id", "protein_id", "structure_target_id", "chain_id", "residue_i", "residue_j", "pair_separation", "contact_threshold_angstrom", "min_sequence_separation", "ca_distance_angstrom", "derived_contact", "contact_scope_status", "contact_map_hash", "derivation_status", "leakage_role", "score_status", "release_status",
    ])
    write_csv(PROT / "pdb_mmcif_distance_matrix_derived.csv", distance_rows, [
        "distance_row_id", "payload_id", "protein_id", "structure_target_id", "chain_id", "residue_i", "residue_j", "pair_separation", "ca_distance_angstrom", "distance_basis", "distance_matrix_hash", "leakage_role", "score_status", "release_status",
    ])
    manifest = {
        "lane": "pdb_mmcif_coordinate_payload_ingest_contact_map_derivation",
        "version_scope": VERSION,
        "status": "target_coordinate_payload_ingest_and_contact_map_derivation_only_no_aod_vs_pdb_score",
        "files": {
            "payload_registry": "manual-2/data/protein/pdb_mmcif_coordinate_payload_registry.csv",
            "atom_site_extract": "manual-2/data/protein/pdb_mmcif_atom_site_extract.csv",
            "residue_coordinate_table": "manual-2/data/protein/pdb_mmcif_residue_coordinate_table.csv",
            "derived_contact_map": "manual-2/data/protein/pdb_mmcif_contact_map_derived.csv",
            "derived_distance_matrix": "manual-2/data/protein/pdb_mmcif_distance_matrix_derived.csv",
            "coordinate_payloads": "manual-2/data/protein/pdb_mmcif_payloads/",
        },
        "input_policy": "read committed PDBx/mmCIF coordinate payload fixtures only; do not read AOD prediction freezes or target-score files",
        "score_policy": "not_scored_in_v40.02r07; downstream comparison requires a separate milestone",
        "leakage_policy": "coordinate payloads, derived contacts, and derived distances are target-only rows and forbidden as prediction premises",
        "claim_discipline": "contact-map derivation gate only; no expanded AOD-vs-PDB scoring, no coordinate-level prediction, no active lambda_fold",
        "carried_forward": [
            "v40.02r05 AOD contact/reclosure prediction freeze unchanged",
            "v40.02r06 manual-fixture contact residual score unchanged",
            "v40.02r06.1 label/manifest polish preserved",
        ],
        "next_milestone": "future expanded PDB target comparison gate, only after explicit scoring scope declaration",
    }
    (PROT / "pdb_mmcif_contact_derivation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
