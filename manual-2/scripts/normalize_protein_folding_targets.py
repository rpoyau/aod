#!/usr/bin/env python3
"""Regenerate Manual II protein folding target-normalization rows.

The script is offline-only. It writes target rows, contact/distance hashes,
coverage/limitation rows, and manifests. It does not download PDB/AlphaFold data
and does not use target coordinates as AOD prediction premises.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_hash(label: str, payload: dict[str, object]) -> str:
    return sha(json.dumps({"label": label, "payload": payload}, sort_keys=True, separators=(",", ":")))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    sequences = [
        {"protein_id": "manual_seed_GAS", "target_packet_id": "manual_seed_GAS_packet", "source": "manual_fixture", "source_accession": "pep_GAS", "isoform_id": "not_applicable", "organism": "manual_fixture", "sequence": "GAS", "sequence_sha256": sha("GAS"), "residue_count": "3", "sequence_status": "committed_manual_fixture_sequence", "normalization_status": "normalized_sequence_packet", "leakage_role": "allowed_input", "target_status": "schema_fixture_not_external_folding_target", "release_status": "v40.02r04_target_normalization_carried_forward"},
        {"protein_id": "manual_seed_MAG", "target_packet_id": "manual_seed_MAG_packet", "source": "manual_fixture", "source_accession": "pep_MAG", "isoform_id": "not_applicable", "organism": "manual_fixture", "sequence": "MAG", "sequence_sha256": sha("MAG"), "residue_count": "3", "sequence_status": "committed_manual_fixture_sequence", "normalization_status": "normalized_sequence_packet", "leakage_role": "allowed_input", "target_status": "schema_fixture_not_external_folding_target", "release_status": "v40.02r04_target_normalization_carried_forward"},
        {"protein_id": "uniprot_P69905_locator", "target_packet_id": "uniprot_P69905_locator", "source": "UniProt", "source_accession": "P69905", "isoform_id": "canonical", "organism": "Homo sapiens locator row", "sequence": "deferred_no_network_fetch", "sequence_sha256": sha("uniprot_P69905_locator|sequence_deferred"), "residue_count": "deferred_no_network_fetch", "sequence_status": "target_locator_only_no_sequence_committed", "normalization_status": "locator_normalized_without_sequence_payload", "leakage_role": "target_only", "target_status": "external_sequence_locator_no_prediction_input", "release_status": "v40.02r04_target_normalization_carried_forward"},
        {"protein_id": "uniprot_P68871_locator", "target_packet_id": "uniprot_P68871_locator", "source": "UniProt", "source_accession": "P68871", "isoform_id": "canonical", "organism": "Homo sapiens locator row", "sequence": "deferred_no_network_fetch", "sequence_sha256": sha("uniprot_P68871_locator|sequence_deferred"), "residue_count": "deferred_no_network_fetch", "sequence_status": "target_locator_only_no_sequence_committed", "normalization_status": "locator_normalized_without_sequence_payload", "leakage_role": "target_only", "target_status": "external_sequence_locator_no_prediction_input", "release_status": "v40.02r04_target_normalization_carried_forward"},
    ]

    pdb_rows: list[dict[str, object]] = []
    for accession in ["1CRN", "1UBQ"]:
        pid = f"pdb_{accession.lower()}_A"
        payload = {"source": "RCSB_PDB", "accession": accession, "chain": "A", "coordinate_payload": "not_committed", "threshold": 8.0, "min_seq_sep": 3}
        pdb_rows.append({"protein_id": pid, "structure_target_id": f"{pid}_mmcif_target", "source": "RCSB_PDB", "source_accession": accession, "structure_source": "PDB/mmCIF", "structure_file": f"{accession}.cif", "structure_sha256": stable_hash(f"{pid}_structure_locator", payload), "chain_id": "A", "entity_id": "deferred_no_network_fetch", "experimental_method": "deferred_no_network_fetch", "resolution_angstrom": "deferred_no_network_fetch", "model_version": "not_applicable", "residue_count": "deferred_no_network_fetch", "resolved_residue_count": "deferred_no_network_fetch", "missing_residue_count": "deferred_no_network_fetch", "ca_coordinate_status": "locator_only_no_coordinate_payload", "cb_coordinate_status": "locator_only_no_coordinate_payload", "contact_threshold_angstrom": "8.0", "min_sequence_separation": "3", "contact_map_hash": stable_hash(f"{pid}_contact_map_locator", payload), "distance_matrix_hash": stable_hash(f"{pid}_distance_matrix_locator", payload), "secondary_structure_status": "deferred_no_coordinate_payload", "confidence_source": "experimental_metadata_deferred", "target_limitation_class": "experimental_structure_locator_only_no_coordinates_committed", "normalization_status": "target_locator_normalized_no_coordinate_payload", "leakage_role": "target_only", "release_status": "v40.02r04_target_normalization_carried_forward"})

    alphafold_rows: list[dict[str, object]] = []
    for acc in ["P69905", "P68871"]:
        pid = f"alphafold_AF-{acc}-F1"
        payload = {"source": "AlphaFold_DB", "accession": f"AF-{acc}-F1", "model_version": "deferred_no_network_fetch", "coordinate_payload": "not_committed", "threshold": 8.0, "min_seq_sep": 3}
        alphafold_rows.append({"protein_id": pid, "structure_target_id": f"{pid}_predicted_target", "source": "AlphaFold_DB", "source_accession": f"AF-{acc}-F1", "structure_source": "AlphaFold_predicted_structure", "structure_file": f"AF-{acc}-F1-model_v4.cif", "structure_sha256": stable_hash(f"{pid}_structure_locator", payload), "chain_id": "A", "entity_id": "canonical_uniprot_chain", "experimental_method": "predicted_model_not_experimental", "resolution_angstrom": "not_applicable", "model_version": "deferred_no_network_fetch", "residue_count": "deferred_no_network_fetch", "resolved_residue_count": "deferred_no_network_fetch", "missing_residue_count": "deferred_no_network_fetch", "ca_coordinate_status": "locator_only_no_coordinate_payload", "cb_coordinate_status": "locator_only_no_coordinate_payload", "contact_threshold_angstrom": "8.0", "min_sequence_separation": "3", "contact_map_hash": stable_hash(f"{pid}_contact_map_locator", payload), "distance_matrix_hash": stable_hash(f"{pid}_distance_matrix_locator", payload), "secondary_structure_status": "deferred_no_coordinate_payload", "confidence_source": "pLDDT_deferred", "plddt_mean": "deferred_no_coordinate_payload", "plddt_min": "deferred_no_coordinate_payload", "plddt_coverage": "deferred_no_coordinate_payload", "pae_available": "deferred_no_network_fetch", "target_limitation_class": "predicted_structure_comparator_not_ground_truth", "normalization_status": "predicted_target_locator_normalized_no_coordinate_payload", "leakage_role": "target_only", "release_status": "v40.02r04_target_normalization_carried_forward"})

    contacts: list[dict[str, object]] = []
    distances: list[dict[str, object]] = []
    manual = [
        ("manual_seed_GAS", "manual_fixture", "pep_GAS", "GAS", "1-3", "1", "[[0,3.8,7.6],[3.8,0,3.8],[7.6,3.8,0]]"),
        ("manual_seed_MAG", "manual_fixture", "pep_MAG", "MAG", "", "0", "[[0,3.8,8.2],[3.8,0,4.4],[8.2,4.4,0]]"),
    ]
    for pid, source, acc, seq, pairs, count, matrix in manual:
        payload = {"protein_id": pid, "sequence": seq, "threshold": 8.0, "min_sequence_separation": 2, "pairs": pairs, "matrix": matrix}
        contacts.append({"contact_target_id": f"{pid}_manual_contact_target", "protein_id": pid, "structure_target_id": f"{pid}_manual_fixture_structure", "structure_source": source, "source_accession": acc, "chain_id": "A", "residue_count": len(seq), "contact_threshold_angstrom": "8.0", "min_sequence_separation": "2", "contact_pairs": pairs, "contact_count": count, "contact_map_hash": stable_hash(f"{pid}_contact_map", payload), "contact_map_status": "normalized_manual_fixture_contact_map", "leakage_role": "comparison_only", "target_status": "schema_fixture_not_external_folding_target", "release_status": "v40.02r04_target_normalization_carried_forward"})
        distances.append({"distance_target_id": f"{pid}_manual_distance_target", "protein_id": pid, "structure_target_id": f"{pid}_manual_fixture_structure", "structure_source": source, "source_accession": acc, "chain_id": "A", "residue_count": len(seq), "distance_matrix_kind": "CA_pairwise_fixture", "distance_matrix_payload": matrix, "distance_matrix_hash": stable_hash(f"{pid}_distance_matrix", payload), "coordinate_status": "normalized_manual_fixture_coordinates", "leakage_role": "comparison_only", "target_status": "schema_fixture_not_external_folding_target", "release_status": "v40.02r04_target_normalization_carried_forward"})
    for row in pdb_rows:
        contacts.append({"contact_target_id": row["structure_target_id"].replace("_target", "_contact_target"), "protein_id": row["protein_id"], "structure_target_id": row["structure_target_id"], "structure_source": row["structure_source"], "source_accession": row["source_accession"], "chain_id": row["chain_id"], "residue_count": row["residue_count"], "contact_threshold_angstrom": row["contact_threshold_angstrom"], "min_sequence_separation": row["min_sequence_separation"], "contact_pairs": "deferred_no_coordinate_payload", "contact_count": "deferred_no_coordinate_payload", "contact_map_hash": row["contact_map_hash"], "contact_map_status": "locator_only_no_coordinate_payload", "leakage_role": "target_only", "target_status": "experimental_target_normalized_as_locator_only", "release_status": "v40.02r04_target_normalization_carried_forward"})
        distances.append({"distance_target_id": row["structure_target_id"].replace("_target", "_distance_target"), "protein_id": row["protein_id"], "structure_target_id": row["structure_target_id"], "structure_source": row["structure_source"], "source_accession": row["source_accession"], "chain_id": row["chain_id"], "residue_count": row["residue_count"], "distance_matrix_kind": "CA_pairwise_deferred", "distance_matrix_payload": "deferred_no_coordinate_payload", "distance_matrix_hash": row["distance_matrix_hash"], "coordinate_status": row["ca_coordinate_status"], "leakage_role": "target_only", "target_status": "experimental_target_normalized_as_locator_only", "release_status": "v40.02r04_target_normalization_carried_forward"})
    for row in alphafold_rows:
        contacts.append({"contact_target_id": row["structure_target_id"].replace("_target", "_contact_target"), "protein_id": row["protein_id"], "structure_target_id": row["structure_target_id"], "structure_source": row["structure_source"], "source_accession": row["source_accession"], "chain_id": row["chain_id"], "residue_count": row["residue_count"], "contact_threshold_angstrom": row["contact_threshold_angstrom"], "min_sequence_separation": row["min_sequence_separation"], "contact_pairs": "deferred_no_coordinate_payload", "contact_count": "deferred_no_coordinate_payload", "contact_map_hash": row["contact_map_hash"], "contact_map_status": "predicted_structure_locator_only_no_coordinate_payload", "leakage_role": "target_only", "target_status": "predicted_structure_comparator_not_ground_truth", "release_status": "v40.02r04_target_normalization_carried_forward"})
        distances.append({"distance_target_id": row["structure_target_id"].replace("_target", "_distance_target"), "protein_id": row["protein_id"], "structure_target_id": row["structure_target_id"], "structure_source": row["structure_source"], "source_accession": row["source_accession"], "chain_id": row["chain_id"], "residue_count": row["residue_count"], "distance_matrix_kind": "CA_pairwise_deferred", "distance_matrix_payload": "deferred_no_coordinate_payload", "distance_matrix_hash": row["distance_matrix_hash"], "coordinate_status": row["ca_coordinate_status"], "leakage_role": "target_only", "target_status": "predicted_structure_comparator_not_ground_truth", "release_status": "v40.02r04_target_normalization_carried_forward"})
    limitations = [
        {"limitation_id": "LIMIT-MANUAL-FIXTURE-001", "target_scope": "manual_fixture_contact_distance_rows", "source_class": "manual_fixture", "limitation_class": "schema_fixture_not_external_ground_truth", "limitation_text": "Manual contact and distance rows exercise the normalization schema only; they are not experimental folding targets.", "score_permission": "no_score_target_normalization_carried_forward", "release_status": "v40.02r04_target_normalization_carried_forward"},
        {"limitation_id": "LIMIT-PDB-LOCATOR-001", "target_scope": "pdb_mmcif_structure_targets", "source_class": "experimental_structure_locator", "limitation_class": "locator_only_no_coordinate_payload", "limitation_text": "PDB/mmCIF rows identify experimental target records and hash their locator-normalization rows; no archive coordinate payload is committed in this release.", "score_permission": "deferred_until_coordinate_payload_loaded_and_prediction_frozen", "release_status": "v40.02r04_target_normalization_carried_forward"},
        {"limitation_id": "LIMIT-AF-COMPARATOR-001", "target_scope": "alphafold_structure_targets", "source_class": "predicted_structure_locator", "limitation_class": "predicted_structure_comparator_not_ground_truth", "limitation_text": "AlphaFold rows are predicted-structure comparator targets, not experimental ground truth and not raw AFC/D.E.C. premises.", "score_permission": "deferred_until_prediction_freeze_then_comparison_only", "release_status": "v40.02r04_target_normalization_carried_forward"},
        {"limitation_id": "LIMIT-LEAKAGE-001", "target_scope": "all_structure_contact_distance_targets", "source_class": "target_coordinate_or_contact_map", "limitation_class": "forbidden_as_prediction_premise", "limitation_text": "Target coordinates, contact maps, distance matrices, and secondary-structure labels are excluded from raw D.E.C. rows and future AOD prediction-freeze inputs.", "score_permission": "comparison_only_after_v40.02r05_prediction_freeze", "release_status": "v40.02r04_target_normalization_carried_forward"},
    ]
    return sequences, pdb_rows, alphafold_rows, contacts, distances, limitations


def main() -> int:
    sequences, pdb_rows, alphafold_rows, contacts, distances, limitations = build_rows()
    write_csv(PROT / "protein_sequence_target_packets.csv", sequences, ["protein_id", "target_packet_id", "source", "source_accession", "isoform_id", "organism", "sequence", "sequence_sha256", "residue_count", "sequence_status", "normalization_status", "leakage_role", "target_status", "release_status"])
    write_csv(PROT / "pdb_mmcif_structure_targets.csv", pdb_rows, ["protein_id", "structure_target_id", "source", "source_accession", "structure_source", "structure_file", "structure_sha256", "chain_id", "entity_id", "experimental_method", "resolution_angstrom", "model_version", "residue_count", "resolved_residue_count", "missing_residue_count", "ca_coordinate_status", "cb_coordinate_status", "contact_threshold_angstrom", "min_sequence_separation", "contact_map_hash", "distance_matrix_hash", "secondary_structure_status", "confidence_source", "target_limitation_class", "normalization_status", "leakage_role", "release_status"])
    write_csv(PROT / "alphafold_structure_targets.csv", alphafold_rows, ["protein_id", "structure_target_id", "source", "source_accession", "structure_source", "structure_file", "structure_sha256", "chain_id", "entity_id", "experimental_method", "resolution_angstrom", "model_version", "residue_count", "resolved_residue_count", "missing_residue_count", "ca_coordinate_status", "cb_coordinate_status", "contact_threshold_angstrom", "min_sequence_separation", "contact_map_hash", "distance_matrix_hash", "secondary_structure_status", "confidence_source", "plddt_mean", "plddt_min", "plddt_coverage", "pae_available", "target_limitation_class", "normalization_status", "leakage_role", "release_status"])
    write_csv(PROT / "protein_contact_map_targets.csv", contacts, ["contact_target_id", "protein_id", "structure_target_id", "structure_source", "source_accession", "chain_id", "residue_count", "contact_threshold_angstrom", "min_sequence_separation", "contact_pairs", "contact_count", "contact_map_hash", "contact_map_status", "leakage_role", "target_status", "release_status"])
    write_csv(PROT / "protein_distance_matrix_targets.csv", distances, ["distance_target_id", "protein_id", "structure_target_id", "structure_source", "source_accession", "chain_id", "residue_count", "distance_matrix_kind", "distance_matrix_payload", "distance_matrix_hash", "coordinate_status", "leakage_role", "target_status", "release_status"])
    write_csv(PROT / "protein_structure_target_limitations.csv", limitations, ["limitation_id", "target_scope", "source_class", "limitation_class", "limitation_text", "score_permission", "release_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
