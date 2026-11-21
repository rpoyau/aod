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


def test_f04_complete_native_parent_identity_and_prefix_binding_regressions():
    mod = _load_alignment_module()
    n = mod.native

    # 1. Two separately admitted native.recurrent parents sharing lineage/scope strings at scales 0 and 1
    w0 = n.recurrent("W", n=3, spacing=10, scope="B:main", scale=0)
    w1 = n.recurrent("W", n=3, spacing=10, scope="B:main", scale=1)
    _check(w0.identity != w1.identity, "native Wave identities at scales 0 and 1 must differ")

    occ0 = mod.project_admitted_wave_occurrences(w0)
    occ1 = mod.project_admitted_wave_occurrences(w1)
    both_canonical = mod.build_occurrence_registry((*occ0, *occ1))

    sw0 = mod.restrict_admitted_wavelet(w0, "sw0", (2, 12), registry=both_canonical)
    sw1 = mod.restrict_admitted_wavelet(w1, "sw1", (2, 12), registry=both_canonical)
    mod.validate_complete_windows((sw0, sw1), both_canonical)
    _check(
        mod.deduplicated_return_count((sw0,), w0, registry=both_canonical) == 1
        and mod.deduplicated_return_count((sw1,), w1, registry=both_canonical) == 1
        and mod.deduplicated_return_count((sw0,), "W", registry=both_canonical) == 1
        and mod.deduplicated_return_count((sw1,), "W", registry=both_canonical) == 1,
        "each admitted scale parent must contribute 1 reclosure in (2, 12]",
    )

    # Combining distinct scale parents in one single-parent wavelet must fail
    _reject(
        lambda: mod.make_wavelet(
            "w_mixed",
            "W",
            ("W:ancestor",),
            (2, 12),
            "seated_duad",
            "local_segment",
            tuple(r["trace_digest"] for r in (*occ0[:2], *occ1[:2])),
            (*occ0[:2], *occ1[:2]),
            registry=both_canonical,
        ),
        ValueError,
        "parent",
    )
    # Forged dict bypass into eligibility, completeness, and union counting must also fail
    forged_mixed = dict(sw0, return_witnesses=(*occ0[:2], *occ1[:2]))
    _reject(
        lambda: mod.eligible_return_ids(forged_mixed, registry=both_canonical),
        ValueError,
        "parent_descriptor",
    )
    _reject(
        lambda: mod.validate_complete_windows((forged_mixed,), both_canonical),
        ValueError,
        "parent_descriptor",
    )
    _reject(
        lambda: mod.deduplicated_return_count((forged_mixed,), w0, registry=both_canonical),
        ValueError,
        "parent_descriptor",
    )

    # Aggregating two separately created wavelets from distinct parents as one current must fail
    _reject(
        lambda: mod.deduplicated_return_count((sw0, sw1), "W", registry=both_canonical),
        ValueError,
        "incompatible parent",
    )
    _reject(
        lambda: mod.deduplicated_return_count((sw0, sw1), w0, registry=both_canonical),
        ValueError,
        "incompatible parent",
    )
    _reject(
        lambda: mod.deduplicated_return_count((sw1,), w0, registry=both_canonical),
        ValueError,
        "parent_descriptor",
    )

    # Same-scale distinct admitted parents (different origin return) also reject mixing/aggregation
    w0_shifted = n.wave(
        [n.certified(n.trace("W", k, start_index=1 + k * 10, scope="B:main", scale=0)) for k in range(3)]
    )
    occ0_shifted = mod.project_admitted_wave_occurrences(w0_shifted)
    same_scale_both = mod.build_occurrence_registry((*occ0, *occ0_shifted))
    sw0_shifted = mod.restrict_admitted_wavelet(
        w0_shifted, "sw0_shifted", (3, 13), registry=same_scale_both
    )
    _reject(
        lambda: mod.deduplicated_return_count((sw0, sw0_shifted), "W", registry=same_scale_both),
        ValueError,
        "incompatible parent",
    )

    # Ambiguous bare lineage string on empty window across multiple canonical parents rejects
    _reject(
        lambda: mod.make_wavelet(
            "w_ambig", "W", ("W:ancestor",), (15, 19),
            "seated_duad", "local_segment", ("rec:0",), (), registry=both_canonical,
        ),
        ValueError,
        "ambiguous parent lineage string",
    )
    w_unbound_empty = mod.make_wavelet(
        "w_unbound_empty", "W", ("W:ancestor",), (2, 12),
        "seated_duad", "local_segment", ("rec:0",), (),
    )
    _reject(
        lambda: mod.validate_complete_windows((w_unbound_empty,), occ0),
        ValueError,
        "omitted",
    )

    # Same admitted parent overlapping windows deduplicate and preserve out-of-window support
    sw0_left = mod.restrict_admitted_wavelet(w0, "sw0_left", (2, 12), registry=occ0)
    sw0_right = mod.restrict_admitted_wavelet(w0, "sw0_right", (5, 22), registry=occ0)
    mod.validate_complete_windows((sw0_left, sw0_right), occ0)
    _check(
        len(mod.eligible_return_ids(sw0_left, registry=occ0))
        + len(mod.eligible_return_ids(sw0_right, registry=occ0))
        == 3
        and mod.deduplicated_return_count((sw0_left, sw0_right), w0, registry=occ0) == 2,
        "same-parent overlapping windows must deduplicate shared return",
    )

    # Prefix digest substitution & origin index promotion rejected
    bad_prefix = deepcopy(occ0[1])
    bad_prefix["lineage_prefix_digest"] = "0" * 64
    _reject(
        lambda: mod.make_wavelet(
            "w_bad_pref", w0, ("W:ancestor",), (2, 12),
            "seated_duad", "local_segment", (occ0[1]["trace_digest"],), (occ0[0], bad_prefix),
        ),
        ValueError,
        "lineage_prefix_digest",
    )
    _reject(
        lambda: mod.deduplicated_return_count(
            (dict(sw0, return_witnesses=(occ0[0], bad_prefix)),), w0, registry=occ0
        ),
        ValueError,
        "lineage_prefix_digest",
    )
    promoted_origin = deepcopy(occ0[0])
    promoted_origin["occurrence_j"] = 1
    _reject(
        lambda: mod.build_occurrence_registry((promoted_origin,)),
        ValueError,
        "lineage_prefix_ids",
    )


def test_f05_supplied_registry_authority_and_explicit_extension_regressions():
    mod = _load_alignment_module()
    w0 = mod.native.recurrent("W", n=3, spacing=10, scope="B:main", scale=0)
    occ = mod.project_admitted_wave_occurrences(w0)
    full_reg = mod.build_occurrence_registry(occ)
    selected = mod.restrict_admitted_wavelet(
        w0, "w_sel", (2, 12), retained_occurrences=occ[:2], registry=full_reg
    )

    fixed_origin_only = mod.build_occurrence_registry((occ[0],))
    snapshot_keys = tuple(fixed_origin_only.keys())

    # Eligibility, completeness, and union aggregation must all reject the absent first reclosure
    _reject(
        lambda: mod.eligible_return_ids(selected, registry=fixed_origin_only),
        ValueError,
        "absent from canonical occurrence registry",
    )
    _reject(
        lambda: mod.validate_complete_windows((selected,), fixed_origin_only),
        ValueError,
        "absent from canonical occurrence registry",
    )
    _reject(
        lambda: mod.deduplicated_return_count((selected,), w0, registry=fixed_origin_only),
        ValueError,
        "absent from canonical occurrence registry",
    )
    _reject(
        lambda: mod.deduplicated_return_count((selected,), "W", registry=fixed_origin_only),
        ValueError,
        "absent from canonical occurrence registry",
    )
    _check(tuple(fixed_origin_only.keys()) == snapshot_keys, "supplied registry was mutated")

    # Explicit empty registry rejects absent witnesses, whereas registry=None performs conditional union
    _reject(
        lambda: mod.deduplicated_return_count((selected,), w0, registry=()),
        ValueError,
        "absent from canonical occurrence registry",
    )
    _check(
        mod.deduplicated_return_count((selected, selected), w0, registry=None) == 1,
        "explicit no-registry conditional union failed",
    )

    # Deliberate upstream extension permits the selected return without mutating fixed_origin_only
    extended = mod.extend_occurrence_registry(fixed_origin_only, (occ[1],))
    _check(tuple(fixed_origin_only.keys()) == snapshot_keys, "extend_occurrence_registry mutated input")
    _check(
        len(mod.eligible_return_ids(selected, registry=extended)) == 1
        and len(mod.validate_complete_windows((selected,), extended)) == 2
        and mod.deduplicated_return_count((selected,), w0, registry=extended) == 1,
        "deliberate upstream registry extension did not validate selected return",
    )


def test_f06_mapped_recipient_replay_preserves_index_and_prefix_regressions():
    mod = _load_alignment_module()
    n = mod.native

    witness = {
        "parent_id": "P",
        "emit_boundary": "boundary:P",
        "cut_coordinate": "K",
        "emit_cut": 12,
        "route": "exo",
        "X_route": Fraction(1, 2),
        "post_shed_parent_state": "P:post12",
    }
    stage_events = {
        "delivered": mod.make_stage_event("ev:d:12", "delivered", "B:recipient", "K", 12),
        "accepted": mod.make_stage_event("ev:a:13", "accepted", "B:recipient", "K", 13),
        "seated": mod.make_stage_event("ev:s:14", "seated", "B:recipient", "K", 14),
    }
    path = ("emitted", "delivered", "accepted", "seated", "reclosed")

    s0 = n.certified(n.trace("R", 0, start_index=1, scope="B:source"))
    s1 = n.certified(n.trace("R", 1, start_index=13, scope="B:source"))
    s2 = n.certified(n.trace("R", 2, start_index=16, scope="B:source"))
    projected = mod.project_admitted_lineage_occurrences((s0, s1, s2), cut_coordinate="K")
    scope_map = mod.declare_conditional_scope_map(
        "map:source-to-recipient", "B:source", "B:recipient", "R", projected
    )
    map_snapshot = deepcopy(scope_map)

    # Fresh C2 at j=2 succeeds and contributes 1 bip
    fresh_ctx = {
        "recipient_lineage": "R",
        "recipient_scope": "B:recipient",
        "cut_coordinate": "K",
        "window": (10, 25),
        "prior_certified_returns": (s0, s1),
    }
    fresh_res = mod.evaluate_recipient_stage(
        witness, fresh_ctx, path, s2, stage_events=stage_events, recipient_scope_map=scope_map
    )
    _check(
        fresh_res["stage"] == "reclosed"
        and fresh_res["closure_phase_delta"] == 1
        and fresh_res["reclosure_bip_delta"] == 1
        and fresh_res["occurrence_j"] == 2,
        "mapped fresh C2 evaluation failed",
    )

    # Append exact certified s2 to prior history; replay s2 (j=2) and s1 (j=1) with unchanged map
    replay_ctx = dict(fresh_ctx, prior_certified_returns=(s0, s1, s2))
    rep_c2 = mod.evaluate_recipient_stage(
        witness, replay_ctx, path, s2, stage_events=stage_events, recipient_scope_map=scope_map
    )
    rep_c1 = mod.evaluate_recipient_stage(
        witness, replay_ctx, path, s1, stage_events=stage_events, recipient_scope_map=scope_map
    )
    _check(
        rep_c2["stage"] == "reclosed_replay"
        and rep_c2["closure_phase_delta"] == 0
        and rep_c2["reclosure_bip_delta"] == 0
        and rep_c2["occurrence_j"] == 2
        and rep_c1["stage"] == "reclosed_replay"
        and rep_c1["closure_phase_delta"] == 0
        and rep_c1["reclosure_bip_delta"] == 0
        and rep_c1["occurrence_j"] == 1
        and scope_map == map_snapshot,
        "mapped replay failed to preserve original occurrence_j and zero-bip result",
    )

    # Mapped initial origin (j=0) and subsequent origin replay using one unchanged multi-return map
    o0 = n.certified(n.trace("R", 0, start_index=14, scope="B:source"))  # ends 16 >= 14
    o1 = n.certified(n.trace("R", 1, start_index=18, scope="B:source"))  # ends 20
    o_proj = mod.project_admitted_lineage_occurrences((o0, o1), cut_coordinate="K")
    o_map = mod.declare_conditional_scope_map(
        "map:origin-and-next", "B:source", "B:recipient", "R", o_proj
    )
    orig_res = mod.evaluate_recipient_stage(
        witness,
        dict(fresh_ctx, prior_certified_returns=()),
        path[:-1] + ("closed_origin",),
        o0,
        stage_events=stage_events,
        recipient_scope_map=o_map,
    )
    orig_rep = mod.evaluate_recipient_stage(
        witness,
        dict(fresh_ctx, prior_certified_returns=(o0,)),
        path,
        o0,
        stage_events=stage_events,
        recipient_scope_map=o_map,
    )
    _check(
        orig_res["stage"] == "closed_origin"
        and orig_res["closure_phase_delta"] == 1
        and orig_res["reclosure_bip_delta"] == 0
        and orig_res["occurrence_j"] == 0
        and orig_rep["stage"] == "reclosed_replay"
        and orig_rep["closure_phase_delta"] == 0
        and orig_rep["reclosure_bip_delta"] == 0
        and orig_rep["occurrence_j"] == 0,
        "mapped origin and origin replay failed",
    )

    # Wrong map, payload mismatch on replay, and chronology inversion on replay still reject
    wrong_target_map = dict(scope_map, target_scope="B:other")
    _reject(
        lambda: mod.evaluate_recipient_stage(
            witness, replay_ctx, path, s2,
            stage_events=stage_events, recipient_scope_map=wrong_target_map,
        ),
        ValueError,
        "scope_map",
    )
    corrupted_bound_map = deepcopy(scope_map)
    corrupted_bound_map["bound_occurrences"][s2[0].return_id] = ("corrupted",)
    _reject(
        lambda: mod.evaluate_recipient_stage(
            witness, replay_ctx, path, s2,
            stage_events=stage_events, recipient_scope_map=corrupted_bound_map,
        ),
        ValueError,
        "conflicts with bound occurrence in scope_map",
    )
    late_emit = dict(witness, emit_cut=19)
    late_events = {
        "delivered": mod.make_stage_event("ev:d:19", "delivered", "B:recipient", "K", 19),
        "accepted": mod.make_stage_event("ev:a:19", "accepted", "B:recipient", "K", 19),
        "seated": mod.make_stage_event("ev:s:19", "seated", "B:recipient", "K", 19),
    }
    _reject(
        lambda: mod.evaluate_recipient_stage(
            late_emit, replay_ctx, path, s2,
            stage_events=late_events, recipient_scope_map=scope_map,
        ),
        ValueError,
        "precedes",
    )


def test_f07_mapped_completeness_unrelated_canonical_parent_regressions():
    mod = _load_alignment_module()
    n = mod.native

    # Exact R03 construction: Parent A and independent Parent B share W / B:source / scale 0
    parent_a = n.recurrent("W", n=3, spacing=10, scope="B:source", scale=0)
    parent_b = n.wave(
        [
            n.certified(n.trace("W", 100 + k, start_index=1 + 10 * k, scope="B:source", scale=0))
            for k in range(3)
        ]
    )
    # Also include an unrelated parent C with an occurrence completing strictly inside (2, 12]
    parent_c = n.wave(
        [
            n.certified(n.trace("W", 200 + k, start_index=1 + 8 * k, scope="B:source", scale=0))
            for k in range(3)
        ]
    )
    _check(
        parent_a.identity != parent_b.identity and parent_a.identity != parent_c.identity,
        "distinct native parents must have distinct identities",
    )

    occ_a = mod.project_admitted_wave_occurrences(parent_a)
    occ_b = mod.project_admitted_wave_occurrences(parent_b)
    occ_c = mod.project_admitted_wave_occurrences(parent_c)
    own_a = mod.build_occurrence_registry(occ_a)
    combined_ab = mod.build_occurrence_registry((*occ_a, *occ_b))
    combined_abc = mod.build_occurrence_registry((*occ_a, *occ_b, *occ_c))
    _check(
        len(combined_ab) == 6
        and n.closure_cycle_count(
            [(r["trace"], r["certificate"], r["certificate_registry"]) for r in combined_ab.values()]
        )
        == 6,
        "combined A+B native closure count must be 6",
    )

    smap = mod.declare_conditional_scope_map("map-W-only", "B:source", "B:main", "W", occ_a)
    w_mapped = mod.make_wavelet(
        "mapped-W",
        parent_a,
        ("W:ancestor",),
        (2, 12),
        "seated_duad",
        "local_segment",
        tuple(r["trace_digest"] for r in occ_a[:2]),
        occ_a[:2],
        scope_id="B:main",
        scope_map=smap,
        registry=combined_ab,
    )

    # Positive controls: own-only, A+B combined, A+B+C (in-window unrelated completion), and local combined
    _check(
        len(mod.eligible_return_ids(w_mapped, scope_map=smap, registry=combined_ab)) == 1
        and mod.deduplicated_return_count((w_mapped,), parent_a, scope_map=smap, registry=combined_ab)
        == 1
        and len(mod.validate_complete_windows((w_mapped,), own_a, scope_map=smap)) == 3
        and len(mod.validate_complete_windows((w_mapped,), combined_ab, scope_map=smap)) == 6
        and len(mod.validate_complete_windows((w_mapped,), combined_abc, scope_map=smap)) == 9,
        "F07 mapped completeness must succeed with unrelated canonical parents and preserve count 1",
    )
    local_a = mod.restrict_admitted_wavelet(parent_a, "local-W", (2, 12), registry=combined_ab)
    _check(
        len(mod.validate_complete_windows((local_a,), combined_ab)) == 6
        and mod.deduplicated_return_count(
            (local_a,), parent_a, target_scope="B:source", registry=combined_ab
        )
        == 1,
        "local combined-registry completeness regression failed",
    )

    # Parent-discovery loops on empty mapped wavelets also classify by full source_parent_root_key
    w_empty_between = mod.make_wavelet(
        "mapped-W-empty-15-19",
        "W",
        ("W:ancestor",),
        (15, 19),
        "seated_duad",
        "local_segment",
        ("retained-prefix",),
        (),
        scope_id="B:main",
        scope_map=smap,
        registry=combined_abc,
    )
    _check(
        len(mod.validate_complete_windows((w_empty_between,), combined_abc, scope_map=smap)) == 9
        and mod.deduplicated_return_count(
            (w_empty_between,), parent_a, scope_map=smap, registry=combined_abc
        )
        == 0,
        "empty mapped wavelet between returns failed on multi-parent registry",
    )
    # Empty mapped wavelet on (2, 12] omitting A's return @12 rejects completeness; absent/wrong map rejects
    w_empty_omitting = mod.make_wavelet(
        "mapped-W-empty-2-12",
        parent_a,
        ("W:ancestor",),
        (2, 12),
        "seated_duad",
        "local_segment",
        ("retained-prefix",),
        (),
        scope_id="B:main",
        scope_map=smap,
        registry=combined_ab,
    )
    _reject(
        lambda: mod.validate_complete_windows((w_empty_omitting,), combined_ab, scope_map=smap),
        ValueError,
        "omitted",
    )
    _reject(
        lambda: mod.validate_complete_windows((w_empty_omitting,), combined_ab, scope_map=None),
        ValueError,
        "explicit validated scope_map",
    )

    # Retained strict negatives against combined multi-parent registry:
    # 1. Relevant own-parent return omitted from asserted-complete window (2, 22]
    w_omit = mod.make_wavelet(
        "mapped-W-omit",
        parent_a,
        ("W:ancestor",),
        (2, 22),
        "seated_duad",
        "local_segment",
        tuple(r["trace_digest"] for r in occ_a[:2]),
        occ_a[:2],
        scope_id="B:main",
        scope_map=smap,
        registry=combined_ab,
    )
    _reject(
        lambda: mod.validate_complete_windows((w_omit,), combined_ab, scope_map=smap),
        ValueError,
        "omitted",
    )
    # 2. Relevant own-parent return (@22) absent from supplied partial map (must not be filtered away)
    partial_map = mod.declare_conditional_scope_map(
        "map-W-only", "B:source", "B:main", "W", occ_a[:2]
    )
    _reject(
        lambda: mod.validate_complete_windows((w_omit,), combined_ab, scope_map=partial_map),
        ValueError,
        "is not bound in supplied scope_map",
    )
    # 3. Selected witness payload conflict with bound map
    bad_map = deepcopy(smap)
    bad_map["bound_occurrences"][occ_a[1]["return_id"]] = ("corrupted-payload",)
    _reject(
        lambda: mod.eligible_return_ids(w_mapped, scope_map=bad_map, registry=combined_ab),
        ValueError,
        "payload conflicts",
    )
    _reject(
        lambda: mod.validate_complete_windows((w_mapped,), combined_ab, scope_map=bad_map),
        ValueError,
        "payload conflicts",
    )
    # 4. Selected witness belonging to unrelated parent B still rejects strictly
    _reject(
        lambda: mod.make_wavelet(
            "wrong-parent-selected",
            parent_a,
            ("W:ancestor",),
            (2, 12),
            "seated_duad",
            "local_segment",
            tuple(r["trace_digest"] for r in (*occ_a[:2], *occ_b[:2])),
            (*occ_a[:2], *occ_b[:2]),
            scope_id="B:main",
            scope_map=smap,
            registry=combined_ab,
        ),
        ValueError,
        "source parent identity mismatch",
    )
    # 5. Absent, Boolean, and wrong-domain maps reject
    _reject(
        lambda: mod.validate_complete_windows((w_mapped,), combined_ab, scope_map=None),
        ValueError,
        "explicit validated scope_map",
    )
    for flag in (False, True):
        _reject(
            lambda flag=flag: mod.validate_complete_windows(
                (w_mapped,), combined_ab, scope_map=flag
            ),
            ValueError,
            "Boolean flag",
        )
    wrong_domain_map = dict(smap, target_scope="B:other")
    _reject(
        lambda: mod.validate_complete_windows((w_mapped,), combined_ab, scope_map=wrong_domain_map),
        ValueError,
        "scope_map",
    )
    # 6. Selected return absent from explicitly supplied registry rejects (F05 preserved)
    _reject(
        lambda: mod.deduplicated_return_count(
            (w_mapped,), parent_a, scope_map=smap, registry=(occ_a[0],)
        ),
        ValueError,
        "absent from canonical occurrence registry",
    )


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
        test_f04_complete_native_parent_identity_and_prefix_binding_regressions,
        test_f05_supplied_registry_authority_and_explicit_extension_regressions,
        test_f06_mapped_recipient_replay_preserves_index_and_prefix_regressions,
        test_f07_mapped_completeness_unrelated_canonical_parent_regressions,
        test_cli_runner_parity_and_standalone_mode_metadata,
    )
    for fn in fns:
        fn()
    return {"status": "PASS", "tests_run": len(fns), "optimized_mode": not __debug__}


if __name__ == "__main__":
    print(json.dumps(run_standalone(), indent=2, sort_keys=True))
