from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def current_version() -> str:
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    m = re.search(r"Canonical version:\s*(\S+)", text)
    assert m, "CANONICAL_VERSION.txt must declare Canonical version"
    return m.group(1)


def current_slug() -> str:
    return current_version().lstrip("v").replace(".", "_").replace("-", "_")


def tex_sources():
    roots = [ROOT / "sections", ROOT / "appendices", ROOT / "manual" / "sections", ROOT / "manual" / "appendices"]
    for root in roots:
        if root.exists():
            yield from root.rglob("*.tex")


def read_all_tex():
    return "\n".join(path.read_text() for path in tex_sources())




def test_main_front_matter_uses_afc_pattern_without_setup_key_framing():
    abstract = (ROOT / "sections" / "01_abstract.tex").read_text()
    front = abstract + "\n" + (ROOT / "sections" / "02_introduction.tex").read_text()
    forbidden = ["setup key", "setup keys", "configuration language", "compiler language", "magic number", "fine-structure constant explained", "new physical laws", "periodic table", "universe operates", "press play"]
    for term in forbidden:
        assert term not in front
    assert "Axioms $\\to$ Distinctions $\\to$ Relations $\\to$ Motifs $\\to$ Calculus" in abstract
    assert "This is the way" in abstract
    assert r"Alpha\(\leftrightarrow\)Omega Dynamics (A\(\Omega\)D)" in abstract
    assert "Axiomatic--Fundamentalism calculus (AFC)" in abstract
    assert "Null potential" in abstract
    assert "declared distinction, relation, region, boundary" in abstract
    assert "hidden relational temporal motifs" in abstract
    assert "The core note gives the calculus" in abstract
    assert "observable maps" in abstract
    assert r"x \mapsto x \succ x = x" not in abstract
    assert r"\operatorname{monon}(x)=\operatorname{cycle}_{H_3}" not in abstract
    assert "compressed specifications" not in abstract
    assert r"Axiomatic--Fundamentalism (AF)~\cite" in abstract

def test_canonical_version_file_declares_this_release():
    text = (ROOT / "CANONICAL_VERSION.txt").read_text()
    assert f"Canonical version: {current_version()}" in text
    assert "Older AOD Temporal Dynamics artifacts are historical comparison artifacts only" in text


def test_sheddic_nomenclature_does_not_regress_to_old_symbols():
    text = read_all_tex()
    forbidden = [
        "ShedPath",
        "X_{\\mathrm{shed}}",
        "X_{\\mathrm{sheddic}}",
        "Xsheddic",
        "shed excess",
        "shed surplus",
        "outward shedding",
        "negative shedding",
    ]
    for term in forbidden:
        assert term not in text
    assert "SheddicPath" in text
    assert "X_{\\mathrm{shedding}}" in text


def test_reclosure_split_preserves_outward_remainder_and_exo_route():
    field = (ROOT / "sections" / "06_field.tex").read_text()
    assert r"X_W^{\mathrm{out}}=(1-\lambda_{\mathrm{reclose}})X_{\mathrm{shedding}}" in field
    assert r"X_W^{\mathrm{exo}}=(1-\lambda_{\mathrm{reclose}})X_{\mathrm{shedding}}" not in field
    assert r"X_W^{\mathrm{out}}=X_{\mathrm{exo}}+X_{\mathrm{redir}}+X_{\mathrm{open}}" in field


def test_solar_rows_are_not_labeled_released_prediction_or_released_table():
    solar = (ROOT / "manual" / "sections" / "05_solar_system_field_tests.tex").read_text()
    assert "released prediction" not in solar
    assert "released-table" not in solar
    assert "manual-solar-released" not in solar
    assert "observable-map fixture" in solar
    assert "observable-map-table" in solar


def test_field_dynamics_registry_status_is_separated():
    registry = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    assert "SPARC five-galaxy square-speed diagnostic & G0 & SPARC radial rows" in registry
    assert "Orbital-retention field-dynamics fixture & G2/G3 & G2/G3 input package" in registry
    assert "final SPARC validation" not in registry
    assert "Gaia-scored prediction" not in registry


def test_no_main_note_application_ledger_terms():
    main_text = "\n".join((ROOT / d / f).read_text() for d in ["sections", "appendices"] for f in [] )
    # Build source text from main note dirs only.
    main_text = "\n".join(path.read_text() for root in [ROOT / "sections", ROOT / "appendices"] for path in root.rglob("*.tex"))
    forbidden = [
        "SPARC",
        "Gaia",
        "Milky Way",
        "NGC",
        "DDO",
        "prediction scored",
        "measured target",
        "dark matter",
        "Poly-SADAR",
        "support morphology",
        "FlipClass",
        "T" + "XOR retention tallies",
        "MAPE_U",
        "\\chi^2_U",
        "\\Delta U",
    ]
    for term in forbidden:
        assert term not in main_text


def test_sheddic_route_is_enum_not_bare_sheddic_class():
    manual = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert r"\mathrm{sheddic\_route}" in manual
    assert r"\mathrm{early\_coupling},\mathrm{fizz},\mathrm{pending},\mathrm{sheddic}" not in manual
    assert "a sheddic" not in manual



def test_manual_container_terms_are_disciplined():
    scope = (ROOT / "manual" / "sections" / "00_scope.tex").read_text()
    assert "Manual rows, ledgers, tables, records, registries, and fixtures are document containers" in scope
    assert "They record declared values" in scope
    assert "A declared A\\(\\Omega\\) field row" not in scope
    assert "A\\(\\Omega\\) field record & support" in scope


def test_main_note_avoids_container_terms_as_ontology_names():
    main_text = "\n".join(path.read_text() for root in [ROOT / "sections", ROOT / "appendices"] for path in root.rglob("*.tex"))
    forbidden = ["readout", "ledger", "motif package", "motif card", "declared object layer"]
    for term in forbidden:
        assert term not in main_text


def test_manual_problematic_row_card_phrases_are_cleaned():
    manual_text = "\n".join(path.read_text() for root in [ROOT / "manual" / "sections", ROOT / "manual" / "appendices"] for path in root.rglob("*.tex"))
    forbidden = [
        "A declared A\\(\\Omega\\) field row",
        "Rest-energy prediction cards",
        "calculation cards",
        "manual row",
        "field row",
        "error report",
    ]
    for term in forbidden:
        assert term not in manual_text


def test_manual_no_card_as_table_header():
    manual_text = "\n".join(path.read_text() for root in [ROOT / "manual" / "sections", ROOT / "manual" / "appendices"] for path in root.rglob("*.tex"))
    assert "Card &" not in manual_text
    assert "Record &" in manual_text



def test_delta_three_replaces_old_exact_residual_public_notation():
    text = read_all_tex()
    old = "T" + "XOR"
    assert old not in text
    assert r"\delta_3" in text
    assert r"s_k^{(3)}" in text or r"s^{(3)}" in text
    assert r"\delta_{3,k}" in text


def test_symbol_compression_rho_omega_and_bowtie_lock():
    text = read_all_tex()
    assert r"\bowtie_B" in text
    assert r"\rho^D_\omega" in text
    assert r"RCD_{ij}(B)=RD_B(C_{ij})\bowtie_B R" in text or r"\RCD_{ij}(B)=RD_B(C_{ij})\bowtie_B R" in text
    old_txor = "T" + "XOR"
    forbidden = ["T" + "TL^D", "T T" + " L^D", "RCD" + " clipping", "s^{" + old_txor + "}", "s_k^{" + old_txor + "}"]
    for term in forbidden:
        assert term not in text
    assert r"\delta_3" in text
    assert r"s_k^{(3)}" in text or r"s^{(3)}" in text



def test_no_bare_ttl_pressure_heading_regression():
    field = (ROOT / "sections" / "06_field.tex").read_text()
    assert r"\subsubsection{TTL}" not in field
    assert r"\subsubsection{Seat-compatible retention duration}" in field
    assert "Seat compatibility and support-enclosure retention" not in field
    assert "support-retention duration" in field


def test_deprecated_enclosure_terminology_is_absent():
    text = "\n".join(
        path.read_text()
        for root in [ROOT / "sections", ROOT / "appendices", ROOT / "manual" / "sections", ROOT / "manual" / "appendices", ROOT / "scripts"]
        for path in root.rglob("*.tex")
        if path.exists()
    )
    # Also check python scripts that generate public figures.
    for root in [ROOT / "scripts"]:
        if root.exists():
            text += "\n" + "\n".join(path.read_text() for path in root.rglob("*.py"))
    deprecated_fragments = ["ca" + "ge", "Ca" + "ge", "ca" + "ged", "Ca" + "ged"]
    for term in deprecated_fragments:
        assert term not in text
    assert "Support enclosure" in text or "support enclosure" in text
    assert "support-enclosure retention" in text



def _index(text, needle):
    assert needle in text
    return text.index(needle)


def test_main_section_order_dependency_progression():
    field = (ROOT / "sections" / "06_field.tex").read_text()
    assert _index(field, r"\subsection{Field disposition}") < _index(field, r"\subsection{Field-as-monon compression}")
    assert _index(field, r"\subsection{Field-as-monon compression}") < _index(field, r"\subsection{Cycle-valued field compression}")
    assert _index(field, r"\subsection{Duonic pressure}") < _index(field, r"\subsection{SADAR}")
    assert _index(field, r"\subsection{SADAR}") < _index(field, r"\subsection{Cycle-shedding and temporal SADAR burden}")
    assert _index(field, r"\subsection{Fusion closure and chain reclosure}") < _index(field, r"\subsection{Fractal Field Ring Gate}")
    assert _index(field, r"\subsection{Fractal Field Ring Gate}") < _index(field, r"\subsection{Field dynamics}")


def test_manual_section_order_dependency_progression():
    manual_main = (ROOT / "manual" / "main.tex").read_text()
    assert _index(manual_main, r"\input{sections/03_short_window_rcd_shedding_fixtures.tex}") < _index(manual_main, r"\input{sections/01_rest_energy_prediction.tex}")
    exact = (ROOT / "manual" / "sections" / "03_short_window_rcd_shedding_fixtures.tex").read_text()
    assert r"\section{Exact Internal Fixtures}" in exact
    rest = (ROOT / "manual" / "sections" / "01_rest_energy_prediction.tex").read_text()
    assert r"\section{Field Rest-Energy Records}" in rest



def test_manual_no_hardcoded_old_frg_section_number():
    manual_text = "\n".join(path.read_text() for root in [ROOT / "manual" / "sections", ROOT / "manual" / "appendices"] for path in root.rglob("*.tex"))
    assert "main note \\S4.15" not in manual_text


def test_main_shell_paths_precede_field_dynamics():
    field = (ROOT / "sections/06_field.tex").read_text()
    assert _index(field, r"\subsection{Seat compatibility and shell/enclosure routing}") < _index(field, r"\subsection{Shell paths}")
    assert _index(field, r"\subsection{Shell paths}") < _index(field, r"\subsection{Fusion closure and chain reclosure}")
    assert _index(field, r"\subsection{Fusion closure and chain reclosure}") < _index(field, r"\subsection{Fractal Field Ring Gate}")
    assert _index(field, r"\subsection{Fractal Field Ring Gate}") < _index(field, r"\subsection{Field dynamics}")


def test_neuronal_benchmark_not_in_exact_internal_fixtures():
    exact = (ROOT / "manual/sections/03_short_window_rcd_shedding_fixtures.tex").read_text()
    registry = (ROOT / "manual/sections/09_prediction_test_fixture_registry.tex").read_text()
    assert "Neuronal-ring benchmark acquisition" not in exact
    assert "Neuronal-ring benchmark acquisition" in registry


def test_galactic_lensing_plan_is_manual_layer_and_uses_delta3_notation():
    manual_main = (ROOT / "manual" / "main.tex").read_text()
    assert r"\input{sections/07_galactic_lensing_plan.tex}" in manual_main
    lens = (ROOT / "manual" / "sections" / "07_galactic_lensing_plan.tex").read_text()
    assert "Galactic Lensing Diagnostic Plan" in lens
    assert r"\delta_3" in lens
    assert r"T^\times_k" in lens
    assert r"C^\times" in lens
    assert "Toy 1 & exact internal" in lens or "Toy 1" in lens
    assert "SPARC5 & L1 & radial lens-medium data-support class" in lens
    assert "SWELLS K0 & L2 & target acquisition" in lens
    assert "K4 & L3 & higher-resolution lensing input-manifest row" in lens
    assert "L3 lensing input package & L3 & L3 input-manifest row" in lens
    assert "T" + "XOR" not in lens
    assert "field-ring ledger" not in lens
    assert "prediction ledger" not in lens
    assert "AOD input side" not in lens


def test_galactic_lensing_registry_statuses_are_explicit():
    registry = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    required = [
        "Toy 1 lensing field-ring fixture & L0 & integer comparator bins",
        "SPARC5 lens-medium diagnostic & L1 & radial lens-medium fields",
        "SWELLS K0 target acquisition & L2 & target acquisition fields",
        "SWELLS K1 retained baseline & L1/L2 & baseline target fields",
        "SWELLS K2/K3 & L1/L2 & audit diagnostics",
        "K4 galactic lensing gate & L3 & higher-resolution input manifest",
        "L3 lensing input package & L3 & L3 input manifest",
    ]
    for item in required:
        assert item in registry
    assert "Galactic lensing & benchmark dataset pending" not in registry


def test_lensing_plan_data_and_figures_are_packaged():
    data_dir = ROOT / "manual" / "data" / "lensing"
    fig_dir = ROOT / "manual" / "figures" / "lensing"
    for name in [
        "toy1_delta3_class_tallies.csv",
        "sparc5_medium_diagnostic_summary.csv",
        "swells_k1_k2_k3_delta3_comparison.csv",
        "k4_3d_timeflow_input_gate.csv",
    ]:
        assert (data_dir / name).exists()
    for name in [
        "02_frg_value_identity_delta3.png",
        "05_swells_k_comparison_delta3.png",
        "07_k4_3d_timeflow_input_gate.png",
        "09_staged_lensing_lane.png",
    ]:
        assert (fig_dir / name).exists()


def test_sadar_operator_moved_after_pressure_and_before_sadar_section():
    field = (ROOT / "sections/06_field.tex").read_text()
    assert _index(field, r"\subsection{Duonic pressure}") < _index(field, r"\subsection{SADAR value operator}")
    assert _index(field, r"\subsection{SADAR value operator}") < _index(field, r"\subsection{SADAR}")
    primitive = (ROOT / "sections/05_curl_closure_duon_current.tex").read_text()
    assert r"\subsection{SADAR operator}" not in primitive
    assert r"\subsection{SADAR value operator}" not in primitive


def test_field_dynamics_figure_source_uses_structural_labels():
    script = (ROOT / "scripts/generate_field_dynamics_layered.py").read_text()
    forbidden = ["energy and " + "mass", "energy and " + "material", "core / " + "impeller", "capacitance or " + "channel capacity", "drives system " + "circulation"]
    for term in forbidden:
        assert term not in script
    required = ["support/current", "core coupling", "channel capacity", "seeds retained circulation"]
    for term in required:
        assert term in script


def test_sparc5_lensing_caption_is_lens_medium():
    lens = (ROOT / "manual/sections/07_galactic_lensing_plan.tex").read_text()
    assert "SPARC5 lens-medium class tallies" in lens
    assert "SPARC5 " + "lensing class tallies" not in lens


def test_registry_splits_toy_fixture_and_neuronal_benchmark_acquisition():
    registry = (ROOT / "manual/sections/09_prediction_test_fixture_registry.tex").read_text()
    assert "Toy 1 field-ring fixture & D0 & integer comparator bins" in registry
    assert "Neuronal-ring benchmark acquisition & L2 & acquisition fields" in registry
    assert "Fractal field ring fixture" + " & exact integer fixture / benchmark acquisition" not in registry


def test_appendix_a_uses_duration_clipping_not_high_rcd_phrase():
    appendix = (ROOT / "manual/appendices/A_simulation_fixtures_and_tau_prediction_context.tex").read_text()
    assert "short-window duration-clipping fixture" in appendix
    assert "short-window high-" + "RCD pressure clipping" not in appendix


def test_q4_kernel_four_edge_implementation_present():
    text = (ROOT / "sections/04_cut_running_fractal_tesseract.tex").read_text()
    assert "Four-edge implementation" in text
    assert "ancestor edge" in text
    assert "up to three successor slots" in text
    assert "return branch, hinge/dwell, and outbound branch" in text


def test_epitaph_contains_afc_non_prerequisite_without_citation():
    title = (ROOT / "sections" / "00_title.tex").read_text()
    manual = (ROOT / "manual" / "main.tex").read_text()
    for text in [title, manual]:
        assert "Comprehension, cooperation, and presence are not prerequisites of AFC." in text
        assert "Comprehension, cooperation, and presence are not prerequisites of AFC~\\cite{afc}" not in text
    assert "Nuff said" in title


def test_manual_field_dynamics_data_support_budget_and_toy_present():
    field_dyn = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert r"\subsection{Data-support classes for manual simulations and comparisons}" in field_dyn
    assert "Data-support classes for manual simulations and comparisons" in field_dyn
    assert "D0" in field_dyn and "G0" in field_dyn and "G3" in field_dyn and "L3" in field_dyn
    assert r"\subsection{Data-support and uncertainty budget}" in field_dyn
    assert "Field dynamics data-support classes" in field_dyn
    assert "Field dynamics uncertainty and report targets" in field_dyn
    assert r"\epsilon_\rho" in field_dyn
    assert r"\epsilon_{\partial}" in field_dyn
    assert r"\operatorname{SheddicPath}" in field_dyn
    assert r"\subsection{Two-dimensional slice / three-dimensional field toy}" in field_dyn
    assert r"\Delta U_{2D\to3D}" in field_dyn
    assert r"\Delta U_{\partial}" in field_dyn
    assert r"\delta_{3,k}(T^{\mathrm{bad}},T^{3D})" in field_dyn



def test_lensing_public_display_labels_are_clean():
    table_text = "\n".join(
        path.read_text()
        for path in [
            ROOT / "manual/data/lensing/sparc5_medium_diagnostic_summary_table.tex",
            ROOT / "manual/data/lensing/swells_k0_target_tallies_table.tex",
            ROOT / "manual/data/lensing/swells_k1_k2_k3_comparison_table.tex",
            ROOT / "manual/data/lensing/k4_3d_timeflow_input_gate_table.tex",
        ]
    )
    forbidden = [
        "exoshedding\\_deflection",
        "open\\_loss\\_scatter",
        "weak\\_refraction",
        "modelled\\_strong\\_lens\\_presence",
        "modelled\\_lens",
        "theta\\_low\\_<0.75",
        "theta\\_high\\_>=1.00",
        "sigma\\_low\\_<200",
        "sigma\\_high\\_>=230",
        "lens-medium diagnostic\\\\",
    ]
    for term in forbidden:
        assert term not in table_text
    required = [
        "exoshedding deflection",
        "strong-lens presence",
        r"\(\theta_E<0.75\)",
        r"\(\theta_E\ge1.00\)",
        r"\(\sigma<200\)",
        r"\(\sigma\ge230\)",
        "lens-medium",
    ]
    for term in required:
        assert term in table_text


def test_field_dynamics_data_support_budget_display_is_compact():
    field_dyn = (ROOT / "manual/sections/06_field_dynamics_applications.tex").read_text()
    assert "Field dynamics data-support classes" in field_dyn
    assert "Field dynamics uncertainty and report targets" in field_dyn
    assert "3D / 2D / radial / proxy" in field_dyn
    assert "3D / 2D / radial / proxy / unresolved" not in field_dyn
    assert "frozen / calibrated / undeclared" not in field_dyn
    assert "route / slosh / pending" not in field_dyn
    assert "Data-support and uncertainty budget" in field_dyn
    assert "Field dynamics setup-error budget" not in field_dyn
    assert "cadence and duration window" not in field_dyn


def test_returned_duration_wording_is_reflection_duration():
    main_text = "\n".join(path.read_text() for root in [ROOT / "sections", ROOT / "appendices"] for path in root.rglob("*.tex"))
    assert "returned-duration accessor" not in main_text
    assert "returned-duration value" not in main_text
    assert "reflection-duration accessor" in main_text


def test_tau_duration_ratio_header_uses_current_duration_language():
    tau_text = "\n".join(path.read_text() for path in (ROOT / "manual/data/tau").glob("*.csv"))
    assert "ttl_ratio_to_tau_window" not in tau_text
    assert "duration_clip_ratio_to_tau_window" in tau_text


def test_release_readiness_file_and_no_stale_lensing_plan_manifests():
    readiness = ROOT / "RELEASE_READINESS.txt"
    assert readiness.exists()
    text = readiness.read_text()
    assert f"Canonical package: {current_version()}" in text
    stale = [
        ROOT / "manual/data/lensing/package_manifest.csv",
        ROOT / "manual/data/lensing/plan_data_manifest.csv",
        ROOT / "manual/data/lensing/plan_figure_manifest.csv",
        ROOT / "manual/data/lensing/notation_refresh_audit.csv",
    ]
    for path in stale:
        assert not path.exists()


def test_introduction_uses_records_not_setup_key_proposes():
    intro = (ROOT / "sections/02_introduction.tex").read_text()
    assert "A compact expression records a curling-curl specification" in intro
    assert "A compact expression proposes a curling-curl specification" not in intro



def test_k4_input_gate_figure_generator_uses_singular_field_label():
    script = (ROOT / "manual" / "scripts" / "generate_k4_input_gate_figure.py").read_text()
    assert 'return "1 field" if n == 1 else f"{n} fields"' in script
    assert '"1 fields"' not in script


def test_labels_are_unique_and_not_stacked_on_one_line():
    import re
    labels = {}
    for path in tex_sources():
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            assert line.count("\\label{") <= 1, f"multiple labels on {path}:{lineno}"
            for label in re.findall(r"\\label\{([^}]*)\}", line):
                assert label not in labels, f"duplicate label {label} in {path}:{lineno} and {labels[label]}"
                labels[label] = f"{path}:{lineno}"


def test_solar_observable_map_table_is_not_duplicated():
    solar = (ROOT / "manual" / "sections" / "05_solar_system_field_tests.tex").read_text()
    assert solar.count("Solar-system observable-map comparison records") == 1
    assert "Classic solar-system observable-map comparison fixtures" not in solar
    assert "tab:manual-solar-observable-map-results" in solar
    assert "tab:manual-solar-observable-map}" not in solar


def test_sheddic_path_definition_is_single_and_audit_is_distinct():
    field = (ROOT / "sections" / "06_field.tex").read_text()
    assert field.count(r"\subsubsection{Sheddic path}") == 1
    assert r"\subsubsection{Sheddic route reference}" in field
    assert r"\subsubsection{Sheddic path audit}" in field


def test_appendix_f_is_wave_presentation_audit_not_second_ontology():
    wave = (ROOT / "appendices" / "F_wave.tex").read_text()
    assert r"\section{Wave presentation and audit}" in wave
    assert "second wave ontology" not in wave


def test_procedural_tracking_language_is_not_used():
    text = read_all_tex()
    forbidden = ["A tracked cut-running", "tracked separately", "A declared wave is tracked", "must track boundary", "Track hinge", "Track slosh"]
    for term in forbidden:
        assert term not in text


def test_no_defensive_ontology_negations():
    text = read_all_tex()
    forbidden = [
        "separate wave ontology",
        "second wave ontology",
        "new wave ontology",
        "does not add ontology",
        "not main-note ontology",
        "without creating additional ontology",
        "not a new A\\(\\Omega\\)D object",
    ]
    for term in forbidden:
        assert term not in text


def test_rcd_and_b_scoped_flux_are_separate_headings():
    field = (ROOT / "sections" / "06_field.tex").read_text()
    assert r"\subsubsection{Reflection-duration coupling}" in field
    assert r"\subsubsection{\texorpdfstring{\(B\)-scoped flux contents}{B-scoped flux contents}}" in field
    assert "Reflection-duration coupling and" not in field


def test_abstract_expands_afc_before_first_acronym_use():
    abstract = (ROOT / "sections" / "01_abstract.tex").read_text()
    first_afc = abstract.find("AFC")
    expansion = abstract.find("Axiomatic--Fundamentalism calculus (AFC)")
    assert expansion != -1
    assert first_afc == expansion + len("Axiomatic--Fundamentalism calculus (")


def test_abstract_uses_null_potential_and_cites_afc_af():
    abstract = (ROOT / "sections" / "01_abstract.tex").read_text()
    assert "Alpha\\(\\leftrightarrow\\)Omega Dynamics (A\\(\\Omega\\)D) is a relational temporal form of the Stokes cut of the Axiomatic--Fundamentalism calculus (AFC)." in abstract
    assert "The starting point is Null potential" in abstract
    assert r"A\(\Omega\)D continues from that AFC Stokes cut" in abstract
    assert "The core note gives the calculus; the manual carries" in abstract
    assert "Axiomatic--Fundamentalism calculus (AFC)~\\cite{afc}." in abstract
    assert "Axiomatic--Fundamentalism (AF)~\\cite{reginald2025af}." in abstract
    assert "develops from" not in abstract
    assert "the calculus of Axiomatic--Fundamentalism" not in abstract


def test_affirmative_quarantine_language():
    text = read_all_tex()
    forbidden = [
        "It is not an A\\(\\Omega\\) field-invariant in the main note",
        "It is not an A\\(\\Omega\\) primitive",
    ]
    for term in forbidden:
        assert term not in text
    assert "manual measured-sector charge/orientation map carried by the manual comparison record" in text
    assert "used only by the external-comparison layer" in text


def test_leprechaun_remark_is_conceptual():
    text = read_all_tex()
    assert "The Art of the Leprechaun is the tracing and exploration of Stokes temporal wave dynamics" in text
    assert "AFC supplies the finite \\(Q_4\\) Hamming--1" not in text


def test_manual_title_page_matches_main_title_with_manual_marker():
    text = (ROOT / "manual" / "main.tex").read_text()
    assert r"Alpha$\leftrightarrow$Omega Dynamics (A$\Omega$D)" in text
    assert "The Hidden Temporal Dynamics of Stokes" in text
    assert r"43 $^\circ\mathrm{c}$" in text
    assert r"{\Large Manual}" in text
    assert "The Art of the Leprechaun: Fractal Calculus" in text
    assert r"A\leftrightarrow_{\mu}\Omega" in text
    assert "Epitaph" in text
    assert "Nuff said" in text


def test_afc_citation_only_in_literature_note():
    title = (ROOT / "sections" / "00_title.tex").read_text()
    manual_title = (ROOT / "manual" / "main.tex").read_text()
    afc = (ROOT / "sections" / "03_afc_basis.tex").read_text()
    assert "\\cite{afc}" not in title
    assert "\\cite{afc}" not in manual_title
    assert "\\cite{afc}" not in afc
    abstract = (ROOT / "sections" / "01_abstract.tex").read_text()
    assert "Axiomatic--Fundamentalism calculus (AFC)~\\cite{afc}." in abstract


def test_note_blocks_use_general_mechanics_style_macro():
    main = (ROOT / "preamble.tex").read_text()
    manual = (ROOT / "manual" / "preamble.tex").read_text()
    expected = r"\newcommand{\aodnoteblock}[2]{\medskip\begingroup\emergencystretch=3em\sloppy\noindent\emph{#1.}\ #2\par\endgroup}"
    assert expected in main
    assert expected in manual
    assert "footnotesize\\emph" not in main
    assert "footnotesize\\emph" not in manual


def test_afc_provenance_block_is_present_and_uncited():
    afc = (ROOT / "sections" / "03_afc_basis.tex").read_text()
    assert r"\subsection{Null potential}" in afc
    assert "AFC provenance used here: Null potential; declared distinctions; induced relations; regions; boundaries; Stokes identity on declared cuts." in afc
    assert "declared fields and regions" not in afc
    assert "Null posture" not in afc
    assert "used by reference~\\cite{afc}" not in afc


def test_afc_provenance_is_note_block_not_intro_subsection():
    intro = (ROOT / "sections" / "02_introduction.tex").read_text()
    assert r"\subsection{AFC provenance}" not in intro
    afc = (ROOT / "sections" / "03_afc_basis.tex").read_text()
    assert r"\aodprovenance{AFC provenance used here:" in afc



def test_null_potential_language_is_consistent():
    sections = "\n".join(p.read_text() for p in (ROOT / "sections").glob("*.tex"))
    assert "Null potential" in sections
    assert "Null posture" not in sections


def test_intro_expands_frg_once():
    intro = (ROOT / "sections" / "02_introduction.tex").read_text()
    assert "Fractal Field Ring Gate (FRG)" in intro


def test_note_block_macros_use_general_mechanics_inline_style():
    main = (ROOT / "preamble.tex").read_text()
    manual = (ROOT / "manual" / "preamble.tex").read_text()
    expected = r"\newcommand{\aodnoteblock}[2]{\medskip\begingroup\emergencystretch=3em\sloppy\noindent\emph{#1.}\ #2\par\endgroup}"
    assert expected in main
    assert expected in manual
    assert r"\emph{#1.}\par" not in main
    assert r"\emph{#1.}\par" not in manual



def test_sadar_balance_figure_script_uses_current_symbols():
    script = (ROOT / "scripts" / "generate_sadar_boundary_balance.py").read_text()
    assert r"\rho^D_{\omega,e}" in script
    assert "min(D_e" not in script
    assert "energy and mass" not in script
    assert "energy and material" not in script


def test_source_root_has_no_release_patch_summaries():
    assert not list(ROOT.glob("AOD_Temporal_Dynamics_v*_PATCH_SUMMARY.txt"))


def test_source_file_names_are_version_neutral():
    allowed = {"CANONICAL_VERSION.txt", "RELEASE_READINESS.txt"}
    forbidden = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if p.name in allowed:
            continue
        if ".git" in rel or "__pycache__" in rel or ".pytest_cache" in rel:
            continue
        name = p.name
        if any(token in name for token in ["v39", "v3_style", "v32", "v39_99r", "AOD_Temporal_Dynamics_v"]):
            forbidden.append(rel)
    assert forbidden == []


def test_build_ci_and_release_bundle_script_present():
    workflow = ROOT / ".github" / "workflows" / "build.yml"
    script = ROOT / "scripts" / "build_release_bundle.py"
    assert workflow.exists()
    assert script.exists()
    wtext = workflow.read_text()
    stext = script.read_text()
    assert "scripts/build_release_bundle.py" in wtext
    assert "python3 -m pytest -q" in wtext
    assert "CANONICAL_VERSION.txt" in stext
    assert "AOD_Temporal_Dynamics_source" in stext
    assert "source.zip" in stext and "bundle.zip" in stext




def test_ci_build_bundle_uses_tests_artifact_and_no_separate_verifier():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert "tests.txt" in workflow
    assert "python3 -m pytest -q | tee tests.txt" in workflow
    obsolete_audit_tool = "audit" + "_" + "pack"
    obsolete_verifier_log = "verifier" + ".log"
    assert obsolete_audit_tool not in workflow
    assert obsolete_verifier_log not in workflow
    assert obsolete_audit_tool not in script
    assert obsolete_verifier_log not in script
    # source-clean.zip is allowed only for legacy bare source-archive mode.
    assert "source-clean.zip" in script
    assert "def build_source_only" in script

def test_canonical_version_file_declares_current_release():
    text = (ROOT / "CANONICAL_VERSION.txt").read_text()
    assert f"Canonical version: {current_version()}" in text
    assert f"AOD_Temporal_Dynamics_v{current_slug()} is the canonical package." in text
    assert "Older AOD Temporal Dynamics artifacts are historical comparison artifacts only" in text

def test_orbital_retention_input_provenance_gate_present():
    manual = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "Orbital-retention input provenance gate" in manual
    assert "SPARC-supported radial" in manual
    assert "external 3D" in manual
    assert "latent / proxy" in manual
    assert "declared proxy" in manual
    assert "Field component & Source & Support status & Uncertainty status & Scored" in manual
    assert "Declare star/gas/core/background/current density inputs and source/status records" in manual


def test_orbital_retention_registry_mentions_input_provenance_gate():
    registry = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    assert "input-provenance gate" in registry
    assert "workbook spine and provenance tables" in registry


def test_release_readiness_mentions_orbital_retention_provenance_gate():
    readiness = (ROOT / "RELEASE_READINESS.txt").read_text()
    assert f"Canonical version: {current_version()}" in readiness
    assert "input-provenance gate" in readiness
    assert "data-support class" in readiness



def test_tau_missing_burden_caption_exact_ratio():
    manual = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "31/50" in manual
    assert r"presentation value \(0.62\)" in manual
    assert "Dimonnanyro row" in manual
    assert "matches the declared missing-fraction target" not in manual



def test_manual_scoped_error_data_support_chain_present():
    scope = (ROOT / "manual" / "sections" / "00_scope.tex").read_text()
    assert r"\subsection{Scoped errors by data-support class}" in scope
    assert r"D\rightarrow R(D)\rightarrow \mathcal M(D,R)" in scope
    assert r"\Pi_{\mathrm{report}}" in scope
    assert r"\epsilon_{\mathrm{report}}" in scope
    assert "Projection and marginalization maps carry their own comparison coordinates and uncertainty records" in scope


def test_manual_data_support_section_notes_present():
    required = {
        "manual/sections/01_rest_energy_prediction.tex": "Rest-energy records are exact internal",
        "manual/sections/02_hydrogen_facing_shell_tests.tex": "Hydrogen shell tests instantiate D0 exact shell-ratio fixtures",
        "manual/sections/03_short_window_rcd_shedding_fixtures.tex": "These are D0 exact internal fixtures",
        "manual/sections/04_boundary_current_applications.tex": "Boundary-current applications are D0 exact scoped-flux fixtures",
        "manual/sections/05_solar_system_field_tests.tex": "Solar records are O0 observable-map fixtures",
    }
    for rel, phrase in required.items():
        assert phrase in (ROOT / rel).read_text()


def test_manual_data_support_negative_language_absent():
    text = "\n".join((ROOT / "manual" / "sections").glob("*.tex").__iter__().__class__ and [p.read_text() for p in (ROOT / "manual" / "sections").glob("*.tex")])
    forbidden = [
        "not full field-fluid",
        "invalid radial",
        "known-missing",
        "K4 & blocked until",
    ]
    for term in forbidden:
        assert term not in text


def test_appendix_a_data_support_class_reference_present():
    appendix = (ROOT / "manual" / "appendices" / "A_simulation_fixtures_and_tau_prediction_context.tex").read_text()
    assert r"\subsection{Data-support class reference}" in appendix
    for cls in ["D0", "O0", "G0", "G1", "G2", "G3", "L0", "L1", "L2", "L3"]:
        assert cls in appendix


def test_registry_has_data_support_class_column():
    registry = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    assert "Record & Class & Active fields" in registry
    for cls in ["D0", "O0", "G0", "G1", "G2/G3", "L0", "L1", "L2", "L3", "D0/O0"]:
        assert cls in registry
    assert "SPARC five-galaxy square-speed diagnostic & G0" in registry
    assert "Orbital-retention field-dynamics fixture & G2/G3" in registry


def test_sparc_scored_table_has_class_and_uncertainty_policy():
    table = (ROOT / "manual" / "data" / "derived" / "sparc_summary_table.tex").read_text()
    assert "Class & $\\sigma$ policy" in table
    assert "G0 & obs-only" in table
    assert "G0 active input fields" in (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    section = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "G0 active input fields" in section
    

def test_ablation_cut_defined():
    section = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert r"\paragraph{Ablation cut.}" in section
    assert "declared data-support cut" in section
    assert "projection or marginalization residuals" in section


def test_release_audit_replaces_registry_falsification():
    registry = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    assert r"\aodnoteblock{Completion rule}" in registry
    assert r"\aodnoteblock{Falsification}" not in registry


def test_negative_data_support_framing_absent():
    text = "\n".join(p.read_text() for p in (ROOT / "manual" / "sections").glob("*.tex"))
    forbidden = [
        "not valid",
        "invalid because missing 3D",
        "negative control",
        "missing orbital-retention gate",
        "full test vs invalid test",
        "not full field-fluid",
        "invalid radial",
        "K4 & blocked until",
    ]
    for term in forbidden:
        assert term not in text


def test_no_standalone_so_lines_in_active_tex():
    offenders = []
    for path in ROOT.rglob('*.tex'):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(errors='ignore')
        for i, line in enumerate(text.splitlines(), start=1):
            if line.strip() == 'so':
                offenders.append(f"{rel}:{i}")
    assert not offenders, offenders


def test_readme_contains_zenodo_description_and_version_neutral_build_notes():
    readme = (ROOT / "README.md").read_text()
    assert "# Alpha-Omega Dynamics: The Hidden Temporal Dynamics of Stokes" in readme
    assert f"**Version:** {current_version()}" in readme
    assert "**Title:** Alpha-Omega Dynamics" in readme
    assert "**Subtitle:** The Hidden Temporal Dynamics of Stokes" in readme
    assert "**Zenodo title:** Alpha-Omega Dynamics: The Hidden Temporal Dynamics of Stokes" in readme
    assert "Alpha↔Omega Dynamics (AΩD) is a relational temporal form of the Stokes cut" in readme
    assert "This release includes the main note, manual, source package, test output, patch summary, bundle, and SHA-256 manifests." in readme
    assert "Versioned names are generated only as release artifacts" in readme
    assert "scripts/build_release_bundle.py" in readme
    assert f"AOD_Temporal_Dynamics_v{current_slug()}" in readme


def test_readme_has_single_versioned_names_sentence():
    readme = (ROOT / "README.md").read_text()
    assert readme.count("Versioned names are generated only as release artifacts") == 1
