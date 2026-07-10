import csv
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'manual-2' / 'data' / 'circle_geometry'


def rows(name):
    with (DATA / name).open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def test_finite_trace_files_manifested_and_closed():
    manifest = json.loads((DATA / 'circle_finite_trace_tau_pi_error_manifest.json').read_text())
    paths = {entry['path'] for entry in manifest['files']}
    assert 'manual-2/data/circle_geometry/circle_finite_trace_audit_records.csv' in paths
    assert 'manual-2/data/circle_geometry/circle_rational_tau_pi_error_audit.csv' in paths
    assert 'manual-2/data/circle_geometry/circle_finite_trace_counterfactual_audit.csv' in paths
    assert manifest['metric_report_status'] == 'closed'
    assert manifest['target_join_status'] == 'closed'
    assert manifest['score_status'] == 'no_score'
    assert manifest['decimal_value_status'] == 'forbidden_in_canonical_scientific_rows'
    assert manifest['trace_identity_contract'] == 'shared_circle_occurrence_with_independent_circumference_and_area_trace_ids'
    assert manifest['circumference_area_trace_id_relation'] == 'must_be_distinct'
    assert manifest['shared_circle_occurrence_status'] == 'allowed'
    assert manifest['shared_tau_cycle_candidate_status'] == 'allowed'


def test_finite_trace_closure_is_exact_and_trace_ids_are_distinct():
    row = rows('circle_finite_trace_audit_records.csv')[0]
    assert row['circumference_trace_id'] != row['area_trace_id']
    assert Fraction(int(row['circumference_tau_num']), int(row['circumference_tau_den'])) == Fraction(710, 113)
    assert Fraction(int(row['area_tau_num']), int(row['area_tau_den'])) == Fraction(710, 113)
    assert Fraction(int(row['tau_difference_num']), int(row['tau_difference_den'])) == 0
    assert Fraction(int(row['closure_residual_num']), int(row['closure_residual_den'])) == 0
    assert row['metric_report_status'] == 'closed'
    assert row['target_value_read_status'] == 'not_read'
    assert row['score_status'] == 'no_score'


def test_rational_tau_pi_error_intervals_are_exact():
    row = rows('circle_rational_tau_pi_error_audit.csv')[0]
    tau_est = Fraction(int(row['tau_estimate_num']), int(row['tau_estimate_den']))
    pi_est = Fraction(int(row['pi_display_estimate_num']), int(row['pi_display_estimate_den']))
    pi_lower = Fraction(103993, 33102)
    pi_upper = Fraction(104348, 33215)
    assert tau_est == Fraction(710, 113)
    assert pi_est == Fraction(355, 113)
    assert Fraction(int(row['pi_lower_num']), int(row['pi_lower_den'])) == pi_lower
    assert Fraction(int(row['pi_upper_num']), int(row['pi_upper_den'])) == pi_upper
    assert Fraction(int(row['tau_lower_num']), int(row['tau_lower_den'])) == 2 * pi_lower
    assert Fraction(int(row['tau_upper_num']), int(row['tau_upper_den'])) == 2 * pi_upper
    assert Fraction(int(row['tau_error_low_num']), int(row['tau_error_low_den'])) == tau_est - 2*pi_upper
    assert Fraction(int(row['tau_error_high_num']), int(row['tau_error_high_den'])) == tau_est - 2*pi_lower
    assert row['decimal_value_status'] == 'forbidden_in_canonical_scientific_rows'


def test_counterfactuals_fail_closed_except_control():
    by_id = {row['counterfactual_id']: row for row in rows('circle_finite_trace_counterfactual_audit.csv')}
    for key in ['cf_decimal_pi_error_value','cf_metric_one_meter_radius_native','cf_reuse_same_trace_id_for_circumference_and_area','cf_target_tau_bound_before_trace_freeze']:
        assert by_id[key]['observed_result'] == 'failed'
        assert by_id[key]['audit_status'] == 'passed'
    assert by_id['cf_unchanged_finite_trace_control']['observed_result'] == 'passed'
    assert by_id['cf_unchanged_finite_trace_control']['audit_status'] == 'passed'


def test_manual2_inputs_finite_trace_section():
    main = (ROOT / 'manual-2' / 'main.tex').read_text()
    assert '02_circle_finite_trace_tau_pi_error_audit.tex' in main
    section = (ROOT / 'manual-2' / 'sections' / '02_circle_finite_trace_tau_pi_error_audit.tex').read_text()
    assert 'Circle Finite-Trace and Rational Tau/Pi Error Audit' in section
    assert '710}{113' in section
    assert 'independent circumference and area trace identifiers' in section
    assert 'Reusing one trace identifier' in section
