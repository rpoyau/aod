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


def read_csv(name: str):
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_r15_contact_map_files_exist_and_are_manifested():
    required = [
        "pdb_external_contact_distance_matrix.csv",
        "pdb_external_contact_map_derived.csv",
        "pdb_external_contact_map_policy_application.csv",
        "pdb_external_contact_map_derivation_block.csv",
        "pdb_external_contact_map_leakage_checks.csv",
        "pdb_external_contact_map_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_contact_map_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r15"
    assert manifest["source_accession"] == "1CRN"
    assert manifest["chain_id"] == "A"
    assert manifest["model_id"] == "1"
    assert manifest["atom_selector"] == "CA"
    assert manifest["coordinate_payload_sha256"] == EXPECTED_PAYLOAD_SHA
    assert manifest["residue_table_sha256"] == EXPECTED_RESIDUE_TABLE_SHA
    assert manifest["residue_coordinate_rows"] == 46
    assert manifest["total_unordered_pair_count"] == 1035
    assert manifest["eligible_pair_count"] == 946
    assert manifest["excluded_short_range_pair_count"] == 89
    assert manifest["target_contact_count"] == 114
    assert manifest["target_noncontact_count"] == 832
    assert manifest["sequence_separation_rule"] == "abs(label_seq_id_j-label_seq_id_i)>=3"
    assert manifest["score_status"] == "not_scored_in_v40.02r15"
    assert manifest["aod_prediction_join_status"] == "not_joined_in_v40.02r15"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r15_contact_map_reads_only_r14_residue_table_and_freezes_rule():
    assert hashlib.sha256((PROT / "pdb_external_residue_coordinate_table.csv").read_bytes()).hexdigest() == EXPECTED_RESIDUE_TABLE_SHA
    policy = read_csv("pdb_external_contact_map_policy_application.csv")[0]
    assert policy["residue_table_sha256"] == EXPECTED_RESIDUE_TABLE_SHA
    assert policy["sequence_separation_rule"] == "abs(label_seq_id_j-label_seq_id_i)>=3"
    assert policy["sequence_separation_rule_status"] == "declared_before_pair_generation"
    assert policy["contact_threshold_angstrom"] == "8.0"
    assert policy["min_sequence_separation"] == "3"
    assert policy["eligible_pair_count"] == "946"
    assert policy["target_contact_count"] == "114"
    assert policy["target_noncontact_count"] == "832"
    assert policy["external_residual_score_status"] == "not_scored_in_v40.02r15"


def test_r15_distance_and_contact_rows_have_expected_counts_and_statuses():
    distances = read_csv("pdb_external_contact_distance_matrix.csv")
    contacts = read_csv("pdb_external_contact_map_derived.csv")
    assert len(distances) == 1035
    assert len(contacts) == 946
    assert sum(row["eligible_for_contact_map"] == "true" for row in distances) == 946
    assert sum(row["eligible_for_contact_map"] == "false" for row in distances) == 89
    assert sum(row["target_contact_value"] == "1" for row in contacts) == 114
    assert sum(row["target_contact_value"] == "0" for row in contacts) == 832
    assert {row["leakage_role"] for row in contacts} == {"target_only_after_AOD_freeze"}
    assert {row["score_status"] for row in contacts} == {"not_scored_in_v40.02r15"}
    assert {row["coordinate_payload_sha256"] for row in contacts} == {EXPECTED_PAYLOAD_SHA}
    assert {row["residue_table_sha256"] for row in contacts} == {EXPECTED_RESIDUE_TABLE_SHA}
    assert min(int(row["sequence_separation"]) for row in contacts) == 3


def test_r15_expected_known_contact_and_noncontact_rows():
    rows = {row["contact_row_id"]: row for row in read_csv("pdb_external_contact_map_derived.csv")}
    assert rows["1CRN_A_model1_CA_label1_label4_contact"]["target_contact_value"] == "0"
    assert rows["1CRN_A_model1_CA_label1_label4_contact"]["distance_angstrom"] == "10.214"
    # A compact local contact in 1CRN under the declared threshold.
    assert rows["1CRN_A_model1_CA_label1_label34_contact"]["target_contact_value"] == "1"
    assert float(rows["1CRN_A_model1_CA_label1_label34_contact"]["distance_angstrom"]) <= 8.0


def test_r15_blocks_score_and_coordinate_metrics_after_contact_map():
    blocks = read_csv("pdb_external_contact_map_derivation_block.csv")
    assert {row["candidate_derivation"] for row in blocks} == {
        "evaluation_pair_boundary",
        "external_residual_score",
        "coordinate_level_metric_score",
    }
    assert any(row["current_status"] == "blocked_until_explicit_evaluation_pair_boundary_gate" for row in blocks)
    assert all("score" not in row["candidate_derivation"] or row["current_status"] == "blocked_in_v40.02r15" for row in blocks)
    checks = read_csv("pdb_external_contact_map_leakage_checks.csv")
    names = {row["check_name"] for row in checks}
    required = {
        "contact_map_reads_only_r14_residue_table",
        "residue_table_sha256_matches_r14_manifest",
        "sequence_separation_rule_declared_before_pair_generation",
        "contact_threshold_8_angstrom_declared_before_contact_bits",
        "eligible_pair_count_matches_declared_rule",
        "target_contact_count_matches_declared_rule",
        "no_external_residual_score_computed_in_r15",
        "no_AOD_prediction_packet_joined_in_r15",
        "coordinate_metrics_remain_deferred",
        "AOD_motif_curling_curls_and_SADAR_stay_upstream_of_future_target_join",
    }
    assert required <= names
    assert {row["check_result"] for row in checks} == {"active_pass"}
    assert {row["score_input_status"] for row in checks} == {"contact_map_gate_only_no_AOD_join_or_score"}


def test_r15_generator_is_offline_reproducible_and_does_not_score():
    before = (PROT / "pdb_external_contact_map_derived.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "derive_external_pdb_contact_map.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "score_scoped" not in text
    assert "score_multipair" not in text
    assert "aod_contact_prediction_freeze" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_contact_map_derived.csv").read_text(encoding="utf-8")
    assert after == before


def test_r15_manual_section_and_roadmap_are_scope_tight():
    section = (ROOT / "manual-2" / "sections" / "14_external_pdb_contact_map_derivation.tex").read_text(encoding="utf-8")
    assert "contact-map derivation gate" in section
    assert "946 eligible rows" in section
    assert "N_{\\mathrm{contact}}=114" in section
    assert "AOD prediction join" in section
    assert "residual score" in section
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "External PDB Contact Map Derivation Gate" in roadmap
    assert "v40.02r17 -- AOD Contact-Prediction Packet Projection Gate" in roadmap
