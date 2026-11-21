"""Manual wavelet continuation and conditional SI alignment verification tests.

Executable both via pytest and directly under normal `python3` and `python3 -O`
without relying on bare `assert` statements for active checks.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "manual" / "scripts" / "aod_manual_wavelet_si_alignment.py"


def _load_alignment_module():
    spec = importlib.util.spec_from_file_location("aod_manual_wavelet_si_alignment", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_p2_01_same_current_seating_and_independent_roles():
    mod = _load_alignment_module()
    out = mod.check_p2_01()
    _check(out["duon_variants"] == 12 and out["independent_seat_role"] is True, "P2-01 failed")


def test_p2_02_localized_wavelet_ancestry_and_non_termination():
    mod = _load_alignment_module()
    out = mod.check_p2_02()
    _check(out["parent_retained"] is True and out["parent_active_beyond_v"] is True, "P2-02 failed")


def test_p2_03_04_window_eligibility_and_overlap_deduplication():
    mod = _load_alignment_module()
    out = mod.check_p2_03_04()
    _check(
        out["overlap_naive_sum"] == 4
        and out["overlap_deduplicated_union"] == 3
        and out["omitted_return_rejected"] is True,
        "P2-03/P2-04 failed",
    )


def test_p2_05_06_shed_witness_recipient_stages_and_passive_transport():
    mod = _load_alignment_module()
    out = mod.check_p2_05_06()
    _check(
        out["closed_origin_bips"] == 0
        and out["replay_bips"] == 0
        and out["fresh_reclosure_bips"] == 1
        and out["out_of_window_bips"] == 0,
        "P2-05/P2-06 failed",
    )


def test_p2_07_cancellation_history_and_inner_outer_disjointness():
    mod = _load_alignment_module()
    out = mod.check_p2_07()
    _check(
        out["net_current"] == 0
        and out["retained_histories"] == 2
        and out["inner_outer_disjoint"] is True,
        "P2-07 failed",
    )


def test_p2_08_repeated_contact_cadence_and_single_contact_association():
    mod = _load_alignment_module()
    out = mod.check_p2_08()
    _check(
        out["coupled_ratio"] == "3/5"
        and out["zero_numerator_repeated_contact"] == "0"
        and out["single_contact_is_cadence"] is False,
        "P2-08 failed",
    )


def test_p2_09_nonrecurrent_localization_on_cs_window():
    mod = _load_alignment_module()
    out = mod.check_p2_09()
    _check(
        out["mean_frequency_hz"] == "0"
        and out["delta_theta_over_tau"] == "0"
        and out["universal_seconds_per_bip"] is False,
        "P2-09 failed",
    )


def test_p2_10_observation_map_and_signed_compared_advance():
    mod = _load_alignment_module()
    out = mod.check_p2_10()
    _check(
        out["signed_C_a"] == "-1/2"
        and out["signed_mean_frequency_hz"] == "-4596315885"
        and out["delta_theta_over_tau"] == "-1/2"
        and out["rate_kind"] == "signed_mean_phase_rate",
        "P2-10 failed",
    )


def test_p2_11_accumulated_si_endpoint_additivity_and_tau_angular():
    mod = _load_alignment_module()
    out = mod.check_p2_11()
    _check(
        out["ratio"] == "7/17"
        and out["delta_theta_over_tau"] == "7/2"
        and out["omega_bar_over_tau_hz"] == "64348422390/17",
        "P2-11 failed",
    )


def test_p2_12_apparatus_separation_and_unknown_budget():
    mod = _load_alignment_module()
    out = mod.check_p2_12()
    _check(
        out["h_exact_mean_hz"] == "14204057517679/10000"
        and out["cs_aug2013_typeB_1e15"] == "0.16"
        and out["cs_typical_typeB_1e15"] == "0.11"
        and out["unknown_uncertainty_preserved"] is True,
        "P2-12 failed",
    )


def test_p2_13_frozen_data_provenance_and_semantic_type_separation():
    mod = _load_alignment_module()
    out = mod.check_p2_13()
    _check(
        out["changed_csvs"] == 0
        and out["tau_ring_diagnostic_1210"] == "9/20"
        and out["rational_difference"] == "1/100"
        and out["shedding_certifies_native_reclosure_or_exo"] is False
        and out["bit_span_vs_summed_lineage_counts_rejected"] is True,
        "P2-13 failed",
    )


def test_p2_14_main_manual_conservation_and_external_references():
    mod = _load_alignment_module()
    out = mod.check_p2_14()
    _check(
        out["frozen_files_verified"] == 166
        and out["phase1_equations_bound_in_manual"] == 10
        and out["phase1_sections_bound_in_manual"] == 2,
        "P2-14 failed",
    )


def test_p2_15_fourier_scope_overtone_and_parseval():
    mod = _load_alignment_module()
    out = mod.check_p2_15()
    _check(
        out["v_hat_3"] == "1/4"
        and out["parseval_exact"] == "1/4"
        and out["certifies_native_reclosure_or_si_frequency"] is False,
        "P2-15 failed",
    )


def test_cli_normal_and_optimized_outputs_match():
    env_cmd_norm = [sys.executable, str(SCRIPT), "--check"]
    env_cmd_opt = [sys.executable, "-O", str(SCRIPT), "--check"]
    res_norm = subprocess.run(env_cmd_norm, cwd=ROOT, capture_output=True, text=True, check=True)
    res_opt = subprocess.run(env_cmd_opt, cwd=ROOT, capture_output=True, text=True, check=True)
    _check(res_norm.stdout == res_opt.stdout, "normal and -O CLI outputs diverged")
    parsed = json.loads(res_norm.stdout)
    _check(parsed["status"] == "PASS", "CLI alignment report did not pass")


def run_standalone() -> dict:
    for fn in (
        test_p2_01_same_current_seating_and_independent_roles,
        test_p2_02_localized_wavelet_ancestry_and_non_termination,
        test_p2_03_04_window_eligibility_and_overlap_deduplication,
        test_p2_05_06_shed_witness_recipient_stages_and_passive_transport,
        test_p2_07_cancellation_history_and_inner_outer_disjointness,
        test_p2_08_repeated_contact_cadence_and_single_contact_association,
        test_p2_09_nonrecurrent_localization_on_cs_window,
        test_p2_10_observation_map_and_signed_compared_advance,
        test_p2_11_accumulated_si_endpoint_additivity_and_tau_angular,
        test_p2_12_apparatus_separation_and_unknown_budget,
        test_p2_13_frozen_data_provenance_and_semantic_type_separation,
        test_p2_14_main_manual_conservation_and_external_references,
        test_p2_15_fourier_scope_overtone_and_parseval,
        test_cli_normal_and_optimized_outputs_match,
    ):
        fn()
    return {"status": "PASS", "tests_run": 14, "optimized_mode": not __debug__}


if __name__ == "__main__":
    print(json.dumps(run_standalone(), indent=2, sort_keys=True))
