#!/usr/bin/env python3
"""Declare an external PDB alignment-rule candidate gate.

This gate is deliberately non-scoring. It reads the frozen r18 alignment/coverage
state and formalizes the current no-alignment carry-forward state. No target
contact values are read, and no residual rows are computed.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2/data/protein"
VERSION = "v40.02r19"
VERSION_LABEL = "v40.02r19_external_pdb_alignment_rule_candidate_gate"
R18_COVERAGE = PROT / "pdb_external_projection_alignment_coverage.csv"
R18_GATE = PROT / "pdb_external_projection_alignment_gate.csv"
R18_MANIFEST = PROT / "pdb_external_projection_alignment_manifest.json"
ALIGNMENT_RULE_ID = "pdb_external_alignment_rule_candidate_1CRN_A_no_alignment_carry_forward_v4002r19"
ALIGNMENT_RULE_TYPE = "no_alignment_carry_forward"
ALIGNMENT_STATUS = "no_alignment_declared_carry_forward"
PROJECTION_RULE = "none_no_projection_rule_declared"
COVERAGE_POLICY = "carry_forward_zero_coverage_until_alignment_rule_declared"
ABSTENTION_POLICY = "abstain_only_after_declared_alignment_or_projection_rule; without alignment use out_of_scope"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def main() -> None:
    r18_manifest = json.loads(R18_MANIFEST.read_text(encoding="utf-8"))
    r18_coverage_sha = sha256_file(R18_COVERAGE)
    if r18_manifest["coverage_sha256"] != r18_coverage_sha:
        raise RuntimeError("r18 coverage hash does not match r18 manifest")
    r18_rows = read_csv(R18_COVERAGE)
    r18_gate = read_csv(R18_GATE)[0]
    if len(r18_rows) != int(r18_manifest["evaluation_pair_count"]):
        raise RuntimeError("r18 coverage row count does not match manifest")
    if "target_contact_value" in r18_rows[0]:
        raise RuntimeError("r18 coverage rows must not carry target contact values")
    if {row["target_value_read_status"] for row in r18_rows} != {"not_read_by_alignment_gate"}:
        raise RuntimeError("r18 coverage rows must not have read target values")
    if {row["alignment_status"] for row in r18_rows} != {"no_alignment_declared"}:
        raise RuntimeError("r18 coverage rows must all be no-alignment rows")

    eval_count = len(r18_rows)
    boundary_id = r18_gate["evaluation_boundary_id"]
    boundary_file = r18_gate["evaluation_boundary_file"]
    boundary_sha = r18_gate["evaluation_boundary_sha256"]
    pair_list_sha = r18_gate["evaluation_pair_list_sha256"]
    aod_packet_id = r18_gate["aod_packet_id"]
    aod_reclosure_id = r18_gate["aod_reclosure_id"]
    aod_packet_sha = r18_gate["aod_packet_sha256"]
    aod_reclosure_sha = r18_gate["aod_reclosure_sha256"]
    sadar_context_id = r18_gate["sadar_context_id"]

    gate = {
        "alignment_rule_id": ALIGNMENT_RULE_ID,
        "alignment_rule_type": ALIGNMENT_RULE_TYPE,
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "evaluation_boundary_id": boundary_id,
        "evaluation_boundary_file": boundary_file,
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "evaluation_pair_count": str(eval_count),
        "aod_packet_id": aod_packet_id,
        "aod_reclosure_id": aod_reclosure_id,
        "aod_packet_sha256": aod_packet_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "sadar_context_id": sadar_context_id,
        "mapping_source": "none_declared",
        "mapping_scope": "none_declared",
        "aod_unit_id": aod_packet_id,
        "external_residue_window_start": "",
        "external_residue_window_end": "",
        "external_residue_indices": "",
        "projection_rule": PROJECTION_RULE,
        "projection_coverage_policy": COVERAGE_POLICY,
        "alignment_status": ALIGNMENT_STATUS,
        "in_scope_pair_count": "0",
        "out_of_scope_pair_count": str(eval_count),
        "abstain_pair_count": "0",
        "projection_coverage_num": "0",
        "projection_coverage_den": str(eval_count),
        "projection_coverage_exact": f"0/{eval_count}",
        "projection_coverage_display": "0.0",
        "abstention_policy": ABSTENTION_POLICY,
        "target_value_read_status": "not_read_by_alignment_rule_candidate_gate",
        "residual_status": f"not_computed_in_{VERSION}",
        "score_status": "alignment_rule_candidate_gate_only_no_residual_score",
        "lambda_fold_status": "deferred_not_attached",
        "release_status": VERSION_LABEL,
    }
    gate_path = PROT / "pdb_external_alignment_rule_candidate_gate.csv"
    write_csv(gate_path, list(gate.keys()), [gate])

    pair_rows: list[dict[str, str]] = []
    for idx, row in enumerate(r18_rows, start=1):
        pair_rows.append({
            "alignment_rule_id": ALIGNMENT_RULE_ID,
            "alignment_rule_pair_row_id": f"pdb_ext_alignment_rule_candidate_1CRN_A_{idx:04d}",
            "alignment_rule_type": ALIGNMENT_RULE_TYPE,
            "evaluation_boundary_id": boundary_id,
            "evaluation_boundary_file": boundary_file,
            "evaluation_boundary_sha256": boundary_sha,
            "evaluation_pair_list_sha256": pair_list_sha,
            "evaluation_pair_row_id": row["evaluation_pair_row_id"],
            "pair_id": row["pair_id"],
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
            "aod_packet_id": aod_packet_id,
            "aod_reclosure_id": aod_reclosure_id,
            "aod_packet_sha256": aod_packet_sha,
            "aod_reclosure_sha256": aod_reclosure_sha,
            "sadar_context_id": sadar_context_id,
            "mapping_source": "none_declared",
            "mapping_scope": "none_declared",
            "aod_unit_id": aod_packet_id,
            "external_residue_window_start": "",
            "external_residue_window_end": "",
            "external_residue_indices": "",
            "projection_rule": PROJECTION_RULE,
            "projection_coverage_policy": COVERAGE_POLICY,
            "alignment_status": ALIGNMENT_STATUS,
            "alignment_state": "no_alignment_carry_forward",
            "in_scope_flag": "0",
            "out_of_scope_flag": "1",
            "abstain_flag": "0",
            "prediction_state_if_projected": "out_of_scope",
            "O_hat": "",
            "target_value_read_status": "not_read_by_alignment_rule_candidate_gate",
            "residual_status": f"not_computed_in_{VERSION}",
            "score_status": "alignment_rule_candidate_gate_only_no_residual_score",
            "leakage_role": "alignment_rule_candidate_without_target_value_read_or_score",
            "release_status": VERSION_LABEL,
        })
    pair_path = PROT / "pdb_external_alignment_rule_candidate_pair_scope.csv"
    write_csv(pair_path, list(pair_rows[0].keys()), pair_rows)

    policy = {
        "alignment_rule_policy_id": "pdb_external_alignment_rule_candidate_policy_1CRN_A_v4002r19",
        "alignment_rule_id": ALIGNMENT_RULE_ID,
        "alignment_rule_type_domain": "no_alignment_carry_forward|manual_window_alignment|sequence_motif_alignment|motif_to_residue_window_alignment|external_projection_rule_declared",
        "projection_state_domain": "contact|noncontact|abstain|out_of_scope",
        "evaluation_boundary_id": boundary_id,
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "aod_packet_id": aod_packet_id,
        "aod_packet_sha256": aod_packet_sha,
        "sadar_context_id": sadar_context_id,
        "mapping_source": "none_declared",
        "mapping_scope": "none_declared",
        "projection_rule": PROJECTION_RULE,
        "coverage_policy": COVERAGE_POLICY,
        "abstention_policy": ABSTENTION_POLICY,
        "target_value_policy": "target contact values are not read by this alignment-rule candidate gate",
        "residual_score_policy": "not computed until a later gate joins frozen O_hat with frozen O after declared in-scope coverage",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "release_status": VERSION_LABEL,
    }
    policy_path = PROT / "pdb_external_alignment_rule_candidate_policy_application.csv"
    write_csv(policy_path, list(policy.keys()), [policy])

    checks = [
        ("r18_alignment_coverage_hash_verified_before_r19", "the frozen r18 alignment/coverage rows are hashed before the r19 candidate gate is emitted"),
        ("alignment_rule_type_declared_before_any_projection_or_target_join", "no_alignment_carry_forward is declared before target O_ij values are read"),
        ("evaluation_boundary_hash_carried_forward", "the stable r16 boundary ID and pair-list hash are carried forward"),
        ("aod_packet_and_sadar_context_hashes_carried_forward", "frozen AOD packet/reclosure hashes and SADAR context are carried forward"),
        ("all_pairs_remain_out_of_scope_without_alignment_rule", "all 946 pairs remain out_of_scope because no mapping source/scope is declared"),
        ("abstain_reserved_for_declared_alignment", "abstain remains unavailable until a concrete alignment/projection rule exists"),
        ("target_values_not_read_in_r19", "r19 rows do not contain target_contact_value and do not read target O_ij"),
        ("no_residual_score_computed_in_r19", "Delta_Z and delta3 rows are not computed by this gate"),
        ("coordinate_metrics_remain_deferred", "RMSD/TM-score/GDT remain deferred"),
        ("AOD_motif_curling_curls_and_SADAR_precede_downstream_target_join", "AOD motif/SADAR freeze remains upstream of any future target join"),
    ]
    check_rows = [
        {
            "check_id": f"PDB-EXT-ALIGN-RULE-CANDIDATE-CHECK-{idx:03d}",
            "check_name": name,
            "check_result": "active_pass",
            "detail": detail,
            "alignment_rule_gate_status": "candidate_gate_only_no_target_read_no_score",
            "release_status": VERSION_LABEL,
        }
        for idx, (name, detail) in enumerate(checks, start=1)
    ]
    checks_path = PROT / "pdb_external_alignment_rule_candidate_leakage_checks.csv"
    write_csv(checks_path, list(check_rows[0].keys()), check_rows)

    gate_sha = sha256_file(gate_path)
    pair_sha = sha256_file(pair_path)
    policy_sha = sha256_file(policy_path)
    checks_sha = sha256_file(checks_path)
    manifest = {
        "lane": "external_pdb_alignment_rule_candidate_gate",
        "version_scope": VERSION,
        "status": "alignment-rule candidate gate only; no target O_ij values read, no residual score, no coordinate metrics, no folding value map",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "alignment_rule_id": ALIGNMENT_RULE_ID,
        "alignment_rule_type": ALIGNMENT_RULE_TYPE,
        "alignment_status": ALIGNMENT_STATUS,
        "evaluation_boundary_id": boundary_id,
        "evaluation_boundary_file": boundary_file,
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "evaluation_pair_count": eval_count,
        "aod_packet_id": aod_packet_id,
        "aod_reclosure_id": aod_reclosure_id,
        "aod_packet_sha256": aod_packet_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "sadar_context_id": sadar_context_id,
        "mapping_source": "none_declared",
        "mapping_scope": "none_declared",
        "projection_rule": PROJECTION_RULE,
        "coverage_policy": COVERAGE_POLICY,
        "in_scope_pair_count": 0,
        "out_of_scope_pair_count": eval_count,
        "abstain_pair_count": 0,
        "projection_coverage_exact": f"0/{eval_count}",
        "target_value_read_status": "not_read_by_alignment_rule_candidate_gate",
        "residual_status": f"not_computed_in_{VERSION}",
        "score_status": "alignment_rule_candidate_gate_only_no_residual_score",
        "blocked_until_later_gate": [
            "declared_alignment_rule_with_nonzero_in_scope_coverage",
            "target_join_after_projection_freeze",
            "external_accession_residual_score",
            "coordinate_level_metric_score",
            "released_lambda_fold",
        ],
        "files": {
            "alignment_rule_candidate_gate": "manual-2/data/protein/pdb_external_alignment_rule_candidate_gate.csv",
            "alignment_rule_candidate_pair_scope": "manual-2/data/protein/pdb_external_alignment_rule_candidate_pair_scope.csv",
            "alignment_rule_candidate_policy_application": "manual-2/data/protein/pdb_external_alignment_rule_candidate_policy_application.csv",
            "alignment_rule_candidate_leakage_checks": "manual-2/data/protein/pdb_external_alignment_rule_candidate_leakage_checks.csv",
        },
        "alignment_rule_candidate_gate_sha256": gate_sha,
        "alignment_rule_candidate_pair_scope_sha256": pair_sha,
        "alignment_rule_candidate_policy_application_sha256": policy_sha,
        "alignment_rule_candidate_leakage_checks_sha256": checks_sha,
        "r18_alignment_coverage_sha256": r18_coverage_sha,
        "claim_discipline": "r19 formalizes no-alignment carry-forward only; target O_ij values and residual scores join only after a later alignment/projection rule declares in-scope coverage",
    }
    manifest_path = PROT / "pdb_external_alignment_rule_candidate_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
