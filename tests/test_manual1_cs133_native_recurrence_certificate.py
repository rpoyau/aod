import csv
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "cs133"
SCRIPT = ROOT / "manual" / "scripts" / "build_cs133_native_recurrence_certificate.py"
PRE = DATA / "cs133_native_recurrence_pre_certificate_manifest.json"
MANIFEST = DATA / "cs133_native_recurrence_manifest.json"


def read_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_module():
    spec = importlib.util.spec_from_file_location("cs133_recurrence", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in {"dist", ".pytest_cache", "__pycache__"} for part in p.parts):
            h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
            h.update(p.read_bytes())
    return h.hexdigest()


def test_generator_is_deterministic_and_manifest_hashes_outputs():
    before = {p.name: p.read_bytes() for p in DATA.glob("cs133_native_recurrence*") if p.is_file()}
    before["operator"] = (DATA / "cs133_core_outer_coupling_operator.csv").read_bytes()
    before["states"] = (DATA / "cs133_native_coupled_state_registry.csv").read_bytes()
    subprocess.run([sys.executable, str(SCRIPT)], check=True)
    after = {p.name: p.read_bytes() for p in DATA.glob("cs133_native_recurrence*") if p.is_file()}
    after["operator"] = (DATA / "cs133_core_outer_coupling_operator.csv").read_bytes()
    after["states"] = (DATA / "cs133_native_coupled_state_registry.csv").read_bytes()
    assert after == before
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["manifest_id"] == "cs133_native_coupled_core_outer_primitive_recurrence_v1"
    for row in manifest["files"]:
        p = ROOT / row["path"]
        assert p.stat().st_size == row["bytes"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row["sha256"]


def test_phase_count_is_derived_from_detected_pq_not_declared_L():
    module = load_module()
    identity = read_csv("cs133_identity_packet.csv")[0]
    binding = read_csv("cs133_fractal_elementary_occurrence_binding.csv")[0]
    detection = read_csv("cs133_structural_detection_result.csv")[0]
    changed_scope = dict(detection)
    changed_scope["declared_scope_L"] = "8"
    operator = module.build_coupling_operator(identity, binding, changed_scope)
    assert operator["detected_p"] == "1"
    assert operator["detected_q"] == "2"
    assert operator["sector_count"] == "3"
    assert operator["native_coupled_state_count"] == "2"
    assert operator["phase_count"] == "6"
    assert operator["declared_scope_L"] == "8"
    assert operator["recurrence_length_uses_declared_L"] == "false"


def test_connected_state_cycle_is_six_distinct_states_and_single_permutation_cycle():
    states = read_csv("cs133_native_coupled_state_registry.csv")
    transitions = read_csv("cs133_native_recurrence_transition_matrix.csv")
    assert len(states) == 6
    assert len({r["state_id"] for r in states}) == 6
    assert [(r["sector_label"], r["coupled_phase"]) for r in states] == [
        ("left_support", "A"),
        ("left_support", "B"),
        ("hinge_support", "A"),
        ("hinge_support", "B"),
        ("right_support", "A"),
        ("right_support", "B"),
    ]
    current = transitions[0]["source_state_id"]
    start = current
    seen = []
    for row in transitions:
        assert row["source_state_id"] == current
        seen.append(current)
        current = row["target_state_id"]
        assert row["execution_mode"] == "enumerate_all"
        assert row["P_exact"] == "1/1"
    assert current == start
    assert len(set(seen)) == 6
    assert start not in seen[1:]


def test_recurrence_execution_uses_realized_integer_bips_and_exact_mass():
    rows = read_csv("cs133_native_recurrence_dec_execution_ledger.csv")
    assert len(rows) == 6
    for i, row in enumerate(rows, start=1):
        incoming = Fraction(int(row["incoming_mass_num"]), int(row["incoming_mass_den"]))
        outgoing = Fraction(int(row["outgoing_mass_num"]), int(row["outgoing_mass_den"]))
        assert incoming == outgoing == 1
        assert row["mass_conservation_status"] == "passed"
        assert row["bip_increment_num"] == "1"
        assert row["bip_increment_den"] == "1"
        assert row["duration_semantics"] == "realized_integer_bip_count"
        assert row["cumulative_bip_count"] == str(i)
        assert row["target_frequency_input_status"] == "absent"
    audit = read_csv("cs133_native_recurrence_mass_audit.csv")
    assert all(r["mass_residual_num"] == "0" for r in audit)
    assert all(r["mass_conservation_status"] == "passed" for r in audit)


def test_primitive_certificate_passes_without_metrological_or_target_input():
    cert = read_csv("cs133_native_recurrence_certificate.csv")[0]
    assert cert["primitive_recurrence_bip_count"] == "6"
    assert cert["duration_semantics"] == "realized_integer_bip_count"
    assert cert["full_period_closure"] == "passed"
    assert cert["proper_prefix_closure_count"] == "0"
    assert cert["primitive_period_minimality"] == "passed"
    assert cert["state_permutation_audit"] == "passed_single_cycle"
    assert cert["exact_mass_conservation"] == "passed"
    assert cert["recurrence_length_uses_declared_L"] == "false"
    assert cert["recurrence_L_coincidence_status"] == "derived_recurrence_count_matches_declared_scope"
    assert cert["target_frequency_input_status"] == "absent"
    assert cert["observation_packet_input_status"] == "absent"
    assert cert["metrological_correspondence_status"] == "not_active_until_M3"
    assert cert["SI_anchor_status"] == "inactive"
    assert cert["certificate_status"] == "passed_native_recurrence_only"
    assert cert["anchor_eligibility_status"] == "eligible_for_M3_metrological_definition"


def test_counterfactual_types_recurrence_as_shared_family_instantiated_at_cs_scope():
    row = read_csv("cs133_native_recurrence_counterfactual_audit.csv")[0]
    assert row["identity_packet_change_status"] == "changed"
    assert row["occurrence_binding_change_status"] == "changed"
    assert row["coupled_state_packet_change_status"] == "changed"
    assert row["transition_matrix_packet_change_status"] == "changed"
    assert row["transition_topology_signature_status"] == "unchanged"
    assert row["primitive_cycle_signature_status"] == "unchanged"
    assert row["recurrence_length_change_status"] == "unchanged"
    assert row["recurrence_specificity_status"] == "shared_elementary_recurrence_instantiated_at_Cs_scope"
    assert row["metrological_definition_status"] == "pending_M3"


def test_pre_certificate_manifest_rejects_mutated_transition_packet(tmp_path):
    module = load_module()
    manifest = json.loads(PRE.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        src = ROOT / artifact["path"]
        dst = tmp_path / artifact["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    manifest_path = tmp_path / PRE.relative_to(ROOT)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRE, manifest_path)
    old_root = module.ROOT
    module.ROOT = tmp_path
    try:
        module.verify_pre_certificate_manifest(manifest_path)
        target = tmp_path / "manual/data/cs133/cs133_native_recurrence_transition_matrix.csv"
        text = target.read_text(encoding="utf-8").replace("1/1", "2/1", 1)
        target.write_text(text, encoding="utf-8")
        with pytest.raises(ValueError, match="SHA mismatch"):
            module.verify_pre_certificate_manifest(manifest_path)
    finally:
        module.ROOT = old_root


def test_m2_files_contain_no_cs_clock_frequency_or_physical_hyperfine_state_claim():
    names = [
        "cs133_core_outer_coupling_operator.csv",
        "cs133_native_coupled_state_registry.csv",
        "cs133_native_recurrence_transition_matrix.csv",
        "cs133_native_recurrence_dec_execution_ledger.csv",
        "cs133_native_recurrence_certificate.csv",
        "cs133_native_recurrence_counterfactual_audit.csv",
        "cs133_native_recurrence_manifest.json",
    ]
    text = "\n".join((DATA / name).read_text(encoding="utf-8") for name in names)
    assert "9192631770" not in text
    assert "9,192,631,770" not in text
    assert "physical_hyperfine" not in text
    assert "target_frequency_input_status,absent" in text or '"target_frequency_input": "absent"' in text


def test_manual_i_renders_m2_and_current_roadmap_retypes_it_as_shared_c6_family():
    appendix = (ROOT / "manual/appendices/F_cs133_structural_occurrence_gate.tex").read_text(encoding="utf-8")
    assert "M2 native coupled core--outer recurrence admission" in appendix
    assert "N_{\\rm phase}" in appendix
    assert "primitive\\_recurrence\\_bip\\_count" in appendix
    assert "shared\\_elementary\\_recurrence\\_instantiated\\_at\\_Cs\\_scope" in appendix
    assert "Roadmap reclassification: recurrence/support fixture" in appendix
    roadmap = (ROOT / "MANUAL_I_ROADMAP.md").read_text(encoding="utf-8")
    assert "six executed transitions" in roadmap
    assert "R0 | v40.03r05.2" in roadmap
    assert "monon-to-bip conversion" in roadmap
    assert "R1 | v40.03r06.3.1" in roadmap
    assert "Canonical serialization" in roadmap

def test_main_shared_and_manual2_stay_frozen_for_m2():
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
