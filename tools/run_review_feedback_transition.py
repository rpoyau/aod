#!/usr/bin/env python3
"""Append independent review findings/events and emit one REVIEW -> FEEDBACK bundle."""
from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

try:
    from bundle_common import (
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        resolve_inside,
        row_sha256,
        sha256_bytes,
        sha256_file,
        validate_schema,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import (
        derive_review_outcome,
        effective_feedback_rows,
        feedback_counts,
        finding_sets,
        reviewer_can_verify,
        resolution_authorized,
        update_workflow_state,
        upstream_lock_ready,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bundle_common import (  # type: ignore
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        resolve_inside,
        row_sha256,
        sha256_bytes,
        sha256_file,
        validate_schema,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import (  # type: ignore
        derive_review_outcome,
        effective_feedback_rows,
        feedback_counts,
        finding_sets,
        reviewer_can_verify,
        resolution_authorized,
        update_workflow_state,
        upstream_lock_ready,
    )

FEEDBACK_HEADER = [
    "sequence", "finding_id", "source_release", "severity", "blocking", "status", "summary",
    "required_action", "evidence_path", "evidence_sha256", "candidate_payload_sha256",
    "previous_row_sha256", "row_sha256",
]
FINDING_INPUT_HEADER = [
    "sequence", "finding_id", "source_release", "severity", "blocking", "status", "summary",
    "required_action", "evidence_path",
]


def _read_csv(path: Path, expected: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected:
            raise ValueError(f"CSV header mismatch: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"malformed CSV: {path}")
    return rows


def _append_rows_bytes(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    existing = path.read_bytes()
    if not existing.endswith(b"\n"):
        raise ValueError("feedback ledger is noncanonical")
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=FEEDBACK_HEADER, lineterminator="\n")
    writer.writerows(rows)
    path.write_bytes(existing + stream.getvalue().encode("utf-8"))


# Finding verification is an appended event; prior rows are immutable.
def _append_feedback(
    root: Path,
    submission: dict[str, Any],
    findings_path: Path,
    submission_snapshot_path: str,
) -> tuple[list[dict[str, str]], str]:
    ledger_path = root / "cycle/FEEDBACK_LEDGER.csv"
    current = _read_csv(ledger_path, FEEDBACK_HEADER)
    current_effective = {row["finding_id"]: row for row in effective_feedback_rows(current)}
    new_findings = _read_csv(findings_path, FINDING_INPUT_HEADER)
    if submission["closed_findings"] and not reviewer_can_verify(submission["reviewer_class"]):
        raise ValueError("reviewer class is not authorized to verify-close findings")
    resolution_ids = [row["finding_id"] for row in submission.get("finding_resolutions", [])]
    if len(resolution_ids) != len(set(resolution_ids)):
        raise ValueError("duplicate finding resolution")
    if set(submission["closed_findings"]) != {row["finding_id"] for row in submission.get("finding_resolutions", []) if row["status"] in {"VERIFIED_CLOSED", "NOT_APPLICABLE_VERIFIED"}}:
        raise ValueError("closed_findings must match verified/not-applicable resolutions")

    seen_new: set[str] = set()
    for finding in new_findings:
        fid = finding["finding_id"]
        if fid in current_effective or fid in seen_new:
            raise ValueError(f"duplicate review finding ID: {fid}")
        seen_new.add(fid)
        if finding["status"] not in {"OPEN", "DISPUTED_OPEN"}:
            raise ValueError("new review findings must enter OPEN or DISPUTED_OPEN")

    candidate_digest = sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt")
    previous = current[-1]["row_sha256"] if current else ""
    sequence = len(current)
    appended: list[dict[str, str]] = []

    # New findings are appended as new events.
    for source in new_findings:
        sequence += 1
        evidence = resolve_inside(root, source["evidence_path"])
        if not evidence.is_file():
            raise ValueError(f"review evidence missing: {source['evidence_path']}")
        row = {
            **source,
            "sequence": str(sequence),
            "evidence_sha256": sha256_file(evidence),
            "candidate_payload_sha256": candidate_digest,
            "previous_row_sha256": previous,
            "row_sha256": "",
        }
        row["row_sha256"] = row_sha256([row[column] for column in FEEDBACK_HEADER[:-1]])
        previous = row["row_sha256"]
        appended.append(row)
        current_effective[row["finding_id"]] = row

    # Finding resolution is an appended event; prior rows are immutable.
    for resolution in submission.get("finding_resolutions", []):
        finding_id = resolution["finding_id"]
        if finding_id not in current_effective:
            raise ValueError(f"review resolves unknown finding: {finding_id}")
        prior = current_effective[finding_id]
        if prior["status"] not in {"OPEN", "DISPUTED_OPEN", "APPLIED_UNVERIFIED"}:
            raise ValueError(f"review resolves finding in invalid state: {finding_id}")
        if not resolution_authorized(submission["reviewer_class"], resolution["status"], resolution.get("authority_id")):
            raise ValueError(f"reviewer authority does not permit {resolution['status']}: {finding_id}")
        evidence = resolve_inside(root, resolution["evidence_path"])
        if not evidence.is_file():
            raise ValueError(f"resolution evidence missing: {resolution['evidence_path']}")
        sequence += 1
        row = {
            "sequence": str(sequence),
            "finding_id": finding_id,
            "source_release": prior["source_release"],
            "severity": prior["severity"],
            "blocking": prior["blocking"],
            "status": resolution["status"],
            "summary": prior["summary"],
            "required_action": prior["required_action"],
            "evidence_path": resolution["evidence_path"],
            "evidence_sha256": sha256_file(evidence),
            "candidate_payload_sha256": candidate_digest,
            "previous_row_sha256": previous,
            "row_sha256": "",
        }
        row["row_sha256"] = row_sha256([row[column] for column in FEEDBACK_HEADER[:-1]])
        previous = row["row_sha256"]
        appended.append(row)
        current_effective[finding_id] = row

    _append_rows_bytes(ledger_path, appended)
    rows = _read_csv(ledger_path, FEEDBACK_HEADER)
    # This also validates immutable finding fields and legal status transitions.
    effective_feedback_rows(rows)
    return rows, sha256_file(ledger_path)


def _review_record(root: Path, submission: dict[str, Any], rows: list[dict[str, str]], feedback_digest: str) -> tuple[dict[str, Any], Path, str, dict[str, Any]]:
    sets = finding_sets(rows)
    if submission["open_findings"] != sets["open"]:
        raise ValueError("review open findings do not match admitted ledger")
    if set(submission["closed_findings"]) - set(sets["closed"]):
        raise ValueError("review closes findings not verified closed")
    counts = feedback_counts(rows)
    upstream = load_json_strict(root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
    outcome = derive_review_outcome(counts, reviewer_class=submission["reviewer_class"], upstream_ready=upstream_lock_ready(upstream))
    if submission["verdict"] != outcome["verdict"] or submission["go_recommended"] != outcome["go_recommended"]:
        raise ValueError("review verdict is not derived from admitted findings")

    candidate = load_json_strict(root / "candidate/WORKING_CANDIDATE.json")
    authoring_path = root / "cycle/AUTHORING_REPORT.json"
    review = {
        "schema_version": "3.1",
        "record_scope": "bundle_instance",
        "review_id": submission["review_id"],
        "candidate_version": candidate["version"],
        "reviewer_class": submission["reviewer_class"],
        "review_scope": submission["review_scope"],
        "governing_constraints": submission["governing_constraints"],
        "bound_digests": {
            "candidate_payload_manifest_sha256": sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt"),
            "delta_manifest_sha256": sha256_file(root / "delta/DELTA_MANIFEST.csv"),
            "source_tree_delta_manifest_sha256": sha256_file(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"),
            "governance_manifest_sha256": sha256_file(root / "governance/GOVERNANCE_CONTENTS_SHA256.txt"),
            "feedback_ledger_sha256": feedback_digest,
            "authoring_report_sha256": sha256_file(authoring_path),
            "tests_sha256": sha256_file(root / "tests.txt"),
            "main_pdf_sha256": sha256_file(root / "main.pdf"),
            "manual_pdf_sha256": sha256_file(root / "manual.pdf"),
            "manual2_pdf_sha256": sha256_file(root / "manual-2.pdf"),
        },
        "checks": submission["checks"],
        "closed_findings": submission["closed_findings"],
        "open_findings": submission["open_findings"],
        "counterfactuals": submission["counterfactuals"],
        "falsification_conditions": submission["falsification_conditions"],
        "verdict": outcome["verdict"],
        "verdict_reason": submission["verdict_reason"],
        "go_recommended": outcome["go_recommended"],
        "r08_status": outcome["r08_status"],
        "provenance": [
            "PAYLOAD_CONTENTS_SHA256.txt", "delta/DELTA_MANIFEST.csv", "delta/SOURCE_TREE_DELTA_MANIFEST.csv",
            "governance/GOVERNANCE_CONTENTS_SHA256.txt", "cycle/FEEDBACK_LEDGER.csv",
            "cycle/AUTHORING_REPORT.json", "tests.txt",
        ],
    }
    review_schema = load_json_strict(root / "cycle/schemas/review-record.schema.json")
    if "finding_resolutions" in review_schema.get("properties", {}):
        review["finding_resolutions"] = submission.get("finding_resolutions", [])
    validate_schema(review, root / "cycle/schemas/review-record.schema.json", label="review record")
    path = root / f"governance/reviews/{submission['review_id']}.json"
    write_canonical_json(path, review)
    digest = sha256_file(path)
    index_path = root / "governance/reviews/REVIEW_INDEX.json"
    index = load_json_strict(index_path)
    old = {"path": index["canonical_review_path"], "sha256": index["canonical_review_sha256"], "status": "historical_noncanonical"}
    history = index["historical_reviews"]
    if old not in history:
        history.append(old)
    index["canonical_review_path"] = path.relative_to(root).as_posix()
    index["canonical_review_sha256"] = digest
    write_canonical_json(index_path, index)
    return review, path, digest, outcome


def build(parent_zip: Path, output_zip: Path, submission_path: Path, findings_path: Path) -> dict[str, Any]:
    parent_zip = parent_zip.resolve()
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        parent = work / "parent"
        successor = work / "successor"
        extract_zip_safe(parent_zip, parent)
        parent_validator = parent / "tools/validate_complete_bundle.py"
        completed = subprocess.run([sys.executable, str(parent_validator), str(parent)], check=False, capture_output=True, text=True)
        if completed.returncode:
            raise ValueError(f"parent bundle validation failed: {completed.stdout}{completed.stderr}")
        shutil.copytree(parent, successor)

        submission = load_json_strict(submission_path.resolve())
        validate_schema(submission, successor / "cycle/schemas/review-template.schema.json", label="external review submission")
        if submission["record_scope"] != "source_template":
            raise ValueError("review submission record scope mismatch")
        candidate = load_json_strict(successor / "candidate/WORKING_CANDIDATE.json")
        if submission["candidate_version"] != candidate["version"]:
            raise ValueError("review submission candidate version mismatch")

        submission_rel = f"governance/reviews/submissions/{submission['review_id']}.submission.json"
        write_canonical_json(successor / submission_rel, submission)
        rows, feedback_digest = _append_feedback(successor, submission, findings_path.resolve(), submission_rel)
        review, review_path, review_digest, outcome = _review_record(successor, submission, rows, feedback_digest)
        counts = feedback_counts(rows)

        parent_state = load_json_strict(parent / "cycle/CYCLE_STATE.json")
        if parent_state["active_phase"] != "REVIEW":
            raise ValueError("parent is not in REVIEW")
        if outcome["go_eligible"]:
            raise ValueError("GO-eligible review must transition REVIEW -> GO, not REVIEW -> FEEDBACK")
        parent_ledger = (parent / "cycle/TRANSITION_LEDGER.jsonl").read_bytes()
        records = [json.loads(line) for line in parent_ledger.decode("utf-8").splitlines() if line]
        previous = records[-1]["row_sha256"]
        payload = {
            "schema_version": "3.1",
            "sequence": parent_state["transition_sequence"] + 1,
            "transition_id": f"transition_{candidate['version']}_review_to_feedback",
            "transition_class": "ordinary_parent_prefix_plus_one",
            "parent_bundle": {"filename": parent_zip.name, "sha256": sha256_file(parent_zip)},
            "predecessor_state": {"path": "cycle/CYCLE_STATE.json", "sha256": sha256_file(parent / "cycle/CYCLE_STATE.json"), "transition_sequence": parent_state["transition_sequence"]},
            "from_phase": "REVIEW", "to_phase": "FEEDBACK", "candidate_id": candidate["candidate_id"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": sha256_file(successor / "PAYLOAD_CONTENTS_SHA256.txt"),
                "delta_manifest_sha256": sha256_file(successor / "delta/DELTA_MANIFEST.csv"),
                "source_tree_delta_manifest_sha256": sha256_file(successor / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"),
                "governance_manifest_sha256": sha256_file(successor / "governance/GOVERNANCE_CONTENTS_SHA256.txt"),
                "feedback_ledger_sha256": feedback_digest,
                "authoring_report_sha256": sha256_file(successor / "cycle/AUTHORING_REPORT.json"),
                "review_record_sha256": review_digest,
            },
            "open_blocking_feedback": counts["open_blocking"], "go_eligible": False, "r08_status": "BLOCKED",
            "recording_semantics": "content_addressed_no_wall_clock", "previous_row_sha256": previous,
        }
        transition = {**payload, "row_sha256": sha256_bytes(canonical_json_bytes(payload))}
        ledger_path = successor / "cycle/TRANSITION_LEDGER.jsonl"
        ledger_path.write_bytes(parent_ledger + canonical_json_bytes(transition))

        candidate["status"] = "feedback_candidate"
        candidate["lineage_parent_bundle"] = parent_zip.name
        candidate["lineage_parent_sha256"] = sha256_file(parent_zip)
        write_canonical_json(successor / "candidate/WORKING_CANDIDATE.json", candidate)

        state = load_json_strict(successor / "cycle/CYCLE_STATE.json")
        state["active_phase"] = "FEEDBACK"; state["last_completed_phase"] = "REVIEW"
        state["lineage_parent"] = {"filename": parent_zip.name, "sha256": sha256_file(parent_zip)}
        state["release"]["status"] = "feedback_candidate"; state["feedback_counts"] = counts
        state["review"] = {"record_path": review_path.relative_to(successor).as_posix(), "record_sha256": review_digest, "verdict": review["verdict"]}
        state["transition_sequence"] = transition["sequence"]
        state["transition"] = {"ledger_path": "cycle/TRANSITION_LEDGER.jsonl", "ledger_sha256": sha256_file(ledger_path), "last_row_sha256": transition["row_sha256"]}
        state["go"]["eligible"] = False; state["go"]["blocking_reason"] = outcome["blocking_reason"]
        state["next_permitted_transitions"] = ["AUTHORING"]
        write_canonical_json(successor / "cycle/CYCLE_STATE.json", state)
        update_workflow_state(
            successor / "BUNDLE_WORKFLOW.md",
            phase="FEEDBACK",
            candidate_version=candidate["version"],
            candidate_status=candidate["status"],
            release_status=state["release"]["status"],
            counts=counts,
            verdict=review["verdict"],
            go_eligible=False,
            r08_status="BLOCKED",
            next_transitions=["AUTHORING"],
        )

        manifest = successor / "BUNDLE_CONTENTS_SHA256.txt"
        files = [path for path in successor.rglob("*") if path.is_file() and path.name != manifest.name]
        write_sha_manifest(manifest, files, successor)
        deterministic_zip_from_directory(successor, output_zip)

        emitted = work / "emitted"; extract_zip_safe(output_zip, emitted)
        emitted_validator = emitted / "tools/validate_complete_bundle.py"
        completed = subprocess.run([sys.executable, str(emitted_validator), str(emitted)], check=False, capture_output=True, text=True)
        if completed.returncode:
            raise ValueError(f"emitted FEEDBACK bundle validation failed: {completed.stdout}{completed.stderr}")
        report = json.loads(completed.stdout.strip().splitlines()[-1])
        return {**report, "output": str(output_zip), "sha256": sha256_file(output_zip), "transition_row_sha256": transition["row_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent_bundle", type=Path)
    parser.add_argument("output_bundle", type=Path)
    parser.add_argument("--review-submission", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.parent_bundle, args.output_bundle, args.review_submission, args.findings), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
