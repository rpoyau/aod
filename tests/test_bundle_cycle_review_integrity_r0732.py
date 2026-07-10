from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from bundle_common import validate_schema
from review_common import (
    derive_review_outcome,
    effective_feedback_rows,
    feedback_counts,
    finding_sets,
    reviewer_can_verify,
)


def event(fid: str, status: str, *, blocking: str = "yes", evidence: str = "e") -> dict[str, str]:
    return {
        "finding_id": fid,
        "source_release": "review",
        "severity": "HIGH",
        "blocking": blocking,
        "status": status,
        "summary": "summary",
        "required_action": "action",
        "evidence_path": evidence,
    }


def test_self_review_cannot_verify_close_findings():
    assert not reviewer_can_verify("self_review")
    assert reviewer_can_verify("independent_bundle_reviewer")
    assert reviewer_can_verify("project_owner")


def test_feedback_status_is_append_only_event_state():
    rows = [event("A", "OPEN"), event("A", "APPLIED_UNVERIFIED"), event("A", "VERIFIED_CLOSED")]
    effective = effective_feedback_rows(rows)
    assert len(effective) == 1
    assert effective[0]["status"] == "VERIFIED_CLOSED"
    assert feedback_counts(rows)["verified_closed"] == 1
    assert finding_sets(rows)["closed"] == ["A"]


def test_feedback_closed_state_is_terminal():
    with pytest.raises(ValueError, match="illegal feedback status transition"):
        effective_feedback_rows([event("A", "OPEN"), event("A", "VERIFIED_CLOSED"), event("A", "OPEN")])


def test_feedback_immutable_finding_fields_cannot_be_rewritten():
    first = event("A", "OPEN")
    second = event("A", "APPLIED_UNVERIFIED")
    second["summary"] = "rewritten"
    with pytest.raises(ValueError, match="immutable-field mutation"):
        effective_feedback_rows([first, second])


def test_review_submission_and_record_use_the_same_check_shape():
    template_schema = json.loads((ROOT / "cycle/schemas/review-template.schema.json").read_text())
    record_schema = json.loads((ROOT / "cycle/schemas/review-record.schema.json").read_text())
    assert template_schema["properties"]["checks"]["items"] == record_schema["properties"]["checks"]["items"]
    submission = json.loads((ROOT / "governance/reviews/REVIEW_SUBMISSION.template.json").read_text())
    validate_schema(submission, ROOT / "cycle/schemas/review-template.schema.json")
    assert isinstance(submission["checks"][0], dict)


def test_authoring_to_review_preserves_external_checks_and_rejects_self_review():
    text = (TOOLS / "run_bundle_transition.py").read_text()
    assert 'checks = review_submission["checks"]' in text
    assert 'AUTHORING-to-REVIEW requires an independent reviewer class' in text
    assert 'reviewer class is not authorized to verify-close findings' in text


def test_complete_validator_is_phase_aware_for_authoring_and_feedback():
    text = (TOOLS / "validate_complete_bundle.py").read_text()
    assert 'if phase != "REVIEW"' in text
    assert 'return validate_phase_bundle.validate(root)' in text


def test_go_path_allows_hydrogen_open_state_in_transition_schema():
    schema = json.loads((ROOT / "cycle/schemas/transition-record.schema.json").read_text())
    assert set(schema["properties"]["r08_status"]["enum"]) == {"BLOCKED", "OPEN"}
    outcome = derive_review_outcome(
        feedback_counts([]),
        reviewer_class="independent_bundle_reviewer",
        upstream_ready=True,
    )
    assert outcome["verdict"] == "GO_RECOMMENDED"
    assert outcome["r08_status"] == "BLOCKED"
    assert (TOOLS / "run_review_go_transition.py").is_file()
    assert '"r08_status": "OPEN"' in (TOOLS / "run_review_go_transition.py").read_text()


def test_review_to_feedback_appends_instead_of_rebuilding_prior_rows():
    text = (TOOLS / "run_review_feedback_transition.py").read_text()
    assert "Finding verification is an appended event; prior rows are immutable." in text
    assert "existing + stream.getvalue().encode" in text
    assert "source_rows" not in text
