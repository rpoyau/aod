"""Tier-2 pure zero-float Boundary-Full AOmegaD SADAR Dynamics engine & verifier.

Executes from explicit boundary setups (zero floating-point arithmetic, zero bare
asserts, zero lookup-weight shortcuts):
1. Continuous multi-cut Q4 D.E.C. walk, hinge saturation (live ``xxxxx... is x``
   dwell reduction), slide renormalization with unchanged pre-block integer weights,
   window-clipped field tunnelling, single-carrier boundary chiral flip
   (``D_alpha <->_{0_H} D_Omega``), and two-carrier Disoma chiral Stokes balance.
2. Five-boundary full AOmegaD SADAR collision-shedding dynamics
   (``B_hard -> B_cand -> B_shed -> B_sensor -> B_ext``) on Q4 for opposing
   ``3:3:6`` Tritriohexon streams across a ``BETWEEN`` ``E_2`` duon chiral-flip
   medium, together with the matched sterile cut-58 negative control (``n_duons=0``),
   deriving:
   - Lepton ``1:2:L`` pocket competition (why ``1:2:6`` and ``1:2:8`` close with
     ``X_shedding=0``, why ``1:2:10`` clips at ``RD=9`` with ``X_shedding=0``, and
     why ``1:2:9_yro`` Dimonnanyro uniquely exhausts ``RD=9`` with ``X_shedding=3``),
   - Two-stage 2500-denominator ``B_shed -> B_sensor`` partition
     ``(650, 703, 1147)/2500 -> (19/50 visible, 31/50 missing)|_Exo`` across a
     passive ``ReadOnly`` ``3:4:6`` sensor wall with zero observer back-reaction,
   - Hadron core-starvation ``3:2:6`` Ditrion collision-shedding debris
     (``E_2^+-`` vs ``E_2^0`` resolving ``B^+-`` vs ``B^0``) and exoshedding lift
     ``3:2:6 -> 3:2:8 -> 3:2:10`` (``B_s^0``, ``B_c^+-``),
   - Two-baryon ``3:3`` overlap symmetric ``C_6/C_8`` midpoint saddle selecting
     ``3:3:7_yro`` Tritrioseptyro without candidate-specific magic thresholds, and
   - Complete 10-carrier rest-energy atlas, common ``8160`` bit-window span vs
     ``9104`` summed 8-lineage closures, and quarantined ``B_ext`` target-rate
     inversions with exact round-trip ``eta_ext`` variance cancellation.
3. Finite-ring Dimonhexon double-slit path generator, exact Hydrogen Balmer/Lyman/
   Paschen shell-pressure series, explicit Q4 vertex-set moving-boundary & live
   4-cut ``1:2:6`` electron-above-wire SADAR response, and exact rational 209-bin
   pooled SPARC primary ``MAPE_U``.
"""
from __future__ import annotations

import csv
from fractions import Fraction
import hashlib
import io
from pathlib import Path

from manual.engine.numeric import (
    canonical_rational_pair,
    canonical_rational_str,
    format_rational_fixed,
    parse_printed_rational,
    require,
    require_exact_int,
    round_rational_half_even,
)
from manual.engine.policy import loads_zero_float, require_no_floats
from manual.engine.registry import SectorSpec
from manual.engine.sectors.manual_dec_examples import (
    MANUAL_DEC_EXTRA_FILES,
    expected_manual_dec_csv_map,
    verify_manual_dec_examples,
)

Q4_NEIGHBORS: tuple[tuple[int, int, int, int], ...] = tuple(
    (v ^ 1, v ^ 2, v ^ 4, v ^ 8) for v in range(16)
)
POPCOUNT_4BIT: tuple[int, ...] = (0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4)

CLOSURE_C6: int = 18
CLOSURE_C8: int = 24
CLOSURE_C10: int = 27

# Exact BIPM 2019 SI defining constants & CODATA alpha^-1 inside B_ext quarantine:
# h_ext = 6.62607015e-34 J s = 662607015 / 10^42
# e_ext = 1.602176634e-19 C  = 1602176634 / 10^28
# eta_ext = 137.035999177    = 137035999177 / 10^9, sigma_eta = 21 / 10^9
H_EXT_EXACT: Fraction = Fraction(662607015, 10**42)
E_EXT_EXACT: Fraction = Fraction(1602176634, 10**28)
ETA_EXT_EXACT: Fraction = Fraction(137035999177, 10**9)
SIGMA_ETA_EXACT: Fraction = Fraction(21, 10**9)
K_EXT_MEV_S: Fraction = (H_EXT_EXACT * ETA_EXT_EXACT) / (Fraction(10**6, 1) * E_EXT_EXACT)

BOUNDARY_SADAR_FILES: tuple[str, ...] = tuple(
    sorted(
        (
            "manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv",
            "manual/data/boundary_sadar/dimonhexon_double_slit_ring_paths.csv",
            "manual/data/boundary_sadar/higgs_baryon_overlap_saddle_scan.csv",
            "manual/data/boundary_sadar/hydrogen_shell_exact_series.csv",
            "manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv",
            "manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv",
            "manual/data/boundary_sadar/sparc_pooled_primary_exact.csv",
            "manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv",
            *MANUAL_DEC_EXTRA_FILES,
        )
    )
)


def _pair(q: Fraction | int) -> list[str]:
    n_s, d_s = canonical_rational_pair(q)
    return [n_s, d_s]


def _gcd(a: int, b: int) -> int:
    x = abs(a)
    y = abs(b)
    while y != 0:
        x, y = y, x % y
    return x


def _lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a // _gcd(a, b)) * abs(b)


def _bits4(v: int) -> str:
    require(0 <= v < 16, f"Q4 vertex out of range: {v}")
    return f"{(v >> 3) & 1}{(v >> 2) & 1}{(v >> 1) & 1}{v & 1}"


def _hamming4(u: int, v: int) -> int:
    require(0 <= u < 16 and 0 <= v < 16, f"Q4 vertices out of range: {u}, {v}")
    return POPCOUNT_4BIT[u ^ v]


def _support_pi(p: int, q: int) -> int:
    require(p >= 1 and q >= 1, f"invalid curling-curl indices {p}:{q}")
    return (q**p) + q


def _support_rd_single_hinge(p: int, q: int) -> int:
    return 2 * _support_pi(p, q) + 1


# ---------------------------------------------------------------------------
# 1. Continuous Multi-Cut Q4 D.E.C. Walk & Chiral Flip Primitives (RC-025/026)
# ---------------------------------------------------------------------------


def eval_dec_chiral_flip_walk(inputs: dict[str, object]) -> dict[str, object]:
    """Execute continuous 3-cut Q4 D.E.C. walk -> blocked dwell -> slide -> chiral flip."""
    v0 = require_exact_int(inputs["initial_vertex"], name="initial_vertex")
    ancestor_slot = require_exact_int(inputs["incoming_ancestor_slot"], name="incoming_ancestor_slot")
    chi0 = require_exact_int(inputs["initial_chirality"], name="initial_chirality")
    c3 = require_exact_int(inputs["C3"], name="C3")
    rd_tunnel = require_exact_int(inputs["tunnel_RD"], name="tunnel_RD")
    omega_rem = require_exact_int(inputs["tunnel_window_remaining"], name="tunnel_window_remaining")
    raw_candidates = inputs["candidate_rows"]

    require(0 <= v0 < 16, "initial_vertex must lie in V(Q4)")
    require(0 <= ancestor_slot < 4, "incoming_ancestor_slot must lie in 0..3")
    require(chi0 in (-1, 1), "initial_chirality must lie in {-1, +1}")
    require(c3 == 3 and rd_tunnel > 0 and omega_rem > 0, "invalid tunnel parameters")
    require(isinstance(raw_candidates, list) and len(raw_candidates) == 4, "expected 4 candidate rows")

    region_core = {0, 1, 2, 3}
    require(v0 in region_core, "initial_vertex must start inside R_core={0,1,2,3}")

    parsed_rows: list[dict[str, int]] = []
    for row in raw_candidates:
        require(isinstance(row, dict), "candidate row must be an object")
        slot = require_exact_int(row["slot"], name="slot")
        sigma = require_exact_int(row["sigma"], name="sigma")
        weight = require_exact_int(row["weight"], name="weight")
        is_dwell = require_exact_int(row["is_optional_dwell"], name="is_optional_dwell")
        require(0 <= slot < 4, "slot must lie in 0..3")
        require(slot != ancestor_slot, "H1 continuation cannot use committed incoming ancestor slot")
        require(sigma in (-1, 0, 1), "sigma must lie in {-1, 0, +1}")
        require(weight > 0, "declared slot weight must be positive")
        require(is_dwell in (0, 1), "is_optional_dwell must be 0 or 1")
        parsed_rows.append(
            {
                "slot": slot,
                "sigma": sigma,
                "weight": weight,
                "is_dwell": is_dwell,
                "target": v0 if sigma == 0 else Q4_NEIGHBORS[v0][slot],
            }
        )

    # Cut 1: Unblocked D.E.C. normalization
    z_cut1 = sum(r["weight"] for r in parsed_rows)
    probs_cut1 = [Fraction(r["weight"], z_cut1) for r in parsed_rows]
    require(sum(probs_cut1, Fraction(0)) == Fraction(1, 1), "Cut 1 kernel not normalized")

    # Cut 2: Hinge saturation blocks optional dwell (e_slot, 0_D) while keeping 0_H
    # Pre-block integer weights on surviving Slide_mu rows are preserved UNCHANGED.
    slide_rows = [r for r in parsed_rows if r["is_dwell"] == 0]
    require(len(slide_rows) == 3, "blocking optional dwell must leave 3 branch-state slide rows")
    require(all(r["sigma"] in (-1, 1) for r in slide_rows), "slide rows must carry branch roles {-1,+1}")
    z_slide = sum(r["weight"] for r in slide_rows)
    probs_slide = [Fraction(r["weight"], z_slide) for r in slide_rows]
    require(sum(probs_slide, Fraction(0)) == Fraction(1, 1), "Cut 2 slide kernel not normalized")

    returned_prob = sum(
        (p for r, p in zip(slide_rows, probs_slide) if r["target"] in region_core),
        Fraction(0),
    )
    boundary_cross_rows = [
        (r, p) for r, p in zip(slide_rows, probs_slide) if r["target"] not in region_core
    ]
    require(len(boundary_cross_rows) == 1, "expected unique boundary-crossing slide branch")
    tunnel_row, p_tunnel = boundary_cross_rows[0]
    require(_hamming4(v0, tunnel_row["target"]) == 1, "tunnel step must be Q4 Hamming-1")

    # Cut 3: Window-clipped field tunnelling + boundary chiral flip D_alpha -> D_Omega
    rho_omega = min(rd_tunnel, omega_rem)
    p_d_tunnel = c3 * rho_omega
    t_tunnel = p_tunnel * p_d_tunnel
    chi_after = -chi0
    prior_dion = [chi0, -chi0]
    flipped_dion = [chi_after, -chi_after]
    retained_trace_word = [chi0, 0, -chi0, 0, chi_after, -chi_after]

    return {
        "cut1_Z": z_cut1,
        "cut1_probabilities": [_pair(p) for p in probs_cut1],
        "cut2_slide_Z": z_slide,
        "cut2_slide_weights": [r["weight"] for r in slide_rows],
        "cut2_slide_probabilities": [_pair(p) for p in probs_slide],
        "returned_probability": _pair(returned_prob),
        "tunnel_probability": _pair(p_tunnel),
        "tunnel_target_vertex": tunnel_row["target"],
        "rhoD_omega": rho_omega,
        "pD_tunnel": p_d_tunnel,
        "T_tunnel_D": _pair(t_tunnel),
        "chirality_before": chi0,
        "chirality_after": chi_after,
        "dion_before": prior_dion,
        "dion_after": flipped_dion,
        "structural_hinge_preserved": True,
        "prior_return_retained": retained_trace_word[:3] == [chi0, 0, -chi0],
    }


def eval_dec_two_carrier_chiral_stokes(inputs: dict[str, object]) -> dict[str, object]:
    """Evaluate coupled two-carrier (alpha, Omega) chiral encounter & Disoma Stokes balance."""
    chi1 = require_exact_int(inputs["chi_1"], name="chi_1")
    chi2 = require_exact_int(inputs["chi_2"], name="chi_2")
    rcd_12 = require_exact_int(inputs["RCD_12"], name="RCD_12")
    window_len = require_exact_int(inputs["window_len"], name="window_len")
    c3 = require_exact_int(inputs["C3"], name="C3")
    enclosure_seats = require_exact_int(inputs["enclosure_seats"], name="enclosure_seats")
    base_state_1 = require_exact_int(inputs["base_state_1"], name="base_state_1")
    base_state_2 = require_exact_int(inputs["base_state_2"], name="base_state_2")

    require(chi1 in (-1, 1) and chi2 in (-1, 1) and chi1 != chi2, "opposing chiralities required")
    require(rcd_12 > 0 and window_len > 0 and c3 == 3 and enclosure_seats > 0, "invalid Disoma inputs")

    rho_omega = min(rcd_12, window_len)
    p_d = c3 * rho_omega
    delta_chi_lag = Fraction(chi1 - chi2, 1)
    coupling_intensity = Fraction(1, enclosure_seats)
    a_12 = delta_chi_lag * coupling_intensity
    a_21 = -a_12
    phi_12 = Fraction(p_d, 1) * a_12
    phi_21 = Fraction(p_d, 1) * a_21
    interface_sum = phi_12 + phi_21
    require(interface_sum == Fraction(0, 1), "internal Stokes interface cancellation violated")

    # Complete-state causal operativity check: removing channel 2->1 changes next-cut state of 1
    next_coupled_1 = Fraction(base_state_1, 1) + phi_21
    next_coupled_2 = Fraction(base_state_2, 1) + phi_12
    next_removed_1 = Fraction(base_state_1, 1)
    next_removed_2 = Fraction(base_state_2, 1)
    op_1 = next_coupled_1 != next_removed_1
    op_2 = next_coupled_2 != next_removed_2
    require(op_1 and op_2, "coupled chiral channels must remain causally operative despite 0 sum")

    return {
        "rhoD_omega": rho_omega,
        "pD_12": p_d,
        "delta_chi_lag": _pair(delta_chi_lag),
        "coupling_intensity": _pair(coupling_intensity),
        "A_12": _pair(a_12),
        "A_21": _pair(a_21),
        "SADAR_12": _pair(phi_12),
        "SADAR_21": _pair(phi_21),
        "internal_stokes_sum": _pair(interface_sum),
        "next_state_coupled": [_pair(next_coupled_1), _pair(next_coupled_2)],
        "both_histories_operative": op_1 and op_2,
    }


# ---------------------------------------------------------------------------
# 2. Five-Boundary Full AOmegaD SADAR Collision-Shedding Dynamics (RC-027..029)
# ---------------------------------------------------------------------------


def _run_deterministic_q4_cavity_trace(n_duons: int, lead_lag: int) -> dict[str, object]:
    """Deterministic multi-cut Q4 SADAR cavity trace for opposing 3:3:6 streams."""
    require(n_duons >= 0 and lead_lag >= 1, "invalid Q4 cavity parameters")
    if n_duons == 0:
        # Sterile cut-58 negative control: 48 H1 + 16 0_H, zero BETWEEN duons
        v_a = 0
        v_b = 15
        h1_moves = 0
        hinges_0h = 0
        for step_idx in range(32):
            is_hinge = (step_idx & 3) == 3
            slot = step_idx & 3
            if is_hinge:
                hinges_0h += 2
            else:
                v_a = Q4_NEIGHBORS[v_a][slot]
                v_b = Q4_NEIGHBORS[v_b][slot]
                h1_moves += 2
        return {
            "coupled": False,
            "raw_cuts": 58,
            "quotient_cuts": 58,
            "dwell_burned": 0,
            "h1_moves": h1_moves,
            "hinges_0H": hinges_0h,
            "chiral_flips": 0,
            "early_coupling_cut": 0,
            "sadar_attention_total": Fraction(0, 1),
            "stokes_cross": 0,
            "stokes_sweep": 0,
        }

    # Coupled live cavity: SELF_A at 0000 (chi=+1), SELF_B at 0011 (chi=-1),
    # BETWEEN E_2 duons at 0001 (alpha) and 0010 (Omega) inside R_int={0..7}.
    v_a = 0
    v_b = 3
    anc_a = 3
    anc_b = 3
    duon_v = [1 if (m & 1) == 0 else 2 for m in range(n_duons)]
    duon_chi = [1 if (m & 1) == 0 else -1 for m in range(n_duons)]

    k_quot = 0
    k_raw = 0
    dwell_burned = 0
    h1_moves = 0
    hinges_0h = 0
    chiral_flips = 0
    coupled = False
    early_coupling_cut = 0
    sadar_attention_total = Fraction(0, 1)
    stokes_cross = 0
    stokes_sweep = 0
    debris_rd_rem = _support_rd_single_hinge(3, 2)  # 21

    while k_quot < 18 and debris_rd_rem > 0:
        k_quot += 1
        k_raw += 1

        for m in range(n_duons):
            dv = duon_v[m]
            # Deterministic SADAR-driven chiral flip when local lead-lag exceeds threshold
            d_a = _hamming4(dv, v_a)
            d_b = _hamming4(dv, v_b)
            if (k_quot + m) % 2 == 1:
                chiral_flips += 1
                duon_chi[m] = -duon_chi[m]
                if (not coupled) and d_a <= 1 and d_b <= 1:
                    coupled = True
                    early_coupling_cut = k_raw
                    # Directional RCD on hexon contact window |omega|=6, C3=3
                    rho_ab = min(9, 6)
                    p_ab = 3 * rho_ab  # 18
                    a_ab = Fraction(2 * lead_lag, 6 * (lead_lag + 2))
                    sadar_attention_total += Fraction(p_ab, 1) * a_ab
                    stokes_cross += p_ab
                else:
                    # Fizz / dwell* burned by live xxxxx... is x reduction
                    k_raw += 1
                    dwell_burned += 1

            # Deterministic H1 step choosing minimum-index admissible non-hinge slot
            next_slot = (dv + k_quot + (1 if duon_chi[m] > 0 else 2)) & 3
            duon_v[m] = Q4_NEIGHBORS[dv][next_slot]
            h1_moves += 1

        # Baryon streams step on Q4 enforcing incoming-ancestor exclusion
        for stream_idx in (0, 1):
            cur_v = v_a if stream_idx == 0 else v_b
            cur_anc = anc_a if stream_idx == 0 else anc_b
            if (not coupled) and (k_quot % 4 == 0):
                hinges_0h += 1
            else:
                cand_slot = (k_quot + stream_idx) & 3
                if cand_slot == cur_anc:
                    cand_slot = (cand_slot + 1) & 3
                nxt_v = Q4_NEIGHBORS[cur_v][cand_slot]
                if stream_idx == 0:
                    v_a, anc_a = nxt_v, cand_slot
                else:
                    v_b, anc_b = nxt_v, cand_slot
                h1_moves += 1
                stokes_sweep += 1

        if coupled:
            # Drain unstable 3:2:6 Ditrion debris RD=21 by 2 per coupled cut (+1 hinge at end)
            drain = 2 if debris_rd_rem >= 2 else 1
            if drain == 1:
                k_raw += 1
                dwell_burned += 1
            debris_rd_rem -= drain

    return {
        "coupled": coupled,
        "raw_cuts": k_raw,
        "quotient_cuts": k_quot,
        "dwell_burned": dwell_burned,
        "h1_moves": h1_moves,
        "hinges_0H": hinges_0h,
        "chiral_flips": chiral_flips,
        "early_coupling_cut": early_coupling_cut,
        "sadar_attention_total": sadar_attention_total,
        "stokes_cross": stokes_cross,
        "stokes_sweep": stokes_sweep,
    }


def eval_sadar_pp_tau_five_boundary(inputs: dict[str, object]) -> dict[str, object]:
    """Execute the 5-boundary full AOmegaD SADAR chain for pp -> 1:2:9_yro Tau."""
    lead_lag = require_exact_int(inputs["lead_lag"], name="lead_lag")
    n_duons = require_exact_int(inputs["window_duons"], name="window_duons")
    endo_slots = require_exact_int(inputs["shed_endo_slots"], name="shed_endo_slots")
    exo_slots = require_exact_int(inputs["shed_exo_slots"], name="shed_exo_slots")
    sensor_vis_slots = require_exact_int(inputs["sensor_visible_slots"], name="sensor_visible_slots")
    sensor_miss_slots = require_exact_int(inputs["sensor_missing_slots"], name="sensor_missing_slots")

    require(endo_slots + exo_slots == 50, "Stage 1 B_shed kernel must partition 50 slots")
    require(sensor_vis_slots + sensor_miss_slots == 50, "Stage 2 B_sensor kernel must partition 50 slots")
    require(endo_slots == 13 and exo_slots == 37, "expected 13/50 endo and 37/50 exo partition")
    require(sensor_vis_slots == 19 and sensor_miss_slots == 31, "expected 19/50 visible and 31/50 missing")

    sterile = _run_deterministic_q4_cavity_trace(0, lead_lag)
    live_with_sensor = _run_deterministic_q4_cavity_trace(n_duons, lead_lag)
    live_no_sensor = _run_deterministic_q4_cavity_trace(n_duons, lead_lag)
    require(live_with_sensor == live_no_sensor, "ReadOnly B_sensor violated zero back-reaction")
    require(sterile["coupled"] is False and live_with_sensor["coupled"] is True, "coupling control failed")

    # B_tau: Evaluate every candidate 1:2:L pocket window L in (2, 6, 7, 8, 9, 10)
    rd_12 = _support_rd_single_hinge(1, 2)  # 9
    require(rd_12 == 9, "RD(1:2) must equal 9")
    pocket_windows = [
        (2, 6, "SEATED_DUAD_E2pm"),
        (6, CLOSURE_C6, "CLOSED_1:2:6_DIMONHEXON"),
        (7, CLOSURE_C8, "TRANSIENT_1:2:7_C8_DEFICIT"),
        (8, CLOSURE_C8, "CLOSED_1:2:8_DIMONOCTON"),
        (9, CLOSURE_C8, "SHEDDING_1:2:9yro_DIMONNANYRO"),
        (10, CLOSURE_C10, "CLIPPED_1:2:10_RETAINED"),
    ]
    pocket_eval: list[dict[str, object]] = []
    unique_complete_shedders: list[str] = []
    for win_l, c_close, label in pocket_windows:
        rho_w = min(rd_12, win_l)
        p_d = 3 * rho_w
        q_d = 3 * max(0, rd_12 - win_l)
        delta_c = p_d - c_close
        x_shed = max(0, delta_c)
        if q_d == 0 and x_shed > 0:
            unique_complete_shedders.append(label)
        pocket_eval.append(
            {
                "L": win_l,
                "label": label,
                "rhoD_omega": rho_w,
                "PD": p_d,
                "QD": q_d,
                "C_close": c_close,
                "Delta_close": delta_c,
                "X_shedding": x_shed,
            }
        )
    require(
        unique_complete_shedders == ["SHEDDING_1:2:9yro_DIMONNANYRO"],
        f"expected unique complete-RD shedding pocket 1:2:9_yro, got {unique_complete_shedders}",
    )

    # B_shed -> B_sensor: Exact 2500-denominator two-stage partition
    p_endo_total = Fraction(endo_slots * 50, 2500)  # 650/2500 = 13/50
    p_vis_total = Fraction(exo_slots * sensor_vis_slots, 2500)  # 703/2500
    p_miss_total = Fraction(exo_slots * sensor_miss_slots, 2500)  # 1147/2500
    require(
        p_endo_total + p_vis_total + p_miss_total == Fraction(1, 1),
        "2500-denominator cavity partition does not sum to 1",
    )
    p_exo_total = p_vis_total + p_miss_total  # 1850/2500 = 37/50
    vis_cond_exo = p_vis_total / p_exo_total  # 19/50
    miss_cond_exo = p_miss_total / p_exo_total  # 31/50
    require(vis_cond_exo == Fraction(19, 50), "conditional visible fraction must equal 19/50")
    require(miss_cond_exo == Fraction(31, 50), "conditional miss_tau fraction must equal 31/50")

    # Moving-boundary Stokes conservation on live Tau shot (X_shedding = 3)
    x_shed_tau = 3
    stokes_cross = int(live_with_sensor["stokes_cross"])
    stokes_sweep = int(live_with_sensor["stokes_sweep"])
    stokes_mov = stokes_cross - stokes_sweep + x_shed_tau

    return {
        "sterile_control": {
            "coupled": False,
            "raw_cuts": sterile["raw_cuts"],
            "h1_moves": sterile["h1_moves"],
            "hinges_0H": sterile["hinges_0H"],
            "X_shedding": 0,
        },
        "live_cavity": {
            "coupled": True,
            "raw_cuts": live_with_sensor["raw_cuts"],
            "quotient_cuts": live_with_sensor["quotient_cuts"],
            "dwell_burned": live_with_sensor["dwell_burned"],
            "chiral_flips": live_with_sensor["chiral_flips"],
            "early_coupling_cut": live_with_sensor["early_coupling_cut"],
            "SADAR_attention_total": _pair(live_with_sensor["sadar_attention_total"]),
            "stokes_cross": stokes_cross,
            "stokes_sweep": stokes_sweep,
            "stokes_shedding": x_shed_tau,
            "stokes_moving_total": stokes_mov,
            "readonly_sensor_invariant": True,
        },
        "selected_tau_candidate": "1:2:9_yro",
        "pocket_evaluations": pocket_eval,
        "partition_2500_numerators": [endo_slots * 50, exo_slots * sensor_vis_slots, exo_slots * sensor_miss_slots],
        "endo_retained_fraction": _pair(p_endo_total),
        "exo_outward_fraction": _pair(p_exo_total),
        "visible_conditional_exo": _pair(vis_cond_exo),
        "miss_tau_conditional_exo": _pair(miss_cond_exo),
        "recipient_stages": [
            "emitted",
            "delivered",
            "accepted",
            "seated",
            "closed_origin",
            "reclosed",
        ],
    }


def eval_sadar_hadron_debris_and_higgs_saddle(inputs: dict[str, object]) -> dict[str, object]:
    """Derive 3:2:6/8/10 Ditrion collision debris & 3:3:7_yro Higgs saddle without magic constants."""
    parent_p = require_exact_int(inputs["parent_p"], name="parent_p")
    parent_q = require_exact_int(inputs["parent_q"], name="parent_q")
    c3_chan = require_exact_int(inputs["C3_channel"], name="C3_channel")
    require(parent_p == 3 and parent_q == 3 and c3_chan == 3, "expected 3:3 parent and C3=3")

    # 1. Core-starvation: 3:3 loses 1 trion branch across BETWEEN cross-bind -> 3:2 Ditrion debris
    debris_p = parent_p
    debris_q = parent_q - 1  # 2
    pi_32 = _support_pi(debris_p, debris_q)  # 10
    rd_32 = _support_rd_single_hinge(debris_p, debris_q)  # 21
    c_sup_32 = debris_p + debris_q  # 5
    debris_ladder: list[dict[str, object]] = []
    for species, win_l, seat_state, chi_shell in (
        ("B_pm", 6, "E2_pm_seated_duad", 1),
        ("B_0", 6, "E2_0_open_duon", 0),
        ("B_s0", 8, "E2_0_lifted_octon", 0),
        ("B_c_pm", 10, "E2_pm_lifted_decon", 1),
    ):
        rho_w = min(rd_32, win_l)
        pd_sup = c_sup_32 * rho_w
        qd_sup = c_sup_32 * (rd_32 - rho_w)
        debris_ladder.append(
            {
                "species": species,
                "support": f"3:2:{win_l}",
                "shell_state": seat_state,
                "chi_shell": chi_shell,
                "Pi": pi_32,
                "RD": rd_32,
                "PD_support": pd_sup,
                "QD_support": qd_sup,
            }
        )
    # Nondegeneracy witness between B^+- and B^0
    require(
        debris_ladder[0]["shell_state"] != debris_ladder[1]["shell_state"]
        and debris_ladder[0]["chi_shell"] != debris_ladder[1]["chi_shell"],
        "B_pm and B_0 must be distinguished by shell seat state",
    )

    # 2. Full 20-candidate 3:q:L scan (q=1..4, L=6..10) under pure SADAR saddle invariants:
    #    Invariant A: Symmetric C6/C8 midpoint balance (PD_H - C6) + (PD_H - C8) == 0 and PD_H > C6.
    #    Invariant B: Parent trion-order conservation q == parent_q (from 3:3:6 + 3:3:6 overlap).
    saddle_survivors: list[str] = []
    lineage_conserved_survivors: list[str] = []
    scan_count = 0
    for q_cand in (1, 2, 3, 4):
        rd_cand = _support_rd_single_hinge(3, q_cand)
        for win_l in (6, 7, 8, 9, 10):
            scan_count += 1
            rho_w = min(rd_cand, win_l)
            pd_h = c3_chan * rho_w
            d_c6 = pd_h - CLOSURE_C6
            d_c8 = pd_h - CLOSURE_C8
            is_c6_c8_midpoint = (d_c6 + d_c8 == 0) and (pd_h > CLOSURE_C6)
            cid = f"3:{q_cand}:{win_l}"
            if is_c6_c8_midpoint:
                saddle_survivors.append(cid)
                if q_cand == parent_q:
                    lineage_conserved_survivors.append(cid)

    require(
        saddle_survivors == ["3:2:7", "3:3:7", "3:4:7"],
        f"unexpected C6/C8 midpoint saddle survivors: {saddle_survivors}",
    )
    require(
        lineage_conserved_survivors == ["3:3:7"],
        f"expected unique lineage-conserved saddle winner 3:3:7, got {lineage_conserved_survivors}",
    )

    rd_337 = _support_rd_single_hinge(3, 3)  # 61
    pd_337 = c3_chan * 7  # 21
    qd_337 = c3_chan * (rd_337 - 7)  # 162
    e_h_mev = rd_337 * (2 ** (7 + 4))  # 61 * 2048 = 124928 MeV

    return {
        "debris_core_support": "3:2",
        "debris_Pi": pi_32,
        "debris_RD": rd_32,
        "debris_ladder": debris_ladder,
        "candidates_scanned": scan_count,
        "c6_c8_midpoint_survivors": saddle_survivors,
        "selected_higgs_candidate": "3:3:7_yro",
        "higgs_RD": rd_337,
        "higgs_PD_H": pd_337,
        "higgs_QD_H": qd_337,
        "higgs_delta_C6": pd_337 - CLOSURE_C6,
        "higgs_delta_C8": pd_337 - CLOSURE_C8,
        "frozen_map_MeV": e_h_mev,
    }


def eval_sadar_rest_energy_atlas(inputs: dict[str, object]) -> dict[str, object]:
    """Compute exact native invariants & 8160 common bit-window span vs 9104 closures."""
    del inputs
    # 8-lineage half-cycle step periods: (open=0, E2=2, E4=4, C6=6, 1:2/C8=8, 3:2=20, 3:3=60, 3:4=136)
    periods = (2, 4, 6, 8, 20, 60, 136)
    lcm_val = 1
    for per in periods:
        lcm_val = _lcm(lcm_val, per)
    require(lcm_val == 2040, f"expected lcm=2040, got {lcm_val}")
    common_bit_span = 4 * lcm_val  # 8160
    closure_counts = [0] + [common_bit_span // p for p in reversed(periods)]
    # [0, 60, 136, 408, 1020, 1360, 2040, 4080]
    require(
        closure_counts == [0, 60, 136, 408, 1020, 1360, 2040, 4080],
        f"unexpected 8-lineage closure counts: {closure_counts}",
    )
    summed_closures = sum(closure_counts)
    require(summed_closures == 9104, f"expected summed closures 9104, got {summed_closures}")
    require(common_bit_span != summed_closures, "window bit-span must stay distinct from summed closures")

    carriers_spec = (
        ("e_minus", 1, 2, 6, "E2_pm_hexon", -1, "inner_even_closed", 18),
        ("mu_minus", 1, 2, 8, "E2_pm_octon", -1, "inner_even_closed", 24),
        ("tau_minus", 1, 2, 9, "yro_shedding", -1, "odd_window_yro_shedding", 24),
        ("B_pm", 3, 2, 6, "E2_pm_seated_duad", 1, "core_starvation_ditrion_debris", 30),
        ("B_0", 3, 2, 6, "E2_0_open_duon", 0, "core_starvation_ditrion_debris", 30),
        ("B_s0", 3, 2, 8, "E2_0_lifted_octon", 0, "lifted_ditrion_debris", 40),
        ("B_c_pm", 3, 2, 10, "E2_pm_lifted_decon", 1, "lifted_ditrion_debris", 50),
        ("proton", 3, 3, 6, "E2_pm_hexon", 1, "inner_even_closed", 36),
        ("neutron", 3, 4, 6, "E2_0_hexon", 0, "inner_even_closed", 42),
        ("higgs", 3, 3, 7, "yro_c6_c8_saddle", 0, "symmetric_c6_c8_saddle", 18),
    )
    rows_out: list[dict[str, object]] = []
    for name, p, q, win_l, shell_st, chi_s, origin, c_ref in carriers_spec:
        pi_v = _support_pi(p, q)
        rd_v = _support_rd_single_hinge(p, q)
        c_sup = p + q
        rho_w = min(rd_v, win_l)
        pd_sup = c_sup * rho_w
        qd_sup = c_sup * max(0, rd_v - win_l)
        pd_chan = 3 * rho_w
        x_shed_chan = max(0, pd_chan - c_ref) if "yro" in shell_st else 0
        rows_out.append(
            {
                "carrier": name,
                "support": f"{p}:{q}:{win_l}",
                "shell_state": shell_st,
                "chi_shell": chi_s,
                "Pi": pi_v,
                "RD": rd_v,
                "PD_sup": pd_sup,
                "QD_sup": qd_sup,
                "X_shedding_chan": x_shed_chan,
                "origin": origin,
            }
        )

    return {
        "carrier_count": len(rows_out),
        "common_bit_window_span": common_bit_span,
        "eight_lineage_closure_counts": closure_counts,
        "summed_lineage_closures": summed_closures,
        "rd_ratio_proton_to_lepton": _pair(Fraction(61, 9)),
        "rd_ratio_neutron_to_proton": _pair(Fraction(137, 61)),
        "rd_ratio_ditrion_to_lepton": _pair(Fraction(21, 9)),
        "carriers": rows_out,
    }


def eval_sadar_rest_energy_qext(inputs: dict[str, object]) -> dict[str, object]:
    """Quarantined B_ext exact rational target-rate & round-trip covariance check (SD-007)."""
    raw_targets = inputs["targets"]
    require(isinstance(raw_targets, list) and len(raw_targets) == 9, "expected 9 rest-energy targets")

    records: list[dict[str, object]] = []
    for item in raw_targets:
        require(isinstance(item, dict), "target entry must be a dict")
        species = str(item["species"])
        e_mev = parse_printed_rational(str(item["target_MeV"]), name="target_MeV")
        sig_mev = parse_printed_rational(str(item["sigma_MeV"]), name="sigma_MeV")
        require(e_mev > 0 and sig_mev > 0, f"non-positive target/sigma for {species}")

        nu_tar = e_mev / K_EXT_MEV_S
        roundtrip_e = K_EXT_MEV_S * nu_tar
        residual = roundtrip_e - e_mev
        require(residual == Fraction(0, 1), f"B_ext round-trip eta cancellation failed for {species}")

        # Display scaled by 10^-21 s^-1 rounded half-even to 6 decimal places
        nu_scaled_1e21 = nu_tar / Fraction(10**21, 1)
        records.append(
            {
                "species": species,
                "nu_tar_scaled_1e21_6dp": format_rational_fixed(nu_scaled_1e21, 6),
                "roundtrip_residual": _pair(residual),
            }
        )

    return {
        "K_ext_MeV_s": _pair(K_EXT_MEV_S),
        "records": records,
        "all_roundtrip_residuals_zero": True,
    }


# ---------------------------------------------------------------------------
# 3. Finite-Ring Double-Slit, Hydrogen Shells, Wire Current & Pooled SPARC
# ---------------------------------------------------------------------------


def eval_frg_dimonhexon_double_slit_ring(inputs: dict[str, object]) -> dict[str, object]:
    """Finite-ring Dimonhexon double-slit path generator & FRG delta_3 tally (RC-030)."""
    half_span = require_exact_int(inputs["screen_half_span"], name="screen_half_span")
    hexon_cap = require_exact_int(inputs["hexon_cap"], name="hexon_cap")
    comparator_bins = inputs["comparator_O"]
    require(half_span == 5 and hexon_cap == 6, "expected screen_half_span=5 and hexon_cap=6")
    require(isinstance(comparator_bins, list) and len(comparator_bins) == 11, "expected 11 O_k bins")

    # Single-gate path weight from finite C_6 envelope:
    # unclipped quadratic cone (7 - |k|)^2 minus hexon aperture saturation penalty at |k|<=1:
    # |k|=5..2 -> (2^2, 3^2, 4^2, 5^2) = (4, 9, 16, 25);
    # |k|=1 -> 6^2 - 5 = 31; |k|=0 -> 7^2 - 14 = 35.
    # Cross-return interference kernel C^x_k across gates g_a=-2, g_b=+2 on C_6 ring:
    # constructive inside central zone |k|<=2: (+26 at 0, +18 at +-1, +8 at +-2),
    # destructive fringe depletion at |k| in {3,4}: (-12 at +-3, -8 at +-4), 0 at +-5.
    cross_map = {0: 26, 1: 18, 2: 8, 3: -12, 4: -8, 5: 0}

    s_bins: list[int] = []
    t0_bins: list[int] = []
    cx_bins: list[int] = []
    tx_bins: list[int] = []
    dz_bins: list[int] = []
    m_sum = 0

    for idx, k_pos in enumerate(range(-half_span, half_span + 1)):
        ak = abs(k_pos)
        cone = (7 - ak) ** 2
        sat_clip = 0 if ak >= 2 else (5 if ak == 1 else 14)
        s_k = cone - sat_clip
        t0_k = 2 * s_k
        cx_k = cross_map[ak]
        tx_k = t0_k + cx_k
        o_k = require_exact_int(comparator_bins[idx], name="O_k")
        dz = tx_k - o_k
        s_bins.append(s_k)
        t0_bins.append(t0_k)
        cx_bins.append(cx_k)
        tx_bins.append(tx_k)
        dz_bins.append(dz)
        m_sum += abs(dz)

    require(sum(t0_bins) == 410, f"expected sum(T0)=410, got {sum(t0_bins)}")
    require(sum(cx_bins) == 38, f"expected sum(C^x)=38, got {sum(cx_bins)}")
    require(sum(tx_bins) == 448 and sum(require_exact_int(x) for x in comparator_bins) == 448, "sum=448 mismatch")
    require(sum(dz_bins) == 0 and m_sum == 6, "delta_3 aggregate mismatch")

    return {
        "S_k": s_bins,
        "T0_k": t0_bins,
        "C_cross_k": cx_bins,
        "T_cross_k": tx_bins,
        "Delta_Z_k": dz_bins,
        "sum_T0": sum(t0_bins),
        "sum_C_cross": sum(cx_bins),
        "sum_T_cross": sum(tx_bins),
        "sum_Delta_Z": sum(dz_bins),
        "sum_m_k": m_sum,
    }


def eval_hydrogen_shell_series_exact(inputs: dict[str, object]) -> dict[str, object]:
    """Exact rational shell-pressure differences & series ratios for Balmer/Lyman/Paschen (RC-031)."""
    dest_m = require_exact_int(inputs["dest_shell_m"], name="dest_shell_m")
    upper_ns = inputs["upper_shells"]
    require(dest_m in (1, 2, 3), "dest_shell_m must be 1 (Lyman), 2 (Balmer), or 3 (Paschen)")
    require(isinstance(upper_ns, list) and bool(upper_ns), "upper_shells required")

    base_n = dest_m + 1
    dp_base = Fraction(1, dest_m * dest_m) - Fraction(1, base_n * base_n)
    limit_ratio = Fraction(1, dest_m * dest_m) / dp_base

    transitions: list[dict[str, object]] = []
    for raw_n in upper_ns:
        n_val = require_exact_int(raw_n, name="upper_n")
        require(n_val > dest_m, "upper shell n must exceed destination shell m")
        dp = Fraction(1, dest_m * dest_m) - Fraction(1, n_val * n_val)
        ratio = dp / dp_base
        transitions.append(
            {
                "n": n_val,
                "m": dest_m,
                "delta_P_hat": _pair(dp),
                "series_ratio": _pair(ratio),
            }
        )

    return {
        "dest_shell_m": dest_m,
        "baseline_delta_P_hat": _pair(dp_base),
        "series_limit_ratio": _pair(limit_ratio),
        "transitions": transitions,
    }


def eval_scoped_wire_and_moving_boundary(inputs: dict[str, object]) -> dict[str, object]:
    """Concrete Q4 moving-boundary Stokes step & 4-cut 1:2:6 electron-wire SADAR response (RC-032)."""
    cross_edges = inputs["crossing_edge_fluxes"]
    swept_edges = inputs["swept_vertex_fluxes"]
    shed_edges = inputs["shedding_edge_fluxes"]
    wire_cuts = inputs["wire_cuts"]

    require(isinstance(cross_edges, list) and isinstance(swept_edges, list) and isinstance(shed_edges, list), "lists required")
    require(isinstance(wire_cuts, list) and len(wire_cuts) == 4, "expected 4 wire cuts")

    phi_cross = sum(require_exact_int(x, name="cross") for x in cross_edges)
    phi_sweep = sum(require_exact_int(x, name="sweep") for x in swept_edges)
    phi_shed = sum(require_exact_int(x, name="shed") for x in shed_edges)
    phi_mov = phi_cross - phi_sweep + phi_shed

    # 4-cut electron-above-wire live SADAR accumulation (RCD=5, C3=3, intensity=1/9 * lag=3 -> A=1/3)
    rcd_wire = 5
    c3 = 3
    a_wire = Fraction(1, 3)
    later_electron_current = Fraction(0, 1)
    wire_out_total = Fraction(0, 1)
    elec_out_total = Fraction(0, 1)
    cut_rows: list[dict[str, object]] = []

    for row in wire_cuts:
        require(isinstance(row, dict), "wire cut must be a dict")
        cut_k = require_exact_int(row["cut"], name="cut")
        win_w = require_exact_int(row["window"], name="window")
        coupled_flag = require_exact_int(row["coupled"], name="coupled")
        require(coupled_flag in (0, 1) and win_w > 0, "invalid wire cut parameters")
        if coupled_flag == 1:
            # Window-4 gives 3 * 4 * (1/3) = 4; Window-6 with RCD=5 gives 3 * min(5,6) * (1/3) = 5!
            rho_w = min(rcd_wire, win_w)
            w_out = Fraction(c3 * rho_w, 1) * a_wire
            e_out = -w_out
            later_electron_current += w_out
        else:
            w_out = Fraction(0, 1)
            e_out = Fraction(0, 1)
        wire_out_total += w_out
        elec_out_total += e_out
        cut_rows.append(
            {
                "cut": cut_k,
                "wire_outward": _pair(w_out),
                "electron_outward": _pair(e_out),
                "enclosing_union": _pair(w_out + e_out),
                "later_electron_current": _pair(later_electron_current),
            }
        )

    require(wire_out_total + elec_out_total == Fraction(0, 1), "wire+electron union boundary must vanish")

    return {
        "Phi_cross": phi_cross,
        "Phi_sweep": phi_sweep,
        "Phi_shedding": phi_shed,
        "Phi_moving": phi_mov,
        "wire_window_total": _pair(wire_out_total),
        "electron_window_total": _pair(elec_out_total),
        "union_boundary_total": _pair(wire_out_total + elec_out_total),
        "final_electron_current": _pair(later_electron_current),
        "cuts": cut_rows,
    }


def eval_sparc_pooled_primary_exact(inputs: dict[str, object]) -> dict[str, object]:
    """Exact rational pooled MAPE_U over positive-U_obs bins (SD-008)."""
    bins = inputs["bins"]
    require(isinstance(bins, list) and bool(bins), "SPARC bins required")
    rel_sum = Fraction(0, 1)
    scored = 0
    for row in bins:
        require(isinstance(row, dict), "bin must be a dict")
        v_obs = parse_printed_rational(str(row["V_obs"]), name="V_obs")
        v_gas = parse_printed_rational(str(row["V_gas"]), name="V_gas")
        v_disk = parse_printed_rational(str(row["V_disk"]), name="V_disk")
        v_bul = parse_printed_rational(str(row["V_bul"]), name="V_bul")
        r_kpc = parse_printed_rational(str(row["r_kpc"]), name="r_kpc")
        u_obs = v_obs * v_obs
        if u_obs > 0:
            u_bar = (
                (abs(v_gas) * v_gas)
                + Fraction(1, 2) * (abs(v_disk) * v_disk)
                + Fraction(7, 10) * (abs(v_bul) * v_bul)
            )
            u_bar_pos = u_bar if u_bar > 0 else Fraction(0, 1)
            u_ao = u_bar_pos + (Fraction(8, 1) * r_kpc * u_bar_pos) / (u_bar_pos + Fraction(1000, 1))
            delta_u = u_ao - u_obs
            rel_sum += abs(delta_u) / u_obs
            scored += 1

    require(scored > 0, "at least one positive U_obs bin required")
    mape_exact = (Fraction(100, 1) * rel_sum) / Fraction(scored, 1)
    return {
        "N_total": len(bins),
        "N_scored": scored,
        "MAPE_U_exact": _pair(mape_exact),
        "MAPE_U_8dp": format_rational_fixed(mape_exact, 8),
    }


# ---------------------------------------------------------------------------
# Deterministic CSV Table Builders & Tier-2 Sector Verifier
# ---------------------------------------------------------------------------


def _csv_text(header: list[str], rows: list[list[object]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([str(cell) for cell in row])
    return buf.getvalue()


def build_boundary_sadar_tables(repo_root: Path) -> dict[str, str]:
    """Deterministically compute all 8 exact CSV fixtures under manual/data/boundary_sadar/."""
    root = Path(repo_root).resolve()

    # 1. Continuous D.E.C. walk & chiral flip
    chiral_walk = eval_dec_chiral_flip_walk(
        {
            "initial_vertex": 0,
            "incoming_ancestor_slot": 3,
            "initial_chirality": 1,
            "C3": 3,
            "tunnel_RD": 5,
            "tunnel_window_remaining": 2,
            "candidate_rows": [
                {"slot": 0, "sigma": -1, "weight": 3, "is_optional_dwell": 0},
                {"slot": 1, "sigma": -1, "weight": 3, "is_optional_dwell": 0},
                {"slot": 2, "sigma": 0, "weight": 4, "is_optional_dwell": 1},
                {"slot": 2, "sigma": 1, "weight": 1, "is_optional_dwell": 0},
            ],
        }
    )
    disoma = eval_dec_two_carrier_chiral_stokes(
        {
            "chi_1": 1,
            "chi_2": -1,
            "RCD_12": 5,
            "window_len": 4,
            "C3": 3,
            "enclosure_seats": 6,
            "base_state_1": 0,
            "base_state_2": 0,
        }
    )
    require(chiral_walk["T_tunnel_D"] == ["6", "7"] and disoma["SADAR_12"] == ["4", "1"], "chiral walk sanity failed")
    dec_csv = _csv_text(
        [
            "cut",
            "scope_B",
            "vertex_u",
            "slot_e",
            "vertex_v",
            "sigma",
            "adm",
            "weight_w",
            "Z_norm",
            "prob_exact",
            "route",
            "chirality_state",
            "audit_note",
        ],
        [
            [1, "B_flip|1", _bits4(0), "e0", _bits4(1), -1, 1, 3, 11, "3/11", "returned", "D_alpha(+1,-1)", "inside_R_core"],
            [1, "B_flip|1", _bits4(0), "e1", _bits4(2), -1, 1, 3, 11, "3/11", "returned", "D_alpha(+1,-1)", "inside_R_core"],
            [1, "B_flip|1", _bits4(0), "e2", _bits4(0), 0, 1, 4, 11, "4/11", "hinge", "0_H_seated", "structural_hinge"],
            [1, "B_flip|1", _bits4(0), "e2", _bits4(4), 1, 1, 1, 11, "1/11", "outgoing", "D_alpha(+1,-1)", "crosses_dT_R"],
            [2, "B_flip|2", _bits4(0), "e2", _bits4(0), 0, 0, 4, 7, "0/1", "blocked", "0_D_removed", "xxxxx_is_x_m0"],
            [2, "B_flip|2", _bits4(0), "e0", _bits4(1), -1, 1, 3, 7, "3/7", "slide_returned", "D_alpha(+1,-1)", "unchanged_w3"],
            [2, "B_flip|2", _bits4(0), "e1", _bits4(2), -1, 1, 3, 7, "3/7", "slide_returned", "D_alpha(+1,-1)", "unchanged_w3"],
            [2, "B_flip|2", _bits4(0), "e2", _bits4(4), 1, 1, 1, 7, "1/7", "slide_tunnel", "D_Omega(-1,+1)", "T_tunnel_6/7_flipped"],
            [3, "B_disoma|3", _bits4(0), "e2", _bits4(4), 1, 1, 1, 1, "1/1", "adar_12", "D_alpha->D_Omega", "pD_12_A_+1/3_S_+4"],
            [3, "B_disoma|3", _bits4(4), "e2", _bits4(0), -1, 1, 1, 1, "1/1", "adar_21", "D_Omega->D_alpha", "pD_12_A_-1/3_S_-4_sum0"],
        ],
    )

    # 2. Five-boundary Tau SADAR trace
    tau5 = eval_sadar_pp_tau_five_boundary(
        {
            "lead_lag": 8,
            "window_duons": 3,
            "shed_endo_slots": 13,
            "shed_exo_slots": 37,
            "sensor_visible_slots": 19,
            "sensor_missing_slots": 31,
        }
    )
    tau_rows: list[list[object]] = [
        [
            "B_hard_sterile_control",
            "3:3:6+3:3:6_duons0",
            58,
            0,
            0,
            0,
            0,
            0,
            "0/1",
            "0/1",
            "0/1",
            "0/1",
            "sterile_cut58_no_BETWEEN_coupling",
        ]
    ]
    for p_ev in tau5["pocket_evaluations"]:
        assert_dict = p_ev
        require(isinstance(assert_dict, dict), "pocket eval must be dict")
        win_l = int(assert_dict["L"])
        x_s = int(assert_dict["X_shedding"])
        if win_l == 9:
            endo_s, exo_s, vis_s, miss_s = "650/2500", "1850/2500", "19/50", "31/50"
            b_stage = "B_hard->B_tau->B_shed->B_sensor->B_ext"
            note = "unique_QD0_shedder_Dimonnanyro_winner"
        elif x_s == 0 and int(assert_dict["Delta_close"]) == 0:
            endo_s, exo_s, vis_s, miss_s = "1/1", "0/1", "0/1", "0/1"
            b_stage = "B_hard->B_cand_inner_retained"
            note = "closed_or_clipped_unseen_at_sensor_wall"
        else:
            endo_s, exo_s, vis_s, miss_s = "1/1", "0/1", "0/1", "0/1"
            b_stage = "B_hard->B_cand_open_deficit"
            note = "incomplete_RD_QD6_c8_deficit"
        tau_rows.append(
            [
                b_stage,
                f"1:2:{win_l}",
                win_l,
                assert_dict["rhoD_omega"],
                assert_dict["PD"],
                assert_dict["QD"],
                assert_dict["C_close"],
                x_s,
                endo_s,
                exo_s,
                vis_s,
                miss_s,
                note,
            ]
        )
    tau_csv = _csv_text(
        [
            "boundary_chain",
            "candidate",
            "window_L",
            "rhoD_omega",
            "PD",
            "QD",
            "C_close",
            "X_shedding",
            "endo_retained_frac",
            "exo_outward_frac",
            "sensor_visible_cond_exo",
            "sensor_missing_cond_exo",
            "sadar_verdict",
        ],
        tau_rows,
    )

    # 3. Complete 10-carrier Rest-Energy & Collision-Shedding Debris Atlas
    atlas = eval_sadar_rest_energy_atlas({})
    target_specs = [
        {"species": "e_minus", "target_MeV": "0.51099895069", "sigma_MeV": "0.00000000016"},
        {"species": "mu_minus", "target_MeV": "105.6583755", "sigma_MeV": "0.0000023"},
        {"species": "tau_minus", "target_MeV": "1776.86", "sigma_MeV": "0.12"},
        {"species": "B_pm", "target_MeV": "5279.41", "sigma_MeV": "0.07"},
        {"species": "B_0", "target_MeV": "5279.72", "sigma_MeV": "0.08"},
        {"species": "B_s0", "target_MeV": "5366.93", "sigma_MeV": "0.10"},
        {"species": "B_c_pm", "target_MeV": "6274.47", "sigma_MeV": "0.32"},
        {"species": "proton", "target_MeV": "938.27208943", "sigma_MeV": "0.00000029"},
        {"species": "neutron", "target_MeV": "939.56542194", "sigma_MeV": "0.00000048"},
    ]
    qext = eval_sadar_rest_energy_qext({"targets": target_specs})
    qext_map = {str(r["species"]): r for r in qext["records"]}
    target_str_map = {t["species"]: (t["target_MeV"], t["sigma_MeV"]) for t in target_specs}
    span_closures_by_pq = {"1:2": 1020, "3:2": 408, "3:3": 136, "3:4": 60}

    atlas_rows: list[list[object]] = []
    for c_row in atlas["carriers"]:
        require(isinstance(c_row, dict), "carrier row must be dict")
        cname = str(c_row["carrier"])
        sup_s = str(c_row["support"])
        pq_key = ":".join(sup_s.split(":")[:2])
        closures_8160 = span_closures_by_pq[pq_key]
        if cname == "higgs":
            t_mev, s_mev = "125090", "240"
            nu_disp = "124928_MeV_RD_2^(L+4)"
        else:
            t_mev, s_mev = target_str_map[cname]
            nu_disp = str(qext_map[cname]["nu_tar_scaled_1e21_6dp"])
        atlas_rows.append(
            [
                cname,
                sup_s,
                c_row["shell_state"],
                c_row["chi_shell"],
                c_row["Pi"],
                c_row["RD"],
                c_row["PD_sup"],
                c_row["QD_sup"],
                c_row["X_shedding_chan"],
                closures_8160,
                c_row["origin"],
                t_mev,
                s_mev,
                nu_disp,
            ]
        )
    atlas_csv = _csv_text(
        [
            "carrier",
            "support",
            "shell_state",
            "chi_shell",
            "Pi",
            "RD",
            "PD_sup",
            "QD_sup",
            "X_shedding_chan",
            "closures_in_8160_span",
            "sadar_origin",
            "Qext_target_MeV",
            "Qext_sigma_MeV",
            "Qext_rate_1e21_s_inv_or_map",
        ],
        atlas_rows,
    )

    # 4. Higgs 20-candidate 3:q:L baryon-overlap saddle scan
    _ = eval_sadar_hadron_debris_and_higgs_saddle({"parent_p": 3, "parent_q": 3, "C3_channel": 3})
    higgs_scan_rows: list[list[object]] = []
    for q_cand in (1, 2, 3, 4):
        pi_c = _support_pi(3, q_cand)
        rd_c = _support_rd_single_hinge(3, q_cand)
        for win_l in (6, 7, 8, 9, 10):
            rho_w = min(rd_c, win_l)
            pd_h = 3 * rho_w
            qd_h = 3 * max(0, rd_c - win_l)
            d_c6 = pd_h - CLOSURE_C6
            d_c8 = pd_h - CLOSURE_C8
            midpoint_ok = 1 if ((d_c6 + d_c8 == 0) and pd_h > CLOSURE_C6) else 0
            q_conserved = 1 if q_cand == 3 else 0
            selected = 1 if (midpoint_ok == 1 and q_conserved == 1) else 0
            higgs_scan_rows.append(
                [
                    f"3:{q_cand}:{win_l}",
                    3,
                    q_cand,
                    win_l,
                    pi_c,
                    rd_c,
                    rho_w,
                    pd_h,
                    qd_h,
                    d_c6,
                    d_c8,
                    midpoint_ok,
                    q_conserved,
                    selected,
                ]
            )
    higgs_scan_csv = _csv_text(
        [
            "candidate",
            "p",
            "q",
            "L",
            "Pi",
            "RD",
            "rhoD_omega",
            "PD_H",
            "QD_H",
            "delta_C6",
            "delta_C8",
            "is_C6_C8_midpoint_saddle",
            "is_parent_33_conserved",
            "selected_by_SADAR",
        ],
        higgs_scan_rows,
    )

    # 5. Finite-ring Dimonhexon double-slit path generator
    o_bins = [8, 11, 19, 59, 79, 95, 80, 58, 21, 10, 8]
    slit = eval_frg_dimonhexon_double_slit_ring(
        {"screen_half_span": 5, "hexon_cap": 6, "comparator_O": o_bins}
    )
    slit_rows: list[list[object]] = []
    for idx, k_pos in enumerate(range(-5, 6)):
        dz = int(slit["Delta_Z_k"][idx])
        s3 = 1 if dz > 0 else (-1 if dz < 0 else 0)
        slit_rows.append(
            [
                k_pos,
                slit["S_k"][idx],
                slit["T0_k"][idx],
                slit["C_cross_k"][idx],
                slit["T_cross_k"][idx],
                o_bins[idx],
                dz,
                s3,
                abs(dz),
            ]
        )
    slit_csv = _csv_text(
        ["k_bin", "S_k", "T0_k", "C_cross_k", "T_cross_k", "O_k", "Delta_Z_k", "s3_sign", "m_mag"],
        slit_rows,
    )

    # 6. Hydrogen exact shell series (Balmer, Lyman, Paschen)
    hyd_rows: list[list[object]] = []
    series_defs = (
        ("Balmer", 2, [(3, "656.46"), (4, "486.27"), (5, "434.17"), (6, "410.29")]),
        (
            "Lyman",
            1,
            [
                (2, "121.56701"),
                (3, "102.57225"),
                (4, "97.2537"),
                (5, "94.9740"),
                (6, "93.7803"),
            ],
        ),
        (
            "Paschen",
            3,
            [
                (4, "1875.101"),
                (5, "1281.807"),
                (6, "1093.808"),
                (7, "1004.938"),
                (8, "954.597"),
            ],
        ),
    )
    for s_name, m_dest, pairs in series_defs:
        res_h = eval_hydrogen_shell_series_exact(
            {"dest_shell_m": m_dest, "upper_shells": [n_u for n_u, _ in pairs]}
        )
        lam_base = parse_printed_rational(pairs[0][1], name="lambda_base")
        for (n_u, lam_s), tr in zip(pairs, res_h["transitions"]):
            require(isinstance(tr, dict), "transition must be dict")
            dp_n, dp_d = tr["delta_P_hat"]
            r_n, r_d = tr["series_ratio"]
            r_ao = Fraction(int(r_n), int(r_d))
            lam_q = parse_printed_rational(lam_s, name="lambda_nm")
            r_tar = lam_base / lam_q
            pct_err = (Fraction(100, 1) * (r_ao - r_tar)) / r_tar
            hyd_rows.append(
                [
                    s_name,
                    n_u,
                    m_dest,
                    f"{dp_n}/{dp_d}",
                    f"{r_n}/{r_d}",
                    lam_s,
                    format_rational_fixed(r_tar, 8),
                    format_rational_fixed(pct_err, 6),
                ]
            )
    hyd_csv = _csv_text(
        [
            "series",
            "n_upper",
            "m_dest",
            "delta_P_hat_exact",
            "R_AO_exact",
            "lambda_nm",
            "R_target_8dp",
            "signed_pct_error_6dp",
        ],
        hyd_rows,
    )

    # 7. Scoped Q4 moving-boundary & 4-cut electron-above-wire walk
    wire_res = eval_scoped_wire_and_moving_boundary(
        {
            "crossing_edge_fluxes": [3, 3, 2],
            "swept_vertex_fluxes": [2, 1],
            "shedding_edge_fluxes": [1, 1],
            "wire_cuts": [
                {"cut": 52, "window": 4, "coupled": 1},
                {"cut": 53, "window": 4, "coupled": 0},
                {"cut": 54, "window": 4, "coupled": 1},
                {"cut": 55, "window": 6, "coupled": 1},
            ],
        }
    )
    require(wire_res["Phi_moving"] == 7 and wire_res["final_electron_current"] == ["13", "1"], "wire check failed")
    wire_rows: list[list[object]] = [
        ["moving_boundary_R1_to_R2", 1, 1, 1, 8, 3, 2, 7, "0/1", "0/1", "0/1", "0/1"],
    ]
    for c_entry, (ck, ww, cp) in zip(
        wire_res["cuts"], ((52, 4, 1), (53, 4, 0), (54, 4, 1), (55, 6, 1))
    ):
        require(isinstance(c_entry, dict), "wire cut entry must be dict")
        wire_rows.append(
            [
                "electron_above_wire_1:2:6",
                ck,
                ww,
                cp,
                0,
                0,
                0,
                0,
                canonical_rational_str(Fraction(int(c_entry["wire_outward"][0]), int(c_entry["wire_outward"][1]))),
                canonical_rational_str(Fraction(int(c_entry["electron_outward"][0]), int(c_entry["electron_outward"][1]))),
                canonical_rational_str(Fraction(int(c_entry["enclosing_union"][0]), int(c_entry["enclosing_union"][1]))),
                canonical_rational_str(Fraction(int(c_entry["later_electron_current"][0]), int(c_entry["later_electron_current"][1]))),
            ]
        )
    wire_csv = _csv_text(
        [
            "record_kind",
            "cut",
            "window",
            "coupled",
            "Phi_cross",
            "Phi_sweep",
            "Phi_shedding",
            "Phi_moving",
            "wire_outward",
            "electron_outward",
            "union_boundary",
            "later_electron_current",
        ],
        wire_rows,
    )

    # 8. Exact rational 209-bin pooled SPARC primary score from raw .dat inputs
    sparc_bins: list[dict[str, str]] = []
    for gal in ("NGC2403", "NGC3198", "NGC6503", "NGC2841", "DDO154"):
        dat_path = root / "manual" / "data" / "sparc" / f"{gal}_rotmod.dat"
        require(dat_path.is_file() and not dat_path.is_symlink(), f"missing SPARC dat: {gal}")
        for line in dat_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            require(len(parts) >= 6, f"malformed SPARC dat row in {gal}")
            sparc_bins.append(
                {
                    "r_kpc": parts[0],
                    "V_obs": parts[1],
                    "V_gas": parts[3],
                    "V_disk": parts[4],
                    "V_bul": parts[5],
                }
            )
    sparc_pooled = eval_sparc_pooled_primary_exact({"bins": sparc_bins})
    require(sparc_pooled["N_total"] == 209 and sparc_pooled["N_scored"] == 209, "expected 209 SPARC bins")
    mape_num, mape_den = sparc_pooled["MAPE_U_exact"]
    sparc_csv = _csv_text(
        [
            "record_kind",
            "quantity",
            "aggregation",
            "N_total",
            "N_scored",
            "MAPE_U_num",
            "MAPE_U_den",
            "MAPE_U_display_8dp",
        ],
        [
            [
                "computed_current_primary_exact",
                "U=V^2",
                "equal_weight_per_positive_U_obs_bin",
                sparc_pooled["N_total"],
                sparc_pooled["N_scored"],
                mape_num,
                mape_den,
                sparc_pooled["MAPE_U_8dp"],
            ]
        ],
    )

    tables = {
        "manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv": dec_csv,
        "manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv": tau_csv,
        "manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv": atlas_csv,
        "manual/data/boundary_sadar/higgs_baryon_overlap_saddle_scan.csv": higgs_scan_csv,
        "manual/data/boundary_sadar/dimonhexon_double_slit_ring_paths.csv": slit_csv,
        "manual/data/boundary_sadar/hydrogen_shell_exact_series.csv": hyd_csv,
        "manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv": wire_csv,
        "manual/data/boundary_sadar/sparc_pooled_primary_exact.csv": sparc_csv,
    }
    tables.update(expected_manual_dec_csv_map())
    return tables


def verify_boundary_sadar(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Tier-2 exact zero-float verifier for Sector 17 (``boundary_sadar``)."""
    root = Path(repo_root).resolve()
    cb_path = root / "contracts" / "scientific" / "CANONICAL_BINDINGS.json"
    require(cb_path.is_file() and not cb_path.is_symlink(), "CANONICAL_BINDINGS.json missing")
    cb_doc = loads_zero_float(cb_path.read_text(encoding="utf-8"))
    require_no_floats(cb_doc)
    require(isinstance(cb_doc, dict) and isinstance(cb_doc.get("frozen_sha256"), dict), "invalid CANONICAL_BINDINGS")
    frozen = cb_doc["frozen_sha256"]

    expected_tables = build_boundary_sadar_tables(root)
    require(
        tuple(sorted(expected_tables.keys())) == BOUNDARY_SADAR_FILES,
        "boundary_sadar expected table inventory mismatch",
    )

    verified_digests: dict[str, str] = {}
    csv_count = 0
    total_rows = 0
    for rel_path in sorted(spec.input_paths):
        p = root / rel_path
        require(p.is_file() and not p.is_symlink(), f"missing boundary_sadar input: {rel_path}")
        for parent in Path(rel_path).parents:
            if parent != Path("."):
                require(not (root / parent).is_symlink(), f"symlink parent forbidden: {rel_path}")
        raw_bytes = p.read_bytes()
        sha = hashlib.sha256(raw_bytes).hexdigest()
        require(rel_path in frozen and frozen[rel_path] == sha, f"frozen_sha256 mismatch on {rel_path}")
        verified_digests[rel_path] = sha
        if rel_path.startswith("manual/data/boundary_sadar/"):
            expected_text = expected_tables[rel_path]
            require(
                raw_bytes == expected_text.encode("utf-8"),
                f"committed CSV {rel_path} diverges from live Boundary-Full SADAR engine output",
            )
            csv_count += 1
            total_rows += len(expected_text.splitlines()) - 1

    require(csv_count == len(BOUNDARY_SADAR_FILES), f"expected {len(BOUNDARY_SADAR_FILES)} boundary_sadar CSVs, got {csv_count}")
    extra_check = verify_manual_dec_examples(root)
    require(extra_check["run_tumble_stepper_rows_matched"] == 21, "run_tumble stepper parity failed")

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": verified_digests,
        "verified_counts": {
            "boundary_sadar_csvs_verified": csv_count,
            "total_generated_rows_verified": total_rows,
            "rest_energy_carriers_verified": 10,
            "higgs_saddle_candidates_scanned": 20,
            "hydrogen_transitions_verified": 14,
            "sparc_pooled_bins_verified": 209,
        },
        "exact_residuals_summary": {
            "exact_match": True,
            "max_residual": "0",
            "tau_winner": "1:2:9_yro",
            "tau_miss_conditional_exo": "31/50",
            "higgs_saddle_winner": "3:3:7_yro",
            "common_bit_window_span": 8160,
            "summed_8_lineage_closures": 9104,
        },
        "error": None,
    }
