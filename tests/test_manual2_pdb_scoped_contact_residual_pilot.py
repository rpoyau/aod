import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_v4002r09_files_exist_and_are_manifested():
    required = [
        "pdb_scoped_contact_residual_pilot.csv",
        "pdb_scoped_contact_score.csv",
        "pdb_scoped_contact_delta3.csv",
        "pdb_scoped_contact_leakage_audit.csv",
        "pdb_scoped_contact_score_summary.csv",
        "pdb_scoped_contact_residual_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_scoped_contact_residual_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r09.1"
    assert manifest["scope_input_version"] == "v40.02r08"
    assert "RMSD" in manifest["metric_policy"]
    assert manifest["lambda_fold_status"] == "deferred_not_attached"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_scoped_pilot_scores_only_declared_pair_after_scope_lock():
    scope = read_csv(PROT / "pdb_contact_comparison_scope_declaration.csv")[0]
    pilot = read_csv(PROT / "pdb_scoped_contact_residual_pilot.csv")
    assert len(pilot) == 1
    row = pilot[0]
    assert row["scope_id"] == scope["scope_id"]
    assert row["prediction_freeze_version"] == "v40.02r05"
    assert row["target_derivation_version"] == "v40.02r07"
    assert row["scope_version"] == "v40.02r08"
    assert row["score_version"] == "v40.02r09.1"
    assert (row["residue_i"], row["residue_j"]) == ("1", "3")
    assert row["predicted_contact"] == "1"
    assert row["target_contact"] == "1"
    assert row["ca_distance_angstrom"] == "7.6"
    assert row["Delta_Z"] == "0"
    assert row["delta3_contact"] == "0"
    assert row["contact_error_class"] == "TP"
    assert row["leakage_status"] == "passed_scope_and_input_lock_checks"
    assert row["value_map_status"] == "quarantined_pdb_contact_residual_not_released_lambda_fold"


def test_scoped_score_records_one_pair_confusion_metrics():
    rows = read_csv(PROT / "pdb_scoped_contact_score.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["score_version"] == "v40.02r09.1"
    assert row["structure_source"] == "manual_fixture_pdbx_mmcif"
    assert row["predicted_pairs"] == row["target_pairs"] == row["evaluation_pairs"] == "1-3"
    assert (row["tp"], row["fp"], row["fn"], row["tn"]) == ("1", "0", "0", "0")
    assert row["precision"] == row["recall"] == row["f1"] == row["jaccard"] == "1"
    assert row["mcc"] == "undefined_no_true_negative_denominator"
    assert row["coordinate_metric_status"] == "contact_map_only_no_coordinate_level_aod_prediction"


def test_scoped_delta3_and_summary_are_zero_residual_and_deferred_lambda():
    delta = read_csv(PROT / "pdb_scoped_contact_delta3.csv")
    assert len(delta) == 1
    assert delta[0]["Delta_Z"] == "0"
    assert delta[0]["delta3_contact"] == "0"
    assert delta[0]["contact_error_class"] == "TP"
    summary = read_csv(PROT / "pdb_scoped_contact_score_summary.csv")
    assert len(summary) == 1
    assert summary[0]["score_version"] == "v40.02r09.1"
    assert summary[0]["lambda_fold_status"] == "deferred_not_attached"
    assert "not_folding_model" in summary[0]["claim_status"]


def test_scope_and_leakage_rows_are_read_before_scoring_and_audited():
    audit = read_csv(PROT / "pdb_scoped_contact_leakage_audit.csv")
    assert len(audit) >= 4
    assert {r["pilot_check_status"] for r in audit} == {"active_pass"}
    assert {r["score_input_status"] for r in audit} == {"scope_rows_read_before_prediction_and_target_rows"}
    assert any("alphafold" in r["forbidden_source"] for r in audit)
    script = (ROOT / "manual-2" / "scripts" / "score_scoped_pdb_contact_residual_pilot.py").read_text(encoding="utf-8")
    assert 'pdb_contact_comparison_scope_declaration.csv' in script
    assert 'pdb_contact_comparison_leakage_checks.csv' in script
    assert script.index('pdb_contact_comparison_scope_declaration.csv') < script.index('aod_contact_prediction_freeze.csv')


def test_scoped_pilot_generator_is_offline_and_reproducible():
    before = (PROT / "pdb_scoped_contact_score.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "score_scoped_pdb_contact_residual_pilot.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_scoped_contact_score.csv").read_text(encoding="utf-8")
    assert after == before


def test_roadmap_current_milestone_is_v4002r09_and_lambdas_deferred():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "Multi-pair Scoped Contact Residual Pilot" in roadmap
    assert "lambda_fold     = deferred_not_attached" in roadmap
