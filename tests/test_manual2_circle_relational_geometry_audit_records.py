import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'manual-2' / 'data' / 'circle_geometry'


def read_csv(name):
    with (DATA / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def test_circle_audit_files_exist_and_manifested():
    manifest = json.loads((DATA / 'circle_relational_geometry_audit_manifest.json').read_text())
    paths = {entry['path'] for entry in manifest['files']}
    expected = {
        'manual-2/data/circle_geometry/circle_relational_geometry_type_card.csv',
        'manual-2/data/circle_geometry/circle_relational_geometry_audit_records.csv',
        'manual-2/data/circle_geometry/circle_trace_independence_requirements.csv',
        'manual-2/data/circle_geometry/circle_tau_pi_notation_policy.csv',
        'manual-2/data/circle_geometry/circle_relational_geometry_counterfactual_audit.csv',
    }
    assert expected <= paths
    assert manifest['target_join_status'] == 'closed'
    assert manifest['metric_report_status'] == 'closed'
    assert manifest['score_status'] == 'no_score'


def test_circle_records_do_not_materialize_targets_or_metric_reports():
    rows = read_csv('circle_relational_geometry_audit_records.csv')
    assert len(rows) == 1
    row = rows[0]
    assert row['circumference_relation'] == 'C=tau_cycle*r'
    assert row['area_relation'] == 'A=tau_cycle*r^2/2'
    assert row['closure_relation'] == 'C*r-2*A=0'
    assert row['pi_native_status'] == 'forbidden_pi_is_tau_over_two_display_notation'
    assert row['metric_report_status'] == 'closed'
    assert row['target_value_read_status'] == 'not_read'
    assert row['residual_status'] == 'not_computed'
    assert row['score_status'] == 'no_score'


def test_tau_pi_policy_quarantines_pi_as_display_notation():
    rows = {row['notation_id']: row for row in read_csv('circle_tau_pi_notation_policy.csv')}
    assert rows['tau_cycle_full_turn']['native_name'] == 'tau_cycle'
    assert rows['pi_half_turn_quarantine']['native_primitive_status'] == 'forbidden'
    assert rows['pi_half_turn_quarantine']['relation_to_tau'] == 'pi=tau_cycle/2'


def test_trace_independence_requirements_are_closed_to_targets():
    rows = read_csv('circle_trace_independence_requirements.csv')
    assert {row['trace_family'] for row in rows} == {'boundary_circumference_flow', 'interior_area_closure'}
    assert all(row['target_join_status'] == 'closed' for row in rows)
    assert all(row['metric_report_status'] == 'closed' for row in rows)


def test_counterfactuals_fail_closed_except_control():
    rows = {row['counterfactual_id']: row for row in read_csv('circle_relational_geometry_counterfactual_audit.csv')}
    for key in ['cf_pi_as_native_primitive', 'cf_si_radius_before_projection', 'cf_target_join_present', 'cf_shared_trace_for_C_and_A']:
        assert rows[key]['observed_result'] == 'failed'
        assert rows[key]['audit_status'] == 'passed'
    assert rows['cf_unchanged_control']['observed_result'] == 'passed'
    assert rows['cf_unchanged_control']['audit_status'] == 'passed'


def test_manual2_renders_circle_section_input():
    main = (ROOT / 'manual-2' / 'main.tex').read_text()
    assert '01_circle_relational_geometry_audit_records.tex' in main
    section = (ROOT / 'manual-2' / 'sections' / '01_circle_relational_geometry_audit_records.tex').read_text()
    assert 'Circle Relational Geometry Audit Records' in section
    assert 'Cr-2A=0' in section
