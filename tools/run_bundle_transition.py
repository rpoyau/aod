#!/usr/bin/env python3
"""Emit one deterministic, complete AOD successor bundle.

The command consumes a parent canonical bundle plus a frozen authoring source
state, materializes the candidate payload, performs the AUTHORING -> REVIEW
transition, binds the independent review evidence, validates the complete tree,
and writes exactly one successor ZIP.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
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
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        parse_sha_manifest,
        row_sha256,
        sha256_bytes,
        sha256_file,
        validate_sha_manifest,
        validate_schema,
        write_canonical_json,
        write_sha_manifest,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bundle_common import (  # type: ignore
        canonical_json_bytes,
        deterministic_zip_from_directory,
        extract_zip_safe,
        load_json_strict,
        parse_sha_manifest,
        row_sha256,
        sha256_bytes,
        sha256_file,
        validate_sha_manifest,
        validate_schema,
        write_canonical_json,
        write_sha_manifest,
    )

SOURCE_INCLUDE_TOP_LEVEL = [
    ".github", "appendices", "figures_jpg", "manual", "manual-2", "shared", "scripts", "sections", "tests",
    "governance", "cycle", "tools", "CANONICAL_VERSION.txt", "RELEASE_READINESS.txt", "main.tex", "preamble.tex",
    "refs.bib", "cycle_shedding_summary.tex", "README.md", "LICENSE", "CITATION.cff", "requirements-ci.txt",
    ".zenodo.json", "BUILD.md", "MANUAL_I_ROADMAP.md", "MANUAL_II_ROADMAP.md",
    "MANUAL_ARTIFACT_BASELINES_SHA256.txt", "GLOBAL_INSTRUCTIONS.json", "BUNDLE_WORKFLOW.md", "patch_summary.txt",
]
EXCLUDE_DIR_NAMES = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".DS_Store", "dist", "build", "release", "_render", "_renders"}
EXCLUDE_SUFFIXES = {".pdf", ".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk", ".xdv", ".synctex.gz", ".pyc", ".pyo", ".bbl", ".blg", ".run.xml"}
PAYLOAD_ROOT_NAMES = [
    "main.pdf", "manual.pdf", "manual-2.pdf", "MANUAL_I_ROADMAP.md", "MANUAL_II_ROADMAP.md",
    "source.zip", "tests.txt", "patch_summary.txt", "MANUAL_ARTIFACT_BASELINES_SHA256.txt", "EXTERNAL_PAYLOADS_SHA256.txt",
]
FEEDBACK_TEMPLATE_HEADER = ["sequence", "finding_id", "source_release", "severity", "blocking", "status", "summary", "required_action", "evidence_path"]
FEEDBACK_HEADER = FEEDBACK_TEMPLATE_HEADER + ["evidence_sha256", "candidate_payload_sha256", "previous_row_sha256", "row_sha256"]
DELTA_HEADER = ["sequence", "operation", "path", "stable_sha256", "candidate_sha256", "source", "classification"]
REVIEW_FINDINGS_HEADER = FEEDBACK_TEMPLATE_HEADER
SOURCE_DELTA_HEADER = ["sequence", "operation", "path", "stable_sha256", "candidate_sha256", "classification"]

from review_common import (
    derive_review_outcome,
    effective_feedback_rows,
    feedback_counts as derive_feedback_counts,
    finding_sets,
    reviewer_can_verify,
    resolution_authorized,
    update_workflow_state,
    upstream_lock_ready,
)


def _excluded(relative: Path) -> bool:
    if set(relative.parts) & EXCLUDE_DIR_NAMES:
        return True
    name = relative.name
    if "governance" in relative.parts and ({"imports", "releases"} & set(relative.parts)):
        return name.endswith((".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk", ".pyc"))
    return any(name.endswith(suffix) for suffix in EXCLUDE_SUFFIXES)


def _build_source_stage(source_root: Path, destination: Path) -> None:
    for name in SOURCE_INCLUDE_TOP_LEVEL:
        source = source_root / name
        if not source.exists():
            continue
        if source.is_file():
            if not _excluded(Path(name)):
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            continue
        for path in sorted(source.rglob("*")):
            relative = path.relative_to(source_root)
            if _excluded(relative) or path.is_dir():
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def _copy_external_payloads(source_root: Path, bundle_root: Path) -> list[Path]:
    inventory = source_root / "manual-2/data/protein/external_payload_bundle_inventory.csv"
    with inventory.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    copied: list[Path] = []
    seen: set[str] = set()
    for row in rows:
        if row["embedding_class"] != "inline_bundle":
            continue
        relative = row["bundle_path"]
        if relative in seen or not relative.startswith("external_payloads/") or ".." in Path(relative).parts:
            raise ValueError(f"invalid external payload path: {relative}")
        seen.add(relative)
        source = source_root / row["source_path"]
        if not source.is_file():
            raise ValueError(f"required external payload missing: {row['source_path']}")
        if source.stat().st_size != int(row["payload_byte_count"]) or sha256_file(source) != row["payload_sha256"]:
            raise ValueError(f"external payload inventory mismatch: {row['source_path']}")
        target = bundle_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied.append(target)
    return sorted(copied)


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _source_hash_map(zip_path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if info.filename in result:
                raise ValueError(f"duplicate source member: {info.filename}")
            result[info.filename] = sha256_bytes(archive.read(info))
    return result


def _payload_delta(stable: dict[str, str], candidate: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for sequence, path in enumerate(sorted(path for path in set(stable) | set(candidate) if stable.get(path) != candidate.get(path)), 1):
        old, new = stable.get(path, ""), candidate.get(path, "")
        operation = "add" if not old else "delete" if not new else "replace"
        rows.append({"sequence": str(sequence), "operation": operation, "path": path, "stable_sha256": old, "candidate_sha256": new, "source": f"root:{path}" if new else "delete", "classification": "release_infrastructure"})
    return rows


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


def _source_delta(stable: dict[str, str], candidate: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for sequence, path in enumerate(sorted(path for path in set(stable) | set(candidate) if stable.get(path) != candidate.get(path)), 1):
        old, new = stable.get(path, ""), candidate.get(path, "")
        operation = "add" if not old else "delete" if not new else "modify"
        rows.append({"sequence": str(sequence), "operation": operation, "path": path, "stable_sha256": old, "candidate_sha256": new, "classification": _classify_source_delta_path(path)})
    return rows


def _copy_control_plane(source_root: Path, bundle_root: Path) -> None:
    for name in ("governance", "cycle", "tools"):
        shutil.copytree(source_root / name, bundle_root / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    shutil.copyfile(source_root / "GLOBAL_INSTRUCTIONS.json", bundle_root / "GLOBAL_INSTRUCTIONS.json")
    shutil.copyfile(source_root / "BUNDLE_WORKFLOW.md", bundle_root / "BUNDLE_WORKFLOW.md")


def _governance_manifest(bundle_root: Path) -> str:
    governance = bundle_root / "governance"
    files = [
        path for path in governance.rglob("*")
        if path.is_file() and path.relative_to(governance).parts[0] != "reviews" and path.name != "GOVERNANCE_CONTENTS_SHA256.txt"
    ]
    manifest = governance / "GOVERNANCE_CONTENTS_SHA256.txt"
    write_sha_manifest(manifest, files, governance)
    return sha256_file(manifest)




def _snapshot_parent_feedback_evidence(parent_root: Path, bundle_root: Path) -> None:
    destination = bundle_root / "cycle/evidence"
    destination.mkdir(parents=True, exist_ok=True)
    existing = parent_root / "cycle/evidence"
    if existing.is_dir():
        shutil.copytree(existing, destination, dirs_exist_ok=True)
    ledger = parent_root / "cycle/FEEDBACK_LEDGER.csv"
    if not ledger.is_file():
        return
    with ledger.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FEEDBACK_HEADER:
            raise ValueError("parent feedback ledger header mismatch")
        rows = list(reader)
    for row in rows:
        digest = row["evidence_sha256"]
        target = destination / f"{digest}.bin"
        if target.is_file():
            if sha256_file(target) != digest:
                raise ValueError("historical evidence snapshot hash mismatch")
            continue
        source = parent_root / row["evidence_path"]
        if source.is_file() and sha256_file(source) == digest:
            shutil.copyfile(source, target)
        else:
            prior = parent_root / "cycle/evidence" / f"{digest}.bin"
            if not prior.is_file() or sha256_file(prior) != digest:
                raise ValueError(f"cannot snapshot parent feedback evidence: {row['finding_id']}")
            shutil.copyfile(prior, target)

def _append_feedback_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    import io
    existing = path.read_bytes()
    if not existing.endswith(b"\n"):
        raise ValueError("feedback ledger is noncanonical")
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=FEEDBACK_HEADER, lineterminator="\n")
    writer.writerows(rows)
    path.write_bytes(existing + stream.getvalue().encode("utf-8"))


def _concrete_feedback(
    bundle_root: Path,
    parent_root: Path,
    candidate_digest: str,
    review_submission: dict[str, Any],
    review_findings_path: Path,
    submission_snapshot_path: str,
) -> tuple[str, dict[str, int], list[dict[str, str]]]:
    parent_ledger = parent_root / "cycle/FEEDBACK_LEDGER.csv"
    path = bundle_root / "cycle/FEEDBACK_LEDGER.csv"
    shutil.copyfile(parent_ledger, path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FEEDBACK_HEADER:
            raise ValueError("feedback ledger header mismatch")
        current = list(reader)
    effective = {row["finding_id"]: row for row in effective_feedback_rows(current)}
    with review_findings_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REVIEW_FINDINGS_HEADER:
            raise ValueError("review findings header mismatch")
        new_findings = list(reader)
    if review_submission["closed_findings"] and not reviewer_can_verify(review_submission["reviewer_class"]):
        raise ValueError("reviewer class is not authorized to verify-close findings")
    resolution_ids = [row["finding_id"] for row in review_submission.get("finding_resolutions", [])]
    if len(resolution_ids) != len(set(resolution_ids)):
        raise ValueError("duplicate finding resolution")
    if set(review_submission["closed_findings"]) != {row["finding_id"] for row in review_submission.get("finding_resolutions", []) if row["status"] in {"VERIFIED_CLOSED", "NOT_APPLICABLE_VERIFIED"}}:
        raise ValueError("closed_findings must match verified/not-applicable resolutions")
    if review_submission["reviewer_class"] == "self_review":
        raise ValueError("AUTHORING-to-REVIEW requires an independent reviewer class")

    seen_new: set[str] = set()
    for finding in new_findings:
        fid = finding["finding_id"]
        if fid in effective or fid in seen_new:
            raise ValueError(f"duplicate review/feedback finding ID: {fid}")
        seen_new.add(fid)
        if finding["status"] not in {"OPEN", "DISPUTED_OPEN"}:
            raise ValueError("new review findings must enter OPEN or DISPUTED_OPEN")

    previous = current[-1]["row_sha256"] if current else ""
    sequence = len(current)
    appended: list[dict[str, str]] = []
    for source in new_findings:
        sequence += 1
        evidence = bundle_root / source["evidence_path"]
        if not evidence.is_file():
            raise ValueError(f"feedback evidence missing: {source['evidence_path']}")
        row = {
            **source, "sequence": str(sequence),
            "evidence_sha256": sha256_file(evidence),
            "candidate_payload_sha256": candidate_digest,
            "previous_row_sha256": previous, "row_sha256": "",
        }
        row["row_sha256"] = row_sha256([row[column] for column in FEEDBACK_HEADER[:-1]])
        previous = row["row_sha256"]
        appended.append(row)
        effective[row["finding_id"]] = row

    for resolution in review_submission.get("finding_resolutions", []):
        finding_id = resolution["finding_id"]
        if finding_id not in effective:
            raise ValueError(f"review resolves unknown finding: {finding_id}")
        prior = effective[finding_id]
        if prior["status"] not in {"APPLIED_UNVERIFIED", "OPEN", "DISPUTED_OPEN"}:
            raise ValueError(f"review resolves finding in invalid state: {finding_id}")
        if not resolution_authorized(review_submission["reviewer_class"], resolution["status"], resolution.get("authority_id")):
            raise ValueError(f"reviewer authority does not permit {resolution['status']}: {finding_id}")
        evidence_rel = resolution["evidence_path"]
        evidence = bundle_root / evidence_rel
        if not evidence.is_file():
            raise ValueError(f"resolution evidence missing: {evidence_rel}")
        sequence += 1
        row = {
            "sequence": str(sequence), "finding_id": finding_id,
            "source_release": prior["source_release"], "severity": prior["severity"],
            "blocking": prior["blocking"], "status": resolution["status"],
            "summary": prior["summary"], "required_action": prior["required_action"],
            "evidence_path": evidence_rel, "evidence_sha256": sha256_file(evidence),
            "candidate_payload_sha256": candidate_digest,
            "previous_row_sha256": previous, "row_sha256": "",
        }
        row["row_sha256"] = row_sha256([row[column] for column in FEEDBACK_HEADER[:-1]])
        previous = row["row_sha256"]
        appended.append(row)
        effective[finding_id] = row

    _append_feedback_rows(path, appended)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    effective_feedback_rows(rows)
    return sha256_file(path), derive_feedback_counts(rows), rows

def _write_review_markdown(path: Path, review: dict[str, Any]) -> None:
    checks = "\n".join(f"- {row['status'].upper()}: {row['check_id']} - {row['evidence']}" for row in review["checks"])
    open_findings = "\n".join(f"- {finding}" for finding in review["open_findings"]) or "- none"
    closed_findings = "\n".join(f"- {finding}" for finding in review["closed_findings"]) or "- none"
    path.write_text(
        f"# {review['review_id']}\n\n"
        f"## Setup\n\nCandidate: `{review['candidate_version']}`. Reviewer class: `{review['reviewer_class']}`. "
        "The adjacent JSON record binds candidate, delta, governance, feedback, authoring, test, and PDF digests.\n\n"
        f"## Scope\n\n{review['review_scope']}\n\n"
        f"## Checks\n\n{checks}\n\n"
        f"## Open findings\n\n{open_findings}\n\n"
        f"## Closed findings\n\n{closed_findings}\n\n"
        f"## Verdict\n\n**{review['verdict']}** — {review['verdict_reason']}\n",
        encoding="utf-8",
    )

def _validate_parent_bundle(parent_root: Path) -> dict[str, Any]:
    state = load_json_strict(parent_root / "cycle/CYCLE_STATE.json")
    if state["active_phase"] != "AUTHORING" or "REVIEW" not in state["next_permitted_transitions"]:
        raise ValueError("parent bundle does not admit AUTHORING -> REVIEW")
    validator = parent_root / "tools/validate_complete_bundle.py"
    if not validator.is_file():
        raise ValueError("AUTHORING parent is missing tools/validate_complete_bundle.py")
    completed = subprocess.run(
        [sys.executable, str(validator), str(parent_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"parent bundle validation failed: {detail}")
    return state



def _tests_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?<![0-9])([0-9]+)\s*/\s*\1\s+(?:tests?\s+)?passed", text, re.IGNORECASE)
    if not match:
        raise ValueError("test-count evidence missing")
    return int(match.group(1))

def _candidate_id_from_source_template(source_root: Path, version: str) -> str:
    """Return the source-template candidate identity without normalizing it.

    Candidate identity is an authored protocol object, not a formatting of the
    release version. A phase materializer may only change it when a reviewed
    identity-transition record explicitly authorizes that change.
    """
    template = load_json_strict(source_root / "cycle/CYCLE_STATE.json")
    bindings = template.get("working_candidate_bindings") or template.get("working_candidate") or {}
    candidate_id = bindings.get("candidate_id")
    if not candidate_id:
        raise ValueError("source template candidate_id binding missing")
    generic = f"working_candidate_{version}"
    if candidate_id == generic:
        raise ValueError("source template candidate_id is generic version-only identity; explicit authored identity required")
    return candidate_id


def _build_once(args: argparse.Namespace, output: Path) -> dict[str, Any]:
    source_root = args.source_root.resolve()
    parent_zip = args.parent_bundle.resolve()
    parent_sha = sha256_file(parent_zip)
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        parent_root = work / "parent"
        bundle_root = work / "bundle"
        source_stage = work / "source_stage"
        parent_root.mkdir(); bundle_root.mkdir(); source_stage.mkdir()
        extract_zip_safe(parent_zip, parent_root)
        parent_expected = {path.relative_to(parent_root).as_posix() for path in parent_root.rglob("*") if path.is_file() and path.name != "BUNDLE_CONTENTS_SHA256.txt"}
        validate_sha_manifest(parent_root, parent_root / "BUNDLE_CONTENTS_SHA256.txt", expected_paths=parent_expected)
        parent_state = _validate_parent_bundle(parent_root)

        _build_source_stage(source_root, source_stage)
        source_zip = work / "source.zip"
        deterministic_zip_from_directory(source_stage, source_zip)

        # Current candidate payload.
        artifact_map = {
            "main.pdf": args.main_pdf.resolve(), "manual.pdf": args.manual_pdf.resolve(), "manual-2.pdf": args.manual2_pdf.resolve(),
            "MANUAL_I_ROADMAP.md": source_root / "MANUAL_I_ROADMAP.md", "MANUAL_II_ROADMAP.md": source_root / "MANUAL_II_ROADMAP.md",
            "source.zip": source_zip, "tests.txt": args.tests_file.resolve(), "patch_summary.txt": source_root / "patch_summary.txt",
            "MANUAL_ARTIFACT_BASELINES_SHA256.txt": source_root / "MANUAL_ARTIFACT_BASELINES_SHA256.txt",
        }
        for name, source in artifact_map.items():
            if not source.is_file():
                raise ValueError(f"candidate artifact missing: {source}")
            shutil.copyfile(source, bundle_root / name)
        external_files = _copy_external_payloads(source_root, bundle_root)
        write_sha_manifest(bundle_root / "EXTERNAL_PAYLOADS_SHA256.txt", external_files, bundle_root)
        payload_files = [bundle_root / name for name in PAYLOAD_ROOT_NAMES] + external_files
        write_sha_manifest(bundle_root / "PAYLOAD_CONTENTS_SHA256.txt", payload_files, bundle_root)
        payload_digest = sha256_file(bundle_root / "PAYLOAD_CONTENTS_SHA256.txt")

        # Stable baseline is inherited, not promoted.
        shutil.copytree(parent_root / "stable", bundle_root / "stable")
        old_stable = load_json_strict(parent_root / "stable/STABLE_BASELINE.json")
        stable_record = {
            "schema_version": "3.1", "baseline_id": old_stable["baseline_id"], "version": old_stable["version"],
            "status": "authorized_stable_payload_embedded", "source_bundle_filename": old_stable["source_bundle_filename"],
            "source_bundle_sha256": old_stable["source_bundle_sha256"], "payload_manifest_path": "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt",
            "payload_manifest_sha256": sha256_file(bundle_root / "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt"),
        }
        write_canonical_json(bundle_root / "stable/STABLE_BASELINE.json", stable_record)

        stable_rows = parse_sha_manifest(bundle_root / "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt")
        candidate_rows = parse_sha_manifest(bundle_root / "PAYLOAD_CONTENTS_SHA256.txt")
        payload_delta = _payload_delta(stable_rows, candidate_rows)
        _write_csv(bundle_root / "delta/DELTA_MANIFEST.csv", DELTA_HEADER, payload_delta)
        delete_paths = [row["path"] for row in payload_delta if row["operation"] == "delete"]
        (bundle_root / "delta/DELETE_PATHS.txt").write_text("\n".join(delete_paths) + ("\n" if delete_paths else ""), encoding="utf-8")
        (bundle_root / "delta/DELTA_PROTOCOL.md").write_text("Stable plus the ordered add/replace/delete rows must reproduce the candidate payload manifest exactly. Source-tree rows are independently recomputed from the two source archives.\n", encoding="utf-8")
        source_delta = _source_delta(_source_hash_map(bundle_root / "stable/payload/source.zip"), _source_hash_map(bundle_root / "source.zip"))
        _write_csv(bundle_root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv", SOURCE_DELTA_HEADER, source_delta)
        delta_digest = sha256_file(bundle_root / "delta/DELTA_MANIFEST.csv")
        source_delta_digest = sha256_file(bundle_root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv")
        delta_summary = {
            "schema_version": "3.1", "delta_id": f"delta_{stable_record['version']}_to_{args.version}",
            "base_version": stable_record["version"], "candidate_version": args.version,
            "delta_manifest_path": "delta/DELTA_MANIFEST.csv", "delta_manifest_sha256": delta_digest,
            "candidate_payload_manifest_sha256": payload_digest,
            "operation_counts": {kind: sum(row["operation"] == kind for row in payload_delta) for kind in ("add", "replace", "delete")},
            "source_tree_delta_manifest_path": "delta/SOURCE_TREE_DELTA_MANIFEST.csv", "source_tree_delta_manifest_sha256": source_delta_digest,
            "source_tree_operation_counts": {kind: sum(row["operation"] == kind for row in source_delta) for kind in ("add", "modify", "delete")},
        }
        write_canonical_json(bundle_root / "delta/DELTA_SUMMARY.json", delta_summary)

        _copy_control_plane(source_root, bundle_root)
        # Preserve the parent's immutable review history; source templates do
        # not replace concrete review records.
        if (parent_root / "governance/reviews").is_dir():
            shutil.copytree(parent_root / "governance/reviews", bundle_root / "governance/reviews", dirs_exist_ok=True)
        _snapshot_parent_feedback_evidence(parent_root, bundle_root)
        governance_digest = _governance_manifest(bundle_root)

        candidate_id = _candidate_id_from_source_template(source_root, args.version)
        candidate = {
            "schema_version": "3.1", "candidate_id": candidate_id, "version": args.version,
            "status": "review_candidate", "stable_baseline_version": stable_record["version"],
            "lineage_parent_bundle": parent_zip.name, "lineage_parent_sha256": parent_sha,
            "payload_manifest_path": "PAYLOAD_CONTENTS_SHA256.txt", "payload_manifest_sha256": payload_digest,
            "delta_manifest_path": "delta/DELTA_MANIFEST.csv", "delta_manifest_sha256": delta_digest,
            "source_tree_delta_manifest_path": "delta/SOURCE_TREE_DELTA_MANIFEST.csv", "source_tree_delta_manifest_sha256": source_delta_digest,
        }
        write_canonical_json(bundle_root / "candidate/WORKING_CANDIDATE.json", candidate)

        review_submission = load_json_strict(args.review_submission.resolve())
        validate_schema(review_submission, source_root / "cycle/schemas/review-template.schema.json", label="external review submission")
        if review_submission["candidate_version"] != args.version:
            raise ValueError("review submission candidate version mismatch")
        if review_submission["record_scope"] != "source_template":
            raise ValueError("review submission scope mismatch")
        submission_rel = f"governance/reviews/submissions/{review_submission['review_id']}.submission.json"
        write_canonical_json(bundle_root / submission_rel, review_submission)
        feedback_digest, feedback_counts, feedback_rows = _concrete_feedback(
            bundle_root,
            parent_root,
            payload_digest,
            review_submission,
            args.review_findings.resolve(),
            submission_rel,
        )
        sets = finding_sets(feedback_rows)
        if review_submission["open_findings"] != sets["open"]:
            raise ValueError("review submission open findings do not match feedback ledger")
        if set(review_submission["closed_findings"]) - set(sets["closed"]):
            raise ValueError("review submission closes findings not verified closed")
        upstream_status = load_json_strict(bundle_root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")
        review_outcome = derive_review_outcome(
            feedback_counts,
            reviewer_class=review_submission["reviewer_class"],
            upstream_ready=upstream_lock_ready(upstream_status),
        )
        if review_submission["verdict"] != review_outcome["verdict"] or review_submission["go_recommended"] != review_outcome["go_recommended"]:
            raise ValueError("review submission verdict is not derived from admitted findings")
        if review_submission.get("candidate_id") not in (None, candidate["candidate_id"]):
            raise ValueError("review submission candidate_id mismatch")

        author_template = load_json_strict(bundle_root / "cycle/AUTHORING_REPORT.template.json")
        authoring = {
            "schema_version": "3.1", "record_scope": "bundle_instance", "report_id": author_template["report_id"],
            "candidate_version": args.version, "authoring_attempt": author_template["authoring_attempt"], "phase": "AUTHORING",
            "classification": author_template["classification"], "implemented_changes": author_template["implemented_changes"],
            "frozen_claim": author_template["frozen_claim"], "test_count": _tests_count(bundle_root / "tests.txt"), "tests_path": "tests.txt",
            "unresolved_blockers": author_template["unresolved_blockers"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": payload_digest, "delta_manifest_sha256": delta_digest,
                "source_tree_delta_manifest_sha256": source_delta_digest, "governance_manifest_sha256": governance_digest,
                "input_feedback_template_sha256": sha256_file(bundle_root / "cycle/FEEDBACK_LEDGER.template.csv"),
            },
            "evidence_paths": [
                "tests.txt",
                "tools/validate_upstream_release_lock.py",
                "tools/validate_complete_bundle.py",
                "tools/validate_phase_bundle.py",
                "tools/run_bundle_transition.py",
                "tools/run_phase_transition.py",
                "delta/SOURCE_TREE_DELTA_MANIFEST.csv",
            ],
        }
        write_canonical_json(bundle_root / "cycle/AUTHORING_REPORT.json", authoring)
        authoring_digest = sha256_file(bundle_root / "cycle/AUTHORING_REPORT.json")

        # Reviewer-performed checks are preserved exactly from the external submission.
        checks = review_submission["checks"]
        review = {
            "schema_version": "3.1", "record_scope": "bundle_instance", "review_id": review_submission["review_id"],
            "candidate_id": candidate["candidate_id"],
            "candidate_version": args.version, "reviewer_class": review_submission["reviewer_class"],
            "review_scope": review_submission["review_scope"], "governing_constraints": review_submission["governing_constraints"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": payload_digest, "delta_manifest_sha256": delta_digest,
                "source_tree_delta_manifest_sha256": source_delta_digest, "governance_manifest_sha256": governance_digest,
                "feedback_ledger_sha256": feedback_digest, "authoring_report_sha256": authoring_digest,
                "tests_sha256": sha256_file(bundle_root / "tests.txt"), "main_pdf_sha256": sha256_file(bundle_root / "main.pdf"),
                "manual_pdf_sha256": sha256_file(bundle_root / "manual.pdf"), "manual2_pdf_sha256": sha256_file(bundle_root / "manual-2.pdf"),
            },
            "checks": checks, "finding_resolutions": review_submission.get("finding_resolutions", []), "closed_findings": review_submission["closed_findings"], "open_findings": review_submission["open_findings"],
            "counterfactuals": review_submission["counterfactuals"], "falsification_conditions": review_submission["falsification_conditions"],
            "verdict": review_outcome["verdict"], "verdict_reason": review_submission["verdict_reason"], "go_recommended": review_outcome["go_recommended"],
            "r08_status": review_outcome["r08_status"],
            "provenance": ["PAYLOAD_CONTENTS_SHA256.txt", "delta/DELTA_MANIFEST.csv", "delta/SOURCE_TREE_DELTA_MANIFEST.csv", "governance/GOVERNANCE_CONTENTS_SHA256.txt", "cycle/FEEDBACK_LEDGER.csv", "cycle/AUTHORING_REPORT.json", "tests.txt"],
        }
        review_json = bundle_root / f"governance/reviews/{review_submission['review_id']}.json"
        write_canonical_json(review_json, review)
        review_digest = sha256_file(review_json)
        _write_review_markdown(bundle_root / f"governance/reviews/{review_submission['review_id']}.md", review)
        index_path = bundle_root / "governance/reviews/REVIEW_INDEX.json"
        if index_path.is_file():
            review_index = load_json_strict(index_path)
            previous = {
                "path": review_index["canonical_review_path"],
                "sha256": review_index["canonical_review_sha256"],
                "status": "historical_noncanonical",
            }
            if previous not in review_index["historical_reviews"]:
                review_index["historical_reviews"].append(previous)
        else:
            historical_path = bundle_root / "governance/reviews/v40.03r07.2_WORKFLOW_BOOTSTRAP_REVIEW.md"
            review_index = {
                "schema_version": "3.1",
                "canonical_review_path": historical_path.relative_to(bundle_root).as_posix(),
                "canonical_review_sha256": sha256_file(historical_path),
                "historical_reviews": [],
            }
        review_index["canonical_review_path"] = review_json.relative_to(bundle_root).as_posix()
        review_index["canonical_review_sha256"] = review_digest
        write_canonical_json(index_path, review_index)

        parent_state_path = parent_root / "cycle/CYCLE_STATE.json"
        parent_ledger_path = parent_root / "cycle/TRANSITION_LEDGER.jsonl"
        if not parent_ledger_path.is_file():
            raise ValueError("nonlegacy AUTHORING parent is missing transition ledger")
        parent_ledger_bytes = parent_ledger_path.read_bytes()
        if not parent_ledger_bytes or not parent_ledger_bytes.endswith(b"\n"):
            raise ValueError("parent transition ledger is empty or noncanonical")
        parent_records = [json.loads(line) for line in parent_ledger_bytes.decode("utf-8").splitlines() if line]
        if not parent_records:
            raise ValueError("parent transition ledger is empty")
        parent_last = parent_records[-1]
        if sha256_bytes(parent_ledger_bytes) != parent_state["transition"]["ledger_sha256"]:
            raise ValueError("parent transition ledger digest/state mismatch")
        if parent_last["row_sha256"] != parent_state["transition"]["last_row_sha256"]:
            raise ValueError("parent transition last-row/state mismatch")
        if parent_last["sequence"] != parent_state["transition_sequence"]:
            raise ValueError("parent transition sequence/state mismatch")
        transition_payload = {
            "schema_version": "3.1", "sequence": int(parent_state.get("transition_sequence", 0)) + 1,
            "transition_id": f"transition_{args.version}_authoring_to_review",
            "transition_class": "ordinary_parent_prefix_plus_one", "parent_bundle": {"filename": parent_zip.name, "sha256": parent_sha},
            "predecessor_state": {"path": "cycle/CYCLE_STATE.json", "sha256": sha256_file(parent_state_path), "transition_sequence": int(parent_state.get("transition_sequence", 0))},
            "from_phase": "AUTHORING", "to_phase": "REVIEW", "candidate_id": candidate["candidate_id"],
            "bound_digests": {
                "candidate_payload_manifest_sha256": payload_digest, "delta_manifest_sha256": delta_digest,
                "source_tree_delta_manifest_sha256": source_delta_digest, "governance_manifest_sha256": governance_digest,
                "feedback_ledger_sha256": feedback_digest, "authoring_report_sha256": authoring_digest,
                "review_record_sha256": review_digest,
            },
            "open_blocking_feedback": feedback_counts["open_blocking"], "go_eligible": review_outcome["go_eligible"], "r08_status": review_outcome["r08_status"],
            "recording_semantics": "content_addressed_no_wall_clock", "previous_row_sha256": parent_last["row_sha256"],
        }
        transition = {**transition_payload, "row_sha256": sha256_bytes(canonical_json_bytes(transition_payload))}
        ledger_path = bundle_root / "cycle/TRANSITION_LEDGER.jsonl"
        ledger_path.write_bytes(parent_ledger_bytes + canonical_json_bytes(transition))
        transition_digest = sha256_file(ledger_path)

        state_template = load_json_strict(bundle_root / "cycle/CYCLE_STATE.json")
        state = {
            "schema_version": "3.1", "record_scope": "bundle_instance", "project_id": "AOD",
            "cycle_protocol_id": "AOD_BUNDLE_CYCLE", "protocol_version": "3.1", "active_phase": "REVIEW",
            "last_completed_phase": "AUTHORING", "authoring_attempt": state_template["authoring_attempt"],
            "transition_sequence": transition["sequence"], "canonical_state_rule": state_template["canonical_state_rule"],
            "lineage_parent": {"filename": parent_zip.name, "sha256": parent_sha},
            "release": {
                "stable_version": state_template["release"]["stable_version"],
                "status": "review_candidate",
                "target_version": args.version,
                "working_version": args.version,
            },
            "working_candidate": {
                "candidate_id": candidate["candidate_id"], "payload_manifest_path": "PAYLOAD_CONTENTS_SHA256.txt",
                "payload_manifest_sha256": payload_digest, "delta_manifest_path": "delta/DELTA_MANIFEST.csv",
                "delta_manifest_sha256": delta_digest, "source_tree_delta_manifest_path": "delta/SOURCE_TREE_DELTA_MANIFEST.csv",
                "source_tree_delta_manifest_sha256": source_delta_digest, "governance_manifest_path": "governance/GOVERNANCE_CONTENTS_SHA256.txt",
                "governance_manifest_sha256": governance_digest,
            },
            "feedback_counts": feedback_counts,
            "review": {"record_path": review_json.relative_to(bundle_root).as_posix(), "record_sha256": review_digest, "verdict": review["verdict"]},
            "transition": {"ledger_path": "cycle/TRANSITION_LEDGER.jsonl", "ledger_sha256": transition_digest, "last_row_sha256": transition["row_sha256"]},
            "go": {**state_template["go"], "eligible": review_outcome["go_eligible"], "blocking_reason": review_outcome["blocking_reason"]}, "next_permitted_transitions": (["GO"] if review_outcome["go_eligible"] else ["FEEDBACK"]),
            "upstream_release_state": {
                "canonical_lock_status": load_json_strict(bundle_root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json")["refresh_attempt_status"],
                "policy": "governance/UPSTREAM_RELEASE_POLICY.json",
                "required_dependencies": ["AF", "AFC", "GM", "AOD"],
                "source_registry": "governance/REPOSITORY_RELEASE_SOURCES.json",
            },
        }
        write_canonical_json(bundle_root / "cycle/CYCLE_STATE.json", state)
        update_workflow_state(
            bundle_root / "BUNDLE_WORKFLOW.md",
            phase="REVIEW",
            candidate_version=candidate["version"],
            candidate_status=candidate["status"],
            release_status=state["release"]["status"],
            counts=feedback_counts,
            verdict=review["verdict"],
            go_eligible=review_outcome["go_eligible"],
            r08_status="BLOCKED",
            next_transitions=state["next_permitted_transitions"],
        )

        # Root pointer must bind the canonical governance record.
        pointer = load_json_strict(bundle_root / "GLOBAL_INSTRUCTIONS.json")
        pointer["canonical_sha256"] = sha256_file(bundle_root / pointer["canonical_path"])
        write_canonical_json(bundle_root / "GLOBAL_INSTRUCTIONS.json", pointer)

        bundle_files = [path for path in bundle_root.rglob("*") if path.is_file() and path.name != "BUNDLE_CONTENTS_SHA256.txt"]
        write_sha_manifest(bundle_root / "BUNDLE_CONTENTS_SHA256.txt", bundle_files, bundle_root)
        deterministic_zip_from_directory(bundle_root, output)

        # Validate the emitted bytes, not merely the staging tree.
        emitted = work / "emitted"
        extract_zip_safe(output, emitted)
        sys.path.insert(0, str(source_root / "tools"))
        from validate_complete_bundle import validate as validate_complete
        report = validate_complete(emitted)
        report["bundle_sha256"] = sha256_file(output)
        return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-bundle", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--main-pdf", type=Path, required=True)
    parser.add_argument("--manual-pdf", type=Path, required=True)
    parser.add_argument("--manual2-pdf", type=Path, required=True)
    parser.add_argument("--tests-file", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--review-submission", type=Path, required=True)
    parser.add_argument("--review-findings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"v[0-9]+(?:\.[0-9]+)*(?:r[0-9]+(?:\.[0-9]+)*)?", args.version):
        raise ValueError("invalid version")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        args.output.unlink()
    report = _build_once(args, args.output.resolve())
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
