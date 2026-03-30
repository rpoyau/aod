#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

INCLUDE_TOP_LEVEL = [
    "README.md",
    ".zenodo.json",
    ".zenodo_doi",
    "main.tex",
    "supplement-a.tex",
    "supplement-b.tex",
    "main.pdf",
    "supplement-a.pdf",
    "supplement-b.pdf",
]

INCLUDE_DIRS = [
    ".github",
    "sections",
    "consequences",
    "examples",
    "appendices",
    "notebooks",
    "audit_pack",
    "supplement-b-artifacts",
    "scripts",
    "release",
]

EXCLUDE_NAMES = {
    ".git",
    ".github/workflows/__pycache__",
    "__pycache__",
    ".DS_Store",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_file():
        copy_if_exists(src, dst)
        return
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        if any(part in EXCLUDE_NAMES for part in p.parts):
            continue
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)


def build_stage(stage: Path) -> list[Path]:
    copied: list[Path] = []
    for name in INCLUDE_TOP_LEVEL:
        src = ROOT / name
        if src.exists():
            dst = stage / name
            copy_if_exists(src, dst)
            if dst.exists():
                copied.append(dst)
    for name in INCLUDE_DIRS:
        src = ROOT / name
        if src.exists():
            copy_tree(src, stage / name)
    for p in stage.rglob("*"):
        if p.is_file():
            copied.append(p)
    return sorted(set(copied))


def write_stats(stage: Path, files: list[Path], tag: str, bundle_name: str) -> None:
    stats = stage / "stats"
    stats.mkdir(parents=True, exist_ok=True)
    manifest_csv = stats / "release_bundle_manifest.csv"
    sha_csv = stats / "release_bundle_sha256.csv"
    report_txt = stats / "release_build_report.txt"

    rows = []
    for f in sorted(files):
        rel = f.relative_to(stage).as_posix()
        rows.append((rel, f.stat().st_size, sha256_file(f)))

    with manifest_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["relative_path", "size_bytes", "sha256"])
        writer.writerows(rows)

    with sha_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["relative_path", "sha256"])
        for rel, _size, digest in rows:
            writer.writerow([rel, digest])

    built_at = datetime.now(timezone.utc).isoformat()
    with report_txt.open("w", encoding="utf-8") as fh:
        fh.write(f"bundle_name={bundle_name}\n")
        fh.write(f"tag={tag}\n")
        fh.write(f"built_at_utc={built_at}\n")
        fh.write(f"file_count={len(rows)}\n")
        fh.write("notes=repo-root release bundle with PDFs, notebooks, stats, audit_pack, and companion artifacts\n")


def zip_stage(stage: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(stage).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default=os.environ.get("TAG", "release"))
    parser.add_argument("--outdir", default="dist")
    parser.add_argument("--bundle-prefix", default="aod-release")
    args = parser.parse_args()

    outdir = (ROOT / args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    bundle_name = f"{args.bundle_prefix}-{args.tag}.zip"
    bundle_path = outdir / bundle_name

    required = [ROOT / "main.pdf", ROOT / "supplement-a.pdf", ROOT / "supplement-b.pdf"]
    missing = [p.name for p in required if not p.exists()]
    if missing:
        print(f"Missing compiled PDFs: {', '.join(missing)}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "bundle"
        stage.mkdir(parents=True, exist_ok=True)
        files = build_stage(stage)
        write_stats(stage, files, args.tag, bundle_name)
        # refresh file list to include stats files
        files = [p for p in stage.rglob("*") if p.is_file()]
        zip_stage(stage, bundle_path)

    print(bundle_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
