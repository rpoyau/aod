import csv
import hashlib
import importlib.util
import itertools
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "c6"
SCRIPT = ROOT / "manual" / "scripts" / "build_consequent_six_slot_form_compatibility_gate.py"
ENUMERATION = DATA / "consequent_six_slot_support_family_enumeration.csv"


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_module():
    spec = importlib.util.spec_from_file_location("c6_gate", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def row_hash(row, field):
    body = {k: row[k] for k in sorted(row) if k != field}
    data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(data).hexdigest()


def packet_for(form_id):
    all_registry = rows("consequent_six_slot_support_family_registry.csv")
    all_enumeration = rows("consequent_six_slot_support_family_enumeration.csv")
    all_inverse = rows("consequent_six_slot_branch_inverse_audit.csv")
    return {
        "occurrence": next(r for r in rows("consequent_six_slot_occurrence_card.csv") if r["form_id"] == form_id),
        "accessor": next(r for r in rows("consequent_six_slot_field_accessor_audit.csv") if r["form_id"] == form_id),
        "registry_rows": [r for r in all_registry if r["form_id"] == form_id],
        "measure_contract": next(r for r in rows("consequent_six_slot_support_family_measure_contract.csv") if r["form_id"] == form_id),
        "enumeration_rows": [r for r in all_enumeration if r["form_id"] == form_id],
        "read_only_packet": next(r for r in rows("consequent_six_slot_support_family_read_only_packet.csv") if r["form_id"] == form_id),
        "support_mass": next(r for r in rows("consequent_six_slot_support_family_mass_audit.csv") if r["form_id"] == form_id),
        "inverse_domain": rows("consequent_six_slot_inverse_solver_domain_contract.csv")[0],
        "inverse_rows": [r for r in all_inverse if r["form_id"] == form_id],
    }


def evaluate_packet(mod, form_id, packet=None):
    packet = deepcopy(packet or packet_for(form_id))
    occurrence = packet["occurrence"]
    source = mod.parse_main_source_rows()[occurrence["route_form"]]
    return mod.evaluate_form_state(policy=mod.load_support_policy(), source=source, **packet)


def test_gate_rows_match_exact_main_note_accessors():
    by = {r["route_form"]: r for r in rows("consequent_six_slot_field_accessor_audit.csv")}
    assert (by["3:3:6"]["Pi_alpha"], by["3:3:6"]["RD_AO"], by["3:3:6"]["PD"], by["3:3:6"]["QD"]) == ("30", "61", "36", "330")
    assert (by["3:4:6"]["Pi_alpha"], by["3:4:6"]["RD_AO"], by["3:4:6"]["PD"], by["3:4:6"]["QD"]) == ("68", "137", "42", "917")
    assert all(r["source_accessor_match_status"] == "passed" for r in by.values())
    assert all(r["capacity_fill_residual"] == "0" for r in by.values())
    assert all(r["capacity_residual_semantics"] == "window_capacity_fill_not_recurrence_closure" for r in by.values())


def test_support_family_is_disjoint_words_and_support_shell_not_local_edges():
    registry = rows("consequent_six_slot_support_family_registry.csv")
    by = {(r["route_form"], r["member_class"]): r for r in registry}
    assert by[("3:3:6", "walk_history")]["member_count"] == "27"
    assert by[("3:3:6", "retained_support_shell")]["member_count"] == "3"
    assert by[("3:4:6", "walk_history")]["member_count"] == "64"
    assert by[("3:4:6", "retained_support_shell")]["member_count"] == "4"
    assert {r["support_family_definition"] for r in registry} == {"F_pq=D_q^p_disjoint_union_S_q"}
    assert {r["local_DEC_edge_status"] for r in registry} == {"not_a_local_Q4_edge_inventory"}
    assert all("retained_edge_shell" not in r["member_class"] for r in registry)

    ledger = rows("consequent_six_slot_support_family_enumeration.csv")
    by_form = {}
    for row in ledger:
        by_form.setdefault(row["route_form"], []).append(row)
        assert row["row_time_semantics"] == "non_temporal_support_family_enumeration"
        assert "local" in row["local_Q4_edge_status"]
    assert len(by_form["3:3:6"]) == 30
    assert len(by_form["3:4:6"]) == 68
    assert sum(r["member_class"] == "walk_history" for r in by_form["3:3:6"]) == 27
    assert sum(r["member_class"] == "retained_support_shell" for r in by_form["3:3:6"]) == 3
    assert sum(r["member_class"] == "walk_history" for r in by_form["3:4:6"]) == 64
    assert sum(r["member_class"] == "retained_support_shell" for r in by_form["3:4:6"]) == 4


def test_cartesian_enumeration_and_shell_completeness():
    ledger = rows("consequent_six_slot_support_family_enumeration.csv")
    for form_id, p, q in (("form_3_3_6", 3, 3), ("form_3_4_6", 3, 4)):
        group = [r for r in ledger if r["form_id"] == form_id]
        words = {r["history_word"] for r in group if r["member_class"] == "walk_history"}
        expected = {".".join(map(str, w)) for w in itertools.product(range(q), repeat=p)}
        assert words == expected
        shells = {int(r["support_shell_member_index"]) for r in group if r["member_class"] == "retained_support_shell"}
        assert shells == set(range(q))
        assert len({r["support_member_id"] for r in group}) == q**p + q
        assert sorted(int(r["support_member_order"]) for r in group) == list(range(q**p + q))


def test_support_family_measure_is_exact_definitional_and_not_dec_kernel():
    contracts = rows("consequent_six_slot_support_family_measure_contract.csv")
    assert len(contracts) == 2
    for row in contracts:
        assert row_hash(row, "support_measure_sha256") == row["support_measure_sha256"]
        count = int(row["support_member_count"])
        measure = Fraction(int(row["member_measure_num"]), int(row["member_measure_den"]))
        assert count * measure == 1
        assert row["measure_sum_num"] == "1"
        assert row["measure_sum_den"] == "1"
        assert row["uniform_weighting_status"] == "declared_definitional_not_physical_probability_law"
        assert row["relation_to_DEC_kernel"] == "distinct_not_a_local_Q4_kernel"
        assert row["execution_mode"] == "support_family_enumeration"

    audits = rows("consequent_six_slot_support_family_mass_audit.csv")
    assert len(audits) == 2
    for row in audits:
        total = Fraction(int(row["analysis_mass_sum_num"]), int(row["analysis_mass_sum_den"]))
        residual = Fraction(int(row["analysis_mass_residual_num"]), int(row["analysis_mass_residual_den"]))
        assert total == 1
        assert residual == 0
        assert row["support_measure_conservation_status"] == "passed"
        assert row["mass_semantics"] == "support_family_analysis_mass_not_DEC_branch_mass"


def test_local_dec_contract_is_strict_separate_and_not_materialized():
    contracts = rows("consequent_six_slot_local_dec_admission_contract.csv")
    assert len(contracts) == 2
    for row in contracts:
        assert row["local_state_space"] == "Q4"
        assert row["vertex_domain"] == "{0,1}^4"
        assert row["hamming_distance_rule"] == "exactly_1"
        assert row["connected_target_source_rule"] == "target_i_equals_source_i_plus_1"
        assert row["epsilon_rule"] == "one_hot_signed_or_TXOR_consistent"
        assert row["local_admissible_edge_slots_max"] == "4"
        assert row["kernel_probability_domain"] == "nonnegative_reduced_rational_sum_exactly_1"
        assert row["support_family_member_reuse_as_edge_status"] == "forbidden"
        assert row["current_local_DEC_status"] == "not_materialized"
        assert row["hydrogen_gate_admission_status"] == "blocked_until_connected_local_Q4_DEC_is_materialized"


def test_primitive_support_policy_is_hash_verified_consumed_and_release_pinned():
    policy = rows("c6_recurrence_support_policy.csv")[0]
    assert policy["outer_enclosure_id"] == "C6"
    assert policy["declared_scope_L"] == "6"
    assert policy["inverse_solver_q_max"] == "4"
    occurrences = rows("consequent_six_slot_occurrence_card.csv")
    for row in occurrences:
        assert row["support_policy_id"] == policy["support_policy_id"]
        assert row["support_policy_sha256"] == policy["support_policy_sha256"]
        assert row["fractal_octave_coordinate"] == policy["fractal_octave_coordinate"]
        assert row["declared_L"] == policy["declared_scope_L"]
        assert row["outer_enclosure_id"] == policy["outer_enclosure_id"]
    gate = rows("consequent_six_slot_compatibility_audit.csv")
    assert {r["support_policy_validation_mode"] for r in gate} == {"hash_verified_semantically_consumed_and_release_pinned"}


def test_inverse_solver_domain_is_frozen_and_rows_bound_to_domain():
    domain = rows("consequent_six_slot_inverse_solver_domain_contract.csv")[0]
    assert domain["p_min"] == "1"
    assert domain["q_min"] == "2"
    assert domain["q_max"] == "4"
    assert domain["domain_basis"] == "Q4_directional_support"
    assert domain["policy_validation_mode"] == "hash_verified_semantically_consumed_and_release_pinned"
    inverse = rows("consequent_six_slot_branch_inverse_audit.csv")
    by = {}
    for row in inverse:
        by.setdefault(row["route_form"], []).append((int(row["candidate_p"]), int(row["candidate_q"])))
        assert row["inverse_solver_domain_id"] == domain["inverse_solver_domain_id"]
        assert row["inverse_domain_row_sha256"] == domain["inverse_domain_row_sha256"]
        assert row["solution_count"] == "1"
        assert row["inverse_status"] == "unique_within_frozen_domain"
        assert row["form_identity_detection_status"] == "diagnostic_only_declared_occurrence_not_replaced"
    assert by["3:3:6"] == [(3, 3)]
    assert by["3:4:6"] == [(3, 4)]


def test_full_packet_evaluator_passes_only_native_bound_packets():
    mod = load_module()
    for form_id in ("form_3_3_6", "form_3_4_6"):
        result = evaluate_packet(mod, form_id)
        assert result["passed"] is True
        assert result["cross_packet_binding_pass"] is True
        assert result["enumeration_completeness_pass"] is True
        assert result["canonical_identity_pass"] is True
        assert result["canonical_enumeration_mapping_pass"] is True
        assert result["inverse_audit_pass"] is True


def test_cross_packet_binding_audit_and_narrow_claim():
    binding = rows("consequent_six_slot_cross_packet_binding_audit.csv")
    assert len(binding) == 2
    assert all(r["cross_packet_binding_status"] == "passed" for r in binding)
    assert all(r["enumeration_completeness_status"] == "passed" for r in binding)
    assert all(r["canonical_identity_status"] == "passed" for r in binding)
    assert all(r["canonical_enumeration_mapping_status"] == "passed" for r in binding)
    assert all(r["global_packet_set_closure_status"] == "passed" for r in binding)
    assert all(r["inverse_binding_status"] == "passed" for r in binding)

    gate = rows("consequent_six_slot_compatibility_audit.csv")
    assert len(gate) == 2
    for row in gate:
        assert row["compatibility_status"] == "passed"
        assert row["compatibility_claim"] == "same_C6_outer_enclosure_exact_accessor_and_fully_bound_support_family_consistency_only"
        assert row["cross_packet_binding_status"] == "passed"
        assert row["enumeration_completeness_status"] == "passed"
        assert row["canonical_identity_status"] == "passed"
        assert row["canonical_enumeration_mapping_status"] == "passed"
        assert row["closed_semantics_binding_status"] == "passed"
        assert row["inverse_audit_status"] == "passed"
        assert row["support_family_status"] == "materialized_non_temporal"
        assert row["local_DEC_execution_status"] == "not_materialized"
        assert row["recurrence_equivalence_status"] == "not_evaluated"
        assert row["temporal_equivalence_status"] == "not_evaluated"
        assert row["SADAR_cadence_equivalence_status"] == "not_evaluated"
        assert row["monon_to_bip_conversion_status"] == "not_declared"
        assert row["target_value_read_status"] == "not_read"
        assert row["empirical_score_status"] == "not_computed"


def test_relational_flow_admission_blocks_hydrogen_until_local_dec_exists():
    gate = rows("consequent_six_slot_relational_flow_admission.csv")
    assert len(gate) == 2
    for row in gate:
        assert row["support_family_enumeration_status"] == "materialized_exact_non_temporal"
        assert row["cross_packet_binding_status"] == "passed"
        assert row["local_DEC_execution_status"] == "not_materialized"
        assert row["admission_status"] == "admitted_as_support_accessor_contract_local_DEC_pending"
        assert row["hydrogen_gate_status"] == "blocked_until_connected_local_Q4_DEC_is_materialized"
        assert row["returned_current_detection_status"] == "not_materialized"
        assert row["subject_SADAR_packet_status"] == "not_materialized"
        assert row["reference_SADAR_packet_status"] == "not_materialized"
        assert row["primitive_phase_lock_status"] == "not_materialized"


def test_counterfactuals_are_mutated_rehashed_re_evaluated_and_gate_fatal():
    audit = rows("consequent_six_slot_counterfactual_audit.csv")
    assert len(audit) == 50
    assert all(row["counterfactual_audit_status"] == "passed" for row in audit)
    classes = {r["mutation_class"] for r in audit}
    assert {
        "outer_enclosure",
        "exact_accessor",
        "cross_packet_identity",
        "enumeration_completeness",
        "inverse_binding",
        "closed_semantics",
        "source_binding",
        "canonical_serialization",
        "pre_map_identity",
        "control",
    } <= classes
    for row in audit:
        if row["mutation_class"] == "control":
            assert row["observed_compatibility"] == "passed"
            assert row["packet_hash_change_status"] == "unchanged"
        else:
            assert row["observed_compatibility"] == "failed"
            assert row["packet_hash_change_status"] == "changed"
            assert row["observed_failure_reasons"]

    mod = load_module()
    compatibility = rows("consequent_six_slot_compatibility_audit.csv")
    broken = deepcopy(audit)
    broken[0]["counterfactual_audit_status"] = "failed"
    statuses = mod.derive_gate_statuses(compatibility, broken, rows("consequent_six_slot_global_packet_set_closure_audit.csv"))
    assert statuses["counterfactual_status"] == "failed"
    assert statuses["overall_gate_status"] == "failed"
    with pytest.raises(SystemExit, match="counterfactual_status"):
        mod.assert_gate_pass({**statuses, "native_compatibility_status": "passed", "cross_packet_binding_status": "passed", "enumeration_completeness_status": "passed", "inverse_audit_status": "passed"})


def test_swapped_and_unrelated_mass_packets_fail():
    mod = load_module()
    packet = packet_for("form_3_3_6")
    other = packet_for("form_3_4_6")
    packet["support_mass"] = other["support_mass"]
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "support_mass_form_id_mismatch" in result["failure_reasons"]

    packet = packet_for("form_3_3_6")
    packet["support_mass"] = mod.mutate_attached(packet["support_mass"], "support_mass_audit_row_sha256", {"form_id": "unrelated", "support_family_id": "unrelated"})
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "support_mass_support_family_id_mismatch" in result["failure_reasons"]


def test_support_member_count_mismatch_fails_even_when_rehashed():
    mod = load_module()
    packet = packet_for("form_3_3_6")
    packet["support_mass"] = mod.mutate_attached(packet["support_mass"], "support_mass_audit_row_sha256", {"support_member_count": "999"})
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "support_mass_support_member_count_mismatch" in result["failure_reasons"]


def test_missing_duplicated_and_malformed_enumeration_members_fail():
    mod = load_module()

    packet = packet_for("form_3_3_6")
    packet["enumeration_rows"] = packet["enumeration_rows"][:-1]
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "enumeration_member_count_mismatch" in result["failure_reasons"]

    packet = packet_for("form_3_3_6")
    packet["enumeration_rows"][-1] = deepcopy(packet["enumeration_rows"][-2])
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "enumeration_support_member_id_not_unique" in result["failure_reasons"]

    packet = packet_for("form_3_3_6")
    first = packet["enumeration_rows"][0]
    packet["enumeration_rows"][0] = mod.mutate_attached(first, "support_member_row_sha256", {"history_word": "0.bad.0"})
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "malformed_direction_word" in result["failure_reasons"]


def test_read_only_enumeration_sha_mismatch_fails():
    mod = load_module()
    packet = packet_for("form_3_3_6")
    packet["read_only_packet"] = mod.mutate_attached(packet["read_only_packet"], "read_only_packet_row_sha256", {"enumeration_ledger_sha256": "0" * 64})
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "read_only_enumeration_ledger_sha256_mismatch" in result["failure_reasons"]


def test_inverse_row_and_domain_mutations_fail():
    mod = load_module()
    packet = packet_for("form_3_3_6")
    packet["inverse_rows"][0] = mod.mutate_attached(packet["inverse_rows"][0], "inverse_audit_row_sha256", {"Pi_alpha": "999", "form_id": "unrelated"})
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "inverse_row_Pi_alpha_mismatch" in result["failure_reasons"]
    assert "inverse_row_form_id_mismatch" in result["failure_reasons"]

    packet = packet_for("form_3_3_6")
    packet["inverse_domain"] = mod.mutate_attached(packet["inverse_domain"], "inverse_domain_row_sha256", {"q_max": "3"})
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "inverse_domain_q_max_mismatch" in result["failure_reasons"]


def test_direct_accessor_rehash_mutation_fails():
    mod = load_module()
    packet = packet_for("form_3_3_6")
    packet["accessor"] = mod.mutate_attached(packet["accessor"], "accessor_audit_row_sha256", {"PD": str(int(packet["accessor"]["PD"]) + 1)})
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "accessor_PD_mismatch" in result["failure_reasons"]


def test_closed_semantic_statuses_and_source_binding_are_enforced():
    mod = load_module()
    cases = [
        ("occurrence", "occurrence_row_sha256", {"local_DEC_status": "materialized"}, "occurrence_local_DEC_status_release_contract_mismatch"),
        ("occurrence", "occurrence_row_sha256", {"target_value_input_status": "present"}, "occurrence_target_value_input_status_release_contract_mismatch"),
        ("occurrence", "occurrence_row_sha256", {"source_row_text_sha256": "0" * 64}, "occurrence_source_row_text_sha256_release_contract_mismatch"),
        ("accessor", "accessor_audit_row_sha256", {"capacity_residual_semantics": "recurrence_closure_certificate"}, "accessor_capacity_residual_semantics_mismatch"),
        ("accessor", "accessor_audit_row_sha256", {"temporal_inference_status": "admitted"}, "accessor_temporal_inference_status_mismatch"),
        ("accessor", "accessor_audit_row_sha256", {"target_value_input_status": "present"}, "accessor_target_value_input_status_mismatch"),
        ("read_only_packet", "read_only_packet_row_sha256", {"support_measure_conservation_status": "failed"}, "read_only_support_measure_conservation_status_mismatch"),
        ("read_only_packet", "read_only_packet_row_sha256", {"local_DEC_trace_status": "materialized"}, "read_only_local_DEC_trace_status_mismatch"),
        ("read_only_packet", "read_only_packet_row_sha256", {"target_value_read_status": "read"}, "read_only_target_value_read_status_mismatch"),
        ("inverse_domain", "inverse_domain_row_sha256", {"identity_use_policy": "replace_declared_occurrence"}, "inverse_domain_identity_use_policy_mismatch"),
        ("inverse_domain", "inverse_domain_row_sha256", {"target_value_input_status": "present"}, "inverse_domain_target_value_input_status_mismatch"),
    ]
    for packet_key, hash_field, changes, reason in cases:
        packet = packet_for("form_3_3_6")
        packet[packet_key] = mod.mutate_attached(packet[packet_key], hash_field, changes)
        result = evaluate_packet(mod, "form_3_3_6", packet)
        assert result["passed"] is False
        assert result["closed_semantics_binding_pass"] is False
        assert reason in result["failure_reasons"]


def test_old_mistyped_artifacts_are_removed_and_retyping_is_explicit():
    old = {
        "consequent_six_slot_kernel_contract.csv",
        "consequent_six_slot_dec_execution_ledger.csv",
        "consequent_six_slot_stage_mass_audit.csv",
        "consequent_six_slot_read_only_trace.csv",
    }
    assert not any((DATA / name).exists() for name in old)
    registry = rows("consequent_six_slot_artifact_retyping_registry.csv")
    assert {row["superseded_artifact"] for row in registry} == old
    assert {row["status"] for row in registry} == {"superseded_removed_from_current_gate"}


def test_pre_audit_freeze_is_enforced_before_compatibility(tmp_path):
    mod = load_module()
    manifest = DATA / "consequent_six_slot_pre_audit_freeze_manifest.csv"
    mod.verify_pre_audit_freeze(manifest)
    copied = tmp_path / "repo"
    copied.mkdir()
    for row in rows("consequent_six_slot_pre_audit_freeze_manifest.csv"):
        src = ROOT / row["artifact_path"]
        dst = copied / row["artifact_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    copied_manifest = copied / manifest.relative_to(ROOT)
    copied_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest, copied_manifest)
    target = copied / "manual/data/c6/consequent_six_slot_support_family_measure_contract.csv"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen artifact SHA-256 mismatch"):
        mod.verify_pre_audit_freeze(copied_manifest, copied)



def test_global_packet_set_closure_is_exact_and_fail_closed():
    mod = load_module()
    raw = mod.load_raw_packet_rows()
    audit = mod.validate_global_packet_set(raw)
    assert audit["passed"] is True
    assert audit["canonical_physical_serialization_status"] == "passed"
    assert audit["pre_map_identity_closure_status"] == "passed"
    assert audit["packet_row_count_total"] == 115
    assert audit["expected_packet_row_count_total"] == 115

    mutations = []
    duplicate_occurrence = deepcopy(raw)
    duplicate_occurrence["occurrences"].append(deepcopy(duplicate_occurrence["occurrences"][0]))
    mutations.append(duplicate_occurrence)

    duplicate_measure = deepcopy(raw)
    duplicate_measure["measures"].append(deepcopy(duplicate_measure["measures"][0]))
    mutations.append(duplicate_measure)

    unrelated_registry = deepcopy(raw)
    unrelated_registry["registries"].append(
        mod.mutate_attached(
            unrelated_registry["registries"][0],
            "support_family_registry_row_sha256",
            {"form_id": "unrelated", "route_form": "unrelated", "support_family_id": "unrelated", "support_measure_id": "unrelated"},
        )
    )
    mutations.append(unrelated_registry)

    unrelated_enumeration = deepcopy(raw)
    unrelated_enumeration["enumeration"].append(
        mod.mutate_attached(
            unrelated_enumeration["enumeration"][0],
            "support_member_row_sha256",
            {
                "enumeration_row_index": "98",
                "form_id": "unrelated",
                "route_form": "unrelated",
                "support_family_id": "unrelated",
                "support_measure_id": "unrelated",
                "support_member_id": "unrelated_member",
            },
        )
    )
    mutations.append(unrelated_enumeration)

    unexpected_inverse = deepcopy(raw)
    unexpected_inverse["inverse"].append(
        mod.mutate_attached(
            unexpected_inverse["inverse"][0],
            "inverse_audit_row_sha256",
            {"form_id": "unrelated", "route_form": "unrelated", "solution_order": "0"},
        )
    )
    mutations.append(unexpected_inverse)

    for mutation in mutations:
        result = mod.validate_global_packet_set(mutation)
        assert result["passed"] is False
        assert result["failure_reasons"]


def test_global_physical_serialization_is_exact_and_order_sensitive():
    mod = load_module()
    raw = mod.load_raw_packet_rows()
    block_a = [row for row in raw["enumeration"] if row["form_id"] == "form_3_3_6"]
    block_b = [row for row in raw["enumeration"] if row["form_id"] == "form_3_4_6"]

    swapped = deepcopy(raw)
    swapped["enumeration"] = block_b + block_a
    result = mod.validate_global_packet_set(swapped)
    assert result["passed"] is False
    assert "global_enumeration_physical_order_mismatch" in result["failure_reasons"]
    assert "global_enumeration_canonical_serialization_mismatch" in result["failure_reasons"]

    interleaved = deepcopy(raw)
    rows_out = []
    for left, right in itertools.zip_longest(block_a, block_b):
        if left is not None:
            rows_out.append(left)
        if right is not None:
            rows_out.append(right)
    interleaved["enumeration"] = rows_out
    result = mod.validate_global_packet_set(interleaved)
    assert result["passed"] is False
    assert "global_enumeration_physical_order_mismatch" in result["failure_reasons"]

    transposed = deepcopy(raw)
    transposed["enumeration"][0], transposed["enumeration"][1] = (
        transposed["enumeration"][1], transposed["enumeration"][0]
    )
    result = mod.validate_global_packet_set(transposed)
    assert result["passed"] is False
    assert "global_enumeration_physical_order_mismatch" in result["failure_reasons"]


def test_pre_map_family_and_measure_identity_closure_is_fail_closed():
    mod = load_module()
    raw = mod.load_raw_packet_rows()

    mutations = []
    measure = deepcopy(raw)
    measure["measures"][0] = mod.mutate_attached(
        measure["measures"][0], "support_measure_sha256", {"support_measure_id": "foreign"}
    )
    mutations.append((measure, "global_measures_support_measure_id_mismatch"))

    read_only = deepcopy(raw)
    read_only["read_only"][0] = mod.mutate_attached(
        read_only["read_only"][0], "read_only_packet_row_sha256", {"support_family_id": "foreign"}
    )
    mutations.append((read_only, "global_read_only_support_family_id_mismatch"))

    mass = deepcopy(raw)
    mass["mass"][0] = mod.mutate_attached(
        mass["mass"][0], "support_mass_audit_row_sha256", {"support_measure_id": "foreign"}
    )
    mutations.append((mass, "global_mass_support_measure_id_mismatch"))

    for mutation, expected_reason in mutations:
        result = mod.validate_global_packet_set(mutation)
        assert result["passed"] is False
        assert result["pre_map_identity_closure_status"] == "failed"
        assert expected_reason in result["failure_reasons"]


def test_global_packet_set_audit_and_counterfactuals_are_materialized():
    audit = rows("consequent_six_slot_global_packet_set_closure_audit.csv")
    assert len(audit) == 1
    assert audit[0]["global_packet_set_closure_status"] == "passed"
    assert audit[0]["canonical_identity_status"] == "passed"
    assert audit[0]["expected_enumeration_rows"] == "98"
    assert audit[0]["global_enumeration_index_policy"] == "physical_sequence_exactly_0_through_97"
    assert audit[0]["canonical_physical_serialization_status"] == "passed"
    assert audit[0]["pre_map_identity_closure_status"] == "passed"

    counterfactuals = rows("consequent_six_slot_counterfactual_audit.csv")
    global_rows = [row for row in counterfactuals if row["form_id"] == "global_packet_set"]
    assert len(global_rows) == 12
    assert all(row["counterfactual_audit_status"] == "passed" for row in global_rows)
    assert {row["counterfactual_id"] for row in global_rows} >= {
        "global_duplicate_occurrence_row",
        "global_duplicate_measure_packet",
        "global_unrelated_registry_row",
        "global_unrelated_enumeration_row",
        "global_unexpected_inverse_row",
        "global_swapped_physical_form_blocks",
        "global_stable_cross_form_interleaving",
        "global_adjacent_physical_row_transposition",
        "global_foreign_measure_contract_identity",
        "global_foreign_read_only_family_identity",
        "global_foreign_mass_measure_identity",
    }


def test_consistently_rehashed_route_rename_fails_release_identity_binding():
    mod = load_module()
    packet = packet_for("form_3_3_6")
    packet["occurrence"] = mod.mutate_attached(packet["occurrence"], "occurrence_row_sha256", {"route_form": "renamed-route"})
    packet["accessor"] = mod.mutate_attached(packet["accessor"], "accessor_audit_row_sha256", {"route_form": "renamed-route"})
    packet["registry_rows"] = [mod.mutate_attached(row, "support_family_registry_row_sha256", {"route_form": "renamed-route"}) for row in packet["registry_rows"]]
    packet["measure_contract"] = mod.mutate_attached(packet["measure_contract"], "support_measure_sha256", {"route_form": "renamed-route"})
    packet["enumeration_rows"] = [mod.mutate_attached(row, "support_member_row_sha256", {"route_form": "renamed-route"}) for row in packet["enumeration_rows"]]
    packet["read_only_packet"] = mod.mutate_attached(packet["read_only_packet"], "read_only_packet_row_sha256", {"route_form": "renamed-route"})
    packet["support_mass"] = mod.mutate_attached(packet["support_mass"], "support_mass_audit_row_sha256", {"route_form": "renamed-route"})
    packet["inverse_rows"] = [mod.mutate_attached(row, "inverse_audit_row_sha256", {"route_form": "renamed-route"}) for row in packet["inverse_rows"]]
    source = mod.parse_main_source_rows()["3:3:6"]
    result = mod.evaluate_form_state(policy=mod.load_support_policy(), source=source, **packet)
    assert result["passed"] is False
    assert "occurrence_route_form_release_contract_mismatch" in result["failure_reasons"]


def test_canonical_member_id_order_and_typing_are_enforced(tmp_path):
    mod = load_module()
    packet = packet_for("form_3_3_6")
    all_rows = rows("consequent_six_slot_support_family_enumeration.csv")

    mutated_group = deepcopy(packet["enumeration_rows"])
    mutated_group[0] = mod.mutate_attached(
        mutated_group[0],
        "support_member_row_sha256",
        {"support_member_id": "arbitrary_unique_member", "row_time_semantics": "local_temporal_event"},
    )
    mutated_all = mutated_group + [row for row in all_rows if row["form_id"] != "form_3_3_6"]
    ledger = tmp_path / "enumeration.csv"
    mod.write_csv(ledger, list(mutated_all[0]), mutated_all)
    packet["enumeration_rows"] = mutated_group
    packet["read_only_packet"] = mod.mutate_attached(
        packet["read_only_packet"],
        "read_only_packet_row_sha256",
        {
            "support_family_subset_sha256": mod.sha_bytes(mod.canonical_json(mutated_group)),
            "enumeration_ledger_sha256": mod.sha_file(ledger),
        },
    )
    source = mod.parse_main_source_rows()[packet["occurrence"]["route_form"]]
    result = mod.evaluate_form_state(
        policy=mod.load_support_policy(), source=source, enumeration_path=ledger, **packet
    )
    assert result["passed"] is False
    assert "canonical_enumeration_support_member_id_mismatch" in result["failure_reasons"]
    assert "canonical_enumeration_row_time_semantics_mismatch" in result["failure_reasons"]

    reversed_group = list(reversed(packet_for("form_3_3_6")["enumeration_rows"]))
    reversed_all = reversed_group + [row for row in all_rows if row["form_id"] != "form_3_3_6"]
    reverse_ledger = tmp_path / "reverse_enumeration.csv"
    mod.write_csv(reverse_ledger, list(reversed_all[0]), reversed_all)
    reverse_packet = packet_for("form_3_3_6")
    reverse_packet["enumeration_rows"] = reversed_group
    reverse_packet["read_only_packet"] = mod.mutate_attached(
        reverse_packet["read_only_packet"],
        "read_only_packet_row_sha256",
        {
            "support_family_subset_sha256": mod.sha_bytes(mod.canonical_json(reversed_group)),
            "enumeration_ledger_sha256": mod.sha_file(reverse_ledger),
        },
    )
    source = mod.parse_main_source_rows()[reverse_packet["occurrence"]["route_form"]]
    result = mod.evaluate_form_state(
        policy=mod.load_support_policy(), source=source, enumeration_path=reverse_ledger, **reverse_packet
    )
    assert result["passed"] is False
    assert any(reason.startswith("canonical_enumeration_") for reason in result["failure_reasons"])


def test_extreme_occurrence_and_malformed_inverse_order_fail_structured():
    mod = load_module()
    packet = packet_for("form_3_3_6")
    packet["occurrence"] = mod.mutate_attached(
        packet["occurrence"], "occurrence_row_sha256", {"declared_p": "1000000000"}
    )
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "occurrence_declared_p_release_contract_mismatch" in result["failure_reasons"]

    packet = packet_for("form_3_3_6")
    packet["inverse_rows"][0] = mod.mutate_attached(
        packet["inverse_rows"][0], "inverse_audit_row_sha256", {"solution_order": "malformed"}
    )
    result = evaluate_packet(mod, "form_3_3_6", packet)
    assert result["passed"] is False
    assert "malformed_integer_inverse_solution_order" in result["failure_reasons"]

def test_generator_is_byte_deterministic_and_fail_closed_manifest_verifies():
    before = {path.name: path.read_bytes() for path in DATA.glob("consequent_six_slot_*")}
    subprocess.run([sys.executable, str(SCRIPT)], check=True)
    after = {path.name: path.read_bytes() for path in DATA.glob("consequent_six_slot_*")}
    assert before == after
    manifest = json.loads((DATA / "consequent_six_slot_gate_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.03r06.3.1"
    assert manifest["compatibility_status"] == "passed"
    assert manifest["native_compatibility_status"] == "passed"
    assert manifest["counterfactual_status"] == "passed"
    assert manifest["cross_packet_binding_status"] == "passed"
    assert manifest["enumeration_completeness_status"] == "passed"
    assert manifest["canonical_identity_status"] == "passed"
    assert manifest["canonical_enumeration_mapping_status"] == "passed"
    assert manifest["closed_semantics_binding_status"] == "passed"
    assert manifest["global_packet_set_closure_status"] == "passed"
    assert manifest["canonical_physical_serialization_status"] == "passed"
    assert manifest["pre_map_identity_closure_status"] == "passed"
    assert manifest["inverse_audit_status"] == "passed"
    assert manifest["overall_gate_status"] == "passed"
    assert manifest["support_policy_validation_mode"] == "hash_verified_semantically_consumed_and_release_pinned"
    assert manifest["support_family_status"] == "materialized_non_temporal"
    assert manifest["local_DEC_execution_status"] == "not_materialized"
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_manual_i_includes_versionless_hardened_gate_appendix():
    main = (ROOT / "manual/main.tex").read_text(encoding="utf-8")
    appendix = (ROOT / "manual/appendices/H_consequent_six_slot_form_compatibility_gate.tex").read_text(encoding="utf-8")
    assert "H_consequent_six_slot_form_compatibility_gate.tex" in main
    assert "Support-Family / Local-D.E.C. Separation" in appendix
    assert "27+3=30" in appendix
    assert "64+4=68" in appendix
    assert "F_{p,q}" in appendix
    assert "retained support-shell" in appendix
    assert "not the AFC/D.E.C. kernel" in appendix
    assert "cross-packet" in appendix.lower()
    assert "global packet-set closure" in appendix.lower()
    assert "canonical enumeration mapping" in appendix.lower()
    assert "canonical physical serialization" in appendix.lower()
    assert "pre-map identity closure" in appendix.lower()
    assert "closed-semantic binding" in appendix.lower()
    assert "fail-closed" in appendix.lower()
    assert "not a recurrence" in appendix.lower()
    assert "monon-to-bip" in appendix
    assert "v40.03" not in appendix
