import csv
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'manual-2' / 'data' / 'circle_geometry'


def rows(name):
    with (DATA / name).open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def test_report_card_manifest_and_closed_lanes():
    manifest = json.loads((DATA / 'circle_one_metre_null_path_report_cards_manifest.json').read_text())
    state = json.loads((ROOT / 'governance' / 'RELEASE_METADATA_STATE.json').read_text())
    assert manifest['milestone'] == state['payload_materialization_milestone']
    paths = {entry['path'] for entry in manifest['files']}
    assert 'manual-2/data/circle_geometry/circle_one_metre_null_path_report_cards.csv' in paths
    assert 'manual-2/data/circle_geometry/circle_one_metre_report_link_index.csv' in paths
    assert 'manual-2/data/circle_geometry/circle_one_metre_null_path_counterfactual_audit.csv' in paths
    assert manifest['native_premise_status'] == 'forbidden'
    assert manifest['metric_report_status'] == 'contract_declared_not_instantiated'
    assert manifest['target_join_status'] == 'closed'
    assert manifest['score_status'] == 'no_score'


def test_one_metre_null_path_card_is_exact_and_downstream():
    row = rows('circle_one_metre_null_path_report_cards.csv')[0]
    assert row['report_card_id'] == 'one_metre_null_path_reference_card'
    assert row['physical_relation_domain'] == 'declared_null_path_light_propagation_only'
    assert Fraction(int(row['exact_constant_num']), int(row['exact_constant_den'])) == Fraction(299792458, 1)
    assert Fraction(int(row['one_metre_light_time_num']), int(row['one_metre_light_time_den'])) == Fraction(1, 299792458)
    assert row['native_premise_status'] == 'forbidden'
    assert row['projection_input_required'] == 'true'
    assert row['metric_report_status'] == 'contract_declared_not_instantiated'
    assert row['target_value_read_status'] == 'not_read'
    assert row['score_status'] == 'no_score'


def test_report_link_preserves_native_quarantine():
    row = rows('circle_one_metre_report_link_index.csv')[0]
    assert row['finite_trace_audit_id'] == 'finite_trace_tau_710_over_113_symbolic_radius'
    assert row['radius_symbol_source'] == 'symbolic_radius_r_from_native_circle_audit'
    assert row['native_trace_binding_status'] == 'not_bound_to_metric_card'
    assert row['metric_radius_binding_status'] == 'downstream_link_declared_not_instantiated'
    assert row['target_value_read_status'] == 'not_read'


def test_one_metre_counterfactuals_fail_closed_except_control():
    by_id = {row['counterfactual_id']: row for row in rows('circle_one_metre_null_path_counterfactual_audit.csv')}
    for key in ['cf_one_metre_radius_as_native_trace_input','cf_speed_of_light_as_DEC_kernel_weight','cf_null_path_report_before_trace_freeze','cf_target_radius_joined_as_observation']:
        assert by_id[key]['observed_result'] == 'failed'
        assert by_id[key]['audit_status'] == 'passed'
    assert by_id['cf_unchanged_one_metre_report_card_control']['observed_result'] == 'passed'
    assert by_id['cf_unchanged_one_metre_report_card_control']['audit_status'] == 'passed'


def test_manual2_inputs_one_metre_report_section():
    main = (ROOT / 'manual-2' / 'main.tex').read_text()
    assert '03_circle_one_metre_null_path_report_cards.tex' in main
    section = (ROOT / 'manual-2' / 'sections' / '03_circle_one_metre_null_path_report_cards.tex').read_text()
    assert 'Circle One-Metre Null-Path Report Cards' in section
    assert 'downstream report contract' in section
    assert 'not a native trace input' in section


def test_report_card_generator_uses_metadata_state_payload_milestone():
    script = (ROOT / 'manual-2' / 'scripts' / 'build_circle_one_metre_null_path_report_cards.py').read_text()
    state = json.loads((ROOT / 'governance' / 'RELEASE_METADATA_STATE.json').read_text())
    assert 'payload_materialization_milestone' in script
    assert '"v40.03r19.2"' not in script
    assert state['payload_materialization_milestone'] == 'v40.03r19.1'
