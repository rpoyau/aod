#!/usr/bin/env python3
"""Canonical validator for a complete AOD cycle bundle."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys

# Canonical tools must not mutate a clean bundle during execution.
sys.dont_write_bytecode = True
import tempfile
import zipfile
from pathlib import Path
from typing import Any

try:
    from bundle_common import (
        canonical_json_bytes,
        csv_rows_strict,
        directory_hash_map,
        extract_zip_safe,
        inspect_zip_path,
        load_json_strict,
        parse_sha_manifest,
        resolve_inside,
        row_sha256,
        safe_relative_path,
        sha256_bytes,
        sha256_file,
        validate_schema,
        validate_sha_manifest,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bundle_common import (  # type: ignore
        canonical_json_bytes,
        csv_rows_strict,
        directory_hash_map,
        extract_zip_safe,
        inspect_zip_path,
        load_json_strict,
        parse_sha_manifest,
        resolve_inside,
        row_sha256,
        safe_relative_path,
        sha256_bytes,
        sha256_file,
        validate_schema,
        validate_sha_manifest,
    )

from validate_upstream_release_lock import validate as validate_upstream_lock
from review_common import (derive_review_outcome, effective_feedback_rows, feedback_counts as derive_feedback_counts, finding_sets, reviewer_can_verify, upstream_lock_ready, validate_workflow_state)

TOP_LEVEL = {
    "BUNDLE_CONTENTS_SHA256.txt", "BUNDLE_WORKFLOW.md", "EXTERNAL_PAYLOADS_SHA256.txt",
    "GLOBAL_INSTRUCTIONS.json", "MANUAL_ARTIFACT_BASELINES_SHA256.txt", "MANUAL_II_ROADMAP.md",
    "MANUAL_I_ROADMAP.md", "PAYLOAD_CONTENTS_SHA256.txt", "candidate", "cycle", "delta",
    "external_payloads", "governance", "main.pdf", "manual-2.pdf", "manual.pdf", "patch_summary.txt",
    "source.zip", "stable", "tests.txt", "tools",
}
PAYLOAD_ROOT_FILES = {
    "EXTERNAL_PAYLOADS_SHA256.txt", "MANUAL_ARTIFACT_BASELINES_SHA256.txt", "MANUAL_II_ROADMAP.md",
    "MANUAL_I_ROADMAP.md", "main.pdf", "manual-2.pdf", "manual.pdf", "patch_summary.txt", "source.zip", "tests.txt",
}
FEEDBACK_HEADER = [
    "sequence", "finding_id", "source_release", "severity", "blocking", "status", "summary",
    "required_action", "evidence_path", "evidence_sha256", "candidate_payload_sha256",
    "previous_row_sha256", "row_sha256",
]
DELTA_HEADER = ["sequence", "operation", "path", "stable_sha256", "candidate_sha256", "source", "classification"]
SOURCE_DELTA_HEADER = ["sequence", "operation", "path", "stable_sha256", "candidate_sha256", "classification"]


def _exact_top_level(root: Path) -> None:
    actual = {path.name for path in root.iterdir()}
    if actual != TOP_LEVEL:
        raise ValueError(f"top-level bundle shape mismatch: missing={sorted(TOP_LEVEL-actual)}, extra={sorted(actual-TOP_LEVEL)}")


def _no_forbidden_files(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink forbidden: {path.relative_to(root)}")
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"} or path.name in {".pytest_cache", ".DS_Store"}:
            raise ValueError(f"generated cache forbidden: {path.relative_to(root)}")


def _validate_payload_manifests(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    external_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "external_payloads").rglob("*")
        if path.is_file()
    }
    external_rows = validate_sha_manifest(root, root / "EXTERNAL_PAYLOADS_SHA256.txt", expected_paths=external_paths)
    payload_expected = PAYLOAD_ROOT_FILES | external_paths
    payload_rows = validate_sha_manifest(root, root / "PAYLOAD_CONTENTS_SHA256.txt", expected_paths=payload_expected)
    if payload_rows["EXTERNAL_PAYLOADS_SHA256.txt"] != sha256_file(root / "EXTERNAL_PAYLOADS_SHA256.txt"):
        raise ValueError("payload does not bind external-payload manifest")
    return payload_rows, external_rows


def _validate_stable(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    stable_record = load_json_strict(root / "stable/STABLE_BASELINE.json")
    validate_schema(stable_record, root / "cycle/schemas/stable-baseline.schema.json", label="stable baseline")
    stable_payload = root / "stable/payload"
    expected = {path.relative_to(stable_payload).as_posix() for path in stable_payload.rglob("*") if path.is_file()}
    stable_rows = validate_sha_manifest(stable_payload, root / "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt", expected_paths=expected)
    if stable_record["payload_manifest_path"] != "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt":
        raise ValueError("stable manifest path mismatch")
    if stable_record["payload_manifest_sha256"] != sha256_file(root / stable_record["payload_manifest_path"]):
        raise ValueError("stable record manifest hash mismatch")
    return stable_record, stable_rows


def _expected_delta(stable: dict[str, str], candidate: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sequence = 1
    for path in sorted(set(stable) | set(candidate)):
        old, new = stable.get(path, ""), candidate.get(path, "")
        if old == new:
            continue
        operation = "add" if not old else "delete" if not new else "replace"
        rows.append({
            "sequence": str(sequence), "operation": operation, "path": path,
            "stable_sha256": old, "candidate_sha256": new,
            "source": f"root:{path}" if new else "delete", "classification": "release_infrastructure",
        })
        sequence += 1
    return rows


def _validate_delta(root: Path, stable_rows: dict[str, str], payload_rows: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    actual = csv_rows_strict(root / "delta/DELTA_MANIFEST.csv", DELTA_HEADER)
    expected = _expected_delta(stable_rows, payload_rows)
    if actual != expected:
        raise ValueError("payload delta manifest does not exactly represent stable-to-candidate changes")
    deletes = [row["path"] for row in expected if row["operation"] == "delete"]
    delete_text = (root / "delta/DELETE_PATHS.txt").read_text(encoding="utf-8").splitlines()
    if delete_text != deletes:
        raise ValueError("DELETE_PATHS does not match delta manifest")
    summary = load_json_strict(root / "delta/DELTA_SUMMARY.json")
    validate_schema(summary, root / "cycle/schemas/delta-summary.schema.json", label="delta summary")
    counts = {kind: sum(row["operation"] == kind for row in actual) for kind in ("add", "replace", "delete")}
    if summary["operation_counts"] != counts:
        raise ValueError("delta summary counts mismatch")
    if summary["delta_manifest_path"] != "delta/DELTA_MANIFEST.csv" or summary["delta_manifest_sha256"] != sha256_file(root / "delta/DELTA_MANIFEST.csv"):
        raise ValueError("delta summary manifest binding mismatch")
    if summary["candidate_payload_manifest_sha256"] != sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt"):
        raise ValueError("delta summary candidate binding mismatch")
    return summary, actual


def _source_map(zip_path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        seen: set[str] = set()
        for info in archive.infolist():
            if info.is_dir():
                continue
            safe_relative_path(info.filename)
            if info.filename in seen:
                raise ValueError(f"duplicate source ZIP member: {info.filename}")
            seen.add(info.filename)
            result[info.filename] = sha256_bytes(archive.read(info))
    return result


def _classify_source_delta_path(path: str) -> str:
    if path.startswith("manual-2/data/molecular/") or path in {
        "manual-2/scripts/build_molecular_matter_transition_atlas.py",
        "manual-2/sections/05_molecular_matter_transition_atlas.tex",
    }:
        return "scientific_source_authoring"
    if path.startswith("manual-2/data/foundation/") or path.startswith("manual-2/data/dec/") or path in {
        "manual-2/sections/00_dec_report_coordinate_overlay.tex",
        "manual/sections/00_foundation_doctrine_tick_tau_sparc.tex",
        "sections/03_foundation_doctrine_tick_tau_sparc.tex",
    }:
        return "release_planning_payload"
    return "release_infrastructure"


def _expected_source_delta(stable_source: dict[str, str], candidate_source: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sequence = 1
    for path in sorted(set(stable_source) | set(candidate_source)):
        old, new = stable_source.get(path, ""), candidate_source.get(path, "")
        if old == new:
            continue
        operation = "add" if not old else "delete" if not new else "modify"
        rows.append({
            "sequence": str(sequence), "operation": operation, "path": path,
            "stable_sha256": old, "candidate_sha256": new, "classification": _classify_source_delta_path(path),
        })
        sequence += 1
    return rows


def _validate_source_delta(root: Path, summary: dict[str, Any]) -> list[dict[str, str]]:
    inspect_zip_path(root / "source.zip", require_flat_root_ready=True)
    inspect_zip_path(root / "stable/payload/source.zip", require_flat_root_ready=True)
    candidate_source = _source_map(root / "source.zip")
    stable_source = _source_map(root / "stable/payload/source.zip")
    expected = _expected_source_delta(stable_source, candidate_source)
    actual = csv_rows_strict(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv", SOURCE_DELTA_HEADER)
    if actual != expected:
        raise ValueError("source-tree delta manifest mismatch")
    counts = {kind: sum(row["operation"] == kind for row in actual) for kind in ("add", "modify", "delete")}
    if summary["source_tree_operation_counts"] != counts:
        raise ValueError("source-tree delta summary counts mismatch")
    if summary["source_tree_delta_manifest_path"] != "delta/SOURCE_TREE_DELTA_MANIFEST.csv" or summary["source_tree_delta_manifest_sha256"] != sha256_file(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"):
        raise ValueError("source-tree delta digest binding mismatch")
    if "CANONICAL_VERSION.txt" not in candidate_source or "patch_summary.txt" not in candidate_source:
        raise ValueError("source archive is not Git-root ready")
    return actual


def _validate_source_templates(root: Path) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        extracted = Path(temporary)
        extract_zip_safe(root / "source.zip", extracted)
        _no_forbidden_files(extracted)
        records = [
            ("cycle/CYCLE_STATE.json", "cycle/schemas/cycle-state-template.schema.json"),
            ("cycle/ACTIVE_GOAL.json", "cycle/schemas/active-goal.schema.json"),
            ("cycle/CYCLE_POLICY.json", "cycle/schemas/cycle-policy.schema.json"),
            ("cycle/AUTHORING_REPORT.template.json", "cycle/schemas/authoring-report-template.schema.json"),
            ("cycle/history/HISTORY_STATUS.json", "cycle/schemas/history-status.schema.json"),
            ("governance/reviews/REVIEW_SUBMISSION.template.json", "cycle/schemas/review-template.schema.json"),
            ("governance/REPOSITORY_RELEASE_SOURCES.json", "governance/schemas/repository-release-sources.schema.json"),
            ("governance/UPSTREAM_RELEASE_POLICY.json", "governance/schemas/upstream-release-policy.schema.json"),
            ("governance/UPSTREAM_RELEASE_LOCK_STATUS.json", "governance/schemas/upstream-release-lock-status.schema.json"),
            ("governance/GLOBAL_INSTRUCTIONS.json", "governance/schemas/global-instructions.schema.json"),
            ("governance/IMPORT_MANIFEST.json", "cycle/schemas/governance-import.schema.json"),
        ]
        for record_path, schema_path in records:
            record = load_json_strict(extracted / record_path)
            validate_schema(record, extracted / schema_path, label=f"source template {record_path}")
        template_header = ["sequence", "finding_id", "source_release", "severity", "blocking", "status", "summary", "required_action", "evidence_path"]
        template_rows = csv_rows_strict(extracted / "cycle/FEEDBACK_LEDGER.template.csv", template_header)
        if not template_rows or any(row["candidate_payload_sha256"] if "candidate_payload_sha256" in row else False for row in template_rows):
            raise ValueError("source feedback template is malformed")
        state = load_json_strict(extracted / "cycle/CYCLE_STATE.json")
        if state["record_scope"] != "source_template":
            raise ValueError("source cycle state is not explicitly typed as a template")


def _validate_governance(root: Path) -> tuple[dict[str, Any], str]:
    pointer = load_json_strict(root / "GLOBAL_INSTRUCTIONS.json")
    if set(pointer) != {"schema_version", "canonical_path", "canonical_sha256", "instruction", "release_source_registry_path"}:
        raise ValueError("root governance pointer schema mismatch")
    canonical_path = resolve_inside(root, pointer["canonical_path"])
    if pointer["schema_version"] != "3.1" or sha256_file(canonical_path) != pointer["canonical_sha256"]:
        raise ValueError("root governance pointer hash mismatch")
    global_instructions = load_json_strict(canonical_path)
    validate_schema(global_instructions, root / "governance/schemas/global-instructions.schema.json", label="global instructions")
    for record, schema in [
        ("governance/REPOSITORY_RELEASE_SOURCES.json", "governance/schemas/repository-release-sources.schema.json"),
        ("governance/UPSTREAM_RELEASE_POLICY.json", "governance/schemas/upstream-release-policy.schema.json"),
        ("governance/UPSTREAM_RELEASE_LOCK_STATUS.json", "governance/schemas/upstream-release-lock-status.schema.json"),
        ("governance/IMPORT_MANIFEST.json", "cycle/schemas/governance-import.schema.json"),
    ]:
        validate_schema(load_json_strict(root / record), root / schema, label=record)
    governance_expected = {
        path.relative_to(root / "governance").as_posix()
        for path in (root / "governance").rglob("*")
        if path.is_file()
        and path.relative_to(root / "governance").parts[0] != "reviews"
        and path.name != "GOVERNANCE_CONTENTS_SHA256.txt"
    }
    validate_sha_manifest(root / "governance", root / "governance/GOVERNANCE_CONTENTS_SHA256.txt", expected_paths=governance_expected)
    governance_digest = sha256_file(root / "governance/GOVERNANCE_CONTENTS_SHA256.txt")
    validate_upstream_lock(root, allow_pending=True)
    return global_instructions, governance_digest


def _validate_candidate(root: Path, stable_record: dict[str, Any], delta_summary: dict[str, Any]) -> dict[str, Any]:
    candidate = load_json_strict(root / "candidate/WORKING_CANDIDATE.json")
    validate_schema(candidate, root / "cycle/schemas/candidate.schema.json", label="working candidate")
    if candidate["stable_baseline_version"] != stable_record["version"]:
        raise ValueError("candidate stable-baseline version mismatch")
    bindings = {
        "payload_manifest_sha256": sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt"),
        "delta_manifest_sha256": sha256_file(root / "delta/DELTA_MANIFEST.csv"),
        "source_tree_delta_manifest_sha256": sha256_file(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"),
    }
    for key, value in bindings.items():
        if candidate[key] != value:
            raise ValueError(f"candidate binding mismatch: {key}")
    if candidate["version"] != delta_summary["candidate_version"]:
        raise ValueError("candidate/delta version mismatch")
    return candidate


def _validate_authoring(root: Path, candidate_digest: str, delta_digest: str, source_delta_digest: str, governance_digest: str) -> tuple[dict[str, Any], str]:
    report_path = root / "cycle/AUTHORING_REPORT.json"
    report = load_json_strict(report_path)
    validate_schema(report, root / "cycle/schemas/authoring-report.schema.json", label="authoring report")
    expected = {
        "candidate_payload_manifest_sha256": candidate_digest,
        "delta_manifest_sha256": delta_digest,
        "source_tree_delta_manifest_sha256": source_delta_digest,
        "governance_manifest_sha256": governance_digest,
    }
    for key, value in expected.items():
        if report["bound_digests"][key] != value:
            raise ValueError(f"authoring report digest mismatch: {key}")
    tests_text = (root / report["tests_path"]).read_text(encoding="utf-8")
    match = re.search(r"(?<![0-9])([0-9]+)\s*/\s*\1\s+(?:tests?\s+)?passed", tests_text, re.IGNORECASE)
    if not match:
        raise ValueError("authoring report test evidence missing")
    observed = int(match.group(1))
    if report["test_count"] != observed:
        raise ValueError("authoring report test count mismatch")
    return report, sha256_file(report_path)

def _validate_feedback(root: Path, candidate_digest: str) -> tuple[list[dict[str, str]], str, dict[str, int]]:
    rows = csv_rows_strict(root / "cycle/FEEDBACK_LEDGER.csv", FEEDBACK_HEADER)
    previous = ""
    for expected_sequence, row in enumerate(rows, 1):
        if int(row["sequence"]) != expected_sequence:
            raise ValueError("feedback sequence is not contiguous")
        if row["blocking"] not in {"yes", "no"} or row["status"] not in {"OPEN", "APPLIED_UNVERIFIED", "VERIFIED_CLOSED", "NOT_APPLICABLE_VERIFIED", "WAIVED_BY_AUTHORITY", "DISPUTED_OPEN"}:
            raise ValueError("invalid feedback status")
        if not re.fullmatch(r"[0-9a-f]{64}", row["candidate_payload_sha256"]):
            raise ValueError("feedback candidate digest is malformed")
        if row["previous_row_sha256"] != previous:
            raise ValueError("feedback predecessor hash mismatch")
        evidence = resolve_inside(root, row["evidence_path"])
        snapshot = root / "cycle/evidence" / f"{row['evidence_sha256']}.bin"
        direct_ok = evidence.is_file() and sha256_file(evidence) == row["evidence_sha256"]
        snapshot_ok = snapshot.is_file() and sha256_file(snapshot) == row["evidence_sha256"]
        if not (direct_ok or snapshot_ok):
            raise ValueError(f"feedback evidence mismatch: {row['finding_id']}")
        values = [row[column] for column in FEEDBACK_HEADER[:-1]]
        computed = row_sha256(values)
        if row["row_sha256"] != computed:
            raise ValueError(f"feedback row hash mismatch: {row['finding_id']}")
        previous = computed
    # Enforce append-only event semantics, immutable finding fields, and legal
    # status transitions. Current counts are derived from each finding's latest event.
    effective_feedback_rows(rows)
    counts = derive_feedback_counts(rows)
    return rows, sha256_file(root / "cycle/FEEDBACK_LEDGER.csv"), counts

def _validate_review(
    root: Path,
    expected_digests: dict[str, str],
    feedback_rows: list[dict[str, str]],
    feedback_counts: dict[str, int],
) -> tuple[dict[str, Any], str, str, dict[str, Any]]:
    index = load_json_strict(root / "governance/reviews/REVIEW_INDEX.json")
    validate_schema(index, root / "cycle/schemas/review-index.schema.json", label="review index")
    review_path = resolve_inside(root, index["canonical_review_path"])
    review = load_json_strict(review_path)
    validate_schema(review, root / "cycle/schemas/review-record.schema.json", label="canonical review")
    review_digest = sha256_file(review_path)
    if index["canonical_review_sha256"] != review_digest:
        raise ValueError("review index digest mismatch")
    for historical in index["historical_reviews"]:
        path = resolve_inside(root, historical["path"])
        if not path.is_file() or sha256_file(path) != historical["sha256"]:
            raise ValueError("historical review index mismatch")
    for key, value in expected_digests.items():
        if review["bound_digests"][key] != value:
            raise ValueError(f"review digest mismatch: {key}")

    sets = finding_sets(feedback_rows)
    if review["open_findings"] != sets["open"]:
        raise ValueError("review open-finding list does not match active feedback ledger")
    invalid_closed = set(review["closed_findings"]) - set(sets["closed"])
    if invalid_closed:
        raise ValueError(f"review claims findings not verified closed: {sorted(invalid_closed)}")
    if review["closed_findings"] and not reviewer_can_verify(review["reviewer_class"]):
        raise ValueError("reviewer class is not authorized to verify-close findings")

    upstream_status = load_json_strict(root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
    outcome = derive_review_outcome(
        feedback_counts,
        reviewer_class=review["reviewer_class"],
        upstream_ready=upstream_lock_ready(upstream_status),
    )
    for key in ("verdict", "go_recommended", "r08_status"):
        if review[key] != outcome[key]:
            raise ValueError(f"review outcome mismatch: {key}")
    return review, review_digest, review_path.relative_to(root).as_posix(), outcome

def _load_json_line(line: str) -> dict[str, Any]:
    seen: set[str] = set()
    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate transition JSON key: {key}")
            result[key] = value
        return result
    return json.loads(line, object_pairs_hook=hook)


def _validate_transition(
    root: Path,
    expected_digests: dict[str, str],
    parent_filename: str,
    parent_sha: str,
    feedback_counts: dict[str, int],
    review_outcome: dict[str, Any],
) -> tuple[list[dict[str, Any]], str, str]:
    path = root / "cycle/TRANSITION_LEDGER.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not lines:
        raise ValueError("transition ledger is empty")
    records = [_load_json_line(line) for line in lines]
    for index, record in enumerate(records):
        validate_schema(record, root / "cycle/schemas/transition-record.schema.json", label=f"transition row {index+1}")
    first = records[0]
    if (
        first["sequence"] != 2
        or first["transition_class"] != "ledger_bootstrap_from_parent_state"
        or first["previous_row_sha256"] is not None
        or first["predecessor_state"]["transition_sequence"] != 1
    ):
        raise ValueError("transition ledger must begin with the one-time sequence-2 bootstrap row")
    previous: str | None = None
    for index, record in enumerate(records):
        if record["sequence"] != index + records[0]["sequence"]:
            raise ValueError("transition sequence is not contiguous")
        if record["predecessor_state"]["transition_sequence"] != record["sequence"] - 1:
            raise ValueError("transition predecessor-state sequence mismatch")
        if index and record["transition_class"] != "ordinary_parent_prefix_plus_one":
            raise ValueError("post-bootstrap transition row is not parent-prefix-plus-one")
        if record["from_phase"] == record["to_phase"]:
            raise ValueError("transition does not change phase")
        if record["previous_row_sha256"] != previous:
            raise ValueError("transition predecessor hash mismatch")
        payload = dict(record)
        declared = payload.pop("row_sha256")
        computed = sha256_bytes(canonical_json_bytes(payload))
        if declared != computed:
            raise ValueError("transition row hash mismatch")
        previous = computed
    last = records[-1]
    if last["parent_bundle"] != {"filename": parent_filename, "sha256": parent_sha}:
        raise ValueError("transition parent bundle binding mismatch")
    for key, value in expected_digests.items():
        if last["bound_digests"][key] != value:
            raise ValueError(f"transition digest mismatch: {key}")
    if last["open_blocking_feedback"] != feedback_counts["open_blocking"]:
        raise ValueError("transition open-blocker count mismatch")
    go_to_authoring_rebaseline = last["from_phase"] == "GO" and last["to_phase"] == "AUTHORING"
    expected_go = False if go_to_authoring_rebaseline else review_outcome["go_eligible"]
    expected_r08 = "OPEN" if (last["to_phase"] == "GO" and review_outcome["go_eligible"]) or go_to_authoring_rebaseline else review_outcome["r08_status"]
    if last["go_eligible"] != expected_go or last["r08_status"] != expected_r08:
        raise ValueError("transition review-outcome mismatch")
    return records, sha256_file(path), previous or ""

def _validate_state(
    root: Path,
    candidate: dict[str, Any],
    feedback_counts: dict[str, int],
    review_path: str,
    review_digest: str,
    review: dict[str, Any],
    review_outcome: dict[str, Any],
    transition_records: list[dict[str, Any]],
    transition_digest: str,
    last_row_sha: str,
    governance_digest: str,
) -> dict[str, Any]:
    state = load_json_strict(root / "cycle/CYCLE_STATE.json")
    validate_schema(state, root / "cycle/schemas/cycle-state.schema.json", label="cycle state")
    if state["release"]["working_version"] != candidate["version"] or state["working_candidate"]["candidate_id"] != candidate["candidate_id"]:
        raise ValueError("cycle state candidate mismatch")
    if candidate["status"] != "review_candidate" or state["release"]["status"] != "review_candidate":
        raise ValueError("REVIEW candidate/release status mismatch")
    if state["release"]["target_version"] != candidate["version"]:
        raise ValueError("REVIEW target-version mismatch")
    if review["candidate_version"] != candidate["version"]:
        raise ValueError("REVIEW record candidate-version mismatch")
    if review.get("candidate_id") != candidate["candidate_id"]:
        raise ValueError("REVIEW record candidate-id mismatch")
    if state["feedback_counts"] != feedback_counts:
        raise ValueError("cycle state feedback counts mismatch")
    if state["review"] != {"record_path": review_path, "record_sha256": review_digest, "verdict": review["verdict"]}:
        raise ValueError("cycle state review binding mismatch")
    if state["transition"]["ledger_sha256"] != transition_digest or state["transition"]["last_row_sha256"] != last_row_sha:
        raise ValueError("cycle state transition binding mismatch")
    last_transition = transition_records[-1]
    if state["transition_sequence"] != last_transition["sequence"]:
        raise ValueError("cycle state transition sequence mismatch")
    if (last_transition["from_phase"], last_transition["to_phase"]) != ("AUTHORING", "REVIEW"):
        raise ValueError("last transition does not materialize REVIEW from AUTHORING")
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
    if state["go"]["eligible"] != review_outcome["go_eligible"]:
        raise ValueError("cycle state GO eligibility mismatch")
    expected_next = ["GO"] if review_outcome["go_eligible"] else ["FEEDBACK"]
    if state["next_permitted_transitions"] != expected_next:
        raise ValueError("cycle state next-transition mismatch")
    upstream = load_json_strict(root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
    expected_upstream = {
        "canonical_lock_status": upstream["refresh_attempt_status"],
        "policy": "governance/UPSTREAM_RELEASE_POLICY.json",
        "required_dependencies": ["AF", "AFC", "GM", "AOD"],
        "source_registry": "governance/REPOSITORY_RELEASE_SOURCES.json",
    }
    if state["upstream_release_state"] != expected_upstream:
        raise ValueError("cycle state upstream refresh binding mismatch")
    validate_workflow_state(
        root / "BUNDLE_WORKFLOW.md",
        phase="REVIEW", candidate_version=candidate["version"], candidate_status=candidate["status"],
        release_status=state["release"]["status"], counts=feedback_counts, verdict=review["verdict"],
        go_eligible=review_outcome["go_eligible"], r08_status="BLOCKED", next_transitions=expected_next,
    )
    return state


def _manual2_rebuild_authorized(root: Path) -> bool:
    state = load_json_strict(root / "cycle/CYCLE_STATE.json")
    working = state.get("release", {}).get("working_version")
    base_required = {
        "manual-2/data/hydrogen_transition/hydrogen_transition_sadar_lock_manifest.json",
        "manual-2/data/hydrogen_transition/hydrogen_transition_native_packets.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_si_second_projection_packets.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_projection_index.csv",
        "manual-2/data/hydrogen_transition/tau_cycle_notation_registry.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_tau_notation_index.csv",
        "manual-2/data/hydrogen_transition/sadar_lock_matter_octave_atlas.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_counterfactual_audit.csv",
        "manual-2/sections/01_hydrogen_transition_sadar_lock_atlas.tex",
        "manual-2/scripts/build_hydrogen_transition_sadar_lock_atlas.py",
    }
    r10_required = {
        "manual-2/data/hydrogen_transition/hydrogen_transition_rd_rcd_packets.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_duonic_pressure_packets.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_sadar_flow_packets.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_phase_lock_packets.csv",
        "manual-2/data/hydrogen_transition/hydrogen_transition_native_materialization_manifest.json",
        "manual-2/data/hydrogen_transition/hydrogen_transition_native_materialization_counterfactual_audit.csv",
        "manual-2/scripts/materialize_hydrogen_transition_native_packets_r10.py",
        "tests/test_manual2_hydrogen_transition_native_packets_r10.py",
    }
    r13_1_required = {
        "manual-2/data/rest_cycle/rest_cycle_type_card.csv",
        "manual-2/data/rest_cycle/duon_current_flow_packets.csv",
        "manual-2/data/rest_cycle/sadar_temporal_flow_packets.csv",
        "manual-2/data/rest_cycle/relational_measurement_packets.csv",
        "manual-2/data/rest_cycle/matter_octave_rest_cycle_atlas.csv",
        "manual-2/data/rest_cycle/native_rest_cycle_relational_atlas_manifest.json",
        "manual-2/sections/01_native_rest_cycle_relational_atlas.tex",
        "manual-2/scripts/build_native_rest_cycle_relational_atlas.py",
        "tests/test_manual2_native_rest_cycle_relational_atlas.py",
    }
    r17_1_required = {
        "manual-2/data/circle_geometry/circle_relational_geometry_type_card.csv",
        "manual-2/data/circle_geometry/circle_relational_geometry_audit_records.csv",
        "manual-2/data/circle_geometry/circle_trace_independence_requirements.csv",
        "manual-2/data/circle_geometry/circle_tau_pi_notation_policy.csv",
        "manual-2/data/circle_geometry/circle_relational_geometry_counterfactual_audit.csv",
        "manual-2/data/circle_geometry/circle_relational_geometry_audit_manifest.json",
        "manual-2/sections/01_circle_relational_geometry_audit_records.tex",
        "manual-2/scripts/build_circle_relational_geometry_audit.py",
        "tests/test_manual2_circle_relational_geometry_audit_records.py",
    }

    r18_1_required = {
        "manual-2/data/circle_geometry/circle_finite_trace_audit_records.csv",
        "manual-2/data/circle_geometry/circle_rational_tau_pi_error_audit.csv",
        "manual-2/data/circle_geometry/circle_finite_trace_counterfactual_audit.csv",
        "manual-2/data/circle_geometry/circle_finite_trace_tau_pi_error_manifest.json",
        "manual-2/sections/02_circle_finite_trace_tau_pi_error_audit.tex",
        "manual-2/scripts/build_circle_finite_trace_tau_pi_error_audit.py",
        "tests/test_manual2_circle_finite_trace_tau_pi_error_audit.py",
    }

    r19_1_required = {
        "manual-2/data/circle_geometry/circle_one_metre_null_path_report_cards.csv",
        "manual-2/data/circle_geometry/circle_one_metre_report_link_index.csv",
        "manual-2/data/circle_geometry/circle_one_metre_null_path_counterfactual_audit.csv",
        "manual-2/data/circle_geometry/circle_one_metre_null_path_report_cards_manifest.json",
        "manual-2/sections/03_circle_one_metre_null_path_report_cards.tex",
        "manual-2/scripts/build_circle_one_metre_null_path_report_cards.py",
        "tests/test_manual2_circle_one_metre_null_path_report_cards.py",
    }

    r24_required = {
        "manual-2/data/elementary/elementary_matter_118_occurrence_cards.csv",
        "manual-2/data/elementary/elementary_matter_118_transition_packets.csv",
        "manual-2/data/elementary/elementary_matter_118_sadar_flow_declarations.csv",
        "manual-2/data/elementary/elementary_matter_118_transition_atlas_summary.csv",
        "manual-2/data/elementary/elementary_matter_118_counterfactual_audit.csv",
        "manual-2/data/elementary/elementary_matter_118_transition_atlas_manifest.json",
        "manual-2/sections/04_elementary_matter_118_transition_atlas.tex",
        "manual-2/scripts/build_elementary_matter_118_transition_atlas.py",
        "tests/test_manual2_elementary_matter_118_transition_atlas.py",
    }
    r25_1_required = {
        "manual-2/data/molecular/molecular_matter_transition_occurrence_cards.csv",
        "manual-2/data/molecular/molecular_matter_transition_packets.csv",
        "manual-2/data/molecular/molecular_matter_sadar_flow_declarations.csv",
        "manual-2/data/molecular/molecular_matter_transition_atlas_summary.csv",
        "manual-2/data/molecular/molecular_matter_counterfactual_audit.csv",
        "manual-2/data/molecular/molecular_matter_transition_atlas_manifest.json",
        "manual-2/sections/05_molecular_matter_transition_atlas.tex",
        "manual-2/scripts/build_molecular_matter_transition_atlas.py",
        "tests/test_manual2_molecular_matter_transition_atlas.py",
    }
    if working in {"v40.03r08", "v40.03r08.1"}:
        required = base_required
    elif working in {"v40.03r10", "v40.03r10.1", "v40.03r10.2", "v40.03r10.6"}:
        required = base_required | r10_required
    elif working in {"v40.03r13.1"}:
        required = r13_1_required
    elif working in {"v40.03r17.1"}:
        required = r17_1_required
    elif working in {"v40.03r18.1", "v40.03r18.2"}:
        required = r17_1_required | r18_1_required
    elif working in {"v40.03r19.2", "v40.03r19.3", "v40.03r19.5"}:
        required = r17_1_required | r18_1_required | r19_1_required
    elif working in {"v40.03r24", "v40.03r24.1"}:
        required = r17_1_required | r18_1_required | r19_1_required | r24_required
    elif working in {"v40.03r25.1", "v40.03r25.2"}:
        required = r17_1_required | r18_1_required | r19_1_required | r24_required | r25_1_required
    else:
        return False
    with zipfile.ZipFile(root / "source.zip") as archive:
        members = {info.filename for info in archive.infolist() if not info.is_dir()}
    return required <= members


def _foundation_doctrine_pdf_rebuild_authorized(root: Path) -> bool:
    state = load_json_strict(root / "cycle/CYCLE_STATE.json")
    working = state.get("release", {}).get("working_version")
    if working != "v40.04r03":
        return False
    required = {
        "sections/03_foundation_doctrine_tick_tau_sparc.tex",
        "manual/sections/00_foundation_doctrine_tick_tau_sparc.tex",
        "manual-2/sections/00_dec_report_coordinate_overlay.tex",
        "manual-2/data/dec/dec_conversion_operator_registry.csv",
        "manual-2/data/dec/dec_report_coordinate_overlay.csv",
        "manual-2/data/dec/dec_error_budget_policy.csv",
        "manual-2/data/dec/dec_reporting_overlay_manifest.json",
        "tests/test_manual1_foundation_doctrine_tick_tau_sparc.py",
        "tests/test_manual2_dec_report_coordinate_overlay.py",
        "tests/test_manual2_dec_error_budget_policy.py",
    }
    with zipfile.ZipFile(root / "source.zip") as archive:
        members = {info.filename for info in archive.infolist() if not info.is_dir()}
    return required <= members


def _validate_pdf_freeze_policy(root: Path) -> None:
    changed = {
        name
        for name in ("main.pdf", "manual.pdf", "manual-2.pdf")
        if (root / name).read_bytes() != (root / "stable/payload" / name).read_bytes()
    }
    if not changed:
        return
    if _foundation_doctrine_pdf_rebuild_authorized(root):
        return
    for name in ("main.pdf", "manual.pdf"):
        if name in changed:
            raise ValueError(f"frozen PDF changed: {name}")
    if "manual-2.pdf" in changed and not _manual2_rebuild_authorized(root):
        raise ValueError("manual-2.pdf changed without an authorized Manual-II materialization manifest for the active milestone")

def _validate_phase_tooling(root: Path, phase: str) -> None:
    required = {"tools/run_phase_transition.py", "tools/validate_phase_bundle.py", "tools/run_review_feedback_transition.py", "tools/run_review_go_transition.py", "tools/review_common.py"}
    for relative in required:
        if not (root / relative).is_file():
            raise ValueError(f"required phase tool missing from bundle: {relative}")
    with zipfile.ZipFile(root / "source.zip") as archive:
        source_members = {info.filename for info in archive.infolist() if not info.is_dir()}
    missing = required - source_members
    if missing:
        raise ValueError(f"required phase tool missing from source.zip: {sorted(missing)}")
    workflow = (root / "BUNDLE_WORKFLOW.md").read_text(encoding="utf-8")
    if f"Current state: {phase}." not in workflow:
        raise ValueError("bundle workflow phase text disagrees with cycle state")


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    state_path = root / "cycle/CYCLE_STATE.json"
    if state_path.is_file():
        phase = load_json_strict(state_path).get("active_phase")
        if phase != "REVIEW":
            # AUTHORING and FEEDBACK are complete bundles too; the phase-aware
            # validator applies the same structural checks with phase-specific
            # review binding rules.
            import validate_phase_bundle
            return validate_phase_bundle.validate(root)
    _exact_top_level(root)
    _no_forbidden_files(root)
    expected_bundle = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "BUNDLE_CONTENTS_SHA256.txt"
    }
    validate_sha_manifest(root, root / "BUNDLE_CONTENTS_SHA256.txt", expected_paths=expected_bundle)
    payload_rows, _ = _validate_payload_manifests(root)
    stable_record, stable_rows = _validate_stable(root)
    delta_summary, _ = _validate_delta(root, stable_rows, payload_rows)
    _validate_source_delta(root, delta_summary)
    _validate_source_templates(root)
    _, governance_digest = _validate_governance(root)
    candidate = _validate_candidate(root, stable_record, delta_summary)

    candidate_digest = sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt")
    delta_digest = sha256_file(root / "delta/DELTA_MANIFEST.csv")
    source_delta_digest = sha256_file(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv")
    authoring, authoring_digest = _validate_authoring(root, candidate_digest, delta_digest, source_delta_digest, governance_digest)
    feedback_rows, feedback_digest, feedback_counts = _validate_feedback(root, candidate_digest)
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
    review, review_digest, review_path, review_outcome = _validate_review(root, review_expected, feedback_rows, feedback_counts)
    transition_expected = {
        "candidate_payload_manifest_sha256": candidate_digest,
        "delta_manifest_sha256": delta_digest,
        "source_tree_delta_manifest_sha256": source_delta_digest,
        "governance_manifest_sha256": governance_digest,
        "feedback_ledger_sha256": feedback_digest,
        "authoring_report_sha256": authoring_digest,
        "review_record_sha256": review_digest,
    }
    transition_records, transition_digest, last_row_sha = _validate_transition(
        root,
        transition_expected,
        candidate["lineage_parent_bundle"],
        candidate["lineage_parent_sha256"],
        feedback_counts,
        review_outcome,
    )
    state = _validate_state(
        root,
        candidate,
        feedback_counts,
        review_path,
        review_digest,
        review,
        review_outcome,
        transition_records,
        transition_digest,
        last_row_sha,
        governance_digest,
    )

    if state["transition_sequence"] < 2 or state["active_phase"] != "REVIEW" or state["last_completed_phase"] != "AUTHORING":
        raise ValueError("cycle phase/sequence mismatch")
    if state["lineage_parent"] != {"filename": candidate["lineage_parent_bundle"], "sha256": candidate["lineage_parent_sha256"]}:
        raise ValueError("state/candidate lineage mismatch")
    _validate_phase_tooling(root, "REVIEW")
    _validate_pdf_freeze_policy(root)
    tests_count = int(authoring["test_count"])
    if review["r08_status"] != review_outcome["r08_status"]:
        raise ValueError("Hydrogen r08 state mismatch")
    return {
        "status": "passed",
        "candidate_version": candidate["version"],
        "payload_files": len(payload_rows),
        "bundle_files": len(expected_bundle) + 1,
        "tests": tests_count,
        "open_blocking_feedback": feedback_counts["open_blocking"],
        "review_verdict": review["verdict"],
        "r08_status": review["r08_status"],
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = validate(args.root)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
