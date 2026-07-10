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


def test_contact_map_residual_files_exist_and_are_manifested():
    required = [
        "protein_contact_score.csv",
        "protein_contact_delta3.csv",
        "protein_score_summary.csv",
        "protein_folding_residual_analysis.csv",
        "protein_contact_score_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "protein_contact_score_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r06"
    assert "contact_map_residual_comparison" in manifest["status"]
    assert "no_active_folding_value_map" in manifest["status"]
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel
    assert "aod_contact_prediction_freeze.csv" in " ".join(manifest["prediction_inputs"])
    assert "protein_contact_map_targets.csv" in " ".join(manifest["target_inputs"])


def test_contact_score_uses_frozen_predictions_and_manual_fixture_targets_only():
    rows = read_csv(PROT / "protein_contact_score.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["prediction_freeze_version"] == "v40.02r05"
    assert row["score_version"] == "v40.02r06"
    assert row["chain_id"] == "chain_GAS_tripeptide_seed"
    assert row["protein_id"] == "manual_seed_GAS"
    assert row["structure_source"] == "manual_fixture"
    assert row["score_scope"] == "declared_contact_subset_min_sequence_separation"
    assert row["min_sequence_separation"] == "2"
    assert row["predicted_pairs"] == "1-3"
    assert row["target_pairs"] == "1-3"
    assert row["evaluation_pairs"] == "1-3"
    assert (row["tp"], row["fp"], row["fn"], row["tn"]) == ("1", "0", "0", "0")
    assert row["precision"] == row["recall"] == row["f1"] == row["jaccard"] == "1"
    assert row["mcc"] == "undefined_no_true_negative_denominator"
    assert row["value_map_status"] == "quarantined_comparison_not_released_lambda_fold"
    assert row["coordinate_metric_status"] == "not_coordinate_level_prediction"


def test_contact_delta3_rows_are_pairwise_and_zero_for_scored_fixture():
    rows = read_csv(PROT / "protein_contact_delta3.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["protein_id"] == "manual_seed_GAS"
    assert row["residue_i"] == "1"
    assert row["residue_j"] == "3"
    assert row["predicted_contact"] == "1"
    assert row["target_contact"] == "1"
    assert row["Delta_Z"] == "0"
    assert row["delta3_contact"] == "0"
    assert row["contact_error_class"] == "TP"


def test_score_summary_records_quarantined_metrics_and_deferred_external_targets():
    rows = read_csv(PROT / "protein_score_summary.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["score_version"] == "v40.02r06"
    assert row["score_rows"] == "1"
    assert int(row["deferred_analysis_rows"]) >= 1
    assert row["precision_micro"] == row["recall_micro"] == row["f1_micro"] == row["jaccard_micro"] == "1"
    assert row["external_target_score_status"] == "deferred_locator_only_no_coordinate_payload"
    assert row["lambda_fold_status"] == "deferred_not_attached"
    assert row["claim_status"] == "contact_map_residual_fixture_not_released_folding_model"


def test_residual_analysis_keeps_unmatched_and_locator_rows_deferred():
    rows = read_csv(PROT / "protein_folding_residual_analysis.csv")
    statuses = {r["comparison_status"] for r in rows}
    assert "scored_against_frozen_prediction" in statuses
    assert "deferred_no_matching_contact_target_in_v40.02r06" in statuses
    assert "deferred_no_matching_frozen_prediction" in statuses
    assert "deferred_locator_only_no_coordinate_payload" in statuses
    scored = next(r for r in rows if r["comparison_status"] == "scored_against_frozen_prediction")
    assert scored["max_abs_Delta_Z"] == "0"
    assert scored["delta3_status"] == "zero_residual"
    assert scored["limitation_class"] == "manual_fixture_not_external_ground_truth"


def test_no_coordinate_level_or_active_folding_value_map_is_released():
    # Guardrail prose may name deferred coordinate metrics, but released score
    # CSV schemas must not expose coordinate-level metric columns.
    header_text = " ".join(
        " ".join(read_csv(PROT / name)[0].keys()).lower()
        for name in [
            "protein_contact_score.csv",
            "protein_contact_delta3.csv",
            "protein_score_summary.csv",
            "protein_folding_residual_analysis.csv",
        ]
    )
    forbidden_columns = ["rmsd", "tm_score", "tm-score", "gdt"]
    assert not any(tok in header_text for tok in forbidden_columns)
    manifest = json.loads((PROT / "protein_contact_score_manifest.json").read_text(encoding="utf-8"))
    assert "RMSD" in manifest["metric_policy"]
    assert "absent" in manifest["metric_policy"]
    lambdas = read_csv(PROT / "protein_value_map_quarantine.csv")
    assert {r["lambda_id"] for r in lambdas} >= {"lambda_fold", "lambda_bio"}
    assert all(r["status"] == "deferred_not_attached" for r in lambdas)
    assert all(r["active_value_map"] == "false" for r in lambdas)
    assert all("v40.02r11" in r["release_status"] for r in lambdas)


def test_contact_score_generator_is_offline_and_reproducible():
    before = (PROT / "protein_contact_score.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "score_protein_contact_map_residuals.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "protein_contact_score.csv").read_text(encoding="utf-8")
    assert after == before


def test_roadmap_current_milestone_is_v4002r08_and_no_score_is_active():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "Scoped PDB Contact-Map Residual Pilot" in roadmap
    assert "PDB/mmCIF Experimental Coordinate Payload Ingest and Contact-Map Derivation Gate" in roadmap
    assert "lambda_fold     = deferred_not_attached" in roadmap
