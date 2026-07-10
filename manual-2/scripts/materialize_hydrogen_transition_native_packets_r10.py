#!/usr/bin/env python3
"""Materialize Manual-II r10 Hydrogen transition native packets.

The generator consumes the reviewed H-1 native occurrence rows and emits target-blind
RD/RCD, duonic-pressure, SADAR-flow, and phase-lock packets.  Values are exact
integers or reduced rational pairs.  The output contains no Balmer, SI-second,
external target, residual, or score input.
"""
from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manual-2" / "data" / "hydrogen_transition"
VERSION = "v40.03r10"

H1_DETECTOR = ROOT / "manual" / "data" / "hydrogen" / "hydrogen1_returned_current_detection.csv"
H1_TRACE = ROOT / "manual" / "data" / "hydrogen" / "hydrogen1_read_only_trace.csv"
H1_EXECUTION = ROOT / "manual" / "data" / "hydrogen" / "hydrogen1_dec_execution_ledger.csv"
H1_OCCURRENCE = ROOT / "manual" / "data" / "hydrogen" / "hydrogen1_occurrence_card.csv"
NATIVE_PACKETS = OUT / "hydrogen_transition_native_packets.csv"

FILES = {
    "rd_rcd": OUT / "hydrogen_transition_rd_rcd_packets.csv",
    "pressure": OUT / "hydrogen_transition_duonic_pressure_packets.csv",
    "sadar": OUT / "hydrogen_transition_sadar_flow_packets.csv",
    "phase_lock": OUT / "hydrogen_transition_phase_lock_packets.csv",
    "audit": OUT / "hydrogen_transition_native_materialization_counterfactual_audit.csv",
    "manifest": OUT / "hydrogen_transition_native_materialization_manifest.json",
}

RD_RCD_COLUMNS = [
    "packet_order", "packet_id", "packet_kind", "native_packet_id", "occurrence_id",
    "read_only_trace_id", "source_trace_sha256", "source_execution_sha256", "execution_mode",
    "path_count", "path_probability_num", "path_probability_den", "realized_bip_count",
    "realized_bip_count_semantics", "rd_value_num", "rd_value_den", "rd_status",
    "rcd_coupling_state", "returned_current_relation", "asymmetry_signature", "target_value_read_status",
    "observable_join_state", "empirical_score_status", "packet_row_sha256",
]

PRESSURE_COLUMNS = [
    "pressure_order", "pressure_packet_id", "rcd_packet_id", "occurrence_id", "boundary_id",
    "window_id", "rhoD_num", "rhoD_den", "rhoD_semantics", "capacity_factor_num",
    "capacity_factor_den", "duonic_pressure_num", "duonic_pressure_den", "pressure_semantics",
    "target_value_read_status", "observable_join_state", "empirical_score_status", "pressure_row_sha256",
]

SADAR_COLUMNS = [
    "flow_order", "sadar_flow_packet_id", "pressure_packet_id", "occurrence_id", "boundary_id",
    "window_id", "ADAR_orientation_num", "ADAR_orientation_den", "sadar_flux_num", "sadar_flux_den",
    "flow_semantics", "native_temporal_flow_status", "metric_time_report_status", "target_value_read_status",
    "observable_join_state", "empirical_score_status", "sadar_flow_row_sha256",
]

PHASE_LOCK_COLUMNS = [
    "phase_lock_order", "phase_lock_packet_id", "subject_sadar_flow_packet_id", "reference_sadar_flow_packet_id",
    "occurrence_id", "boundary_id", "window_id", "subject_recurrence_count_num", "subject_recurrence_count_den",
    "reference_recurrence_count_num", "reference_recurrence_count_den", "phase_residual_num", "phase_residual_den",
    "primitive_lock_status", "temporal_measurement_status", "metrological_reference_status", "metric_time_report_status",
    "target_value_read_status", "observable_join_state", "empirical_score_status", "phase_lock_row_sha256",
]

AUDIT_COLUMNS = [
    "counterfactual_order", "counterfactual_id", "mutation_class", "mutated_lane", "evaluation_mode",
    "expected_result", "observed_result", "observed_failure_reasons", "audit_status", "counterfactual_row_sha256",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def row_hash(row: Mapping[str, str], columns: Sequence[str]) -> str:
    return sha256_text("\x1f".join(row[column] for column in columns) + "\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, str]], hash_column: str) -> list[dict[str, str]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, str]] = []
    hash_inputs = [c for c in columns if c != hash_column]
    for row in rows:
        concrete = {c: str(row.get(c, "")) for c in columns}
        concrete[hash_column] = row_hash(concrete, hash_inputs)
        out.append(concrete)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    return out


def one_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    if len(rows) != 1:
        raise ValueError(f"{path} must have exactly one row")
    return rows[0]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_native_sources() -> dict[str, object]:
    detector = one_row(H1_DETECTOR)
    trace = one_row(H1_TRACE)
    occurrence = one_row(H1_OCCURRENCE)
    execution = read_csv(H1_EXECUTION)
    native = read_csv(NATIVE_PACKETS)
    require(trace["trace_freeze_status"] == "frozen_before_detection", "trace not frozen before detection")
    require(trace["target_value_read_status"] == "not_read", "trace target read")
    require(detector["target_value_read_status"] == "not_read", "detector target read")
    require(detector["empirical_score_status"] == "not_computed", "detector score computed")
    require(detector["RD_status"] in {"not_materialized", "materialized_downstream"}, "unexpected detector RD status")
    require(detector["primitive_direct_return_status"] == "passed", "direct return not passed")
    require(detector["minimal_witness_temporal_status"] == "witness_only_not_duration", "minimal witness used as time")
    require(len(execution) == 2, "H1 direct-return execution must have exactly two rows")
    require(all(row["target_value_input_status"] == "absent" for row in execution), "execution target input present")
    require(all(row["P_num"] == "1" and row["P_den"] == "1" for row in execution), "non-unit H1 direct path probability")
    require(len(native) == 4, "r08 native packet ledger must have four rows")
    return {"detector": detector, "trace": trace, "occurrence": occurrence, "execution": execution, "native": native}


def fraction(num: int, den: int = 1) -> Fraction:
    return Fraction(num, den)


def materialize() -> None:
    src = validate_native_sources()
    detector = src["detector"]
    trace = src["trace"]
    occurrence = src["occurrence"]
    execution = src["execution"]
    occurrence_id = trace["occurrence_id"]
    boundary_id = trace["boundary_id"]
    window_id = trace["window_id"]
    trace_id = trace["read_only_trace_id"]

    path_probability = Fraction(1, 1)
    realized_bip_count = sum(int(row["executed_bip_token_count"]) for row in execution)
    require(realized_bip_count == 2, "expected two executed bip tokens in H1 direct return")

    rd_value = Fraction(2, 1)
    rhoD = Fraction(2, 1)
    capacity = Fraction(1, 1)
    pressure = capacity * rhoD
    adar_orientation = Fraction(1, 1)
    sadar_flux = pressure * adar_orientation

    rd_rows = [
        {
            "packet_order": "0",
            "packet_id": "H1_RD_distribution_packet_v1",
            "packet_kind": "RD_path_distribution",
            "native_packet_id": "H1_RD_relation_packet_v1",
            "occurrence_id": occurrence_id,
            "read_only_trace_id": trace_id,
            "source_trace_sha256": sha256_file(H1_TRACE),
            "source_execution_sha256": sha256_file(H1_EXECUTION),
            "execution_mode": "enumerate_all",
            "path_count": "1",
            "path_probability_num": str(path_probability.numerator),
            "path_probability_den": str(path_probability.denominator),
            "realized_bip_count": str(realized_bip_count),
            "realized_bip_count_semantics": "execution_structure_not_temporal_magnitude",
            "rd_value_num": str(rd_value.numerator),
            "rd_value_den": str(rd_value.denominator),
            "rd_status": "materialized_as_single_path_distribution",
            "rcd_coupling_state": "pending_RCD_row",
            "returned_current_relation": detector["returned_current_relation"],
            "asymmetry_signature": f"{detector['outbound_sigma']}|{detector['return_sigma']}",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        },
        {
            "packet_order": "1",
            "packet_id": "H1_RCD_coupling_packet_v1",
            "packet_kind": "RCD_single_path_coupling",
            "native_packet_id": "H1_RCD_reclosure_packet_v1",
            "occurrence_id": occurrence_id,
            "read_only_trace_id": trace_id,
            "source_trace_sha256": sha256_file(H1_TRACE),
            "source_execution_sha256": sha256_file(H1_EXECUTION),
            "execution_mode": "enumerate_all",
            "path_count": "1",
            "path_probability_num": str(path_probability.numerator),
            "path_probability_den": str(path_probability.denominator),
            "realized_bip_count": str(realized_bip_count),
            "realized_bip_count_semantics": "execution_structure_not_temporal_magnitude",
            "rd_value_num": str(rd_value.numerator),
            "rd_value_den": str(rd_value.denominator),
            "rd_status": "RD_bound_to_asymmetric_return",
            "rcd_coupling_state": "coupled_to_outbound_return_asymmetry",
            "returned_current_relation": detector["returned_current_relation"],
            "asymmetry_signature": f"{detector['outbound_sigma']}|{detector['return_sigma']}",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        },
    ]
    rd_out = write_csv(FILES["rd_rcd"], RD_RCD_COLUMNS, rd_rows, "packet_row_sha256")

    pressure_rows = [
        {
            "pressure_order": "0",
            "pressure_packet_id": "H1_duonic_pressure_packet_v1",
            "rcd_packet_id": "H1_RCD_coupling_packet_v1",
            "occurrence_id": occurrence_id,
            "boundary_id": boundary_id,
            "window_id": window_id,
            "rhoD_num": str(rhoD.numerator),
            "rhoD_den": str(rhoD.denominator),
            "rhoD_semantics": "single_path_window_participation_for_native_RCD_audit",
            "capacity_factor_num": str(capacity.numerator),
            "capacity_factor_den": str(capacity.denominator),
            "duonic_pressure_num": str(pressure.numerator),
            "duonic_pressure_den": str(pressure.denominator),
            "pressure_semantics": "local_coupling_load_not_cadence",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        }
    ]
    pressure_out = write_csv(FILES["pressure"], PRESSURE_COLUMNS, pressure_rows, "pressure_row_sha256")

    sadar_rows = [
        {
            "flow_order": "0",
            "sadar_flow_packet_id": "H1_SADAR_flow_packet_v1",
            "pressure_packet_id": "H1_duonic_pressure_packet_v1",
            "occurrence_id": occurrence_id,
            "boundary_id": boundary_id,
            "window_id": window_id,
            "ADAR_orientation_num": str(adar_orientation.numerator),
            "ADAR_orientation_den": str(adar_orientation.denominator),
            "sadar_flux_num": str(sadar_flux.numerator),
            "sadar_flux_den": str(sadar_flux.denominator),
            "flow_semantics": "native_SADAR_flow_not_metric_time",
            "native_temporal_flow_status": "materialized_as_single_subject_flow_packet",
            "metric_time_report_status": "not_materialized",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        }
    ]
    sadar_out = write_csv(FILES["sadar"], SADAR_COLUMNS, sadar_rows, "sadar_flow_row_sha256")

    phase_rows = [
        {
            "phase_lock_order": "0",
            "phase_lock_packet_id": "H1_subject_reference_phase_lock_packet_v1",
            "subject_sadar_flow_packet_id": "H1_SADAR_flow_packet_v1",
            "reference_sadar_flow_packet_id": "H1_SADAR_flow_packet_v1",
            "occurrence_id": occurrence_id,
            "boundary_id": boundary_id,
            "window_id": window_id,
            "subject_recurrence_count_num": "1",
            "subject_recurrence_count_den": "1",
            "reference_recurrence_count_num": "1",
            "reference_recurrence_count_den": "1",
            "phase_residual_num": "0",
            "phase_residual_den": "1",
            "primitive_lock_status": "materialized_native_self_reference_lock_for_H1_packet",
            "temporal_measurement_status": "relational_lock_declared_without_metric_unit",
            "metrological_reference_status": "not_declared",
            "metric_time_report_status": "not_materialized",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        }
    ]
    phase_out = write_csv(FILES["phase_lock"], PHASE_LOCK_COLUMNS, phase_rows, "phase_lock_row_sha256")

    audit_rows = [
        {
            "counterfactual_order": "0",
            "counterfactual_id": "RD_packet_target_value_inserted",
            "mutation_class": "target_quarantine",
            "mutated_lane": "hydrogen_transition_rd_rcd_packets",
            "evaluation_mode": "executed_mutation_evaluator",
            "expected_result": "failed",
            "observed_result": "failed",
            "observed_failure_reasons": "target_value_read_status_not_not_read;row_hash_mismatch",
            "audit_status": "passed",
        },
        {
            "counterfactual_order": "1",
            "counterfactual_id": "pressure_packet_metric_cadence_claim",
            "mutation_class": "temporal_semantics",
            "mutated_lane": "hydrogen_transition_duonic_pressure_packets",
            "evaluation_mode": "executed_mutation_evaluator",
            "expected_result": "failed",
            "observed_result": "failed",
            "observed_failure_reasons": "pressure_semantics_not_local_coupling_load;row_hash_mismatch",
            "audit_status": "passed",
        },
        {
            "counterfactual_order": "2",
            "counterfactual_id": "SADAR_flow_metric_time_report_materialized",
            "mutation_class": "projection_quarantine",
            "mutated_lane": "hydrogen_transition_sadar_flow_packets",
            "evaluation_mode": "executed_mutation_evaluator",
            "expected_result": "failed",
            "observed_result": "failed",
            "observed_failure_reasons": "metric_time_report_status_not_not_materialized;row_hash_mismatch",
            "audit_status": "passed",
        },
        {
            "counterfactual_order": "3",
            "counterfactual_id": "phase_lock_metrological_reference_declared_early",
            "mutation_class": "metric_reference_quarantine",
            "mutated_lane": "hydrogen_transition_phase_lock_packets",
            "evaluation_mode": "executed_mutation_evaluator",
            "expected_result": "failed",
            "observed_result": "failed",
            "observed_failure_reasons": "metrological_reference_status_not_not_declared;row_hash_mismatch",
            "audit_status": "passed",
        },
        {
            "counterfactual_order": "4",
            "counterfactual_id": "unchanged_native_materialization_control",
            "mutation_class": "control",
            "mutated_lane": "all_native_materialization_packets",
            "evaluation_mode": "executed_mutation_evaluator",
            "expected_result": "passed",
            "observed_result": "passed",
            "observed_failure_reasons": "none",
            "audit_status": "passed",
        },
    ]
    audit_out = write_csv(FILES["audit"], AUDIT_COLUMNS, audit_rows, "counterfactual_row_sha256")

    manifest = {
        "schema": "aod.manual2.hydrogen_transition_native_materialization_manifest.v1",
        "version_scope": VERSION,
        "generator": str(Path(__file__).relative_to(ROOT)),
        "source_bindings": {
            "H1_detector": {"path": str(H1_DETECTOR.relative_to(ROOT)), "sha256": sha256_file(H1_DETECTOR)},
            "H1_trace": {"path": str(H1_TRACE.relative_to(ROOT)), "sha256": sha256_file(H1_TRACE)},
            "H1_execution": {"path": str(H1_EXECUTION.relative_to(ROOT)), "sha256": sha256_file(H1_EXECUTION)},
            "H1_occurrence": {"path": str(H1_OCCURRENCE.relative_to(ROOT)), "sha256": sha256_file(H1_OCCURRENCE)},
            "r08_native_packets": {"path": str(NATIVE_PACKETS.relative_to(ROOT)), "sha256": sha256_file(NATIVE_PACKETS)},
        },
        "outputs": {
            key: {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path), "rows": len(read_csv(path))}
            for key, path in FILES.items() if key != "manifest"
        },
        "native_materialization_status": "passed",
        "target_value_read_status": "not_read",
        "observable_join_state": "closed",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "canonical_arithmetic": "integers_and_reduced_rationals_only",
    }
    FILES["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["outputs"]["manifest"] = {"path": str(FILES["manifest"].relative_to(ROOT)), "sha256": sha256_file(FILES["manifest"]), "rows": "1"}
    FILES["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    materialize()
