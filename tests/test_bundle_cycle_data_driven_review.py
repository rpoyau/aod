from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from review_common import derive_review_outcome, feedback_counts, finding_sets


def row(fid: str, *, blocking: str, status: str) -> dict[str, str]:
    return {"finding_id": fid, "blocking": blocking, "status": status}


def test_multiple_blocking_findings_are_data_driven():
    rows = [row("A", blocking="yes", status="OPEN"), row("B", blocking="yes", status="DISPUTED_OPEN")]
    counts = feedback_counts(rows)
    assert counts["open_blocking"] == 2
    outcome = derive_review_outcome(counts, reviewer_class="independent_bundle_reviewer", upstream_ready=True)
    assert outcome["verdict"] == "HOLD"
    assert not outcome["go_recommended"]


def test_unknown_finding_ids_are_admitted_by_state_derivation():
    rows = [row("REVIEWER-NEW-UNREGISTERED-ID", blocking="no", status="OPEN")]
    assert finding_sets(rows)["open"] == ["REVIEWER-NEW-UNREGISTERED-ID"]
    outcome = derive_review_outcome(feedback_counts(rows), reviewer_class="independent_bundle_reviewer", upstream_ready=True)
    assert outcome["verdict"] == "FEEDBACK_REQUIRED"


def test_go_requires_zero_open_or_unverified_findings_and_independent_authority():
    empty = feedback_counts([])
    assert derive_review_outcome(empty, reviewer_class="independent_bundle_reviewer", upstream_ready=True)["verdict"] == "GO_RECOMMENDED"
    assert derive_review_outcome(empty, reviewer_class="self_review", upstream_ready=True)["verdict"] == "FEEDBACK_REQUIRED"
    unverified = feedback_counts([row("C", blocking="yes", status="APPLIED_UNVERIFIED")])
    assert derive_review_outcome(unverified, reviewer_class="independent_bundle_reviewer", upstream_ready=True)["verdict"] == "HOLD"


def test_authoring_builder_requires_external_reviewer_inputs():
    text = (TOOLS / "run_bundle_transition.py").read_text(encoding="utf-8")
    assert 'parser.add_argument("--review-submission"' in text
    assert 'parser.add_argument("--review-findings"' in text
    assert "WORKFLOW_HARDENING_REVIEW.template.json" not in text


def test_review_feedback_transition_command_exists_and_is_independent():
    text = (TOOLS / "run_review_feedback_transition.py").read_text(encoding="utf-8")
    assert "Append independent review findings" in text
    assert 'parser.add_argument("--review-submission"' in text
    assert 'parser.add_argument("--findings"' in text
    assert '"from_phase": "REVIEW"' in text
    assert '"to_phase": "FEEDBACK"' in text


def test_feedback_template_carries_new_authoring_findings_as_unverified():
    with (ROOT / "cycle/FEEDBACK_LEDGER.template.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    new = [item for item in rows if item["finding_id"] in {"R073-F006", "R073-F007", "R073-F008"}]
    assert len(new) == 3
    assert {item["status"] for item in new} == {"APPLIED_UNVERIFIED"}
