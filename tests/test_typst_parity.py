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
    assert res["ordered_content_files_verified"] == 44
    assert res["ordered_tokens_verified"] >= 43000
    assert res["all_math_asts_verified"] >= 2900
    assert res["literal_code_tokens_verified"] >= 100
    assert res["unsupported_math_constructs"] == 0
    assert len(res["immutable_tables_verified_cell_by_cell"]) == 7
    assert res["labeled_equations_verified_structurally"] == {"main": 198, "manual": 20}
    assert res["flowcharts_verified"] == 4
    assert res["figure_image_bindings_verified"] == 34


def test_build_typst_manual_digest_includes_nested_figure_subdirectories():
    bt = _load_module("aod_build_typst", "scripts/build_typst.py")
    _, rel_files = bt.compute_manual_sources_digest(ROOT)
    rel_set = set(rel_files)
    assert "manual/figures/higgs/higgs_yro_saddle_signature.png" in rel_set
    assert "manual/figures/lensing/05_swells_k_comparison_delta3.png" in rel_set
    manual_figs = [p for p in rel_files if p.startswith("manual/figures/")]
    assert len(manual_figs) == 31


def test_typst_evaluation_policy_pins_templates_and_constrains_content():
    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))
    res = vp.verify_typst_evaluation_policy(ROOT, manifest)
    assert res["trusted_template_files_pinned"] == 5
    assert res["manifest_typst_digests_enforced"] == 48
    assert res["content_files_policy_checked"] == 44
    assert res["content_policy_violations"] == 0

    head = '#import "../preamble.typ": *\n'
    rejected = {
        "show_string": '#show "19": "91"\nText 19.\n',
        "show_in_code_block": '#{ show "a": "b"; [x] }\n',
        "white_text": "#text(fill: white)[no] physical.\n",
        "hide": "#hide[no] physical\n",
        "math_hide": "$ hide(x) + 1 $\n",
        "math_std_hide": "$ std.hide(x) + 1 $\n",
        "math_recolour": "$ text(fill: white, -) x $\n",
        "let_binding": "#let x = 3\n",
        "set_page_fill": "#set page(fill: red)\n",
        "set_text_fill": "#set text(fill: white)\n",
        "negative_space": "#v(-2em) text\n",
        "tiny_text": "#text(size: 1pt)[no] text\n",
        "place_overlay": "#place(top)[x]\n",
        "rect_overlay": "#block(width: 100%)[#rect(fill: white)]\n",
        "raw_box_in_content": '#box(stroke: 0.5pt + black, inset: 4pt)[$ x $]\n',
        "foreign_import": '#import "evil.typ": *\n',
        "context": "#context [x]\n",
        "eval": '#eval("1+1")\n',
        "hide_in_nested_math": "$ #aod-boxed($ x #hide[y] $) $\n",
        "argument_spread": "#block(..(clip: true, height: 0pt))[No]\n",
        "paren_callee": "#(hide)[No]\n",
        "zero_pad": "#pad(left: 0em)[x]\n",
        "flowchart_out_of_bounds": (
            '#aod-flowchart(width: 10.0cm, height: 5.0cm, '
            '((id: "a", x: 5.0cm, y: 12.0cm, w: 2.0cm, h: 1.0cm, body: [A]),), ())\n'
        ),
    }
    for name, body in rejected.items():
        violations, _ = vp._content_policy_violations("typst/sections/x.typ", head + body, set())
        assert violations, name
    accepted = {
        "figure_image": '#figure(image("/figures/a.png", width: 80%), caption: [A])\n',
        "prose_math_ref": 'Some *strong* text with $a_(b)^2 = sum_(i) x_i$ and #eqref("eq:x").\n',
        "boxed_display_math": '#aod-boxed($ display(K_(tau)^(star) = 1) $)\n',
        "in_bounds_flowchart": (
            '#aod-flowchart(width: 10.0cm, height: 5.0cm, '
            '((id: "a", x: 5.0cm, y: 1.0cm, w: 3.0cm, h: 1.0cm, body: [A]), '
            '(id: "b", x: 5.0cm, y: 3.5cm, w: 3.0cm, h: 1.0cm, body: [B])), '
            '((from: "a", to: "b"),))\n'
        ),
    }
    for name, body in accepted.items():
        violations, _ = vp._content_policy_violations("typst/sections/x.typ", head + body, set())
        assert violations == [], (name, violations)


def test_typst_rendered_gate_helpers():
    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    vocab = {"retention", "line", "break", "phase", "type", "phasetype"}
    assert vp._dehyphenate_with_vocab("reten-\ntion", vocab) == "retention"
    assert vp._dehyphenate_with_vocab("line-\nbreak", vocab) == "line break"
    assert vp._dehyphenate_with_vocab("phase-\ntype", vocab) == "phasetype"
    runs = vp._vocab_runs(["line", "break", "x", "phase", "type", "retention", "line"], vocab)
    assert runs == [["line", "break"], ["phase", "type", "retention", "line"]]
    assert vp._run_ngrams(runs) == ["phase type retention line"]
    assert vp._rendered_body("Contents\nReferences\nbody text\nReferences\n[1] x") == "Contents\nReferences\nbody text"
    # Ligatures decompose on both sides; Typst math-alphanumeric words are counted as math tokens.
    assert vp._norm_rendered_text_tokens("Adm\ufb01b coe\ufb00icient", is_typst=False) == "Admfib coefficient"
    counts = vp._typst_math_word_counts("supp\U0001d463\u0302 \u2286 \U0001d43b and support Admfib")
    assert counts == {"suppv": 1, "H": 1}


def test_typst_source_negative_controls_reject_mutations(tmp_path):
    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))

    def make_tree(dest: Path) -> Path:
        for d in ("sections", "appendices", "typst", "scripts"):
            shutil.copytree(ROOT / d, dest / d, ignore=shutil.ignore_patterns("__pycache__"))
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
        shutil.copytree(ROOT / "figures_jpg", dest / "figures_jpg")
        shutil.copytree(ROOT / "manual" / "figures", dest / "manual" / "figures")
        return dest

    base = make_tree(tmp_path / "base")

    # 1a. Changed exact table value
    t1 = tmp_path / "c1a"
    shutil.copytree(base, t1)
    p = t1 / "typst/manual/tables/sparc_summary_table.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("10893.83", "10893.84", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Table cell parity mismatch"):
        vp.verify_source_and_content_parity(t1, manifest)

    # 1b. Changed labeled-equation exponent
    t2 = tmp_path / "c1b"
    shutil.copytree(base, t2)
    p = t2 / "typst/sections/03_afc_basis.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("iota^2", "iota^3", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Equation structure mismatch"):
        vp.verify_source_and_content_parity(t2, manifest)

    # 2. Removed scientific qualification ('never')
    t3 = tmp_path / "c2"
    shutil.copytree(base, t3)
    p = t3 / "typst/sections/04_cut_running_fractal_tesseract.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("never", "", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
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

    # 6. Review counterexample #1: removed short negation ('no' -> 'a')
    t6 = tmp_path / "c6"
    shutil.copytree(base, t6)
    p = t6 / "typst/manual/sections/02_mapping_error.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            "This example has no physical discrepancy model",
            "This example has a physical discrepancy model",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        vp.verify_source_and_content_parity(t6, manifest)

    # 7. Review counterexample #2: changed inline integer (f(x)=2x -> f(x)=3x)
    t7 = tmp_path / "c7"
    shutil.copytree(base, t7)
    p = t7 / "typst/manual/sections/02_mapping_error.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace("$f(x) = 2 x$", "$f(x) = 3 x$", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        vp.verify_source_and_content_parity(t7, manifest)

    # 8. Review counterexample #3: changed equation grouping (1/(1-a^2) -> 1/(1-a)^2)
    t8 = tmp_path / "c8"
    shutil.copytree(base, t8)
    p = t8 / "typst/manual/sections/02_mapping_error.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            "bb(E)[U] = frac(1, 1 - a^2)",
            "bb(E)[U] = frac(1, (1 - a)^2)",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Equation structure mismatch"):
        vp.verify_source_and_content_parity(t8, manifest)

    # C1.1 & C1.2 regressions: corrupted CLI flag and swallowed semicolon
    t_cli = tmp_path / "c_cli"
    shutil.copytree(base, t_cli)
    p = t_cli / "typst/manual/sections/00_awareness_fixtures.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace("--check-data", "\u2013check-data", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        vp.verify_source_and_content_parity(t_cli, manifest)

    t_semi = tmp_path / "c_semi"
    shutil.copytree(base, t_semi)
    p = t_semi / "typst/sections/03_afc_basis.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            '#secref("sec:closure-phase-wave")\\;',
            '#secref("sec:closure-phase-wave");',
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch|Unescaped semicolon"):
        vp.verify_source_and_content_parity(t_semi, manifest)

    # R02 R4: two figure image paths swapped (captions unchanged) -> ordered image bindings.
    t_img = tmp_path / "c_img"
    shutil.copytree(base, t_img)
    p = t_img / "typst/manual/sections/01_rest_energy_prediction.typ"
    a_img = "/manual/figures/higgs/higgs_yro_saddle_signature.png"
    b_img = "/manual/figures/higgs/higgs_tritrioseptyro_trace_flow.png"
    txt = p.read_text(encoding="utf-8")
    p.write_text(txt.replace(a_img, "@@A@@").replace(b_img, a_img).replace("@@A@@", b_img), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        vp.verify_source_and_content_parity(t_img, manifest)

    # R02 R3: show rule inside an immutable table -> evaluation policy (digest re-pinned).
    t_r3 = tmp_path / "c_r3"
    shutil.copytree(base, t_r3)
    rel = "typst/manual/tables/swells_k0_target_tallies_table.typ"
    p = t_r3 / rel
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            "  set par(justify: false)\n", '  set par(justify: false)\n  show "19": "91"\n', 1
        ),
        encoding="utf-8",
    )
    m2 = json.loads(json.dumps(manifest))
    for e in m2["active_source_map"]:
        if e["typst_target"] == rel:
            e["typst_sha256"] = vp.sha256_file(p)
    with pytest.raises(ValueError, match="forbidden `show`"):
        vp.verify_typst_evaluation_policy(t_r3, m2)
    with pytest.raises(ValueError, match="Typst unit digest differs"):
        vp.verify_typst_evaluation_policy(t_r3, manifest)

    # R03 conversion fidelity: emptyset->diameter, matrix augment, bar->overline, bold italic, flowchart edge/math.
    t_sym = tmp_path / "c_sym"
    shutil.copytree(base, t_sym)
    p = t_sym / "typst/sections/08_awareness_learning_mindfulness.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("emptyset", "diameter", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="diameter"):
        vp.verify_source_and_content_parity(t_sym, manifest)

    t_mat = tmp_path / "c_mat"
    shutil.copytree(base, t_mat)
    p = t_mat / "typst/manual/appendices/A_simulation_fixtures_and_tau_prediction_context.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace("augment: #1, ", "", 1), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        vp.verify_source_and_content_parity(t_mat, manifest)

    t_bar = tmp_path / "c_bar"
    shutil.copytree(base, t_bar)
    p = t_bar / "typst/sections/06_field.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("macron(e)", "overline(e)", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch|Equation structure mismatch"):
        vp.verify_source_and_content_parity(t_bar, manifest)

    t_bf = tmp_path / "c_bf"
    shutil.copytree(base, t_bf)
    p = t_bf / "typst/sections/03_afc_basis.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("bold(upright(a))", "bold(a)", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch|Equation structure mismatch"):
        vp.verify_source_and_content_parity(t_bf, manifest)

    t_fc = tmp_path / "c_fc"
    shutil.copytree(base, t_fc)
    p = t_fc / "typst/manual/sections/02_hydrogen_facing_shell_tests.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace('(from: "scope", to: "shells")', '(from: "shells", to: "scope")', 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="FLOWCHART"):
        vp.verify_source_and_content_parity(t_fc, manifest)


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
    assert res["equation_numbering"]["main"]["numbered_block_equations"] == 187
    assert res["equation_numbering"]["main"]["unlabeled_numbered_equations"] == 0
    assert res["equation_numbering"]["manual"]["numbered_block_equations"] == 19
    assert res["equation_numbering"]["manual"]["unlabeled_numbered_equations"] == 0
    assert res["manual_mainrefs_verified"] == 172
    assert res["main_bib_entries"] == 10
    assert res["manual_bib_entries"] == 43
    assert res["cli_commands_verified_verbatim"] >= 9
    assert res["pdf_stats"]["main"]["internal_links"] >= 500
    assert res["pdf_stats"]["manual"]["peer_pdf_links"] >= 172

    delivery = res["delivered_peer_pdf_verification"]
    assert delivery["delivered_peer_pdf"] == "main_typst.pdf"
    assert delivery["peer_pdf_sha256_verified"] is True
    assert delivery["stale_main_pdf_links"] == 0
    assert delivery["all_target_page_anchors_verified"] == 172
    assert delivery["witness_main_eq33"]["pdf_destination"].startswith("main_typst.pdf#page=")

    paint = res["rendered_text_paint"]
    for surf in ("main", "manual"):
        assert paint[surf]["non_black_or_invisible"] == 0
        assert paint[surf]["min_font_size"] >= 4.0
        assert paint[surf]["alpha_and_clip_checked"] is True
        clauses = res["baseline_pdf_comparison"]["rendered_prose_clauses_typst_only"][surf]
        assert clauses["unverified"] == 0

    neg = vp.run_negative_controls(ROOT, typst_bin)
    baseline_only = {"11b_R1c_rendered_insertion", "12b_R2b_rendered_glyph_parity", "16b_R6_rendered_clause"}
    for name, item in neg.items():
        if name in baseline_only:
            assert item["rejected"] is None and "baseline" in item["skipped"], name
        else:
            assert item["rejected"] is True, name
    assert {
        "1a_changed_table_value",
        "1b_changed_equation_exponent",
        "2_removed_qualification",
        "3_omitted_active_table",
        "4_wrong_reference_target_type",
        "5_stale_main_registry",
        "6_removed_short_negation",
        "7_changed_inline_integer",
        "8_changed_equation_grouping",
        "9_show_rule_rendered_mutation",
        "10_wrong_peer_pdf_filename",
        "11a_R1c_template_pin",
        "12a_R2b_template_pin",
        "13_R3_table_show_rule_policy",
        "14_R4_figure_image_swap",
        "15a_R5_white_text_policy",
        "15b_R5_white_text_paint_scan",
        "16a_R6_content_show_policy",
        "17_spurious_boxed_eq_number",
        "18_symbol_emptyset_to_diameter",
        "19_matrix_augment_removed",
        "20a_flowchart_edge_reversed",
        "20b_flowchart_math_mutated",
        "20c_flowchart_out_of_bounds_overlay",
        "21a_spread_hidden_block_policy",
        "21b_transparent_luma_paint_scan",
    } | baseline_only == set(neg)


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
    report = json.loads((out_norm / "parity_report.json").read_text(encoding="utf-8"))
    assert report["schema"] == "aod.typst.parity-report.v2"
    assert report["verdict"] == "PARTIAL_NON_ACCEPTANCE_MISSING_BASELINE_PDFS"
