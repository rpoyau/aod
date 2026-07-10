#!/usr/bin/env python3
"""Emit one deterministic AOD phase-only successor bundle.

This engine handles REVIEW -> FEEDBACK and FEEDBACK -> AUTHORING. A
GO -> AUTHORING successor is not a phase-only copy: it must rebaseline the
accepted GO payload and seed the next authoring goal, so this command rejects
that transition rather than exporting stale stable/goal state. AUTHORING ->
REVIEW materialization remains owned by run_bundle_transition.py.
"""
from __future__ import annotations

import argparse
import json
import shutil
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
        sha256_bytes,
        sha256_file,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import feedback_counts, update_workflow_state
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bundle_common import (  # type: ignore
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        sha256_bytes,
        sha256_file,
        write_canonical_json,
        write_sha_manifest,
    )
    from review_common import feedback_counts, update_workflow_state  # type: ignore
    from review_common import feedback_counts, update_workflow_state


RULES = {
    ("REVIEW", "FEEDBACK"): {
        "candidate_status": "feedback_candidate",
        "release_status": "feedback_candidate",
        "next": ["AUTHORING"],
    },
    ("FEEDBACK", "AUTHORING"): {
        "candidate_status": "authoring_candidate",
        "release_status": "authoring_candidate",
        "next": ["REVIEW"],
    },
}


def _validator_for(root: Path):
    phase = load_json_strict(root / "cycle/CYCLE_STATE.json")["active_phase"]
    if phase == "REVIEW":
        import validate_complete_bundle as validator
    else:
        import validate_phase_bundle as validator
    return validator


def build(parent_zip: Path, output_zip: Path, to_phase: str) -> dict[str, Any]:
    parent_zip = parent_zip.resolve()
    parent_sha = sha256_file(parent_zip)
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        parent_root = temporary_root / "parent"
        successor_root = temporary_root / "successor"
        extract_zip_safe(parent_zip, parent_root)
        _validator_for(parent_root).validate(parent_root)
        shutil.copytree(parent_root, successor_root)
        # Carry the canonical runtime copies into the successor toolset.
        runtime_tools = Path(__file__).resolve().parent
        for tool_name in ("run_phase_transition.py", "validate_phase_bundle.py", "validate_complete_bundle.py", "run_review_feedback_transition.py", "run_review_go_transition.py", "review_common.py"):
            shutil.copyfile(runtime_tools / tool_name, successor_root / "tools" / tool_name)

        parent_state_path = parent_root / "cycle/CYCLE_STATE.json"
        parent_state = load_json_strict(parent_state_path)
        from_phase = parent_state["active_phase"]
        if from_phase == "GO" and to_phase == "AUTHORING":
            raise ValueError(
                "GO -> AUTHORING is not a phase-only transition; emit an "
                "authorized rebaseline successor that promotes the GO payload "
                "to stable/payload and seeds the next AUTHORING goal."
            )
        rule = RULES.get((from_phase, to_phase))
        if rule is None or to_phase not in parent_state["next_permitted_transitions"]:
            raise ValueError(f"illegal phase-only transition: {from_phase} -> {to_phase}")

        candidate_path = successor_root / "candidate/WORKING_CANDIDATE.json"
        candidate = load_json_strict(candidate_path)
        candidate["status"] = rule["candidate_status"]
        candidate["lineage_parent_bundle"] = parent_zip.name
        candidate["lineage_parent_sha256"] = parent_sha
        write_canonical_json(candidate_path, candidate)

        parent_ledger_path = parent_root / "cycle/TRANSITION_LEDGER.jsonl"
        parent_ledger_bytes = parent_ledger_path.read_bytes()
        if not parent_ledger_bytes or not parent_ledger_bytes.endswith(b"\n"):
            raise ValueError("parent transition ledger is empty or noncanonical")
        records = [json.loads(line) for line in parent_ledger_bytes.decode("utf-8").splitlines() if line]
        if not records:
            raise ValueError("parent transition ledger is empty")
        if sha256_bytes(parent_ledger_bytes) != parent_state["transition"]["ledger_sha256"]:
            raise ValueError("parent transition ledger digest/state mismatch")
        if records[-1]["row_sha256"] != parent_state["transition"]["last_row_sha256"]:
            raise ValueError("parent transition last-row/state mismatch")
        if records[-1]["sequence"] != parent_state["transition_sequence"]:
            raise ValueError("parent transition sequence/state mismatch")
        ledger_path = successor_root / "cycle/TRANSITION_LEDGER.jsonl"
        review_path = successor_root / parent_state["review"]["record_path"]
        payload = {
            "schema_version": "3.1",
            "sequence": int(parent_state["transition_sequence"]) + 1,
            "transition_id": f"transition_{candidate['version']}_{from_phase.lower()}_to_{to_phase.lower()}",
            "transition_class": "ordinary_parent_prefix_plus_one",
            "parent_bundle": {"filename": parent_zip.name, "sha256": parent_sha},
            "predecessor_state": {
                "path": "cycle/CYCLE_STATE.json",
                "sha256": sha256_file(parent_state_path),
                "transition_sequence": int(parent_state["transition_sequence"]),
            },
            "from_phase": from_phase,
            "to_phase": to_phase,
            "candidate_id": candidate["candidate_id"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": sha256_file(successor_root / "PAYLOAD_CONTENTS_SHA256.txt"),
                "delta_manifest_sha256": sha256_file(successor_root / "delta/DELTA_MANIFEST.csv"),
                "source_tree_delta_manifest_sha256": sha256_file(successor_root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"),
                "governance_manifest_sha256": sha256_file(successor_root / "governance/GOVERNANCE_CONTENTS_SHA256.txt"),
                "feedback_ledger_sha256": sha256_file(successor_root / "cycle/FEEDBACK_LEDGER.csv"),
                "authoring_report_sha256": sha256_file(successor_root / "cycle/AUTHORING_REPORT.json"),
                "review_record_sha256": sha256_file(review_path),
            },
            "open_blocking_feedback": int(parent_state["feedback_counts"]["open_blocking"]),
            "go_eligible": False,
            "r08_status": "OPEN" if from_phase == "GO" and to_phase == "AUTHORING" else "BLOCKED",
            "recording_semantics": "content_addressed_no_wall_clock",
            "previous_row_sha256": records[-1]["row_sha256"],
        }
        transition = {**payload, "row_sha256": sha256_bytes(canonical_json_bytes(payload))}
        ledger_path.write_bytes(parent_ledger_bytes + canonical_json_bytes(transition))

        state_path = successor_root / "cycle/CYCLE_STATE.json"
        state = load_json_strict(state_path)
        state["active_phase"] = to_phase
        state["last_completed_phase"] = from_phase
        state["lineage_parent"] = {"filename": parent_zip.name, "sha256": parent_sha}
        state["release"]["status"] = rule["release_status"]
        state["transition_sequence"] = transition["sequence"]
        state["transition"] = {
            "ledger_path": "cycle/TRANSITION_LEDGER.jsonl",
            "ledger_sha256": sha256_file(ledger_path),
            "last_row_sha256": transition["row_sha256"],
        }
        state["next_permitted_transitions"] = rule["next"]
        state["go"]["eligible"] = False
        state["go"]["blocking_reason"] = "independent_review_required"
        write_canonical_json(state_path, state)
        update_workflow_state(
            successor_root / "BUNDLE_WORKFLOW.md",
            phase=to_phase, candidate_version=candidate["version"], candidate_status=candidate["status"],
            release_status=state["release"]["status"], counts=state["feedback_counts"],
            verdict=state["review"]["verdict"], go_eligible=False, r08_status=transition["r08_status"],
            next_transitions=state["next_permitted_transitions"],
        )

        manifest = successor_root / "BUNDLE_CONTENTS_SHA256.txt"
        files = [path for path in successor_root.rglob("*") if path.is_file() and path.name != manifest.name]
        write_sha_manifest(manifest, files, successor_root)
        deterministic_zip_from_directory(successor_root, output_zip)

        extracted = temporary_root / "emitted"
        extract_zip_safe(output_zip, extracted)
        import validate_phase_bundle
        report = validate_phase_bundle.validate(extracted)
        return {
            **report,
            "output": str(output_zip),
            "sha256": sha256_file(output_zip),
            "parent_sha256": parent_sha,
            "transition_row_sha256": transition["row_sha256"],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent_bundle", type=Path)
    parser.add_argument("output_bundle", type=Path)
    parser.add_argument("--to-phase", required=True, choices=["FEEDBACK", "AUTHORING"])
    args = parser.parse_args()
    print(json.dumps(build(args.parent_bundle, args.output_bundle, args.to_phase), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
