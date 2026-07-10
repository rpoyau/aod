from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from bundle_common import load_json_strict, validate_schema
from review_common import derive_review_outcome, upstream_lock_ready
from validate_upstream_release_lock import validate as validate_upstream


def load_module(name: str, path: Path):
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


def test_authoring_always_attempts_latest_but_candidate_is_frozen():
    policy = load_json_strict(ROOT / "governance/UPSTREAM_RELEASE_POLICY.json")
    registry = load_json_strict(ROOT / "governance/REPOSITORY_RELEASE_SOURCES.json")
    assert policy["discovery"]["latest_refresh_mode"] == "always_attempt_on_authoring"
    assert policy["discovery"]["resolved_snapshot_frozen_per_candidate"] is True
    assert policy["activation"]["latest_change_after_candidate_freeze_applies_next_authoring"] is True
    assert registry["refresh_contract"]["review_feedback_go_network_access"] is False


def test_explicit_refresh_fallback_is_not_a_go_blocker():
    status = load_json_strict(ROOT / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
    assert status["canonical_lock_present"] is False
    assert status["go_eligible"] is True
    assert status["go_blocking"] is False
    assert status["fallback_claims_latest"] is False
    assert upstream_lock_ready(status)
    outcome = derive_review_outcome(
        {"open_blocking": 0, "open_nonblocking": 0, "applied_unverified": 0, "verified_closed": 1, "waived": 0},
        reviewer_class="independent_bundle_reviewer",
        upstream_ready=upstream_lock_ready(status),
    )
    assert outcome["verdict"] == "GO_RECOMMENDED"


def test_nonblocking_fallback_validates_strictly():
    report = validate_upstream(ROOT, allow_pending=False)
    assert_nonblocking_or_trusted_project_scope(report)


def test_resolver_records_nonblocking_failure(monkeypatch, tmp_path: Path):
    resolver = load_module("rolling_resolver", TOOLS / "resolve_github_releases.py")
    import shutil
    work = tmp_path / "source"
    shutil.copytree(ROOT, work)
    def boom(*args, **kwargs):
        raise OSError("network unavailable")
    monkeypatch.setattr(resolver, "resolve", boom)
    path = resolver._record_nonblocking_fallback(work, "network unavailable")
    status = load_json_strict(path)
    validate_schema(status, work / "governance/schemas/upstream-release-lock-status.schema.json")
    assert_nonblocking_or_trusted_project_scope(validate_upstream(work, allow_pending=False))
    assert status["go_eligible"] is True
    assert status["fallback_claims_latest"] is False
