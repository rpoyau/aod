"""Adversarial Phase 5 (P5-geometric-figures-and-seal) QA & Handoff Verification Suite.

Independently verifies all Phase 5 deliverables and cross-phase M4.5 seals across
BND-P5-01 through BND-P5-04:
1. Zero `#aod-panel` text cards remaining in Main (`05_curl_closure_duon_current.typ`,
   `06_field.typ`), Manual §2 (`00_native_closure_wave_temporal_fixtures.typ`), or any
   active Typst content unit; all 9 newly authored geometric vector figures (7 Main +
   2 Manual) exist under `typst/lib/figures/{main,manual}/`, are actively `#include`d
   inside `#figure(...) <fig:...>`, contain genuine geometric primitives (`#aod-canvas`,
   `#aod-figure-header`, arrows, boxes, circles/rings/vertices), and propagate cleanly
   into generated `latex/`.
2. Zero legacy `y = 0.54 / 0.94` colliding title-subtitle headers and zero stale claims
   across all 49 Manual vector figures AND all 53 exported Manual PDFs, plus positive
   claim/citation verification (`53` vectors / `RC-045`, `26.57055342` + `SD-008`,
   `raw 28`, `SD-007` + `SD-004` + `RC-027`, `RC-032`).
3. 100% Gate A2 evaluation-policy cleanliness across all 110 files (44 content units +
   4 shared diagrams + 62 vector figures) via `verify_typst_parity.verify_typst_evaluation_policy`,
   plus adversarial negative controls and verification of all 12 live CSV tables bound
   via `#aod-csv-table("/manual/data/boundary_sadar/...")`.
4. 66-figure exported PDF & `typst/figure_inventory.json` / `typst/manifest.json` /
   `latex/GENERATION_MANIFEST.json` / `typst/lib/main_registry.json` cryptographic seal,
   including live `pypdf` + `export_typst_figures.require_zero_pdf_rasters` + `pdftotext`
   verification on every exported PDF.
5. Historical `98ddfa0` baseline archive (`211/211`: 41 `archived_editorial_tex` +
   1 `archived_baseline_data` for `cells_geometry.json` vs live G6 4D tesseract data +
   169 preserved in place), honest M4.5 G6 representation-change ledger (`8` amended,
   `9` untouched, `CELL_MEASURE_SPEC.json` `scientific_substance_changed is True`),
   `verify_baseline_immutability`, and release bundler `.uow/` exclusion + complete
   `build_source_tree` verification.
6. End-to-end cross-phase M4.5 integrity: AST audit confirming zero bare `assert` in
   4 core verification/release scripts, live subprocess verification of
   `scripts/typ2tex.py --root . --outdir latex --check` and
   `scripts/audit_scientific_sources.py .`, plus self-AST audit enforcing zero bare
   `assert` and zero `float` literals/references in this QA file.
"""
from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
import csv
from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any

from pypdf import PdfReader
from pypdf.generic import StreamObject

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

# =============================================================================
# Canonical Phase 5 Expectations (Exact Integer / String / SHA-256 Constants)
# =============================================================================

NINE_NEW_GEOMETRIC_FIGURES: tuple[tuple[str, str, str, str, str, str], ...] = (
    # (owning_typ, figure_component_rel, expected_include_str, expected_label, latex_tex_rel, exported_pdf_name)
    (
        "typst/sections/05_curl_closure_duon_current.typ",
        "typst/lib/figures/main/curl_to_duon_current_support.typ",
        "../lib/figures/main/curl_to_duon_current_support.typ",
        "fig:curl-to-duon-current-support",
        "latex/sections/05_curl_closure_duon_current.tex",
        "curl-to-duon-current-support.pdf",
    ),
    (
        "typst/sections/05_curl_closure_duon_current.typ",
        "typst/lib/figures/main/closure_ladder.typ",
        "../lib/figures/main/closure_ladder.typ",
        "fig:closure-ladder",
        "latex/sections/05_curl_closure_duon_current.tex",
        "closure-ladder.pdf",
    ),
    (
        "typst/sections/06_field.typ",
        "typst/lib/figures/main/sadar_b_scoped_afc_flux.typ",
        "../lib/figures/main/sadar_b_scoped_afc_flux.typ",
        "fig:sadar-b-scoped-afc-flux",
        "latex/sections/06_field.tex",
        "sadar-b-scoped-afc-flux.pdf",
    ),
    (
        "typst/sections/06_field.typ",
        "typst/lib/figures/main/duon_current_boundary_accounting.typ",
        "../lib/figures/main/duon_current_boundary_accounting.typ",
        "fig:v39-duon-current-boundary-accounting",
        "latex/sections/06_field.tex",
        "duon-current-boundary-accounting.pdf",
    ),
    (
        "typst/sections/06_field.typ",
        "typst/lib/figures/main/sadar_boundary_relative_balance.typ",
        "../lib/figures/main/sadar_boundary_relative_balance.typ",
        "fig:sadar-boundary-relative-balance",
        "latex/sections/06_field.tex",
        "sadar-boundary-relative-balance.pdf",
    ),
    (
        "typst/sections/06_field.typ",
        "typst/lib/figures/main/fractal_calculus_spine.typ",
        "../lib/figures/main/fractal_calculus_spine.typ",
        "fig:fractal-calculus-spine",
        "latex/sections/06_field.tex",
        "fractal-calculus-spine.pdf",
    ),
    (
        "typst/sections/06_field.typ",
        "typst/lib/figures/main/cycle_wave_identity.typ",
        "../lib/figures/main/cycle_wave_identity.typ",
        "fig:cycle-wave-identity",
        "latex/sections/06_field.tex",
        "cycle-wave-identity.pdf",
    ),
    (
        "typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ",
        "typst/lib/figures/manual/field_count_scope.typ",
        "../../lib/figures/manual/field_count_scope.typ",
        "fig:field-count",
        "latex/manual/sections/00_native_closure_wave_temporal_fixtures.tex",
        "field-count-scope.pdf",
    ),
    (
        "typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ",
        "typst/lib/figures/manual/fractal_tesseract_beat_family.typ",
        "../../lib/figures/manual/fractal_tesseract_beat_family.typ",
        "fig:fractal-tesseract-beat-family",
        "latex/manual/sections/00_native_closure_wave_temporal_fixtures.tex",
        "fractal-tesseract-beat-family.pdf",
    ),
)

EXPECTED_12_MANUAL_CSV_TABLES: dict[str, str] = {
    "00_native_closure_wave_temporal_fixtures.typ": "/manual/data/boundary_sadar/native_closure_wave_dec_walk.csv",
    "00_awareness_fixtures.typ": "/manual/data/boundary_sadar/awareness_operativity_dec_walk.csv",
    "01_rest_energy_prediction.typ": "/manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv",
    "02_hydrogen_facing_shell_tests.typ": "/manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv",
    "03_short_window_rcd_shedding_fixtures.typ": "/manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv",
    "03_temporal_observation.typ": "/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv",
    "04_boundary_current_applications.typ": "/manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv",
    "05_solar_system_field_tests.typ": "/manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv",
    "06_field_dynamics_applications.typ": "/manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv",
    "07_galactic_lensing_plan.typ": "/manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv",
    "A_simulation_fixtures_and_tau_prediction_context.typ": "/manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv",
    "C_3d_coordinate_phase_cycle_delta3_fixture.typ": "/manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv",
}

ARCHIVED_CELLS_GEOMETRY_ORIG: str = "manual/data/cell_measures/cells_geometry.json"
ARCHIVED_CELLS_GEOMETRY_RETAINED: str = (
    "archive/latex_baseline_98ddfa0/manual/data/cell_measures/cells_geometry.json"
)
ARCHIVED_CELLS_GEOMETRY_SHA256: str = (
    "f941856c7bc86356bdb461e44ecaa34ae399597e7abb76ed61178b20b8232ef0"
)
ARCHIVED_CELLS_GEOMETRY_BYTES: int = 58548
LIVE_CELLS_GEOMETRY_BYTES: int = 78163

ZERO_ASSERT_AUDITED_SCRIPTS: tuple[str, ...] = (
    "scripts/materialize_latex_baseline.py",
    "scripts/build_release_bundle.py",
    "scripts/audit_ontology_compaction.py",
    "scripts/verify_typst_parity.py",
)

ARROW_PRIMITIVES: tuple[str, ...] = (
    "aod-arrow(",
    "aod-arc-arrow(",
    "aod-curve-arrow(",
    "aod-wavy-arrow(",
)
BOX_PRIMITIVES: tuple[str, ...] = (
    "aod-box(",
    "aod-box-tl(",
)
CIRCLE_OR_NODE_PRIMITIVES: tuple[str, ...] = (
    "aod-circle(",
    "aod-chiral-vertex(",
    "aod-seat-ring(",
    "aod-tesseract-q4(",
)


# =============================================================================
# Non-Strippable Assertion & Utility Helpers (Zero bare assert, Zero float)
# =============================================================================


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _check_eq(actual: object, expected: object, label: str) -> None:
    if actual != expected or type(actual) is not type(expected):
        raise AssertionError(
            f"{label}: mismatch\n"
            f"  actual   ({type(actual).__name__}): {actual!r}\n"
            f"  expected ({type(expected).__name__}): {expected!r}"
        )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


@lru_cache(maxsize=8)
def _load_script_module(module_name: str, rel_path: str) -> ModuleType:
    script_path = REPO_ROOT.joinpath(rel_path)
    _check(script_path.is_file(), f"missing script module: {rel_path}")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    _check(spec is not None and spec.loader is not None, f"failed to load module spec for {rel_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_json(rel_path: str) -> dict[str, Any]:
    path = REPO_ROOT.joinpath(rel_path)
    _check(path.is_file(), f"missing required JSON artifact: {rel_path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    _check(isinstance(data, dict), f"expected JSON object in {rel_path}")
    return data


def _tool_env() -> dict[str, str]:
    env = dict(os.environ)
    local_bin = str(Path.home().joinpath(".local", "bin"))
    cur_path = env.get("PATH", "")
    parts = cur_path.split(os.pathsep) if cur_path else []
    if local_bin not in parts:
        env["PATH"] = f"{local_bin}{os.pathsep}{cur_path}" if cur_path else local_bin
    return env


_PDF_INLINE_BI_RE = re.compile(rb"(?:^|[\x00\t\n\x0c\r ])BI[\x00\t\n\x0c\r ]")


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract PDF text deterministically offline via pdftotext (fast) with pypdf fallback."""
    pdftotext_bin = shutil.which("pdftotext")
    if pdftotext_bin is not None:
        proc = subprocess.run(
            [pdftotext_bin, str(pdf_path), "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        _check(
            proc.returncode == 0,
            f"pdftotext failed on {pdf_path.name} (rc={proc.returncode}): {proc.stderr}",
        )
        return proc.stdout
    reader = PdfReader(str(pdf_path))
    return "\n".join((pg.extract_text() or "") for pg in reader.pages)


def _inspect_pure_vector_pdf(pdf_path: Path) -> dict[str, Any]:
    """Deep-inspect a PDF: 1 page, 0 /Image XObjects (recursive), 0 inline BI rasters, BT text present."""
    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    seen_res: set[int] = set()
    xobj_images = 0
    inline_images = 0
    has_bt = False

    def _scan_stream(obj: Any) -> None:
        nonlocal inline_images, has_bt
        if obj is None:
            return
        resolved = obj.get_object() if hasattr(obj, "get_object") else obj
        if isinstance(resolved, list):
            for item in resolved:
                _scan_stream(item)
            return
        if isinstance(resolved, StreamObject):
            data = resolved.get_data()
            if b"BT" in data:
                has_bt = True
            if _PDF_INLINE_BI_RE.search(data) is not None:
                inline_images += 1

    def _walk_resources(res: Any) -> None:
        nonlocal xobj_images
        if res is None:
            return
        ro = res.get_object() if hasattr(res, "get_object") else res
        if not isinstance(ro, dict) or id(ro) in seen_res:
            return
        seen_res.add(id(ro))
        for bucket in ("/XObject", "/Pattern"):
            sub = ro.get(bucket)
            if sub is None:
                continue
            so = sub.get_object() if hasattr(sub, "get_object") else sub
            if not isinstance(so, dict):
                continue
            for val in so.values():
                vo = val.get_object() if hasattr(val, "get_object") else val
                if not isinstance(vo, dict):
                    continue
                if str(vo.get("/Subtype") or "") == "/Image":
                    xobj_images += 1
                else:
                    if isinstance(vo, StreamObject):
                        _scan_stream(vo)
                    _walk_resources(vo.get("/Resources"))
        fonts = ro.get("/Font")
        if fonts is not None:
            fo = fonts.get_object() if hasattr(fonts, "get_object") else fonts
            if isinstance(fo, dict):
                for fv in fo.values():
                    fvo = fv.get_object() if hasattr(fv, "get_object") else fv
                    if isinstance(fvo, dict) and str(fvo.get("/Subtype") or "") == "/Type3":
                        _walk_resources(fvo.get("/Resources"))
                        cp = fvo.get("/CharProcs")
                        if cp is not None:
                            cpo = cp.get_object() if hasattr(cp, "get_object") else cp
                            if isinstance(cpo, dict):
                                for gv in cpo.values():
                                    _scan_stream(gv)
        egs = ro.get("/ExtGState")
        if egs is not None:
            eo = egs.get_object() if hasattr(egs, "get_object") else egs
            if isinstance(eo, dict):
                for ev in eo.values():
                    evo = ev.get_object() if hasattr(ev, "get_object") else ev
                    if isinstance(evo, dict):
                        sm = evo.get("/SMask")
                        smo = sm.get_object() if (sm is not None and hasattr(sm, "get_object")) else sm
                        if isinstance(smo, dict) and "/G" in smo:
                            g_raw = smo.get("/G")
                            g_obj = g_raw.get_object() if hasattr(g_raw, "get_object") else g_raw
                            if isinstance(g_obj, StreamObject):
                                _scan_stream(g_obj)
                                _walk_resources(g_obj.get("/Resources"))

    for pg in reader.pages:
        _scan_stream(pg.get("/Contents"))
        _walk_resources(pg.get("/Resources"))
        annots = pg.get("/Annots")
        if annots is not None:
            ao_list = annots.get_object() if hasattr(annots, "get_object") else annots
            if isinstance(ao_list, list):
                for an in ao_list:
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
                        if isinstance(sto, StreamObject):
                            _scan_stream(sto)
                            _walk_resources(sto.get("/Resources"))
                        elif isinstance(sto, dict):
                            for sub_v in sto.values():
                                svo = sub_v.get_object() if hasattr(sub_v, "get_object") else sub_v
                                if isinstance(svo, StreamObject):
                                    _scan_stream(svo)
                                    _walk_resources(svo.get("/Resources"))

    return {
        "page_count": page_count,
        "raster_image_xobjects": xobj_images,
        "inline_raster_images": inline_images,
        "total_raster_images": xobj_images + inline_images,
        "has_bt_text": has_bt,
    }


# =============================================================================
# 1. Zero `#aod-panel` Cards & 9 Newly Authored Geometric Vector Figures
# =============================================================================


def test_zero_aod_panel_cards_and_nine_new_geometric_figures() -> None:
    """Verify zero `#aod-panel` text cards remain and all 9 new vector figures are genuine geometric diagrams."""
    # Confirm collision-proof #aod-figure-header primitive exists in typst/lib/aod_plots.typ
    plots_text = REPO_ROOT.joinpath("typst", "lib", "aod_plots.typ").read_text(encoding="utf-8")
    _check("#let aod-figure-header(" in plots_text, "aod_plots.typ missing #let aod-figure-header definition")
    hdr_block = plots_text[plots_text.index("#let aod-figure-header("):]
    _check("stack(dir: ttb" in hdr_block, "aod-figure-header must stack title/subtitle vertically via stack(dir: ttb)")
    _check("fill: black" in hdr_block, "aod-figure-header must enforce opaque black text fill")
    _check("< 6pt" in hdr_block, "aod-figure-header must enforce >= 6pt minimum font-size clamp")

    # 1a. Zero `#aod-panel` text cards in Main §05, Main §06, Manual §2, and ALL active Typst content/figure units
    target_zero_panel_files = (
        "typst/sections/05_curl_closure_duon_current.typ",
        "typst/sections/06_field.typ",
        "typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ",
    )
    for rel in target_zero_panel_files:
        text = REPO_ROOT.joinpath(rel).read_text(encoding="utf-8")
        _check("aod-panel" not in text, f"legacy #aod-panel text card still present in {rel}")

    content_dirs = (
        REPO_ROOT.joinpath("typst", "sections"),
        REPO_ROOT.joinpath("typst", "appendices"),
        REPO_ROOT.joinpath("typst", "manual", "sections"),
        REPO_ROOT.joinpath("typst", "manual", "appendices"),
        REPO_ROOT.joinpath("typst", "lib", "diagrams"),
        REPO_ROOT.joinpath("typst", "lib", "figures", "main"),
        REPO_ROOT.joinpath("typst", "lib", "figures", "manual"),
    )
    for directory in content_dirs:
        for typ_file in sorted(directory.glob("*.typ")):
            rel = typ_file.relative_to(REPO_ROOT).as_posix()
            _check(
                "aod-panel" not in typ_file.read_text(encoding="utf-8"),
                f"unexpected #aod-panel occurrence in {rel}",
            )

    # 1b. Verify exact 9 newly authored geometric vector figures (7 Main + 2 Manual)
    _check_eq(len(NINE_NEW_GEOMETRIC_FIGURES), 9, "newly authored geometric vector figure count")
    main_new_count = sum(1 for row in NINE_NEW_GEOMETRIC_FIGURES if "/main/" in row[1])
    manual_new_count = sum(1 for row in NINE_NEW_GEOMETRIC_FIGURES if "/manual/" in row[1])
    _check_eq(main_new_count, 7, "Main newly authored geometric figure count")
    _check_eq(manual_new_count, 2, "Manual newly authored geometric figure count")

    for owning_typ, fig_rel, inc_str, expected_label, latex_rel, pdf_name in NINE_NEW_GEOMETRIC_FIGURES:
        fig_path = REPO_ROOT.joinpath(fig_rel)
        _check(fig_path.is_file(), f"missing newly authored vector figure: {fig_rel}")
        fig_text = fig_path.read_text(encoding="utf-8")

        # Must use aod_plots.typ, literal dimensions, single #aod-canvas, and #aod-figure-header
        _check(
            '#import "/typst/lib/aod_plots.typ": *' in fig_text,
            f"{fig_rel}: missing #import \"/typst/lib/aod_plots.typ\": *",
        )
        _check(
            re.search(r"#let\s+fig-width-cm\s*=\s*[0-9]+(?:\.[0-9]+)?\b", fig_text) is not None,
            f"{fig_rel}: missing literal fig-width-cm",
        )
        _check(
            re.search(r"#let\s+fig-height-cm\s*=\s*[0-9]+(?:\.[0-9]+)?\b", fig_text) is not None,
            f"{fig_rel}: missing literal fig-height-cm",
        )
        _check_eq(fig_text.count("#aod-canvas("), 1, f"{fig_rel} #aod-canvas count")
        _check("#aod-figure-header(" in fig_text, f"{fig_rel}: missing collision-proof #aod-figure-header(")

        # Must contain genuine geometric drawing primitives (arrows + boxes + circles/rings/vertices)
        _check(
            any(tok in fig_text for tok in ARROW_PRIMITIVES),
            f"{fig_rel}: missing arrow geometric drawing primitive ({ARROW_PRIMITIVES})",
        )
        _check(
            any(tok in fig_text for tok in BOX_PRIMITIVES),
            f"{fig_rel}: missing box geometric drawing primitive ({BOX_PRIMITIVES})",
        )
        _check(
            any(tok in fig_text for tok in CIRCLE_OR_NODE_PRIMITIVES),
            f"{fig_rel}: missing circle/ring/vertex geometric drawing primitive ({CIRCLE_OR_NODE_PRIMITIVES})",
        )

        # Must be actively #include-d inside #figure(...) <fig:...> in its owning Typst section
        owner_text = REPO_ROOT.joinpath(owning_typ).read_text(encoding="utf-8")
        fig_block_pat = re.compile(
            r"#figure\(\s*kind:\s*image,\s*\[[^\]]*#include\s+\""
            + re.escape(inc_str)
            + r"\"[^\]]*\],\s*caption:\s*\[.*?\],?\s*\)\s*<"
            + re.escape(expected_label)
            + r">",
            flags=re.DOTALL,
        )
        _check(
            fig_block_pat.search(owner_text) is not None,
            f"{owning_typ}: missing active #figure(kind: image, [#include \"{inc_str}\"], ...) <{expected_label}>",
        )

        # Generated LaTeX counterpart must embed the exported PDF via \includegraphics
        tex_text = REPO_ROOT.joinpath(latex_rel).read_text(encoding="utf-8")
        _check(
            re.search(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*" + re.escape(pdf_name) + r"\}", tex_text)
            is not None,
            f"{latex_rel}: missing \\includegraphics for exported PDF {pdf_name}",
        )


# =============================================================================
# 2. Zero Legacy `y = 0.54 / 0.94` Colliding Headers & Zero Stale Claims
# =============================================================================


def test_manual_49_figures_and_pdfs_collision_and_stale_claim_audit() -> None:
    """Verify zero y=0.54/0.94 colliding headers and zero stale claims across all 49 Manual figures + PDFs."""
    main_figs = sorted(REPO_ROOT.joinpath("typst", "lib", "figures", "main").glob("*.typ"))
    manual_figs = sorted(REPO_ROOT.joinpath("typst", "lib", "figures", "manual").glob("*.typ"))
    _check_eq(len(main_figs), 13, "Main vector figure .typ count")
    _check_eq(len(manual_figs), 49, "Manual vector figure .typ count")

    # Anchor on the 2nd argument (y-coordinate) of aod-text(x, y, ...) to avoid false hits on x-coordinates
    y054_pat = re.compile(r"aod-text\(\s*[^,\n]+,\s*0\.54\b")
    y094_pat = re.compile(r"aod-text\(\s*[^,\n]+,\s*0\.94\b")

    global_stale_tokens: tuple[str, ...] = (
        "64.70291920",
        "raw count 26",
        "raw 26",
        "52-vector",
        "52 vectors",
        "fifty-two",
    )

    for fig_path in manual_figs:
        text = fig_path.read_text(encoding="utf-8")
        _check(
            y054_pat.search(text) is None,
            f"{fig_path.name}: legacy colliding title y=0.54 aod-text(...) found",
        )
        _check(
            y094_pat.search(text) is None,
            f"{fig_path.name}: legacy colliding subtitle y=0.94 aod-text(...) found",
        )
        lowered = text.lower()
        for stale in global_stale_tokens:
            _check(
                stale.lower() not in lowered,
                f"{fig_path.name}: forbidden stale claim {stale!r} present in Typst source",
            )

    # Also verify Main vector figures carry zero colliding y=0.54/0.94 headers
    for fig_path in main_figs:
        text = fig_path.read_text(encoding="utf-8")
        _check(
            y054_pat.search(text) is None and y094_pat.search(text) is None,
            f"{fig_path.name}: legacy colliding y=0.54/0.94 aod-text(...) found in Main figure",
        )

    # Scan ALL 53 exported Manual PDFs (49 vector figures + 4 flowcharts) for stale claims
    manual_pdf_dir = REPO_ROOT.joinpath("latex", "manual", "figures", "generated")
    manual_pdfs = sorted(manual_pdf_dir.glob("*.pdf"))
    _check_eq(len(manual_pdfs), 53, "exported Manual PDF count")

    with ThreadPoolExecutor(max_workers=4) as pool:
        extracted_texts = list(pool.map(_extract_pdf_text, manual_pdfs))
    pdf_text_cache: dict[str, str] = {}
    for pdf_path, extracted in zip(manual_pdfs, extracted_texts):
        _check(bool(extracted.strip()), f"{pdf_path.name}: exported PDF has empty extracted text")
        pdf_text_cache[pdf_path.name] = extracted
        lowered_pdf = extracted.lower()
        for stale in global_stale_tokens:
            _check(
                stale.lower() not in lowered_pdf,
                f"{pdf_path.name}: forbidden stale claim {stale!r} rendered in exported PDF",
            )

    # Targeted figure-specific anti-stale and positive-claim verification (both .typ source AND exported PDF)
    def _read_manual_fig(name: str) -> str:
        return REPO_ROOT.joinpath("typst", "lib", "figures", "manual", name).read_text(encoding="utf-8")

    # (a) qext_quarantine_firewall.typ
    qext_typ = _read_manual_fig("qext_quarantine_firewall.typ")
    qext_pdf = pdf_text_cache["qext-quarantine-firewall.pdf"]
    _check("RC-025" not in qext_typ, "qext_quarantine_firewall.typ contains forbidden stale RC-025")
    _check("RC-025" not in qext_pdf, "qext-quarantine-firewall.pdf renders forbidden stale RC-025")
    for req in ("SD-007", "SD-004", "RC-027"):
        _check(req in qext_typ, f"qext_quarantine_firewall.typ missing {req!r}")
        _check(req in qext_pdf, f"qext-quarantine-firewall.pdf missing rendered {req!r}")

    # (b) wire_moving_boundary_feynman.typ
    wire_typ = _read_manual_fig("wire_moving_boundary_feynman.typ")
    wire_pdf = pdf_text_cache["wire-moving-boundary-feynman.pdf"]
    for bad in ("RC-030", "RC-031"):
        _check(bad not in wire_typ, f"wire_moving_boundary_feynman.typ contains forbidden stale {bad!r}")
        _check(bad not in wire_pdf, f"wire-moving-boundary-feynman.pdf renders forbidden stale {bad!r}")
    _check("RC-032" in wire_typ, "wire_moving_boundary_feynman.typ missing RC-032")
    _check("RC-032" in wire_pdf, "wire-moving-boundary-feynman.pdf missing rendered RC-032")

    # (c) field_dynamics_boundary_feynman.typ (binds 26.57055342 live from sparc_pooled_primary_exact.csv)
    fd_typ = _read_manual_fig("field_dynamics_boundary_feynman.typ")
    fd_pdf = pdf_text_cache["field-dynamics-boundary-feynman.pdf"]
    for bad in ("RC-032", "64.70291920"):
        _check(bad not in fd_typ, f"field_dynamics_boundary_feynman.typ contains forbidden stale {bad!r}")
        _check(bad not in fd_pdf, f"field-dynamics-boundary-feynman.pdf renders forbidden stale {bad!r}")
    for req_typ in ("SD-008", "RC-041", "sparc_pooled_primary_exact.csv", "MAPE_U_display_8dp"):
        _check(req_typ in fd_typ, f"field_dynamics_boundary_feynman.typ missing live binding/token {req_typ!r}")
    with REPO_ROOT.joinpath("manual", "data", "boundary_sadar", "sparc_pooled_primary_exact.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        sparc_rows = list(csv.DictReader(fh))
    _check_eq(len(sparc_rows), 1, "sparc_pooled_primary_exact.csv row count")
    _check_eq(sparc_rows[0]["MAPE_U_display_8dp"], "26.57055342", "sparc_pooled_primary_exact MAPE_U_display_8dp")
    for req_pdf in ("26.57055342", "SD-008", "RC-041"):
        _check(req_pdf in fd_pdf, f"field-dynamics-boundary-feynman.pdf missing rendered {req_pdf!r}")

    # (d) registry_engine_coverage_atlas.typ & five_boundary_calculation_spine.typ
    for typ_name, pdf_name in (
        ("registry_engine_coverage_atlas.typ", "registry-engine-coverage-atlas.pdf"),
        ("five_boundary_calculation_spine.typ", "five-boundary-calculation-spine.pdf"),
    ):
        typ_src = _read_manual_fig(typ_name)
        pdf_src = pdf_text_cache[pdf_name]
        for bad in ("52-vector", "RC-044"):
            _check(bad not in typ_src, f"{typ_name} contains forbidden stale {bad!r}")
            _check(bad not in pdf_src, f"{pdf_name} renders forbidden stale {bad!r}")
        for req in ("53", "RC-045", "SD-008"):
            _check(req in typ_src, f"{typ_name} missing required token {req!r}")
            _check(req in pdf_src, f"{pdf_name} missing rendered token {req!r}")

    # (e) tau_five_boundary_sadar_setup.typ
    tau_typ = _read_manual_fig("tau_five_boundary_sadar_setup.typ")
    tau_pdf = pdf_text_cache["tau-five-boundary-sadar-setup.pdf"]
    _check(
        re.search(r"raw\s+\$?28\b", tau_typ) is not None,
        "tau_five_boundary_sadar_setup.typ missing 'raw 28' / 'raw $28'",
    )
    _check("raw 28" in tau_pdf, "tau-five-boundary-sadar-setup.pdf missing rendered 'raw 28'")
    _check("RC-027" in tau_typ and "RC-027" in tau_pdf, "tau figure/PDF missing RC-027")


# =============================================================================
# 3. 100% Gate A2 Evaluation Policy (110 Files) & All 12 Live `#aod-csv-table`s
# =============================================================================


def test_gate_a2_evaluation_policy_110_files_and_negative_controls() -> None:
    """Run verify_typst_evaluation_policy directly across all 110 files and test adversarial negative controls."""
    vtp = _load_script_module("qa_p5_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = _load_json("typst/manifest.json")

    res = vtp.verify_typst_evaluation_policy(REPO_ROOT, manifest)
    _check_eq(res["content_policy_violations"], 0, "Gate A2 content_policy_violations")
    _check_eq(res["trusted_template_files_pinned"], 6, "Gate A2 trusted_template_files_pinned")
    _check_eq(res["diagram_components_pinned"], 4, "Gate A2 diagram_components_pinned")
    _check_eq(res["vector_figure_components_pinned"], 62, "Gate A2 vector_figure_components_pinned")
    _check_eq(res["manifest_typst_digests_enforced"], 48, "Gate A2 manifest_typst_digests_enforced")
    _check_eq(res["content_files_policy_checked"], 110, "Gate A2 content_files_policy_checked")
    _check(
        isinstance(res["content_events_checked"], int) and res["content_events_checked"] > 0,
        f"Gate A2 content_events_checked must be positive int, got {res['content_events_checked']!r}",
    )

    # Explicitly confirm cell_staircase_fold_boundary.typ (fixed in BND-P5-02) has zero Gate A2 violations
    inv_map = vtp._load_figure_inventory_map(REPO_ROOT)
    cell_rel = "typst/lib/figures/manual/cell_staircase_fold_boundary.typ"
    _check(cell_rel in inv_map, f"{cell_rel} missing from figure inventory map")
    cell_violations = vtp._vector_figure_policy_violations(
        cell_rel,
        REPO_ROOT.joinpath(cell_rel).read_text(encoding="utf-8"),
        inv_map[cell_rel],
    )
    _check_eq(cell_violations, [], f"Gate A2 violations in {cell_rel}")

    # Adversarial negative controls (strictly in-memory, zero disk mutations):
    sample_fig_rel = "typst/lib/figures/main/closure_ladder.typ"
    sample_fig_text = REPO_ROOT.joinpath(sample_fig_rel).read_text(encoding="utf-8")
    sample_inv = inv_map[sample_fig_rel]

    # (NC-1) Injecting #image(...) into a vector figure MUST fail Gate A2
    bad_image_v = vtp._vector_figure_policy_violations(
        sample_fig_rel,
        sample_fig_text + '\n#image("/figures_jpg/null_four_edge_x_witness.png")\n',
        sample_inv,
    )
    _check(len(bad_image_v) > 0, "Gate A2 negative control failed: injected #image() in vector figure was not rejected")

    # (NC-2) Injecting undeclared csv(...) into a conceptual vector figure MUST fail Gate A2
    bad_csv_v = vtp._vector_figure_policy_violations(
        sample_fig_rel,
        sample_fig_text + '\n#let _x = csv("/manual/data/boundary_sadar/sparc_pooled_primary_exact.csv")\n',
        sample_inv,
    )
    _check(len(bad_csv_v) > 0, "Gate A2 negative control failed: undeclared csv() in vector figure was not rejected")

    # (NC-3) Injecting raw csv(...) or out-of-scope #aod-csv-table path into a content file MUST fail Gate A2
    allowed_includes = (
        {e["typst_target"] for e in manifest["active_source_map"]}
        | set(manifest["diagram_components"])
        | set(manifest["vector_figure_components"])
    )
    bad_content_raw_csv, _ = vtp._content_policy_violations(
        "typst/manual/sections/00_awareness_fixtures.typ",
        '#let rows = csv("/manual/data/boundary_sadar/awareness_operativity_dec_walk.csv")\n',
        allowed_includes,
    )
    _check(
        len(bad_content_raw_csv) > 0,
        "Gate A2 negative control failed: raw csv() in content unit was not rejected",
    )
    bad_content_escape, _ = vtp._content_policy_violations(
        "typst/manual/sections/00_awareness_fixtures.typ",
        '#aod-csv-table("/manual/data/../../etc/passwd", columns: (1fr,), align: (left,), headers: ([A],), cells: ("a",))\n',
        allowed_includes,
    )
    _check(
        len(bad_content_escape) > 0,
        "Gate A2 negative control failed: path-traversal #aod-csv-table() was not rejected",
    )


def test_all_12_manual_live_csv_tables_bound_via_aod_csv_table() -> None:
    """Verify all 12 live CSV tables in Manual use #aod-csv-table and point to valid committed boundary_sadar CSVs."""
    # Confirm trusted macros exist in typst/lib/aod_schema.typ
    schema_text = REPO_ROOT.joinpath("typst", "lib", "aod_schema.typ").read_text(encoding="utf-8")
    _check("#let aod-csv-table(" in schema_text, "aod_schema.typ missing #let aod-csv-table(")
    _check("#let aod-raw-wrap(" in schema_text, "aod_schema.typ missing #let aod-raw-wrap(")
    _check("_aod-csv-path-re" in schema_text, "aod_schema.typ missing _aod-csv-path-re path guard")

    manual_files = sorted(REPO_ROOT.joinpath("typst", "manual", "sections").glob("*.typ")) + sorted(
        REPO_ROOT.joinpath("typst", "manual", "appendices").glob("*.typ")
    )
    _check_eq(len(manual_files), 18, "Manual content .typ file count")

    csv_table_pat = re.compile(r'#aod-csv-table\(\s*"([^"]+)"')
    raw_csv_pat = re.compile(r"(?<![A-Za-z0-9_-])csv\(")

    discovered: dict[str, list[str]] = {}
    total_bindings = 0
    for typ_path in manual_files:
        text = typ_path.read_text(encoding="utf-8")
        # Zero raw csv() calls allowed in Manual content units post-P5-03 migration
        _check(
            raw_csv_pat.search(text) is None,
            f"{typ_path.name}: raw csv() call remains in Manual content unit (must use #aod-csv-table)",
        )
        uris = csv_table_pat.findall(text)
        if uris:
            discovered[typ_path.name] = uris
            total_bindings += len(uris)

    _check_eq(total_bindings, 12, "total #aod-csv-table bindings across Manual")
    _check_eq(
        set(discovered.keys()),
        set(EXPECTED_12_MANUAL_CSV_TABLES.keys()),
        "set of Manual files with #aod-csv-table bindings",
    )

    for typ_name, expected_uri in sorted(EXPECTED_12_MANUAL_CSV_TABLES.items()):
        _check_eq(discovered[typ_name], [expected_uri], f"{typ_name} #aod-csv-table URI")
        _check(
            expected_uri.startswith("/manual/data/boundary_sadar/") and expected_uri.endswith(".csv"),
            f"{typ_name}: unexpected CSV table URI {expected_uri!r}",
        )
        csv_disk = REPO_ROOT.joinpath(expected_uri.lstrip("/"))
        _check(csv_disk.is_file() and not csv_disk.is_symlink(), f"missing or symlinked CSV: {expected_uri}")
        with csv_disk.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            _check(
                reader.fieldnames is not None and len(reader.fieldnames) >= 2,
                f"{expected_uri}: invalid CSV header {reader.fieldnames!r}",
            )
            rows = list(reader)
        _check(len(rows) > 0, f"{expected_uri}: CSV has 0 rows")
        for idx, row in enumerate(rows):
            _check(None not in row, f"{expected_uri} row {idx}: unkeyed overflow columns")
            for col, val in row.items():
                _check(
                    isinstance(val, str) and len(val.strip()) > 0,
                    f"{expected_uri} row {idx} col {col!r}: empty cell value",
                )

    # Confirm zero leaked Typst table/figure macro names in any generated latex/**/*.tex file
    for tex_file in sorted(REPO_ROOT.joinpath("latex").rglob("*.tex")):
        tex_text = tex_file.read_text(encoding="utf-8")
        for leaked in ("aod-csv-table", "aod-raw-wrap", "aod-figure-header", "aod-panel"):
            _check(
                leaked not in tex_text,
                f"{tex_file.relative_to(REPO_ROOT).as_posix()}: leaked Typst macro {leaked!r} in generated LaTeX",
            )


# =============================================================================
# 4. 66-Figure Exported PDF, figure_inventory, manifest, & main_registry Seal
# =============================================================================


def test_figure_inventory_62_vector_figures_byte_exact_seal() -> None:
    """Verify typst/figure_inventory.json summary and every SHA-256 against disk and typst/manifest.json."""
    inv = _load_json("typst/figure_inventory.json")
    manifest = _load_json("typst/manifest.json")

    _check_eq(inv.get("schema"), "aod.m4.s1b.figure-inventory.v1", "figure_inventory.json schema")
    _check_eq(
        manifest.get("figure_inventory_sha256"),
        _sha256_file(REPO_ROOT.joinpath("typst", "figure_inventory.json")),
        "manifest figure_inventory_sha256 vs disk",
    )
    _check_eq(
        manifest.get("plots_library_sha256"),
        _sha256_file(REPO_ROOT.joinpath("typst", "lib", "aod_plots.typ")),
        "manifest plots_library_sha256 vs disk",
    )

    summary = inv["summary"]
    _check_eq(summary["converted_vector"], 34, "figure_inventory summary.converted_vector")
    _check_eq(summary["authored_native_vector"], 28, "figure_inventory summary.authored_native_vector")
    _check_eq(summary["total_vector_figures"], 62, "figure_inventory summary.total_vector_figures")
    _check_eq(summary["total_active_rasters"], 34, "figure_inventory summary.total_active_rasters")
    _check_eq(summary["main_rasters"], 6, "figure_inventory summary.main_rasters")
    _check_eq(summary["manual_rasters"], 28, "figure_inventory summary.manual_rasters")
    _check_eq(summary["DATA_BACKED_VERIFIED"], 39, "figure_inventory summary.DATA_BACKED_VERIFIED")
    _check_eq(summary["CONCEPTUAL_SCHEMATIC"], 23, "figure_inventory summary.CONCEPTUAL_SCHEMATIC")
    _check_eq(summary["UNRESOLVED_RETAINED"], 0, "figure_inventory summary.UNRESOLVED_RETAINED")
    _check_eq(summary["retained_raster"], 0, "figure_inventory summary.retained_raster")

    figures = inv["figures"]
    _check(isinstance(figures, list), "figure_inventory.figures must be a list")
    _check_eq(len(figures), 62, "figure_inventory.figures length")

    main_count = 0
    manual_count = 0
    converted_count = 0
    authored_count = 0
    data_backed_count = 0
    conceptual_count = 0

    seen_slugs: set[str] = set()
    seen_labels: set[str] = set()
    seen_components: set[str] = set()
    seen_pdfs: set[str] = set()
    manifest_vec_comps: dict[str, str] = manifest["vector_figure_components"]

    for entry in figures:
        slug = entry["slug"]
        surface = entry["surface"]
        label = entry["label"]
        comp_rel = entry["target_typst_component"]
        pdf_rel = entry["target_exported_pdf"]
        conv_status = entry["conversion_status"]
        prov_class = entry["provenance_class"]

        _check(slug not in seen_slugs, f"duplicate slug in figure_inventory: {slug}")
        _check(label not in seen_labels, f"duplicate label in figure_inventory: {label}")
        _check(comp_rel not in seen_components, f"duplicate component in figure_inventory: {comp_rel}")
        _check(pdf_rel not in seen_pdfs, f"duplicate exported PDF in figure_inventory: {pdf_rel}")
        seen_slugs.add(slug)
        seen_labels.add(label)
        seen_components.add(comp_rel)
        seen_pdfs.add(pdf_rel)

        if surface == "main":
            main_count += 1
        elif surface == "manual":
            manual_count += 1
        else:
            _check(False, f"{slug}: unexpected surface {surface!r}")

        if conv_status == "CONVERTED_VECTOR":
            converted_count += 1
        elif conv_status == "AUTHORED_NATIVE_VECTOR":
            authored_count += 1
        else:
            _check(False, f"{slug}: unexpected conversion_status {conv_status!r}")

        if prov_class == "DATA_BACKED_VERIFIED":
            data_backed_count += 1
        elif prov_class == "CONCEPTUAL_SCHEMATIC":
            conceptual_count += 1
        else:
            _check(False, f"{slug}: unexpected provenance_class {prov_class!r}")

        _check_eq(
            entry["data_check_verified"],
            prov_class == "DATA_BACKED_VERIFIED",
            f"{slug}: data_check_verified vs provenance_class",
        )
        _check_eq(entry["visual_comparison_recorded"], True, f"{slug}: visual_comparison_recorded")
        _check_eq(entry["raster_image_xobjects"], 0, f"{slug}: raster_image_xobjects")

        # Typst component file SHA-256 vs inventory AND vs typst/manifest.json
        comp_path = REPO_ROOT.joinpath(comp_rel)
        _check(comp_path.is_file(), f"{slug}: missing target_typst_component {comp_rel}")
        actual_comp_sha = _sha256_file(comp_path)
        _check_eq(actual_comp_sha, entry["typst_component_sha256"], f"{slug}: typst_component_sha256")
        _check(comp_rel in manifest_vec_comps, f"{slug}: component missing from typst/manifest.json")
        _check_eq(manifest_vec_comps[comp_rel], actual_comp_sha, f"{slug}: manifest vector_figure_components sha256")

        # Exported PDF SHA-256 and byte count vs disk
        pdf_path = REPO_ROOT.joinpath(pdf_rel)
        _check(pdf_path.is_file(), f"{slug}: missing target_exported_pdf {pdf_rel}")
        _check_eq(pdf_path.stat().st_size, entry["exported_pdf_bytes"], f"{slug}: exported_pdf_bytes")
        _check_eq(_sha256_file(pdf_path), entry["exported_pdf_sha256"], f"{slug}: exported_pdf_sha256")

        # Every data_sources[*].sha256 matches disk byte-for-byte
        data_sources = entry["data_sources"]
        _check(isinstance(data_sources, list), f"{slug}: data_sources must be a list")
        if prov_class == "DATA_BACKED_VERIFIED":
            _check(len(data_sources) > 0, f"{slug}: DATA_BACKED_VERIFIED figure has empty data_sources")
        for ds in data_sources:
            ds_path = REPO_ROOT.joinpath(ds["path"])
            _check(ds_path.is_file(), f"{slug}: missing data_source {ds['path']}")
            _check_eq(_sha256_file(ds_path), ds["sha256"], f"{slug}: data_source sha256 ({ds['path']})")

        # All 34 historical rasters preserved byte-for-byte; 28 authored have null raster fields
        if conv_status == "CONVERTED_VECTOR":
            raster_rel = entry["raster_path"]
            _check(isinstance(raster_rel, str) and len(raster_rel) > 0, f"{slug}: missing raster_path")
            raster_path = REPO_ROOT.joinpath(raster_rel)
            _check(raster_path.is_file(), f"{slug}: missing retained historical raster {raster_rel}")
            _check_eq(raster_path.stat().st_size, entry["raster_bytes"], f"{slug}: raster_bytes")
            _check_eq(_sha256_file(raster_path), entry["raster_sha256"], f"{slug}: raster_sha256")
        else:
            _check(entry["raster_path"] is None, f"{slug}: authored figure must have raster_path=None")
            _check(entry["raster_sha256"] is None, f"{slug}: authored figure must have raster_sha256=None")

        # Generator script digest when recorded
        if entry.get("generator_script") is not None:
            gs_path = REPO_ROOT.joinpath(entry["generator_script"])
            _check(gs_path.is_file(), f"{slug}: missing generator_script {entry['generator_script']}")
            _check_eq(
                _sha256_file(gs_path),
                entry["generator_script_sha256"],
                f"{slug}: generator_script_sha256",
            )

    _check_eq(main_count, 13, "figure_inventory Main surface count")
    _check_eq(manual_count, 49, "figure_inventory Manual surface count")
    _check_eq(converted_count, 34, "figure_inventory CONVERTED_VECTOR count")
    _check_eq(authored_count, 28, "figure_inventory AUTHORED_NATIVE_VECTOR count")
    _check_eq(data_backed_count, 39, "figure_inventory DATA_BACKED_VERIFIED count")
    _check_eq(conceptual_count, 23, "figure_inventory CONCEPTUAL_SCHEMATIC count")
    _check_eq(seen_components, set(manifest_vec_comps.keys()), "figure_inventory vs manifest component set")


def test_66_exported_pdfs_pure_vector_and_generation_manifest_seal() -> None:
    """Verify all 66 exported PDFs (13 Main + 53 Manual) are pure-vector 1-page PDFs matching manifests."""
    main_mf_rel = "latex/figures/generated/FIGURE_MANIFEST.json"
    manual_mf_rel = "latex/manual/figures/generated/FIGURE_MANIFEST.json"
    main_mf = _load_json(main_mf_rel)
    manual_mf = _load_json(manual_mf_rel)
    gen_mf = _load_json("latex/GENERATION_MANIFEST.json")

    schema_sha = _sha256_file(REPO_ROOT.joinpath("typst", "lib", "aod_schema.typ"))
    plots_sha = _sha256_file(REPO_ROOT.joinpath("typst", "lib", "aod_plots.typ"))

    _check_eq(main_mf["figure_count"], 13, "Main FIGURE_MANIFEST figure_count")
    _check_eq(len(main_mf["figures"]), 13, "Main FIGURE_MANIFEST figures len")
    _check_eq(manual_mf["figure_count"], 53, "Manual FIGURE_MANIFEST figure_count")
    _check_eq(len(manual_mf["figures"]), 53, "Manual FIGURE_MANIFEST figures len")
    _check_eq(main_mf["figure_count"] + manual_mf["figure_count"], 66, "total exported PDF count")

    # Map relative path (under latex/) -> (sha256, bytes, component_kind)
    manifest_pdfs: dict[str, tuple[str, int, str]] = {}
    flowchart_count = 0
    vector_fig_count = 0

    for surface_name, mf, gen_dir_rel, latex_sub_rel in (
        ("main", main_mf, "latex/figures/generated", "figures/generated"),
        ("manual", manual_mf, "latex/manual/figures/generated", "manual/figures/generated"),
    ):
        _check_eq(mf["schema"], "aod.typst.figure-export.v1", f"{surface_name} FIGURE_MANIFEST schema")
        _check_eq(mf["surface"], surface_name, f"{surface_name} FIGURE_MANIFEST surface")
        _check_eq(mf["format"], "pdf", f"{surface_name} FIGURE_MANIFEST format")
        _check_eq(mf["schema_sha256"], schema_sha, f"{surface_name} FIGURE_MANIFEST schema_sha256")
        _check_eq(mf["plots_lib_sha256"], plots_sha, f"{surface_name} FIGURE_MANIFEST plots_lib_sha256")

        gen_dir = REPO_ROOT.joinpath(gen_dir_rel)
        disk_pdfs = {p.name for p in gen_dir.glob("*.pdf") if p.is_file()}
        declared_names: set[str] = set()

        for entry in mf["figures"]:
            out_name = entry["output_filename"]
            declared_names.add(out_name)
            pdf_path = gen_dir.joinpath(out_name)
            _check(pdf_path.is_file(), f"missing exported PDF: {gen_dir_rel}/{out_name}")

            actual_sha = _sha256_file(pdf_path)
            actual_bytes = pdf_path.stat().st_size
            _check_eq(actual_sha, entry["output_sha256"], f"{out_name}: output_sha256")
            _check_eq(actual_bytes, entry["output_bytes"], f"{out_name}: output_bytes")

            # Manifest invariants
            _check_eq(entry["page_count"], 1, f"{out_name}: manifest page_count")
            _check_eq(entry["raster_image_xobjects"], 0, f"{out_name}: manifest raster_image_xobjects")
            _check_eq(entry["inline_raster_images"], 0, f"{out_name}: manifest inline_raster_images")
            _check_eq(entry["total_raster_images"], 0, f"{out_name}: manifest total_raster_images")
            _check_eq(entry["has_extractable_text"], True, f"{out_name}: manifest has_extractable_text")

            # Source component & data input digests
            comp_path = REPO_ROOT.joinpath(entry["diagram_component"])
            _check(comp_path.is_file(), f"{out_name}: missing source component {entry['diagram_component']}")
            _check_eq(_sha256_file(comp_path), entry["diagram_sha256"], f"{out_name}: diagram_sha256")
            for di in entry["data_inputs"]:
                di_path = REPO_ROOT.joinpath(di["path"])
                _check(di_path.is_file(), f"{out_name}: missing data_input {di['path']}")
                _check_eq(_sha256_file(di_path), di["sha256"], f"{out_name}: data_input sha256 ({di['path']})")

            # Live independent PDF verification: 1 page, 0 raster XObjects, 0 inline rasters, BT text present
            live_info = _inspect_pure_vector_pdf(pdf_path)
            _check_eq(live_info["page_count"], 1, f"{out_name}: live PDF page count")
            _check_eq(live_info["raster_image_xobjects"], 0, f"{out_name}: live raster_image_xobjects")
            _check_eq(live_info["inline_raster_images"], 0, f"{out_name}: live inline_raster_images")
            _check_eq(live_info["total_raster_images"], 0, f"{out_name}: live total_raster_images")
            _check_eq(live_info["has_bt_text"], True, f"{out_name}: live PDF text block operator (BT)")

            kind = entry["component_kind"]
            if kind == "flowchart_diagram":
                flowchart_count += 1
            elif kind == "vector_figure":
                vector_fig_count += 1
            else:
                _check(False, f"{out_name}: unexpected component_kind {kind!r}")

            manifest_pdfs[f"{latex_sub_rel}/{out_name}"] = (actual_sha, actual_bytes, kind)

        _check_eq(disk_pdfs, declared_names, f"{gen_dir_rel} disk PDF set vs FIGURE_MANIFEST.json")

    _check_eq(flowchart_count, 4, "total exported flowchart_diagram count")
    _check_eq(vector_fig_count, 62, "total exported vector_figure count")
    _check_eq(len(manifest_pdfs), 66, "total verified exported PDFs")

    # Cross-check latex/GENERATION_MANIFEST.json against all 66 exported PDFs and manifest files
    _check_eq(gen_mf["schema"], "aod.typ2tex.manifest.v1", "GENERATION_MANIFEST schema")
    _check_eq(
        gen_mf["generator_sha256"],
        _sha256_file(REPO_ROOT.joinpath("scripts", "typ2tex.py")),
        "GENERATION_MANIFEST generator_sha256",
    )
    _check_eq(
        gen_mf["figure_exporter_sha256"],
        _sha256_file(REPO_ROOT.joinpath("scripts", "export_typst_figures.py")),
        "GENERATION_MANIFEST figure_exporter_sha256",
    )
    by_kind = gen_mf["counts"]["by_kind"]
    _check_eq(by_kind["exported_diagram"], 4, "GENERATION_MANIFEST exported_diagram count")
    _check_eq(by_kind["exported_vector_figure"], 62, "GENERATION_MANIFEST exported_vector_figure count")
    _check_eq(by_kind["figure_manifest"], 2, "GENERATION_MANIFEST figure_manifest count")

    gen_pdf_map: dict[str, tuple[str, int, str]] = {}
    gen_mf_digests: dict[str, str] = {}
    for out_entry in gen_mf["outputs"]:
        kind = out_entry["kind"]
        rel_p = out_entry["path"]
        if kind in ("exported_diagram", "exported_vector_figure"):
            expected_comp_kind = "flowchart_diagram" if kind == "exported_diagram" else "vector_figure"
            gen_pdf_map[rel_p] = (out_entry["sha256"], out_entry["bytes"], expected_comp_kind)
        elif kind == "figure_manifest":
            gen_mf_digests[rel_p] = out_entry["sha256"]

    _check_eq(gen_pdf_map, manifest_pdfs, "GENERATION_MANIFEST 66 PDFs vs FIGURE_MANIFESTs")
    _check_eq(
        gen_mf_digests,
        {
            "figures/generated/FIGURE_MANIFEST.json": _sha256_file(REPO_ROOT.joinpath(main_mf_rel)),
            "manual/figures/generated/FIGURE_MANIFEST.json": _sha256_file(REPO_ROOT.joinpath(manual_mf_rel)),
        },
        "GENERATION_MANIFEST figure_manifest SHA-256s vs disk",
    )


def test_main_registry_json_seal() -> None:
    """Verify typst/lib/main_registry.json has 455 entries, main.pdf filename, and live Main digest match."""
    bt = _load_script_module("qa_p5_build_typst", "scripts/build_typst.py")
    reg = _load_json("typst/lib/main_registry.json")

    _check_eq(reg.get("schema"), "aod.typst.main-registry.v1", "main_registry schema")
    _check_eq(reg.get("entry_count"), 455, "main_registry entry_count")
    _check_eq(reg.get("main_pdf_filename"), "main.pdf", "main_registry main_pdf_filename")

    entries = reg.get("entries")
    _check(isinstance(entries, dict), "main_registry.entries must be a dict")
    _check_eq(len(entries), 455, "main_registry len(entries)")

    live_digest, live_inputs = bt.compute_main_sources_digest(REPO_ROOT)
    _check_eq(reg.get("main_sources_sha256"), live_digest, "main_registry main_sources_sha256 vs live")
    _check_eq(reg.get("main_input_count"), len(live_inputs), "main_registry main_input_count vs live")

    # Confirm all 7 newly authored Main figure labels are registered in main_registry.json
    for _, fig_rel, _, label, _, _ in NINE_NEW_GEOMETRIC_FIGURES:
        if "/main/" in fig_rel:
            _check(label in entries, f"Main figure label {label!r} missing from main_registry.json")
            entry = entries[label]
            _check_eq(entry["kind"], "figure", f"main_registry[{label!r}].kind")
            _check(
                isinstance(entry["page"], int) and entry["page"] >= 1,
                f"main_registry[{label!r}].page must be positive int, got {entry['page']!r}",
            )


# =============================================================================
# 5. Historical 98ddfa0 Baseline (211/211), M4.5 G6 Ledger, & Release Bundler
# =============================================================================


def test_historical_98ddfa0_baseline_211_and_g6_cells_geometry_split() -> None:
    """Verify 211/211 historical baseline archive and archived vs live G6 cells_geometry.json split."""
    mat = _load_script_module("qa_p5_materialize_latex_baseline", "scripts/materialize_latex_baseline.py")
    baseline = mat.load_and_verify_baseline(REPO_ROOT)

    entries = baseline["entries"]
    _check_eq(len(entries), 211, "BASELINE_MANIFEST total entries")

    archived_tex = [e for e in entries if e["role"] == "archived_editorial_tex"]
    archived_data = [e for e in entries if e["role"] == "archived_baseline_data"]
    preserved_in_place = [
        e for e in entries if e["role"] not in ("archived_editorial_tex", "archived_baseline_data")
    ]
    _check_eq(len(archived_tex), 41, "archived_editorial_tex count")
    _check_eq(len(archived_data), 1, "archived_baseline_data count")
    _check_eq(len(preserved_in_place), 169, "preserved_in_place count")
    _check_eq(len(archived_tex) + len(archived_data) + len(preserved_in_place), 211, "baseline partition sum")

    counts = baseline["counts"]
    _check_eq(counts["total_baseline_protected"], 211, "counts.total_baseline_protected")
    _check_eq(counts["archived_editorial_tex"], 41, "counts.archived_editorial_tex")
    _check_eq(counts["archived_baseline_data"], 1, "counts.archived_baseline_data")
    _check_eq(counts["preserved_in_place"], 169, "counts.preserved_in_place")

    # Verify exact archived 98ddfa0 cells_geometry.json record and disk bytes
    cg_entry = archived_data[0]
    _check_eq(cg_entry["original_path"], ARCHIVED_CELLS_GEOMETRY_ORIG, "archived_baseline_data original_path")
    _check_eq(
        cg_entry["retained_location"],
        ARCHIVED_CELLS_GEOMETRY_RETAINED,
        "archived_baseline_data retained_location",
    )
    _check_eq(cg_entry["sha256"], ARCHIVED_CELLS_GEOMETRY_SHA256, "archived_baseline_data sha256")
    _check_eq(cg_entry["bytes"], ARCHIVED_CELLS_GEOMETRY_BYTES, "archived_baseline_data bytes")

    arch_cg_path = REPO_ROOT.joinpath(ARCHIVED_CELLS_GEOMETRY_RETAINED)
    _check(arch_cg_path.is_file(), f"missing archived baseline file: {ARCHIVED_CELLS_GEOMETRY_RETAINED}")
    _check_eq(arch_cg_path.stat().st_size, ARCHIVED_CELLS_GEOMETRY_BYTES, "archived cells_geometry.json disk bytes")
    _check_eq(_sha256_file(arch_cg_path), ARCHIVED_CELLS_GEOMETRY_SHA256, "archived cells_geometry.json disk sha256")
    arch_cg_json = json.loads(arch_cg_path.read_text(encoding="utf-8"))
    _check_eq(arch_cg_json["G6"]["status"], "not_opened", "archived 98ddfa0 cells_geometry G6.status")

    # Verify live cells_geometry.json retains G6 4D tesseract extension (78,163 bytes)
    live_cg_path = REPO_ROOT.joinpath(ARCHIVED_CELLS_GEOMETRY_ORIG)
    _check(live_cg_path.is_file(), f"missing live cells_geometry.json: {ARCHIVED_CELLS_GEOMETRY_ORIG}")
    _check_eq(live_cg_path.stat().st_size, LIVE_CELLS_GEOMETRY_BYTES, "live cells_geometry.json disk bytes")
    _check(
        _sha256_file(live_cg_path) != ARCHIVED_CELLS_GEOMETRY_SHA256,
        "live cells_geometry.json SHA-256 must differ from historical 98ddfa0 baseline",
    )
    live_cg_json = json.loads(live_cg_path.read_text(encoding="utf-8"))
    _check_eq(
        live_cg_json["G6"]["status"],
        "opened_declared_verification_model",
        "live cells_geometry G6.status",
    )
    for g6_key in ("levels", "refinement", "shared_q_controls", "reference_comparisons", "object"):
        _check(g6_key in live_cg_json["G6"], f"live cells_geometry G6 missing key {g6_key!r}")


def test_honest_m4_5_g6_representation_ledger_and_baseline_immutability() -> None:
    """Verify representation_change_ledger.json honestly records M4.5 G6 and verify_baseline_immutability passes."""
    vtp = _load_script_module("qa_p5_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = _load_json("typst/manifest.json")
    ledger = _load_json("typst/representation_change_ledger.json")

    summary = ledger["summary"]
    _check_eq(summary["contracts_amended"], 8, "ledger summary.contracts_amended")
    _check_eq(summary["contracts_untouched"], 9, "ledger summary.contracts_untouched")

    amendments = ledger["contract_amendments"]
    _check(isinstance(amendments, list), "ledger contract_amendments must be a list")
    _check_eq(len(amendments), 8, "len(ledger.contract_amendments)")

    cell_spec_rel = "contracts/scientific/CELL_MEASURE_SPEC.json"
    by_contract = {rec["contract"]: rec for rec in amendments}
    _check_eq(len(by_contract), 8, "unique contracts in ledger.contract_amendments")
    _check(cell_spec_rel in by_contract, f"{cell_spec_rel} missing from ledger.contract_amendments")

    for c_rel, rec in sorted(by_contract.items()):
        disk_sha = _sha256_file(REPO_ROOT.joinpath(c_rel))
        _check_eq(rec["new_sha256"], disk_sha, f"ledger new_sha256 vs disk for {c_rel}")
        _check(rec["old_sha256"] != rec["new_sha256"], f"no-op amendment in ledger for {c_rel}")
        if c_rel == cell_spec_rel:
            _check_eq(
                rec["scientific_substance_changed"],
                True,
                f"{cell_spec_rel}: scientific_substance_changed must be True",
            )
            _check_eq(
                rec["scope"],
                "m4_5_g6_tesseract_extension",
                f"{cell_spec_rel}: scope must be 'm4_5_g6_tesseract_extension'",
            )
        else:
            _check_eq(
                rec["scientific_substance_changed"],
                False,
                f"{c_rel}: scientific_substance_changed must be False",
            )

    # Run verify_baseline_immutability directly
    base_res = vtp.verify_baseline_immutability(REPO_ROOT, manifest)
    _check_eq(base_res["protected_baseline_files"], 211, "verify_baseline_immutability protected_baseline_files")
    _check_eq(base_res["archived_editorial_tex_files"], 41, "verify_baseline_immutability archived_editorial_tex_files")
    _check_eq(base_res["archived_baseline_data_files"], 1, "verify_baseline_immutability archived_baseline_data_files")
    _check_eq(base_res["preserved_in_place_files"], 169, "verify_baseline_immutability preserved_in_place_files")
    _check_eq(
        base_res["historical_baseline_preservation_verified"],
        True,
        "verify_baseline_immutability historical_baseline_preservation_verified",
    )
    _check_eq(
        base_res["phase1_transition_verified"],
        True,
        "verify_baseline_immutability phase1_transition_verified",
    )
    _check_eq(
        base_res["representation_change_ledger_verified"],
        True,
        "verify_baseline_immutability representation_change_ledger_verified",
    )
    _check_eq(base_res["amended_contracts_count"], 8, "verify_baseline_immutability amended_contracts_count")


def test_release_bundler_uow_exclusion_and_source_tree_completeness(tmp_path: Path) -> None:
    """Verify scripts/build_release_bundle.py excludes .uow/ and includes archived baseline + all 66 PDFs."""
    brb = _load_script_module("qa_p5_build_release_bundle", "scripts/build_release_bundle.py")

    _check(".uow" in brb.EXCLUDE_DIR_NAMES, "'.uow' missing from build_release_bundle.EXCLUDE_DIR_NAMES")
    _check(
        brb.excluded(Path(".uow/milestones/M4_5-uow-overhaul/phases/P5-geometric-figures-and-seal/phase.toml"))
        is True,
        "build_release_bundle.excluded() must reject .uow/ paths",
    )
    _check(
        brb.excluded(Path("sub/.uow/worktree_state.json")) is True,
        "build_release_bundle.excluded() must reject nested .uow/ paths",
    )
    _check(
        brb.excluded(Path("main.pdf")) is True,
        "build_release_bundle.excluded() must still reject arbitrary build PDFs like main.pdf",
    )

    declared_figs = brb.declared_generated_figure_assets(REPO_ROOT)
    _check_eq(len(declared_figs), 66, "declared_generated_figure_assets() count")
    for rel_pdf in sorted(declared_figs):
        _check(
            brb.excluded(Path(rel_pdf)) is False,
            f"declared generated figure PDF wrongly excluded by bundler: {rel_pdf}",
        )

    source_root = brb.build_source_tree(tmp_path)
    _check(source_root.is_dir(), "build_source_tree did not return an existing directory")

    all_paths = list(source_root.rglob("*"))
    _check(len(all_paths) > 0, "build_source_tree produced an empty tree")

    uow_hits = [
        p.relative_to(source_root).as_posix()
        for p in all_paths
        if ".uow" in p.relative_to(source_root).parts
    ]
    _check_eq(uow_hits, [], "ZERO .uow entries allowed in release source_root")

    # Archived 98ddfa0 cells_geometry.json must be staged byte-for-byte
    staged_arch_cg = source_root.joinpath(ARCHIVED_CELLS_GEOMETRY_RETAINED)
    _check(staged_arch_cg.is_file(), f"release source_root missing {ARCHIVED_CELLS_GEOMETRY_RETAINED}")
    _check_eq(staged_arch_cg.stat().st_size, ARCHIVED_CELLS_GEOMETRY_BYTES, "staged archived cells_geometry bytes")
    _check_eq(_sha256_file(staged_arch_cg), ARCHIVED_CELLS_GEOMETRY_SHA256, "staged archived cells_geometry sha256")

    # Live G6 cells_geometry.json must also be staged byte-for-byte
    staged_live_cg = source_root.joinpath(ARCHIVED_CELLS_GEOMETRY_ORIG)
    _check(staged_live_cg.is_file(), f"release source_root missing live {ARCHIVED_CELLS_GEOMETRY_ORIG}")
    _check_eq(staged_live_cg.stat().st_size, LIVE_CELLS_GEOMETRY_BYTES, "staged live cells_geometry bytes")

    # All 66 generated figure PDFs must be staged with exact disk SHA-256 parity
    for rel_pdf in sorted(declared_figs):
        staged_pdf = source_root.joinpath(rel_pdf)
        _check(staged_pdf.is_file(), f"release source_root missing generated figure PDF: {rel_pdf}")
        _check_eq(
            _sha256_file(staged_pdf),
            _sha256_file(REPO_ROOT.joinpath(rel_pdf)),
            f"staged PDF SHA-256 parity for {rel_pdf}",
        )

    # Exact PDF set in source_root: 66 generated figure PDFs + 2 primary SOURCE_DOCUMENTS = 68 (no stray PDFs)
    staged_pdfs = {
        p.relative_to(source_root).as_posix()
        for p in source_root.rglob("*.pdf")
        if p.is_file()
    }
    expected_staged_pdfs = declared_figs | set(brb.SOURCE_DOCUMENTS)
    _check_eq(len(expected_staged_pdfs), 68, "expected total staged PDFs (66 generated + 2 primary sources)")
    _check_eq(staged_pdfs, expected_staged_pdfs, "staged PDF set vs declared generated + SOURCE_DOCUMENTS")


# =============================================================================
# 6. End-to-End Cross-Phase M4.5 Integrity & Self-AST Audit
# =============================================================================


def test_production_scripts_zero_bare_asserts_ast_audit() -> None:
    """Verify zero bare `assert` statements via Python AST walk across core M4.5 seal scripts."""
    for rel in ZERO_ASSERT_AUDITED_SCRIPTS:
        script_path = REPO_ROOT.joinpath(rel)
        _check(script_path.is_file(), f"missing audited script: {rel}")
        tree = ast.parse(script_path.read_text(encoding="utf-8"), filename=rel)
        assert_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        _check(
            not assert_lines,
            f"{rel} contains forbidden bare `assert` statements at lines: {assert_lines}",
        )


def test_typ2tex_check_and_audit_scientific_sources_e2e() -> None:
    """Verify live read-only subprocess execution of typ2tex.py --check and audit_scientific_sources.py."""
    env = _tool_env()
    py_flags = ["-B", "-O"] if sys.flags.optimize else ["-B"]

    # Both commands are strictly read-only against the repo tree (typ2tex --check stages into mkdtemp)
    proc_typ2tex = subprocess.Popen(
        [sys.executable, *py_flags, "scripts/typ2tex.py", "--root", ".", "--outdir", "latex", "--check"],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    proc_audit = subprocess.Popen(
        [sys.executable, *py_flags, "scripts/audit_scientific_sources.py", "."],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    t2t_out, t2t_err = proc_typ2tex.communicate()
    aud_out, aud_err = proc_audit.communicate()

    _check(
        proc_typ2tex.returncode == 0,
        f"typ2tex.py --check failed (rc={proc_typ2tex.returncode}):\nSTDOUT:\n{t2t_out}\nSTDERR:\n{t2t_err}",
    )
    t2t_report = json.loads(t2t_out)
    _check_eq(t2t_report.get("status"), "PASS", "typ2tex.py --check status")
    _check_eq(t2t_report.get("mode"), "check", "typ2tex.py --check mode")
    _check_eq(t2t_report.get("removed_outputs"), [], "typ2tex.py --check removed_outputs")
    _check_eq(t2t_report["counts"]["by_kind"]["exported_diagram"], 4, "typ2tex.py --check exported_diagram")
    _check_eq(t2t_report["counts"]["by_kind"]["exported_vector_figure"], 62, "typ2tex.py --check exported_vector_figure")

    _check(
        proc_audit.returncode == 0,
        f"audit_scientific_sources.py failed (rc={proc_audit.returncode}):\nSTDOUT:\n{aud_out}\nSTDERR:\n{aud_err}",
    )


def test_self_ast_zero_bare_asserts_and_zero_floats() -> None:
    """Verify zero bare `assert` statements and zero float literals/references in this QA file."""
    self_path = Path(__file__).resolve()
    tree = ast.parse(self_path.read_text(encoding="utf-8"), filename=str(self_path))

    assert_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    _check(
        not assert_lines,
        f"{self_path.name} contains forbidden bare `assert` statements at lines: {assert_lines}",
    )

    float_const_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value).__name__ == "float"
    ]
    _check(
        not float_const_lines,
        f"{self_path.name} contains forbidden float literals at lines: {float_const_lines}",
    )

    float_name_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "float"
    ]
    _check(
        not float_name_lines,
        f"{self_path.name} contains forbidden `float` references/calls at lines: {float_name_lines}",
    )

    div_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Div)]
    _check(
        not div_lines,
        f"{self_path.name} contains forbidden `/` division operators at lines: {div_lines}",
    )
