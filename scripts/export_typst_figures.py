#!/usr/bin/env python3
"""Export authoritative shared native Typst diagrams for generated LaTeX inclusion.

Reads the single authoritative diagram components under typst/lib/diagrams/
referenced by the canonical Typst Manual sections, compiles each diagram body
(without caption or figure number; generated LaTeX owns those) into tightly
bounded 1-page vector PDFs (default) or optional 300/600 ppi PNGs, verifies
PDF vector/text invariants, and writes a deterministic FIGURE_MANIFEST.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_REL = Path("typst/lib/aod_schema.typ")
DIAGRAMS_REL = Path("typst/lib/diagrams")
MANIFEST_NAME = "FIGURE_MANIFEST.json"
MANIFEST_SCHEMA = "aod.typst.figure-export.v1"

INCLUDE_DIAGRAM_RE = re.compile(
    r'#include\s+"(?:\.\./)+lib/diagrams/([a-z0-9_]+\.typ)"'
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _extract_flowchart_dims(component_path: Path) -> tuple[float, float]:
    text = component_path.read_text(encoding="utf-8")
    _require(
        text.count("#aod-flowchart(") == 1,
        f"Expected exactly one #aod-flowchart(...) call in {component_path}",
    )
    wm = re.search(r"\bwidth:\s*([0-9]+(?:\.[0-9]+)?)cm\b", text)
    hm = re.search(r"\bheight:\s*([0-9]+(?:\.[0-9]+)?)cm\b", text)
    _require(wm is not None and hm is not None, f"Missing literal cm width/height in {component_path}")
    w_cm = float(wm.group(1))
    h_cm = float(hm.group(1))
    _require(w_cm > 0 and h_cm > 0, f"Non-positive diagram dimensions in {component_path}")
    return w_cm, h_cm


def discover_diagrams(root: Path) -> list[dict]:
    """Discover all active native diagram bindings from canonical typst/ sections."""
    root = Path(root).resolve()
    typst_root = root / "typst"
    _require(typst_root.is_dir(), f"Missing typst/ directory under {root}")

    bindings: list[dict] = []
    seen_slugs: set[str] = set()
    seen_labels: set[str] = set()

    for typ_file in sorted(typst_root.rglob("*.typ")):
        rel = typ_file.relative_to(root).as_posix()
        if rel.startswith("typst/lib/"):
            continue
        text = typ_file.read_text(encoding="utf-8")
        _require(
            "#aod-flowchart(" not in text,
            f"Inline #aod-flowchart(...) found outside typst/lib/diagrams/: {rel}",
        )
        for m in INCLUDE_DIAGRAM_RE.finditer(text):
            mod_name = m.group(1)
            comp_rel = (DIAGRAMS_REL / mod_name).as_posix()
            comp_path = root / comp_rel
            _require(comp_path.is_file(), f"Missing diagram component {comp_rel} referenced by {rel}")
            following = text[m.end():]
            lm = re.search(r"<(fig:[^>]+)>", following)
            _require(lm is not None, f"Missing figure label after {comp_rel} in {rel}")
            label = lm.group(1)
            slug = mod_name[:-4].replace("_", "-")
            _require(slug not in seen_slugs, f"Duplicate native diagram slug: {slug}")
            _require(label not in seen_labels, f"Duplicate native diagram label: {label}")
            seen_slugs.add(slug)
            seen_labels.add(label)
            w_cm, h_cm = _extract_flowchart_dims(comp_path)
            bindings.append({
                "slug": slug,
                "label": label,
                "typst_section": rel,
                "diagram_component": comp_rel,
                "diagram_sha256": sha256_file(comp_path),
                "width_cm": w_cm,
                "height_cm": h_cm,
            })

    # Ensure every component file under typst/lib/diagrams/ is actively bound.
    diag_dir = root / DIAGRAMS_REL
    if diag_dir.is_dir():
        on_disk = {p.relative_to(root).as_posix() for p in diag_dir.glob("*.typ")}
        bound = {b["diagram_component"] for b in bindings}
        _require(
            on_disk == bound,
            f"Unbound or missing diagram components: extra={sorted(on_disk - bound)}, missing={sorted(bound - on_disk)}",
        )

    return bindings


def _inspect_pdf(pdf_path: Path, expected_w_cm: float, expected_h_cm: float) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    _require(len(reader.pages) == 1, f"Exported diagram PDF must have 1 page, got {len(reader.pages)}: {pdf_path}")
    page = reader.pages[0]
    text = (page.extract_text() or "").strip()
    _require(bool(text), f"Exported diagram PDF has no extractable text: {pdf_path}")

    # Count raster image XObjects recursively inside page /Resources /XObject
    raster_count = 0

    def _walk_xobjects(resources) -> None:
        nonlocal raster_count
        if resources is None:
            return
        res_obj = resources.get_object() if hasattr(resources, "get_object") else resources
        xobjs = res_obj.get("/XObject")
        if xobjs is None:
            return
        xobjs_dict = xobjs.get_object() if hasattr(xobjs, "get_object") else xobjs
        for val in xobjs_dict.values():
            obj = val.get_object() if hasattr(val, "get_object") else val
            subtype = str(obj.get("/Subtype", ""))
            if subtype == "/Image":
                raster_count += 1
            elif subtype == "/Form":
                _walk_xobjects(obj.get("/Resources"))

    _walk_xobjects(page.get("/Resources"))
    _require(raster_count == 0, f"Exported vector diagram PDF contains {raster_count} raster XObjects: {pdf_path}")

    w_pt = round(float(page.mediabox.width), 3)
    h_pt = round(float(page.mediabox.height), 3)
    exp_w_pt = expected_w_cm * 72.0 / 2.54
    exp_h_pt = expected_h_cm * 72.0 / 2.54
    _require(
        abs(w_pt - exp_w_pt) <= 0.5 and abs(h_pt - exp_h_pt) <= 0.5,
        f"Exported PDF box [{w_pt}, {h_pt}] pt differs from expected [{exp_w_pt:.2f}, {exp_h_pt:.2f}] pt",
    )
    return {
        "page_count": 1,
        "page_points": [w_pt, h_pt],
        "raster_image_xobjects": raster_count,
        "extracted_text_chars": len(text),
    }


def export_figures(
    root: Path,
    outdir: Path,
    *,
    fmt: str = "pdf",
    ppi: int = 300,
    typst_bin: str | None = None,
) -> dict:
    root = Path(root).resolve()
    outdir = Path(outdir).resolve()
    _require(fmt in ("pdf", "png"), f"Unsupported diagram export format: {fmt!r} (expected 'pdf' or 'png')")
    if fmt == "png":
        _require(ppi in (300, 600), f"PNG diagram export requires --ppi 300 or 600, got {ppi}")

    typst = find_typst(typst_bin)
    ver_proc = subprocess.run([typst, "--version"], capture_output=True, text=True, check=True)
    typst_version = ver_proc.stdout.strip()

    schema_path = root / SCHEMA_REL
    _require(schema_path.is_file(), f"Missing Typst schema: {schema_path}")
    schema_sha = sha256_file(schema_path)
    bindings = discover_diagrams(root)
    _require(len(bindings) > 0, "No active native Typst diagrams found to export")

    creation_ts = os.environ.get("SOURCE_DATE_EPOCH", "0")

    with tempfile.TemporaryDirectory(prefix="aod_fig_export_") as tmp:
        tmp_path = Path(tmp)
        stage_out = tmp_path / "out"
        stage_out.mkdir(parents=True, exist_ok=True)
        # Keep wrappers under a hidden dir inside tmp; compile with --root=root
        # by placing temporary wrappers? Typst requires input inside --root, so
        # we compile via stdin (`-`) with `--root <root>` — zero writes into root!
        results: list[dict] = []
        for item in bindings:
            slug = item["slug"]
            out_name = f"{slug}.{fmt}"
            out_file = stage_out / out_name
            wrapper = (
                f'#set page(width: {item["width_cm"]}cm, height: {item["height_cm"]}cm, '
                'margin: 0pt, numbering: none, fill: white)\n'
                '#set text(font: ("Latin Modern Roman", "DejaVu Serif"), size: 11pt, lang: "en")\n'
                '#show math.equation: set text(font: ("Latin Modern Math", "New Computer Modern Math"))\n'
                '#set par(leading: 0.6em, spacing: 1.05em, justify: true, first-line-indent: 0pt)\n'
                '#set math.equation(numbering: none)\n'
                f'#include "/{item["diagram_component"]}"\n'
            )
            cmd = [
                typst, "compile",
                "--root", str(root),
                "--creation-timestamp", str(creation_ts),
                "--format", fmt,
            ]
            if fmt == "png":
                cmd.extend(["--ppi", str(ppi)])
            cmd.extend(["-", str(out_file)])
            proc = subprocess.run(cmd, input=wrapper, cwd=root, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"typst compile failed for {item['diagram_component']}:\n{proc.stderr}")

            os.chmod(out_file, 0o644)
            entry = {
                "slug": slug,
                "label": item["label"],
                "typst_section": item["typst_section"],
                "diagram_component": item["diagram_component"],
                "diagram_sha256": item["diagram_sha256"],
                "width_cm": item["width_cm"],
                "height_cm": item["height_cm"],
                "format": fmt,
                "output_filename": out_name,
                "output_sha256": sha256_file(out_file),
                "output_bytes": out_file.stat().st_size,
            }
            if fmt == "png":
                entry["ppi"] = ppi
            else:
                entry.update(_inspect_pdf(out_file, item["width_cm"], item["height_cm"]))
            results.append(entry)

        manifest = {
            "schema": MANIFEST_SCHEMA,
            "typst_version": typst_version,
            "format": fmt,
            "ppi": ppi if fmt == "png" else None,
            "schema_path": SCHEMA_REL.as_posix(),
            "schema_sha256": schema_sha,
            "figure_count": len(results),
            "figures": results,
        }
        manifest_path = stage_out / MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        os.chmod(manifest_path, 0o644)

        # Atomic replacement of managed generated figures directory
        outdir.parent.mkdir(parents=True, exist_ok=True)
        if outdir.exists():
            shutil.rmtree(outdir)
        shutil.copytree(stage_out, outdir)

    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--outdir", type=Path, default=Path("latex/manual/figures/generated"))
    ap.add_argument("--format", choices=("pdf", "png"), default="pdf")
    ap.add_argument("--ppi", type=int, default=300, choices=(300, 600))
    ap.add_argument("--typst-bin", default=None)
    args = ap.parse_args(argv)

    root = args.root.resolve()
    outdir = args.outdir if args.outdir.is_absolute() else (root / args.outdir)
    manifest = export_figures(root, outdir, fmt=args.format, ppi=args.ppi, typst_bin=args.typst_bin)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
