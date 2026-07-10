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
EXPECTED_BYTES = "69506"


def read_csv(name):
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_r13_payload_file_is_committed_and_hash_locked():
    assert PAYLOAD.exists()
    data = PAYLOAD.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED_SHA
    assert str(len(data)) == EXPECTED_BYTES
    assert data.startswith(b"data_1CRN")
    row = read_csv("pdb_external_coordinate_payload_byte_hash_lock.csv")[0]
    assert row["version_scope"] == "v40.02r13"
    assert row["local_payload_path"] == "manual-2/data/protein/external_pdb_payloads/1CRN.cif"
    assert row["coordinate_payload_sha256"] == EXPECTED_SHA
    assert row["coordinate_payload_byte_count"] == EXPECTED_BYTES
    assert row["coordinate_payload_byte_hash_status"] == "byte_payload_sha256_locked_from_local_payload"
    assert row["byte_hash_distinct_from_locator_policy_registration_sha256"] == "true"
    assert row["coordinate_payload_sha256"] != row["locator_policy_registration_sha256"]


def test_r13_hash_lock_is_target_only_and_does_not_derive_rows_or_score():
    row = read_csv("pdb_external_coordinate_payload_byte_hash_lock.csv")[0]
    assert row["residue_table_derivation_status"] == "not_derived_in_this_gate_requires_explicit_next_gate"
    assert row["contact_map_derivation_status"] == "not_derived_in_this_gate_requires_residue_table_gate"
    assert row["external_residual_score_status"] == "not_scored_in_this_gate_requires_contact_map_and_scope_gate"
    assert row["coordinate_metric_status"] == "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze"
    blocks = read_csv("pdb_external_coordinate_payload_byte_hash_derivation_block.csv")
    assert {r["current_status"] for r in blocks} == {"blocked_in_v40.02r13"}
    assert {r["candidate_derivation"] for r in blocks} == {
        "external_residue_coordinate_table",
        "external_contact_map",
        "external_residual_score",
    }


def test_r13_leakage_audit_preserves_freeze_before_target_join():
    rows = read_csv("pdb_external_coordinate_payload_byte_hash_leakage_checks.csv")
    names = {r["check_name"] for r in rows}
    required = {
        "coordinate_payload_byte_sha256_exists_before_residue_table",
        "coordinate_payload_byte_hash_differs_from_locator_policy_hash",
        "residue_coordinate_table_remains_blocked_until_explicit_next_gate",
        "contact_map_remains_blocked_until_residue_table_gate",
        "external_payload_forbidden_as_raw_dec_or_aod_freeze_premise",
        "target_rows_remain_downstream_of_frozen_AOD_packet",
        "coordinate_level_metrics_remain_deferred",
        "AOD_motif_curling_curls_and_SADAR_precede_future_external_target_map",
    }
    assert required <= names
    assert {r["check_result"] for r in rows} == {"active_pass"}
    assert {r["score_input_status"] for r in rows} == {"hash_gate_only_no_score"}


def test_r13_manifest_records_byte_hash_lock_without_claiming_derivation():
    manifest = json.loads((PROT / "pdb_external_coordinate_payload_byte_hash_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r13"
    assert manifest["coordinate_payload_sha256"] == EXPECTED_SHA
    assert str(manifest["coordinate_payload_byte_count"]) == EXPECTED_BYTES
    assert manifest["local_payload_path"] == "manual-2/data/protein/external_pdb_payloads/1CRN.cif"
    assert "not residue-table derivation" in manifest["claim_discipline"] or "not residue" in manifest["claim_discipline"]
    assert "external_residue_coordinate_table_derivation" in manifest["blocked_until_later_gate"]
    assert "local_payload" in manifest["files"]


def test_r13_lock_generator_is_offline_and_reproducible():
    before = (PROT / "pdb_external_coordinate_payload_byte_hash_lock.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "lock_external_pdb_coordinate_payload_byte_hash.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "pdb_mmcif_atom_site_extract.csv" not in text
    assert "pdb_mmcif_contact_map_derived.csv" not in text
    assert "pdb_external_accession_residual" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_external_coordinate_payload_byte_hash_lock.csv").read_text(encoding="utf-8")
    assert after == before


def test_r13_manual_section_is_byte_hash_lock_only():
    section = (ROOT / "manual-2" / "sections" / "12_external_pdb_coordinate_payload_byte_hash_lock.tex").read_text(encoding="utf-8")
    assert "coordinate byte-payload hash lock" in section
    assert EXPECTED_SHA in section
    assert "not a residue-table derivation" in section
    assert "not a contact-map score" in section
    compact = section.replace("\\_", "_")
    assert "not_derived_in_this_gate" in compact
    assert "not_scored_in_this_gate" in compact
    assert "AOD motif / curling-curls specification" in section
    assert "SADAR context" in section
    assert "RMSD" not in section
    assert "TM-score" not in section
    assert "GDT" not in section


def test_r13_roadmap_current_and_next_gate_are_correct():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "External PDB Coordinate Payload Byte-Hash Lock" in roadmap
    assert EXPECTED_SHA in roadmap
    assert "v40.02r14 -- External PDB Residue Coordinate Table Derivation Gate" in roadmap
