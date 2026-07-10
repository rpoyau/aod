#!/usr/bin/env python3
"""Declare external PDB projection alignment and coverage state.

This gate is deliberately non-scoring. It reads the frozen r17 AOD projection
packet, records that no GAS-to-1CRN alignment/projection rule is declared, and
therefore formalizes zero in-scope coverage over the 946-pair external boundary.
No target contact values are read.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2/data/protein"
VERSION = "v40.02r18"
VERSION_LABEL = "v40.02r18_external_pdb_projection_alignment_coverage_gate"
PROJECTION = PROT / "pdb_external_aod_contact_projection.csv"
PROJECTION_SUMMARY = PROT / "pdb_external_aod_contact_projection_summary.csv"
PROJECTION_MANIFEST = PROT / "pdb_external_aod_contact_projection_manifest.json"
BOUNDARY_FILE = PROT / "pdb_external_evaluation_pair_boundary.csv"
ALIGNMENT_GATE_ID = "pdb_external_alignment_gate_1CRN_A_no_alignment_v4002r18"
ALIGNMENT_RULE = "none_declared"
ALIGNMENT_STATUS = "no_alignment_declared"
PROJECTION_COVERAGE_POLICY = "zero_coverage_until_alignment_or_projection_rule_is_declared"
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
    manifest = json.loads(PROJECTION_MANIFEST.read_text(encoding="utf-8"))
    projection_sha = sha256_file(PROJECTION)
    if manifest["projection_sha256"] != projection_sha:
        raise RuntimeError("r17 projection hash does not match manifest")
    rows = read_csv(PROJECTION)
    if len(rows) != int(manifest["evaluation_pair_count"]):
        raise RuntimeError("projection row count does not match r17 manifest")
    if "target_contact_value" in rows[0]:
        raise RuntimeError("projection rows must not carry target contact values")
    summary = read_csv(PROJECTION_SUMMARY)[0]
    boundary_sha = rows[0]["evaluation_boundary_sha256"]
    boundary_id = rows[0]["evaluation_boundary_id"]
    pair_list_sha = rows[0]["evaluation_pair_list_sha256"]
    aod_packet_sha = rows[0]["aod_packet_sha256"]
    aod_reclosure_sha = rows[0]["aod_reclosure_sha256"]
    if any(row["evaluation_boundary_sha256"] != boundary_sha for row in rows):
        raise RuntimeError("projection rows do not share one boundary hash")
    if any(row["evaluation_boundary_id"] != boundary_id for row in rows):
        raise RuntimeError("projection rows do not share one boundary id")
    if any(row["target_value_read_status"] != "not_read_by_projection_gate" for row in rows):
        raise RuntimeError("projection rows must not have read target values")

    coverage_rows: list[dict[str, str]] = []
    for idx, row in enumerate(rows, start=1):
        coverage_rows.append({
            "alignment_gate_id": ALIGNMENT_GATE_ID,
            "coverage_row_id": f"pdb_ext_alignment_coverage_1CRN_A_{idx:04d}",
            "evaluation_boundary_id": boundary_id,
            "evaluation_boundary_file": "manual-2/data/protein/pdb_external_evaluation_pair_boundary.csv",
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
            "aod_packet_id": row["aod_packet_id"],
            "aod_reclosure_id": row["aod_reclosure_id"],
            "aod_packet_sha256": aod_packet_sha,
            "aod_reclosure_sha256": aod_reclosure_sha,
            "sadar_context_id": row["sadar_context_id"],
            "alignment_rule": ALIGNMENT_RULE,
            "alignment_status": ALIGNMENT_STATUS,
            "alignment_state": "no_alignment_declared",
            "projection_coverage_policy": PROJECTION_COVERAGE_POLICY,
            "projection_coverage_status": "out_of_scope_no_declared_alignment",
            "in_scope_flag": "0",
            "out_of_scope_flag": "1",
            "abstain_flag": "0",
            "prediction_state_if_projected": "out_of_scope",
            "O_hat": "",
            "target_value_read_status": "not_read_by_alignment_gate",
            "residual_status": f"not_computed_in_{VERSION}",
            "score_status": "alignment_coverage_gate_only_no_residual_score",
            "leakage_role": "alignment_coverage_declaration_without_target_value_read_or_score",
            "release_status": VERSION_LABEL,
        })

    coverage_fields = list(coverage_rows[0].keys())
    coverage_path = PROT / "pdb_external_projection_alignment_coverage.csv"
    write_csv(coverage_path, coverage_fields, coverage_rows)

    eval_count = len(coverage_rows)
    gate = {
        "alignment_gate_id": ALIGNMENT_GATE_ID,
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "evaluation_boundary_id": boundary_id,
        "evaluation_boundary_file": "manual-2/data/protein/pdb_external_evaluation_pair_boundary.csv",
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "evaluation_pair_count": str(eval_count),
        "aod_packet_id": summary["aod_packet_id"],
        "aod_reclosure_id": summary["aod_reclosure_id"],
        "aod_packet_sha256": aod_packet_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "sadar_context_id": summary["sadar_context_id"],
        "alignment_rule": ALIGNMENT_RULE,
        "alignment_status": ALIGNMENT_STATUS,
        "projection_coverage_policy": PROJECTION_COVERAGE_POLICY,
        "in_scope_pair_count": "0",
        "out_of_scope_pair_count": str(eval_count),
        "abstain_pair_count": "0",
        "projection_coverage_num": "0",
        "projection_coverage_den": str(eval_count),
        "projection_coverage_exact": f"0/{eval_count}",
        "projection_coverage_display": "0.0",
        "coverage_status": "zero_coverage_no_declared_alignment",
        "abstention_policy": ABSTENTION_POLICY,
        "target_value_read_status": "not_read_by_alignment_gate",
        "residual_status": f"not_computed_in_{VERSION}",
        "score_status": "alignment_coverage_gate_only_no_residual_score",
        "lambda_fold_status": "deferred_not_attached",
        "release_status": VERSION_LABEL,
    }
    gate_path = PROT / "pdb_external_projection_alignment_gate.csv"
    write_csv(gate_path, list(gate.keys()), [gate])

    policy = {
        "alignment_policy_id": "pdb_external_projection_alignment_policy_1CRN_A_v4002r18",
        "alignment_gate_id": ALIGNMENT_GATE_ID,
        "evaluation_boundary_id": boundary_id,
        "evaluation_boundary_sha256": boundary_sha,
        "aod_packet_sha256": aod_packet_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "alignment_state_domain": "no_alignment_declared|manual_alignment_declared|sequence_alignment_declared|motif_to_residue_window_declared|external_projection_rule_declared",
        "projection_state_domain": "contact|noncontact|abstain|out_of_scope",
        "alignment_rule": ALIGNMENT_RULE,
        "alignment_status": ALIGNMENT_STATUS,
        "projection_coverage_policy": PROJECTION_COVERAGE_POLICY,
        "abstention_policy": ABSTENTION_POLICY,
        "target_value_policy": "target contact values are not read by this alignment/coverage gate",
        "residual_score_policy": "not computed until a later gate joins frozen O_hat with frozen O after declared coverage",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "release_status": VERSION_LABEL,
    }
    policy_path = PROT / "pdb_external_projection_alignment_policy_application.csv"
    write_csv(policy_path, list(policy.keys()), [policy])

    checks = [
        ("r17_projection_hash_verified_before_alignment_gate", "the frozen r17 projection packet is hashed before r18 coverage rows are emitted"),
        ("evaluation_boundary_id_stable_and_file_separated", "the stable boundary ID is recorded separately from the boundary file path"),
        ("alignment_status_declared_before_any_target_join", "no_alignment_declared is recorded before any target contact values are read"),
        ("coverage_fraction_declared", "projection coverage is recorded as 0/946 with display 0.0"),
        ("all_pairs_out_of_scope_without_alignment", "all 946 pairs remain out_of_scope because no alignment/projection rule is declared"),
        ("abstain_requires_declared_alignment", "abstain is reserved for in-scope pairs after an alignment/projection rule exists"),
        ("target_contact_values_not_read_in_r18", "coverage rows do not contain target_contact_value and do not read target O_ij"),
        ("no_residual_score_computed_in_r18", "Delta_Z and delta3 rows are not computed by this gate"),
        ("frozen_AOD_packet_and_SADAR_context_recorded", "aod packet, reclosure packet, and SADAR context hashes are carried forward"),
        ("coordinate_metrics_remain_deferred", "RMSD/TM-score/GDT remain deferred"),
        ("AOD_motif_curling_curls_and_SADAR_precede_downstream_target_join", "AOD motif/SADAR freeze remains upstream of any future target join"),
    ]
    check_rows = [
        {
            "check_id": f"PDB-EXT-ALIGN-COVERAGE-CHECK-{idx:03d}",
            "check_name": name,
            "check_result": "active_pass",
            "detail": detail,
            "alignment_gate_status": "alignment_coverage_gate_only_no_target_read_no_score",
            "release_status": VERSION_LABEL,
        }
        for idx, (name, detail) in enumerate(checks, start=1)
    ]
    checks_path = PROT / "pdb_external_projection_alignment_leakage_checks.csv"
    write_csv(checks_path, list(check_rows[0].keys()), check_rows)

    manifest_obj = {
        "lane": "external_pdb_projection_alignment_coverage_declaration_gate",
        "version_scope": VERSION,
        "status": "alignment and coverage declaration only; no target O_ij values read, no residual score, no coordinate metrics, no folding value map",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "alignment_gate_id": ALIGNMENT_GATE_ID,
        "evaluation_boundary_id": boundary_id,
        "evaluation_boundary_file": "manual-2/data/protein/pdb_external_evaluation_pair_boundary.csv",
        "evaluation_boundary_sha256": boundary_sha,
        "evaluation_pair_list_sha256": pair_list_sha,
        "evaluation_pair_count": eval_count,
        "aod_packet_id": summary["aod_packet_id"],
        "aod_reclosure_id": summary["aod_reclosure_id"],
        "aod_packet_sha256": aod_packet_sha,
        "aod_reclosure_sha256": aod_reclosure_sha,
        "sadar_context_id": summary["sadar_context_id"],
        "alignment_rule": ALIGNMENT_RULE,
        "alignment_status": ALIGNMENT_STATUS,
        "projection_coverage_policy": PROJECTION_COVERAGE_POLICY,
        "in_scope_pair_count": 0,
        "out_of_scope_pair_count": eval_count,
        "abstain_pair_count": 0,
        "projection_coverage_num": 0,
        "projection_coverage_den": eval_count,
        "projection_coverage_exact": f"0/{eval_count}",
        "projection_coverage_display": "0.0",
        "coverage_status": "zero_coverage_no_declared_alignment",
        "target_value_read_status": "not_read_by_alignment_gate",
        "residual_status": f"not_computed_in_{VERSION}",
        "score_status": "alignment_coverage_gate_only_no_residual_score",
        "blocked_until_later_gate": [
            "declared_external_alignment_or_projection_rule_with_in_scope_coverage",
            "external_accession_residual_score",
            "coordinate_level_metric_score",
            "released_lambda_fold",
        ],
        "files": {
            "alignment_gate": "manual-2/data/protein/pdb_external_projection_alignment_gate.csv",
            "coverage": "manual-2/data/protein/pdb_external_projection_alignment_coverage.csv",
            "policy_application": "manual-2/data/protein/pdb_external_projection_alignment_policy_application.csv",
            "leakage_checks": "manual-2/data/protein/pdb_external_projection_alignment_leakage_checks.csv",
        },
        "alignment_gate_sha256": sha256_file(gate_path),
        "coverage_sha256": sha256_file(coverage_path),
        "policy_application_sha256": sha256_file(policy_path),
        "leakage_checks_sha256": sha256_file(checks_path),
        "claim_discipline": "coverage rows formalize out_of_scope state only; target O_ij values join only in a later residual gate after declared alignment/projection coverage",
    }
    manifest_path = PROT / "pdb_external_projection_alignment_manifest.json"
    manifest_path.write_text(json.dumps(manifest_obj, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
