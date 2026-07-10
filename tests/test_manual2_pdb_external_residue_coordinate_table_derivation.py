import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"
PAYLOAD = PROT / "external_pdb_payloads" / "1CRN.cif"
EXPECTED_SHA = "23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_r14_residue_coordinate_table_files_exist_and_are_manifested():
    required = [
        "pdb_external_atom_site_extract.csv",
        "pdb_external_residue_coordinate_table.csv",
        "pdb_external_missing_residue_audit.csv",
        "pdb_external_residue_coordinate_policy_application.csv",
        "pdb_external_residue_coordinate_derivation_block.csv",
        "pdb_external_residue_coordinate_leakage_checks.csv",
        "pdb_external_residue_coordinate_table_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "pdb_external_residue_coordinate_table_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r14"
    assert manifest["source_accession"] == "1CRN"
    assert manifest["chain_id"] == "A"
    assert manifest["model_id"] == "1"
    assert manifest["atom_selector"] == "CA"
    assert manifest["coordinate_payload_sha256"] == EXPECTED_SHA
    assert manifest["selected_residue_coordinate_rows"] == 46
    assert manifest["atom_site_extract_rows"] == 46
    assert "external_contact_map_derivation" in manifest["blocked_until_later_gate"]
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_r14_residue_table_reads_only_locked_payload_and_preserves_hash():
    assert hashlib.sha256(PAYLOAD.read_bytes()).hexdigest() == EXPECTED_SHA
    lock = read_csv(PROT / "pdb_external_coordinate_payload_byte_hash_lock.csv")[0]
    assert lock["coordinate_payload_sha256"] == EXPECTED_SHA
    rows = read_csv(PROT / "pdb_external_residue_coordinate_table.csv")
    assert len(rows) == 46
    assert {r["coordinate_payload_sha256"] for r in rows} == {EXPECTED_SHA}
    assert {r["coordinate_source_hash"] for r in rows} == {EXPECTED_SHA}
    assert {r["source_accession"] for r in rows} == {"1CRN"}
    assert {r["chain_id"] for r in rows} == {"A"}
    assert {r["model_id"] for r in rows} == {"1"}
    assert {r["atom_selector"] for r in rows} == {"CA"}
    assert {r["atom_name"] for r in rows} == {"CA"}
    assert {r["leakage_role"] for r in rows} == {"target_only_after_AOD_freeze"}
    assert {r["contact_map_status"] for r in rows} == {"not_derived_in_v40.02r14"}
    assert {r["score_status"] for r in rows} == {"not_scored_in_v40.02r14"}


def test_r14_first_and_last_residue_rows_are_expected_ca_coordinates():
    rows = read_csv(PROT / "pdb_external_residue_coordinate_table.csv")
    first = rows[0]
    last = rows[-1]
    assert first["coordinate_row_id"] == "1CRN_A_model1_CA_auth1_label1"
    assert first["auth_seq_id"] == "1"
    assert first["label_seq_id"] == "1"
    assert first["residue_name"] == "THR"
    assert first["x"] == "16.967"
    assert first["y"] == "12.784"
    assert first["z"] == "4.338"
    assert last["coordinate_row_id"] == "1CRN_A_model1_CA_auth46_label46"
    assert last["auth_seq_id"] == "46"
    assert last["label_seq_id"] == "46"
    assert last["residue_name"] == "ASN"
    assert last["x"] == "13.512"
    assert last["y"] == "5.395"
    assert last["z"] == "12.878"


def test_r14_policy_application_and_missing_residue_audit_are_explicit():
    policy = read_csv(PROT / "pdb_external_residue_coordinate_policy_application.csv")[0]
    assert policy["coordinate_payload_sha256"] == EXPECTED_SHA
    assert policy["chain_id"] == "A"
    assert policy["model_id"] == "1"
    assert policy["residue_index_basis"] == "one_based_residue_sequence_position"
    assert policy["atom_selector"] == "CA"
    assert policy["selected_coordinate_rows"] == "46"
    assert policy["atom_site_extract_rows"] == "46"
    assert policy["contact_map_derivation_status"] == "not_derived_in_v40.02r14"
    assert policy["external_residual_score_status"] == "not_scored_in_v40.02r14"
    missing = read_csv(PROT / "pdb_external_missing_residue_audit.csv")
    assert len(missing) == 1
    assert missing[0]["missing_residue_status"] == "no_missing_CA_coordinates_in_selected_chain_model_policy"
    assert missing[0]["missing_residue_policy"] == "explicit_gap_rows_required_before_contact_derivation"


def test_r14_derivation_blocks_contact_map_and_external_score():
    blocks = read_csv(PROT / "pdb_external_residue_coordinate_derivation_block.csv")
    assert {r["candidate_derivation"] for r in blocks} == {
        "external_contact_map",
        "evaluation_pair_boundary",
        "external_residual_score",
    }
    assert {r["current_status"] for r in blocks} == {"blocked_in_v40.02r14"}
    checks = read_csv(PROT / "pdb_external_residue_coordinate_leakage_checks.csv")
    names = {r["check_name"] for r in checks}
    required = {
        "residue_table_reads_only_locked_byte_hash_payload",
        "coordinate_payload_sha256_matches_r13_lock",
        "chain_id_A_filter_applied",
        "atom_selector_CA_filter_applied",
        "model_policy_applied",
        "altloc_policy_applied_or_recorded",
        "missing_residue_policy_recorded",
        "no_contact_map_derived_in_r14",
        "no_external_residual_score_computed_in_r14",
        "coordinate_metrics_remain_deferred",
        "AOD_motif_curling_curls_and_SADAR_stay_upstream_of_future_target_join",
    }
    assert required <= names
    assert {r["check_result"] for r in checks} == {"active_pass"}
    assert {r["score_input_status"] for r in checks} == {"residue_table_gate_only_no_contact_map_or_score"}


def test_r14_generator_is_offline_reproducible_and_does_not_score():
    before = (PROT / "pdb_external_residue_coordinate_table.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "derive_external_pdb_residue_coordinate_table.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "score_scoped" not in text
    assert "score_multipair" not in text
    assert "pdb_external_contact_map" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_residue_coordinate_table.csv").read_text(encoding="utf-8")
    assert after == before


def test_r14_manual_section_and_roadmap_are_scope_tight():
    section = (ROOT / "manual-2" / "sections" / "13_external_pdb_residue_coordinate_table_derivation.tex").read_text(encoding="utf-8")
    assert "residue-coordinate table derivation gate" in section
    assert EXPECTED_SHA in section
    assert "not a contact-map derivation" in section
    assert "not a score" in section
    assert "46 residue-coordinate rows" in section
    assert "SADAR" not in section or "freeze" in section
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "External PDB Residue Coordinate Table Derivation Gate" in roadmap
    assert "v40.02r15 -- External PDB Contact Map Derivation Gate" in roadmap
