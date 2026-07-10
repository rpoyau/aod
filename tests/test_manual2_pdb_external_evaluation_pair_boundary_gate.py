import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"
EXPECTED_PAYLOAD_SHA = "23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba"
EXPECTED_RESIDUE_TABLE_SHA = "9aadae50bce02e7de3bfaa9432a5708351f9e3513bb1925f33f9484274000dab"
EXPECTED_CONTACT_MAP_SHA = "1f72dc9eb44350709fae92739780756346d11be34b700e08f41361aef580b810"
EXPECTED_DISTANCE_MATRIX_SHA = "aea7a6164ba2092161a18f3b83c3ce4557a78b19cdb4f7dad28bafe7c6978d15"


def read_csv(name: str):
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r16_evaluation_pair_boundary_files_exist_and_are_manifested():
    required = [
        "pdb_external_evaluation_pair_boundary.csv",
        "pdb_external_evaluation_pair_scope_summary.csv",
        "pdb_external_evaluation_pair_policy_application.csv",
        "pdb_external_evaluation_pair_leakage_checks.csv",
        "pdb_external_evaluation_pair_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_evaluation_pair_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r16"
    assert manifest["source_accession"] == "1CRN"
    assert manifest["coordinate_payload_sha256"] == EXPECTED_PAYLOAD_SHA
    assert manifest["residue_table_sha256"] == EXPECTED_RESIDUE_TABLE_SHA
    assert manifest["contact_map_sha256"] == EXPECTED_CONTACT_MAP_SHA
    assert manifest["distance_matrix_sha256"] == EXPECTED_DISTANCE_MATRIX_SHA
    assert manifest["evaluation_pair_selection_rule"] == "all_eligible_external_contact_map_pairs"
    assert manifest["evaluation_pair_count"] == 946
    assert manifest["target_contact_count"] == 114
    assert manifest["target_noncontact_count"] == 832
    assert manifest["score_status"] == "not_scored_in_v40.02r16"
    assert manifest["aod_prediction_join_status"] == "not_joined_in_v40.02r16"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r16_boundary_reads_only_r15_contact_map_and_preserves_counts():
    assert sha(PROT / "pdb_external_contact_map_derived.csv") == EXPECTED_CONTACT_MAP_SHA
    assert sha(PROT / "pdb_external_contact_distance_matrix.csv") == EXPECTED_DISTANCE_MATRIX_SHA
    rows = read_csv("pdb_external_evaluation_pair_boundary.csv")
    assert len(rows) == 946
    assert sum(row["target_contact_value"] == "1" for row in rows) == 114
    assert sum(row["target_contact_value"] == "0" for row in rows) == 832
    assert {row["coordinate_payload_sha256"] for row in rows} == {EXPECTED_PAYLOAD_SHA}
    assert {row["residue_table_sha256"] for row in rows} == {EXPECTED_RESIDUE_TABLE_SHA}
    assert {row["contact_map_sha256"] for row in rows} == {EXPECTED_CONTACT_MAP_SHA}
    assert {row["evaluation_pair_selection_rule"] for row in rows} == {"all_eligible_external_contact_map_pairs"}
    assert {row["score_status"] for row in rows} == {"not_scored_in_v40.02r16"}
    assert {row["aod_prediction_join_status"] for row in rows} == {"not_joined_in_v40.02r16"}
    assert {row["leakage_role"] for row in rows} == {"target_evaluation_boundary_only_after_contact_map_derivation_before_score"}


def test_r16_scope_summary_and_policy_lock_precision_before_scoring():
    summary = read_csv("pdb_external_evaluation_pair_scope_summary.csv")[0]
    assert summary["evaluation_pair_count"] == "946"
    assert summary["target_contact_count"] == "114"
    assert summary["target_noncontact_count"] == "832"
    assert summary["score_status"] == "not_scored_in_v40.02r16"
    assert summary["aod_prediction_join_status"] == "not_joined_in_v40.02r16"
    policy = read_csv("pdb_external_evaluation_pair_policy_application.csv")[0]
    assert policy["contact_threshold_angstrom"] == "8.0"
    assert policy["min_sequence_separation"] == "3"
    assert policy["sequence_separation_rule"] == "abs(label_seq_id_j-label_seq_id_i)>=3"
    assert policy["sequence_separation_rule_status"] == "carried_forward_from_contact_map_derivation_before_pair_selection"
    assert policy["evaluation_pair_boundary_status"] == "declared_before_external_residual_score"
    assert policy["distance_computation_precision"] == "full_precision_from_residue_table_coordinates"
    assert policy["distance_display_precision"] == "0.001_angstrom"
    assert policy["target_contact_value_rule"] == "full_precision_distance <= 8.0"
    assert policy["contact_value_precision_policy"] == "target_contact_value computed from full-precision distance before display rounding"
    assert policy["external_residual_score_status"] == "not_scored_in_v40.02r16"


def test_r16_leakage_checks_freeze_boundary_before_score():
    checks = read_csv("pdb_external_evaluation_pair_leakage_checks.csv")
    names = {row["check_name"] for row in checks}
    required = {
        "contact_map_derived_before_evaluation_pair_boundary",
        "contact_map_sha256_matches_r15_manifest",
        "residue_table_sha256_matches_contact_map_manifest",
        "sequence_separation_rule_declared_before_pair_selection",
        "evaluation_pair_selection_rule_declared_before_score",
        "evaluation_pair_count_matches_contact_map_row_count",
        "target_contact_count_matches_contact_map",
        "target_noncontact_count_matches_contact_map",
        "distance_precision_policy_recorded",
        "no_AOD_prediction_packet_joined_in_r16",
        "no_external_residual_score_computed_in_r16",
        "coordinate_metrics_remain_deferred",
        "AOD_motif_curling_curls_and_SADAR_stay_upstream_of_future_target_join",
    }
    assert required <= names
    assert {row["check_result"] for row in checks} == {"active_pass"}
    assert {row["score_input_status"] for row in checks} == {"evaluation_boundary_gate_only_no_AOD_join_or_score"}


def test_r16_generator_is_offline_reproducible_and_does_not_score_or_join_aod():
    before = (PROT / "pdb_external_evaluation_pair_boundary.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "declare_external_pdb_evaluation_pair_boundary.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "aod_contact_prediction_freeze" not in text
    assert "score_scoped" not in text
    assert "score_multipair" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_evaluation_pair_boundary.csv").read_text(encoding="utf-8")
    assert after == before


def test_r16_manual_section_and_roadmap_are_scope_tight():
    section = (ROOT / "manual-2" / "sections" / "15_external_pdb_evaluation_pair_boundary_gate.tex").read_text(encoding="utf-8")
    assert "evaluation-pair boundary gate" in section
    assert "N_{\\mathrm{eval}}=946" in section
    assert "N_{\\mathrm{contact}}=114" in section
    assert "N_{\\mathrm{noncontact}}=832" in section
    assert "AOD prediction packet" in section
    assert "does not compute an external residual score" in section
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "External PDB Evaluation-Pair Boundary Gate" in roadmap
    assert "v40.02r20 -- External PDB Alignment Rule Freeze / No-Alignment Carry-Forward Gate" in roadmap
