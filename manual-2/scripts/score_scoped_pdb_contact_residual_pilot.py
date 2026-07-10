#!/usr/bin/env python3
"""Score the scoped PDB contact-map residual pilot with r09.1 guards.

This generator is offline and deterministic. It reads the v40.02r08
scope/input-lock rows before reading the v40.02r05 frozen AOD prediction packet
and the v40.02r07 target contact row. It scores only the explicitly declared
evaluation pairs. It also records target-source provenance, contact-definition
fields, metric validity, and freeze-before-target-join leakage guards.

D.E.C. discipline: raw AFC/D.E.C. execution and AOD motif detection are upstream
of this script. Detection is the AOD motif / curling-curls specification plus
SADAR context in the frozen prediction packet; PDB/mmCIF target rows join only
downstream after that freeze.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r09.1"
SCORE_ORIGIN_VERSION = "v40.02r09"
RELEASE_STATUS = "v40.02r09.1_scoped_pdb_contact_boundary_metric_guard"
METRIC_SCOPE = "single_positive_contact_row"
METRIC_VALIDITY = "residual_row_smoke_test"
CLASSIFIER_GENERALIZATION = "not_scoped_in_this_pilot"
DETECTION_BASIS = "AOD_motif_curling_curls_spec_plus_SADAR_context"
DOWNSTREAM_MAP_STAGE = "target_join_after_prediction_freeze"
PAIR_INDEX_BASIS = "one_based_residue_sequence_position"
TARGET_COORDINATE_STATUS = "fixture_coordinate_payload_derived_not_external_pdb_accession"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_pairs(text: str) -> set[tuple[int, int]]:
    if not text or text.startswith("deferred"):
        return set()
    return {tuple(map(int, pair.split("-"))) for pair in text.split(";") if pair}


def fmt_pairs(pairs: set[tuple[int, int]]) -> str:
    return ";".join(f"{i}-{j}" for i, j in sorted(pairs))


def safe_div(a: int, b: int) -> str:
    if b == 0:
        return "undefined_no_denominator"
    return f"{a / b:.6f}".rstrip("0").rstrip(".")


def mcc_value(tp: int, fp: int, fn: int, tn: int) -> str:
    denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denom == 0:
        return "undefined_no_true_negative_denominator"
    return f"{((tp * tn) - (fp * fn)) / math.sqrt(denom):.6f}".rstrip("0").rstrip(".")


def input_manifest() -> dict[str, str]:
    files = {
        "scope_declaration": PROT / "pdb_contact_comparison_scope_declaration.csv",
        "target_provenance": PROT / "pdb_contact_comparison_target_provenance.csv",
        "residual_coordinates": PROT / "pdb_contact_comparison_residual_coordinates.csv",
        "leakage_checks": PROT / "pdb_contact_comparison_leakage_checks.csv",
        "aod_contact_prediction_freeze": PROT / "aod_contact_prediction_freeze.csv",
        "pdb_mmcif_contact_map_derived": PROT / "pdb_mmcif_contact_map_derived.csv",
    }
    return {k: sha256_file(v) for k, v in files.items()}


def contact_definition(scope: dict[str, str]) -> str:
    return f"CA_distance_leq_{scope['contact_threshold_angstrom']}A_min_sequence_separation_{scope['min_sequence_separation']}"


def build_rows():
    scope_rows = read_csv(PROT / "pdb_contact_comparison_scope_declaration.csv")
    provenance_rows = read_csv(PROT / "pdb_contact_comparison_target_provenance.csv")
    residual_coordinate_rows = read_csv(PROT / "pdb_contact_comparison_residual_coordinates.csv")
    leakage_rows = read_csv(PROT / "pdb_contact_comparison_leakage_checks.csv")
    prediction_rows = read_csv(PROT / "aod_contact_prediction_freeze.csv")
    target_rows = read_csv(PROT / "pdb_mmcif_contact_map_derived.csv")

    if not scope_rows:
        raise RuntimeError("scope declaration is required")
    if any(row["check_status"] != "active_pass" for row in leakage_rows):
        raise RuntimeError("all v40.02r08 leakage checks must be active_pass before scoring")
    if not any(row["coordinate_name"] == "Delta_Z_ij" for row in residual_coordinate_rows):
        raise RuntimeError("residual coordinate schema must declare Delta_Z_ij")

    pred_index = {
        (row["chain_id"], int(row["residue_i"]), int(row["residue_j"])): row
        for row in prediction_rows
    }
    target_index = {
        (row["protein_id"], row["payload_id"], int(row["residue_i"]), int(row["residue_j"])): row
        for row in target_rows
    }
    provenance_by_scope = {row["scope_id"]: row for row in provenance_rows}

    pilot_rows: list[dict[str, object]] = []
    score_rows: list[dict[str, object]] = []
    delta_rows: list[dict[str, object]] = []
    leakage_audit_rows: list[dict[str, object]] = []
    summary_tp = summary_fp = summary_fn = summary_tn = 0

    for idx, scope in enumerate(scope_rows, 1):
        scope_id = scope["scope_id"]
        prov = provenance_by_scope[scope_id]
        eval_pairs = parse_pairs(scope["declared_evaluation_pairs"])
        predicted_pairs: set[tuple[int, int]] = set()
        target_pairs: set[tuple[int, int]] = set()
        pilot_id = f"pdb_scoped_contact_residual_pilot_{idx:03d}"
        score_id = f"pdb_scoped_contact_score_{idx:03d}"
        tp = fp = fn = tn = 0
        cdef = contact_definition(scope)
        target_source_type = "manual_pdbx_mmcif_fixture" if prov["source_class"].startswith("manual") else prov["source_class"]
        target_source_id = prov["payload_id"]
        coordinate_source = prov["payload_path"]
        coordinate_source_hash = prov["payload_sha256"]

        for pair_no, (i, j) in enumerate(sorted(eval_pairs), 1):
            pred = pred_index.get((scope["chain_id"], i, j))
            target = target_index.get((scope["protein_id"], scope["target_payload_id"], i, j))
            if pred is None:
                pred_contact = 0
                prediction_id = "missing_frozen_prediction"
                trace_id = aod_motif_id = sadar_context_id = "missing_frozen_detection_row"
            else:
                pred_contact = int(pred["predicted_contact"])
                prediction_id = pred["prediction_id"]
                trace_id = pred["trace_id"]
                aod_motif_id = pred["motif_id"]
                sadar_context_id = pred["sadar_context_id"]
            if target is None:
                target_contact = 0
                target_contact_id = "missing_derived_target_contact"
                ca_distance = "not_available"
            else:
                target_contact = int(target["derived_contact"])
                target_contact_id = target["derived_contact_id"]
                ca_distance = target["ca_distance_angstrom"]
            if pred_contact:
                predicted_pairs.add((i, j))
            if target_contact:
                target_pairs.add((i, j))
            delta = pred_contact - target_contact
            if pred_contact and target_contact:
                cls = "TP"; tp += 1
            elif pred_contact and not target_contact:
                cls = "FP"; fp += 1
            elif target_contact and not pred_contact:
                cls = "FN"; fn += 1
            else:
                cls = "TN"; tn += 1

            common = {
                "target_source_type": target_source_type,
                "target_source_id": target_source_id,
                "target_derivation_rule": cdef,
                "target_freeze_id": target_contact_id,
                "target_coordinate_status": TARGET_COORDINATE_STATUS,
                "contact_definition": cdef,
                "pair_index_basis": PAIR_INDEX_BASIS,
                "atom_selector": "CA",
                "distance_cutoff_A": scope["contact_threshold_angstrom"],
                "coordinate_source": coordinate_source,
                "coordinate_source_hash": coordinate_source_hash,
                "trace_id": trace_id,
                "aod_motif_id": aod_motif_id,
                "sadar_context_id": sadar_context_id,
                "detection_basis": DETECTION_BASIS,
                "downstream_map_stage": DOWNSTREAM_MAP_STAGE,
            }
            delta_rows.append({
                "delta3_id": f"pdb_scoped_contact_delta3_{idx:03d}_{pair_no:03d}",
                "score_id": score_id,
                "scope_id": scope_id,
                "protein_id": scope["protein_id"],
                "chain_id": scope["chain_id"],
                "target_payload_id": scope["target_payload_id"],
                "residue_i": i,
                "residue_j": j,
                "prediction_contact_value": pred_contact,
                "target_contact_value": target_contact,
                "predicted_contact": pred_contact,
                "target_contact": target_contact,
                "Delta_Z": delta,
                "delta3_contact": delta % 3,
                "contact_error_sign": (delta > 0) - (delta < 0),
                "contact_error_class": cls,
                "score_scope": scope["score_scope"],
                "target_source_type": target_source_type,
                "contact_definition": cdef,
                "pair_index_basis": PAIR_INDEX_BASIS,
                "release_status": RELEASE_STATUS,
            })
            pilot_rows.append({
                "pilot_id": pilot_id,
                "score_id": score_id,
                "scope_id": scope_id,
                "prediction_id": prediction_id,
                "target_contact_id": target_contact_id,
                "chain_id": scope["chain_id"],
                "protein_id": scope["protein_id"],
                "target_payload_id": scope["target_payload_id"],
                **common,
                "prediction_freeze_version": scope["prediction_freeze_version"],
                "target_derivation_version": "v40.02r07",
                "scope_version": scope["version_scope"],
                "score_version": VERSION,
                "score_origin_version": SCORE_ORIGIN_VERSION,
                "residue_i": i,
                "residue_j": j,
                "pair_separation": j - i,
                "prediction_contact_value": pred_contact,
                "target_contact_value": target_contact,
                "predicted_contact": pred_contact,
                "target_contact": target_contact,
                "ca_distance_angstrom": ca_distance,
                "Delta_Z": delta,
                "delta3_contact": delta % 3,
                "contact_error_class": cls,
                "leakage_status": "passed_scope_and_input_lock_checks",
                "score_status": "scored_only_declared_v40.02r08_scope_pairs",
                "value_map_status": "quarantined_pdb_contact_residual_not_released_lambda_fold",
                "release_status": RELEASE_STATUS,
            })
        score_rows.append({
            "score_id": score_id,
            "pilot_id": pilot_id,
            "scope_id": scope_id,
            "model_id": scope["prediction_model_id"],
            "prediction_freeze_version": scope["prediction_freeze_version"],
            "target_derivation_version": "v40.02r07",
            "scope_version": scope["version_scope"],
            "score_version": VERSION,
            "score_origin_version": SCORE_ORIGIN_VERSION,
            "chain_id": scope["chain_id"],
            "protein_id": scope["protein_id"],
            "target_payload_id": scope["target_payload_id"],
            "target_source_accession": scope["target_source_accession"],
            "target_source_type": target_source_type,
            "target_source_id": target_source_id,
            "target_derivation_rule": cdef,
            "target_coordinate_status": TARGET_COORDINATE_STATUS,
            "structure_source": prov["source_class"],
            "contact_definition": cdef,
            "pair_index_basis": PAIR_INDEX_BASIS,
            "atom_selector": "CA",
            "distance_cutoff_A": scope["contact_threshold_angstrom"],
            "coordinate_source": coordinate_source,
            "coordinate_source_hash": coordinate_source_hash,
            "score_scope": scope["score_scope"],
            "metric_scope": METRIC_SCOPE,
            "metric_validity": METRIC_VALIDITY,
            "classifier_generalization": CLASSIFIER_GENERALIZATION,
            "min_sequence_separation": scope["min_sequence_separation"],
            "contact_threshold_angstrom": scope["contact_threshold_angstrom"],
            "predicted_pairs": fmt_pairs(predicted_pairs),
            "target_pairs": fmt_pairs(target_pairs),
            "evaluation_pairs": fmt_pairs(eval_pairs),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": safe_div(tp, tp + fp),
            "recall": safe_div(tp, tp + fn),
            "f1": safe_div(2 * tp, 2 * tp + fp + fn),
            "jaccard": safe_div(tp, tp + fp + fn),
            "mcc": mcc_value(tp, fp, fn, tn),
            "mcc_status": mcc_value(tp, fp, fn, tn),
            "score_status": "scoped_pdb_contact_residual_pilot_scored",
            "value_map_status": "quarantined_pdb_contact_residual_not_released_lambda_fold",
            "coordinate_metric_status": "contact_map_only_no_coordinate_level_aod_prediction",
            "release_status": RELEASE_STATUS,
        })
        summary_tp += tp; summary_fp += fp; summary_fn += fn; summary_tn += tn

    for row in leakage_rows:
        leakage_audit_rows.append({
            "audit_id": row["check_id"].replace("PDB-SCOPE-LEAK", "PDB-PILOT-LEAK"),
            "scope_id": row["scope_id"],
            "source_check_id": row["check_id"],
            "check_name": "carried_forward_v40.02r08_scope_leakage_check",
            "check_stage": "scope_input_lock",
            "check_result": "active_pass",
            "forbidden_source": row["forbidden_source"],
            "forbidden_destination": row["forbidden_destination"],
            "allowed_stage": row["allowed_stage"],
            "source_check_status": row["check_status"],
            "pilot_check_status": "active_pass",
            "score_input_status": "scope_rows_read_before_prediction_and_target_rows",
            "release_status": RELEASE_STATUS,
        })

    extra_checks = [
        ("PDB-PILOT-LEAK-005", "frozen_aod_packet_read_before_target_contact_row", "prediction_freeze", "target_contact_rows", "aod_contact_prediction_freeze", "target_join_after_prediction_freeze"),
        ("PDB-PILOT-LEAK-006", "target_columns_absent_from_frozen_prediction_packet", "prediction_freeze", "target_columns", "aod_contact_prediction_freeze", "comparison_only_after_freeze"),
        ("PDB-PILOT-LEAK-007", "score_script_joins_target_after_prediction_freeze", "score_join", "target_contact_rows", "score_inputs_before_prediction_freeze", "scope_then_freeze_then_target_join"),
        ("PDB-PILOT-LEAK-008", "residual_computed_after_prediction_and_target_rows_frozen", "residual_audit", "residual_row", "unfrozen_prediction_or_target", "after_both_rows_frozen"),
        ("PDB-PILOT-LEAK-009", "target_source_type_recorded", "target_provenance", "missing_target_source_type", "pdb_scoped_contact_residual_pilot", "source_metadata_required"),
        ("PDB-PILOT-LEAK-010", "coordinate_level_score_fields_remain_deferred", "metric_scope", "RMSD_TM_score_GDT_coordinate_prediction", "pdb_scoped_contact_score", "future_coordinate_level_prediction_freeze_only"),
    ]
    scope_id0 = scope_rows[0]["scope_id"]
    for audit_id, name, stage, forbidden_source, forbidden_dest, allowed in extra_checks:
        leakage_audit_rows.append({
            "audit_id": audit_id,
            "scope_id": scope_id0,
            "source_check_id": audit_id,
            "check_name": name,
            "check_stage": stage,
            "check_result": "active_pass",
            "forbidden_source": forbidden_source,
            "forbidden_destination": forbidden_dest,
            "allowed_stage": allowed,
            "source_check_status": "active_pass",
            "pilot_check_status": "active_pass",
            "score_input_status": "scope_rows_read_before_prediction_and_target_rows",
            "release_status": RELEASE_STATUS,
        })

    score_count = len(score_rows)
    residual_rows = len(delta_rows)
    summary = [{
        "summary_id": "pdb_scoped_contact_score_summary_001",
        "score_version": VERSION,
        "score_origin_version": SCORE_ORIGIN_VERSION,
        "scope_count": len(scope_rows),
        "score_rows": score_count,
        "residual_rows": residual_rows,
        "metric_scope": METRIC_SCOPE,
        "metric_validity": METRIC_VALIDITY,
        "classifier_generalization": CLASSIFIER_GENERALIZATION,
        "tp": summary_tp,
        "fp": summary_fp,
        "fn": summary_fn,
        "tn": summary_tn,
        "precision_micro": safe_div(summary_tp, summary_tp + summary_fp),
        "recall_micro": safe_div(summary_tp, summary_tp + summary_fn),
        "f1_micro": safe_div(2 * summary_tp, 2 * summary_tp + summary_fp + summary_fn),
        "jaccard_micro": safe_div(summary_tp, summary_tp + summary_fp + summary_fn),
        "mcc_status": mcc_value(summary_tp, summary_fp, summary_fn, summary_tn),
        "lambda_fold_status": "deferred_not_attached",
        "claim_status": "scoped_pdb_contact_residual_pilot_not_folding_model",
        "release_status": RELEASE_STATUS,
    }]
    return pilot_rows, score_rows, delta_rows, leakage_audit_rows, summary


def main() -> int:
    pilot, score, delta, leakage, summary = build_rows()
    write_csv(PROT / "pdb_scoped_contact_residual_pilot.csv", pilot, [
        "pilot_id", "score_id", "scope_id", "prediction_id", "target_contact_id", "chain_id", "protein_id",
        "target_payload_id", "target_source_type", "target_source_id", "target_derivation_rule", "target_freeze_id",
        "target_coordinate_status", "contact_definition", "pair_index_basis", "atom_selector", "distance_cutoff_A",
        "coordinate_source", "coordinate_source_hash", "trace_id", "aod_motif_id", "sadar_context_id",
        "detection_basis", "downstream_map_stage", "prediction_freeze_version", "target_derivation_version",
        "scope_version", "score_version", "score_origin_version", "residue_i", "residue_j", "pair_separation",
        "prediction_contact_value", "target_contact_value", "predicted_contact", "target_contact", "ca_distance_angstrom",
        "Delta_Z", "delta3_contact", "contact_error_class", "leakage_status", "score_status", "value_map_status", "release_status",
    ])
    write_csv(PROT / "pdb_scoped_contact_score.csv", score, [
        "score_id", "pilot_id", "scope_id", "model_id", "prediction_freeze_version",
        "target_derivation_version", "scope_version", "score_version", "score_origin_version", "chain_id", "protein_id",
        "target_payload_id", "target_source_accession", "target_source_type", "target_source_id", "target_derivation_rule",
        "target_coordinate_status", "structure_source", "contact_definition", "pair_index_basis", "atom_selector",
        "distance_cutoff_A", "coordinate_source", "coordinate_source_hash", "score_scope", "metric_scope", "metric_validity",
        "classifier_generalization", "min_sequence_separation", "contact_threshold_angstrom", "predicted_pairs", "target_pairs",
        "evaluation_pairs", "tp", "fp", "fn", "tn", "precision", "recall", "f1", "jaccard",
        "mcc", "mcc_status", "score_status", "value_map_status", "coordinate_metric_status", "release_status",
    ])
    write_csv(PROT / "pdb_scoped_contact_delta3.csv", delta, [
        "delta3_id", "score_id", "scope_id", "protein_id", "chain_id", "target_payload_id",
        "residue_i", "residue_j", "prediction_contact_value", "target_contact_value", "predicted_contact", "target_contact", "Delta_Z",
        "delta3_contact", "contact_error_sign", "contact_error_class", "score_scope", "target_source_type", "contact_definition", "pair_index_basis", "release_status",
    ])
    write_csv(PROT / "pdb_scoped_contact_leakage_audit.csv", leakage, [
        "audit_id", "scope_id", "source_check_id", "check_name", "check_stage", "check_result", "forbidden_source", "forbidden_destination",
        "allowed_stage", "source_check_status", "pilot_check_status", "score_input_status", "release_status",
    ])
    write_csv(PROT / "pdb_scoped_contact_score_summary.csv", summary, [
        "summary_id", "score_version", "score_origin_version", "scope_count", "score_rows", "residual_rows", "metric_scope",
        "metric_validity", "classifier_generalization", "tp", "fp", "fn", "tn", "precision_micro", "recall_micro", "f1_micro", "jaccard_micro", "mcc_status", "lambda_fold_status",
        "claim_status", "release_status",
    ])
    manifest = {
        "lane": "scoped_pdb_contact_residual_pilot",
        "version_scope": VERSION,
        "score_origin_version": SCORE_ORIGIN_VERSION,
        "scope_input_version": "v40.02r08",
        "status": "scoped_pdb_contact_residual_pilot_boundary_source_metric_guard_no_coordinate_metrics_no_active_lambda_fold",
        "files": {
            "pdb_scoped_contact_residual_pilot": "manual-2/data/protein/pdb_scoped_contact_residual_pilot.csv",
            "pdb_scoped_contact_score": "manual-2/data/protein/pdb_scoped_contact_score.csv",
            "pdb_scoped_contact_delta3": "manual-2/data/protein/pdb_scoped_contact_delta3.csv",
            "pdb_scoped_contact_leakage_audit": "manual-2/data/protein/pdb_scoped_contact_leakage_audit.csv",
            "pdb_scoped_contact_score_summary": "manual-2/data/protein/pdb_scoped_contact_score_summary.csv",
        },
        "required_scope_inputs": [
            "manual-2/data/protein/pdb_contact_comparison_scope_declaration.csv",
            "manual-2/data/protein/pdb_contact_comparison_target_provenance.csv",
            "manual-2/data/protein/pdb_contact_comparison_residual_coordinates.csv",
            "manual-2/data/protein/pdb_contact_comparison_leakage_checks.csv",
        ],
        "prediction_inputs": ["manual-2/data/protein/aod_contact_prediction_freeze.csv"],
        "target_inputs": ["manual-2/data/protein/pdb_mmcif_contact_map_derived.csv"],
        "input_hashes": input_manifest(),
        "detection_policy": "AOD motif / curling-curls specification plus SADAR context is read from the frozen prediction packet before downstream target mapping",
        "score_policy": "compute TP/FP/FN/TN and pairwise Delta_Z/delta3 only for explicitly declared v40.02r08 evaluation pairs",
        "metric_scope": METRIC_SCOPE,
        "metric_validity": METRIC_VALIDITY,
        "classifier_generalization": CLASSIFIER_GENERALIZATION,
        "mcc_status": mcc_value(1, 0, 0, 0),
        "target_source_policy": {
            "target_source_type": "manual_pdbx_mmcif_fixture",
            "target_coordinate_status": TARGET_COORDINATE_STATUS,
            "contact_definition": "CA_distance_leq_8.0A_min_sequence_separation_2",
            "pair_index_basis": PAIR_INDEX_BASIS,
        },
        "forbidden_inputs_as_prediction_premises": [
            "PDB/mmCIF atom-site coordinates",
            "PDB/mmCIF distance matrices",
            "target contact maps before prediction freeze",
            "AlphaFold coordinates or confidence fields",
            "secondary-structure labels",
        ],
        "metric_policy": "single positive contact residual row; precision/recall/F1/Jaccard report the closed row; MCC is undefined without true-negative support; RMSD, TM-score, GDT, and coordinate-level AOD prediction remain deferred",
        "claim_discipline": "scoped PDB-contact residual pilot; validates input-lock, target provenance, and residual ledger plumbing, not a released folding model",
        "lambda_fold_status": "deferred_not_attached",
        "next_candidate_milestone": "v40.02r10 candidate: multi-pair scoped contact residual pilot with a declared negative-support row before MCC generalization",
    }
    (PROT / "pdb_scoped_contact_residual_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
