#!/usr/bin/env python3
"""Build AOD release source and bundle artifacts from the current tree.

Source-internal paths are generic. Generated release artifact names are stable
so Zenodo latest-file links keep working across revisions; the release version is
recorded in metadata and manifests.
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
    ".github", "appendices", "figures_jpg", "manual", "scripts", "sections", "tests",
    "CANONICAL_VERSION.txt", "RELEASE_READINESS.txt", "main.tex", "preamble.tex",
    "refs.bib", "cycle_shedding_summary.tex", "README.md", "LICENSE", "CITATION.cff",
    "requirements-ci.txt", ".zenodo.json", "BUILD.md",
]


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


def build_source_tree(stage_root: Path) -> list[Path]:
    source_root = stage_root / "AOD_Temporal_Dynamics_source"
    source_root.mkdir(parents=True, exist_ok=True)
    for name in INCLUDE_TOP_LEVEL:
        src = ROOT / name
        if src.exists():
            copy_item(src, source_root / name)
    return sorted([p for p in source_root.rglob("*") if p.is_file()])




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
        raise ValueError(".zenodo.json references must be synchronized from refs.bib and manual/refs.bib")


def zip_dir(src_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(src_dir.parent).as_posix())


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
    ap.add_argument("--tests", default="tests.txt")
    ap.add_argument("--patch-summary", default="PATCH_SUMMARY.txt")
    args = ap.parse_args()

    version = read_version(args.version)
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
    tests_txt = (ROOT / args.tests).resolve()
    for required in [main_pdf, manual_pdf, tests_txt]:
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
    tests_out = outdir / "tests.txt"
    shutil.copy2(main_pdf, main_out)
    shutil.copy2(manual_pdf, manual_out)
    shutil.copy2(tests_txt, tests_out)

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        source_files = build_source_tree(stage)
        source_zip = outdir / "source.zip"
        zip_dir(stage / "AOD_Temporal_Dynamics_source", source_zip)


    # Bundle uses stable internal names so downstream tools do not depend on the version.
    bundle_tmp = outdir / "_bundle"
    bundle_tmp.mkdir(parents=True, exist_ok=True)
    shutil.copy2(main_out, bundle_tmp / "main.pdf")
    shutil.copy2(manual_out, bundle_tmp / "manual.pdf")
    shutil.copy2(source_zip, bundle_tmp / "source.zip")
    shutil.copy2(tests_out, bundle_tmp / "tests.txt")
    shutil.copy2(patch_summary, bundle_tmp / "patch_summary.txt")
    bundle_contents = bundle_tmp / "BUNDLE_CONTENTS_SHA256.txt"
    bundle_members = [p for p in bundle_tmp.iterdir() if p.is_file() and p.name != "BUNDLE_CONTENTS_SHA256.txt"]
    write_sha_manifest(bundle_contents, sorted(bundle_members), bundle_tmp)

    bundle_zip = outdir / "bundle.zip"
    bundle_order = [
        "main.pdf",
        "manual.pdf",
        "source.zip",
        "tests.txt",
        "patch_summary.txt",
        "BUNDLE_CONTENTS_SHA256.txt",
    ]
    with zipfile.ZipFile(bundle_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in bundle_order:
            p = bundle_tmp / name
            if p.is_file():
                zf.write(p, p.name)

    bundle_contents_out = outdir / "BUNDLE_CONTENTS_SHA256.txt"
    shutil.copy2(bundle_contents, bundle_contents_out)

    sha_out = outdir / "SHA256.txt"
    top_files = [main_out, manual_out, source_zip, tests_out, patch_summary, bundle_contents_out, bundle_zip]
    write_sha_manifest(sha_out, top_files)
    shutil.rmtree(bundle_tmp)

    print(f"built release artifacts for {version} in {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
