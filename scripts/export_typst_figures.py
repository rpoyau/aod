#!/usr/bin/env python3
"""Export authoritative shared native Typst diagrams and vector figures for generated LaTeX.

Reads the single authoritative figure components under:
  - typst/lib/diagrams/*.typ        (Manual flowchart diagrams, #aod-flowchart)
  - typst/lib/figures/main/*.typ    (Main native vector figures, #aod-canvas)
  - typst/lib/figures/manual/*.typ  (Manual native vector figures, #aod-canvas)
referenced by the canonical Typst Main and Manual sections, compiles each figure
body (without caption or figure number; generated LaTeX owns those) into tightly
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
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_REL = Path("typst/lib/aod_schema.typ")
PLOTS_REL = Path("typst/lib/aod_plots.typ")
DIAGRAMS_REL = Path("typst/lib/diagrams")
FIGURES_REL = Path("typst/lib/figures")
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
INCLUDE_FIGURE_RE = re.compile(
    r'#include\s+"(?:\.\./)+lib/figures/(main|manual)/([a-z0-9_]+\.typ)"'
)
CSV_REF_RE = re.compile(r'\bcsv\(\s*"/([^"]+)"')


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


def _strip_typst_comments(text: str) -> str:
    """Strip Typst // line comments and nested /* ... */ block comments while preserving strings, raw spans, and newlines."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(text[i:j])
            i = j
            continue
        if c == "`":
            m_raw = re.match(r"`+", text[i:])
            fence = m_raw.group(0)
            if len(fence) == 2:
                out.append("``")
                i += 2
                continue
            j = text.find(fence, i + len(fence))
            end = n if j < 0 else j + len(fence)
            out.append(text[i:end])
            i = end
            continue
        if text.startswith("//", i) and (i == 0 or text[i - 1] != ":"):
            k = text.find("\n", i)
            i = n if k < 0 else k
            continue
        if text.startswith("/*", i):
            depth = 1
            j = i + 2
            while j < n and depth > 0:
                if text.startswith("/*", j):
                    depth += 1
                    j += 2
                elif text.startswith("*/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            newlines = text[i:j].count("\n")
            out.append("\n" * newlines if newlines else " ")
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _extract_flowchart_dims(component_path: Path) -> tuple[float, float]:
    text = _strip_typst_comments(component_path.read_text(encoding="utf-8"))
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


def _extract_vector_figure_dims(component_path: Path) -> tuple[float, float]:
    text = _strip_typst_comments(component_path.read_text(encoding="utf-8"))
    _require(
        text.count("#aod-canvas(") == 1,
        f"Expected exactly one #aod-canvas(...) call in {component_path}",
    )
    wm = re.search(r"#let\s+fig-width-cm\s*=\s*([0-9]+(?:\.[0-9]+)?)\b", text)
    hm = re.search(r"#let\s+fig-height-cm\s*=\s*([0-9]+(?:\.[0-9]+)?)\b", text)
    _require(
        wm is not None and hm is not None,
        f"Missing literal #let fig-width-cm / fig-height-cm in {component_path}",
    )
    w_cm = float(wm.group(1))
    h_cm = float(hm.group(1))
    _require(w_cm > 0 and h_cm > 0, f"Non-positive figure dimensions in {component_path}")
    return w_cm, h_cm


def _extract_csv_inputs(component_path: Path, root: Path) -> list[dict]:
    text = _strip_typst_comments(component_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    refs: list[dict] = []
    for m in CSV_REF_RE.finditer(text):
        rel = m.group(1)
        if rel in seen:
            continue
        seen.add(rel)
        p = (root / rel).resolve()
        _require(
            p.is_file() and p.is_relative_to(root),
            f"Missing CSV input {rel} referenced by {component_path}",
        )
        refs.append({"path": rel, "sha256": sha256_file(p)})
    refs.sort(key=lambda d: d["path"])
    return refs


def discover_diagrams(root: Path, *, surface: str | None = None) -> list[dict]:
    """Discover all active native diagram and vector-figure bindings from canonical typst/ sections."""
    root = Path(root).resolve()
    if surface is not None:
        _require(surface in ("main", "manual"), f"Unsupported surface: {surface!r}")
    typst_root = root / "typst"
    _require(typst_root.is_dir(), f"Missing typst/ directory under {root}")

    bindings: list[dict] = []
    seen_slugs: set[tuple[str, str]] = set()
    seen_labels: set[str] = set()

    for typ_file in sorted(typst_root.rglob("*.typ")):
        rel = typ_file.relative_to(root).as_posix()
        if rel.startswith("typst/lib/"):
            continue
        sec_surface = "manual" if rel.startswith("typst/manual/") else "main"
        text = typ_file.read_text(encoding="utf-8")
        _require(
            "#aod-flowchart(" not in text,
            f"Inline #aod-flowchart(...) found outside typst/lib/diagrams/: {rel}",
        )
        _require(
            "#aod-canvas(" not in text,
            f"Inline #aod-canvas(...) found outside typst/lib/figures/: {rel}",
        )

        matches: list[tuple[int, int, str, str, str]] = []
        for m in INCLUDE_DIAGRAM_RE.finditer(text):
            mod_name = m.group(1)
            comp_rel = (DIAGRAMS_REL / mod_name).as_posix()
            matches.append((m.start(), m.end(), "manual", "flowchart_diagram", comp_rel))
        for m in INCLUDE_FIGURE_RE.finditer(text):
            fig_surf, mod_name = m.group(1), m.group(2)
            comp_rel = (FIGURES_REL / fig_surf / mod_name).as_posix()
            matches.append((m.start(), m.end(), fig_surf, "vector_figure", comp_rel))
        matches.sort(key=lambda item: item[0])

        for _, end_pos, comp_surface, comp_kind, comp_rel in matches:
            _require(
                comp_surface == sec_surface,
                f"Surface mismatch: {rel} ({sec_surface}) includes {comp_rel} ({comp_surface})",
            )
            comp_path = root / comp_rel
            _require(comp_path.is_file(), f"Missing component {comp_rel} referenced by {rel}")
            following = text[end_pos:]
            lm = re.search(r"<(fig:[^>]+)>", following)
            _require(lm is not None, f"Missing figure label after {comp_rel} in {rel}")
            label = lm.group(1)
            slug = Path(comp_rel).stem.replace("_", "-")
            _require((comp_surface, slug) not in seen_slugs, f"Duplicate slug in {comp_surface}: {slug}")
            _require(label not in seen_labels, f"Duplicate native figure label: {label}")
            seen_slugs.add((comp_surface, slug))
            seen_labels.add(label)
            if comp_kind == "flowchart_diagram":
                w_cm, h_cm = _extract_flowchart_dims(comp_path)
            else:
                w_cm, h_cm = _extract_vector_figure_dims(comp_path)
            data_inputs = _extract_csv_inputs(comp_path, root)
            bindings.append({
                "surface": comp_surface,
                "component_kind": comp_kind,
                "slug": slug,
                "label": label,
                "typst_section": rel,
                "diagram_component": comp_rel,
                "diagram_sha256": sha256_file(comp_path),
                "width_cm": w_cm,
                "height_cm": h_cm,
                "data_inputs": data_inputs,
            })

    # Ensure every component file on disk for the requested surface(s) is actively bound.
    surfaces_to_check = [surface] if surface is not None else ["main", "manual"]
    for surf in surfaces_to_check:
        on_disk: set[str] = set()
        if surf == "manual":
            diag_dir = root / DIAGRAMS_REL
            if diag_dir.is_dir():
                on_disk.update(p.relative_to(root).as_posix() for p in diag_dir.glob("*.typ"))
        fig_dir = root / FIGURES_REL / surf
        if fig_dir.is_dir():
            on_disk.update(p.relative_to(root).as_posix() for p in fig_dir.glob("*.typ"))
        bound = {b["diagram_component"] for b in bindings if b["surface"] == surf}
        _require(
            on_disk == bound,
            f"Unbound or missing {surf} components: extra={sorted(on_disk - bound)}, missing={sorted(bound - on_disk)}",
        )

    if surface is not None:
        return [b for b in bindings if b["surface"] == surface]
    return bindings


def inspect_pdf_rasters(pdf_path: Path) -> dict:
    """Recursively inspect a PDF for raster /Image XObjects and inline BI/ID/EI images.

    Traverses every page /Contents stream (single StreamObject or ArrayObject),
    /Resources (/XObject /Image and /Form, /Pattern Type 1 tiling patterns,
    /Font /Type3 /CharProcs, /ExtGState /SMask /G), and /Annots /AP appearance streams.
    Fails closed (raises ValueError) on malformed or uninspectable content streams.
    """
    from pypdf import PdfReader
    from pypdf.generic import ArrayObject, ContentStream, StreamObject

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"Uninspectable or malformed PDF file {pdf_path}: {exc}") from exc

    seen_res: set[tuple] = set()
    seen_streams: set[tuple] = set()
    xobj_images = 0
    inline_images = 0
    streams_inspected = 0

    def _obj_key(raw_obj, resolved_obj) -> tuple:
        if hasattr(raw_obj, "idnum") and hasattr(raw_obj, "generation"):
            return ("ref", raw_obj.idnum, raw_obj.generation)
        return ("id", id(resolved_obj))

    def _scan_content(raw_content, ctx: str) -> None:
        nonlocal inline_images, streams_inspected
        if raw_content is None:
            return
        resolved = raw_content.get_object() if hasattr(raw_content, "get_object") else raw_content
        if isinstance(resolved, ArrayObject):
            if len(resolved) == 0:
                return
            elem_keys: list[tuple] = []
            for idx, el in enumerate(resolved):
                el_obj = el.get_object() if hasattr(el, "get_object") else el
                if not isinstance(el_obj, StreamObject):
                    raise ValueError(
                        f"Malformed PDF /Contents array element #{idx} ({type(el_obj).__name__}) in {ctx}"
                    )
                elem_keys.append(_obj_key(el, el_obj))
            sk: tuple = ("arr", tuple(elem_keys))
        elif isinstance(resolved, StreamObject):
            sk = _obj_key(raw_content, resolved)
        else:
            raise ValueError(f"Unsupported PDF content object ({type(resolved).__name__}) in {ctx}")
        if sk in seen_streams:
            return
        seen_streams.add(sk)
        try:
            cs = ContentStream(resolved, reader)
            ops = cs.operations
        except Exception as exc:
            raise ValueError(f"Uninspectable or malformed PDF content stream in {ctx}: {exc}") from exc
        streams_inspected += 1
        for _, op in ops:
            if op in (b"INLINE IMAGE", b"BI"):
                inline_images += 1

    def _walk_resources(res, ctx: str) -> None:
        nonlocal xobj_images
        if res is None:
            return
        ro = res.get_object() if hasattr(res, "get_object") else res
        if not isinstance(ro, dict):
            raise ValueError(f"Malformed PDF /Resources object ({type(ro).__name__}) in {ctx}")
        rk = _obj_key(res, ro)
        if rk in seen_res:
            return
        seen_res.add(rk)
        for bucket in ("/XObject", "/Pattern"):
            sub = ro.get(bucket)
            if sub is None:
                continue
            so = sub.get_object() if hasattr(sub, "get_object") else sub
            if not isinstance(so, dict):
                raise ValueError(f"Malformed PDF {bucket} dictionary ({type(so).__name__}) in {ctx}")
            for name, v in so.items():
                vo = v.get_object() if hasattr(v, "get_object") else v
                if not isinstance(vo, dict):
                    continue
                if str(vo.get("/Subtype") or "") == "/Image":
                    xobj_images += 1
                else:
                    sub_ctx = f"{ctx}/{bucket[1:]}:{name}"
                    if isinstance(vo, StreamObject):
                        _scan_content(v, sub_ctx)
                    _walk_resources(vo.get("/Resources"), sub_ctx)
        fonts = ro.get("/Font")
        if fonts is not None:
            fo = fonts.get_object() if hasattr(fonts, "get_object") else fonts
            if isinstance(fo, dict):
                for fname, fv in fo.items():
                    fvo = fv.get_object() if hasattr(fv, "get_object") else fv
                    if isinstance(fvo, dict) and str(fvo.get("/Subtype") or "") == "/Type3":
                        f_ctx = f"{ctx}/Font:{fname}"
                        _walk_resources(fvo.get("/Resources"), f_ctx)
                        cp = fvo.get("/CharProcs")
                        if cp is not None:
                            cpo = cp.get_object() if hasattr(cp, "get_object") else cp
                            if isinstance(cpo, dict):
                                for gname, gv in cpo.items():
                                    gvo = gv.get_object() if hasattr(gv, "get_object") else gv
                                    if isinstance(gvo, StreamObject):
                                        _scan_content(gv, f"{f_ctx}/CharProc:{gname}")
        egs = ro.get("/ExtGState")
        if egs is not None:
            eo = egs.get_object() if hasattr(egs, "get_object") else egs
            if isinstance(eo, dict):
                for ename, ev in eo.items():
                    evo = ev.get_object() if hasattr(ev, "get_object") else ev
                    if isinstance(evo, dict):
                        sm = evo.get("/SMask")
                        smo = sm.get_object() if (sm is not None and hasattr(sm, "get_object")) else sm
                        if isinstance(smo, dict) and "/G" in smo:
                            g_raw = smo.get("/G")
                            g_obj = g_raw.get_object() if hasattr(g_raw, "get_object") else g_raw
                            if isinstance(g_obj, StreamObject):
                                g_ctx = f"{ctx}/ExtGState:{ename}/SMask"
                                _scan_content(g_raw, g_ctx)
                                _walk_resources(g_obj.get("/Resources"), g_ctx)

    for pg_idx, pg in enumerate(reader.pages, 1):
        p_ctx = f"{pdf_path.name}:p{pg_idx}"
        _scan_content(pg.get("/Contents"), p_ctx)
        _walk_resources(pg.get("/Resources"), p_ctx)
        annots = pg.get("/Annots")
        if annots is not None:
            ao_list = annots.get_object() if hasattr(annots, "get_object") else annots
            if isinstance(ao_list, list):
                for a_idx, an in enumerate(ao_list, 1):
                    ao = an.get_object() if hasattr(an, "get_object") else an
                    if not isinstance(ao, dict):
                        continue
                    ap = ao.get("/AP")
                    if ap is None:
                        continue
                    apo = ap.get_object() if hasattr(ap, "get_object") else ap
                    if not isinstance(apo, dict):
                        continue
                    for ap_key in ("/N", "/R", "/D"):
                        st = apo.get(ap_key)
                        if st is None:
                            continue
                        sto = st.get_object() if hasattr(st, "get_object") else st
                        ap_ctx = f"{p_ctx}/Annot{a_idx}/AP{ap_key}"
                        if isinstance(sto, StreamObject):
                            _scan_content(st, ap_ctx)
                            _walk_resources(sto.get("/Resources"), ap_ctx)
                        elif isinstance(sto, dict):
                            for sub_k, sub_v in sto.items():
                                svo = sub_v.get_object() if hasattr(sub_v, "get_object") else sub_v
                                if isinstance(svo, StreamObject):
                                    _scan_content(sub_v, f"{ap_ctx}:{sub_k}")
                                    _walk_resources(svo.get("/Resources"), f"{ap_ctx}:{sub_k}")

    return {
        "raster_image_xobjects": xobj_images,
        "inline_raster_images": inline_images,
        "total_raster_images": xobj_images + inline_images,
        "streams_inspected": streams_inspected,
    }


def require_zero_pdf_rasters(pdf_path: Path, label: str) -> dict:
    """Fail closed if a PDF expected to be pure vector contains any raster XObject or inline image."""
    info = inspect_pdf_rasters(pdf_path)
    _require(
        info["total_raster_images"] == 0,
        f"Unexpected raster image(s) in pure-vector PDF {label}: "
        f"raster_image_xobjects={info['raster_image_xobjects']}, "
        f"inline_raster_images={info['inline_raster_images']}, "
        f"total_raster_images={info['total_raster_images']} (expected 0)",
    )
    return info


def _inspect_pdf(pdf_path: Path, expected_w_cm: float, expected_h_cm: float) -> tuple[dict, dict]:
    """Validate exported vector PDF invariants and return (deterministic_fields, runtime_diagnostics)."""
    import pypdf
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    _require(len(reader.pages) == 1, f"Exported diagram PDF must have 1 page, got {len(reader.pages)}: {pdf_path}")
    page = reader.pages[0]
    text = (page.extract_text() or "").strip()
    _require(bool(text), f"Exported diagram PDF has no extractable text: {pdf_path}")

    # Shared fail-closed raster check covering /Image XObjects and inline BI/ID/EI images.
    raster_info = require_zero_pdf_rasters(pdf_path, str(pdf_path))

    # Collect resolved BaseFont identities recursively for runtime diagnostics.
    resolved_fonts: set[str] = set()
    seen_font_res: set[int] = set()

    def _collect_fonts(resources) -> None:
        if resources is None:
            return
        res_obj = resources.get_object() if hasattr(resources, "get_object") else resources
        if not isinstance(res_obj, dict) or id(res_obj) in seen_font_res:
            return
        seen_font_res.add(id(res_obj))
        fonts = res_obj.get("/Font")
        if fonts is not None:
            fonts_dict = fonts.get_object() if hasattr(fonts, "get_object") else fonts
            for fval in fonts_dict.values():
                fobj = fval.get_object() if hasattr(fval, "get_object") else fval
                bf = fobj.get("/BaseFont")
                if bf is not None:
                    name = str(bf).lstrip("/")
                    if "+" in name and len(name.split("+", 1)[0]) == 6:
                        name = name.split("+", 1)[1]
                    resolved_fonts.add(name)
        xobjs = res_obj.get("/XObject")
        if xobjs is None:
            return
        xobjs_dict = xobjs.get_object() if hasattr(xobjs, "get_object") else xobjs
        for val in xobjs_dict.values():
            obj = val.get_object() if hasattr(val, "get_object") else val
            if isinstance(obj, dict) and str(obj.get("/Subtype", "")) == "/Form":
                _collect_fonts(obj.get("/Resources"))

    _collect_fonts(page.get("/Resources"))

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
        "raster_image_xobjects": raster_info["raster_image_xobjects"],
        "inline_raster_images": raster_info["inline_raster_images"],
        "total_raster_images": raster_info["total_raster_images"],
        "has_extractable_text": True,
    }
    runtime = {
        "pypdf_version": getattr(pypdf, "__version__", "unknown"),
        "extracted_text_chars": len(text),
        "streams_inspected": raster_info["streams_inspected"],
        "resolved_fonts": sorted(resolved_fonts),
    }
    return deterministic, runtime


def export_figures(
    root: Path,
    outdir: Path,
    *,
    surface: str = "manual",
    fmt: str = "pdf",
    ppi: int = 300,
    typst_bin: str | None = None,
    check_only: bool = False,
    runtime_out: dict | None = None,
    before_commit_hook=None,
) -> dict:
    root = Path(root).resolve()
    outdir = Path(outdir).resolve()
    _require(surface in ("main", "manual"), f"Unsupported export surface: {surface!r}")
    _require(fmt in ("pdf", "png"), f"Unsupported diagram export format: {fmt!r} (expected 'pdf' or 'png')")
    if fmt == "png":
        _require(ppi in (300, 600), f"PNG diagram export requires --ppi 300 or 600, got {ppi}")

    typst = find_typst(typst_bin)
    ver_proc = subprocess.run([typst, "--version"], capture_output=True, text=True, check=True)
    typst_version = ver_proc.stdout.strip()

    schema_path = root / SCHEMA_REL
    _require(schema_path.is_file(), f"Missing Typst schema: {schema_path}")
    schema_sha = sha256_file(schema_path)
    plots_path = root / PLOTS_REL
    plots_sha = sha256_file(plots_path) if plots_path.is_file() else None

    bindings = discover_diagrams(root, surface=surface)
    _require(len(bindings) > 0, f"No active native Typst {surface} figures found to export")

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
                "surface": item["surface"],
                "component_kind": item["component_kind"],
                "slug": slug,
                "label": item["label"],
                "typst_section": item["typst_section"],
                "diagram_component": item["diagram_component"],
                "diagram_sha256": item["diagram_sha256"],
                "data_inputs": item["data_inputs"],
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
        manifest: dict = {
            "schema": MANIFEST_SCHEMA,
            "surface": surface,
            "format": fmt,
            "ppi": ppi if fmt == "png" else None,
            "background": DECLARED_BACKGROUND,
            "font_families": DECLARED_FONT_FAMILIES,
            "schema_path": SCHEMA_REL.as_posix(),
            "schema_sha256": schema_sha,
            "plots_lib_path": PLOTS_REL.as_posix() if plots_sha else None,
            "plots_lib_sha256": plots_sha,
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
            "surface": surface,
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
    ap.add_argument("--surface", choices=("main", "manual"), default="manual")
    ap.add_argument("--outdir", type=Path, default=None)
    ap.add_argument("--format", choices=("pdf", "png"), default="pdf")
    ap.add_argument("--ppi", type=int, default=300, choices=(300, 600))
    ap.add_argument("--typst-bin", default=None)
    ap.add_argument("--check", action="store_true", help="Verify outdir matches fresh export without modifying it")
    ap.add_argument("--runtime-report", type=Path, default=None, help="Optional JSON path for runtime/extractor diagnostics")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    default_out = Path("latex/figures/generated") if args.surface == "main" else Path("latex/manual/figures/generated")
    out_arg = args.outdir if args.outdir is not None else default_out
    outdir = out_arg if out_arg.is_absolute() else (root / out_arg)
    runtime_diag: dict = {}
    manifest = export_figures(
        root,
        outdir,
        surface=args.surface,
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
