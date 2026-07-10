import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMP=ROOT/'manual-2'/'data'/'temporal'
SEC=ROOT/'manual-2'/'sections'
SHARED_APP=ROOT/'shared'/'appendices'/'exact_native_dec_and_metric_projection_protocol.tex'

def rows(name):
    with (TEMP/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def text(p): return p.read_text(encoding='utf-8')

def test_shared_temporal_protocol_appendix_is_rendered_after_manual2_appendices():
    main=text(ROOT/'manual-2'/'main.tex')
    shared='../shared/appendices/exact_native_dec_and_metric_projection_protocol.tex'
    assert shared in main
    assert main.index('sections/C_roadmap_release_pointer.tex') < main.index(shared)

def test_native_duration_is_separate_from_si_and_observation_time():
    appendix=text(SHARED_APP)
    for token in ['tau_{\\mathrm{caus}}','t_{\\mathrm{SI}}','t_{\\mathrm{obs}}','not identified with SI proper time']:
        assert token in appendix
    assert 'K_{\\tau\\ell}' in appendix

def test_event_order_remains_in_native_packet_and_scalarization_is_noninjective():
    appendix=text(SHARED_APP)
    assert '\\prec_{\\omega}' in appendix
    info={r['projection_id']:r for r in rows('aod_temporal_projection_information_loss_registry.csv')}
    assert info['native_packet_to_scalar_tau_caus']['injectivity_status']=='noninjective'
    assert info['native_packet_to_scalar_tau_caus']['E_proj_status']=='not_a_projection_defect'

def test_cesium_projection_contract_is_exact_but_uninstantiated():
    cards={r['card_id']:r for r in rows('aod_cesium_time_projection_registry.csv')}
    ref=cards['cs133_si_time_reference_card']
    m=cards['aod_cesium_time_projection_linear_contract_v1']
    assert ref['si_frequency_hz_exact']=='9192631770'
    assert ref['si_time_report_rule']=='t_SI=N_Cs/9192631770_s'
    assert m['map_state']=='contract_declared_not_instantiated'
    assert m['map_coefficient_num']=='' and m['map_coefficient_den']==''
    assert m['target_value_read_status']=='not_read'

def test_si_defining_constant_values_and_domain_guards_are_exact():
    reg={r['registry_row_id']:r for r in rows('aod_si_defining_constant_projection_registry.csv')}
    assert reg['si_const_delta_nu_Cs']['exact_numerator']=='9192631770'
    assert reg['si_const_c']['exact_numerator']=='299792458'
    assert reg['si_const_h']['exact_numerator']=='662607015'
    assert reg['si_const_N_A']['exact_numerator']=='602214076000000000000000'
    assert reg['si_map_light_path']['domain_requirement']=='declared null or light propagation path'
    assert reg['si_map_photon_energy']['domain_requirement']=='declared photon-frequency lane'

def test_delta_oct_and_E_oct_are_distinct():
    reg={r['component_id']:r for r in rows('aod_temporal_typed_residual_registry.csv')}
    assert reg['Delta_oct']['meaning'].startswith('lawful exact change')
    assert reg['E_oct']['meaning'].startswith('failure of a declared')
    assert 'I_Pi' in reg and 'E_lineage' in reg

def test_lane_packet_schemas_preserve_motif_occurrence_boundary_window_and_hash_fields():
    for name in ['aod_elementary_temporal_packet_schema.csv','aod_molecular_temporal_packet_schema.csv','aod_protein_temporal_packet_schema.csv']:
        fields={r['field_name'] for r in rows(name)}
        for required in ['motif_family','scoped_occurrence_id','fractal_coord','boundary_id','window_id','event_order_sha256','native_packet_sha256']:
            assert required in fields

def test_application_registry_includes_established_lanes_without_instantiating_values():
    reg={r['lane_id']:r for r in rows('aod_temporal_application_lane_registry.csv')}
    for lane in ['elementary_118_temporal_lane','molecular_chain_temporal_lane','tau_boundary_ring_temporal_lane','higgs_support_temporal_lane','field_dynamics_temporal_lane','protein_contact_temporal_lane']:
        assert lane in reg
        assert reg[lane]['target_join_state']=='closed'
    assert reg['tau_boundary_ring_temporal_lane']['current_state']=='protocol_compatible_not_instantiated'

def test_clock_lineage_is_frozen_before_prediction_read():
    schema={r['field_name']:r for r in rows('aod_target_clock_lineage_schema.csv')}
    assert schema['prediction_read_status']['role']=='must be not_read at observation freeze'
    assert 'relativistic_correction_policy_id' in schema

def test_cross_map_audits_require_declared_physical_domain():
    audits={r['audit_id']:r for r in rows('aod_cross_map_consistency_audit_schema.csv')}
    assert audits['cross_map_h_nu']['declared_domain']=='photon_frequency_lane'
    assert audits['cross_map_c_t']['declared_domain']=='null_or_light_path_lane'
    assert audits['cross_map_nu_t']['declared_domain']=='recurring_cycle_lane'
    assert all(r['current_state']=='schema_declared_not_instantiated' for r in audits.values())

def test_temporal_manifest_regenerates_byte_identically_and_gate_remains_closed():
    p=TEMP/'aod_native_causal_duration_projection_manifest.json'
    before=p.read_bytes()
    script=ROOT/'manual-2'/'scripts'/'build_native_causal_duration_projection_protocol.py'
    result=subprocess.run([sys.executable,str(script)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert p.read_bytes()==before
    m=json.loads(p.read_text(encoding='utf-8'))
    assert m['cesium_projection_state']=='contract_declared_not_instantiated'
    assert m['current_empirical_state']=={'comparison_join_state':'closed','score_status':'no_score','target_value_read_status':'not_read'}

def test_existing_scientific_ledgers_remain_present_and_temporal_generator_does_not_write_them():
    script=text(ROOT/'manual-2'/'scripts'/'build_native_causal_duration_projection_protocol.py')
    forbidden=['fusion_ladder_336.csv','fusion_ladder_346.csv','chain_formula_predictions.csv','molecular_chain_delta3_audit.csv','aod_contact_prediction_freeze.csv']
    for name in forbidden:
        assert name not in script

def test_manual2_has_bipm_defining_constants_reference():
    refs=text(ROOT/'manual-2'/'refs.bib')
    assert '@misc{bipm-si-defining-constants' in refs
    assert 'https://www.bipm.org/en/measurement-units/si-defining-constants' in refs
