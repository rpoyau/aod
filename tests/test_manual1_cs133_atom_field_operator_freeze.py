import csv
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "cs133"
SCRIPT = ROOT / "manual" / "scripts" / "build_cs133_atom_field_operator_freeze.py"
MANIFEST = DATA / "cs133_atom_field_operator_manifest.json"


def read_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in {"dist", ".pytest_cache", "__pycache__"} for part in p.parts):
            h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
            h.update(p.read_bytes())
    return h.hexdigest()


def test_generator_is_deterministic_and_manifest_hashes_contract_files():
    names = [
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
    ]
    before = {name: (DATA / name).read_bytes() for name in names}
    subprocess.run([sys.executable, str(SCRIPT)], check=True)
    after = {name: (DATA / name).read_bytes() for name in names}
    assert before == after
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["manifest_id"] == "cs133_scoped_native_atom_field_operator_freeze_v1"
    assert manifest["current_state"]["M3_atom_field_operator"] == "complete_frozen_not_executed"
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_input_lock_binds_only_m2_native_recurrence_artifacts_and_target_is_absent():
    row = read_csv("cs133_atom_field_input_lock.csv")[0]
    assert row["primitive_recurrence_bip_count"] == "6"
    assert row["duration_semantics"] == "realized_integer_bip_count"
    assert row["target_frequency_input_status"] == "absent"
    assert row["observation_packet_input_status"] == "absent"
    assert row["target_value_read_status"] == "not_read"
    paths = row["allowed_input_paths"].split(";")
    assert all(path.startswith("manual/data/cs133/") for path in paths)
    assert not any("shared/data" in path or "observation" in path for path in paths)


def test_drive_phase_domain_is_exact_Q_mod_Z_with_unique_canonical_representatives():
    rows = read_csv("cs133_drive_phase_domain.csv")
    assert len(rows) == 12
    canonical = []
    for order, row in enumerate(rows):
        assert int(row["candidate_order"]) == order
        assert row["drive_unit"] == "turns_per_bip"
        assert row["phase_equivalence_rule"] == "theta_equivalent_theta_plus_integer_turns"
        value = Fraction(int(row["canonical_phase_num"]), int(row["canonical_phase_den"]))
        assert 0 <= value < 1
        assert row["canonical_phase_exact"] == f"{value.numerator}/{value.denominator}"
        canonical.append(value)
    assert len(set(canonical)) == 12
    assert Fraction(1, 6) in canonical


def test_interaction_windows_are_derived_from_the_six_bip_cycle_before_search():
    rows = read_csv("cs133_atom_field_interaction_window_policy.csv")
    assert [r["interaction_window_id"] for r in rows] == [
        "primary_half_cycle_window",
        "refinement_preclosure_window",
    ]
    assert [r["free_evolution_bip_count"] for r in rows] == ["3", "5"]
    assert [r["native_phase_advance_exact"] for r in rows] == ["1/2", "5/6"]
    assert all(r["target_frequency_input_status"] == "absent" for r in rows)
    assert all(r["window_status"] == "frozen_before_search" for r in rows)


def test_exact_operator_rules_conserve_unit_mass_and_do_not_claim_continuum_ramsey_math():
    rows = read_csv("cs133_atom_field_operator_transition_rules.csv")
    by_id = {r["transition_rule_id"]: r for r in rows}
    assert by_id["balanced_first_interaction"]["mass_assignment"] == "A=1/2;B=1/2"
    assert by_id["aligned_phase_recombination"]["mass_assignment"] == "A=0/1;B=1/1"
    assert by_id["anti_aligned_phase_recombination"]["mass_assignment"] == "A=1/1;B=0/1"
    assert by_id["generic_off_phase_recombination"]["mass_assignment"] == "A=1/2;B=1/2"
    assert all(r["arithmetic_domain"] == "exact_rational_finite_state_operator" for r in rows)
    response = read_csv("cs133_atom_field_response_function_contract.csv")[0]
    assert response["response_range_exact"] == "{0/1,1/2,1/1}"
    assert response["continuum_trigonometric_claim_status"] == "not_claimed"
    assert response["decimal_comparison_status"] == "forbidden"


def test_response_representation_registry_separates_rational_algebraic_and_symbolic_domains():
    rows = read_csv("cs133_atom_field_exact_response_representation_registry.csv")
    by_domain = {r["arithmetic_domain"]: r for r in rows}
    assert set(by_domain) == {
        "exact_rational_finite_state_operator",
        "exact_algebraic_operator",
        "exact_symbolic_operator",
    }
    assert by_domain["exact_rational_finite_state_operator"]["selected_for_current_operator"] == "true"
    assert all(r["decimal_winner_policy"] == "forbidden" for r in rows)


def test_selector_freezes_alias_resolution_and_separates_cadence_from_period():
    row = read_csv("cs133_atom_field_resonance_selector_contract.csv")[0]
    assert row["alias_equivalence_rule"] == "Q_mod_Z"
    assert row["primary_window_id"] == "primary_half_cycle_window"
    assert row["refinement_window_id"] == "refinement_preclosure_window"
    assert row["cadence_primary_object"] == "native_resonance_cadence_turns_per_bip"
    assert row["period_inverse_rule"] == "invert_only_positive_unique_rational_cadence"
    assert row["selector_status"] == "frozen_not_executed"
    assert row["target_frequency_input_status"] == "absent"


def test_zero_perturbation_and_control_audits_are_frozen_before_search():
    zero = read_csv("cs133_atom_field_zero_perturbation_policy.csv")[0]
    assert zero["external_field_state"] == "zero"
    assert zero["thermal_motion_state"] == "zero"
    assert zero["collision_loading_state"] == "zero"
    assert zero["zero_perturbation_extraction_rule"] == "select_all_zero_perturbation_states_before_phase_scan"
    assert zero["policy_status"] == "frozen_before_search"
    controls = read_csv("cs133_atom_field_resonance_control_audit_plan.csv")
    assert {r["control_id"] for r in controls} == {
        "drive_off",
        "phase_permuted",
        "detuned_candidate",
        "state_label_permutation",
        "counterfactual_identity_packet",
    }
    assert all(r["control_status"] == "declared_not_executed" for r in controls)


def test_operator_is_frozen_but_unexecuted_and_physical_state_labels_remain_pending():
    row = read_csv("cs133_atom_field_interaction_operator.csv")[0]
    assert row["operator_execution_status"] == "frozen_not_executed"
    assert row["native_resonance_search_status"] == "not_started"
    assert row["clock_state_interpretation_status"] == "pending_correspondence_mode_gate"
    assert row["physical_hyperfine_interpretation_status"] == "not_active_until_correspondence_mode_gate"
    assert row["SI_anchor_status"] == "inactive"
    assert row["target_frequency_input_status"] == "absent"
    assert row["target_value_read_status"] == "not_read"


def test_si_activation_guard_requires_unique_exact_zero_perturbation_result():
    row = read_csv("cs133_atom_field_si_activation_guard.csv")[0]
    assert row["required_resonance_status"] == "exact_unique_candidate"
    assert row["required_alias_class_count"] == "1"
    assert row["required_zero_perturbation_status"] == "passed"
    assert row["required_response_contrast_status"] == "strict_positive_peak_contrast"
    assert row["candidate_set_or_interval_action"] == "keep_SI_anchor_pending"
    assert row["current_SI_anchor_status"] == "inactive"


def test_m3_files_contain_no_cs_reference_number_and_no_search_result():
    paths = list(DATA.glob("cs133_atom_field*")) + [DATA / "cs133_drive_phase_domain.csv", SCRIPT]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.is_file())
    forbidden = ["".join(("919", "263", "1770")), ",".join(("9", "192", "631", "770"))]
    assert not any(token in text for token in forbidden)
    assert "target_frequency_input_status,absent" in text or '"target_frequency_input": "absent"' in text
    assert "exact_unique_candidate" in text  # guard/status vocabulary only
    assert read_csv("cs133_atom_field_interaction_operator.csv")[0]["native_resonance_search_status"] == "not_started"


def test_manual_i_retains_operator_freeze_as_historical_adapter_after_c6_rebase():
    appendix = (ROOT / "manual/appendices/F_cs133_structural_occurrence_gate.tex").read_text(encoding="utf-8")
    assert "M3 Cs-scoped native atom--field interaction operator freeze" in appendix
    assert "\\mathbb{Q}/\\mathbb{Z}" in appendix
    assert "exact rational finite-state response operator" in appendix.lower()
    assert "target frequency remains absent" in appendix.lower()
    assert "historical adapter" in appendix
    roadmap = (ROOT / "MANUAL_I_ROADMAP.md").read_text(encoding="utf-8")
    assert "historical frozen adapter" in roadmap
    assert "It is not the source of native AOD time" in roadmap
    assert "R1 | v40.03r06.3.1" in roadmap
    assert "Canonical serialization" in roadmap

def test_main_shared_stays_frozen_and_manual2_hash_tracks_active_goal():
    active_goal_for_sections = json.loads((ROOT / "cycle" / "ACTIVE_GOAL.json").read_text(encoding="utf-8"))
    expected_sections_hash = {"R3": "37df5b19df58635fe4a4bc821b35b5eb80bcf654436cf28fcc9cd3e4431dd640"}.get(active_goal_for_sections.get("milestone_id"), "b94666bbec27fbd494f196c7ca780c01395eff1a15fc22f08d3be551ef649837")
    assert tree_hash(ROOT / "sections") == expected_sections_hash
    assert tree_hash(ROOT / "appendices") == "186538b1adca28b42675c36de5b66f80fa8bce774b0c45620d4e55b46f8443a8"
    assert tree_hash(ROOT / "shared") == "bdc0be37dd11f3c28d9c720d1ec99196015ede0a491a6fb5c31a3ffa270bfa39"
    active_goal = json.loads((ROOT / "cycle" / "ACTIVE_GOAL.json").read_text(encoding="utf-8"))
    expected_manual2_hash = {
        "R1": "345842a20f4ee5c9928ad1b3d648e41d0a2bb53a6b8f679fff2b71be158fdacd",
        "R2": "345842a20f4ee5c9928ad1b3d648e41d0a2bb53a6b8f679fff2b71be158fdacd",
        "R3": "7c50763b9f7c1f7574635f67f18a574e966665a27b6b70f6d17c35b81c1baf04",
        "R08": "23f31bf58e9f90cb4142b4c2f90c1d2ea32f4b0121573fbacee0448670dd2248",
        "R08.1": "d6c48ba0372edc133092734055b2d8574da30a255941d28241f4ef13d362d8b6",
        "R10": "df413022d98d58272e912c7751db4978c59d1c6993a2f2680b00797f2f1aa905",
        "R11": "be610b1e95c564e087646fc074563854bd75b98fd8f7f73c79aa74d431180080",
        "R12": "be610b1e95c564e087646fc074563854bd75b98fd8f7f73c79aa74d431180080",
            "R13": "7e11fc292f00db45978c28c69d1bf1e4cb1c04e36c92198391da5fbf5b9f4bce",
            "R15": "7e11fc292f00db45978c28c69d1bf1e4cb1c04e36c92198391da5fbf5b9f4bce",
            "R15.1": "7e11fc292f00db45978c28c69d1bf1e4cb1c04e36c92198391da5fbf5b9f4bce",
        "R21": "e38769e59aeb2ee069adef912cce936f3650df75493b65f4a257e625f22305df",
        "R21.1": "e38769e59aeb2ee069adef912cce936f3650df75493b65f4a257e625f22305df",
        "R21.2": "e38769e59aeb2ee069adef912cce936f3650df75493b65f4a257e625f22305df",
        "R22": "e38769e59aeb2ee069adef912cce936f3650df75493b65f4a257e625f22305df",
        "R23": "e38769e59aeb2ee069adef912cce936f3650df75493b65f4a257e625f22305df",
        "R23.1": "e38769e59aeb2ee069adef912cce936f3650df75493b65f4a257e625f22305df",
        "R24": "85128799364c4df53cf70a88fd58caf5c03e131487d173002ea981bc46e2beb7",
        "R24.1": "85128799364c4df53cf70a88fd58caf5c03e131487d173002ea981bc46e2beb7",
        "R25": "345842a20f4ee5c9928ad1b3d648e41d0a2bb53a6b8f679fff2b71be158fdacd",
            "R15.2": "7e11fc292f00db45978c28c69d1bf1e4cb1c04e36c92198391da5fbf5b9f4bce",
            "R16": "7e11fc292f00db45978c28c69d1bf1e4cb1c04e36c92198391da5fbf5b9f4bce",
    }.get(active_goal.get("milestone_id"), "83cd28ec6bf0422a721e6fe881debdd8488fee8e84eaef3a8a0d0940d05e8b0f")
    assert tree_hash(ROOT / "manual-2") == expected_manual2_hash
