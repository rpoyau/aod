#!/usr/bin/env python3
"""Verify and materialize the immutable historical 98ddfa0 LaTeX baseline without Git.

Reads archive/latex_baseline_98ddfa0/BASELINE_MANIFEST.json, verifies every one
of the 211 bound SHA-256 digests against its retained location (41 archived
editorial TeX files under archive/latex_baseline_98ddfa0/ plus 170 shared
bibliography, image, data, and historical-evidence files preserved in place),
and optionally materializes a complete standalone historical LaTeX build root
into --outdir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE_REL = Path("archive/latex_baseline_98ddfa0")
MANIFEST_REL = BASELINE_REL / "BASELINE_MANIFEST.json"
EXPECTED_SCHEMA = "aod.latex-baseline-snapshot.v1"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_rel(rel: str) -> Path:
    p = Path(rel)
    _require(
        bool(rel) and not p.is_absolute() and ".." not in p.parts and "\\" not in rel,
        f"Unsafe relative path in baseline manifest: {rel!r}",
    )
    return p


def load_and_verify_baseline(root: Path) -> dict:
    root = Path(root).resolve()
    manifest_path = root / MANIFEST_REL
    _require(manifest_path.is_file(), f"Missing baseline manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require(
        isinstance(manifest, dict) and manifest.get("schema") == EXPECTED_SCHEMA,
        f"Invalid baseline manifest schema in {manifest_path}",
    )
    entries = manifest.get("entries")
    _require(isinstance(entries, list) and len(entries) == 211, "Expected exactly 211 baseline entries")

    archived_expected: set[str] = set()
    seen_orig: set[str] = set()
    for entry in entries:
        orig = entry["original_path"]
        retained = entry["retained_location"]
        _require(orig not in seen_orig, f"Duplicate original_path in baseline manifest: {orig}")
        seen_orig.add(orig)
        _safe_rel(orig)
        _safe_rel(retained)
        src = root / retained
        _require(not src.is_symlink(), f"Baseline file must not be a symlink: {retained}")
        _require(src.is_file(), f"Missing retained baseline file: {retained}")
        actual_bytes = src.stat().st_size
        _require(actual_bytes == entry["bytes"], f"Byte count mismatch for {retained}: {actual_bytes} != {entry['bytes']}")
        actual_sha = sha256_file(src)
        _require(actual_sha == entry["sha256"], f"SHA-256 mismatch for {retained}")
        if entry["role"] == "archived_editorial_tex":
            archived_expected.add(retained)

    # Confirm no undeclared extra files exist inside archive/latex_baseline_98ddfa0/
    snap_dir = root / BASELINE_REL
    actual_archived = {
        p.relative_to(root).as_posix()
        for p in snap_dir.rglob("*")
        if p.is_file() and p.relative_to(root) != MANIFEST_REL
    }
    _require(
        actual_archived == archived_expected,
        f"Archived baseline directory mismatch: extra={sorted(actual_archived - archived_expected)}, "
        f"missing={sorted(archived_expected - actual_archived)}",
    )
    return manifest


def materialize_baseline(root: Path, outdir: Path) -> dict:
    root = Path(root).resolve()
    outdir = Path(outdir).resolve()
    _require(outdir != root and root not in outdir.parents, "--outdir must be outside --root")
    manifest = load_and_verify_baseline(root)
    if outdir.exists():
        _require(outdir.is_dir() and not any(outdir.iterdir()), "--outdir must not exist or must be empty")
    outdir.mkdir(parents=True, exist_ok=True)

    for entry in manifest["entries"]:
        src = root / entry["retained_location"]
        dst = outdir / entry["original_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        mode = 0o755 if entry.get("mode") == "100755" else 0o644
        os.chmod(dst, mode)

    return {
        "schema": "aod.latex-baseline-materialization.v1",
        "historical_scientific_baseline_commit": manifest["historical_scientific_baseline_commit"],
        "phase1_accepted_commit": manifest["phase1_accepted_commit"],
        "materialized_files": len(manifest["entries"]),
        "outdir": str(outdir),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--outdir", type=Path, default=None, help="Fresh target directory for materialized baseline")
    ap.add_argument("--verify-only", action="store_true", help="Verify all 211 retained baseline files without copying")
    args = ap.parse_args(argv)

    if args.verify_only or args.outdir is None:
        manifest = load_and_verify_baseline(args.root)
        print(json.dumps({
            "status": "PASS",
            "historical_scientific_baseline_commit": manifest["historical_scientific_baseline_commit"],
            "verified_files": len(manifest["entries"]),
            "counts": manifest["counts"],
        }, indent=2))
        return 0

    result = materialize_baseline(args.root, args.outdir)
    print(json.dumps({"status": "PASS", **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
