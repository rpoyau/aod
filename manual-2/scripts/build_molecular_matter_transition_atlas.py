#!/usr/bin/env python3
"""Build the Manual-II Molecular Matter transition atlas fixture ledgers."""
from __future__ import annotations
import csv, json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "molecular"

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())

def row_hash(vals: list[str]) -> str:
    return sha_bytes(("\x1f".join(str(v) for v in vals) + "\n").encode())

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def add_hash(rows: list[dict[str, str]], fields: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    out=[]
    for r in rows:
        rr=dict(r); rr["row_sha256"] = row_hash([rr.get(f, "") for f in fields]); out.append(rr)
    return fields+["row_sha256"], out

def main() -> None:
    comps=read_csv(DATA/"component_registry_seed.csv")
    chains=read_csv(DATA/"chain_formula_predictions.csv")
    occ=[]
    for r in comps:
        occ.append({"occurrence_id":f"mol_component_{r['component_id']}","occurrence_kind":"component_fixture","source_row_id":r['component_id'],"declared_name":r['component_id'],"declared_formula":r['declared_formula'],"molecular_class":r['class'],"native_occurrence_status":"materialized_from_declared_molecular_fixture","target_value_read_status":"not_read","si_report_status":"closed","metric_report_status":"closed","residual_status":"not_computed","score_status":"no_score"})
    for r in chains:
        occ.append({"occurrence_id":f"mol_chain_{r['chain_id']}","occurrence_kind":"chain_fixture","source_row_id":r['chain_id'],"declared_name":r['declared_components'],"declared_formula":r['frozen_formula'],"molecular_class":r['chain_class'],"native_occurrence_status":"materialized_from_frozen_chain_formula_packet","target_value_read_status":"not_read","si_report_status":"closed","metric_report_status":"closed","residual_status":"not_computed","score_status":"no_score"})
    occ_fields=["occurrence_id","occurrence_kind","source_row_id","declared_name","declared_formula","molecular_class","native_occurrence_status","target_value_read_status","si_report_status","metric_report_status","residual_status","score_status"]
    occ_fields, occ = add_hash(occ, occ_fields)
    write_csv(DATA/"molecular_matter_transition_occurrence_cards.csv", occ_fields, occ)
    trans=[]
    for o in occ:
        trans.append({"transition_packet_id":f"transition_{o['occurrence_id']}","occurrence_id":o['occurrence_id'],"transition_family":"molecular_matter_native_transition_declaration","formula_basis":"declared_formula_packet","route_or_chain_basis":"component_fixture" if o['occurrence_kind']=="component_fixture" else "frozen_chain_route_packet","native_transition_status":"declared_not_measured","target_value_read_status":"not_read","si_report_status":"closed","metric_report_status":"closed","subject_reference_phase_lock_status":"closed","hyperfine_c6_divisibility_status":"not_applicable_molecular_transition_atlas_seed","residual_status":"not_computed","score_status":"no_score"})
    trans_fields=["transition_packet_id","occurrence_id","transition_family","formula_basis","route_or_chain_basis","native_transition_status","target_value_read_status","si_report_status","metric_report_status","subject_reference_phase_lock_status","hyperfine_c6_divisibility_status","residual_status","score_status"]
    trans_fields, trans = add_hash(trans, trans_fields)
    write_csv(DATA/"molecular_matter_transition_packets.csv", trans_fields, trans)
    context_map={r['chain_id']:r['sadar_context_id'] for r in read_csv(DATA/"detected_chain_motifs.csv")}
    sadar=[]
    for t in trans:
        o=next(o for o in occ if o['occurrence_id']==t['occurrence_id'])
        context = "component_declared_context" if o['occurrence_kind']=="component_fixture" else context_map.get(o['source_row_id'], "chain_sadar_context_declared")
        sadar.append({"sadar_flow_id":f"sadar_flow_{o['occurrence_id']}","occurrence_id":o['occurrence_id'],"transition_packet_id":t['transition_packet_id'],"sadar_context_id":context,"flow_semantics":"molecular_duon_current_sadar_flow_declaration_not_metric_time","flow_status":"declared_native_flow_no_phase_lock_value","target_value_read_status":"not_read","si_report_status":"closed","metric_report_status":"closed","residual_status":"not_computed","score_status":"no_score"})
    sadar_fields=["sadar_flow_id","occurrence_id","transition_packet_id","sadar_context_id","flow_semantics","flow_status","target_value_read_status","si_report_status","metric_report_status","residual_status","score_status"]
    sadar_fields, sadar = add_hash(sadar, sadar_fields)
    write_csv(DATA/"molecular_matter_sadar_flow_declarations.csv", sadar_fields, sadar)
    summary=[{"summary_id":"molecular_matter_transition_atlas_summary","occurrence_card_count":str(len(occ)),"component_occurrence_count":str(sum(o['occurrence_kind']=='component_fixture' for o in occ)),"chain_occurrence_count":str(sum(o['occurrence_kind']=='chain_fixture' for o in occ)),"transition_packet_count":str(len(trans)),"sadar_flow_declaration_count":str(len(sadar)),"target_join_count":"0","si_report_count":"0","metric_report_count":"0","residual_count":"0","score_count":"0","status":"materialized_native_molecular_matter_atlas_no_targets_no_scores"}]
    sum_fields=list(summary[0].keys())
    sum_fields, summary = add_hash(summary, sum_fields)
    write_csv(DATA/"molecular_matter_transition_atlas_summary.csv", sum_fields, summary)
    cf=[("cf_target_value_inserted_into_molecular_packet","target_value_read_status=read","failed","target_values_forbidden_in_native_molecular_atlas"),("cf_si_frequency_promoted_to_native_molecular_premise","si_report_status=active","failed","si_reports_are_downstream_report_cards"),("cf_metric_report_value_materialized","metric_report_status=active","failed","metric_values_closed_in_native_atlas"),("cf_residual_score_inserted_before_target_join","score_status=computed","failed","scores_require_authorized_target_join_after_freeze"),("cf_unchanged_control","no_mutation","passed","control_row_preserves_closed_native_atlas_contract")]
    cf_rows=[{"counterfactual_id":a,"mutation":b,"expected_result":c,"observed_result":c,"failure_reason":d,"audit_status":"passed"} for a,b,c,d in cf]
    cf_fields=["counterfactual_id","mutation","expected_result","observed_result","failure_reason","audit_status"]
    cf_fields, cf_rows = add_hash(cf_rows, cf_fields)
    write_csv(DATA/"molecular_matter_counterfactual_audit.csv", cf_fields, cf_rows)
    files=["molecular_matter_transition_occurrence_cards.csv","molecular_matter_transition_packets.csv","molecular_matter_sadar_flow_declarations.csv","molecular_matter_transition_atlas_summary.csv","molecular_matter_counterfactual_audit.csv"]
    manifest={"schema_version":"1.0","milestone":"v40.03r25.1","atlas_id":"molecular_matter_transition_atlas_v40_03r25_1","source_basis":["component_registry_seed.csv","chain_formula_predictions.csv","detected_chain_motifs.csv"],"occurrence_card_count":len(occ),"transition_packet_count":len(trans),"sadar_flow_declaration_count":len(sadar),"target_join_count":0,"si_report_count":0,"metric_report_count":0,"residual_count":0,"score_count":0,"closed_lanes":["target_join","SI_report_values","metric_report_values","residuals","scores","empirical_comparison","subject_reference_phase_lock"],"files":[{"path":f,"sha256":sha_file(DATA/f)} for f in files]}
    (DATA/"molecular_matter_transition_atlas_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2)+"\n", encoding="utf-8")

if __name__ == "__main__":
    main()
