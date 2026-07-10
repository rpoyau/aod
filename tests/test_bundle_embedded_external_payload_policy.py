from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2/data/protein"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory_rows() -> list[dict[str, str]]:
    with (PROT / "external_payload_bundle_inventory.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_inventory_is_authoritative_and_all_registered_assets_match():
    rows = inventory_rows()
    assert len(rows) == 10
    assert any(r["payload_class"] == "candidate_universe_archive_query_specification" for r in rows)
    assert all(r["source_path"] and r["bundle_path"] for r in rows)
    assert len({r["source_path"] for r in rows}) == len(rows)
    assert len({r["bundle_path"] for r in rows}) == len(rows)
    for row in rows:
        p = ROOT / row["source_path"]
        assert p.is_file(), p
        assert str(p.stat().st_size) == row["payload_byte_count"]
        assert sha256(p) == row["payload_sha256"]
        assert row["bundle_path"].startswith("external_payloads/")
        assert row["origin_class"] in {"archive_external", "release_local_derived", "release_policy_metadata"}
        assert row["embedding_class"] == "inline_bundle"
        assert row["required_for_release"] == "yes"


def test_all_committed_archive_payload_files_are_registered():
    rows = inventory_rows()
    registered = {(ROOT / r["source_path"]).resolve() for r in rows}
    for rel in [
        "manual-2/data/protein/external_pdb_payloads",
        "manual-2/data/protein/external_pdb_validation_payloads",
        "manual-2/data/protein/external_pdb_probe_evidence_snapshots",
    ]:
        for p in (ROOT / rel).rglob("*"):
            if p.is_file():
                assert p.resolve() in registered, p


def test_bundle_builder_uses_inventory_allowlist_not_recursive_discovery():
    builder = (ROOT / "scripts/build_release_bundle.py").read_text(encoding="utf-8")
    assert "BUNDLE_EXTERNAL_PAYLOAD_INVENTORY" in builder
    assert "read_external_payload_inventory" in builder
    assert "validate_required_bundle_external_payloads" in builder
    assert "copy_bundle_external_payloads(bundle_tmp)" in builder
    assert "BUNDLE_EXTERNAL_PAYLOAD_SOURCES" not in builder
    assert "REQUIRED_BUNDLE_EXTERNAL_PAYLOADS" not in builder
    assert 'external_payload_manifest = bundle_tmp / "EXTERNAL_PAYLOADS_SHA256.txt"' in builder
    assert 'payload_root = bundle_tmp / "external_payloads"' in builder


def test_bundle_payload_status_and_large_payload_policy_are_explicit():
    d = json.loads((PROT / "external_payload_bundle_status.json").read_text(encoding="utf-8"))
    assert d["policy_version"] == "v40.03r01"
    assert d["inventory_authority"].endswith("external_payload_bundle_inventory.csv")
    assert set(d["archive_validation_payloads"].values()) == {"archive_payload_byte_hash_locked"}
    assert d["historical_versioned_bundles"] == "immutable_not_rewritten"
    policy = (PROT / "external_payload_embedding_policy.csv").read_text(encoding="utf-8")
    assert "separate_versioned_payload_pack" in policy
    assert "manifest_only_external_lock" in policy
    assert "raw_diffraction_images" in policy


def test_workflow_publishes_external_payload_manifest_and_installs_pypdf():
    workflow = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
    assert "dist/EXTERNAL_PAYLOADS_SHA256.txt" in workflow
    assert "requirements-ci.txt" in workflow
