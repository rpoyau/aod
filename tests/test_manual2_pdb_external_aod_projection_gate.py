import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def read_csv(name: str):
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r17_projection_files_exist_and_are_manifested():
    required = [
        "pdb_external_aod_contact_projection.csv",
        "pdb_external_aod_contact_projection_summary.csv",
        "pdb_external_aod_contact_projection_policy_application.csv",
        "pdb_external_aod_contact_projection_leakage_checks.csv",
        "pdb_external_aod_contact_projection_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_aod_contact_projection_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r17"
    assert manifest["evaluation_pair_count"] == 946
    assert manifest["projection_out_of_scope_count"] == 946
    assert manifest["projection_contact_count"] == 0
    assert manifest["target_value_read_status"] == "not_read_by_projection_gate"
    assert manifest["residual_status"] == "not_computed_in_v40.02r17"
    assert manifest["score_status"] == "projection_gate_only_no_residual_score"
    assert manifest["sadar_context_id"] == "sadar_mol_005"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r17_projection_reads_frozen_boundary_and_frozen_aod_packet_but_no_target_values():
    manifest = json.loads((PROT / "pdb_external_aod_contact_projection_manifest.json").read_text(encoding="utf-8"))
    boundary_manifest = json.loads((PROT / "pdb_external_evaluation_pair_manifest.json").read_text(encoding="utf-8"))
    assert manifest["evaluation_boundary_sha256"] == boundary_manifest["boundary_sha256"]
    assert manifest["aod_packet_sha256"] == sha(PROT / "aod_contact_prediction_freeze.csv")
    assert manifest["aod_reclosure_sha256"] == sha(PROT / "aod_reclosure_motif_predictions.csv")
    rows = read_csv("pdb_external_aod_contact_projection.csv")
    assert len(rows) == 946
    assert {row["prediction_state"] for row in rows} == {"out_of_scope"}
    assert {row["O_hat"] for row in rows} == {""}
    assert {row["target_value_read_status"] for row in rows} == {"not_read_by_projection_gate"}
    assert "target_contact_value" not in rows[0]
    assert {row["residual_status"] for row in rows} == {"not_computed_in_v40.02r17"}
    assert {row["score_status"] for row in rows} == {"projection_gate_only_no_residual_score"}


def test_r17_projection_summary_and_policy_are_scope_tight():
    summary = read_csv("pdb_external_aod_contact_projection_summary.csv")[0]
    assert summary["evaluation_pair_count"] == "946"
    assert summary["projection_contact_count"] == "0"
    assert summary["projection_noncontact_count"] == "0"
    assert summary["projection_abstain_count"] == "0"
    assert summary["projection_out_of_scope_count"] == "946"
    assert summary["target_value_read_status"] == "not_read_by_projection_gate"
    policy = read_csv("pdb_external_aod_contact_projection_policy_application.csv")[0]
    assert policy["projection_state_domain"] == "contact|noncontact|abstain|out_of_scope"
    assert policy["alignment_status"] == "no_declared_external_1CRN_to_GAS_alignment_in_v40.02r17"
    assert policy["target_value_policy"] == "target contact values are not read by this projection gate"
    assert policy["residual_score_policy"] == "not computed until a later gate joins frozen O_hat with frozen O"


def test_r17_leakage_checks_enforce_freeze_before_future_target_join():
    checks = read_csv("pdb_external_aod_contact_projection_leakage_checks.csv")
    names = {row["check_name"] for row in checks}
    required = {
        "evaluation_boundary_hash_matches_r16_manifest",
        "evaluation_pair_list_hash_frozen_before_projection",
        "frozen_AOD_packet_hash_recorded",
        "frozen_reclosure_packet_hash_recorded",
        "SADAR_context_recorded_before_projection",
        "projection_states_explicit",
        "no_declared_external_alignment_all_pairs_out_of_scope",
        "target_contact_values_not_read_in_r17",
        "no_external_residual_score_computed_in_r17",
        "coordinate_metrics_remain_deferred",
        "AOD_motif_curling_curls_and_SADAR_precede_downstream_target_join",
    }
    assert required <= names
    assert {row["check_result"] for row in checks} == {"active_pass"}
    assert {row["projection_input_status"] for row in checks} == {"projection_gate_only_boundary_plus_frozen_AOD_packet_no_target_values_no_score"}


def test_r17_generator_is_offline_reproducible_and_does_not_read_target_values_or_score():
    before = (PROT / "pdb_external_aod_contact_projection.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "project_external_pdb_aod_contact_prediction_packet.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "row[\"target_contact_value\"]" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_aod_contact_projection.csv").read_text(encoding="utf-8")
    assert after == before


def test_r17_manual_section_and_roadmap_are_projection_only():
    section = (ROOT / "manual-2" / "sections" / "16_external_pdb_aod_contact_projection_gate.tex").read_text(encoding="utf-8")
    assert "AOD contact-prediction projection gate" in section
    assert "N_{\\mathrm{eval}}=946" in section
    assert "out\\_of\\_scope" in section
    assert "does not read target contact values" in section
    assert "does not compare" in section
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "AOD Contact-Prediction Packet Projection Gate" in roadmap
    assert "v40.02r20 -- External PDB Alignment Rule Freeze / No-Alignment Carry-Forward Gate" in roadmap
