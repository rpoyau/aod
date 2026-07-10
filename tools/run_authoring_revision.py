#!/usr/bin/env python3
"""Materialize a deterministic FEEDBACK -> AUTHORING revision bundle.

This command is the authoring-side counterpart to run_bundle_transition.py. It
updates the candidate payload from a source tree, appends feedback status events,
preserves immutable review/transition history, validates the complete successor,
and emits exactly one ZIP.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

try:
    import run_bundle_transition as materializer
    import resolve_github_releases as release_resolver
    from bundle_common import (
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        parse_sha_manifest,
        row_sha256,
        sha256_bytes,
        sha256_file,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import effective_feedback_rows, feedback_counts, update_workflow_state
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import run_bundle_transition as materializer  # type: ignore
    import resolve_github_releases as release_resolver  # type: ignore
    from bundle_common import (  # type: ignore
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        parse_sha_manifest,
        row_sha256,
        sha256_bytes,
        sha256_file,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import effective_feedback_rows, feedback_counts, update_workflow_state  # type: ignore

FEEDBACK_HEADER = materializer.FEEDBACK_HEADER
APPLIED_HEADER = ["finding_id", "evidence_path"]


def _read_csv(path: Path, header: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != header:
            raise ValueError(f"CSV header mismatch: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"malformed CSV: {path}")
    return rows


def _append_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    existing = path.read_bytes()
    if not existing.endswith(b"\n"):
        raise ValueError("feedback ledger is noncanonical")
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=FEEDBACK_HEADER, lineterminator="\n")
    writer.writerows(rows)
    path.write_bytes(existing + stream.getvalue().encode("utf-8"))


def _append_applied_events(root: Path, applied_path: Path, candidate_digest: str) -> tuple[list[dict[str, str]], str]:
    ledger_path = root / "cycle/FEEDBACK_LEDGER.csv"
    current = _read_csv(ledger_path, FEEDBACK_HEADER)
    latest = {row["finding_id"]: row for row in effective_feedback_rows(current)}
    instructions = _read_csv(applied_path, APPLIED_HEADER)
    previous = current[-1]["row_sha256"] if current else ""
    sequence = len(current)
    appended: list[dict[str, str]] = []
    seen: set[str] = set()
    for instruction in instructions:
        finding_id = instruction["finding_id"]
        if finding_id in seen:
            raise ValueError(f"duplicate applied finding instruction: {finding_id}")
        seen.add(finding_id)
        if finding_id not in latest:
            raise ValueError(f"applied finding is unknown: {finding_id}")
        prior = latest[finding_id]
        if prior["status"] not in {"OPEN", "DISPUTED_OPEN"}:
            raise ValueError(f"finding is not open for authoring application: {finding_id}")
        evidence_path = instruction["evidence_path"]
        evidence = root / evidence_path
        if not evidence.is_file():
            raise ValueError(f"authoring evidence missing: {evidence_path}")
        sequence += 1
        row = {
            "sequence": str(sequence),
            "finding_id": finding_id,
            "source_release": prior["source_release"],
            "severity": prior["severity"],
            "blocking": prior["blocking"],
            "status": "APPLIED_UNVERIFIED",
            "summary": prior["summary"],
            "required_action": prior["required_action"],
            "evidence_path": evidence_path,
            "evidence_sha256": sha256_file(evidence),
            "candidate_payload_sha256": candidate_digest,
            "previous_row_sha256": previous,
            "row_sha256": "",
        }
        row["row_sha256"] = row_sha256([row[column] for column in FEEDBACK_HEADER[:-1]])
        previous = row["row_sha256"]
        appended.append(row)
        latest[finding_id] = row
    _append_csv_rows(ledger_path, appended)
    rows = _read_csv(ledger_path, FEEDBACK_HEADER)
    effective_feedback_rows(rows)
    return rows, sha256_file(ledger_path)


def build(args: argparse.Namespace) -> dict[str, Any]:
    parent_zip = args.parent_bundle.resolve()
    source_root = args.source_root.resolve()
    parent_sha = sha256_file(parent_zip)
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        parent = work / "parent"
        root = work / "bundle"
        source_stage = work / "source_stage"
        parent.mkdir(); root.mkdir(); source_stage.mkdir()
        extract_zip_safe(parent_zip, parent)
        parent_validator = parent / "tools/validate_complete_bundle.py"
        completed = subprocess.run([sys.executable, str(parent_validator), str(parent)], check=False, capture_output=True, text=True)
        if completed.returncode:
            raise ValueError(f"parent bundle validation failed: {completed.stdout}{completed.stderr}")
        parent_state = load_json_strict(parent / "cycle/CYCLE_STATE.json")
        if parent_state["active_phase"] != "FEEDBACK" or "AUTHORING" not in parent_state["next_permitted_transitions"]:
            raise ValueError("parent bundle does not admit FEEDBACK -> AUTHORING")

        materializer._build_source_stage(source_root, source_stage)
        # Every AUTHORING candidate attempts the rolling latest GitHub refresh.
        # Resolution occurs in isolated staging and commits only after all four
        # AF/AFC/GM/AOD dependencies validate. A network/API failure records a
        # candidate-bound receipt and preserves the complete prior fallback.
        release_resolver.refresh_or_fallback(
            source_stage,
            token=os.environ.get("GITHUB_TOKEN"),
            timeout=args.refresh_timeout,
            attempted_at_utc=args.refresh_attempted_at_utc,
            candidate_release=args.version,
            strict_refresh=False,
        )
        source_zip = work / "source.zip"
        deterministic_zip_from_directory(source_stage, source_zip)

        artifacts = {
            "main.pdf": parent / "main.pdf",
            "manual.pdf": parent / "manual.pdf",
            "manual-2.pdf": parent / "manual-2.pdf",
            "MANUAL_I_ROADMAP.md": source_stage / "MANUAL_I_ROADMAP.md",
            "MANUAL_II_ROADMAP.md": source_stage / "MANUAL_II_ROADMAP.md",
            "source.zip": source_zip,
            "tests.txt": args.tests_file.resolve(),
            "patch_summary.txt": source_stage / "patch_summary.txt",
            "MANUAL_ARTIFACT_BASELINES_SHA256.txt": source_stage / "MANUAL_ARTIFACT_BASELINES_SHA256.txt",
        }
        for name, source in artifacts.items():
            if not source.is_file():
                raise ValueError(f"candidate artifact missing: {source}")
            shutil.copyfile(source, root / name)
        external = materializer._copy_external_payloads(source_stage, root)
        write_sha_manifest(root / "EXTERNAL_PAYLOADS_SHA256.txt", external, root)
        payload_files = [root / name for name in materializer.PAYLOAD_ROOT_NAMES] + external
        write_sha_manifest(root / "PAYLOAD_CONTENTS_SHA256.txt", payload_files, root)
        payload_digest = sha256_file(root / "PAYLOAD_CONTENTS_SHA256.txt")

        shutil.copytree(parent / "stable", root / "stable")
        stable = load_json_strict(parent / "stable/STABLE_BASELINE.json")
        stable["payload_manifest_sha256"] = sha256_file(root / "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt")
        write_canonical_json(root / "stable/STABLE_BASELINE.json", stable)
        stable_rows = parse_sha_manifest(root / "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt")
        candidate_rows = parse_sha_manifest(root / "PAYLOAD_CONTENTS_SHA256.txt")
        payload_delta = materializer._payload_delta(stable_rows, candidate_rows)
        materializer._write_csv(root / "delta/DELTA_MANIFEST.csv", materializer.DELTA_HEADER, payload_delta)
        deletes = [row["path"] for row in payload_delta if row["operation"] == "delete"]
        (root / "delta/DELETE_PATHS.txt").write_text("\n".join(deletes) + ("\n" if deletes else ""), encoding="utf-8")
        (root / "delta/DELTA_PROTOCOL.md").write_text("Stable plus the ordered add/replace/delete rows must reproduce the candidate payload manifest exactly. Source-tree rows are independently recomputed from the two source archives.\n", encoding="utf-8")
        source_delta = materializer._source_delta(materializer._source_hash_map(root / "stable/payload/source.zip"), materializer._source_hash_map(root / "source.zip"))
        materializer._write_csv(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv", materializer.SOURCE_DELTA_HEADER, source_delta)
        delta_digest = sha256_file(root / "delta/DELTA_MANIFEST.csv")
        source_delta_digest = sha256_file(root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv")
        summary = {
            "schema_version": "3.1",
            "delta_id": f"delta_{stable['version']}_to_{args.version}",
            "base_version": stable["version"], "candidate_version": args.version,
            "delta_manifest_path": "delta/DELTA_MANIFEST.csv", "delta_manifest_sha256": delta_digest,
            "candidate_payload_manifest_sha256": payload_digest,
            "operation_counts": {kind: sum(row["operation"] == kind for row in payload_delta) for kind in ("add", "replace", "delete")},
            "source_tree_delta_manifest_path": "delta/SOURCE_TREE_DELTA_MANIFEST.csv", "source_tree_delta_manifest_sha256": source_delta_digest,
            "source_tree_operation_counts": {kind: sum(row["operation"] == kind for row in source_delta) for kind in ("add", "modify", "delete")},
        }
        write_canonical_json(root / "delta/DELTA_SUMMARY.json", summary)

        materializer._copy_control_plane(source_stage, root)
        shutil.copytree(parent / "governance/reviews", root / "governance/reviews", dirs_exist_ok=True)
        materializer._snapshot_parent_feedback_evidence(parent, root)
        # Preserve concrete append-only ledgers from the parent rather than source templates.
        shutil.copyfile(parent / "cycle/FEEDBACK_LEDGER.csv", root / "cycle/FEEDBACK_LEDGER.csv")
        shutil.copyfile(parent / "cycle/TRANSITION_LEDGER.jsonl", root / "cycle/TRANSITION_LEDGER.jsonl")
        governance_digest = materializer._governance_manifest(root)

        candidate_id = materializer._candidate_id_from_source_template(source_stage, args.version)
        candidate = {
            "schema_version": "3.1", "candidate_id": candidate_id, "version": args.version,
            "status": "authoring_candidate", "stable_baseline_version": stable["version"],
            "lineage_parent_bundle": parent_zip.name, "lineage_parent_sha256": parent_sha,
            "payload_manifest_path": "PAYLOAD_CONTENTS_SHA256.txt", "payload_manifest_sha256": payload_digest,
            "delta_manifest_path": "delta/DELTA_MANIFEST.csv", "delta_manifest_sha256": delta_digest,
            "source_tree_delta_manifest_path": "delta/SOURCE_TREE_DELTA_MANIFEST.csv", "source_tree_delta_manifest_sha256": source_delta_digest,
        }
        write_canonical_json(root / "candidate/WORKING_CANDIDATE.json", candidate)

        feedback_rows, feedback_digest = _append_applied_events(root, args.applied_findings.resolve(), payload_digest)
        counts = feedback_counts(feedback_rows)

        author_template = load_json_strict(root / "cycle/AUTHORING_REPORT.template.json")
        authoring = {
            "schema_version": "3.1", "record_scope": "bundle_instance", "report_id": author_template["report_id"],
            "candidate_version": args.version, "authoring_attempt": author_template["authoring_attempt"], "phase": "AUTHORING",
            "classification": author_template["classification"], "implemented_changes": author_template["implemented_changes"],
            "frozen_claim": author_template["frozen_claim"], "test_count": materializer._tests_count(root / "tests.txt"), "tests_path": "tests.txt",
            "unresolved_blockers": author_template["unresolved_blockers"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": payload_digest, "delta_manifest_sha256": delta_digest,
                "source_tree_delta_manifest_sha256": source_delta_digest, "governance_manifest_sha256": governance_digest,
                "input_feedback_template_sha256": sha256_file(root / "cycle/FEEDBACK_LEDGER.template.csv"),
            },
            "evidence_paths": [
                "tests.txt", "tools/validate_complete_bundle.py", "tools/run_bundle_transition.py",
                "tools/run_review_feedback_transition.py", "tools/review_common.py",
                "tools/resolve_github_releases.py", "tools/validate_upstream_release_lock.py",
                "tools/run_review_go_transition.py", "tools/validate_phase_bundle.py",
                "governance/UPSTREAM_RELEASE_POLICY.json",
                "governance/UPSTREAM_REFRESH_ATTEMPT.json", "governance/UPSTREAM_FALLBACK_SNAPSHOT.json",
                "governance/v40.03r07.3.4_DELTA2_CORRECTIVE_AUTHORING_EVIDENCE.md",
                "cycle/schemas/review-template.schema.json", "cycle/schemas/transition-record.schema.json",
                "cycle/schemas/cycle-state.schema.json", "delta/SOURCE_TREE_DELTA_MANIFEST.csv",
            ],
        }
        write_canonical_json(root / "cycle/AUTHORING_REPORT.json", authoring)
        authoring_digest = sha256_file(root / "cycle/AUTHORING_REPORT.json")

        review_index = load_json_strict(root / "governance/reviews/REVIEW_INDEX.json")
        review_path = root / review_index["canonical_review_path"]
        review_digest = sha256_file(review_path)
        review = load_json_strict(review_path)

        parent_ledger = (parent / "cycle/TRANSITION_LEDGER.jsonl").read_bytes()
        records = [json.loads(line) for line in parent_ledger.decode("utf-8").splitlines() if line]
        previous = records[-1]["row_sha256"]
        transition_payload = {
            "schema_version": "3.1", "sequence": parent_state["transition_sequence"] + 1,
            "transition_id": f"transition_{args.version}_feedback_to_authoring",
            "transition_class": "ordinary_parent_prefix_plus_one",
            "parent_bundle": {"filename": parent_zip.name, "sha256": parent_sha},
            "predecessor_state": {"path": "cycle/CYCLE_STATE.json", "sha256": sha256_file(parent / "cycle/CYCLE_STATE.json"), "transition_sequence": parent_state["transition_sequence"]},
            "from_phase": "FEEDBACK", "to_phase": "AUTHORING", "candidate_id": candidate["candidate_id"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": payload_digest, "delta_manifest_sha256": delta_digest,
                "source_tree_delta_manifest_sha256": source_delta_digest, "governance_manifest_sha256": governance_digest,
                "feedback_ledger_sha256": feedback_digest, "authoring_report_sha256": authoring_digest,
                "review_record_sha256": review_digest,
            },
            "open_blocking_feedback": counts["open_blocking"], "go_eligible": False, "r08_status": "BLOCKED",
            "recording_semantics": "content_addressed_no_wall_clock", "previous_row_sha256": previous,
        }
        transition = {**transition_payload, "row_sha256": sha256_bytes(canonical_json_bytes(transition_payload))}
        ledger_path = root / "cycle/TRANSITION_LEDGER.jsonl"
        ledger_path.write_bytes(parent_ledger + canonical_json_bytes(transition))

        template = load_json_strict(root / "cycle/CYCLE_STATE.json")
        state = {
            "schema_version": "3.1", "record_scope": "bundle_instance", "project_id": "AOD",
            "cycle_protocol_id": "AOD_BUNDLE_CYCLE", "protocol_version": "3.1", "active_phase": "AUTHORING",
            "last_completed_phase": "FEEDBACK", "authoring_attempt": template["authoring_attempt"],
            "transition_sequence": transition["sequence"], "canonical_state_rule": template["canonical_state_rule"],
            "lineage_parent": {"filename": parent_zip.name, "sha256": parent_sha},
            "release": template["release"],
            "working_candidate": {
                "candidate_id": candidate["candidate_id"], "payload_manifest_path": "PAYLOAD_CONTENTS_SHA256.txt", "payload_manifest_sha256": payload_digest,
                "delta_manifest_path": "delta/DELTA_MANIFEST.csv", "delta_manifest_sha256": delta_digest,
                "source_tree_delta_manifest_path": "delta/SOURCE_TREE_DELTA_MANIFEST.csv", "source_tree_delta_manifest_sha256": source_delta_digest,
                "governance_manifest_path": "governance/GOVERNANCE_CONTENTS_SHA256.txt", "governance_manifest_sha256": governance_digest,
            },
            "feedback_counts": counts,
            "review": {"record_path": review_index["canonical_review_path"], "record_sha256": review_digest, "verdict": review["verdict"]},
            "transition": {"ledger_path": "cycle/TRANSITION_LEDGER.jsonl", "ledger_sha256": sha256_file(ledger_path), "last_row_sha256": transition["row_sha256"]},
            "go": {**template["go"], "eligible": False, "blocking_reason": "applied_unverified_feedback" if counts["applied_unverified"] else "open_blocking_feedback"},
            "next_permitted_transitions": ["REVIEW"],
            "upstream_release_state": {
                "canonical_lock_status": load_json_strict(root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")["refresh_attempt_status"],
                "policy": "governance/UPSTREAM_RELEASE_POLICY.json",
                "required_dependencies": ["AF", "AFC", "GM", "AOD"],
                "source_registry": "governance/REPOSITORY_RELEASE_SOURCES.json",
            },
        }
        write_canonical_json(root / "cycle/CYCLE_STATE.json", state)
        update_workflow_state(
            root / "BUNDLE_WORKFLOW.md",
            phase="AUTHORING",
            candidate_version=candidate["version"],
            candidate_status=candidate["status"],
            release_status=state["release"]["status"],
            counts=counts,
            verdict=review["verdict"],
            go_eligible=False,
            r08_status="BLOCKED",
            next_transitions=["REVIEW"],
        )
        pointer = load_json_strict(root / "GLOBAL_INSTRUCTIONS.json")
        pointer["canonical_sha256"] = sha256_file(root / pointer["canonical_path"])
        write_canonical_json(root / "GLOBAL_INSTRUCTIONS.json", pointer)

        manifest = root / "BUNDLE_CONTENTS_SHA256.txt"
        write_sha_manifest(manifest, [p for p in root.rglob("*") if p.is_file() and p.name != manifest.name], root)
        deterministic_zip_from_directory(root, args.output.resolve())
        emitted = work / "emitted"; extract_zip_safe(args.output.resolve(), emitted)
        import validate_complete_bundle as complete
        report = complete.validate(emitted)
        return {**report, "output": str(args.output), "sha256": sha256_file(args.output), "transition_row_sha256": transition["row_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-bundle", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--tests-file", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--applied-findings", type=Path, required=True)
    parser.add_argument("--refresh-attempted-at-utc", required=True)
    parser.add_argument("--refresh-timeout", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists(): args.output.unlink()
    print(json.dumps(build(args), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
