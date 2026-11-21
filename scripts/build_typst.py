#!/usr/bin/env python3
"""Build the native Typst AOD Main and Manual publications with Main->Manual registry verification.

Preserves all baseline LaTeX sources untouched and writes PDFs to a separate
output directory (default: _build/typst). Updates typst/lib/main_registry.json
from the evaluated Main build before compiling Manual with a cryptographic
freshness binding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

MAIN_FIGURES = (
    "figures_jpg/null_four_edge_x_witness.png",
    "figures_jpg/fractal_tesseract_q4_witness.jpg",
    "figures_jpg/curling_curl_layers.png",
    "figures_jpg/cycle_disturbance_shedding.png",
    "figures_jpg/support_enclosure_retention.png",
    "figures_jpg/field_dynamics_layered_main.png",
)


def find_typst(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    env_bin = os.environ.get("TYPST_BIN")
    if env_bin and Path(env_bin).is_file():
        return env_bin
    found = shutil.which("typst")
    if found:
        return found
    local_bin = Path.home() / ".local" / "bin" / "typst"
    if local_bin.is_file():
        return str(local_bin)
    raise FileNotFoundError("typst binary not found on PATH, TYPST_BIN, or ~/.local/bin/typst")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_main_sources_digest(root: Path) -> tuple[str, list[str]]:
    """Compute deterministic SHA-256 over all active Main Typst, bibliography, and figure inputs."""
    files: list[Path] = [
        root / "typst" / "main.typ",
        root / "typst" / "preamble.typ",
        root / "typst" / "lib" / "aod_schema.typ",
        root / "refs.bib",
    ]
    files.extend(sorted((root / "typst" / "sections").glob("*.typ")))
    files.extend(sorted((root / "typst" / "appendices").glob("*.typ")))
    files.extend(root / rel for rel in MAIN_FIGURES)

    h = hashlib.sha256()
    rel_list: list[str] = []
    for p in sorted(set(files), key=lambda x: x.relative_to(root).as_posix()):
        if not p.is_file():
            raise FileNotFoundError(f"Missing active Main Typst input: {p}")
        rel = p.relative_to(root).as_posix()
        rel_list.append(rel)
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest(), rel_list


def run_typst_eval(typst_bin: str, root: Path, doc_path: Path, selector: str, inputs: dict[str, str] | None = None) -> list[dict]:
    cmd = [typst_bin, "eval", "--root", str(root), f"query({selector})", "--in", str(doc_path)]
    for k, v in (inputs or {}).items():
        cmd.extend(["--input", f"{k}={v}"])
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"typst eval failed ({selector} in {doc_path}):\n{proc.stderr}")
    return json.loads(proc.stdout)


def extract_registry(main_entries_raw: list[dict], main_digest: str, main_inputs: list[str]) -> dict:
    entries: dict[str, dict] = {}
    for item in main_entries_raw:
        val = item.get("value")
        if not isinstance(val, dict) or "id" not in val:
            continue
        lbl_id = val["id"]
        if lbl_id in entries:
            raise ValueError(f"Duplicate Main reference registry entry: {lbl_id}")
        entries[lbl_id] = {
            "kind": val["kind"],
            "number": val["number"],
            "display": val.get("display", val["number"]),
            "page": val["page"],
        }
    return {
        "schema": "aod.typst.main-registry.v1",
        "main_sources_sha256": main_digest,
        "main_input_count": len(main_inputs),
        "entry_count": len(entries),
        "entries": dict(sorted(entries.items())),
    }


def compile_doc(typst_bin: str, root: Path, src: Path, out_pdf: Path, inputs: dict[str, str] | None = None) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [typst_bin, "compile", "--root", str(root), str(src), str(out_pdf)]
    for k, v in (inputs or {}).items():
        cmd.extend(["--input", f"{k}={v}"])
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"typst compile failed ({src}):\n{proc.stderr}")
    if proc.stderr.strip():
        print(f"[typst warnings for {src.relative_to(root)}]:\n{proc.stderr.strip()}", file=sys.stderr)


def build_all(
    root: Path,
    outdir: Path,
    typst_bin: str,
    write_registry: bool = True,
    check_registry_only: bool = False,
) -> dict:
    ver_proc = subprocess.run([typst_bin, "--version"], capture_output=True, text=True, check=True)
    typst_version = ver_proc.stdout.strip()

    main_digest, main_inputs = compute_main_sources_digest(root)
    main_src = root / "typst" / "main.typ"
    manual_src = root / "typst" / "manual" / "main.typ"
    main_pdf = outdir / "main_typst.pdf"
    manual_pdf = outdir / "manual_typst.pdf"

    # 1. Compile Main
    compile_doc(typst_bin, root, main_src, main_pdf)

    # 2. Export deterministic Main reference registry
    main_ref_entries = run_typst_eval(typst_bin, root, main_src, "<aod-ref-entry>")
    registry = extract_registry(main_ref_entries, main_digest, main_inputs)
    registry_path = root / "typst" / "lib" / "main_registry.json"
    registry_text = json.dumps(registry, indent=2, sort_keys=True) + "\n"

    if check_registry_only:
        if not registry_path.is_file():
            raise FileNotFoundError(f"Missing committed Main registry: {registry_path}")
        if registry_path.read_text(encoding="utf-8") != registry_text:
            raise ValueError("Committed typst/lib/main_registry.json is out of date with typst/main.typ")
    elif write_registry:
        registry_path.write_text(registry_text, encoding="utf-8")

    # 3. Compile Manual with strict Main digest freshness check
    compile_doc(
        typst_bin,
        root,
        manual_src,
        manual_pdf,
        inputs={"expected_main_digest": main_digest},
    )

    manual_ref_entries = run_typst_eval(
        typst_bin, root, manual_src, "<aod-ref-entry>",
        inputs={"expected_main_digest": main_digest},
    )
    manual_mainrefs = run_typst_eval(
        typst_bin, root, manual_src, "<aod-mainref-use>",
        inputs={"expected_main_digest": main_digest},
    )

    report = {
        "schema": "aod.typst.build-report.v1",
        "typst_version": typst_version,
        "main_sources_sha256": main_digest,
        "main_pdf": main_pdf.name,
        "main_pdf_sha256": sha256_file(main_pdf),
        "main_pdf_bytes": main_pdf.stat().st_size,
        "manual_pdf": manual_pdf.name,
        "manual_pdf_sha256": sha256_file(manual_pdf),
        "manual_pdf_bytes": manual_pdf.stat().st_size,
        "main_registry_entries": registry["entry_count"],
        "manual_ref_entries": len(manual_ref_entries),
        "manual_mainref_uses": len(manual_mainrefs),
    }
    (outdir / "build_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Build native Typst AOD Main and Manual PDFs.")
    ap.add_argument("--root", default=str(ROOT), help="Repository root directory")
    ap.add_argument("--outdir", default="_build/typst", help="Output directory for PDFs and build report")
    ap.add_argument("--typst-bin", default=None, help="Explicit path to typst binary")
    ap.add_argument("--check-registry", action="store_true", help="Fail if committed main_registry.json differs instead of rewriting it")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = (root / outdir).resolve()
    typst_bin = find_typst(args.typst_bin)

    report = build_all(
        root=root,
        outdir=outdir,
        typst_bin=typst_bin,
        write_registry=not args.check_registry,
        check_registry_only=args.check_registry,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
