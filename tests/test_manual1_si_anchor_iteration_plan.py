import csv
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "manual" / "data" / "roadmap"
C6 = ROOT / "manual" / "data" / "c6"
SCRIPT = ROOT / "manual" / "scripts" / "build_c6_hydrogen_first_roadmap.py"


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in {"dist", ".pytest_cache", "__pycache__"} for part in p.parts):
            h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
            h.update(p.read_bytes())
    return h.hexdigest()


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_release_is_hydrogen1_native_occurrence_gate_and_next_gate_is_transition_atlas():
    version = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    assert "Canonical version:" in version
    roadmap = (ROOT / "MANUAL_I_ROADMAP.md").read_text(encoding="utf-8")
    assert "R0 | v40.03r05.2" in roadmap
    assert "monon-to-bip" in roadmap
    assert "R1 | v40.03r06.3.1" in roadmap
    assert "carried forward complete" in roadmap
    assert "Canonical serialization" in roadmap
    assert "R2 | v40.03r07" in roadmap
    assert "Hydrogen-1 native occurrence" in roadmap
    assert "current complete" in roadmap
    assert "R3 | v40.03r08" in roadmap
    assert "Hydrogen transition and SADAR-lock atlas" in roadmap
    assert "next" in roadmap
    assert "historical frozen adapter" in roadmap
    assert "Hydrogen r10" in (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")


def test_manual1_versionless_roadmap_appendix_is_relational_and_hydrogen_first():
    appendix = (ROOT / "manual/appendices/E_native_si_anchor_iteration_plan.tex").read_text(encoding="utf-8")
    assert "Relational Temporal Semantics and Hydrogen-First Roadmap" in appendix
    assert "N_{\\mathrm{bip}}^{\\min}(\\mathrm{monon})=2" in appendix
    assert "witness-count statement" in appendix
    assert "Hydrogen-first verification" in appendix
    assert "500:675:756:800" in appendix
    assert "1512:1120:1000:945" in appendix
    assert "v40." not in appendix


def test_c6_support_policy_retypes_recurrence_without_calibration():
    policy = rows(C6 / "c6_recurrence_support_policy.csv")[0]
    assert policy["primitive_support_id"] == "00o8_C6_1_2_6"
    assert policy["scope_conditioned_form"] == "1:2:6"
    assert policy["connected_transition_count"] == "6"
    assert policy["executed_bip_count"] == "6"
    assert policy["bip_semantics"] == "admitted_executed_directed_beat_token"
    assert policy["trace_count_temporal_status"] == "execution_structure_not_temporal_magnitude"
    assert policy["monon_semantics"] == "primitive_completed_cycle_class"
    assert policy["minimal_direct_witness_total_bip_count"] == "2"
    assert policy["minimal_direct_witness_status"] == "witness_only_not_duration"
    assert policy["monon_to_bip_conversion_status"] == "not_declared"
    assert policy["C6_role"] == "six_slot_support_and_shared_recurrence_fixture"
    assert policy["cs_lane_role"] == "historical_adapter_optional_downstream_reference"
    assert policy["target_value_read_status"] == "not_read"


def test_consequent_forms_share_one_support_packet_and_do_not_define_time():
    data = rows(C6 / "primitive_and_consequent_form_registry.csv")
    assert [r["route_form"] for r in data] == ["1:2:6", "3:3:6", "3:4:6"]
    assert {r["primitive_support_id"] for r in data} == {"00o8_C6_1_2_6"}
    assert {r["outer_support_length"] for r in data} == {"6"}
    assert {r["temporal_unit_status"] for r in data} == {"not_defined_by_support_form"}
    assert {r["monon_conversion_status"] for r in data} == {"not_declared"}
    by_form = {r["route_form"]: r for r in data}
    assert by_form["1:2:6"]["C6_compatibility_status"] == "certified_by_M2_shared_recurrence_family"
    assert by_form["3:3:6"]["C6_compatibility_status"] == "passed_r06_3_1_canonical_serialization_closed_semantics_and_support_family_consistency"
    assert by_form["3:4:6"]["C6_compatibility_status"] == "passed_r06_3_1_canonical_serialization_closed_semantics_and_support_family_consistency"


def test_hydrogen_plan_uses_relational_protocol_without_target_value():
    data = rows(C6 / "hydrogen_occurrence_plan.csv")
    assert [r["occurrence_id"] for r in data] == ["H1_00o8", "H2_00o8", "H3_00o8"]
    assert [r["extension_3_4_6_count"] for r in data] == ["0", "1", "2"]
    assert {r["primitive_support_id"] for r in data} == {"00o8_C6_1_2_6"}
    assert {r["relational_temporal_protocol_id"] for r in data} == {"aod_relational_temporal_measurement_packet_v1"}
    assert data[0]["generator_status"] == "materialized_connected_local_Q4_direct_return_occurrence"
    assert {r["generator_status"] for r in data[1:]} == {"planned_not_materialized"}
    assert {r["target_value_read_status"] for r in data} == {"not_read"}


def test_balmer_exact_ratio_card_is_derived_and_downstream_only():
    data = rows(C6 / "balmer_exact_ratio_card.csv")
    assert [int(r["frequency_ratio_integer"]) for r in data] == [500, 675, 756, 800]
    assert [int(r["period_ratio_integer"]) for r in data] == [1512, 1120, 1000, 945]
    factors = [Fraction(int(r["ideal_frequency_factor_num"]), int(r["ideal_frequency_factor_den"])) for r in data]
    assert factors == [Fraction(5, 36), Fraction(3, 16), Fraction(21, 100), Fraction(2, 9)]
    assert {r["ratio_card_role"] for r in data} == {"downstream_dimensionless_relational_comparison"}
    assert {r["native_generator_access_status"] for r in data} == {"forbidden"}
    assert {r["SI_unit_status"] for r in data} == {"not_required"}


def test_milestone_plan_rebases_calibration_lane_to_relational_time():
    plan = rows(ROADMAP / "manual1_c6_hydrogen_first_milestone_plan.csv")
    assert [r["milestone_id"] for r in plan] == [f"R{i}" for i in range(14)]
    assert [int(r["sequence"]) for r in plan] == list(range(14))
    assert plan[0]["target_release"] == "v40.03r05.2"
    assert plan[0]["status"] == "carried_forward_complete"
    assert plan[1]["target_release"] == "v40.03r06.3.1"
    assert plan[1]["status"] == "carried_forward_complete"
    assert plan[2]["target_release"] == "v40.03r07"
    assert plan[2]["status"] == "current_complete"
    assert plan[3]["status"] == "next"
    assert plan[1]["title"] == "Canonical serialization and closed-semantics binding"
    assert plan[2]["title"] == "Hydrogen-1 native occurrence gate"
    assert plan[3]["title"] == "Hydrogen native transition and SADAR lock atlas"
    assert plan[13]["title"] == "Manual-II reassessment"
    assert {r["dependency_graph_role"] for r in plan} == {"authoritative_execution_order"}


def test_semantic_migration_removes_type_error_without_recomputing_rows():
    data = rows(C6 / "r05_1_to_r05_2_temporal_semantics_migration.csv")
    assert len(data) >= 4
    assert {r["scientific_row_change"] for r in data} <= {"no_scientific_row_recompute", "semantic_only"}
    assert any(r["new_semantic_id"] == "monon_cycle_class_with_two_bip_minimal_direct_witness" for r in data)
    assert any(r["new_semantic_id"] == "sheddic_exchange_channel" for r in data)


def test_generator_is_deterministic_and_manifest_is_semantic_repair():
    generated = [
        C6 / "c6_recurrence_support_policy.csv",
        C6 / "primitive_and_consequent_form_registry.csv",
        C6 / "hydrogen_occurrence_plan.csv",
        C6 / "balmer_exact_ratio_card.csv",
        C6 / "element_118_atlas_schema.csv",
        C6 / "r05_1_to_r05_2_temporal_semantics_migration.csv",
        C6 / "c6_hydrogen_first_plan_manifest.json",
        ROADMAP / "manual1_c6_hydrogen_first_milestone_plan.csv",
        ROADMAP / "manual1_c6_hydrogen_first_gate_dependencies.csv",
        ROADMAP / "manual1_c6_hydrogen_first_file_change_matrix.csv",
        ROADMAP / "manual1_roadmap_supersession_registry.csv",
        ROADMAP / "manual1_c6_hydrogen_first_change_plan.md",
        ROADMAP / "manual1_c6_hydrogen_first_plan_manifest.json",
    ]
    before = {p: p.read_bytes() for p in generated}
    subprocess.run([sys.executable, str(SCRIPT)], check=True)
    after = {p: p.read_bytes() for p in generated}
    assert before == after
    manifest = json.loads((ROADMAP / "manual1_c6_hydrogen_first_plan_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.03r07"
    assert manifest["release_class"] == "target_blind_H1_native_occurrence_gate_no_target_or_score"
    assert manifest["current_state"]["H1_native_occurrence"] == "materialized_connected_local_Q4_direct_return"
    assert manifest["current_state"]["monon_to_bip_conversion_status"] == "not_declared"
    assert manifest["current_state"]["temporal_measurement"] == "primitive_subject_reference_SADAR_lock"
    assert manifest["current_state"]["sheddic_terminology"] == "native_sheddic_only"
    for row in manifest["files"]:
        p = ROOT / row["path"]
        assert p.stat().st_size == row["bytes"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row["sha256"]


def test_main_shared_and_manual2_remain_frozen():
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
