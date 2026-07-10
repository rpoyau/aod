
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


def test_r11_external_accession_scope_files_exist_and_are_manifested():
    required = [
        "pdb_external_accession_scope_declaration.csv",
        "pdb_external_accession_target_provenance.csv",
        "pdb_external_accession_boundary_lock.csv",
        "pdb_external_accession_leakage_checks.csv",
        "pdb_external_accession_scope_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_accession_scope_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r11"
    assert manifest["external_accession_scope"]["source_database"] == "RCSB_PDB"
    assert manifest["external_accession_scope"]["source_accession"] == "1CRN"
    assert manifest["external_accession_scope"]["chain_id"] == "A"
    assert manifest["external_accession_scope"]["coordinate_payload_status"] == "deferred_not_ingested_in_this_gate"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r11_external_accession_scope_declares_boundary_before_scoring():
    row = read_csv(PROT / "pdb_external_accession_scope_declaration.csv")[0]
    assert row["version_scope"] == "v40.02r11"
    assert row["source_accession"] == "1CRN"
    assert row["chain_id"] == "A"
    assert row["accession_declaration_status"] == "external_accession_declared_before_payload_ingest_or_scoring"
    assert row["coordinate_payload_status"] == "deferred_not_ingested_in_this_gate"
    assert row["coordinate_payload_hash_status"] == "required_before_any_external_accession_score"
    assert row["residue_index_basis"] == "one_based_residue_sequence_position_declared_before_score"
    assert row["atom_selector"] == "CA"
    assert row["contact_threshold_angstrom"] == "8.0"
    assert row["min_sequence_separation"] == "3"
    assert row["score_boundary_status"] == "declared_scope_only_no_score_rows"
    assert row["downstream_score_status"] == "not_scored_in_this_gate"
    assert row["prediction_premise_policy"] == "external_accession_payload_forbidden_as_raw_dec_or_aod_freeze_premise"


def test_r11_provenance_links_to_existing_locator_rows_without_coordinate_payload():
    prov = read_csv(PROT / "pdb_external_accession_target_provenance.csv")[0]
    assert prov["source_database"] == "RCSB_PDB"
    assert prov["source_accession"] == "1CRN"
    assert prov["target_packet_id"] == "pdb_1crn_A_locator"
    assert prov["existing_locator_row"].endswith("pdb_structure_target_packets.csv:pdb_1crn_A_locator")
    assert prov["structure_target_row"].endswith("pdb_mmcif_structure_targets.csv:pdb_1crn_A_mmcif_target")
    assert prov["coordinate_payload_status"] == "not_committed_external_locator_only"
    assert prov["coordinate_payload_sha256"] == "deferred_until_payload_ingest"
    assert prov["target_source_role"] == "target_locator_only_not_prediction_premise"
    assert prov["score_status"] == "no_external_accession_score_in_this_gate"


def test_r11_boundary_lock_requires_payload_hash_and_pair_scope_before_future_score():
    row = read_csv(PROT / "pdb_external_accession_boundary_lock.csv")[0]
    assert row["coordinate_payload_hash_requirement"] == "required_before_any_contact_derivation_or_score"
    assert row["evaluation_pair_declaration_requirement"] == "required_after_payload_derivation_and_before_residual_score"
    assert row["negative_support_requirement"] == "required_before_MCC_or_classifier_generalization_metrics"
    assert row["allowed_future_score_input_order"] == "scope_rows_then_frozen_AOD_packet_then_external_accession_target_rows_then_residual"
    assert row["forbidden_future_score_input_order"] == "external_coordinate_payload_before_AOD_prediction_freeze"
    assert row["score_status"] == "boundary_declared_no_score"
    assert row["coordinate_metric_status"] == "deferred_no_RMSD_TM_score_GDT"


def test_r11_leakage_audit_keeps_external_accession_downstream_of_aod_detection_freeze():
    audit = read_csv(PROT / "pdb_external_accession_leakage_checks.csv")
    names = {r["check_name"] for r in audit}
    required = {
        "external_accession_declared_before_payload_ingest",
        "coordinate_payload_hash_status_recorded_before_score",
        "chain_id_residue_basis_atom_selector_cutoff_declared_before_score",
        "external_accession_target_rows_forbidden_as_prediction_premises",
        "future_residual_order_freeze_first_target_join_second",
        "coordinate_level_metrics_remain_deferred",
        "aod_motif_curling_curls_and_sadar_precede_external_target_map",
    }
    assert required <= names
    assert {r["check_result"] for r in audit} == {"active_pass"}
    assert {r["score_input_status"] for r in audit} == {"scope_rows_only_no_score"}


def test_r11_generator_is_offline_reproducible_and_does_not_read_score_rows():
    before = (PROT / "pdb_external_accession_scope_declaration.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "declare_external_pdb_accession_scope.py"
    text = script.read_text(encoding="utf-8")
    assert "pdb_multipair_contact_score.csv" not in text
    assert "protein_contact_score.csv" not in text
    assert "aod_contact_prediction_freeze.csv" not in text
    assert "scope rows are declared first" in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_accession_scope_declaration.csv").read_text(encoding="utf-8")
    assert after == before


def test_r11_manual_section_is_scope_gate_only_and_keeps_target_downstream():
    section = (ROOT / "manual-2" / "sections" / "10_external_pdb_accession_scope_gate.tex").read_text(encoding="utf-8")
    assert "The next contact-map step is not another score" in section
    assert "accession}=\\texttt{1CRN}" in section
    assert "chain}=A" in section
    assert "coordinate\\_payload\\_status" in section
    assert "deferred\\_not\\_ingested" in section
    assert "scope row" in section
    assert "frozen AOD contact packet" in section
    assert "external target row" in section
    assert "AOD motif / curling-curls specification" in section
    assert "SADAR context" in section
    assert "never enters the raw D.E.C. row" in section
    assert "RMSD" not in section
    assert "TM-score" not in section
    assert "GDT" not in section


def test_r11_metadata_tracks_current_gate_without_changing_r10_score_files():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "v40.02r11 -- External PDB Accession Scope Gate" in roadmap
    assert "coordinate_payload_status = deferred_not_ingested_in_this_gate" in roadmap
    r10_score = read_csv(PROT / "pdb_multipair_contact_score.csv")[0]
    assert r10_score["score_version"] == "v40.02r10"
    assert r10_score["mcc"] == "1"
    q = read_csv(PROT / "protein_value_map_quarantine.csv")
    assert {row["status"] for row in q} == {"deferred_not_attached"}
    assert {row["active_value_map"] for row in q} == {"false"}
