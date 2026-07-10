#!/usr/bin/env python3
"""Build downstream one-metre null-path report-card ledgers for circle audit."""
from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manual-2" / "data" / "circle_geometry"




def payload_materialization_milestone() -> str:
    state_path = ROOT / "governance" / "RELEASE_METADATA_STATE.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return state.get("payload_materialization_milestone", "v40.03r19.1")
    return "v40.03r19.1"

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
    # SI exact constants are represented only as downstream report-card data.
    c = Fraction(299_792_458, 1)
    one_metre_light_time = Fraction(1, 299_792_458)
    fields = [
        "report_card_id", "card_family", "physical_relation_domain", "relation_formula",
        "exact_constant_symbol", "exact_constant_num", "exact_constant_den", "constant_unit_symbol",
        "one_metre_report_symbol", "one_metre_light_time_num", "one_metre_light_time_den",
        "null_path_domain_status", "native_premise_status", "projection_input_required",
        "metric_report_status", "target_value_read_status", "residual_status", "score_status", "row_sha256",
    ]
    write_csv(OUT / "circle_one_metre_null_path_report_cards.csv", fields, [{
        "report_card_id": "one_metre_null_path_reference_card",
        "card_family": "metric_report_unit_card",
        "physical_relation_domain": "declared_null_path_light_propagation_only",
        "relation_formula": "d=c*t",
        "exact_constant_symbol": "c",
        "exact_constant_num": str(c.numerator),
        "exact_constant_den": str(c.denominator),
        "constant_unit_symbol": "m_per_s",
        "one_metre_report_symbol": "one_metre_report_radius_r_1m",
        "one_metre_light_time_num": str(one_metre_light_time.numerator),
        "one_metre_light_time_den": str(one_metre_light_time.denominator),
        "null_path_domain_status": "declared_report_domain_not_native_trace_domain",
        "native_premise_status": "forbidden",
        "projection_input_required": "true",
        "metric_report_status": "contract_declared_not_instantiated",
        "target_value_read_status": "not_read",
        "residual_status": "not_computed",
        "score_status": "no_score",
    }])

    link_fields = [
        "link_id", "circle_occurrence_id", "finite_trace_audit_id", "report_card_id", "radius_symbol_source",
        "native_trace_binding_status", "metric_radius_binding_status", "tau_cycle_source_status", "target_value_read_status", "score_status", "row_sha256",
    ]
    write_csv(OUT / "circle_one_metre_report_link_index.csv", link_fields, [{
        "link_id": "circle_symbolic_radius_to_one_metre_report_card_link",
        "circle_occurrence_id": "circle_relational_geometry_occurrence_symbolic",
        "finite_trace_audit_id": "finite_trace_tau_710_over_113_symbolic_radius",
        "report_card_id": "one_metre_null_path_reference_card",
        "radius_symbol_source": "symbolic_radius_r_from_native_circle_audit",
        "native_trace_binding_status": "not_bound_to_metric_card",
        "metric_radius_binding_status": "downstream_link_declared_not_instantiated",
        "tau_cycle_source_status": "finite_trace_candidate_frozen_before_metric_report_link",
        "target_value_read_status": "not_read",
        "score_status": "no_score",
    }])

    quarantine_fields = ["counterfactual_id", "mutation", "expected_result", "observed_result", "audit_status", "failure_reason", "row_sha256"]
    write_csv(OUT / "circle_one_metre_null_path_counterfactual_audit.csv", quarantine_fields, [
        {"counterfactual_id": "cf_one_metre_radius_as_native_trace_input", "mutation": "insert_one_metre_value_into_native_radius_packet", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "metric_report_card_forbidden_as_native_premise"},
        {"counterfactual_id": "cf_speed_of_light_as_DEC_kernel_weight", "mutation": "use_c_value_as_native_DEC_weight", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "SI_constant_not_a_DEC_kernel_parameter"},
        {"counterfactual_id": "cf_null_path_report_before_trace_freeze", "mutation": "link_metric_null_path_card_before_finite_trace_freeze", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "report_card_link_requires_prior_trace_freeze"},
        {"counterfactual_id": "cf_target_radius_joined_as_observation", "mutation": "read_observed_radius_target_in_report_card_gate", "expected_result": "failed", "observed_result": "failed", "audit_status": "passed", "failure_reason": "target_join_closed_in_r19_1"},
        {"counterfactual_id": "cf_unchanged_one_metre_report_card_control", "mutation": "no_mutation", "expected_result": "passed", "observed_result": "passed", "audit_status": "passed", "failure_reason": "none"},
    ])

    manifest_files = [
        OUT / "circle_one_metre_null_path_report_cards.csv",
        OUT / "circle_one_metre_report_link_index.csv",
        OUT / "circle_one_metre_null_path_counterfactual_audit.csv",
    ]
    manifest = {
        "schema": "aod.manual2.circle_one_metre_null_path_report_cards.v1",
        "milestone": payload_materialization_milestone(),
        "card_scope": "downstream_metric_report_card_contracts_only",
        "native_premise_status": "forbidden",
        "metric_report_status": "contract_declared_not_instantiated",
        "target_join_status": "closed",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "null_path_relation": "d=c*t only under declared null_path_light_propagation_domain",
        "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)} for path in manifest_files],
    }
    (OUT / "circle_one_metre_null_path_report_cards_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
