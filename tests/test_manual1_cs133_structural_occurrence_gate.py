import csv
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "cs133"
SCRIPT = ROOT / "manual" / "scripts" / "build_cs133_structural_occurrence_gate.py"
FREEZE_MANIFEST = DATA / "cs133_pre_detection_freeze_manifest.json"


def read_csv(name_or_path):
    path = DATA / name_or_path if isinstance(name_or_path, str) else name_or_path
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def file_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob("*")) if p.is_file()}


def load_gate_module():
    spec = importlib.util.spec_from_file_location("cs133_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_frozen_packet(tmp_path: Path):
    manifest = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        src = ROOT / artifact["path"]
        dst = tmp_path / artifact["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    manifest_path = tmp_path / "manual/data/cs133/cs133_pre_detection_freeze_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FREEZE_MANIFEST, manifest_path)
    return manifest_path


def refresh_manifest_artifact(module, root: Path, manifest_path: Path, relative_path: str):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        if artifact["path"] == relative_path:
            path = root / relative_path
            artifact["bytes"] = path.stat().st_size
            artifact["sha256"] = module.sha256_file(path)
            break
    else:
        raise AssertionError(relative_path)
    manifest.pop("freeze_manifest_sha256", None)
    manifest["freeze_manifest_sha256"] = module.canonical_json_hash(manifest)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_identity_is_registry_bound_at_origin_anchor_with_bip_monon_basis():
    identity = read_csv("cs133_identity_packet.csv")[0]
    assert identity["fractal_octave_coordinate"] == "00_(8)"
    assert (identity["atomic_number"], identity["mass_number"], identity["neutron_count"]) == ("55", "133", "78")
    assert identity["element_symbol"] == "Cs"
    assert identity["element_name"] == "Caesium"
    assert identity["element_registry_source_path"] == "manual-2/data/elementary/element_registry_118.csv"
    assert identity["native_count_unit"] == "bip"
    assert identity["primitive_completion_object"] == "monon"
    assert identity["observation_target_input_status"] == "absent"
    assert identity["clock_frequency_input_status"] == "absent"


def test_occurrence_binding_and_shared_topology_are_explicit():
    binding = read_csv("cs133_fractal_elementary_occurrence_binding.csv")[0]
    assert binding["identity_binding_status"] == "identity_bound_to_scoped_occurrence"
    assert binding["identity_specificity_status"] == "identity_specific_scope_shared_native_topology_family"
    assert binding["monon_completion_certificate_status"] == "pending_connected_cycle_trace_M2"
    rule = read_csv("cs133_identity_to_trace_construction_rule.csv")[0]
    assert rule["construction_equivalence_class_id"] == binding["construction_equivalence_class_id"]
    assert rule["stage_topology"] == "left_branch:4;hinge:1;right_branch:4"
    assert rule["identity_arithmetic_role"] == "scope_binding_not_topology_count_formula"


def test_current_nine_rows_are_kernel_enumeration_not_causal_recurrence():
    rows = read_csv("cs133_native_structural_kernel_enumeration.csv")
    assert len(rows) == 9
    assert [int(r["enumeration_row_index"]) for r in rows] == list(range(9))
    assert all(r["row_role"] == "native_structural_kernel_enumeration" for r in rows)
    assert all(r["row_time_semantics"] == "non_temporal_alternative_enumeration" for r in rows)
    assert all(r["monon_completion_status"] == "pending_connected_cycle_trace_M2" for r in rows)
    assert not (DATA / "cs133_native_structural_dec_trace.csv").exists()
    assert not (DATA / "cs133_native_structural_read_only_trace.csv").exists()


def test_kernel_contracts_and_enumeration_rows_are_exact_and_linked():
    contracts = {r["stage_id"]: r for r in read_csv("cs133_structural_kernel_contract.csv")}
    rows = read_csv("cs133_native_structural_kernel_enumeration.csv")
    expected_counts = {"left_branch": 4, "hinge": 1, "right_branch": 4}
    for stage, count in expected_counts.items():
        stage_rows = [r for r in rows if r["stage_id"] == stage]
        assert len(stage_rows) == count
        assert all(r["kernel_id"] == contracts[stage]["kernel_id"] for r in stage_rows)
        assert all(r["kernel_sha256"] == contracts[stage]["kernel_sha256"] for r in stage_rows)
        assert all(r["adm_e_B"] in {"0", "1"} for r in stage_rows)
        assert all(int(r["w_den"]) > 0 and int(r["P_den"]) > 0 for r in stage_rows)
        assert all(math.gcd(abs(int(r["P_num"])), int(r["P_den"])) == 1 for r in stage_rows)
        total = sum(Fraction(int(r["P_num"]), int(r["P_den"])) for r in stage_rows)
        assert total == 1
        z_values = {Fraction(int(r["Z_num"]), int(r["Z_den"])) for r in stage_rows}
        assert z_values == {Fraction(count, 1)}
        assert all(r["P_exact"] == f"{r['P_num']}/{r['P_den']}" for r in stage_rows)


def test_canonical_enumerate_all_execution_propagates_and_conserves_exact_mass():
    rows = read_csv("cs133_native_structural_dec_execution_ledger.csv")
    assert len(rows) == 9
    assert [int(r["execution_row_index"]) for r in rows] == list(range(9))
    assert all(r["row_role"] == "canonical_enumerate_all_mass_propagation" for r in rows)
    assert all(r["row_time_semantics"] == "non_temporal_structural_execution" for r in rows)
    for row in rows:
        incoming = Fraction(int(row["incoming_mass_num"]), int(row["incoming_mass_den"]))
        probability = Fraction(int(row["kernel_probability_num"]), int(row["kernel_probability_den"]))
        outgoing = Fraction(int(row["outgoing_mass_num"]), int(row["outgoing_mass_den"]))
        assert outgoing == incoming * probability
    left = [r for r in rows if r["stage_id"] == "left_branch"]
    hinge = [r for r in rows if r["stage_id"] == "hinge"]
    right = [r for r in rows if r["stage_id"] == "right_branch"]
    assert sum(Fraction(int(r["outgoing_mass_num"]), int(r["outgoing_mass_den"])) for r in left) == 1
    assert hinge[0]["aggregation_rule_id"] == "sum_parent_outgoing_mass"
    assert len(hinge[0]["parent_transition_ids"].split(";")) == 4
    assert Fraction(int(hinge[0]["incoming_mass_num"]), int(hinge[0]["incoming_mass_den"])) == 1
    assert Fraction(int(hinge[0]["outgoing_mass_num"]), int(hinge[0]["outgoing_mass_den"])) == 1
    assert sum(Fraction(int(r["outgoing_mass_num"]), int(r["outgoing_mass_den"])) for r in right) == 1
    audits = read_csv("cs133_structural_execution_mass_audit.csv")
    assert {r["stage_id"] for r in audits} == {"left_branch", "hinge", "right_branch"}
    assert all(r["mass_conservation_status"] == "passed_exact" for r in audits)
    assert all(Fraction(int(r["mass_residual_num"]), int(r["mass_residual_den"])) == 0 for r in audits)


def test_pre_detection_manifest_covers_and_verifies_all_frozen_inputs():
    module = load_gate_module()
    packet = module.verify_pre_detection_freeze(FREEZE_MANIFEST)
    manifest = packet["manifest"]
    roles = {a["artifact_role"] for a in manifest["artifacts"]}
    assert roles == {
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
    assert packet["read_only_enumeration_status"]["stage_kernel_normalization_status"] == "passed_exact"
    assert packet["read_only_execution_status"]["execution_mass_conservation_status"] == "passed_exact"


@pytest.mark.parametrize(
    ("relative_path", "field", "new_value"),
    [
        ("manual/data/cs133/cs133_native_structural_read_only_kernel_enumeration.csv", "identity_packet_sha256", "0" * 64),
        ("manual/data/cs133/cs133_native_structural_read_only_kernel_enumeration.csv", "sigma_e", "mutated"),
        ("manual/data/cs133/cs133_native_structural_read_only_kernel_enumeration.csv", "Z_num", "99"),
        ("manual/data/cs133/cs133_native_structural_read_only_kernel_enumeration.csv", "read_only_row_sha256", "f" * 64),
        ("manual/data/cs133/cs133_structural_boundary_card.csv", "boundary_card_sha256", "e" * 64),
        ("manual/data/cs133/cs133_structural_boundary_card.csv", "boundary_id", "B_mutated"),
        ("manual/data/cs133/cs133_structural_boundary_card.csv", "fractal_octave_coordinate", "01_(8)"),
    ],
)
def test_detector_rejects_any_undeclared_frozen_packet_mutation(tmp_path, relative_path, field, new_value):
    module = load_gate_module()
    manifest_path = copy_frozen_packet(tmp_path)
    path = tmp_path / relative_path
    rows = read_csv(path)
    rows[0][field] = new_value
    write_csv(path, rows)
    with pytest.raises(ValueError, match="frozen artifact (SHA-256|byte-count) mismatch"):
        module.detect_support_form(manifest_path, root=tmp_path)


def test_detector_rejects_row_mutation_even_if_outer_file_hash_is_refreshed(tmp_path):
    module = load_gate_module()
    manifest_path = copy_frozen_packet(tmp_path)
    rel = "manual/data/cs133/cs133_native_structural_read_only_kernel_enumeration.csv"
    path = tmp_path / rel
    rows = read_csv(path)
    rows[0]["sigma_e"] = "mutated"
    write_csv(path, rows)
    refresh_manifest_artifact(module, tmp_path, manifest_path, rel)
    with pytest.raises(ValueError, match="read_only_row_sha256 mismatch"):
        module.detect_support_form(manifest_path, root=tmp_path)


def test_detector_rejects_cross_packet_boundary_mutation_even_with_rehashed_rows(tmp_path):
    module = load_gate_module()
    manifest_path = copy_frozen_packet(tmp_path)
    enum_rel = "manual/data/cs133/cs133_native_structural_kernel_enumeration.csv"
    ro_rel = "manual/data/cs133/cs133_native_structural_read_only_kernel_enumeration.csv"
    enum_path = tmp_path / enum_rel
    ro_path = tmp_path / ro_rel
    enum_rows = read_csv(enum_path)
    ro_rows = read_csv(ro_path)
    enum_rows[0]["boundary_id"] = "B_other"
    enum_rows[0]["enumeration_row_sha256"] = module.canonical_row_hash(enum_rows[0], "enumeration_row_sha256")
    ro_rows[0]["boundary_id"] = "B_other"
    ro_rows[0]["enumeration_row_sha256"] = enum_rows[0]["enumeration_row_sha256"]
    ro_rows[0]["read_only_row_sha256"] = module.canonical_row_hash(ro_rows[0], "read_only_row_sha256")
    write_csv(enum_path, enum_rows)
    write_csv(ro_path, ro_rows)
    refresh_manifest_artifact(module, tmp_path, manifest_path, enum_rel)
    refresh_manifest_artifact(module, tmp_path, manifest_path, ro_rel)
    with pytest.raises(ValueError, match="cross-packet mismatch for boundary_id"):
        module.detect_support_form(manifest_path, root=tmp_path)


def test_detector_classifies_only_pq_under_declared_L():
    module = load_gate_module()
    result = read_csv("cs133_structural_detection_result.csv")[0]
    assert result["detected_support_core"] == "1:2"
    assert result["declared_scope_L"] == "6"
    assert result["scope_conditioned_form"] == "1:2:6"
    assert result["classification_mode"] == "blind_pq_under_declared_L"
    assert result["pq_hypothesis_visible_to_detector"] == "false"
    assert result["L_scope_visible_to_detector"] == "true"
    assert result["pre_detection_freeze_status"] == "passed"
    assert result["execution_mass_conservation_status"] == "passed_exact"
    assert module.solve_support_parameters(4) == [(1, 2)]
    assert module.solve_support_parameters(3) == []


def test_hypothesis_and_pq_only_counterfactual_are_computed_after_detection():
    audit = read_csv("cs133_structural_hypothesis_detection_audit.csv")[0]
    assert audit["detection_precedes_hypothesis_join"] == "true"
    assert audit["detected_support_core"] == "1:2"
    assert audit["support_core_hypothesis"] == "1:2"
    assert audit["pq_hypothesis_match_status"] == "match"
    assert audit["scope_consistency_status"] == "match"
    assert audit["hypothesis_match_status"] == "match"
    counterfactual = read_csv("cs133_structural_hypothesis_counterfactual_audit.csv")[0]
    assert counterfactual["counterfactual_hidden_hypothesis"] == "2:2:6"
    assert counterfactual["detected_support_core"] == "1:2"
    assert counterfactual["pq_hypothesis_match_status"] == "mismatch"
    assert counterfactual["scope_consistency_status"] == "match"
    assert counterfactual["detector_output_change_status"] == "unchanged"
    assert counterfactual["audit_status"] == "passed"


def test_counterfactual_identity_is_a_separate_occurrence_and_statuses_are_computed():
    row = read_csv("cs133_identity_counterfactual_audit.csv")[0]
    assert row["identity_packet_change_status"] == "changed"
    assert row["occurrence_binding_change_status"] == "changed"
    assert row["trace_topology_change_status"] == "unchanged_by_declared_shared_motif_equivalence_class"
    assert row["kernel_enumeration_packet_change_status"] == "changed_due_to_identity_bound_provenance"
    assert row["execution_packet_change_status"] == "changed_due_to_identity_bound_provenance"
    assert row["counterfactual_row_hash_status"] == "passed"
    assert row["counterfactual_packet_admission_status"] == "valid_separate_scoped_occurrence"
    assert row["audit_status"] == "passed_declared_equivalence_class"
    assert row["reference_trace_topology_sha256"] == row["counterfactual_trace_topology_sha256"]
    assert row["reference_kernel_enumeration_packet_sha256"] != row["counterfactual_kernel_enumeration_packet_sha256"]


def test_capacity_fill_audit_is_rule_derived_and_not_recurrence_closure():
    rule = read_csv("cs133_c3_window_capacity_rule.csv")[0]
    assert rule["C3_value"] == "3"
    assert rule["window_capacity_rule"] == "C3_times_declared_L"
    assert rule["window_capacity_derivation"] == "3*6"
    assert rule["window_capacity_value"] == "18"
    row = read_csv("cs133_structural_support_audit.csv")[0]
    expected = {
        "Pi_support": "4",
        "hinge_contribution": "1",
        "RD_AO": "9",
        "omega": "6",
        "rhoD_omega": "6",
        "C3": "3",
        "PD": "18",
        "QD": "9",
        "window_capacity": "18",
        "capacity_fill_residual": "0",
        "X_shedding": "0",
    }
    for key, value in expected.items():
        assert row[key] == value
    assert row["recurrence_closure_status"] == "not_evaluated_M1"
    assert row["full_period_closure"] == "not_evaluated_M1"
    assert row["proper_prefix_closure_count"] == "not_evaluated_M1"
    assert row["primitive_period"] == "not_evaluated_M1"
    assert "recurrence_closure" in row["support_quantities_role"]
    assert not (DATA / "cs133_c3_closure_rule.csv").exists()


def test_target_independence_audit_is_computed_and_score_lane_closed():
    rows = read_csv("cs133_target_independence_audit.csv")
    assert len(rows) >= 18
    assert all(r["status"] == "pass" for r in rows)
    assert all(r["target_value_read_status"] == "not_read" for r in rows)
    assert {r["check_id"] for r in rows} >= {
        "pre_detection_manifest_verified",
        "execution_mode_enforced",
        "stage_kernel_normalization_enforced",
        "stage_mass_conservation_enforced",
        "support_core_derived_from_enumeration",
        "L_is_declared_scope",
        "identity_specific_occurrence_manifested",
        "capacity_not_recurrence_closure",
        "enumeration_not_causal_time",
        "recurrence_not_claimed",
        "SI_anchor_inactive",
        "target_join_closed",
    }


def test_manifest_hashes_all_gate_files_and_keeps_M2_closed():
    manifest = json.loads((DATA / "cs133_structural_occurrence_manifest.json").read_text(encoding="utf-8"))
    state = manifest["current_state"]
    assert state["kernel_enumeration"] == "frozen_non_temporal"
    assert state["canonical_DEC_execution"] == "enumerate_all_mass_conserved"
    assert state["pre_detection_freeze"] == "cryptographically_enforced"
    assert state["detected_support_core"] == "1:2"
    assert state["declared_scope_L"] == "6"
    assert state["scope_conditioned_form"] == "1:2:6"
    assert state["capacity_fill_audit"] == "passed_exact_not_recurrence_closure"
    assert state["temporal_recurrence_certificate"] == "not_materialized"
    assert state["SI_anchor"] == "inactive"
    assert state["target_join"] == "closed"
    for row in manifest["files"]:
        p = ROOT / row["path"]
        assert p.is_file()
        assert p.stat().st_size == row["bytes"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row["sha256"]


def test_gate_generator_is_deterministic():
    before = file_hashes()
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    after = file_hashes()
    assert after == before
