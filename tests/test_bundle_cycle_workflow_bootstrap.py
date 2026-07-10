from __future__ import annotations

import csv
import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def current_version():
    import re
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    m = re.search(r"Canonical version:\s*(\S+)", text)
    assert m
    return m.group(1)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_workflow_files_and_rebase():
    state = json.loads((ROOT / "cycle/CYCLE_STATE.json").read_text())
    assert state["record_scope"] == "source_template"
    assert state["release"]["working_version"] == current_version()
    assert state["lineage_parent_binding"] == "BIND_FROM_INPUT_BUNDLE_FILENAME_AND_SHA256"
    assert not state["go"]["eligible"]
    assert not (ROOT / "governance/UPSTREAM_RELEASE_LOCK.json").exists()


def test_domain_authority_and_source_scope():
    governance = json.loads((ROOT / "governance/GLOBAL_INSTRUCTIONS.json").read_text())
    assert set(governance["authority_domains"]) == {"AF", "AFC", "AOD_governance", "GM"}
    registry = json.loads((ROOT / "governance/REPOSITORY_RELEASE_SOURCES.json").read_text())
    assert registry["release_source_scope"] == "governance_and_project_baseline_dependencies"


def test_source_builder_excludes_python_cache_and_includes_patch_summary():
    text = (ROOT / "scripts/build_release_bundle.py").read_text()
    assert '"__pycache__"' in text and '".pyc"' in text
    assert '"patch_summary.txt"' in text
    assert "tools/run_bundle_transition.py" in text


def test_archive_safety_and_roles():
    resolver = load("resolver", ROOT / "tools/resolve_github_releases.py")
    import io

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("../escape", "x")
    try:
        resolver.inspect_archive_bytes("x.zip", payload.getvalue())
        assert False
    except ValueError:
        pass
    assets = [
        {"name": "bundle-v1.zip", "role": "canonical_bundle", "asset_id": 1, "byte_count": 1, "sha256": "0" * 64},
        {"name": "source.zip", "role": "source_archive", "asset_id": 2, "byte_count": 1, "sha256": "0" * 64},
        {"name": "main.pdf", "role": "pdf", "asset_id": 3, "byte_count": 1, "sha256": "0" * 64},
        {"name": "SHA256.txt", "role": "checksum_manifest", "asset_id": 4, "byte_count": 1, "sha256": "0" * 64},
    ]
    resolver.validate_role_contract("AOD", assets)


def test_feedback_template_records_policy_application_as_latest_event():
    rows = list(csv.DictReader((ROOT / "cycle/FEEDBACK_LEDGER.template.csv").open()))
    latest = {}
    for row in rows:
        latest[row["finding_id"]] = row
    assert latest["FB-R072-001"]["status"] == "APPLIED_UNVERIFIED"
    assert sum(row["status"] == "APPLIED_UNVERIFIED" for row in rows) == 9
