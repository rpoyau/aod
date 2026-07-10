#!/usr/bin/env python3
"""Freeze Manual II v40.02r05 AOD contact/reclosure predictions.

This generator is offline and deterministic. It reads only committed chain-spec,
trace, detector, and SADAR-context rows from the molecular D.E.C. lane. It does
not read PDB, AlphaFold, target contact-map, target distance-matrix,
secondary-structure, or confidence rows.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
MOL = ROOT / "manual-2" / "data" / "molecular"
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r05"
MODEL_ID = "AOD-CRPF-v40.02r05"

AA_ONE = {
    "glycine": "G",
    "alanine": "A",
    "serine": "S",
    "methionine": "M",
}


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


def peptide_sequence(chain_word: str) -> str:
    parts = chain_word.split("-")
    try:
        return "".join(AA_ONE[p] for p in parts)
    except KeyError:
        return ""


def build_predictions() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    specs = {row["chain_id"]: row for row in read_csv(MOL / "chain_word_spec.csv")}
    motifs = {row["chain_id"]: row for row in read_csv(MOL / "detected_chain_motifs.csv")}
    contexts = {row["chain_id"]: row for row in read_csv(MOL / "sadar_detector_context.csv")}

    input_contract = "ChainWordSpec+ReadOnlyTrace+DetectedChainMotif+SADARContext"
    model_rows = [{
        "model_id": MODEL_ID,
        "model_name": "AOD contact/reclosure prediction freeze",
        "version_scope": VERSION,
        "input_contract": input_contract,
        "allowed_input_files": ";".join([
            "manual-2/data/molecular/chain_word_spec.csv",
            "manual-2/data/molecular/read_only_trace_molecular_chain.csv",
            "manual-2/data/molecular/detected_chain_motifs.csv",
            "manual-2/data/molecular/sadar_detector_context.csv",
        ]),
        "forbidden_input_classes": ";".join([
            "external_structure_coordinates",
            "external_contact_maps",
            "external_distance_matrices",
            "secondary_structure_labels",
            "confidence_fields",
        ]),
        "prediction_output_files": "aod_contact_prediction_freeze.csv;aod_reclosure_motif_predictions.csv",
        "prediction_object": "contact/reclosure motifs only",
        "geometry_status": "not_full_3d_geometry_prediction",
        "contact_score_status": "not_scored_in_v40.02r05",
        "comparison_status": "not_compared_in_v40.02r05",
        "freeze_status": "frozen_before_external_comparison",
        "release_status": "v40.02r05_prediction_freeze",
    }]

    contact_rows: list[dict[str, object]] = []
    reclosure_rows: list[dict[str, object]] = []
    pair_index = 1
    reclosure_index = 1
    for chain_id in ["chain_GA_peptide_seed", "chain_GAS_tripeptide_seed"]:
        spec = specs[chain_id]
        motif = motifs[chain_id]
        context = contexts[chain_id]
        seq = peptide_sequence(spec["chain_word"])
        if not seq:
            continue
        n = len(seq)
        # Adjacent route contacts are recorded for all adjacent residue pairs.
        adjacent_pairs = [(i, i + 1, "adjacent_route_support") for i in range(1, n)]
        # Multi-link peptide rows also freeze a reclosure span from the first to last residue.
        reclosure_pairs = []
        if int(spec["link_count"]) >= 2:
            reclosure_pairs.append((1, n, "multi_link_reclosure_span"))
        seen: set[tuple[int, int]] = set()
        predicted_pairs: list[str] = []
        for i, j, pair_class in adjacent_pairs + reclosure_pairs:
            if (i, j) in seen:
                continue
            seen.add((i, j))
            predicted_pairs.append(f"{i}-{j}")
            contact_rows.append({
                "prediction_id": f"aod_contact_pred_{pair_index:03d}",
                "model_id": MODEL_ID,
                "chain_id": chain_id,
                "chain_class": spec["chain_class"],
                "sequence_alias": seq,
                "residue_i": i,
                "residue_j": j,
                "pair_separation": j - i,
                "predicted_contact": 1,
                "pair_class": pair_class,
                "prediction_basis": "water_route_reclosure_from_detected_chain_motif",
                "trace_id": motif["trace_id"],
                "motif_id": motif["motif_id"],
                "sadar_context_id": context["sadar_context_id"],
                "support_units": motif["support_units"],
                "input_basis": input_contract,
                "comparison_input_used": "false",
                "leak_check_status": "passed_no_external_comparison_input",
                "freeze_status": "frozen_before_external_comparison",
                "score_status": "not_scored_in_v40.02r05",
                "release_status": "v40.02r05_prediction_freeze",
            })
            pair_index += 1
        if predicted_pairs:
            reclosure_rows.append({
                "reclosure_id": f"aod_reclosure_pred_{reclosure_index:03d}",
                "model_id": MODEL_ID,
                "chain_id": chain_id,
                "sequence_alias": seq,
                "motif_kind": "water_route_chain_reclosure",
                "residue_span": f"1-{n}",
                "component_span": spec["declared_components"],
                "route_support_units": motif["support_units"],
                "trace_id": motif["trace_id"],
                "motif_id": motif["motif_id"],
                "sadar_context_id": context["sadar_context_id"],
                "predicted_reclosure_pairs": ";".join(predicted_pairs),
                "prediction_basis": "detected_route_support_and_sadar_context",
                "geometry_status": "contact_reclosure_only_not_full_3d_geometry",
                "scalar_status": "sadar_context_not_scalar_evaluated",
                "freeze_status": "frozen_before_external_comparison",
                "score_status": "not_scored_in_v40.02r05",
                "release_status": "v40.02r05_prediction_freeze",
            })
            reclosure_index += 1

    manifest = {
        "lane": "aod_contact_reclosure_prediction_freeze",
        "version_scope": VERSION,
        "status": "prediction_freeze_no_target_comparison_no_contact_score",
        "files": {
            "aod_folding_prediction_model_registry": "manual-2/data/protein/aod_folding_prediction_model_registry.csv",
            "aod_contact_prediction_freeze": "manual-2/data/protein/aod_contact_prediction_freeze.csv",
            "aod_reclosure_motif_predictions": "manual-2/data/protein/aod_reclosure_motif_predictions.csv",
        },
        "allowed_input_files": [
            "manual-2/data/molecular/chain_word_spec.csv",
            "manual-2/data/molecular/read_only_trace_molecular_chain.csv",
            "manual-2/data/molecular/detected_chain_motifs.csv",
            "manual-2/data/molecular/sadar_detector_context.csv",
        ],
        "forbidden_prediction_premises": [
            "PDB/mmCIF coordinates",
            "AlphaFold coordinates",
            "target contact maps",
            "target distance matrices",
            "secondary-structure labels",
            "confidence fields",
        ],
        "leakage_policy": "prediction rows are frozen before target comparison and use no external structure, contact, distance, secondary-structure, or confidence payloads",
        "freeze_policy": "contact/reclosure motif packets are immutable inputs for the later v40.02r06 residual comparison gate",
        "score_policy": "no contact score, RMSD, TM-score, GDT, or active folding value map is released in v40.02r05",
        "next_milestone": "v40.02r06 -- Protein Contact-Map Residual / Folding Target Comparison",
    }
    return model_rows, contact_rows, reclosure_rows, manifest


def main() -> int:
    model_rows, contact_rows, reclosure_rows, manifest = build_predictions()
    write_csv(PROT / "aod_folding_prediction_model_registry.csv", model_rows, [
        "model_id", "model_name", "version_scope", "input_contract", "allowed_input_files",
        "forbidden_input_classes", "prediction_output_files", "prediction_object", "geometry_status",
        "contact_score_status", "comparison_status", "freeze_status", "release_status",
    ])
    write_csv(PROT / "aod_contact_prediction_freeze.csv", contact_rows, [
        "prediction_id", "model_id", "chain_id", "chain_class", "sequence_alias", "residue_i",
        "residue_j", "pair_separation", "predicted_contact", "pair_class", "prediction_basis",
        "trace_id", "motif_id", "sadar_context_id", "support_units", "input_basis",
        "comparison_input_used", "leak_check_status", "freeze_status", "score_status", "release_status",
    ])
    write_csv(PROT / "aod_reclosure_motif_predictions.csv", reclosure_rows, [
        "reclosure_id", "model_id", "chain_id", "sequence_alias", "motif_kind", "residue_span",
        "component_span", "route_support_units", "trace_id", "motif_id", "sadar_context_id",
        "predicted_reclosure_pairs", "prediction_basis", "geometry_status", "scalar_status",
        "freeze_status", "score_status", "release_status",
    ])
    (PROT / "aod_prediction_freeze_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
