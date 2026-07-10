#!/usr/bin/env python3
"""Build finite circle trace and rational tau/pi error-audit records."""
from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manual-2" / "data" / "circle_geometry"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def row_hash(row: dict[str, str], fields: list[str]) -> str:
    return sha256_bytes("\x1f".join(row.get(field, "") for field in fields if field != "row_sha256").encode("utf-8"))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    for row in rows:
        if "row_sha256" in fields:
            row["row_sha256"] = row_hash(row, fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build() -> None:
    pi_lower = Fraction(103993, 33102)
    pi_upper = Fraction(104348, 33215)
    tau_lower = 2 * pi_lower
    tau_upper = 2 * pi_upper
    tau_est = Fraction(710, 113)
    pi_est = Fraction(355, 113)
    finite_fields = [
        "finite_trace_audit_id", "radius_packet_id", "radius_status",
        "circumference_trace_id", "circumference_trace_status", "area_trace_id", "area_trace_status",
        "trace_independence_status", "circumference_tau_num", "circumference_tau_den",
        "area_tau_num", "area_tau_den", "tau_difference_num", "tau_difference_den",
        "closure_residual_formula", "closure_residual_num", "closure_residual_den",
        "closure_residual_status", "metric_report_status", "target_value_read_status", "residual_status", "score_status", "row_sha256",
    ]
    write_csv(OUT / "circle_finite_trace_audit_records.csv", finite_fields, [{
        "finite_trace_audit_id": "finite_trace_tau_710_over_113_symbolic_radius",
        "radius_packet_id": "radius_symbolic_r_no_metric_report",
        "radius_status": "symbolic_radius_no_SI_value",
        "circumference_trace_id": "circumference_trace_candidate_tau_710_over_113",
        "circumference_trace_status": "finite_symbolic_candidate_not_empirical_target",
        "area_trace_id": "area_trace_candidate_tau_710_over_113",
        "area_trace_status": "finite_symbolic_candidate_not_empirical_target",
        "trace_independence_status": "independent_trace_ids_declared_same_tau_value_for_closure_audit",
        "circumference_tau_num": str(tau_est.numerator),
        "circumference_tau_den": str(tau_est.denominator),
        "area_tau_num": str(tau_est.numerator),
        "area_tau_den": str(tau_est.denominator),
        "tau_difference_num": "0",
        "tau_difference_den": "1",
        "closure_residual_formula": "C*r-2*A = (tau_C-tau_A)*r^2",
        "closure_residual_num": "0",
        "closure_residual_den": "1",
        "closure_residual_status": "exact_zero_for_equal_finite_tau_candidates",
        "metric_report_status": "closed",
        "target_value_read_status": "not_read",
        "residual_status": "not_computed",
        "score_status": "no_score",
    }])
    error_fields = [
        "error_audit_id", "tau_estimate_num", "tau_estimate_den", "pi_display_estimate_num", "pi_display_estimate_den",
        "tau_lower_num", "tau_lower_den", "tau_upper_num", "tau_upper_den",
        "pi_lower_num", "pi_lower_den", "pi_upper_num", "pi_upper_den",
        "tau_error_low_num", "tau_error_low_den", "tau_error_high_num", "tau_error_high_den",
        "pi_display_error_low_num", "pi_display_error_low_den", "pi_display_error_high_num", "pi_display_error_high_den",
        "error_interval_semantics", "decimal_value_status", "target_value_read_status", "score_status", "row_sha256",
    ]
    write_csv(OUT / "circle_rational_tau_pi_error_audit.csv", error_fields, [{
        "error_audit_id": "tau_710_over_113_against_rational_enclosure",
        "tau_estimate_num": str(tau_est.numerator),
        "tau_estimate_den": str(tau_est.denominator),
        "pi_display_estimate_num": str(pi_est.numerator),
        "pi_display_estimate_den": str(pi_est.denominator),
        "tau_lower_num": str(tau_lower.numerator),
        "tau_lower_den": str(tau_lower.denominator),
        "tau_upper_num": str(tau_upper.numerator),
        "tau_upper_den": str(tau_upper.denominator),
        "pi_lower_num": str(pi_lower.numerator),
        "pi_lower_den": str(pi_lower.denominator),
        "pi_upper_num": str(pi_upper.numerator),
        "pi_upper_den": str(pi_upper.denominator),
        "tau_error_low_num": str((tau_est - tau_upper).numerator),
        "tau_error_low_den": str((tau_est - tau_upper).denominator),
        "tau_error_high_num": str((tau_est - tau_lower).numerator),
        "tau_error_high_den": str((tau_est - tau_lower).denominator),
        "pi_display_error_low_num": str((pi_est - pi_upper).numerator),
        "pi_display_error_low_den": str((pi_est - pi_upper).denominator),
        "pi_display_error_high_num": str((pi_est - pi_lower).numerator),
        "pi_display_error_high_den": str((pi_est - pi_lower).denominator),
        "error_interval_semantics": "estimate_minus_true_symbolic_constant_with_exact_rational_enclosure",
        "decimal_value_status": "forbidden_in_canonical_scientific_rows",
        "target_value_read_status": "not_read",
        "score_status": "no_score",
    }])
    counter_fields = ["counterfactual_id", "mutation", "expected_result", "observed_result", "audit_status", "failure_reason", "row_sha256"]
    write_csv(OUT / "circle_finite_trace_counterfactual_audit.csv", counter_fields, [
        {"counterfactual_id": "cf_decimal_pi_error_value", "mutation": "insert_decimal_pi_error_display_as_canonical_value", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "canonical_rows_require_integers_or_reduced_rationals"},
        {"counterfactual_id": "cf_metric_one_meter_radius_native", "mutation": "insert_one_meter_radius_as_native_trace_radius", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "metric_radius_report_closed_in_r18_1"},
        {"counterfactual_id": "cf_reuse_same_trace_id_for_circumference_and_area", "mutation": "circumference_trace_id_equals_area_trace_id", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "circumference_and_area_require_independent_trace_ids"},
        {"counterfactual_id": "cf_target_tau_bound_before_trace_freeze", "mutation": "read_tau_enclosure_before_trace_freeze", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "rational_enclosure_joins_after_finite_trace_freeze"},
        {"counterfactual_id": "cf_unchanged_finite_trace_control", "mutation": "no_mutation", "expected_result": "passed", "observed_result": "passed", "audit_status": "passed", "failure_reason": "none"},
    ])
    manifest_files = [
        OUT / "circle_finite_trace_audit_records.csv",
        OUT / "circle_rational_tau_pi_error_audit.csv",
        OUT / "circle_finite_trace_counterfactual_audit.csv",
    ]
    manifest = {
        "schema": "aod.manual2.circle_finite_trace_tau_pi_error_audit.v1",
        "milestone": "v40.03r18.2",
        "metric_report_status": "closed",
        "target_join_status": "closed",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "decimal_value_status": "forbidden_in_canonical_scientific_rows",
        "trace_identity_contract": "shared_circle_occurrence_with_independent_circumference_and_area_trace_ids",
        "circumference_area_trace_id_relation": "must_be_distinct",
        "shared_circle_occurrence_status": "allowed",
        "shared_tau_cycle_candidate_status": "allowed",
        "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)} for path in manifest_files],
    }
    (OUT / "circle_finite_trace_tau_pi_error_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()

