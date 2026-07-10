from __future__ import annotations

import csv
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2/data/protein"
PAY = PROT / "external_pdb_validation_payloads"


def rows(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_original_validation_archives_are_committed_and_gzip_valid() -> None:
    expected = {
        "1crn_validation.xml.gz": "c67174996cef25bfd3d7a61e1ad21a88c83d07d9758f6a0a20642b0cd743719d",
        "1crn_validation.cif.gz": "0d822c7f3e60f01852e5f426e7602223ef7b3ce61584f2f121e890393ea4d25e",
        "1crn_full_validation.pdf.gz": "a5332328f61705d7e7acdcd3bea09267e5f5f55a1c8d9cefde0760205db6195d",
    }
    for name, digest in expected.items():
        path = PAY / name
        assert path.is_file(), name
        assert sha(path) == digest
        assert len(gzip.decompress(path.read_bytes())) > 0


def test_archive_payload_lock_ledger_matches_bytes_and_content_hashes() -> None:
    r = rows("pdb_external_validation_archive_payload_byte_lock.csv")
    assert len(r) == 3
    assert {x["byte_lock_status"] for x in r} == {"archive_payload_byte_hash_locked"}
    assert {x["origin_class"] for x in r} == {"archive_external"}
    for row in r:
        path = ROOT / row["local_payload_path"]
        raw = path.read_bytes()
        content = gzip.decompress(raw)
        assert hashlib.sha256(raw).hexdigest() == row["archive_payload_sha256"]
        assert str(len(raw)) == row["archive_payload_byte_count"]
        assert hashlib.sha256(content).hexdigest() == row["decompressed_content_sha256"]
        assert str(len(content)) == row["decompressed_content_byte_count"]
        assert row["archive_payload_source_url"].startswith("https://files.rcsb.org/validation/download/")


def test_archive_regenerated_snapshot_is_field_equivalent() -> None:
    regenerated = PAY / "1crn_full_validation_report_archive_regenerated_snapshot.json"
    assert regenerated.is_file()
    audit = rows("pdb_external_validation_snapshot_field_equivalence_audit.csv")
    assert len(audit) == 41
    assert {x["field_equivalence_status"] for x in audit} == {"exact_after_declared_normalization"}
    assert {x["field_equivalence_residual"] for x in audit} == {"0"}
    assert {x["parsed_snapshot_regeneration_sha256"] for x in audit} == {sha(regenerated)}
    assert all(x["machine_field_locator"] for x in audit)


def test_evidence_locators_are_locked_and_machine_stable_where_available() -> None:
    r = rows("pdb_external_validation_snapshot_evidence_locators.csv")
    assert len(r) == 41
    assert {x["source_payload_lock_status"] for x in r} == {"archive_payload_byte_hash_locked"}
    assert {x["field_equivalence_status"] for x in r} == {"exact_after_declared_normalization"}
    assert all(x["source_machine_locator"] for x in r)
    assert any("/wwPDB-validation-information/" in x["source_machine_locator"] for x in r)
    assert any("_pdbx_vrpt_" in x["source_machine_locator"] for x in r)
    assert any("PDF page" in x["source_machine_locator"] for x in r)


def test_r22b1_manifest_records_no_score_and_equivalence() -> None:
    d = json.loads((PROT / "pdb_external_validation_archive_payload_manifest.json").read_text(encoding="utf-8"))
    assert d["version_scope"] == "v40.02r22B.1"
    assert d["archive_payload_count"] == 3
    assert d["field_equivalence_audit_count"] == 41
    assert d["field_equivalence_exact_count"] == 41
    assert d["field_equivalence_mismatch_count"] == 0
    assert d["quality_mask_recomputation_status"].startswith("not_required")
    assert d["target_join_status"].startswith("closed")
    assert d["residual_status"] == "not_computed"
    assert d["score_status"] == "no_score"


def test_quality_mask_and_target_join_remain_closed() -> None:
    summary = rows("pdb_external_quality_masked_contact_summary.csv")[0]
    assert summary["effective_contact_count"] == "0"
    assert summary["effective_noncontact_count"] == "0"
    assert summary["effective_abstain_count"] == "946"
    assert summary["aod_comparison_join_gate_state"] == "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs"


def test_manual_section_is_versionless_and_gate_only() -> None:
    text = (ROOT / "manual-2/sections/25_original_validation_payload_byte_lock_gate.tex").read_text(encoding="utf-8")
    assert "Original validation-payload byte-lock gate" in text
    assert "N_{\\rm audited}=41" in text
    assert "N_{\\rm equivalent}=41" in text
    assert "Inventory-driven bundle embedding" in text
    assert "v40.02" not in text
    assert "score audits" in text


def test_r22b1_generator_is_offline_and_reproducible() -> None:
    tracked = [
        PROT / "pdb_external_validation_archive_payload_byte_lock.csv",
        PROT / "pdb_external_validation_snapshot_field_equivalence_audit.csv",
        PROT / "pdb_external_validation_snapshot_evidence_locators.csv",
        PROT / "pdb_external_validation_archive_payload_manifest.json",
        PAY / "1crn_full_validation_report_archive_regenerated_snapshot.json",
        PROT / "pdb_external_validation_payload_byte_lock.csv",
        PROT / "pdb_external_validation_payload_provenance.csv",
        PROT / "pdb_external_experimental_payload_availability.csv",
    ]
    before = {p.name: p.read_bytes() for p in tracked}
    script = ROOT / "manual-2/scripts/lock_original_pdb_validation_payloads.py"
    text = script.read_text(encoding="utf-8")
    assert "requests" not in text
    assert "urllib" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = {p.name: p.read_bytes() for p in tracked}
    assert after == before
