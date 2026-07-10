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


def test_v4002r08_scope_files_exist_and_are_manifested():
    required = [
        "pdb_contact_comparison_scope_declaration.csv",
        "pdb_contact_comparison_target_provenance.csv",
        "pdb_contact_comparison_residual_coordinates.csv",
        "pdb_contact_comparison_leakage_checks.csv",
        "pdb_contact_comparison_scope_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_contact_comparison_scope_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r08"
    assert "declared_no_expanded_score" in manifest["status"]
    assert "no TP/FP/FN/TN" in manifest["score_policy"]
    assert "lambda_fold" in manifest["claim_discipline"]
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_scope_declaration_defines_allowed_and_excluded_rows_but_no_score():
    rows = read_csv(PROT / "pdb_contact_comparison_scope_declaration.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["version_scope"] == "v40.02r08"
    assert row["protein_id"] == "manual_seed_GAS"
    assert row["chain_id"] == "chain_GAS_tripeptide_seed"
    assert row["contact_threshold_angstrom"] == "8.0"
    assert row["min_sequence_separation"] == "2"
    assert row["score_status"] == "scope_declared_no_score_in_v40.02r08"
    assert "in_scope" in row["allowed_target_rows"]
    assert "below_min_sequence_separation" in row["excluded_target_rows"]
    assert "not_ground_truth" in row["alpha_fold_policy"]
    assert "RMSD" in row["coordinate_metric_policy"]
    forbidden_score_columns = {"tp", "fp", "fn", "tn", "precision", "recall", "f1", "jaccard", "mcc"}
    assert not forbidden_score_columns.intersection({k.lower() for k in row.keys()})


def test_target_provenance_points_to_derived_pdb_target_rows_only():
    rows = read_csv(PROT / "pdb_contact_comparison_target_provenance.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["source_class"] == "manual_fixture_pdbx_mmcif"
    assert row["leakage_role"] == "target_only_after_prediction_freeze"
    assert row["score_status"] == "not_scored_in_v40.02r08"
    assert (ROOT / row["payload_path"]).exists()
    assert (ROOT / row["derived_contact_source"]).exists()
    assert (ROOT / row["distance_matrix_source"]).exists()
    assert row["contact_map_hash"] == read_csv(PROT / "pdb_mmcif_coordinate_payload_registry.csv")[0]["contact_map_hash"]


def test_residual_coordinates_are_declared_not_computed():
    rows = read_csv(PROT / "pdb_contact_comparison_residual_coordinates.csv")
    names = {r["coordinate_name"] for r in rows}
    assert {"Delta_Z_ij", "delta3_contact_ij", "TP_FP_FN_TN", "precision_recall_F1_Jaccard_MCC", "RMSD_TM_score_GDT"} <= names
    assert all("computed" not in r["metric_status"].replace("not_computed", "") for r in rows)
    assert any(r["metric_status"] == "deferred_absent_no_coordinate_level_prediction" for r in rows)


def test_leakage_checks_block_target_rows_from_prediction_premises():
    rows = read_csv(PROT / "pdb_contact_comparison_leakage_checks.csv")
    assert len(rows) >= 4
    assert all(r["check_status"] == "active_pass" for r in rows)
    destinations = {r["forbidden_destination"] for r in rows}
    assert "aod_contact_reclosure_prediction_freeze_inputs" in destinations
    assert "prediction_model_registry_or_freeze_generator" in destinations
    assert any("alphafold" in r["forbidden_source"] for r in rows)


def test_existing_score_and_derivation_rows_are_carried_forward_unchanged():
    score = read_csv(PROT / "protein_contact_score.csv")
    assert len(score) == 1
    assert score[0]["score_version"] == "v40.02r06"
    assert score[0]["predicted_pairs"] == score[0]["target_pairs"] == "1-3"
    derived = read_csv(PROT / "pdb_mmcif_contact_map_derived.csv")
    assert {r["score_status"] for r in derived} == {"not_scored_in_v40.02r07"}
    assert not (PROT / "pdb_contact_score.csv").exists()
    assert not (PROT / "pdb_contact_delta3.csv").exists()


def test_scope_generator_is_offline_and_reproducible():
    before = (PROT / "pdb_contact_comparison_scope_declaration.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "declare_pdb_contact_comparison_scope.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_contact_comparison_scope_declaration.csv").read_text(encoding="utf-8")
    assert after == before


def test_roadmap_current_milestone_is_v4002r08_and_next_is_scoped_pdb_pilot():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "Scoped PDB Contact-Map Residual Pilot" in roadmap
    assert "v40.02r09 -- Scoped PDB Contact-Map Residual Pilot" in roadmap
    assert "v40.02r08 scope rows are carried forward" in roadmap
    assert "lambda_fold     = deferred_not_attached" in roadmap
