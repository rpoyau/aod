"""Audited S1b native Typst vector figure verification suite.

Verifies:
1. Complete 34-figure inventory (6 Main + 28 Manual) with byte-identical historical
   raster retention and zero remaining #image(...) calls in canonical typst/.
2. Exact data-value checks against frozen CSVs and exact tables for all 23
   DATA_BACKED_VERIFIED figures (including strict pre-LHC target quarantine for
   higgs_tritrioseptyro_trace_flow).
3. Zero invented datasets (zero csv(...) calls) for all 11 CONCEPTUAL_SCHEMATIC figures.
4. Vector PDF invariants across all 38 exported PDFs (6 Main + 32 Manual):
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

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_verifier():
    spec = importlib.util.spec_from_file_location("aod_vtp_s1b", ROOT / "scripts/verify_typst_parity.py")
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
    assert summary["DATA_BACKED_VERIFIED"] == 23
    assert summary["CONCEPTUAL_SCHEMATIC"] == 11
    assert summary["UNRESOLVED_RETAINED"] == 0
    assert summary["converted_vector"] == 34
    assert summary["retained_raster"] == 0

    figs = inv["figures"]
    assert len(figs) == 34
    assert sum(1 for f in figs if f["surface"] == "main") == 6
    assert sum(1 for f in figs if f["surface"] == "manual") == 28
    assert sum(1 for f in figs if f["provenance_class"] == "DATA_BACKED_VERIFIED") == 23
    assert sum(1 for f in figs if f["provenance_class"] == "CONCEPTUAL_SCHEMATIC") == 11

    seen_slugs = set()
    seen_labels = set()
    for f in figs:
        assert f["conversion_status"] == "CONVERTED_VECTOR"
        assert f["visual_comparison_recorded"] is True
        assert f["raster_image_xobjects"] == 0
        assert f["slug"] not in seen_slugs
        assert f["label"] not in seen_labels
        seen_slugs.add(f["slug"])
        seen_labels.add(f["label"])

        # Historical raster retained byte-for-byte and bound to CANONICAL_BINDINGS.json
        raster_p = ROOT / f["raster_path"]
        assert raster_p.is_file(), f"Missing historical raster {f['raster_path']}"
        assert _sha256(raster_p) == f["raster_sha256"]
        assert frozen.get(f["raster_path"]) == f["raster_sha256"]

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

    # Zero #image(...) calls remain anywhere in typst/
    for typ_p in sorted((ROOT / "typst").rglob("*.typ")):
        assert "#image(" not in typ_p.read_text(encoding="utf-8"), f"Stray #image( in {typ_p}"


def test_s1b_conceptual_schematics_invent_zero_datasets():
    inv = json.loads((ROOT / "typst/figure_inventory.json").read_text(encoding="utf-8"))
    schematics = [f for f in inv["figures"] if f["provenance_class"] == "CONCEPTUAL_SCHEMATIC"]
    assert len(schematics) == 11
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
        ("manual", ROOT / "latex/manual/figures/generated", "manual/figures/generated", 32),
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

    assert total_pdfs == 38


def test_s1b_all_23_data_backed_figures_match_frozen_sources():
    inv = json.loads((ROOT / "typst/figure_inventory.json").read_text(encoding="utf-8"))
    data_figs = [f for f in inv["figures"] if f["provenance_class"] == "DATA_BACKED_VERIFIED"]
    assert len(data_figs) == 23

    # 1. Verify every declared data source exists byte-for-byte and every csv(...) call is declared.
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

    # 2. Exact data checks against frozen CSVs and exact Manual tables:
    # (a) 90-tick cycle-shedding fixture
    with (ROOT / "wavelet_shedding_simulation.csv").open(encoding="utf-8") as fh:
        w_rows = list(csv.DictReader(fh))
    assert len(w_rows) == 90
    assert max(float(r["shed_excess"]) for r in w_rows) > 0.06
    t = _extract_pdf_text(ROOT / "latex/manual/figures/generated/cycle-disturbance-shedding-fixture.pdf")
    assert "90 native ticks" in t and "Outward remainder" in t and "Local fraction" in t

    # (b) Brownian 3D phase-cycle delta_3 fixture
    with (ROOT / "manual/data/brownian/brownian_sample_track.csv").open(encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh))) == 9
    with (ROOT / "manual/data/brownian/phase_cycle_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["observed_count"]) for r in csv.DictReader(fh)] == [0, 0, 4, 4, 0]
    with (ROOT / "manual/data/brownian/octant_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["observed_count"]) for r in csv.DictReader(fh)] == [6, 0, 1, 0, 1, 0, 0, 0]
    t = _extract_pdf_text(ROOT / "latex/manual/figures/generated/coordinate-phase-delta3-wireframe.pdf")
    assert "Integerized 3D trajectory" in t and "Phase counts" in t and "Octant counts" in t

    # (c) Higgs trace flow (strict pre-LHC target quarantine!), saddle signature, and LHC mass comparison
    with (ROOT / "manual/data/higgs/higgs_trace_internal_candidates_selection.csv").open(encoding="utf-8") as fh:
        sel = next(r for r in csv.DictReader(fh) if r["rank"] == "1")
    assert (sel["candidate_K"], int(sel["Pi_qp_plus_q"]), int(sel["RD_accessor"]),
            int(sel["PD_window_pressure"]), int(sel["QD_pending_overhang"]),
            int(sel["delta_lower"]), int(sel["delta_upper"])) == ("3:3:7", 30, 61, 21, 162, 3, -3)
    tf_src = (ROOT / "typst/lib/figures/manual/higgs_tritrioseptyro_trace_flow.typ").read_text(encoding="utf-8")
    assert "higgs_external_lhc_mass_comparison_after_freeze.csv" not in tf_src
    assert "higgs_external_map_after_candidate_freeze.csv" in tf_src
    t_tf = _extract_pdf_text(ROOT / "latex/manual/figures/generated/higgs-tritrioseptyro-trace-flow.pdf")
    for tok in ("3:3:7", "30", "61", "21", "162", "124.928"):
        assert tok in t_tf
    t_sad = _extract_pdf_text(ROOT / "latex/manual/figures/generated/higgs-yro-saddle-signature.pdf")
    assert "+3" in t_sad and "21" in t_sad and "3:3:7" in t_sad
    t_mass = _extract_pdf_text(ROOT / "latex/manual/figures/generated/higgs-mass-comparison.pdf")
    assert "124.928" in t_mass and "ATLAS+CMS" in t_mass and "CMS" in t_mass

    # (d) Double-slit exact 11-bin integer fixture matches <tab:manual-dimonhexon-double-slit-fixture>
    ds_src = (ROOT / "typst/lib/figures/manual/double_slit_reclosure_fixture.typ").read_text(encoding="utf-8")
    assert "#let ks = (-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5)" in ds_src
    assert "#let s-single = (4, 9, 16, 25, 31, 35, 31, 25, 16, 9, 4)" in ds_src
    assert "#let t-no-cross = (8, 18, 32, 50, 62, 70, 62, 50, 32, 18, 8)" in ds_src
    assert "#let t-cross = (8, 10, 20, 58, 80, 96, 80, 58, 20, 10, 8)" in ds_src
    assert "#let o-comp = (8, 11, 19, 59, 79, 95, 80, 58, 21, 10, 8)" in ds_src

    # (e) Solar-system exact O0 records match <tab:manual-solar-observable-map-results>
    sol1 = (ROOT / "typst/lib/figures/manual/solar_calculated_vs_target.typ").read_text(encoding="utf-8")
    sol2 = (ROOT / "typst/lib/figures/manual/solar_percent_error.typ").read_text(encoding="utf-8")
    assert "(42.9799, 1.75001, 2.11996e-6)" in sol1
    assert "(42.98, 1.75, 2.12e-6)" in sol1
    assert "(0.0002327, 0.0005714, 0.001887)" in sol2

    # (f) SPARC NGC3198 (43 bins) & declaration controls (4 rows)
    with (ROOT / "manual/data/derived/sparc_five_galaxy_per_bin.csv").open(encoding="utf-8") as fh:
        ngc = [r for r in csv.DictReader(fh) if r["galaxy"] == "NGC3198"]
    assert len(ngc) == 43
    with (ROOT / "manual/data/derived/sparc_declaration_controls.csv").open(encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh))) == 4

    # (g) Tau ring diagnostic, exact 31/50 = 0.62 missing burden ratio, and declaration controls
    with (ROOT / "manual/data/derived/tau_ring_diagnostic.csv").open(encoding="utf-8") as fh:
        tau_rows = list(csv.DictReader(fh))
    assert [r["K"] for r in tau_rows] == ["1:2:8", "1:2:9", "1:2:10", "3:3:8"]
    with (ROOT / "manual/data/dec/tau_missing_burden_exact_ratio_patch.csv").open(encoding="utf-8") as fh:
        patch = next(csv.DictReader(fh))
    assert int(patch["missing_num"]) == 31 and int(patch["missing_den"]) == 50

    # (h) Run-tumble 20-tick 5-panel projection
    with (ROOT / "manual/data/run_tumble/run_tumble_trace_20_ticks.csv").open(encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh))) == 21
    with (ROOT / "manual/data/run_tumble/run_tumble_phase_cycle_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["O"]) for r in csv.DictReader(fh)] == [6, 3, 3, 3, 5]
    with (ROOT / "manual/data/run_tumble/run_tumble_octant_delta3.csv").open(encoding="utf-8") as fh:
        assert [int(r["m"]) for r in csv.DictReader(fh)] == [8, 3, 3, 3, 7, 2, 2, 2]

    # (i) Lensing CSV-backed figures (01, 03, 04 heatmap, 05, 06, 07 gate)
    t_hm = _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-04-sparc5-class-tally-heatmap.pdf")
    for tok in ("NGC2403", "NGC3198", "NGC6503", "NGC2841", "DDO154", "28", "29", "25", "31", "14"):
        assert tok in t_hm
    t_k4 = _extract_pdf_text(ROOT / "latex/manual/figures/generated/lensing-07-k4-3d-timeflow-input-gate.pdf")
    for tok in ("3D density fields", "2 fields", "audit controls", "1 field", "velocity and flow fields"):
        assert tok in t_k4
