#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

EXCLUDED_PARTS = {"dist", ".pytest_cache", "__pycache__"}
DUPLICATE_SURFACES = [
    "BUNDLE_WORKFLOW.md",
    "MANUAL_I_ROADMAP.md",
    "MANUAL_II_ROADMAP.md",
    "patch_summary.txt",
    "GLOBAL_INSTRUCTIONS.json",
    "MANUAL_ARTIFACT_BASELINES_SHA256.txt",
]
CLOSED_LANE_NEEDLES = [
    "target joins",
    "SI report",
    "metric report",
    "residual",
    "scores",
    "empirical comparisons",
    "subject/reference phase locks",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in EXCLUDED_PARTS for part in p.parts):
            h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
            h.update(p.read_bytes())
    return h.hexdigest()


def check_source_root(root: Path, *, strict_source: bool) -> list[str]:
    errors: list[str] = []
    state_path = root / "governance/RELEASE_METADATA_STATE.json"
    if not state_path.is_file():
        return [f"missing {state_path}"] if strict_source else []
    state = load_json(state_path)
    version = state.get("candidate_version")
    title = state.get("active_goal_title") or state.get("active_repair_scope")
    baseline = state.get("stable_baseline_version")
    manual2_hash = state.get("manual2_source_tree_hash")
    next_milestone = state.get("next_milestone", {})
    next_version = next_milestone.get("version")
    next_title = next_milestone.get("title")

    required = {
        "README.md": [version, title, f"This package opens the {version} AUTHORING lane"],
        "CANONICAL_VERSION.txt": ["Canonical version:", version, baseline, manual2_hash],
        "RELEASE_READINESS.txt": ["Canonical package:", "Canonical version:", version, baseline, manual2_hash],
        "BUNDLE_WORKFLOW.md": ["<!-- AOD_STATE_BEGIN -->", "<!-- AOD_STATE_END -->", version, baseline, title],
        "MANUAL_I_ROADMAP.md": [version, title],
        "MANUAL_II_ROADMAP.md": [version, title],
    }
    for rel, needles in required.items():
        path = root / rel
        if not path.is_file():
            if strict_source:
                errors.append(f"missing surface {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle and str(needle) not in text:
                errors.append(f"{rel} missing {needle!r}")

    # README must not advertise a stale prior lane as the current package opening.
    readme = root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        stale = "This package opens the v40.03r25.1 AUTHORING lane"
        if stale in text and version != "v40.03r25.1":
            errors.append("README.md advertises stale v40.03r25.1 opening as current lane")

    if (root / "manual-2").is_dir():
        actual = tree_hash(root / "manual-2")
        if manual2_hash != actual:
            errors.append(f"manual-2 tree hash mismatch: {manual2_hash} != {actual}")

    canonical = root / "CANONICAL_VERSION.txt"
    if canonical.is_file() and manual2_hash:
        if f"Manual-II source-tree hash: {manual2_hash}" not in canonical.read_text(encoding="utf-8"):
            errors.append("CANONICAL_VERSION.txt missing active Manual-II source-tree hash binding")

    zpath = root / ".zenodo.json"
    if zpath.is_file():
        z = load_json(zpath)
        if z.get("version") != version:
            errors.append(f".zenodo.json version mismatch: {z.get('version')} != {version}")
        if str(z.get("license")).lower() != "mit":
            errors.append(".zenodo.json license mismatch")
        description = z.get("description", "")
        if title and title.split(" / ")[0] not in description and title not in description:
            errors.append(".zenodo.json description missing active title fragment")

    for rel in ["README.md", "RELEASE_READINESS.txt", "MANUAL_II_ROADMAP.md"]:
        path = root / rel
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for needle in CLOSED_LANE_NEEDLES:
                if needle not in text:
                    errors.append(f"{rel} missing closed-lane scaffold {needle!r}")

    if next_version and next_title:
        joined = "\n".join(
            (root / rel).read_text(encoding="utf-8")
            for rel in ["README.md", "MANUAL_I_ROADMAP.md", "MANUAL_II_ROADMAP.md", "CANONICAL_VERSION.txt"]
            if (root / rel).is_file()
        )
        if next_version not in joined or next_title not in joined:
            errors.append("next milestone is not synchronized across roadmap/canonical surfaces")

    return errors



def check_workflow_phase_surfaces(bundle_root: Path, source_root: Path) -> list[str]:
    errors: list[str] = []
    root_workflow = bundle_root / "BUNDLE_WORKFLOW.md"
    source_workflow = source_root / "BUNDLE_WORKFLOW.md"
    root_state_path = bundle_root / "cycle/CYCLE_STATE.json"
    source_state_path = source_root / "cycle/CYCLE_STATE.json"
    if not all(path.is_file() for path in (root_workflow, source_workflow, root_state_path, source_state_path)):
        return errors
    root_state = load_json(root_state_path)
    source_state = load_json(source_state_path)
    root_phase = root_state.get("active_phase")
    source_phase = source_state.get("active_phase")
    version = root_state.get("release", {}).get("target_version") or root_state.get("release", {}).get("working_version")
    root_text = root_workflow.read_text(encoding="utf-8")
    source_text = source_workflow.read_text(encoding="utf-8")
    if root_phase == "AUTHORING":
        if root_workflow.read_bytes() != source_workflow.read_bytes():
            errors.append("root/source duplicate mismatch: BUNDLE_WORKFLOW.md")
        return errors
    if root_phase not in {"REVIEW", "GO", "FEEDBACK"}:
        errors.append(f"unsupported bundle workflow phase: {root_phase}")
        return errors
    if source_phase != "AUTHORING":
        errors.append(f"embedded source workflow phase must remain AUTHORING, found {source_phase}")
    if "Current state: AUTHORING." not in source_text:
        errors.append("embedded source BUNDLE_WORKFLOW.md missing AUTHORING state block")
    if f"Current state: {root_phase}." not in root_text:
        errors.append(f"root BUNDLE_WORKFLOW.md missing {root_phase} state block")
    if version:
        marker = f"Candidate version: {version}."
        if marker not in root_text:
            errors.append("root BUNDLE_WORKFLOW.md candidate version mismatch")
        if marker not in source_text:
            errors.append("embedded source BUNDLE_WORKFLOW.md candidate version mismatch")
    if root_workflow.read_bytes() == source_workflow.read_bytes():
        errors.append("phase-instance BUNDLE_WORKFLOW.md was not materialized separately from embedded AUTHORING source")
    return errors

def check_bundle_root(root: Path) -> list[str]:
    errors: list[str] = []
    if not (root / "source.zip").is_file():
        return check_source_root(root, strict_source=True)
    with tempfile.TemporaryDirectory() as d:
        source_root = Path(d) / "source"
        source_root.mkdir()
        with zipfile.ZipFile(root / "source.zip") as z:
            z.extractall(source_root)
        errors.extend("source.zip:" + e for e in check_source_root(source_root, strict_source=True))
        errors.extend(check_source_root(root, strict_source=False))
        errors.extend(check_workflow_phase_surfaces(root, source_root))
        for rel in DUPLICATE_SURFACES:
            if rel == "BUNDLE_WORKFLOW.md":
                continue
            outer = root / rel
            inner = source_root / rel
            if outer.is_file() and inner.is_file() and outer.read_bytes() != inner.read_bytes():
                errors.append(f"root/source duplicate mismatch: {rel}")
    return errors



def check_active_goal_artifact_policy(root: Path) -> list[str]:
    errors: list[str] = []
    goal_path = root / "cycle/ACTIVE_GOAL.json"
    if not goal_path.is_file():
        return errors
    goal = load_json(goal_path)
    frozen = set(goal.get("frozen_artifacts", []))
    revised = set(goal.get("intentionally_revised_artifacts", []))
    overlap = sorted(frozen & revised)
    if overlap:
        errors.append("active goal artifact appears in both frozen and intentionally revised sets: " + ", ".join(overlap))
    payload_delta = root / "delta/DELTA_MANIFEST.csv"
    source_delta = root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"
    changed: set[str] = set()
    import csv
    for path in (payload_delta, source_delta):
        if path.is_file():
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    changed.add(row.get("path", ""))
    for item in frozen:
        prefix = item.rstrip("/") + "/" if item.endswith("/") else item
        for path in changed:
            if path == item or (item.endswith("/") and path.startswith(prefix)):
                errors.append(f"frozen artifact changed by active delta: {item} -> {path}")
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    errors = check_bundle_root(root)
    errors.extend(check_active_goal_artifact_policy(root))
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({"status": "passed", "validator": "surface_synchronization"}, sort_keys=True))


if __name__ == "__main__":
    main()
