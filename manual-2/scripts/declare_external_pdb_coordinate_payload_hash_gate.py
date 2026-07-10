#!/usr/bin/env python3
"""Emit the Manual II external PDB coordinate-payload hash gate.

This script is offline and deterministic. It does not fetch or parse external
PDB coordinates. It records the payload URI, boundary/readout policy, and a
locator/policy registration hash, then blocks residue/contact derivation until a later
gate registers an actual external coordinate byte-payload SHA-256.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r12.1"
SCOPE_ID = "pdb_external_accession_scope_1CRN_A_v4002r11"
HASH_GATE_ID = "pdb_external_coordinate_payload_hash_gate_1CRN_A_v4002r12"
PAYLOAD_REG_ID = "pdb_external_coordinate_payload_lock_1CRN_A_001"
EXTERNAL_URI = "https://files.rcsb.org/download/1CRN.cif"


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def locator_policy_registration_sha256() -> str:
    material = "|".join([
        "RCSB_PDB",
        "1CRN",
        "A",
        EXTERNAL_URI,
        "PDBx/mmCIF",
        "CA",
        "8.0",
        "3",
        "one_based_residue_sequence_position",
        "model_1_preferred_single_model_policy",
        "altloc_primary_or_highest_occupancy_required",
        "missing_residue_explicit_gap_policy_required",
        "external_coordinate_bytes_not_committed_in_v40.02r12.1",
    ])
    return sha_text(material)


def main() -> int:
    packet = {r["target_packet_id"]: r for r in read_csv(PROT / "pdb_structure_target_packets.csv")}["pdb_1crn_A_locator"]
    target = {r["structure_target_id"]: r for r in read_csv(PROT / "pdb_mmcif_structure_targets.csv")}["pdb_1crn_A_mmcif_target"]
    reg_sha = locator_policy_registration_sha256()

    write_csv(PROT / "pdb_external_coordinate_payload_hash_gate.csv", [
        "hash_gate_id", "version_scope", "prior_scope_id", "source_database", "source_accession", "pdb_id", "chain_id",
        "coordinate_payload_path", "coordinate_payload_path_status", "coordinate_payload_sha256", "coordinate_payload_sha256_status",
        "payload_registration_sha256", "locator_policy_registration_sha256", "download_or_registration_timestamp", "coordinate_payload_status", "coordinate_payload_hash_gate_status",
        "coordinate_contact_derivation_status", "residue_table_derivation_status", "score_status", "release_status",
    ], [{
        "hash_gate_id": HASH_GATE_ID,
        "version_scope": VERSION,
        "prior_scope_id": SCOPE_ID,
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "pdb_id": "1CRN",
        "chain_id": "A",
        "coordinate_payload_path": EXTERNAL_URI,
        "coordinate_payload_path_status": "external_uri_declared_payload_bytes_not_committed",
        "coordinate_payload_sha256": "required_after_external_payload_bytes_are_registered_before_contact_derivation",
        "coordinate_payload_sha256_status": "byte_payload_hash_required_not_satisfied_in_this_gate",
        "payload_registration_sha256": reg_sha,
        "locator_policy_registration_sha256": reg_sha,
        "download_or_registration_timestamp": "2026-06-16T00:00:00Z",
        "coordinate_payload_status": "external_payload_uri_and_registration_hash_locked_no_coordinate_bytes_committed",
        "coordinate_payload_hash_gate_status": "active_gate_blocks_contact_derivation_until_byte_hash_exists",
        "coordinate_contact_derivation_status": "blocked_no_external_contact_map_derivation_in_this_gate",
        "residue_table_derivation_status": "blocked_until_payload_byte_hash_lock",
        "score_status": "hash_gate_only_no_score",
        "release_status": f"{VERSION}_external_pdb_coordinate_payload_hash_gate",
    }])

    write_csv(PROT / "pdb_external_coordinate_payload_provenance_lock.csv", [
        "payload_registration_id", "hash_gate_id", "source_database", "source_accession", "coordinate_payload_path", "coordinate_payload_path_status",
        "coordinate_payload_sha256", "coordinate_payload_sha256_status", "payload_registration_sha256", "locator_policy_registration_sha256", "raw_locator_sha256", "normalized_locator_sha256",
        "structure_target_sha256", "download_or_registration_timestamp", "license_or_terms_ref", "payload_license_or_terms_ref", "payload_role",
        "target_source_role", "release_status",
    ], [{
        "payload_registration_id": PAYLOAD_REG_ID,
        "hash_gate_id": HASH_GATE_ID,
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "coordinate_payload_path": EXTERNAL_URI,
        "coordinate_payload_path_status": "external_uri_declared_payload_bytes_not_committed",
        "coordinate_payload_sha256": "required_after_external_payload_bytes_are_registered_before_contact_derivation",
        "coordinate_payload_sha256_status": "byte_payload_hash_required_not_satisfied_in_this_gate",
        "payload_registration_sha256": reg_sha,
        "locator_policy_registration_sha256": reg_sha,
        "raw_locator_sha256": packet["raw_sha256"],
        "normalized_locator_sha256": packet["normalized_sha256"],
        "structure_target_sha256": target["structure_sha256"],
        "download_or_registration_timestamp": "2026-06-16T00:00:00Z",
        "license_or_terms_ref": "external database terms; coordinate bytes not redistributed in this gate",
        "payload_license_or_terms_ref": "RCSB_PDB_terms_locator_only_until_external_payload_fetch",
        "payload_role": "external_coordinate_payload_hash_lock_requirement_not_prediction_premise",
        "target_source_role": "downstream_target_payload_only_after_AOD_freeze",
        "release_status": f"{VERSION}_external_pdb_coordinate_payload_hash_gate",
    }])

    write_csv(PROT / "pdb_external_coordinate_payload_policy_lock.csv", [
        "policy_id", "hash_gate_id", "chain_id", "model_id", "model_policy", "residue_index_basis", "atom_selector", "altloc_policy",
        "missing_residue_policy", "contact_threshold_angstrom", "min_sequence_separation", "coordinate_payload_hash_requirement", "residue_table_policy",
        "contact_map_policy", "evaluation_pair_policy", "negative_support_policy", "allowed_future_order", "forbidden_future_order", "coordinate_metric_status", "release_status",
    ], [{
        "policy_id": "pdb_external_coordinate_payload_policy_1CRN_A_001",
        "hash_gate_id": HASH_GATE_ID,
        "chain_id": "A",
        "model_id": "1",
        "model_policy": "model_1_preferred_single_model_policy",
        "residue_index_basis": "one_based_residue_sequence_position",
        "atom_selector": "CA",
        "altloc_policy": "primary_or_highest_occupancy_altloc_required_before_derivation",
        "missing_residue_policy": "explicit_gap_rows_required_before_contact_derivation",
        "contact_threshold_angstrom": "8.0",
        "min_sequence_separation": "3",
        "coordinate_payload_hash_requirement": "byte_payload_sha256_required_before_residue_table_or_contact_derivation",
        "residue_table_policy": "derive_only_after_coordinate_payload_byte_hash_lock",
        "contact_map_policy": "derive_only_after_payload_hash_lock_and_residue_table_derivation",
        "evaluation_pair_policy": "declare_pairs_after_residue_table_and_before_residual_scoring",
        "negative_support_policy": "declare_negative_support_before_MCC_or_classifier_metrics",
        "allowed_future_order": "accession_scope_then_payload_byte_hash_lock_then_residue_table_then_contact_map_then_evaluation_pair_boundary_then_AOD_freeze_target_join_then_residual",
        "forbidden_future_order": "contact_map_or_score_before_payload_byte_hash_lock",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "release_status": f"{VERSION}_external_pdb_coordinate_payload_hash_gate",
    }])

    write_csv(PROT / "pdb_external_coordinate_payload_derivation_block.csv", [
        "block_id", "hash_gate_id", "candidate_derivation", "required_precondition", "current_status", "leakage_role", "release_status",
    ], [
        {"block_id": "PDB-EXT-HASH-BLOCK-001", "hash_gate_id": HASH_GATE_ID, "candidate_derivation": "external_residue_coordinate_table", "required_precondition": "coordinate_payload_byte_sha256_locked", "current_status": "blocked_in_v40.02r12.1", "leakage_role": "target_only_after_AOD_freeze", "release_status": f"{VERSION}_external_pdb_coordinate_payload_hash_gate"},
        {"block_id": "PDB-EXT-HASH-BLOCK-002", "hash_gate_id": HASH_GATE_ID, "candidate_derivation": "external_contact_map", "required_precondition": "coordinate_payload_byte_sha256_locked_and_residue_table_derived", "current_status": "blocked_in_v40.02r12.1", "leakage_role": "target_only_after_AOD_freeze", "release_status": f"{VERSION}_external_pdb_coordinate_payload_hash_gate"},
        {"block_id": "PDB-EXT-HASH-BLOCK-003", "hash_gate_id": HASH_GATE_ID, "candidate_derivation": "external_residual_score", "required_precondition": "evaluation_pair_boundary_declared_after_contact_map_derivation", "current_status": "blocked_in_v40.02r12.1", "leakage_role": "downstream_score_only_after_freeze_target_join", "release_status": f"{VERSION}_external_pdb_coordinate_payload_hash_gate"},
    ])

    checks = [
        ("PDB-EXT-HASH-001", "external_accession_scope_exists_before_payload_hash_gate", "scope_link", "missing_r11_accession_scope", "payload_hash_gate", "r11_scope_rows_read_first", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-002", "coordinate_payload_path_declared_before_hash_lock", "provenance_lock", "undeclared_payload_uri", "coordinate_payload_hash_gate", "external_uri_declared_before_payload_byte_fetch", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-003", "coordinate_payload_byte_sha256_required_before_residue_table", "payload_hash_lock", "unhashed_coordinate_payload", "residue_coordinate_table_derivation", "residue_table_blocked_until_byte_hash", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-004", "residue_table_derivation_blocked_until_payload_hash_lock", "derivation_quarantine", "unhashed_coordinate_payload", "residue_coordinate_table_or_contact_map", "derive_only_after_payload_byte_hash_lock", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-005", "evaluation_pairs_deferred_until_residue_table_exists", "boundary_order", "undeclared_or_coordinate_unchecked_pairs", "residual_scoring", "declare_pairs_after_payload_residue_table", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-006", "negative_support_policy_deferred_but_required_before_classifier_metrics", "metric_scope", "negative_support_absent", "MCC_or_classifier_generalization_metrics", "declare_negative_support_before_classifier_metrics", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-007", "external_payload_forbidden_as_raw_dec_or_aod_freeze_premise", "prediction_freeze_quarantine", "external_coordinate_payload_or_target_contact_rows", "raw_DEC_or_AOD_prediction_freeze", "target_payload_downstream_after_AOD_freeze", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-008", "aod_motif_curling_curls_and_sadar_precede_future_external_target_map", "detection_order", "external_PDB_target_rows", "AOD_motif_or_SADAR_detection_packet", "AOD_motif_SADAR_before_downstream_target_map", "hash_gate_only_no_score"),
        ("PDB-EXT-HASH-009", "coordinate_level_metrics_remain_deferred", "metric_quarantine", "RMSD_TM_score_GDT", "current_release_score_rows", "coordinate_metrics_after_coordinate_level_AOD_prediction_freeze", "hash_gate_only_no_score"),
    ]
    write_csv(PROT / "pdb_external_coordinate_payload_leakage_checks.csv", [
        "audit_id", "hash_gate_id", "check_name", "check_stage", "check_result", "forbidden_source", "forbidden_destination", "allowed_stage", "score_input_status", "release_status",
    ], [{
        "audit_id": i,
        "hash_gate_id": HASH_GATE_ID,
        "check_name": n,
        "check_stage": s,
        "check_result": "active_pass",
        "forbidden_source": fs,
        "forbidden_destination": fd,
        "allowed_stage": al,
        "score_input_status": st,
        "release_status": f"{VERSION}_external_pdb_coordinate_payload_hash_gate",
    } for i, n, s, fs, fd, al, st in checks])



    write_csv(PROT / "pdb_external_coordinate_payload_hash_terminology.csv", [
        "term_id", "field_name", "definition", "is_coordinate_byte_hash", "relationship_to_future_coordinate_payload_sha256", "release_status",
    ], [
        {
            "term_id": "PDB-EXT-TERM-001",
            "field_name": "payload_registration_sha256",
            "definition": "compatibility alias for the locator/policy registration hash; this is not the external mmCIF byte-payload SHA-256",
            "is_coordinate_byte_hash": "false",
            "relationship_to_future_coordinate_payload_sha256": "distinct_from_future_coordinate_payload_sha256",
            "release_status": f"{VERSION}_terminology_clarity",
        },
        {
            "term_id": "PDB-EXT-TERM-002",
            "field_name": "locator_policy_registration_sha256",
            "definition": "hash of the locked external payload locator plus boundary/readout policy card",
            "is_coordinate_byte_hash": "false",
            "relationship_to_future_coordinate_payload_sha256": "precedes_and_does_not_replace_future_coordinate_payload_sha256",
            "release_status": f"{VERSION}_terminology_clarity",
        },
        {
            "term_id": "PDB-EXT-TERM-003",
            "field_name": "coordinate_payload_sha256",
            "definition": "future SHA-256 of the actual external PDBx/mmCIF coordinate byte payload",
            "is_coordinate_byte_hash": "true_when_registered_in_future_gate",
            "relationship_to_future_coordinate_payload_sha256": "required_before_external_residue_or_contact_derivation",
            "release_status": f"{VERSION}_terminology_clarity",
        },
    ])

    write_csv(PROT / "pdb_external_coordinate_payload_carried_forward_fixture_scope.csv", [
        "fixture_scope_id", "carried_forward_file", "source_status", "relationship_to_external_1CRN_gate", "score_status", "release_status",
    ], [
        {
            "fixture_scope_id": "PDB-EXT-FIXTURE-SCOPE-001",
            "carried_forward_file": "manual-2/data/protein/pdb_mmcif_coordinate_payload_registry.csv",
            "source_status": "manual_GAS_target_only_fixture_carried_forward",
            "relationship_to_external_1CRN_gate": "not_the_external_1CRN_byte_payload",
            "score_status": "not_scored_as_external_accession_in_this_gate",
            "release_status": f"{VERSION}_carried_forward_fixture_scope",
        },
        {
            "fixture_scope_id": "PDB-EXT-FIXTURE-SCOPE-002",
            "carried_forward_file": "manual-2/data/protein/pdb_mmcif_residue_coordinate_table.csv",
            "source_status": "manual_GAS_target_only_fixture_carried_forward",
            "relationship_to_external_1CRN_gate": "not_derived_from_external_1CRN_byte_hash_lock",
            "score_status": "not_scored_as_external_accession_in_this_gate",
            "release_status": f"{VERSION}_carried_forward_fixture_scope",
        },
        {
            "fixture_scope_id": "PDB-EXT-FIXTURE-SCOPE-003",
            "carried_forward_file": "manual-2/data/protein/pdb_mmcif_contact_map_derived.csv",
            "source_status": "manual_GAS_target_only_fixture_carried_forward",
            "relationship_to_external_1CRN_gate": "not_the_external_1CRN_contact_map",
            "score_status": "not_scored_as_external_accession_in_this_gate",
            "release_status": f"{VERSION}_carried_forward_fixture_scope",
        },
    ])

    manifest = {
        "lane": "external_pdb_coordinate_payload_hash_gate",
        "version_scope": VERSION,
        "status": "external PDB coordinate payload hash/provenance gate only; no coordinate bytes are parsed, no residue table is derived, and no external-accession score is computed",
        "prior_scope": "manual-2/data/protein/pdb_external_accession_scope_declaration.csv",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "chain_id": "A",
        "coordinate_payload_path": EXTERNAL_URI,
        "coordinate_payload_path_status": "external_uri_declared_payload_bytes_not_committed",
        "coordinate_payload_sha256": "required_after_external_payload_bytes_are_registered_before_contact_derivation",
        "coordinate_payload_sha256_status": "byte_payload_hash_required_not_satisfied_in_this_gate",
        "payload_registration_sha256": reg_sha,
        "locator_policy_registration_sha256": reg_sha,
        "registration_hash_note": "payload_registration_sha256 is a compatibility alias for locator_policy_registration_sha256; it is not the external coordinate byte-payload SHA-256",
        "download_or_registration_timestamp": "2026-06-16T00:00:00Z",
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
            "coordinate_payload_byte_hash_lock",
            "residue_coordinate_table_derivation",
            "external_contact_map_derivation",
            "evaluation_pair_boundary_declaration",
            "external_accession_residual_score",
        ],
        "files": {
            "hash_gate": "manual-2/data/protein/pdb_external_coordinate_payload_hash_gate.csv",
            "provenance_lock": "manual-2/data/protein/pdb_external_coordinate_payload_provenance_lock.csv",
            "policy_lock": "manual-2/data/protein/pdb_external_coordinate_payload_policy_lock.csv",
            "derivation_block": "manual-2/data/protein/pdb_external_coordinate_payload_derivation_block.csv",
            "leakage_checks": "manual-2/data/protein/pdb_external_coordinate_payload_leakage_checks.csv",
            "terminology": "manual-2/data/protein/pdb_external_coordinate_payload_hash_terminology.csv",
            "carried_forward_fixture_scope": "manual-2/data/protein/pdb_external_coordinate_payload_carried_forward_fixture_scope.csv",
        },
        "input_order_policy": "r11 accession scope first; payload byte-hash lock second; residue/contact derivation only after payload byte-hash; AOD motif/curling-curls/SADAR freeze stays upstream of any future target join",
        "claim_discipline": "Hash/provenance gate only. This is not a coordinate-ingest release, not an external PDB contact score, and not a folding model.",
    }
    (PROT / "pdb_external_coordinate_payload_hash_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
