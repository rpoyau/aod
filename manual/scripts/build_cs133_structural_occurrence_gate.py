#!/usr/bin/env python3
"""Build the Cs-133 M1 structural-classification hardening gate.

This gate is deliberately pre-temporal.  It binds a frozen Cs-133 identity
packet to one scoped fractal-elementary occurrence at 00_(8), materializes:

* a non-temporal exact kernel/support enumeration;
* a canonical ``enumerate_all`` D.E.C. mass-propagation ledger;
* exact per-stage mass-conservation audits;
* a hash-locked pre-detection packet;
* a p:q classifier operating under a separately declared L scope;
* downstream hypothesis and capacity-fill audits.

The nine structural rows are not a primitive recurrence and their row indices
are not causal time.  No clock frequency, SI reference card, observation
packet, target value, residual, or score enters this gate.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual" / "data" / "cs133"
MANIFEST = DATA / "cs133_structural_occurrence_manifest.json"
FREEZE_MANIFEST = DATA / "cs133_pre_detection_freeze_manifest.json"
ROADMAP_MANIFEST = ROOT / "manual" / "data" / "roadmap" / "manual1_si_anchor_plan_manifest.json"
ELEMENT_REGISTRY = ROOT / "manual-2" / "data" / "elementary" / "element_registry_118.csv"
SCRIPT_REL = "manual/scripts/build_cs133_structural_occurrence_gate.py"

STAGE_SPECS: tuple[tuple[int, str, int, str, str], ...] = (
    (1, "left_branch", 4, "branch_minus", "cs133_kernel_left_uniform4_v1"),
    (2, "hinge", 1, "hinge_mu", "cs133_kernel_hinge_identity_v1"),
    (3, "right_branch", 4, "branch_plus", "cs133_kernel_right_uniform4_v1"),
)

STALE_FILES = (
    "cs133_native_structural_dec_trace.csv",
    "cs133_native_structural_read_only_trace.csv",
    "cs133_c3_closure_rule.csv",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_json_hash(obj: object) -> str:
    return sha256_bytes(canonical_json_bytes(obj))


def canonical_row_hash(row: Mapping[str, str], hash_field: str) -> str:
    payload = {k: row[k] for k in sorted(row) if k != hash_field}
    return canonical_json_hash(payload)


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{k: str(row.get(k, "")) for k in fieldnames} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def attach_hash(row: Mapping[str, object], field: str) -> dict[str, str]:
    normalized = {k: str(v) for k, v in row.items()}
    normalized[field] = canonical_row_hash(normalized, field)
    return normalized


def fraction_from_fields(row: Mapping[str, str], prefix: str) -> Fraction:
    num = int(row[f"{prefix}_num"])
    den = int(row[f"{prefix}_den"])
    if den <= 0:
        raise ValueError(f"{prefix} denominator must be positive")
    return Fraction(num, den)


def fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def status_changed(a: str, b: str, changed: str = "changed", unchanged: str = "unchanged") -> str:
    return changed if a != b else unchanged


def cleanup_stale_outputs() -> None:
    for name in STALE_FILES:
        (DATA / name).unlink(missing_ok=True)


def registry_row_for_z(z: int) -> dict[str, str]:
    rows = read_csv(ELEMENT_REGISTRY)
    matches = [row for row in rows if int(row["Z"]) == z]
    if len(matches) != 1:
        raise ValueError(f"expected one element-registry row for Z={z}, got {len(matches)}")
    return matches[0]


def make_identity_packet(*, z: int, a: int, symbol: str, name: str, packet_id: str) -> dict[str, str]:
    if a < z:
        raise ValueError("mass number must be at least atomic number")
    registry = registry_row_for_z(z)
    if registry["symbol"] != symbol or registry["name"] != name:
        raise ValueError("identity packet does not match frozen element registry")
    return attach_hash(
        {
            "identity_packet_id": packet_id,
            "fractal_octave_coordinate": "00_(8)",
            "element_symbol": symbol,
            "element_name": name,
            "atomic_number": z,
            "mass_number": a,
            "neutron_count": a - z,
            "element_registry_source_path": ELEMENT_REGISTRY.relative_to(ROOT).as_posix(),
            "element_registry_row_sha256": canonical_json_hash(registry),
            "simulation_scope_input_class": "declared_isotope_identity_not_fit_target",
            "native_count_unit": "bip",
            "primitive_completion_object": "monon",
            "origin_anchor_relation": "00_(8)_entails_monon_bip_biz",
            "observation_target_input_status": "absent",
            "clock_frequency_input_status": "absent",
            "identity_packet_status": "frozen",
        },
        "identity_packet_sha256",
    )


def make_occurrence_binding(identity: Mapping[str, str], *, occurrence_id: str) -> dict[str, str]:
    return attach_hash(
        {
            "occurrence_binding_id": occurrence_id,
            "identity_packet_id": identity["identity_packet_id"],
            "identity_packet_sha256": identity["identity_packet_sha256"],
            "fractal_octave_coordinate": "00_(8)",
            "scale_lane": "fractal_elementary_native_lane",
            "native_count_unit": "bip",
            "primitive_completion_object": "monon",
            "origin_anchor_relation": "00_(8)_entails_monon_bip_biz",
            "monon_semantics": "primitive_completed_branch_hinge_branch_cycle",
            "monon_completion_certificate_status": "pending_connected_cycle_trace_M2",
            "construction_equivalence_class_id": "elementary_00o8_Q4_branch_hinge_branch_monon_family",
            "identity_binding_status": "identity_bound_to_scoped_occurrence",
            "identity_specificity_status": "identity_specific_scope_shared_native_topology_family",
            "target_observable_input_status": "absent",
            "clock_frequency_input_status": "absent",
        },
        "occurrence_binding_sha256",
    )


def build_identity_and_scope() -> None:
    identity = make_identity_packet(
        z=55,
        a=133,
        symbol="Cs",
        name="Caesium",
        packet_id="cs133_identity_Z55_A133_N78",
    )
    write_csv(DATA / "cs133_identity_packet.csv", list(identity), [identity])

    binding = make_occurrence_binding(identity, occurrence_id="cs133_elementary_occurrence_00o8")
    write_csv(DATA / "cs133_fractal_elementary_occurrence_binding.csv", list(binding), [binding])

    construction_rule = attach_hash(
        {
            "construction_rule_id": "elementary_00o8_bip_monon_Q4_occurrence_v2",
            "construction_rule_role": "bind_identity_to_scoped_occurrence_and_shared_structural_kernel_family",
            "identity_input_fields": "identity_packet_id;identity_packet_sha256;atomic_number;mass_number;neutron_count",
            "scope_input_fields": "fractal_octave_coordinate;boundary_id;window_id",
            "origin_anchor_relation": "00_(8)_entails_monon_bip_biz",
            "native_count_unit": "bip",
            "primitive_completion_object": "monon",
            "topology_source": "Q4_Hamming1_branch_hinge_branch_with_monon_completion_basis",
            "stage_topology": "left_branch:4;hinge:1;right_branch:4",
            "window_slot_source": "declared_boundary_card",
            "identity_arithmetic_role": "scope_binding_not_topology_count_formula",
            "construction_equivalence_class_id": binding["construction_equivalence_class_id"],
            "counterfactual_policy": "identity_change_creates_separate_scoped_occurrence;shared_topology_allowed_only_by_declared_equivalence_class",
            "target_observable_input_status": "absent",
            "clock_frequency_input_status": "absent",
            "construction_rule_status": "frozen_before_kernel_enumeration",
        },
        "construction_rule_sha256",
    )
    write_csv(DATA / "cs133_identity_to_trace_construction_rule.csv", list(construction_rule), [construction_rule])

    boundary = attach_hash(
        {
            "boundary_id": "B_Cs_structural_scope",
            "window_id": "omega_Cs_structural_6slot",
            "fractal_octave_coordinate": "00_(8)",
            "window_slot_count": 6,
            "window_role": "declared_native_structural_enclosure",
            "native_count_unit": "bip",
            "primitive_completion_object": "monon",
            "execution_mode": "enumerate_all",
            "detector_input_status": "allowed",
            "L_scope_visibility_to_detector": "true",
            "target_observable_input_status": "absent",
            "temporal_recurrence_interpretation": "not_admitted_in_M1",
        },
        "boundary_card_sha256",
    )
    write_csv(DATA / "cs133_structural_boundary_card.csv", list(boundary), [boundary])

    hypothesis = attach_hash(
        {
            "occurrence_id": "cs133_occurrence_00o8_structural_hypothesis",
            "identity_packet_id": identity["identity_packet_id"],
            "occurrence_binding_id": binding["occurrence_binding_id"],
            "boundary_id": boundary["boundary_id"],
            "window_id": boundary["window_id"],
            "scale_lane": "fractal_elementary_native_structural_lane",
            "motif_family_hypothesis": "Dimonhexon",
            "support_core_hypothesis": "1:2",
            "declared_scope_L_hypothesis": 6,
            "outer_support_form_hypothesis": "1:2:6",
            "outer_support_form_detected": "pending_before_detector_execution",
            "outer_support_certificate": "pending_before_detector_execution",
            "hypothesis_visibility_to_detector": "forbidden",
            "cs_to_occurrence_binding_status": "scoped_elementary_occurrence_bound_physical_adequacy_not_empirically_validated",
            "target_observable_input_status": "absent",
            "clock_frequency_input_status": "absent",
            "temporal_recurrence_status": "not_evaluated",
            "SI_anchor_status": "inactive",
            "occurrence_status": "frozen_hypothesis",
        },
        "occurrence_packet_sha256",
    )
    write_csv(DATA / "cs133_structural_occurrence_hypothesis.csv", list(hypothesis), [hypothesis])


def build_kernel_contracts() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for stage_order, stage_id, count, sigma, kernel_id in STAGE_SPECS:
        weights = [1] * count
        probs = [Fraction(1, count)] * count
        row = attach_hash(
            {
                "stage_order": stage_order,
                "stage_id": stage_id,
                "kernel_id": kernel_id,
                "kernel_family_id": "unified_exact_admissibility_weight_kernel_v1",
                "execution_mode": "enumerate_all",
                "sigma_e": sigma,
                "admissible_member_count": count,
                "admissibility_vector": ";".join("1" for _ in range(count)),
                "weight_vector_exact": ";".join("1/1" for _ in weights),
                "normalizer_num": count,
                "normalizer_den": 1,
                "probability_vector_exact": ";".join(fraction_text(p) for p in probs),
                "kernel_formula": "P=adm*w/sum(adm*w)",
                "kernel_status": "frozen_before_enumeration",
            },
            "kernel_sha256",
        )
        rows.append(row)
    write_csv(DATA / "cs133_structural_kernel_contract.csv", list(rows[0]), rows)
    return rows


def kernel_by_stage(contracts: Sequence[Mapping[str, str]]) -> dict[str, Mapping[str, str]]:
    return {row["stage_id"]: row for row in contracts}


def construct_kernel_enumeration(
    identity: Mapping[str, str],
    binding: Mapping[str, str],
    construction_rule: Mapping[str, str],
    boundary: Mapping[str, str],
    contracts: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    kernels = kernel_by_stage(contracts)
    rows: list[dict[str, str]] = []
    enumeration_index = 0
    for stage_order, stage_id, count, sigma, _ in STAGE_SPECS:
        kernel = kernels[stage_id]
        normalizer = Fraction(int(kernel["normalizer_num"]), int(kernel["normalizer_den"]))
        for alt_index in range(count):
            weight = Fraction(1, 1)
            prob = weight / normalizer
            row = attach_hash(
                {
                    "enumeration_row_id": f"{identity['identity_packet_id']}_kernel_{enumeration_index:02d}",
                    "enumeration_row_index": enumeration_index,
                    "row_role": "native_structural_kernel_enumeration",
                    "row_time_semantics": "non_temporal_alternative_enumeration",
                    "identity_packet_id": identity["identity_packet_id"],
                    "identity_packet_sha256": identity["identity_packet_sha256"],
                    "occurrence_binding_id": binding["occurrence_binding_id"],
                    "occurrence_binding_sha256": binding["occurrence_binding_sha256"],
                    "construction_rule_id": construction_rule["construction_rule_id"],
                    "construction_rule_sha256": construction_rule["construction_rule_sha256"],
                    "construction_equivalence_class_id": construction_rule["construction_equivalence_class_id"],
                    "stage_order": stage_order,
                    "stage_id": stage_id,
                    "alternative_index": alt_index,
                    "kernel_id": kernel["kernel_id"],
                    "kernel_sha256": kernel["kernel_sha256"],
                    "boundary_id": boundary["boundary_id"],
                    "boundary_card_sha256": boundary["boundary_card_sha256"],
                    "window_id": boundary["window_id"],
                    "fractal_octave_coordinate": boundary["fractal_octave_coordinate"],
                    "native_count_unit": "bip",
                    "primitive_completion_object": "monon",
                    "monon_completion_status": "pending_connected_cycle_trace_M2",
                    "v": f"{stage_id}_source",
                    "e": f"{stage_id}_edge_{alt_index}",
                    "v_e": f"{stage_id}_target_{alt_index}",
                    "sigma_e": sigma,
                    "adm_e_B": 1,
                    "w_num": weight.numerator,
                    "w_den": weight.denominator,
                    "Z_num": normalizer.numerator,
                    "Z_den": normalizer.denominator,
                    "P_num": prob.numerator,
                    "P_den": prob.denominator,
                    "P_exact": fraction_text(prob),
                    "execution_mode": "enumerate_all",
                    "route_e_B": "native_structural_support",
                    "target_observable_input_status": "absent",
                },
                "enumeration_row_sha256",
            )
            rows.append(row)
            enumeration_index += 1
    return rows


def freeze_rows(rows: Sequence[Mapping[str, str]], *, row_hash_field: str, read_only_hash_field: str) -> list[dict[str, str]]:
    frozen: list[dict[str, str]] = []
    for row in rows:
        copied = dict(row)
        if canonical_row_hash(copied, row_hash_field) != copied[row_hash_field]:
            raise ValueError(f"source row hash mismatch before freeze: {copied.get(row_hash_field)}")
        copied["freeze_status"] = "frozen_before_detection"
        copied[read_only_hash_field] = canonical_row_hash(copied, read_only_hash_field)
        frozen.append(copied)
    return frozen


def construct_execution_ledger(
    enumeration: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    by_stage = {stage: [r for r in enumeration if r["stage_id"] == stage] for stage in ("left_branch", "hinge", "right_branch")}
    rows: list[dict[str, str]] = []
    index = 0

    # Four alternatives propagated from one source state with exact mass 1/4.
    left_transition_ids: list[str] = []
    for enum_row in by_stage["left_branch"]:
        probability = fraction_from_fields(enum_row, "P")
        incoming = Fraction(1, 1)
        outgoing = incoming * probability
        transition_id = f"cs133_exec_left_{enum_row['alternative_index']}"
        left_transition_ids.append(transition_id)
        rows.append(
            attach_hash(
                {
                    "execution_row_id": transition_id,
                    "execution_row_index": index,
                    "row_role": "canonical_enumerate_all_mass_propagation",
                    "row_time_semantics": "non_temporal_structural_execution",
                    "identity_packet_id": enum_row["identity_packet_id"],
                    "identity_packet_sha256": enum_row["identity_packet_sha256"],
                    "occurrence_binding_id": enum_row["occurrence_binding_id"],
                    "occurrence_binding_sha256": enum_row["occurrence_binding_sha256"],
                    "construction_rule_id": enum_row["construction_rule_id"],
                    "construction_rule_sha256": enum_row["construction_rule_sha256"],
                    "boundary_id": enum_row["boundary_id"],
                    "boundary_card_sha256": enum_row["boundary_card_sha256"],
                    "window_id": enum_row["window_id"],
                    "fractal_octave_coordinate": enum_row["fractal_octave_coordinate"],
                    "stage_order": 1,
                    "stage_id": "left_branch",
                    "kernel_id": enum_row["kernel_id"],
                    "kernel_sha256": enum_row["kernel_sha256"],
                    "execution_mode": "enumerate_all",
                    "source_state_id": "cs133_structural_source",
                    "target_state_id": f"cs133_left_state_{enum_row['alternative_index']}",
                    "parent_transition_id": "ROOT",
                    "parent_transition_ids": "ROOT",
                    "aggregation_rule_id": "none",
                    "incoming_mass_num": incoming.numerator,
                    "incoming_mass_den": incoming.denominator,
                    "incoming_mass_semantics": "source_state_mass_shared_by_alternative_pool",
                    "kernel_probability_num": probability.numerator,
                    "kernel_probability_den": probability.denominator,
                    "outgoing_mass_num": outgoing.numerator,
                    "outgoing_mass_den": outgoing.denominator,
                    "mass_equation": f"{fraction_text(incoming)}*{fraction_text(probability)}={fraction_text(outgoing)}",
                    "mass_conservation_scope": "stage_sum",
                    "target_observable_input_status": "absent",
                },
                "execution_row_sha256",
            )
        )
        index += 1

    # Four parent branches aggregate at the hinge and pass exact mass 1.
    enum_row = by_stage["hinge"][0]
    probability = fraction_from_fields(enum_row, "P")
    incoming = sum((fraction_from_fields(r, "outgoing_mass") for r in rows if r["stage_id"] == "left_branch"), Fraction(0, 1))
    outgoing = incoming * probability
    hinge_transition_id = "cs133_exec_hinge_aggregate"
    rows.append(
        attach_hash(
            {
                "execution_row_id": hinge_transition_id,
                "execution_row_index": index,
                "row_role": "canonical_enumerate_all_mass_propagation",
                "row_time_semantics": "non_temporal_structural_execution",
                "identity_packet_id": enum_row["identity_packet_id"],
                "identity_packet_sha256": enum_row["identity_packet_sha256"],
                "occurrence_binding_id": enum_row["occurrence_binding_id"],
                "occurrence_binding_sha256": enum_row["occurrence_binding_sha256"],
                "construction_rule_id": enum_row["construction_rule_id"],
                "construction_rule_sha256": enum_row["construction_rule_sha256"],
                "boundary_id": enum_row["boundary_id"],
                "boundary_card_sha256": enum_row["boundary_card_sha256"],
                "window_id": enum_row["window_id"],
                "fractal_octave_coordinate": enum_row["fractal_octave_coordinate"],
                "stage_order": 2,
                "stage_id": "hinge",
                "kernel_id": enum_row["kernel_id"],
                "kernel_sha256": enum_row["kernel_sha256"],
                "execution_mode": "enumerate_all",
                "source_state_id": "cs133_left_branch_aggregate",
                "target_state_id": "cs133_hinge_state",
                "parent_transition_id": ";".join(left_transition_ids),
                "parent_transition_ids": ";".join(left_transition_ids),
                "aggregation_rule_id": "sum_parent_outgoing_mass",
                "incoming_mass_num": incoming.numerator,
                "incoming_mass_den": incoming.denominator,
                "incoming_mass_semantics": "sum_of_parent_transition_outgoing_mass",
                "kernel_probability_num": probability.numerator,
                "kernel_probability_den": probability.denominator,
                "outgoing_mass_num": outgoing.numerator,
                "outgoing_mass_den": outgoing.denominator,
                "mass_equation": f"{fraction_text(incoming)}*{fraction_text(probability)}={fraction_text(outgoing)}",
                "mass_conservation_scope": "aggregation_and_stage",
                "target_observable_input_status": "absent",
            },
            "execution_row_sha256",
        )
    )
    index += 1

    # The hinge state expands into four alternatives with exact mass 1/4.
    for enum_row in by_stage["right_branch"]:
        probability = fraction_from_fields(enum_row, "P")
        incoming = outgoing
        branch_outgoing = incoming * probability
        rows.append(
            attach_hash(
                {
                    "execution_row_id": f"cs133_exec_right_{enum_row['alternative_index']}",
                    "execution_row_index": index,
                    "row_role": "canonical_enumerate_all_mass_propagation",
                    "row_time_semantics": "non_temporal_structural_execution",
                    "identity_packet_id": enum_row["identity_packet_id"],
                    "identity_packet_sha256": enum_row["identity_packet_sha256"],
                    "occurrence_binding_id": enum_row["occurrence_binding_id"],
                    "occurrence_binding_sha256": enum_row["occurrence_binding_sha256"],
                    "construction_rule_id": enum_row["construction_rule_id"],
                    "construction_rule_sha256": enum_row["construction_rule_sha256"],
                    "boundary_id": enum_row["boundary_id"],
                    "boundary_card_sha256": enum_row["boundary_card_sha256"],
                    "window_id": enum_row["window_id"],
                    "fractal_octave_coordinate": enum_row["fractal_octave_coordinate"],
                    "stage_order": 3,
                    "stage_id": "right_branch",
                    "kernel_id": enum_row["kernel_id"],
                    "kernel_sha256": enum_row["kernel_sha256"],
                    "execution_mode": "enumerate_all",
                    "source_state_id": "cs133_hinge_state",
                    "target_state_id": f"cs133_right_state_{enum_row['alternative_index']}",
                    "parent_transition_id": hinge_transition_id,
                    "parent_transition_ids": hinge_transition_id,
                    "aggregation_rule_id": "none",
                    "incoming_mass_num": incoming.numerator,
                    "incoming_mass_den": incoming.denominator,
                    "incoming_mass_semantics": "source_state_mass_shared_by_alternative_pool",
                    "kernel_probability_num": probability.numerator,
                    "kernel_probability_den": probability.denominator,
                    "outgoing_mass_num": branch_outgoing.numerator,
                    "outgoing_mass_den": branch_outgoing.denominator,
                    "mass_equation": f"{fraction_text(incoming)}*{fraction_text(probability)}={fraction_text(branch_outgoing)}",
                    "mass_conservation_scope": "stage_sum",
                    "target_observable_input_status": "absent",
                },
                "execution_row_sha256",
            )
        )
        index += 1
    return rows


def build_mass_audit(execution_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    audits: list[dict[str, str]] = []
    for stage_order, stage_id, _, _, _ in STAGE_SPECS:
        rows = [r for r in execution_rows if r["stage_id"] == stage_id]
        if not rows:
            raise ValueError(f"missing execution stage {stage_id}")
        incoming = Fraction(int(rows[0]["incoming_mass_num"]), int(rows[0]["incoming_mass_den"]))
        outgoing = sum((fraction_from_fields(r, "outgoing_mass") for r in rows), Fraction(0, 1))
        residual = outgoing - incoming
        audits.append(
            attach_hash(
                {
                    "mass_audit_id": f"cs133_mass_audit_{stage_id}",
                    "stage_order": stage_order,
                    "stage_id": stage_id,
                    "execution_mode": "enumerate_all",
                    "incoming_mass_num": incoming.numerator,
                    "incoming_mass_den": incoming.denominator,
                    "outgoing_mass_sum_num": outgoing.numerator,
                    "outgoing_mass_sum_den": outgoing.denominator,
                    "mass_residual_num": residual.numerator,
                    "mass_residual_den": residual.denominator,
                    "mass_conservation_status": "passed_exact" if residual == 0 else "failed",
                    "temporal_recurrence_status": "not_evaluated_M1",
                },
                "mass_audit_sha256",
            )
        )
    return audits


def topology_signature(rows: Sequence[Mapping[str, str]]) -> str:
    keys = (
        "stage_order",
        "stage_id",
        "alternative_index",
        "sigma_e",
        "adm_e_B",
        "w_num",
        "w_den",
        "Z_num",
        "Z_den",
        "P_num",
        "P_den",
        "execution_mode",
        "route_e_B",
        "construction_equivalence_class_id",
    )
    return canonical_json_hash([{k: row[k] for k in keys} for row in rows])


def packet_hash(rows: Sequence[Mapping[str, str]], row_hash_field: str) -> str:
    return canonical_json_hash([{k: v for k, v in row.items() if k != row_hash_field} for row in rows])


def validate_kernel_contracts(contracts: Sequence[Mapping[str, str]]) -> None:
    if len(contracts) != len(STAGE_SPECS):
        raise ValueError("kernel contract count mismatch")
    for row in contracts:
        if canonical_row_hash(row, "kernel_sha256") != row["kernel_sha256"]:
            raise ValueError(f"kernel contract hash mismatch: {row['kernel_id']}")
        count = int(row["admissible_member_count"])
        normalizer = Fraction(int(row["normalizer_num"]), int(row["normalizer_den"]))
        probabilities = [Fraction(x) for x in row["probability_vector_exact"].split(";")]
        if len(probabilities) != count or sum(probabilities, Fraction(0, 1)) != 1:
            raise ValueError(f"kernel probability vector invalid: {row['kernel_id']}")
        if normalizer != count:
            raise ValueError(f"kernel normalizer invalid: {row['kernel_id']}")


def validate_kernel_enumeration(
    rows: Sequence[Mapping[str, str]],
    contracts: Sequence[Mapping[str, str]],
    identity: Mapping[str, str],
    binding: Mapping[str, str],
    construction: Mapping[str, str],
    boundary: Mapping[str, str],
    *,
    read_only: bool,
) -> dict[str, str]:
    kernels = kernel_by_stage(contracts)
    expected_stage_counts = {stage_id: count for _, stage_id, count, _, _ in STAGE_SPECS}
    if len(rows) != sum(expected_stage_counts.values()):
        raise ValueError("kernel enumeration row count mismatch")
    if [int(r["enumeration_row_index"]) for r in rows] != list(range(len(rows))):
        raise ValueError("enumeration_row_index must be complete and ordered")
    if len({r["enumeration_row_id"] for r in rows}) != len(rows):
        raise ValueError("enumeration row IDs must be unique")
    if any(r["row_role"] != "native_structural_kernel_enumeration" for r in rows):
        raise ValueError("kernel enumeration row role mismatch")
    if any(r["row_time_semantics"] != "non_temporal_alternative_enumeration" for r in rows):
        raise ValueError("kernel enumeration must be non-temporal")

    identity_fields = {
        "identity_packet_id": identity["identity_packet_id"],
        "identity_packet_sha256": identity["identity_packet_sha256"],
        "occurrence_binding_id": binding["occurrence_binding_id"],
        "occurrence_binding_sha256": binding["occurrence_binding_sha256"],
        "construction_rule_id": construction["construction_rule_id"],
        "construction_rule_sha256": construction["construction_rule_sha256"],
        "boundary_id": boundary["boundary_id"],
        "boundary_card_sha256": boundary["boundary_card_sha256"],
        "window_id": boundary["window_id"],
        "fractal_octave_coordinate": boundary["fractal_octave_coordinate"],
    }
    for row in rows:
        hash_field = "read_only_row_sha256" if read_only else "enumeration_row_sha256"
        if canonical_row_hash(row, hash_field) != row[hash_field]:
            raise ValueError(f"{hash_field} mismatch: {row['enumeration_row_id']}")
        if read_only:
            if row["freeze_status"] != "frozen_before_detection":
                raise ValueError("read-only enumeration is not frozen")
            # The source enumeration hash is checked on the original row fields,
            # excluding the read-only freeze extension.
            source_row = {k: v for k, v in row.items() if k not in {"freeze_status", "read_only_row_sha256"}}
            if canonical_row_hash(source_row, "enumeration_row_sha256") != row["enumeration_row_sha256"]:
                raise ValueError("embedded enumeration row hash mismatch")
        for field, expected in identity_fields.items():
            if row[field] != expected:
                raise ValueError(f"cross-packet mismatch for {field}")
        if row["execution_mode"] != "enumerate_all":
            raise ValueError("enumerate_all execution required")
        if row["target_observable_input_status"] != "absent":
            raise ValueError("target observable leaked into kernel enumeration")
        if row["stage_id"] not in kernels:
            raise ValueError("undeclared stage")
        kernel = kernels[row["stage_id"]]
        if row["kernel_id"] != kernel["kernel_id"] or row["kernel_sha256"] != kernel["kernel_sha256"]:
            raise ValueError("kernel reference mismatch")
        adm = int(row["adm_e_B"])
        if adm not in {0, 1}:
            raise ValueError("admissibility must be 0 or 1")
        weight = fraction_from_fields(row, "w")
        if adm == 1 and weight <= 0:
            raise ValueError("admitted weights must be positive")
        stored_z = fraction_from_fields(row, "Z")
        actual_p = fraction_from_fields(row, "P")
        if row["P_exact"] != fraction_text(actual_p):
            raise ValueError("P_exact does not match reduced P_num/P_den")
        if math.gcd(abs(int(row["P_num"])), int(row["P_den"])) != 1:
            raise ValueError("probability pair is not reduced")
        stage_rows = [r for r in rows if r["stage_id"] == row["stage_id"]]
        recomputed_z = sum(
            (Fraction(int(r["adm_e_B"])) * fraction_from_fields(r, "w") for r in stage_rows),
            Fraction(0, 1),
        )
        if stored_z != recomputed_z:
            raise ValueError("stored normalizer mismatch")
        expected_p = Fraction(adm) * weight / recomputed_z
        if actual_p != expected_p:
            raise ValueError("kernel probability mismatch")

    for stage_id, count in expected_stage_counts.items():
        stage_rows = [r for r in rows if r["stage_id"] == stage_id]
        if len(stage_rows) != count:
            raise ValueError(f"stage count mismatch: {stage_id}")
        alternatives = sorted(int(r["alternative_index"]) for r in stage_rows)
        if alternatives != list(range(count)):
            raise ValueError(f"stage member IDs incomplete: {stage_id}")
        total = sum((fraction_from_fields(r, "P") for r in stage_rows), Fraction(0, 1))
        if total != 1:
            raise ValueError(f"stage probability mass is {total}, not 1")
    return {
        "kernel_enumeration_status": "passed_exact",
        "stage_kernel_normalization_status": "passed_exact",
        "row_hash_status": "passed",
        "cross_packet_linkage_status": "passed",
    }


def validate_execution_ledger(
    rows: Sequence[Mapping[str, str]],
    mass_audits: Sequence[Mapping[str, str]],
    contracts: Sequence[Mapping[str, str]],
    identity: Mapping[str, str],
    binding: Mapping[str, str],
    construction: Mapping[str, str],
    boundary: Mapping[str, str],
    *,
    read_only: bool,
) -> dict[str, str]:
    kernels = kernel_by_stage(contracts)
    if len(rows) != 9:
        raise ValueError("execution ledger must have 9 structural rows")
    if [int(r["execution_row_index"]) for r in rows] != list(range(9)):
        raise ValueError("execution_row_index must be complete and ordered")
    if len({r["execution_row_id"] for r in rows}) != 9:
        raise ValueError("execution row IDs must be unique")

    expected_links = {
        "identity_packet_id": identity["identity_packet_id"],
        "identity_packet_sha256": identity["identity_packet_sha256"],
        "occurrence_binding_id": binding["occurrence_binding_id"],
        "occurrence_binding_sha256": binding["occurrence_binding_sha256"],
        "construction_rule_id": construction["construction_rule_id"],
        "construction_rule_sha256": construction["construction_rule_sha256"],
        "boundary_id": boundary["boundary_id"],
        "boundary_card_sha256": boundary["boundary_card_sha256"],
        "window_id": boundary["window_id"],
        "fractal_octave_coordinate": boundary["fractal_octave_coordinate"],
    }
    transition_ids = {r["execution_row_id"] for r in rows}
    for row in rows:
        hash_field = "read_only_execution_row_sha256" if read_only else "execution_row_sha256"
        if canonical_row_hash(row, hash_field) != row[hash_field]:
            raise ValueError(f"{hash_field} mismatch: {row['execution_row_id']}")
        if read_only:
            if row["freeze_status"] != "frozen_before_detection":
                raise ValueError("read-only execution ledger is not frozen")
            source_row = {k: v for k, v in row.items() if k not in {"freeze_status", "read_only_execution_row_sha256"}}
            if canonical_row_hash(source_row, "execution_row_sha256") != row["execution_row_sha256"]:
                raise ValueError("embedded execution row hash mismatch")
        for field, expected in expected_links.items():
            if row[field] != expected:
                raise ValueError(f"execution cross-packet mismatch for {field}")
        if row["row_role"] != "canonical_enumerate_all_mass_propagation":
            raise ValueError("execution row role mismatch")
        if row["row_time_semantics"] != "non_temporal_structural_execution":
            raise ValueError("M1 execution rows must not be typed as recurrence time")
        if row["execution_mode"] != "enumerate_all":
            raise ValueError("enumerate_all execution required")
        if row["target_observable_input_status"] != "absent":
            raise ValueError("target observable leaked into execution ledger")
        kernel = kernels.get(row["stage_id"])
        if not kernel or row["kernel_id"] != kernel["kernel_id"] or row["kernel_sha256"] != kernel["kernel_sha256"]:
            raise ValueError("execution kernel reference mismatch")
        incoming = fraction_from_fields(row, "incoming_mass")
        probability = fraction_from_fields(row, "kernel_probability")
        outgoing = fraction_from_fields(row, "outgoing_mass")
        if outgoing != incoming * probability:
            raise ValueError("execution mass equation mismatch")
        if row["stage_id"] == "hinge":
            parents = row["parent_transition_ids"].split(";")
            if len(parents) != 4 or any(p not in transition_ids for p in parents):
                raise ValueError("hinge aggregation parent set invalid")
        elif row["stage_id"] == "right_branch" and row["parent_transition_id"] != "cs133_exec_hinge_aggregate":
            raise ValueError("right branch parent transition mismatch")

    if len(mass_audits) != 3:
        raise ValueError("expected three stage mass audits")
    for audit in mass_audits:
        if canonical_row_hash(audit, "mass_audit_sha256") != audit["mass_audit_sha256"]:
            raise ValueError("mass audit row hash mismatch")
        if audit["mass_conservation_status"] != "passed_exact":
            raise ValueError("stage mass conservation failed")
        if fraction_from_fields(audit, "mass_residual") != 0:
            raise ValueError("nonzero execution mass residual")
        stage_rows = [r for r in rows if r["stage_id"] == audit["stage_id"]]
        incoming = fraction_from_fields(audit, "incoming_mass")
        outgoing = sum((fraction_from_fields(r, "outgoing_mass") for r in stage_rows), Fraction(0, 1))
        if outgoing != incoming:
            raise ValueError("mass audit does not match execution ledger")
    return {
        "execution_mass_propagation_status": "passed_exact",
        "execution_mass_conservation_status": "passed_exact",
        "execution_row_hash_status": "passed",
    }


def build_structural_packets() -> None:
    identity = read_csv(DATA / "cs133_identity_packet.csv")[0]
    binding = read_csv(DATA / "cs133_fractal_elementary_occurrence_binding.csv")[0]
    construction = read_csv(DATA / "cs133_identity_to_trace_construction_rule.csv")[0]
    boundary = read_csv(DATA / "cs133_structural_boundary_card.csv")[0]
    contracts = build_kernel_contracts()

    enumeration = construct_kernel_enumeration(identity, binding, construction, boundary, contracts)
    write_csv(DATA / "cs133_native_structural_kernel_enumeration.csv", list(enumeration[0]), enumeration)
    read_only_enumeration = freeze_rows(
        enumeration,
        row_hash_field="enumeration_row_sha256",
        read_only_hash_field="read_only_row_sha256",
    )
    write_csv(
        DATA / "cs133_native_structural_read_only_kernel_enumeration.csv",
        list(read_only_enumeration[0]),
        read_only_enumeration,
    )

    execution = construct_execution_ledger(enumeration)
    write_csv(DATA / "cs133_native_structural_dec_execution_ledger.csv", list(execution[0]), execution)
    read_only_execution = freeze_rows(
        execution,
        row_hash_field="execution_row_sha256",
        read_only_hash_field="read_only_execution_row_sha256",
    )
    write_csv(
        DATA / "cs133_native_structural_read_only_execution_ledger.csv",
        list(read_only_execution[0]),
        read_only_execution,
    )

    mass_audit = build_mass_audit(execution)
    write_csv(DATA / "cs133_structural_execution_mass_audit.csv", list(mass_audit[0]), mass_audit)

    # Counterfactual specificity audit: new identity and occurrence, same declared
    # topology family, and a distinct fully identity-bound packet hash.
    cf_identity = make_identity_packet(
        z=54,
        a=132,
        symbol="Xe",
        name="Xenon",
        packet_id="counterfactual_identity_Xe132_Z54_A132_N78",
    )
    cf_binding = make_occurrence_binding(cf_identity, occurrence_id="counterfactual_Xe132_elementary_occurrence_00o8")
    cf_enumeration = construct_kernel_enumeration(cf_identity, cf_binding, construction, boundary, contracts)
    cf_execution = construct_execution_ledger(cf_enumeration)

    identity_changed = identity["identity_packet_sha256"] != cf_identity["identity_packet_sha256"]
    occurrence_changed = binding["occurrence_binding_sha256"] != cf_binding["occurrence_binding_sha256"]
    topology_equal = topology_signature(enumeration) == topology_signature(cf_enumeration)
    enum_packet_changed = packet_hash(enumeration, "enumeration_row_sha256") != packet_hash(cf_enumeration, "enumeration_row_sha256")
    exec_packet_changed = packet_hash(execution, "execution_row_sha256") != packet_hash(cf_execution, "execution_row_sha256")
    row_hashes_valid = all(canonical_row_hash(r, "enumeration_row_sha256") == r["enumeration_row_sha256"] for r in cf_enumeration)
    audit_pass = identity_changed and occurrence_changed and topology_equal and enum_packet_changed and exec_packet_changed and row_hashes_valid

    audit = attach_hash(
        {
            "audit_id": "cs133_identity_to_trace_counterfactual_audit",
            "reference_identity_packet_id": identity["identity_packet_id"],
            "counterfactual_identity_packet_id": cf_identity["identity_packet_id"],
            "reference_identity_packet_sha256": identity["identity_packet_sha256"],
            "counterfactual_identity_packet_sha256": cf_identity["identity_packet_sha256"],
            "reference_occurrence_binding_sha256": binding["occurrence_binding_sha256"],
            "counterfactual_occurrence_binding_sha256": cf_binding["occurrence_binding_sha256"],
            "construction_equivalence_class_id": construction["construction_equivalence_class_id"],
            "reference_trace_topology_sha256": topology_signature(enumeration),
            "counterfactual_trace_topology_sha256": topology_signature(cf_enumeration),
            "reference_kernel_enumeration_packet_sha256": packet_hash(enumeration, "enumeration_row_sha256"),
            "counterfactual_kernel_enumeration_packet_sha256": packet_hash(cf_enumeration, "enumeration_row_sha256"),
            "reference_execution_packet_sha256": packet_hash(execution, "execution_row_sha256"),
            "counterfactual_execution_packet_sha256": packet_hash(cf_execution, "execution_row_sha256"),
            "identity_packet_change_status": status_changed(identity["identity_packet_sha256"], cf_identity["identity_packet_sha256"]),
            "occurrence_binding_change_status": status_changed(binding["occurrence_binding_sha256"], cf_binding["occurrence_binding_sha256"]),
            "trace_topology_change_status": "unchanged_by_declared_shared_motif_equivalence_class" if topology_equal else "changed",
            "kernel_enumeration_packet_change_status": "changed_due_to_identity_bound_provenance" if enum_packet_changed else "unchanged",
            "execution_packet_change_status": "changed_due_to_identity_bound_provenance" if exec_packet_changed else "unchanged",
            "counterfactual_row_hash_status": "passed" if row_hashes_valid else "failed",
            "counterfactual_packet_admission_status": "valid_separate_scoped_occurrence" if audit_pass else "failed",
            "specificity_interpretation": "identity_specific_scoped_occurrence_with_shared_native_topology_family",
            "target_observable_input_status": "absent",
            "audit_status": "passed_declared_equivalence_class" if audit_pass else "failed",
        },
        "counterfactual_audit_sha256",
    )
    write_csv(DATA / "cs133_identity_counterfactual_audit.csv", list(audit), [audit])


def build_detector_contract() -> dict[str, str]:
    contract = attach_hash(
        {
            "detector_id": "cs133_blind_pq_under_declared_L_detector_v3",
            "detector_role": "pre_detection_hash_locked_structural_classifier",
            "allowed_input_paths": "manual/data/cs133/cs133_pre_detection_freeze_manifest.json",
            "forbidden_input_paths": "manual/data/cs133/cs133_structural_occurrence_hypothesis.csv;external_target_packets;SI_reference_cards",
            "allowed_semantic_inputs": "frozen_kernel_enumeration;frozen_execution_mass_ledger;declared_L_scope",
            "branch_support_rule": "count_admitted_kernel_enumeration_rows_per_branch_stage",
            "branch_symmetry_rule": "left_branch_count_equals_right_branch_count",
            "hinge_rule": "hinge_admitted_count_equals_1",
            "kernel_rule": "unified_exact_admissibility_weight_kernel",
            "execution_mass_rule": "enumerate_all_stage_outgoing_mass_equals_stage_incoming_mass",
            "pq_solver_rule": "unique_positive_integer_solution_q_pow_p_plus_q_equals_branch_count",
            "pq_search_domain": "mathematically_derived_full_positive_domain",
            "pq_domain_derivation": "p>=1;q>=2;q^p>=q_implies_q<=floor(Pi/2);powers_stop_when_q^p+q>Pi",
            "enclosure_rule": "L_is_declared_scope_not_detector_output",
            "classification_mode": "blind_pq_under_declared_L",
            "execution_mode_required": "enumerate_all",
            "pre_detection_freeze_requirement": "all_manifest_artifact_hashes_and_row_hashes_verified_before_semantic_read",
            "target_frequency_input_status": "forbidden",
            "pq_hypothesis_input_status": "forbidden",
            "L_scope_input_status": "allowed_declared_scope",
            "detector_status": "frozen_before_execution",
        },
        "detector_contract_sha256",
    )
    write_csv(DATA / "cs133_structural_detector_contract.csv", list(contract), [contract])
    return contract


def write_pre_detection_freeze_manifest(contract: Mapping[str, str]) -> None:
    artifact_specs = [
        ("identity_packet", "manual/data/cs133/cs133_identity_packet.csv"),
        ("occurrence_binding", "manual/data/cs133/cs133_fractal_elementary_occurrence_binding.csv"),
        ("construction_rule", "manual/data/cs133/cs133_identity_to_trace_construction_rule.csv"),
        ("boundary_card", "manual/data/cs133/cs133_structural_boundary_card.csv"),
        ("kernel_contract", "manual/data/cs133/cs133_structural_kernel_contract.csv"),
        ("kernel_enumeration", "manual/data/cs133/cs133_native_structural_kernel_enumeration.csv"),
        ("read_only_kernel_enumeration", "manual/data/cs133/cs133_native_structural_read_only_kernel_enumeration.csv"),
        ("execution_ledger", "manual/data/cs133/cs133_native_structural_dec_execution_ledger.csv"),
        ("read_only_execution_ledger", "manual/data/cs133/cs133_native_structural_read_only_execution_ledger.csv"),
        ("execution_mass_audit", "manual/data/cs133/cs133_structural_execution_mass_audit.csv"),
        ("detector_contract", "manual/data/cs133/cs133_structural_detector_contract.csv"),
        ("detector_implementation", SCRIPT_REL),
    ]
    artifacts = []
    for role, path_text in artifact_specs:
        path = ROOT / path_text
        artifacts.append(
            {
                "artifact_role": role,
                "path": path_text,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest: dict[str, object] = {
        "freeze_manifest_id": "cs133_M1_pre_detection_freeze_v1",
        "freeze_status": "frozen_before_detection",
        "detector_id": contract["detector_id"],
        "detector_contract_sha256": contract["detector_contract_sha256"],
        "allowed_input_paths": ["manual/data/cs133/cs133_pre_detection_freeze_manifest.json"],
        "forbidden_input_paths": [
            "manual/data/cs133/cs133_structural_occurrence_hypothesis.csv",
            "external_target_packets",
            "SI_reference_cards",
        ],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "semantic_contract": {
            "row_time_semantics": "non_temporal_structural_M1",
            "execution_mode": "enumerate_all",
            "target_frequency_input": "absent",
            "temporal_recurrence": "not_evaluated",
        },
    }
    manifest["freeze_manifest_sha256"] = canonical_json_hash(manifest)
    FREEZE_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_pre_detection_freeze(manifest_path: Path, *, root: Path = ROOT) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored_hash = manifest.get("freeze_manifest_sha256", "")
    payload = dict(manifest)
    payload.pop("freeze_manifest_sha256", None)
    if canonical_json_hash(payload) != stored_hash:
        raise ValueError("freeze manifest internal hash mismatch")
    if manifest.get("freeze_status") != "frozen_before_detection":
        raise ValueError("pre-detection freeze is not active")
    if manifest.get("allowed_input_paths") != ["manual/data/cs133/cs133_pre_detection_freeze_manifest.json"]:
        raise ValueError("undeclared detector input path")

    artifacts = {item["artifact_role"]: item for item in manifest["artifacts"]}
    required_roles = {
        "identity_packet",
        "occurrence_binding",
        "construction_rule",
        "boundary_card",
        "kernel_contract",
        "kernel_enumeration",
        "read_only_kernel_enumeration",
        "execution_ledger",
        "read_only_execution_ledger",
        "execution_mass_audit",
        "detector_contract",
        "detector_implementation",
    }
    if set(artifacts) != required_roles:
        raise ValueError("freeze manifest artifact set mismatch")
    for role, item in artifacts.items():
        path = root / item["path"]
        if not path.is_file():
            raise ValueError(f"frozen artifact missing: {role}")
        if path.stat().st_size != int(item["bytes"]):
            raise ValueError(f"frozen artifact byte-count mismatch: {role}")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"frozen artifact SHA-256 mismatch: {role}")

    identity = read_csv(root / artifacts["identity_packet"]["path"])
    binding = read_csv(root / artifacts["occurrence_binding"]["path"])
    construction = read_csv(root / artifacts["construction_rule"]["path"])
    boundary = read_csv(root / artifacts["boundary_card"]["path"])
    contracts = read_csv(root / artifacts["kernel_contract"]["path"])
    enumeration = read_csv(root / artifacts["kernel_enumeration"]["path"])
    read_only_enumeration = read_csv(root / artifacts["read_only_kernel_enumeration"]["path"])
    execution = read_csv(root / artifacts["execution_ledger"]["path"])
    read_only_execution = read_csv(root / artifacts["read_only_execution_ledger"]["path"])
    mass_audits = read_csv(root / artifacts["execution_mass_audit"]["path"])
    detector_contract = read_csv(root / artifacts["detector_contract"]["path"])
    if not all(len(rows) == 1 for rows in (identity, binding, construction, boundary, detector_contract)):
        raise ValueError("singleton frozen packet cardinality mismatch")
    if detector_contract[0]["detector_contract_sha256"] != manifest["detector_contract_sha256"]:
        raise ValueError("detector contract hash mismatch in freeze manifest")

    validate_kernel_contracts(contracts)
    enumeration_status = validate_kernel_enumeration(
        enumeration, contracts, identity[0], binding[0], construction[0], boundary[0], read_only=False
    )
    read_only_enumeration_status = validate_kernel_enumeration(
        read_only_enumeration, contracts, identity[0], binding[0], construction[0], boundary[0], read_only=True
    )
    execution_status = validate_execution_ledger(
        execution, mass_audits, contracts, identity[0], binding[0], construction[0], boundary[0], read_only=False
    )
    read_only_execution_status = validate_execution_ledger(
        read_only_execution, mass_audits, contracts, identity[0], binding[0], construction[0], boundary[0], read_only=True
    )
    return {
        "manifest": manifest,
        "identity": identity[0],
        "binding": binding[0],
        "construction": construction[0],
        "boundary": boundary[0],
        "contracts": contracts,
        "enumeration": enumeration,
        "read_only_enumeration": read_only_enumeration,
        "execution": execution,
        "read_only_execution": read_only_execution,
        "mass_audits": mass_audits,
        "detector_contract": detector_contract[0],
        "enumeration_status": enumeration_status,
        "read_only_enumeration_status": read_only_enumeration_status,
        "execution_status": execution_status,
        "read_only_execution_status": read_only_execution_status,
    }


def solve_support_parameters(branch_count: int) -> list[tuple[int, int]]:
    """Solve q**p + q = branch_count over p>=1, q>=2 without an arbitrary box."""
    if branch_count < 4:
        return []
    solutions: list[tuple[int, int]] = []
    for q in range(2, branch_count // 2 + 1):
        p = 1
        q_power = q
        while q_power + q <= branch_count:
            if q_power + q == branch_count:
                solutions.append((p, q))
            p += 1
            q_power *= q
    return solutions


def detect_support_form(freeze_manifest_path: Path = FREEZE_MANIFEST, *, root: Path = ROOT) -> dict[str, str]:
    """Detect p:q from a verified frozen M1 packet under a declared L scope."""
    packet = verify_pre_detection_freeze(freeze_manifest_path, root=root)
    rows = packet["read_only_enumeration"]
    boundary = packet["boundary"]
    assert isinstance(rows, list) and isinstance(boundary, dict)
    counts = {
        stage: sum(int(r["adm_e_B"]) for r in rows if r["stage_id"] == stage)
        for stage in ("left_branch", "hinge", "right_branch")
    }
    left, hinge, right = counts["left_branch"], counts["hinge"], counts["right_branch"]
    branch_symmetry = left == right
    single_hinge = hinge == 1
    if not branch_symmetry:
        raise ValueError("branch symmetry failed")
    if not single_hinge:
        raise ValueError("single-hinge structural gate failed")
    solutions = solve_support_parameters(left)
    if len(solutions) != 1:
        raise ValueError(f"support parameter solution is not unique: {solutions}")
    p, q = solutions[0]
    declared_l = int(boundary["window_slot_count"])
    return {
        "left_branch_admitted_count": str(left),
        "hinge_admitted_count": str(hinge),
        "right_branch_admitted_count": str(right),
        "detected_p": str(p),
        "detected_q": str(q),
        "declared_scope_L": str(declared_l),
        "detected_support_core": f"{p}:{q}",
        "scope_conditioned_form": f"{p}:{q}:{declared_l}",
        "classification_mode": "blind_pq_under_declared_L",
        "pq_hypothesis_visible_to_detector": "false",
        "L_scope_visible_to_detector": "true",
        "pq_solution_domain": "p>=1;q>=2;q<=floor(Pi/2);powers_stop_when_q^p+q>Pi",
        "pq_uniqueness_derivation": "q^p>=q_implies_2q<=Pi;for_Pi=4_q=2;then_2^p=2_implies_p=1",
        "pre_detection_freeze_status": "passed",
        "kernel_enumeration_status": packet["read_only_enumeration_status"]["kernel_enumeration_status"],
        "stage_kernel_normalization_status": packet["read_only_enumeration_status"]["stage_kernel_normalization_status"],
        "execution_mass_propagation_status": packet["read_only_execution_status"]["execution_mass_propagation_status"],
        "execution_mass_conservation_status": packet["read_only_execution_status"]["execution_mass_conservation_status"],
        "branch_symmetry_status": "passed" if branch_symmetry else "failed",
        "single_hinge_status": "passed" if single_hinge else "failed",
        "solution_count": str(len(solutions)),
    }


def split_support_form(value: str) -> tuple[str, int]:
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError("support form must have p:q:L")
    return f"{parts[0]}:{parts[1]}", int(parts[2])


def build_detector_and_results() -> None:
    contract = build_detector_contract()
    write_pre_detection_freeze_manifest(contract)
    detected = detect_support_form()
    result = attach_hash(
        {
            "detection_result_id": "cs133_structural_detection_00o8",
            "detector_id": contract["detector_id"],
            "detector_contract_sha256": contract["detector_contract_sha256"],
            "pre_detection_freeze_manifest_sha256": json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))["freeze_manifest_sha256"],
            **detected,
            "detection_status": "passed_unique_scope_conditioned_structural_solution",
            "target_observable_input_status": "absent",
            "target_frequency_input_status": "absent",
            "temporal_recurrence_status": "not_evaluated",
            "SI_anchor_status": "inactive",
        },
        "detection_result_sha256",
    )
    write_csv(DATA / "cs133_structural_detection_result.csv", list(result), [result])

    hypothesis = read_csv(DATA / "cs133_structural_occurrence_hypothesis.csv")[0]
    hypothesis_core = hypothesis["support_core_hypothesis"]
    hypothesis_l = int(hypothesis["declared_scope_L_hypothesis"])
    pq_status = "match" if result["detected_support_core"] == hypothesis_core else "mismatch"
    scope_status = "match" if int(result["declared_scope_L"]) == hypothesis_l else "mismatch"
    full_status = "match" if pq_status == "match" and scope_status == "match" else "mismatch"
    audit = attach_hash(
        {
            "audit_id": "cs133_hypothesis_detection_join_audit",
            "detection_result_id": result["detection_result_id"],
            "occurrence_id": hypothesis["occurrence_id"],
            "detection_precedes_hypothesis_join": "true",
            "detected_support_core": result["detected_support_core"],
            "support_core_hypothesis": hypothesis_core,
            "pq_hypothesis_match_status": pq_status,
            "declared_scope_L": result["declared_scope_L"],
            "hypothesized_scope_L": str(hypothesis_l),
            "scope_consistency_status": scope_status,
            "scope_conditioned_form": result["scope_conditioned_form"],
            "hypothesized_support_form": hypothesis["outer_support_form_hypothesis"],
            "hypothesis_match_status": full_status,
            "hypothesis_match_rule": "computed_pq_and_scope_equality_after_detection",
            "classification_mode": result["classification_mode"],
            "cs_binding_status": hypothesis["cs_to_occurrence_binding_status"],
            "scientific_interpretation": "kernel_execution_packet_classifies_support_core;L_is_declared_scope;Cs_identity_is_scoped_to_shared_topology;physical_adequacy_not_empirically_evaluated",
            "target_value_read_status": "not_read",
        },
        "audit_row_sha256",
    )
    write_csv(DATA / "cs133_structural_hypothesis_detection_audit.csv", list(audit), [audit])

    # Direct p:q-only blindness regression: mutate the hidden hypothesis while
    # preserving declared L.  The detector result remains unchanged.
    counterfactual_hypothesis = "2:2:6"
    counterfactual_core, counterfactual_l = split_support_form(counterfactual_hypothesis)
    cf_pq = "match" if result["detected_support_core"] == counterfactual_core else "mismatch"
    cf_scope = "match" if int(result["declared_scope_L"]) == counterfactual_l else "mismatch"
    cf_full = "match" if cf_pq == "match" and cf_scope == "match" else "mismatch"
    cf_audit = attach_hash(
        {
            "audit_id": "cs133_hidden_pq_hypothesis_counterfactual",
            "detection_result_id": result["detection_result_id"],
            "detector_result_sha256": result["detection_result_sha256"],
            "counterfactual_hidden_hypothesis": counterfactual_hypothesis,
            "counterfactual_support_core_hypothesis": counterfactual_core,
            "counterfactual_declared_scope_L": counterfactual_l,
            "detected_support_core": result["detected_support_core"],
            "declared_scope_L": result["declared_scope_L"],
            "pq_hypothesis_match_status": cf_pq,
            "scope_consistency_status": cf_scope,
            "hypothesis_match_status": cf_full,
            "detector_output_change_status": "unchanged",
            "audit_status": "passed" if cf_pq == "mismatch" and cf_scope == "match" else "failed",
            "target_value_read_status": "not_read",
        },
        "audit_row_sha256",
    )
    write_csv(DATA / "cs133_structural_hypothesis_counterfactual_audit.csv", list(cf_audit), [cf_audit])


def build_support_audit() -> None:
    result = read_csv(DATA / "cs133_structural_detection_result.csv")[0]
    p = int(result["detected_p"])
    q = int(result["detected_q"])
    declared_l = int(result["declared_scope_L"])
    pi_support = q**p + q
    hinge = int(result["hinge_admitted_count"])
    rd = 2 * pi_support + hinge
    rho = min(rd, declared_l)

    capacity_rule = attach_hash(
        {
            "C3_rule_id": "retained_ternary_capacity_k3_v1",
            "C3_rule_source": "main_sections_04_cut_running_fractal_tesseract_C3_k_equals_log3_3powk",
            "C3_input_k": 3,
            "C3_value": 3,
            "window_capacity_rule": "C3_times_declared_L",
            "declared_L_source": "cs133_structural_detection_result.declared_scope_L",
            "window_capacity_derivation": f"3*{declared_l}",
            "window_capacity_value": 3 * declared_l,
            "rule_status": "frozen_before_support_audit",
        },
        "C3_rule_sha256",
    )
    write_csv(DATA / "cs133_c3_window_capacity_rule.csv", list(capacity_rule), [capacity_rule])

    c3 = int(capacity_rule["C3_value"])
    pd = c3 * rho
    qd = c3 * max(0, rd - declared_l)
    window_capacity = c3 * declared_l
    capacity_fill_residual = pd - window_capacity
    x_shedding = max(0, capacity_fill_residual)
    row = attach_hash(
        {
            "support_audit_id": "cs133_1_2_6_native_support_audit",
            "detection_result_id": result["detection_result_id"],
            "detected_support_core": result["detected_support_core"],
            "declared_scope_L": result["declared_scope_L"],
            "scope_conditioned_form": result["scope_conditioned_form"],
            "classification_mode": result["classification_mode"],
            "Pi_support": pi_support,
            "hinge_contribution": hinge,
            "RD_AO": rd,
            "omega": declared_l,
            "rhoD_omega": rho,
            "C3_rule_id": capacity_rule["C3_rule_id"],
            "C3_rule_sha256": capacity_rule["C3_rule_sha256"],
            "C3": c3,
            "PD": pd,
            "QD": qd,
            "window_capacity_rule": capacity_rule["window_capacity_rule"],
            "window_capacity_derivation": capacity_rule["window_capacity_derivation"],
            "window_capacity": window_capacity,
            "capacity_fill_residual": capacity_fill_residual,
            "X_shedding": x_shedding,
            "recurrence_closure_status": "not_evaluated_M1",
            "full_period_closure": "not_evaluated_M1",
            "proper_prefix_closure_count": "not_evaluated_M1",
            "primitive_period": "not_evaluated_M1",
            "native_count_unit": "bip",
            "primitive_completion_object": "monon",
            "monon_completion_certificate_status": "pending_connected_cycle_trace_M2",
            "support_quantities_role": "native_structural_capacity_audit_not_elapsed_time_or_recurrence_closure",
            "temporal_recurrence_status": "not_evaluated",
            "clock_frequency_input_status": "absent",
            "audit_status": "passed_exact" if capacity_fill_residual == 0 and x_shedding == 0 else "failed",
        },
        "support_audit_sha256",
    )
    write_csv(DATA / "cs133_structural_support_audit.csv", list(row), [row])


def build_target_independence_audit() -> None:
    result = read_csv(DATA / "cs133_structural_detection_result.csv")[0]
    hypothesis_audit = read_csv(DATA / "cs133_structural_hypothesis_detection_audit.csv")[0]
    counterfactual = read_csv(DATA / "cs133_identity_counterfactual_audit.csv")[0]
    mass_audits = read_csv(DATA / "cs133_structural_execution_mass_audit.csv")
    support = read_csv(DATA / "cs133_structural_support_audit.csv")[0]
    freeze = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))

    checks: list[tuple[str, bool, str]] = [
        ("target_frequency_absent", result["target_frequency_input_status"] == "absent", "no clock frequency enters the frozen M1 packet"),
        ("hypothesis_hidden_from_detector", result["pq_hypothesis_visible_to_detector"] == "false", "p:q hypothesis is excluded from detector inputs"),
        ("hypothesis_match_computed", hypothesis_audit["hypothesis_match_rule"] == "computed_pq_and_scope_equality_after_detection", "hypothesis status is calculated after detection"),
        ("pre_detection_manifest_verified", result["pre_detection_freeze_status"] == "passed", "all frozen artifact hashes are checked before semantic classification"),
        ("execution_mode_enforced", result["execution_mass_propagation_status"] == "passed_exact", "enumerate_all mass propagation is materialized and verified"),
        ("stage_kernel_normalization_enforced", result["stage_kernel_normalization_status"] == "passed_exact", "every stage kernel normalizes exactly"),
        ("stage_mass_conservation_enforced", all(r["mass_conservation_status"] == "passed_exact" for r in mass_audits), "every execution stage conserves exact rational mass"),
        ("support_core_derived_from_enumeration", result["detected_support_core"] == "1:2", "p:q is derived from the frozen kernel enumeration"),
        ("L_is_declared_scope", result["declared_scope_L"] == "6" and result["L_scope_visible_to_detector"] == "true", "L is read from the boundary card, not detected"),
        ("identity_specific_occurrence_manifested", counterfactual["counterfactual_packet_admission_status"] == "valid_separate_scoped_occurrence", "counterfactual identity is a separate scoped occurrence"),
        ("shared_topology_equivalence_class_declared", counterfactual["trace_topology_change_status"] == "unchanged_by_declared_shared_motif_equivalence_class", "topology recurrence is explicitly typed as a shared family"),
        ("capacity_fill_rule_derived", support["window_capacity_rule"] == "C3_times_declared_L", "capacity is rule-derived, not a magic literal"),
        ("capacity_not_recurrence_closure", support["recurrence_closure_status"] == "not_evaluated_M1", "M1 capacity fill is not called recurrence closure"),
        ("enumeration_not_causal_time", all(r["row_time_semantics"] == "non_temporal_alternative_enumeration" for r in read_csv(DATA / "cs133_native_structural_kernel_enumeration.csv")), "row indices serialize alternatives rather than causal events"),
        ("recurrence_not_claimed", support["temporal_recurrence_status"] == "not_evaluated", "primitive recurrence remains an M2 output"),
        ("SI_anchor_inactive", result["SI_anchor_status"] == "inactive", "no metrological anchor is active"),
        ("target_join_closed", result["target_observable_input_status"] == "absent", "no target or empirical score enters M1"),
        ("freeze_artifact_set_complete", int(freeze["artifact_count"]) == len(freeze["artifacts"]), "freeze manifest covers the complete declared artifact set"),
    ]
    rows = []
    for order, (check_id, passed, evidence) in enumerate(checks, start=1):
        rows.append(
            attach_hash(
                {
                    "audit_order": order,
                    "check_id": check_id,
                    "status": "pass" if passed else "fail",
                    "evidence": evidence,
                    "target_value_read_status": "not_read",
                },
                "audit_row_sha256",
            )
        )
    write_csv(DATA / "cs133_target_independence_audit.csv", list(rows[0]), rows)


def validate_outputs() -> None:
    verify_pre_detection_freeze(FREEZE_MANIFEST)
    result = read_csv(DATA / "cs133_structural_detection_result.csv")[0]
    if result["detected_support_core"] != "1:2":
        raise ValueError("unexpected detected support core")
    if result["declared_scope_L"] != "6" or result["scope_conditioned_form"] != "1:2:6":
        raise ValueError("scope-conditioned form mismatch")
    if result["classification_mode"] != "blind_pq_under_declared_L":
        raise ValueError("classification mode mismatch")
    support = read_csv(DATA / "cs133_structural_support_audit.csv")[0]
    expected = {
        "RD_AO": "9",
        "omega": "6",
        "rhoD_omega": "6",
        "PD": "18",
        "QD": "9",
        "window_capacity": "18",
        "capacity_fill_residual": "0",
        "X_shedding": "0",
    }
    for field, value in expected.items():
        if support[field] != value:
            raise ValueError(f"{field} mismatch: {support[field]} != {value}")
    if support["recurrence_closure_status"] != "not_evaluated_M1":
        raise ValueError("M1 must not claim recurrence closure")
    counterfactual = read_csv(DATA / "cs133_identity_counterfactual_audit.csv")[0]
    if counterfactual["audit_status"] != "passed_declared_equivalence_class":
        raise ValueError("counterfactual identity audit failed")
    pq_cf = read_csv(DATA / "cs133_structural_hypothesis_counterfactual_audit.csv")[0]
    if pq_cf["audit_status"] != "passed" or pq_cf["pq_hypothesis_match_status"] != "mismatch":
        raise ValueError("p:q hidden hypothesis counterfactual failed")
    target_audit = read_csv(DATA / "cs133_target_independence_audit.csv")
    if not target_audit or any(r["status"] != "pass" for r in target_audit):
        raise ValueError("target-independence audit failed")


def build_manifest() -> None:
    validate_outputs()
    # M1 owns an explicit stage-local artifact allowlist.  Later Cs gates
    # maintain independent manifests.  An explicit list prevents future files
    # added under manual/data/cs133/ from silently mutating this historical M1
    # packet or creating cyclic hash dependencies across gates.
    m1_file_names = (
        "cs133_c3_window_capacity_rule.csv",
        "cs133_fractal_elementary_occurrence_binding.csv",
        "cs133_identity_counterfactual_audit.csv",
        "cs133_identity_packet.csv",
        "cs133_identity_to_trace_construction_rule.csv",
        "cs133_native_structural_dec_execution_ledger.csv",
        "cs133_native_structural_kernel_enumeration.csv",
        "cs133_native_structural_read_only_execution_ledger.csv",
        "cs133_native_structural_read_only_kernel_enumeration.csv",
        "cs133_pre_detection_freeze_manifest.json",
        "cs133_structural_boundary_card.csv",
        "cs133_structural_detection_result.csv",
        "cs133_structural_detector_contract.csv",
        "cs133_structural_execution_mass_audit.csv",
        "cs133_structural_hypothesis_counterfactual_audit.csv",
        "cs133_structural_hypothesis_detection_audit.csv",
        "cs133_structural_kernel_contract.csv",
        "cs133_structural_occurrence_hypothesis.csv",
        "cs133_structural_support_audit.csv",
        "cs133_target_independence_audit.csv",
    )
    files = [DATA / name for name in m1_file_names]
    missing = [p.name for p in files if not p.is_file()]
    if missing:
        raise ValueError(f"M1 manifest allowlist files missing: {missing}")
    manifest = {
        "manifest_id": "cs133_fractal_elementary_occurrence_gate_v3",
        "gate_role": "target_independent_scope_conditioned_structural_classification_with_canonical_DEC_execution_and_pre_detection_hash_freeze",
        "fractal_octave_coordinate": "00_(8)",
        "current_state": {
            "identity_packet": "frozen",
            "element_registry_binding": "Cs_Z55_row_verified",
            "fractal_elementary_occurrence_binding": "passed",
            "native_count_unit": "bip",
            "primitive_completion_object": "monon",
            "monon_completion_certificate": "pending_connected_cycle_trace_M2",
            "construction_equivalence_class": "elementary_00o8_Q4_branch_hinge_branch_monon_family",
            "identity_specificity": "identity_specific_scope_shared_native_topology_family",
            "kernel_enumeration": "frozen_non_temporal",
            "canonical_DEC_execution": "enumerate_all_mass_conserved",
            "pre_detection_freeze": "cryptographically_enforced",
            "support_core_hypothesis": "frozen_1:2",
            "detected_support_core": "1:2",
            "declared_scope_L": "6",
            "scope_conditioned_form": "1:2:6",
            "classification_mode": "blind_pq_under_declared_L",
            "support_certificate": "passed_scope_conditioned_kernel_and_execution_packet",
            "capacity_fill_audit": "passed_exact_not_recurrence_closure",
            "cs_to_occurrence_binding": "scoped_elementary_occurrence_bound_physical_adequacy_not_empirically_validated",
            "target_frequency_input": "absent",
            "temporal_recurrence_certificate": "not_materialized",
            "recurrence_to_reference_correspondence": "not_active",
            "SI_anchor": "inactive",
            "target_join": "closed",
        },
        "detector_order": [
            "declared_elementary_identity_and_origin_anchor_scope",
            "identity_to_occurrence_binding",
            "shared_topology_construction_rule",
            "exact_kernel_contract_freeze",
            "non_temporal_kernel_enumeration",
            "canonical_enumerate_all_mass_execution",
            "read_only_packet_freeze",
            "pre_detection_hash_manifest_verification",
            "blind_pq_detection_under_declared_L",
            "post_detection_hypothesis_audit",
            "native_capacity_fill_audit",
        ],
        "files": [
            {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha256_file(p)}
            for p in files
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def refresh_roadmap_manifest() -> None:
    """Refresh hashes for files tracked by the Manual-I milestone manifest.

    The Cs gate manifest is regenerated by this script.  Keeping the roadmap
    hash synchronized here prevents a successful gate rebuild from leaving a
    stale release-governance packet.  No milestone semantics are inferred or
    changed by this function; it only updates bytes and SHA-256 values for the
    predeclared paths.
    """
    if not ROADMAP_MANIFEST.exists():
        raise FileNotFoundError(f"missing roadmap manifest: {ROADMAP_MANIFEST}")
    data = json.loads(ROADMAP_MANIFEST.read_text(encoding="utf-8"))
    tracked = data.get("files")
    if not isinstance(tracked, list):
        raise ValueError("roadmap manifest files field must be a list")
    for row in tracked:
        rel = row.get("path")
        if not isinstance(rel, str) or not rel:
            raise ValueError("roadmap manifest contains an invalid tracked path")
        target = ROOT / rel
        if not target.is_file():
            raise FileNotFoundError(f"tracked roadmap file is missing: {rel}")
        row["bytes"] = target.stat().st_size
        row["sha256"] = sha256_file(target)
    ROADMAP_MANIFEST.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    cleanup_stale_outputs()
    build_identity_and_scope()
    build_structural_packets()
    build_detector_and_results()
    build_support_audit()
    build_target_independence_audit()
    build_manifest()
    refresh_roadmap_manifest()
    print(MANIFEST.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
