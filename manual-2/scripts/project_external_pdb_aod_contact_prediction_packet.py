#!/usr/bin/env python3
"""Project the frozen AOD contact packet onto the frozen external PDB boundary.

This gate does not compute residuals or scores. It reads the external evaluation
pair boundary only as a frozen pair list and intentionally ignores target contact
values. Because no alignment from the frozen GAS AOD packet to external 1CRN is
declared in this milestone, every external pair is projected as out_of_scope.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2/data/protein"
VERSION = "v40.02r17"
VERSION_LABEL = "v40.02r17_aod_contact_prediction_packet_projection_gate"
BOUNDARY = PROT / "pdb_external_evaluation_pair_boundary.csv"
BOUNDARY_MANIFEST = PROT / "pdb_external_evaluation_pair_manifest.json"
AOD_FREEZE = PROT / "aod_contact_prediction_freeze.csv"
AOD_RECLOSURE = PROT / "aod_reclosure_motif_predictions.csv"
SADAR_CONTEXT_ID = "sadar_mol_005"
AOD_PACKET_ID = "aod_reclosure_pred_002"
AOD_CONTACT_PACKET_ID = "chain_GAS_tripeptide_seed"
PROJECTION_RULE = "no_declared_alignment_between_GAS_AOD_packet_and_external_1CRN_boundary_all_pairs_out_of_scope"
ABSTENTION_POLICY = "abstain_only_after_declared_alignment; without alignment use out_of_scope"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def pair_id(row: dict[str, str]) -> str:
    return (
        f"{row['source_accession']}_{row['chain_id']}_model{row['model_id']}_"
        f"{row['atom_selector']}_label{int(row['label_seq_i']):04d}_label{int(row['label_seq_j']):04d}"
    )


def main() -> None:
    manifest = json.loads(BOUNDARY_MANIFEST.read_text(encoding="utf-8"))
    boundary_sha = sha256_file(BOUNDARY)
    if manifest["boundary_sha256"] != boundary_sha:
        raise RuntimeError("r16 evaluation boundary hash does not match manifest")
    aod_freeze_sha = sha256_file(AOD_FREEZE)
    aod_reclosure_sha = sha256_file(AOD_RECLOSURE)
    boundary_rows = read_csv(BOUNDARY)
    if len(boundary_rows) != int(manifest["evaluation_pair_count"]):
        raise RuntimeError("boundary row count does not match r16 manifest")
    aod_rows = read_csv(AOD_FREEZE)
    reclosure_rows = read_csv(AOD_RECLOSURE)
    if not any(row["chain_id"] == AOD_CONTACT_PACKET_ID for row in aod_rows):
        raise RuntimeError("frozen GAS AOD contact packet is missing")
    if not any(row["reclosure_id"] == AOD_PACKET_ID for row in reclosure_rows):
        raise RuntimeError("frozen GAS AOD reclosure packet is missing")

    pair_list_text = "\n".join(pair_id(row) for row in boundary_rows) + "\n"
    pair_list_sha = sha256_text(pair_list_text)
    projection_rows: list[dict[str, str]] = []
    for idx, row in enumerate(boundary_rows, start=1):
        projection_rows.append({
            "projection_id": f"pdb_ext_aod_projection_1CRN_A_{idx:04d}",
            "evaluation_boundary_id": row["evaluation_pair_boundary_id"],
            "evaluation_boundary_sha256": boundary_sha,
            "evaluation_pair_list_sha256": pair_list_sha,
            "evaluation_pair_row_id": row["evaluation_pair_row_id"],
            "pair_id": pair_id(row),
            "source_database": row["source_database"],
            "source_accession": row["source_accession"],
            "chain_id": row["chain_id"],
            "model_id": row["model_id"],
            "atom_selector": row["atom_selector"],
            "label_seq_i": row["label_seq_i"],
            "label_seq_j": row["label_seq_j"],
            "auth_seq_i": row["auth_seq_i"],
            "auth_seq_j": row["auth_seq_j"],
            "residue_name_i": row["residue_name_i"],
            "residue_name_j": row["residue_name_j"],
            "aod_packet_id": AOD_CONTACT_PACKET_ID,
            "aod_reclosure_id": AOD_PACKET_ID,
            "aod_packet_sha256": aod_freeze_sha,
            "aod_reclosure_sha256": aod_reclosure_sha,
            "sadar_context_id": SADAR_CONTEXT_ID,
            "prediction_state": "out_of_scope",
            "O_hat": "",
            "prediction_coverage_status": "out_of_scope_no_declared_GAS_to_1CRN_alignment",
            "abstention_policy": ABSTENTION_POLICY,
            "projection_rule": PROJECTION_RULE,
            "target_value_read_status": "not_read_by_projection_gate",
            "residual_status": "not_computed_in_v40.02r17",
            "score_status": "projection_gate_only_no_residual_score",
            "leakage_role": "frozen_aod_packet_projected_after_boundary_without_target_value_read",
            "release_status": VERSION_LABEL,
        })

    projection_fields = [
        "projection_id", "evaluation_boundary_id", "evaluation_boundary_sha256", "evaluation_pair_list_sha256",
        "evaluation_pair_row_id", "pair_id", "source_database", "source_accession", "chain_id", "model_id",
        "atom_selector", "label_seq_i", "label_seq_j", "auth_seq_i", "auth_seq_j", "residue_name_i",
        "residue_name_j", "aod_packet_id", "aod_reclosure_id", "aod_packet_sha256", "aod_reclosure_sha256",
        "sadar_context_id", "prediction_state", "O_hat", "prediction_coverage_status", "abstention_policy",
        "projection_rule", "target_value_read_status", "residual_status", "score_status", "leakage_role", "release_status",
    ]
    projection_path = PROT / "pdb_external_aod_contact_projection.csv"
    write_csv(projection_path, projection_fields, projection_rows)

    counts = {
        "contact": 0,
        "noncontact": 0,
        "abstain": 0,
        "out_of_scope": len(projection_rows),
    }
    summary = {
        "projection_gate_id": "pdb_external_aod_projection_1CRN_A_v4002r17",
        "evaluation_boundary_id": manifest["files"]["evaluation_pair_boundary"],
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "evaluation_pair_count": str(len(projection_rows)),
        "projection_contact_count": str(counts["contact"]),
        "projection_noncontact_count": str(counts["noncontact"]),
        "projection_abstain_count": str(counts["abstain"]),
        "projection_out_of_scope_count": str(counts["out_of_scope"]),
        "aod_packet_id": AOD_CONTACT_PACKET_ID,
        "aod_reclosure_id": AOD_PACKET_ID,
        "aod_packet_sha256": aod_freeze_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "sadar_context_id": SADAR_CONTEXT_ID,
        "projection_rule": PROJECTION_RULE,
        "target_value_read_status": "not_read_by_projection_gate",
        "residual_status": "not_computed_in_v40.02r17",
        "score_status": "projection_gate_only_no_residual_score",
        "lambda_fold_status": "deferred_not_attached",
        "release_status": VERSION_LABEL,
    }
    write_csv(PROT / "pdb_external_aod_contact_projection_summary.csv", list(summary.keys()), [summary])

    policy = {
        "projection_policy_id": "pdb_external_aod_projection_policy_1CRN_A_v4002r17",
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "aod_packet_sha256": aod_freeze_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "projection_state_domain": "contact|noncontact|abstain|out_of_scope",
        "projection_rule": PROJECTION_RULE,
        "abstention_policy": ABSTENTION_POLICY,
        "alignment_status": "no_declared_external_1CRN_to_GAS_alignment_in_v40.02r17",
        "target_value_policy": "target contact values are not read by this projection gate",
        "residual_score_policy": "not computed until a later gate joins frozen O_hat with frozen O",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "release_status": VERSION_LABEL,
    }
    write_csv(PROT / "pdb_external_aod_contact_projection_policy_application.csv", list(policy.keys()), [policy])

    checks = [
        ("evaluation_boundary_hash_matches_r16_manifest", "r16 evaluation boundary hash is verified before projection rows are emitted"),
        ("evaluation_pair_list_hash_frozen_before_projection", "pair IDs are hashed before the projection packet is written"),
        ("frozen_AOD_packet_hash_recorded", "aod_contact_prediction_freeze.csv SHA-256 is recorded"),
        ("frozen_reclosure_packet_hash_recorded", "aod_reclosure_motif_predictions.csv SHA-256 is recorded"),
        ("SADAR_context_recorded_before_projection", "sadar_mol_005 is recorded before downstream target comparison"),
        ("projection_states_explicit", "contact, noncontact, abstain, and out_of_scope are the declared state domain"),
        ("no_declared_external_alignment_all_pairs_out_of_scope", "without a declared 1CRN-to-GAS alignment, every external pair is out_of_scope"),
        ("target_contact_values_not_read_in_r17", "projection rows ignore target contact values and carry only pair identity"),
        ("no_external_residual_score_computed_in_r17", "Delta_Z and delta3 rows are not computed by this gate"),
        ("coordinate_metrics_remain_deferred", "RMSD/TM-score/GDT remain deferred"),
        ("AOD_motif_curling_curls_and_SADAR_precede_downstream_target_join", "AOD motif/SADAR freeze remains upstream of future target join"),
    ]
    check_rows = [
        {
            "check_id": f"PDB-EXT-AOD-PROJ-CHECK-{idx:03d}",
            "check_name": name,
            "check_result": "active_pass",
            "detail": detail,
            "projection_input_status": "projection_gate_only_boundary_plus_frozen_AOD_packet_no_target_values_no_score",
            "release_status": VERSION_LABEL,
        }
        for idx, (name, detail) in enumerate(checks, start=1)
    ]
    write_csv(PROT / "pdb_external_aod_contact_projection_leakage_checks.csv", list(check_rows[0].keys()), check_rows)

    manifest_obj = {
        "lane": "external_pdb_aod_contact_prediction_projection_gate",
        "version_scope": VERSION,
        "status": "projection of the frozen AOD contact/reclosure packet onto the frozen r16 external evaluation boundary; no target contact values read, no residual score, no coordinate metrics, no folding value map",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "evaluation_pair_count": len(projection_rows),
        "projection_contact_count": counts["contact"],
        "projection_noncontact_count": counts["noncontact"],
        "projection_abstain_count": counts["abstain"],
        "projection_out_of_scope_count": counts["out_of_scope"],
        "aod_packet_id": AOD_CONTACT_PACKET_ID,
        "aod_reclosure_id": AOD_PACKET_ID,
        "aod_packet_sha256": aod_freeze_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "sadar_context_id": SADAR_CONTEXT_ID,
        "projection_rule": PROJECTION_RULE,
        "target_value_read_status": "not_read_by_projection_gate",
        "residual_status": "not_computed_in_v40.02r17",
        "score_status": "projection_gate_only_no_residual_score",
        "blocked_until_later_gate": [
            "declared_external_alignment_or_projection_rule_with_coverage",
            "external_accession_residual_score",
            "coordinate_level_metric_score",
            "released_lambda_fold"
        ],
        "files": {
            "projection": "manual-2/data/protein/pdb_external_aod_contact_projection.csv",
            "summary": "manual-2/data/protein/pdb_external_aod_contact_projection_summary.csv",
            "policy_application": "manual-2/data/protein/pdb_external_aod_contact_projection_policy_application.csv",
            "leakage_checks": "manual-2/data/protein/pdb_external_aod_contact_projection_leakage_checks.csv"
        },
        "projection_sha256": sha256_file(projection_path),
        "summary_sha256": sha256_file(PROT / "pdb_external_aod_contact_projection_summary.csv"),
        "policy_application_sha256": sha256_file(PROT / "pdb_external_aod_contact_projection_policy_application.csv"),
        "leakage_checks_sha256": sha256_file(PROT / "pdb_external_aod_contact_projection_leakage_checks.csv"),
        "claim_discipline": "projection rows are AOD-side coverage rows over a frozen boundary; target O_ij values join only in a later residual gate"
    }
    (PROT / "pdb_external_aod_contact_projection_manifest.json").write_text(json.dumps(manifest_obj, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
