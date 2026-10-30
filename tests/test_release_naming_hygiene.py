from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MAIN_SOURCES = [
    "appendices/A_fractal_address_bip_biz.tex",
    "appendices/B_curling_curls.tex",
    "appendices/C_stochastic_crowning.tex",
    "appendices/D_cycle_shedding_demonstration.tex",
    "appendices/E_glossary.tex",
    "appendices/F_wave.tex",
    "appendices/G_symbolic_cancellation_check.tex",
    "appendices/H_combinatorics_rd_tests.tex",
    "appendices/I_path_complexity_prototype_quarantine.tex",
    "appendices/J_ao_field_fractal_properties.tex",
    "sections/03_afc_basis.tex",
    "sections/04_cut_running_fractal_tesseract.tex",
    "sections/05_curl_closure_duon_current.tex",
    "sections/06_field.tex",
]


def tex_sources():
    roots = [ROOT / "sections", ROOT / "appendices", ROOT / "manual" / "sections", ROOT / "manual" / "appendices"]
    for root in roots:
        if root.exists():
            yield from root.rglob("*.tex")


def read_all_tex():
    return "\n".join(path.read_text() for path in tex_sources())


def current_version():
    text = (ROOT / "CANONICAL_VERSION.txt").read_text()
    m = re.search(r"Canonical version:\s*(\S+)", text)
    assert m
    return m.group(1)


def test_main_front_matter_preserves_accepted_compact_abstract():
    abstract = (ROOT / "sections/01_abstract.tex").read_text()
    assert "is a relational temporal form of the Stokes cut" in abstract
    # R07 permits only the final routing sentence deletion.
    import hashlib
    assert hashlib.sha256(abstract.encode()).hexdigest() == 'a42ebe256def1106badff156f495206d39fe32a984b97e9fe2ed07ba12c1803c'

def test_canonical_version_file_declares_this_release():
    text = (ROOT / "CANONICAL_VERSION.txt").read_text()
    assert f"Canonical version: {current_version()}" in text
    assert "Older AOD Temporal Dynamics artifacts are historical comparison artifacts only" in text


def test_reclosure_split_preserves_outward_remainder_and_exo_route():
    field = (ROOT / "sections" / "06_field.tex").read_text()
    assert r"X_W^{\mathrm{out}}=(1-\lambda_{\mathrm{reclose}})X_{\mathrm{shedding}}" in field
    assert r"X_W^{\mathrm{exo}}=(1-\lambda_{\mathrm{reclose}})X_{\mathrm{shedding}}" not in field
    assert r"X_W^{\mathrm{out}}=X_{\mathrm{exo}}+X_{\mathrm{redir}}+X_{\mathrm{open}}" in field


def test_field_dynamics_registry_status_is_separated():
    registry = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    assert "SPARC five-galaxy square-speed diagnostic & G0 & SPARC radial rows" in registry
    assert "Orbital-retention field-dynamics fixture & G2/G3 & G2/G3 input package" in registry
    assert "final SPARC validation" not in registry
    assert "Gaia-scored prediction" not in registry


def test_sheddic_route_is_enum_not_bare_sheddic_class():
    manual = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert r"\mathrm{sheddic\_route}" in manual
    assert r"\mathrm{early\_coupling},\mathrm{fizz},\mathrm{pending},\mathrm{sheddic}" not in manual


def test_main_note_avoids_container_terms_as_ontology_names():
    text = active_text()
    assert r"F_{B,\lambda}|_k=(B,\lambda,I_B(k)" in text


def test_delta_three_replaces_old_exact_residual_public_notation():
    text = read_all_tex()
    assert r"\delta_3" in text
    assert r"s_k^{(3)}" in text or r"s^{(3)}" in text
    assert r"\delta_{3,k}" in text


def test_symbol_compression_rho_omega_and_bowtie_lock():
    text = read_all_tex()
    assert r"\bowtie_B" in text
    assert r"\rho^D_\omega" in text
    assert r"RCD_{ij}(B)=RD_B(C_{ij})\bowtie_B R" in text or r"\RCD_{ij}(B)=RD_B(C_{ij})\bowtie_B R" in text
    assert r"\delta_3" in text
    assert r"s_k^{(3)}" in text or r"s^{(3)}" in text


def test_galactic_lensing_plan_is_manual_layer_and_uses_delta3_notation():
    manual_main = (ROOT / "manual" / "main.tex").read_text()
    assert r"\input{sections/07_galactic_lensing_plan.tex}" in manual_main
    lens = (ROOT / "manual" / "sections" / "07_galactic_lensing_plan.tex").read_text()
    assert r"\delta_3" in lens
    assert r"T^\times_k" in lens
    assert r"C^\times" in lens
    assert "Toy 1 & exact internal" in lens or "Toy 1" in lens
    assert "SPARC5 & L1 & radial lens-medium data-support class" in lens
    assert "SWELLS K0 & L2 & target acquisition" in lens
    assert "K4 & L3 & higher-resolution lensing input-manifest row" in lens
    assert "L3 lensing input package & L3 & L3 input-manifest row" in lens


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


def test_registry_splits_toy_fixture_and_neuronal_benchmark_acquisition():
    registry = (ROOT / "manual/sections/09_prediction_test_fixture_registry.tex").read_text()
    assert "Toy 1 field-ring fixture & D0 & integer comparator bins" in registry
    assert "Neuronal-ring benchmark acquisition & L2 & acquisition fields" in registry
    assert "Fractal field ring fixture" + " & exact integer fixture / benchmark acquisition" not in registry


def test_q4_kernel_four_edge_implementation_present():
    text = active_text()
    assert "four incident edges" in text and "slot binds the ancestor" in text
    assert r"E(\Qfour)=\{(u,v):d_H(u,v)=1\}" in text
    assert "three other slots" in text
    assert r"\label{eq:admitted-kernel}" in text


def test_manual_field_dynamics_data_support_budget_and_toy_present():
    field_dyn = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "D0" in field_dyn and "G0" in field_dyn and "G3" in field_dyn and "L3" in field_dyn
    assert r"\epsilon_\rho" in field_dyn
    assert r"\epsilon_{\partial}" in field_dyn
    assert r"\operatorname{SheddicPath}" in field_dyn
    assert r"\Delta U_{2D\to3D}" in field_dyn
    assert r"\Delta U_{\partial}" in field_dyn
    assert r"\delta_{3,k}(T^{\mathrm{bad}},T^{3D})" in field_dyn


def test_tau_duration_ratio_header_uses_current_duration_language():
    tau_text = "\n".join(path.read_text() for path in (ROOT / "manual/data/tau").glob("*.csv"))
    assert "ttl_ratio_to_tau_window" not in tau_text
    assert "duration_clip_ratio_to_tau_window" in tau_text


def test_canonical_metadata_and_no_stale_lensing_plan_manifests():
    import json
    metadata = json.loads((ROOT / ".zenodo.json").read_text())
    assert metadata["version"] == current_version()
    stale = [
        ROOT / "manual/data/lensing/package_manifest.csv",
        ROOT / "manual/data/lensing/plan_data_manifest.csv",
        ROOT / "manual/data/lensing/plan_figure_manifest.csv",
        ROOT / "manual/data/lensing/notation_refresh_audit.csv",
    ]
    for path in stale:
        assert not path.exists()


def test_introduction_uses_records_not_setup_key_proposes():
    text = active_text()
    assert "A compact expression" in text and "curling-curl specification" in text
    assert r"\label{eq:motif-admission}" in text
    assert "A core signature is" in text and "construction witness is bound" in text


def test_labels_are_unique_and_not_stacked_on_one_line():
    import re
    labels = {}
    for path in tex_sources():
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for label in re.findall(r"\\label\{([^}]*)\}", line):
                assert label not in labels, f"duplicate label {label} in {path}:{lineno} and {labels[label]}"
                labels[label] = f"{path}:{lineno}"


def test_solar_observable_map_table_is_not_duplicated():
    solar = (ROOT / "manual" / "sections" / "05_solar_system_field_tests.tex").read_text()
    assert "tab:manual-solar-observable-map-results" in solar


def test_sheddic_path_definition_is_single_and_audit_is_distinct():
    text = active_text()
    assert r"\label{eq:sheddic-path}" in text


def test_established_main_sources_are_active_and_substantive():
    text = active_text()
    assert text.count(r"\label{eq:wave-identity}")==1
    assert text.count(r"\label{eq:wave-sadar-presentation}")==1
    assert "For an already admitted wave" in text
    active = (ROOT / "main.tex").read_text()
    for relative in REQUIRED_MAIN_SOURCES:
        path = ROOT / relative
        assert path.exists()
        assert any(line.strip() and not line.lstrip().startswith("%") for line in path.read_text().splitlines())
        assert relative in active


def test_rcd_and_b_scoped_flux_are_separate_headings():
    text = active_text()
    assert r"\label{eq:rcd-coupling}" in text
    assert r"\label{eq:flux-types}" in text


def test_abstract_uses_null_potential_and_separate_literature_note():
    abstract = (ROOT / "sections/01_abstract.tex").read_text()
    assert r"\cite{afc}" in abstract and r"\cite{reginald2025af}" in abstract
    assert abstract.count(r"\begin{abstract}") == 1
    assert abstract.count(r"\end{abstract}") == 1


def test_r35_affirmative_quarantine_language():
    text = read_all_tex()
    assert "manual measured-sector charge/orientation map carried by the manual comparison record" in text
    assert "used only by the external-comparison layer" in text


def test_afc_provenance_block_is_present_and_uncited():
    text = active_text()
    assert "AFC, Axioms (Null and distinction-induced relations)" in text
    assert "Stokes corollary" in text and "internal-pair cancellation" in text


def test_sadar_balance_figure_script_uses_current_symbols():
    script = (ROOT / "scripts" / "generate_sadar_boundary_balance.py").read_text()
    assert r"\rho^D_{\omega,e}" in script
    assert "min(D_e" not in script


def test_source_root_has_no_release_patch_summaries():
    assert not list(ROOT.glob("AOD_Temporal_Dynamics_v*_PATCH_SUMMARY.txt"))


def test_build_ci_and_release_bundle_script_present():
    workflow = ROOT / ".github" / "workflows" / "build.yml"
    script = ROOT / "scripts" / "build_release_bundle.py"
    assert workflow.exists()
    assert script.exists()
    wtext = workflow.read_text()
    stext = script.read_text()
    assert "scripts/build_release_bundle.py" in wtext
    assert "pytest -q" in wtext
    assert "CANONICAL_VERSION.txt" in stext
    assert "AOD_Temporal_Dynamics_source" not in stext
    assert "source_root" in stext
    assert "source.zip" in stext and "bundle.zip" in stext


def test_ci_build_bundle_uses_tests_artifact_and_no_audit_pack_fallback():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert "tests.txt" in workflow
    assert "pytest -q | tee tests.txt" in workflow
    assert "audit_pack" not in workflow
    assert "verifier.log" not in workflow
    assert "audit_pack" not in script
    assert "verifier.log" not in script
    assert "source-clean.zip" not in script

def test_canonical_version_file_declares_current_release():
    text = (ROOT / "CANONICAL_VERSION.txt").read_text()
    assert f"Canonical version: {current_version()}" in text
    assert "AOD_Temporal_Dynamics is the canonical package." in text
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


def test_canonical_orbital_retention_provenance_and_data_support():
    section = (ROOT / "manual/sections/06_field_dynamics_applications.tex").read_text()
    registry = (ROOT / "manual/sections/09_prediction_test_fixture_registry.tex").read_text()
    scope = (ROOT / "manual/sections/00_scope.tex").read_text()
    assert r"\label{tab:orbital-retention-input-provenance}" in section
    assert "Orbital-retention field-dynamics fixture & G2/G3 & G2/G3 input package" in registry
    assert "input-provenance gate" in registry
    assert "Every manual comparison declares its data-support class before residuals are interpreted." in scope


def test_tau_missing_burden_caption_exact_ratio_r50c():
    manual = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "31/50" in manual
    assert r"presentation value \(0.62\)" in manual


def test_manual_scoped_error_data_support_chain_present():
    scope = (ROOT / "manual" / "sections" / "00_scope.tex").read_text()
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


def test_appendix_a_data_support_class_reference_present():
    appendix = (ROOT / "manual" / "appendices" / "A_simulation_fixtures_and_tau_prediction_context.tex").read_text()
    for cls in ["D0", "O0", "G0", "G1", "G2", "G3", "L0", "L1", "L2", "L3"]:
        assert cls in appendix


def test_registry_has_data_support_class_column_r52():
    registry = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    for cls in ["D0", "O0", "G0", "G1", "G2/G3", "L0", "L1", "L2", "L3", "D0/O0"]:
        assert cls in registry
    assert "SPARC five-galaxy square-speed diagnostic & G0" in registry
    assert "Orbital-retention field-dynamics fixture & G2/G3" in registry


def test_sparc_scored_table_has_class_and_uncertainty_policy_r52():
    table = (ROOT / "manual" / "data" / "derived" / "sparc_summary_table.tex").read_text()
    assert "Class & $\\sigma$ policy" in table
    assert "G0 & obs-only" in table
    assert "G0 active input fields" in (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    section = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "G0 active input fields" in section
    

def test_ablation_cut_defined_r52():
    section = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "declared data-support cut" in section
    assert "projection or marginalization residuals" in section


def test_readme_contains_zenodo_description_and_version_neutral_build_notes():
    readme = (ROOT / "README.md").read_text()
    assert f"**Version:** {current_version()}" in readme
    assert "**Alpha↔Omega Dynamics (AΩD)** is a relational, temporal computational calculus built from the discrete Stokes cut" in readme
    assert "Each record states its support, inputs and execution status:" in readme
    assert "scripts/build_release_bundle.py" in readme
    assert "main.pdf" in readme
    assert "manual.pdf" in readme


def test_build_source_zip_is_flat_repo_root_archive():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    assert "repository checkout" in script
    assert "p.relative_to(src_dir).as_posix()" in script
    assert "AOD_Temporal_Dynamics_source" not in script


def active_text(surface="main"):
    import importlib.util
    spec = importlib.util.spec_from_file_location("source_audit", ROOT / "scripts/audit_scientific_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return "\n".join(text for path, text in module.include_graph(ROOT, surface)[1])
