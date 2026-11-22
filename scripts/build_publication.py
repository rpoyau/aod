#!/usr/bin/env python3
"""Top-level AOD publication builder (canonical Typst primary + generated LaTeX compatibility).

Orchestrates:
  1. Canonical Typst Main -> typst/lib/main_registry.json -> Canonical Typst Manual
     delivering <outdir>/main.pdf and <outdir>/manual.pdf.
  2. (With --with-latex) Typst-to-LaTeX export/check via scripts/typ2tex.py
     and XeLaTeX compilation of latex/main.tex then latex/manual/main.tex,
     delivering the compatibility sibling pair <outdir>/latex/main.pdf and
     <outdir>/latex/manual.pdf with working sibling peer links.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_script(root: Path, rel: str, mod_name: str):
    path = root / rel
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_latex_compatibility(latex_dir: Path, latex_outdir: Path) -> dict:
    """Compile generated latex/main.tex and latex/manual/main.tex with latexmk -xelatex."""
    latexmk = shutil.which("latexmk")
    if not latexmk:
        raise FileNotFoundError("latexmk is required to compile generated LaTeX (--with-latex)")
    if not shutil.which("xelatex"):
        raise FileNotFoundError("xelatex is required to compile generated LaTeX (--with-latex)")

    main_tex = latex_dir / "main.tex"
    manual_tex = latex_dir / "manual" / "main.tex"
    if not main_tex.is_file() or not manual_tex.is_file():
        raise FileNotFoundError(f"Generated LaTeX drivers missing under {latex_dir}")

    subprocess.run(
        [latexmk, "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        cwd=latex_dir,
        check=True,
    )
    subprocess.run(
        [latexmk, "-cd", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "manual/main.tex"],
        cwd=latex_dir,
        check=True,
    )

    latex_outdir.mkdir(parents=True, exist_ok=True)
    main_out = latex_outdir / "main.pdf"
    manual_out = latex_outdir / "manual.pdf"
    shutil.copy2(latex_dir / "main.pdf", main_out)
    shutil.copy2(latex_dir / "manual" / "main.pdf", manual_out)
    return {
        "main_pdf": main_out.name,
        "main_pdf_sha256": sha256_file(main_out),
        "main_pdf_bytes": main_out.stat().st_size,
        "manual_pdf": manual_out.name,
        "manual_pdf_sha256": sha256_file(manual_out),
        "manual_pdf_bytes": manual_out.stat().st_size,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--outdir", type=Path, default=Path("dist"))
    ap.add_argument("--latex-dir", type=Path, default=Path("latex"))
    ap.add_argument("--typst-bin", default=None)
    ap.add_argument("--check-registry", action="store_true", help="Fail if typst/lib/main_registry.json differs")
    ap.add_argument("--with-latex", action="store_true", help="Also generate/check latex/ and compile XeLaTeX compatibility PDFs")
    ap.add_argument("--check-latex", action="store_true", help="Verify latex/ matches fresh typ2tex output without overwriting")
    ap.add_argument("--figure-format", choices=("pdf", "png"), default="pdf")
    ap.add_argument("--ppi", type=int, default=300, choices=(300, 600))
    args = ap.parse_args(argv)

    root = args.root.resolve()
    outdir = args.outdir if args.outdir.is_absolute() else (root / args.outdir)
    latex_dir = args.latex_dir if args.latex_dir.is_absolute() else (root / args.latex_dir)

    build_typst = _load_script(root, "scripts/build_typst.py", "aod_build_typst")
    typst_bin = build_typst.find_typst(args.typst_bin)
    outdir.mkdir(parents=True, exist_ok=True)

    native_report = build_typst.build_all(
        root=root,
        outdir=outdir,
        typst_bin=typst_bin,
        write_registry=not args.check_registry,
        check_registry_only=args.check_registry,
    )

    pub_report: dict = {
        "schema": "aod.publication.build-report.v1",
        "primary_authority": "typst",
        "native": native_report,
        "latex_compatibility": None,
    }

    if args.with_latex:
        typ2tex = _load_script(root, "scripts/typ2tex.py", "aod_typ2tex")
        gen_manifest = typ2tex.generate_latex_tree(
            root=root,
            outdir=latex_dir,
            check_only=args.check_latex,
            figure_format=args.figure_format,
            ppi=args.ppi,
            typst_bin=typst_bin,
        )
        latex_pdfs = build_latex_compatibility(latex_dir, outdir / "latex")
        pub_report["latex_compatibility"] = {
            "generation_counts": gen_manifest["counts"],
            "figure_format": args.figure_format,
            **latex_pdfs,
        }

    (outdir / "publication_build_report.json").write_text(
        json.dumps(pub_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(pub_report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
