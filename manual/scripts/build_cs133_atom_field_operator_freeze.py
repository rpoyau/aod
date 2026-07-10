#!/usr/bin/env python3
"""Freeze the target-blind Cs-scoped native atom-field interaction operator.

M3 reads only the admitted M2 native recurrence packet. It freezes an exact
finite-state, two-interaction phase-coincidence operator, its phase-alias
domain, interaction windows, zero-perturbation policy, response representation,
selector contract, controls, and SI-activation guard. It does not execute the
resonance search and does not read the SI caesium frequency, an observation
packet, a target value, a residual, or a score.
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
SCRIPT_REL = "manual/scripts/build_cs133_atom_field_operator_freeze.py"
M2_MANIFEST = DATA / "cs133_native_recurrence_manifest.json"
M2_CERTIFICATE = DATA / "cs133_native_recurrence_certificate.csv"
M2_STATES = DATA / "cs133_native_coupled_state_registry.csv"
M2_TRANSITIONS = DATA / "cs133_native_recurrence_transition_matrix.csv"
M2_COUPLING = DATA / "cs133_core_outer_coupling_operator.csv"
PRE_FREEZE = DATA / "cs133_atom_field_operator_pre_freeze_manifest.json"
FINAL_MANIFEST = DATA / "cs133_atom_field_operator_manifest.json"

OUTPUT_NAMES = (
    "cs133_atom_field_input_lock.csv",
    "cs133_drive_phase_domain.csv",
    "cs133_atom_field_interaction_window_policy.csv",
    "cs133_atom_field_operator_transition_rules.csv",
    "cs133_atom_field_response_function_contract.csv",
    "cs133_atom_field_exact_response_representation_registry.csv",
    "cs133_atom_field_zero_perturbation_policy.csv",
    "cs133_atom_field_resonance_selector_contract.csv",
    "cs133_atom_field_resonance_control_audit_plan.csv",
    "cs133_atom_field_si_activation_guard.csv",
    "cs133_atom_field_interaction_operator.csv",
    "cs133_atom_field_operator_pre_freeze_manifest.json",
    "cs133_atom_field_operator_manifest.json",
)

FORBIDDEN_TARGET_TOKENS = ("".join(("919", "263", "1770")), ",".join(("9", "192", "631", "770")))


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


def reduced_text(num: int, den: int) -> tuple[int, int, str]:
    value = Fraction(num, den)
    return value.numerator, value.denominator, f"{value.numerator}/{value.denominator}"


def verify_file_against_manifest(manifest: Mapping[str, object], path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    matches = [row for row in manifest.get("files", []) if row.get("path") == rel]
    if len(matches) != 1:
        raise ValueError(f"M2 manifest missing unique row for {rel}")
    row = matches[0]
    if path.stat().st_size != int(row["bytes"]):
        raise ValueError(f"M2 byte mismatch: {rel}")
    if sha256_file(path) != row["sha256"]:
        raise ValueError(f"M2 SHA-256 mismatch: {rel}")


def verify_m2_inputs() -> tuple[dict[str, str], dict[str, str], list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    manifest = json.loads(M2_MANIFEST.read_text(encoding="utf-8"))
    for path in (M2_CERTIFICATE, M2_STATES, M2_TRANSITIONS, M2_COUPLING):
        verify_file_against_manifest(manifest, path)
    certificate = read_one(M2_CERTIFICATE)
    coupling = read_one(M2_COUPLING)
    states = read_csv(M2_STATES)
    transitions = read_csv(M2_TRANSITIONS)
    required = {
        "certificate_status": "passed_native_recurrence_only",
        "duration_semantics": "realized_integer_bip_count",
        "full_period_closure": "passed",
        "proper_prefix_closure_count": "0",
        "exact_mass_conservation": "passed",
        "target_frequency_input_status": "absent",
        "observation_packet_input_status": "absent",
        "SI_anchor_status": "inactive",
    }
    for field, expected in required.items():
        if certificate.get(field) != expected:
            raise ValueError(f"M2 certificate field {field}={certificate.get(field)!r}, expected {expected!r}")
    n = int(certificate["primitive_recurrence_bip_count"])
    if n <= 0 or n % 2:
        raise ValueError("M3 current operator requires a positive even primitive recurrence")
    if len(states) != n or len(transitions) != n:
        raise ValueError("state/transition count does not match primitive recurrence")
    if coupling["native_coupled_state_A_id"] != certificate["native_coupled_state_A_id"]:
        raise ValueError("native state A mismatch")
    if coupling["native_coupled_state_B_id"] != certificate["native_coupled_state_B_id"]:
        raise ValueError("native state B mismatch")
    return certificate, coupling, states, transitions, manifest


def build_input_lock(certificate: Mapping[str, str], coupling: Mapping[str, str]) -> dict[str, str]:
    allowed = [
        M2_CERTIFICATE.relative_to(ROOT).as_posix(),
        M2_STATES.relative_to(ROOT).as_posix(),
        M2_TRANSITIONS.relative_to(ROOT).as_posix(),
        M2_COUPLING.relative_to(ROOT).as_posix(),
        M2_MANIFEST.relative_to(ROOT).as_posix(),
    ]
    return attach_hash(
        {
            "operator_input_lock_id": "cs133_atom_field_M3_input_lock_v1",
            "primitive_recurrence_id": certificate["recurrence_certificate_id"],
            "primitive_recurrence_certificate_sha256": certificate["recurrence_certificate_sha256"],
            "identity_packet_id": certificate["identity_packet_id"],
            "identity_packet_sha256": certificate["identity_packet_sha256"],
            "occurrence_binding_id": certificate["occurrence_binding_id"],
            "occurrence_binding_sha256": certificate["occurrence_binding_sha256"],
            "core_outer_coupling_operator_id": coupling["coupling_operator_id"],
            "core_outer_coupling_operator_sha256": coupling["coupling_operator_sha256"],
            "native_coupled_state_A_id": certificate["native_coupled_state_A_id"],
            "native_coupled_state_B_id": certificate["native_coupled_state_B_id"],
            "primitive_recurrence_bip_count": certificate["primitive_recurrence_bip_count"],
            "duration_semantics": certificate["duration_semantics"],
            "state_registry_file_sha256": sha256_file(M2_STATES),
            "transition_matrix_file_sha256": sha256_file(M2_TRANSITIONS),
            "recurrence_manifest_file_sha256": sha256_file(M2_MANIFEST),
            "allowed_input_paths": ";".join(allowed),
            "target_frequency_input_status": "absent",
            "observation_packet_input_status": "absent",
            "target_value_read_status": "not_read",
            "input_lock_status": "frozen_before_atom_field_operator_declaration",
        },
        "operator_input_lock_sha256",
    )


def build_phase_domain(n: int) -> list[dict[str, str]]:
    denominator = 2 * n
    rows: list[dict[str, str]] = []
    for k in range(denominator):
        num, den, text = reduced_text(k, denominator)
        rows.append(
            attach_hash(
                {
                    "drive_cadence_domain_id": "cs133_drive_phase_QmodZ_grid_2N_v1",
                    "candidate_order": k,
                    "raw_phase_num": k,
                    "raw_phase_den": denominator,
                    "canonical_phase_num": num,
                    "canonical_phase_den": den,
                    "canonical_phase_exact": text,
                    "drive_unit": "turns_per_bip",
                    "phase_equivalence_rule": "theta_equivalent_theta_plus_integer_turns",
                    "canonical_phase_domain": "0_le_theta_lt_1_turn_per_bip",
                    "alias_class_policy": "Q_mod_Z",
                    "alias_representative_rule": "reduced_fraction_in_half_open_unit_interval",
                    "alias_class_id": f"phase_alias_{num}_{den}",
                    "grid_rule_id": "two_samples_per_native_recurrence_slot_v1",
                    "grid_derivation": "k_over_2_times_primitive_recurrence_bip_count",
                    "primitive_recurrence_bip_count": n,
                    "grid_denominator": denominator,
                    "candidate_status": "frozen_for_target_blind_M4_search",
                    "target_frequency_input_status": "absent",
                },
                "phase_candidate_sha256",
            )
        )
    if len({(r["canonical_phase_num"], r["canonical_phase_den"]) for r in rows}) != denominator:
        raise ValueError("phase-domain canonical representatives are not unique")
    return rows


def build_windows(n: int) -> list[dict[str, str]]:
    primary = n // 2
    refinement = n - 1
    configs = [
        ("primary_half_cycle_window", "primary_alias_class_scan", primary, "primitive_recurrence_bip_count_div_2"),
        ("refinement_preclosure_window", "alias_resolution_refinement", refinement, "primitive_recurrence_bip_count_minus_1"),
    ]
    rows = []
    for order, (window_id, role, free_bips, rule) in enumerate(configs):
        pnum, pden, ptxt = reduced_text(free_bips, n)
        rows.append(
            attach_hash(
                {
                    "window_order": order,
                    "interaction_window_id": window_id,
                    "window_role": role,
                    "window_derivation_rule": rule,
                    "primitive_recurrence_bip_count": n,
                    "interaction_1_event_index": 0,
                    "free_evolution_bip_count": free_bips,
                    "interaction_2_event_index": free_bips,
                    "readout_event_index": free_bips + 1,
                    "native_phase_advance_num": pnum,
                    "native_phase_advance_den": pden,
                    "native_phase_advance_exact": ptxt,
                    "phase_comparison_rule": "delta_mod_1_equals_free_bips_times_drive_phase_minus_native_phase_advance",
                    "interaction_realization_type": "two_interaction_free_evolution_readout_finite_state",
                    "target_frequency_input_status": "absent",
                    "window_status": "frozen_before_search",
                },
                "window_policy_sha256",
            )
        )
    return rows


def build_transition_rules() -> list[dict[str, str]]:
    raw_rows = [
        {
            "rule_order": 0,
            "transition_rule_id": "prepare_native_state_A",
            "operator_stage": "state_preparation",
            "condition": "always",
            "source_state": "unprepared",
            "target_state": "native_coupled_state_A",
            "mass_assignment": "A=1/1;B=0/1",
            "phase_update_rule": "phase_register_set_to_0",
            "exact_mass_conservation_rule": "A_plus_B_equals_1",
        },
        {
            "rule_order": 1,
            "transition_rule_id": "balanced_first_interaction",
            "operator_stage": "interaction_1",
            "condition": "drive_enabled",
            "source_state": "native_coupled_state_A_or_B",
            "target_state": "balanced_native_state_packet",
            "mass_assignment": "A=1/2;B=1/2",
            "phase_update_rule": "retain_canonical_drive_phase",
            "exact_mass_conservation_rule": "1/2_plus_1/2_equals_1",
        },
        {
            "rule_order": 2,
            "transition_rule_id": "exact_free_evolution_phase_advance",
            "operator_stage": "free_evolution",
            "condition": "window_policy_selected",
            "source_state": "balanced_native_state_packet",
            "target_state": "phase_advanced_balanced_packet",
            "mass_assignment": "A=1/2;B=1/2",
            "phase_update_rule": "drive_phase_plus_free_bips_times_theta_mod_1;native_phase_plus_free_bips_over_N_mod_1",
            "exact_mass_conservation_rule": "mass_unchanged",
        },
        {
            "rule_order": 3,
            "transition_rule_id": "aligned_phase_recombination",
            "operator_stage": "interaction_2",
            "condition": "phase_delta_mod_1_equals_0",
            "source_state": "phase_advanced_balanced_packet",
            "target_state": "native_coupled_state_B",
            "mass_assignment": "A=0/1;B=1/1",
            "phase_update_rule": "phase_register_frozen_for_readout",
            "exact_mass_conservation_rule": "0_plus_1_equals_1",
        },
        {
            "rule_order": 4,
            "transition_rule_id": "anti_aligned_phase_recombination",
            "operator_stage": "interaction_2",
            "condition": "phase_delta_mod_1_equals_1/2",
            "source_state": "phase_advanced_balanced_packet",
            "target_state": "native_coupled_state_A",
            "mass_assignment": "A=1/1;B=0/1",
            "phase_update_rule": "phase_register_frozen_for_readout",
            "exact_mass_conservation_rule": "1_plus_0_equals_1",
        },
        {
            "rule_order": 5,
            "transition_rule_id": "generic_off_phase_recombination",
            "operator_stage": "interaction_2",
            "condition": "phase_delta_mod_1_not_in_{0,1/2}",
            "source_state": "phase_advanced_balanced_packet",
            "target_state": "balanced_native_state_packet",
            "mass_assignment": "A=1/2;B=1/2",
            "phase_update_rule": "phase_register_frozen_for_readout",
            "exact_mass_conservation_rule": "1/2_plus_1/2_equals_1",
        },
        {
            "rule_order": 6,
            "transition_rule_id": "read_native_state_B_mass",
            "operator_stage": "state_readout",
            "condition": "after_interaction_2",
            "source_state": "final_native_state_packet",
            "target_state": "response_packet",
            "mass_assignment": "response=M_B/(M_A+M_B)",
            "phase_update_rule": "none",
            "exact_mass_conservation_rule": "readout_does_not_modify_mass",
        },
    ]
    return [
        attach_hash(
            {
                **row,
                "arithmetic_domain": "exact_rational_finite_state_operator",
                "target_frequency_input_status": "absent",
                "rule_status": "frozen_not_executed",
            },
            "transition_rule_sha256",
        )
        for row in raw_rows
    ]


def build_response_contract(n: int) -> dict[str, str]:
    return attach_hash(
        {
            "response_function_id": "cs133_exact_phase_coincidence_response_v1",
            "arithmetic_domain": "exact_rational_finite_state_operator",
            "phase_delta_rule": "delta=mod1(free_evolution_bips*theta-native_phase_advance)",
            "aligned_condition": "delta=0",
            "aligned_response_num": 1,
            "aligned_response_den": 1,
            "anti_aligned_condition": "delta=1/2",
            "anti_aligned_response_num": 0,
            "anti_aligned_response_den": 1,
            "generic_off_phase_condition": "delta_not_in_{0,1/2}",
            "generic_off_phase_response_num": 1,
            "generic_off_phase_response_den": 2,
            "drive_off_response_num": 0,
            "drive_off_response_den": 1,
            "response_unit": "native_state_B_mass_fraction",
            "response_range_exact": "{0/1,1/2,1/1}",
            "primitive_recurrence_bip_count": n,
            "continuum_trigonometric_claim_status": "not_claimed",
            "decimal_comparison_status": "forbidden",
            "target_frequency_input_status": "absent",
            "response_contract_status": "frozen_before_search",
        },
        "response_function_sha256",
    )


def build_representation_registry() -> list[dict[str, str]]:
    rows = [
        {
            "representation_id": "exact_rational_response_v1",
            "arithmetic_domain": "exact_rational_finite_state_operator",
            "canonical_fields": "response_num;response_den",
            "exact_comparison_rule": "integer_cross_multiplication",
            "selected_for_current_operator": "true",
            "decimal_winner_policy": "forbidden",
            "status": "active_contract",
        },
        {
            "representation_id": "exact_algebraic_response_v1",
            "arithmetic_domain": "exact_algebraic_operator",
            "canonical_fields": "minimal_polynomial;root_index;isolating_interval_rational_bounds",
            "exact_comparison_rule": "algebraic_number_order_proof",
            "selected_for_current_operator": "false",
            "decimal_winner_policy": "forbidden",
            "status": "registry_only",
        },
        {
            "representation_id": "exact_symbolic_response_v1",
            "arithmetic_domain": "exact_symbolic_operator",
            "canonical_fields": "canonical_expression;canonical_expression_sha256;simplification_rule_id;comparison_proof_id",
            "exact_comparison_rule": "symbolic_proof_or_exact_order_certificate",
            "selected_for_current_operator": "false",
            "decimal_winner_policy": "forbidden",
            "status": "registry_only",
        },
    ]
    return [attach_hash(row, "representation_row_sha256") for row in rows]


def build_zero_perturbation_policy() -> dict[str, str]:
    return attach_hash(
        {
            "zero_perturbation_policy_id": "cs133_zero_perturbation_finite_state_policy_v1",
            "drive_strength_domain": "ideal_balanced_interaction_only",
            "drive_amplitude_policy_id": "cs133_ideal_balanced_interaction_amplitude_v1",
            "weak_drive_limit_rule": "not_applicable_to_declared_exact_balanced_finite_state_operator",
            "external_field_state": "zero",
            "thermal_motion_state": "zero",
            "collision_loading_state": "zero",
            "boundary_loading_state": "native_scope_only",
            "drive_amplitude_shift_state": "zero_by_operator_definition",
            "perturbation_parameter_order": "external_field;thermal_motion;collision_loading;boundary_loading;drive_amplitude_shift",
            "zero_perturbation_extraction_rule": "select_all_zero_perturbation_states_before_phase_scan",
            "driven_response_status": "operator_contract_only_not_executed",
            "unperturbed_resonance_label": "native_resonance_cadence_zero_perturbation_candidate",
            "physical_clock_state_interpretation_status": "pending_correspondence_mode_gate",
            "target_frequency_input_status": "absent",
            "policy_status": "frozen_before_search",
        },
        "zero_perturbation_policy_sha256",
    )


def build_selector_contract() -> dict[str, str]:
    return attach_hash(
        {
            "resonance_selector_id": "cs133_exact_two_window_alias_resolving_selector_v1",
            "drive_cadence_domain_id": "cs133_drive_phase_QmodZ_grid_2N_v1",
            "primary_window_id": "primary_half_cycle_window",
            "refinement_window_id": "refinement_preclosure_window",
            "selector_stage_order": "primary_exact_maxima;refinement_exact_maxima;alias_class_intersection;canonical_representative",
            "response_order_rule": "exact_rational_cross_multiplication",
            "alias_equivalence_rule": "Q_mod_Z",
            "canonical_representative_rule": "reduced_fraction_in_half_open_unit_interval",
            "unique_candidate_status": "exact_unique_candidate",
            "tied_candidate_status": "exact_tied_candidate_set",
            "interval_status": "rational_resonance_interval",
            "unresolved_status": "unresolved",
            "cadence_primary_object": "native_resonance_cadence_turns_per_bip",
            "period_inverse_rule": "invert_only_positive_unique_rational_cadence",
            "period_inverse_block_status": "blocked_for_zero_tied_interval_or_unresolved",
            "scan_refinement_stability_rule": "candidate_must_survive_both_frozen_windows",
            "target_frequency_input_status": "absent",
            "target_value_read_status": "not_read",
            "selector_status": "frozen_not_executed",
        },
        "resonance_selector_sha256",
    )


def build_control_plan() -> list[dict[str, str]]:
    controls = [
        ("drive_off", "disable_both_interactions", "response_B_mass_equals_0", "detect_constant_or_readout_artifact"),
        ("phase_permuted", "add_1_over_12_turn_to_every_candidate_mod_1", "selected_alias_class_shifts_equivariantly", "detect_hard_coded_candidate"),
        ("detuned_candidate", "evaluate_exact_neighbor_candidates", "detuned_response_strictly_below_unique_peak_or_tie_reported", "establish_peak_contrast"),
        ("state_label_permutation", "swap_A_B_and_remap_readout", "response_order_invariant_after_label_remap", "detect_label_artifact"),
        ("counterfactual_identity_packet", "bind_operator_family_to_counterfactual_scoped_occurrence", "packet_hash_changes_and_operator_family_status_reported", "audit_identity_specificity"),
    ]
    return [
        attach_hash(
            {
                "control_order": i,
                "control_id": cid,
                "control_operation": operation,
                "required_exact_outcome": outcome,
                "control_purpose": purpose,
                "response_baseline_field": "response_num/response_den",
                "response_peak_field": "response_num/response_den",
                "peak_contrast_field": "exact_rational_difference",
                "candidate_uniqueness_field": "resonance_status",
                "alias_class_count_field": "alias_class_count",
                "scan_refinement_status_field": "selector_stability_status",
                "target_frequency_input_status": "absent",
                "control_status": "declared_not_executed",
            },
            "control_plan_row_sha256",
        )
        for i, (cid, operation, outcome, purpose) in enumerate(controls)
    ]


def build_activation_guard() -> dict[str, str]:
    return attach_hash(
        {
            "si_activation_guard_id": "cs133_M6_unique_native_resonance_guard_v1",
            "required_resonance_status": "exact_unique_candidate",
            "required_alias_class_count": 1,
            "required_zero_perturbation_status": "passed",
            "required_selector_stability_status": "passed_across_frozen_windows",
            "required_response_contrast_status": "strict_positive_peak_contrast",
            "required_off_resonance_control_status": "passed",
            "required_target_frequency_input_status": "absent_through_M5",
            "required_cadence_status": "positive_exact_rational",
            "required_period_inverse_status": "admitted",
            "candidate_set_or_interval_action": "keep_SI_anchor_pending",
            "unresolved_action": "keep_SI_anchor_pending",
            "current_resonance_status": "not_searched",
            "current_SI_anchor_status": "inactive",
            "correspondence_mode_status": "not_declared_until_M6",
            "guard_status": "frozen_before_search",
        },
        "si_activation_guard_sha256",
    )


def build_operator(
    certificate: Mapping[str, str],
    coupling: Mapping[str, str],
    input_lock: Mapping[str, str],
    response: Mapping[str, str],
    zero_policy: Mapping[str, str],
    selector: Mapping[str, str],
) -> dict[str, str]:
    return attach_hash(
        {
            "measurement_operator_family_id": "cs133_native_atom_field_interaction_family_v1",
            "measurement_operator_state_id": "cs133_atom_field_operator_frozen_unexecuted_v1",
            "measurement_operator_declaration_id": "cs133_atom_field_operator_M3_declaration_v1",
            "operator_input_lock_id": input_lock["operator_input_lock_id"],
            "operator_input_lock_sha256": input_lock["operator_input_lock_sha256"],
            "cs_atom_packet_id": certificate["identity_packet_id"],
            "cs_atom_packet_sha256": certificate["identity_packet_sha256"],
            "primitive_recurrence_id": certificate["recurrence_certificate_id"],
            "primitive_recurrence_sha256": certificate["recurrence_certificate_sha256"],
            "primitive_recurrence_bip_count": certificate["primitive_recurrence_bip_count"],
            "duration_semantics": certificate["duration_semantics"],
            "core_occurrence_id": certificate["core_occurrence_id"],
            "outer_occurrence_id": certificate["outer_occurrence_id"],
            "core_outer_coupling_operator_id": coupling["coupling_operator_id"],
            "core_outer_coupling_operator_sha256": coupling["coupling_operator_sha256"],
            "native_coupled_state_A_id": certificate["native_coupled_state_A_id"],
            "native_coupled_state_B_id": certificate["native_coupled_state_B_id"],
            "clock_state_candidate_mapping_id": "cs133_native_states_to_clock_state_candidates_pending_M6",
            "clock_state_interpretation_status": "pending_correspondence_mode_gate",
            "native_drive_operator_id": "cs133_two_interaction_phase_coincidence_drive_v1",
            "drive_phase_rule_id": "cs133_QmodZ_canonical_phase_rule_v1",
            "drive_cadence_domain_id": "cs133_drive_phase_QmodZ_grid_2N_v1",
            "drive_amplitude_policy_id": zero_policy["drive_amplitude_policy_id"],
            "interaction_window_family_id": "cs133_primary_and_refinement_two_window_family_v1",
            "free_evolution_window_family_id": "cs133_native_cycle_derived_free_evolution_windows_v1",
            "state_readout_operator_id": "cs133_native_state_B_mass_fraction_readout_v1",
            "zero_perturbation_policy_id": zero_policy["zero_perturbation_policy_id"],
            "zero_perturbation_policy_sha256": zero_policy["zero_perturbation_policy_sha256"],
            "response_function_id": response["response_function_id"],
            "response_function_sha256": response["response_function_sha256"],
            "resonance_selector_id": selector["resonance_selector_id"],
            "resonance_selector_sha256": selector["resonance_selector_sha256"],
            "arithmetic_domain": "exact_rational_finite_state_operator",
            "phase_register_modulus": int(certificate["primitive_recurrence_bip_count"]) * 2,
            "state_preparation_rule": "prepare_native_coupled_state_A_with_unit_mass",
            "first_interaction_rule": "exact_balanced_split",
            "free_evolution_rule": "exact_native_and_drive_phase_register_advance",
            "second_interaction_rule": "exact_phase_coincidence_recombination",
            "readout_rule": "native_state_B_mass_fraction",
            "operator_execution_status": "frozen_not_executed",
            "native_resonance_search_status": "not_started",
            "target_frequency_input_status": "absent",
            "observation_packet_input_status": "absent",
            "target_value_read_status": "not_read",
            "physical_hyperfine_interpretation_status": "not_active_until_correspondence_mode_gate",
            "SI_anchor_status": "inactive",
            "operator_status": "passed_target_blind_operator_freeze",
        },
        "measurement_operator_declaration_sha256",
    )


def write_pre_freeze_manifest(files: Sequence[Path]) -> dict[str, object]:
    artifacts = [
        {
            "path": p.relative_to(ROOT).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }
        for p in sorted(files)
    ]
    manifest = {
        "manifest_id": "cs133_atom_field_operator_pre_freeze_manifest_v1",
        "freeze_order": [
            "verify_M2_native_recurrence",
            "freeze_QmodZ_drive_domain",
            "freeze_interaction_windows",
            "freeze_exact_operator_rules",
            "freeze_zero_perturbation_policy",
            "freeze_response_representation",
            "freeze_selector_and_controls",
            "freeze_SI_activation_guard",
            "freeze_operator_declaration",
        ],
        "allowed_input_paths": [
            M2_CERTIFICATE.relative_to(ROOT).as_posix(),
            M2_STATES.relative_to(ROOT).as_posix(),
            M2_TRANSITIONS.relative_to(ROOT).as_posix(),
            M2_COUPLING.relative_to(ROOT).as_posix(),
            M2_MANIFEST.relative_to(ROOT).as_posix(),
        ],
        "target_frequency_input_status": "absent",
        "observation_packet_input_status": "absent",
        "operator_execution_status": "not_executed",
        "files": artifacts,
    }
    PRE_FREEZE.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def write_final_manifest(files: Sequence[Path], operator: Mapping[str, str], n: int) -> None:
    artifacts = [
        {
            "path": p.relative_to(ROOT).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }
        for p in sorted(files)
    ]
    manifest = {
        "manifest_id": "cs133_scoped_native_atom_field_operator_freeze_v1",
        "version_scope": "v40.03r05",
        "gate_role": "target_blind_atom_field_interaction_operator_freeze",
        "current_state": {
            "M2_native_recurrence": "complete_v40.03r04",
            "M3_atom_field_operator": "complete_frozen_not_executed",
            "primitive_recurrence_bip_count": str(n),
            "drive_phase_domain": "Q_mod_Z_on_2N_exact_grid",
            "arithmetic_domain": "exact_rational_finite_state_operator",
            "native_resonance_search": "not_started",
            "native_resonance_certificate": "not_materialized",
            "target_frequency_input": "absent",
            "observation_packet_input": "absent",
            "physical_hyperfine_interpretation": "pending_correspondence_mode_gate",
            "SI_anchor": "inactive",
        },
        "operator_declaration_id": operator["measurement_operator_declaration_id"],
        "operator_declaration_sha256": operator["measurement_operator_declaration_sha256"],
        "files": artifacts,
    }
    FINAL_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_no_target_tokens(paths: Sequence[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TARGET_TOKENS:
            if token in text:
                raise ValueError(f"forbidden target token {token!r} in {path}")


def main() -> int:
    certificate, coupling, states, transitions, _ = verify_m2_inputs()
    n = int(certificate["primitive_recurrence_bip_count"])
    input_lock = build_input_lock(certificate, coupling)
    phase_rows = build_phase_domain(n)
    window_rows = build_windows(n)
    transition_rows = build_transition_rules()
    response = build_response_contract(n)
    representation_rows = build_representation_registry()
    zero_policy = build_zero_perturbation_policy()
    selector = build_selector_contract()
    control_rows = build_control_plan()
    guard = build_activation_guard()
    operator = build_operator(certificate, coupling, input_lock, response, zero_policy, selector)

    write_csv(DATA / "cs133_atom_field_input_lock.csv", list(input_lock), [input_lock])
    write_csv(DATA / "cs133_drive_phase_domain.csv", list(phase_rows[0]), phase_rows)
    write_csv(DATA / "cs133_atom_field_interaction_window_policy.csv", list(window_rows[0]), window_rows)
    write_csv(DATA / "cs133_atom_field_operator_transition_rules.csv", list(transition_rows[0]), transition_rows)
    write_csv(DATA / "cs133_atom_field_response_function_contract.csv", list(response), [response])
    write_csv(DATA / "cs133_atom_field_exact_response_representation_registry.csv", list(representation_rows[0]), representation_rows)
    write_csv(DATA / "cs133_atom_field_zero_perturbation_policy.csv", list(zero_policy), [zero_policy])
    write_csv(DATA / "cs133_atom_field_resonance_selector_contract.csv", list(selector), [selector])
    write_csv(DATA / "cs133_atom_field_resonance_control_audit_plan.csv", list(control_rows[0]), control_rows)
    write_csv(DATA / "cs133_atom_field_si_activation_guard.csv", list(guard), [guard])
    write_csv(DATA / "cs133_atom_field_interaction_operator.csv", list(operator), [operator])

    contract_files = [
        DATA / "cs133_atom_field_input_lock.csv",
        DATA / "cs133_drive_phase_domain.csv",
        DATA / "cs133_atom_field_interaction_window_policy.csv",
        DATA / "cs133_atom_field_operator_transition_rules.csv",
        DATA / "cs133_atom_field_response_function_contract.csv",
        DATA / "cs133_atom_field_exact_response_representation_registry.csv",
        DATA / "cs133_atom_field_zero_perturbation_policy.csv",
        DATA / "cs133_atom_field_resonance_selector_contract.csv",
        DATA / "cs133_atom_field_resonance_control_audit_plan.csv",
        DATA / "cs133_atom_field_si_activation_guard.csv",
        DATA / "cs133_atom_field_interaction_operator.csv",
        ROOT / SCRIPT_REL,
    ]
    ensure_no_target_tokens(contract_files)
    write_pre_freeze_manifest(contract_files)
    final_files = contract_files + [PRE_FREEZE]
    write_final_manifest(final_files, operator, n)
    ensure_no_target_tokens(final_files + [FINAL_MANIFEST])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
