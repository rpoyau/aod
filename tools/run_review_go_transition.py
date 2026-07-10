#!/usr/bin/env python3
"""Emit one deterministic REVIEW -> GO successor after authority-bound approval."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

try:
    import run_bundle_transition as materializer
    from bundle_common import (
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        sha256_bytes,
        sha256_file,
        validate_schema,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import (
        feedback_counts,
        reviewer_can_verify,
        update_workflow_state,
        upstream_lock_ready,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import run_bundle_transition as materializer  # type: ignore
    from bundle_common import (  # type: ignore
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        sha256_bytes,
        sha256_file,
        validate_schema,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import (  # type: ignore
        feedback_counts,
        reviewer_can_verify,
        update_workflow_state,
        upstream_lock_ready,
    )

FEEDBACK_HEADER = materializer.FEEDBACK_HEADER


def _feedback_rows(root: Path) -> list[dict[str, str]]:
    with (root / "cycle/FEEDBACK_LEDGER.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FEEDBACK_HEADER:
            raise ValueError("feedback ledger header mismatch")
        rows = list(reader)
    return rows


def build(parent_zip: Path, output_zip: Path, decision_path: Path) -> dict[str, Any]:
    parent_zip = parent_zip.resolve()
    parent_sha = sha256_file(parent_zip)
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        parent = work / "parent"
        successor = work / "successor"
        extract_zip_safe(parent_zip, parent)
        import validate_complete_bundle
        validate_complete_bundle.validate(parent)

        state = load_json_strict(parent / "cycle/CYCLE_STATE.json")
        if state["active_phase"] != "REVIEW" or state["next_permitted_transitions"] != ["GO"]:
            raise ValueError("parent REVIEW bundle is not GO-admissible")
        candidate = load_json_strict(parent / "candidate/WORKING_CANDIDATE.json")
        review = load_json_strict(parent / state["review"]["record_path"])
        if review["verdict"] != "GO_RECOMMENDED" or not review["go_recommended"]:
            raise ValueError("canonical review does not recommend GO")
        rows = _feedback_rows(parent)
        counts = feedback_counts(rows)
        if any(counts[key] for key in ("open_blocking", "open_nonblocking", "applied_unverified")):
            raise ValueError("GO requires zero open and applied-unverified findings")
        upstream = load_json_strict(parent / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
        if not upstream_lock_ready(upstream):
            raise ValueError("upstream refresh state is not GO-admissible")

        decision_template = load_json_strict(decision_path.resolve())
        validate_schema(decision_template, parent / "governance/schemas/go-decision.schema.json", label="GO decision")
        if decision_template["record_scope"] != "source_template":
            raise ValueError("GO decision input must be a source template")
        if decision_template["candidate_version"] != candidate["version"]:
            raise ValueError("GO decision candidate version mismatch")
        if decision_template["authority_class"] not in {"project_owner", "designated_reviewer"}:
            raise ValueError("GO authority class is not admitted")
        if not reviewer_can_verify(review["reviewer_class"]):
            raise ValueError("canonical review lacks independent verification authority")

        shutil.copytree(parent, successor)
        runtime_tools = Path(__file__).resolve().parent
        for tool_name in (
            "run_review_go_transition.py", "run_phase_transition.py", "validate_phase_bundle.py",
            "validate_complete_bundle.py", "run_review_feedback_transition.py", "review_common.py",
        ):
            shutil.copyfile(runtime_tools / tool_name, successor / "tools" / tool_name)

        concrete_decision = {
            **decision_template,
            "record_scope": "bundle_instance",
            "candidate_payload_manifest_sha256": sha256_file(successor / "PAYLOAD_CONTENTS_SHA256.txt"),
            "feedback_ledger_sha256": sha256_file(successor / "cycle/FEEDBACK_LEDGER.csv"),
            "review_record_path": state["review"]["record_path"],
            "review_record_sha256": state["review"]["record_sha256"],
        }
        go_path = successor / "cycle/GO_DECISION.json"
        write_canonical_json(go_path, concrete_decision)
        go_decision_sha256 = sha256_file(go_path)

        parent_ledger = (parent / "cycle/TRANSITION_LEDGER.jsonl").read_bytes()
        records = [json.loads(line) for line in parent_ledger.decode("utf-8").splitlines() if line]
        last = records[-1]
        payload = {
            "schema_version": "3.1",
            "sequence": state["transition_sequence"] + 1,
            "transition_id": f"transition_{candidate['version']}_review_to_go",
            "transition_class": "ordinary_parent_prefix_plus_one",
            "parent_bundle": {"filename": parent_zip.name, "sha256": parent_sha},
            "predecessor_state": {
                "path": "cycle/CYCLE_STATE.json",
                "sha256": sha256_file(parent / "cycle/CYCLE_STATE.json"),
                "transition_sequence": state["transition_sequence"],
            },
            "from_phase": "REVIEW",
            "to_phase": "GO",
            "candidate_id": candidate["candidate_id"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": sha256_file(successor / "PAYLOAD_CONTENTS_SHA256.txt"),
                "delta_manifest_sha256": sha256_file(successor / "delta/DELTA_MANIFEST.csv"),
                "source_tree_delta_manifest_sha256": sha256_file(successor / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"),
                "governance_manifest_sha256": sha256_file(successor / "governance/GOVERNANCE_CONTENTS_SHA256.txt"),
                "feedback_ledger_sha256": sha256_file(successor / "cycle/FEEDBACK_LEDGER.csv"),
                "authoring_report_sha256": sha256_file(successor / "cycle/AUTHORING_REPORT.json"),
                "review_record_sha256": state["review"]["record_sha256"],
                "go_decision_sha256": go_decision_sha256,
            },
            "open_blocking_feedback": 0,
            "go_eligible": True,
            "r08_status": "OPEN",
            "recording_semantics": "content_addressed_no_wall_clock",
            "previous_row_sha256": last["row_sha256"],
        }
        transition = {**payload, "row_sha256": sha256_bytes(canonical_json_bytes(payload))}
        ledger_path = successor / "cycle/TRANSITION_LEDGER.jsonl"
        ledger_path.write_bytes(parent_ledger + canonical_json_bytes(transition))

        candidate["status"] = "go_candidate"
        candidate["lineage_parent_bundle"] = parent_zip.name
        candidate["lineage_parent_sha256"] = parent_sha
        write_canonical_json(successor / "candidate/WORKING_CANDIDATE.json", candidate)

        state["active_phase"] = "GO"
        state["last_completed_phase"] = "REVIEW"
        state["lineage_parent"] = {"filename": parent_zip.name, "sha256": parent_sha}
        state["release"]["status"] = "go_candidate"
        state["transition_sequence"] = transition["sequence"]
        state["transition"] = {
            "ledger_path": "cycle/TRANSITION_LEDGER.jsonl",
            "ledger_sha256": sha256_file(ledger_path),
            "last_row_sha256": transition["row_sha256"],
        }
        state["go"]["eligible"] = True
        state["go"]["blocking_reason"] = "none"
        state["go"]["decision_path"] = "cycle/GO_DECISION.json"
        state["go"]["decision_sha256"] = go_decision_sha256
        state["next_permitted_transitions"] = ["AUTHORING"]
        write_canonical_json(successor / "cycle/CYCLE_STATE.json", state)
        update_workflow_state(
            successor / "BUNDLE_WORKFLOW.md",
            phase="GO",
            candidate_version=candidate["version"],
            candidate_status=candidate["status"],
            release_status=state["release"]["status"],
            counts=counts,
            verdict=review["verdict"],
            go_eligible=True,
            r08_status="OPEN",
            next_transitions=["AUTHORING"],
        )

        manifest = successor / "BUNDLE_CONTENTS_SHA256.txt"
        write_sha_manifest(manifest, [p for p in successor.rglob("*") if p.is_file() and p.name != manifest.name], successor)
        deterministic_zip_from_directory(successor, output_zip)
        emitted = work / "emitted"
        extract_zip_safe(output_zip, emitted)
        # The canonical complete-bundle entry point must admit and fully validate
        # the emitted GO successor; the phase validator is retained as an explicit
        # independent cross-check of the same bytes.
        complete_report = validate_complete_bundle.validate(emitted)
        import validate_phase_bundle
        phase_report = validate_phase_bundle.validate(emitted)
        if complete_report != phase_report:
            raise ValueError("complete and phase GO validation reports disagree")
        return {
            **complete_report,
            "complete_validation": "passed",
            "phase_validation": "passed",
            "go_decision_sha256": go_decision_sha256,
            "output": str(output_zip),
            "sha256": sha256_file(output_zip),
            "transition_row_sha256": transition["row_sha256"],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent_bundle", type=Path)
    parser.add_argument("output_bundle", type=Path)
    parser.add_argument("--decision", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.parent_bundle, args.output_bundle, args.decision), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
