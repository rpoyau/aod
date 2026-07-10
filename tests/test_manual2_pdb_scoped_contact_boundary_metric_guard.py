import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_r091_metric_scope_and_classifier_generalization_guard():
    summary = read_csv(PROT / "pdb_scoped_contact_score_summary.csv")[0]
    assert summary["score_version"] == "v40.02r09.1"
    assert summary["score_origin_version"] == "v40.02r09"
    assert summary["metric_scope"] == "single_positive_contact_row"
    assert summary["metric_validity"] == "residual_row_smoke_test"
    assert summary["classifier_generalization"] == "not_scoped_in_this_pilot"
    assert summary["mcc_status"] == "undefined_no_true_negative_denominator"


def test_r091_target_source_and_contact_definition_are_explicit():
    pilot = read_csv(PROT / "pdb_scoped_contact_residual_pilot.csv")[0]
    assert pilot["target_source_type"] == "manual_pdbx_mmcif_fixture"
    assert pilot["target_source_id"] == "manual_seed_GAS_pdbx_mmcif_payload_fixture"
    assert pilot["target_derivation_rule"] == "CA_distance_leq_8.0A_min_sequence_separation_2"
    assert pilot["target_freeze_id"] == "manual_seed_GAS_pdbx_mmcif_payload_fixture_contact_002"
    assert pilot["target_coordinate_status"] == "fixture_coordinate_payload_derived_not_external_pdb_accession"
    assert pilot["contact_definition"] == "CA_distance_leq_8.0A_min_sequence_separation_2"
    assert pilot["pair_index_basis"] == "one_based_residue_sequence_position"
    assert pilot["atom_selector"] == "CA"
    assert pilot["distance_cutoff_A"] == "8.0"


def test_r091_detection_is_aod_motif_sadar_before_downstream_target_map():
    pilot = read_csv(PROT / "pdb_scoped_contact_residual_pilot.csv")[0]
    assert pilot["trace_id"] == "trace_mol_005"
    assert pilot["aod_motif_id"] == "motif_mol_005"
    assert pilot["sadar_context_id"] == "sadar_mol_005"
    assert pilot["detection_basis"] == "AOD_motif_curling_curls_spec_plus_SADAR_context"
    assert pilot["downstream_map_stage"] == "target_join_after_prediction_freeze"
    freeze = read_csv(PROT / "aod_contact_prediction_freeze.csv")
    freeze_row = [r for r in freeze if r["prediction_id"] == pilot["prediction_id"]][0]
    assert freeze_row["comparison_input_used"] == "false"
    assert freeze_row["freeze_status"] == "frozen_before_external_comparison"


def test_r091_leakage_audit_has_freeze_before_target_join_checks():
    audit = read_csv(PROT / "pdb_scoped_contact_leakage_audit.csv")
    names = {r["check_name"] for r in audit}
    required = {
        "frozen_aod_packet_read_before_target_contact_row",
        "target_columns_absent_from_frozen_prediction_packet",
        "score_script_joins_target_after_prediction_freeze",
        "residual_computed_after_prediction_and_target_rows_frozen",
        "target_source_type_recorded",
        "coordinate_level_score_fields_remain_deferred",
    }
    assert required <= names
    assert {r["check_result"] for r in audit} == {"active_pass"}
    assert {r["pilot_check_status"] for r in audit} == {"active_pass"}


def test_r091_manifest_records_valid_dec_boundary_metric_scope():
    manifest = json.loads((PROT / "pdb_scoped_contact_residual_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r09.1"
    assert manifest["score_origin_version"] == "v40.02r09"
    assert "curling-curls" in manifest["detection_policy"]
    assert manifest["metric_scope"] == "single_positive_contact_row"
    assert manifest["metric_validity"] == "residual_row_smoke_test"
    assert manifest["classifier_generalization"] == "not_scoped_in_this_pilot"
    assert manifest["target_source_policy"]["target_source_type"] == "manual_pdbx_mmcif_fixture"
    assert manifest["target_source_policy"]["pair_index_basis"] == "one_based_residue_sequence_position"


def test_r091_manual_section_uses_affirmative_score_scope_language():
    section = (ROOT / "manual-2" / "sections" / "08_scoped_pdb_contact_residual_pilot.tex").read_text(encoding="utf-8")
    assert "Detection status" in section
    assert "curling-curls specification" in section
    assert "target\\_source\\_type" in section
    assert "Score status" in section
    assert "metric\\_scope" in section
    assert "Current score scope" in section
    assert "No folding claim" not in section
