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
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_REL = Path("typst/lib/aod_schema.typ")
DIAGRAMS_REL = Path("typst/lib/diagrams")
MANIFEST_NAME = "FIGURE_MANIFEST.json"
MANIFEST_SCHEMA = "aod.typst.figure-export.v1"
RUNTIME_SCHEMA = "aod.typst.figure-export.runtime.v1"

DECLARED_BACKGROUND = "white"
DECLARED_FONT_FAMILIES = {
    "text": ["Latin Modern Roman", "DejaVu Serif"],
    "math": ["Latin Modern Math", "New Computer Modern Math"],
}

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


def _dir_file_inventory(base: Path) -> dict[str, str]:
    if not base.is_dir():
        return {}
    return {
        p.relative_to(base).as_posix(): sha256_file(p)
        for p in sorted(base.rglob("*"))
        if p.is_file()
    }


def atomic_replace_directory(
    stage_dir: Path,
    target_dir: Path,
    *,
    before_commit_hook=None,
) -> list[str]:
    """Atomically swap stage_dir into target_dir on the same filesystem with rollback on failure.

    Returns the sorted list of relative file paths removed from the previous target_dir.
    """
    stage_dir = Path(stage_dir).resolve()
    target_dir = Path(target_dir).resolve()
    _require(stage_dir.is_dir(), f"Stage directory does not exist: {stage_dir}")
    _require(
        stage_dir.parent == target_dir.parent,
        f"Stage directory {stage_dir} must share parent filesystem with target {target_dir}",
    )

    prev_inv = _dir_file_inventory(target_dir) if target_dir.is_dir() else {}
    new_inv = _dir_file_inventory(stage_dir)
    removed_outputs = sorted(set(prev_inv) - set(new_inv))

    backup_dir: Path | None = None
    if target_dir.exists():
        backup_dir = target_dir.parent / f".{target_dir.name}.backup.{os.getpid()}.{uuid.uuid4().hex[:8]}"
        os.rename(target_dir, backup_dir)

    try:
        if before_commit_hook is not None:
            before_commit_hook(stage_dir, target_dir, backup_dir)
        os.rename(stage_dir, target_dir)
    except BaseException:
        if backup_dir is not None and backup_dir.exists() and not target_dir.exists():
            os.rename(backup_dir, target_dir)
        raise

    if backup_dir is not None and backup_dir.exists():
        shutil.rmtree(backup_dir)
    return removed_outputs


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


def _inspect_pdf(pdf_path: Path, expected_w_cm: float, expected_h_cm: float) -> tuple[dict, dict]:
    """Validate exported vector PDF invariants and return (deterministic_fields, runtime_diagnostics)."""
    import pypdf
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    _require(len(reader.pages) == 1, f"Exported diagram PDF must have 1 page, got {len(reader.pages)}: {pdf_path}")
    page = reader.pages[0]
    text = (page.extract_text() or "").strip()
    _require(bool(text), f"Exported diagram PDF has no extractable text: {pdf_path}")

    # Count raster image XObjects and collect resolved BaseFont identities recursively.
    raster_count = 0
    resolved_fonts: set[str] = set()

    def _walk_resources(resources) -> None:
        nonlocal raster_count
        if resources is None:
            return
        res_obj = resources.get_object() if hasattr(resources, "get_object") else resources
        fonts = res_obj.get("/Font")
        if fonts is not None:
            fonts_dict = fonts.get_object() if hasattr(fonts, "get_object") else fonts
            for fval in fonts_dict.values():
                fobj = fval.get_object() if hasattr(fval, "get_object") else fval
                bf = fobj.get("/BaseFont")
                if bf is not None:
                    name = str(bf).lstrip("/")
                    # Strip deterministic 6-letter subset tag prefix (e.g. ABCDEF+LMRoman10-Regular)
                    if "+" in name and len(name.split("+", 1)[0]) == 6:
                        name = name.split("+", 1)[1]
                    resolved_fonts.add(name)
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
                _walk_resources(obj.get("/Resources"))

    _walk_resources(page.get("/Resources"))
    _require(raster_count == 0, f"Exported vector diagram PDF contains {raster_count} raster XObjects: {pdf_path}")

    w_pt = round(float(page.mediabox.width), 3)
    h_pt = round(float(page.mediabox.height), 3)
    exp_w_pt = expected_w_cm * 72.0 / 2.54
    exp_h_pt = expected_h_cm * 72.0 / 2.54
    _require(
        abs(w_pt - exp_w_pt) <= 0.5 and abs(h_pt - exp_h_pt) <= 0.5,
        f"Exported PDF box [{w_pt}, {h_pt}] pt differs from expected [{exp_w_pt:.2f}, {exp_h_pt:.2f}] pt",
    )
    deterministic = {
        "page_count": 1,
        "page_points": [w_pt, h_pt],
        "raster_image_xobjects": raster_count,
        "has_extractable_text": True,
    }
    runtime = {
        "pypdf_version": getattr(pypdf, "__version__", "unknown"),
        "extracted_text_chars": len(text),
        "resolved_fonts": sorted(resolved_fonts),
    }
    return deterministic, runtime


def export_figures(
    root: Path,
    outdir: Path,
    *,
    fmt: str = "pdf",
    ppi: int = 300,
    typst_bin: str | None = None,
    check_only: bool = False,
    runtime_out: dict | None = None,
    before_commit_hook=None,
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
    text_fonts_typ = ", ".join(f'"{f}"' for f in DECLARED_FONT_FAMILIES["text"])
    math_fonts_typ = ", ".join(f'"{f}"' for f in DECLARED_FONT_FAMILIES["math"])

    stage_parent = outdir.parent
    if not check_only:
        stage_parent.mkdir(parents=True, exist_ok=True)
        stage_out = Path(tempfile.mkdtemp(prefix=f".{outdir.name}.stage.", dir=str(stage_parent)))
    else:
        stage_out = Path(tempfile.mkdtemp(prefix="aod_fig_check_"))

    try:
        results: list[dict] = []
        runtime_figures: list[dict] = []
        pypdf_version: str | None = None
        for item in bindings:
            slug = item["slug"]
            out_name = f"{slug}.{fmt}"
            out_file = stage_out / out_name
            wrapper = (
                f'#set page(width: {item["width_cm"]}cm, height: {item["height_cm"]}cm, '
                f'margin: 0pt, numbering: none, fill: {DECLARED_BACKGROUND})\n'
                f'#set text(font: ({text_fonts_typ}), size: 11pt, lang: "en")\n'
                f'#show math.equation: set text(font: ({math_fonts_typ}))\n'
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
                "background": DECLARED_BACKGROUND,
                "font_families": DECLARED_FONT_FAMILIES,
                "format": fmt,
                "output_filename": out_name,
                "output_sha256": sha256_file(out_file),
                "output_bytes": out_file.stat().st_size,
            }
            rt_entry: dict = {
                "slug": slug,
                "output_filename": out_name,
                "output_sha256": entry["output_sha256"],
            }
            if fmt == "png":
                entry["ppi"] = ppi
            else:
                det_pdf, rt_pdf = _inspect_pdf(out_file, item["width_cm"], item["height_cm"])
                entry.update(det_pdf)
                pypdf_version = rt_pdf["pypdf_version"]
                rt_entry["extracted_text_chars"] = rt_pdf["extracted_text_chars"]
                rt_entry["resolved_fonts"] = rt_pdf["resolved_fonts"]
            results.append(entry)
            runtime_figures.append(rt_entry)

        # Deterministic committed manifest: source/settings/output identities only;
        # no extractor-version-dependent counts, compiler version banners, or removal logs.
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "format": fmt,
            "ppi": ppi if fmt == "png" else None,
            "background": DECLARED_BACKGROUND,
            "font_families": DECLARED_FONT_FAMILIES,
            "schema_path": SCHEMA_REL.as_posix(),
            "schema_sha256": schema_sha,
            "figure_count": len(results),
            "figures": results,
        }
        manifest_path = stage_out / MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        os.chmod(manifest_path, 0o644)

        removed_outputs: list[str] = []
        if check_only:
            _require(outdir.is_dir(), f"Exported figure directory does not exist: {outdir}")
            exp_inv = _dir_file_inventory(stage_out)
            act_inv = _dir_file_inventory(outdir)
            missing = sorted(set(exp_inv) - set(act_inv))
            extra = sorted(set(act_inv) - set(exp_inv))
            changed = sorted(k for k in set(exp_inv) & set(act_inv) if exp_inv[k] != act_inv[k])
            if missing or extra or changed:
                raise ValueError(
                    f"Exported figure directory differs from fresh export (--check failed): "
                    f"missing={missing}, extra={extra}, changed={changed}"
                )
        else:
            removed_outputs = atomic_replace_directory(
                stage_out, outdir, before_commit_hook=before_commit_hook
            )

        rt_report = {
            "schema": RUNTIME_SCHEMA,
            "typst_version": typst_version,
            "pypdf_version": pypdf_version,
            "creation_timestamp": str(creation_ts),
            "background": DECLARED_BACKGROUND,
            "declared_font_families": DECLARED_FONT_FAMILIES,
            "removed_outputs": removed_outputs,
            "figures": runtime_figures,
        }
        if runtime_out is not None:
            runtime_out.clear()
            runtime_out.update(rt_report)
    finally:
        if stage_out.exists():
            shutil.rmtree(stage_out)

    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--outdir", type=Path, default=Path("latex/manual/figures/generated"))
    ap.add_argument("--format", choices=("pdf", "png"), default="pdf")
    ap.add_argument("--ppi", type=int, default=300, choices=(300, 600))
    ap.add_argument("--typst-bin", default=None)
    ap.add_argument("--check", action="store_true", help="Verify outdir matches fresh export without modifying it")
    ap.add_argument("--runtime-report", type=Path, default=None, help="Optional JSON path for runtime/extractor diagnostics")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    outdir = args.outdir if args.outdir.is_absolute() else (root / args.outdir)
    runtime_diag: dict = {}
    manifest = export_figures(
        root,
        outdir,
        fmt=args.format,
        ppi=args.ppi,
        typst_bin=args.typst_bin,
        check_only=args.check,
        runtime_out=runtime_diag,
    )
    if args.runtime_report is not None:
        rp = args.runtime_report if args.runtime_report.is_absolute() else (root / args.runtime_report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(runtime_diag, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": manifest, "runtime_diagnostics": runtime_diag}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
