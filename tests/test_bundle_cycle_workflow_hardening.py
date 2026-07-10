from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from bundle_common import deterministic_zip_from_directory, load_json_strict, row_sha256, validate_schema
from validate_upstream_release_lock import validate as validate_upstream_lock
from review_common import derive_review_outcome, upstream_lock_ready


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def assert_nonblocking_or_trusted_project_scope(report: dict) -> None:
    assert report["status"] in {
        "nonblocking_refresh_fallback_valid",
        "trusted_project_sources_delta_scope_valid",
    }
    if report["status"] == "trusted_project_sources_delta_scope_valid":
        assert report["repositories_validated"] == 0
        assert report["dependency_scope"] == "project_source_trust_delta_scoped"
        assert report["dependency_payload_validation"] in {"not_required", "required_by_touch"}
    else:
        assert report["repositories_validated"] == 4



def test_native_31_records_validate_against_exact_schemas():
    pairs = [
        ("cycle/CYCLE_STATE.json", "cycle/schemas/cycle-state-template.schema.json"),
        ("cycle/ACTIVE_GOAL.json", "cycle/schemas/active-goal.schema.json"),
        ("cycle/CYCLE_POLICY.json", "cycle/schemas/cycle-policy.schema.json"),
        ("cycle/AUTHORING_REPORT.template.json", "cycle/schemas/authoring-report-template.schema.json"),
        ("governance/REPOSITORY_RELEASE_SOURCES.json", "governance/schemas/repository-release-sources.schema.json"),
        ("governance/UPSTREAM_RELEASE_POLICY.json", "governance/schemas/upstream-release-policy.schema.json"),
        ("governance/UPSTREAM_RELEASE_LOCK_STATUS.json", "governance/schemas/upstream-release-lock-status.schema.json"),
        ("governance/GLOBAL_INSTRUCTIONS.json", "governance/schemas/global-instructions.schema.json"),
    ]
    for record, schema in pairs:
        validate_schema(load_json_strict(ROOT / record), ROOT / schema, label=record)


def test_exact_schema_rejects_unknown_cycle_state_field():
    state = load_json_strict(ROOT / "cycle/CYCLE_STATE.json")
    state["unknown_field"] = "forbidden"
    with pytest.raises(ValueError):
        validate_schema(state, ROOT / "cycle/schemas/cycle-state-template.schema.json")


def test_duplicate_json_key_is_rejected(tmp_path: Path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"a":1,"a":2}\n')
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_json_strict(path)


def test_unavailable_latest_refresh_is_explicit_and_nonblocking():
    report = validate_upstream_lock(ROOT, allow_pending=False)
    assert_nonblocking_or_trusted_project_scope(report)
    assert report["fallback_mode"] == "bootstrap_hash_locked_until_first_successful_refresh"


def test_fallback_cannot_claim_latest_or_block_go(tmp_path: Path):
    shutil.copytree(ROOT / "governance", tmp_path / "governance")
    status_path = tmp_path / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json"
    status = load_json_strict(status_path)
    status["fallback_claims_latest"] = True
    status_path.write_text(json.dumps(status))
    with pytest.raises(ValueError):
        validate_upstream_lock(tmp_path, allow_pending=False)


def test_bogus_release_lock_fails_strict_validator(tmp_path: Path):
    shutil.copytree(ROOT / "governance", tmp_path / "governance")
    bogus = {
        "schema_version": "bogus",
        "lock_id": "x",
        "resolved_at_utc": "not-a-date",
        "resolver_version": "x",
        "repositories": [],
    }
    (tmp_path / "governance/UPSTREAM_RELEASE_LOCK.json").write_text(json.dumps(bogus))
    status = load_json_strict(tmp_path / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
    status["canonical_lock_present"] = True
    (tmp_path / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json").write_text(json.dumps(status))
    with pytest.raises(ValueError):
        validate_upstream_lock(tmp_path, allow_pending=False)


def test_role_contract_requires_pdf_and_source_snapshot():
    resolver = load("resolver_hardening", ROOT / "tools/resolve_github_releases.py")
    with pytest.raises(ValueError, match="PDF asset required"):
        resolver.validate_role_contract("AF", [], source_snapshot_present=True)
    with pytest.raises(ValueError, match="source snapshot required"):
        resolver.validate_role_contract("AF", [{"role": "pdf"}], source_snapshot_present=False)


def test_aod_authored_checksum_coverage_must_be_complete():
    resolver = load("resolver_checksums", ROOT / "tools/resolve_github_releases.py")
    assets = [
        {"name": "bundle-v1.zip", "role": "canonical_bundle", "sha256": "1" * 64},
        {"name": "main.pdf", "role": "pdf", "sha256": "2" * 64},
        {"name": "SHA256.txt", "role": "checksum_manifest", "sha256": "3" * 64},
    ]
    manifest = ("1" * 64 + "  bundle-v1.zip\n").encode()
    with pytest.raises(ValueError, match="coverage incomplete"):
        resolver.verify_authored_manifests("AOD", assets, {"bundle-v1.zip": b"x", "main.pdf": b"y", "SHA256.txt": manifest})


def test_source_feedback_template_preserves_author_review_separation():
    rows = list(csv.DictReader((ROOT / "cycle/FEEDBACK_LEDGER.template.csv").open()))
    new = [row for row in rows if row["finding_id"].startswith("R073-F")]
    assert len(new) == 8
    assert {row["status"] for row in new[:5]} == {"VERIFIED_CLOSED"}
    assert {row["status"] for row in new[5:]} == {"APPLIED_UNVERIFIED"}


def test_feedback_row_hash_is_order_sensitive_and_chainable():
    first = row_sha256(["1", "A", "OPEN"])
    second = row_sha256(["2", "B", first])
    assert first != row_sha256(["A", "1", "OPEN"])
    assert second == row_sha256(["2", "B", first])


def test_deterministic_zip_bytes_are_identical(tmp_path: Path):
    source = tmp_path / "tree"
    source.mkdir()
    (source / "b.txt").write_text("b\n")
    (source / "a.txt").write_text("a\n")
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    deterministic_zip_from_directory(source, first)
    deterministic_zip_from_directory(source, second)
    assert first.read_bytes() == second.read_bytes()


def test_complete_transition_engine_and_patch_summary_are_canonical():
    workflow = (ROOT / "BUNDLE_WORKFLOW.md").read_text()
    builder = (ROOT / "scripts/build_release_bundle.py").read_text()
    materializer = (TOOLS / "run_bundle_transition.py").read_text()
    phase_engine = (TOOLS / "run_phase_transition.py").read_text()
    complete_validator = (TOOLS / "validate_complete_bundle.py").read_text()
    assert "Current state: AUTHORING." in workflow
    assert "Next permitted transitions: REVIEW." in workflow
    assert "CANONICAL_COMPLETE_BUNDLE_COMMAND" in builder
    assert '"patch_summary.txt"' in builder
    for name in [
        "resolve_github_releases.py",
        "run_bundle_transition.py",
        "run_phase_transition.py",
        "run_review_feedback_transition.py",
        "review_common.py",
        "validate_complete_bundle.py",
        "validate_phase_bundle.py",
        "validate_upstream_release_lock.py",
        "validate_cycle_bundle.py",
    ]:
        assert "sys.dont_write_bytecode = True" in (TOOLS / name).read_text()
    assert '"transition_class": "ordinary_parent_prefix_plus_one"' in materializer
    assert "parent_ledger_bytes + canonical_json_bytes(transition)" in materializer
    assert "parent_ledger_bytes + canonical_json_bytes(transition)" in phase_engine
    assert "transition ledger must begin with the one-time sequence-2 bootstrap row" in complete_validator
    assert "required phase tool missing from source.zip" in complete_validator


def test_review_submission_template_is_noncanonical_and_data_driven():
    review = load_json_strict(ROOT / "governance/reviews/REVIEW_SUBMISSION.template.json")
    assert review["closed_findings"] == []
    assert review["open_findings"] == []
    status = load_json_strict(ROOT / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
    expected = derive_review_outcome(
        {"open_blocking": 0, "open_nonblocking": 0, "applied_unverified": 0, "verified_closed": 0, "waived": 0},
        reviewer_class=review["reviewer_class"],
        upstream_ready=upstream_lock_ready(status),
    )
    assert review["verdict"] == expected["verdict"]
    assert review["go_recommended"] == expected["go_recommended"]
    assert "external reviewer-supplied" in review["binding_policy"]
