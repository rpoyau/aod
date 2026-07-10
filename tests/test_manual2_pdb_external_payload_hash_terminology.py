import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def rows(name):
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_locator_policy_registration_hash_is_not_coordinate_byte_hash():
    gate = rows("pdb_external_coordinate_payload_hash_gate.csv")[0]
    assert gate["coordinate_payload_sha256_status"] == "byte_payload_hash_required_not_satisfied_in_this_gate"
    assert gate["coordinate_payload_sha256"] == "required_after_external_payload_bytes_are_registered_before_contact_derivation"
    assert len(gate["locator_policy_registration_sha256"]) == 64
    assert gate["payload_registration_sha256"] == gate["locator_policy_registration_sha256"]
    terms = {r["field_name"]: r for r in rows("pdb_external_coordinate_payload_hash_terminology.csv")}
    assert terms["locator_policy_registration_sha256"]["is_coordinate_byte_hash"] == "false"
    assert terms["payload_registration_sha256"]["relationship_to_future_coordinate_payload_sha256"] == "distinct_from_future_coordinate_payload_sha256"
    assert terms["coordinate_payload_sha256"]["is_coordinate_byte_hash"] == "true_when_registered_in_future_gate"


def test_carried_forward_pdb_mmcif_fixtures_are_not_external_1crn_ingest():
    fixtures = rows("pdb_external_coordinate_payload_carried_forward_fixture_scope.csv")
    assert fixtures
    assert {r["source_status"] for r in fixtures} == {"manual_GAS_target_only_fixture_carried_forward"}
    assert all("not_" in r["relationship_to_external_1CRN_gate"] for r in fixtures)
    assert {r["score_status"] for r in fixtures} == {"not_scored_as_external_accession_in_this_gate"}
    manifest = json.loads((PROT / "pdb_external_coordinate_payload_hash_manifest.json").read_text(encoding="utf-8"))
    assert "terminology" in manifest["files"]
    assert "carried_forward_fixture_scope" in manifest["files"]
    assert "registration_hash_note" in manifest
    assert "not the external coordinate byte-payload SHA-256" in manifest["registration_hash_note"]


def test_offline_byte_hash_registration_script_hashes_supplied_local_payload(tmp_path):
    payload = tmp_path / "1CRN.cif"
    payload.write_bytes(b"data_1CRN\n#\n")
    out = tmp_path / "hash.csv"
    script = ROOT / "manual-2" / "scripts" / "register_external_pdb_coordinate_payload_byte_hash.py"
    text = script.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    result = subprocess.run([sys.executable, str(script), "--payload", str(payload), "--out", str(out)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    row = list(csv.DictReader(out.open(newline="", encoding="utf-8")))[0]
    assert row["coordinate_payload_sha256"] == hashlib.sha256(payload.read_bytes()).hexdigest()
    assert row["coordinate_payload_byte_count"] == str(len(payload.read_bytes()))
    assert row["derivation_status_after_registration"] == "residue_table_still_requires_explicit_next_gate"


def test_r12_1_manual_section_separates_hash_roles_and_carried_forward_fixtures():
    section = (ROOT / "manual-2" / "sections" / "11_external_pdb_coordinate_payload_hash_gate.tex").read_text(encoding="utf-8")
    assert "Registration hash versus byte-payload hash" in section
    assert "locator/policy registration hash" in section
    assert "not the external mmCIF byte-payload hash" in section
    assert "pdb\\_mmcif\\_*" in section
    assert "not the external \\texttt{1CRN} byte-payload ingest lane" in section
