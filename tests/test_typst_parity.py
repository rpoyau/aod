"""Pytest integration for M4 Objective 1 native Typst migration parity gates."""
from __future__ import annotations

import hashlib
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
    assert res["trusted_template_files_pinned"] == 6
    assert res["diagram_components_pinned"] == 4
    assert res["vector_figure_components_pinned"] == 34
    assert res["manifest_typst_digests_enforced"] == 48
    assert res["content_files_policy_checked"] == 82
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
    mat = _load_module("aod_materialize_latex_baseline", "scripts/materialize_latex_baseline.py")
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))

    b_root = tmp_path / "baseline_98ddfa0"
    mat.materialize_baseline(ROOT, b_root)

    def make_tree(dest: Path) -> Path:
        for d in ("typst", "scripts"):
            shutil.copytree(ROOT / d, dest / d, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "refs.bib", dest / "refs.bib")
        (dest / "manual").mkdir()
        shutil.copy2(ROOT / "manual" / "refs.bib", dest / "manual" / "refs.bib")
        shutil.copytree(ROOT / "figures_jpg", dest / "figures_jpg")
        shutil.copytree(ROOT / "manual" / "figures", dest / "manual" / "figures")
        return dest

    def check_src(tree: Path):
        return vp.verify_source_and_content_parity(
            tree, manifest, baseline_root=b_root, check_generated_latex=False
        )

    base = make_tree(tmp_path / "base")

    # 1a. Changed exact table value
    t1 = tmp_path / "c1a"
    shutil.copytree(base, t1)
    p = t1 / "typst/manual/tables/sparc_summary_table.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("10893.83", "10893.84", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Table cell parity mismatch"):
        check_src(t1)

    # 1b. Changed labeled-equation exponent
    t2 = tmp_path / "c1b"
    shutil.copytree(base, t2)
    p = t2 / "typst/sections/03_afc_basis.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("iota^2", "iota^3", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Equation structure mismatch"):
        check_src(t2)

    # 2. Removed scientific qualification ('never')
    t3 = tmp_path / "c2"
    shutil.copytree(base, t3)
    p = t3 / "typst/sections/04_cut_running_fractal_tesseract.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("never", "", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        check_src(t3)

    # 3. Omitted active table
    t4 = tmp_path / "c3"
    shutil.copytree(base, t4)
    p = t4 / "typst/manual/sections/06_field_dynamics_applications.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace('#include "../tables/sparc_summary_table.typ"', "", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not included"):
        check_src(t4)

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
        check_src(t6)

    # 7. Review counterexample #2: changed inline integer (f(x)=2x -> f(x)=3x)
    t7 = tmp_path / "c7"
    shutil.copytree(base, t7)
    p = t7 / "typst/manual/sections/02_mapping_error.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace("$f(x) = 2 x$", "$f(x) = 3 x$", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        check_src(t7)

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
        check_src(t8)

    # C1.1 & C1.2 regressions: corrupted CLI flag and swallowed semicolon
    t_cli = tmp_path / "c_cli"
    shutil.copytree(base, t_cli)
    p = t_cli / "typst/manual/sections/00_awareness_fixtures.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace("--check-data", "\u2013check-data", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        check_src(t_cli)

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
        check_src(t_semi)

    # R02 R4: two figure bindings swapped (captions unchanged) -> ordered image bindings.
    t_img = tmp_path / "c_img"
    shutil.copytree(base, t_img)
    p = t_img / "typst/manual/sections/01_rest_energy_prediction.typ"
    a_img = "../../lib/figures/manual/higgs_yro_saddle_signature.typ"
    b_img = "../../lib/figures/manual/higgs_tritrioseptyro_trace_flow.typ"
    txt = p.read_text(encoding="utf-8")
    p.write_text(txt.replace(a_img, "@@A@@").replace(b_img, a_img).replace("@@A@@", b_img), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        check_src(t_img)

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
        check_src(t_sym)

    t_mat = tmp_path / "c_mat"
    shutil.copytree(base, t_mat)
    p = t_mat / "typst/manual/appendices/A_simulation_fixtures_and_tau_prediction_context.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace("augment: #1, ", "", 1), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch"):
        check_src(t_mat)

    t_bar = tmp_path / "c_bar"
    shutil.copytree(base, t_bar)
    p = t_bar / "typst/sections/06_field.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("macron(e)", "overline(e)", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch|Equation structure mismatch"):
        check_src(t_bar)

    t_bf = tmp_path / "c_bf"
    shutil.copytree(base, t_bf)
    p = t_bf / "typst/sections/03_afc_basis.typ"
    p.write_text(p.read_text(encoding="utf-8").replace("bold(upright(a))", "bold(a)", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Ordered content/math parity mismatch|Equation structure mismatch"):
        check_src(t_bf)

    t_fc = tmp_path / "c_fc"
    shutil.copytree(base, t_fc)
    p = t_fc / "typst/lib/diagrams/hydrogen_shell_setup.typ"
    p.write_text(
        p.read_text(encoding="utf-8").replace('(from: "scope", to: "shells")', '(from: "shells", to: "scope")', 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="FLOWCHART"):
        check_src(t_fc)


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
    assert delivery["delivered_peer_pdf"] == "main.pdf"
    assert delivery["peer_pdf_sha256_verified"] is True
    assert delivery["stale_peer_pdf_links"] == 0
    assert delivery["all_target_page_anchors_verified"] == 172
    assert delivery["witness_main_eq33"]["pdf_destination"].startswith("main.pdf#page=")

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
        "22a_R1_ledger_historical_old_hash",
        "22b_R1_ledger_duplicate_entry",
        "22c_R1_ledger_substituted_origin",
        "22d_R1_undeclared_contract_transition",
        "23a_R2_generated_boundary_glued",
        "23b_R3_generated_bookmark_stripped",
        "24_R5_missing_gotor_peer_destination",
        "24a_S1b_vector_figure_show_rule",
        "24b_S1b_vector_figure_unauthorized_csv",
        "24c_S1b_vector_figure_dynamic_csv",
        "24d_S1b_vector_figure_nonwildcard_import",
        "24e_S1b_vector_figure_alias_csv_and_read",
        "24f_S1b_vector_figure_bracket_import_and_set",
        "24g_S1b_pdf_raster_xobject_injection",
        "25_R6_unsupported_syntax_line_number",
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
    assert report["typ2tex_compatibility_status"] == "PARTIAL_SOURCE_ONLY_GENERATED_PDFS_NOT_VERIFIED"
    assert report["canonical_source_promotion"] == "PARTIAL_NOT_ACCEPTED"
    assert report["coverage"]["generated_latex"]["source_tree_verified"] is True
    assert report["coverage"]["generated_latex"]["source_freshness_check_passed"] is True
    assert report["coverage"]["generated_latex"]["pdfs_supplied_and_verified"] is False
    assert report["coverage"]["provenance_and_controls"]["phase1_transition_verified"] is True
    assert "baseline_pdfs" in report["coverage"]["missing_acceptance_requirements"]
    assert "generated_latex_pdfs" in report["coverage"]["missing_acceptance_requirements"]


def test_phase2_baseline_snapshot_verify_and_materialize(tmp_path):
    mat = _load_module("aod_materialize_latex_baseline", "scripts/materialize_latex_baseline.py")
    manifest = mat.load_and_verify_baseline(ROOT)
    assert manifest["historical_scientific_baseline_commit"] == "98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3"
    assert len(manifest["entries"]) == 211
    out = tmp_path / "mat_baseline"
    summary = mat.materialize_baseline(ROOT, out)
    assert summary["materialized_files"] == 211
    for entry in manifest["entries"]:
        p = out / entry["original_path"]
        assert p.is_file()
        assert mat.sha256_file(p) == entry["sha256"]


def test_phase2_export_typst_figures_vector_pdf_determinism_and_png(tmp_path):
    typst_bin = _find_typst_or_none()
    if typst_bin is None:
        pytest.skip("typst is required for native diagram export tests")
    pytest.importorskip("pypdf")

    exp = _load_module("aod_export_typst_figures", "scripts/export_typst_figures.py")
    out1 = tmp_path / "pdf1"
    out2 = tmp_path / "pdf2"
    rt1: dict = {}
    rt2: dict = {}
    m1 = exp.export_figures(ROOT, out1, fmt="pdf", typst_bin=typst_bin, runtime_out=rt1)
    m2 = exp.export_figures(ROOT, out2, fmt="pdf", typst_bin=typst_bin, runtime_out=rt2)
    assert len(m1["figures"]) == 32
    assert m1 == m2
    assert "typst_version" not in m1
    assert "removed_outputs" not in m1
    assert m1["background"] == "white"
    assert isinstance(m1["font_families"], dict)
    assert rt1["typst_version"] and rt1["pypdf_version"]
    assert len(rt1["figures"]) == 32
    for d, rtd in zip(m1["figures"], rt1["figures"]):
        assert d["page_count"] == 1
        assert d["raster_image_xobjects"] == 0
        assert d["has_extractable_text"] is True
        assert "extracted_text_chars" not in d
        assert rtd["extracted_text_chars"] > 0
        assert isinstance(rtd["resolved_fonts"], list) and len(rtd["resolved_fonts"]) > 0
        p1 = out1 / d["output_filename"]
        p2 = out2 / d["output_filename"]
        assert p1.read_bytes() == p2.read_bytes()

    # Main vector figure export determinism (6 Main vector figures)
    out_m1 = tmp_path / "main_pdf1"
    out_m2 = tmp_path / "main_pdf2"
    mm1 = exp.export_figures(ROOT, out_m1, surface="main", fmt="pdf", typst_bin=typst_bin)
    mm2 = exp.export_figures(ROOT, out_m2, surface="main", fmt="pdf", typst_bin=typst_bin)
    assert len(mm1["figures"]) == 6
    assert mm1 == mm2
    for d in mm1["figures"]:
        assert d["page_count"] == 1 and d["raster_image_xobjects"] == 0
        assert (out_m1 / d["output_filename"]).read_bytes() == (out_m2 / d["output_filename"]).read_bytes()

    # Optional raster PNG export path (300 ppi) on Main (6 figures)
    out_png = tmp_path / "png300"
    m_png = exp.export_figures(ROOT, out_png, surface="main", fmt="png", ppi=300, typst_bin=typst_bin)
    assert len(m_png["figures"]) == 6
    for d in m_png["figures"]:
        assert d["output_filename"].endswith(".png")
        assert (out_png / d["output_filename"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_phase2_typ2tex_clean_room_determinism_propagation_and_fail_closed(tmp_path):
    typst_bin = _find_typst_or_none()
    if typst_bin is None:
        pytest.skip("typst is required for typ2tex clean-room and propagation tests")
    pytest.importorskip("pypdf")

    t2t = _load_module("aod_typ2tex", "scripts/typ2tex.py")

    # 1. Clean-room sandbox with ZERO .tex files anywhere (proves C2: never reads archived/historical TeX)
    sb = tmp_path / "clean_room"
    sb.mkdir()
    shutil.copytree(ROOT / "typst", sb / "typst")
    shutil.copytree(ROOT / "figures_jpg", sb / "figures_jpg")
    shutil.copy2(ROOT / "wavelet_shedding_simulation.csv", sb / "wavelet_shedding_simulation.csv")
    (sb / "manual").mkdir()
    shutil.copytree(ROOT / "manual/figures", sb / "manual/figures")
    shutil.copytree(ROOT / "manual/data", sb / "manual/data", ignore=shutil.ignore_patterns("*.tex"))
    shutil.copy2(ROOT / "refs.bib", sb / "refs.bib")
    shutil.copy2(ROOT / "manual/refs.bib", sb / "manual/refs.bib")
    (sb / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/typ2tex.py", sb / "scripts/typ2tex.py")
    shutil.copy2(ROOT / "scripts/export_typst_figures.py", sb / "scripts/export_typst_figures.py")
    assert list(sb.rglob("*.tex")) == []

    gen_dir = sb / "latex"
    rt_init: dict = {}
    t2t.generate_latex_tree(sb, gen_dir, check_only=False, typst_bin=typst_bin, runtime_out=rt_init)
    # Clean-room generated tree must match committed latex/ byte-for-byte
    t2t._verify_trees_match(gen_dir, ROOT / "latex")
    manifest_text = (gen_dir / "GENERATION_MANIFEST.json").read_text(encoding="utf-8")
    assert "removed_outputs" not in json.loads(manifest_text)

    # 2. Determinism and --check pass (read-only)
    t2t.generate_latex_tree(sb, gen_dir, check_only=True, typst_bin=typst_bin)

    # 3. Stale output removal & drift detection via --check (reported in runtime_out, NOT manifest)
    stale = gen_dir / "sections/99_stale_artifact.tex"
    stale.write_text("% stale\n", encoding="utf-8")
    with pytest.raises(ValueError):
        t2t.generate_latex_tree(sb, gen_dir, check_only=True, typst_bin=typst_bin)
    assert stale.exists()  # --check must remain strictly read-only
    rt_clean: dict = {}
    t2t.generate_latex_tree(sb, gen_dir, check_only=False, typst_bin=typst_bin, runtime_out=rt_clean)
    assert not stale.exists()
    assert "sections/99_stale_artifact.tex" in rt_clean["removed_outputs"]
    assert (gen_dir / "GENERATION_MANIFEST.json").read_text(encoding="utf-8") == manifest_text

    # 4. Prose, equation exponent, and table value edits propagate directly into generated latex/
    p_abs = sb / "typst/sections/01_abstract.typ"
    p_abs.write_text(p_abs.read_text(encoding="utf-8") + "\nPHASE2PROSEPROBETOKEN\n", encoding="utf-8")
    p_eq = sb / "typst/sections/03_afc_basis.typ"
    p_eq.write_text(p_eq.read_text(encoding="utf-8").replace("iota^2", "iota^9", 1), encoding="utf-8")
    p_tbl = sb / "typst/manual/tables/sparc_summary_table.typ"
    p_tbl.write_text(p_tbl.read_text(encoding="utf-8").replace("10893.83", "99999.99", 1), encoding="utf-8")
    t2t.generate_latex_tree(sb, gen_dir, check_only=False, typst_bin=typst_bin)
    assert "PHASE2PROSEPROBETOKEN" in (gen_dir / "sections/01_abstract.tex").read_text(encoding="utf-8")
    assert r"\iota^9" in (gen_dir / "sections/03_afc_basis.tex").read_text(encoding="utf-8")
    assert "99999.99" in (gen_dir / "manual/data/derived/sparc_summary_table.tex").read_text(encoding="utf-8")

    # 5. Unsupported construct fails closed with exact real source file:line location (not :1)
    orig_eq = p_eq.read_text(encoding="utf-8")
    expected_line = orig_eq.count("\n") + 2
    assert expected_line > 150
    p_eq.write_text(orig_eq + "\n#unsupported-magic-widget(1)\n", encoding="utf-8")
    with pytest.raises(ValueError, match=rf"typst/sections/03_afc_basis\.typ:{expected_line}\b"):
        t2t.generate_latex_tree(sb, gen_dir, check_only=False, typst_bin=typst_bin)


def test_phase2_r1_transition_provenance_git_and_nongit_controls(tmp_path):
    """R1 finite acceptance: dual-relation Gate A passes in Git & non-Git and rejects provenance tampering."""
    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")
    manifest = json.loads((ROOT / "typst/manifest.json").read_text(encoding="utf-8"))

    # 1. Git-backed repo passes both relations
    res_git = vp.verify_baseline_immutability(ROOT, manifest)
    assert res_git["historical_baseline_preservation_verified"] is True
    assert res_git["phase1_transition_verified"] is True
    assert res_git["phase1_accepted_commit"] == vp.PHASE1_ACCEPTED_COMMIT

    # 2. Non-Git copy (no .git directory, zero symlinks) verifies the exact same transition independently
    def make_nongit(dest: Path) -> Path:
        shutil.copytree(
            ROOT,
            dest,
            ignore=shutil.ignore_patterns(".git", "dist_typst", "_build", "__pycache__", "latex"),
        )
        assert not (dest / ".git").exists()
        return dest

    ng_clean = make_nongit(tmp_path / "nongit_clean")
    res_ng = vp.verify_baseline_immutability(ng_clean, manifest)
    assert res_ng["historical_baseline_preservation_verified"] is True
    assert res_ng["phase1_transition_verified"] is True
    assert res_ng["git_baseline_cross_checked"] is False
    assert res_ng["git_phase1_cross_checked"] is False

    # 3. Actual historical 98ddfa0 old_sha256 rejected for both engineering frozen amendments (Git & non-Git)
    historical_bad = {
        "scripts/build_release_bundle.py": "571fd0aa967e6835005ae5681ffd01e1aadd3fb5edcb30abe243c4775822fe7b",
        "tests/test_ci_release_builder.py": "aaf254dbf18602a8d3252906c99fde38b8cdc658a5c79900d24a87216d2d2588",
    }
    git_has_hist = (
        (ROOT / ".git").exists()
        and subprocess.run(
            ["git", "rev-parse", "--verify", f"{vp.SCIENTIFIC_BASELINE_COMMIT}^{{commit}}"],
            cwd=ROOT, capture_output=True, text=True,
        ).returncode == 0
    )
    if git_has_hist:
        for target_path, hist_sha in historical_bad.items():
            raw_hist = subprocess.run(
                ["git", "show", f"{vp.SCIENTIFIC_BASELINE_COMMIT}:{target_path}"],
                cwd=ROOT, capture_output=True, check=True,
            ).stdout
            assert hashlib.sha256(raw_hist).hexdigest() == hist_sha
    for idx, (target_path, hist_sha) in enumerate(historical_bad.items()):
        sb = make_nongit(tmp_path / f"hist_old_nongit_{idx}")
        lp = sb / "typst/representation_change_ledger.json"
        ldata = json.loads(lp.read_text(encoding="utf-8"))
        for rec in ldata["frozen_sha256_amendments"]:
            if rec["path"] == target_path:
                rec["old_sha256"] = hist_sha
        lp.write_text(json.dumps(ldata, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="disagrees with accepted Phase 1"):
            vp.verify_baseline_immutability(sb, manifest)
    if git_has_hist:
        for idx, (target_path, hist_sha) in enumerate(historical_bad.items()):
            sb_git = tmp_path / f"hist_old_git_{idx}"
            subprocess.run(
                ["git", "clone", "--local", "--shared", "--quiet", str(ROOT), str(sb_git)],
                check=True,
            )
            lp = sb_git / "typst/representation_change_ledger.json"
            ldata = json.loads(lp.read_text(encoding="utf-8"))
            for rec in ldata["frozen_sha256_amendments"]:
                if rec["path"] == target_path:
                    rec["old_sha256"] = hist_sha
            lp.write_text(json.dumps(ldata, indent=2) + "\n", encoding="utf-8")
            with pytest.raises(ValueError, match="disagrees with accepted Phase 1"):
                vp.verify_baseline_immutability(sb_git, manifest)

    # 4. Substituted origin commit rejected
    sb_orig = make_nongit(tmp_path / "sub_origin")
    lp = sb_orig / "typst/representation_change_ledger.json"
    ldata = json.loads(lp.read_text(encoding="utf-8"))
    ldata["phase1_accepted_commit"] = vp.SCIENTIFIC_BASELINE_COMMIT
    lp.write_text(json.dumps(ldata, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="phase1_accepted_commit mismatch"):
        vp.verify_baseline_immutability(sb_orig, manifest)

    # 5. Duplicate ledger entry rejected
    sb_dup = make_nongit(tmp_path / "dup_entry")
    lp = sb_dup / "typst/representation_change_ledger.json"
    ldata = json.loads(lp.read_text(encoding="utf-8"))
    ldata["contract_amendments"].append(dict(ldata["contract_amendments"][0]))
    lp.write_text(json.dumps(ldata, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate entry in representation ledger"):
        vp.verify_baseline_immutability(sb_dup, manifest)

    # 6. Undeclared contract transition rejected
    sb_undec = make_nongit(tmp_path / "undeclared_contract")
    cp = sb_undec / "contracts/scientific/CELL_MEASURE_SPEC.json"
    cp.write_text(cp.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Undeclared contract transition"):
        vp.verify_baseline_immutability(sb_undec, manifest)

    # 7. Tampered offline Phase 1 origin inventory rejected
    sb_inv = make_nongit(tmp_path / "tampered_inv")
    ip = sb_inv / vp.PHASE1_ORIGIN_INVENTORY_REL
    ip.write_text(ip.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="origin inventory digest mismatch"):
        vp.verify_baseline_immutability(sb_inv, manifest)


def test_phase2_r2_r3_spacing_unit_boundaries_and_bookmark_titles():
    """R2 & R3 finite acceptance: spaced vs unspaced math/text, single-letter J unit, and math bookmarks."""
    t2t = _load_module("aod_typ2tex", "scripts/typ2tex.py")
    conv = t2t.TypstToLatexConverter(
        root=ROOT,
        surface="main",
        current_typ=ROOT / "typst/sections/05_curl_closure_duon_current.typ",
        unit_map={},
        diagram_format="pdf",
        used_rasters=set(),
        used_diagrams=set(),
    )

    def m(expr: str) -> str:
        return t2t.convert_math(expr, "test:1", conv.convert_inline)

    # Spaced vs unspaced Duon probe must remain distinguishable
    assert m('upright("Duon") "has"') == r"\mathrm{Duon}\ \text{has}"
    assert m('upright("Duon")"has"') == r"\mathrm{Duon}\text{has}"

    # All four demonstrated corpus constructs
    assert m('upright("Duon") "has the support of " #eqref("eq:a")') == r"\mathrm{Duon}\ \text{has the support of }\eqref{eq:a}"
    assert m('R_e "is valid"') == r"R_e\ \text{is valid}"
    assert m('upright("tetron") "is the " E_4 " enclosure of "') == r"\mathrm{tetron}\ \text{is the }E_4\text{ enclosure of }"
    assert m('2.84684357388924 times 10^(- 10) upright("J").') == r"2.84684357388924\times10^{-10}\,\mathrm{J}."

    # Intentional adjacency and native tight inverse-second forms remain unchanged
    assert m("A Omega") == r"A\Omega"
    assert m('2 upright("i")') == r"2\mathrm{i}"
    assert m('4.2964283646910 times 10^(23) upright("s")^(- 1) .') == r"4.2964283646910\times10^{23}\mathrm{s}^{-1}."

    # All six restored math-bearing heading bookmark PDF strings
    assert conv.convert_inline('E2$""^(plus.minus)$ duad', for_heading=True) == r"E2\texorpdfstring{$^{\pm}$}{±} duad"
    assert conv.convert_inline('A$arrow.l.r Omega$ Field Fractal Properties', for_heading=True) == r"A\texorpdfstring{$\leftrightarrow\Omega$}{<->Omega} Field Fractal Properties"
    assert conv.convert_inline('A$Omega$ field-map table', for_heading=True) == r"A\texorpdfstring{$\Omega$}{Omega} field-map table"
    assert conv.convert_inline('3D Brownian phase-cycle $delta_3$ fixture', for_heading=True) == r"3D Brownian phase-cycle \texorpdfstring{$\delta_3$}{delta3} fixture"
    assert conv.convert_inline('3D coordinate phase-cycle $delta_3$ fixture specification', for_heading=True) == r"3D coordinate phase-cycle \texorpdfstring{$\delta_3$}{delta3} fixture specification"
    assert conv.convert_inline('AFC/A$Omega$D mapping', for_heading=True) == r"AFC/A\texorpdfstring{$\Omega$}{Omega}D mapping"


def test_phase2_r4_extractor_count_drift_does_not_invalidate_identical_pdfs(tmp_path, monkeypatch):
    """R4 finite acceptance: differing pypdf char counts (181/180, 203/202, 190/184) on identical PDFs do not fail --check, while empty text or raster XObjects still fail closed."""
    typst_bin = _find_typst_or_none()
    if typst_bin is None:
        pytest.skip("typst is required for R4 diagram export verification")
    pypdf = pytest.importorskip("pypdf")

    exp = _load_module("aod_export_typst_figures", "scripts/export_typst_figures.py")
    out_dir = tmp_path / "figs"
    exp.export_figures(ROOT, out_dir, fmt="pdf", typst_bin=typst_bin)

    orig_inspect = exp._inspect_pdf

    # Simulate pypdf version drift (181->180, 203->202, 190->184) on identical exported PDFs
    drift_counts = {
        "hydrogen-shell-setup.pdf": 180,
        "short-window-setup.pdf": 202,
        "boundary-current-spine.pdf": 184,
        "solar-system-spine.pdf": 203,
    }

    def drifted_inspect(pdf_path: Path, exp_w: float, exp_h: float):
        det, rt = orig_inspect(pdf_path, exp_w, exp_h)
        rt["extracted_text_chars"] = drift_counts.get(pdf_path.name, rt["extracted_text_chars"])
        return det, rt

    monkeypatch.setattr(exp, "_inspect_pdf", drifted_inspect)
    rt_drift: dict = {}
    exp.export_figures(ROOT, out_dir, fmt="pdf", typst_bin=typst_bin, check_only=True, runtime_out=rt_drift)
    got_by_file = {f["output_filename"]: f["extracted_text_chars"] for f in rt_drift["figures"]}
    assert {k: got_by_file[k] for k in drift_counts} == drift_counts

    # Missing text (0 chars) in real _inspect_pdf MUST still fail closed
    monkeypatch.setattr(exp, "_inspect_pdf", orig_inspect)
    monkeypatch.setattr(pypdf.PageObject, "extract_text", lambda self, *a, **kw: "")
    with pytest.raises(ValueError, match="no extractable text"):
        exp.export_figures(ROOT, out_dir, fmt="pdf", typst_bin=typst_bin, check_only=True)

    # Embedded raster image XObject in a real PDF MUST still fail closed in _inspect_pdf
    monkeypatch.undo()
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, NumberObject, StreamObject

    src_pdf = out_dir / "hydrogen-shell-setup.pdf"
    w = PdfWriter()
    w.clone_document_from_reader(PdfReader(str(src_pdf)))
    pg = w.pages[0]
    res = pg[NameObject("/Resources")].get_object()
    xobjs = res.get("/XObject")
    if xobjs is None:
        xobjs = DictionaryObject()
        res[NameObject("/XObject")] = xobjs
    else:
        xobjs = xobjs.get_object()
    img_stream = StreamObject()
    img_stream[NameObject("/Type")] = NameObject("/XObject")
    img_stream[NameObject("/Subtype")] = NameObject("/Image")
    img_stream[NameObject("/Width")] = NumberObject(1)
    img_stream[NameObject("/Height")] = NumberObject(1)
    img_stream._data = b"\x00"
    xobjs[NameObject("/ImFakeRaster")] = w._add_object(img_stream)
    raster_pdf = tmp_path / "with_raster.pdf"
    with raster_pdf.open("wb") as fh:
        w.write(fh)
    with pytest.raises(ValueError, match="raster XObjects"):
        exp._inspect_pdf(raster_pdf, 14.2, 6.2)


def test_phase2_r5_local_and_peer_destination_and_outline_rejection(tmp_path):
    """R5 finite acceptance: reject missing local /GoTo, missing sibling /GoToR /D, and symbol-stripped bookmarks."""
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter
    from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

    vp = _load_module("aod_verify_typst_parity", "scripts/verify_typst_parity.py")

    # 1. Missing local /GoTo destination reported in broken_local_destinations (rejected by Gate C)
    bad_local = tmp_path / "bad_local.pdf"
    w = PdfWriter()
    pg = w.add_blank_page(width=612, height=792)
    pg[NameObject("/Annots")] = ArrayObject([
        DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject([NumberObject(10), NumberObject(10), NumberObject(40), NumberObject(20)]),
            NameObject("/A"): DictionaryObject({
                NameObject("/S"): NameObject("/GoTo"),
                NameObject("/D"): TextStringObject("__MISSING_LOCAL_DEST__"),
            }),
        })
    ])
    with bad_local.open("wb") as fh:
        w.write(fh)
    local_info = vp._inspect_pdf_links(bad_local, expected_peer_pdf=None)
    assert local_info["broken_local_destinations"] == [(1, "missing-local-dest:'__MISSING_LOCAL_DEST__'")]

    # 2. Missing sibling peer /GoToR /D rejected by _verify_gotor_peer_destinations
    peer_main = tmp_path / "main.pdf"
    wm = PdfWriter()
    wm.add_blank_page(width=612, height=792)
    with peer_main.open("wb") as fh:
        wm.write(fh)

    bad_peer = tmp_path / "manual.pdf"
    wman = PdfWriter()
    pg2 = wman.add_blank_page(width=612, height=792)
    pg2[NameObject("/Annots")] = ArrayObject([
        DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject([NumberObject(10), NumberObject(10), NumberObject(40), NumberObject(20)]),
            NameObject("/A"): DictionaryObject({
                NameObject("/S"): NameObject("/GoToR"),
                NameObject("/F"): TextStringObject("main.pdf"),
                NameObject("/D"): TextStringObject("__AOD_REVIEW_MISSING_DESTINATION__"),
            }),
        })
    ])
    with bad_peer.open("wb") as fh:
        wman.write(fh)
    m_links = vp._inspect_pdf_links(peer_main, expected_peer_pdf=None)
    man_links = vp._inspect_pdf_links(bad_peer, expected_peer_pdf="main.pdf")
    with pytest.raises(ValueError, match="missing sibling peer /GoToR /D destination"):
        vp._verify_gotor_peer_destinations(man_links, m_links, [""])

    # 3. Legitimate AMS.63 -> AMS.61 rename passes when RG4 semantic tag matches
    fake_base_main = {"named_destinations": {"AMS.63": 1, "equation.0.33": 1}}
    fake_base_man = {"gotor_peer_links": [(1, "main.pdf", "AMS.63"), (1, "main.pdf", "equation.0.33")]}
    fake_gen_main = {"named_destinations": {"AMS.61": 1, "equation.0.33": 1}}
    fake_gen_man = {"gotor_peer_links": [(1, "main.pdf", "AMS.61"), (1, "main.pdf", "equation.0.33")]}
    ok_res = vp._verify_gotor_peer_destinations(
        fake_gen_man, fake_gen_main, ["(RG4) and (33)"],
        baseline_manual_links=fake_base_man,
        baseline_main_links=fake_base_main,
        baseline_main_pages_txt=["(RG4) and (33)"],
    )
    assert ok_res["missing_peer_destinations"] == 0
    assert ok_res["accepted_internal_destination_renames"] == [{
        "baseline_dest": "AMS.63",
        "generated_dest": "AMS.61",
        "shared_semantic_tags": ["(RG4)"],
    }]

    # 4. Symbol-stripped bookmark title rejected
    bad_outline_pdf = tmp_path / "bad_outline.pdf"
    wo = PdfWriter()
    wo.add_blank_page(width=612, height=792)
    wo.add_outline_item(title="E2 duad", page_number=0)
    with bad_outline_pdf.open("wb") as fh:
        wo.write(fh)
    with pytest.raises(ValueError, match="missing required mathematical bookmark title"):
        vp._verify_pdf_outlines_and_boundaries("main", bad_outline_pdf, "Duon has the support of")


def test_phase2_r6_atomic_install_rollback_preserves_prior_outputs(tmp_path):
    """R6 finite acceptance: injected install failure in both exporters preserves every prior file/hash intact."""
    typst_bin = _find_typst_or_none()
    if typst_bin is None:
        pytest.skip("typst is required for R6 atomic install rollback tests")
    pytest.importorskip("pypdf")

    exp = _load_module("aod_export_typst_figures", "scripts/export_typst_figures.py")
    t2t = _load_module("aod_typ2tex", "scripts/typ2tex.py")

    def snapshot_tree(d: Path) -> dict[str, bytes]:
        return {
            p.relative_to(d).as_posix(): p.read_bytes()
            for p in sorted(d.rglob("*"))
            if p.is_file()
        }

    def fail_hook(_stage: Path, _target: Path, _backup: Path | None) -> None:
        raise RuntimeError("injected final-install failure")

    # 1. export_typst_figures rollback
    fig_dir = tmp_path / "figs_rollback"
    exp.export_figures(ROOT, fig_dir, fmt="pdf", typst_bin=typst_bin)
    sentinel_fig = fig_dir / "prior_sentinel.txt"
    sentinel_fig.write_text("prior-figure-state\n", encoding="utf-8")
    before_figs = snapshot_tree(fig_dir)

    with pytest.raises(RuntimeError, match="injected final-install failure"):
        exp.export_figures(ROOT, fig_dir, fmt="pdf", typst_bin=typst_bin, before_commit_hook=fail_hook)
    assert snapshot_tree(fig_dir) == before_figs

    # 2. typ2tex rollback
    gen_dir = tmp_path / "latex_rollback"
    t2t.generate_latex_tree(ROOT, gen_dir, check_only=False, typst_bin=typst_bin)
    sentinel_tex = gen_dir / "sections/prior_sentinel.tex"
    sentinel_tex.write_text("% prior-latex-state\n", encoding="utf-8")
    before_tex = snapshot_tree(gen_dir)

    with pytest.raises(RuntimeError, match="injected final-install failure"):
        t2t.generate_latex_tree(ROOT, gen_dir, check_only=False, typst_bin=typst_bin, before_commit_hook=fail_hook)
    assert snapshot_tree(gen_dir) == before_tex

