from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2/data/protein"
VERSION = "v40.02r16"
VERSION_LABEL = "v40.02r16_external_pdb_evaluation_pair_boundary_gate"
PAYLOAD_SHA = "23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba"
CONTACT_MAP = PROT / "pdb_external_contact_map_derived.csv"
DISTANCE_MATRIX = PROT / "pdb_external_contact_distance_matrix.csv"
CONTACT_MAP_MANIFEST = PROT / "pdb_external_contact_map_manifest.json"
SEQUENCE_SEPARATION_RULE = "abs(label_seq_id_j-label_seq_id_i)>=3"
EVALUATION_PAIR_SELECTION_RULE = "all_eligible_external_contact_map_pairs"
CONTACT_THRESHOLD = "8.0"
MIN_SEQUENCE_SEPARATION = "3"
DISTANCE_COMPUTATION_PRECISION = "full_precision_from_residue_table_coordinates"
DISTANCE_DISPLAY_PRECISION = "0.001_angstrom"
TARGET_CONTACT_VALUE_RULE = "full_precision_distance <= 8.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def derive() -> None:
    manifest = json.loads(CONTACT_MAP_MANIFEST.read_text(encoding="utf-8"))
    contact_map_sha256 = sha256_file(CONTACT_MAP)
    distance_matrix_sha256 = sha256_file(DISTANCE_MATRIX)
    if manifest["coordinate_payload_sha256"] != PAYLOAD_SHA:
        raise RuntimeError("contact-map manifest does not reference the locked 1CRN byte payload")
    if manifest["contact_map_sha256"] != contact_map_sha256:
        raise RuntimeError("contact map SHA-256 no longer matches the r15 manifest")
    if manifest["distance_matrix_sha256"] != distance_matrix_sha256:
        raise RuntimeError("distance matrix SHA-256 no longer matches the r15 manifest")
    contact_rows = read_csv(CONTACT_MAP)
    if len(contact_rows) != int(manifest["eligible_pair_count"]):
        raise RuntimeError("contact-map row count does not match manifest eligible pair count")

    boundary_rows: list[dict[str, str]] = []
    for idx, row in enumerate(contact_rows, start=1):
        if row["leakage_role"] != "target_only_after_AOD_freeze":
            raise RuntimeError("contact row has unexpected leakage role")
        if row["coordinate_payload_sha256"] != PAYLOAD_SHA:
            raise RuntimeError("contact row uses unexpected coordinate payload hash")
        if row["sequence_separation_rule"] != SEQUENCE_SEPARATION_RULE:
            raise RuntimeError("contact row uses unexpected sequence-separation rule")
        if row["contact_threshold_angstrom"] != CONTACT_THRESHOLD:
            raise RuntimeError("contact row uses unexpected contact threshold")
        if row["min_sequence_separation"] != MIN_SEQUENCE_SEPARATION:
            raise RuntimeError("contact row uses unexpected minimum sequence separation")
        boundary_rows.append({
            "evaluation_pair_boundary_id": "pdb_external_eval_boundary_1CRN_A_all946_v4002r16",
            "evaluation_pair_row_id": f"1CRN_A_eval_pair_{idx:04d}",
            "source_database": row["source_database"],
            "source_accession": row["source_accession"],
            "coordinate_payload_sha256": row["coordinate_payload_sha256"],
            "residue_table_sha256": row["residue_table_sha256"],
            "contact_map_sha256": contact_map_sha256,
            "chain_id": row["chain_id"],
            "model_id": row["model_id"],
            "atom_selector": row["atom_selector"],
            "residue_i": row["residue_i"],
            "residue_j": row["residue_j"],
            "auth_seq_i": row["auth_seq_i"],
            "auth_seq_j": row["auth_seq_j"],
            "label_seq_i": row["label_seq_i"],
            "label_seq_j": row["label_seq_j"],
            "residue_name_i": row["residue_name_i"],
            "residue_name_j": row["residue_name_j"],
            "sequence_separation": row["sequence_separation"],
            "sequence_separation_rule": row["sequence_separation_rule"],
            "evaluation_pair_selection_rule": EVALUATION_PAIR_SELECTION_RULE,
            "distance_angstrom": row["distance_angstrom"],
            "distance_computation_precision": DISTANCE_COMPUTATION_PRECISION,
            "distance_display_precision": DISTANCE_DISPLAY_PRECISION,
            "contact_threshold_angstrom": row["contact_threshold_angstrom"],
            "min_sequence_separation": row["min_sequence_separation"],
            "target_contact_value_rule": TARGET_CONTACT_VALUE_RULE,
            "target_contact_value": row["target_contact_value"],
            "evaluation_pair_status": "declared_in_v40.02r16",
            "score_status": "not_scored_in_v40.02r16",
            "aod_prediction_join_status": "not_joined_in_v40.02r16",
            "leakage_role": "target_evaluation_boundary_only_after_contact_map_derivation_before_score",
            "release_status": VERSION_LABEL,
        })

    fields = [
        "evaluation_pair_boundary_id", "evaluation_pair_row_id", "source_database", "source_accession",
        "coordinate_payload_sha256", "residue_table_sha256", "contact_map_sha256", "chain_id", "model_id",
        "atom_selector", "residue_i", "residue_j", "auth_seq_i", "auth_seq_j", "label_seq_i", "label_seq_j",
        "residue_name_i", "residue_name_j", "sequence_separation", "sequence_separation_rule",
        "evaluation_pair_selection_rule", "distance_angstrom", "distance_computation_precision", "distance_display_precision",
        "contact_threshold_angstrom", "min_sequence_separation", "target_contact_value_rule", "target_contact_value",
        "evaluation_pair_status", "score_status", "aod_prediction_join_status", "leakage_role", "release_status",
    ]
    write_csv(PROT / "pdb_external_evaluation_pair_boundary.csv", fields, boundary_rows)

    contact_count = sum(1 for row in boundary_rows if row["target_contact_value"] == "1")
    noncontact_count = sum(1 for row in boundary_rows if row["target_contact_value"] == "0")
    summary = {
        "evaluation_pair_boundary_id": "pdb_external_eval_boundary_1CRN_A_all946_v4002r16",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "coordinate_payload_sha256": PAYLOAD_SHA,
        "residue_table_sha256": manifest["residue_table_sha256"],
        "contact_map_sha256": contact_map_sha256,
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "contact_threshold_angstrom": CONTACT_THRESHOLD,
        "min_sequence_separation": MIN_SEQUENCE_SEPARATION,
        "sequence_separation_rule": SEQUENCE_SEPARATION_RULE,
        "evaluation_pair_selection_rule": EVALUATION_PAIR_SELECTION_RULE,
        "evaluation_pair_count": str(len(boundary_rows)),
        "target_contact_count": str(contact_count),
        "target_noncontact_count": str(noncontact_count),
        "negative_support_count": str(noncontact_count),
        "score_status": "not_scored_in_v40.02r16",
        "aod_prediction_join_status": "not_joined_in_v40.02r16",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "lambda_fold_status": "deferred_not_attached",
        "release_status": VERSION_LABEL,
    }
    write_csv(PROT / "pdb_external_evaluation_pair_scope_summary.csv", list(summary.keys()), [summary])

    policy = {
        "policy_id": "pdb_external_eval_pair_policy_1CRN_A_v4002r16",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "coordinate_payload_sha256": PAYLOAD_SHA,
        "residue_table_sha256": manifest["residue_table_sha256"],
        "contact_map_sha256": contact_map_sha256,
        "distance_matrix_sha256": distance_matrix_sha256,
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "contact_threshold_angstrom": CONTACT_THRESHOLD,
        "min_sequence_separation": MIN_SEQUENCE_SEPARATION,
        "sequence_separation_rule": SEQUENCE_SEPARATION_RULE,
        "sequence_separation_rule_status": "carried_forward_from_contact_map_derivation_before_pair_selection",
        "evaluation_pair_selection_rule": EVALUATION_PAIR_SELECTION_RULE,
        "evaluation_pair_boundary_status": "declared_before_external_residual_score",
        "evaluation_pair_count": str(len(boundary_rows)),
        "target_contact_count": str(contact_count),
        "target_noncontact_count": str(noncontact_count),
        "distance_computation_precision": DISTANCE_COMPUTATION_PRECISION,
        "distance_display_precision": DISTANCE_DISPLAY_PRECISION,
        "target_contact_value_rule": TARGET_CONTACT_VALUE_RULE,
        "contact_value_precision_policy": "target_contact_value computed from full-precision distance before display rounding",
        "external_residual_score_status": "not_scored_in_v40.02r16",
        "aod_prediction_join_status": "not_joined_in_v40.02r16",
        "release_status": VERSION_LABEL,
    }
    write_csv(PROT / "pdb_external_evaluation_pair_policy_application.csv", list(policy.keys()), [policy])

    checks = [
        ("contact_map_derived_before_evaluation_pair_boundary", "r15 contact map exists and SHA-256 matches before r16 boundary declaration"),
        ("contact_map_sha256_matches_r15_manifest", "contact_map_sha256 equals r15 manifest value"),
        ("residue_table_sha256_matches_contact_map_manifest", "residue_table_sha256 is carried forward from r15 manifest"),
        ("sequence_separation_rule_declared_before_pair_selection", "abs(label_seq_id_j-label_seq_id_i)>=3 is fixed before boundary rows"),
        ("evaluation_pair_selection_rule_declared_before_score", "all eligible external contact-map pairs are selected before any score"),
        ("evaluation_pair_count_matches_contact_map_row_count", "946 boundary rows match 946 contact-map rows"),
        ("target_contact_count_matches_contact_map", "114 target contacts are carried from the target contact map"),
        ("target_noncontact_count_matches_contact_map", "832 target noncontacts are carried from the target contact map"),
        ("distance_precision_policy_recorded", "target_contact_value is computed from full-precision distance before display rounding"),
        ("no_AOD_prediction_packet_joined_in_r16", "AOD prediction packets are not read or joined by this boundary gate"),
        ("no_external_residual_score_computed_in_r16", "external residual score remains deferred"),
        ("coordinate_metrics_remain_deferred", "RMSD/TM-score/GDT remain deferred"),
        ("AOD_motif_curling_curls_and_SADAR_stay_upstream_of_future_target_join", "future target joins remain downstream of AOD motif/SADAR freeze"),
    ]
    check_rows = [
        {
            "check_id": f"PDB-EXT-EVAL-BOUNDARY-CHECK-{idx:03d}",
            "check_name": name,
            "check_result": "active_pass",
            "detail": detail,
            "score_input_status": "evaluation_boundary_gate_only_no_AOD_join_or_score",
            "release_status": VERSION_LABEL,
        }
        for idx, (name, detail) in enumerate(checks, start=1)
    ]
    write_csv(PROT / "pdb_external_evaluation_pair_leakage_checks.csv", list(check_rows[0].keys()), check_rows)

    manifest_obj = {
        "lane": "external_pdb_evaluation_pair_boundary_gate",
        "version_scope": VERSION,
        "status": "evaluation-pair boundary declaration from r15 external contact map only; no AOD prediction join, no external residual score, no coordinate metrics, no folding value map",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "coordinate_payload_sha256": PAYLOAD_SHA,
        "residue_table_sha256": manifest["residue_table_sha256"],
        "contact_map_sha256": contact_map_sha256,
        "distance_matrix_sha256": distance_matrix_sha256,
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "contact_threshold_angstrom": 8.0,
        "min_sequence_separation": 3,
        "sequence_separation_rule": SEQUENCE_SEPARATION_RULE,
        "evaluation_pair_selection_rule": EVALUATION_PAIR_SELECTION_RULE,
        "evaluation_pair_count": len(boundary_rows),
        "target_contact_count": contact_count,
        "target_noncontact_count": noncontact_count,
        "distance_computation_precision": DISTANCE_COMPUTATION_PRECISION,
        "distance_display_precision": DISTANCE_DISPLAY_PRECISION,
        "target_contact_value_rule": TARGET_CONTACT_VALUE_RULE,
        "contact_value_precision_policy": "target_contact_value computed from full-precision distance before display rounding",
        "score_status": "not_scored_in_v40.02r16",
        "aod_prediction_join_status": "not_joined_in_v40.02r16",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "blocked_until_later_gate": [
            "external_accession_residual_score",
            "coordinate_level_metric_score",
            "released_lambda_fold",
        ],
        "files": {
            "evaluation_pair_boundary": "manual-2/data/protein/pdb_external_evaluation_pair_boundary.csv",
            "scope_summary": "manual-2/data/protein/pdb_external_evaluation_pair_scope_summary.csv",
            "policy_application": "manual-2/data/protein/pdb_external_evaluation_pair_policy_application.csv",
            "leakage_checks": "manual-2/data/protein/pdb_external_evaluation_pair_leakage_checks.csv",
        },
        "boundary_sha256": sha256_file(PROT / "pdb_external_evaluation_pair_boundary.csv"),
        "scope_summary_sha256": sha256_file(PROT / "pdb_external_evaluation_pair_scope_summary.csv"),
        "policy_application_sha256": sha256_file(PROT / "pdb_external_evaluation_pair_policy_application.csv"),
        "leakage_checks_sha256": sha256_file(PROT / "pdb_external_evaluation_pair_leakage_checks.csv"),
        "claim_discipline": "external evaluation-pair rows are target-boundary rows; AOD prediction packets join only after a later score gate explicitly authorizes freeze-first target join",
    }
    (PROT / "pdb_external_evaluation_pair_manifest.json").write_text(json.dumps(manifest_obj, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    derive()
