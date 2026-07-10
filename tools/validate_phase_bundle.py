#!/usr/bin/env python3
"""Validate AOD FEEDBACK/AUTHORING successors without mutating payload bytes."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

try:
    import validate_complete_bundle as base
    from bundle_common import load_json_strict, resolve_inside, sha256_file, validate_schema
    from review_common import derive_review_outcome, reviewer_can_verify, upstream_lock_ready, validate_workflow_state
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import validate_complete_bundle as base  # type: ignore
    from bundle_common import load_json_strict, resolve_inside, sha256_file, validate_schema  # type: ignore
    from review_common import derive_review_outcome, reviewer_can_verify, upstream_lock_ready, validate_workflow_state  # type: ignore


PHASE_RULES = {
    "FEEDBACK": {
        "last_completed": "REVIEW",
        "next": ["AUTHORING"],
        "candidate_status": "feedback_candidate",
        "release_status": "feedback_candidate",
        "last_transition": ("REVIEW", "FEEDBACK"),
        "review_must_bind_current_feedback": True,
    },
    "AUTHORING": {
        "last_completed": {"FEEDBACK", "GO"},
        "next": ["REVIEW"],
        "candidate_status": "authoring_candidate",
        "release_status": "authoring_candidate",
        "last_transition": {("FEEDBACK", "AUTHORING"), ("GO", "AUTHORING")},
        "review_must_bind_current_feedback": False,
    },
    "GO": {
        "last_completed": "REVIEW",
        "next": ["AUTHORING"],
        "candidate_status": "go_candidate",
        "release_status": "go_candidate",
        "last_transition": ("REVIEW", "GO"),
        "review_must_bind_current_feedback": True,
    },
}


def _load_review_identity(root: Path) -> tuple[dict[str, Any], str, str]:
    index = load_json_strict(root / "governance/reviews/REVIEW_INDEX.json")
    validate_schema(index, root / "cycle/schemas/review-index.schema.json", label="review index")
    path = resolve_inside(root, index["canonical_review_path"])
    review = load_json_strict(path)
    validate_schema(review, root / "cycle/schemas/review-record.schema.json", label="canonical review")
    digest = sha256_file(path)
    if index["canonical_review_sha256"] != digest:
        raise ValueError("review index digest mismatch")
    for historical in index["historical_reviews"]:
        hpath = resolve_inside(root, historical["path"])
        if not hpath.is_file() or sha256_file(hpath) != historical["sha256"]:
            raise ValueError("historical review index mismatch")
    return review, digest, path.relative_to(root).as_posix()


def _validate_state(
    root: Path,
    candidate: dict[str, Any],
    feedback_counts: dict[str, int],
    review_path: str,
    review_digest: str,
    review: dict[str, Any],
    transition_records: list[dict[str, Any]],
    transition_digest: str,
    last_row_sha: str,
    governance_digest: str,
) -> dict[str, Any]:
    state = load_json_strict(root / "cycle/CYCLE_STATE.json")
    validate_schema(state, root / "cycle/schemas/cycle-state.schema.json", label="cycle state")
    phase = state["active_phase"]
    if phase not in PHASE_RULES:
        raise ValueError(f"phase-only validator does not admit active phase: {phase}")
    rule = PHASE_RULES[phase]
    allowed_completed = rule["last_completed"] if isinstance(rule["last_completed"], set) else {rule["last_completed"]}
    if state["last_completed_phase"] not in allowed_completed:
        raise ValueError("cycle last-completed phase mismatch")
    if state["next_permitted_transitions"] != rule["next"]:
        raise ValueError("cycle next-transition mismatch")
    if candidate["status"] != rule["candidate_status"] or state["release"]["status"] != rule["release_status"]:
        raise ValueError("candidate/release phase status mismatch")
    if state["release"]["working_version"] != candidate["version"] or state["working_candidate"]["candidate_id"] != candidate["candidate_id"]:
        raise ValueError("cycle state candidate mismatch")
    if state["release"]["target_version"] != candidate["version"]:
        raise ValueError("phase target-version mismatch")
    if phase in {"FEEDBACK", "GO"} and review["candidate_version"] != candidate["version"]:
        raise ValueError("phase review candidate-version mismatch")
    if review.get("candidate_id") is not None and review["candidate_id"] != candidate["candidate_id"]:
        raise ValueError("phase review candidate-id mismatch")
    if state["feedback_counts"] != feedback_counts:
        raise ValueError("cycle state feedback counts mismatch")
    if state["review"] != {"record_path": review_path, "record_sha256": review_digest, "verdict": review["verdict"]}:
        raise ValueError("cycle state review binding mismatch")
    if state["transition"] != {
        "ledger_path": "cycle/TRANSITION_LEDGER.jsonl",
        "ledger_sha256": transition_digest,
        "last_row_sha256": last_row_sha,
    }:
        raise ValueError("cycle state transition binding mismatch")
    expected_working = {
        "candidate_id": candidate["candidate_id"],
        "payload_manifest_path": "PAYLOAD_CONTENTS_SHA256.txt",
        "payload_manifest_sha256": sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt"),
        "delta_manifest_path": "delta/DELTA_MANIFEST.csv",
        "delta_manifest_sha256": sha256_file(root / "delta/DELTA_MANIFEST.csv"),
        "source_tree_delta_manifest_path": "delta/SOURCE_TREE_DELTA_MANIFEST.csv",
        "source_tree_delta_manifest_sha256": sha256_file(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"),
        "governance_manifest_path": "governance/GOVERNANCE_CONTENTS_SHA256.txt",
        "governance_manifest_sha256": governance_digest,
    }
    if state["working_candidate"] != expected_working:
        raise ValueError("cycle state working-candidate digest mismatch")
    lineage = {"filename": candidate["lineage_parent_bundle"], "sha256": candidate["lineage_parent_sha256"]}
    if state["lineage_parent"] != lineage:
        raise ValueError("state/candidate lineage mismatch")
    if phase == "GO":
        if not state["go"]["eligible"] or state["go"]["blocking_reason"] != "none":
            raise ValueError("GO phase lacks active GO state")
    elif state["go"]["eligible"]:
        raise ValueError("non-GO phase crosses GO boundary")
    last = transition_records[-1]
    allowed_transitions = rule["last_transition"] if isinstance(rule["last_transition"], set) else {rule["last_transition"]}
    if (last["from_phase"], last["to_phase"]) not in allowed_transitions:
        raise ValueError("last transition does not materialize active phase")
    if last["sequence"] != state["transition_sequence"] or last["candidate_id"] != candidate["candidate_id"]:
        raise ValueError("state/transition binding mismatch")
    upstream = load_json_strict(root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
    expected_upstream = {
        "canonical_lock_status": upstream["refresh_attempt_status"],
        "policy": "governance/UPSTREAM_RELEASE_POLICY.json",
        "required_dependencies": ["AF", "AFC", "GM", "AOD"],
        "source_registry": "governance/REPOSITORY_RELEASE_SOURCES.json",
    }
    if state["upstream_release_state"] != expected_upstream:
        raise ValueError("phase state upstream refresh binding mismatch")
    expected_r08 = transition_records[-1]["r08_status"]
    validate_workflow_state(
        root / "BUNDLE_WORKFLOW.md",
        phase=phase, candidate_version=candidate["version"], candidate_status=candidate["status"],
        release_status=state["release"]["status"], counts=feedback_counts, verdict=review["verdict"],
        go_eligible=(phase == "GO"), r08_status=expected_r08, next_transitions=rule["next"],
    )
    return state



def _version_milestone(version: str) -> str | None:
    import re
    match = re.search(r"r(\d+)", version)
    if not match:
        return None
    return f"R{int(match.group(1))}"


def _validate_authoring_rebaseline_policy(root: Path, state: dict[str, Any], candidate: dict[str, Any], stable_record: dict[str, Any], transition_records: list[dict[str, Any]]) -> None:
    if state["active_phase"] != "AUTHORING":
        return
    if state["release"]["stable_version"] != stable_record["version"]:
        raise ValueError("AUTHORING release stable-version does not match embedded stable baseline")
    goal = load_json_strict(root / "cycle/ACTIVE_GOAL.json")
    validate_schema(goal, root / "cycle/schemas/active-goal.schema.json", label="active goal")
    expected_milestone = _version_milestone(candidate["version"])
    if expected_milestone and goal["milestone_id"] != expected_milestone:
        raise ValueError("AUTHORING active goal milestone does not match candidate version")
    last = transition_records[-1]
    if last["from_phase"] == "GO" and last["to_phase"] == "AUTHORING":
        parent = last["parent_bundle"]
        if stable_record["source_bundle_filename"] != parent["filename"] or stable_record["source_bundle_sha256"] != parent["sha256"]:
            raise ValueError("GO-to-AUTHORING successor did not promote the parent GO bundle as the stable baseline")
        if candidate["version"] == stable_record["version"]:
            raise ValueError("GO-to-AUTHORING successor did not seed a new working candidate version")


def _validate_go_decision(
    root: Path, candidate: dict[str, Any], review: dict[str, Any], review_path: str, review_digest: str,
    feedback_digest: str, feedback_counts: dict[str, int], transition_records: list[dict[str, Any]],
    state: dict[str, Any],
) -> str:
    path = root / "cycle/GO_DECISION.json"
    if not path.is_file():
        raise ValueError("GO phase missing GO decision record")
    decision = load_json_strict(path)
    validate_schema(decision, root / "governance/schemas/go-decision.schema.json", label="GO decision")
    if decision["record_scope"] != "bundle_instance" or decision["candidate_version"] != candidate["version"]:
        raise ValueError("GO decision candidate/scope mismatch")
    if decision["candidate_payload_manifest_sha256"] != sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt"):
        raise ValueError("GO decision payload binding mismatch")
    if decision["feedback_ledger_sha256"] != feedback_digest:
        raise ValueError("GO decision feedback binding mismatch")
    if decision["review_record_path"] != review_path or decision["review_record_sha256"] != review_digest:
        raise ValueError("GO decision review binding mismatch")
    if decision["authority_class"] not in {"project_owner", "designated_reviewer"} or not decision["authority_id"]:
        raise ValueError("GO decision authority mismatch")
    if review["verdict"] != "GO_RECOMMENDED" or not review["go_recommended"]:
        raise ValueError("GO decision lacks GO-recommended review")
    if any(feedback_counts[key] for key in ("open_blocking", "open_nonblocking", "applied_unverified")):
        raise ValueError("GO decision has unresolved feedback")
    digest = sha256_file(path)
    if transition_records[-1]["bound_digests"].get("go_decision_sha256") != digest:
        raise ValueError("GO transition decision binding mismatch")
    if state["go"].get("decision_path") != "cycle/GO_DECISION.json" or state["go"].get("decision_sha256") != digest:
        raise ValueError("GO state decision binding mismatch")
    return digest

def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    base._exact_top_level(root)
    base._no_forbidden_files(root)
    expected_bundle = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "BUNDLE_CONTENTS_SHA256.txt"
    }
    base.validate_sha_manifest(root, root / "BUNDLE_CONTENTS_SHA256.txt", expected_paths=expected_bundle)
    payload_rows, _ = base._validate_payload_manifests(root)
    stable_record, stable_rows = base._validate_stable(root)
    delta_summary, _ = base._validate_delta(root, stable_rows, payload_rows)
    base._validate_source_delta(root, delta_summary)
    base._validate_source_templates(root)
    _, governance_digest = base._validate_governance(root)
    candidate = base._validate_candidate(root, stable_record, delta_summary)

    candidate_digest = sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt")
    delta_digest = sha256_file(root / "delta/DELTA_MANIFEST.csv")
    source_delta_digest = sha256_file(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv")
    authoring, authoring_digest = base._validate_authoring(root, candidate_digest, delta_digest, source_delta_digest, governance_digest)
    feedback_rows, feedback_digest, feedback_counts = base._validate_feedback(root, candidate_digest)

    state_preview = load_json_strict(root / "cycle/CYCLE_STATE.json")
    phase = state_preview["active_phase"]
    if phase not in PHASE_RULES:
        raise ValueError(f"phase-only validator does not admit active phase: {phase}")
    rule = PHASE_RULES[phase]

    review_expected = {
        "candidate_payload_manifest_sha256": candidate_digest,
        "delta_manifest_sha256": delta_digest,
        "source_tree_delta_manifest_sha256": source_delta_digest,
        "governance_manifest_sha256": governance_digest,
        "feedback_ledger_sha256": feedback_digest,
        "authoring_report_sha256": authoring_digest,
        "tests_sha256": sha256_file(root / "tests.txt"),
        "main_pdf_sha256": sha256_file(root / "main.pdf"),
        "manual_pdf_sha256": sha256_file(root / "manual.pdf"),
        "manual2_pdf_sha256": sha256_file(root / "manual-2.pdf"),
    }
    if rule["review_must_bind_current_feedback"]:
        review, review_digest, review_path, outcome = base._validate_review(root, review_expected, feedback_rows, feedback_counts)
    else:
        review, review_digest, review_path = _load_review_identity(root)
        upstream = load_json_strict(root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
        outcome = derive_review_outcome(
            feedback_counts,
            reviewer_class=review["reviewer_class"],
            upstream_ready=upstream_lock_ready(upstream),
        )

    transition_expected = {
        "candidate_payload_manifest_sha256": candidate_digest,
        "delta_manifest_sha256": delta_digest,
        "source_tree_delta_manifest_sha256": source_delta_digest,
        "governance_manifest_sha256": governance_digest,
        "feedback_ledger_sha256": feedback_digest,
        "authoring_report_sha256": authoring_digest,
        "review_record_sha256": review_digest,
    }
    if phase == "GO":
        go_path = root / "cycle/GO_DECISION.json"
        if not go_path.is_file():
            raise ValueError("GO phase missing GO decision record")
        transition_expected["go_decision_sha256"] = sha256_file(go_path)
    records, transition_digest, last_row_sha = base._validate_transition(
        root,
        transition_expected,
        candidate["lineage_parent_bundle"],
        candidate["lineage_parent_sha256"],
        feedback_counts,
        outcome,
    )
    state = _validate_state(
        root,
        candidate,
        feedback_counts,
        review_path,
        review_digest,
        review,
        records,
        transition_digest,
        last_row_sha,
        governance_digest,
    )
    _validate_authoring_rebaseline_policy(root, state, candidate, stable_record, records)
    if state["active_phase"] == "GO":
        _validate_go_decision(
            root, candidate, review, review_path, review_digest, feedback_digest,
            feedback_counts, records, state,
        )
    base._validate_phase_tooling(root, state["active_phase"])

    base._validate_pdf_freeze_policy(root)
    return {
        "status": "passed",
        "active_phase": state["active_phase"],
        "candidate_version": candidate["version"],
        "payload_files": len(payload_rows),
        "bundle_files": len(expected_bundle) + 1,
        "tests": int(authoring["test_count"]),
        "open_blocking_feedback": feedback_counts["open_blocking"],
        "applied_unverified_feedback": feedback_counts["applied_unverified"],
        "review_verdict": review["verdict"],
        "r08_status": records[-1]["r08_status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
