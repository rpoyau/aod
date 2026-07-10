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


def test_r19_alignment_rule_candidate_files_exist_and_are_manifested():
    required = [
        "pdb_external_alignment_rule_candidate_gate.csv",
        "pdb_external_alignment_rule_candidate_pair_scope.csv",
        "pdb_external_alignment_rule_candidate_policy_application.csv",
        "pdb_external_alignment_rule_candidate_leakage_checks.csv",
        "pdb_external_alignment_rule_candidate_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_alignment_rule_candidate_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r19"
    assert manifest["source_accession"] == "1CRN"
    assert manifest["alignment_rule_type"] == "no_alignment_carry_forward"
    assert manifest["alignment_status"] == "no_alignment_declared_carry_forward"
    assert manifest["mapping_source"] == "none_declared"
    assert manifest["mapping_scope"] == "none_declared"
    assert manifest["evaluation_pair_count"] == 946
    assert manifest["in_scope_pair_count"] == 0
    assert manifest["out_of_scope_pair_count"] == 946
    assert manifest["projection_coverage_exact"] == "0/946"
    assert manifest["target_value_read_status"] == "not_read_by_alignment_rule_candidate_gate"
    assert manifest["residual_status"] == "not_computed_in_v40.02r19"
    assert manifest["score_status"] == "alignment_rule_candidate_gate_only_no_residual_score"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r19_reads_r18_coverage_and_carries_no_alignment_forward_without_target_values():
    manifest = json.loads((PROT / "pdb_external_alignment_rule_candidate_manifest.json").read_text(encoding="utf-8"))
    r18_manifest = json.loads((PROT / "pdb_external_projection_alignment_manifest.json").read_text(encoding="utf-8"))
    assert manifest["r18_alignment_coverage_sha256"] == r18_manifest["coverage_sha256"]
    rows = read_csv("pdb_external_alignment_rule_candidate_pair_scope.csv")
    assert len(rows) == 946
    assert "target_contact_value" not in rows[0]
    assert {row["target_value_read_status"] for row in rows} == {"not_read_by_alignment_rule_candidate_gate"}
    assert {row["alignment_rule_type"] for row in rows} == {"no_alignment_carry_forward"}
    assert {row["alignment_status"] for row in rows} == {"no_alignment_declared_carry_forward"}
    assert {row["mapping_source"] for row in rows} == {"none_declared"}
    assert {row["mapping_scope"] for row in rows} == {"none_declared"}
    assert {row["in_scope_flag"] for row in rows} == {"0"}
    assert {row["out_of_scope_flag"] for row in rows} == {"1"}
    assert {row["prediction_state_if_projected"] for row in rows} == {"out_of_scope"}
    assert {row["O_hat"] for row in rows} == {""}
    assert {row["residual_status"] for row in rows} == {"not_computed_in_v40.02r19"}
    assert {row["score_status"] for row in rows} == {"alignment_rule_candidate_gate_only_no_residual_score"}


def test_r19_gate_summary_records_candidate_rule_and_zero_coverage():
    gate = read_csv("pdb_external_alignment_rule_candidate_gate.csv")[0]
    assert gate["alignment_rule_id"] == "pdb_external_alignment_rule_candidate_1CRN_A_no_alignment_carry_forward_v4002r19"
    assert gate["alignment_rule_type"] == "no_alignment_carry_forward"
    assert gate["evaluation_boundary_id"] == "pdb_external_eval_boundary_1CRN_A_all946_v4002r16"
    assert gate["projection_rule"] == "none_no_projection_rule_declared"
    assert gate["projection_coverage_exact"] == "0/946"
    assert gate["in_scope_pair_count"] == "0"
    assert gate["out_of_scope_pair_count"] == "946"
    assert gate["abstention_policy"].startswith("abstain_only_after_declared_alignment")


def test_r19_leakage_checks_enforce_candidate_before_target_join_or_score():
    checks = read_csv("pdb_external_alignment_rule_candidate_leakage_checks.csv")
    names = {row["check_name"] for row in checks}
    required = {
        "r18_alignment_coverage_hash_verified_before_r19",
        "alignment_rule_type_declared_before_any_projection_or_target_join",
        "evaluation_boundary_hash_carried_forward",
        "aod_packet_and_sadar_context_hashes_carried_forward",
        "all_pairs_remain_out_of_scope_without_alignment_rule",
        "abstain_reserved_for_declared_alignment",
        "target_values_not_read_in_r19",
        "no_residual_score_computed_in_r19",
        "coordinate_metrics_remain_deferred",
        "AOD_motif_curling_curls_and_SADAR_precede_downstream_target_join",
    }
    assert required <= names
    assert {row["check_result"] for row in checks} == {"active_pass"}
    assert {row["alignment_rule_gate_status"] for row in checks} == {"candidate_gate_only_no_target_read_no_score"}


def test_r19_generator_is_offline_reproducible_and_does_not_read_target_values_or_score():
    before = (PROT / "pdb_external_alignment_rule_candidate_pair_scope.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "declare_external_pdb_alignment_rule_candidate_gate.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "target_contact_value" not in before
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_alignment_rule_candidate_pair_scope.csv").read_text(encoding="utf-8")
    assert after == before


def test_r19_manual_section_and_roadmap_are_candidate_gate_only():
    section = (ROOT / "manual-2" / "sections" / "18_external_pdb_alignment_rule_candidate_gate.tex").read_text(encoding="utf-8")
    assert "External PDB alignment-rule candidate" in section
    assert r"no\_alignment\_carry\_forward" in section
    assert "N_{\\mathrm{in\\ scope}}=0" in section
    assert "0/946=0.0" in section
    assert "does not read target contact values" in section
    assert "does not compute residual rows" in section
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "External PDB Alignment Rule Candidate Gate" in roadmap
    assert "v40.02r20" in roadmap
