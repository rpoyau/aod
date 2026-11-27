"""Complete 17-sector execution registry and dual data-dependency coverage audit.

Maintains two separately auditable sets per S2_SPEC.md:
1. Execution obligations: 17 named sectors (9 Tier 1 + 7 Tier 2 + 1 Tier 3).
2. Covered data dependencies: all 18 subdirectories under manual/data/ (124 files)
   plus root wavelet_shedding_simulation.csv and cycle_shedding_summary.tex.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from manual.engine.numeric import require

EXPECTED_MANUAL_DATA_SUBDIRS: tuple[str, ...] = (
    "awareness",
    "boundary_sadar",
    "brownian",
    "cell_measures",
    "dec",
    "derived",
    "experimental_comparison",
    "higgs",
    "historical_metrology",
    "lensing",
    "mapping_error",
    "native_closure_wave",
    "run_tumble",
    "sparc",
    "tau",
    "temporal_anchor",
    "temporal_metrology",
    "temporal_observation",
)

EXPECTED_MANUAL_DATA_FILE_COUNT: int = 136

EXPECTED_ROOT_DATA_FILES: tuple[str, ...] = (
    "cycle_shedding_summary.tex",
    "wavelet_shedding_simulation.csv",
)

_HISTORICAL_METROLOGY_FILES: tuple[str, ...] = (
    "manual/data/historical_metrology/historical_target/manual2/data/m1/bipm/raw/ClockOutputCovData2025_mod_basis_n=153_TAI_05092025_ExpandUncV1_AdHocCorrV2_2.dat",
    "manual/data/historical_metrology/historical_target/manual2/data/m1/bipm/raw/ClockOutputData2025_mod_basis_n=153_TAI_05092025_ExpandUncV1_AdHocCorrV2_2.dat",
    "manual/data/historical_metrology/historical_target/manual2/scripts/matter1_bipm.py",
    "manual/data/historical_metrology/historical_target/manual2/scripts/matter1_metrology.py",
    "manual/data/historical_metrology/historical_target/sections/06_wave_state_relational_time.tex",
    "manual/data/historical_metrology/original-output.json",
    "manual/data/historical_metrology/prior_mapping_error.json",
    "manual/data/historical_metrology/probe_metrology_edges.py",
    "manual/data/historical_metrology/source_bindings.json",
)

_TEMPORAL_METROLOGY_FILES: tuple[str, ...] = (
    "manual/data/temporal_metrology/cesium/notes.md",
    "manual/data/temporal_metrology/cesium/protocol.json",
    "manual/data/temporal_metrology/cesium/source/heavner2014.pdf",
    "manual/data/temporal_metrology/cesium/source/source_receipt.json",
    "manual/data/temporal_metrology/exact_fixtures.json",
    "manual/data/temporal_metrology/hydrogen/notes.md",
    "manual/data/temporal_metrology/hydrogen/protocol.json",
    "manual/data/temporal_metrology/hydrogen/reported_uncertainty.json",
    "manual/data/temporal_metrology/hydrogen/source/hellwig1970.pdf",
    "manual/data/temporal_metrology/hydrogen/source/source_receipt.json",
    "manual/data/temporal_metrology/report.json",
)

_TEMPORAL_ANCHOR_FILES: tuple[str, ...] = (
    "manual/data/temporal_anchor/cases/baseline.json.gz",
    "manual/data/temporal_anchor/cases/compared_population.json.gz",
    "manual/data/temporal_anchor/cases/reference_exposure.json.gz",
    "manual/data/temporal_anchor/cases/second_support_pair.json.gz",
    "manual/data/temporal_anchor/inputs.json",
    "manual/data/temporal_anchor/report.json",
    "manual/data/temporal_anchor/source/baseline/input/MODEL.json",
    "manual/data/temporal_anchor/source/baseline/input/PREDECESSOR_BINDING.json",
    "manual/data/temporal_anchor/source/baseline/input/PREDECESSOR_MODEL.json",
    "manual/data/temporal_anchor/source/baseline/input/SOURCE_BINDING.json",
    "manual/data/temporal_anchor/source/baseline/input/common_reference.py",
    "manual/data/temporal_anchor/source/baseline/input/pair_trial.py",
    "manual/data/temporal_anchor/source/baseline/input/population.py",
    "manual/data/temporal_anchor/source/baseline/input/results/background_only.couplings.json.gz",
    "manual/data/temporal_anchor/source/baseline/input/results/background_only.histories.json.gz",
    "manual/data/temporal_anchor/source/baseline/input/results/background_only.summary.json",
    "manual/data/temporal_anchor/source/baseline/input/results/direct_pair.couplings.json.gz",
    "manual/data/temporal_anchor/source/baseline/input/results/direct_pair.histories.json.gz",
    "manual/data/temporal_anchor/source/baseline/input/results/direct_pair.summary.json",
    "manual/data/temporal_anchor/source/baseline/input/results/recorded_only.couplings.json.gz",
    "manual/data/temporal_anchor/source/baseline/input/results/recorded_only.histories.json.gz",
    "manual/data/temporal_anchor/source/baseline/input/results/recorded_only.summary.json",
    "manual/data/temporal_anchor/source/baseline/input/upstream/LICENSE",
    "manual/data/temporal_anchor/source/baseline/input/upstream/appendices/H_combinatorics_rd_tests.tex",
    "manual/data/temporal_anchor/source/baseline/input/upstream/manual/scripts/aod_m3_temporal.py",
    "manual/data/temporal_anchor/source/baseline/input/upstream/manual/scripts/aod_mapping_error.py",
    "manual/data/temporal_anchor/source/baseline/input/upstream/manual/scripts/aod_native_closure_wave.py",
    "manual/data/temporal_anchor/source/baseline/input/upstream/sections/05_curl_closure_duon_current.tex",
    "manual/data/temporal_anchor/source/baseline/input/upstream/sections/06_field.tex",
    "manual/data/temporal_anchor/source/baseline/input/upstream/sections/06_wave_state_relational_time.tex",
    "manual/data/temporal_anchor/source/baseline/results/window_records.json",
    "manual/data/temporal_anchor/source/baseline/si_bridge.py",
    "manual/data/temporal_anchor/source/results/admitted_validation.json",
    "manual/data/temporal_anchor/source/results/endpoint_perturbations.json",
    "manual/data/temporal_anchor/source/results/report.json",
    "manual/data/temporal_anchor/source/results/rolling_count_windows.json",
    "manual/data/temporal_anchor/source_members.json",
)

_SPARC_ROTMOD_FILES: tuple[str, ...] = (
    "manual/data/sparc/DDO154_rotmod.dat",
    "manual/data/sparc/NGC2403_rotmod.dat",
    "manual/data/sparc/NGC2841_rotmod.dat",
    "manual/data/sparc/NGC3198_rotmod.dat",
    "manual/data/sparc/NGC6503_rotmod.dat",
)


@dataclass(frozen=True)
class SectorSpec:
    """Immutable metadata contract for one registered Stage 2 verification sector."""

    sector_id: str
    adapter_id: str
    tier: str
    bound_source_operation: str
    invocation: tuple[str, ...]
    input_paths: tuple[str, ...]
    data_subdirs: tuple[str, ...]
    required_outputs: tuple[tuple[str, int], ...]
    capability: str
    scientific_status: str
    retained_holds: tuple[str, ...]

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "bound_source_operation": self.bound_source_operation,
            "capability": self.capability,
            "data_subdirs": list(self.data_subdirs),
            "input_paths": list(self.input_paths),
            "invocation": list(self.invocation),
            "required_outputs": {k: v for k, v in self.required_outputs},
            "retained_holds": list(self.retained_holds),
            "scientific_status": self.scientific_status,
            "sector_id": self.sector_id,
            "tier": self.tier,
        }


SECTOR_SPECS: tuple[SectorSpec, ...] = (
    # --- Tier 1: 9 Canonical Subprocess Adapters ---
    SectorSpec(
        sector_id="native_closure_wave",
        adapter_id="tier1.native_closure_wave",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_native_closure_wave.py --check-data",
        invocation=("manual/scripts/aod_native_closure_wave.py", "--check-data"),
        input_paths=(
            "manual/data/native_closure_wave/closure_phase_reclosure.csv",
            "manual/data/native_closure_wave/h1_composite_paths.csv",
            "manual/data/native_closure_wave/harmonic_reconstruction.csv",
            "manual/data/native_closure_wave/motif_fold_fusion.csv",
            "manual/data/native_closure_wave/relational_time_coupling.csv",
            "manual/scripts/aod_native_closure_wave.py",
        ),
        data_subdirs=("native_closure_wave",),
        required_outputs=(("fixtures_total", 83), ("fixtures_passed", 83)),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "sympy_exact_dft_declared_in_FOURIER_SCOPE_md",
            "no_universal_dynamics_or_physical_metrology_inferred",
        ),
    ),
    SectorSpec(
        sector_id="awareness",
        adapter_id="tier1.awareness",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_awareness.py --check-data",
        invocation=("manual/scripts/aod_awareness.py", "--check-data"),
        input_paths=(
            "contracts/scientific/AWARENESS_ACTIVE_CAUSAL_SPEC.json",
            "contracts/scientific/OPERATIVE_SELF_SCHEMA.json",
            "contracts/scientific/OWNERSHIP_AND_FIXTURES.json",
            "manual/data/awareness/awareness_cases.jsonl",
            "manual/scripts/aod_awareness.py",
            "manual/scripts/aod_native_closure_wave.py",
        ),
        data_subdirs=("awareness",),
        required_outputs=(("fixtures_total", 47), ("fixtures_passed", 47)),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "declared_finite_causal_model_only",
            "historical_19_toys_SOURCE_MISSING_rerun_claim_NONE",
        ),
    ),
    SectorSpec(
        sector_id="cell_measures",
        adapter_id="tier1.cell_measures",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_cell_measures.py --check-data",
        invocation=("manual/scripts/aod_cell_measures.py", "--check-data"),
        input_paths=(
            "contracts/scientific/CELL_MEASURE_SPEC.json",
            "manual/data/cell_measures/cells_geometry.json",
            "manual/scripts/aod_cell_measures.py",
        ),
        data_subdirs=("cell_measures",),
        required_outputs=(
            ("disk_refinement_levels", 6),
            ("negative_controls", 12),
            ("pi_reference_comparisons", 3),
            ("tesseract_4d_levels", 6),
        ),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "native_metric_not_established",
            "native_higher_cell_status_not_established",
            "physical_metric_unknown",
            "G6_4d_tesseract_to_pi_declared_model_only",
        ),
    ),
    SectorSpec(
        sector_id="mapping_error",
        adapter_id="tier1.mapping_error",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_mapping_error.py --check",
        invocation=("manual/scripts/aod_mapping_error.py", "--check"),
        input_paths=(
            "contracts/scientific/ERROR_BUDGET.json",
            "contracts/scientific/MAP_CONTRACT.json",
            *_HISTORICAL_METROLOGY_FILES,
            "manual/data/mapping_error/mapping_error.json",
            "manual/scripts/aod_mapping_error.py",
        ),
        data_subdirs=("historical_metrology", "mapping_error"),
        required_outputs=(
            ("maps", 3),
            ("historical_laws", 2),
            ("historical_bound_files", 8),
        ),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "MAP-07_open_higher_cell_extraction",
            "MAP-28_open_source_precision_BIPM_zero_policy",
            "G6_sphere_extension_not_opened",
            "physical_model_discrepancy_unknown",
            "transitive_decimal_presentation_in_mapping_error_and_historical_replay",
        ),
    ),
    SectorSpec(
        sector_id="temporal_observation",
        adapter_id="tier1.temporal_observation",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_temporal_observation.py --check",
        invocation=("manual/scripts/aod_temporal_observation.py", "--check"),
        input_paths=(
            "contracts/scientific/TEMPORAL_OBSERVATION.json",
            "manual/data/temporal_observation/temporal.json",
            "manual/scripts/aod_mapping_error.py",
            "manual/scripts/aod_native_closure_wave.py",
            "manual/scripts/aod_temporal_observation.py",
        ),
        data_subdirs=("temporal_observation",),
        required_outputs=(("schema_version", 3), ("gain_countermodels", 2)),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "atomic_prediction_incomplete",
            "complete_physical_standard_uncertainty_unknown",
            "known_H_previously_exposed_no_blind_claim",
            "physical_applicability_unknown",
        ),
    ),
    SectorSpec(
        sector_id="temporal_metrology",
        adapter_id="tier1.temporal_metrology",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_temporal_metrology.py --check",
        invocation=("manual/scripts/aod_temporal_metrology.py", "--check"),
        input_paths=(
            "contracts/scientific/TEMPORAL_METROLOGY.json",
            *_TEMPORAL_METROLOGY_FILES,
            "manual/scripts/aod_temporal_metrology.py",
        ),
        data_subdirs=("temporal_metrology",),
        required_outputs=(
            ("hydrogen_reductions", 3),
            ("cesium_campaigns", 2),
            ("primary_source_receipts", 2),
            ("bound_data_files", 11),
        ),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "separate_H_maser_and_Cs_fountain_chains",
            "complete_physical_uncertainty_unknown",
            "no_universal_seconds_per_bip",
            "no_raw_experimental_phase_reconstruction",
            "independent_atomic_prediction_not_established",
            "nuclear_dynamics_not_implemented",
        ),
    ),
    SectorSpec(
        sector_id="experimental_comparison",
        adapter_id="tier1.experimental_comparison",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_experimental_comparison.py --check",
        invocation=("manual/scripts/aod_experimental_comparison.py", "--check"),
        input_paths=(
            "contracts/scientific/ERROR_BUDGET.json",
            "contracts/scientific/MAP_CONTRACT.json",
            "contracts/scientific/TEMPORAL_METROLOGY.json",
            "contracts/scientific/TEMPORAL_OBSERVATION.json",
            "manual/data/experimental_comparison/experimental_input_comparison.json",
            "manual/scripts/aod_experimental_comparison.py",
        ),
        data_subdirs=("experimental_comparison",),
        required_outputs=(
            ("quantity_routes", 10),
            ("reduction_controls", 5),
            ("code_bindings", 9),
        ),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "independent_validation_false",
            "corrections_applied_false",
            "physical_discrepancy_unresolved",
            "freeze_does_not_establish_chronological_blindness",
        ),
    ),
    SectorSpec(
        sector_id="temporal_anchor",
        adapter_id="tier1.temporal_anchor",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_temporal_anchor.py --check-data (nested: manual/scripts/aod_anchor_replay.py)",
        invocation=("manual/scripts/aod_temporal_anchor.py", "--check-data"),
        input_paths=(
            *_TEMPORAL_ANCHOR_FILES,
            "manual/scripts/aod_anchor_replay.py",
            "manual/scripts/aod_temporal_anchor.py",
        ),
        data_subdirs=("temporal_anchor",),
        required_outputs=(
            ("generated_outputs", 6),
            ("anchor_cases", 4),
            ("nested_replay_checks", 33),
            ("scientific_source_members", 30),
        ),
        capability="declared_fixture_replay",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "retrospective_count_transfer_controls_only",
            "fixed_transfer_fails_heldout_validation_A_minus_5_29_B_minus_49_151",
            "independent_reference_evidence_false",
            "physical_Cs_observation_law_none",
            "physical_SI_prediction_none",
        ),
    ),
    SectorSpec(
        sector_id="wavelet_si_alignment",
        adapter_id="tier1.wavelet_si_alignment",
        tier="tier1_canonical_adapter",
        bound_source_operation="manual/scripts/aod_manual_wavelet_si_alignment.py --check (check_p2_01..15)",
        invocation=("manual/scripts/aod_manual_wavelet_si_alignment.py", "--check"),
        input_paths=(
            "contracts/scientific/CANONICAL_BINDINGS.json",
            "contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json",
            "manual/data/derived/tau_ring_diagnostic.csv",
            "manual/data/tau/aod_tau_fractal_ring_summary.csv",
            "manual/scripts/aod_manual_wavelet_si_alignment.py",
            "wavelet_shedding_simulation.csv",
        ),
        data_subdirs=("derived", "tau"),
        required_outputs=(
            ("check_groups", 13),
            ("p2_checks_covered", 15),
            ("frozen_files_verified", 192),
            ("phase1_equations_bound", 10),
        ),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "physical_SI_holds_preserved",
            "open_shedding_90_rows_do_not_certify_native_reclosure_or_exo",
            "tau_ring_generator_unresolved_not_authenticated",
            "deliberate_3_0_negative_control_literal_at_line_3002_outside_engine",
        ),
    ),
    # --- Tier 2: 7 Pure Zero-Float Data & Boundary SADAR Verifiers ---
    SectorSpec(
        sector_id="dec_ledger",
        adapter_id="tier2.dec_ledger",
        tier="tier2_exact_data_verifier",
        bound_source_operation="manual.engine.sectors.tier2_exact:verify_dec_ledger",
        invocation=("manual.engine.sectors.tier2_exact:verify_dec_ledger",),
        input_paths=(
            "manual/data/dec/dec_hinge_slide_example.csv",
            "manual/data/dec/dec_one_node_ledger_example.csv",
            "manual/data/dec/field_tunnelling_hinge_slide_window_clip.csv",
            "manual/data/dec/tau_missing_burden_exact_ratio_patch.csv",
        ),
        data_subdirs=("dec",),
        required_outputs=(
            ("one_node_rows", 4),
            ("hinge_slide_rows", 3),
            ("tunnelling_rows", 3),
            ("tau_ratio_patch_rows", 1),
        ),
        capability="declared_fixture_replay",
        scientific_status="CONFORMANT_DECLARED_FIXTURE",
        retained_holds=(
            "verifies_dec_fixture_conformance_only",
            "raw_AFC_execution_precedes_passive_trace_and_motif_naming",
        ),
    ),
    SectorSpec(
        sector_id="higgs_trace",
        adapter_id="tier2.higgs_trace",
        tier="tier2_exact_data_verifier",
        bound_source_operation="manual.engine.sectors.tier2_exact:verify_higgs_trace",
        invocation=("manual.engine.sectors.tier2_exact:verify_higgs_trace",),
        input_paths=(
            "manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv",
            "manual/data/higgs/higgs_external_map_after_candidate_freeze.csv",
            "manual/data/higgs/higgs_trace_internal_candidates_selection.csv",
            "manual/data/higgs/higgs_trace_score_formula.md",
            "manual/data/higgs/yro_aliases_and_renames.csv",
        ),
        data_subdirs=("higgs",),
        required_outputs=(
            ("internal_candidates", 8),
            ("freeze_map_rows", 4),
            ("lhc_comparison_rows", 4),
            ("yro_alias_rows", 3),
        ),
        capability="retained_data_conformance",
        scientific_status="RETAINED_DATA_CONFORMANT",
        retained_holds=(
            "target_quarantine_enforced_declared_evaluation_order_only",
            "does_not_establish_historical_pre_exposure_freeze",
            "originating_history_producer_detector_thresholds_and_exponent_exposure_history_held",
        ),
    ),
    SectorSpec(
        sector_id="phase_delta3_3d",
        adapter_id="tier2.phase_delta3_3d",
        tier="tier2_exact_data_verifier",
        bound_source_operation="manual.engine.sectors.tier2_exact:verify_phase_delta3_3d",
        invocation=("manual.engine.sectors.tier2_exact:verify_phase_delta3_3d",),
        input_paths=(
            "manual/data/brownian/brownian_displacements.csv",
            "manual/data/brownian/brownian_sample_track.csv",
            "manual/data/brownian/displacement_q_counts.csv",
            "manual/data/brownian/integer_motion_ratios.csv",
            "manual/data/brownian/octant_delta3.csv",
            "manual/data/brownian/phase_cycle_delta3.csv",
            "manual/data/run_tumble/run_tumble_integer_motion_ratios.csv",
            "manual/data/run_tumble/run_tumble_octant_delta3.csv",
            "manual/data/run_tumble/run_tumble_phase_cycle_delta3.csv",
            "manual/data/run_tumble/run_tumble_trace_20_ticks.csv",
            "manual/data/run_tumble/run_tumble_trace_table.tex",
        ),
        data_subdirs=("brownian", "run_tumble"),
        required_outputs=(
            ("brownian_track_points", 9),
            ("brownian_displacements", 8),
            ("run_tumble_trace_rows", 21),
            ("run_tumble_active_ticks", 20),
        ),
        capability="declared_fixture_replay",
        scientific_status="CONFORMANT_DECLARED_FIXTURE",
        retained_holds=(
            "verifies_track_to_delta3_conformance_only",
            "does_not_assert_kernel_generation_of_track",
            "continuous_diffusion_summaries_remain_downstream_presentation",
        ),
    ),
    SectorSpec(
        sector_id="cycle_shedding",
        adapter_id="tier2.cycle_shedding",
        tier="tier2_exact_data_verifier",
        bound_source_operation="manual.engine.sectors.tier2_exact:verify_cycle_shedding",
        invocation=("manual.engine.sectors.tier2_exact:verify_cycle_shedding",),
        input_paths=(
            "cycle_shedding_summary.tex",
            "wavelet_shedding_simulation.csv",
        ),
        data_subdirs=(),
        required_outputs=(
            ("simulation_rows", 90),
            ("open_state_rows", 90),
            ("summary_table_entries", 8),
        ),
        capability="retained_data_conformance",
        scientific_status="RETAINED_DATA_CONFORMANT",
        retained_holds=(
            "90_open_rows_do_not_certify_native_reclosure_or_exoshedding",
            "retained_legacy_float_records_verified_only_against_inherited_1e_12_bound",
            "lambda_reclose_19_50_is_model_fraction_not_certified_return",
        ),
    ),
    SectorSpec(
        sector_id="lensing_tallies",
        adapter_id="tier2.lensing_tallies",
        tier="tier2_exact_data_verifier",
        bound_source_operation="manual.engine.sectors.tier2_exact:verify_lensing_tallies",
        invocation=("manual.engine.sectors.tier2_exact:verify_lensing_tallies",),
        input_paths=(
            "manual/data/lensing/k4_3d_timeflow_input_gate.csv",
            "manual/data/lensing/k4_3d_timeflow_input_gate_table.tex",
            "manual/data/lensing/sparc5_lensing_class_tallies.csv",
            "manual/data/lensing/sparc5_medium_diagnostic_summary.csv",
            "manual/data/lensing/sparc5_medium_diagnostic_summary_table.tex",
            "manual/data/lensing/swells_k0_target_tallies_delta3_acquisition.csv",
            "manual/data/lensing/swells_k0_target_tallies_table.tex",
            "manual/data/lensing/swells_k1_k2_k3_comparison_table.tex",
            "manual/data/lensing/swells_k1_k2_k3_delta3_comparison.csv",
            "manual/data/lensing/swells_k1_thetaE_delta3_scores.csv",
            "manual/data/lensing/toy1_delta3_class_tallies.csv",
            "manual/data/lensing/toy1_verification_checks.csv",
            *_SPARC_ROTMOD_FILES,
        ),
        data_subdirs=("lensing", "sparc"),
        required_outputs=(
            ("k4_gate_rows", 9),
            ("toy1_checks_passed", 11),
            ("sparc5_galaxies", 5),
            ("swells_k1_k2_k3_runs", 3),
        ),
        capability="retained_data_conformance",
        scientific_status="RETAINED_DATA_CONFORMANT",
        retained_holds=(
            "K1_target_selected_development_baseline_not_blind_validation",
            "per_system_SWELLS_inputs_cohort_membership_and_gate_evaluator_missing",
            "K4_L3_3D_timeflow_input_gate_not_opened",
            "sparc5_medium_proxy_carries_no_lensing_image_targets",
        ),
    ),
    SectorSpec(
        sector_id="sparc_five_galaxy",
        adapter_id="tier2.sparc_five_galaxy",
        tier="tier2_exact_data_verifier",
        bound_source_operation="manual.engine.sectors.tier2_exact:verify_sparc_five_galaxy",
        invocation=("manual.engine.sectors.tier2_exact:verify_sparc_five_galaxy",),
        input_paths=(
            "manual/data/derived/sparc_five_galaxy_per_bin.csv",
            "manual/data/derived/sparc_five_galaxy_per_galaxy.csv",
            "manual/data/derived/sparc_summary_table.tex",
            *_SPARC_ROTMOD_FILES,
        ),
        data_subdirs=("derived", "sparc"),
        required_outputs=(
            ("galaxies", 5),
            ("per_bin_rows", 209),
            ("summary_table_rows", 5),
        ),
        capability="retained_data_conformance",
        scientific_status="RETAINED_DATA_CONFORMANT",
        retained_holds=(
            "G0_radial_shell_observation_only_sigma_U_linearized_diagnostic",
            "V_disp_is_non_scoring_display_only",
            "legacy_float_recorded_columns_not_claimed_exact_residuals_reported",
            "carried_sparc_declaration_controls_excluded_and_quarantined_in_tier3",
        ),
    ),
    SectorSpec(
        sector_id="boundary_sadar",
        adapter_id="tier2.boundary_sadar",
        tier="tier2_exact_data_verifier",
        bound_source_operation="manual.engine.sectors.boundary_sadar:verify_boundary_sadar",
        invocation=("manual.engine.sectors.boundary_sadar:verify_boundary_sadar",),
        input_paths=(
            "manual/data/boundary_sadar/awareness_operativity_dec_walk.csv",
            "manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv",
            "manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv",
            "manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv",
            "manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv",
            "manual/data/boundary_sadar/dimonhexon_double_slit_ring_paths.csv",
            "manual/data/boundary_sadar/higgs_baryon_overlap_saddle_scan.csv",
            "manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv",
            "manual/data/boundary_sadar/hydrogen_shell_exact_series.csv",
            "manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv",
            "manual/data/boundary_sadar/native_closure_wave_dec_walk.csv",
            "manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv",
            "manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv",
            "manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv",
            "manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv",
            "manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv",
            "manual/data/boundary_sadar/sparc_pooled_primary_exact.csv",
            "manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv",
            "manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv",
            "manual/data/boundary_sadar/typed_map_joint_law_ledger.csv",
            *_SPARC_ROTMOD_FILES,
        ),
        data_subdirs=("boundary_sadar", "sparc"),
        required_outputs=(
            ("boundary_sadar_csvs_verified", 20),
            ("rest_energy_carriers_verified", 10),
            ("higgs_saddle_candidates_scanned", 20),
            ("hydrogen_transitions_verified", 14),
            ("sparc_pooled_bins_verified", 209),
        ),
        capability="canonical_calculation",
        scientific_status="AUTHENTICATED_EXACT",
        retained_holds=(
            "external_SI_and_PDG_targets_quarantined_in_B_ext_comparators_only",
            "universal_SI_bridge_open_until_second_independent_observable_closed",
            "passive_ReadOnly_sensor_wall_zero_observer_back_reaction",
            "pooled_SPARC_G0_radial_shell_observation_only",
        ),
    ),
    # --- Tier 3: 1 Provenance Quarantine Guard ---
    SectorSpec(
        sector_id="provenance_quarantine",
        adapter_id="tier3.provenance_quarantine",
        tier="tier3_provenance_guard",
        bound_source_operation="manual.engine.sectors.tier3_quarantine:verify_provenance_quarantine",
        invocation=("manual.engine.sectors.tier3_quarantine:verify_provenance_quarantine",),
        input_paths=(
            "manual/data/derived/sparc_declaration_controls.csv",
            "manual/data/derived/tau_declaration_controls.csv",
            "manual/data/derived/tau_ring_diagnostic.csv",
            "manual/data/tau/aod_tau_fractal_ring_baseline_compatible.csv",
            "manual/data/tau/aod_tau_fractal_ring_comparison.csv",
            "manual/data/tau/aod_tau_fractal_ring_primary_lane_audit.csv",
            "manual/data/tau/aod_tau_fractal_ring_summary.csv",
            "manual/data/tau/aod_tau_fractal_ring_top_cells.csv",
            "manual/data/tau/aod_tau_fractal_ring_verification.csv",
        ),
        data_subdirs=("derived", "tau"),
        required_outputs=(
            ("quarantined_files_verified", 9),
            ("tau_1210_summary_depth_rows", 3),
            ("sparc_carried_controls", 4),
            ("tau_carried_controls", 4),
        ),
        capability="provenance_guard",
        scientific_status="UNRESOLVED_PROVENANCE_QUARANTINED",
        retained_holds=(
            "quarantine_PASS_does_not_authenticate_SPARC_carried_controls_or_Tau_generator",
            "tau_1210_9_20_distinct_from_nominal_23_50_difference_1_100",
            "sparc_declaration_variant_recipes_and_aggregation_provenance_missing",
            "tau_fractal_ring_generator_unauthenticated_held_for_S3",
        ),
    ),
)

SECTOR_MAP: dict[str, SectorSpec] = {spec.sector_id: spec for spec in SECTOR_SPECS}


def verify_registry_completeness() -> None:
    """Fail-closed static integrity check on the 17-sector execution registry."""
    require(len(SECTOR_SPECS) == 17, f"expected 17 registered sectors, got {len(SECTOR_SPECS)}")
    sector_ids = [spec.sector_id for spec in SECTOR_SPECS]
    adapter_ids = [spec.adapter_id for spec in SECTOR_SPECS]
    require(len(set(sector_ids)) == 17, "duplicate sector_id in registry")
    require(len(set(adapter_ids)) == 17, "duplicate adapter_id in registry")
    tier_counts: dict[str, int] = {}
    for spec in SECTOR_SPECS:
        require(bool(spec.input_paths), f"sector {spec.sector_id} has empty input_paths")
        require(bool(spec.required_outputs), f"sector {spec.sector_id} has empty required_outputs")
        require(
            len(set(spec.input_paths)) == len(spec.input_paths),
            f"sector {spec.sector_id} has duplicate input_paths",
        )
        tier_counts[spec.tier] = tier_counts.get(spec.tier, 0) + 1
    require(
        tier_counts
        == {
            "tier1_canonical_adapter": 9,
            "tier2_exact_data_verifier": 7,
            "tier3_provenance_guard": 1,
        },
        f"unexpected tier distribution: {tier_counts}",
    )


def registry_digest() -> str:
    """Deterministic SHA-256 digest of the complete canonical 17-sector registry."""
    verify_registry_completeness()
    payload = [spec.to_canonical_dict() for spec in SECTOR_SPECS]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_data_coverage(repo_root: Path) -> dict[str, object]:
    """Verify complete dual coverage of manual/data/ (18 subdirs, 124 files) and root CSV/TeX."""
    verify_registry_completeness()
    root = Path(repo_root).resolve()
    data_root = root / "manual" / "data"
    require(data_root.is_dir() and not data_root.is_symlink(), "manual/data directory missing or symlink")

    actual_subdirs = sorted(
        p.name for p in data_root.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    require(
        tuple(actual_subdirs) == EXPECTED_MANUAL_DATA_SUBDIRS,
        f"manual/data subdirectories mismatch: actual={actual_subdirs}, expected={list(EXPECTED_MANUAL_DATA_SUBDIRS)}",
    )

    actual_data_files: list[str] = []
    for path in sorted(data_root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        require(not path.is_symlink(), f"symlink forbidden under manual/data: {rel}")
        if path.is_file():
            actual_data_files.append(rel)

    require(
        len(actual_data_files) == EXPECTED_MANUAL_DATA_FILE_COUNT,
        f"expected {EXPECTED_MANUAL_DATA_FILE_COUNT} files under manual/data/, found {len(actual_data_files)}",
    )

    file_to_sectors: dict[str, list[str]] = {}
    for spec in SECTOR_SPECS:
        for rel in spec.input_paths:
            file_to_sectors.setdefault(rel, []).append(spec.sector_id)

    uncovered_manual_data = [f for f in actual_data_files if f not in file_to_sectors]
    require(
        not uncovered_manual_data,
        f"uncovered files under manual/data/: {uncovered_manual_data}",
    )

    for root_rel in EXPECTED_ROOT_DATA_FILES:
        rpath = root / root_rel
        require(
            rpath.is_file() and not rpath.is_symlink(),
            f"required root data file missing or symlink: {root_rel}",
        )
        require(
            root_rel in file_to_sectors,
            f"root data file uncovered by registry: {root_rel}",
        )

    overlap_map = {
        rel: sorted(sectors)
        for rel, sectors in sorted(file_to_sectors.items())
        if len(sectors) > 1
        and (rel.startswith("manual/data/") or rel in EXPECTED_ROOT_DATA_FILES)
    }

    return {
        "status": "PASS",
        "manual_data_subdirs": len(actual_subdirs),
        "manual_data_files": len(actual_data_files),
        "root_data_files": len(EXPECTED_ROOT_DATA_FILES),
        "uncovered_files": 0,
        "declared_data_overlaps": overlap_map,
    }


def get_sector(sector_id: str) -> SectorSpec:
    """Return a registered SectorSpec by exact sector_id or raise KeyError."""
    if sector_id not in SECTOR_MAP:
        raise KeyError(f"unknown sector_id: {sector_id!r}")
    return SECTOR_MAP[sector_id]
