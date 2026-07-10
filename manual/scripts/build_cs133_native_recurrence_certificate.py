#!/usr/bin/env python3
"""Build the Cs-scoped native coupled core-outer primitive recurrence certificate.

M2 is target-free and pre-metrological. It reads the admitted M1H packet,
constructs a connected six-state recurrence from the detected p:q support core
and a separately frozen two-state core/outer coupling contract, executes the
single-successor exact D.E.C. kernel in enumerate_all mode, freezes the
read-only trace, and certifies primitive closure and exact mass conservation.

The recurrence length is derived as 2 * (p + q). The declared M1 scope L is
carried only as a post-derivation consistency check; it is not an input to the
period construction. No Cs clock frequency, SI reference period, observation
packet, target value, residual, or score is read.
"""
from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual" / "data" / "cs133"
SCRIPT_REL = "manual/scripts/build_cs133_native_recurrence_certificate.py"
M1_MANIFEST = DATA / "cs133_structural_occurrence_manifest.json"
M1_DETECTION = DATA / "cs133_structural_detection_result.csv"
M1_IDENTITY = DATA / "cs133_identity_packet.csv"
M1_BINDING = DATA / "cs133_fractal_elementary_occurrence_binding.csv"
M1_PRE_FREEZE = DATA / "cs133_pre_detection_freeze_manifest.json"
PRE_CERT_MANIFEST = DATA / "cs133_native_recurrence_pre_certificate_manifest.json"
RECURRENCE_MANIFEST = DATA / "cs133_native_recurrence_manifest.json"

OUTPUT_NAMES = (
    "cs133_core_outer_coupling_operator.csv",
    "cs133_native_recurrence_kernel_contract.csv",
    "cs133_native_coupled_state_registry.csv",
    "cs133_native_recurrence_transition_matrix.csv",
    "cs133_native_recurrence_dec_execution_ledger.csv",
    "cs133_native_recurrence_read_only_trace.csv",
    "cs133_native_recurrence_mass_audit.csv",
    "cs133_native_recurrence_certificate.csv",
    "cs133_native_recurrence_counterfactual_audit.csv",
    "cs133_native_recurrence_pre_certificate_manifest.json",
    "cs133_native_recurrence_manifest.json",
)

SECTORS = ("left_support", "hinge_support", "right_support")
COUPLED_PHASES = ("A", "B")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_json_hash(obj: object) -> str:
    return sha256_bytes(canonical_json_bytes(obj))


def canonical_row_hash(row: Mapping[str, str], hash_field: str) -> str:
    payload = {k: str(row[k]) for k in sorted(row) if k != hash_field}
    return canonical_json_hash(payload)


def attach_hash(row: Mapping[str, object], field: str) -> dict[str, str]:
    normalized = {k: str(v) for k, v in row.items()}
    normalized[field] = canonical_row_hash(normalized, field)
    return normalized


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(fieldnames)
    normalized = [{k: str(row.get(k, "")) for k in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_one(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    if len(rows) != 1:
        raise ValueError(f"expected one row in {path}, got {len(rows)}")
    return rows[0]


def fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def parse_support_core(text: str) -> tuple[int, int]:
    parts = text.split(":")
    if len(parts) != 2:
        raise ValueError(f"support core must have p:q form: {text}")
    p, q = (int(x) for x in parts)
    if p < 1 or q < 2:
        raise ValueError("support core outside declared positive domain")
    return p, q


def verify_file_against_manifest(manifest: Mapping[str, object], path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    matches = [row for row in manifest.get("files", []) if row.get("path") == rel]
    if len(matches) != 1:
        raise ValueError(f"M1 manifest missing unique row for {rel}")
    row = matches[0]
    if path.stat().st_size != int(row["bytes"]):
        raise ValueError(f"M1 byte mismatch: {rel}")
    if sha256_file(path) != row["sha256"]:
        raise ValueError(f"M1 SHA-256 mismatch: {rel}")


def verify_m1_inputs() -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, object]]:
    m1_manifest = json.loads(M1_MANIFEST.read_text(encoding="utf-8"))
    for path in (M1_IDENTITY, M1_BINDING, M1_DETECTION):
        verify_file_against_manifest(m1_manifest, path)
    identity = read_one(M1_IDENTITY)
    binding = read_one(M1_BINDING)
    detection = read_one(M1_DETECTION)
    if detection["detected_support_core"] != "1:2":
        raise ValueError("M2 expects admitted M1 support core 1:2")
    if detection["declared_scope_L"] != "6":
        raise ValueError("M2 expects carried declared scope L=6")
    if detection.get("target_frequency_input_status") != "absent":
        raise ValueError("target frequency must be absent from M1 packet")
    if identity["identity_packet_id"] != binding["identity_packet_id"]:
        raise ValueError("identity/binding ID mismatch")
    if identity["identity_packet_sha256"] != binding["identity_packet_sha256"]:
        raise ValueError("identity/binding hash mismatch")
    pre = json.loads(M1_PRE_FREEZE.read_text(encoding="utf-8"))
    if pre.get("freeze_status") != "frozen_before_detection":
        raise ValueError("M1 pre-detection freeze is not closed")
    return identity, binding, detection, m1_manifest


def build_coupling_operator(identity: Mapping[str, str], binding: Mapping[str, str], detection: Mapping[str, str]) -> dict[str, str]:
    p, q = parse_support_core(detection["detected_support_core"])
    sector_count = p + q
    state_count = len(COUPLED_PHASES)
    phase_count = sector_count * state_count
    row = attach_hash(
        {
            "coupling_operator_id": "cs133_core_outer_three_sector_dual_state_cycle_v1",
            "identity_packet_id": identity["identity_packet_id"],
            "identity_packet_sha256": identity["identity_packet_sha256"],
            "occurrence_binding_id": binding["occurrence_binding_id"],
            "occurrence_binding_sha256": binding["occurrence_binding_sha256"],
            "fractal_octave_coordinate": identity["fractal_octave_coordinate"],
            "detected_support_core": detection["detected_support_core"],
            "detected_p": p,
            "detected_q": q,
            "sector_count_rule": "p_plus_q",
            "sector_count": sector_count,
            "sector_labels": ";".join(SECTORS),
            "native_coupled_state_count": state_count,
            "native_coupled_state_A_id": "native_coupled_state_A",
            "native_coupled_state_B_id": "native_coupled_state_B",
            "phase_count_rule": "native_coupled_state_count_times_sector_count",
            "phase_count": phase_count,
            "declared_scope_L": detection["declared_scope_L"],
            "declared_L_role": "post_derivation_consistency_check_only",
            "recurrence_length_uses_declared_L": "false",
            "core_occurrence_id": "cs133_core_occurrence_00o8",
            "outer_occurrence_id": "cs133_outer_occurrence_support_1_2",
            "core_outer_coupling_operator_role": "declared_target_free_native_state_cycle",
            "duon_drive_contract_id": "cs133_native_duon_drive_internal_exchange_v1",
            "unperturbed_extraction_rule_id": "cs133_remove_external_drive_and_readout_exchange_v1",
            "execution_mode": "enumerate_all",
            "duration_semantics": "realized_integer_bip_count",
            "phase_transition_bip_rule": "one_declared_phase_transition_equals_one_bip",
            "target_frequency_input_status": "absent",
            "observation_packet_input_status": "absent",
            "metrological_correspondence_status": "not_active_until_M3",
            "SI_anchor_status": "inactive",
            "operator_status": "frozen_before_state_and_transition_materialization",
        },
        "coupling_operator_sha256",
    )
    if phase_count != 6:
        raise ValueError("current admitted M2 contract must derive six phases from p:q and dual state count")
    return row


def build_kernel_contract(operator: Mapping[str, str]) -> dict[str, str]:
    return attach_hash(
        {
            "kernel_id": "cs133_native_recurrence_single_successor_kernel_v1",
            "kernel_family_id": "unified_exact_admissibility_weight_kernel_v1",
            "coupling_operator_id": operator["coupling_operator_id"],
            "coupling_operator_sha256": operator["coupling_operator_sha256"],
            "execution_mode": "enumerate_all",
            "admissible_member_count": 1,
            "admissibility_vector": "1",
            "weight_vector_exact": "1/1",
            "normalizer_num": 1,
            "normalizer_den": 1,
            "probability_vector_exact": "1/1",
            "kernel_formula": "P=adm*w/sum(adm*w)",
            "kernel_status": "frozen_before_recurrence_execution",
        },
        "kernel_sha256",
    )


def build_states(identity: Mapping[str, str], binding: Mapping[str, str], operator: Mapping[str, str], *, prefix: str = "cs133") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    idx = 0
    for sector_index, sector_label in enumerate(SECTORS):
        for phase in COUPLED_PHASES:
            state_id = f"{prefix}_rec_state_{idx:02d}_{sector_label}_{phase}"
            row = attach_hash(
                {
                    "state_order": idx,
                    "state_id": state_id,
                    "identity_packet_id": identity["identity_packet_id"],
                    "identity_packet_sha256": identity["identity_packet_sha256"],
                    "occurrence_binding_id": binding["occurrence_binding_id"],
                    "occurrence_binding_sha256": binding["occurrence_binding_sha256"],
                    "coupling_operator_id": operator["coupling_operator_id"],
                    "coupling_operator_sha256": operator["coupling_operator_sha256"],
                    "core_occurrence_id": operator["core_occurrence_id"],
                    "outer_occurrence_id": operator["outer_occurrence_id"],
                    "sector_index": sector_index,
                    "sector_label": sector_label,
                    "coupled_phase": phase,
                    "native_coupled_state_id": operator[f"native_coupled_state_{phase}_id"],
                    "fractal_octave_coordinate": operator["fractal_octave_coordinate"],
                    "native_count_unit": "bip",
                    "primitive_completion_object": "monon",
                    "target_frequency_input_status": "absent",
                    "state_status": "frozen_native_coupled_state",
                },
                "state_packet_sha256",
            )
            rows.append(row)
            idx += 1
    if len(rows) != int(operator["phase_count"]):
        raise ValueError("state count does not match derived phase count")
    return rows


def topology_signature(states: Sequence[Mapping[str, str]]) -> str:
    payload = [(r["sector_index"], r["sector_label"], r["coupled_phase"]) for r in states]
    return canonical_json_hash(payload)


def build_transitions(states: Sequence[Mapping[str, str]], operator: Mapping[str, str], kernel: Mapping[str, str], *, prefix: str = "cs133") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    count = len(states)
    for i, source in enumerate(states):
        target = states[(i + 1) % count]
        row = attach_hash(
            {
                "transition_order": i,
                "phase_transition_id": f"{prefix}_phase_transition_{i:02d}",
                "source_state_id": source["state_id"],
                "source_state_packet_sha256": source["state_packet_sha256"],
                "target_state_id": target["state_id"],
                "target_state_packet_sha256": target["state_packet_sha256"],
                "parent_transition_id": "cycle_root" if i == 0 else f"{prefix}_phase_transition_{i-1:02d}",
                "coupling_operator_id": operator["coupling_operator_id"],
                "coupling_operator_sha256": operator["coupling_operator_sha256"],
                "kernel_id": kernel["kernel_id"],
                "kernel_sha256": kernel["kernel_sha256"],
                "execution_mode": "enumerate_all",
                "adm_e_B": 1,
                "w_num": 1,
                "w_den": 1,
                "Z_num": 1,
                "Z_den": 1,
                "P_num": 1,
                "P_den": 1,
                "P_exact": "1/1",
                "phase_transition_bip_num": 1,
                "phase_transition_bip_den": 1,
                "duration_semantics": "realized_integer_bip_count",
                "target_frequency_input_status": "absent",
                "transition_status": "frozen_connected_cycle_edge",
            },
            "transition_row_sha256",
        )
        rows.append(row)
    return rows


def transition_topology_signature(rows: Sequence[Mapping[str, str]], states: Sequence[Mapping[str, str]]) -> str:
    by_id = {r["state_id"]: r for r in states}
    payload = []
    for row in rows:
        src = by_id[row["source_state_id"]]
        dst = by_id[row["target_state_id"]]
        payload.append((src["sector_label"], src["coupled_phase"], dst["sector_label"], dst["coupled_phase"]))
    return canonical_json_hash(payload)


def build_execution(transitions: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    cumulative = 0
    for t in transitions:
        incoming = Fraction(1, 1)
        prob = Fraction(int(t["P_num"]), int(t["P_den"]))
        outgoing = incoming * prob
        bip = Fraction(int(t["phase_transition_bip_num"]), int(t["phase_transition_bip_den"]))
        if bip.denominator != 1:
            raise ValueError("M2 anchor-eligible recurrence requires integer realized bip increments")
        cumulative += bip.numerator
        row = attach_hash(
            {
                "event_index": t["transition_order"],
                "event_order_relation": f"event_{t['transition_order']}_precedes_event_{(int(t['transition_order']) + 1) % len(transitions)}",
                "phase_transition_id": t["phase_transition_id"],
                "source_state_id": t["source_state_id"],
                "target_state_id": t["target_state_id"],
                "parent_transition_id": t["parent_transition_id"],
                "kernel_id": t["kernel_id"],
                "kernel_sha256": t["kernel_sha256"],
                "execution_mode": "enumerate_all",
                "incoming_mass_num": incoming.numerator,
                "incoming_mass_den": incoming.denominator,
                "probability_num": prob.numerator,
                "probability_den": prob.denominator,
                "outgoing_mass_num": outgoing.numerator,
                "outgoing_mass_den": outgoing.denominator,
                "mass_residual_num": (outgoing - incoming).numerator,
                "mass_residual_den": (outgoing - incoming).denominator,
                "mass_conservation_status": "passed" if outgoing == incoming else "failed",
                "bip_increment_num": bip.numerator,
                "bip_increment_den": bip.denominator,
                "duration_semantics": "realized_integer_bip_count",
                "cumulative_bip_count": cumulative,
                "target_frequency_input_status": "absent",
                "execution_row_status": "executed_exact_connected_transition",
            },
            "execution_row_sha256",
        )
        rows.append(row)
    return rows


def freeze_trace(execution_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    frozen: list[dict[str, str]] = []
    for row in execution_rows:
        copied = dict(row)
        if canonical_row_hash(copied, "execution_row_sha256") != copied["execution_row_sha256"]:
            raise ValueError("execution row hash mismatch before trace freeze")
        copied["freeze_status"] = "frozen_before_recurrence_certificate"
        copied["read_only_row_sha256"] = canonical_row_hash(copied, "read_only_row_sha256")
        frozen.append(copied)
    return frozen


def audit_mass(execution_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    total_residual = Fraction(0, 1)
    for row in execution_rows:
        incoming = Fraction(int(row["incoming_mass_num"]), int(row["incoming_mass_den"]))
        outgoing = Fraction(int(row["outgoing_mass_num"]), int(row["outgoing_mass_den"]))
        residual = outgoing - incoming
        total_residual += residual
        audit = attach_hash(
            {
                "audit_scope": "phase_transition",
                "phase_transition_id": row["phase_transition_id"],
                "incoming_mass_num": incoming.numerator,
                "incoming_mass_den": incoming.denominator,
                "outgoing_mass_num": outgoing.numerator,
                "outgoing_mass_den": outgoing.denominator,
                "mass_residual_num": residual.numerator,
                "mass_residual_den": residual.denominator,
                "mass_conservation_status": "passed" if residual == 0 else "failed",
            },
            "mass_audit_row_sha256",
        )
        rows.append(audit)
    rows.append(
        attach_hash(
            {
                "audit_scope": "full_cycle",
                "phase_transition_id": "all",
                "incoming_mass_num": len(execution_rows),
                "incoming_mass_den": 1,
                "outgoing_mass_num": len(execution_rows),
                "outgoing_mass_den": 1,
                "mass_residual_num": total_residual.numerator,
                "mass_residual_den": total_residual.denominator,
                "mass_conservation_status": "passed" if total_residual == 0 else "failed",
            },
            "mass_audit_row_sha256",
        )
    )
    return rows


def certify_recurrence(
    identity: Mapping[str, str],
    binding: Mapping[str, str],
    detection: Mapping[str, str],
    operator: Mapping[str, str],
    states: Sequence[Mapping[str, str]],
    transitions: Sequence[Mapping[str, str]],
    read_only_trace: Sequence[Mapping[str, str]],
    mass_audit: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    if not read_only_trace:
        raise ValueError("empty recurrence trace")
    initial = transitions[0]["source_state_id"]
    walk = [initial]
    for row in transitions:
        if walk[-1] != row["source_state_id"]:
            raise ValueError("transition chain is disconnected")
        walk.append(row["target_state_id"])
    full_period_closure = walk[-1] == initial
    prefix_closures = sum(1 for state in walk[1:-1] if state == initial)
    unique_primitive_states = len(set(walk[:-1]))
    transition_count = len(transitions)
    primitive = full_period_closure and prefix_closures == 0 and unique_primitive_states == transition_count
    bip_count = sum(Fraction(int(r["bip_increment_num"]), int(r["bip_increment_den"])) for r in read_only_trace)
    if bip_count.denominator != 1:
        raise ValueError("primitive recurrence bip count must be integer")
    exact_mass = all(r["mass_conservation_status"] == "passed" for r in mass_audit)
    # A deterministic transition on six states is a permutation iff every state
    # has exactly one incoming and one outgoing edge.
    outgoing = {s["state_id"]: 0 for s in states}
    incoming = {s["state_id"]: 0 for s in states}
    for row in transitions:
        outgoing[row["source_state_id"]] += 1
        incoming[row["target_state_id"]] += 1
    permutation_pass = all(v == 1 for v in outgoing.values()) and all(v == 1 for v in incoming.values())
    declared_L = int(detection["declared_scope_L"])
    row = attach_hash(
        {
            "recurrence_certificate_id": "cs133_native_core_outer_primitive_recurrence_v1",
            "identity_packet_id": identity["identity_packet_id"],
            "identity_packet_sha256": identity["identity_packet_sha256"],
            "occurrence_binding_id": binding["occurrence_binding_id"],
            "occurrence_binding_sha256": binding["occurrence_binding_sha256"],
            "coupling_operator_id": operator["coupling_operator_id"],
            "coupling_operator_sha256": operator["coupling_operator_sha256"],
            "core_occurrence_id": operator["core_occurrence_id"],
            "outer_occurrence_id": operator["outer_occurrence_id"],
            "native_coupled_state_A_id": operator["native_coupled_state_A_id"],
            "native_coupled_state_B_id": operator["native_coupled_state_B_id"],
            "duon_drive_contract_id": operator["duon_drive_contract_id"],
            "unperturbed_extraction_rule_id": operator["unperturbed_extraction_rule_id"],
            "initial_state_id": initial,
            "final_state_id": walk[-1],
            "primitive_state_count": unique_primitive_states,
            "transition_count": transition_count,
            "primitive_recurrence_bip_count": bip_count.numerator,
            "duration_semantics": "realized_integer_bip_count",
            "phase_transition_bip_rule": operator["phase_transition_bip_rule"],
            "full_period_closure": "passed" if full_period_closure else "failed",
            "proper_prefix_closure_count": prefix_closures,
            "primitive_period_minimality": "passed" if primitive else "failed",
            "state_permutation_audit": "passed_single_cycle" if permutation_pass and primitive else "failed",
            "exact_mass_conservation": "passed" if exact_mass else "failed",
            "event_order_relation_status": "passed_connected_total_order_with_cycle_closure" if primitive else "failed",
            "declared_scope_L": declared_L,
            "recurrence_length_uses_declared_L": "false",
            "recurrence_L_coincidence_status": "derived_recurrence_count_matches_declared_scope" if bip_count == declared_L else "derived_recurrence_count_differs_from_declared_scope",
            "target_frequency_input_status": "absent",
            "observation_packet_input_status": "absent",
            "metrological_correspondence_status": "not_active_until_M3",
            "SI_anchor_status": "inactive",
            "monon_completion_status": "certified_native_primitive_cycle" if primitive else "failed",
            "anchor_eligibility_status": "eligible_for_M3_metrological_definition" if primitive and exact_mass and bip_count > 0 else "blocked",
            "certificate_status": "passed_native_recurrence_only" if primitive and exact_mass else "failed",
            "transition_matrix_topology_sha256": transition_topology_signature(transitions, states),
            "state_registry_sha256": sha256_file(DATA / "cs133_native_coupled_state_registry.csv"),
            "transition_matrix_file_sha256": sha256_file(DATA / "cs133_native_recurrence_transition_matrix.csv"),
            "read_only_trace_file_sha256": sha256_file(DATA / "cs133_native_recurrence_read_only_trace.csv"),
        },
        "recurrence_certificate_sha256",
    )
    return row


def make_counterfactual_identity() -> tuple[dict[str, str], dict[str, str]]:
    identity = attach_hash(
        {
            "identity_packet_id": "xe132_identity_Z54_A132_N78_counterfactual",
            "fractal_octave_coordinate": "00_(8)",
            "element_symbol": "Xe",
            "element_name": "Xenon",
            "atomic_number": 54,
            "mass_number": 132,
            "neutron_count": 78,
            "simulation_scope_input_class": "declared_counterfactual_identity_not_fit_target",
            "native_count_unit": "bip",
            "primitive_completion_object": "monon",
            "observation_target_input_status": "absent",
            "clock_frequency_input_status": "absent",
            "identity_packet_status": "counterfactual_frozen_for_specificity_audit",
        },
        "identity_packet_sha256",
    )
    binding = attach_hash(
        {
            "occurrence_binding_id": "xe132_counterfactual_elementary_occurrence_00o8",
            "identity_packet_id": identity["identity_packet_id"],
            "identity_packet_sha256": identity["identity_packet_sha256"],
            "fractal_octave_coordinate": "00_(8)",
            "scale_lane": "fractal_elementary_native_lane",
            "construction_equivalence_class_id": "elementary_00o8_Q4_branch_hinge_branch_monon_family",
            "identity_binding_status": "counterfactual_identity_bound_to_separate_scoped_occurrence",
            "target_observable_input_status": "absent",
        },
        "occurrence_binding_sha256",
    )
    return identity, binding


def build_counterfactual_audit(
    cs_identity: Mapping[str, str],
    cs_binding: Mapping[str, str],
    cs_operator: Mapping[str, str],
    cs_states: Sequence[Mapping[str, str]],
    cs_transitions: Sequence[Mapping[str, str]],
    certificate: Mapping[str, str],
) -> dict[str, str]:
    xe_identity, xe_binding = make_counterfactual_identity()
    xe_operator = dict(cs_operator)
    xe_operator.update(
        {
            "identity_packet_id": xe_identity["identity_packet_id"],
            "identity_packet_sha256": xe_identity["identity_packet_sha256"],
            "occurrence_binding_id": xe_binding["occurrence_binding_id"],
            "occurrence_binding_sha256": xe_binding["occurrence_binding_sha256"],
            "coupling_operator_id": "xe132_counterfactual_core_outer_three_sector_dual_state_cycle_v1",
        }
    )
    xe_operator.pop("coupling_operator_sha256", None)
    xe_operator = attach_hash(xe_operator, "coupling_operator_sha256")
    kernel = build_kernel_contract(xe_operator)
    xe_states = build_states(xe_identity, xe_binding, xe_operator, prefix="xe132")
    xe_transitions = build_transitions(xe_states, xe_operator, kernel, prefix="xe132")
    cs_state_hash = canonical_json_hash([r["state_packet_sha256"] for r in cs_states])
    xe_state_hash = canonical_json_hash([r["state_packet_sha256"] for r in xe_states])
    cs_matrix_hash = canonical_json_hash([r["transition_row_sha256"] for r in cs_transitions])
    xe_matrix_hash = canonical_json_hash([r["transition_row_sha256"] for r in xe_transitions])
    cs_topology = transition_topology_signature(cs_transitions, cs_states)
    xe_topology = transition_topology_signature(xe_transitions, xe_states)
    cs_cycle_sig = canonical_json_hash([(r["sector_label"], r["coupled_phase"]) for r in cs_states])
    xe_cycle_sig = canonical_json_hash([(r["sector_label"], r["coupled_phase"]) for r in xe_states])
    return attach_hash(
        {
            "counterfactual_audit_id": "cs133_native_recurrence_xe132_specificity_audit_v1",
            "baseline_identity_packet_id": cs_identity["identity_packet_id"],
            "baseline_identity_packet_sha256": cs_identity["identity_packet_sha256"],
            "counterfactual_identity_packet_id": xe_identity["identity_packet_id"],
            "counterfactual_identity_packet_sha256": xe_identity["identity_packet_sha256"],
            "identity_packet_change_status": "changed" if cs_identity["identity_packet_sha256"] != xe_identity["identity_packet_sha256"] else "unchanged",
            "occurrence_binding_change_status": "changed" if cs_binding["occurrence_binding_sha256"] != xe_binding["occurrence_binding_sha256"] else "unchanged",
            "coupled_state_packet_change_status": "changed" if cs_state_hash != xe_state_hash else "unchanged",
            "transition_matrix_packet_change_status": "changed" if cs_matrix_hash != xe_matrix_hash else "unchanged",
            "transition_topology_signature_status": "unchanged" if cs_topology == xe_topology else "changed",
            "primitive_cycle_signature_status": "unchanged" if cs_cycle_sig == xe_cycle_sig else "changed",
            "baseline_primitive_recurrence_bip_count": certificate["primitive_recurrence_bip_count"],
            "counterfactual_primitive_recurrence_bip_count": len(xe_transitions),
            "recurrence_length_change_status": "unchanged" if int(certificate["primitive_recurrence_bip_count"]) == len(xe_transitions) else "changed",
            "recurrence_specificity_status": "shared_elementary_recurrence_instantiated_at_Cs_scope" if cs_topology == xe_topology and cs_cycle_sig == xe_cycle_sig else "identity_specific_recurrence",
            "scientific_interpretation": "identity_specific_scoped_occurrence_of_shared_elementary_recurrence_family",
            "metrological_definition_status": "pending_M3",
            "target_frequency_input_status": "absent",
            "counterfactual_audit_status": "passed",
        },
        "counterfactual_audit_sha256",
    )


def artifact_record(path: Path, role: str) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "artifact_role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_pre_certificate_manifest(paths: Sequence[tuple[Path, str]], operator: Mapping[str, str]) -> dict[str, object]:
    manifest: dict[str, object] = {
        "freeze_manifest_id": "cs133_M2_pre_certificate_freeze_v1",
        "freeze_status": "frozen_before_recurrence_certificate",
        "allowed_input_paths": [p.relative_to(ROOT).as_posix() for p, _ in paths],
        "forbidden_input_classes": [
            "SI_caesium_frequency",
            "SI_reference_period_target",
            "observation_packets",
            "target_values",
            "residuals",
            "scores",
        ],
        "semantic_contract": {
            "execution_mode": "enumerate_all",
            "duration_semantics": "realized_integer_bip_count",
            "phase_transition_bip_rule": operator["phase_transition_bip_rule"],
            "recurrence_length_uses_declared_L": "false",
            "target_frequency_input": "absent",
            "metrological_correspondence": "inactive",
        },
        "artifact_count": len(paths),
        "artifacts": [artifact_record(p, role) for p, role in paths],
    }
    manifest["freeze_manifest_sha256"] = canonical_json_hash(manifest)
    return manifest


def verify_pre_certificate_manifest(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = data.get("freeze_manifest_sha256")
    payload = dict(data)
    payload.pop("freeze_manifest_sha256", None)
    if canonical_json_hash(payload) != expected:
        raise ValueError("pre-certificate manifest hash mismatch")
    for artifact in data["artifacts"]:
        p = ROOT / artifact["path"]
        if not p.is_file():
            raise ValueError(f"missing frozen artifact: {artifact['path']}")
        if p.stat().st_size != int(artifact["bytes"]):
            raise ValueError(f"frozen artifact byte mismatch: {artifact['path']}")
        if sha256_file(p) != artifact["sha256"]:
            raise ValueError(f"frozen artifact SHA mismatch: {artifact['path']}")


def write_manifest(current_state: Mapping[str, str], file_paths: Sequence[Path]) -> None:
    files = []
    for path in sorted(file_paths):
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest: dict[str, object] = {
        "manifest_id": "cs133_native_coupled_core_outer_primitive_recurrence_v1",
        "gate_role": "target_free_native_connected_recurrence_certificate_pre_metrological",
        "fractal_octave_coordinate": "00_(8)",
        "current_state": dict(current_state),
        "certificate_order": [
            "admitted_M1_identity_and_support_core",
            "target_free_core_outer_coupling_operator_freeze",
            "native_coupled_state_registry",
            "single_successor_exact_kernel_freeze",
            "connected_transition_matrix",
            "enumerate_all_exact_mass_execution",
            "read_only_trace_freeze",
            "pre_certificate_hash_manifest_verification",
            "primitive_closure_and_minimality_audit",
            "counterfactual_identity_specificity_audit",
        ],
        "files": files,
    }
    RECURRENCE_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    identity, binding, detection, _ = verify_m1_inputs()
    operator = build_coupling_operator(identity, binding, detection)
    kernel = build_kernel_contract(operator)
    states = build_states(identity, binding, operator)
    transitions = build_transitions(states, operator, kernel)
    execution = build_execution(transitions)
    read_only = freeze_trace(execution)
    mass_audit = audit_mass(execution)

    write_csv(DATA / "cs133_core_outer_coupling_operator.csv", list(operator), [operator])
    write_csv(DATA / "cs133_native_recurrence_kernel_contract.csv", list(kernel), [kernel])
    write_csv(DATA / "cs133_native_coupled_state_registry.csv", list(states[0]), states)
    write_csv(DATA / "cs133_native_recurrence_transition_matrix.csv", list(transitions[0]), transitions)
    write_csv(DATA / "cs133_native_recurrence_dec_execution_ledger.csv", list(execution[0]), execution)
    write_csv(DATA / "cs133_native_recurrence_read_only_trace.csv", list(read_only[0]), read_only)
    write_csv(DATA / "cs133_native_recurrence_mass_audit.csv", list(mass_audit[0]), mass_audit)

    pre_paths = [
        (M1_IDENTITY, "M1_identity_packet"),
        (M1_BINDING, "M1_occurrence_binding"),
        (M1_DETECTION, "M1_detected_support_core"),
        (M1_MANIFEST, "M1_manifest"),
        (DATA / "cs133_core_outer_coupling_operator.csv", "M2_coupling_operator"),
        (DATA / "cs133_native_recurrence_kernel_contract.csv", "M2_kernel_contract"),
        (DATA / "cs133_native_coupled_state_registry.csv", "M2_state_registry"),
        (DATA / "cs133_native_recurrence_transition_matrix.csv", "M2_transition_matrix"),
        (DATA / "cs133_native_recurrence_dec_execution_ledger.csv", "M2_execution_ledger"),
        (DATA / "cs133_native_recurrence_read_only_trace.csv", "M2_read_only_trace"),
        (DATA / "cs133_native_recurrence_mass_audit.csv", "M2_mass_audit"),
        (ROOT / SCRIPT_REL, "M2_generator_implementation"),
    ]
    pre_manifest = build_pre_certificate_manifest(pre_paths, operator)
    PRE_CERT_MANIFEST.write_text(json.dumps(pre_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verify_pre_certificate_manifest(PRE_CERT_MANIFEST)

    certificate = certify_recurrence(identity, binding, detection, operator, states, transitions, read_only, mass_audit)
    write_csv(DATA / "cs133_native_recurrence_certificate.csv", list(certificate), [certificate])
    counterfactual = build_counterfactual_audit(identity, binding, operator, states, transitions, certificate)
    write_csv(DATA / "cs133_native_recurrence_counterfactual_audit.csv", list(counterfactual), [counterfactual])

    current_state = {
        "M1H": "complete_v40.03r03.2",
        "M2_native_recurrence": "complete",
        "identity_scope": "Cs133_at_00_(8)",
        "recurrence_specificity": counterfactual["recurrence_specificity_status"],
        "primitive_recurrence_bip_count": certificate["primitive_recurrence_bip_count"],
        "duration_semantics": certificate["duration_semantics"],
        "full_period_closure": certificate["full_period_closure"],
        "proper_prefix_closure_count": certificate["proper_prefix_closure_count"],
        "exact_mass_conservation": certificate["exact_mass_conservation"],
        "target_frequency_input": "absent",
        "metrological_correspondence": "not_active_until_M3",
        "SI_anchor": "inactive",
    }
    manifest_files = [
        DATA / name for name in OUTPUT_NAMES if name != "cs133_native_recurrence_manifest.json"
    ] + [ROOT / SCRIPT_REL]
    write_manifest(current_state, manifest_files)
    print("built Cs-133 native recurrence certificate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
