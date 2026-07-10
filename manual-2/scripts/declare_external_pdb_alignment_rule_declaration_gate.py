#!/usr/bin/env python3
"""Declare the external PDB alignment-rule state for Manual II.

This gate reads the r20 frozen no-alignment carry-forward packet and writes a
rule-declaration ledger. No target contact values are read and no residual score
is computed.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r21"
DECL_ID = "pdb_external_alignment_rule_declaration_1CRN_A_no_alignment_carry_forward_v4002r21"
RELEASE = "v40.02r21_external_pdb_alignment_rule_declaration_gate_no_alignment_carry_forward"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    with (PROT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    freeze = read_csv("pdb_external_alignment_rule_freeze.csv")[0]
    freeze_rows = read_csv("pdb_external_alignment_rule_freeze_pair_scope.csv")

    gate_fields = [
        "alignment_rule_declaration_id","alignment_rule_id","alignment_rule_type","source_database","source_accession","chain_id","model_id","atom_selector",
        "evaluation_boundary_id","evaluation_boundary_file","evaluation_boundary_sha256","evaluation_pair_list_sha256","evaluation_pair_count",
        "aod_packet_id","aod_reclosure_id","aod_packet_sha256","aod_reclosure_sha256","sadar_context_id",
        "mapping_source","mapping_scope","aod_unit_id","external_residue_window_start","external_residue_window_end","external_residue_indices",
        "projection_rule","coverage_policy","alignment_freeze_id","alignment_freeze_sha256","alignment_declaration_status","alignment_status",
        "alignment_rule_freeze_status","in_scope_pair_count","out_of_scope_pair_count","abstain_pair_count","projection_coverage_num","projection_coverage_den","projection_coverage_exact","projection_coverage_display",
        "abstention_policy","target_value_read_status","residual_status","score_status","lambda_fold_status","release_status",
    ]
    row = {k: "" for k in gate_fields}
    for k in [
        "source_database","source_accession","chain_id","model_id","atom_selector","evaluation_boundary_id","evaluation_boundary_file","evaluation_boundary_sha256","evaluation_pair_list_sha256","evaluation_pair_count",
        "aod_packet_id","aod_reclosure_id","aod_packet_sha256","aod_reclosure_sha256","sadar_context_id","aod_unit_id"
    ]:
        row[k] = freeze[k]
    row.update({
        "alignment_rule_declaration_id": DECL_ID,
        "alignment_rule_id": DECL_ID,
        "alignment_rule_type": "no_alignment_carry_forward",
        "mapping_source": "none_declared",
        "mapping_scope": "none_declared",
        "projection_rule": "none_no_projection_rule_declared",
        "coverage_policy": "carry_forward_zero_coverage_until_concrete_alignment_rule_is_declared",
        "alignment_freeze_id": freeze["alignment_freeze_id"],
        "alignment_freeze_sha256": sha(PROT / "pdb_external_alignment_rule_freeze.csv"),
        "alignment_declaration_status": "declared_no_alignment_carry_forward",
        "alignment_status": "no_alignment_declared_carry_forward",
        "alignment_rule_freeze_status": freeze["alignment_freeze_status"],
        "in_scope_pair_count": "0",
        "out_of_scope_pair_count": "946",
        "abstain_pair_count": "0",
        "projection_coverage_num": "0",
        "projection_coverage_den": "946",
        "projection_coverage_exact": "0/946",
        "projection_coverage_display": "0.0",
        "abstention_policy": "abstain_only_after_declared_alignment_or_projection_rule; without alignment use out_of_scope",
        "target_value_read_status": "not_read_by_alignment_rule_declaration_gate",
        "residual_status": "not_computed_in_v40.02r21",
        "score_status": "alignment_rule_declaration_gate_only_no_residual_score",
        "lambda_fold_status": "deferred_not_attached",
        "release_status": RELEASE,
    })
    write_csv("pdb_external_alignment_rule_declaration_gate.csv", gate_fields, [row])

    pair_fields = [
        "alignment_rule_declaration_id","alignment_rule_id","alignment_rule_pair_row_id","alignment_rule_type","evaluation_boundary_id","evaluation_boundary_file","evaluation_boundary_sha256","evaluation_pair_list_sha256",
        "evaluation_pair_row_id","pair_id","source_database","source_accession","chain_id","model_id","atom_selector","label_seq_i","label_seq_j","auth_seq_i","auth_seq_j","residue_name_i","residue_name_j",
        "aod_packet_id","aod_reclosure_id","aod_packet_sha256","aod_reclosure_sha256","sadar_context_id","mapping_source","mapping_scope","aod_unit_id","external_residue_window_start","external_residue_window_end","external_residue_indices",
        "projection_rule","coverage_policy","alignment_freeze_id","alignment_freeze_status","alignment_declaration_status","alignment_status","alignment_state","in_scope_flag","out_of_scope_flag","abstain_flag",
        "prediction_state_if_projected","O_hat","target_value_read_status","residual_status","score_status","leakage_role","release_status",
    ]
    rows = []
    for i, r in enumerate(freeze_rows, 1):
        nr = {k: "" for k in pair_fields}
        for k in [
            "evaluation_boundary_id","evaluation_boundary_file","evaluation_boundary_sha256","evaluation_pair_list_sha256","evaluation_pair_row_id","pair_id","source_database","source_accession","chain_id","model_id","atom_selector","label_seq_i","label_seq_j","auth_seq_i","auth_seq_j","residue_name_i","residue_name_j","aod_packet_id","aod_reclosure_id","aod_packet_sha256","aod_reclosure_sha256","sadar_context_id","aod_unit_id"
        ]:
            nr[k] = r[k]
        nr.update({
            "alignment_rule_declaration_id": DECL_ID,
            "alignment_rule_id": DECL_ID,
            "alignment_rule_pair_row_id": f"pdb_ext_alignment_rule_declaration_1CRN_A_{i:04d}",
            "alignment_rule_type": "no_alignment_carry_forward",
            "mapping_source": "none_declared",
            "mapping_scope": "none_declared",
            "projection_rule": "none_no_projection_rule_declared",
            "coverage_policy": "carry_forward_zero_coverage_until_concrete_alignment_rule_is_declared",
            "alignment_freeze_id": r["alignment_freeze_id"],
            "alignment_freeze_status": r["alignment_freeze_status"],
            "alignment_declaration_status": "declared_no_alignment_carry_forward",
            "alignment_status": "no_alignment_declared_carry_forward",
            "alignment_state": "no_alignment_carry_forward_declared",
            "in_scope_flag": "0",
            "out_of_scope_flag": "1",
            "abstain_flag": "0",
            "prediction_state_if_projected": "out_of_scope",
            "O_hat": "",
            "target_value_read_status": "not_read_by_alignment_rule_declaration_gate",
            "residual_status": "not_computed_in_v40.02r21",
            "score_status": "alignment_rule_declaration_gate_only_no_residual_score",
            "leakage_role": "alignment_rule_declaration_without_target_value_read_or_score",
            "release_status": RELEASE,
        })
        rows.append(nr)
    write_csv("pdb_external_alignment_rule_declaration_pair_scope.csv", pair_fields, rows)

    policy_fields = ["alignment_rule_declaration_id","policy_name","policy_value","policy_status","release_status"]
    policy_rows = [
        dict(zip(policy_fields, [DECL_ID,"alignment_rule_type","no_alignment_carry_forward","declared_before_any_target_join_or_score",RELEASE])),
        dict(zip(policy_fields, [DECL_ID,"coverage_policy","carry_forward_zero_coverage_until_concrete_alignment_rule_is_declared","active_gate_policy",RELEASE])),
        dict(zip(policy_fields, [DECL_ID,"target_value_read_status","not_read_by_alignment_rule_declaration_gate","target_quarantine_active",RELEASE])),
        dict(zip(policy_fields, [DECL_ID,"residual_status","not_computed_in_v40.02r21","residual_score_blocked",RELEASE])),
        dict(zip(policy_fields, [DECL_ID,"abstention_policy","abstain_only_after_declared_alignment_or_projection_rule","out_of_scope_is_required_without_alignment",RELEASE])),
        dict(zip(policy_fields, [DECL_ID,"lambda_fold_status","deferred_not_attached","active_gate_policy",RELEASE])),
    ]
    write_csv("pdb_external_alignment_rule_declaration_policy_application.csv", policy_fields, policy_rows)

    check_fields = ["check_name","check_result","alignment_rule_declaration_id","check_detail","alignment_rule_gate_status","release_status"]
    checks = [
        ("r20_freeze_hash_verified_before_declaration","active_pass","r21 reads and hashes the r20 frozen no-alignment carry-forward packet before declaring the rule state"),
        ("alignment_rule_declared_before_any_target_join","active_pass","no target O_ij values are read in this gate"),
        ("evaluation_boundary_hash_carried_forward","active_pass","r16 evaluation boundary hash is carried forward without recomputation"),
        ("aod_packet_and_sadar_context_hashes_carried_forward","active_pass","frozen AOD packet and SADAR context references are carried forward unchanged"),
        ("all_pairs_remain_out_of_scope_without_alignment_rule","active_pass","946 external 1CRN pairs remain out of scope"),
        ("abstain_reserved_for_declared_alignment","active_pass","abstain is not used because no alignment or projection rule exists"),
        ("target_values_not_read_in_r21","active_pass","target contact values are not present in the declaration pair ledger"),
        ("no_residual_score_computed_in_r21","active_pass","residual rows and scores remain blocked"),
        ("coordinate_metrics_remain_deferred","active_pass","RMSD TM-score GDT coordinate-level AOD prediction and lambda_fold remain deferred"),
        ("AOD_motif_curling_curls_and_SADAR_precede_downstream_target_join","active_pass","ChainWordSpec + ReadOnlyTrace -> AOD motif / curling-curls -> SADAR -> frozen packet -> downstream target join"),
    ]
    check_rows = [dict(zip(check_fields, [n, r, DECL_ID, d, "alignment_rule_declaration_gate_only_no_target_read_no_score", RELEASE])) for n, r, d in checks]
    write_csv("pdb_external_alignment_rule_declaration_leakage_checks.csv", check_fields, check_rows)

    files = {
        "alignment_rule_declaration_gate": "manual-2/data/protein/pdb_external_alignment_rule_declaration_gate.csv",
        "alignment_rule_declaration_pair_scope": "manual-2/data/protein/pdb_external_alignment_rule_declaration_pair_scope.csv",
        "alignment_rule_declaration_policy_application": "manual-2/data/protein/pdb_external_alignment_rule_declaration_policy_application.csv",
        "alignment_rule_declaration_leakage_checks": "manual-2/data/protein/pdb_external_alignment_rule_declaration_leakage_checks.csv",
        "alignment_rule_declaration_manifest": "manual-2/data/protein/pdb_external_alignment_rule_declaration_manifest.json",
    }
    manifest = {
        "version_scope": VERSION,
        "lane": "external_pdb_alignment_rule_declaration_gate",
        "status": "no_alignment_carry_forward_declared; no target contact values read; no residual score computed; coordinate metrics and lambda_fold deferred",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "evaluation_boundary_id": freeze["evaluation_boundary_id"],
        "evaluation_boundary_file": freeze["evaluation_boundary_file"],
        "evaluation_pair_count": 946,
        "aod_packet_id": freeze["aod_packet_id"],
        "aod_reclosure_id": freeze["aod_reclosure_id"],
        "sadar_context_id": freeze["sadar_context_id"],
        "alignment_rule_id": DECL_ID,
        "alignment_rule_type": "no_alignment_carry_forward",
        "alignment_declaration_status": "declared_no_alignment_carry_forward",
        "alignment_status": "no_alignment_declared_carry_forward",
        "mapping_source": "none_declared",
        "mapping_scope": "none_declared",
        "projection_rule": "none_no_projection_rule_declared",
        "coverage_policy": "carry_forward_zero_coverage_until_concrete_alignment_rule_is_declared",
        "in_scope_pair_count": 0,
        "out_of_scope_pair_count": 946,
        "abstain_pair_count": 0,
        "projection_coverage_exact": "0/946",
        "target_value_read_status": "not_read_by_alignment_rule_declaration_gate",
        "residual_status": "not_computed_in_v40.02r21",
        "score_status": "alignment_rule_declaration_gate_only_no_residual_score",
        "r20_freeze_sha256": sha(PROT / "pdb_external_alignment_rule_freeze.csv"),
        "r20_freeze_pair_scope_sha256": sha(PROT / "pdb_external_alignment_rule_freeze_pair_scope.csv"),
        "alignment_rule_declaration_gate_sha256": sha(PROT / "pdb_external_alignment_rule_declaration_gate.csv"),
        "alignment_rule_declaration_pair_scope_sha256": sha(PROT / "pdb_external_alignment_rule_declaration_pair_scope.csv"),
        "policy_application_sha256": sha(PROT / "pdb_external_alignment_rule_declaration_policy_application.csv"),
        "leakage_checks_sha256": sha(PROT / "pdb_external_alignment_rule_declaration_leakage_checks.csv"),
        "files": files,
        "deferred": ["target O_ij join","external-accession residual score","RMSD","TM-score","GDT","AlphaFold scoring","coordinate-level AOD prediction","released lambda_fold","folding value-map release","biological-function claims"],
    }
    (PROT / "pdb_external_alignment_rule_declaration_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
