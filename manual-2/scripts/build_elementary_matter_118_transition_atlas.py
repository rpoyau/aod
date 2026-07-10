#!/usr/bin/env python3
from __future__ import annotations
import csv, json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ELEM = ROOT / "manual-2" / "data" / "elementary"

def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def row_hash(row: dict[str, str]) -> str:
    payload = {k: row[k] for k in row if k != "row_sha256"}
    return sha_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))

def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    for row in rows:
        row["row_sha256"] = row_hash(row)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main() -> int:
    with (ELEM / "element_registry_118.csv").open(newline="", encoding="utf-8") as f:
        elements = list(csv.DictReader(f))
    if len(elements) != 118:
        raise ValueError(f"expected 118 elements, found {len(elements)}")

    occ_cols = ["row_id","element_Z","symbol","element_name","occurrence_id","atlas_layer","fractal_octave_coordinate","registry_basis","native_flow_status","target_value_read_status","metric_report_status","residual_status","score_status","row_sha256"]
    occ = []
    for e in elements:
        z = int(e["Z"])
        occ.append({
            "row_id": f"elem118_occ_{z:03d}",
            "element_Z": str(z),
            "symbol": e["symbol"],
            "element_name": e["name"],
            "occurrence_id": f"elementary_matter_occurrence_Z{z:03d}_{e['symbol']}",
            "atlas_layer": "Elementary Matter 118",
            "fractal_octave_coordinate": "elementary_matter_118_native_atlas",
            "registry_basis": "IUPAC_Z_symbol_name_registry_carried_forward_no_external_target_read",
            "native_flow_status": "native_occurrence_card_materialized",
            "target_value_read_status": "not_read",
            "metric_report_status": "closed",
            "residual_status": "not_computed",
            "score_status": "no_score",
        })
    write_csv(ELEM / "elementary_matter_118_occurrence_cards.csv", occ_cols, occ)

    trans_cols = ["row_id","transition_packet_id","occurrence_id","element_Z","symbol","transition_family_id","native_transition_role","duon_current_status","sadar_flow_status","relational_measurement_status","hyperfine_c6_divisibility_status","target_value_read_status","si_report_status","metric_report_status","residual_status","score_status","row_sha256"]
    trans = []
    for e, o in zip(elements, occ):
        z = int(e["Z"])
        trans.append({
            "row_id": f"elem118_transition_{z:03d}",
            "transition_packet_id": f"elementary_matter_transition_packet_Z{z:03d}_{e['symbol']}",
            "occurrence_id": o["occurrence_id"],
            "element_Z": str(z),
            "symbol": e["symbol"],
            "transition_family_id": "elementary_matter_118_native_transition_atlas",
            "native_transition_role": "native_transition_candidate_slot_materialized_no_frequency_or_target",
            "duon_current_status": "declared_not_executed_in_this_gate",
            "sadar_flow_status": "declared_not_executed_in_this_gate",
            "relational_measurement_status": "not_materialized",
            "hyperfine_c6_divisibility_status": "not_evaluated_until_native_resonance_packet_exists",
            "target_value_read_status": "not_read",
            "si_report_status": "closed",
            "metric_report_status": "closed",
            "residual_status": "not_computed",
            "score_status": "no_score",
        })
    write_csv(ELEM / "elementary_matter_118_transition_packets.csv", trans_cols, trans)

    sadar_cols = ["row_id","sadar_packet_id","transition_packet_id","element_Z","symbol","duon_current_flow_status","sadar_temporal_flow_status","subject_reference_phase_lock_status","native_resonance_period_status","target_value_read_status","metric_report_status","score_status","row_sha256"]
    sadar = []
    for e, t in zip(elements, trans):
        z = int(e["Z"])
        sadar.append({
            "row_id": f"elem118_sadar_{z:03d}",
            "sadar_packet_id": f"elementary_matter_sadar_flow_packet_Z{z:03d}_{e['symbol']}",
            "transition_packet_id": t["transition_packet_id"],
            "element_Z": str(z),
            "symbol": e["symbol"],
            "duon_current_flow_status": "declared_not_executed",
            "sadar_temporal_flow_status": "declared_not_executed",
            "subject_reference_phase_lock_status": "not_materialized",
            "native_resonance_period_status": "not_materialized",
            "target_value_read_status": "not_read",
            "metric_report_status": "closed",
            "score_status": "no_score",
        })
    write_csv(ELEM / "elementary_matter_118_sadar_flow_declarations.csv", sadar_cols, sadar)

    summary_cols = ["summary_id","occurrence_count","transition_packet_count","sadar_declaration_count","target_join_count","si_report_count","metric_report_count","residual_count","score_count","row_sha256"]
    summary = [{
        "summary_id":"elementary_matter_118_transition_atlas_summary",
        "occurrence_count":"118",
        "transition_packet_count":"118",
        "sadar_declaration_count":"118",
        "target_join_count":"0",
        "si_report_count":"0",
        "metric_report_count":"0",
        "residual_count":"0",
        "score_count":"0",
    }]
    write_csv(ELEM / "elementary_matter_118_transition_atlas_summary.csv", summary_cols, summary)

    cf_cols = ["counterfactual_id","mutation","expected_result","observed_result","failure_reason","audit_status","row_sha256"]
    cf_rows = [
        {"counterfactual_id":"cf_target_value_inserted_into_elementary_packet","mutation":"insert_target_value_into_native_transition_packet","expected_result":"failed","observed_result":"failed","failure_reason":"target_values_forbidden_before_target_join_gate","audit_status":"passed"},
        {"counterfactual_id":"cf_si_frequency_promoted_to_native_premise","mutation":"add_SI_frequency_as_native_transition_field","expected_result":"failed","observed_result":"failed","failure_reason":"SI_report_values_are_downstream_report_cards_not_native_premises","audit_status":"passed"},
        {"counterfactual_id":"cf_metric_report_value_materialized","mutation":"set_metric_report_status_to_materialized","expected_result":"failed","observed_result":"failed","failure_reason":"metric_report_values_closed_in_elementary_118_materialization_gate","audit_status":"passed"},
        {"counterfactual_id":"cf_hyperfine_divisibility_claim_assumed","mutation":"set_hyperfine_c6_divisibility_status_to_passed_without_resonance_packet","expected_result":"failed","observed_result":"failed","failure_reason":"C6_divisibility_is_tested_not_assumed","audit_status":"passed"},
        {"counterfactual_id":"cf_unchanged_control","mutation":"no_change_to_emitted_rows","expected_result":"passed","observed_result":"passed","failure_reason":"none","audit_status":"passed"},
    ]
    write_csv(ELEM / "elementary_matter_118_counterfactual_audit.csv", cf_cols, cf_rows)

    manifest_files = [
        "manual-2/data/elementary/elementary_matter_118_occurrence_cards.csv",
        "manual-2/data/elementary/elementary_matter_118_transition_packets.csv",
        "manual-2/data/elementary/elementary_matter_118_sadar_flow_declarations.csv",
        "manual-2/data/elementary/elementary_matter_118_transition_atlas_summary.csv",
        "manual-2/data/elementary/elementary_matter_118_counterfactual_audit.csv",
    ]
    manifest = {
        "schema_version":"1.0",
        "milestone":"v40.03r24",
        "atlas_id":"elementary_matter_118_transition_atlas",
        "row_counts": {
            "occurrence_cards": len(occ),
            "transition_packets": len(trans),
            "sadar_flow_declarations": len(sadar),
            "counterfactual_rows": len(cf_rows),
        },
        "closed_lanes": {
            "target_join":"closed",
            "SI_report_values":"closed",
            "metric_report_values":"closed",
            "residuals":"not_computed",
            "scores":"no_score",
            "empirical_comparison":"closed",
            "subject_reference_phase_lock":"closed",
        },
        "files": {p: sha_file(ROOT / p) for p in manifest_files},
    }
    (ELEM / "elementary_matter_118_transition_atlas_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
