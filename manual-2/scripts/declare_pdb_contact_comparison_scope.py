#!/usr/bin/env python3
"""Declare the v40.02r08 PDB/mmCIF contact-comparison scope.

This offline generator does not score any AOD-vs-PDB row. It reads the
already-frozen v40.02r05 AOD contact/reclosure prediction packets and the
already-derived v40.02r07 PDBx/mmCIF target contact rows only to declare the
future comparison scope, leakage checks, target provenance, and residual
coordinate schema. It emits no TP/FP/FN/TN counts and no contact-score rows.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r08"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def pair_list(rows: Iterable[dict[str, str]], i_col: str = "residue_i", j_col: str = "residue_j") -> list[str]:
    return sorted({f"{row[i_col]}-{row[j_col]}" for row in rows}, key=lambda x: tuple(map(int, x.split("-"))))


def build_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    freeze_path = PROT / "aod_contact_prediction_freeze.csv"
    target_path = PROT / "pdb_mmcif_contact_map_derived.csv"
    distance_path = PROT / "pdb_mmcif_distance_matrix_derived.csv"
    payload_registry_path = PROT / "pdb_mmcif_coordinate_payload_registry.csv"
    derivation_manifest_path = PROT / "pdb_mmcif_contact_derivation_manifest.json"

    freeze_rows = read_csv(freeze_path)
    target_rows = read_csv(target_path)
    payload = read_csv(payload_registry_path)[0]

    candidate_predictions = [
        r for r in freeze_rows
        if r["chain_id"] == "chain_GAS_tripeptide_seed"
        and int(r["pair_separation"]) >= int(payload["min_sequence_separation"])
    ]
    all_gas_predictions = [r for r in freeze_rows if r["chain_id"] == "chain_GAS_tripeptide_seed"]
    candidate_targets = [
        r for r in target_rows
        if r["payload_id"] == payload["payload_id"] and r["contact_scope_status"] == "in_scope"
    ]
    excluded_targets = [r for r in target_rows if r["contact_scope_status"] != "in_scope"]

    declared_prediction_pairs = pair_list(candidate_predictions)
    declared_target_pairs = pair_list(candidate_targets)
    declared_evaluation_pairs = sorted(
        set(declared_prediction_pairs) & set(declared_target_pairs),
        key=lambda x: tuple(map(int, x.split("-"))),
    )
    excluded_prediction_pairs = sorted(
        set(pair_list(all_gas_predictions)) - set(declared_prediction_pairs),
        key=lambda x: tuple(map(int, x.split("-"))),
    )

    scope_id = "pdb_contact_scope_manual_GAS_v4002r08"
    schema_id = "pdb_contact_residual_schema_binary_contact_delta3_v4002r08"

    scope_rows = [{
        "scope_id": scope_id,
        "version_scope": VERSION,
        "prediction_freeze_version": "v40.02r05",
        "prediction_model_id": "AOD-CRPF-v40.02r05",
        "chain_id": "chain_GAS_tripeptide_seed",
        "protein_id": payload["protein_id"],
        "target_payload_id": payload["payload_id"],
        "target_source_accession": payload["source_accession"],
        "score_scope": "pdb_mmcif_derived_contact_subset_min_sequence_separation",
        "contact_threshold_angstrom": payload["contact_threshold_angstrom"],
        "min_sequence_separation": payload["min_sequence_separation"],
        "declared_prediction_pairs": ";".join(declared_prediction_pairs),
        "declared_target_pairs": ";".join(declared_target_pairs),
        "declared_evaluation_pairs": ";".join(declared_evaluation_pairs),
        "excluded_prediction_pairs": ";".join(excluded_prediction_pairs) or "none",
        "allowed_target_rows": ";".join(r["derived_contact_id"] + ":in_scope" for r in candidate_targets),
        "excluded_target_rows": ";".join(r["derived_contact_id"] + ":" + r["contact_scope_status"] for r in excluded_targets),
        "target_contact_map_hash": payload["contact_map_hash"],
        "target_distance_matrix_hash": payload["distance_matrix_hash"],
        "residual_schema_id": schema_id,
        "alpha_fold_policy": "alphafold_predicted_structure_comparator_not_ground_truth_not_scored_in_v40.02r08",
        "coordinate_metric_policy": "RMSD_TM_score_GDT_absent_until_coordinate_level_AOD_prediction_freeze",
        "score_status": "scope_declared_no_score_in_v40.02r08",
        "comparison_status": "future_score_requires_separate_milestone",
        "value_map_status": "quarantined_scope_declaration_no_lambda_fold",
        "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
    }]

    provenance_rows = [{
        "target_provenance_id": "pdb_contact_target_provenance_manual_GAS_v4002r08",
        "scope_id": scope_id,
        "source_class": payload["source"],
        "source_accession": payload["source_accession"],
        "protein_id": payload["protein_id"],
        "payload_id": payload["payload_id"],
        "payload_path": payload["payload_file"],
        "payload_sha256": payload["payload_sha256"],
        "derived_contact_source": "manual-2/data/protein/pdb_mmcif_contact_map_derived.csv",
        "distance_matrix_source": "manual-2/data/protein/pdb_mmcif_distance_matrix_derived.csv",
        "derivation_manifest_source": "manual-2/data/protein/pdb_mmcif_contact_derivation_manifest.json",
        "contact_map_hash": payload["contact_map_hash"],
        "distance_matrix_hash": payload["distance_matrix_hash"],
        "target_provenance_status": "manual_fixture_provenance_declared_not_external_validation",
        "external_accession_status": "not_external_pdb_accession_in_v40.02r08",
        "leakage_role": "target_only_after_prediction_freeze",
        "score_status": "not_scored_in_v40.02r08",
        "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
    }]

    residual_rows = [
        {
            "residual_schema_id": schema_id,
            "coordinate_name": "Delta_Z_ij",
            "definition": "predicted_contact_ij - target_contact_ij",
            "input_columns": "predicted_contact,target_contact",
            "metric_status": "declared_not_computed_in_v40.02r08",
            "metric_class": "pairwise_integer_residual",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
        {
            "residual_schema_id": schema_id,
            "coordinate_name": "delta3_contact_ij",
            "definition": "Delta_Z_ij mod 3 with sign/error-class ledger",
            "input_columns": "Delta_Z_ij",
            "metric_status": "declared_not_computed_in_v40.02r08",
            "metric_class": "pairwise_delta3_residual",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
        {
            "residual_schema_id": schema_id,
            "coordinate_name": "TP_FP_FN_TN",
            "definition": "binary contact confusion counts over declared_evaluation_pairs",
            "input_columns": "predicted_contact,target_contact",
            "metric_status": "declared_not_computed_in_v40.02r08",
            "metric_class": "contact_map_binary_count",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
        {
            "residual_schema_id": schema_id,
            "coordinate_name": "precision_recall_F1_Jaccard_MCC",
            "definition": "summary metrics computed only after a future score milestone emits TP/FP/FN/TN",
            "input_columns": "TP,FP,FN,TN",
            "metric_status": "declared_not_computed_in_v40.02r08",
            "metric_class": "contact_map_summary_metric",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
        {
            "residual_schema_id": schema_id,
            "coordinate_name": "RMSD_TM_score_GDT",
            "definition": "coordinate-level metrics are absent unless a coordinate-level AOD prediction freeze exists",
            "input_columns": "coordinate_prediction,target_coordinates",
            "metric_status": "deferred_absent_no_coordinate_level_prediction",
            "metric_class": "coordinate_level_metric_absent",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
    ]

    leakage_rows = [
        {
            "check_id": "PDB-SCOPE-LEAK-001",
            "scope_id": scope_id,
            "forbidden_source": "pdb_mmcif_coordinate_payloads_contact_maps_distance_matrices",
            "forbidden_destination": "aod_contact_reclosure_prediction_freeze_inputs",
            "allowed_stage": "comparison_scope_declaration_after_prediction_freeze",
            "check_status": "active_pass",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
        {
            "check_id": "PDB-SCOPE-LEAK-002",
            "scope_id": scope_id,
            "forbidden_source": "pdb_mmcif_contact_comparison_scope_rows",
            "forbidden_destination": "prediction_model_registry_or_freeze_generator",
            "allowed_stage": "comparison_scope_declaration_only",
            "check_status": "active_pass",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
        {
            "check_id": "PDB-SCOPE-LEAK-003",
            "scope_id": scope_id,
            "forbidden_source": "alphafold_predicted_structure_coordinates_confidence_fields",
            "forbidden_destination": "aod_contact_reclosure_prediction_freeze_inputs",
            "allowed_stage": "future_comparator_lane_after_prediction_freeze_only",
            "check_status": "active_pass",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
        {
            "check_id": "PDB-SCOPE-LEAK-004",
            "scope_id": scope_id,
            "forbidden_source": "scope_declaration_rows",
            "forbidden_destination": "protein_contact_score_without_future_score_milestone",
            "allowed_stage": "not_scored_in_v40.02r08",
            "check_status": "active_pass",
            "release_status": "v40.02r08_pdb_contact_comparison_scope_declaration",
        },
    ]

    manifest = {
        "lane": "pdb_contact_comparison_scope_declaration",
        "version_scope": VERSION,
        "status": "declared_no_expanded_score_scope_only",
        "files": {
            "scope_declaration": "manual-2/data/protein/pdb_contact_comparison_scope_declaration.csv",
            "target_provenance": "manual-2/data/protein/pdb_contact_comparison_target_provenance.csv",
            "residual_coordinates": "manual-2/data/protein/pdb_contact_comparison_residual_coordinates.csv",
            "leakage_checks": "manual-2/data/protein/pdb_contact_comparison_leakage_checks.csv",
        },
        "prediction_inputs": [
            "manual-2/data/protein/aod_contact_prediction_freeze.csv",
            "manual-2/data/protein/aod_reclosure_motif_predictions.csv",
        ],
        "target_inputs": [
            "manual-2/data/protein/pdb_mmcif_contact_map_derived.csv",
            "manual-2/data/protein/pdb_mmcif_distance_matrix_derived.csv",
            "manual-2/data/protein/pdb_mmcif_coordinate_payload_registry.csv",
        ],
        "input_hashes": {
            "aod_contact_prediction_freeze": sha256_file(freeze_path),
            "pdb_mmcif_contact_map_derived": sha256_file(target_path),
            "pdb_mmcif_distance_matrix_derived": sha256_file(distance_path),
            "pdb_mmcif_coordinate_payload_registry": sha256_file(payload_registry_path),
            "pdb_mmcif_contact_derivation_manifest": sha256_file(derivation_manifest_path),
        },
        "score_policy": "no TP/FP/FN/TN, precision, recall, F1, Jaccard, MCC, RMSD, TM-score, or GDT computed in v40.02r08",
        "leakage_policy": "target rows may be read only after the v40.02r05 prediction freeze; target rows remain forbidden as raw D.E.C. or prediction-freeze premises",
        "claim_discipline": "scope declaration gate only; no expanded AOD-vs-PDB score, no coordinate-level prediction, no active lambda_fold",
        "next_milestone": "v40.02r09 -- Scoped PDB Contact-Map Residual Pilot",
    }
    return scope_rows, provenance_rows, residual_rows, leakage_rows, manifest


def main() -> int:
    scope, provenance, residual, leakage, manifest = build_rows()
    write_csv(PROT / "pdb_contact_comparison_scope_declaration.csv", scope, [
        "scope_id", "version_scope", "prediction_freeze_version", "prediction_model_id", "chain_id", "protein_id", "target_payload_id", "target_source_accession", "score_scope", "contact_threshold_angstrom", "min_sequence_separation", "declared_prediction_pairs", "declared_target_pairs", "declared_evaluation_pairs", "excluded_prediction_pairs", "allowed_target_rows", "excluded_target_rows", "target_contact_map_hash", "target_distance_matrix_hash", "residual_schema_id", "alpha_fold_policy", "coordinate_metric_policy", "score_status", "comparison_status", "value_map_status", "release_status"
    ])
    write_csv(PROT / "pdb_contact_comparison_target_provenance.csv", provenance, [
        "target_provenance_id", "scope_id", "source_class", "source_accession", "protein_id", "payload_id", "payload_path", "payload_sha256", "derived_contact_source", "distance_matrix_source", "derivation_manifest_source", "contact_map_hash", "distance_matrix_hash", "target_provenance_status", "external_accession_status", "leakage_role", "score_status", "release_status"
    ])
    write_csv(PROT / "pdb_contact_comparison_residual_coordinates.csv", residual, [
        "residual_schema_id", "coordinate_name", "definition", "input_columns", "metric_status", "metric_class", "release_status"
    ])
    write_csv(PROT / "pdb_contact_comparison_leakage_checks.csv", leakage, [
        "check_id", "scope_id", "forbidden_source", "forbidden_destination", "allowed_stage", "check_status", "release_status"
    ])
    (PROT / "pdb_contact_comparison_scope_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Remove earlier draft aliases if present; the canonical v40.02r08 files use
    # the comparison_scope_declaration names above.
    for name in [
        "pdb_contact_comparison_scope_registry.csv",
        "pdb_contact_comparison_input_lock.csv",
        "pdb_contact_target_provenance_registry.csv",
        "pdb_contact_residual_coordinate_schema.csv",
    ]:
        path = PROT / name
        if path.exists():
            path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
