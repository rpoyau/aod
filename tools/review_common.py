#!/usr/bin/env python3
"""Shared, data-driven review/feedback state derivation for AOD cycle bundles."""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

from collections import OrderedDict
from typing import Any, Iterable

OPEN_STATUSES = {"OPEN", "DISPUTED_OPEN"}
CLOSED_STATUSES = {"VERIFIED_CLOSED", "NOT_APPLICABLE_VERIFIED"}
APPLIED_STATUS = "APPLIED_UNVERIFIED"
WAIVED_STATUS = "WAIVED_BY_AUTHORITY"
INDEPENDENT_REVIEWERS = {"independent_bundle_reviewer", "project_owner", "designated_reviewer"}
ALL_STATUSES = OPEN_STATUSES | CLOSED_STATUSES | {APPLIED_STATUS, WAIVED_STATUS}

# Fields which define the finding itself. Later append-only status events must
# preserve these values; evidence and candidate bindings may advance.
IMMUTABLE_FINDING_FIELDS = (
    "finding_id",
    "source_release",
    "severity",
    "blocking",
    "summary",
    "required_action",
)

# A closed finding is terminal. A regression is represented by a new finding
# rather than by rewriting or reopening the historical event chain.
ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"DISPUTED_OPEN", "APPLIED_UNVERIFIED", "VERIFIED_CLOSED", "NOT_APPLICABLE_VERIFIED", "WAIVED_BY_AUTHORITY"},
    "DISPUTED_OPEN": {"OPEN", "APPLIED_UNVERIFIED", "VERIFIED_CLOSED", "NOT_APPLICABLE_VERIFIED", "WAIVED_BY_AUTHORITY"},
    "APPLIED_UNVERIFIED": {"OPEN", "DISPUTED_OPEN", "VERIFIED_CLOSED", "NOT_APPLICABLE_VERIFIED", "WAIVED_BY_AUTHORITY"},
    "VERIFIED_CLOSED": set(),
    "NOT_APPLICABLE_VERIFIED": set(),
    "WAIVED_BY_AUTHORITY": set(),
}


def reviewer_can_verify(reviewer_class: str) -> bool:
    """Return whether a reviewer may verify-close findings."""
    return reviewer_class in INDEPENDENT_REVIEWERS


def effective_feedback_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Collapse an append-only feedback event ledger to its latest state.

    Output order is the first-appearance order of each finding, while the row
    value is the latest event for that finding.
    """
    latest: "OrderedDict[str, dict[str, str]]" = OrderedDict()
    immutable: dict[str, dict[str, str]] = {}
    prior_status: dict[str, str] = {}
    for row in rows:
        finding_id = row["finding_id"]
        status = row["status"]
        if status not in ALL_STATUSES:
            raise ValueError(f"invalid feedback status: {status}")
        if finding_id not in immutable:
            immutable[finding_id] = {field: row.get(field, "") for field in IMMUTABLE_FINDING_FIELDS}
        else:
            for field, expected in immutable[finding_id].items():
                if row.get(field, "") != expected:
                    raise ValueError(f"feedback immutable-field mutation: {finding_id}:{field}")
            previous = prior_status[finding_id]
            if status not in ALLOWED_STATUS_TRANSITIONS[previous]:
                raise ValueError(f"illegal feedback status transition: {finding_id}: {previous} -> {status}")
        prior_status[finding_id] = status
        latest[finding_id] = row
    return list(latest.values())


def feedback_counts(rows: Iterable[dict[str, str]]) -> dict[str, int]:
    rows = effective_feedback_rows(rows)
    return {
        "open_blocking": sum(row["blocking"] == "yes" and row["status"] in OPEN_STATUSES for row in rows),
        "open_nonblocking": sum(row["blocking"] == "no" and row["status"] in OPEN_STATUSES for row in rows),
        "applied_unverified": sum(row["status"] == APPLIED_STATUS for row in rows),
        "verified_closed": sum(row["status"] in CLOSED_STATUSES for row in rows),
        "waived": sum(row["status"] == WAIVED_STATUS for row in rows),
    }


def finding_sets(rows: Iterable[dict[str, str]]) -> dict[str, list[str]]:
    rows = effective_feedback_rows(rows)
    return {
        "open": [row["finding_id"] for row in rows if row["status"] in OPEN_STATUSES],
        "closed": [row["finding_id"] for row in rows if row["status"] in CLOSED_STATUSES],
        "applied_unverified": [row["finding_id"] for row in rows if row["status"] == APPLIED_STATUS],
        "waived": [row["finding_id"] for row in rows if row["status"] == WAIVED_STATUS],
    }


def upstream_lock_ready(status: dict[str, Any]) -> bool:
    """Return whether upstream governance is admissible for review/GO.

    A resolved immutable lock is preferred. Under the rolling-latest policy, an
    explicit nonblocking fallback is also admissible; it never claims that the
    carried material is the current GitHub latest release.
    """
    mode = status.get("validation_mode")
    if mode == "strict_lock_when_present_or_explicit_nonblocking_fallback":
        return bool(status.get("go_eligible") and not status.get("go_blocking"))
    return bool(
        status.get("canonical_lock_present")
        and status.get("go_eligible")
        and mode == "strict_lock_or_exact_pending_state"
    )



def resolution_authorized(reviewer_class: str, status: str, authority_id: str | None) -> bool:
    """Validate AF-accurate closure/retirement authority."""
    if status == "VERIFIED_CLOSED":
        return reviewer_can_verify(reviewer_class)
    if status == "NOT_APPLICABLE_VERIFIED":
        return reviewer_can_verify(reviewer_class) and bool(authority_id)
    if status == "WAIVED_BY_AUTHORITY":
        return reviewer_class in {"project_owner", "designated_reviewer"} and bool(authority_id)
    return False


def render_workflow_state_block(
    *,
    phase: str,
    candidate_version: str,
    candidate_status: str,
    release_status: str,
    counts: dict[str, int],
    verdict: str,
    go_eligible: bool,
    r08_status: str,
    next_transitions: list[str],
) -> str:
    """Render the canonical human-readable state block from machine state."""
    return "\n".join([
        "<!-- AOD_STATE_BEGIN -->",
        f"Current state: {phase}.",
        f"Candidate version: {candidate_version}.",
        f"Candidate status: {candidate_status}.",
        f"Release status: {release_status}.",
        f"Review verdict: {verdict}.",
        f"Open blocking findings: {counts['open_blocking']}.",
        f"Open nonblocking findings: {counts['open_nonblocking']}.",
        f"Applied unverified findings: {counts['applied_unverified']}.",
        f"Verified/not-applicable closed findings: {counts['verified_closed']}.",
        f"Authority-waived findings: {counts['waived']}.",
        f"GO eligible: {str(go_eligible).lower()}.",
        f"Hydrogen r08: {r08_status}.",
        f"Next permitted transitions: {','.join(next_transitions)}.",
        "<!-- AOD_STATE_END -->",
    ]) + "\n"


def update_workflow_state(path, **values: Any) -> None:
    """Replace or append the canonical state block in BUNDLE_WORKFLOW.md."""
    from pathlib import Path
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    begin = "<!-- AOD_STATE_BEGIN -->"
    end = "<!-- AOD_STATE_END -->"
    block = render_workflow_state_block(**values)
    if begin in text and end in text:
        prefix = text[: text.index(begin)].rstrip()
        suffix = text[text.index(end) + len(end):].strip()
        text = prefix + "\n\n" + block
        if suffix:
            text += "\n" + suffix + "\n"
    else:
        marker = "Current state:"
        if marker in text:
            text = text[:text.index(marker)].rstrip()
        text = text.rstrip() + "\n\n" + block
    path.write_text(text, encoding="utf-8")


def validate_workflow_state(path, **values: Any) -> None:
    from pathlib import Path
    text = Path(path).read_text(encoding="utf-8")
    expected = render_workflow_state_block(**values).strip()
    if expected not in text:
        raise ValueError("bundle workflow state block mismatch")

def derive_review_outcome(
    counts: dict[str, int],
    *,
    reviewer_class: str,
    upstream_ready: bool,
) -> dict[str, Any]:
    if counts["open_blocking"] > 0 or counts["applied_unverified"] > 0:
        verdict = "HOLD"
    elif counts["open_nonblocking"] > 0:
        verdict = "FEEDBACK_REQUIRED"
    elif reviewer_class not in INDEPENDENT_REVIEWERS:
        verdict = "FEEDBACK_REQUIRED"
    elif not upstream_ready:
        verdict = "HOLD"
    else:
        verdict = "GO_RECOMMENDED"

    go_recommended = verdict == "GO_RECOMMENDED"
    return {
        "verdict": verdict,
        "go_recommended": go_recommended,
        # Hydrogen opens only after an authorized REVIEW -> GO transition.
        "r08_status": "BLOCKED",
        "go_eligible": go_recommended,
        "blocking_reason": "none" if go_recommended else _blocking_reason(counts, reviewer_class, upstream_ready),
    }


def _blocking_reason(counts: dict[str, int], reviewer_class: str, upstream_ready: bool) -> str:
    if counts["open_blocking"] > 0:
        return "open_blocking_feedback"
    if counts["applied_unverified"] > 0:
        return "applied_unverified_feedback"
    if counts["open_nonblocking"] > 0:
        return "open_nonblocking_feedback"
    if reviewer_class not in INDEPENDENT_REVIEWERS:
        return "independent_review_required"
    if not upstream_ready:
        return "upstream_refresh_policy_not_ready"
    return "unknown_blocking_state"
