#!/usr/bin/env python3
"""Build the repaired C6/hydrogen-first Manual-I roadmap artifacts.

The certified six-transition recurrence is retained as a shared recurrence and
support fixture. It is not a temporal calibration and it does not define a
monon-to-bip conversion. Temporal measurement is delegated to the relational
SADAR lock protocol. No target value is read and no scientific row is recomputed.
"""
from __future__ import annotations
import csv, hashlib, json, math
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
C6 = ROOT / "manual" / "data" / "c6"
ROADMAP = ROOT / "manual" / "data" / "roadmap"
VERSION = "v40.03r07"
M1_DETECTION = ROOT / "manual/data/cs133/cs133_structural_detection_result.csv"
M2_CERTIFICATE = ROOT / "manual/data/cs133/cs133_native_recurrence_certificate.csv"
M2_COUNTERFACTUAL = ROOT / "manual/data/cs133/cs133_native_recurrence_counterfactual_audit.csv"
TEMPORAL_MANIFEST = ROOT / "manual/data/temporal_relational/relational_temporal_semantics_manifest.json"


def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def cjson(obj: object) -> bytes: return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
def attach(row: Mapping[str, object], field: str) -> dict[str, str]:
    out={k:str(v) for k,v in row.items()}; out[field]=sha(cjson({k:out[k] for k in sorted(out) if k!=field})); return out

def read_one(p: Path) -> dict[str,str]:
    with p.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    if len(rows)!=1: raise ValueError(p)
    return rows[0]

def write_csv(p: Path, fields: Sequence[str], rows: Iterable[Mapping[str,object]]) -> None:
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(fields),lineterminator="\n"); w.writeheader()
        for row in rows: w.writerow({k:str(row.get(k,"")) for k in fields})

def verify_source() -> tuple[dict[str,str],dict[str,str],dict[str,str]]:
    d,c,x=read_one(M1_DETECTION),read_one(M2_CERTIFICATE),read_one(M2_COUNTERFACTUAL)
    for k,v in {"detected_support_core":"1:2","declared_scope_L":"6","scope_conditioned_form":"1:2:6","target_frequency_input_status":"absent"}.items():
        if d.get(k)!=v: raise ValueError((k,d.get(k),v))
    for k,v in {"transition_count":"6","primitive_recurrence_bip_count":"6","full_period_closure":"passed","proper_prefix_closure_count":"0","target_frequency_input_status":"absent"}.items():
        if c.get(k)!=v: raise ValueError((k,c.get(k),v))
    if not TEMPORAL_MANIFEST.is_file(): raise FileNotFoundError(TEMPORAL_MANIFEST)
    return d,c,x

def build_support_policy(d,c,x):
    return attach({
        "support_policy_id":"aod_00o8_C6_recurrence_support_policy_v3",
        "primitive_support_id":"00o8_C6_1_2_6",
        "fractal_octave_coordinate":"00_(8)",
        "detected_support_core":d["detected_support_core"],
        "declared_scope_L":d["declared_scope_L"],
        "outer_enclosure_id":"C6",
        "inverse_solver_p_min":"1",
        "inverse_solver_q_min":"2",
        "inverse_solver_q_max":"4",
        "inverse_solver_domain_basis":"Q4_directional_support",
        "local_Q4_edge_slots":"4",
        "scope_conditioned_form":d["scope_conditioned_form"],
        "source_recurrence_certificate_id":c["recurrence_certificate_id"],
        "source_recurrence_certificate_sha256":c["recurrence_certificate_sha256"],
        "recurrence_family_status":x["recurrence_specificity_status"],
        "connected_transition_count":c["transition_count"],
        "executed_bip_count":c["primitive_recurrence_bip_count"],
        "bip_semantics":"admitted_executed_directed_beat_token",
        "trace_count_temporal_status":"execution_structure_not_temporal_magnitude",
        "monon_semantics":"primitive_completed_cycle_class",
        "minimal_direct_witness_outbound_bip_count":"1",
        "minimal_direct_witness_inbound_bip_count":"1",
        "minimal_direct_witness_total_bip_count":"2",
        "minimal_direct_witness_status":"witness_only_not_duration",
        "monon_to_bip_conversion_status":"not_declared",
        "C6_role":"six_slot_support_and_shared_recurrence_fixture",
        "temporal_measurement_protocol_id":"aod_relational_temporal_measurement_packet_v1",
        "universal_application_status":"consequent_support_family_cross_packet_binding_passed_local_DEC_pending_hydrogen_occurrence_pending",
        "cs_lane_role":"historical_adapter_optional_downstream_reference",
        "SI_realization_status":"inactive_optional_downstream",
        "target_value_read_status":"not_read",
        "empirical_score_status":"not_computed",
    },"support_policy_sha256")

def build_forms():
    specs=[
      (0,"1:2:6","primitive_shared_recurrence_and_support_fixture","certified_by_M2_shared_recurrence_family","carried_forward_retyped"),
      (1,"3:3:6","consequent_core_facing_six_slot_form","passed_r06_3_1_canonical_serialization_closed_semantics_and_support_family_consistency","carried_forward_source_row_verified_no_recompute"),
      (2,"3:4:6","consequent_extension_six_slot_form","passed_r06_3_1_canonical_serialization_closed_semantics_and_support_family_consistency","carried_forward_source_row_verified_no_recompute"),
    ]
    return [attach({"form_order":i,"primitive_support_id":"00o8_C6_1_2_6","fractal_octave_coordinate":"00_(8)","route_form":f,"outer_support_length":"6","support_role":role,"C6_compatibility_status":status,"temporal_unit_status":"not_defined_by_support_form","monon_conversion_status":"not_declared","scientific_row_status":s},"form_registry_row_sha256") for i,f,role,status,s in specs]

def build_hydrogen():
    specs=[
      (0,"H1_00o8",1,1,0,0,"first_element_relational_flow_verification","materialized_connected_local_Q4_direct_return_occurrence"),
      (1,"H2_00o8",1,2,1,1,"isotope_extension","planned_not_materialized"),
      (2,"H3_00o8",1,3,2,2,"isotope_extension","planned_not_materialized"),
    ]
    return [attach({"occurrence_order":i,"occurrence_id":oid,"element_symbol":"H","atomic_number":z,"mass_number":a,"neutron_count":n,"core_form":"3:3:6","extension_3_4_6_count":ext,"outer_form":"1:2:6","primitive_support_id":"00o8_C6_1_2_6","occurrence_role":role,"relational_temporal_protocol_id":"aod_relational_temporal_measurement_packet_v1","generator_status":status,"target_value_read_status":"not_read"},"hydrogen_occurrence_plan_row_sha256") for i,oid,z,a,n,ext,role,status in specs]

def build_balmer():
    vals=[]
    for name,n in (("H_alpha",3),("H_beta",4),("H_gamma",5),("H_delta",6)):
        vals.append((name,n,Fraction(1,4)-Fraction(1,n*n)))
    l=math.lcm(*(f.denominator for _,_,f in vals)); freq=[f.numerator*(l//f.denominator) for _,_,f in vals]; g=math.gcd(*freq); freq=[x//g for x in freq]
    inv=[1/f for _,_,f in vals]; l2=math.lcm(*(f.denominator for f in inv)); per=[f.numerator*(l2//f.denominator) for f in inv]; g2=math.gcd(*per); per=[x//g2 for x in per]
    if freq != [500,675,756,800] or per != [1512,1120,1000,945]: raise ValueError((freq,per))
    rows=[]
    for i,((name,n,f),fi,pi) in enumerate(zip(vals,freq,per)):
        rows.append(attach({"line_order":i,"line_id":name,"transition":f"{n}->2","n_upper":n,"ideal_frequency_factor_num":f.numerator,"ideal_frequency_factor_den":f.denominator,"frequency_ratio_integer":fi,"period_ratio_integer":pi,"native_phase_lock_packet_status":"not_materialized","ratio_card_role":"downstream_dimensionless_relational_comparison","native_generator_access_status":"forbidden","SI_unit_status":"not_required","observed_line_packet_status":"separate_downstream_target_lane","target_join_status":"closed_pending_native_phase_lock_freeze","decimal_target_use_status":"forbidden"},"balmer_ratio_card_row_sha256"))
    return rows

def build_atlas():
    fields=[
      ("element_Z","integer","yes","element identity"),("element_symbol","string","yes","registry symbol after identity freeze"),("isotope_A","integer","yes_for_isotope_row","mass-number scope"),("neutron_count","integer","yes_for_isotope_row","A_minus_Z"),("charge_state","integer","yes","declared charge scope"),("state_id","string","yes","native state packet"),("transition_channel_id","string","yes_for_transition_row","native transition occurrence"),("primitive_support_id","string","yes","shared C6 support/recurrence fixture"),("subject_sadar_packet_id","string","yes_for_transition_row","element transition flow"),("drive_sadar_packet_id","string","yes_for_transition_row","declared sheddic-drive flow"),("phase_lock_packet_id","string","yes_for_transition_row","primitive relational temporal lock"),("native_period_ratio_num","integer","yes_when_compared","exact ratio numerator"),("native_period_ratio_den","positive_integer","yes_when_compared","exact ratio denominator"),("private_bip_to_second_coefficient_status","enum","yes","forbidden"),("native_packet_sha256","sha256","yes","native packet lock")]
    return [attach({"field_order":i,"field":f,"type":t,"required":req,"role":role},"atlas_schema_row_sha256") for i,(f,t,req,role) in enumerate(fields)]

def build_migration():
    rows=[
      (0,"universal_monon_six_bip_equivalence","remove_type_error","withdrawn","monon_cycle_class_with_two_bip_minimal_direct_witness","no_scientific_row_recompute"),
      (1,"six_bip_recurrence_as_time_calibration","retype","withdrawn","six_executed_transition_recurrence_fixture","no_scientific_row_recompute"),
      (2,"C6_native_temporal_calibration","retype","withdrawn","C6_support_and_shared_recurrence_fixture","no_scientific_row_recompute"),
      (3,"Cs_active_calibration_path","retain_historical_adapter","inactive","optional_downstream_reference_fixture","no_scientific_row_recompute"),
      (4,"radiation_channel_terminology","replace_native_term","withdrawn","sheddic_exchange_channel","semantic_only"),
    ]
    return [attach({"migration_order":i,"old_semantic_id":old,"action":action,"old_status":status,"new_semantic_id":new,"scientific_row_change":chg},"migration_row_sha256") for i,old,action,status,new,chg in rows]

MILESTONES=[
 ("R0",0,"v40.03r05.2","Relational temporal semantics and C6 roadmap repair","carried_forward_complete","remove monon/bip type error; freeze relational SADAR time protocol","no target or score"),
 ("R1",1,"v40.03r06.3.1","Canonical serialization and closed-semantics binding","carried_forward_complete","3:3:6 and 3:4:6 globally closed canonical support-family/accessor packets with physical-order and semantic-status binding","local D.E.C. remains pending; primitive support unchanged"),
 ("R2",2,"v40.03r07","Hydrogen-1 native occurrence gate","current_complete","target-blind H-1 occurrence","no Balmer target input"),
 ("R3",3,"v40.03r08","Hydrogen native transition and SADAR lock atlas","next","native transition flows and phase locks","no SI units"),
 ("R4",4,"v40.03r09","Exact Balmer relational-ratio audit","planned","dimensionless exact ratio audit","native packets frozen first"),
 ("R5",5,"v40.03r10","Hydrogen isotope extension","planned","H-2/H-3 occurrences","same relational protocol"),
 ("R6",6,"v40.03r11","118-element relational transition atlas","planned","element transition flow schemas","no private conversion"),
 ("R7",7,"v40.03r12","Hyperfine C6 compatibility and divisibility audit","planned","post-freeze compatibility audit","mismatch allowed"),
 ("R8",8,"v40.03r13","Native rest-cycle relational atlas","planned","rest and transition packets separate","target-free"),
 ("R9",9,"v40.03r14","Optional metrological reference cards","planned","reference flow to SI report cards","native flows unchanged"),
 ("R10",10,"v40.03r15","Circle relational geometry audit","planned","R_CA exact audit","zero not imposed"),
 ("R11",11,"v40.03r16","Tau survival/hazard and migration audit","planned","stochastic survival flow","no fixed Tau bip duration"),
 ("R12",12,"v40.03r17","Manual-I consolidation","planned","protocol audit complete","empirical mismatch allowed"),
 ("R13",13,"v40.03r18","Manual-II reassessment","deferred","synchronized reassessment","manual-2 frozen until then"),
]

def write_outputs(d,c,x):
    C6.mkdir(parents=True,exist_ok=True); ROADMAP.mkdir(parents=True,exist_ok=True)
    obsolete=[C6/"c6_native_calibration_policy.csv",C6/"cs_centered_to_c6_rebase_migration.csv"]
    for p in obsolete:
        if p.exists(): p.unlink()
    policy=build_support_policy(d,c,x); forms=build_forms(); hyd=build_hydrogen(); bal=build_balmer(); atlas=build_atlas(); mig=build_migration()
    write_csv(C6/"c6_recurrence_support_policy.csv",list(policy),[policy])
    write_csv(C6/"primitive_and_consequent_form_registry.csv",list(forms[0]),forms)
    write_csv(C6/"hydrogen_occurrence_plan.csv",list(hyd[0]),hyd)
    write_csv(C6/"balmer_exact_ratio_card.csv",list(bal[0]),bal)
    write_csv(C6/"element_118_atlas_schema.csv",list(atlas[0]),atlas)
    write_csv(C6/"r05_1_to_r05_2_temporal_semantics_migration.csv",list(mig[0]),mig)
    files=[]
    for p in sorted(C6.glob("*.csv")): files.append({"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p.read_bytes())})
    manifest={"manifest_id":"aod_C6_recurrence_support_and_relational_temporal_cards_v2","version_scope":VERSION,"support_policy_id":policy["support_policy_id"],"primitive_support_id":"00o8_C6_1_2_6","monon_to_bip_conversion_status":"not_declared","relational_temporal_protocol_id":"aod_relational_temporal_measurement_packet_v1","target_join_status":"closed","empirical_score_status":"not_computed","files":files}
    (C6/"c6_hydrogen_first_plan_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    plan=[]
    for mid,seq,rel,title,status,inputs,exitc in MILESTONES:
        plan.append(attach({"milestone_id":mid,"sequence":seq,"target_release":rel,"title":title,"status":status,"inputs_or_scope":inputs,"exit_condition":exitc,"dependency_graph_role":"authoritative_execution_order"},"milestone_row_sha256"))
    write_csv(ROADMAP/"manual1_c6_hydrogen_first_milestone_plan.csv",list(plan[0]),plan)
    deps=[]
    for mid,seq,*_ in MILESTONES:
        dep="" if seq==0 else ("R0" if seq==1 else f"R{seq-1}")
        deps.append(attach({"milestone_id":mid,"depends_on":dep,"dependency_status":"satisfied" if seq <= 2 else "pending","dependency_graph_role":"authoritative_execution_order"},"dependency_row_sha256"))
    write_csv(ROADMAP/"manual1_c6_hydrogen_first_gate_dependencies.csv",list(deps[0]),deps)
    matrix=[]
    for mid,seq,rel,title,status,*_ in MILESTONES:
        matrix.append(attach({"milestone_id":mid,"sequence":seq,"target_release":rel,"manual_appendix":"E/G" if seq==0 else ("H" if seq==1 else ("I" if seq==2 else "E")),"data_root":"manual/data/temporal_relational" if seq==0 else ("manual/data/hydrogen" if seq==2 else "manual/data/c6"),"script_root":"manual/scripts","test_root":"tests","shared_status":"frozen","manual2_status":"frozen_until_R13","status":status},"file_change_row_sha256"))
    write_csv(ROADMAP/"manual1_c6_hydrogen_first_file_change_matrix.csv",list(matrix[0]),matrix)
    supersession=attach({"registry_id":"manual1_r05_2_temporal_semantics_supersession","superseded_plan":"universal_C6_native_temporal_calibration_r05_1","current_plan":"relational_SADAR_time_and_hydrogen_first_r07","scientific_row_recomputation":"none","status":"superseded_for_future_execution"},"supersession_row_sha256")
    write_csv(ROADMAP/"manual1_roadmap_supersession_registry.csv",list(supersession),[supersession])
    change_plan = """# Manual I relational temporal semantics and Hydrogen-first roadmap\n\nThe current package carries forward the repaired monon/bip semantics and certifies the consequent 3:3:6 and 3:4:6 forms against the shared C6 outer-support packet.\n\n```text\nscoped occurrence -> D.E.C. execution -> duon current -> RD/RCD -> duonic pressure -> SADAR flow -> primitive relational phase lock -> temporal report\n```\n\nA bip is an admitted executed directed beat token. A trace count is execution structure. A monon is a completed cycle class whose shortest direct witness contains one outbound and one inbound bip; the witness count is not a universal duration. Time measurement is the exact primitive lock between subject and reference SADAR flow packets. Native exchange terminology is sheddic only.\n\nThe 3:3:6 and 3:4:6 compatibility gate is complete at support/enclosure and exact-accessor level. The H-1 gate now materializes one identity-bound connected local Q4 direct-return occurrence with target values absent. RD/RCD, pressure, SADAR flow, phase lock, and the exact Balmer ratio card remain downstream.\n"""
    (ROADMAP/"manual1_c6_hydrogen_first_change_plan.md").write_text(change_plan,encoding="utf-8")
    out_files=[C6/"c6_hydrogen_first_plan_manifest.json",ROADMAP/"manual1_c6_hydrogen_first_milestone_plan.csv",ROADMAP/"manual1_c6_hydrogen_first_gate_dependencies.csv",ROADMAP/"manual1_c6_hydrogen_first_file_change_matrix.csv",ROADMAP/"manual1_roadmap_supersession_registry.csv",ROADMAP/"manual1_c6_hydrogen_first_change_plan.md"]
    pmanifest={"manifest_id":"manual1_relational_temporal_hydrogen_first_roadmap_v4","version_scope":VERSION,"release_class":"target_blind_H1_native_occurrence_gate_no_target_or_score","current_state":{"monon_to_bip_conversion_status":"not_declared","C6_role":"support_and_shared_recurrence_fixture","consequent_form_compatibility":"passed_global_packet_set_physical_serialization_pre_map_identity_closed_semantics_support_family_accessor_scope","H1_native_occurrence":"materialized_connected_local_Q4_direct_return","temporal_measurement":"primitive_subject_reference_SADAR_lock","sheddic_terminology":"native_sheddic_only","cs_active_calibration_role":"none","target_value_read_status":"not_read"},"files":[{"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p.read_bytes())} for p in out_files]}
    (ROADMAP/"manual1_c6_hydrogen_first_plan_manifest.json").write_text(json.dumps(pmanifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main()->int:
    d,c,x=verify_source(); write_outputs(d,c,x); return 0
if __name__=="__main__": raise SystemExit(main())
