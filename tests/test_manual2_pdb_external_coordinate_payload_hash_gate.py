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


def test_r12_external_coordinate_payload_hash_gate_files_exist_and_are_manifested():
    required = [
        "pdb_external_coordinate_payload_hash_gate.csv",
        "pdb_external_coordinate_payload_provenance_lock.csv",
        "pdb_external_coordinate_payload_policy_lock.csv",
        "pdb_external_coordinate_payload_derivation_block.csv",
        "pdb_external_coordinate_payload_leakage_checks.csv",
        "pdb_external_coordinate_payload_hash_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_coordinate_payload_hash_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r12.1"
    assert manifest["source_database"] == "RCSB_PDB"
    assert manifest["source_accession"] == "1CRN"
    assert manifest["chain_id"] == "A"
    assert manifest["coordinate_payload_sha256_status"] == "byte_payload_hash_required_not_satisfied_in_this_gate"
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r12_payload_hash_gate_locks_uri_and_blocks_derivation_until_byte_hash():
    row = read_csv(PROT / "pdb_external_coordinate_payload_hash_gate.csv")[0]
    assert row["version_scope"] == "v40.02r12.1"
    assert row["prior_scope_id"] == "pdb_external_accession_scope_1CRN_A_v4002r11"
    assert row["coordinate_payload_path"] == "https://files.rcsb.org/download/1CRN.cif"
    assert row["coordinate_payload_path_status"] == "external_uri_declared_payload_bytes_not_committed"
    assert row["coordinate_payload_sha256"] == "required_after_external_payload_bytes_are_registered_before_contact_derivation"
    assert row["coordinate_payload_sha256_status"] == "byte_payload_hash_required_not_satisfied_in_this_gate"
    assert len(row["payload_registration_sha256"]) == 64
    assert row["coordinate_payload_hash_gate_status"] == "active_gate_blocks_contact_derivation_until_byte_hash_exists"
    assert row["coordinate_contact_derivation_status"] == "blocked_no_external_contact_map_derivation_in_this_gate"
    assert row["residue_table_derivation_status"] == "blocked_until_payload_byte_hash_lock"
    assert row["score_status"] == "hash_gate_only_no_score"


def test_r12_provenance_lock_references_existing_locator_hashes_without_claiming_coordinate_bytes():
    prov = read_csv(PROT / "pdb_external_coordinate_payload_provenance_lock.csv")[0]
    locator = read_csv(PROT / "pdb_structure_target_packets.csv")[0]
    target = read_csv(PROT / "pdb_mmcif_structure_targets.csv")[0]
    assert prov["source_accession"] == "1CRN"
    assert prov["coordinate_payload_path_status"] == "external_uri_declared_payload_bytes_not_committed"
    assert prov["raw_locator_sha256"] == locator["raw_sha256"]
    assert prov["normalized_locator_sha256"] == locator["normalized_sha256"]
    assert prov["structure_target_sha256"] == target["structure_sha256"]
    assert prov["payload_role"] == "external_coordinate_payload_hash_lock_requirement_not_prediction_premise"
    assert prov["target_source_role"] == "downstream_target_payload_only_after_AOD_freeze"


def test_r12_policy_lock_declares_model_residue_atom_altloc_missing_and_contact_boundary():
    row = read_csv(PROT / "pdb_external_coordinate_payload_policy_lock.csv")[0]
    assert row["model_id"] == "1"
    assert row["model_policy"] == "model_1_preferred_single_model_policy"
    assert row["residue_index_basis"] == "one_based_residue_sequence_position"
    assert row["atom_selector"] == "CA"
    assert row["altloc_policy"] == "primary_or_highest_occupancy_altloc_required_before_derivation"
    assert row["missing_residue_policy"] == "explicit_gap_rows_required_before_contact_derivation"
    assert row["contact_threshold_angstrom"] == "8.0"
    assert row["min_sequence_separation"] == "3"
    assert row["residue_table_policy"] == "derive_only_after_coordinate_payload_byte_hash_lock"
    assert row["contact_map_policy"] == "derive_only_after_payload_hash_lock_and_residue_table_derivation"
    assert row["forbidden_future_order"] == "contact_map_or_score_before_payload_byte_hash_lock"
    assert row["coordinate_metric_status"] == "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze"


def test_r12_derivation_block_prevents_residue_contact_and_score_rows():
    rows = read_csv(PROT / "pdb_external_coordinate_payload_derivation_block.csv")
    by_derivation = {r["candidate_derivation"]: r for r in rows}
    assert set(by_derivation) == {
        "external_residue_coordinate_table",
        "external_contact_map",
        "external_residual_score",
    }
    assert by_derivation["external_residue_coordinate_table"]["required_precondition"] == "coordinate_payload_byte_sha256_locked"
    assert by_derivation["external_contact_map"]["required_precondition"] == "coordinate_payload_byte_sha256_locked_and_residue_table_derived"
    assert by_derivation["external_residual_score"]["required_precondition"] == "evaluation_pair_boundary_declared_after_contact_map_derivation"
    assert {r["current_status"] for r in rows} == {"blocked_in_v40.02r12.1"}


def test_r12_leakage_audit_enforces_hash_before_derivation_and_freeze_before_target():
    audit = read_csv(PROT / "pdb_external_coordinate_payload_leakage_checks.csv")
    names = {r["check_name"] for r in audit}
    required = {
        "external_accession_scope_exists_before_payload_hash_gate",
        "coordinate_payload_path_declared_before_hash_lock",
        "coordinate_payload_byte_sha256_required_before_residue_table",
        "residue_table_derivation_blocked_until_payload_hash_lock",
        "evaluation_pairs_deferred_until_residue_table_exists",
        "negative_support_policy_deferred_but_required_before_classifier_metrics",
        "external_payload_forbidden_as_raw_dec_or_aod_freeze_premise",
        "aod_motif_curling_curls_and_sadar_precede_future_external_target_map",
        "coordinate_level_metrics_remain_deferred",
    }
    assert required <= names
    assert {r["check_result"] for r in audit} == {"active_pass"}
    assert {r["score_input_status"] for r in audit} == {"hash_gate_only_no_score"}


def test_r12_generator_is_offline_reproducible_and_does_not_read_score_rows():
    before = (PROT / "pdb_external_coordinate_payload_hash_gate.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "declare_external_pdb_coordinate_payload_hash_gate.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "pdb_multipair_contact_score.csv" not in text
    assert "pdb_scoped_contact_score.csv" not in text
    assert "score rows" not in text.lower()
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_coordinate_payload_hash_gate.csv").read_text(encoding="utf-8")
    assert after == before


def test_r12_manual_section_is_hash_gate_only_and_keeps_target_downstream():
    section = (ROOT / "manual-2" / "sections" / "11_external_pdb_coordinate_payload_hash_gate.tex").read_text(encoding="utf-8")
    assert "coordinate-payload hash gate" in section
    assert "payload byte-hash lock" in section
    assert "blocked_until_payload_byte_hash_lock" in section
    assert "AOD motif / curling-curls specification" in section
    assert "SADAR context" in section
    assert "The target payload still never enters the raw D.E.C. row" in section
    assert "no coordinate parsing" in section
    assert "no contact-map derivation" in section
    assert "no external-accession residual score" in section
    assert "RMSD" not in section
    assert "TM-score" not in section
    assert "GDT" not in section


def test_r12_roadmap_and_value_maps_keep_science_deferred():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "External PDB Residue Coordinate Table Derivation Gate" in roadmap
    assert "coordinate_payload_sha256 = 23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba" in roadmap
    q = read_csv(PROT / "protein_value_map_quarantine.csv")
    assert {row["status"] for row in q} == {"deferred_not_attached"}
    assert {row["active_value_map"] for row in q} == {"false"}
