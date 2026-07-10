#!/usr/bin/env python3
"""Build Manual II native causal-duration and SI projection protocol schemas."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'manual-2'/'data'/'temporal'
OUT.mkdir(parents=True,exist_ok=True)

def write_csv(name, fields, rows):
    p=OUT/name
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    return p

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def row_hash(row, omit):
    d={k:v for k,v in row.items() if k!=omit}
    return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()

native_fields=['field_name','exact_type','required','role','current_state']
native_rows=[
 {'field_name':'temporal_packet_id','exact_type':'identifier','required':'yes','role':'stable native temporal packet identifier','current_state':'schema_declared'},
 {'field_name':'motif_family','exact_type':'identifier','required':'yes','role':'recurring motif-family identifier','current_state':'schema_declared'},
 {'field_name':'scoped_occurrence_id','exact_type':'identifier','required':'yes','role':'boundary/window-qualified occurrence identifier','current_state':'schema_declared'},
 {'field_name':'fractal_coord','exact_type':'identifier','required':'yes','role':'declared fractal coordinate','current_state':'schema_declared'},
 {'field_name':'boundary_id','exact_type':'identifier','required':'yes','role':'declared boundary package','current_state':'schema_declared'},
 {'field_name':'window_id','exact_type':'identifier','required':'yes','role':'declared finite temporal window','current_state':'schema_declared'},
 {'field_name':'scale_lane','exact_type':'enum','required':'yes','role':'elementary molecular collision field or protein lane','current_state':'schema_declared'},
 {'field_name':'dec_trace_id','exact_type':'identifier','required':'yes','role':'read-only D.E.C. trace pointer','current_state':'schema_declared'},
 {'field_name':'event_order_sha256','exact_type':'sha256_hex','required':'yes','role':'hash of exact event-order relation','current_state':'schema_declared'},
 {'field_name':'native_duration_num','exact_type':'integer_nonnegative','required':'yes','role':'native rational bip-duration numerator','current_state':'not_materialized'},
 {'field_name':'native_duration_den','exact_type':'integer_positive','required':'yes','role':'native rational bip-duration denominator','current_state':'not_materialized'},
 {'field_name':'native_duration_unit','exact_type':'enum','required':'yes','role':'must be bip','current_state':'fixed_bip'},
 {'field_name':'native_biz_num','exact_type':'integer','required':'conditional','role':'exact rational biz-rate numerator','current_state':'not_materialized'},
 {'field_name':'native_biz_den','exact_type':'integer_positive','required':'conditional','role':'exact rational biz-rate denominator','current_state':'not_materialized'},
 {'field_name':'curling_curls_incidence_id','exact_type':'identifier','required':'conditional','role':'detected AOD curling-curls incidence pointer','current_state':'not_materialized'},
 {'field_name':'reclosure_relation_id','exact_type':'identifier','required':'conditional','role':'detected reclosure relation pointer','current_state':'not_materialized'},
 {'field_name':'native_residual_packet_id','exact_type':'identifier','required':'yes','role':'native exact residual packet pointer','current_state':'schema_declared'},
 {'field_name':'native_packet_sha256','exact_type':'sha256_hex','required':'yes','role':'hash of complete native temporal packet','current_state':'not_materialized'},
]
files={}
files['native_packet_schema']=write_csv('aod_native_causal_duration_packet_schema.csv',native_fields,native_rows)

cs_fields=['card_id','card_role','native_duration_domain','native_bip_basis','cesium_period_count_rule','map_coefficient_num','map_coefficient_den','frame_policy','proper_time_policy','si_frequency_hz_exact','si_time_report_rule','map_state','target_value_read_status','map_freeze_sha256']
cs_rows=[
 {'card_id':'cs133_elementary_occurrence_card','card_role':'AOD_elementary_occurrence','native_duration_domain':'elementary_occurrence_schema','native_bip_basis':'declared_by_elementary_packet','cesium_period_count_rule':'not_applicable','map_coefficient_num':'','map_coefficient_den':'','frame_policy':'AOD_native_scope_only','proper_time_policy':'not_applicable','si_frequency_hz_exact':'','si_time_report_rule':'none','map_state':'schema_reference_only','target_value_read_status':'not_read','map_freeze_sha256':''},
 {'card_id':'cs133_si_time_reference_card','card_role':'external_metrological_anchor','native_duration_domain':'SI_reference','native_bip_basis':'not_applicable','cesium_period_count_rule':'fixed_defining_frequency','map_coefficient_num':'','map_coefficient_den':'','frame_policy':'SI_reference_card','proper_time_policy':'realization_and_frame_policy_required_for_clock_comparison','si_frequency_hz_exact':'9192631770','si_time_report_rule':'t_SI=N_Cs/9192631770_s','map_state':'reference_card_active','target_value_read_status':'not_read','map_freeze_sha256':''},
 {'card_id':'aod_cesium_time_projection_linear_contract_v1','card_role':'AOD_to_SI_projection_contract','native_duration_domain':'rational_bip_duration','native_bip_basis':'must_be_declared_before_instantiation','cesium_period_count_rule':'N_Cs=kappa_Cs*tau_caus','map_coefficient_num':'','map_coefficient_den':'','frame_policy':'must_be_frozen_before_instantiation','proper_time_policy':'must_be_frozen_before_clock_target_join','si_frequency_hz_exact':'9192631770','si_time_report_rule':'t_SI=N_Cs/9192631770_s','map_state':'contract_declared_not_instantiated','target_value_read_status':'not_read','map_freeze_sha256':''},
]
for row in cs_rows: row['map_freeze_sha256']=row_hash(row,'map_freeze_sha256')
files['cesium_projection']=write_csv('aod_cesium_time_projection_registry.csv',cs_fields,cs_rows)

si_fields=['registry_row_id','row_type','symbol','exact_value_expression','exact_numerator','exact_denominator','si_unit','projection_rule_id','projection_rule','domain_requirement','operator_state','source_id']
si_rows=[
 {'registry_row_id':'si_const_delta_nu_Cs','row_type':'defining_constant','symbol':'Delta_nu_Cs','exact_value_expression':'9192631770','exact_numerator':'9192631770','exact_denominator':'1','si_unit':'Hz','projection_rule_id':'','projection_rule':'','domain_requirement':'SI defining constant','operator_state':'exact_reference_active','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_const_c','row_type':'defining_constant','symbol':'c','exact_value_expression':'299792458','exact_numerator':'299792458','exact_denominator':'1','si_unit':'m s^-1','projection_rule_id':'','projection_rule':'','domain_requirement':'SI defining constant','operator_state':'exact_reference_active','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_const_h','row_type':'defining_constant','symbol':'h','exact_value_expression':'6.62607015e-34','exact_numerator':'662607015','exact_denominator':'1000000000000000000000000000000000000000000','si_unit':'J s','projection_rule_id':'','projection_rule':'','domain_requirement':'SI defining constant','operator_state':'exact_reference_active','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_const_N_A','row_type':'defining_constant','symbol':'N_A','exact_value_expression':'6.02214076e23','exact_numerator':'602214076000000000000000','exact_denominator':'1','si_unit':'mol^-1','projection_rule_id':'','projection_rule':'','domain_requirement':'SI defining constant','operator_state':'exact_reference_active','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_map_time_from_cesium_periods','row_type':'projection_rule','symbol':'t_SI','exact_value_expression':'N_Cs/9192631770','exact_numerator':'','exact_denominator':'','si_unit':'s','projection_rule_id':'time_from_cesium_periods','projection_rule':'t_SI=N_Cs/Delta_nu_Cs','domain_requirement':'frozen N_Cs period-count map and clock/frame policy','operator_state':'contract_declared_not_instantiated','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_map_light_path','row_type':'projection_rule','symbol':'d_SI','exact_value_expression':'c*t_SI','exact_numerator':'','exact_denominator':'','si_unit':'m','projection_rule_id':'light_path_from_time','projection_rule':'d_SI=c*t_SI','domain_requirement':'declared null or light propagation path','operator_state':'contract_declared_not_instantiated','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_map_frequency','row_type':'projection_rule','symbol':'nu_SI','exact_value_expression':'n_cycle/t_SI','exact_numerator':'','exact_denominator':'','si_unit':'Hz','projection_rule_id':'frequency_from_cycles','projection_rule':'nu_SI=n_cycle/t_SI','domain_requirement':'declared recurring cycle and nonzero time','operator_state':'contract_declared_not_instantiated','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_map_photon_energy','row_type':'projection_rule','symbol':'E_SI','exact_value_expression':'h*nu_SI','exact_numerator':'','exact_denominator':'','si_unit':'J','projection_rule_id':'photon_energy_from_frequency','projection_rule':'E_SI=h*nu_SI','domain_requirement':'declared photon-frequency lane','operator_state':'contract_declared_not_instantiated','source_id':'BIPM_defining_constants'},
 {'registry_row_id':'si_map_amount','row_type':'projection_rule','symbol':'n_mol','exact_value_expression':'N/N_A','exact_numerator':'','exact_denominator':'','si_unit':'mol','projection_rule_id':'amount_from_entity_count','projection_rule':'n_mol=N/N_A','domain_requirement':'specified exact entity count and entity type','operator_state':'contract_declared_not_instantiated','source_id':'BIPM_defining_constants'},
]
files['si_registry']=write_csv('aod_si_defining_constant_projection_registry.csv',si_fields,si_rows)

il_fields=['projection_id','domain','codomain','exact_execution_status','injectivity_status','discarded_native_distinction','inverse_domain_status','information_loss_status','E_proj_status']
il_rows=[
 {'projection_id':'native_packet_to_scalar_tau_caus','domain':'ordered_native_temporal_packet','codomain':'rational_bip_duration','exact_execution_status':'contract_declared','injectivity_status':'noninjective','discarded_native_distinction':'event_order_and_motif_path_not_recoverable_from_scalar_duration_alone','inverse_domain_status':'no_inverse_declared','information_loss_status':'declared_in_I_Pi','E_proj_status':'not_a_projection_defect'},
 {'projection_id':'tau_caus_to_cesium_period_count','domain':'rational_bip_duration','codomain':'rational_cesium_period_count','exact_execution_status':'not_instantiated','injectivity_status':'conditional_on_nonzero_kappa','discarded_native_distinction':'none_beyond_prior_scalarization','inverse_domain_status':'blocked_until_kappa_instantiated','information_loss_status':'declared','E_proj_status':'blocked'},
 {'projection_id':'cesium_period_count_to_SI_time','domain':'rational_cesium_period_count','codomain':'rational_SI_seconds','exact_execution_status':'exact_reference_map','injectivity_status':'injective','discarded_native_distinction':'none','inverse_domain_status':'exact_inverse_by_multiplication','information_loss_status':'none','E_proj_status':'none'},
 {'projection_id':'display_rounding','domain':'exact_metric_report','codomain':'decimal_display','exact_execution_status':'optional_renderer','injectivity_status':'noninjective','discarded_native_distinction':'sub-display-resolution digits','inverse_domain_status':'none','information_loss_status':'renderer_metadata','E_proj_status':'not_used_use_E_rep'},
]
files['information_loss']=write_csv('aod_temporal_projection_information_loss_registry.csv',il_fields,il_rows)

clock_fields=['field_name','exact_type','required','role','freeze_stage']
clock_rows=[
 {'field_name':'clock_target_packet_id','exact_type':'identifier','required':'yes','role':'stable time-target packet identifier','freeze_stage':'observation_branch'},
 {'field_name':'source_payload_sha256','exact_type':'sha256_hex','required':'yes','role':'clock or timing payload byte identity','freeze_stage':'observation_branch'},
 {'field_name':'clock_lineage_id','exact_type':'identifier','required':'yes','role':'clock realization and calibration lineage','freeze_stage':'observation_branch'},
 {'field_name':'t_obs_num','exact_type':'integer','required':'yes','role':'observed rational time numerator','freeze_stage':'observation_branch'},
 {'field_name':'t_obs_den','exact_type':'integer_positive','required':'yes','role':'observed rational time denominator','freeze_stage':'observation_branch'},
 {'field_name':'uncertainty_lower_num','exact_type':'integer','required':'conditional','role':'lower uncertainty-bound numerator','freeze_stage':'observation_branch'},
 {'field_name':'uncertainty_lower_den','exact_type':'integer_positive','required':'conditional','role':'lower uncertainty-bound denominator','freeze_stage':'observation_branch'},
 {'field_name':'uncertainty_upper_num','exact_type':'integer','required':'conditional','role':'upper uncertainty-bound numerator','freeze_stage':'observation_branch'},
 {'field_name':'uncertainty_upper_den','exact_type':'integer_positive','required':'conditional','role':'upper uncertainty-bound denominator','freeze_stage':'observation_branch'},
 {'field_name':'proper_time_frame','exact_type':'identifier','required':'yes','role':'declared proper-time frame or realization frame','freeze_stage':'observation_branch'},
 {'field_name':'synchronization_policy_id','exact_type':'identifier','required':'yes','role':'clock synchronization policy','freeze_stage':'observation_branch'},
 {'field_name':'relativistic_correction_policy_id','exact_type':'identifier','required':'yes','role':'relativistic correction policy','freeze_stage':'observation_branch'},
 {'field_name':'quality_state','exact_type':'enum','required':'yes','role':'supported ambiguous excluded unavailable','freeze_stage':'observation_branch'},
 {'field_name':'prediction_read_status','exact_type':'enum','required':'yes','role':'must be not_read at observation freeze','freeze_stage':'observation_branch'},
 {'field_name':'clock_packet_sha256','exact_type':'sha256_hex','required':'yes','role':'hash of frozen clock-lineage packet','freeze_stage':'observation_branch'},
]
files['clock_schema']=write_csv('aod_target_clock_lineage_schema.csv',clock_fields,clock_rows)

tr_fields=['component_id','exact_type','stage','meaning','correction_target']
tr_rows=[
 {'component_id':'E_calc','exact_type':'integer_or_hash_audit','stage':'native','meaning':'native D.E.C. arithmetic incidence or hash defect','correction_target':'implementation'},
 {'component_id':'Delta_oct','exact_type':'declared_refinement_difference','stage':'native','meaning':'lawful exact change under a frozen octave refinement relation','correction_target':'none_retained_as_comparison_coordinate'},
 {'component_id':'E_oct','exact_type':'declared_refinement_condition_failure','stage':'native','meaning':'failure of a declared octave relation or condition','correction_target':'octave_relation_or_scope'},
 {'component_id':'E_proj','exact_type':'projection_contract_audit','stage':'projection','meaning':'projection domain basis denominator frame or execution defect','correction_target':'projection_operator'},
 {'component_id':'I_Pi','exact_type':'projection_information_loss_card','stage':'projection','meaning':'declared noninjectivity or discarded native distinctions','correction_target':'metadata_not_arithmetic'},
 {'component_id':'U_obs','exact_type':'exact_interval_set_or_mask','stage':'observation','meaning':'measurement reconstruction normalization and support uncertainty','correction_target':'observation_branch'},
 {'component_id':'E_lineage','exact_type':'hash_relation_or_policy_audit','stage':'observation','meaning':'payload clock synchronization reconstruction or provenance defect','correction_target':'observation_lineage'},
 {'component_id':'E_scope','exact_type':'set_difference_or_relation_status','stage':'join','meaning':'frame boundary pair alignment or window mismatch','correction_target':'join_scope'},
 {'component_id':'E_emp','exact_type':'rational_interval_or_set_distance','stage':'post_join','meaning':'supported prediction versus target disagreement','correction_target':'hypothesis_only_after_other_layers_pass'},
 {'component_id':'E_rep','exact_type':'rational_rendering_difference','stage':'render','meaning':'display unit or rounding difference','correction_target':'renderer'},
]
files['typed_residual']=write_csv('aod_temporal_typed_residual_registry.csv',tr_fields,tr_rows)

# Common schema helper for lane packet files
lane_fields=['field_name','exact_type','required','role','current_state']
element_rows=[
 {'field_name':'element_native_row_id','exact_type':'identifier','required':'yes','role':'stable elementary native packet row','current_state':'schema_declared'},
 {'field_name':'motif_family','exact_type':'identifier','required':'yes','role':'recurring motif-family identifier','current_state':'schema_declared'},
 {'field_name':'route_form','exact_type':'identifier','required':'yes','role':'declared elementary route form','current_state':'schema_declared'},
 {'field_name':'scoped_occurrence_id','exact_type':'identifier','required':'yes','role':'occurrence card','current_state':'schema_declared'},
 {'field_name':'fractal_coord','exact_type':'identifier','required':'yes','role':'fractal coordinate','current_state':'schema_declared'},
 {'field_name':'boundary_id','exact_type':'identifier','required':'yes','role':'boundary package','current_state':'schema_declared'},
 {'field_name':'window_id','exact_type':'identifier','required':'yes','role':'temporal window','current_state':'schema_declared'},
 {'field_name':'gamma_group','exact_type':'identifier','required':'conditional','role':'declared group/support identifier','current_state':'schema_declared'},
 {'field_name':'support_enclosure','exact_type':'identifier','required':'conditional','role':'declared support enclosure','current_state':'schema_declared'},
 {'field_name':'dec_trace_id','exact_type':'identifier','required':'yes','role':'read-only trace pointer','current_state':'schema_declared'},
 {'field_name':'event_order_sha256','exact_type':'sha256_hex','required':'yes','role':'event-order hash','current_state':'not_materialized'},
 {'field_name':'native_bip_num','exact_type':'integer_nonnegative','required':'yes','role':'native bip numerator','current_state':'not_materialized'},
 {'field_name':'native_bip_den','exact_type':'integer_positive','required':'yes','role':'native bip denominator','current_state':'not_materialized'},
 {'field_name':'native_biz_num','exact_type':'integer','required':'conditional','role':'native biz numerator','current_state':'not_materialized'},
 {'field_name':'native_biz_den','exact_type':'integer_positive','required':'conditional','role':'native biz denominator','current_state':'not_materialized'},
 {'field_name':'RCD','exact_type':'relation_packet','required':'conditional','role':'reflection-duration coupling','current_state':'not_materialized'},
 {'field_name':'rhoD_omega','exact_type':'rational','required':'conditional','role':'window participation','current_state':'not_materialized'},
 {'field_name':'PD','exact_type':'integer_or_rational','required':'conditional','role':'declared pressure/current packet','current_state':'not_materialized'},
 {'field_name':'closure_residual','exact_type':'integer_or_rational','required':'yes','role':'native closure audit','current_state':'not_materialized'},
 {'field_name':'shedding_route','exact_type':'identifier','required':'conditional','role':'native sheddic route','current_state':'not_materialized'},
 {'field_name':'native_packet_sha256','exact_type':'sha256_hex','required':'yes','role':'native packet hash','current_state':'not_materialized'},
]
files['elementary_schema']=write_csv('aod_elementary_temporal_packet_schema.csv',lane_fields,element_rows)

mol_rows=[
 {'field_name':'molecular_native_row_id','exact_type':'identifier','required':'yes','role':'stable molecular native packet row','current_state':'schema_declared'},
 {'field_name':'motif_family','exact_type':'identifier','required':'yes','role':'recurring motif family','current_state':'schema_declared'},
 {'field_name':'scoped_occurrence_id','exact_type':'identifier','required':'yes','role':'molecular scoped occurrence','current_state':'schema_declared'},
 {'field_name':'fractal_coord','exact_type':'identifier','required':'yes','role':'fractal coordinate','current_state':'schema_declared'},
 {'field_name':'boundary_id','exact_type':'identifier','required':'yes','role':'boundary package','current_state':'schema_declared'},
 {'field_name':'window_id','exact_type':'identifier','required':'yes','role':'temporal window','current_state':'schema_declared'},
 {'field_name':'reactant_formula_packet','exact_type':'formula_packet','required':'yes','role':'exact input formulas','current_state':'carried_forward'},
 {'field_name':'route_unit_packet','exact_type':'formula_packet','required':'yes','role':'exact route/shedding unit','current_state':'carried_forward'},
 {'field_name':'product_formula_packet','exact_type':'formula_packet','required':'yes','role':'exact output formula','current_state':'carried_forward'},
 {'field_name':'CHONPS_residual','exact_type':'integer_vector','required':'yes','role':'exact formula residual','current_state':'carried_forward'},
 {'field_name':'dec_trace_id','exact_type':'identifier','required':'yes','role':'read-only trace','current_state':'carried_forward'},
 {'field_name':'event_order_sha256','exact_type':'sha256_hex','required':'yes','role':'event-order hash','current_state':'not_materialized'},
 {'field_name':'native_duration_num','exact_type':'integer_nonnegative','required':'yes','role':'native bip numerator','current_state':'not_materialized'},
 {'field_name':'native_duration_den','exact_type':'integer_positive','required':'yes','role':'native bip denominator','current_state':'not_materialized'},
 {'field_name':'RCD','exact_type':'relation_packet','required':'conditional','role':'reflection-duration coupling','current_state':'not_materialized'},
 {'field_name':'rhoD_omega','exact_type':'rational','required':'conditional','role':'window participation','current_state':'not_materialized'},
 {'field_name':'PD','exact_type':'integer_or_rational','required':'conditional','role':'pressure/current packet','current_state':'not_materialized'},
 {'field_name':'SADAR_context_id','exact_type':'identifier','required':'yes','role':'SADAR context pointer','current_state':'carried_forward'},
 {'field_name':'shedding_route','exact_type':'identifier','required':'conditional','role':'native route','current_state':'carried_forward'},
 {'field_name':'native_packet_sha256','exact_type':'sha256_hex','required':'yes','role':'native temporal packet hash','current_state':'not_materialized'},
]
files['molecular_schema']=write_csv('aod_molecular_temporal_packet_schema.csv',lane_fields,mol_rows)

protein_rows=[
 {'field_name':'protein_temporal_packet_id','exact_type':'identifier','required':'yes','role':'stable protein temporal packet row','current_state':'schema_declared'},
 {'field_name':'motif_family','exact_type':'identifier','required':'yes','role':'recurring motif family','current_state':'schema_declared'},
 {'field_name':'scoped_occurrence_id','exact_type':'identifier','required':'yes','role':'protein scoped occurrence','current_state':'schema_declared'},
 {'field_name':'fractal_coord','exact_type':'identifier','required':'yes','role':'fractal coordinate','current_state':'schema_declared'},
 {'field_name':'boundary_id','exact_type':'identifier','required':'yes','role':'boundary package','current_state':'schema_declared'},
 {'field_name':'window_id','exact_type':'identifier','required':'yes','role':'temporal window','current_state':'schema_declared'},
 {'field_name':'dec_trace_id','exact_type':'identifier','required':'yes','role':'read-only trace pointer','current_state':'carried_forward'},
 {'field_name':'event_order_sha256','exact_type':'sha256_hex','required':'yes','role':'native event-order hash','current_state':'not_materialized'},
 {'field_name':'curl_incidence_id','exact_type':'identifier','required':'conditional','role':'curl incidence pointer','current_state':'not_materialized'},
 {'field_name':'curling_curls_incidence_id','exact_type':'identifier','required':'conditional','role':'curling-curls incidence pointer','current_state':'not_materialized'},
 {'field_name':'reclosure_relation_id','exact_type':'identifier','required':'yes','role':'frozen reclosure relation','current_state':'carried_forward_fixture'},
 {'field_name':'Q4_address_packet_id','exact_type':'identifier','required':'conditional','role':'relational tesseract support packet','current_state':'not_materialized'},
 {'field_name':'cell_count_packet_id','exact_type':'identifier','required':'conditional','role':'exact cell counts','current_state':'not_materialized'},
 {'field_name':'native_bip_num','exact_type':'integer_nonnegative','required':'yes','role':'native bip numerator','current_state':'not_materialized'},
 {'field_name':'native_bip_den','exact_type':'integer_positive','required':'yes','role':'native bip denominator','current_state':'not_materialized'},
 {'field_name':'native_biz_num','exact_type':'integer','required':'conditional','role':'native biz numerator','current_state':'not_materialized'},
 {'field_name':'native_biz_den','exact_type':'integer_positive','required':'conditional','role':'native biz denominator','current_state':'not_materialized'},
 {'field_name':'native_residual_packet_id','exact_type':'identifier','required':'yes','role':'native residual packet','current_state':'schema_declared'},
 {'field_name':'native_packet_sha256','exact_type':'sha256_hex','required':'yes','role':'native temporal packet hash','current_state':'not_materialized'},
]
files['protein_schema']=write_csv('aod_protein_temporal_packet_schema.csv',lane_fields,protein_rows)

cross_fields=['audit_id','declared_domain','prediction_input','observation_inputs','exact_relation','residual_expression','required_lineage_fields','current_state']
cross_rows=[
 {'audit_id':'cross_map_h_nu','declared_domain':'photon_frequency_lane','prediction_input':'none_protocol_only','observation_inputs':'E_obs;nu_obs','exact_relation':'E=h*nu','residual_expression':'R_hnu=E_obs-h*nu_obs','required_lineage_fields':'energy_lineage;frequency_lineage;unit_policy','current_state':'schema_declared_not_instantiated'},
 {'audit_id':'cross_map_c_t','declared_domain':'null_or_light_path_lane','prediction_input':'none_protocol_only','observation_inputs':'d_obs;t_obs','exact_relation':'d=c*t','residual_expression':'R_ct=d_obs-c*t_obs','required_lineage_fields':'distance_lineage;clock_lineage;frame_policy','current_state':'schema_declared_not_instantiated'},
 {'audit_id':'cross_map_nu_t','declared_domain':'recurring_cycle_lane','prediction_input':'none_protocol_only','observation_inputs':'nu_obs;t_obs;n_cycle','exact_relation':'nu*t=n_cycle','residual_expression':'R_nut=nu_obs*t_obs-n_cycle','required_lineage_fields':'frequency_lineage;clock_lineage;cycle_count_policy','current_state':'schema_declared_not_instantiated'},
]
files['cross_map_schema']=write_csv('aod_cross_map_consistency_audit_schema.csv',cross_fields,cross_rows)

app_fields=['lane_id','scale_lane','application_lane','motif_family_source','scoped_occurrence_required','native_packet_schema','metric_projection_state','target_join_state','current_state']
app_rows=[
 {'lane_id':'elementary_118_temporal_lane','scale_lane':'elementary','application_lane':'118_element_registry_and_fusion_ladder','motif_family_source':'manual2_ontology_registry','scoped_occurrence_required':'yes','native_packet_schema':'aod_elementary_temporal_packet_schema.csv','metric_projection_state':'contracts_only','target_join_state':'closed','current_state':'schema_declared_no_duration_rows'},
 {'lane_id':'molecular_chain_temporal_lane','scale_lane':'molecular','application_lane':'molecular_chain_fusion_and_fission','motif_family_source':'manual2_ontology_registry','scoped_occurrence_required':'yes','native_packet_schema':'aod_molecular_temporal_packet_schema.csv','metric_projection_state':'contracts_only','target_join_state':'closed','current_state':'schema_declared_formula_rows_unchanged'},
 {'lane_id':'tau_boundary_ring_temporal_lane','scale_lane':'collision_support','application_lane':'Tau_boundary_ring_support_fixture','motif_family_source':'Dimonnanyro','scoped_occurrence_required':'yes','native_packet_schema':'aod_native_causal_duration_packet_schema.csv','metric_projection_state':'contracts_only','target_join_state':'closed','current_state':'protocol_compatible_not_instantiated'},
 {'lane_id':'higgs_support_temporal_lane','scale_lane':'collision_support','application_lane':'Higgs_support_mass_map_fixture','motif_family_source':'Tritrioseptyro','scoped_occurrence_required':'yes','native_packet_schema':'aod_native_causal_duration_packet_schema.csv','metric_projection_state':'contracts_only','target_join_state':'closed','current_state':'protocol_compatible_not_instantiated'},
 {'lane_id':'field_dynamics_temporal_lane','scale_lane':'field_dynamics','application_lane':'field_tunnelling_and_orbital_retention','motif_family_source':'field_tunnelling','scoped_occurrence_required':'yes','native_packet_schema':'aod_native_causal_duration_packet_schema.csv','metric_projection_state':'contracts_only','target_join_state':'closed','current_state':'protocol_compatible_not_instantiated'},
 {'lane_id':'protein_contact_temporal_lane','scale_lane':'protein','application_lane':'contact_reclosure_and_fold_packet','motif_family_source':'contact_reclosure','scoped_occurrence_required':'yes','native_packet_schema':'aod_protein_temporal_packet_schema.csv','metric_projection_state':'contracts_only','target_join_state':'closed','current_state':'schema_declared_contact_fixture_unchanged'},
]
files['application_lane_registry']=write_csv('aod_temporal_application_lane_registry.csv',app_fields,app_rows)

# validate constants and closed state
assert si_rows[0]['exact_numerator']=='9192631770'
assert si_rows[1]['exact_numerator']=='299792458'
assert si_rows[2]['exact_numerator']=='662607015'
assert si_rows[3]['exact_numerator']=='602214076000000000000000'
state_path=ROOT/'manual-2'/'data'/'protein'/'aod_double_blind_comparison_protocol_state.csv'
with state_path.open(newline='',encoding='utf-8') as f: state=list(csv.DictReader(f))[0]
assert state['target_value_read_status']=='not_read'
assert state['comparison_join_state']=='closed'
assert state['score_status']=='no_score'
manifest={
 'appendix_role':'protocol_only_no_empirical_gate_activation',
 'native_time_semantics':'exact_ordered_DEC_duration_in_bip_not_SI_time_until_projection_instantiated',
 'cesium_projection_state':'contract_declared_not_instantiated',
 'si_reference_source':'BIPM_defining_constants',
 'octave_residual_rule':'Delta_oct_lawful_change_E_oct_declared_condition_failure',
 'motif_detection_rule':'family_and_occurrence_cards_pre_run_detected_AOD_motif_after_trace_then_SADAR',
 'current_empirical_state':{'target_value_read_status':state['target_value_read_status'],'comparison_join_state':state['comparison_join_state'],'score_status':state['score_status']},
 'files':{k:str(v.relative_to(ROOT)) for k,v in files.items()},
 'sha256':{k:sha(v) for k,v in files.items()},
}
mp=OUT/'aod_native_causal_duration_projection_manifest.json'
mp.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
alias={
 'manifest_role':'short_inventory_alias',
 'canonical_manifest':'aod_native_causal_duration_projection_manifest.json',
 'canonical_manifest_sha256':sha(mp),
 'protocol_state':'schemas_declared_maps_uninstantiated_empirical_join_closed',
}
(OUT/'manifest.json').write_text(json.dumps(alias,indent=2,sort_keys=True)+'\n',encoding='utf-8')

if __name__=='__main__': pass
