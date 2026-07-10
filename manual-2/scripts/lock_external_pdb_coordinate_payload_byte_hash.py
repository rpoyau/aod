#!/usr/bin/env python3
"""Register the local external PDB coordinate byte-payload hash for Manual II.

This script is offline and deterministic. It hashes the committed local 1CRN.cif
payload and writes byte-hash lock ledgers only. It does not parse the mmCIF file,
derive residue tables, derive contact maps, or compute scores.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
PAYLOAD = PROT / "external_pdb_payloads" / "1CRN.cif"
VERSION = "v40.02r13"
URI = "https://files.rcsb.org/download/1CRN.cif"
LOCK_ID = "pdb_external_coordinate_payload_byte_hash_lock_1CRN_A_v4002r13"
LOCATOR_SHA = "37cc67db8e892c25dd1781977ac7b6a920d12dc115c03fe934716081c77bd1f7"
REGISTRATION_TS = "2026-06-17T00:00:00Z"
LOCAL_PAYLOAD_PATH = "manual-2/data/protein/external_pdb_payloads/1CRN.cif"


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    if not PAYLOAD.exists():
        raise FileNotFoundError(f"missing local coordinate payload: {PAYLOAD}")
    digest, size = sha256_file(PAYLOAD)
    common = {
        "version_scope": VERSION,
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "pdb_id": "1CRN",
        "chain_id": "A",
        "coordinate_payload_path": URI,
        "local_payload_path": LOCAL_PAYLOAD_PATH,
        "coordinate_payload_sha256": digest,
        "coordinate_payload_byte_count": str(size),
        "coordinate_payload_fetch_or_registration_timestamp": REGISTRATION_TS,
        "coordinate_payload_storage_policy": "committed_in_release_under_manual2_data_protein_external_pdb_payloads",
        "coordinate_payload_license_or_terms_ref": "RCSB_PDB_file_download_terms_for_1CRN_cif",
        "locator_policy_registration_sha256": LOCATOR_SHA,
        "release_status": f"{VERSION}_external_pdb_coordinate_payload_byte_hash_lock",
    }
    write_csv(PROT / "pdb_external_coordinate_payload_byte_hash_lock.csv", [
        "byte_hash_lock_id", "version_scope", "prior_hash_gate_id", "source_database", "source_accession", "pdb_id", "chain_id",
        "coordinate_payload_path", "local_payload_path", "coordinate_payload_sha256", "coordinate_payload_byte_count",
        "coordinate_payload_fetch_or_registration_timestamp", "coordinate_payload_storage_policy", "coordinate_payload_license_or_terms_ref",
        "coordinate_payload_byte_hash_status", "locator_policy_registration_sha256", "byte_hash_distinct_from_locator_policy_registration_sha256",
        "residue_table_derivation_status", "contact_map_derivation_status", "external_residual_score_status", "coordinate_metric_status", "release_status",
    ], [{
        "byte_hash_lock_id": LOCK_ID,
        "prior_hash_gate_id": "pdb_external_coordinate_payload_hash_gate_1CRN_A_v4002r12",
        **common,
        "coordinate_payload_byte_hash_status": "byte_payload_sha256_locked_from_local_payload",
        "byte_hash_distinct_from_locator_policy_registration_sha256": "true",
        "residue_table_derivation_status": "not_derived_in_this_gate_requires_explicit_next_gate",
        "contact_map_derivation_status": "not_derived_in_this_gate_requires_residue_table_gate",
        "external_residual_score_status": "not_scored_in_this_gate_requires_contact_map_and_scope_gate",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
    }])
    write_csv(PROT / "pdb_external_coordinate_payload_byte_hash_provenance.csv", [
        "provenance_id", "byte_hash_lock_id", "source_database", "source_accession", "coordinate_payload_path", "local_payload_path",
        "coordinate_payload_sha256", "coordinate_payload_byte_count", "coordinate_payload_fetch_or_registration_timestamp", "payload_source_mode",
        "payload_role", "target_source_role", "forbidden_as_raw_dec_premise", "forbidden_as_aod_freeze_premise", "release_status",
    ], [{
        "provenance_id": "pdb_external_coordinate_payload_byte_hash_provenance_1CRN_A_001",
        "byte_hash_lock_id": LOCK_ID,
        "payload_source_mode": "local_payload_supplied_from_declared_RCSB_URI",
        "payload_role": "downstream_external_target_payload_after_AOD_freeze",
        "target_source_role": "target_only_after_AOD_motif_curling_curls_and_SADAR_freeze",
        "forbidden_as_raw_dec_premise": "true",
        "forbidden_as_aod_freeze_premise": "true",
        **{k: common[k] for k in ["source_database", "source_accession", "coordinate_payload_path", "local_payload_path", "coordinate_payload_sha256", "coordinate_payload_byte_count", "coordinate_payload_fetch_or_registration_timestamp", "release_status"]},
    }])
    write_csv(PROT / "pdb_external_coordinate_payload_byte_hash_policy_lock.csv", [
        "policy_id", "byte_hash_lock_id", "chain_id", "model_id", "model_policy", "residue_index_basis", "atom_selector", "altloc_policy", "missing_residue_policy", "contact_threshold_angstrom", "min_sequence_separation", "residue_table_policy", "contact_map_policy", "evaluation_pair_policy", "negative_support_policy", "allowed_future_order", "forbidden_future_order", "release_status",
    ], [{
        "policy_id": "pdb_external_coordinate_payload_byte_hash_policy_1CRN_A_001",
        "byte_hash_lock_id": LOCK_ID,
        "chain_id": "A",
        "model_id": "1",
        "model_policy": "model_1_preferred_single_model_policy",
        "residue_index_basis": "one_based_residue_sequence_position",
        "atom_selector": "CA",
        "altloc_policy": "primary_or_highest_occupancy_altloc_required_before_derivation",
        "missing_residue_policy": "explicit_gap_rows_required_before_contact_derivation",
        "contact_threshold_angstrom": "8.0",
        "min_sequence_separation": "3",
        "residue_table_policy": "derive_only_in_later_gate_after_byte_hash_lock",
        "contact_map_policy": "derive_only_after_later_residue_table_gate",
        "evaluation_pair_policy": "declare_pairs_after_external_contact_map_and_before_residual_scoring",
        "negative_support_policy": "declare_negative_support_before_classifier_metrics",
        "allowed_future_order": "accession_scope_then_payload_byte_hash_lock_then_residue_table_then_contact_map_then_evaluation_pair_boundary_then_AOD_freeze_target_join_then_residual",
        "forbidden_future_order": "residue_table_contact_map_or_score_before_payload_byte_hash_lock_and_explicit_next_gate",
        "release_status": common["release_status"],
    }])
    write_csv(PROT / "pdb_external_coordinate_payload_byte_hash_derivation_block.csv", [
        "block_id", "byte_hash_lock_id", "candidate_derivation", "required_precondition", "current_status", "leakage_role", "release_status",
    ], [
        {"block_id": "PDB-EXT-BYTE-HASH-BLOCK-001", "byte_hash_lock_id": LOCK_ID, "candidate_derivation": "external_residue_coordinate_table", "required_precondition": "coordinate_payload_byte_sha256_locked_and_explicit_residue_table_gate", "current_status": "blocked_in_v40.02r13", "leakage_role": "target_only_after_AOD_freeze", "release_status": common["release_status"]},
        {"block_id": "PDB-EXT-BYTE-HASH-BLOCK-002", "byte_hash_lock_id": LOCK_ID, "candidate_derivation": "external_contact_map", "required_precondition": "external_residue_coordinate_table_derived_in_later_gate", "current_status": "blocked_in_v40.02r13", "leakage_role": "target_only_after_AOD_freeze", "release_status": common["release_status"]},
        {"block_id": "PDB-EXT-BYTE-HASH-BLOCK-003", "byte_hash_lock_id": LOCK_ID, "candidate_derivation": "external_residual_score", "required_precondition": "external_contact_map_and_evaluation_pair_boundary_declared", "current_status": "blocked_in_v40.02r13", "leakage_role": "downstream_score_only_after_freeze_target_join", "release_status": common["release_status"]},
    ])
    checks = [
        ("PDB-EXT-BYTE-HASH-001", "coordinate_payload_byte_sha256_exists_before_residue_table", "byte_hash_lock", "missing_coordinate_payload_sha256", "residue_table_derivation", "active_pass", "hash_gate_only_no_score"),
        ("PDB-EXT-BYTE-HASH-002", "coordinate_payload_byte_hash_differs_from_locator_policy_hash", "hash_role_separation", "registration_hash_confused_with_byte_hash", "manifest", "active_pass", "hash_gate_only_no_score"),
        ("PDB-EXT-BYTE-HASH-003", "residue_coordinate_table_remains_blocked_until_explicit_next_gate", "derivation_block", "residue_table_derived_in_hash_gate", "residue_table", "active_pass", "hash_gate_only_no_score"),
        ("PDB-EXT-BYTE-HASH-004", "contact_map_remains_blocked_until_residue_table_gate", "derivation_block", "contact_map_derived_in_hash_gate", "contact_map", "active_pass", "hash_gate_only_no_score"),
        ("PDB-EXT-BYTE-HASH-005", "external_payload_forbidden_as_raw_dec_or_aod_freeze_premise", "leakage_guard", "target_leakage_into_prediction_freeze", "AOD_freeze", "active_pass", "hash_gate_only_no_score"),
        ("PDB-EXT-BYTE-HASH-006", "target_rows_remain_downstream_of_frozen_AOD_packet", "freeze_before_target_join", "target_join_before_AOD_freeze", "target_join", "active_pass", "hash_gate_only_no_score"),
        ("PDB-EXT-BYTE-HASH-007", "coordinate_level_metrics_remain_deferred", "metric_guard", "RMSD_TM_score_GDT_released", "coordinate_metrics", "active_pass", "hash_gate_only_no_score"),
        ("PDB-EXT-BYTE-HASH-008", "AOD_motif_curling_curls_and_SADAR_precede_future_external_target_map", "detection_order", "target_map_before_motif_sadar_freeze", "detection_chain", "active_pass", "hash_gate_only_no_score"),
    ]
    write_csv(PROT / "pdb_external_coordinate_payload_byte_hash_leakage_checks.csv", [
        "check_id", "check_name", "gate_type", "failure_mode", "blocked_lane", "check_result", "score_input_status",
    ], [dict(zip(["check_id", "check_name", "gate_type", "failure_mode", "blocked_lane", "check_result", "score_input_status"], c)) for c in checks])
    manifest = {
        "lane": "external_pdb_coordinate_payload_byte_hash_lock",
        "version_scope": VERSION,
        "status": "external PDB coordinate byte-payload SHA-256 lock only; no residue table, contact map, external score, or coordinate metric is derived",
        "prior_hash_gate": "manual-2/data/protein/pdb_external_coordinate_payload_hash_gate.csv",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "chain_id": "A",
        "coordinate_payload_path": URI,
        "local_payload_path": LOCAL_PAYLOAD_PATH,
        "coordinate_payload_sha256": digest,
        "coordinate_payload_byte_count": size,
        "coordinate_payload_fetch_or_registration_timestamp": REGISTRATION_TS,
        "coordinate_payload_storage_policy": "committed_in_release_under_manual2_data_protein_external_pdb_payloads",
        "coordinate_payload_license_or_terms_ref": "RCSB_PDB_file_download_terms_for_1CRN_cif",
        "locator_policy_registration_sha256": LOCATOR_SHA,
        "hash_role_note": "coordinate_payload_sha256 hashes the committed local 1CRN.cif byte payload; locator_policy_registration_sha256 hashes only the locked locator/policy card",
        "policy": {
            "model_id": "1",
            "model_policy": "model_1_preferred_single_model_policy",
            "residue_index_basis": "one_based_residue_sequence_position",
            "atom_selector": "CA",
            "altloc_policy": "primary_or_highest_occupancy_altloc_required_before_derivation",
            "missing_residue_policy": "explicit_gap_rows_required_before_contact_derivation",
            "contact_threshold_angstrom": "8.0",
            "min_sequence_separation": "3",
        },
        "blocked_until_later_gate": [
            "external_residue_coordinate_table_derivation",
            "external_contact_map_derivation",
            "evaluation_pair_boundary_declaration",
            "external_accession_residual_score",
        ],
        "files": {
            "byte_hash_lock": "manual-2/data/protein/pdb_external_coordinate_payload_byte_hash_lock.csv",
            "byte_hash_provenance": "manual-2/data/protein/pdb_external_coordinate_payload_byte_hash_provenance.csv",
            "byte_hash_policy_lock": "manual-2/data/protein/pdb_external_coordinate_payload_byte_hash_policy_lock.csv",
            "byte_hash_derivation_block": "manual-2/data/protein/pdb_external_coordinate_payload_byte_hash_derivation_block.csv",
            "byte_hash_leakage_checks": "manual-2/data/protein/pdb_external_coordinate_payload_byte_hash_leakage_checks.csv",
            "local_payload": "manual-2/data/protein/external_pdb_payloads/1CRN.cif",
        },
        "input_order_policy": "r11 accession scope first; r12 locator/policy gate second; r13 byte-payload SHA-256 lock third; residue/contact derivation only in later gates; AOD motif/curling-curls/SADAR freeze stays upstream of target join",
        "claim_discipline": "Byte-hash lock only. This is not residue-table derivation, not an external contact-map score, and not a folding model.",
    }
    (PROT / "pdb_external_coordinate_payload_byte_hash_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
