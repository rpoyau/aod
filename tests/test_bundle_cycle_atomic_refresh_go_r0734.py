from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def current_version():
    import re
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    m = re.search(r"Canonical version:\s*(\S+)", text)
    assert m
    return m.group(1)
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from bundle_common import load_json_strict, sha256_file, validate_schema, write_canonical_json
from review_common import derive_review_outcome, feedback_counts, resolution_authorized
import validate_upstream_release_lock as upstream_validator
from validate_upstream_release_lock import validate as validate_upstream


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_authoring_transition_invokes_candidate_bound_refresh():
    text = (TOOLS / "run_authoring_revision.py").read_text()
    assert "release_resolver.refresh_or_fallback" in text
    assert "candidate_release=args.version" in text
    assert "attempted_at_utc=args.refresh_attempted_at_utc" in text
    assert 'parser.add_argument("--refresh-attempted-at-utc", required=True)' in text


def test_static_candidate_refresh_receipt_is_complete_and_bound():
    receipt = load_json_strict(ROOT / "governance/UPSTREAM_REFRESH_ATTEMPT.json")
    fallback = load_json_strict(ROOT / "governance/UPSTREAM_FALLBACK_SNAPSHOT.json")
    assert receipt["candidate_release"] == current_version()
    assert receipt["attempt_status"] != "not_yet_attempted"
    assert receipt["dependency_order"] == ["AF", "AFC", "GM", "AOD"]
    assert fallback["candidate_release"] == receipt["candidate_release"]
    assert [row["dependency_id"] for row in fallback["dependencies"]] == ["AF", "AFC", "GM", "AOD"]
    upstream_report = validate_upstream(ROOT, allow_pending=False)
    assert upstream_report["status"] in {
        "nonblocking_refresh_fallback_valid",
        "trusted_project_sources_delta_scope_valid",
    }
    if upstream_report["status"] == "trusted_project_sources_delta_scope_valid":
        assert upstream_report["repositories_validated"] == 0
        assert upstream_report["dependency_scope"] == "project_source_trust_delta_scoped"
        assert upstream_report["dependency_payload_validation"] in {"not_required", "required_by_touch"}
    else:
        assert upstream_report["repositories_validated"] == 4


def test_atomic_resolution_rolls_back_partial_stage_mutation(monkeypatch, tmp_path: Path):
    resolver = load_module("atomic_resolver_r0734", TOOLS / "resolve_github_releases.py")
    root = tmp_path / "root"
    shutil.copytree(ROOT, root)
    profile = root / "governance/AF_PROTOCOL_PROFILE.json"
    before = sha256_file(profile)

    def partial_then_fail(stage_root: Path, **kwargs):
        (stage_root / "governance/AF_PROTOCOL_PROFILE.json").write_text('{"partial":true}\n', encoding="utf-8")
        raise OSError("simulated second-dependency network failure")

    monkeypatch.setattr(resolver, "_resolve_in_place", partial_then_fail)
    resolver.refresh_or_fallback(
        root,
        token=None,
        timeout=1,
        attempted_at_utc="2026-06-24T19:00:00Z",
        candidate_release=current_version(),
    )
    assert sha256_file(profile) == before
    receipt = load_json_strict(root / "governance/UPSTREAM_REFRESH_ATTEMPT.json")
    assert receipt["atomic_commit_status"] == "not_committed_fallback_preserved"
    assert receipt["partial_mutation_rollback_status"] == "passed_no_candidate_mutation"


def test_fallback_without_aod_dependency_fails(tmp_path: Path):
    root = tmp_path / "root"
    shutil.copytree(ROOT, root)
    fallback_path = root / "governance/UPSTREAM_FALLBACK_SNAPSHOT.json"
    fallback = load_json_strict(fallback_path)
    fallback["dependencies"] = fallback["dependencies"][:3]
    fallback["complete"] = True
    fallback_path.write_text(json.dumps(fallback, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    status_path = root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json"
    status = load_json_strict(status_path)
    status["fallback_snapshot_sha256"] = sha256_file(fallback_path)
    status_path.write_text(json.dumps(status, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_upstream(root, allow_pending=False)


def test_review_remains_blocked_until_go_transition_executes():
    outcome = derive_review_outcome(
        feedback_counts([]),
        reviewer_class="independent_bundle_reviewer",
        upstream_ready=True,
    )
    assert outcome["verdict"] == "GO_RECOMMENDED"
    assert outcome["r08_status"] == "BLOCKED"
    go_text = (TOOLS / "run_review_go_transition.py").read_text()
    assert '"to_phase": "GO"' in go_text
    assert '"r08_status": "OPEN"' in go_text
    assert 'candidate["status"] = "go_candidate"' in go_text


def test_af_accurate_finding_retirement_authority():
    assert resolution_authorized("independent_bundle_reviewer", "NOT_APPLICABLE_VERIFIED", "AF_POLICY_v40.03r07.3.4")
    assert not resolution_authorized("self_review", "NOT_APPLICABLE_VERIFIED", "AF_POLICY_v40.03r07.3.4")
    assert resolution_authorized("project_owner", "WAIVED_BY_AUTHORITY", "PROJECT_OWNER")
    assert not resolution_authorized("independent_bundle_reviewer", "WAIVED_BY_AUTHORITY", "PROJECT_OWNER")


def test_complete_and_phase_validators_cross_bind_human_state():
    complete = (TOOLS / "validate_complete_bundle.py").read_text()
    phase = (TOOLS / "validate_phase_bundle.py").read_text()
    for text in (complete, phase):
        assert "validate_workflow_state" in text
        assert "upstream refresh binding mismatch" in text
    assert 'candidate["status"] != "review_candidate"' in complete
    assert 'state["release"]["status"] != "review_candidate"' in complete


def test_go_decision_schema_and_command_are_present():
    assert (ROOT / "governance/schemas/go-decision.schema.json").is_file()
    assert (ROOT / "governance/GO_DECISION.template.json").is_file()
    assert (TOOLS / "run_review_go_transition.py").is_file()



def test_locked_fallback_rows_are_exactly_cross_bound_to_verified_lock(tmp_path: Path):
    repositories = []
    dependencies = []
    for dependency_id in ["AF", "AFC", "GM", "AOD"]:
        path = f"governance/releases/{dependency_id}/release.json"
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f'{{"dependency":"{dependency_id}"}}\n', encoding="utf-8")
        digest = sha256_file(target)
        repositories.append({
            "dependency_id": dependency_id,
            "release_metadata_path": path,
            "release_metadata_sha256": digest,
        })
        dependencies.append({
            "dependency_id": dependency_id,
            "path": path,
            "sha256": digest,
            "provenance_status": "resolved_release_supersedes_bootstrap",
        })
    lock = {"repositories": repositories}
    fallback = {"dependencies": dependencies}
    upstream_validator._validate_locked_fallback_dependencies(tmp_path, fallback, lock)

    tampered = json.loads(json.dumps(fallback))
    tampered["dependencies"][2]["path"] = tampered["dependencies"][1]["path"]
    with pytest.raises(ValueError, match="locked fallback identity mismatch"):
        upstream_validator._validate_locked_fallback_dependencies(tmp_path, tampered, lock)


def _go_record_fixture(root: Path) -> tuple[dict, dict, str, str, str]:
    schema_target = root / "governance/schemas/go-decision.schema.json"
    schema_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "governance/schemas/go-decision.schema.json", schema_target)
    (root / "cycle").mkdir(parents=True, exist_ok=True)
    (root / "PAYLOAD_CONTENTS_SHA256.txt").write_text("payload\n", encoding="utf-8")
    feedback_path = root / "cycle/FEEDBACK_LEDGER.csv"
    feedback_path.write_text("feedback\n", encoding="utf-8")
    review_path = "governance/reviews/review.json"
    review_target = root / review_path
    review_target.parent.mkdir(parents=True, exist_ok=True)
    review_target.write_text("{}\n", encoding="utf-8")
    review_digest = sha256_file(review_target)
    decision = {
        "schema_version": "3.1",
        "record_scope": "bundle_instance",
        "decision_id": "GO_DECISION_TEST",
        "candidate_version": "v-test",
        "authority_class": "project_owner",
        "authority_id": "PROJECT_OWNER",
        "decision": "GO",
        "rationale": "Independent review recommended GO and every finding is closed.",
        "checks": [{"check_id": "review", "status": "passed", "evidence": "canonical review"}],
        "candidate_payload_manifest_sha256": sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt"),
        "feedback_ledger_sha256": sha256_file(feedback_path),
        "review_record_path": review_path,
        "review_record_sha256": review_digest,
    }
    go_path = root / "cycle/GO_DECISION.json"
    write_canonical_json(go_path, decision)
    return {"version": "v-test"}, {"verdict": "GO_RECOMMENDED", "go_recommended": True}, review_path, review_digest, sha256_file(go_path)


def test_go_decision_is_cross_bound_by_transition_and_state(tmp_path: Path):
    phase_validator = load_module("phase_validator_r0734_delta2", TOOLS / "validate_phase_bundle.py")
    candidate, review, review_path, review_digest, decision_digest = _go_record_fixture(tmp_path)
    records = [{"bound_digests": {"go_decision_sha256": decision_digest}}]
    state = {"go": {"decision_path": "cycle/GO_DECISION.json", "decision_sha256": decision_digest}}
    observed = phase_validator._validate_go_decision(
        tmp_path,
        candidate,
        review,
        review_path,
        review_digest,
        sha256_file(tmp_path / "cycle/FEEDBACK_LEDGER.csv"),
        {"open_blocking": 0, "open_nonblocking": 0, "applied_unverified": 0},
        records,
        state,
    )
    assert observed == decision_digest
    records[0]["bound_digests"]["go_decision_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="GO transition decision binding mismatch"):
        phase_validator._validate_go_decision(
            tmp_path,
            candidate,
            review,
            review_path,
            review_digest,
            sha256_file(tmp_path / "cycle/FEEDBACK_LEDGER.csv"),
            {"open_blocking": 0, "open_nonblocking": 0, "applied_unverified": 0},
            records,
            state,
        )


def test_go_transition_schema_requires_decision_digest_and_command_revalidates_complete_bundle():
    schema = ROOT / "cycle/schemas/transition-record.schema.json"
    base = {
        "schema_version": "3.1",
        "sequence": 2,
        "transition_id": "test_review_to_go",
        "transition_class": "ledger_bootstrap_from_parent_state",
        "parent_bundle": {"filename": "bundle-vtest.zip", "sha256": "1" * 64},
        "predecessor_state": {"path": "cycle/CYCLE_STATE.json", "sha256": "2" * 64, "transition_sequence": 1},
        "from_phase": "REVIEW",
        "to_phase": "GO",
        "candidate_id": "candidate",
        "bound_digests": {
            "candidate_payload_manifest_sha256": "3" * 64,
            "delta_manifest_sha256": "4" * 64,
            "source_tree_delta_manifest_sha256": "5" * 64,
            "governance_manifest_sha256": "6" * 64,
            "feedback_ledger_sha256": "7" * 64,
            "authoring_report_sha256": "8" * 64,
            "review_record_sha256": "9" * 64,
        },
        "open_blocking_feedback": 0,
        "go_eligible": True,
        "r08_status": "OPEN",
        "recording_semantics": "content_addressed_no_wall_clock",
        "previous_row_sha256": None,
        "row_sha256": "a" * 64,
    }
    with pytest.raises(ValueError, match="go_decision_sha256"):
        validate_schema(base, schema, label="GO transition")
    base["bound_digests"]["go_decision_sha256"] = "b" * 64
    validate_schema(base, schema, label="GO transition")
    command = (TOOLS / "run_review_go_transition.py").read_text(encoding="utf-8")
    assert '"go_decision_sha256": go_decision_sha256' in command
    assert "complete_report = validate_complete_bundle.validate(emitted)" in command
    assert 'state["go"]["decision_sha256"] = go_decision_sha256' in command
