#!/usr/bin/env python3
"""Build AOD release source and bundle artifacts from the current tree.

Source-internal paths are generic. The source archive is always flat so it can be
unzipped directly into a repository checkout. The primary bundle is versioned
(`bundle-<version>.zip`) while a stable `bundle.zip` compatibility alias is also
written for downstream tooling.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]

# This file remains the low-level legacy payload packager. The canonical complete
# cycle-bundle command is tools/run_bundle_transition.py.
CANONICAL_COMPLETE_BUNDLE_COMMAND = "tools/run_bundle_transition.py"

EXCLUDE_DIR_NAMES = {
    ".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache",
    ".DS_Store", "dist", "build", "release", "_render", "_renders"
}

EXCLUDE_SUFFIXES = {
    ".pdf", ".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk",
    ".xdv", ".synctex.gz", ".pyc", ".pyo", ".bbl", ".blg", ".run.xml"
}

EXCLUDE_FILE_PATTERNS = [
    re.compile(r"AOD_Temporal_Dynamics_v.*_PATCH_SUMMARY\.txt$"),
    re.compile(r"AOD_Temporal_Dynamics_v.*_SHA256\.txt$"),
    re.compile(r"AOD_Temporal_Dynamics_v.*_BUNDLE_CONTENTS_SHA256\.txt$"),
    re.compile(r"AOD_Temporal_Dynamics_v.*_tests\.txt$"),
]

INCLUDE_TOP_LEVEL = [
    ".github", "appendices", "figures_jpg", "manual", "manual-2", "shared", "scripts", "sections", "tests", "governance", "cycle", "tools",
    "CANONICAL_VERSION.txt", "RELEASE_READINESS.txt", "main.tex", "preamble.tex",
    "refs.bib", "cycle_shedding_summary.tex", "README.md", "LICENSE", "CITATION.cff",
    "requirements-ci.txt", ".zenodo.json", "BUILD.md", "MANUAL_I_ROADMAP.md", "MANUAL_II_ROADMAP.md",
    "MANUAL_ARTIFACT_BASELINES_SHA256.txt", "GLOBAL_INSTRUCTIONS.json", "BUNDLE_WORKFLOW.md", "patch_summary.txt",
]


# The inventory is the authoritative allowlist for direct bundle payloads.
# Files are never discovered recursively for embedding: each embedded asset must
# have one registered source path, one stable bundle path, a byte count, and a
# SHA-256.
BUNDLE_EXTERNAL_PAYLOAD_INVENTORY = (
    ROOT / "manual-2" / "data" / "protein" / "external_payload_bundle_inventory.csv"
)
BUNDLE_EXTERNAL_PAYLOAD_SCAN_ROOTS = [
    ROOT / "manual-2" / "data" / "protein" / "external_pdb_payloads",
    ROOT / "manual-2" / "data" / "protein" / "external_pdb_validation_payloads",
    ROOT / "manual-2" / "data" / "protein" / "external_pdb_probe_evidence_snapshots",
]
REQUIRED_EXTERNAL_PAYLOAD_INVENTORY_COLUMNS = {
    "source_path", "bundle_path", "payload_class", "payload_status",
    "origin_class", "required_for_release", "embedding_class",
    "payload_byte_count", "payload_sha256", "inline_embedding_limit_bytes",
    "redistribution_status", "license_or_terms_ref", "source_url",
    "retrieval_or_registration_timestamp_utc", "payload_pack_id",
}


def read_version(explicit: str | None) -> str:
    if explicit:
        return explicit
    p = ROOT / "CANONICAL_VERSION.txt"
    if not p.exists():
        return "release"
    m = re.search(r"Canonical version:\s*(\S+)", p.read_text(encoding="utf-8"))
    return m.group(1) if m else "release"


def version_slug(version: str) -> str:
    return version.strip().lstrip("v").replace(".", "_").replace("-", "_")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIR_NAMES:
        return True
    name = path.name
    if any(rx.match(name) for rx in EXCLUDE_FILE_PATTERNS):
        return True
    # Governance imports and resolved release assets are canonical embedded inputs,
    # not generated project PDFs; retain them in the flat source archive.
    if "governance" in parts and ({"imports", "releases"} & parts):
        return name.endswith((".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk", ".pyc"))
    return any(name.endswith(suf) for suf in EXCLUDE_SUFFIXES)


def copy_item(src: Path, dst: Path) -> None:
    if not src.exists() or excluded(src):
        return
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    elif src.is_dir():
        for p in src.rglob("*"):
            if excluded(p):
                continue
            rel = p.relative_to(src)
            target = dst / rel
            if p.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)


def build_source_tree(stage_root: Path) -> Path:
    """Build a flat source tree whose contents unzip directly into a repo root."""
    source_root = stage_root / "source_root"
    source_root.mkdir(parents=True, exist_ok=True)
    for name in INCLUDE_TOP_LEVEL:
        src = ROOT / name
        if src.exists():
            copy_item(src, source_root / name)
    return source_root




def read_external_payload_inventory() -> list[dict[str, str]]:
    import csv

    if not BUNDLE_EXTERNAL_PAYLOAD_INVENTORY.is_file():
        raise FileNotFoundError(f"external payload inventory missing: {BUNDLE_EXTERNAL_PAYLOAD_INVENTORY}")
    with BUNDLE_EXTERNAL_PAYLOAD_INVENTORY.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_EXTERNAL_PAYLOAD_INVENTORY_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"external payload inventory columns missing: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("external payload inventory is empty")
    return rows


def validate_required_bundle_external_payloads() -> list[dict[str, str]]:
    rows = read_external_payload_inventory()
    source_seen: set[str] = set()
    bundle_seen: set[str] = set()
    registered_source_paths: set[Path] = set()
    errors: list[str] = []

    for row in rows:
        source_rel = row["source_path"]
        bundle_rel = row["bundle_path"]
        if source_rel in source_seen:
            errors.append(f"duplicate source_path: {source_rel}")
        if bundle_rel in bundle_seen:
            errors.append(f"duplicate bundle_path: {bundle_rel}")
        source_seen.add(source_rel)
        bundle_seen.add(bundle_rel)
        if not bundle_rel.startswith("external_payloads/") or ".." in Path(bundle_rel).parts:
            errors.append(f"unsafe bundle_path: {bundle_rel}")
        src = ROOT / source_rel
        registered_source_paths.add(src.resolve())
        required = row["required_for_release"].strip().lower() in {"yes", "true", "1"}
        if required and not src.is_file():
            errors.append(f"required payload missing: {source_rel}")
            continue
        if not src.is_file():
            continue
        actual_size = src.stat().st_size
        actual_sha = sha256_file(src)
        if str(actual_size) != row["payload_byte_count"]:
            errors.append(f"byte-count mismatch for {source_rel}: {actual_size} != {row['payload_byte_count']}")
        if actual_sha != row["payload_sha256"]:
            errors.append(f"SHA-256 mismatch for {source_rel}: {actual_sha} != {row['payload_sha256']}")
        if row["embedding_class"] == "inline_bundle":
            limit = int(row["inline_embedding_limit_bytes"] or "0")
            if limit and actual_size > limit:
                errors.append(f"inline payload exceeds frozen limit: {source_rel}")

    # Every committed file in the canonical archive-payload directories must be
    # registered. Policy metadata outside those directories is registered by
    # explicit inventory rows.
    for root in BUNDLE_EXTERNAL_PAYLOAD_SCAN_ROOTS:
        if root.exists():
            for src in root.rglob("*"):
                if src.is_file() and src.resolve() not in registered_source_paths:
                    errors.append(f"unregistered committed external payload: {src.relative_to(ROOT)}")

    if errors:
        raise ValueError("external payload inventory validation failed:\n" + "\n".join(errors))
    return rows


def copy_bundle_external_payloads(bundle_root: Path) -> list[Path]:
    """Copy only inventory-authorized inline payloads into the bundle."""
    rows = validate_required_bundle_external_payloads()
    copied: list[Path] = []
    for row in rows:
        if row["embedding_class"] != "inline_bundle":
            continue
        src = ROOT / row["source_path"]
        if not src.is_file():
            continue
        dst = bundle_root / row["bundle_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha256_file(dst) != row["payload_sha256"] or str(dst.stat().st_size) != row["payload_byte_count"]:
            raise ValueError(f"embedded payload verification failed: {row['bundle_path']}")
        copied.append(dst)
    return sorted(copied)



def check_zenodo_references() -> None:
    sync_script = ROOT / "scripts" / "sync_zenodo_references.py"
    if sync_script.exists():
        subprocess.run([sys.executable, str(sync_script), "--check"], check=True)


def validate_zenodo_metadata(version: str) -> None:
    """Validate repository-root .zenodo.json used by GitHub-Zenodo sync."""
    meta_path = ROOT / ".zenodo.json"
    if not meta_path.exists():
        raise FileNotFoundError("repository-root .zenodo.json is required for GitHub-Zenodo sync")
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    if data.get("version") != version:
        raise ValueError(f".zenodo.json version {data.get('version')!r} does not match {version!r}")
    if not data.get("title"):
        raise ValueError(".zenodo.json title is required")
    if "references" not in data or not data["references"]:
        raise ValueError(".zenodo.json references must be synchronized from refs.bib, manual/refs.bib, and manual-2/refs.bib")


def zip_dir(src_dir: Path, zip_path: Path) -> None:
    """Zip the *contents* of src_dir, not src_dir itself.

    The source archive is intentionally flat: unzipping source.zip into a
    repository checkout writes files directly into that checkout instead of
    creating an extra wrapper directory.
    """
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(src_dir).as_posix())


def write_sha_manifest(path: Path, files: list[Path], base: Path | None = None) -> None:
    lines = []
    for f in files:
        rel = f.relative_to(base).as_posix() if base else f.name
        lines.append(f"{sha256_file(f)}  {rel}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version")
    ap.add_argument("--outdir", default="dist")
    ap.add_argument("--main", default="main.pdf")
    ap.add_argument("--manual", default="manual.pdf")
    ap.add_argument("--manual2", default="manual-2.pdf")
    ap.add_argument("--tests", default="tests.txt")
    ap.add_argument("--patch-summary", default="patch_summary.txt")
    ap.add_argument("--manual-roadmap", default="MANUAL_I_ROADMAP.md")
    ap.add_argument("--roadmap", default="MANUAL_II_ROADMAP.md")
    args = ap.parse_args()

    version = read_version(args.version)
    validate_required_bundle_external_payloads()
    check_zenodo_references()
    validate_zenodo_metadata(version)
    slug = version_slug(version)
    prefix = "AOD_Temporal_Dynamics"
    outdir = (ROOT / args.outdir).resolve()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    main_pdf = (ROOT / args.main).resolve()
    manual_pdf = (ROOT / args.manual).resolve()
    manual2_pdf = (ROOT / args.manual2).resolve()
    tests_txt = (ROOT / args.tests).resolve()
    manual_roadmap_src = (ROOT / args.manual_roadmap).resolve()
    roadmap_src = (ROOT / args.roadmap).resolve()
    manual_baseline_src = (ROOT / "MANUAL_ARTIFACT_BASELINES_SHA256.txt").resolve()
    for required in [main_pdf, manual_pdf, manual2_pdf, tests_txt, manual_roadmap_src, roadmap_src, manual_baseline_src]:
        if not required.exists():
            print(f"required artifact missing: {required}", file=sys.stderr)
            return 2

    patch_summary_src = (ROOT / args.patch_summary).resolve()
    patch_summary = outdir / "patch_summary.txt"
    if patch_summary_src.exists():
        shutil.copy2(patch_summary_src, patch_summary)
    else:
        patch_summary.write_text(
            f"{version} release bundle generated by scripts/build_release_bundle.py.\n",
            encoding="utf-8",
        )

    main_out = outdir / "main.pdf"
    manual_out = outdir / "manual.pdf"
    manual2_out = outdir / "manual-2.pdf"
    manual_roadmap_out = outdir / "MANUAL_I_ROADMAP.md"
    roadmap_out = outdir / "MANUAL_II_ROADMAP.md"
    tests_out = outdir / "tests.txt"
    manual_baseline_out = outdir / "MANUAL_ARTIFACT_BASELINES_SHA256.txt"
    shutil.copy2(main_pdf, main_out)
    shutil.copy2(manual_pdf, manual_out)
    shutil.copy2(manual2_pdf, manual2_out)
    shutil.copy2(manual_roadmap_src, manual_roadmap_out)
    shutil.copy2(roadmap_src, roadmap_out)
    shutil.copy2(tests_txt, tests_out)
    shutil.copy2(manual_baseline_src, manual_baseline_out)

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        source_root = build_source_tree(stage)
        source_zip = outdir / "source.zip"
        zip_dir(source_root, source_zip)


    # Bundle uses stable internal names so downstream tools do not depend on the version.
    bundle_tmp = outdir / "_bundle"
    bundle_tmp.mkdir(parents=True, exist_ok=True)
    shutil.copy2(main_out, bundle_tmp / "main.pdf")
    shutil.copy2(manual_out, bundle_tmp / "manual.pdf")
    shutil.copy2(manual2_out, bundle_tmp / "manual-2.pdf")
    shutil.copy2(manual_roadmap_out, bundle_tmp / "MANUAL_I_ROADMAP.md")
    shutil.copy2(roadmap_out, bundle_tmp / "MANUAL_II_ROADMAP.md")
    shutil.copy2(source_zip, bundle_tmp / "source.zip")
    shutil.copy2(tests_out, bundle_tmp / "tests.txt")
    shutil.copy2(patch_summary, bundle_tmp / "patch_summary.txt")
    shutil.copy2(manual_baseline_out, bundle_tmp / "MANUAL_ARTIFACT_BASELINES_SHA256.txt")

    external_payload_files = copy_bundle_external_payloads(bundle_tmp)
    external_payload_manifest = bundle_tmp / "EXTERNAL_PAYLOADS_SHA256.txt"
    write_sha_manifest(external_payload_manifest, external_payload_files, bundle_tmp)

    bundle_contents = bundle_tmp / "BUNDLE_CONTENTS_SHA256.txt"
    bundle_members = [
        p for p in bundle_tmp.rglob("*")
        if p.is_file() and p.name != "BUNDLE_CONTENTS_SHA256.txt"
    ]
    write_sha_manifest(bundle_contents, sorted(bundle_members), bundle_tmp)

    bundle_versioned_zip = outdir / f"bundle-{version}.zip"
    bundle_zip = outdir / "bundle.zip"
    bundle_order = [
        "main.pdf",
        "manual.pdf",
        "manual-2.pdf",
        "MANUAL_I_ROADMAP.md",
        "MANUAL_II_ROADMAP.md",
        "source.zip",
        "tests.txt",
        "patch_summary.txt",
        "MANUAL_ARTIFACT_BASELINES_SHA256.txt",
        "EXTERNAL_PAYLOADS_SHA256.txt",
        "BUNDLE_CONTENTS_SHA256.txt",
    ]
    with zipfile.ZipFile(bundle_versioned_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in bundle_order:
            p = bundle_tmp / name
            if p.is_file():
                zf.write(p, p.name)
        payload_root = bundle_tmp / "external_payloads"
        if payload_root.exists():
            for p in sorted(payload_root.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(bundle_tmp).as_posix())
    shutil.copy2(bundle_versioned_zip, bundle_zip)

    bundle_contents_out = outdir / "BUNDLE_CONTENTS_SHA256.txt"
    shutil.copy2(bundle_contents, bundle_contents_out)
    external_payloads_out = outdir / "EXTERNAL_PAYLOADS_SHA256.txt"
    shutil.copy2(external_payload_manifest, external_payloads_out)

    sha_out = outdir / "SHA256.txt"
    top_files = [
        main_out,
        manual_out,
        manual2_out,
        manual_roadmap_out,
        roadmap_out,
        source_zip,
        tests_out,
        patch_summary,
        manual_baseline_out,
        bundle_contents_out,
        external_payloads_out,
        bundle_versioned_zip,
        bundle_zip,
    ]
    write_sha_manifest(sha_out, top_files)
    shutil.rmtree(bundle_tmp)

    print(f"built release artifacts for {version} in {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
