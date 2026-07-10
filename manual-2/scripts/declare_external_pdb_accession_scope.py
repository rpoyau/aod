#!/usr/bin/env python3
"""Emit the Manual II external PDB accession scope gate.

This script is intentionally offline and deterministic. It declares an external
RCSB PDB accession locator, boundary/contact policy, and leakage checks before
any coordinate-payload ingest or external-accession score. It does not read PDB
coordinate payloads and does not read score rows.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r11"
SCOPE_ID = "pdb_external_accession_scope_1CRN_A_v4002r11"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    # scope rows are declared first; score rows are deliberately not read here.
    scope_fields = [
        "scope_id", "version_scope", "prior_scope_id", "external_source", "source_accession", "pdb_id", "chain_id",
        "target_packet_id", "pdb_structure_target_id", "protein_id", "accession_declaration_status", "coordinate_payload_status",
        "coordinate_payload_path", "coordinate_payload_sha256", "coordinate_payload_hash_status", "chain_id_status", "residue_index_basis",
        "atom_selector", "contact_threshold_angstrom", "min_sequence_separation", "score_boundary_status", "evaluation_pair_policy",
        "candidate_residue_range", "positive_negative_support_policy", "target_map_stage", "prediction_premise_policy", "downstream_score_status",
        "coordinate_metric_policy", "alpha_fold_policy", "value_map_status", "release_status",
    ]
    write_csv(PROT / "pdb_external_accession_scope_declaration.csv", scope_fields, [{
        "scope_id": SCOPE_ID,
        "version_scope": VERSION,
        "prior_scope_id": "pdb_contact_scope_manual_GAS_multipair_v4002r10",
        "external_source": "RCSB_PDB",
        "source_accession": "1CRN",
        "pdb_id": "1CRN",
        "chain_id": "A",
        "target_packet_id": "pdb_1crn_A_locator",
        "pdb_structure_target_id": "pdb_1crn_A_mmcif_target",
        "protein_id": "pdb_1crn_A",
        "accession_declaration_status": "external_accession_declared_before_payload_ingest_or_scoring",
        "coordinate_payload_status": "deferred_not_ingested_in_this_gate",
        "coordinate_payload_path": "deferred_external_pdb_mmcif_payload_not_committed",
        "coordinate_payload_sha256": "deferred_until_coordinate_payload_ingest_gate",
        "coordinate_payload_hash_status": "required_before_any_external_accession_score",
        "chain_id_status": "declared_before_payload_ingest",
        "residue_index_basis": "one_based_residue_sequence_position_declared_before_score",
        "atom_selector": "CA",
        "contact_threshold_angstrom": "8.0",
        "min_sequence_separation": "3",
        "score_boundary_status": "declared_scope_only_no_score_rows",
        "evaluation_pair_policy": "must_be_declared_after_coordinate_payload_ingest_and_before_score",
        "candidate_residue_range": "deferred_until_payload_residue_table_exists",
        "positive_negative_support_policy": "negative_support_rows_required_before_classifier_metrics",
        "target_map_stage": "downstream_target_map_after_aod_freeze",
        "prediction_premise_policy": "external_accession_payload_forbidden_as_raw_dec_or_aod_freeze_premise",
        "downstream_score_status": "not_scored_in_this_gate",
        "coordinate_metric_policy": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "alpha_fold_policy": "separate_predicted_structure_comparator_not_scored_here",
        "value_map_status": "lambda_fold_deferred_not_attached",
        "release_status": f"{VERSION}_external_pdb_accession_scope_gate",
    }])

    write_csv(PROT / "pdb_external_accession_target_provenance.csv", [
        "provenance_id", "scope_id", "source_database", "source_accession", "download_url", "target_packet_id",
        "existing_locator_row", "structure_target_row", "chain_id", "entity_id", "coordinate_payload_status", "coordinate_payload_sha256",
        "coordinate_source_hash_status", "license_or_terms_ref", "target_source_role", "target_map_stage", "score_status", "release_status",
    ], [{
        "provenance_id": "pdb_external_accession_provenance_1CRN_A_001",
        "scope_id": SCOPE_ID,
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "download_url": "https://files.rcsb.org/download/1CRN.cif",
        "target_packet_id": "pdb_1crn_A_locator",
        "existing_locator_row": "manual-2/data/protein/pdb_structure_target_packets.csv:pdb_1crn_A_locator",
        "structure_target_row": "manual-2/data/protein/pdb_mmcif_structure_targets.csv:pdb_1crn_A_mmcif_target",
        "chain_id": "A",
        "entity_id": "deferred_until_payload_ingest",
        "coordinate_payload_status": "not_committed_external_locator_only",
        "coordinate_payload_sha256": "deferred_until_payload_ingest",
        "coordinate_source_hash_status": "hash_required_before_score",
        "license_or_terms_ref": "external_database_terms_locator_only",
        "target_source_role": "target_locator_only_not_prediction_premise",
        "target_map_stage": "downstream_after_aod_prediction_freeze",
        "score_status": "no_external_accession_score_in_this_gate",
        "release_status": f"{VERSION}_external_pdb_accession_scope_gate",
    }])

    write_csv(PROT / "pdb_external_accession_boundary_lock.csv", [
        "boundary_id", "scope_id", "source_accession", "chain_id", "residue_index_basis", "atom_selector", "contact_threshold_angstrom",
        "min_sequence_separation", "coordinate_payload_hash_requirement", "evaluation_pair_declaration_requirement",
        "negative_support_requirement", "allowed_future_score_input_order", "forbidden_future_score_input_order", "score_status", "coordinate_metric_status", "release_status",
    ], [{
        "boundary_id": "pdb_external_accession_boundary_lock_1CRN_A_001",
        "scope_id": SCOPE_ID,
        "source_accession": "1CRN",
        "chain_id": "A",
        "residue_index_basis": "one_based_residue_sequence_position",
        "atom_selector": "CA",
        "contact_threshold_angstrom": "8.0",
        "min_sequence_separation": "3",
        "coordinate_payload_hash_requirement": "required_before_any_contact_derivation_or_score",
        "evaluation_pair_declaration_requirement": "required_after_payload_derivation_and_before_residual_score",
        "negative_support_requirement": "required_before_MCC_or_classifier_generalization_metrics",
        "allowed_future_score_input_order": "scope_rows_then_frozen_AOD_packet_then_external_accession_target_rows_then_residual",
        "forbidden_future_score_input_order": "external_coordinate_payload_before_AOD_prediction_freeze",
        "score_status": "boundary_declared_no_score",
        "coordinate_metric_status": "deferred_no_RMSD_TM_score_GDT",
        "release_status": f"{VERSION}_external_pdb_accession_scope_gate",
    }])

    checks = [
        ("PDB-EXT-SCOPE-001", "external_accession_declared_before_payload_ingest", "scope_input_lock", "undeclared_external_accession", "coordinate_payload_ingest_or_score", "accession_scope_declaration_before_payload_ingest", "scope_rows_only_no_score"),
        ("PDB-EXT-SCOPE-002", "coordinate_payload_hash_status_recorded_before_score", "provenance_lock", "unhashed_coordinate_payload", "external_accession_score", "hash_required_before_any_future_score", "scope_rows_only_no_score"),
        ("PDB-EXT-SCOPE-003", "chain_id_residue_basis_atom_selector_cutoff_declared_before_score", "boundary_lock", "undeclared_contact_boundary", "external_accession_score", "boundary_lock_before_contact_derivation", "scope_rows_only_no_score"),
        ("PDB-EXT-SCOPE-004", "external_accession_target_rows_forbidden_as_prediction_premises", "prediction_freeze_quarantine", "RCSB_PDB_coordinate_payload_or_target_rows", "aod_contact_prediction_freeze_or_raw_dec_inputs", "target_rows_downstream_after_freeze", "scope_rows_only_no_score"),
        ("PDB-EXT-SCOPE-005", "future_residual_order_freeze_first_target_join_second", "future_score_order", "target_contact_rows_before_frozen_AOD_packet", "residual_or_score_output", "frozen_AOD_then_target_join_then_residual", "scope_rows_only_no_score"),
        ("PDB-EXT-SCOPE-006", "coordinate_level_metrics_remain_deferred", "metric_quarantine", "coordinate_level_RMSD_TM_score_GDT", "current_release_score_rows", "coordinate_metrics_after_coordinate_level_AOD_prediction_freeze", "scope_rows_only_no_score"),
        ("PDB-EXT-SCOPE-007", "aod_motif_curling_curls_and_sadar_precede_external_target_map", "detection_order", "external_PDB_target_rows", "AOD_motif_or_SADAR_detection_packet", "AOD_motif_SADAR_before_downstream_target_map", "scope_rows_only_no_score"),
    ]
    write_csv(PROT / "pdb_external_accession_leakage_checks.csv", [
        "audit_id", "scope_id", "check_name", "check_stage", "check_result", "forbidden_source", "forbidden_destination", "allowed_stage", "score_input_status", "release_status",
    ], [{
        "audit_id": i,
        "scope_id": SCOPE_ID,
        "check_name": n,
        "check_stage": s,
        "check_result": "active_pass",
        "forbidden_source": fs,
        "forbidden_destination": fd,
        "allowed_stage": al,
        "score_input_status": st,
        "release_status": f"{VERSION}_external_pdb_accession_scope_gate",
    } for i, n, s, fs, fd, al, st in checks])

    manifest = {
        "lane": "external_pdb_accession_scope_gate",
        "version_scope": VERSION,
        "status": "external PDB accession scope and provenance gate only; no external coordinate payload ingest, no contact residual score, and no coordinate-level folding claim",
        "external_accession_scope": {
            "source_database": "RCSB_PDB",
            "source_accession": "1CRN",
            "chain_id": "A",
            "target_packet_id": "pdb_1crn_A_locator",
            "coordinate_payload_status": "deferred_not_ingested_in_this_gate",
            "coordinate_payload_hash_status": "required_before_any_external_accession_score",
            "atom_selector": "CA",
            "contact_threshold_angstrom": "8.0",
            "min_sequence_separation": "3",
        },
        "input_order_policy": "declare external accession and boundary; keep AOD motif/curling-curls/SADAR freeze upstream; join external target rows only downstream after freeze; compute residual only in a later declared score gate",
        "files": {
            "scope_declaration": "manual-2/data/protein/pdb_external_accession_scope_declaration.csv",
            "target_provenance": "manual-2/data/protein/pdb_external_accession_target_provenance.csv",
            "boundary_lock": "manual-2/data/protein/pdb_external_accession_boundary_lock.csv",
            "leakage_checks": "manual-2/data/protein/pdb_external_accession_leakage_checks.csv",
        },
        "deferred": [
            "coordinate_payload_ingest", "external_accession_contact_derivation", "external_accession_residual_score",
            "RMSD", "TM-score", "GDT", "AlphaFold scoring", "coordinate-level AOD prediction", "lambda_fold",
        ],
        "claim_discipline": "Scope/provenance gate only. This is not a PDB validation and not a folding model.",
    }
    (PROT / "pdb_external_accession_scope_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
