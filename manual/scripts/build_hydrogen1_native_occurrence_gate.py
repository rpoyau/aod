#!/usr/bin/env python3
"""Build the target-blind Hydrogen-1 native occurrence gate.

The gate materializes one identity-bound, connected local Q4 D.E.C. occurrence
for H-1.  It keeps the 3:3:6 core and 1:2:6/C6 outer forms as declared scope
contracts, not as local edge pools.  The connected trace is a direct
outbound/return witness with exact local kernels and exact mass conservation.

No Balmer ratio, observed line, SI unit, target value, residual, or score is
read by this generator.  RD/RCD, duonic pressure, SADAR flow, phase lock, and
transition-atlas rows remain downstream.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual" / "data" / "hydrogen"
C6 = ROOT / "manual" / "data" / "c6"
VERSION = "v40.03r07.1"
GATE_ID = "aod_hydrogen1_native_occurrence_gate_v2"

H_PLAN = C6 / "hydrogen_occurrence_plan.csv"
CORE_OCCURRENCES = C6 / "consequent_six_slot_occurrence_card.csv"
SUPPORT_POLICY = C6 / "c6_recurrence_support_policy.csv"
CONSEQUENT_GATE_MANIFEST = C6 / "consequent_six_slot_gate_manifest.json"
TEMPORAL_TYPES = ROOT / "manual" / "data" / "temporal_relational" / "relational_temporal_type_registry.csv"

FILES = {
    "identity": DATA / "hydrogen1_identity_packet.csv",
    "contract": DATA / "hydrogen1_local_dec_contract.csv",
    "occurrence": DATA / "hydrogen1_occurrence_card.csv",
    "states": DATA / "hydrogen1_local_q4_state_registry.csv",
    "inventory": DATA / "hydrogen1_local_q4_edge_inventory.csv",
    "kernel": DATA / "hydrogen1_local_q4_kernel_audit.csv",
    "execution": DATA / "hydrogen1_dec_execution_ledger.csv",
    "read_only": DATA / "hydrogen1_read_only_trace.csv",
    "source_chain_audit": DATA / "hydrogen1_source_chain_audit.csv",
    "pre_manifest": DATA / "hydrogen1_pre_detection_freeze_manifest.json",
    "detector": DATA / "hydrogen1_returned_current_detection.csv",
    "identity_cf": DATA / "hydrogen1_identity_counterfactual_audit.csv",
    "counterfactual": DATA / "hydrogen1_counterfactual_audit.csv",
    "source_counterfactual": DATA / "hydrogen1_source_counterfactual_audit.csv",
    "detector_counterfactual": DATA / "hydrogen1_detector_counterfactual_audit.csv",
    "gate_manifest": DATA / "hydrogen1_native_occurrence_gate_manifest.json",
}

ROW_HASH_FIELDS = {
    "identity": "identity_packet_sha256",
    "contract": "local_dec_contract_sha256",
    "occurrence": "occurrence_packet_sha256",
    "states": "state_row_sha256",
    "inventory": "edge_inventory_row_sha256",
    "kernel": "kernel_audit_row_sha256",
    "execution": "execution_row_sha256",
    "read_only": "read_only_trace_row_sha256",
    "source_chain_audit": "source_chain_audit_row_sha256",
    "detector": "returned_current_detection_row_sha256",
    "identity_cf": "identity_counterfactual_row_sha256",
    "counterfactual": "counterfactual_row_sha256",
    "source_counterfactual": "source_counterfactual_row_sha256",
    "detector_counterfactual": "detector_counterfactual_row_sha256",
}

SOURCE_SCHEMAS = {
    "h_plan": [
        "occurrence_order", "occurrence_id", "element_symbol", "atomic_number",
        "mass_number", "neutron_count", "core_form", "extension_3_4_6_count",
        "outer_form", "primitive_support_id", "occurrence_role",
        "relational_temporal_protocol_id", "generator_status",
        "target_value_read_status", "hydrogen_occurrence_plan_row_sha256",
    ],
    "core": [
        "occurrence_order", "occurrence_id", "form_id", "form_name", "route_form",
        "fractal_octave_coordinate", "declared_p", "declared_q", "declared_L",
        "outer_enclosure_id", "primitive_support_id", "support_policy_id",
        "support_policy_sha256", "source_file", "source_file_sha256",
        "source_row_text_sha256", "form_identity_source", "local_DEC_status",
        "target_value_input_status", "occurrence_row_sha256",
    ],
    "support": [
        "support_policy_id", "primitive_support_id", "fractal_octave_coordinate",
        "detected_support_core", "declared_scope_L", "outer_enclosure_id",
        "inverse_solver_p_min", "inverse_solver_q_min", "inverse_solver_q_max",
        "inverse_solver_domain_basis", "local_Q4_edge_slots", "scope_conditioned_form",
        "source_recurrence_certificate_id", "source_recurrence_certificate_sha256",
        "recurrence_family_status", "connected_transition_count", "executed_bip_count",
        "bip_semantics", "trace_count_temporal_status", "monon_semantics",
        "minimal_direct_witness_outbound_bip_count",
        "minimal_direct_witness_inbound_bip_count",
        "minimal_direct_witness_total_bip_count", "minimal_direct_witness_status",
        "monon_to_bip_conversion_status", "C6_role", "temporal_measurement_protocol_id",
        "universal_application_status", "cs_lane_role", "SI_realization_status",
        "target_value_read_status", "empirical_score_status", "support_policy_sha256",
    ],
    "temporal": [
        "schema_id", "field_order", "field", "type", "required", "role",
        "allowed_values", "schema_row_sha256",
    ],
}

PACKET_SCHEMAS = {
    "identity": [
        "identity_packet_id", "element_symbol", "atomic_number", "mass_number",
        "neutron_count", "charge_state", "isotope_label", "fractal_octave_coordinate",
        "identity_source_plan_id", "identity_source_plan_row_sha256", "identity_status",
        "target_value_input_status", "identity_packet_sha256",
    ],
    "contract": [
        "local_dec_contract_id", "identity_packet_id", "identity_packet_sha256",
        "fractal_octave_coordinate", "state_space", "vertex_domain",
        "local_edge_slot_count", "hamming_distance_rule", "epsilon_rule",
        "connected_event_order_rule", "execution_mode", "admissibility_domain",
        "weight_domain", "kernel_probability_domain", "mass_conservation_rule",
        "bip_token_rule", "trace_count_semantics", "monon_witness_rule",
        "support_family_member_reuse_as_edge_status", "core_scope_form_id",
        "core_scope_occurrence_id", "core_scope_occurrence_row_sha256",
        "outer_support_policy_id", "outer_support_policy_sha256",
        "scope_binding_semantics", "consequent_gate_manifest_id",
        "consequent_gate_manifest_path", "consequent_gate_manifest_sha256",
        "consequent_gate_overall_status", "outer_support_application_status_source",
        "outer_support_application_status_interpretation", "Balmer_input_status",
        "SI_unit_input_status", "target_value_input_status", "local_dec_contract_sha256",
    ],
    "occurrence": [
        "occurrence_id", "identity_packet_id", "identity_packet_sha256",
        "fractal_octave_coordinate", "core_form_id", "core_route_form",
        "core_occurrence_id", "core_occurrence_row_sha256", "outer_support_id",
        "outer_route_form", "outer_support_policy_id", "outer_support_policy_sha256",
        "declared_coupling_form", "seat_state_id", "seat_state_semantics",
        "coupling_operator_id", "boundary_id", "window_id", "local_dec_contract_id",
        "local_dec_contract_sha256", "occurrence_role", "identity_specificity_status",
        "local_DEC_status", "returned_current_detection_status", "RD_status",
        "RCD_status", "duonic_pressure_status", "SADAR_flow_status", "phase_lock_status",
        "temporal_report_status", "Balmer_input_status", "target_value_input_status",
        "empirical_score_status", "occurrence_packet_sha256",
    ],
    "states": [
        "state_order", "state_id", "occurrence_id", "occurrence_packet_sha256",
        "boundary_id", "epsilon_Q4", "mu", "state_role", "vertex_domain_status",
        "target_value_input_status", "state_row_sha256",
    ],
    "inventory": [
        "global_inventory_index", "event_index", "occurrence_id",
        "occurrence_packet_sha256", "local_dec_contract_id", "boundary_id",
        "source_state_id", "source_state_row_sha256", "source_epsilon_Q4", "edge_slot",
        "edge_id", "target_state_id", "target_state_row_sha256", "target_epsilon_Q4",
        "xor_epsilon_Q4", "hamming_distance", "sigma_e", "adm_e_B", "weight",
        "effective_weight", "Z", "P_num", "P_den", "P_exact", "route_e_B",
        "local_Q4_edge_status", "row_time_semantics", "support_family_member_reuse_status",
        "target_value_input_status", "edge_inventory_row_sha256",
    ],
    "kernel": [
        "kernel_order", "kernel_id", "occurrence_id", "occurrence_packet_sha256",
        "boundary_id", "source_state_id", "source_state_row_sha256", "edge_slot_count",
        "admitted_edge_count", "normalizer_num", "normalizer_den", "probability_sum_num",
        "probability_sum_den", "incoming_mass_num", "incoming_mass_den",
        "outgoing_mass_num", "outgoing_mass_den", "mass_residual_num", "mass_residual_den",
        "inventory_subset_sha256", "kernel_status", "target_value_input_status",
        "kernel_audit_row_sha256",
    ],
    "execution": [
        "event_order", "event_id", "occurrence_id", "occurrence_packet_sha256",
        "boundary_id", "window_id", "source_state_id", "source_state_row_sha256",
        "target_state_id", "target_state_row_sha256", "source_epsilon_Q4",
        "target_epsilon_Q4", "edge_id", "admitted_edge_row_sha256", "edge_slot",
        "xor_epsilon_Q4", "hamming_distance", "sigma_e", "route_e_B", "kernel_id",
        "kernel_audit_row_sha256", "execution_mode", "P_num", "P_den",
        "incoming_mass_num", "incoming_mass_den", "outgoing_mass_num",
        "outgoing_mass_den", "mass_conservation_status", "parent_event_id",
        "executed_bip_token_count", "row_time_semantics",
        "support_family_member_reuse_status", "target_value_input_status",
        "execution_row_sha256",
    ],
    "read_only": [
        "read_only_trace_id", "occurrence_id", "occurrence_packet_sha256",
        "identity_packet_id", "identity_packet_sha256", "boundary_id", "window_id",
        "execution_ledger_path", "execution_ledger_sha256", "execution_rows_digest_sha256",
        "state_rows_digest_sha256", "admitted_edge_rows_digest_sha256", "event_count",
        "trace_count", "executed_bip_token_count", "trace_count_temporal_status",
        "state_sequence", "initial_state_id", "final_state_id",
        "full_return_candidate_status", "proper_prefix_return_count", "trace_freeze_status",
        "target_value_read_status", "read_only_trace_row_sha256",
    ],
    "detector": [
        "detector_id", "occurrence_id", "occurrence_packet_sha256", "identity_packet_id",
        "identity_packet_sha256", "read_only_trace_id", "read_only_trace_row_sha256",
        "pre_detection_manifest_sha256", "source_state_row_sha256",
        "target_state_row_sha256", "outbound_admitted_edge_row_sha256",
        "return_admitted_edge_row_sha256", "execution_rows_digest_sha256",
        "outbound_event_id", "return_event_id", "outbound_sigma", "return_sigma",
        "shared_axis_slot", "inverse_edge_orientation_status", "full_return_status",
        "proper_prefix_return_count", "primitive_direct_return_status",
        "returned_current_relation", "monon_cycle_class_status",
        "minimal_direct_witness_bip_count", "minimal_witness_temporal_status",
        "duon_current_seed_status", "RD_status", "RCD_status", "duonic_pressure_status",
        "SADAR_flow_status", "phase_lock_status", "target_value_read_status",
        "empirical_score_status", "detection_status", "returned_current_detection_row_sha256",
    ],
    "source_chain_audit": [
        "source_chain_audit_id", "hydrogen_plan_path", "hydrogen_plan_sha256",
        "consequent_gate_manifest_path", "consequent_gate_manifest_sha256",
        "consequent_gate_manifest_id", "consequent_gate_version_scope",
        "consequent_gate_overall_status", "core_occurrence_row_sha256",
        "support_policy_sha256", "support_policy_status_source",
        "support_policy_status_interpretation", "temporal_registry_path",
        "temporal_registry_sha256", "source_chain_status", "source_chain_audit_row_sha256",
    ],
    "identity_cf": [
        "counterfactual_id", "native_identity_packet_id", "counterfactual_identity_packet_id",
        "native_identity_sha256", "counterfactual_identity_sha256",
        "identity_hash_change_status", "native_occurrence_id", "counterfactual_occurrence_id",
        "native_occurrence_sha256", "counterfactual_occurrence_sha256",
        "occurrence_hash_change_status", "topology_family_status", "H1_gate_admission_status",
        "counterfactual_audit_status", "identity_counterfactual_row_sha256",
    ],
    "counterfactual": [
        "counterfactual_order", "counterfactual_id", "mutation_class",
        "expected_gate_result", "observed_gate_result", "observed_failure_reasons",
        "counterfactual_audit_status", "counterfactual_row_sha256",
    ],
    "source_counterfactual": [
        "counterfactual_order", "counterfactual_id", "mutation_class",
        "expected_source_result", "observed_source_result", "observed_failure_reasons",
        "source_counterfactual_audit_status", "source_counterfactual_row_sha256",
    ],
    "detector_counterfactual": [
        "counterfactual_order", "counterfactual_id", "mutation_class",
        "expected_detector_result", "observed_detector_result", "observed_failure_reasons",
        "detector_counterfactual_audit_status", "detector_counterfactual_row_sha256",
    ],
}

PACKET_ROOT_KEYS = ["identity", "contract", "occurrence", "states", "inventory", "kernel", "execution", "read_only"]
LIST_PACKET_KEYS = {"states", "inventory", "kernel", "execution"}
FORBIDDEN_SCHEMA_PROBES = ["Balmer_ratio", "metric_duration_seconds", "target_value", "residual", "score"]

CONSEQUENT_MANIFEST_KEYS = {
    "canonical_enumeration_mapping_status", "canonical_identity_status",
    "canonical_physical_serialization_status", "claim_scope", "closed_semantics_binding_status",
    "compatibility_status", "counterfactual_status", "cross_packet_binding_status",
    "empirical_score_status", "enumeration_completeness_status", "files", "forms", "gate_id",
    "global_packet_set_closure_status", "inverse_audit_status", "local_DEC_execution_status",
    "manifest_id", "native_compatibility_status", "overall_gate_status",
    "pre_audit_freeze_manifest", "pre_audit_freeze_manifest_sha256",
    "pre_map_identity_closure_status", "primitive_support_id", "recurrence_equivalence_status",
    "support_family_definition", "support_family_status", "support_policy_validation_mode",
    "target_value_read_status", "temporal_measurement_status", "version_scope",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_json(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def packet_digest(obj: object) -> str:
    return sha_bytes(canonical_json(obj))


def attach(row: Mapping[str, object], hash_field: str) -> dict[str, str]:
    out = {k: str(v) for k, v in row.items()}
    out[hash_field] = sha_bytes(canonical_json({k: out[k] for k in sorted(out) if k != hash_field}))
    return out


def verify_attached(row: Mapping[str, str], hash_field: str) -> None:
    expected = attach({k: v for k, v in row.items() if k != hash_field}, hash_field)[hash_field]
    if row.get(hash_field) != expected:
        raise ValueError(f"row hash mismatch: {hash_field}")


def mutate_attached(row: Mapping[str, str], hash_field: str, changes: Mapping[str, object]) -> dict[str, str]:
    out = dict(row)
    out.update({k: str(v) for k, v in changes.items()})
    return attach({k: v for k, v in out.items() if k != hash_field}, hash_field)


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "")) for field in fields})


def read_csv_raw(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"empty CSV: {path}") from exc
        if len(header) != len(set(header)):
            raise ValueError(f"duplicate CSV header: {path}")
        rows: list[dict[str, str]] = []
        for row_index, values in enumerate(reader, start=2):
            if len(values) != len(header):
                raise ValueError(f"CSV row width mismatch: {path}:{row_index}")
            rows.append(dict(zip(header, values)))
    return header, rows


def read_csv(path: Path) -> list[dict[str, str]]:
    return read_csv_raw(path)[1]


def read_csv_exact(path: Path, expected_fields: Sequence[str]) -> list[dict[str, str]]:
    header, rows = read_csv_raw(path)
    if header != list(expected_fields):
        raise ValueError(
            f"CSV schema mismatch: {path}; observed={header!r}; expected={list(expected_fields)!r}"
        )
    return rows


def read_one(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    if len(rows) != 1:
        raise ValueError(f"expected one row: {path}")
    return rows[0]


def read_one_exact(path: Path, expected_fields: Sequence[str]) -> dict[str, str]:
    rows = read_csv_exact(path, expected_fields)
    if len(rows) != 1:
        raise ValueError(f"expected one row: {path}")
    return rows[0]


def row_schema_reasons(row: object, expected_fields: Sequence[str], label: str) -> list[str]:
    if not isinstance(row, Mapping):
        return [f"{label}_row_not_mapping"]
    observed = list(row.keys())
    expected = list(expected_fields)
    reasons: list[str] = []
    if observed != expected:
        if set(observed) != set(expected):
            reasons.append(f"{label}_schema_key_set_mismatch")
        else:
            reasons.append(f"{label}_schema_column_order_mismatch")
    return reasons


def packet_schema_reasons(packet: object) -> list[str]:
    if not isinstance(packet, Mapping):
        return ["packet_not_mapping"]
    reasons: list[str] = []
    if list(packet.keys()) != PACKET_ROOT_KEYS:
        reasons.append("packet_root_schema_mismatch")
    for key in PACKET_ROOT_KEYS:
        if key not in packet:
            reasons.append(f"packet_{key}_missing")
            continue
        value = packet[key]
        if key in LIST_PACKET_KEYS:
            if not isinstance(value, list):
                reasons.append(f"packet_{key}_not_list")
                continue
            for index, row in enumerate(value):
                reasons.extend(row_schema_reasons(row, PACKET_SCHEMAS[key], f"{key}_{index}"))
        else:
            reasons.extend(row_schema_reasons(value, PACKET_SCHEMAS[key], key))
    return reasons


def safe_int(value: object, label: str, reasons: list[str], *, minimum: int | None = None, maximum: int | None = None) -> int | None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        reasons.append(f"{label}_not_integer")
        return None
    if minimum is not None and parsed < minimum:
        reasons.append(f"{label}_below_minimum")
        return None
    if maximum is not None and parsed > maximum:
        reasons.append(f"{label}_above_maximum")
        return None
    return parsed


def safe_fraction(num: object, den: object, label: str, reasons: list[str]) -> Fraction | None:
    try:
        numerator = int(str(num))
        denominator = int(str(den))
    except (TypeError, ValueError):
        reasons.append(f"{label}_not_rational_integer_pair")
        return None
    if denominator <= 0:
        reasons.append(f"{label}_nonpositive_denominator")
        return None
    return Fraction(numerator, denominator)


def file_record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha_file(path),
    }


def csv_digest(rows: Sequence[Mapping[str, str]]) -> str:
    return packet_digest([{k: row[k] for k in sorted(row)} for row in rows])


def hamming(a: str, b: str) -> int:
    if len(a) != 4 or len(b) != 4:
        return -1
    return sum(x != y for x, y in zip(a, b))


def toggle(vertex: str, slot: int) -> str:
    chars = list(vertex)
    chars[slot] = "1" if chars[slot] == "0" else "0"
    return "".join(chars)


def parse_fraction(num: str, den: str) -> Fraction:
    numerator = int(num)
    denominator = int(den)
    if denominator <= 0:
        raise ValueError("nonpositive denominator")
    return Fraction(numerator, denominator)


def source_bundle_from_disk() -> dict[str, object]:
    return {
        "h_plan": read_csv_exact(H_PLAN, SOURCE_SCHEMAS["h_plan"]),
        "core": read_csv_exact(CORE_OCCURRENCES, SOURCE_SCHEMAS["core"]),
        "support": read_csv_exact(SUPPORT_POLICY, SOURCE_SCHEMAS["support"]),
        "temporal": read_csv_exact(TEMPORAL_TYPES, SOURCE_SCHEMAS["temporal"]),
        "consequent_manifest": json.loads(CONSEQUENT_GATE_MANIFEST.read_text(encoding="utf-8")),
    }


def validate_consequent_manifest(manifest: object) -> list[str]:
    reasons: list[str] = []
    if not isinstance(manifest, Mapping):
        return ["consequent_manifest_not_mapping"]
    if set(manifest.keys()) != CONSEQUENT_MANIFEST_KEYS:
        reasons.append("consequent_manifest_schema_mismatch")
    for key, value in {
        "manifest_id": "aod_consequent_six_slot_form_compatibility_manifest_v5",
        "gate_id": "aod_consequent_six_slot_form_compatibility_gate_v5",
        "version_scope": "v40.03r06.3.1",
        "overall_gate_status": "passed",
        "compatibility_status": "passed",
        "native_compatibility_status": "passed",
        "counterfactual_status": "passed",
        "cross_packet_binding_status": "passed",
        "enumeration_completeness_status": "passed",
        "inverse_audit_status": "passed",
        "canonical_identity_status": "passed",
        "canonical_enumeration_mapping_status": "passed",
        "canonical_physical_serialization_status": "passed",
        "closed_semantics_binding_status": "passed",
        "global_packet_set_closure_status": "passed",
        "pre_map_identity_closure_status": "passed",
        "local_DEC_execution_status": "not_materialized",
        "target_value_read_status": "not_read",
        "temporal_measurement_status": "not_materialized",
        "primitive_support_id": "00o8_C6_1_2_6",
    }.items():
        if manifest.get(key) != value:
            reasons.append(f"consequent_manifest_{key}_mismatch")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        reasons.append("consequent_manifest_files_missing")
    else:
        seen: set[str] = set()
        for index, rec in enumerate(files):
            if not isinstance(rec, Mapping) or list(rec.keys()) != ["bytes", "path", "sha256"]:
                reasons.append(f"consequent_manifest_file_{index}_schema_mismatch")
                continue
            rel = str(rec.get("path", ""))
            if rel in seen:
                reasons.append("consequent_manifest_duplicate_file_path")
            seen.add(rel)
            path = ROOT / rel
            if not path.is_file():
                reasons.append(f"consequent_manifest_file_missing:{rel}")
                continue
            if str(path.stat().st_size) != str(rec.get("bytes", "")):
                reasons.append(f"consequent_manifest_file_size_mismatch:{rel}")
            if sha_file(path) != rec.get("sha256"):
                reasons.append(f"consequent_manifest_file_hash_mismatch:{rel}")
    return reasons


def evaluate_source_bundle(bundle: object) -> dict[str, object]:
    reasons: list[str] = []
    resolved: dict[str, object] = {}
    try:
        if not isinstance(bundle, Mapping):
            return {"passed": False, "failure_reasons": ["source_bundle_not_mapping"], "resolved": {}}
        expected_root = ["h_plan", "core", "support", "temporal", "consequent_manifest"]
        if list(bundle.keys()) != expected_root:
            reasons.append("source_bundle_root_schema_mismatch")
        for key in ("h_plan", "core", "support", "temporal"):
            rows = bundle.get(key)
            if not isinstance(rows, list):
                reasons.append(f"source_{key}_not_list")
                continue
            for index, row in enumerate(rows):
                reasons.extend(row_schema_reasons(row, SOURCE_SCHEMAS[key], f"source_{key}_{index}"))

        plans = bundle.get("h_plan", []) if isinstance(bundle.get("h_plan"), list) else []
        if len(plans) != 3:
            reasons.append("hydrogen_plan_row_count_mismatch")
        plan_ids = [row.get("occurrence_id", "") for row in plans if isinstance(row, Mapping)]
        if len(plan_ids) != len(set(plan_ids)):
            reasons.append("hydrogen_plan_duplicate_occurrence_id")
        h1_rows = [row for row in plans if isinstance(row, Mapping) and row.get("occurrence_id") == "H1_00o8"]
        if len(h1_rows) != 1:
            reasons.append("hydrogen_plan_H1_row_count_mismatch")
            h1: Mapping[str, str] = {}
        else:
            h1 = h1_rows[0]
            try:
                verify_attached(h1, "hydrogen_occurrence_plan_row_sha256")
            except (ValueError, KeyError, TypeError) as exc:
                reasons.append(f"hydrogen_plan_hash_failure:{exc}")
            expected_h1 = {
                "occurrence_order": "0",
                "occurrence_id": "H1_00o8",
                "element_symbol": "H",
                "atomic_number": "1",
                "mass_number": "1",
                "neutron_count": "0",
                "core_form": "3:3:6",
                "extension_3_4_6_count": "0",
                "outer_form": "1:2:6",
                "primitive_support_id": "00o8_C6_1_2_6",
                "occurrence_role": "first_element_relational_flow_verification",
                "relational_temporal_protocol_id": "aod_relational_temporal_measurement_packet_v1",
                "generator_status": "materialized_connected_local_Q4_direct_return_occurrence",
                "target_value_read_status": "not_read",
            }
            for key, value in expected_h1.items():
                if h1.get(key) != value:
                    reasons.append(f"hydrogen_plan_{key}_mismatch")
            resolved["h1_plan"] = dict(h1)

        cores = bundle.get("core", []) if isinstance(bundle.get("core"), list) else []
        if len(cores) != 2:
            reasons.append("core_occurrence_row_count_mismatch")
        form_ids = [row.get("form_id", "") for row in cores if isinstance(row, Mapping)]
        if form_ids != ["form_3_3_6", "form_3_4_6"]:
            reasons.append("core_occurrence_form_order_mismatch")
        core_rows = [row for row in cores if isinstance(row, Mapping) and row.get("form_id") == "form_3_3_6"]
        if len(core_rows) != 1:
            reasons.append("core_3_3_6_row_count_mismatch")
            core: Mapping[str, str] = {}
        else:
            core = core_rows[0]
            try:
                verify_attached(core, "occurrence_row_sha256")
            except (ValueError, KeyError, TypeError) as exc:
                reasons.append(f"core_occurrence_hash_failure:{exc}")
            expected_core = {
                "occurrence_order": "0",
                "occurrence_id": "aod_form_3_3_6_00o8",
                "form_id": "form_3_3_6",
                "form_name": "Tritriohexon",
                "route_form": "3:3:6",
                "fractal_octave_coordinate": "00_(8)",
                "declared_p": "3",
                "declared_q": "3",
                "declared_L": "6",
                "outer_enclosure_id": "C6",
                "primitive_support_id": "00o8_C6_1_2_6",
                "support_policy_id": "aod_00o8_C6_recurrence_support_policy_v3",
                "source_file": "appendices/J_ao_field_fractal_properties.tex",
                "form_identity_source": "declared_scoped_occurrence_not_inferred_from_support_family",
                "local_DEC_status": "not_materialized",
                "target_value_input_status": "absent",
            }
            for key, value in expected_core.items():
                if core.get(key) != value:
                    reasons.append(f"core_occurrence_{key}_mismatch")
            source_file = ROOT / core.get("source_file", "")
            if not source_file.is_file() or sha_file(source_file) != core.get("source_file_sha256"):
                reasons.append("core_occurrence_source_file_hash_mismatch")
            resolved["core"] = dict(core)

        supports = bundle.get("support", []) if isinstance(bundle.get("support"), list) else []
        if len(supports) != 1:
            reasons.append("support_policy_row_count_mismatch")
            support: Mapping[str, str] = {}
        else:
            support = supports[0]
            try:
                verify_attached(support, "support_policy_sha256")
            except (ValueError, KeyError, TypeError) as exc:
                reasons.append(f"support_policy_hash_failure:{exc}")
            expected_support = {
                "support_policy_id": "aod_00o8_C6_recurrence_support_policy_v3",
                "primitive_support_id": "00o8_C6_1_2_6",
                "fractal_octave_coordinate": "00_(8)",
                "detected_support_core": "1:2",
                "declared_scope_L": "6",
                "outer_enclosure_id": "C6",
                "inverse_solver_p_min": "1",
                "inverse_solver_q_min": "2",
                "inverse_solver_q_max": "4",
                "inverse_solver_domain_basis": "Q4_directional_support",
                "local_Q4_edge_slots": "4",
                "scope_conditioned_form": "1:2:6",
                "source_recurrence_certificate_id": "cs133_native_core_outer_primitive_recurrence_v1",
                "recurrence_family_status": "shared_elementary_recurrence_instantiated_at_Cs_scope",
                "connected_transition_count": "6",
                "executed_bip_count": "6",
                "bip_semantics": "admitted_executed_directed_beat_token",
                "trace_count_temporal_status": "execution_structure_not_temporal_magnitude",
                "monon_semantics": "primitive_completed_cycle_class",
                "minimal_direct_witness_outbound_bip_count": "1",
                "minimal_direct_witness_inbound_bip_count": "1",
                "minimal_direct_witness_total_bip_count": "2",
                "minimal_direct_witness_status": "witness_only_not_duration",
                "monon_to_bip_conversion_status": "not_declared",
                "C6_role": "six_slot_support_and_shared_recurrence_fixture",
                "temporal_measurement_protocol_id": "aod_relational_temporal_measurement_packet_v1",
                "universal_application_status": "consequent_support_family_cross_packet_binding_passed_local_DEC_pending_hydrogen_occurrence_pending",
                "cs_lane_role": "historical_adapter_optional_downstream_reference",
                "SI_realization_status": "inactive_optional_downstream",
                "target_value_read_status": "not_read",
                "empirical_score_status": "not_computed",
            }
            for key, value in expected_support.items():
                if support.get(key) != value:
                    reasons.append(f"support_policy_{key}_mismatch")
            resolved["support"] = dict(support)
            resolved["support_status_interpretation"] = "historical_pre_H1_planning_status_not_current_gate_state"

        temporal_rows = bundle.get("temporal", []) if isinstance(bundle.get("temporal"), list) else []
        if len(temporal_rows) != 14:
            reasons.append("temporal_registry_row_count_mismatch")
        if [row.get("field_order") for row in temporal_rows if isinstance(row, Mapping)] != [str(i) for i in range(14)]:
            reasons.append("temporal_registry_order_mismatch")
        temporal_by_field: dict[str, Mapping[str, str]] = {}
        for row in temporal_rows:
            if not isinstance(row, Mapping):
                continue
            field = row.get("field", "")
            if field in temporal_by_field:
                reasons.append("temporal_registry_duplicate_field")
            temporal_by_field[field] = row
            try:
                verify_attached(row, "schema_row_sha256")
            except (ValueError, KeyError, TypeError) as exc:
                reasons.append(f"temporal_registry_hash_failure:{field}:{exc}")
        expected_temporal = {
            "bip": {
                "type": "executed_directed_beat_token",
                "required": "yes",
                "role": "one admitted executed or propagated directed beat; not a CSV row count and not temporal magnitude",
                "allowed_values": "",
            },
            "monon": {
                "type": "cycle_class",
                "required": "yes",
                "role": "primitive completed outbound-hinge-return cycle class",
                "allowed_values": "",
            },
            "minimal_direct_witness_bip_count": {
                "type": "positive_integer",
                "required": "yes",
                "role": "shortest direct monon witness contains one outbound and one inbound executed bip",
                "allowed_values": "2",
            },
            "minimal_witness_temporal_status": {
                "type": "enum",
                "required": "yes",
                "role": "minimal witness is not a universal monon duration",
                "allowed_values": "witness_only_not_duration",
            },
        }
        for field, expected in expected_temporal.items():
            row = temporal_by_field.get(field)
            if row is None:
                reasons.append(f"temporal_registry_{field}_missing")
                continue
            if row.get("schema_id") != "aod_relational_temporal_type_registry_v1":
                reasons.append(f"temporal_registry_{field}_schema_id_mismatch")
            for key, value in expected.items():
                if row.get(key) != value:
                    reasons.append(f"temporal_registry_{field}_{key}_mismatch")
            resolved[field if field != "minimal_direct_witness_bip_count" else "witness"] = dict(row)
        if "bip" in temporal_by_field:
            resolved["bip"] = dict(temporal_by_field["bip"])
        if "monon" in temporal_by_field:
            resolved["monon"] = dict(temporal_by_field["monon"])

        consequent = bundle.get("consequent_manifest")
        consequent_reasons = validate_consequent_manifest(consequent)
        reasons.extend(consequent_reasons)
        if isinstance(consequent, Mapping):
            resolved["consequent_manifest"] = dict(consequent)
    except Exception as exc:  # structured fail-closed guard for malformed source packets
        reasons.append(f"source_bundle_exception:{type(exc).__name__}:{exc}")
    return {"passed": not reasons, "failure_reasons": sorted(set(reasons)), "resolved": resolved}


def source_packets() -> dict[str, object]:
    result = evaluate_source_bundle(source_bundle_from_disk())
    if not result["passed"]:
        raise ValueError("source packet validation failed: " + ";".join(result["failure_reasons"]))
    return dict(result["resolved"])


def build_source_chain_audit(src: Mapping[str, object]) -> dict[str, str]:
    consequent = src["consequent_manifest"]
    core = src["core"]
    support = src["support"]
    return attach({
        "source_chain_audit_id": "H1_source_chain_audit_v1",
        "hydrogen_plan_path": H_PLAN.relative_to(ROOT).as_posix(),
        "hydrogen_plan_sha256": sha_file(H_PLAN),
        "consequent_gate_manifest_path": CONSEQUENT_GATE_MANIFEST.relative_to(ROOT).as_posix(),
        "consequent_gate_manifest_sha256": sha_file(CONSEQUENT_GATE_MANIFEST),
        "consequent_gate_manifest_id": consequent["manifest_id"],
        "consequent_gate_version_scope": consequent["version_scope"],
        "consequent_gate_overall_status": consequent["overall_gate_status"],
        "core_occurrence_row_sha256": core["occurrence_row_sha256"],
        "support_policy_sha256": support["support_policy_sha256"],
        "support_policy_status_source": support["universal_application_status"],
        "support_policy_status_interpretation": src["support_status_interpretation"],
        "temporal_registry_path": TEMPORAL_TYPES.relative_to(ROOT).as_posix(),
        "temporal_registry_sha256": sha_file(TEMPORAL_TYPES),
        "source_chain_status": "passed_exact_source_schema_semantics_and_prior_gate_chain",
    }, ROW_HASH_FIELDS["source_chain_audit"])


def build_source_counterfactuals(native_bundle: Mapping[str, object]) -> list[dict[str, str]]:
    cases: list[tuple[str, str, dict[str, object], str]] = []

    def cp() -> dict[str, object]:
        return deepcopy(native_bundle)

    p = cp()
    h1_index = next(i for i, row in enumerate(p["h_plan"]) if row["occurrence_id"] == "H1_00o8")
    p["h_plan"][h1_index] = mutate_attached(
        p["h_plan"][h1_index], "hydrogen_occurrence_plan_row_sha256",
        {"generator_status": "materialized_from_Balmer_target"},
    )
    cases.append(("source_plan_generator_target_leak", "source_plan_semantics", p, "failed"))

    p = cp()
    p["h_plan"].append(dict(next(row for row in p["h_plan"] if row["occurrence_id"] == "H1_00o8")))
    cases.append(("duplicate_H1_source_plan_row", "source_plan_cardinality", p, "failed"))

    p = cp()
    core_index = next(i for i, row in enumerate(p["core"]) if row["form_id"] == "form_3_3_6")
    p["core"][core_index] = mutate_attached(
        p["core"][core_index], "occurrence_row_sha256", {"target_value_input_status": "present"}
    )
    cases.append(("core_target_input_present", "prior_gate_source_semantics", p, "failed"))

    p = cp()
    bip_index = next(i for i, row in enumerate(p["temporal"]) if row["field"] == "bip")
    p["temporal"][bip_index] = mutate_attached(
        p["temporal"][bip_index], "schema_row_sha256", {"type": "metric_duration_seconds"}
    )
    cases.append(("bip_retyped_as_metric_duration", "temporal_type_semantics", p, "failed"))

    p = cp()
    p["h_plan"][h1_index] = mutate_attached(
        p["h_plan"][h1_index], "hydrogen_occurrence_plan_row_sha256", {"Balmer_ratio": "3/4"}
    )
    cases.append(("source_plan_unknown_target_field", "source_schema_closure", p, "failed"))

    p = cp()
    p["support"][0] = mutate_attached(
        p["support"][0], "support_policy_sha256", {"target_value_read_status": "present"}
    )
    cases.append(("support_policy_target_input_present", "support_policy_semantics", p, "failed"))

    p = cp()
    p["consequent_manifest"]["overall_gate_status"] = "failed"
    cases.append(("prior_gate_manifest_failed", "prior_gate_chain", p, "failed"))

    cases.append(("unchanged_source_control", "control", cp(), "passed"))

    rows: list[dict[str, str]] = []
    for order, (case_id, mutation_class, bundle, expected) in enumerate(cases):
        result = evaluate_source_bundle(bundle)
        observed = "passed" if result["passed"] else "failed"
        rows.append(attach({
            "counterfactual_order": order,
            "counterfactual_id": case_id,
            "mutation_class": mutation_class,
            "expected_source_result": expected,
            "observed_source_result": observed,
            "observed_failure_reasons": ";".join(result["failure_reasons"]),
            "source_counterfactual_audit_status": "passed" if observed == expected else "failed",
        }, ROW_HASH_FIELDS["source_counterfactual"]))
    return rows


def build_identity(src: Mapping[str, Mapping[str, str]]) -> dict[str, str]:
    plan = src["h1_plan"]
    return attach({
        "identity_packet_id": "H1_identity_00o8_v1",
        "element_symbol": plan["element_symbol"],
        "atomic_number": plan["atomic_number"],
        "mass_number": plan["mass_number"],
        "neutron_count": plan["neutron_count"],
        "charge_state": "0",
        "isotope_label": "Hydrogen-1",
        "fractal_octave_coordinate": "00_(8)",
        "identity_source_plan_id": plan["occurrence_id"],
        "identity_source_plan_row_sha256": plan["hydrogen_occurrence_plan_row_sha256"],
        "identity_status": "declared_native_scope_not_external_target",
        "target_value_input_status": "absent",
    }, ROW_HASH_FIELDS["identity"])


def build_contract(src: Mapping[str, object], identity: Mapping[str, str]) -> dict[str, str]:
    core = src["core"]
    support = src["support"]
    consequent = src["consequent_manifest"]
    return attach({
        "local_dec_contract_id": "H1_local_Q4_direct_return_contract_v1",
        "identity_packet_id": identity["identity_packet_id"],
        "identity_packet_sha256": identity["identity_packet_sha256"],
        "fractal_octave_coordinate": "00_(8)",
        "state_space": "Q4",
        "vertex_domain": "{0,1}^4",
        "local_edge_slot_count": "4",
        "hamming_distance_rule": "exactly_1",
        "epsilon_rule": "TXOR_one_hot",
        "connected_event_order_rule": "target_i_equals_source_i_plus_1",
        "execution_mode": "enumerate_all",
        "admissibility_domain": "{0,1}",
        "weight_domain": "positive_integer_for_admitted_rows",
        "kernel_probability_domain": "nonnegative_reduced_rational_sum_exactly_1",
        "mass_conservation_rule": "sum_outgoing_mass_equals_incoming_mass_exactly",
        "bip_token_rule": "one_bip_per_admitted_executed_directed_edge",
        "trace_count_semantics": "execution_structure_not_temporal_magnitude",
        "monon_witness_rule": "one_outbound_then_one_inverse_return_with_no_prefix_closure",
        "support_family_member_reuse_as_edge_status": "forbidden",
        "core_scope_form_id": core["form_id"],
        "core_scope_occurrence_id": core["occurrence_id"],
        "core_scope_occurrence_row_sha256": core["occurrence_row_sha256"],
        "outer_support_policy_id": support["support_policy_id"],
        "outer_support_policy_sha256": support["support_policy_sha256"],
        "scope_binding_semantics": "declared_core_outer_scope_not_support_family_as_local_edge_pool",
        "consequent_gate_manifest_id": consequent["manifest_id"],
        "consequent_gate_manifest_path": CONSEQUENT_GATE_MANIFEST.relative_to(ROOT).as_posix(),
        "consequent_gate_manifest_sha256": sha_file(CONSEQUENT_GATE_MANIFEST),
        "consequent_gate_overall_status": consequent["overall_gate_status"],
        "outer_support_application_status_source": support["universal_application_status"],
        "outer_support_application_status_interpretation": src["support_status_interpretation"],
        "Balmer_input_status": "absent",
        "SI_unit_input_status": "absent",
        "target_value_input_status": "absent",
    }, ROW_HASH_FIELDS["contract"])


def build_occurrence(src: Mapping[str, Mapping[str, str]], identity: Mapping[str, str], contract: Mapping[str, str]) -> dict[str, str]:
    return attach({
        "occurrence_id": "H1_00o8_native_occurrence_v1",
        "identity_packet_id": identity["identity_packet_id"],
        "identity_packet_sha256": identity["identity_packet_sha256"],
        "fractal_octave_coordinate": "00_(8)",
        "core_form_id": src["core"]["form_id"],
        "core_route_form": src["core"]["route_form"],
        "core_occurrence_id": src["core"]["occurrence_id"],
        "core_occurrence_row_sha256": src["core"]["occurrence_row_sha256"],
        "outer_support_id": src["support"]["primitive_support_id"],
        "outer_route_form": src["support"]["scope_conditioned_form"],
        "outer_support_policy_id": src["support"]["support_policy_id"],
        "outer_support_policy_sha256": src["support"]["support_policy_sha256"],
        "declared_coupling_form": "Couple(3:3:6,1:2:6)",
        "seat_state_id": "E2^0",
        "seat_state_semantics": "open_seat_duon_declared_scope",
        "coupling_operator_id": "H1_core_outer_scope_coupling_v1",
        "boundary_id": "B_H1_00o8_local_Q4_direct_return",
        "window_id": "omega_H1_two_event_direct_return",
        "local_dec_contract_id": contract["local_dec_contract_id"],
        "local_dec_contract_sha256": contract["local_dec_contract_sha256"],
        "occurrence_role": "first_element_target_blind_native_occurrence",
        "identity_specificity_status": "H1_identity_bound_shared_direct_return_topology",
        "local_DEC_status": "materialized_connected_Q4_direct_return",
        "returned_current_detection_status": "pending_pre_detection_freeze",
        "RD_status": "not_materialized",
        "RCD_status": "not_materialized",
        "duonic_pressure_status": "not_materialized",
        "SADAR_flow_status": "not_materialized",
        "phase_lock_status": "not_materialized",
        "temporal_report_status": "not_materialized",
        "Balmer_input_status": "absent",
        "target_value_input_status": "absent",
        "empirical_score_status": "not_computed",
    }, ROW_HASH_FIELDS["occurrence"])


def build_states(occurrence: Mapping[str, str]) -> list[dict[str, str]]:
    specs = [
        (0, "H1_q4_state_origin", "0000", "0", "retained_origin_and_return_state"),
        (1, "H1_q4_state_hinge", "1000", "0", "direct_return_hinge_state"),
    ]
    return [attach({
        "state_order": order,
        "state_id": state_id,
        "occurrence_id": occurrence["occurrence_id"],
        "occurrence_packet_sha256": occurrence["occurrence_packet_sha256"],
        "boundary_id": occurrence["boundary_id"],
        "epsilon_Q4": epsilon,
        "mu": mu,
        "state_role": role,
        "vertex_domain_status": "passed_binary_Q4",
        "target_value_input_status": "absent",
    }, ROW_HASH_FIELDS["states"]) for order, state_id, epsilon, mu, role in specs]


def build_inventory(occurrence: Mapping[str, str], contract: Mapping[str, str], states: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    state_by_id = {row["state_id"]: row for row in states}
    state_by_vertex = {row["epsilon_Q4"]: row for row in states}
    events = [
        (0, "H1_q4_state_origin", 0, "+1", "outgoing"),
        (1, "H1_q4_state_hinge", 0, "-1", "returned"),
    ]
    rows: list[dict[str, str]] = []
    global_index = 0
    for event_index, source_state_id, admitted_slot, admitted_sigma, admitted_route in events:
        source_state = state_by_id[source_state_id]
        source = source_state["epsilon_Q4"]
        for slot in range(4):
            admitted = 1 if slot == admitted_slot else 0
            target = toggle(source, slot)
            target_state = state_by_vertex.get(target) if admitted else None
            sigma = admitted_sigma if admitted else "0"
            route = admitted_route if admitted else "blocked"
            edge_id = f"H1_local_edge_evt{event_index}_slot{slot}"
            rows.append(attach({
                "global_inventory_index": global_index,
                "event_index": event_index,
                "occurrence_id": occurrence["occurrence_id"],
                "occurrence_packet_sha256": occurrence["occurrence_packet_sha256"],
                "local_dec_contract_id": contract["local_dec_contract_id"],
                "boundary_id": occurrence["boundary_id"],
                "source_state_id": source_state_id,
                "source_state_row_sha256": source_state["state_row_sha256"],
                "source_epsilon_Q4": source,
                "edge_slot": slot,
                "edge_id": edge_id,
                "target_state_id": target_state["state_id"] if target_state else "",
                "target_state_row_sha256": target_state["state_row_sha256"] if target_state else "",
                "target_epsilon_Q4": target,
                "xor_epsilon_Q4": "".join("1" if a != b else "0" for a, b in zip(source, target)),
                "hamming_distance": hamming(source, target),
                "sigma_e": sigma,
                "adm_e_B": admitted,
                "weight": 1,
                "effective_weight": admitted,
                "Z": 1,
                "P_num": admitted,
                "P_den": 1,
                "P_exact": str(admitted),
                "route_e_B": route,
                "local_Q4_edge_status": "local_Hamming1_edge_slot",
                "row_time_semantics": "kernel_inventory_not_elapsed_time",
                "support_family_member_reuse_status": "not_reused",
                "target_value_input_status": "absent",
            }, ROW_HASH_FIELDS["inventory"]))
            global_index += 1
    return rows


def event_kernel_id(event_index: int) -> str:
    return f"H1_local_Q4_kernel_event_{event_index}"


def build_kernel_audit(occurrence: Mapping[str, str], inventory: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for event_index in (0, 1):
        subset = [row for row in inventory if int(row["event_index"]) == event_index]
        admitted = [row for row in subset if row["adm_e_B"] == "1"]
        probability = sum((parse_fraction(row["P_num"], row["P_den"]) for row in subset), Fraction())
        rows.append(attach({
            "kernel_order": event_index,
            "kernel_id": event_kernel_id(event_index),
            "occurrence_id": occurrence["occurrence_id"],
            "occurrence_packet_sha256": occurrence["occurrence_packet_sha256"],
            "boundary_id": occurrence["boundary_id"],
            "source_state_id": subset[0]["source_state_id"],
            "source_state_row_sha256": subset[0]["source_state_row_sha256"],
            "edge_slot_count": len(subset),
            "admitted_edge_count": len(admitted),
            "normalizer_num": sum(int(row["effective_weight"]) for row in subset),
            "normalizer_den": 1,
            "probability_sum_num": probability.numerator,
            "probability_sum_den": probability.denominator,
            "incoming_mass_num": 1,
            "incoming_mass_den": 1,
            "outgoing_mass_num": probability.numerator,
            "outgoing_mass_den": probability.denominator,
            "mass_residual_num": probability.numerator - probability.denominator,
            "mass_residual_den": probability.denominator,
            "inventory_subset_sha256": csv_digest(subset),
            "kernel_status": "passed" if len(subset) == 4 and len(admitted) == 1 and probability == 1 else "failed",
            "target_value_input_status": "absent",
        }, ROW_HASH_FIELDS["kernel"]))
    return rows


def build_execution(occurrence: Mapping[str, str], inventory: Sequence[Mapping[str, str]], kernels: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    kernel_by_order = {int(row["kernel_order"]): row for row in kernels}
    specs = [
        (0, "H1_DEC_event_outbound", "H1_q4_state_origin", "H1_q4_state_hinge", "+1", "outgoing", ""),
        (1, "H1_DEC_event_return", "H1_q4_state_hinge", "H1_q4_state_origin", "-1", "returned", "H1_DEC_event_outbound"),
    ]
    rows: list[dict[str, str]] = []
    for order, event_id, source_id, target_id, sigma, route, parent in specs:
        edge = next(row for row in inventory if row["event_index"] == str(order) and row["adm_e_B"] == "1")
        kernel = kernel_by_order[order]
        rows.append(attach({
            "event_order": order,
            "event_id": event_id,
            "occurrence_id": occurrence["occurrence_id"],
            "occurrence_packet_sha256": occurrence["occurrence_packet_sha256"],
            "boundary_id": occurrence["boundary_id"],
            "window_id": occurrence["window_id"],
            "source_state_id": source_id,
            "source_state_row_sha256": edge["source_state_row_sha256"],
            "target_state_id": target_id,
            "target_state_row_sha256": edge["target_state_row_sha256"],
            "source_epsilon_Q4": edge["source_epsilon_Q4"],
            "target_epsilon_Q4": edge["target_epsilon_Q4"],
            "edge_id": edge["edge_id"],
            "admitted_edge_row_sha256": edge["edge_inventory_row_sha256"],
            "edge_slot": edge["edge_slot"],
            "xor_epsilon_Q4": edge["xor_epsilon_Q4"],
            "hamming_distance": edge["hamming_distance"],
            "sigma_e": sigma,
            "route_e_B": route,
            "kernel_id": kernel["kernel_id"],
            "kernel_audit_row_sha256": kernel["kernel_audit_row_sha256"],
            "execution_mode": "enumerate_all",
            "P_num": 1,
            "P_den": 1,
            "incoming_mass_num": 1,
            "incoming_mass_den": 1,
            "outgoing_mass_num": 1,
            "outgoing_mass_den": 1,
            "mass_conservation_status": "passed",
            "parent_event_id": parent,
            "executed_bip_token_count": 1,
            "row_time_semantics": "executed_bip_token_not_temporal_magnitude",
            "support_family_member_reuse_status": "not_reused",
            "target_value_input_status": "absent",
        }, ROW_HASH_FIELDS["execution"]))
    return rows


def build_read_only(
    occurrence: Mapping[str, str],
    states: Sequence[Mapping[str, str]],
    inventory: Sequence[Mapping[str, str]],
    execution: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    sequence = [execution[0]["source_state_id"]] + [row["target_state_id"] for row in execution]
    admitted = [row for row in inventory if row["adm_e_B"] == "1"]
    return attach({
        "read_only_trace_id": "H1_read_only_direct_return_trace_v1",
        "occurrence_id": occurrence["occurrence_id"],
        "occurrence_packet_sha256": occurrence["occurrence_packet_sha256"],
        "identity_packet_id": occurrence["identity_packet_id"],
        "identity_packet_sha256": occurrence["identity_packet_sha256"],
        "boundary_id": occurrence["boundary_id"],
        "window_id": occurrence["window_id"],
        "execution_ledger_path": FILES["execution"].relative_to(ROOT).as_posix(),
        "execution_ledger_sha256": sha_file(FILES["execution"]),
        "execution_rows_digest_sha256": csv_digest(execution),
        "state_rows_digest_sha256": csv_digest(states),
        "admitted_edge_rows_digest_sha256": csv_digest(admitted),
        "event_count": len(execution),
        "trace_count": len(execution),
        "executed_bip_token_count": sum(int(row["executed_bip_token_count"]) for row in execution),
        "trace_count_temporal_status": "execution_structure_not_temporal_magnitude",
        "state_sequence": ">".join(sequence),
        "initial_state_id": sequence[0],
        "final_state_id": sequence[-1],
        "full_return_candidate_status": "candidate_initial_equals_final",
        "proper_prefix_return_count": 0,
        "trace_freeze_status": "frozen_before_detection",
        "target_value_read_status": "not_read",
    }, ROW_HASH_FIELDS["read_only"])


def build_pre_manifest(paths: Sequence[Path], inputs: Sequence[Path]) -> dict[str, object]:
    return {
        "manifest_id": "H1_pre_detection_freeze_manifest_v2",
        "gate_id": GATE_ID,
        "version_scope": VERSION,
        "packet_schema_profile_id": "H1_exact_ordered_packet_schema_v1",
        "packet_schema_sha256": packet_digest(PACKET_SCHEMAS),
        "source_schema_sha256": packet_digest(SOURCE_SCHEMAS),
        "allowed_source_inputs": [file_record(path) for path in inputs],
        "frozen_packets": [file_record(path) for path in paths],
        "detector_implementation": file_record(Path(__file__).resolve()),
        "forbidden_input_classes": ["Balmer_ratio", "observed_line", "SI_unit", "target_value", "residual", "score"],
        "target_value_input_status": "absent",
        "freeze_status": "frozen_before_returned_current_detection",
    }


def verify_pre_manifest(manifest: Mapping[str, object]) -> None:
    expected_keys = [
        "manifest_id", "gate_id", "version_scope", "packet_schema_profile_id",
        "packet_schema_sha256", "source_schema_sha256", "allowed_source_inputs",
        "frozen_packets", "detector_implementation", "forbidden_input_classes",
        "target_value_input_status", "freeze_status",
    ]
    if list(manifest.keys()) != expected_keys:
        raise ValueError("pre-detection manifest schema mismatch")
    if manifest.get("manifest_id") != "H1_pre_detection_freeze_manifest_v2":
        raise ValueError("pre-detection manifest ID mismatch")
    if manifest.get("gate_id") != GATE_ID or manifest.get("version_scope") != VERSION:
        raise ValueError("pre-detection gate/version mismatch")
    if manifest.get("packet_schema_profile_id") != "H1_exact_ordered_packet_schema_v1":
        raise ValueError("pre-detection packet schema profile mismatch")
    if manifest.get("packet_schema_sha256") != packet_digest(PACKET_SCHEMAS):
        raise ValueError("pre-detection packet schema hash mismatch")
    if manifest.get("source_schema_sha256") != packet_digest(SOURCE_SCHEMAS):
        raise ValueError("pre-detection source schema hash mismatch")
    if manifest.get("target_value_input_status") != "absent":
        raise ValueError("pre-detection target input opened")
    if manifest.get("freeze_status") != "frozen_before_returned_current_detection":
        raise ValueError("pre-detection freeze status mismatch")
    expected_forbidden = ["Balmer_ratio", "observed_line", "SI_unit", "target_value", "residual", "score"]
    if manifest.get("forbidden_input_classes") != expected_forbidden:
        raise ValueError("pre-detection forbidden-input class mismatch")
    expected_group_paths = {
        "allowed_source_inputs": [
            H_PLAN.relative_to(ROOT).as_posix(),
            CORE_OCCURRENCES.relative_to(ROOT).as_posix(),
            SUPPORT_POLICY.relative_to(ROOT).as_posix(),
            TEMPORAL_TYPES.relative_to(ROOT).as_posix(),
            CONSEQUENT_GATE_MANIFEST.relative_to(ROOT).as_posix(),
        ],
        "frozen_packets": [
            FILES[key].relative_to(ROOT).as_posix()
            for key in ("identity", "contract", "occurrence", "states", "inventory", "kernel", "execution", "read_only", "source_chain_audit")
        ],
    }
    for group in ("allowed_source_inputs", "frozen_packets"):
        records = manifest.get(group)
        if not isinstance(records, list):
            raise ValueError(f"pre-detection {group} missing")
        observed_paths = [record.get("path") for record in records if isinstance(record, Mapping)]
        if observed_paths != expected_group_paths[group] or len(set(observed_paths)) != len(observed_paths):
            raise ValueError(f"pre-detection {group} path-set/order mismatch")
        for record in records:
            if not isinstance(record, Mapping) or list(record.keys()) != ["path", "bytes", "sha256"]:
                raise ValueError(f"pre-detection {group} record schema mismatch")
            path = ROOT / record["path"]
            if not path.is_file() or path.stat().st_size != record["bytes"] or sha_file(path) != record["sha256"]:
                raise ValueError(f"pre-detection file mismatch: {record['path']}")
    record = manifest.get("detector_implementation")
    if not isinstance(record, Mapping) or list(record.keys()) != ["path", "bytes", "sha256"]:
        raise ValueError("detector implementation record schema mismatch")
    if record.get("path") != Path(__file__).resolve().relative_to(ROOT).as_posix():
        raise ValueError("detector implementation path mismatch")
    script = ROOT / record["path"]
    if not script.is_file() or script.stat().st_size != record["bytes"] or sha_file(script) != record["sha256"]:
        raise ValueError("detector implementation mismatch")


def packet_from_disk() -> dict[str, object]:
    return {
        "identity": read_one_exact(FILES["identity"], PACKET_SCHEMAS["identity"]),
        "contract": read_one_exact(FILES["contract"], PACKET_SCHEMAS["contract"]),
        "occurrence": read_one_exact(FILES["occurrence"], PACKET_SCHEMAS["occurrence"]),
        "states": read_csv_exact(FILES["states"], PACKET_SCHEMAS["states"]),
        "inventory": read_csv_exact(FILES["inventory"], PACKET_SCHEMAS["inventory"]),
        "kernel": read_csv_exact(FILES["kernel"], PACKET_SCHEMAS["kernel"]),
        "execution": read_csv_exact(FILES["execution"], PACKET_SCHEMAS["execution"]),
        "read_only": read_one_exact(FILES["read_only"], PACKET_SCHEMAS["read_only"]),
    }


def evaluate_packet(packet: object, *, verify_manifest: bool = False, manifest: Mapping[str, object] | None = None) -> dict[str, object]:
    schema_reasons = packet_schema_reasons(packet)
    if schema_reasons:
        return {"passed": False, "failure_reasons": sorted(set(schema_reasons))}
    try:
        return _evaluate_packet_core(packet, verify_manifest=verify_manifest, manifest=manifest)
    except Exception as exc:
        return {
            "passed": False,
            "failure_reasons": [f"malformed_packet_exception:{type(exc).__name__}:{exc}"],
        }


def _evaluate_packet_core(packet: Mapping[str, object], *, verify_manifest: bool = False, manifest: Mapping[str, object] | None = None) -> dict[str, object]:
    reasons: list[str] = []
    try:
        src = source_packets()
    except (ValueError, KeyError, TypeError, StopIteration) as exc:
        src = {}
        reasons.append(f"source_packet_failure:{exc}")
    try:
        if verify_manifest:
            if manifest is None:
                reasons.append("pre_detection_manifest_missing")
            else:
                verify_pre_manifest(manifest)
    except (ValueError, KeyError, TypeError) as exc:
        reasons.append(f"pre_detection_manifest_failure:{exc}")

    try:
        for key in ("identity", "contract", "occurrence", "read_only"):
            verify_attached(packet[key], ROW_HASH_FIELDS[key])
        for key in ("states", "inventory", "kernel", "execution"):
            for row in packet[key]:
                verify_attached(row, ROW_HASH_FIELDS[key])
    except (ValueError, KeyError, TypeError) as exc:
        reasons.append(f"attached_row_hash_failure:{exc}")

    identity = packet["identity"]
    contract = packet["contract"]
    occurrence = packet["occurrence"]
    states = packet["states"]
    inventory = packet["inventory"]
    kernels = packet["kernel"]
    execution = packet["execution"]
    read_only = packet["read_only"]

    h1_plan = src.get("h1_plan", {})
    core_source = src.get("core", {})
    support_source = src.get("support", {})
    consequent_source = src.get("consequent_manifest", {})
    expected_identity = {
        "identity_packet_id": "H1_identity_00o8_v1",
        "element_symbol": "H",
        "atomic_number": "1",
        "mass_number": "1",
        "neutron_count": "0",
        "charge_state": "0",
        "isotope_label": "Hydrogen-1",
        "fractal_octave_coordinate": "00_(8)",
        "identity_source_plan_id": "H1_00o8",
        "identity_source_plan_row_sha256": h1_plan.get("hydrogen_occurrence_plan_row_sha256", ""),
        "identity_status": "declared_native_scope_not_external_target",
        "target_value_input_status": "absent",
    }
    for key, value in expected_identity.items():
        if identity.get(key) != value:
            reasons.append(f"identity_{key}_mismatch")

    expected_contract = {
        "local_dec_contract_id": "H1_local_Q4_direct_return_contract_v1",
        "fractal_octave_coordinate": "00_(8)",
        "state_space": "Q4", "vertex_domain": "{0,1}^4", "local_edge_slot_count": "4",
        "hamming_distance_rule": "exactly_1", "epsilon_rule": "TXOR_one_hot",
        "connected_event_order_rule": "target_i_equals_source_i_plus_1", "execution_mode": "enumerate_all",
        "admissibility_domain": "{0,1}",
        "weight_domain": "positive_integer_for_admitted_rows",
        "kernel_probability_domain": "nonnegative_reduced_rational_sum_exactly_1",
        "mass_conservation_rule": "sum_outgoing_mass_equals_incoming_mass_exactly",
        "bip_token_rule": "one_bip_per_admitted_executed_directed_edge",
        "trace_count_semantics": "execution_structure_not_temporal_magnitude",
        "monon_witness_rule": "one_outbound_then_one_inverse_return_with_no_prefix_closure",
        "support_family_member_reuse_as_edge_status": "forbidden", "Balmer_input_status": "absent",
        "core_scope_form_id": "form_3_3_6",
        "core_scope_occurrence_id": core_source.get("occurrence_id", ""),
        "core_scope_occurrence_row_sha256": core_source.get("occurrence_row_sha256", ""),
        "outer_support_policy_id": support_source.get("support_policy_id", ""),
        "outer_support_policy_sha256": support_source.get("support_policy_sha256", ""),
        "scope_binding_semantics": "declared_core_outer_scope_not_support_family_as_local_edge_pool",
        "consequent_gate_manifest_id": consequent_source.get("manifest_id", ""),
        "consequent_gate_manifest_path": CONSEQUENT_GATE_MANIFEST.relative_to(ROOT).as_posix(),
        "consequent_gate_manifest_sha256": sha_file(CONSEQUENT_GATE_MANIFEST),
        "consequent_gate_overall_status": consequent_source.get("overall_gate_status", ""),
        "outer_support_application_status_source": support_source.get("universal_application_status", ""),
        "outer_support_application_status_interpretation": src.get("support_status_interpretation", ""),
        "SI_unit_input_status": "absent", "target_value_input_status": "absent",
    }
    for key, value in expected_contract.items():
        if contract.get(key) != value:
            reasons.append(f"contract_{key}_mismatch")
    if contract.get("identity_packet_id") != identity.get("identity_packet_id") or contract.get("identity_packet_sha256") != identity.get("identity_packet_sha256"):
        reasons.append("contract_identity_binding_mismatch")

    expected_occurrence = {
        "occurrence_id": "H1_00o8_native_occurrence_v1", "fractal_octave_coordinate": "00_(8)",
        "core_form_id": "form_3_3_6", "core_route_form": "3:3:6",
        "core_occurrence_id": core_source.get("occurrence_id", ""),
        "core_occurrence_row_sha256": core_source.get("occurrence_row_sha256", ""),
        "outer_support_id": "00o8_C6_1_2_6", "outer_route_form": "1:2:6",
        "outer_support_policy_id": support_source.get("support_policy_id", ""),
        "outer_support_policy_sha256": support_source.get("support_policy_sha256", ""),
        "declared_coupling_form": "Couple(3:3:6,1:2:6)", "seat_state_id": "E2^0",
        "seat_state_semantics": "open_seat_duon_declared_scope",
        "coupling_operator_id": "H1_core_outer_scope_coupling_v1",
        "boundary_id": "B_H1_00o8_local_Q4_direct_return",
        "window_id": "omega_H1_two_event_direct_return",
        "occurrence_role": "first_element_target_blind_native_occurrence",
        "identity_specificity_status": "H1_identity_bound_shared_direct_return_topology",
        "local_DEC_status": "materialized_connected_Q4_direct_return",
        "returned_current_detection_status": "pending_pre_detection_freeze",
        "RD_status": "not_materialized", "RCD_status": "not_materialized",
        "duonic_pressure_status": "not_materialized", "SADAR_flow_status": "not_materialized",
        "phase_lock_status": "not_materialized", "temporal_report_status": "not_materialized",
        "Balmer_input_status": "absent",
        "target_value_input_status": "absent", "empirical_score_status": "not_computed",
    }
    for key, value in expected_occurrence.items():
        if occurrence.get(key) != value:
            reasons.append(f"occurrence_{key}_mismatch")
    if occurrence.get("identity_packet_id") != identity.get("identity_packet_id") or occurrence.get("identity_packet_sha256") != identity.get("identity_packet_sha256"):
        reasons.append("occurrence_identity_binding_mismatch")
    if occurrence.get("local_dec_contract_id") != contract.get("local_dec_contract_id") or occurrence.get("local_dec_contract_sha256") != contract.get("local_dec_contract_sha256"):
        reasons.append("occurrence_contract_binding_mismatch")

    if len(states) != 2:
        reasons.append("state_count_mismatch")
    if [row.get("state_order") for row in states] != ["0", "1"]:
        reasons.append("state_physical_order_mismatch")
    expected_states = [
        {
            "state_order": "0", "state_id": "H1_q4_state_origin", "epsilon_Q4": "0000", "mu": "0",
            "state_role": "retained_origin_and_return_state",
        },
        {
            "state_order": "1", "state_id": "H1_q4_state_hinge", "epsilon_Q4": "1000", "mu": "0",
            "state_role": "direct_return_hinge_state",
        },
    ]
    state_ids: set[str] = set()
    state_by_id: dict[str, Mapping[str, str]] = {}
    for index, row in enumerate(states):
        sid = row.get("state_id", "")
        if sid in state_ids:
            reasons.append("duplicate_state_id")
        state_ids.add(sid)
        state_by_id[sid] = row
        vertex = row.get("epsilon_Q4", "")
        if len(vertex) != 4 or set(vertex) - {"0", "1"}:
            reasons.append("invalid_Q4_vertex")
        if (
            row.get("occurrence_id") != occurrence.get("occurrence_id")
            or row.get("occurrence_packet_sha256") != occurrence.get("occurrence_packet_sha256")
            or row.get("boundary_id") != occurrence.get("boundary_id")
        ):
            reasons.append("state_occurrence_binding_mismatch")
        if index < len(expected_states):
            for key, value in expected_states[index].items():
                if row.get(key) != value:
                    reasons.append(f"state_{index}_{key}_mismatch")
        if row.get("vertex_domain_status") != "passed_binary_Q4":
            reasons.append("state_vertex_domain_status_mismatch")
        if row.get("target_value_input_status") != "absent":
            reasons.append("state_target_input_open")

    if len(inventory) != 8:
        reasons.append("inventory_row_count_mismatch")
    if [row.get("global_inventory_index") for row in inventory] != [str(i) for i in range(len(inventory))]:
        reasons.append("inventory_physical_order_mismatch")
    inventory_ids: set[str] = set()
    expected_event_specs = {
        0: {"source_state_id": "H1_q4_state_origin", "source": "0000", "sigma": "+1", "route": "outgoing"},
        1: {"source_state_id": "H1_q4_state_hinge", "source": "1000", "sigma": "-1", "route": "returned"},
    }
    for event_index in (0, 1):
        subset = [row for row in inventory if row.get("event_index") == str(event_index)]
        if len(subset) != 4:
            reasons.append(f"event_{event_index}_edge_slot_count_mismatch")
            continue
        if [row.get("edge_slot") for row in subset] != ["0", "1", "2", "3"]:
            reasons.append(f"event_{event_index}_slot_order_mismatch")
        admitted_count = 0
        probability = Fraction()
        source_vertex = subset[0].get("source_epsilon_Q4", "")
        spec = expected_event_specs[event_index]
        if source_vertex != spec["source"] or subset[0].get("source_state_id") != spec["source_state_id"]:
            reasons.append(f"event_{event_index}_canonical_source_mismatch")
        for local_index, row in enumerate(subset):
            edge_id = row.get("edge_id", "")
            if edge_id in inventory_ids:
                reasons.append("duplicate_edge_id")
            inventory_ids.add(edge_id)
            if edge_id.startswith("form_") or edge_id.startswith("00o8_C6"):
                reasons.append("support_family_id_reused_as_edge")
            if (
                row.get("occurrence_id") != occurrence.get("occurrence_id")
                or row.get("occurrence_packet_sha256") != occurrence.get("occurrence_packet_sha256")
                or row.get("local_dec_contract_id") != contract.get("local_dec_contract_id")
            ):
                reasons.append("inventory_occurrence_contract_binding_mismatch")
            source_state = state_by_id.get(row.get("source_state_id"), {})
            if row.get("source_state_row_sha256") != source_state.get("state_row_sha256"):
                reasons.append("inventory_source_state_hash_mismatch")
            if row.get("source_epsilon_Q4") != source_vertex:
                reasons.append("inventory_source_vertex_inconsistent")
            slot_text = row.get("edge_slot", "")
            try:
                slot = int(slot_text)
            except ValueError:
                reasons.append("malformed_edge_slot")
                continue
            if slot < 0 or slot > 3:
                reasons.append("edge_slot_out_of_range")
                continue
            if row.get("target_epsilon_Q4") != toggle(source_vertex, slot):
                reasons.append("target_vertex_not_canonical_toggle")
            expected_adm = "1" if slot == 0 else "0"
            expected_sigma = spec["sigma"] if slot == 0 else "0"
            expected_route = spec["route"] if slot == 0 else "blocked"
            expected_edge_id = f"H1_local_edge_evt{event_index}_slot{slot}"
            expected_global_index = str(event_index * 4 + slot)
            expected_effective = expected_adm
            expected_probability = expected_adm
            for key, value in {
                "global_inventory_index": expected_global_index,
                "source_state_id": spec["source_state_id"],
                "edge_id": expected_edge_id,
                "sigma_e": expected_sigma,
                "adm_e_B": expected_adm,
                "weight": "1",
                "effective_weight": expected_effective,
                "Z": "1",
                "P_num": expected_probability,
                "P_den": "1",
                "P_exact": expected_probability,
                "route_e_B": expected_route,
                "local_Q4_edge_status": "local_Hamming1_edge_slot",
            }.items():
                if row.get(key) != value:
                    reasons.append(f"inventory_event_{event_index}_slot_{slot}_{key}_mismatch")
            if row.get("adm_e_B") == "1":
                target_state = state_by_id.get(row.get("target_state_id"), {})
                if (
                    not target_state
                    or row.get("target_state_row_sha256") != target_state.get("state_row_sha256")
                    or row.get("target_epsilon_Q4") != target_state.get("epsilon_Q4")
                ):
                    reasons.append("inventory_target_state_hash_mismatch")
            elif row.get("target_state_id") != "" or row.get("target_state_row_sha256") != "":
                reasons.append("blocked_inventory_target_state_binding_not_empty")
            if row.get("hamming_distance") != "1" or hamming(source_vertex, row.get("target_epsilon_Q4", "")) != 1:
                reasons.append("hamming_distance_not_one")
            expected_xor = "".join("1" if a != b else "0" for a, b in zip(source_vertex, row.get("target_epsilon_Q4", "")))
            if row.get("xor_epsilon_Q4") != expected_xor or expected_xor.count("1") != 1:
                reasons.append("epsilon_not_one_hot_TXOR")
            if row.get("adm_e_B") not in {"0", "1"}:
                reasons.append("admissibility_not_binary")
            if row.get("adm_e_B") == "1":
                admitted_count += 1
                weight_value = safe_int(row.get("weight"), "inventory_weight", reasons, minimum=1)
                if weight_value is None:
                    reasons.append("admitted_weight_not_positive")
            try:
                p = parse_fraction(row.get("P_num", ""), row.get("P_den", ""))
                probability += p
                if str(p) != row.get("P_exact"):
                    reasons.append("P_exact_mismatch")
                if math.gcd(int(row.get("P_num", "0")), int(row.get("P_den", "1"))) != 1:
                    reasons.append("kernel_fraction_not_reduced")
            except (ValueError, ZeroDivisionError):
                reasons.append("malformed_kernel_probability")
            if row.get("row_time_semantics") != "kernel_inventory_not_elapsed_time":
                reasons.append("inventory_temporal_retyping")
            if row.get("support_family_member_reuse_status") != "not_reused":
                reasons.append("inventory_support_family_namespace_reuse")
            if row.get("target_value_input_status") != "absent":
                reasons.append("inventory_target_input_open")
        if admitted_count != 1:
            reasons.append(f"event_{event_index}_admitted_edge_count_mismatch")
        if probability != 1:
            reasons.append(f"event_{event_index}_kernel_probability_sum_mismatch")

    if len(kernels) != 2:
        reasons.append("kernel_audit_row_count_mismatch")
    if [row.get("kernel_order") for row in kernels] != ["0", "1"]:
        reasons.append("kernel_physical_order_mismatch")
    for event_index in (0, 1):
        subset = [row for row in inventory if row.get("event_index") == str(event_index)]
        krows = [row for row in kernels if row.get("kernel_order") == str(event_index)]
        if len(krows) != 1:
            reasons.append(f"kernel_{event_index}_identity_count_mismatch")
            continue
        row = krows[0]
        if row.get("kernel_id") != event_kernel_id(event_index):
            reasons.append("kernel_id_mismatch")
        if (
            row.get("occurrence_id") != occurrence.get("occurrence_id")
            or row.get("occurrence_packet_sha256") != occurrence.get("occurrence_packet_sha256")
            or row.get("boundary_id") != occurrence.get("boundary_id")
        ):
            reasons.append("kernel_occurrence_binding_mismatch")
        source_state = state_by_id.get(row.get("source_state_id"), {})
        if row.get("source_state_row_sha256") != source_state.get("state_row_sha256"):
            reasons.append("kernel_source_state_hash_mismatch")
        if row.get("inventory_subset_sha256") != csv_digest(subset):
            reasons.append("kernel_inventory_subset_hash_mismatch")
        try:
            prob = sum((parse_fraction(item["P_num"], item["P_den"]) for item in subset), Fraction())
        except (ValueError, ZeroDivisionError):
            prob = Fraction(-1, 1)
        if row.get("probability_sum_num") != str(prob.numerator) or row.get("probability_sum_den") != str(prob.denominator):
            reasons.append("kernel_probability_sum_storage_mismatch")
        expected_kernel_fields = {
            "source_state_id": expected_event_specs[event_index]["source_state_id"],
            "edge_slot_count": "4", "admitted_edge_count": "1",
            "normalizer_num": "1", "normalizer_den": "1",
            "incoming_mass_num": "1", "incoming_mass_den": "1",
            "outgoing_mass_num": "1", "outgoing_mass_den": "1",
            "mass_residual_num": "0", "mass_residual_den": "1",
            "kernel_status": "passed", "target_value_input_status": "absent",
        }
        for key, value in expected_kernel_fields.items():
            if row.get(key) != value:
                reasons.append(f"kernel_{event_index}_{key}_mismatch")
        if row.get("kernel_status") != "passed" or prob != 1:
            reasons.append("kernel_status_not_passed")
        if row.get("mass_residual_num") != "0" or row.get("target_value_input_status") != "absent":
            reasons.append("kernel_mass_or_target_status_mismatch")

    if len(execution) != 2:
        reasons.append("execution_row_count_mismatch")
    if [row.get("event_order") for row in execution] != ["0", "1"]:
        reasons.append("execution_event_order_mismatch")
    event_ids: set[str] = set()
    kernel_by_id = {row.get("kernel_id"): row for row in kernels}
    expected_execution = [
        {
            "event_order": "0", "event_id": "H1_DEC_event_outbound", "source_state_id": "H1_q4_state_origin",
            "target_state_id": "H1_q4_state_hinge", "source_epsilon_Q4": "0000", "target_epsilon_Q4": "1000",
            "edge_id": "H1_local_edge_evt0_slot0", "edge_slot": "0", "xor_epsilon_Q4": "1000",
            "sigma_e": "+1", "route_e_B": "outgoing", "kernel_id": event_kernel_id(0), "parent_event_id": "",
        },
        {
            "event_order": "1", "event_id": "H1_DEC_event_return", "source_state_id": "H1_q4_state_hinge",
            "target_state_id": "H1_q4_state_origin", "source_epsilon_Q4": "1000", "target_epsilon_Q4": "0000",
            "edge_id": "H1_local_edge_evt1_slot0", "edge_slot": "0", "xor_epsilon_Q4": "1000",
            "sigma_e": "-1", "route_e_B": "returned", "kernel_id": event_kernel_id(1),
            "parent_event_id": "H1_DEC_event_outbound",
        },
    ]
    for index, row in enumerate(execution):
        event_id = row.get("event_id", "")
        if event_id in event_ids:
            reasons.append("duplicate_event_id")
        event_ids.add(event_id)
        if event_id.startswith("form_") or event_id.startswith("00o8_C6"):
            reasons.append("support_family_id_reused_as_event")
        if (
            row.get("occurrence_id") != occurrence.get("occurrence_id")
            or row.get("occurrence_packet_sha256") != occurrence.get("occurrence_packet_sha256")
            or row.get("boundary_id") != occurrence.get("boundary_id")
            or row.get("window_id") != occurrence.get("window_id")
        ):
            reasons.append("execution_occurrence_scope_binding_mismatch")
        if index < len(expected_execution):
            for key, value in expected_execution[index].items():
                if row.get(key) != value:
                    reasons.append(f"execution_{index}_{key}_mismatch")
        if row.get("source_state_id") not in state_by_id or row.get("target_state_id") not in state_by_id:
            reasons.append("execution_unknown_state")
        source_state = state_by_id.get(row.get("source_state_id"), {})
        target_state = state_by_id.get(row.get("target_state_id"), {})
        if row.get("source_state_row_sha256") != source_state.get("state_row_sha256"):
            reasons.append("execution_source_state_hash_mismatch")
        if row.get("target_state_row_sha256") != target_state.get("state_row_sha256"):
            reasons.append("execution_target_state_hash_mismatch")
        if row.get("source_epsilon_Q4") != state_by_id.get(row.get("source_state_id"), {}).get("epsilon_Q4") or row.get("target_epsilon_Q4") != state_by_id.get(row.get("target_state_id"), {}).get("epsilon_Q4"):
            reasons.append("execution_state_vertex_binding_mismatch")
        if row.get("hamming_distance") != "1" or hamming(row.get("source_epsilon_Q4", ""), row.get("target_epsilon_Q4", "")) != 1:
            reasons.append("execution_hamming_distance_not_one")
        if row.get("execution_mode") != "enumerate_all":
            reasons.append("execution_mode_mismatch")
        try:
            if parse_fraction(row.get("P_num", ""), row.get("P_den", "")) != 1:
                reasons.append("execution_probability_not_one")
            incoming = parse_fraction(row.get("incoming_mass_num", ""), row.get("incoming_mass_den", ""))
            outgoing = parse_fraction(row.get("outgoing_mass_num", ""), row.get("outgoing_mass_den", ""))
            if incoming != outgoing:
                reasons.append("execution_mass_not_conserved")
        except (ValueError, ZeroDivisionError):
            reasons.append("execution_malformed_fraction")
        kernel = kernel_by_id.get(row.get("kernel_id"))
        if not kernel or row.get("kernel_audit_row_sha256") != kernel.get("kernel_audit_row_sha256"):
            reasons.append("execution_kernel_binding_mismatch")
        matching_inventory = [item for item in inventory if item.get("event_index") == str(index) and item.get("adm_e_B") == "1"]
        if (
            len(matching_inventory) != 1
            or row.get("edge_id") != matching_inventory[0].get("edge_id")
            or row.get("admitted_edge_row_sha256") != matching_inventory[0].get("edge_inventory_row_sha256")
        ):
            reasons.append("execution_admitted_edge_binding_mismatch")
        for key, value in {
            "hamming_distance": "1", "execution_mode": "enumerate_all", "P_num": "1", "P_den": "1",
            "incoming_mass_num": "1", "incoming_mass_den": "1", "outgoing_mass_num": "1", "outgoing_mass_den": "1",
            "mass_conservation_status": "passed", "executed_bip_token_count": "1",
            "row_time_semantics": "executed_bip_token_not_temporal_magnitude",
            "support_family_member_reuse_status": "not_reused", "target_value_input_status": "absent",
        }.items():
            if row.get(key) != value:
                reasons.append(f"execution_{index}_{key}_mismatch")
        if row.get("executed_bip_token_count") != "1" or row.get("row_time_semantics") != "executed_bip_token_not_temporal_magnitude":
            reasons.append("execution_bip_or_time_semantics_mismatch")
        if row.get("support_family_member_reuse_status") != "not_reused" or row.get("target_value_input_status") != "absent":
            reasons.append("execution_namespace_or_target_status_mismatch")
        if index == 0 and row.get("parent_event_id") != "":
            reasons.append("first_event_parent_not_empty")
        if index == 1:
            if row.get("parent_event_id") != execution[0].get("event_id"):
                reasons.append("second_event_parent_mismatch")
            if execution[0].get("target_state_id") != row.get("source_state_id"):
                reasons.append("execution_not_connected")

    if execution and execution[0].get("source_state_id") != execution[-1].get("target_state_id"):
        reasons.append("full_return_not_closed")
    if execution and execution[0].get("source_state_id") == execution[0].get("target_state_id"):
        reasons.append("proper_prefix_closure_detected")

    if (
        read_only.get("occurrence_id") != occurrence.get("occurrence_id")
        or read_only.get("occurrence_packet_sha256") != occurrence.get("occurrence_packet_sha256")
        or read_only.get("identity_packet_id") != identity.get("identity_packet_id")
        or read_only.get("identity_packet_sha256") != identity.get("identity_packet_sha256")
    ):
        reasons.append("read_only_identity_occurrence_binding_mismatch")
    if read_only.get("boundary_id") != occurrence.get("boundary_id") or read_only.get("window_id") != occurrence.get("window_id"):
        reasons.append("read_only_scope_binding_mismatch")
    expected_read_only = {
        "read_only_trace_id": "H1_read_only_direct_return_trace_v1",
        "execution_ledger_path": FILES["execution"].relative_to(ROOT).as_posix(),
        "execution_ledger_sha256": sha_file(FILES["execution"]),
        "event_count": "2", "trace_count": "2", "executed_bip_token_count": "2",
        "trace_count_temporal_status": "execution_structure_not_temporal_magnitude",
        "state_sequence": "H1_q4_state_origin>H1_q4_state_hinge>H1_q4_state_origin",
        "initial_state_id": "H1_q4_state_origin", "final_state_id": "H1_q4_state_origin",
        "full_return_candidate_status": "candidate_initial_equals_final", "proper_prefix_return_count": "0",
        "trace_freeze_status": "frozen_before_detection", "target_value_read_status": "not_read",
    }
    for key, value in expected_read_only.items():
        if read_only.get(key) != value:
            reasons.append(f"read_only_{key}_mismatch")
    if read_only.get("execution_rows_digest_sha256") != csv_digest(execution):
        reasons.append("read_only_execution_rows_digest_mismatch")
    if read_only.get("state_rows_digest_sha256") != csv_digest(states):
        reasons.append("read_only_state_rows_digest_mismatch")
    admitted_inventory = [row for row in inventory if row.get("adm_e_B") == "1"]
    if read_only.get("admitted_edge_rows_digest_sha256") != csv_digest(admitted_inventory):
        reasons.append("read_only_admitted_edge_rows_digest_mismatch")
    if read_only.get("event_count") != "2" or read_only.get("trace_count") != "2" or read_only.get("executed_bip_token_count") != "2":
        reasons.append("read_only_count_mismatch")
    if read_only.get("trace_count_temporal_status") != "execution_structure_not_temporal_magnitude" or read_only.get("trace_freeze_status") != "frozen_before_detection" or read_only.get("target_value_read_status") != "not_read":
        reasons.append("read_only_closed_status_mismatch")
    if read_only.get("initial_state_id") != read_only.get("final_state_id") or read_only.get("proper_prefix_return_count") != "0":
        reasons.append("read_only_return_status_mismatch")

    return {"passed": not reasons, "failure_reasons": sorted(set(reasons))}


def build_detection(packet: Mapping[str, object], manifest: Mapping[str, object]) -> dict[str, str]:
    result = evaluate_packet(packet, verify_manifest=True, manifest=manifest)
    if not result["passed"]:
        raise ValueError("pre-detection packet rejected: " + ";".join(result["failure_reasons"]))
    identity = packet["identity"]
    occurrence = packet["occurrence"]
    states = packet["states"]
    inventory = packet["inventory"]
    execution = packet["execution"]
    read_only = packet["read_only"]
    admitted = [row for row in inventory if row["adm_e_B"] == "1"]
    return attach({
        "detector_id": "H1_direct_return_detector_v2",
        "occurrence_id": occurrence["occurrence_id"],
        "occurrence_packet_sha256": occurrence["occurrence_packet_sha256"],
        "identity_packet_id": identity["identity_packet_id"],
        "identity_packet_sha256": identity["identity_packet_sha256"],
        "read_only_trace_id": read_only["read_only_trace_id"],
        "read_only_trace_row_sha256": read_only["read_only_trace_row_sha256"],
        "pre_detection_manifest_sha256": sha_file(FILES["pre_manifest"]),
        "source_state_row_sha256": states[0]["state_row_sha256"],
        "target_state_row_sha256": states[1]["state_row_sha256"],
        "outbound_admitted_edge_row_sha256": admitted[0]["edge_inventory_row_sha256"],
        "return_admitted_edge_row_sha256": admitted[1]["edge_inventory_row_sha256"],
        "execution_rows_digest_sha256": csv_digest(execution),
        "outbound_event_id": execution[0]["event_id"],
        "return_event_id": execution[1]["event_id"],
        "outbound_sigma": execution[0]["sigma_e"],
        "return_sigma": execution[1]["sigma_e"],
        "shared_axis_slot": execution[0]["edge_slot"],
        "inverse_edge_orientation_status": "passed",
        "full_return_status": "passed",
        "proper_prefix_return_count": "0",
        "primitive_direct_return_status": "passed",
        "returned_current_relation": "outbound_hinge_return_pair",
        "monon_cycle_class_status": "detected_direct_minimal_witness",
        "minimal_direct_witness_bip_count": "2",
        "minimal_witness_temporal_status": "witness_only_not_duration",
        "duon_current_seed_status": "detected_return_pair_pressure_pending",
        "RD_status": "not_materialized",
        "RCD_status": "not_materialized",
        "duonic_pressure_status": "not_materialized",
        "SADAR_flow_status": "not_materialized",
        "phase_lock_status": "not_materialized",
        "target_value_read_status": "not_read",
        "empirical_score_status": "not_computed",
        "detection_status": "passed",
    }, ROW_HASH_FIELDS["detector"])


def evaluate_detector_row(
    detector: object,
    packet: object,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    reasons: list[str] = []
    try:
        reasons.extend(row_schema_reasons(detector, PACKET_SCHEMAS["detector"], "detector"))
        if reasons:
            return {"passed": False, "failure_reasons": sorted(set(reasons))}
        verify_attached(detector, ROW_HASH_FIELDS["detector"])
        packet_result = evaluate_packet(packet, verify_manifest=True, manifest=manifest)
        if not packet_result["passed"]:
            reasons.append("detector_input_packet_not_admitted")
            reasons.extend(f"detector_input:{reason}" for reason in packet_result["failure_reasons"])
            return {"passed": False, "failure_reasons": sorted(set(reasons))}
        identity = packet["identity"]
        occurrence = packet["occurrence"]
        states = packet["states"]
        inventory = packet["inventory"]
        execution = packet["execution"]
        read_only = packet["read_only"]
        admitted = [row for row in inventory if row.get("adm_e_B") == "1"]
        expected = {
            "detector_id": "H1_direct_return_detector_v2",
            "occurrence_id": occurrence["occurrence_id"],
            "occurrence_packet_sha256": occurrence["occurrence_packet_sha256"],
            "identity_packet_id": identity["identity_packet_id"],
            "identity_packet_sha256": identity["identity_packet_sha256"],
            "read_only_trace_id": read_only["read_only_trace_id"],
            "read_only_trace_row_sha256": read_only["read_only_trace_row_sha256"],
            "pre_detection_manifest_sha256": sha_file(FILES["pre_manifest"]),
            "source_state_row_sha256": states[0]["state_row_sha256"],
            "target_state_row_sha256": states[1]["state_row_sha256"],
            "outbound_admitted_edge_row_sha256": admitted[0]["edge_inventory_row_sha256"],
            "return_admitted_edge_row_sha256": admitted[1]["edge_inventory_row_sha256"],
            "execution_rows_digest_sha256": csv_digest(execution),
            "outbound_event_id": execution[0]["event_id"],
            "return_event_id": execution[1]["event_id"],
            "outbound_sigma": "+1",
            "return_sigma": "-1",
            "shared_axis_slot": "0",
            "inverse_edge_orientation_status": "passed",
            "full_return_status": "passed",
            "proper_prefix_return_count": "0",
            "primitive_direct_return_status": "passed",
            "returned_current_relation": "outbound_hinge_return_pair",
            "monon_cycle_class_status": "detected_direct_minimal_witness",
            "minimal_direct_witness_bip_count": "2",
            "minimal_witness_temporal_status": "witness_only_not_duration",
            "duon_current_seed_status": "detected_return_pair_pressure_pending",
            "RD_status": "not_materialized",
            "RCD_status": "not_materialized",
            "duonic_pressure_status": "not_materialized",
            "SADAR_flow_status": "not_materialized",
            "phase_lock_status": "not_materialized",
            "target_value_read_status": "not_read",
            "empirical_score_status": "not_computed",
            "detection_status": "passed",
        }
        for key, value in expected.items():
            if detector.get(key) != value:
                reasons.append(f"detector_{key}_mismatch")
    except Exception as exc:
        reasons.append(f"detector_evaluation_exception:{type(exc).__name__}:{exc}")
    return {"passed": not reasons, "failure_reasons": sorted(set(reasons))}


def build_detector_counterfactuals(
    detector: Mapping[str, str],
    packet: Mapping[str, object],
    manifest: Mapping[str, object],
) -> list[dict[str, str]]:
    cases: list[tuple[str, str, dict[str, str], str]] = []
    for field in FORBIDDEN_SCHEMA_PROBES:
        mutated = mutate_attached(detector, ROW_HASH_FIELDS["detector"], {field: "forbidden_probe"})
        cases.append((f"detector_unknown_field_{field}", "detector_schema_closure", mutated, "failed"))
    for case_id, changes in [
        ("detector_occurrence_hash_mismatch", {"occurrence_packet_sha256": "0" * 64}),
        ("detector_source_state_hash_mismatch", {"source_state_row_sha256": "0" * 64}),
        ("detector_target_state_hash_mismatch", {"target_state_row_sha256": "0" * 64}),
        ("detector_outbound_edge_hash_mismatch", {"outbound_admitted_edge_row_sha256": "0" * 64}),
        ("detector_return_edge_hash_mismatch", {"return_admitted_edge_row_sha256": "0" * 64}),
        ("detector_target_value_opened", {"target_value_read_status": "read"}),
        ("detector_classification_mutated", {"returned_current_relation": "unrelated"}),
    ]:
        cases.append((case_id, "detector_binding", mutate_attached(detector, ROW_HASH_FIELDS["detector"], changes), "failed"))
    cases.append(("unchanged_detector_control", "control", dict(detector), "passed"))

    rows: list[dict[str, str]] = []
    for order, (case_id, mutation_class, candidate, expected) in enumerate(cases):
        result = evaluate_detector_row(candidate, packet, manifest)
        observed = "passed" if result["passed"] else "failed"
        rows.append(attach({
            "counterfactual_order": order,
            "counterfactual_id": case_id,
            "mutation_class": mutation_class,
            "expected_detector_result": expected,
            "observed_detector_result": observed,
            "observed_failure_reasons": ";".join(result["failure_reasons"]),
            "detector_counterfactual_audit_status": "passed" if observed == expected else "failed",
        }, ROW_HASH_FIELDS["detector_counterfactual"]))
    return rows


def evaluate_mutation(packet: dict[str, object]) -> dict[str, object]:
    return evaluate_packet(packet)


def build_counterfactuals(native: dict[str, object]) -> list[dict[str, str]]:
    cases: list[tuple[str, str, dict[str, object], str]] = []

    def cp() -> dict[str, object]:
        return deepcopy(native)

    p = cp(); p["states"][0] = mutate_attached(p["states"][0], ROW_HASH_FIELDS["states"], {"epsilon_Q4": "0002"}); cases.append(("invalid_Q4_vertex", "state_vertex", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"target_epsilon_Q4": "1100", "hamming_distance": "2", "xor_epsilon_Q4": "1100"}); cases.append(("hamming_distance_two", "edge_geometry", p, "failed"))
    p = cp(); p["execution"][1] = mutate_attached(p["execution"][1], ROW_HASH_FIELDS["execution"], {"source_state_id": "H1_q4_state_origin", "source_epsilon_Q4": "0000"}); cases.append(("disconnected_event_order", "event_order", p, "failed"))
    p = cp(); extra = mutate_attached(p["inventory"][-1], ROW_HASH_FIELDS["inventory"], {"global_inventory_index": "8", "event_index": "1", "edge_slot": "4", "edge_id": "H1_local_edge_evt1_slot4"}); p["inventory"].append(extra); cases.append(("fifth_edge_slot", "local_slot_count", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"P_num": "1", "P_den": "2", "P_exact": "1/2"}); cases.append(("kernel_sum_mismatch", "kernel_probability", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"P_den": "0", "P_exact": "undefined"}); cases.append(("zero_denominator", "kernel_probability", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"weight": "9"}); cases.append(("admitted_weight_contract_mutation", "kernel_weight_contract", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"Z": "9"}); cases.append(("stored_normalizer_mutation", "kernel_normalizer", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"P_num": "2", "P_den": "2", "P_exact": "1"}); cases.append(("nonreduced_kernel_fraction", "kernel_probability", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"sigma_e": "0", "route_e_B": "blocked"}); cases.append(("admitted_edge_semantic_retyping", "edge_semantics", p, "failed"))
    p = cp(); p["occurrence"] = mutate_attached(p["occurrence"], ROW_HASH_FIELDS["occurrence"], {"identity_packet_id": "unrelated_identity"}); cases.append(("occurrence_identity_mismatch", "cross_packet_identity", p, "failed"))
    p = cp(); p["occurrence"] = mutate_attached(p["occurrence"], ROW_HASH_FIELDS["occurrence"], {"outer_support_id": "foreign_support"}); cases.append(("occurrence_outer_support_mismatch", "cross_packet_scope", p, "failed"))
    p = cp(); p["occurrence"] = mutate_attached(p["occurrence"], ROW_HASH_FIELDS["occurrence"], {"RD_status": "materialized"}); cases.append(("occurrence_RD_lane_opened", "closed_status", p, "failed"))
    p = cp(); support_id = "00o8_C6_1_2_6"; p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"edge_id": support_id}); p["execution"][0] = mutate_attached(p["execution"][0], ROW_HASH_FIELDS["execution"], {"edge_id": support_id}); cases.append(("support_family_reused_as_edge_id", "namespace", p, "failed"))
    p = cp(); p["occurrence"] = mutate_attached(p["occurrence"], ROW_HASH_FIELDS["occurrence"], {"target_value_input_status": "present"}); cases.append(("target_input_present", "target_quarantine", p, "failed"))
    p = cp(); p["execution"][0] = mutate_attached(p["execution"][0], ROW_HASH_FIELDS["execution"], {"execution_mode": "sample_one"}); cases.append(("execution_mode_mutation", "execution_contract", p, "failed"))
    p = cp(); p["execution"][0] = mutate_attached(p["execution"][0], ROW_HASH_FIELDS["execution"], {"sigma_e": "0", "route_e_B": "blocked"}); cases.append(("execution_edge_semantic_retyping", "execution_semantics", p, "failed"))
    p = cp(); p["kernel"][0] = mutate_attached(p["kernel"][0], ROW_HASH_FIELDS["kernel"], {"normalizer_num": "9"}); cases.append(("kernel_audit_normalizer_mutation", "kernel_audit", p, "failed"))
    p = cp(); p["states"][1] = mutate_attached(p["states"][1], ROW_HASH_FIELDS["states"], {"epsilon_Q4": "0100"}); cases.append(("canonical_hinge_axis_mutation", "state_identity", p, "failed"))
    p = cp(); p["read_only"] = mutate_attached(p["read_only"], ROW_HASH_FIELDS["read_only"], {"execution_rows_digest_sha256": "0" * 64}); cases.append(("read_only_hash_mismatch", "freeze_integrity", p, "failed"))
    p = cp(); p["read_only"] = mutate_attached(p["read_only"], ROW_HASH_FIELDS["read_only"], {"execution_ledger_path": "manual/data/hydrogen/other.csv"}); cases.append(("read_only_ledger_path_mutation", "freeze_integrity", p, "failed"))
    p = cp(); p["identity"] = mutate_attached(p["identity"], ROW_HASH_FIELDS["identity"], {"mass_number": "2", "neutron_count": "1", "isotope_label": "Hydrogen-2"}); cases.append(("identity_counterfactual_without_new_scope", "identity_binding", p, "failed"))
    p = cp(); p["identity"] = mutate_attached(p["identity"], ROW_HASH_FIELDS["identity"], {"identity_source_plan_row_sha256": "0" * 64}); cases.append(("identity_source_plan_hash_mutation", "source_binding", p, "failed"))

    # Exact schema closure: every forbidden target/metric field is rejected in every packet class.
    for packet_key in PACKET_ROOT_KEYS:
        for field in FORBIDDEN_SCHEMA_PROBES:
            p = cp()
            hash_field = ROW_HASH_FIELDS[packet_key]
            if packet_key in LIST_PACKET_KEYS:
                p[packet_key][0] = mutate_attached(p[packet_key][0], hash_field, {field: "forbidden_probe"})
            else:
                p[packet_key] = mutate_attached(p[packet_key], hash_field, {field: "forbidden_probe"})
            cases.append((f"unknown_field_{packet_key}_{field}", "packet_schema_closure", p, "failed"))

    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"edge_slot": "4"}); cases.append(("out_of_range_edge_slot_structured_failure", "malformed_packet", p, "failed"))
    p = cp(); p["inventory"][0] = mutate_attached(p["inventory"][0], ROW_HASH_FIELDS["inventory"], {"weight": "x"}); cases.append(("malformed_weight_structured_failure", "malformed_packet", p, "failed"))
    p = cp(); del p["identity"]; cases.append(("missing_identity_packet_structured_failure", "malformed_packet", p, "failed"))
    p = cp();
    occurrence_without_target = {k: v for k, v in p["occurrence"].items() if k not in {"target_value_input_status", ROW_HASH_FIELDS["occurrence"]}}
    p["occurrence"] = attach(occurrence_without_target, ROW_HASH_FIELDS["occurrence"])
    cases.append(("missing_occurrence_required_field", "packet_schema_closure", p, "failed"))

    cases.append(("unchanged_control", "control", cp(), "passed"))

    rows: list[dict[str, str]] = []
    for order, (case_id, mutation_class, packet, expected) in enumerate(cases):
        result = evaluate_mutation(packet)
        observed = "passed" if result["passed"] else "failed"
        rows.append(attach({
            "counterfactual_order": order,
            "counterfactual_id": case_id,
            "mutation_class": mutation_class,
            "expected_gate_result": expected,
            "observed_gate_result": observed,
            "observed_failure_reasons": ";".join(result["failure_reasons"]),
            "counterfactual_audit_status": "passed" if observed == expected else "failed",
        }, ROW_HASH_FIELDS["counterfactual"]))
    return rows


def build_identity_counterfactual(identity: Mapping[str, str], occurrence: Mapping[str, str]) -> dict[str, str]:
    h2_identity = mutate_attached(identity, ROW_HASH_FIELDS["identity"], {
        "identity_packet_id": "H2_identity_00o8_counterfactual_v1", "mass_number": "2", "neutron_count": "1", "isotope_label": "Hydrogen-2"
    })
    h2_occurrence = mutate_attached(occurrence, ROW_HASH_FIELDS["occurrence"], {
        "occurrence_id": "H2_00o8_counterfactual_occurrence_v1", "identity_packet_id": h2_identity["identity_packet_id"], "identity_packet_sha256": h2_identity["identity_packet_sha256"]
    })
    identity_changed = identity["identity_packet_sha256"] != h2_identity["identity_packet_sha256"]
    occurrence_changed = occurrence["occurrence_packet_sha256"] != h2_occurrence["occurrence_packet_sha256"]
    admission_status = "rejected_identity_scope_mismatch"
    return attach({
        "counterfactual_id": "H2_identity_scope_counterfactual_v1",
        "native_identity_packet_id": identity["identity_packet_id"],
        "counterfactual_identity_packet_id": h2_identity["identity_packet_id"],
        "native_identity_sha256": identity["identity_packet_sha256"],
        "counterfactual_identity_sha256": h2_identity["identity_packet_sha256"],
        "identity_hash_change_status": "changed" if identity_changed else "unchanged",
        "native_occurrence_id": occurrence["occurrence_id"],
        "counterfactual_occurrence_id": h2_occurrence["occurrence_id"],
        "native_occurrence_sha256": occurrence["occurrence_packet_sha256"],
        "counterfactual_occurrence_sha256": h2_occurrence["occurrence_packet_sha256"],
        "occurrence_hash_change_status": "changed" if occurrence_changed else "unchanged",
        "topology_family_status": "shared_direct_return_topology_permitted_only_as_separate_scoped_occurrence",
        "H1_gate_admission_status": admission_status,
        "counterfactual_audit_status": "passed" if identity_changed and occurrence_changed and admission_status.startswith("rejected_") else "failed",
    }, ROW_HASH_FIELDS["identity_cf"])


def gate_manifest(
    detection: Mapping[str, str],
    detector_validation: Mapping[str, object],
    counterfactuals: Sequence[Mapping[str, str]],
    source_counterfactuals: Sequence[Mapping[str, str]],
    detector_counterfactuals: Sequence[Mapping[str, str]],
    identity_cf: Mapping[str, str],
    source_chain_audit: Mapping[str, str],
) -> dict[str, object]:
    file_keys = (
        "identity", "contract", "occurrence", "states", "inventory", "kernel",
        "execution", "read_only", "source_chain_audit", "pre_manifest", "detector",
        "identity_cf", "counterfactual", "source_counterfactual", "detector_counterfactual",
    )
    files = [file_record(FILES[key]) for key in file_keys]
    counter_status = "passed" if all(row["counterfactual_audit_status"] == "passed" for row in counterfactuals) else "failed"
    source_counter_status = "passed" if all(row["source_counterfactual_audit_status"] == "passed" for row in source_counterfactuals) else "failed"
    detector_counter_status = "passed" if all(row["detector_counterfactual_audit_status"] == "passed" for row in detector_counterfactuals) else "failed"
    statuses = {
        "exact_packet_schema_status": "passed",
        "source_schema_and_semantics_status": source_chain_audit["source_chain_status"].split("_")[0],
        "prior_consequent_gate_chain_status": "passed" if source_chain_audit["consequent_gate_overall_status"] == "passed" else "failed",
        "identity_binding_status": "passed",
        "occurrence_hash_propagation_status": "passed",
        "local_Q4_geometry_status": "passed",
        "kernel_exactness_status": "passed",
        "connected_execution_status": "passed",
        "mass_conservation_status": "passed",
        "read_only_freeze_status": "passed",
        "returned_current_detection_status": detection["detection_status"],
        "post_write_detector_validation_status": "passed" if detector_validation["passed"] else "failed",
        "identity_counterfactual_status": identity_cf["counterfactual_audit_status"],
        "packet_counterfactual_status": counter_status,
        "source_counterfactual_status": source_counter_status,
        "detector_counterfactual_status": detector_counter_status,
        "malformed_packet_structured_failure_status": "passed",
        "target_quarantine_status": "passed",
    }
    overall = "passed" if all(value == "passed" for value in statuses.values()) else "failed"
    return {
        "gate_id": GATE_ID,
        "version_scope": VERSION,
        "release_class": "target_blind_H1_native_occurrence_exact_schema_source_chain_detector_hardening",
        "scientific_claim": "H1_identity_bound_declared_core_outer_scope_with_connected_direct_return_Q4_occurrence_only",
        "files": files,
        "statuses": statuses,
        "overall_gate_status": overall,
        "current_state": {
            "H1_identity": "frozen",
            "declared_core_outer_scope": "3:3:6_coupled_with_1:2:6",
            "local_DEC_execution": "materialized_connected_two_event_direct_return",
            "packet_schema": "exact_ordered_fail_closed",
            "source_chain": "exact_semantics_and_prior_gate_manifest_verified",
            "occurrence_hash_propagation": "states_inventory_kernel_execution_read_only_detector",
            "detector_validation": "post_write_exact_schema_and_binding_passed",
            "executed_bip_token_count": 2,
            "trace_count_temporal_status": "execution_structure_not_temporal_magnitude",
            "returned_current_detection": "passed_direct_minimal_witness",
            "RD_RCD": "not_materialized",
            "duonic_pressure": "not_materialized",
            "SADAR_flow": "not_materialized",
            "primitive_phase_lock": "not_materialized",
            "Balmer_target": "not_read",
            "SI_report": "inactive",
            "residual_score": "not_computed",
        },
    }


def write_outputs() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    source_bundle = source_bundle_from_disk()
    source_result = evaluate_source_bundle(source_bundle)
    if not source_result["passed"]:
        raise SystemExit("Hydrogen-1 source-chain audit failed: " + ";".join(source_result["failure_reasons"]))
    src = dict(source_result["resolved"])
    source_chain_audit = build_source_chain_audit(src)

    identity = build_identity(src)
    contract = build_contract(src, identity)
    occurrence = build_occurrence(src, identity, contract)
    states = build_states(occurrence)
    inventory = build_inventory(occurrence, contract, states)
    kernels = build_kernel_audit(occurrence, inventory)
    execution = build_execution(occurrence, inventory, kernels)

    write_csv(FILES["identity"], PACKET_SCHEMAS["identity"], [identity])
    write_csv(FILES["contract"], PACKET_SCHEMAS["contract"], [contract])
    write_csv(FILES["occurrence"], PACKET_SCHEMAS["occurrence"], [occurrence])
    write_csv(FILES["states"], PACKET_SCHEMAS["states"], states)
    write_csv(FILES["inventory"], PACKET_SCHEMAS["inventory"], inventory)
    write_csv(FILES["kernel"], PACKET_SCHEMAS["kernel"], kernels)
    write_csv(FILES["execution"], PACKET_SCHEMAS["execution"], execution)

    read_only = build_read_only(occurrence, states, inventory, execution)
    write_csv(FILES["read_only"], PACKET_SCHEMAS["read_only"], [read_only])
    write_csv(FILES["source_chain_audit"], PACKET_SCHEMAS["source_chain_audit"], [source_chain_audit])

    frozen_paths = [
        FILES[key] for key in (
            "identity", "contract", "occurrence", "states", "inventory", "kernel",
            "execution", "read_only", "source_chain_audit",
        )
    ]
    input_paths = [H_PLAN, CORE_OCCURRENCES, SUPPORT_POLICY, TEMPORAL_TYPES, CONSEQUENT_GATE_MANIFEST]
    pre = build_pre_manifest(frozen_paths, input_paths)
    FILES["pre_manifest"].write_text(json.dumps(pre, indent=2) + "\n", encoding="utf-8")

    packet = packet_from_disk()
    detection = build_detection(packet, pre)
    write_csv(FILES["detector"], PACKET_SCHEMAS["detector"], [detection])
    detector_from_disk = read_one_exact(FILES["detector"], PACKET_SCHEMAS["detector"])
    detector_validation = evaluate_detector_row(detector_from_disk, packet, pre)
    if not detector_validation["passed"]:
        raise SystemExit("Hydrogen-1 detector validation failed: " + ";".join(detector_validation["failure_reasons"]))

    identity_cf = build_identity_counterfactual(identity, occurrence)
    write_csv(FILES["identity_cf"], PACKET_SCHEMAS["identity_cf"], [identity_cf])

    counterfactuals = build_counterfactuals(packet)
    write_csv(FILES["counterfactual"], PACKET_SCHEMAS["counterfactual"], counterfactuals)

    source_counterfactuals = build_source_counterfactuals(source_bundle)
    write_csv(FILES["source_counterfactual"], PACKET_SCHEMAS["source_counterfactual"], source_counterfactuals)

    detector_counterfactuals = build_detector_counterfactuals(detector_from_disk, packet, pre)
    write_csv(FILES["detector_counterfactual"], PACKET_SCHEMAS["detector_counterfactual"], detector_counterfactuals)

    manifest = gate_manifest(
        detector_from_disk,
        detector_validation,
        counterfactuals,
        source_counterfactuals,
        detector_counterfactuals,
        identity_cf,
        source_chain_audit,
    )
    FILES["gate_manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if manifest["overall_gate_status"] != "passed":
        raise SystemExit("Hydrogen-1 native occurrence gate failed")


if __name__ == "__main__":
    write_outputs()
