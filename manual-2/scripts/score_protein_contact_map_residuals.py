#!/usr/bin/env python3
"""Score frozen AOD contact/reclosure predictions against normalized target contact maps.

This v40.02r06 generator is offline and deterministic. It reads the frozen
v40.02r05 AOD contact/reclosure prediction packets and only then reads
normalized target contact-map rows. It does not compute RMSD, TM-score, GDT, or
any full coordinate-level structure metric.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r06"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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


def build_rows():
    predictions = read_csv(PROT / "aod_contact_prediction_freeze.csv")
    targets = read_csv(PROT / "protein_contact_map_targets.csv")
    by_chain: dict[str, list[dict[str, str]]] = {}
    for row in predictions:
        by_chain.setdefault(row["chain_id"], []).append(row)
    target_by_protein = {row["protein_id"]: row for row in targets if row["contact_pairs"] and not row["contact_pairs"].startswith("deferred")}
    chain_to_protein = {"chain_GAS_tripeptide_seed": "manual_seed_GAS"}

    score_rows: list[dict[str, object]] = []
    delta_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    delta_index = 1
    for score_index, (chain_id, protein_id) in enumerate(chain_to_protein.items(), 1):
        target = target_by_protein[protein_id]
        min_sep = int(target["min_sequence_separation"])
        n = int(target["residue_count"])
        allowed_pairs = {(i, j) for i in range(1, n + 1) for j in range(i + 1, n + 1) if (j - i) >= min_sep}
        predicted = {(int(row["residue_i"]), int(row["residue_j"])) for row in by_chain[chain_id] if int(row["pair_separation"]) >= min_sep and row["predicted_contact"] == "1"}
        observed = parse_pairs(target["contact_pairs"])
        eval_pairs = allowed_pairs | predicted | observed
        tp = sum(1 for pair in eval_pairs if pair in predicted and pair in observed)
        fp = sum(1 for pair in eval_pairs if pair in predicted and pair not in observed)
        fn = sum(1 for pair in eval_pairs if pair not in predicted and pair in observed)
        tn = sum(1 for pair in eval_pairs if pair not in predicted and pair not in observed)
        denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        mcc = "undefined_no_true_negative_denominator" if denom == 0 else f"{((tp * tn) - (fp * fn)) / math.sqrt(denom):.6f}".rstrip("0").rstrip(".")
        score_id = f"protein_contact_score_{score_index:03d}"
        score_rows.append({"score_id": score_id, "model_id": "AOD-CRPF-v40.02r05", "prediction_freeze_version": "v40.02r05", "score_version": VERSION, "chain_id": chain_id, "protein_id": protein_id, "contact_target_id": target["contact_target_id"], "structure_source": target["structure_source"], "score_scope": "declared_contact_subset_min_sequence_separation", "min_sequence_separation": min_sep, "contact_threshold_angstrom": target["contact_threshold_angstrom"], "residue_count": n, "predicted_pairs": fmt_pairs(predicted), "target_pairs": fmt_pairs(observed), "evaluation_pairs": fmt_pairs(eval_pairs), "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": safe_div(tp, tp + fp), "recall": safe_div(tp, tp + fn), "f1": safe_div(2 * tp, 2 * tp + fp + fn), "jaccard": safe_div(tp, tp + fp + fn), "mcc": mcc, "score_status": "scored_manual_fixture_contact_map", "value_map_status": "quarantined_comparison_not_released_lambda_fold", "coordinate_metric_status": "not_coordinate_level_prediction", "release_status": "v40.02r06_contact_residual_comparison"})
        for i, j in sorted(eval_pairs):
            pred = 1 if (i, j) in predicted else 0
            obs = 1 if (i, j) in observed else 0
            delta = pred - obs
            if pred and obs:
                cls = "TP"
            elif pred and not obs:
                cls = "FP"
            elif obs and not pred:
                cls = "FN"
            else:
                cls = "TN"
            delta_rows.append({"delta3_id": f"protein_contact_delta3_{delta_index:03d}", "score_id": score_id, "protein_id": protein_id, "chain_id": chain_id, "residue_i": i, "residue_j": j, "predicted_contact": pred, "target_contact": obs, "Delta_Z": delta, "delta3_contact": delta % 3, "contact_error_sign": (delta > 0) - (delta < 0), "contact_error_class": cls, "score_scope": "declared_contact_subset_min_sequence_separation", "release_status": "v40.02r06_contact_residual_comparison"})
            delta_index += 1
        max_abs = max(abs(int(row["Delta_Z"])) for row in delta_rows if row["score_id"] == score_id)
        residual_rows.append({"analysis_id": "protein_residual_analysis_001", "subject_id": protein_id, "subject_class": "manual_fixture_contact_map", "score_id": score_id, "comparison_status": "scored_against_frozen_prediction", "support_count": len(eval_pairs), "max_abs_Delta_Z": max_abs, "delta3_status": "zero_residual" if fp == 0 and fn == 0 else "nonzero_residual", "limitation_class": "manual_fixture_not_external_ground_truth", "residual_note": "manual schema fixture only; validates contact-map residual machinery, not an experimental folding claim", "release_status": "v40.02r06_contact_residual_comparison"})

    for chain_id in sorted(by_chain):
        if chain_id not in chain_to_protein:
            residual_rows.append({"analysis_id": f"protein_residual_analysis_{len(residual_rows) + 1:03d}", "subject_id": chain_id, "subject_class": "frozen_prediction_without_target_map", "score_id": "not_scored", "comparison_status": "deferred_no_matching_contact_target_in_v40.02r06", "support_count": "0", "max_abs_Delta_Z": "not_evaluated", "delta3_status": "not_evaluated", "limitation_class": "target_packet_missing_for_this_chain", "residual_note": "frozen prediction is retained for future target mapping; no surrogate target is introduced", "release_status": "v40.02r06_contact_residual_comparison"})
    for target in targets:
        if target["protein_id"] not in chain_to_protein.values():
            deferred = target["contact_pairs"].startswith("deferred")
            residual_rows.append({"analysis_id": f"protein_residual_analysis_{len(residual_rows) + 1:03d}", "subject_id": target["protein_id"], "subject_class": target["structure_source"], "score_id": "not_scored", "comparison_status": "deferred_locator_only_no_coordinate_payload" if deferred else "deferred_no_matching_frozen_prediction", "support_count": "0", "max_abs_Delta_Z": "not_evaluated", "delta3_status": "not_evaluated", "limitation_class": "locator_only_no_coordinate_payload" if deferred else "manual_fixture_target_without_aod_prediction", "residual_note": "target row is not used as a prediction premise and remains comparison-only until a frozen prediction and coordinate/contact payload exist", "release_status": "v40.02r06_contact_residual_comparison"})
    tp = sum(int(row["tp"]) for row in score_rows)
    fp = sum(int(row["fp"]) for row in score_rows)
    fn = sum(int(row["fn"]) for row in score_rows)
    tn = sum(int(row["tn"]) for row in score_rows)
    summary = [{"summary_id": "protein_contact_score_summary_001", "score_scope": "manual_fixture_declared_min_sequence_subset", "prediction_freeze_version": "v40.02r05", "score_version": VERSION, "score_rows": len(score_rows), "deferred_analysis_rows": sum(1 for row in residual_rows if row["score_id"] == "not_scored"), "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision_micro": safe_div(tp, tp + fp), "recall_micro": safe_div(tp, tp + fn), "f1_micro": safe_div(2 * tp, 2 * tp + fp + fn), "jaccard_micro": safe_div(tp, tp + fp + fn), "mcc_status": "undefined_no_true_negative_denominator" if (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn) == 0 else "computed", "external_target_score_status": "deferred_locator_only_no_coordinate_payload", "lambda_fold_status": "deferred_not_attached", "claim_status": "contact_map_residual_fixture_not_released_folding_model", "release_status": "v40.02r06_contact_residual_comparison"}]
    return score_rows, delta_rows, summary, residual_rows


def main() -> int:
    score, delta, summary, residual = build_rows()
    write_csv(PROT / "protein_contact_score.csv", score, ["score_id", "model_id", "prediction_freeze_version", "score_version", "chain_id", "protein_id", "contact_target_id", "structure_source", "score_scope", "min_sequence_separation", "contact_threshold_angstrom", "residue_count", "predicted_pairs", "target_pairs", "evaluation_pairs", "tp", "fp", "fn", "tn", "precision", "recall", "f1", "jaccard", "mcc", "score_status", "value_map_status", "coordinate_metric_status", "release_status"])
    write_csv(PROT / "protein_contact_delta3.csv", delta, ["delta3_id", "score_id", "protein_id", "chain_id", "residue_i", "residue_j", "predicted_contact", "target_contact", "Delta_Z", "delta3_contact", "contact_error_sign", "contact_error_class", "score_scope", "release_status"])
    write_csv(PROT / "protein_score_summary.csv", summary, ["summary_id", "score_scope", "prediction_freeze_version", "score_version", "score_rows", "deferred_analysis_rows", "tp", "fp", "fn", "tn", "precision_micro", "recall_micro", "f1_micro", "jaccard_micro", "mcc_status", "external_target_score_status", "lambda_fold_status", "claim_status", "release_status"])
    write_csv(PROT / "protein_folding_residual_analysis.csv", residual, ["analysis_id", "subject_id", "subject_class", "score_id", "comparison_status", "support_count", "max_abs_Delta_Z", "delta3_status", "limitation_class", "residual_note", "release_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
