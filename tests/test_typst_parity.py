"""Pytest integration for M4 Objective 1 native Typst migration parity gates."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _find_typst_or_none() -> str | None:
    builder = _load_module("aod_build_typst", "scripts/build_typst.py")
    try:
        return builder.find_typst(None)
    except FileNotFoundError:
        return None


def test_typst_baseline_immutability_and_narrow_engineering_amendments():
    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))
    res = vp.verify_baseline_immutability(ROOT, manifest)
    assert res["protected_baseline_files"] == 211
    assert res["tex_files_unchanged"] == 54
    assert res["bib_files_unchanged"] == 2
    assert res["image_files_unchanged"] == 49
    assert res["manual_data_files_unchanged"] == 116


def test_typst_complete_active_graph_equations_tables_prose_and_qualifiers():
    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))
    res = vp.verify_source_and_content_parity(ROOT, manifest)
    assert res["active_main_tex_files"] == 21
    assert res["active_manual_tex_files"] == 27
    assert res["active_files_mapped"] == 48
    assert len(res["immutable_tables_verified_cell_by_cell"]) == 7
    assert res["labeled_equations_verified_structurally"] == {"main": 198, "manual": 20}
    assert res["prose_and_qualifier_files_verified"] == 43


def test_typst_source_negative_controls_reject_mutations(tmp_path):
    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))

    def make_tree(dest: Path) -> Path:
        for d in ("sections", "appendices", "typst"):
            shutil.copytree(ROOT / d, dest / d)
        for f in ("main.tex", "preamble.tex", "refs.bib", "cycle_shedding_summary.tex"):
            shutil.copy2(ROOT / f, dest / f)
        (dest / "manual").mkdir()
        for f in ("main.tex", "preamble.tex", "refs.bib"):
            shutil.copy2(ROOT / "manual" / f, dest / "manual" / f)
        for d in ("sections", "appendices"):
            shutil.copytree(ROOT / "manual" / d, dest / "manual" / d)
        for tbl in vp.IMMUTABLE_MANUAL_TABLES:
            t_dst = dest / tbl
            t_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / tbl, t_dst)
        return dest

    base = make_tree(tmp_path / "base")

    # 1a. Changed exact table value
    t1 = tmp_path / "c1a"
    shutil.copytree(base, t1)
    p = t1 / "typst/manual/tables/sparc_summary_table.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("10893.83", "10893.84", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Table cell parity mismatch"):
        vp.verify_source_and_content_parity(t1, manifest)

    # 1b. Changed equation exponent
    t2 = tmp_path / "c1b"
    shutil.copytree(base, t2)
    p = t2 / "typst/sections/03_afc_basis.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("iota^2", "iota^3", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Equation structure mismatch"):
        vp.verify_source_and_content_parity(t2, manifest)

    # 2. Removed scientific qualification
    t3 = tmp_path / "c2"
    shutil.copytree(base, t3)
    p = t3 / "typst/sections/04_cut_running_fractal_tesseract.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("never", "", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Scientific qualifier"):
        vp.verify_source_and_content_parity(t3, manifest)

    # 3. Omitted active table
    t4 = tmp_path / "c3"
    shutil.copytree(base, t4)
    p = t4 / "typst/manual/sections/06_field_dynamics_applications.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace('#include "../tables/sparc_summary_table.typ"', "", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not included"):
        vp.verify_source_and_content_parity(t4, manifest)


def test_typst_evaluated_build_pdfs_and_compiler_negative_controls(tmp_path):
    typst_bin = _find_typst_or_none()
    if typst_bin is None or shutil.which("pdftotext") is None:
        pytest.skip("typst and pdftotext are required for evaluated Typst build/PDF parity controls")
    pytest.importorskip("pypdf")

    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    outdir = tmp_path / "typst_eval"
    res = vp.verify_evaluated_and_rendered(ROOT, typst_bin, outdir)
    assert res["main_labels_verified"] == 455
    assert res["manual_labels_verified"] == 227
    assert res["manual_mainrefs_verified"] == 172
    assert res["main_bib_entries"] == 10
    assert res["manual_bib_entries"] == 43
    assert res["pdf_stats"]["main"]["internal_links"] >= 500
    assert res["pdf_stats"]["manual"]["main_pdf_links"] >= 172

    neg = vp.run_negative_controls(ROOT, typst_bin)
    assert all(item["rejected"] is True for item in neg.values())
    assert {
        "1a_changed_table_value",
        "1b_changed_equation_exponent",
        "2_removed_qualification",
        "3_omitted_active_table",
        "4_wrong_reference_target_type",
        "5_stale_main_registry",
    } <= set(neg)


def test_typst_parity_cli_normal_and_optimized_agree(tmp_path):
    typst_bin = _find_typst_or_none()
    if typst_bin is None or shutil.which("pdftotext") is None:
        pytest.skip("typst and pdftotext are required for CLI normal/-O parity check")
    pytest.importorskip("pypdf")

    out_norm = tmp_path / "norm"
    out_opt = tmp_path / "opt"
    for py_flags, outdir in (([], out_norm), (["-O"], out_opt)):
        cmd = [
            sys.executable, *py_flags, str(ROOT / "scripts/verify_typst_parity.py"),
            "--outdir", str(outdir), "--typst-bin", typst_bin, "--skip-negative-controls",
        ]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
    assert (out_norm / "parity_report.json").read_bytes() == (out_opt / "parity_report.json").read_bytes()
