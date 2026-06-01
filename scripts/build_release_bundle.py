#!/usr/bin/env python3
"""Build AOD release source and bundle artifacts from the current tree.

This script deliberately keeps source-internal paths generic. Versioned names are
created only as release artifacts from CANONICAL_VERSION.txt or --version.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
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
    "requirements-ci.txt", ".zenodo.json", "BUILD.md", "build.yml",
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



def require_tests_artifact(tests_txt: Path) -> bool:
    """Require the canonical pytest output artifact.

    The release bundle consumes tests.txt directly. CI and local release builds
    must create this artifact before invoking this builder. SymPy
    exact-arithmetic checks live inside the pytest suite. The builder does not
    run tests and does not consume verifier/audit-pack logs.
    """
    if not tests_txt.exists() or tests_txt.stat().st_size == 0:
        print(f"required test artifact missing or empty: {tests_txt}", file=sys.stderr)
        print("create tests.txt from the pytest suite before invoking this builder", file=sys.stderr)
        return False
    return True

def build_source_only(outdir: Path) -> Path:
    """Build only the generic source-clean archive for legacy workflow calls.

    This mode is used only when the script is invoked with no command-line
    arguments. It keeps older CI calls from failing while preserving the
    release-bundle rule: full release bundles still require an explicit
    pytest-produced tests.txt artifact.
    """
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        build_source_tree(stage)
        source_clean = outdir / "source-clean.zip"
        zip_dir(stage / "AOD_Temporal_Dynamics_source", source_clean)
    print(f"built generic source archive: {source_clean}")
    return source_clean


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version")
    ap.add_argument("--outdir", default="dist")
    ap.add_argument("--main", default="main.pdf")
    ap.add_argument("--manual", default="manual.pdf")
    ap.add_argument("--tests", default="tests.txt")
    ap.add_argument("--patch-summary", default="PATCH_SUMMARY.txt")
    args = ap.parse_args()

    # Compatibility path for stale/legacy workflows that invoke the builder as
    # `python3 scripts/build_release_bundle.py` only to create a source archive.
    # Full release bundle generation still requires explicit artifact arguments
    # and a pytest-produced tests.txt.
    if len(sys.argv) == 1:
        build_source_only((ROOT / args.outdir).resolve())
        return 0

    version = read_version(args.version)
    slug = version_slug(version)
    prefix = f"AOD_Temporal_Dynamics_v{slug}"
    outdir = (ROOT / args.outdir).resolve()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    main_pdf = (ROOT / args.main).resolve()
    manual_pdf = (ROOT / args.manual).resolve()
    tests_txt = (ROOT / args.tests).resolve()
    for required in [main_pdf, manual_pdf]:
        if not required.exists():
            print(f"required artifact missing: {required}", file=sys.stderr)
            return 2
    if not require_tests_artifact(tests_txt):
        return 2

    patch_summary_src = (ROOT / args.patch_summary).resolve()
    patch_summary = outdir / f"{prefix}_PATCH_SUMMARY.txt"
    if patch_summary_src.exists():
        shutil.copy2(patch_summary_src, patch_summary)
    else:
        patch_summary.write_text(
            f"{version} release bundle generated by scripts/build_release_bundle.py.\n",
            encoding="utf-8",
        )

    main_out = outdir / f"{prefix}_main.pdf"
    manual_out = outdir / f"{prefix}_manual.pdf"
    tests_out = outdir / f"{prefix}_tests.txt"
    shutil.copy2(main_pdf, main_out)
    shutil.copy2(manual_pdf, manual_out)
    shutil.copy2(tests_txt, tests_out)

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        source_files = build_source_tree(stage)
        source_zip = outdir / f"{prefix}_source.zip"
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

    bundle_zip = outdir / f"{prefix}_bundle.zip"
    with zipfile.ZipFile(bundle_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(bundle_tmp.iterdir()):
            if p.is_file():
                zf.write(p, p.name)

    bundle_contents_out = outdir / f"{prefix}_BUNDLE_CONTENTS_SHA256.txt"
    shutil.copy2(bundle_contents, bundle_contents_out)

    sha_out = outdir / f"{prefix}_SHA256.txt"
    top_files = [main_out, manual_out, source_zip, tests_out, patch_summary, bundle_contents_out, bundle_zip]
    write_sha_manifest(sha_out, top_files)
    shutil.rmtree(bundle_tmp)

    print(f"built release artifacts for {version} in {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
