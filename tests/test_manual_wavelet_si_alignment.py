"""Manual wavelet continuation and conditional SI alignment verification tests.

Executable both via pytest and directly under normal `python3` and `python3 -O`
without relying on bare `assert` statements for active checks. Includes targeted
regressions for PR #46 AF review findings F01, F02, F03, and N01.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import re
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


def _reject(callable_obj, exc_type, match: str | None = None) -> None:
    try:
        callable_obj()
    except exc_type as exc:
        if match is not None and not re.search(match, str(exc)):
            raise AssertionError(
                f"expected error matching {match!r}, got {str(exc)!r}"
            ) from exc
        return
    raise AssertionError(f"expected {exc_type.__name__} to be raised")


def test_p2_01_same_current_seating_and_independent_roles():
    mod = _load_alignment_module()
    out = mod.check_p2_01()
    _check(out["duon_variants"] == 12 and out["independent_seat_role"] is True, "P2-01 failed")


def test_p2_02_localized_wavelet_ancestry_and_non_termination():
    mod = _load_alignment_module()
    out = mod.check_p2_02()
    _check(
        out["parent_retained"] is True
        and out["parent_active_beyond_v"] is True
        and out["default_scope_map_absent"] is True,
        "P2-02 failed",
    )


def test_p2_03_04_window_eligibility_and_overlap_deduplication():
    mod = _load_alignment_module()
    out = mod.check_p2_03_04()
    _check(
        out["overlap_naive_sum"] == 4
        and out["overlap_deduplicated_union"] == 3
        and out["native_trace_overlap_union"] == 3
        and out["omitted_return_rejected"] is True
        and out["payload_conflict_collision_alias_rejected"] is True
        and out["unmapped_cross_scope_rejected"] is True,
        "P2-03/P2-04 failed",
    )


def test_p2_05_06_shed_witness_recipient_stages_and_passive_transport():
    mod = _load_alignment_module()
    out = mod.check_p2_05_06()
    _check(
        out["closed_origin_bips"] == 0
        and out["replay_bips"] == 0
        and out["fresh_reclosure_bips"] == 1
        and out["out_of_window_bips"] == 0
        and out["pre_emission_completion_rejected"] is True
        and out["boolean_certificate_rejected"] is True,
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
        out["nonzero_modes"] == [0, 3, 6, 9]
        and out["v_hat_3"] == "1/4"
        and out["parseval_exact"] == "1/4"
        and out["certifies_native_reclosure_or_si_frequency"] is False,
        "P2-15 failed",
    )


def test_f01_canonical_occurrence_binding_collision_and_alias_regressions():
    mod = _load_alignment_module()

    def make_w(records):
        return mod.make_wavelet(
            "w", "W", ("ancestor",), (0, 8),
            "seated_duad", "coupled_segment", ("retained-prefix",), tuple(records),
        )

    # 1. Fixed-registry payload conflict under unchanged ID 'C1' inside (0, 8]
    known = mod.make_return_witness("C1", 1, 2, "W", "B:main")
    changed = mod.make_return_witness("C1", 2, 6, "W", "B:main")
    w_conflict = make_w((changed,))
    _reject(
        lambda: mod.validate_complete_windows((w_conflict,), (known,)),
        ValueError,
        "conflicts with canonical occurrence record",
    )
    _reject(
        lambda: mod.deduplicated_return_count((w_conflict,), "W", registry=(known,)),
        ValueError,
        "collision",
    )

    # 2. Return ID collision: two different completions assigned same ID
    col1 = mod.make_return_witness("collision", 1, 2, "W", "B:main")
    col2 = mod.make_return_witness("collision", 2, 6, "W", "B:main")
    _reject(lambda: make_w((col1, col2)), ValueError, "collision")
    _reject(lambda: mod.build_occurrence_registry((col1, col2)), ValueError, "collision")

    # 3. Alias: one canonical occurrence assigned two IDs (same wavelet and split across wavelets)
    al1 = mod.make_return_witness("C1", 1, 2, "W", "B:main")
    al2 = mod.make_return_witness("C1-repackaged", 1, 2, "W", "B:main")
    _reject(lambda: make_w((al1, al2)), ValueError, "aliased under multiple return_ids")
    w_a = make_w((al1,))
    w_b = make_w((al2,))
    _reject(
        lambda: mod.deduplicated_return_count((w_a, w_b), "W"),
        ValueError,
        "aliased under multiple return_ids",
    )

    # 4. Idempotent repackaging of identical valid occurrence remains count 1
    w_idem = make_w((known, deepcopy(known)))
    mod.validate_complete_windows((w_idem,), (known,))
    _check(mod.deduplicated_return_count((w_idem,), "W", registry=(known,)) == 1, "idempotency failed")

    # 5. Tampering with an admitted native Trace/Certificate witness rejected;
    #    single admitted closure derives origin occurrence_j == 0 (never >= 1)
    w_nat = mod.native.recurrent("W_tamper", n=3, spacing=10, scope="B:main", scale=0)
    occ = mod.project_admitted_wave_occurrences(w_nat)
    single_occ = mod.project_admitted_lineage_occurrences(
        [(occ[0]["trace"], occ[0]["certificate"], occ[0]["certificate_registry"])]
    )
    _check(single_occ[0]["occurrence_j"] == 0, "single admitted closure must derive origin j=0")
    tampered = dict(occ[1], completion_cut=occ[1]["completion_cut"] + 1)
    _reject(lambda: mod.build_occurrence_registry((occ[0], tampered)), ValueError, "diverges")
    forged_trace = replace(occ[1]["trace"], ancestor="forged:ancestor")
    _reject(
        lambda: mod.project_admitted_lineage_occurrences(
            [(forged_trace, occ[1]["certificate"], occ[1]["certificate_registry"])]
        ),
        mod.native.AdmissionError,
    )

    # 6. Empty string committed record rejected
    _reject(
        lambda: mod.make_wavelet(
            "w_empty_rec", "W", ("ancestor",), (0, 4),
            "seated_duad", "coupled_segment", ("",), (known,), is_admitted_wave=True,
        ),
        ValueError,
        "committed record",
    )


def test_f02_explicit_cross_scope_map_regressions():
    mod = _load_alignment_module()
    c_unrel = mod.make_return_witness("C1", 1, 2, "W", "unrelated-scope")

    # Omitted scope_map argument must reject cross-scope witness
    _reject(
        lambda: mod.make_wavelet(
            "w", "W", ("ancestor",), (0, 8),
            "seated_duad", "coupled_segment", ("retained-prefix",), (c_unrel,),
        ),
        ValueError,
        "explicit validated scope_map",
    )
    # Explicit False and True booleans must both be rejected
    for flag in (False, True):
        _reject(
            lambda flag=flag: mod.make_wavelet(
                "w", "W", ("ancestor",), (0, 8),
                "seated_duad", "coupled_segment", ("retained-prefix",), (c_unrel,),
                scope_map=flag,
            ),
            ValueError,
            "Boolean flag",
        )
    # Implicit scope_mapped key injected into witness dict rejected
    injected = dict(c_unrel, scope_mapped=True)
    _reject(lambda: mod.build_occurrence_registry((injected,)), ValueError, "scope_mapped")

    # Valid same-scope works directly without any map
    c_same = mod.make_return_witness("C1", 1, 2, "W", "B:main")
    w_same = mod.make_wavelet(
        "w_same", "W", ("ancestor",), (0, 8),
        "seated_duad", "coupled_segment", ("retained-prefix",), (c_same,),
        is_admitted_wave=True,
    )
    _check(mod.deduplicated_return_count((w_same,), "W") == 1, "same-scope direct eligibility failed")


def test_f03_recipient_chronology_and_certificate_regressions():
    mod = _load_alignment_module()
    shed = {
        "parent_id": "P",
        "emit_boundary": "B:shared",
        "cut_coordinate": "shared_committed_k",
        "emit_cut": 19,
        "route": "exo",
        "X_route": Fraction(1, 2),
        "post_shed_parent_state": "Ppost19",
    }
    r0 = mod.native.certified(mod.native.trace("R", 0, scope="B:shared", start_index=1))   # ends 3
    r1 = mod.native.certified(mod.native.trace("R", 1, scope="B:shared", start_index=11))  # ends 13
    r2_at_18 = mod.native.certified(mod.native.trace("R", 2, scope="B:shared", start_index=16))  # ends 18
    context = {
        "recipient_lineage": "R",
        "recipient_scope": "B:shared",
        "cut_coordinate": "shared_committed_k",
        "window": (10, 20),
        "prior_certified_returns": (r0, r1),
    }
    ev_19 = {
        "delivered": mod.make_stage_event("d", "delivered", "B:shared", "shared_committed_k", 19),
        "accepted": mod.make_stage_event("a", "accepted", "B:shared", "shared_committed_k", 19),
        "seated": mod.make_stage_event("s", "seated", "B:shared", "shared_committed_k", 19),
    }
    # Completion at 18 before emission at 19 on shared coordinate rejected
    _reject(
        lambda: mod.evaluate_recipient_stage(
            shed,
            context,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            r2_at_18,
            stage_events=ev_19,
        ),
        ValueError,
        "precedes",
    )
    # Bare Boolean has_certificate=True dict rejected
    r2_at_20 = mod.native.certified(mod.native.trace("R", 2, scope="B:shared", start_index=18))  # ends 20
    _reject(
        lambda: mod.evaluate_recipient_stage(
            shed,
            context,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            {
                "has_certificate": True,
                "lineage_id": "R",
                "scope_id": "B:shared",
                "cut_coordinate": "shared_committed_k",
                "return_id": "R2",
                "occurrence_j": 2,
                "completion_cut": 20,
            },
            stage_events=ev_19,
        ),
        ValueError,
        "has_certificate Boolean does not authenticate",
    )
    # Valid completion at cut 20 >= emission cut 19 with admitted certificate and stage events succeeds
    ok = mod.evaluate_recipient_stage(
        shed,
        context,
        ("emitted", "delivered", "accepted", "seated", "reclosed"),
        r2_at_20,
        stage_events=ev_19,
    )
    _check(ok["reclosure_bip_delta"] == 1 and ok["occurrence_j"] == 2, "valid post-emission reclosure failed")


def test_cli_runner_parity_and_standalone_mode_metadata():
    # N01: CLI runner JSON is byte-identical across normal and -O modes;
    # standalone test runner passes in both modes with intentional optimized_mode metadata difference.
    res_norm = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    res_opt = subprocess.run(
        [sys.executable, "-O", str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    _check(res_norm.stdout == res_opt.stdout, "alignment CLI normal and -O outputs diverged")
    parsed = json.loads(res_norm.stdout)
    _check(parsed["status"] == "PASS", "CLI alignment report did not pass")


def run_standalone() -> dict:
    fns = (
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
        test_f01_canonical_occurrence_binding_collision_and_alias_regressions,
        test_f02_explicit_cross_scope_map_regressions,
        test_f03_recipient_chronology_and_certificate_regressions,
        test_cli_runner_parity_and_standalone_mode_metadata,
    )
    for fn in fns:
        fn()
    return {"status": "PASS", "tests_run": len(fns), "optimized_mode": not __debug__}


if __name__ == "__main__":
    print(json.dumps(run_standalone(), indent=2, sort_keys=True))
