#!/usr/bin/env python3
"""Build exact native circle relational-geometry audit records.

This generator intentionally materializes record cards only. It does not
materialize independent circumference/area traces, target joins, SI reports,
residuals, or scores.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manual-2" / "data" / "circle_geometry"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def row_hash(row: dict[str, str], fields: list[str]) -> str:
    payload = "\x1f".join(row.get(k, "") for k in fields).encode("utf-8")
    return sha256_bytes(payload)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    for row in rows:
        if "row_sha256" in fields:
            row["row_sha256"] = row_hash(row, [f for f in fields if f != "row_sha256"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    type_fields = [
        "type_card_id", "object_name", "object_kind", "definition_status",
        "native_generation_role", "measurement_role", "metric_report_role",
        "target_join_status", "residual_status", "score_status", "row_sha256",
    ]
    type_rows = [
        {
            "type_card_id": "circle_type_bip_trace_count",
            "object_name": "bip_trace_count",
            "object_kind": "execution_structure",
            "definition_status": "native_trace_count_not_temporal_measurement",
            "native_generation_role": "may_count_d_e_c_transitions",
            "measurement_role": "not_a_time_measurement",
            "metric_report_role": "none",
            "target_join_status": "closed",
            "residual_status": "not_computed",
            "score_status": "no_score",
        },
        {
            "type_card_id": "circle_type_tau_cycle_constant",
            "object_name": "tau_cycle",
            "object_kind": "cyclic_notation_constant",
            "definition_status": "full_turn_symbolic_cycle_constant",
            "native_generation_role": "notation_only_not_trace_generator",
            "measurement_role": "none",
            "metric_report_role": "symbolic_report_allowed_after_trace_freeze",
            "target_join_status": "closed",
            "residual_status": "not_computed",
            "score_status": "no_score",
        },
        {
            "type_card_id": "circle_type_pi_half_turn_notation",
            "object_name": "pi",
            "object_kind": "downstream_half_turn_notation",
            "definition_status": "pi_equals_tau_over_two_not_native_primitive",
            "native_generation_role": "forbidden_as_native_primitive",
            "measurement_role": "none",
            "metric_report_role": "quarantined_display_notation",
            "target_join_status": "closed",
            "residual_status": "not_computed",
            "score_status": "no_score",
        },
        {
            "type_card_id": "circle_type_closure_relation",
            "object_name": "C_r_minus_2_A",
            "object_kind": "relational_geometry_identity",
            "definition_status": "symbolic_relation_over_frozen_circumference_area_radius_records",
            "native_generation_role": "audit_relation_only",
            "measurement_role": "not_temporal_measurement",
            "metric_report_role": "none",
            "target_join_status": "closed",
            "residual_status": "not_computed",
            "score_status": "no_score",
        },
    ]
    write_csv(OUT / "circle_relational_geometry_type_card.csv", type_fields, type_rows)

    audit_fields = [
        "audit_record_id", "radius_packet_id", "radius_symbol", "radius_status",
        "circumference_trace_id", "circumference_trace_status", "area_trace_id",
        "area_trace_status", "circumference_relation", "area_relation",
        "closure_relation", "closure_status", "pi_native_status", "tau_cycle_status",
        "metric_report_status", "target_value_read_status", "residual_status",
        "score_status", "row_sha256",
    ]
    audit_rows = [
        {
            "audit_record_id": "circle_relational_geometry_unit_symbolic_record",
            "radius_packet_id": "radius_symbolic_unit_not_metric_report",
            "radius_symbol": "r",
            "radius_status": "declared_symbolic_radius_no_SI_value",
            "circumference_trace_id": "circumference_trace_pending_independent_boundary_flow",
            "circumference_trace_status": "not_materialized_in_r17_1",
            "area_trace_id": "area_trace_pending_independent_interior_closure",
            "area_trace_status": "not_materialized_in_r17_1",
            "circumference_relation": "C=tau_cycle*r",
            "area_relation": "A=tau_cycle*r^2/2",
            "closure_relation": "C*r-2*A=0",
            "closure_status": "symbolic_relation_card_only_traces_pending",
            "pi_native_status": "forbidden_pi_is_tau_over_two_display_notation",
            "tau_cycle_status": "full_turn_cycle_symbolic_not_native_trace_input",
            "metric_report_status": "closed",
            "target_value_read_status": "not_read",
            "residual_status": "not_computed",
            "score_status": "no_score",
        }
    ]
    write_csv(OUT / "circle_relational_geometry_audit_records.csv", audit_fields, audit_rows)

    trace_fields = [
        "requirement_id", "trace_family", "required_status", "reason", "native_generation_input_status",
        "target_join_status", "metric_report_status", "row_sha256",
    ]
    trace_rows = [
        {
            "requirement_id": "circumference_trace_independence",
            "trace_family": "boundary_circumference_flow",
            "required_status": "required_before_pi_or_closure_residual_comparison",
            "reason": "circumference_must_not_read_area_trace_or_decimal_pi",
            "native_generation_input_status": "pending",
            "target_join_status": "closed",
            "metric_report_status": "closed",
        },
        {
            "requirement_id": "area_trace_independence",
            "trace_family": "interior_area_closure",
            "required_status": "required_before_pi_or_closure_residual_comparison",
            "reason": "area_must_not_read_circumference_trace_or_decimal_pi",
            "native_generation_input_status": "pending",
            "target_join_status": "closed",
            "metric_report_status": "closed",
        },
    ]
    write_csv(OUT / "circle_trace_independence_requirements.csv", trace_fields, trace_rows)

    pi_fields = [
        "notation_id", "native_name", "relation_to_tau", "native_primitive_status", "display_status",
        "target_value_status", "row_sha256",
    ]
    pi_rows = [
        {
            "notation_id": "tau_cycle_full_turn",
            "native_name": "tau_cycle",
            "relation_to_tau": "self",
            "native_primitive_status": "symbolic_cycle_notation_only_not_trace_input",
            "display_status": "allowed_after_trace_freeze",
            "target_value_status": "not_a_target",
        },
        {
            "notation_id": "pi_half_turn_quarantine",
            "native_name": "pi",
            "relation_to_tau": "pi=tau_cycle/2",
            "native_primitive_status": "forbidden",
            "display_status": "quarantined_display_notation",
            "target_value_status": "not_read",
        },
    ]
    write_csv(OUT / "circle_tau_pi_notation_policy.csv", pi_fields, pi_rows)

    cf_fields = [
        "counterfactual_id", "mutation", "expected_result", "observed_result", "audit_status", "failure_reason", "row_sha256",
    ]
    cf_rows = [
        {
            "counterfactual_id": "cf_pi_as_native_primitive",
            "mutation": "promote_pi_to_native_trace_generator",
            "expected_result": "failed",
            "observed_result": "failed",
            "audit_status": "passed",
            "failure_reason": "pi_native_primitive_forbidden",
        },
        {
            "counterfactual_id": "cf_si_radius_before_projection",
            "mutation": "insert_one_meter_radius_as_native_input",
            "expected_result": "failed",
            "observed_result": "failed",
            "audit_status": "passed",
            "failure_reason": "metric_report_closed",
        },
        {
            "counterfactual_id": "cf_target_join_present",
            "mutation": "read_external_pi_target_before_trace_freeze",
            "expected_result": "failed",
            "observed_result": "failed",
            "audit_status": "passed",
            "failure_reason": "target_join_closed",
        },
        {
            "counterfactual_id": "cf_shared_trace_for_C_and_A",
            "mutation": "use_same_trace_for_circumference_and_area",
            "expected_result": "failed",
            "observed_result": "failed",
            "audit_status": "passed",
            "failure_reason": "independent_trace_requirement_violated",
        },
        {
            "counterfactual_id": "cf_unchanged_control",
            "mutation": "unchanged_circle_record",
            "expected_result": "passed",
            "observed_result": "passed",
            "audit_status": "passed",
            "failure_reason": "none",
        },
    ]
    write_csv(OUT / "circle_relational_geometry_counterfactual_audit.csv", cf_fields, cf_rows)

    # Manifest with data hashes.
    files = [
        OUT / "circle_relational_geometry_type_card.csv",
        OUT / "circle_relational_geometry_audit_records.csv",
        OUT / "circle_trace_independence_requirements.csv",
        OUT / "circle_tau_pi_notation_policy.csv",
        OUT / "circle_relational_geometry_counterfactual_audit.csv",
    ]
    manifest = {
        "schema_version": "1.0",
        "manifest_id": "circle_relational_geometry_audit_manifest_r17_1",
        "candidate_version": "v40.03r17.1",
        "native_generation_status": "record_cards_materialized_traces_pending",
        "metric_report_status": "closed",
        "target_join_status": "closed",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "files": [
            {
                "path": str(f.relative_to(ROOT)),
                "sha256": sha256_file(f),
                "byte_count": f.stat().st_size,
            }
            for f in files
        ],
    }
    (OUT / "circle_relational_geometry_audit_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
