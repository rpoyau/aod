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


def test_r10_multipair_files_exist_and_are_manifested():
    required = [
        "pdb_multipair_contact_scope_declaration.csv",
        "pdb_multipair_contact_residual_pilot.csv",
        "pdb_multipair_contact_delta3.csv",
        "pdb_multipair_contact_score.csv",
        "pdb_multipair_contact_leakage_audit.csv",
        "pdb_multipair_contact_score_summary.csv",
        "pdb_multipair_contact_residual_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_multipair_contact_residual_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r10"
    assert manifest["lambda_fold_status"] == "deferred_not_attached"
    assert "negative_support_policy" in manifest
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r10_negative_support_scope_is_declared_before_score():
    scope = read_csv(PROT / "pdb_multipair_contact_scope_declaration.csv")[0]
    assert scope["version_scope"] == "v40.02r10"
    assert scope["negative_support_declaration_status"] == "declared_before_score"
    assert scope["declared_evaluation_pairs"] == "1-2;1-3;2-3"
    assert scope["positive_evaluation_pairs"] == "1-3"
    assert scope["negative_support_pairs"] == "1-2;2-3"
    assert "projected_to_noncontact_negative_support" in scope["projection_policy"]
    assert scope["coordinate_metric_policy"] == "RMSD_TM_score_GDT_absent_until_coordinate_level_AOD_prediction_freeze"


def test_r10_pilot_has_two_negative_support_rows_and_one_positive_contact_row():
    rows = read_csv(PROT / "pdb_multipair_contact_residual_pilot.csv")
    assert len(rows) == 3
    by_pair = {(r["residue_i"], r["residue_j"]): r for r in rows}
    assert set(by_pair) == {("1", "2"), ("1", "3"), ("2", "3")}
    assert by_pair[("1", "3")]["contact_error_class"] == "TP"
    assert by_pair[("1", "3")]["score_projection_contact_value"] == "1"
    assert by_pair[("1", "3")]["target_contact_value"] == "1"
    for pair in [("1", "2"), ("2", "3")]:
        row = by_pair[pair]
        assert row["contact_error_class"] == "TN"
        assert row["raw_frozen_prediction_contact_value"] == "1"
        assert row["score_projection_contact_value"] == "0"
        assert row["target_contact_value"] == "0"
        assert row["metric_pair_class"] == "declared_negative_support_boundary_control"
        assert row["projection_status"] == "adjacent_route_support_projected_to_noncontact_negative_support"
    assert {r["Delta_Z"] for r in rows} == {"0"}
    assert {r["delta3_contact"] for r in rows} == {"0"}


def test_r10_detection_order_remains_aod_motif_sadar_then_downstream_target_join():
    rows = read_csv(PROT / "pdb_multipair_contact_residual_pilot.csv")
    for row in rows:
        assert row["trace_id"] == "trace_mol_005"
        assert row["aod_motif_id"] == "motif_mol_005"
        assert row["sadar_context_id"] == "sadar_mol_005"
        assert row["detection_basis"] == "AOD_motif_curling_curls_spec_plus_SADAR_context"
        assert row["downstream_map_stage"] == "target_join_after_prediction_freeze"
    freeze = read_csv(PROT / "aod_contact_prediction_freeze.csv")
    freeze_by_id = {r["prediction_id"]: r for r in freeze}
    for row in rows:
        freeze_row = freeze_by_id[row["prediction_id"]]
        assert freeze_row["comparison_input_used"] == "false"
        assert freeze_row["freeze_status"] == "frozen_before_external_comparison"


def test_r10_score_has_defined_mcc_with_declared_negative_support():
    score = read_csv(PROT / "pdb_multipair_contact_score.csv")[0]
    assert score["score_version"] == "v40.02r10"
    assert score["metric_scope"] == "three_pair_fixture_with_two_declared_negative_support_rows"
    assert score["metric_validity"] == "multi_pair_residual_denominator_check"
    assert score["classifier_generalization"] == "not_scoped_beyond_manual_GAS_fixture"
    assert score["evaluation_pairs"] == "1-2;1-3;2-3"
    assert score["negative_support_pairs"] == "1-2;2-3"
    assert (score["tp"], score["fp"], score["fn"], score["tn"]) == ("1", "0", "0", "2")
    assert score["precision"] == score["recall"] == score["f1"] == score["jaccard"] == score["mcc"] == "1"
    assert score["mcc_status"] == "defined_with_declared_negative_support_pairs"
    assert score["coordinate_metric_status"] == "contact_map_only_no_coordinate_level_aod_prediction"


def test_r10_delta3_summary_and_lambda_fold_are_deferred():
    delta = read_csv(PROT / "pdb_multipair_contact_delta3.csv")
    assert len(delta) == 3
    assert {r["Delta_Z"] for r in delta} == {"0"}
    assert {r["delta3_contact"] for r in delta} == {"0"}
    summary = read_csv(PROT / "pdb_multipair_contact_score_summary.csv")[0]
    assert summary["score_version"] == "v40.02r10"
    assert summary["tn"] == "2"
    assert summary["mcc_micro"] == "1"
    assert summary["lambda_fold_status"] == "deferred_not_attached"
    assert "not_folding_model" in summary["claim_status"]


def test_r10_leakage_audit_records_scope_freeze_target_order_and_deferred_coordinate_metrics():
    audit = read_csv(PROT / "pdb_multipair_contact_leakage_audit.csv")
    names = {r["check_name"] for r in audit}
    required = {
        "multipair_scope_declared_before_scoring",
        "frozen_aod_packet_read_before_target_contact_row",
        "target_columns_absent_from_frozen_prediction_packet",
        "score_script_joins_target_after_prediction_freeze",
        "residual_computed_after_prediction_and_target_rows_frozen",
        "negative_support_pairs_have_target_zero_and_projected_prediction_zero",
        "coordinate_level_score_fields_remain_deferred",
        "aod_detection_basis_keeps_motif_curling_curls_and_sadar_before_target_map",
    }
    assert required <= names
    assert {r["check_result"] for r in audit} == {"active_pass"}
    assert {r["score_input_status"] for r in audit} == {"scope_rows_read_before_prediction_and_target_rows"}


def test_r10_generator_is_offline_reproducible_and_reads_scope_before_freeze():
    before = (PROT / "pdb_multipair_contact_score.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "score_multipair_pdb_contact_residual_pilot.py"
    text = script.read_text(encoding="utf-8")
    assert text.index("pdb_contact_comparison_scope_declaration.csv") < text.index("aod_contact_prediction_freeze.csv")
    assert text.index("aod_contact_prediction_freeze.csv") < text.index("pdb_mmcif_contact_map_derived.csv")
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_multipair_contact_score.csv").read_text(encoding="utf-8")
    assert after == before


def test_r10_manual_section_uses_valid_dec_order_without_coordinate_claims():
    section = (ROOT / "manual-2" / "sections" / "09_multipair_scoped_contact_residual_pilot.tex").read_text(encoding="utf-8")
    assert "declared before scoring" in section
    assert "frozen contact packet" in section
    assert "target rows join only after this freeze" in section
    assert "TN=2" in section
    assert "MCC" in section
    assert "coordinate-level scores" in section
    assert "folding model" not in section.lower()
