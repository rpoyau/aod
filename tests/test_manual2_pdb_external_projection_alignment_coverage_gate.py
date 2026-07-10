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


def test_r18_alignment_coverage_files_exist_and_are_manifested():
    required = [
        "pdb_external_projection_alignment_gate.csv",
        "pdb_external_projection_alignment_coverage.csv",
        "pdb_external_projection_alignment_policy_application.csv",
        "pdb_external_projection_alignment_leakage_checks.csv",
        "pdb_external_projection_alignment_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_projection_alignment_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r18"
    assert manifest["source_accession"] == "1CRN"
    assert manifest["evaluation_pair_count"] == 946
    assert manifest["alignment_status"] == "no_alignment_declared"
    assert manifest["alignment_rule"] == "none_declared"
    assert manifest["in_scope_pair_count"] == 0
    assert manifest["out_of_scope_pair_count"] == 946
    assert manifest["projection_coverage_exact"] == "0/946"
    assert manifest["target_value_read_status"] == "not_read_by_alignment_gate"
    assert manifest["residual_status"] == "not_computed_in_v40.02r18"
    assert manifest["score_status"] == "alignment_coverage_gate_only_no_residual_score"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r18_alignment_reads_frozen_r17_projection_but_no_target_values():
    manifest = json.loads((PROT / "pdb_external_projection_alignment_manifest.json").read_text(encoding="utf-8"))
    r17_manifest = json.loads((PROT / "pdb_external_aod_contact_projection_manifest.json").read_text(encoding="utf-8"))
    assert manifest["evaluation_boundary_sha256"] == r17_manifest["evaluation_boundary_sha256"]
    assert manifest["evaluation_pair_list_sha256"] == r17_manifest["evaluation_pair_list_sha256"]
    assert manifest["aod_packet_sha256"] == r17_manifest["aod_packet_sha256"]
    assert manifest["aod_reclosure_sha256"] == r17_manifest["aod_reclosure_sha256"]
    rows = read_csv("pdb_external_projection_alignment_coverage.csv")
    assert len(rows) == 946
    assert "target_contact_value" not in rows[0]
    assert {row["target_value_read_status"] for row in rows} == {"not_read_by_alignment_gate"}
    assert {row["alignment_status"] for row in rows} == {"no_alignment_declared"}
    assert {row["alignment_rule"] for row in rows} == {"none_declared"}
    assert {row["in_scope_flag"] for row in rows} == {"0"}
    assert {row["out_of_scope_flag"] for row in rows} == {"1"}
    assert {row["prediction_state_if_projected"] for row in rows} == {"out_of_scope"}
    assert {row["O_hat"] for row in rows} == {""}
    assert {row["residual_status"] for row in rows} == {"not_computed_in_v40.02r18"}
    assert {row["score_status"] for row in rows} == {"alignment_coverage_gate_only_no_residual_score"}


def test_r18_gate_summary_records_zero_coverage_and_stable_boundary_id():
    gate = read_csv("pdb_external_projection_alignment_gate.csv")[0]
    assert gate["evaluation_boundary_id"] == "pdb_external_eval_boundary_1CRN_A_all946_v4002r16"
    assert gate["evaluation_boundary_file"] == "manual-2/data/protein/pdb_external_evaluation_pair_boundary.csv"
    assert gate["projection_coverage_num"] == "0"
    assert gate["projection_coverage_den"] == "946"
    assert gate["projection_coverage_exact"] == "0/946"
    assert gate["projection_coverage_display"] == "0.0"
    assert gate["coverage_status"] == "zero_coverage_no_declared_alignment"
    assert gate["abstention_policy"].startswith("abstain_only_after_declared_alignment")


def test_r18_leakage_checks_enforce_alignment_before_target_join_or_score():
    checks = read_csv("pdb_external_projection_alignment_leakage_checks.csv")
    names = {row["check_name"] for row in checks}
    required = {
        "r17_projection_hash_verified_before_alignment_gate",
        "evaluation_boundary_id_stable_and_file_separated",
        "alignment_status_declared_before_any_target_join",
        "coverage_fraction_declared",
        "all_pairs_out_of_scope_without_alignment",
        "abstain_requires_declared_alignment",
        "target_contact_values_not_read_in_r18",
        "no_residual_score_computed_in_r18",
        "frozen_AOD_packet_and_SADAR_context_recorded",
        "coordinate_metrics_remain_deferred",
        "AOD_motif_curling_curls_and_SADAR_precede_downstream_target_join",
    }
    assert required <= names
    assert {row["check_result"] for row in checks} == {"active_pass"}
    assert {row["alignment_gate_status"] for row in checks} == {"alignment_coverage_gate_only_no_target_read_no_score"}


def test_r18_generator_is_offline_reproducible_and_does_not_read_target_values_or_score():
    before = (PROT / "pdb_external_projection_alignment_coverage.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "declare_external_pdb_projection_alignment_coverage_gate.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "row[\"target_contact_value\"]" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_projection_alignment_coverage.csv").read_text(encoding="utf-8")
    assert after == before


def test_r18_manual_section_and_roadmap_are_alignment_gate_only():
    section = (ROOT / "manual-2" / "sections" / "17_external_pdb_projection_alignment_coverage_gate.tex").read_text(encoding="utf-8")
    assert "External PDB projection alignment" in section
    assert "N_{\\mathrm{eval}}=946" in section
    assert "N_{\\mathrm{in\\ scope}}=0" in section
    assert "0/946=0.0" in section
    assert "does not read target contact values" in section
    assert "not a residual score" in section
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "External PDB Projection Alignment / Coverage Declaration Gate" in roadmap
    assert "v40.02r20 -- External PDB Alignment Rule Freeze / No-Alignment Carry-Forward Gate" in roadmap
