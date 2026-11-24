"""Audited S1b native Typst vector figure verification suite.

Verifies:
1. Complete 39-figure inventory (6 Main + 33 Manual: 34 converted + 5 authored native)
   with byte-identical historical raster retention and zero remaining #image(...) calls in canonical typst/.
2. Exact data-value checks against frozen CSVs and exact tables for all 26
   DATA_BACKED_VERIFIED figures (including strict pre-LHC target quarantine for
   higgs_tritrioseptyro_trace_flow).
3. Zero invented datasets (zero csv(...) calls) for all 13 CONCEPTUAL_SCHEMATIC figures.
4. Vector PDF invariants across all 43 exported PDFs (6 Main + 37 Manual):
   1 page, 0 raster XObjects, extractable text, opaque black text (>= 4pt),
   zero @preview/* dependencies, and exact manifest/GENERATION_MANIFEST hashes.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import pypdf
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_verifier():
    spec = importlib.util.spec_from_file_location("aod_vtp_s1b", ROOT / "scripts/verify_typst_parity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_exporter():
    spec = importlib.util.spec_from_file_location("aod_exp_s1b", ROOT / "scripts/export_typst_figures.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _count_raster_xobjects(pdf_path: Path) -> int:
    reader = pypdf.PdfReader(str(pdf_path))
    count = 0

    def _walk(resources) -> None:
        nonlocal count
        if resources is None:
            return
        res_obj = resources.get_object() if hasattr(resources, "get_object") else resources
        xobjs = res_obj.get("/XObject")
        if xobjs is None:
            return
        xobjs_dict = xobjs.get_object() if hasattr(xobjs, "get_object") else xobjs
        for val in xobjs_dict.values():
            obj = val.get_object() if hasattr(val, "get_object") else val
            st = str(obj.get("/Subtype", ""))
            if st == "/Image":
                count += 1
            elif st == "/Form":
                _walk(obj.get("/Resources"))

    for page in reader.pages:
        _walk(page.get("/Resources"))
    return count


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = pypdf.PdfReader(str(pdf_path))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def test_s1b_figure_inventory_complete_and_historical_rasters_retained():
    inv = json.loads((ROOT / "typst/figure_inventory.json").read_text(encoding="utf-8"))
    cb = json.loads((ROOT / "contracts/scientific/CANONICAL_BINDINGS.json").read_text(encoding="utf-8"))
    frozen = cb["frozen_sha256"]

    assert inv["schema"] == "aod.m4.s1b.figure-inventory.v1"
    summary = inv["summary"]
    assert summary["total_active_rasters"] == 34
    assert summary["main_rasters"] == 6
    assert summary["manual_rasters"] == 28
    assert summary["authored_native_vector"] == 5
    assert summary["total_vector_figures"] == 39
    assert summary["DATA_BACKED_VERIFIED"] == 26
    assert summary["CONCEPTUAL_SCHEMATIC"] == 13
    assert summary["UNRESOLVED_RETAINED"] == 0
    assert summary["converted_vector"] == 34
    assert summary["retained_raster"] == 0

    figs = inv["figures"]
    assert len(figs) == 39
    assert sum(1 for f in figs if f["surface"] == "main") == 6
    assert sum(1 for f in figs if f["surface"] == "manual") == 33
    assert sum(1 for f in figs if f["provenance_class"] == "DATA_BACKED_VERIFIED") == 26
    assert sum(1 for f in figs if f["provenance_class"] == "CONCEPTUAL_SCHEMATIC") == 13

    seen_slugs = set()
    seen_labels = set()
    converted_count = 0
    authored_count = 0
    for f in figs:
        assert f["conversion_status"] in ("CONVERTED_VECTOR", "AUTHORED_NATIVE_VECTOR")
        assert f["visual_comparison_recorded"] is True
        assert f["raster_image_xobjects"] == 0
        assert f["slug"] not in seen_slugs
        assert f["label"] not in seen_labels
        seen_slugs.add(f["slug"])
        seen_labels.add(f["label"])

        if f["conversion_status"] == "CONVERTED_VECTOR":
            converted_count += 1
            # Historical raster retained byte-for-byte and bound to CANONICAL_BINDINGS.json
            raster_p = ROOT / f["raster_path"]
            assert raster_p.is_file(), f"Missing historical raster {f['raster_path']}"
            assert _sha256(raster_p) == f["raster_sha256"]
            assert frozen.get(f["raster_path"]) == f["raster_sha256"]
        else:
            authored_count += 1
            assert f["raster_path"] is None and f["raster_sha256"] is None

        # Typst component and exported PDF exist and match recorded hashes
        comp_p = ROOT / f["target_typst_component"]
        pdf_p = ROOT / f["target_exported_pdf"]
        assert comp_p.is_file()
        assert pdf_p.is_file()
        assert _sha256(comp_p) == f["typst_component_sha256"]
        assert _sha256(pdf_p) == f["exported_pdf_sha256"]

        # Section file binds this component via #include and preserves the exact <label>
        sec_text = (ROOT / f["typst_section"]).read_text(encoding="utf-8")
        assert f"<{f['label']}>" in sec_text
        assert Path(f["target_typst_component"]).name in sec_text
    assert converted_count == 34 and authored_count == 5

    # Zero #image(...) calls remain anywhere in typst/
    for typ_p in sorted((ROOT / "typst").rglob("*.typ")):
        assert "#image(" not in typ_p.read_text(encoding="utf-8"), f"Stray #image( in {typ_p}"


def test_s1b_conceptual_schematics_invent_zero_datasets():
    inv = json.loads((ROOT / "typst/figure_inventory.json").read_text(encoding="utf-8"))
    schematics = [f for f in inv["figures"] if f["provenance_class"] == "CONCEPTUAL_SCHEMATIC"]
    assert len(schematics) == 13
    for f in schematics:
        assert f["data_sources"] == []
        assert f["data_check_verified"] is False
        src = (ROOT / f["target_typst_component"]).read_text(encoding="utf-8")
        assert "csv(" not in src, f"Conceptual schematic must not read a dataset: {f['slug']}"


def test_s1b_all_38_exported_vector_pdfs_invariants():
    vtp = _load_verifier()
    gen_manifest = json.loads((ROOT / "latex/GENERATION_MANIFEST.json").read_text(encoding="utf-8"))
    gen_out_sha = {o["path"]: o["sha256"] for o in gen_manifest["outputs"]}
    # Zero staged rasters remain in generated latex/
    assert not [o for o in gen_manifest["outputs"] if o["kind"] == "staged_raster"]

    expected = [
        ("main", ROOT / "latex/figures/generated", "figures/generated", 6),
        ("manual", ROOT / "latex/manual/figures/generated", "manual/figures/generated", 37),
    ]
    total_pdfs = 0
    for surf, fig_dir, rel_dir, exp_count in expected:
        mf_path = fig_dir / "FIGURE_MANIFEST.json"
        assert mf_path.is_file()
        mf = json.loads(mf_path.read_text(encoding="utf-8"))
        assert mf["schema"] == "aod.typst.figure-export.v1"
        assert mf["surface"] == surf
        assert "typst_version" not in mf and "removed_outputs" not in mf
        assert len(mf["figures"]) == exp_count

        for entry in mf["figures"]:
            pdf_p = fig_dir / entry["output_filename"]
            assert pdf_p.is_file()
            digest = _sha256(pdf_p)
            assert digest == entry["output_sha256"]
            assert gen_out_sha.get(f"{rel_dir}/{entry['output_filename']}") == digest

            reader = pypdf.PdfReader(str(pdf_p))
            assert len(reader.pages) == 1
            assert _count_raster_xobjects(pdf_p) == 0
            text = _extract_pdf_text(pdf_p).strip()
            assert text, f"No extractable text in {pdf_p}"

            paint = vtp._scan_pdf_text_paint(pdf_p)
            assert paint["non_black_or_invisible"] == 0
            assert paint["min_font_size"] >= 4.0

            comp_src = (ROOT / entry["diagram_component"]).read_text(encoding="utf-8")
            assert "@preview/" not in comp_src and "@local/" not in comp_src
            total_pdfs += 1

    assert total_pdfs == 43


def _parse_typ_num_tuple(src: str, var_name: str) -> list[float]:
    m = re.search(rf"#let\s+{re.escape(var_name)}\s*=\s*\(([^)]+)\)", src)
    assert m is not None, f"Missing tuple binding #let {var_name} = (...)"
    return [float(tok.strip()) for tok in m.group(1).split(",") if tok.strip()]


def _parse_xlim_ylim(src: str) -> tuple[tuple[float, float], tuple[float, float]]:
    mx = re.search(r"\bxlim\s*:\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)", src)
    my = re.search(r"\bylim\s*:\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)", src)
    assert mx is not None and my is not None, "Missing xlim/ylim in plot"
    return (float(mx.group(1)), float(mx.group(2))), (float(my.group(1)), float(my.group(2)))


def _parse_typ_cell_number(cell: str) -> float:
    cleaned = cell.replace("$", "").replace("−", "-")
    cleaned = re.sub(r'"%"', "", cleaned)
    cleaned = re.sub(r"\barcsec(?:/cy)?\b", "", cleaned).strip()
    m_sci = re.match(r"^(-?\s*[0-9.]+)\s*times\s*10\^\(\s*(-\s*[0-9]+|[0-9]+)\s*\)$", cleaned)
    if m_sci:
        return float(f"{m_sci.group(1).replace(' ', '')}e{m_sci.group(2).replace(' ', '')}")
    return float(cleaned.replace(" ", ""))


def test_s1b_all_23_data_backed_figures_match_frozen_sources():
    inv = json.loads((ROOT / "typst/figure_inventory.json").read_text(encoding="utf-8"))
    data_figs = [f for f in inv["figures"] if f["provenance_class"] == "DATA_BACKED_VERIFIED"]
    assert len(data_figs) == 26

    # 1. Verify every declared data source exists byte-for-byte and every csv(...) call is literal and declared.
    for f in data_figs:
        assert f["data_check_verified"] is True
        declared_csvs = set()
        for ds in f["data_sources"]:
            if isinstance(ds, dict) and "path" in ds:
                ds_p = ROOT / ds["path"]
                assert ds_p.is_file(), f"Missing declared data source {ds['path']} for {f['slug']}"
                assert _sha256(ds_p) == ds["sha256"]
                if ds["path"].endswith(".csv"):
                    declared_csvs.add(ds["path"])
        src = (ROOT / f["target_typst_component"]).read_text(encoding="utf-8")
        used_csvs = {m.group(1) for m in re.finditer(r'\bcsv\(\s*"/([^"]+)"', src)}
        assert used_csvs == declared_csvs, (
            f"CSV mismatch in {f['slug']}: used={sorted(used_csvs)} vs declared={sorted(declared_csvs)}"
        )

    # 2. Exact data, column-binding, axis-bound, and rendered-text checks across ALL 23 DATA_BACKED_VERIFIED figures:
    # (a) 90-tick cycle-shedding fixture
    with (ROOT / "wavelet_shedding_simulation.csv").open(encoding="utf-8") as fh:
        w_rows = list(csv.DictReader(fh))
    assert len(w_rows) == 90
    assert max(float(r["shed_excess"]) for r in w_rows) > 0.06
    t = _extract_pdf_text(ROOT / "latex/manual/figures/generated/cycle-disturbance-shedding-fixture.pdf")
    for tok in ("90 native ticks", "Lead", "Lag", "Post-clipping burden", "Outward remainder", "Local fraction"):
        assert tok in t

    # (b) Brownian 3D phase-cycle delta_3 fixture
    with (ROOT / "manual/data/brownian/brownian_sample_track.csv").open(encoding="utf-8") as fh:
        b_track = list(csv.DictReader(fh))
    assert len(b_track) == 9
    assert max(int(r["x"]) for r in b_track) == 6 and max(int(r["y"]) for r in b_track) == 5 and max(int(r["z"]) for r in b_track) == 5
    with (ROOT / "manual/data/brownian/phase_cycle_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["observed_count"]) for r in csv.DictReader(fh)] == [0, 0, 4, 4, 0]
    with (ROOT / "manual/data/brownian/octant_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["observed_count"]) for r in csv.DictReader(fh)] == [6, 0, 1, 0, 1, 0, 0, 0]
    t = _extract_pdf_text(ROOT / "latex/manual/figures/generated/coordinate-phase-delta3-wireframe.pdf")
    for tok in ("Integerized 3D trajectory", "Phase counts", "Octant counts", "integer ratios"):
        assert tok in t

    # (c) Higgs trace flow (strict pre-LHC target quarantine + q^p + q formula), saddle signature, and LHC mass comparison
    with (ROOT / "manual/data/higgs/higgs_trace_internal_candidates_selection.csv").open(encoding="utf-8") as fh:
        h_rows = list(csv.DictReader(fh))
    sel = next(r for r in h_rows if r["rank"] == "1")
    assert (sel["candidate_K"], int(sel["Pi_qp_plus_q"]), int(sel["RD_accessor"]),
            int(sel["PD_window_pressure"]), int(sel["QD_pending_overhang"]),
            int(sel["delta_lower"]), int(sel["delta_upper"])) == ("3:3:7", 30, 61, 21, 162, 3, -3)
    # Verify Pi_qp_plus_q == q^p + q across all rows (including p != q)
    for hr in h_rows:
        p_i, q_i = int(hr["p"]), int(hr["q"])
        assert q_i ** p_i + q_i == int(hr["Pi_qp_plus_q"])
    tf_src = (ROOT / "typst/lib/figures/manual/higgs_tritrioseptyro_trace_flow.typ").read_text(encoding="utf-8")
    assert "higgs_external_lhc_mass_comparison_after_freeze.csv" not in tf_src
    assert "higgs_external_map_after_candidate_freeze.csv" in tf_src
    assert "#sel.q ^#sel.p + #sel.q" in tf_src
    t_tf = _extract_pdf_text(ROOT / "latex/manual/figures/generated/higgs-tritrioseptyro-trace-flow.pdf")
    for tok in ("3:3:7", "30", "61", "21", "162", "124.928"):
        assert tok in t_tf
    t_sad = _extract_pdf_text(ROOT / "latex/manual/figures/generated/higgs-yro-saddle-signature.pdf")
    assert "+3" in t_sad and "21" in t_sad and "3:3:7" in t_sad
    with (ROOT / "manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv").open(encoding="utf-8") as fh:
        lhc_rows = list(csv.DictReader(fh))
    hm_src = (ROOT / "typst/lib/figures/manual/higgs_mass_comparison.typ").read_text(encoding="utf-8")
    _, (hm_ylo, hm_yhi) = _parse_xlim_ylim(hm_src)
    for lr in lhc_rows:
        m_v, s_v = float(lr["mass_GeV"]), float(lr["sigma_GeV"])
        assert hm_ylo < m_v - s_v and m_v + s_v < hm_yhi
    t_mass = _extract_pdf_text(ROOT / "latex/manual/figures/generated/higgs-mass-comparison.pdf")
    assert "124.928" in t_mass and "ATLAS+CMS" in t_mass and "CMS" in t_mass

    # (d) Double-slit exact 11-bin integer fixture dynamically cross-checked against <tab:manual-dimonhexon-double-slit-fixture>
    ds_sec = (ROOT / "typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ").read_text(encoding="utf-8")
    ds_pos = ds_sec.find("<tab:manual-dimonhexon-double-slit-fixture>")
    ds_tbl_start = ds_sec.rfind("#figure(", 0, ds_pos)
    ds_tbl = ds_sec[ds_tbl_start:ds_pos]
    row_re = re.compile(
        r"\[(\$-?\s*\d+\$|\$\d+\$)\],\s*\[(\d+)\],\s*\[(\d+)\],\s*\[(-?\d+)\],\s*\[(\d+)\],\s*\[(\d+)\],"
    )
    parsed_ds = [
        (int(_parse_typ_cell_number(m.group(1))), int(m.group(2)), int(m.group(3)), int(m.group(5)), int(m.group(6)))
        for m in row_re.finditer(ds_tbl)
    ]
    assert len(parsed_ds) == 11, f"Expected 11 parsed rows from double-slit table, got {len(parsed_ds)}"
    ds_src = (ROOT / "typst/lib/figures/manual/double_slit_reclosure_fixture.typ").read_text(encoding="utf-8")
    assert [int(x) for x in _parse_typ_num_tuple(ds_src, "ks")] == [r[0] for r in parsed_ds]
    assert [int(x) for x in _parse_typ_num_tuple(ds_src, "s-single")] == [r[1] for r in parsed_ds]
    assert [int(x) for x in _parse_typ_num_tuple(ds_src, "t-no-cross")] == [r[2] for r in parsed_ds]
    assert [int(x) for x in _parse_typ_num_tuple(ds_src, "t-cross")] == [r[3] for r in parsed_ds]
    assert [int(x) for x in _parse_typ_num_tuple(ds_src, "o-comp")] == [r[4] for r in parsed_ds]
    t_ds = _extract_pdf_text(ROOT / "latex/manual/figures/generated/double-slit-reclosure-fixture.pdf")
    for tok in ("Dimonhexon double-slit reclosure fixture", "two/cross calc", "fixture comparator"):
        assert tok in t_ds

    # (e) Solar-system exact O0 records dynamically cross-checked against <tab:manual-solar-observable-map-results>
    sol_sec = (ROOT / "typst/manual/sections/05_solar_system_field_tests.typ").read_text(encoding="utf-8")
    sol_pos = sol_sec.find("<tab:manual-solar-observable-map-results>")
    sol_tbl = sol_sec[sol_sec.rfind("#figure(", 0, sol_pos):sol_pos]
    sol_row_re = re.compile(
        r"\[(Mercury perihelion|Solar light bending|Solar redshift)\],\s*\[([^\]]+)\],\s*\[([^\]]+)\],\s*\[([^\]]+)\],\s*\[([^\]]+)\],"
    )
    parsed_sol = [
        (m.group(1), _parse_typ_cell_number(m.group(2)), _parse_typ_cell_number(m.group(3)), _parse_typ_cell_number(m.group(5)))
        for m in sol_row_re.finditer(sol_tbl)
    ]
    assert len(parsed_sol) == 3, f"Expected 3 parsed rows from solar table, got {len(parsed_sol)}"
    sol1 = (ROOT / "typst/lib/figures/manual/solar_calculated_vs_target.typ").read_text(encoding="utf-8")
    sol2 = (ROOT / "typst/lib/figures/manual/solar_percent_error.typ").read_text(encoding="utf-8")
    assert _parse_typ_num_tuple(sol1, "ao-vals") == [r[1] for r in parsed_sol]
    assert _parse_typ_num_tuple(sol1, "tgt-vals") == [r[2] for r in parsed_sol]
    assert _parse_typ_num_tuple(sol2, "errs") == [r[3] for r in parsed_sol]
    for pdf_name, tok in (
        ("solar-calculated-vs-target.pdf", "Mercury perihelion"),
        ("solar-percent-error.pdf", "Solar redshift"),
    ):
        assert tok in _extract_pdf_text(ROOT / "latex/manual/figures/generated" / pdf_name)

    # (f) SPARC NGC3198 (43 bins) & declaration controls (4 rows): column bindings, axis bounds, and rendered PDF text
    with (ROOT / "manual/data/derived/sparc_five_galaxy_per_bin.csv").open(encoding="utf-8") as fh:
        ngc = [r for r in csv.DictReader(fh) if r["galaxy"] == "NGC3198"]
    assert len(ngc) == 43
    r_vals = [float(r["R"]) for r in ngc]
    with (ROOT / "manual/data/derived/sparc_declaration_controls.csv").open(encoding="utf-8") as fh:
        sparc_ctrl = list(csv.DictReader(fh))
    assert len(sparc_ctrl) == 4
    sparc_checks = [
        ("sparc_declaration_controls.typ", "sparc-declaration-controls.pdf", ("MAPE_U_percent",),
         [float(r["MAPE_U_percent"]) for r in sparc_ctrl], ("SPARC declaration controls", "radial only", "boundary-face slow")),
        ("sparc_square_speed_comparison.typ", "sparc-square-speed-comparison.pdf", ("r.R", "r.U_obs", "r.U_AO"),
         [float(r["U_obs"]) for r in ngc] + [float(r["U_AO"]) for r in ngc], ("SPARC square-speed comparison", "R [kpc]")),
        ("sparc_square_speed_residuals.typ", "sparc-square-speed-residuals.pdf", ("r.R", "r.Delta_U"),
         [float(r["Delta_U"]) for r in ngc], ("SPARC square-speed residuals", "primary declaration")),
        ("sparc_display_speed_view.typ", "sparc-display-speed-view.pdf", ("r.R", "r.Vobs", "r.V_disp"),
         [float(r["Vobs"]) for r in ngc] + [float(r["V_disp"]) for r in ngc], ("Display speed view", "benchmark target speed")),
    ]
    for typ_name, pdf_name, cols, yvals, toks in sparc_checks:
        s_txt = (ROOT / "typst/lib/figures/manual" / typ_name).read_text(encoding="utf-8")
        for c in cols:
            assert c in s_txt, f"Missing column binding {c} in {typ_name}"
        (xlo, xhi), (ylo, yhi) = _parse_xlim_ylim(s_txt)
        if "r.R" in cols:
            assert xlo <= min(r_vals) and max(r_vals) <= xhi
        assert ylo <= min(yvals) and max(yvals) <= yhi, f"Data clipped in {typ_name}: [{min(yvals)}, {max(yvals)}] vs [{ylo}, {yhi}]"
        p_txt = _extract_pdf_text(ROOT / "latex/manual/figures/generated" / pdf_name)
        for tok in toks:
            assert tok in p_txt, f"Missing {tok!r} in {pdf_name}"

    # (g) Tau ring diagnostic (4 rows), exact 31/50 = 0.62 missing burden ratio, and declaration controls (4 rows)
    with (ROOT / "manual/data/derived/tau_ring_diagnostic.csv").open(encoding="utf-8") as fh:
        tau_rows = list(csv.DictReader(fh))
    assert [r["K"] for r in tau_rows] == ["1:2:8", "1:2:9", "1:2:10", "3:3:8"]
    with (ROOT / "manual/data/dec/tau_missing_burden_exact_ratio_patch.csv").open(encoding="utf-8") as fh:
        patch = next(csv.DictReader(fh))
    assert int(patch["missing_num"]) == 31 and int(patch["missing_den"]) == 50
    with (ROOT / "manual/data/derived/tau_declaration_controls.csv").open(encoding="utf-8") as fh:
        tau_ctrl = list(csv.DictReader(fh))
    assert len(tau_ctrl) == 4
    tau_checks = [
        ("tau_ring_support_score.typ", "tau-ring-support-score.pdf", ("r.S_tau", "r.S_tau_ring"),
         [float(r["S_tau"]) for r in tau_rows] + [float(r["S_tau_ring"]) for r in tau_rows],
         ("Tau ring support score", "1:2:9", "cell score", "ring score")),
        ("tau_missing_burden_diagnostic.typ", "tau-missing-burden-diagnostic.pdf", ("r.missing_fraction", 'type: "hline"'),
         [float(r["missing_fraction"]) for r in tau_rows] + [31.0 / 50.0],
         ("Tau missing-burden diagnostic", "Tau missing-burden target", "1:2:9")),
        ("tau_support_residuals.typ", "tau-support-residuals.pdf", ("r.S_tau_ring",),
         [float(r["S_tau_ring"]) for r in tau_rows], ("Tau-support residuals", "primary declaration", "1:2:9")),
        ("tau_declaration_controls.typ", "tau-declaration-controls.pdf", ("r.winner_margin_percent",),
         [float(r["winner_margin_percent"]) for r in tau_ctrl], ("Tau declaration controls", "winner margin", "ring d=3")),
    ]
    for typ_name, pdf_name, cols, yvals, toks in tau_checks:
        s_txt = (ROOT / "typst/lib/figures/manual" / typ_name).read_text(encoding="utf-8")
        for c in cols:
            assert c in s_txt, f"Missing {c} in {typ_name}"
        _, (ylo, yhi) = _parse_xlim_ylim(s_txt)
        assert ylo <= min(yvals) and max(yvals) <= yhi, f"Data clipped in {typ_name}"
        p_txt = _extract_pdf_text(ROOT / "latex/manual/figures/generated" / pdf_name)
        for tok in toks:
            assert tok in p_txt, f"Missing {tok!r} in {pdf_name}"

    # (h) Run-tumble 20-tick 5-panel projection
    with (ROOT / "manual/data/run_tumble/run_tumble_trace_20_ticks.csv").open(encoding="utf-8") as fh:
        rt_rows = list(csv.DictReader(fh))
    assert len(rt_rows) == 21
    with (ROOT / "manual/data/run_tumble/run_tumble_phase_cycle_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["O"]) for r in csv.DictReader(fh)] == [6, 3, 3, 3, 5]
    with (ROOT / "manual/data/run_tumble/run_tumble_octant_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["m"]) for r in csv.DictReader(fh)] == [8, 3, 3, 3, 7, 2, 2, 2]
    t_rt = _extract_pdf_text(ROOT / "latex/manual/figures/generated/run-tumble-trace-3d-projection.pdf")
    for tok in ("Run-tumble tracer-current projection", "mode strip: init/run/tumble", "phase counts", "magnitudes"):
        assert tok in t_rt

    # (i) All 6 Lensing CSV-backed figures (01, 03, 04 heatmap, 05, 06, 07 gate)
    with (ROOT / "manual/data/lensing/toy1_delta3_class_tallies.csv").open(encoding="utf-8") as fh:
        l1_rows = list(csv.DictReader(fh))
    l1_src = (ROOT / "typst/lib/figures/manual/lensing_01_toy1_delta3_class_tallies.typ").read_text(encoding="utf-8")
    _, (l1_lo, l1_hi) = _parse_xlim_ylim(l1_src)
    assert l1_lo <= 0 and max(float(r["T_cross_predicted_tally"]) for r in l1_rows) <= l1_hi
    assert "Toy 1 exact internal" in _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-01-toy1-delta3-class-tallies.pdf")

    with (ROOT / "manual/data/lensing/sparc5_medium_diagnostic_summary.csv").open(encoding="utf-8") as fh:
        l3_rows = list(csv.DictReader(fh))
    l3_src = (ROOT / "typst/lib/figures/manual/lensing_03_sparc5_lens_medium_phase_proxy.typ").read_text(encoding="utf-8")
    _, (l3_lo, l3_hi) = _parse_xlim_ylim(l3_src)
    assert l3_lo <= 0 and max(float(r["max_abs_ΔAγ"]) for r in l3_rows) <= l3_hi
    t_l3 = _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-03-sparc5-lens-medium-phase-proxy.pdf")
    for g in ("NGC2403", "NGC3198", "NGC6503", "NGC2841", "DDO154"):
        assert g in t_l3

    t_hm = _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-04-sparc5-class-tally-heatmap.pdf")
    for tok in ("NGC2403", "NGC3198", "NGC6503", "NGC2841", "DDO154", "28", "29", "25", "31", "14"):
        assert tok in t_hm

    with (ROOT / "manual/data/lensing/swells_k1_k2_k3_delta3_comparison.csv").open(encoding="utf-8") as fh:
        l5_rows = list(csv.DictReader(fh))
    l5_src = (ROOT / "typst/lib/figures/manual/lensing_05_swells_k_comparison_delta3.typ").read_text(encoding="utf-8")
    _, (l5_lo, l5_hi) = _parse_xlim_ylim(l5_src)
    assert l5_lo <= 0 and max(max(float(r["thetaE_delta3_total_m"]), float(r["sigma_delta3_total_m"])) for r in l5_rows) <= l5_hi
    t_l5 = _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-05-swells-k-comparison-delta3.pdf")
    for tok in ("SWELLS K1/K2/K3", "K1", "K2", "K3"):
        assert tok in t_l5

    with (ROOT / "manual/data/lensing/swells_k1_thetaE_delta3_scores.csv").open(encoding="utf-8") as fh:
        l6_rows = list(csv.DictReader(fh))
    l6_src = (ROOT / "typst/lib/figures/manual/lensing_06_swells_k1_thetae_delta3_tallies.typ").read_text(encoding="utf-8")
    _, (l6_lo, l6_hi) = _parse_xlim_ylim(l6_src)
    assert l6_lo <= 0 and max(max(float(r["T_cross_predicted_tally"]), float(r["O_observed_tally"])) for r in l6_rows) <= l6_hi
    assert "SWELLS K1" in _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-06-swells-k1-thetae-delta3-tallies.pdf")

    t_k4 = _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-07-k4-3d-timeflow-input-gate.pdf")
    for tok in ("3D density fields", "2 fields", "audit controls", "1 field", "velocity and flow fields"):
        assert tok in t_k4

    # (j) Boundary-Full SADAR data-backed figures: Q4 chiral walk, 5-boundary Tau stack, and 10-carrier debris atlas
    with (ROOT / "manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv").open(encoding="utf-8") as fh:
        walk_rows = list(csv.DictReader(fh))
    assert len(walk_rows) == 10
    t_walk = _extract_pdf_text(ROOT / "latex/manual/figures/generated/dec-hinge-slide-chiral-vertex.pdf")
    for tok in ("0000", "0100", "3/7", "1/7", "6/7"):
        assert tok in t_walk

    with (ROOT / "manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv").open(encoding="utf-8") as fh:
        tau5_rows = list(csv.DictReader(fh))
    assert len(tau5_rows) == 7
    t_tau5 = _extract_pdf_text(ROOT / "latex/manual/figures/generated/tau-five-boundary-sadar-setup.pdf")
    for tok in ("650/2500", "1850/2500", "19/50", "31/50", "1776.86"):
        assert tok in t_tau5

    with (ROOT / "manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv").open(encoding="utf-8") as fh:
        atlas_rows = list(csv.DictReader(fh))
    assert len(atlas_rows) == 10
    t_atlas = _extract_pdf_text(ROOT / "latex/manual/figures/generated/rest-energy-stability-debris-atlas.pdf")
    for tok in ("8160", "9104", "1020", "408", "917"):
        assert tok in t_atlas


def test_s1b_no_math_escape_typos_and_no_phantom_comment_paths():
    for typ_p in sorted((ROOT / "typst/lib/figures").rglob("*.typ")) + sorted((ROOT / "typst/lib/diagrams").rglob("*.typ")) + [ROOT / "typst/lib/aod_plots.typ"]:
        text = typ_p.read_text(encoding="utf-8")
        assert not re.search(r"\\[,;:!]", text), f"LaTeX math-spacing escape renders literally in Typst: {typ_p}"
        if typ_p.name != "aod_plots.typ":
            non_comment = "\n".join(ln for ln in text.splitlines() if not ln.strip().startswith("//"))
            assert "`" not in non_comment, (
                f"Raw backtick span in figure component falls back to OS-dependent monospace font: {typ_p}"
            )
        for idx, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("//"):
                for m in re.finditer(
                    r"((?:scripts|manual|figures_jpg|typst)/[A-Za-z0-9_./{},-]+\.(?:py|png|jpg|csv|typ))",
                    line,
                ):
                    ref = m.group(1)
                    if "{" in ref:
                        continue
                    assert (ROOT / ref).exists(), f"Phantom repo path in comment {typ_p}:{idx}: {ref}"


def test_s1b_vector_figure_policy_rejects_bypass_attempts():
    vtp = _load_verifier()
    base_entry = {"data_sources": [{"path": "manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv"}]}
    base_src = (ROOT / "typst/lib/figures/manual/higgs_mass_comparison.typ").read_text(encoding="utf-8")
    assert vtp._vector_figure_policy_violations("typst/lib/figures/manual/higgs_mass_comparison.typ", base_src, base_entry) == []

    # Dynamic csv(var) bypass must fail closed
    dyn_src = base_src.replace(
        'csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv"',
        'csv(secret_path',
    )
    v_dyn = vtp._vector_figure_policy_violations("test.typ", dyn_src, base_entry)
    assert any("dynamic or non-literal csv(" in v for v in v_dyn)

    # Non-wildcard #import bypass must fail closed
    imp_src = base_src + '\n#import "/typst/lib/aod_schema.typ": aod-boxed\n'
    v_imp = vtp._vector_figure_policy_violations("test.typ", imp_src, base_entry)
    assert any("may only contain the single `#import" in v for v in v_imp)

    # #include bypass must fail closed
    inc_src = base_src + '\n#include "/typst/sections/01_introduction.typ"\n'
    v_inc = vtp._vector_figure_policy_violations("test.typ", inc_src, base_entry)
    assert any("forbidden `include`" in v for v in v_inc)

    # Block-comment (including nested) obfuscated unauthorized csv must fail closed
    bc_src = base_src.replace(
        'csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv"',
        'csv(/* outer /* inner */ */"/manual/data/derived/tau_ring_diagnostic.csv"',
    )
    v_bc = vtp._vector_figure_policy_violations("test.typ", bc_src, base_entry)
    assert any("unauthorized csv(" in v for v in v_bc)

    # First-class function aliasing, higher-order call, std/sys/plugin/read/image,
    # bracketed directives, set rules, spread args, and math-mode bypasses must ALL fail closed
    red_team_mutations = [
        ("let_alias_csv", "#let r = csv\n#let _ = r(\"/manual/data/derived/tau_ring_diagnostic.csv\")\n", "aliasing or non-direct reference to `csv`"),
        ("higher_order_csv", "#let _ = ((f) => f(\"/manual/data/derived/tau_ring_diagnostic.csv\"))(csv)\n", "aliasing or non-direct reference to `csv`"),
        ("let_alias_read", "#let rd = read\n", "forbidden identifier/call `read`"),
        ("let_alias_image", "#let im = image\n", "forbidden identifier/call `image`"),
        ("std_csv", "#let _ = std.csv(\"/manual/data/derived/tau_ring_diagnostic.csv\")\n", "`std.` module access is forbidden"),
        ("bracket_import", "#[ok]#import \"/typst/lib/aod_schema.typ\": aod-boxed\n", "may only contain the single `#import"),
        ("bracket_include", "#[ok]#include \"/typst/sections/01_introduction.typ\"\n", "forbidden `include`"),
        ("plugin_call", "#let _ = plugin(\"/foo.wasm\")\n", "forbidden identifier/call `plugin`"),
        ("sys_inputs", "#let _ = sys.inputs\n", "forbidden identifier/call `sys.inputs`"),
        ("set_rule", "#set text(fill: white)\n", "forbidden `set` rule"),
        ("math_image", "$ image(\"/figures/fig_1.png\") $\n", "forbidden identifier/call `image`"),
        ("math_std_eval", "$ std.eval(\"1+1\") $\n", "`std.` module access is forbidden"),
        ("math_std_sys", "$ std.sys.inputs $\n", "`std.` module access is forbidden"),
        ("math_hash_eval", "$ #eval(\"1+1\") $\n", "forbidden identifier/call `eval`"),
        ("context_kw", "#context [x]\n", "forbidden keyword `context`"),
        ("hide_call", "#hide[secret]\n", "forbidden identifier/call `hide`"),
    ]
    for label, injection, expected_sub in red_team_mutations:
        mutated = base_src.replace("#aod-canvas(", injection + "#aod-canvas(", 1)
        viols = vtp._vector_figure_policy_violations(f"redteam_{label}.typ", mutated, base_entry)
        assert viols, f"Red-team payload {label} was NOT rejected!"
        assert any(expected_sub in v for v in viols), f"Red-team payload {label} got unexpected violations: {viols}"

    # Spread arguments in csv(...) must fail closed
    spread_src = base_src.replace(
        'csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv", row-type: dictionary)',
        'csv(..args)',
    )
    v_spread = vtp._vector_figure_policy_violations("test_spread.typ", spread_src, base_entry)
    assert any("argument spread is forbidden" in v for v in v_spread)


def test_s1b_pdf_raster_xobject_scanner_and_comment_stripped_csv_extractor(tmp_path):
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, NumberObject, StreamObject

    vtp = _load_verifier()
    exp = _load_exporter()

    # 1. Real exported vector figure PDF must report 0 raster /Image XObjects
    sample_pdf = ROOT / "latex/figures/generated/fractal-tesseract-q4-witness.pdf"
    assert vtp._count_pdf_raster_xobjects(sample_pdf) == 0
    assert vtp._require_zero_pdf_raster_xobjects(sample_pdf, sample_pdf.name) == 0

    # 2. Synthetic PDF with embedded /Image XObject (including nested inside a /Form XObject) must fail closed
    nested_pdf = tmp_path / "nested_raster.pdf"
    w = PdfWriter()
    pg = w.add_blank_page(width=100, height=100)
    img = StreamObject()
    img[NameObject("/Type")] = NameObject("/XObject")
    img[NameObject("/Subtype")] = NameObject("/Image")
    img[NameObject("/Width")] = NumberObject(1)
    img[NameObject("/Height")] = NumberObject(1)
    img[NameObject("/ColorSpace")] = NameObject("/DeviceGray")
    img[NameObject("/BitsPerComponent")] = NumberObject(8)
    img._data = b"\x00"
    img_ref = w._add_object(img)
    form = StreamObject()
    form[NameObject("/Type")] = NameObject("/XObject")
    form[NameObject("/Subtype")] = NameObject("/Form")
    form[NameObject("/Resources")] = DictionaryObject({
        NameObject("/XObject"): DictionaryObject({NameObject("/ImNested"): img_ref}),
    })
    form._data = b""
    form_ref = w._add_object(form)
    pg[NameObject("/Resources")] = DictionaryObject({
        NameObject("/XObject"): DictionaryObject({NameObject("/Fm0"): form_ref}),
    })
    with nested_pdf.open("wb") as fh:
        w.write(fh)
    assert vtp._count_pdf_raster_xobjects(nested_pdf) == 1
    with pytest.raises(ValueError, match="Unexpected raster image\\(s\\) in pure-vector PDF.*raster_image_xobjects=1"):
        vtp._require_zero_pdf_raster_xobjects(nested_pdf, "nested_raster.pdf")
    with pytest.raises(ValueError, match="Unexpected raster image\\(s\\) in pure-vector PDF.*raster_image_xobjects=1"):
        exp.require_zero_pdf_rasters(nested_pdf, "nested_raster.pdf")

    # 3. _extract_csv_inputs must ignore commented-out csv(...) references (line and nested block comments)
    comp = tmp_path / "sample_fig.typ"
    comp.write_text(
        '// csv("/manual/data/does_not_exist_line.csv")\n'
        '/* outer /* nested */ csv("/manual/data/does_not_exist_block.csv") */\n'
        '#let rows = csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv", row-type: dictionary)\n',
        encoding="utf-8",
    )
    refs = exp._extract_csv_inputs(comp, ROOT)
    assert [r["path"] for r in refs] == ["manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv"]

    # 4. _pure_vector_surfaces must actively enforce both Main and Manual on the live repo,
    #    and exclude a surface if any figure on that surface is UNRESOLVED_RETAINED
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))
    assert vtp._pure_vector_surfaces(ROOT, manifest) == {"main", "manual"}
    syn_root = tmp_path / "syn_inv_root"
    (syn_root / "typst").mkdir(parents=True)
    inv_copy = json.loads((ROOT / "typst/figure_inventory.json").read_text(encoding="utf-8"))
    for fig in inv_copy["figures"]:
        if fig["surface"] == "manual":
            fig["conversion_status"] = "UNRESOLVED_RETAINED"
            break
    (syn_root / "typst/figure_inventory.json").write_text(json.dumps(inv_copy), encoding="utf-8")
    assert vtp._pure_vector_surfaces(syn_root, manifest) == {"main"}


def test_s1b_r2_shared_inline_raster_guard_and_malformed_stream_rejection(tmp_path):
    """S1B-F2 / R2: shared verifier & exporter guard rejects page, nested Form, Pattern, AP inline images and malformed streams."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject

    vtp = _load_verifier()
    exp = _load_exporter()

    # Verifier and exporter share the exact same raster inspection implementation (no divergence possible)
    assert vtp._shared_figure_exporter().__file__ == exp.__file__

    inline_bitmap = (
        b"\nq\n18 0 0 18 72 36 cm\nBI\n/W 2 /H 2 /CS /RGB /BPC 8\nID\n"
        + b"\xff\x00\x00\x00\xff\x00\x00\x00\xff\xff\xff\x00"
        + b"\nEI\nQ\n"
    )

    # 1. All 38 committed exported PDFs pass the shared inspector with 0 XObject & 0 inline rasters
    for fig_pdf in sorted((ROOT / "latex").rglob("*.pdf")):
        info = exp.require_zero_pdf_rasters(fig_pdf, fig_pdf.name)
        assert info["raster_image_xobjects"] == 0
        assert info["inline_raster_images"] == 0
        assert info["total_raster_images"] == 0
        assert info["streams_inspected"] >= 1

    # 2. Inline-mutated clone of a real 1-page exported figure (preserving text!) fails BOTH exporter._inspect_pdf AND verifier
    real_fig = ROOT / "latex/figures/generated/cycle-disturbance-shedding.pdf"
    w_cm, h_cm = exp._extract_vector_figure_dims(ROOT / "typst/lib/figures/main/cycle_disturbance_shedding.typ")
    mut_fig = tmp_path / "figure_inline_raster.pdf"
    w = PdfWriter()
    w.clone_document_from_reader(PdfReader(str(real_fig)))
    pg = w.pages[0]
    st = DecodedStreamObject()
    st.set_data(inline_bitmap)
    st_ref = w._add_object(st)
    pg[NameObject("/Contents")] = ArrayObject([pg.get("/Contents"), st_ref])
    with mut_fig.open("wb") as fh:
        w.write(fh)
    # Raw extracted text remains intact while inline bitmap is detected
    assert PdfReader(str(mut_fig)).pages[0].extract_text() == PdfReader(str(real_fig)).pages[0].extract_text()
    mut_info = vtp._inspect_pdf_rasters(mut_fig)
    assert mut_info["raster_image_xobjects"] == 0
    assert mut_info["inline_raster_images"] == 1
    assert mut_info["total_raster_images"] == 1
    with pytest.raises(ValueError, match="inline_raster_images=1"):
        exp._inspect_pdf(mut_fig, w_cm, h_cm)
    with pytest.raises(ValueError, match="inline_raster_images=1"):
        vtp._require_zero_pdf_rasters(mut_fig, mut_fig.name)

    # 3. Inline bitmap nested inside a Form XObject, a Type-1 Pattern, and an Annot /AP stream all fail closed
    for case_name in ("form", "pattern", "annot_ap"):
        p_case = tmp_path / f"nested_{case_name}_inline.pdf"
        wc = PdfWriter()
        pgc = wc.add_blank_page(width=200, height=200)
        s_in = DecodedStreamObject()
        s_in.set_data(inline_bitmap)
        if case_name == "form":
            s_in[NameObject("/Type")] = NameObject("/XObject")
            s_in[NameObject("/Subtype")] = NameObject("/Form")
            pgc[NameObject("/Resources")] = DictionaryObject({
                NameObject("/XObject"): DictionaryObject({NameObject("/Fm0"): wc._add_object(s_in)}),
            })
        elif case_name == "pattern":
            s_in[NameObject("/Type")] = NameObject("/Pattern")
            s_in[NameObject("/PatternType")] = NumberObject(1)
            pgc[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Pattern"): DictionaryObject({NameObject("/P0"): wc._add_object(s_in)}),
            })
        else:
            s_in[NameObject("/Type")] = NameObject("/XObject")
            s_in[NameObject("/Subtype")] = NameObject("/Form")
            annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Widget"),
                NameObject("/AP"): DictionaryObject({NameObject("/N"): wc._add_object(s_in)}),
            })
            pgc[NameObject("/Annots")] = ArrayObject([wc._add_object(annot)])
        with p_case.open("wb") as fh:
            wc.write(fh)
        with pytest.raises(ValueError, match="inline_raster_images=1"):
            vtp._require_zero_pdf_rasters(p_case, p_case.name)

    # 4. Literal string "(BI /W 2 /H 2 ID xxx EI)" produces ZERO false positives
    lit_pdf = tmp_path / "literal_bi_text.pdf"
    wl = PdfWriter()
    pgl = wl.add_blank_page(width=200, height=200)
    sl = DecodedStreamObject()
    sl.set_data(b"BT (BI /W 2 /H 2 ID xxx EI) Tj ET\n")
    pgl[NameObject("/Contents")] = wl._add_object(sl)
    with lit_pdf.open("wb") as fh:
        wl.write(fh)
    assert exp.require_zero_pdf_rasters(lit_pdf, lit_pdf.name)["total_raster_images"] == 0

    # 5. Malformed/uninspectable content stream fails closed (never treated as 0)
    mal_pdf = tmp_path / "malformed_bi.pdf"
    wm = PdfWriter()
    pgm = wm.add_blank_page(width=200, height=200)
    sm = DecodedStreamObject()
    sm.set_data(b"q BI /W 2 /H 2 /CS /RGB /BPC 8 ID \xff\x00\x00")
    pgm[NameObject("/Contents")] = wm._add_object(sm)
    with mal_pdf.open("wb") as fh:
        wm.write(fh)
    with pytest.raises(ValueError, match="Uninspectable or malformed PDF content stream"):
        vtp._require_zero_pdf_rasters(mal_pdf, mal_pdf.name)


def test_s1b_r1_figure9_compiled_math_attachment_and_negative_control(tmp_path):
    """S1B-F1 / R1: compiled Typst AST of Main Figure 9 binds P_W^S (∂F, ω) with S alone in top attachment."""
    import shutil

    vtp = _load_verifier()
    exp = _load_exporter()
    try:
        typst_bin = exp.find_typst(None)
    except FileNotFoundError:
        pytest.skip("typst binary required for compiled Figure 9 AST regression")

    # 1. Clean canonical Figure 9 passes compiled-structure check
    res = vtp._verify_figure9_math_attachment(typst_bin, ROOT)
    assert res["verified"] is True
    assert res["base"] == "P"
    assert res["bottom"] == "W"
    assert res["top"] == "S"
    assert res["baseline_args"] == ["(", "∂", "F", ",", "ω", ")"]

    # 2. Restoring the defective P_W^S(partial F, omega) attachment MUST fail the compiled-structure check
    sb = tmp_path / "fig9_bad_sb"
    (sb / "typst/lib/figures/main").mkdir(parents=True)
    shutil.copy2(ROOT / "typst/lib/aod_plots.typ", sb / "typst/lib/aod_plots.typ")
    fig9_rel = "typst/lib/figures/main/cycle_disturbance_shedding.typ"
    bad_src = (ROOT / fig9_rel).read_text(encoding="utf-8").replace(
        "P_W^S (partial F, omega)", "P_W^S(partial F, omega)", 1
    )
    assert "P_W^S(partial F, omega)" in bad_src
    (sb / fig9_rel).write_text(bad_src, encoding="utf-8")
    with pytest.raises(ValueError, match="Figure 9 formula superscript attachment defect"):
        vtp._verify_figure9_math_attachment(typst_bin, sb, fig9_rel)




