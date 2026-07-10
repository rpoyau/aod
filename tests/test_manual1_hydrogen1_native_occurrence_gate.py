import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "hydrogen"
SCRIPT = ROOT / "manual" / "scripts" / "build_hydrogen1_native_occurrence_gate.py"


def rows(name: str):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def one(name: str):
    data = rows(name)
    assert len(data) == 1
    return data[0]


def load_module():
    spec = importlib.util.spec_from_file_location("h1_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def file_tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(part in {"dist", ".pytest_cache", "__pycache__"} for part in path.parts):
            h.update(path.relative_to(root).as_posix().encode() + b"\0")
            h.update(path.read_bytes())
    return h.hexdigest()


def test_release_and_manual_appendix_are_hydrogen1_gate():
    version = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    assert "Canonical version:" in version
    manual_main = (ROOT / "manual/main.tex").read_text(encoding="utf-8")
    assert r"\input{appendices/I_hydrogen1_native_occurrence_gate.tex}" in manual_main
    appendix = (ROOT / "manual/appendices/I_hydrogen1_native_occurrence_gate.tex").read_text(encoding="utf-8")
    assert "Hydrogen-1 Native Occurrence Gate" in appendix
    assert r"\operatorname{Couple}" in appendix
    assert "3{:}3{:}6,1{:}2{:}6" in appendix
    assert "N_{\\mathrm{bip}}(\\gamma_{H1})=2" in appendix
    assert "not a metric duration" in appendix
    assert "Balmer ratio" in appendix
    assert "Exact schema, source-chain, and detector admission" in appendix
    assert "unknown, missing, duplicated, or reordered" in appendix
    assert "structured failed audit" in appendix
    assert "v40." not in appendix


def test_identity_and_occurrence_are_target_blind_and_fully_bound():
    identity = one("hydrogen1_identity_packet.csv")
    assert identity["element_symbol"] == "H"
    assert identity["atomic_number"] == "1"
    assert identity["mass_number"] == "1"
    assert identity["neutron_count"] == "0"
    assert identity["charge_state"] == "0"
    assert identity["fractal_octave_coordinate"] == "00_(8)"
    assert identity["target_value_input_status"] == "absent"

    occurrence = one("hydrogen1_occurrence_card.csv")
    assert occurrence["identity_packet_id"] == identity["identity_packet_id"]
    assert occurrence["identity_packet_sha256"] == identity["identity_packet_sha256"]
    assert occurrence["core_form_id"] == "form_3_3_6"
    assert occurrence["core_route_form"] == "3:3:6"
    assert occurrence["outer_route_form"] == "1:2:6"
    assert occurrence["declared_coupling_form"] == "Couple(3:3:6,1:2:6)"
    assert occurrence["seat_state_id"] == "E2^0"
    assert occurrence["local_DEC_status"] == "materialized_connected_Q4_direct_return"
    assert occurrence["Balmer_input_status"] == "absent"
    assert occurrence["target_value_input_status"] == "absent"
    assert occurrence["RD_status"] == "not_materialized"
    assert occurrence["SADAR_flow_status"] == "not_materialized"
    assert occurrence["phase_lock_status"] == "not_materialized"


def test_local_q4_inventory_is_complete_hamming1_and_exact():
    inventory = rows("hydrogen1_local_q4_edge_inventory.csv")
    assert len(inventory) == 8
    assert [int(r["global_inventory_index"]) for r in inventory] == list(range(8))
    for event in (0, 1):
        subset = [r for r in inventory if int(r["event_index"]) == event]
        assert [int(r["edge_slot"]) for r in subset] == [0, 1, 2, 3]
        assert sum(int(r["adm_e_B"]) for r in subset) == 1
        assert sum((Fraction(int(r["P_num"]), int(r["P_den"])) for r in subset), Fraction()) == 1
        for row in subset:
            assert len(row["source_epsilon_Q4"]) == 4
            assert set(row["source_epsilon_Q4"]) <= {"0", "1"}
            assert len(row["target_epsilon_Q4"]) == 4
            assert set(row["target_epsilon_Q4"]) <= {"0", "1"}
            assert row["hamming_distance"] == "1"
            assert row["xor_epsilon_Q4"].count("1") == 1
            assert row["local_Q4_edge_status"] == "local_Hamming1_edge_slot"
            assert row["row_time_semantics"] == "kernel_inventory_not_elapsed_time"
            assert row["support_family_member_reuse_status"] == "not_reused"
            assert row["target_value_input_status"] == "absent"


def test_execution_is_connected_exact_and_not_metric_time():
    execution = rows("hydrogen1_dec_execution_ledger.csv")
    assert [r["event_order"] for r in execution] == ["0", "1"]
    assert execution[0]["source_state_id"] == "H1_q4_state_origin"
    assert execution[0]["target_state_id"] == "H1_q4_state_hinge"
    assert execution[1]["source_state_id"] == execution[0]["target_state_id"]
    assert execution[1]["target_state_id"] == execution[0]["source_state_id"]
    assert [r["sigma_e"] for r in execution] == ["+1", "-1"]
    assert [r["route_e_B"] for r in execution] == ["outgoing", "returned"]
    for row in execution:
        assert row["execution_mode"] == "enumerate_all"
        assert Fraction(int(row["P_num"]), int(row["P_den"])) == 1
        assert Fraction(int(row["incoming_mass_num"]), int(row["incoming_mass_den"])) == 1
        assert Fraction(int(row["outgoing_mass_num"]), int(row["outgoing_mass_den"])) == 1
        assert row["mass_conservation_status"] == "passed"
        assert row["executed_bip_token_count"] == "1"
        assert row["row_time_semantics"] == "executed_bip_token_not_temporal_magnitude"
        assert not row["edge_id"].startswith("form_")
        assert not row["event_id"].startswith("form_")

    trace = one("hydrogen1_read_only_trace.csv")
    assert trace["event_count"] == "2"
    assert trace["trace_count"] == "2"
    assert trace["executed_bip_token_count"] == "2"
    assert trace["trace_count_temporal_status"] == "execution_structure_not_temporal_magnitude"
    assert trace["state_sequence"] == "H1_q4_state_origin>H1_q4_state_hinge>H1_q4_state_origin"
    assert trace["proper_prefix_return_count"] == "0"
    assert trace["trace_freeze_status"] == "frozen_before_detection"


def test_returned_current_detection_stops_before_rd_sadar_and_phase_lock():
    row = one("hydrogen1_returned_current_detection.csv")
    assert row["inverse_edge_orientation_status"] == "passed"
    assert row["full_return_status"] == "passed"
    assert row["proper_prefix_return_count"] == "0"
    assert row["primitive_direct_return_status"] == "passed"
    assert row["returned_current_relation"] == "outbound_hinge_return_pair"
    assert row["monon_cycle_class_status"] == "detected_direct_minimal_witness"
    assert row["minimal_direct_witness_bip_count"] == "2"
    assert row["minimal_witness_temporal_status"] == "witness_only_not_duration"
    assert row["RD_status"] == "not_materialized"
    assert row["RCD_status"] == "not_materialized"
    assert row["duonic_pressure_status"] == "not_materialized"
    assert row["SADAR_flow_status"] == "not_materialized"
    assert row["phase_lock_status"] == "not_materialized"
    assert row["target_value_read_status"] == "not_read"
    assert row["occurrence_packet_sha256"] == one("hydrogen1_occurrence_card.csv")["occurrence_packet_sha256"]
    assert row["identity_packet_sha256"] == one("hydrogen1_identity_packet.csv")["identity_packet_sha256"]
    assert row["source_state_row_sha256"] == rows("hydrogen1_local_q4_state_registry.csv")[0]["state_row_sha256"]
    assert row["target_state_row_sha256"] == rows("hydrogen1_local_q4_state_registry.csv")[1]["state_row_sha256"]


def test_gate_manifest_and_all_file_hashes_pass():
    manifest = json.loads((DATA / "hydrogen1_native_occurrence_gate_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.03r07.1"
    assert manifest["overall_gate_status"] == "passed"
    assert set(manifest["statuses"].values()) == {"passed"}
    assert manifest["current_state"]["executed_bip_token_count"] == 2
    assert manifest["current_state"]["trace_count_temporal_status"] == "execution_structure_not_temporal_magnitude"
    assert manifest["current_state"]["Balmer_target"] == "not_read"
    for rec in manifest["files"]:
        path = ROOT / rec["path"]
        assert path.stat().st_size == rec["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"]

    pre = json.loads((DATA / "hydrogen1_pre_detection_freeze_manifest.json").read_text(encoding="utf-8"))
    assert pre["freeze_status"] == "frozen_before_returned_current_detection"
    assert "Balmer_ratio" in pre["forbidden_input_classes"]
    for group in ("allowed_source_inputs", "frozen_packets"):
        for rec in pre[group]:
            path = ROOT / rec["path"]
            assert path.stat().st_size == rec["bytes"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"]


def test_counterfactuals_are_real_and_gate_fatal():
    audit = rows("hydrogen1_counterfactual_audit.csv")
    assert len(audit) == 68
    assert all(r["counterfactual_audit_status"] == "passed" for r in audit)
    assert {r["counterfactual_id"] for r in audit} >= {
        "invalid_Q4_vertex", "hamming_distance_two", "disconnected_event_order",
        "fifth_edge_slot", "kernel_sum_mismatch", "zero_denominator",
        "occurrence_identity_mismatch", "support_family_reused_as_edge_id",
        "target_input_present", "execution_mode_mutation", "read_only_hash_mismatch",
        "identity_counterfactual_without_new_scope", "unchanged_control",
        "admitted_weight_contract_mutation", "stored_normalizer_mutation",
        "nonreduced_kernel_fraction", "admitted_edge_semantic_retyping",
        "occurrence_outer_support_mismatch", "occurrence_RD_lane_opened",
        "execution_edge_semantic_retyping", "kernel_audit_normalizer_mutation",
        "canonical_hinge_axis_mutation", "read_only_ledger_path_mutation",
        "identity_source_plan_hash_mutation",
    }
    for row in audit:
        if row["counterfactual_id"] == "unchanged_control":
            assert row["observed_gate_result"] == "passed"
        else:
            assert row["observed_gate_result"] == "failed"
            assert row["observed_failure_reasons"]

    identity_cf = one("hydrogen1_identity_counterfactual_audit.csv")
    assert identity_cf["identity_hash_change_status"] == "changed"
    assert identity_cf["occurrence_hash_change_status"] == "changed"
    assert identity_cf["topology_family_status"] == "shared_direct_return_topology_permitted_only_as_separate_scoped_occurrence"
    assert identity_cf["H1_gate_admission_status"] == "rejected_identity_scope_mismatch"


def test_generator_is_deterministic_and_does_not_read_balmer_or_targets():
    before = file_tree_hash(DATA)
    subprocess.run([sys.executable, str(SCRIPT)], check=True)
    after = file_tree_hash(DATA)
    assert before == after
    source = SCRIPT.read_text(encoding="utf-8")
    assert "balmer_exact_ratio_card" not in source.lower()
    assert "nist" not in source.lower()
    assert "9192631770" not in source
    assert "target_value_input_status" in source


def test_native_evaluator_rejects_disconnected_and_open_target_packets():
    mod = load_module()
    packet = mod.packet_from_disk()
    assert mod.evaluate_packet(packet)["passed"] is True

    broken = deepcopy(packet)
    broken["execution"][1] = mod.mutate_attached(
        broken["execution"][1], mod.ROW_HASH_FIELDS["execution"],
        {"source_state_id": "H1_q4_state_origin", "source_epsilon_Q4": "0000"},
    )
    result = mod.evaluate_packet(broken)
    assert result["passed"] is False
    assert "execution_not_connected" in result["failure_reasons"]

    broken = deepcopy(packet)
    broken["occurrence"] = mod.mutate_attached(
        broken["occurrence"], mod.ROW_HASH_FIELDS["occurrence"],
        {"target_value_input_status": "present"},
    )
    result = mod.evaluate_packet(broken)
    assert result["passed"] is False
    assert "occurrence_target_value_input_status_mismatch" in result["failure_reasons"]


def test_native_evaluator_binds_canonical_kernel_state_and_freeze_semantics():
    mod = load_module()
    packet = mod.packet_from_disk()

    cases = [
        ("inventory", 0, {"weight": "9"}, "inventory_event_0_slot_0_weight_mismatch"),
        ("inventory", 0, {"Z": "9"}, "inventory_event_0_slot_0_Z_mismatch"),
        ("inventory", 0, {"sigma_e": "0", "route_e_B": "blocked"}, "inventory_event_0_slot_0_sigma_e_mismatch"),
        ("kernel", 0, {"normalizer_num": "9"}, "kernel_0_normalizer_num_mismatch"),
        ("states", 1, {"epsilon_Q4": "0100"}, "state_1_epsilon_Q4_mismatch"),
        ("execution", 0, {"sigma_e": "0", "route_e_B": "blocked"}, "execution_0_sigma_e_mismatch"),
    ]
    for packet_key, index, changes, expected_reason in cases:
        broken = deepcopy(packet)
        hash_field = mod.ROW_HASH_FIELDS[packet_key]
        broken[packet_key][index] = mod.mutate_attached(broken[packet_key][index], hash_field, changes)
        result = mod.evaluate_packet(broken)
        assert result["passed"] is False
        assert expected_reason in result["failure_reasons"]

    broken = deepcopy(packet)
    broken["read_only"] = mod.mutate_attached(
        broken["read_only"], mod.ROW_HASH_FIELDS["read_only"],
        {"execution_ledger_path": "manual/data/hydrogen/foreign.csv"},
    )
    result = mod.evaluate_packet(broken)
    assert result["passed"] is False
    assert "read_only_execution_ledger_path_mismatch" in result["failure_reasons"]



def test_exact_packet_schemas_source_chain_and_prior_gate_are_closed():
    mod = load_module()
    packet = mod.packet_from_disk()
    assert mod.packet_schema_reasons(packet) == []
    source_result = mod.evaluate_source_bundle(mod.source_bundle_from_disk())
    assert source_result["passed"] is True
    audit = one("hydrogen1_source_chain_audit.csv")
    assert audit["consequent_gate_overall_status"] == "passed"
    assert audit["support_policy_status_interpretation"] == "historical_pre_H1_planning_status_not_current_gate_state"
    assert audit["source_chain_status"] == "passed_exact_source_schema_semantics_and_prior_gate_chain"
    contract = one("hydrogen1_local_dec_contract.csv")
    assert contract["consequent_gate_overall_status"] == "passed"
    assert contract["outer_support_application_status_interpretation"] == "historical_pre_H1_planning_status_not_current_gate_state"


def test_occurrence_hash_propagates_through_all_native_packets():
    occurrence_hash = one("hydrogen1_occurrence_card.csv")["occurrence_packet_sha256"]
    for name in [
        "hydrogen1_local_q4_state_registry.csv",
        "hydrogen1_local_q4_edge_inventory.csv",
        "hydrogen1_local_q4_kernel_audit.csv",
        "hydrogen1_dec_execution_ledger.csv",
        "hydrogen1_read_only_trace.csv",
        "hydrogen1_returned_current_detection.csv",
    ]:
        data = rows(name)
        assert data
        assert {row["occurrence_packet_sha256"] for row in data} == {occurrence_hash}
    execution = rows("hydrogen1_dec_execution_ledger.csv")
    inventory = {row["edge_inventory_row_sha256"]: row for row in rows("hydrogen1_local_q4_edge_inventory.csv")}
    states = {row["state_row_sha256"]: row for row in rows("hydrogen1_local_q4_state_registry.csv")}
    for row in execution:
        assert row["source_state_row_sha256"] in states
        assert row["target_state_row_sha256"] in states
        assert row["admitted_edge_row_sha256"] in inventory


def test_unknown_target_metric_fields_are_rejected_for_every_packet_class():
    mod = load_module()
    packet = mod.packet_from_disk()
    for packet_key in mod.PACKET_ROOT_KEYS:
        for field in mod.FORBIDDEN_SCHEMA_PROBES:
            broken = deepcopy(packet)
            hash_field = mod.ROW_HASH_FIELDS[packet_key]
            if packet_key in mod.LIST_PACKET_KEYS:
                broken[packet_key][0] = mod.mutate_attached(broken[packet_key][0], hash_field, {field: "probe"})
            else:
                broken[packet_key] = mod.mutate_attached(broken[packet_key], hash_field, {field: "probe"})
            result = mod.evaluate_packet(broken)
            assert result["passed"] is False
            assert any("schema" in reason for reason in result["failure_reasons"])


def test_source_and_detector_counterfactual_audits_are_fail_closed():
    source_audit = rows("hydrogen1_source_counterfactual_audit.csv")
    detector_audit = rows("hydrogen1_detector_counterfactual_audit.csv")
    assert len(source_audit) == 8
    assert len(detector_audit) == 13
    assert all(row["source_counterfactual_audit_status"] == "passed" for row in source_audit)
    assert all(row["detector_counterfactual_audit_status"] == "passed" for row in detector_audit)
    assert {row["counterfactual_id"] for row in source_audit} >= {
        "source_plan_generator_target_leak", "duplicate_H1_source_plan_row",
        "core_target_input_present", "bip_retyped_as_metric_duration",
        "source_plan_unknown_target_field", "prior_gate_manifest_failed",
    }
    assert {row["counterfactual_id"] for row in detector_audit} >= {
        "detector_occurrence_hash_mismatch", "detector_source_state_hash_mismatch",
        "detector_target_state_hash_mismatch", "detector_target_value_opened",
        "detector_classification_mutated", "unchanged_detector_control",
    }


def test_malformed_packets_return_structured_failures_not_exceptions():
    mod = load_module()
    packet = mod.packet_from_disk()

    broken = deepcopy(packet)
    broken["inventory"][0] = mod.mutate_attached(
        broken["inventory"][0], mod.ROW_HASH_FIELDS["inventory"], {"edge_slot": "4"}
    )
    result = mod.evaluate_packet(broken)
    assert result["passed"] is False
    assert result["failure_reasons"]

    broken = deepcopy(packet)
    broken["inventory"][0] = mod.mutate_attached(
        broken["inventory"][0], mod.ROW_HASH_FIELDS["inventory"], {"weight": "x"}
    )
    result = mod.evaluate_packet(broken)
    assert result["passed"] is False
    assert result["failure_reasons"]

    broken = deepcopy(packet)
    del broken["identity"]
    result = mod.evaluate_packet(broken)
    assert result["passed"] is False
    assert "packet_identity_missing" in result["failure_reasons"]


def test_exact_csv_reader_rejects_duplicate_unknown_and_reordered_headers(tmp_path):
    mod = load_module()
    schema = mod.PACKET_SCHEMAS["identity"]
    canonical = one("hydrogen1_identity_packet.csv")

    duplicate = tmp_path / "duplicate.csv"
    duplicate.write_text(",".join(schema + [schema[-1]]) + "\n" + ",".join(canonical.get(k, "") for k in schema + [schema[-1]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mod.read_csv_exact(duplicate, schema)

    unknown = tmp_path / "unknown.csv"
    unknown.write_text(",".join(schema + ["target_value"]) + "\n" + ",".join([canonical.get(k, "") for k in schema] + ["1"]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mod.read_csv_exact(unknown, schema)

    reordered = tmp_path / "reordered.csv"
    reordered_schema = [schema[1], schema[0], *schema[2:]]
    reordered.write_text(",".join(reordered_schema) + "\n" + ",".join(canonical.get(k, "") for k in reordered_schema) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mod.read_csv_exact(reordered, schema)
