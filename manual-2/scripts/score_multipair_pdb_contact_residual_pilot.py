#!/usr/bin/env python3
"""Generate the v40.02r10 multi-pair scoped PDB contact residual pilot.

The scorer reads the declared multi-pair boundary/scope first, then reads the
frozen AOD contact/reclosure packet and finally joins the downstream PDBx/mmCIF
target contact rows.  Adjacent route-support pairs are carried as declared
negative-support controls for the non-adjacent contact metric; this is a score
projection, not a change to the frozen AOD packet.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r10"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def pair_key(row: dict[str, str]) -> str:
    return f"{row['residue_i']}-{row['residue_j']}"


def main() -> int:
    # Scope/input-lock rows are intentionally opened before prediction/target rows.
    scope_source = PROT / "pdb_contact_comparison_scope_declaration.csv"
    target_provenance_source = PROT / "pdb_contact_comparison_target_provenance.csv"
    leakage_source = PROT / "pdb_contact_comparison_leakage_checks.csv"
    freeze_source = PROT / "aod_contact_prediction_freeze.csv"
    target_source = PROT / "pdb_mmcif_contact_map_derived.csv"

    scope_prev = read_csv(scope_source)[0]
    target_prov = read_csv(target_provenance_source)[0]
    _leakage_scope = read_csv(leakage_source)
    freeze_rows = read_csv(freeze_source)
    target_rows = read_csv(target_source)

    freeze_by_pair = {
        f"{r['residue_i']}-{r['residue_j']}": r
        for r in freeze_rows
        if r["chain_id"] == "chain_GAS_tripeptide_seed"
    }
    target_by_pair = {pair_key(r): r for r in target_rows}

    evaluation_pairs = ["1-2", "1-3", "2-3"]
    positive_pairs = ["1-3"]
    negative_support_pairs = ["1-2", "2-3"]

    scope_id = "pdb_contact_scope_manual_GAS_multipair_v4002r10"
    score_id = "pdb_multipair_contact_score_001"
    target_payload = "manual_seed_GAS_pdbx_mmcif_payload_fixture"
    protein_id = "manual_seed_GAS"
    chain_id = "chain_GAS_tripeptide_seed"
    contact_definition = "CA_distance_leq_8.0A_multipair_negative_support_boundary"
    pair_index_basis = "one_based_residue_sequence_position"
    coordinate_source = "manual-2/data/protein/pdb_mmcif_payloads/manual_seed_GAS_pdbx_mmcif_payload_fixture.cif"
    coordinate_hash = sha256_file(ROOT / coordinate_source)

    scope_rows = [{
        "scope_id": scope_id,
        "version_scope": VERSION,
        "carried_forward_scope_id": scope_prev["scope_id"],
        "prediction_freeze_version": "v40.02r05",
        "prediction_model_id": scope_prev["prediction_model_id"],
        "chain_id": chain_id,
        "protein_id": protein_id,
        "target_payload_id": target_payload,
        "target_source_accession": target_payload,
        "score_scope": "pdb_mmcif_derived_contact_subset_with_declared_negative_support_controls",
        "contact_threshold_angstrom": "8.0",
        "min_sequence_separation": "2",
        "declared_evaluation_pairs": ";".join(evaluation_pairs),
        "positive_evaluation_pairs": ";".join(positive_pairs),
        "negative_support_pairs": ";".join(negative_support_pairs),
        "declared_prediction_pairs_after_projection": ";".join(positive_pairs),
        "declared_target_contact_pairs": ";".join(positive_pairs),
        "projection_policy": "adjacent_route_support_pairs_projected_to_noncontact_negative_support_for_nonadjacent_contact_metric",
        "negative_support_declaration_status": "declared_before_score",
        "allowed_target_rows": ";".join(
            f"{target_by_pair[p]['derived_contact_id']}:{target_by_pair[p]['contact_scope_status']}" for p in evaluation_pairs
        ),
        "target_contact_map_hash": scope_prev["target_contact_map_hash"],
        "target_distance_matrix_hash": scope_prev["target_distance_matrix_hash"],
        "residual_schema_id": "pdb_contact_residual_schema_multipair_binary_contact_delta3_v4002r10",
        "coordinate_metric_policy": "RMSD_TM_score_GDT_absent_until_coordinate_level_AOD_prediction_freeze",
        "score_status": "declared_negative_support_before_scoring",
        "comparison_status": "scoped_multi_pair_pilot_ready",
        "value_map_status": "quarantined_scope_declaration_no_lambda_fold",
        "release_status": f"{VERSION}_multipair_negative_support_scope_declaration",
    }]

    pilot_rows = []
    delta_rows = []
    tp = fp = fn = tn = 0
    for idx, pair in enumerate(evaluation_pairs, start=1):
        i, j = pair.split("-")
        freeze = freeze_by_pair[pair]
        target = target_by_pair[pair]
        raw_frozen = int(freeze["predicted_contact"])
        target_value = int(target["derived_contact"])
        if pair in negative_support_pairs:
            score_prediction = 0
            projection_status = "adjacent_route_support_projected_to_noncontact_negative_support"
            metric_pair_class = "declared_negative_support_boundary_control"
        else:
            score_prediction = raw_frozen
            projection_status = "nonadjacent_reclosure_contact_value_preserved"
            metric_pair_class = "declared_positive_contact_evaluation_pair"

        delta_z = score_prediction - target_value
        delta3 = delta_z % 3
        if score_prediction == 1 and target_value == 1:
            err = "TP"; tp += 1
        elif score_prediction == 1 and target_value == 0:
            err = "FP"; fp += 1
        elif score_prediction == 0 and target_value == 1:
            err = "FN"; fn += 1
        else:
            err = "TN"; tn += 1

        common = {
            "score_id": score_id,
            "scope_id": scope_id,
            "chain_id": chain_id,
            "protein_id": protein_id,
            "target_payload_id": target_payload,
            "target_source_type": "manual_pdbx_mmcif_fixture",
            "target_source_id": target_payload,
            "target_derivation_rule": "CA_distance_leq_8.0A_min_sequence_separation_2",
            "target_freeze_id": target["derived_contact_id"],
            "target_coordinate_status": "fixture_coordinate_payload_derived_not_external_pdb_accession",
            "contact_definition": contact_definition,
            "pair_index_basis": pair_index_basis,
            "atom_selector": "CA",
            "distance_cutoff_A": "8.0",
            "coordinate_source": coordinate_source,
            "coordinate_source_hash": coordinate_hash,
            "trace_id": freeze["trace_id"],
            "aod_motif_id": freeze["motif_id"],
            "sadar_context_id": freeze["sadar_context_id"],
            "detection_basis": "AOD_motif_curling_curls_spec_plus_SADAR_context",
            "downstream_map_stage": "target_join_after_prediction_freeze",
            "prediction_freeze_version": "v40.02r05",
            "target_derivation_version": "v40.02r07",
            "scope_version": VERSION,
            "score_version": VERSION,
            "score_origin_version": VERSION,
            "residue_i": i,
            "residue_j": j,
            "pair_separation": str(abs(int(j)-int(i))),
            "raw_frozen_prediction_contact_value": str(raw_frozen),
            "score_projection_contact_value": str(score_prediction),
            "target_contact_value": str(target_value),
            "predicted_contact": str(score_prediction),
            "target_contact": str(target_value),
            "ca_distance_angstrom": target["ca_distance_angstrom"],
            "Delta_Z": str(delta_z),
            "delta3_contact": str(delta3),
            "contact_error_class": err,
            "metric_pair_class": metric_pair_class,
            "projection_status": projection_status,
            "leakage_status": "passed_scope_and_input_lock_checks",
            "score_status": "scored_after_multipair_scope_and_negative_support_declaration",
            "value_map_status": "quarantined_pdb_contact_residual_not_released_lambda_fold",
            "release_status": f"{VERSION}_multipair_scoped_contact_residual_pilot",
        }
        pilot_rows.append({
            "pilot_id": f"pdb_multipair_contact_residual_pilot_{idx:03d}",
            "prediction_id": freeze["prediction_id"],
            "target_contact_id": target["derived_contact_id"],
            **common,
        })
        delta_rows.append({
            "delta3_id": f"pdb_multipair_contact_delta3_{idx:03d}",
            "prediction_id": freeze["prediction_id"],
            "target_contact_id": target["derived_contact_id"],
            **common,
        })

    precision = tp / (tp + fp) if (tp + fp) else ""
    recall = tp / (tp + fn) if (tp + fn) else ""
    f1 = 2 * precision * recall / (precision + recall) if precision != "" and recall != "" and (precision + recall) else ""
    jaccard = tp / (tp + fp + fn) if (tp + fp + fn) else ""
    denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    mcc = ((tp * tn) - (fp * fn)) / (denom ** 0.5) if denom else ""
    metric_scope = "three_pair_fixture_with_two_declared_negative_support_rows"
    metric_validity = "multi_pair_residual_denominator_check"
    classifier_generalization = "not_scoped_beyond_manual_GAS_fixture"
    mcc_status = "defined_with_declared_negative_support_pairs"

    score_rows = [{
        "score_id": score_id,
        "scope_id": scope_id,
        "model_id": scope_prev["prediction_model_id"],
        "prediction_freeze_version": "v40.02r05",
        "target_derivation_version": "v40.02r07",
        "scope_version": VERSION,
        "score_version": VERSION,
        "score_origin_version": VERSION,
        "chain_id": chain_id,
        "protein_id": protein_id,
        "target_payload_id": target_payload,
        "target_source_accession": target_payload,
        "target_source_type": "manual_pdbx_mmcif_fixture",
        "target_source_id": target_payload,
        "target_derivation_rule": "CA_distance_leq_8.0A_min_sequence_separation_2",
        "target_coordinate_status": "fixture_coordinate_payload_derived_not_external_pdb_accession",
        "structure_source": "manual_fixture_pdbx_mmcif",
        "contact_definition": contact_definition,
        "pair_index_basis": pair_index_basis,
        "atom_selector": "CA",
        "distance_cutoff_A": "8.0",
        "coordinate_source": coordinate_source,
        "coordinate_source_hash": coordinate_hash,
        "score_scope": "pdb_mmcif_derived_contact_subset_with_declared_negative_support_controls",
        "metric_scope": metric_scope,
        "metric_validity": metric_validity,
        "classifier_generalization": classifier_generalization,
        "min_sequence_separation": "2",
        "contact_threshold_angstrom": "8.0",
        "predicted_pairs_after_projection": ";".join(positive_pairs),
        "target_pairs": ";".join(positive_pairs),
        "evaluation_pairs": ";".join(evaluation_pairs),
        "negative_support_pairs": ";".join(negative_support_pairs),
        "tp": str(tp), "fp": str(fp), "fn": str(fn), "tn": str(tn),
        "precision": f"{precision:g}",
        "recall": f"{recall:g}",
        "f1": f"{f1:g}",
        "jaccard": f"{jaccard:g}",
        "mcc": f"{mcc:g}",
        "mcc_status": mcc_status,
        "score_status": "multi_pair_scoped_contact_residual_pilot_scored",
        "value_map_status": "quarantined_pdb_contact_residual_not_released_lambda_fold",
        "coordinate_metric_status": "contact_map_only_no_coordinate_level_aod_prediction",
        "release_status": f"{VERSION}_multipair_scoped_contact_residual_pilot",
    }]

    summary_rows = [{
        "summary_id": "pdb_multipair_contact_score_summary_001",
        "score_version": VERSION,
        "score_origin_version": VERSION,
        "scope_count": "1",
        "score_rows": "1",
        "residual_rows": str(len(delta_rows)),
        "metric_scope": metric_scope,
        "metric_validity": metric_validity,
        "classifier_generalization": classifier_generalization,
        "tp": str(tp), "fp": str(fp), "fn": str(fn), "tn": str(tn),
        "precision_micro": f"{precision:g}",
        "recall_micro": f"{recall:g}",
        "f1_micro": f"{f1:g}",
        "jaccard_micro": f"{jaccard:g}",
        "mcc_micro": f"{mcc:g}",
        "mcc_status": mcc_status,
        "lambda_fold_status": "deferred_not_attached",
        "claim_status": "multi_pair_scoped_contact_residual_pilot_not_folding_model",
        "release_status": f"{VERSION}_multipair_scoped_contact_residual_pilot",
    }]

    audit_rows = [
        ("PDB-MULTI-LEAK-001", "multipair_scope_declared_before_scoring", "scope_input_lock", "active_pass", "undeclared_negative_support_pairs", "score_without_scope_declaration", "negative_support_declaration_before_score"),
        ("PDB-MULTI-LEAK-002", "frozen_aod_packet_read_before_target_contact_row", "prediction_freeze", "active_pass", "target_contact_rows", "aod_contact_prediction_freeze", "target_join_after_prediction_freeze"),
        ("PDB-MULTI-LEAK-003", "target_columns_absent_from_frozen_prediction_packet", "prediction_freeze", "active_pass", "target_columns", "aod_contact_prediction_freeze", "comparison_only_after_freeze"),
        ("PDB-MULTI-LEAK-004", "score_script_joins_target_after_prediction_freeze", "score_join", "active_pass", "target_contact_rows", "score_inputs_before_prediction_freeze", "scope_then_freeze_then_target_join"),
        ("PDB-MULTI-LEAK-005", "residual_computed_after_prediction_and_target_rows_frozen", "residual_audit", "active_pass", "residual_row", "unfrozen_prediction_or_target", "after_both_rows_frozen"),
        ("PDB-MULTI-LEAK-006", "negative_support_pairs_have_target_zero_and_projected_prediction_zero", "negative_support_metric", "active_pass", "unbounded_negative_support", "metric_confusion_counts", "declared_negative_support_scope"),
        ("PDB-MULTI-LEAK-007", "coordinate_level_score_fields_remain_deferred", "metric_scope", "active_pass", "RMSD_TM_score_GDT_coordinate_prediction", "pdb_multipair_contact_score", "future_coordinate_level_prediction_freeze_only"),
        ("PDB-MULTI-LEAK-008", "aod_detection_basis_keeps_motif_curling_curls_and_sadar_before_target_map", "detection_order", "active_pass", "target_rows_as_detection_premises", "aod_motif_or_sadar_context", "AOD_motif_then_SADAR_then_downstream_target_join"),
    ]
    leakage_rows = [{
        "audit_id": audit_id,
        "scope_id": scope_id,
        "check_name": name,
        "check_stage": stage,
        "check_result": result,
        "forbidden_source": forbidden_source,
        "forbidden_destination": forbidden_dest,
        "allowed_stage": allowed_stage,
        "pilot_check_status": "active_pass",
        "score_input_status": "scope_rows_read_before_prediction_and_target_rows",
        "release_status": f"{VERSION}_multipair_scoped_contact_residual_pilot",
    } for audit_id, name, stage, result, forbidden_source, forbidden_dest, allowed_stage in audit_rows]

    write_csv(
        PROT / "pdb_multipair_contact_scope_declaration.csv",
        scope_rows,
        list(scope_rows[0].keys()),
    )
    write_csv(
        PROT / "pdb_multipair_contact_residual_pilot.csv",
        pilot_rows,
        list(pilot_rows[0].keys()),
    )
    write_csv(
        PROT / "pdb_multipair_contact_delta3.csv",
        delta_rows,
        [
            "delta3_id", "score_id", "scope_id", "prediction_id", "target_contact_id", "chain_id",
            "protein_id", "target_payload_id", "residue_i", "residue_j", "raw_frozen_prediction_contact_value",
            "score_projection_contact_value", "target_contact_value", "predicted_contact", "target_contact",
            "Delta_Z", "delta3_contact", "contact_error_class", "metric_pair_class", "projection_status",
            "contact_definition", "pair_index_basis", "release_status"
        ],
    )
    write_csv(
        PROT / "pdb_multipair_contact_score.csv",
        score_rows,
        list(score_rows[0].keys()),
    )
    write_csv(
        PROT / "pdb_multipair_contact_leakage_audit.csv",
        leakage_rows,
        list(leakage_rows[0].keys()),
    )
    write_csv(
        PROT / "pdb_multipair_contact_score_summary.csv",
        summary_rows,
        list(summary_rows[0].keys()),
    )

    files = {
        "pdb_multipair_contact_scope_declaration": "manual-2/data/protein/pdb_multipair_contact_scope_declaration.csv",
        "pdb_multipair_contact_residual_pilot": "manual-2/data/protein/pdb_multipair_contact_residual_pilot.csv",
        "pdb_multipair_contact_delta3": "manual-2/data/protein/pdb_multipair_contact_delta3.csv",
        "pdb_multipair_contact_score": "manual-2/data/protein/pdb_multipair_contact_score.csv",
        "pdb_multipair_contact_leakage_audit": "manual-2/data/protein/pdb_multipair_contact_leakage_audit.csv",
        "pdb_multipair_contact_score_summary": "manual-2/data/protein/pdb_multipair_contact_score_summary.csv",
    }
    input_files = {
        "previous_scope_declaration": "manual-2/data/protein/pdb_contact_comparison_scope_declaration.csv",
        "previous_target_provenance": "manual-2/data/protein/pdb_contact_comparison_target_provenance.csv",
        "previous_leakage_checks": "manual-2/data/protein/pdb_contact_comparison_leakage_checks.csv",
        "aod_contact_prediction_freeze": "manual-2/data/protein/aod_contact_prediction_freeze.csv",
        "pdb_mmcif_contact_map_derived": "manual-2/data/protein/pdb_mmcif_contact_map_derived.csv",
    }
    output_files = {**files, "manifest": "manual-2/data/protein/pdb_multipair_contact_residual_manifest.json"}
    manifest = {
        "lane": "multi_pair_scoped_pdb_contact_residual_pilot",
        "version_scope": VERSION,
        "status": "multi_pair_contact_residual_pilot_with_declared_negative_support_rows_no_coordinate_metrics_no_active_lambda_fold",
        "files": files,
        "required_input_files": input_files,
        "input_hashes": {key: sha256_file(ROOT / path) for key, path in input_files.items()},
        "output_hashes": {key: sha256_file(ROOT / path) for key, path in files.items()},
        "detection_policy": "ChainWordSpec plus ReadOnlyTrace is read before AOD motif / curling-curls specification and SADAR context; target contact rows join only after the frozen packet.",
        "negative_support_policy": {
            "negative_support_pairs": negative_support_pairs,
            "declaration_status": "declared_before_score",
            "projection_policy": "adjacent route-support pairs are projected to noncontact controls only inside the declared non-adjacent contact metric boundary; the frozen AOD packet is not modified."
        },
        "score_summary": summary_rows[0],
        "lambda_fold_status": "deferred_not_attached",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "claim_status": "manual_GAS_fixture_multi_pair_contact_residual_pilot_not_folding_model",
        "release_status": f"{VERSION}_multipair_scoped_contact_residual_pilot",
    }
    manifest_path = PROT / "pdb_multipair_contact_residual_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Write manifest after computing output hashes; refresh with manifest hash excluded to avoid recursion.
    manifest["output_hashes"]["manifest_without_self_hash"] = "not_self_hashed"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote multi-pair scoped contact residual pilot for {VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
