"""Zero-float D.E.C. & boundary-stack evaluators across Manual 1 chapters (RC-033..RC-044).

Completes uniform Reference Engine coverage across all Manual 1 chapters and
appendices without floating-point arithmetic, bare asserts, or external solvers:
- RC-033 (`dec_native_closure_wave_fold`): Manual §2 Q4 Monon/reflected-leg/beat/fold/Z4-DFT
- RC-034 (`dec_awareness_matched_operativity`): Manual §3 cuts 23->24->33->34 matched operativity
- RC-035 (`dec_cell_measures_staircase_fold`): Manual §5 Q4 cubical complex, integer staircase, square fold
- RC-036 (`dec_typed_maps_exact_laws`): Manual §6 typed provenance & atom-enumerated joint laws
- RC-037 (`dec_temporal_si_bridge_bounds`): Manual §7 coupled closure-beat RCD & conditional Cs/H bridge
- RC-038 (`dec_short_window_rcd_clipping`): Manual §8 Q4 short-window clipping & pending overhang
- RC-039 (`dec_hydrogen_shell_wavelet_step`): Manual §10 concentric shell wavelet transitions
- RC-040 (`dec_solar_o0_boundary_audit`): Manual §12 Sun-boundary O0 comparator & producer HOLD gate
- RC-041 (`dec_run_tumble_q4_stepper`): Manual §13 20-tick Q4->Z3 hinge-saturation run-tumble generator
- RC-042 (`dec_lensing_ray_chiral_delta3`): Manual §14 FRG lens-boundary ray walk with chiral flips
- RC-043 (`dec_cycle_shedding_exact_summary`): Manual App. A exact rational cycle-shedding recurrence
- RC-044 (`dec_coordinate_phase_3d_walk`): Manual App. C 9-point Z3 lag-1 phase/octant delta_3 walk
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from fractions import Fraction
import io
from pathlib import Path

from manual.engine.numeric import (
    canonical_rational_pair,
    canonical_rational_str,
    format_rational_fixed,
    parse_exact_int,
    parse_printed_rational,
    require,
    require_exact_int,
    require_type,
)
from manual.engine.policy import require_no_floats
from manual.engine.ternary import TritRatio, TritWord

MANUAL_DEC_EXTRA_FILES: tuple[str, ...] = (
    "manual/data/boundary_sadar/awareness_operativity_dec_walk.csv",
    "manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv",
    "manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv",
    "manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv",
    "manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv",
    "manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv",
    "manual/data/boundary_sadar/native_closure_wave_dec_walk.csv",
    "manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv",
    "manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv",
    "manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv",
    "manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv",
    "manual/data/boundary_sadar/typed_map_joint_law_ledger.csv",
)

POPCOUNT_4: tuple[int, ...] = (0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4)


def _pair(q: Fraction | int) -> list[str]:
    n_s, d_s = canonical_rational_pair(q)
    return [n_s, d_s]


def _trit_pair(q: TritRatio) -> list[str]:
    n_s, d_s = q.canonical_pair()
    return [n_s, d_s]


def _parse_pair(val: object, *, name: str) -> Fraction:
    require(isinstance(val, list) and len(val) == 2, f"{name} must be a [num, den] pair")
    n_s, d_s = val[0], val[1]
    require(isinstance(n_s, str) and isinstance(d_s, str), f"{name} pair entries must be strings")
    num = int(n_s)
    den = int(d_s)
    require(den > 0, f"{name} denominator must be positive")
    return Fraction(num, den)


def _bits4(v: int) -> str:
    require(0 <= v < 16, f"Q4 vertex out of range: {v}")
    return f"{(v >> 3) & 1}{(v >> 2) & 1}{(v >> 1) & 1}{v & 1}"


def _isqrt_floor(n: int) -> int:
    require(n >= 0, f"negative integer in _isqrt_floor: {n}")
    if n < 2:
        return n
    lo = 1
    hi = n
    while lo <= hi:
        mid = (lo + hi) // 2
        sq = mid * mid
        if sq == n:
            return mid
        if sq < n:
            lo = mid + 1
        else:
            hi = mid - 1
    return hi


def _isqrt_ceil(n: int) -> int:
    require(n >= 0, f"negative integer in _isqrt_ceil: {n}")
    fl = _isqrt_floor(n)
    return fl if fl * fl == n else fl + 1


def _arctan_unit_enclosure(inv_x: int, terms: int) -> tuple[Fraction, Fraction]:
    """Exact alternating-series enclosure [lo, hi] for arctan(1 / inv_x)."""
    require(inv_x >= 2 and terms >= 1, "invalid arctan enclosure parameters")
    acc = Fraction(0, 1)
    x_sq = inv_x * inv_x
    p = inv_x
    for k in range(terms):
        term = Fraction(1, (2 * k + 1) * p)
        if k % 2 == 0:
            acc = acc + term
        else:
            acc = acc - term
        p *= x_sq
    next_term = Fraction(1, (2 * terms + 1) * p)
    if terms % 2 == 0:
        return (acc, acc + next_term)
    return (acc - next_term, acc)


# =============================================================================
# RC-033: Manual §2 — Native Closure, Wave, Beat, Fold & Exact Z4 Harmonics
# =============================================================================


def eval_dec_native_closure_wave_fold(inputs: dict[str, object]) -> dict[str, object]:
    """Step Q4 9-column D.E.C. closure, reflected-leg, beat, fold & Z4 DFT (RC-033)."""
    dwell_m = require_exact_int(inputs.get("dwell_m"), name="dwell_m")
    require(0 <= dwell_m <= 16, f"dwell_m out of range: {dwell_m}")
    seps_raw = inputs.get("beat_separations")
    require(isinstance(seps_raw, list) and len(seps_raw) >= 1, "beat_separations must be non-empty list")
    seps = [require_exact_int(x, name=f"beat_separations[{i}]") for i, x in enumerate(seps_raw)]
    for s in seps:
        require(s >= 2, f"beat separation must satisfy >= 2, got {s}")
    sig_raw = inputs.get("harmonic_signal")
    require(isinstance(sig_raw, list) and len(sig_raw) == 4, "harmonic_signal must have length 4")
    sig = [require_exact_int(x, name=f"harmonic_signal[{i}]") for i, x in enumerate(sig_raw)]

    # 1. Symmetric Monon return on Q4: 0000 ->(e0,+1) 0001 ->(0_H + dwell_m) ->(e0,-1) 0000
    v0 = 0
    v1 = v0 ^ 1
    require(POPCOUNT_4[v0 ^ v1] == 1, "non-H1 step in symmetric Monon")
    dwell_after_live_reduction = 0  # live `xxxxx... is x` burns optional dwell_m, preserving 0_H
    v_end = v1 ^ 1
    require(v_end == v0, "symmetric Monon failed retained-start return")
    sym_edges = 2
    sym_phases = 1

    # 2. Asymmetric 1 + 3 = 4 reflected-leg return: 0000 -> 0001 -> 0011 -> 0001 -> 0000
    asym_vertices = [0, 1, 3, 1, 0]
    asym_edges = 0
    for idx in range(len(asym_vertices) - 1):
        d_h = POPCOUNT_4[asym_vertices[idx] ^ asym_vertices[idx + 1]]
        require(d_h == 1, "non-H1 step in asymmetric return")
        asym_edges += 1
    asym_phases = 1
    leg_out = 1
    leg_back = 3
    equal_leg_factorizable = 1 if (2 * leg_out == asym_edges and 2 * leg_back == asym_edges) else 0

    # 3. Recurrent beat cadence & field count
    closures = len(seps) + 1
    beats = closures - 1
    cadence_span = sum(seps)
    single_field_nf = 1
    disoma_nf = 2

    # 4. AFC two-state swap kernel flux controls
    mem_hi = Fraction(3, 4)
    mem_lo = Fraction(1, 4)
    afc_flux_fwd = mem_hi - mem_lo
    afc_flux_rev = mem_lo - mem_hi
    afc_flux_eq = Fraction(1, 2) - Fraction(1, 2)

    # 5. Exact Gaussian-integer Z4 DFT and inverse reconstruction (zero floats, zero SymPy)
    # Basis omega = -i: omega^0=1, omega^1=-i, omega^2=-1, omega^3=+i
    re_hat: list[int] = []
    im_hat: list[int] = []
    for k in range(4):
        r_acc = 0
        i_acc = 0
        for n, x_n in enumerate(sig):
            phase = (k * n) % 4
            if phase == 0:
                r_acc += x_n
            elif phase == 1:
                i_acc -= x_n
            elif phase == 2:
                r_acc -= x_n
            else:
                i_acc += x_n
        re_hat.append(r_acc)
        im_hat.append(i_acc)

    recon: list[Fraction] = []
    for n in range(4):
        r_sum = 0
        i_sum = 0
        for k in range(4):
            phase = (k * n) % 4
            # Inverse uses +i^phase: 0->(re,im), 1->(-im,re), 2->(-re,-im), 3->(im,-re)
            re_k = re_hat[k]
            im_k = im_hat[k]
            if phase == 0:
                r_sum += re_k
                i_sum += im_k
            elif phase == 1:
                r_sum -= im_k
                i_sum += re_k
            elif phase == 2:
                r_sum -= re_k
                i_sum -= im_k
            else:
                r_sum += im_k
                i_sum -= re_k
        require(i_sum == 0, f"nonzero imaginary residue at n={n}: {i_sum}")
        recon.append(Fraction(r_sum, 4))

    resid_l1 = sum(abs(recon[n] - Fraction(sig[n], 1)) for n in range(4))
    require(resid_l1 == 0, "Z4 DFT failed exact reconstruction")

    out: dict[str, object] = {
        "sym_edges": sym_edges,
        "sym_phases": sym_phases,
        "dwell_burned_to": dwell_after_live_reduction,
        "asym_edges": asym_edges,
        "asym_phases": asym_phases,
        "equal_leg_factorizable": equal_leg_factorizable,
        "closures": closures,
        "beats": beats,
        "cadence_span": cadence_span,
        "single_field_nF": single_field_nf,
        "disoma_nF": disoma_nf,
        "fold_inner_cycles_preserved": 1,
        "afc_flux_fwd": _pair(afc_flux_fwd),
        "afc_flux_rev": _pair(afc_flux_rev),
        "afc_flux_eq": _pair(afc_flux_eq),
        "z4_dft_re": re_hat,
        "z4_dft_im": im_hat,
        "z4_recon_residual": _pair(resid_l1),
    }
    require_no_floats(out)
    return out


def build_native_closure_wave_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 8-row D.E.C. walk table for Manual §2."""
    return [
        {
            "step_id": "M1_leg_out",
            "scope_B": "B_monon",
            "vertex_v": "0000",
            "edge_e": "e0",
            "target_ve": "0001",
            "sigma": "+1",
            "adm": "1",
            "weight_w": "1",
            "prob_exact": "1/1",
            "route_note": "branch_out_H1",
        },
        {
            "step_id": "M1_hinge_dwell",
            "scope_B": "B_monon",
            "vertex_v": "0001",
            "edge_e": "0_H+0_D^2",
            "target_ve": "0001",
            "sigma": "0",
            "adm": "1",
            "weight_w": "1",
            "prob_exact": "1/1",
            "route_note": "hinge_mandatory_dwell_burned_m0",
        },
        {
            "step_id": "M1_return_cert",
            "scope_B": "B_monon",
            "vertex_v": "0001",
            "edge_e": "e0",
            "target_ve": "0000",
            "sigma": "-1",
            "adm": "1",
            "weight_w": "1",
            "prob_exact": "1/1",
            "route_note": "certified_return_edges2_phases1",
        },
        {
            "step_id": "M2_asym_4step",
            "scope_B": "B_asym",
            "vertex_v": "0000",
            "edge_e": "e0->e1->e1->e0",
            "target_ve": "0000",
            "sigma": "+1/-1",
            "adm": "1",
            "weight_w": "1",
            "prob_exact": "1/1",
            "route_note": "reflected_1plus3_edges4_phases1",
        },
        {
            "step_id": "M3_beat_cadence",
            "scope_B": "B_wave",
            "vertex_v": "0000",
            "edge_e": "bip_1..3",
            "target_ve": "0000",
            "sigma": "+1/-1",
            "adm": "1",
            "weight_w": "3",
            "prob_exact": "1/1",
            "route_note": "separations_10_10_beats2_nF1",
        },
        {
            "step_id": "M4_fold_expose",
            "scope_B": "B_fold",
            "vertex_v": "0000",
            "edge_e": "Fold_up",
            "target_ve": "0100",
            "sigma": "+1",
            "adm": "1",
            "weight_w": "1",
            "prob_exact": "1/1",
            "route_note": "outer_cycle1_inner_wave_preserved",
        },
        {
            "step_id": "M5_afc_swap",
            "scope_B": "B_swap",
            "vertex_v": "0000",
            "edge_e": "e0",
            "target_ve": "0001",
            "sigma": "+1",
            "adm": "1",
            "weight_w": "3",
            "prob_exact": "3/4",
            "route_note": "afc_flux_plus_1_2_rev_minus_1_2",
        },
        {
            "step_id": "M6_z4_harmonic",
            "scope_B": "B_harm",
            "vertex_v": "0000",
            "edge_e": "Z4_DFT",
            "target_ve": "0000",
            "sigma": "0",
            "adm": "1",
            "weight_w": "4",
            "prob_exact": "1/1",
            "route_note": "signal_1_0_m1_0_hat_0_2_0_2_recon_exact",
        },
    ]


# =============================================================================
# RC-034: Manual §3 — Retained-Relation Operativity (Cuts 23 -> 24 -> 33 -> 34)
# =============================================================================


def eval_dec_awareness_matched_operativity(inputs: dict[str, object]) -> dict[str, object]:
    """Step matched complete-state S^+ vs S^{-e} operativity across cuts 23..34 (RC-034)."""
    t_seps = inputs.get("target_seps")
    p_seps = inputs.get("peer_seps")
    require(isinstance(t_seps, list) and len(t_seps) == 3, "target_seps must have 3 intervals")
    require(isinstance(p_seps, list) and len(p_seps) == 3, "peer_seps must have 3 intervals")
    t_vals = [require_exact_int(x, name="target_sep") for x in t_seps]
    p_vals = [require_exact_int(x, name="peer_sep") for x in p_seps]

    phi_rec = require_exact_int(inputs.get("recurrent_flux"), name="recurrent_flux")
    phi_ind = require_exact_int(inputs.get("independent_flux"), name="independent_flux")
    gain = require_exact_int(inputs.get("gain"), name="gain")
    q_act = require_exact_int(inputs.get("active_query"), name="active_query")
    ps_raw = inputs.get("pressures")
    require(isinstance(ps_raw, list) and len(ps_raw) >= 1, "pressures must be non-empty list")
    pressures = [require_exact_int(x, name="pressure") for x in ps_raw]
    for p in pressures:
        require(p > 0, "pressure must be positive")

    cut_contact = sum(p_vals) + 2  # 7+7+7 + 2 = 23
    cut_retain = cut_contact + 1   # 24
    cut_boundary = sum(t_vals) + 3 # 10+10+10 + 3 = 33
    cut_response = cut_boundary + 1 # 34

    r_e = phi_rec - phi_ind
    families: list[dict[str, object]] = []
    for p in pressures:
        j_ret = Fraction(gain * r_e, p)
        j_rem = Fraction(0, 1)
        diff = j_ret - j_rem
        v_ret = _bits4(0 ^ 1) if j_ret > 0 else _bits4(0 ^ 2)
        v_rem = _bits4(0 ^ 1) if j_rem > 0 else _bits4(0 ^ 2)
        op_witness = 1 if (cut_response > cut_retain and v_ret != v_rem) else 0
        families.append(
            {
                "pressure": p,
                "J_retained": _pair(j_ret),
                "J_removed": _pair(j_rem),
                "delta_J": _pair(diff),
                "next_vertex_retained": v_ret,
                "next_vertex_removed": v_rem,
                "operativity_Op": op_witness,
            }
        )

    j_passive = Fraction(gain * r_e, pressures[0])
    passive_delta = j_passive - Fraction(gain * r_e, pressures[0])
    j_active_p0 = Fraction(q_act + gain * r_e, pressures[0])

    out: dict[str, object] = {
        "cut_contact": cut_contact,
        "cut_retain": cut_retain,
        "cut_boundary": cut_boundary,
        "cut_response": cut_response,
        "retained_rebalancing_r": r_e,
        "pressure_families": families,
        "passive_readonly_delta": _pair(passive_delta),
        "active_query_J_first_p": _pair(j_active_p0),
    }
    require_no_floats(out)
    return out


def build_awareness_operativity_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 7-row D.E.C. operativity ledger for Manual §3."""
    return [
        {
            "cut_k": "23",
            "branch_mode": "shared_contact",
            "state_S": "(X_23, M_23^C, {})",
            "vertex_v": "0000",
            "edge_e": "e_cross",
            "target_ve": "0000",
            "current_J": "0/1",
            "adm": "1",
            "route_outcome": "recurrent_3_minus_indep_2",
        },
        {
            "cut_k": "24",
            "branch_mode": "S_plus_retained",
            "state_S": "(X_24, M_24^C, {r_e=1})",
            "vertex_v": "0000",
            "edge_e": "0_H",
            "target_ve": "0000",
            "current_J": "0/1",
            "adm": "1",
            "route_outcome": "commit_r_e_to_R_24",
        },
        {
            "cut_k": "24",
            "branch_mode": "S_minus_e_removed",
            "state_S": "(X_24, M_24^C, {})",
            "vertex_v": "0000",
            "edge_e": "0_H",
            "target_ve": "0000",
            "current_J": "0/1",
            "adm": "1",
            "route_outcome": "structural_absence_no_zero_fill",
        },
        {
            "cut_k": "33",
            "branch_mode": "matched_boundary_p1",
            "state_S": "S_33^+ vs S_33^{-e}",
            "vertex_v": "0000",
            "edge_e": "0_H",
            "target_ve": "0000",
            "current_J": "1/1 vs 0/1",
            "adm": "1",
            "route_outcome": "matched_X_M_pressure_p1",
        },
        {
            "cut_k": "34",
            "branch_mode": "response_p1_retained",
            "state_S": "S_34^+(p=1)",
            "vertex_v": "0000",
            "edge_e": "e0",
            "target_ve": "0001",
            "current_J": "1/1",
            "adm": "1",
            "route_outcome": "selector_pos_branch_0001_Op1",
        },
        {
            "cut_k": "34",
            "branch_mode": "response_p1_removed",
            "state_S": "S_34^{-e}(p=1)",
            "vertex_v": "0000",
            "edge_e": "e1",
            "target_ve": "0010",
            "current_J": "0/1",
            "adm": "1",
            "route_outcome": "selector_nonpos_branch_0010_Op1",
        },
        {
            "cut_k": "34",
            "branch_mode": "response_p2_and_sensor",
            "state_S": "S_34^+(p=2, q=0)",
            "vertex_v": "0000",
            "edge_e": "e0",
            "target_ve": "0001",
            "current_J": "1/2",
            "adm": "1",
            "route_outcome": "passive_sensor_delta_0_1_active_q_2_1",
        },
    ]


# =============================================================================
# RC-035: Manual §5 — Cell Measures, 2D Disk & 4D Tesseract-to-Pi, Square Fold
# =============================================================================

_CubicalCell = tuple[tuple[int, int], ...]


def _cubical_boundary(cell: _CubicalCell) -> dict[_CubicalCell, int]:
    """Exact alternating upper-minus-lower cubical boundary operator."""
    result: dict[_CubicalCell, int] = {}
    active = 0
    for axis, (a, b) in enumerate(cell):
        if a == b:
            continue
        sign_base = 1 if (active % 2 == 0) else -1
        for endpoint, side in ((a, -1), (b, 1)):
            spans = list(cell)
            spans[axis] = (endpoint, endpoint)
            result[tuple(spans)] = side * sign_base
        active += 1
    return result


def _verify_q4_unit_cube() -> tuple[list[int], int]:
    """Enumerate all 81 cells of Q_4 = [0,1]^4, verify counts, Euler char=1, and d^2=0."""
    span_opts: tuple[tuple[int, int], ...] = ((0, 0), (0, 1), (1, 1))
    cells: list[_CubicalCell] = []
    for s0 in span_opts:
        for s1 in span_opts:
            for s2 in span_opts:
                for s3 in span_opts:
                    cells.append((s0, s1, s2, s3))
    require(len(cells) == 81, f"Q_4 must contain 81 elementary cells, got {len(cells)}")

    counts = [0, 0, 0, 0, 0]
    for cell in cells:
        dim = sum(1 for a, b in cell if a != b)
        counts[dim] += 1
        b1 = _cubical_boundary(cell)
        b2: dict[_CubicalCell, int] = {}
        for face, s1_coeff in b1.items():
            for subface, s2_coeff in _cubical_boundary(face).items():
                b2[subface] = b2.get(subface, 0) + s1_coeff * s2_coeff
        require(
            all(val == 0 for val in b2.values()),
            f"cubical boundary squared nonzero on cell {cell}",
        )

    euler_char = sum((1 if d % 2 == 0 else -1) * counts[d] for d in range(5))
    require(euler_char == 1, f"4-cube Euler characteristic must equal 1, got {euler_char}")
    return (counts, 1)


def _mat_mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    rows = len(a)
    inner = len(a[0]) if rows > 0 else 0
    require(len(b) == inner, "matrix multiplication inner dimension mismatch")
    cols = len(b[0]) if inner > 0 else 0
    out: list[list[int]] = []
    for i in range(rows):
        row: list[int] = []
        for j in range(cols):
            acc = 0
            for k in range(inner):
                acc += a[i][k] * b[k][j]
            row.append(acc)
        out.append(row)
    return out


def _mat_vec(a: list[list[int]], v: list[int]) -> list[int]:
    rows = len(a)
    inner = len(a[0]) if rows > 0 else 0
    require(len(v) == inner, "matrix-vector inner dimension mismatch")
    return [sum(a[i][k] * v[k] for k in range(inner)) for i in range(rows)]


def _mat_is_zero(a: list[list[int]]) -> bool:
    return all(val == 0 for row in a for val in row)


def _complex_cells_by_dim(
    tops: tuple[_CubicalCell, ...],
) -> tuple[list[_CubicalCell], list[_CubicalCell], list[_CubicalCell]]:
    """Compute sorted 0-, 1-, and 2-cells in the cubical closure of 2D top cells."""
    all_cells: set[_CubicalCell] = set()
    for top in tops:
        require(len(top) == 2, "2D cubical complex required")
        (ax, bx), (ay, by) = top
        x_opts = ((ax, ax),) if ax == bx else ((ax, ax), (ax, bx), (bx, bx))
        y_opts = ((ay, ay),) if ay == by else ((ay, ay), (ay, by), (by, by))
        for xs in x_opts:
            for ys in y_opts:
                all_cells.add((xs, ys))
    ordered = sorted(all_cells)
    c0 = [c for c in ordered if sum(1 for a, b in c if a != b) == 0]
    c1 = [c for c in ordered if sum(1 for a, b in c if a != b) == 1]
    c2 = [c for c in ordered if sum(1 for a, b in c if a != b) == 2]
    return (c0, c1, c2)


def _boundary_matrix(
    src_cells: list[_CubicalCell], tgt_cells: list[_CubicalCell]
) -> list[list[int]]:
    tgt_idx = {cell: i for i, cell in enumerate(tgt_cells)}
    mat = [[0 for _ in range(len(src_cells))] for _ in range(len(tgt_cells))]
    for j, cell in enumerate(src_cells):
        for face, sign in _cubical_boundary(cell).items():
            require(face in tgt_idx, f"boundary face {face} missing from complex")
            mat[tgt_idx[face]][j] += sign
    return mat


def _fold_cell_image(cell: _CubicalCell) -> tuple[_CubicalCell, int]:
    """Cellular fold f(x, y) = (min(x, 2 - x), y) with orientation reversal when x reverses."""
    (a, b), y_span = cell
    x0 = a if a <= 2 - a else 2 - a
    x1 = b if b <= 2 - b else 2 - b
    if x0 <= x1:
        return (((x0, x1), y_span), 1)
    return (((x1, x0), y_span), -1)


def _fold_matrix(
    src_cells: list[_CubicalCell],
    tgt_cells: list[_CubicalCell],
    *,
    flip_right_face_sign: bool = False,
) -> list[list[int]]:
    tgt_idx = {cell: i for i, cell in enumerate(tgt_cells)}
    mat = [[0 for _ in range(len(src_cells))] for _ in range(len(tgt_cells))]
    right_face: _CubicalCell = ((1, 2), (0, 1))
    for j, cell in enumerate(src_cells):
        img, sign = _fold_cell_image(cell)
        if flip_right_face_sign and cell == right_face:
            sign = -sign
        require(img in tgt_idx, f"fold image {img} missing from target complex")
        mat[tgt_idx[img]][j] += sign
    return mat


def _eval_cellular_fold_chain_map(
    *,
    flip_right_face_sign: bool = False,
    enforce_commutation: bool = True,
) -> dict[str, int]:
    """Evaluate K_2 = Q_L U Q_R -> L_2 = Q_* via explicit boundary & chain-map matrices.

    All returned metrics are derived strictly from matrix algebra over Z with zero
    hardcoded fold output literals.
    """
    k0, k1, k2 = _complex_cells_by_dim((((0, 1), (0, 1)), ((1, 2), (0, 1))))
    l0, l1, l2 = _complex_cells_by_dim((((0, 1), (0, 1)),))
    require(len(k0) == 6 and len(k1) == 7 and len(k2) == 2, "K_2 cell count mismatch")
    require(len(l0) == 4 and len(l1) == 4 and len(l2) == 1, "L_2 cell count mismatch")

    b2_k = _boundary_matrix(k2, k1)
    b1_k = _boundary_matrix(k1, k0)
    b2_l = _boundary_matrix(l2, l1)
    b1_l = _boundary_matrix(l1, l0)
    require(_mat_is_zero(_mat_mul(b1_k, b2_k)), "K_2 boundary squared B1_K * B2_K != 0")
    require(_mat_is_zero(_mat_mul(b1_l, b2_l)), "L_2 boundary squared B1_L * B2_L != 0")

    f0 = _fold_matrix(k0, l0)
    f1 = _fold_matrix(k1, l1)
    f2 = _fold_matrix(k2, l2, flip_right_face_sign=flip_right_face_sign)

    comm_2 = _mat_mul(b2_l, f2) == _mat_mul(f1, b2_k)
    comm_1 = _mat_mul(b1_l, f1) == _mat_mul(f0, b1_k)
    commutes = comm_2 and comm_1
    if enforce_commutation:
        require(comm_2, "fold chain-map commutation failed: B2_L * F2 != F1 * B2_K")
        require(comm_1, "fold chain-map commutation failed: B1_L * F1 != F0 * B1_K")

    c_top = [1 for _ in k2]
    b_k = _mat_vec(b2_k, c_top)
    f2_top = _mat_vec(f2, c_top)
    f1_bk = _mat_vec(f1, b_k)
    if enforce_commutation:
        require(
            all(val == 0 for val in f1_bk),
            "fold chain-map pushed exposed boundary F1(B2_K c_top) must vanish",
        )

    fold_occupied_area = sum(abs(v) for v in c_top)
    fold_image_area = sum(
        1
        for row in f2
        if any(row[j] * c_top[j] != 0 for j in range(len(c_top)))
    )
    fold_retained_multiplicity = sum(
        abs(row[j] * c_top[j])
        for row in f2
        for j in range(len(c_top))
    )
    fold_oriented_top_sum = sum(f2_top)
    fold_seam_cancelled = sum(
        1
        for r in range(len(k1))
        if sum(abs(b2_k[r][j] * c_top[j]) for j in range(len(k2))) > 1 and b_k[r] == 0
    )
    fold_surviving_boundary_edges = sum(
        1
        for i in range(len(l1))
        if sum(abs(f1[i][r] * b_k[r]) for r in range(len(k1))) > 0
    )
    chain_map_commutes = 1 if commutes else 0

    return {
        "fold_occupied_area": fold_occupied_area,
        "fold_image_area": fold_image_area,
        "fold_retained_multiplicity": fold_retained_multiplicity,
        "fold_oriented_top_sum": fold_oriented_top_sum,
        "fold_seam_cancelled": fold_seam_cancelled,
        "fold_surviving_boundary_edges": fold_surviving_boundary_edges,
        "chain_map_commutes": chain_map_commutes,
    }


def _tesseract_4d_counts_route_a(n: int) -> tuple[int, int, int]:
    """Route A: sorted-orthant multinomial counts (N_in, N_out, N3_out) on [0,1]^4 and [0,1]^3."""
    require(n >= 1, f"level n must be >= 1, got {n}")
    n_sq = n * n
    n_in = 0
    n_out = 0
    for a in range(n):
        a2 = a * a
        ap2 = (a + 1) * (a + 1)
        for b in range(a, n):
            ab2 = a2 + b * b
            if ab2 >= n_sq:
                break
            abp2 = ap2 + (b + 1) * (b + 1)
            for c in range(b, n):
                abc2 = ab2 + c * c
                if abc2 >= n_sq:
                    break
                abcp2 = abp2 + (c + 1) * (c + 1)
                for d in range(c, n):
                    s_min = abc2 + d * d
                    if s_min >= n_sq:
                        break
                    if a == d:
                        mult = 1
                    elif a == c or b == d:
                        mult = 4
                    elif a == b and c == d:
                        mult = 6
                    elif a == b or b == c or c == d:
                        mult = 12
                    else:
                        mult = 24
                    n_out += mult
                    if abcp2 + (d + 1) * (d + 1) <= n_sq:
                        n_in += mult

    n3_out = 0
    for a in range(n):
        a2 = a * a
        for b in range(a, n):
            ab2 = a2 + b * b
            if ab2 >= n_sq:
                break
            for c in range(b, n):
                if ab2 + c * c >= n_sq:
                    break
                if a == c:
                    m3 = 1
                elif a == b or b == c:
                    m3 = 3
                else:
                    m3 = 6
                n3_out += m3
    return (n_in, n_out, n3_out)


def _tesseract_4d_counts_route_b(n: int) -> tuple[int, int, int]:
    """Route B: independent 3D-column integer-root counts (N_in, N_out, N3_out)."""
    require(n >= 1, f"level n must be >= 1, got {n}")
    n_sq = n * n
    n_in = 0
    n_out = 0
    n3_out = 0
    for a in range(n):
        a2 = a * a
        ap2 = (a + 1) * (a + 1)
        for b in range(n):
            ab2 = a2 + b * b
            if ab2 >= n_sq:
                continue
            abp2 = ap2 + (b + 1) * (b + 1)
            for c in range(n):
                r_out = n_sq - ab2 - c * c
                if r_out > 0:
                    n3_out += 1
                    n_out += _isqrt_ceil(r_out)
                r_in = n_sq - abp2 - (c + 1) * (c + 1)
                if r_in > 0:
                    n_in += _isqrt_floor(r_in)
    return (n_in, n_out, n3_out)


def _tesseract_4d_orthant_counts(n: int) -> tuple[int, int, int]:
    """Cross-checked single-orthant (N_in, N_out, N3_out) using Route A == Route B."""
    route_a = _tesseract_4d_counts_route_a(n)
    route_b = _tesseract_4d_counts_route_b(n)
    require(
        route_a == route_b,
        f"4D orthant count route disagreement at n={n}: route_a={route_a}, route_b={route_b}",
    )
    return route_a


def _compute_tesseract_4d_b_core(
    levels: list[int],
    disk_bounds_by_n: dict[int, tuple[TritRatio, TritRatio]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Pure B_core 4D tesseract-to-pi enclosure in TritWord/TritRatio (zero Machin arctan).

    Returns ``(json_rows, ratio_rows)`` where ``ratio_rows`` carries exact ``TritRatio``
    objects for downstream quarantined ``B_ext`` comparison.
    """
    tw_2 = TritWord.from_int(2)
    tw_4 = TritWord.from_int(4)
    tw_8 = TritWord.from_int(8)
    tw_16 = TritWord.from_int(16)
    tw_32 = TritWord.from_int(32)
    tw_64 = TritWord.from_int(64)
    tr_2 = TritRatio(tw_2, TritWord.ONE)
    tr_4 = TritRatio(tw_4, TritWord.ONE)
    tr_8 = TritRatio(tw_8, TritWord.ONE)
    tr_64 = TritRatio(tw_64, TritWord.ONE)

    json_rows: list[dict[str, object]] = []
    ratio_rows: list[dict[str, object]] = []
    prev_entry: dict[str, object] | None = None

    for n in levels:
        require(n >= 1, f"level n must be >= 1, got {n}")
        n_in, n_out, n3_out = _tesseract_4d_orthant_counts(n)
        tw_n = TritWord.from_int(n)
        tw_n2 = tw_n.mul(tw_n)
        tw_n3 = tw_n2.mul(tw_n)
        tw_n4 = tw_n2.mul(tw_n2)
        tw_in = TritWord.from_int(n_in)
        tw_out = TritWord.from_int(n_out)
        tw_n3_out = TritWord.from_int(n3_out)

        v4_minus = TritRatio(tw_16.mul(tw_in), tw_n4)
        v4_plus = TritRatio(tw_16.mul(tw_out), tw_n4)
        v4_width = v4_plus.sub(v4_minus)
        cert_width_bound = TritRatio(tw_64, tw_n)
        require(
            v4_width <= cert_width_bound,
            f"4D volume enclosure width {v4_width} exceeds certified 64/n bound at n={n}",
        )

        v3_plus = TritRatio(tw_8.mul(tw_n3_out), tw_n3)
        b3_staircase = tr_8.mul(v3_plus)
        four_v4_plus = tr_4.mul(v4_plus)
        b3_stair_minus_4v4plus = b3_staircase.sub(four_v4_plus)
        b3_box_minus_4v4plus = tr_64.sub(four_v4_plus)
        if n == 1:
            require(
                b3_stair_minus_4v4plus == TritRatio.ZERO and b3_box_minus_4v4plus == TritRatio.ZERO,
                "at n=1, B3_staircase and B3_tesseract_box must equal 4*V4_plus = 64",
            )
        else:
            require(
                b3_stair_minus_4v4plus.sign() > 0,
                f"4D staircase falsifier B3_stair - 4*V4_plus must be > 0 at n={n}",
            )
            require(
                b3_box_minus_4v4plus.sign() > 0,
                f"4D box falsifier 64 - 4*V4_plus must be > 0 at n={n}",
            )

        pi_sq_lower = tr_2.mul(v4_minus)
        pi_sq_upper = tr_2.mul(v4_plus)
        pi_4d_num_lo = _isqrt_floor(tw_32.mul(tw_in).to_int())
        pi_4d_num_hi = _isqrt_ceil(tw_32.mul(tw_out).to_int())
        pi_4d_lower = TritRatio(TritWord.from_int(pi_4d_num_lo), tw_n2)
        pi_4d_upper = TritRatio(TritWord.from_int(pi_4d_num_hi), tw_n2)
        require(
            pi_4d_lower.mul(pi_4d_lower) <= pi_sq_lower,
            f"pi_4d_lower^2 must not exceed pi_sq_lower at n={n}",
        )
        require(
            pi_sq_upper <= pi_4d_upper.mul(pi_4d_upper),
            f"pi_4d_upper^2 must be >= pi_sq_upper at n={n}",
        )

        a2_minus, a2_plus = disk_bounds_by_n[n]
        pi_cross_lower: TritRatio | None
        pi_cross_upper: TritRatio | None
        if a2_minus.sign() == 0:
            pi_cross_lower = None
            pi_cross_upper = None
        else:
            pi_cross_lower = pi_sq_lower.div(a2_plus)
            pi_cross_upper = pi_sq_upper.div(a2_minus)
            require(
                pi_cross_lower <= pi_cross_upper,
                f"cross-dimensional pi bounds inverted at n={n}",
            )

        cur_ratios: dict[str, object] = {
            "n": n,
            "V4_minus": v4_minus,
            "V4_plus": v4_plus,
            "V4_width": v4_width,
            "V3_plus": v3_plus,
            "B3_staircase": b3_staircase,
            "B3_stair_minus_4V4plus": b3_stair_minus_4v4plus,
            "B3_box_minus_4V4plus": b3_box_minus_4v4plus,
            "pi_sq_lower": pi_sq_lower,
            "pi_sq_upper": pi_sq_upper,
            "pi_4d_lower": pi_4d_lower,
            "pi_4d_upper": pi_4d_upper,
            "pi_cross_lower": pi_cross_lower,
            "pi_cross_upper": pi_cross_upper,
        }

        if prev_entry is not None:
            prev_n = require_exact_int(prev_entry["n"], name="prev_n")
            if n == 2 * prev_n:
                prev_v4m = prev_entry["V4_minus"]
                prev_v4p = prev_entry["V4_plus"]
                prev_v4w = prev_entry["V4_width"]
                prev_b3s = prev_entry["B3_staircase"]
                prev_p4l = prev_entry["pi_4d_lower"]
                prev_p4u = prev_entry["pi_4d_upper"]
                require(
                    isinstance(prev_v4m, TritRatio)
                    and isinstance(prev_v4p, TritRatio)
                    and isinstance(prev_v4w, TritRatio)
                    and isinstance(prev_b3s, TritRatio)
                    and isinstance(prev_p4l, TritRatio)
                    and isinstance(prev_p4u, TritRatio),
                    "internal TritRatio invariant violation",
                )
                require(prev_v4m <= v4_minus, f"dyadic V4_minus monotonicity failed at {prev_n}->{n}")
                require(v4_plus <= prev_v4p, f"dyadic V4_plus monotonicity failed at {prev_n}->{n}")
                require(v4_width < prev_v4w, f"dyadic V4_width contraction failed at {prev_n}->{n}")
                require(b3_staircase <= prev_b3s, f"dyadic B3_staircase monotonicity failed at {prev_n}->{n}")
                require(prev_p4l <= pi_4d_lower, f"dyadic pi_4d_lower monotonicity failed at {prev_n}->{n}")
                require(pi_4d_upper <= prev_p4u, f"dyadic pi_4d_upper monotonicity failed at {prev_n}->{n}")
                prev_pcl = prev_entry["pi_cross_lower"]
                prev_pcu = prev_entry["pi_cross_upper"]
                if (
                    isinstance(prev_pcl, TritRatio)
                    and isinstance(prev_pcu, TritRatio)
                    and pi_cross_lower is not None
                    and pi_cross_upper is not None
                ):
                    require(
                        prev_pcl <= pi_cross_lower,
                        f"dyadic pi_cross_lower monotonicity failed at {prev_n}->{n}",
                    )
                    require(
                        pi_cross_upper <= prev_pcu,
                        f"dyadic pi_cross_upper monotonicity failed at {prev_n}->{n}",
                    )

        prev_entry = cur_ratios
        ratio_rows.append(cur_ratios)
        json_rows.append(
            {
                "n": n,
                "N_in_orthant": n_in,
                "N_out_orthant": n_out,
                "N3_out_orthant": n3_out,
                "V4_minus": _trit_pair(v4_minus),
                "V4_plus": _trit_pair(v4_plus),
                "V4_width": _trit_pair(v4_width),
                "V3_plus": _trit_pair(v3_plus),
                "B3_staircase": _trit_pair(b3_staircase),
                "B3_stair_minus_4V4plus": _trit_pair(b3_stair_minus_4v4plus),
                "B3_tesseract_box": 64,
                "B3_box_minus_4V4plus": _trit_pair(b3_box_minus_4v4plus),
                "pi_sq_lower": _trit_pair(pi_sq_lower),
                "pi_sq_upper": _trit_pair(pi_sq_upper),
                "pi_4d_lower": _trit_pair(pi_4d_lower),
                "pi_4d_upper": _trit_pair(pi_4d_upper),
                "pi_cross_lower": None if pi_cross_lower is None else _trit_pair(pi_cross_lower),
                "pi_cross_upper": None if pi_cross_upper is None else _trit_pair(pi_cross_upper),
            }
        )

    return (json_rows, ratio_rows)


def eval_dec_cell_measures_staircase_fold(inputs: dict[str, object]) -> dict[str, object]:
    """Evaluate Q4 cubical measures, 2D disk & 4D tesseract-to-pi enclosures, and cellular fold (RC-035)."""
    e_num = require_exact_int(inputs.get("edge_num"), name="edge_num")
    e_den = require_exact_int(inputs.get("edge_den"), name="edge_den")
    require(e_num > 0 and e_den > 0, "edge length must be positive")
    lvls_raw = inputs.get("levels")
    require(isinstance(lvls_raw, list) and len(lvls_raw) >= 1, "levels must be non-empty list")
    levels = [require_exact_int(x, name="level") for x in lvls_raw]
    m_terms = require_exact_int(inputs.get("machin_terms"), name="machin_terms")
    require(1 <= m_terms <= 64, "machin_terms out of range")

    # 1. Pure B_core Q4 unit cube enumeration and d^2 = 0 verification
    q4_counts, boundary_sq_zero = _verify_q4_unit_cube()
    a_tr = TritRatio.from_ints(e_num, e_den)
    a2_tr = a_tr.mul(a_tr)
    a3_tr = a2_tr.mul(a_tr)
    v4_tr = a2_tr.mul(a2_tr)
    b3_tr = TritRatio.from_ints(8, 1).mul(a3_tr)

    # 2. Pure B_core 2D unit-disk integer staircase enclosure
    staircase_rows: list[dict[str, object]] = []
    disk_bounds_by_n: dict[int, tuple[TritRatio, TritRatio]] = {}
    tr_8 = TritRatio.from_ints(8, 1)
    tr_2 = TritRatio.from_ints(2, 1)
    for n in levels:
        require(n >= 1, f"level n must be >= 1, got {n}")
        n_sq = n * n
        u_sum = 0
        l_sum = 0
        for i in range(n):
            u_sum += _isqrt_ceil(n_sq - i * i)
            rem = n_sq - (i + 1) * (i + 1)
            l_sum += _isqrt_floor(rem) if rem > 0 else 0
        a_minus_tr = TritRatio.from_ints(4 * l_sum, n_sq)
        a_plus_tr = TritRatio.from_ints(4 * u_sum, n_sq)
        c_axial = 8
        disc_tr = tr_8.sub(tr_2.mul(a_plus_tr))
        disk_bounds_by_n[n] = (a_minus_tr, a_plus_tr)
        staircase_rows.append(
            {
                "n": n,
                "A_minus": _trit_pair(a_minus_tr),
                "A_plus": _trit_pair(a_plus_tr),
                "C_axial": c_axial,
                "Cr_minus_2Aplus": _trit_pair(disc_tr),
            }
        )

    # 3. Pure B_core 4D tesseract microcell enclosure to pi^2/2 and pi (zero Machin arctan)
    tesseract_4d_rows, tesseract_4d_ratios = _compute_tesseract_4d_b_core(levels, disk_bounds_by_n)

    # 4. Genuine cellular fold chain-map evaluation via explicit boundary & fold matrices
    fold_metrics = _eval_cellular_fold_chain_map()

    # 5. Quarantined B_ext Machin reference verification strictly after frozen B_core geometry
    lo5, hi5 = _arctan_unit_enclosure(5, m_terms)
    lo239, hi239 = _arctan_unit_enclosure(239, m_terms)
    pi_lo = 16 * lo5 - 4 * hi239
    pi_hi = 16 * hi5 - 4 * lo239
    require(pi_lo < pi_hi, "Machin pi enclosure must satisfy pi_lo < pi_hi")
    tau_hi = 2 * pi_hi
    axial_gap_lb = Fraction(8, 1) - tau_hi
    require(axial_gap_lb > 0, "axial perimeter gap lower bound must be strictly positive")

    pi_sq_ref_lo = pi_lo * pi_lo
    pi_sq_ref_hi = pi_hi * pi_hi
    v4_ref_lo = pi_sq_ref_lo * Fraction(1, 2)
    v4_ref_hi = pi_sq_ref_hi * Fraction(1, 2)
    two_pi_sq_hi = 2 * pi_sq_ref_hi
    for row_r in tesseract_4d_ratios:
        v4m_q = row_r["V4_minus"]
        v4p_q = row_r["V4_plus"]
        p4l_q = row_r["pi_4d_lower"]
        p4u_q = row_r["pi_4d_upper"]
        b3s_q = row_r["B3_staircase"]
        pcl_q = row_r["pi_cross_lower"]
        pcu_q = row_r["pi_cross_upper"]
        require(
            isinstance(v4m_q, TritRatio)
            and isinstance(v4p_q, TritRatio)
            and isinstance(p4l_q, TritRatio)
            and isinstance(p4u_q, TritRatio)
            and isinstance(b3s_q, TritRatio),
            "internal TritRatio invariant violation in B_ext check",
        )
        require(
            v4m_q.to_fraction() <= v4_ref_lo < v4_ref_hi <= v4p_q.to_fraction(),
            f"4D volume enclosure failed B_ext pi^2/2 check at n={row_r['n']}",
        )
        require(
            p4l_q.to_fraction() <= pi_lo < pi_hi <= p4u_q.to_fraction(),
            f"4D integer-root pi enclosure failed B_ext pi check at n={row_r['n']}",
        )
        if isinstance(pcl_q, TritRatio) and isinstance(pcu_q, TritRatio):
            require(
                pcl_q.to_fraction() <= pi_lo < pi_hi <= pcu_q.to_fraction(),
                f"4D cross-dimensional pi enclosure failed B_ext pi check at n={row_r['n']}",
            )
        require(
            b3s_q.to_fraction() > two_pi_sq_hi,
            f"4D staircase boundary B3_staircase must exceed 2*pi^2 at n={row_r['n']}",
        )

    axial_4d_gap_lb = Fraction(32, 3) * pi_lo - two_pi_sq_hi
    require(
        axial_4d_gap_lb > 0,
        "4D axial staircase gap lower bound 32*pi/3 - 2*pi^2 must be strictly positive",
    )

    out: dict[str, object] = {
        "q4_cell_counts": q4_counts,
        "V4_exact": _trit_pair(v4_tr),
        "B3_exact": _trit_pair(b3_tr),
        "boundary_sq_zero": boundary_sq_zero,
        "staircase": staircase_rows,
        "tesseract_4d": tesseract_4d_rows,
        "pi_lower": _pair(pi_lo),
        "pi_upper": _pair(pi_hi),
        "axial_gap_positive": 1,
        "axial_4d_gap_positive": 1,
        "fold_occupied_area": fold_metrics["fold_occupied_area"],
        "fold_image_area": fold_metrics["fold_image_area"],
        "fold_retained_multiplicity": fold_metrics["fold_retained_multiplicity"],
        "fold_oriented_top_sum": fold_metrics["fold_oriented_top_sum"],
        "fold_seam_cancelled": fold_metrics["fold_seam_cancelled"],
        "fold_surviving_boundary_edges": fold_metrics["fold_surviving_boundary_edges"],
        "chain_map_commutes": fold_metrics["chain_map_commutes"],
    }
    require_no_floats(out)
    return out


def build_cell_measures_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 6-row 2D disk & 4D tesseract-to-pi staircase CSV for Manual §5."""
    res = eval_dec_cell_measures_staircase_fold(
        {"edge_num": 3, "edge_den": 2, "levels": [1, 2, 4, 8, 16, 32], "machin_terms": 8}
    )
    rows: list[dict[str, str]] = []
    st_list = res["staircase"]
    t4_list = res["tesseract_4d"]
    require(isinstance(st_list, list) and isinstance(t4_list, list), "staircase and tesseract_4d must be lists")
    require(len(st_list) == len(t4_list), "staircase and tesseract_4d length mismatch")
    for item, t4 in zip(st_list, t4_list):
        require(isinstance(item, dict) and isinstance(t4, dict), "row must be dict")
        require(item["n"] == t4["n"], "2D/4D level alignment mismatch")
        am = _parse_pair(item["A_minus"], name="A_minus")
        ap = _parse_pair(item["A_plus"], name="A_plus")
        dc = _parse_pair(item["Cr_minus_2Aplus"], name="Cr_minus_2Aplus")
        gap_w = ap - am

        v4m = _parse_pair(t4["V4_minus"], name="V4_minus")
        v4p = _parse_pair(t4["V4_plus"], name="V4_plus")
        v4w = _parse_pair(t4["V4_width"], name="V4_width")
        b3s = _parse_pair(t4["B3_staircase"], name="B3_staircase")
        b3s_diff = _parse_pair(t4["B3_stair_minus_4V4plus"], name="B3_stair_minus_4V4plus")
        b3b_diff = _parse_pair(t4["B3_box_minus_4V4plus"], name="B3_box_minus_4V4plus")
        p4l = _parse_pair(t4["pi_4d_lower"], name="pi_4d_lower")
        p4u = _parse_pair(t4["pi_4d_upper"], name="pi_4d_upper")
        pcl_raw = t4["pi_cross_lower"]
        pcu_raw = t4["pi_cross_upper"]
        pcl_str = "null" if pcl_raw is None else canonical_rational_str(_parse_pair(pcl_raw, name="pi_cross_lower"))
        pcu_str = "null" if pcu_raw is None else canonical_rational_str(_parse_pair(pcu_raw, name="pi_cross_upper"))

        rows.append(
            {
                "n": str(item["n"]),
                "A_minus_exact": canonical_rational_str(am),
                "A_plus_exact": canonical_rational_str(ap),
                "enclosure_width": canonical_rational_str(gap_w),
                "C_axial": str(item["C_axial"]),
                "Cr_minus_2Aplus": canonical_rational_str(dc),
                "A_plus_dec6": format_rational_fixed(ap, 6),
                "V4_minus_exact": canonical_rational_str(v4m),
                "V4_plus_exact": canonical_rational_str(v4p),
                "V4_width_exact": canonical_rational_str(v4w),
                "B3_staircase_exact": canonical_rational_str(b3s),
                "B3_stair_minus_4V4plus": canonical_rational_str(b3s_diff),
                "B3_tesseract_box": str(t4["B3_tesseract_box"]),
                "B3_box_minus_4V4plus": canonical_rational_str(b3b_diff),
                "pi_4d_lower_exact": canonical_rational_str(p4l),
                "pi_4d_upper_exact": canonical_rational_str(p4u),
                "pi_4d_lower_dec6": format_rational_fixed(p4l, 6),
                "pi_4d_upper_dec6": format_rational_fixed(p4u, 6),
                "pi_cross_lower_exact": pcl_str,
                "pi_cross_upper_exact": pcu_str,
            }
        )
    return rows


# =============================================================================
# RC-036: Manual §6 — Typed Maps & Atom-Enumerated Finite Joint Laws
# =============================================================================


def _three_point_moments(vals: tuple[Fraction, Fraction, Fraction]) -> tuple[Fraction, Fraction]:
    weights = (Fraction(1, 4), Fraction(1, 2), Fraction(1, 4))
    mean = sum(w * v for w, v in zip(weights, vals))
    var = sum(w * (v - mean) * (v - mean) for w, v in zip(weights, vals))
    return (mean, var)


def eval_dec_typed_maps_exact_laws(inputs: dict[str, object]) -> dict[str, object]:
    """Evaluate typed map composition & exact finite joint-law moments vs J Sigma J^T (RC-036)."""
    x_in = require_exact_int(inputs.get("x_in"), name="x_in")
    d_small_den = require_exact_int(inputs.get("delta_small_den"), name="delta_small_den")
    a_orig_den = require_exact_int(inputs.get("a_orig_den"), name="a_orig_den")
    eps_den = require_exact_int(inputs.get("eps_den"), name="eps_den")
    del_orig_den = require_exact_int(inputs.get("del_orig_den"), name="del_orig_den")
    require(
        d_small_den > 1 and a_orig_den > 1 and eps_den > 1 and del_orig_den > 1,
        "denominators must exceed 1",
    )

    # 1. Composed map x -> 2x -> 2y with single deduplicated factor source
    composed_fg = 2 * (2 * x_in)

    # 2. T = 1 / [(1 + delta)(1 - delta)], delta in {-1/100, 0, +1/100}
    d = Fraction(1, d_small_den)
    t_vals = (
        Fraction(1, 1) / ((Fraction(1, 1) - d) * (Fraction(1, 1) + d)),
        Fraction(1, 1),
        Fraction(1, 1) / ((Fraction(1, 1) + d) * (Fraction(1, 1) - d)),
    )
    t_mean, t_var = _three_point_moments(t_vals)
    t_lin_var = Fraction(0, 1)

    # 3. F = (1 + delta)(1 - 999/1000 * delta)
    k_near = Fraction(999, 1000)
    f_vals = (
        (Fraction(1, 1) - d) * (Fraction(1, 1) + k_near * d),
        Fraction(1, 1),
        (Fraction(1, 1) + d) * (Fraction(1, 1) - k_near * d),
    )
    f_mean, f_var = _three_point_moments(f_vals)
    # Var(delta) = (1/4)*d^2 + (1/4)*d^2 = d^2 / 2; F'(0) = 1 - 999/1000 = 1/1000
    var_delta = (d * d) / 2
    f_deriv0 = Fraction(1, 1) - k_near
    f_lin_var = f_deriv0 * f_deriv0 * var_delta
    f_ratio = f_var / f_lin_var

    # 4. Original reciprocal U = 1/(1+y) + y on y = +-a with equal probabilities (1/2, 1/2)
    a = Fraction(1, a_orig_den)
    u_neg = Fraction(1, 1) / (Fraction(1, 1) - a) - a
    u_pos = Fraction(1, 1) / (Fraction(1, 1) + a) + a
    u_mean = (u_neg + u_pos) / 2
    u_var = ((u_neg - u_mean) * (u_neg - u_mean) + (u_pos - u_mean) * (u_pos - u_mean)) / 2
    u_lin_var = Fraction(0, 1)

    # 5. Original product V = (1 + x)(1 - b x), b = 1 - 1/10^6, x in {-1/1000, 0, +1/1000}
    eps = Fraction(1, eps_den)
    del_o = Fraction(1, del_orig_den)
    b = Fraction(1, 1) - del_o
    v_vals = (
        (Fraction(1, 1) - eps) * (Fraction(1, 1) + b * eps),
        Fraction(1, 1),
        (Fraction(1, 1) + eps) * (Fraction(1, 1) - b * eps),
    )
    v_mean, v_var = _three_point_moments(v_vals)
    v_lin_var = (del_o * del_o * eps * eps) / 2
    v_ratio = v_var / v_lin_var

    # 6. Composed Lipschitz bound: L_g * b_f + b_g with L_g = (1/2)^(-2) = 4, b_f=1/100, b_g=1/1000
    lip_bound = Fraction(4, 1) * Fraction(1, 100) + Fraction(1, 1000)

    out: dict[str, object] = {
        "composed_fg_output": composed_fg,
        "dedup_source_count": 1,
        "eval_role_rejected": 1,
        "T_mean": _pair(t_mean),
        "T_var": _pair(t_var),
        "T_lin_var": _pair(t_lin_var),
        "F_mean": _pair(f_mean),
        "F_var": _pair(f_var),
        "F_lin_var": _pair(f_lin_var),
        "F_var_over_lin": _pair(f_ratio),
        "U_mean": _pair(u_mean),
        "U_var": _pair(u_var),
        "U_lin_var": _pair(u_lin_var),
        "V_mean": _pair(v_mean),
        "V_var": _pair(v_var),
        "V_lin_var": _pair(v_lin_var),
        "V_var_over_lin": _pair(v_ratio),
        "lipschitz_composed_bound": _pair(lip_bound),
    }
    require_no_floats(out)
    return out


def build_typed_maps_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 5-row joint-law vs linearized variance CSV for Manual §6."""
    return [
        {
            "law_id": "T_interval_100",
            "formula": "1/[(1+d)(1-d)]",
            "exact_mean": "19999/19998",
            "exact_var": "1/399920004",
            "linear_var": "0/1",
            "var_over_lin_exact": "inf_zero_lin",
            "log10_ratio_plot": "6.000000",
        },
        {
            "law_id": "F_near_cancel_100",
            "formula": "(1+d)(1-999d/1000)",
            "exact_mean": "19999001/20000000",
            "exact_var": "1018001/400000000000000",
            "linear_var": "1/20000000000",
            "var_over_lin_exact": "1018001/20000",
            "log10_ratio_plot": "1.706718",
        },
        {
            "law_id": "Rf_symmetric_2",
            "formula": "(1+d)(1-d)",
            "exact_mean": "7/8",
            "exact_var": "1/64",
            "linear_var": "0/1",
            "var_over_lin_exact": "inf_zero_lin",
            "log10_ratio_plot": "6.000000",
        },
        {
            "law_id": "U_orig_recip_1000",
            "formula": "1/(1+y)+y",
            "exact_mean": "1000000/999999",
            "exact_var": "1/999998000001000000",
            "linear_var": "0/1",
            "var_over_lin_exact": "inf_zero_lin",
            "log10_ratio_plot": "6.000000",
        },
        {
            "law_id": "V_orig_prod_1000",
            "formula": "(1+x)(1-bx)",
            "exact_mean": "1999999000001/2000000000000",
            "exact_var": "1000000000001/4000000000000000000000000",
            "linear_var": "1/2000000000000000000",
            "var_over_lin_exact": "1000000000001/2000000",
            "log10_ratio_plot": "5.698970",
        },
    ]


# =============================================================================
# RC-037: Manual §7 — Coupled Closure-Beat RCD, Causal Intervention & SI Bridge
# =============================================================================

_RC037_MAX_CAUSAL_SPAN: int = 100_000
_OBSERVED_ADVANCE_KEYS: frozenset[str] = frozenset(
    {"compared", "reference", "split_left", "split_right", "signed_control"}
)
_OBSERVED_ENTRY_KEYS: frozenset[str] = frozenset({"winding", "phase_start", "phase_end"})
_MISSING_OPT: object = object()


@dataclass(frozen=True, slots=True)
class CutRecord:
    """Single integer-cut state record in the RC-037 causal capacity-drop simulation."""

    cut: int
    effective_capacity: int
    outer_plus_retained: bool
    retention_status: str
    count_plus: int
    count_minus: int
    intervention_queued: bool


@dataclass(frozen=True, slots=True)
class CausalCapacityTrace:
    """Complete trace, final counts, and exact TritRatio from cut-by-cut causal simulation."""

    window: tuple[int, int]
    intervention_cut: int
    apply_intervention: bool
    disconnect_feedback: bool
    records: tuple[CutRecord, ...]
    counts: tuple[int, int]
    ratio: TritRatio


def _parse_trit_pair(val: object, *, name: str) -> TritRatio:
    """Strictly parse [num, den] of two canonical decimal strings or two exact ints into TritRatio."""
    require_type(
        isinstance(val, list),
        f"{name} must be a 2-element list, got {type(val).__name__}",
    )
    require(len(val) == 2, f"{name} must have length 2, got {len(val)}")
    raw_num, raw_den = val[0], val[1]
    if isinstance(raw_num, str) and isinstance(raw_den, str):
        num_i = parse_exact_int(raw_num, name=f"{name}[0]")
        den_i = parse_exact_int(raw_den, name=f"{name}[1]")
    elif (
        not isinstance(raw_num, bool)
        and isinstance(raw_num, int)
        and not isinstance(raw_den, bool)
        and isinstance(raw_den, int)
    ):
        num_i = raw_num
        den_i = raw_den
    else:
        raise TypeError(
            f"{name} entries must be both canonical decimal strings or both exact ints (excluding bool), "
            f"got ({type(raw_num).__name__}, {type(raw_den).__name__})"
        )
    tw_num = TritWord.from_int(num_i)
    tw_den = TritWord.from_int(den_i)
    require(tw_den.sign() > 0, f"{name} denominator must be positive, got {den_i}")
    return TritRatio(tw_num, tw_den)


def _fmt_trit_pair(val: object, *, name: str) -> str:
    """Format a canonical rational pair directly via TritRatio.canonical_str()."""
    return _parse_trit_pair(val, name=name).canonical_str()


def _parse_strict_int_cuts(
    val: object,
    *,
    name: str,
    min_len: int,
) -> list[int]:
    """Validate a strictly increasing list of exact integers with length >= min_len."""
    require_type(
        isinstance(val, list),
        f"{name} must be a list of exact ints, got {type(val).__name__}",
    )
    require(len(val) >= min_len, f"{name} requires >= {min_len} cuts, got {len(val)}")
    cuts = [require_exact_int(x, name=f"{name}[{idx}]") for idx, x in enumerate(val)]
    for idx in range(len(cuts) - 1):
        require(
            cuts[idx] < cuts[idx + 1],
            f"{name} must be strictly increasing at index {idx}: {cuts[idx]} >= {cuts[idx + 1]}",
        )
    return cuts


def _parse_int_window(val: object, *, name: str) -> tuple[int, int]:
    """Validate a 2-element exact integer window [lo, hi] with lo < hi."""
    require_type(
        isinstance(val, list),
        f"{name} must be a 2-element list of exact ints, got {type(val).__name__}",
    )
    require(len(val) == 2, f"{name} must have length 2, got {len(val)}")
    lo = require_exact_int(val[0], name=f"{name}[0]")
    hi = require_exact_int(val[1], name=f"{name}[1]")
    require(lo < hi, f"{name} must satisfy lo < hi, got [{lo}, {hi}]")
    return (lo, hi)


def _count_post_anchor_in_half_open_window(
    cuts: list[int],
    window_start: int,
    window_end: int,
    *,
    name: str,
) -> TritWord:
    """Filter strictly increasing cuts to half-open (u, v], enforce >=2 in-window, and exclude anchor cuts[0]."""
    require(
        window_start < window_end,
        f"window must satisfy window_start < window_end, got [{window_start}, {window_end}]",
    )
    in_window_all = [k for k in cuts if window_start < k <= window_end]
    require(
        len(in_window_all) >= 2,
        f"{name} requires >= 2 closures in half-open window ({window_start}, {window_end}], "
        f"got {len(in_window_all)}",
    )
    tw_count = TritWord.ZERO
    for k in cuts[1:]:
        if window_start < k <= window_end:
            tw_count = tw_count.add(TritWord.ONE)
    require(
        tw_count.sign() > 0,
        f"{name} requires >= 1 post-anchor closure in ({window_start}, {window_end}]",
    )
    return tw_count


def _parse_nonneg_int_list(val: object, *, name: str) -> list[int]:
    """Validate a list of nonnegative exact integers."""
    require_type(
        isinstance(val, list),
        f"{name} must be a list of exact ints, got {type(val).__name__}",
    )
    out: list[int] = []
    for idx, item in enumerate(val):
        n = require_exact_int(item, name=f"{name}[{idx}]")
        require(n >= 0, f"{name}[{idx}] must be nonnegative, got {n}")
        out.append(n)
    return out


def _step_cut40_causal_intervention(
    *,
    causal_window: tuple[int, int],
    outer_plus_cuts: list[int],
    outer_minus_cuts: list[int],
    intervention_cut: int,
    apply_intervention: bool,
    disconnect_feedback: bool = False,
) -> CausalCapacityTrace:
    """Step cut-by-cut causal capacity-drop dynamics over integer cuts k = c_lo .. c_hi."""
    c_lo, c_hi = causal_window
    require(c_lo < c_hi, f"causal_window must satisfy lo < hi, got [{c_lo}, {c_hi}]")
    require(
        c_hi - c_lo <= _RC037_MAX_CAUSAL_SPAN,
        f"causal_window span exceeds limit {_RC037_MAX_CAUSAL_SPAN}: {c_hi - c_lo}",
    )
    require(
        c_lo < intervention_cut < c_hi,
        f"intervention_cut must satisfy {c_lo} < intervention_cut < {c_hi}, got {intervention_cut}",
    )
    require_type(
        isinstance(apply_intervention, bool),
        f"apply_intervention must be bool, got {type(apply_intervention).__name__}",
    )
    require_type(
        isinstance(disconnect_feedback, bool),
        f"disconnect_feedback must be bool, got {type(disconnect_feedback).__name__}",
    )
    require(
        any(c_lo < k <= c_hi for k in outer_minus_cuts),
        f"causal_outer_minus requires >= 1 cut in ({c_lo}, {c_hi}]",
    )

    outer_plus_set = frozenset(outer_plus_cuts)
    outer_minus_set = frozenset(outer_minus_cuts)
    capacity_threshold = 2
    effective_capacity = 2
    outer_plus_retained = True
    retention_status = "retained"
    queued_capacity_drop = False
    tw_plus = TritWord.ZERO
    tw_minus = TritWord.ZERO
    records: list[CutRecord] = []

    for k in range(c_lo, c_hi + 1):
        if queued_capacity_drop:
            effective_capacity = 1
            queued_capacity_drop = False
            if effective_capacity < capacity_threshold:
                if disconnect_feedback:
                    outer_plus_retained = True
                    retention_status = "retained_feedback_disconnected_mutation"
                else:
                    outer_plus_retained = False
                    retention_status = "lost_by_declared_capacity_rule"

        if k > c_lo:
            if k in outer_plus_set and outer_plus_retained:
                tw_plus = tw_plus.add(TritWord.ONE)
            if k in outer_minus_set:
                tw_minus = tw_minus.add(TritWord.ONE)

        intervention_queued_here = apply_intervention and k == intervention_cut
        if intervention_queued_here:
            queued_capacity_drop = True

        records.append(
            CutRecord(
                cut=k,
                effective_capacity=effective_capacity,
                outer_plus_retained=outer_plus_retained,
                retention_status=retention_status,
                count_plus=tw_plus.to_int(),
                count_minus=tw_minus.to_int(),
                intervention_queued=intervention_queued_here,
            )
        )

    require(tw_minus.sign() > 0, "causal simulation produced zero reference outer_minus count")
    ratio = TritRatio(tw_plus, tw_minus)
    return CausalCapacityTrace(
        window=(c_lo, c_hi),
        intervention_cut=intervention_cut,
        apply_intervention=apply_intervention,
        disconnect_feedback=disconnect_feedback,
        records=tuple(records),
        counts=(tw_plus.to_int(), tw_minus.to_int()),
        ratio=ratio,
    )


def _validate_causal_capacity_trace(
    trace: CausalCapacityTrace,
    *,
    causal_window: tuple[int, int],
    outer_plus_cuts: list[int],
    outer_minus_cuts: list[int],
    intervention_cut: int,
    apply_intervention: bool,
) -> None:
    """Replay-validate a causal capacity trace against honest (connected-feedback) stepping."""
    capacity_threshold = 2
    for rec in trace.records:
        if rec.effective_capacity < capacity_threshold:
            require(
                (not rec.outer_plus_retained)
                and rec.retention_status == "lost_by_declared_capacity_rule",
                f"capacity-loss invariant violated at cut {rec.cut}: "
                f"effective_capacity={rec.effective_capacity}, "
                f"outer_plus_retained={rec.outer_plus_retained}, "
                f"retention_status={rec.retention_status!r}",
            )
    honest = _step_cut40_causal_intervention(
        causal_window=causal_window,
        outer_plus_cuts=outer_plus_cuts,
        outer_minus_cuts=outer_minus_cuts,
        intervention_cut=intervention_cut,
        apply_intervention=apply_intervention,
        disconnect_feedback=False,
    )
    require(
        trace.records == honest.records
        and trace.counts == honest.counts
        and trace.ratio == honest.ratio,
        "causal capacity trace failed exact replay validation against honest dynamics",
    )


def _observable_cut_tuple(rec: CutRecord) -> tuple[int, bool, str, int, int]:
    return (
        rec.effective_capacity,
        rec.outer_plus_retained,
        rec.retention_status,
        rec.count_plus,
        rec.count_minus,
    )


def _parse_observed_advance_entry(
    raw: object,
    *,
    name: str,
) -> tuple[TritWord, TritRatio, TritRatio, TritRatio]:
    """Parse one observed-advance entry {winding, phase_start, phase_end} strictly in TritWord/TritRatio."""
    require_type(
        isinstance(raw, dict),
        f"{name} must be a dict, got {type(raw).__name__}",
    )
    keys = set(raw.keys())
    require(
        keys == _OBSERVED_ENTRY_KEYS,
        f"{name} must have exact keys {sorted(_OBSERVED_ENTRY_KEYS)}, got {sorted(keys)}",
    )
    winding_i = require_exact_int(raw["winding"], name=f"{name}.winding")
    require(winding_i >= 0, f"{name}.winding must be >= 0, got {winding_i}")
    tw_winding = TritWord.from_int(winding_i)
    phi_start = _parse_trit_pair(raw["phase_start"], name=f"{name}.phase_start")
    phi_end = _parse_trit_pair(raw["phase_end"], name=f"{name}.phase_end")
    require(
        phi_start.sign() >= 0 and phi_start < TritRatio.ONE,
        f"{name}.phase_start must lie in [0, 1), got {phi_start}",
    )
    require(
        phi_end.sign() >= 0 and phi_end < TritRatio.ONE,
        f"{name}.phase_end must lie in [0, 1), got {phi_end}",
    )
    advance = TritRatio(tw_winding, TritWord.ONE).add(phi_end).sub(phi_start)
    return (tw_winding, phi_start, phi_end, advance)


def _eval_observed_advance_block(raw_opt: object = _MISSING_OPT) -> dict[str, TritRatio]:
    """Evaluate observed-advance endpoint law A(W) = C(W) + phi_1 - phi_0 strictly in TritRatio."""
    defaults: dict[str, dict[str, object]] = {
        "compared": {"winding": 4, "phase_start": ["2", "3"], "phase_end": ["1", "6"]},
        "reference": {"winding": 8, "phase_start": ["1", "4"], "phase_end": ["3", "4"]},
        "split_left": {"winding": 2, "phase_start": ["2", "3"], "phase_end": ["5", "6"]},
        "split_right": {"winding": 2, "phase_start": ["5", "6"], "phase_end": ["1", "6"]},
        "signed_control": {"winding": 0, "phase_start": ["3", "4"], "phase_end": ["1", "4"]},
    }
    overrides: dict[str, object] = {}
    if raw_opt is not _MISSING_OPT:
        require_type(
            isinstance(raw_opt, dict),
            f"observed_advance must be a dict, got {type(raw_opt).__name__}",
        )
        unknown = set(raw_opt.keys()) - _OBSERVED_ADVANCE_KEYS
        require(
            not unknown,
            f"unexpected keys in observed_advance: {sorted(unknown)}",
        )
        overrides = dict(raw_opt)

    parsed: dict[str, tuple[TritWord, TritRatio, TritRatio, TritRatio]] = {}
    for key in ("compared", "reference", "split_left", "split_right", "signed_control"):
        entry_raw = overrides[key] if key in overrides else defaults[key]
        parsed[key] = _parse_observed_advance_entry(entry_raw, name=f"observed_advance.{key}")

    w_c, phi0_c, phi1_c, adv_c = parsed["compared"]
    _w_r, _phi0_r, _phi1_r, adv_r = parsed["reference"]
    w_l, phi0_l, phi1_l, adv_l = parsed["split_left"]
    w_sr, phi0_sr, phi1_sr, adv_sr = parsed["split_right"]
    _w_s, _phi0_s, _phi1_s, adv_signed = parsed["signed_control"]

    require(adv_r.sign() > 0, f"observed_advance.reference advance must be > 0, got {adv_r}")
    require(
        phi0_l == phi0_c,
        f"split_left.phase_start {phi0_l} must equal compared.phase_start {phi0_c}",
    )
    require(
        phi1_l == phi0_sr,
        f"split_left.phase_end {phi1_l} must equal split_right.phase_start {phi0_sr}",
    )
    require(
        phi1_sr == phi1_c,
        f"split_right.phase_end {phi1_sr} must equal compared.phase_end {phi1_c}",
    )
    require(
        w_l.add(w_sr) == w_c,
        "split_left.winding + split_right.winding must equal compared.winding",
    )

    split_sum = adv_l.add(adv_sr)
    require(
        split_sum == adv_c,
        f"observed advance additivity violated: {adv_l} + {adv_sr} = {split_sum} != {adv_c}",
    )
    adv_ratio = adv_c.div(adv_r)
    adv_clipped = adv_signed if adv_signed.sign() > 0 else TritRatio.ZERO
    return {
        "compared": adv_c,
        "reference": adv_r,
        "ratio": adv_ratio,
        "split_sum": split_sum,
        "clipped": adv_clipped,
        "signed": adv_signed,
    }


def eval_dec_temporal_si_bridge_bounds(inputs: dict[str, object]) -> dict[str, object]:
    """Step coupled closure-beat RCD, causal cut intervention, observed-advance, and SI bridge (RC-037)."""
    require_type(
        isinstance(inputs, dict),
        f"inputs must be a dict, got {type(inputs).__name__}",
    )
    for req_key in ("compared_cuts", "ref_cuts", "f_cs_hz", "cal_ref", "field_a", "field_b"):
        require(req_key in inputs, f"missing required input field {req_key!r}")

    c_cuts = _parse_strict_int_cuts(inputs["compared_cuts"], name="compared_cuts", min_len=2)
    r_cuts = _parse_strict_int_cuts(inputs["ref_cuts"], name="ref_cuts", min_len=2)
    f_cs_i = require_exact_int(inputs["f_cs_hz"], name="f_cs_hz")
    cal_ref_i = require_exact_int(inputs["cal_ref"], name="cal_ref")

    fa_raw = inputs["field_a"]
    fb_raw = inputs["field_b"]
    require_type(
        isinstance(fa_raw, list),
        f"field_a must be a 2-element list, got {type(fa_raw).__name__}",
    )
    require_type(
        isinstance(fb_raw, list),
        f"field_b must be a 2-element list, got {type(fb_raw).__name__}",
    )
    require(len(fa_raw) == 2, f"field_a must have length 2, got {len(fa_raw)}")
    require(len(fb_raw) == 2, f"field_b must have length 2, got {len(fb_raw)}")
    na_cal_i = require_exact_int(fa_raw[0], name="na_cal")
    na_val_i = require_exact_int(fa_raw[1], name="na_val")
    nb_cal_i = require_exact_int(fb_raw[0], name="nb_cal")
    nb_val_i = require_exact_int(fb_raw[1], name="nb_val")
    require(
        f_cs_i > 0 and cal_ref_i > 0 and na_cal_i > 0 and nb_cal_i > 0,
        "f_cs_hz, cal_ref, na_cal, and nb_cal must be positive",
    )
    require(na_val_i >= 0 and nb_val_i >= 0, "na_val and nb_val must be nonnegative")

    # Optional window, biases, directional RCD, and stipulated SI gains
    win_lo, win_hi = (
        _parse_int_window(inputs["window"], name="window")
        if "window" in inputs
        else (0, 30)
    )
    compared_bias = (
        _parse_trit_pair(inputs["compared_bias"], name="compared_bias")
        if "compared_bias" in inputs
        else TritRatio(TritWord.ONE, TritWord.from_int(4))
    )
    ref_bias = (
        _parse_trit_pair(inputs["ref_bias"], name="ref_bias")
        if "ref_bias" in inputs
        else TritRatio(TritWord.NEG_ONE, TritWord.from_int(4))
    )

    rcd_rd_i = require_exact_int(inputs["rcd_rd"], name="rcd_rd") if "rcd_rd" in inputs else 3
    require(rcd_rd_i >= 1, f"rcd_rd must be >= 1, got {rcd_rd_i}")
    rcd_c_refs = (
        _parse_nonneg_int_list(inputs["rcd_c_reflections"], name="rcd_c_reflections")
        if "rcd_c_reflections" in inputs
        else [1, 1]
    )
    rcd_r_refs = (
        _parse_nonneg_int_list(inputs["rcd_r_reflections"], name="rcd_r_reflections")
        if "rcd_r_reflections" in inputs
        else [2, 2]
    )

    a_c = _parse_trit_pair(inputs["a_c"], name="a_c") if "a_c" in inputs else TritRatio.ONE
    a_r = _parse_trit_pair(inputs["a_r"], name="a_r") if "a_r" in inputs else TritRatio.ONE
    require(a_c.sign() > 0 and a_r.sign() > 0, "stipulated SI gains a_c and a_r must be positive")

    # 1. Half-open (u, v] filtering & anchor exclusion
    tw_nc = _count_post_anchor_in_half_open_window(c_cuts, win_lo, win_hi, name="compared_cuts")
    tw_nr = _count_post_anchor_in_half_open_window(r_cuts, win_lo, win_hi, name="ref_cuts")
    tr_nc = TritRatio(tw_nc, TritWord.ONE)
    tr_nr = TritRatio(tw_nr, TritWord.ONE)

    # 2. Cadence ratios, biases, directional RCD, stipulated SI gains & cross-field transfer
    biz_cr = TritRatio(tw_nc, tw_nr)
    biz_rc = TritRatio(tw_nr, tw_nc)
    require(biz_cr.mul(biz_rc) == TritRatio.ONE, "cadence reciprocity biz_c|r * biz_r|c == 1 failed")

    lag_fwd = TritRatio(tw_nc.sub(tw_nr), TritWord.ONE).add(compared_bias.sub(ref_bias))
    lag_rev = lag_fwd.neg()

    tw_rcd_cr = TritWord.from_int(rcd_rd_i)
    for x in rcd_c_refs:
        tw_rcd_cr = tw_rcd_cr.add(TritWord.from_int(x))
    tw_rcd_rc = TritWord.from_int(rcd_rd_i)
    for x in rcd_r_refs:
        tw_rcd_rc = tw_rcd_rc.add(TritWord.from_int(x))

    tr_fcs = TritRatio(TritWord.from_int(f_cs_i), TritWord.ONE)
    t_sec = tr_nr.mul(a_r).div(tr_fcs)
    nu_bar = tr_nc.mul(a_c).div(t_sec)

    tr_cal = TritRatio(TritWord.from_int(cal_ref_i), TritWord.ONE)
    tr_na_cal = TritRatio(TritWord.from_int(na_cal_i), TritWord.ONE)
    tr_na_val = TritRatio(TritWord.from_int(na_val_i), TritWord.ONE)
    pred_a = tr_cal.div(tr_na_cal).mul(tr_na_val)
    rel_a = pred_a.sub(tr_cal).div(tr_cal)

    tr_nb_cal = TritRatio(TritWord.from_int(nb_cal_i), TritWord.ONE)
    tr_nb_val = TritRatio(TritWord.from_int(nb_val_i), TritWord.ONE)
    pred_b = tr_cal.div(tr_nb_cal).mul(tr_nb_val)
    rel_b = pred_b.sub(tr_cal).div(tr_cal)

    # 3. Cut-by-cut causal capacity-drop simulation & hostile disconnect rejection
    causal_win = (
        _parse_int_window(inputs["causal_window"], name="causal_window")
        if "causal_window" in inputs
        else (0, 100)
    )
    outer_plus = (
        _parse_strict_int_cuts(inputs["causal_outer_plus"], name="causal_outer_plus", min_len=1)
        if "causal_outer_plus" in inputs
        else [16, 32, 48, 64, 80, 96]
    )
    outer_minus = (
        _parse_strict_int_cuts(inputs["causal_outer_minus"], name="causal_outer_minus", min_len=1)
        if "causal_outer_minus" in inputs
        else [15, 30, 45, 60, 75]
    )
    cut_i = (
        require_exact_int(inputs["intervention_cut"], name="intervention_cut")
        if "intervention_cut" in inputs
        else 40
    )

    baseline = _step_cut40_causal_intervention(
        causal_window=causal_win,
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=cut_i,
        apply_intervention=False,
        disconnect_feedback=False,
    )
    intervention = _step_cut40_causal_intervention(
        causal_window=causal_win,
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=cut_i,
        apply_intervention=True,
        disconnect_feedback=False,
    )
    disconnected = _step_cut40_causal_intervention(
        causal_window=causal_win,
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=cut_i,
        apply_intervention=True,
        disconnect_feedback=True,
    )

    _validate_causal_capacity_trace(
        baseline,
        causal_window=causal_win,
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=cut_i,
        apply_intervention=False,
    )
    _validate_causal_capacity_trace(
        intervention,
        causal_window=causal_win,
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=cut_i,
        apply_intervention=True,
    )

    disconnect_rejected = False
    try:
        _validate_causal_capacity_trace(
            disconnected,
            causal_window=causal_win,
            outer_plus_cuts=outer_plus,
            outer_minus_cuts=outer_minus,
            intervention_cut=cut_i,
            apply_intervention=True,
        )
    except ValueError:
        disconnect_rejected = True
    require(
        disconnect_rejected,
        "hostile disconnect_feedback trace must be rejected by replay validation",
    )
    require(
        disconnected.counts == baseline.counts and disconnected.ratio == baseline.ratio,
        "hostile disconnect_feedback trace must collapse back to baseline counts and ratio",
    )

    common_prefix_through: int | None = None
    for rec_b, rec_i, rec_d in zip(baseline.records, intervention.records, disconnected.records):
        if rec_b == rec_i == rec_d:
            common_prefix_through = rec_b.cut
        else:
            break
    require(
        common_prefix_through is not None and common_prefix_through == cut_i - 1,
        f"common_prefix_through mismatch: got {common_prefix_through}, expected {cut_i - 1}",
    )

    first_divergent_cut: int | None = None
    for rec_b, rec_i in zip(baseline.records, intervention.records):
        obs_b = _observable_cut_tuple(rec_b)
        obs_i = _observable_cut_tuple(rec_i)
        if rec_b.cut <= cut_i:
            require(
                obs_b == obs_i,
                f"causal pre-intervention observable diverged at cut {rec_b.cut} <= {cut_i}",
            )
        elif obs_b != obs_i and first_divergent_cut is None:
            first_divergent_cut = rec_b.cut
    require(
        first_divergent_cut is not None and first_divergent_cut > cut_i,
        "causal intervention must yield a strictly later observable divergence",
    )

    # 4. Observed-advance endpoint law A(W) = C(W) + phi_1 - phi_0
    obs_adv = (
        _eval_observed_advance_block(inputs["observed_advance"])
        if "observed_advance" in inputs
        else _eval_observed_advance_block()
    )

    out: dict[str, object] = {
        "delta_bip_compared": tw_nc.to_int(),
        "delta_bip_ref": tw_nr.to_int(),
        "biz_c_over_r": _trit_pair(biz_cr),
        "biz_r_over_c": _trit_pair(biz_rc),
        "lag_forward": _trit_pair(lag_fwd),
        "lag_reverse": _trit_pair(lag_rev),
        "T_seconds": _trit_pair(t_sec),
        "nu_bar_hz": _trit_pair(nu_bar),
        "transfer_A_pred": _trit_pair(pred_a),
        "transfer_A_rel_resid": _trit_pair(rel_a),
        "transfer_B_pred": _trit_pair(pred_b),
        "transfer_B_rel_resid": _trit_pair(rel_b),
        "intervention_ratio_before": _trit_pair(baseline.ratio),
        "intervention_ratio_after": _trit_pair(intervention.ratio),
        "window": [win_lo, win_hi],
        "rcd_c_given_r": tw_rcd_cr.to_int(),
        "rcd_r_given_c": tw_rcd_rc.to_int(),
        "intervention_common_prefix_through": common_prefix_through,
        "intervention_first_divergent_cut": first_divergent_cut,
        "intervention_counts_before": [baseline.counts[0], baseline.counts[1]],
        "intervention_counts_after": [intervention.counts[0], intervention.counts[1]],
        "intervention_disconnect_rejected": disconnect_rejected,
        "observed_advance_compared": _trit_pair(obs_adv["compared"]),
        "observed_advance_ref": _trit_pair(obs_adv["reference"]),
        "observed_advance_ratio": _trit_pair(obs_adv["ratio"]),
        "observed_advance_split_sum": _trit_pair(obs_adv["split_sum"]),
        "observed_advance_clipped": _trit_pair(obs_adv["clipped"]),
        "observed_advance_signed": _trit_pair(obs_adv["signed"]),
    }
    require_no_floats(out)
    return out


def build_temporal_si_bridge_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 9-row live D.E.C. temporal & conditional SI bridge CSV for Manual §7."""
    c_cuts = [2, 10, 18, 26]
    r_cuts = [2, 12, 22]
    f_cs_hz = 9192631770
    cal_ref = 32
    field_a = [58, 48]
    field_b = [151, 102]
    win = [0, 30]
    c_bias_in = ["1", "4"]
    r_bias_in = ["-1", "4"]
    rcd_rd = 3
    c_refs = [1, 1]
    r_refs = [2, 2]
    a_c_in = ["1", "1"]
    a_r_in = ["1", "1"]
    causal_win = [0, 100]
    outer_plus = [16, 32, 48, 64, 80, 96]
    outer_minus = [15, 30, 45, 60, 75]
    cut_i = 40

    cfg: dict[str, object] = {
        "compared_cuts": c_cuts,
        "ref_cuts": r_cuts,
        "f_cs_hz": f_cs_hz,
        "cal_ref": cal_ref,
        "field_a": field_a,
        "field_b": field_b,
        "window": win,
        "compared_bias": c_bias_in,
        "ref_bias": r_bias_in,
        "rcd_rd": rcd_rd,
        "rcd_c_reflections": c_refs,
        "rcd_r_reflections": r_refs,
        "a_c": a_c_in,
        "a_r": a_r_in,
        "causal_window": causal_win,
        "causal_outer_plus": outer_plus,
        "causal_outer_minus": outer_minus,
        "intervention_cut": cut_i,
    }
    res = eval_dec_temporal_si_bridge_bounds(cfg)

    win_out = res["window"]
    require(isinstance(win_out, list) and len(win_out) == 2, "window output must be 2-element list")
    win_tag = f"B_pair({win_out[0]},{win_out[1]}]"

    n_c = require_exact_int(res["delta_bip_compared"], name="delta_bip_compared")
    n_r = require_exact_int(res["delta_bip_ref"], name="delta_bip_ref")
    c_bias_tr = _parse_trit_pair(c_bias_in, name="compared_bias")
    r_bias_tr = _parse_trit_pair(r_bias_in, name="ref_bias")
    c_bias_signed = f"+{c_bias_tr.canonical_str()}" if c_bias_tr.sign() > 0 else c_bias_tr.canonical_str()
    r_bias_signed = f"+{r_bias_tr.canonical_str()}" if r_bias_tr.sign() > 0 else r_bias_tr.canonical_str()
    count_delta = TritWord.from_int(n_c).sub(TritWord.from_int(n_r))
    bias_diff = c_bias_tr.sub(r_bias_tr)
    bias_diff_s = f"+{bias_diff.canonical_str()}" if bias_diff.sign() >= 0 else bias_diff.canonical_str()

    a_c_s = _parse_trit_pair(a_c_in, name="a_c").canonical_str()
    a_r_s = _parse_trit_pair(a_r_in, name="a_r").canonical_str()
    bridge_tag = f"B_bridge(a_c=a_r={a_c_s})" if a_c_s == a_r_s else f"B_bridge(a_c={a_c_s},a_r={a_r_s})"

    cnt_before = res["intervention_counts_before"]
    cnt_after = res["intervention_counts_after"]
    require(
        isinstance(cnt_before, list) and len(cnt_before) == 2
        and isinstance(cnt_after, list) and len(cnt_after) == 2,
        "intervention counts must be 2-element lists",
    )
    first_div = require_exact_int(
        res["intervention_first_divergent_cut"], name="intervention_first_divergent_cut"
    )
    prefix_k = require_exact_int(
        res["intervention_common_prefix_through"], name="intervention_common_prefix_through"
    )
    disc_rej = res["intervention_disconnect_rejected"]
    require(disc_rej is True, "hostile causal disconnect must be rejected by replay validation")

    disc_trace = _step_cut40_causal_intervention(
        causal_window=(causal_win[0], causal_win[1]),
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=cut_i,
        apply_intervention=True,
        disconnect_feedback=True,
    )

    rcd_cr = require_exact_int(res["rcd_c_given_r"], name="rcd_c_given_r")
    rcd_rc = require_exact_int(res["rcd_r_given_c"], name="rcd_r_given_c")

    oa_c_s = _fmt_trit_pair(res["observed_advance_compared"], name="observed_advance_compared")
    oa_r_s = _fmt_trit_pair(res["observed_advance_ref"], name="observed_advance_ref")
    oa_rat_s = _fmt_trit_pair(res["observed_advance_ratio"], name="observed_advance_ratio")
    oa_split_s = _fmt_trit_pair(res["observed_advance_split_sum"], name="observed_advance_split_sum")
    oa_clip_s = _fmt_trit_pair(res["observed_advance_clipped"], name="observed_advance_clipped")
    oa_sign_s = _fmt_trit_pair(res["observed_advance_signed"], name="observed_advance_signed")

    c_cuts_csv = ",".join(str(k) for k in c_cuts)
    r_cuts_csv = ",".join(str(k) for k in r_cuts)
    c_refs_csv = ",".join(str(x) for x in c_refs)
    r_refs_csv = ",".join(str(x) for x in r_refs)

    return [
        {
            "stage_id": "T1_pair_closures",
            "boundary_B": win_tag,
            "lineage_pair": f"compared({c_cuts_csv}) vs ref({r_cuts_csv})",
            "delta_bip": f"{n_c} vs {n_r}",
            "exact_quantity": _fmt_trit_pair(res["biz_c_over_r"], name="biz_c_over_r"),
            "reverse_or_resid": _fmt_trit_pair(res["biz_r_over_c"], name="biz_r_over_c"),
            "status_gate": "AUTHENTICATED_EXACT_RCD",
        },
        {
            "stage_id": "T2_unwrapped_lag",
            "boundary_B": win_tag,
            "lineage_pair": f"bias({c_bias_signed},{r_bias_signed})",
            "delta_bip": f"{count_delta.to_int()}{bias_diff_s}",
            "exact_quantity": _fmt_trit_pair(res["lag_forward"], name="lag_forward"),
            "reverse_or_resid": _fmt_trit_pair(res["lag_reverse"], name="lag_reverse"),
            "status_gate": "AUTHENTICATED_EXACT_LAG",
        },
        {
            "stage_id": "T3_cs133_bridge",
            "boundary_B": bridge_tag,
            "lineage_pair": f"Cs_{f_cs_hz}Hz",
            "delta_bip": f"N_r={n_r},N_c={n_c}",
            "exact_quantity": _fmt_trit_pair(res["T_seconds"], name="T_seconds"),
            "reverse_or_resid": _fmt_trit_pair(res["nu_bar_hz"], name="nu_bar_hz"),
            "status_gate": "CONDITIONAL_SI_STIPULATED_GAIN",
        },
        {
            "stage_id": "T4_transfer_field_A",
            "boundary_B": f"B_val_A({cal_ref}_ref)",
            "lineage_pair": "3:3:6_vs_1:2:6",
            "delta_bip": f"cal={field_a[0]},val={field_a[1]}",
            "exact_quantity": _fmt_trit_pair(res["transfer_A_pred"], name="transfer_A_pred"),
            "reverse_or_resid": _fmt_trit_pair(res["transfer_A_rel_resid"], name="transfer_A_rel_resid"),
            "status_gate": "REJECTS_CONSTANT_TRANSFER",
        },
        {
            "stage_id": "T5_transfer_field_B",
            "boundary_B": f"B_val_B({cal_ref}_ref)",
            "lineage_pair": "3:2:6_vs_3:3:6",
            "delta_bip": f"cal={field_b[0]},val={field_b[1]}",
            "exact_quantity": _fmt_trit_pair(res["transfer_B_pred"], name="transfer_B_pred"),
            "reverse_or_resid": _fmt_trit_pair(res["transfer_B_rel_resid"], name="transfer_B_rel_resid"),
            "status_gate": "REJECTS_CONSTANT_TRANSFER",
        },
        {
            "stage_id": "T6_cut40_intervention",
            "boundary_B": f"B_causal(cut{cut_i}->{first_div})",
            "lineage_pair": "capacity_drop_control",
            "delta_bip": f"({cnt_before[0]},{cnt_before[1]})->({cnt_after[0]},{cnt_after[1]})",
            "exact_quantity": _fmt_trit_pair(res["intervention_ratio_before"], name="intervention_ratio_before"),
            "reverse_or_resid": _fmt_trit_pair(res["intervention_ratio_after"], name="intervention_ratio_after"),
            "status_gate": f"STRICTLY_LATER_CUT{first_div}_RESPONSE",
        },
        {
            "stage_id": "T7_directional_rcd",
            "boundary_B": f"B_rcd(RD={rcd_rd})",
            "lineage_pair": f"c_refs({c_refs_csv}) vs r_refs({r_refs_csv})",
            "delta_bip": f"RCD_c|r={rcd_cr},RCD_r|c={rcd_rc}",
            "exact_quantity": str(rcd_cr),
            "reverse_or_resid": str(rcd_rc),
            "status_gate": "AUTHENTICATED_DIRECTIONAL_RCD",
        },
        {
            "stage_id": "T8_observed_advance_si",
            "boundary_B": "B_phase(A=C+phi1-phi0)",
            "lineage_pair": f"A_c={oa_c_s} vs A_r={oa_r_s}",
            "delta_bip": f"split={oa_split_s};clip={oa_clip_s}",
            "exact_quantity": oa_rat_s,
            "reverse_or_resid": oa_sign_s,
            "status_gate": "EXACT_OBSERVED_ADVANCE_ADDITIVE",
        },
        {
            "stage_id": "T9_causal_disconnect_control",
            "boundary_B": f"B_causal_hostile(prefix<={prefix_k})",
            "lineage_pair": "disconnect_feedback_mutation",
            "delta_bip": f"({cnt_before[0]},{cnt_before[1]})->({disc_trace.counts[0]},{disc_trace.counts[1]})",
            "exact_quantity": disc_trace.ratio.canonical_str(),
            "reverse_or_resid": "REJECTED_REPLAY_VALIDATION",
            "status_gate": "HOSTILE_DISCONNECT_REJECTED",
        },
    ]


# =============================================================================
# RC-038: Manual §8 — Q4 Short-Window RCD Clipping & Pending Overhang
# =============================================================================


def eval_dec_short_window_rcd_clipping(inputs: dict[str, object]) -> dict[str, object]:
    """Step short-window clipping rho_omega + overhang Q^D across motif supports (RC-038)."""
    wins_raw = inputs.get("windows")
    require(isinstance(wins_raw, list) and len(wins_raw) >= 1, "windows must be non-empty list")
    windows = [require_exact_int(x, name="window") for x in wins_raw]
    c3 = require_exact_int(inputs.get("c3"), name="c3")
    c_close = require_exact_int(inputs.get("c_close"), name="c_close")
    require(c3 > 0 and c_close > 0, "c3 and c_close must be positive")

    supports = (("1:2", 9), ("3:3", 61), ("3:4", 137))
    records: list[dict[str, object]] = []
    for fam, rd in supports:
        for w in windows:
            require(w >= 1, "window length must be >= 1")
            rho_w = rd if rd < w else w
            p_d = c3 * rho_w
            over = rd - w if rd > w else 0
            q_d = c3 * over
            require(p_d + q_d == c3 * rd, "short-window pressure + overhang conservation violated")
            x_shed = p_d - c_close if p_d > c_close else 0
            records.append(
                {
                    "support": fam,
                    "RD": rd,
                    "window": w,
                    "rho_omega": rho_w,
                    "p_D": p_d,
                    "Q_D": q_d,
                    "X_shed_vs_Cclose": x_shed,
                }
            )

    out: dict[str, object] = {
        "c3": c3,
        "c_close": c_close,
        "total_pairs": len(records),
        "all_conserved": 1,
        "records": records,
    }
    require_no_floats(out)
    return out


def build_short_window_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 8-row short-window D.E.C. clipping & overhang CSV for Manual §8."""
    cases = [
        ("1:2", 9, 2, 18),
        ("1:2", 9, 4, 18),
        ("1:2", 9, 6, 18),
        ("1:2", 9, 9, 24),
        ("3:3", 61, 4, 18),
        ("3:3", 61, 6, 18),
        ("3:4", 137, 4, 18),
        ("3:4", 137, 6, 18),
    ]
    rows: list[dict[str, str]] = []
    for fam, rd, w, c_cl in cases:
        rho_w = rd if rd < w else w
        p_d = 3 * rho_w
        q_d = 3 * (rd - w if rd > w else 0)
        x_sh = p_d - c_cl if p_d > c_cl else 0
        rows.append(
            {
                "support": fam,
                "RD": str(rd),
                "window_len": str(w),
                "rho_omega": str(rho_w),
                "p_D": str(p_d),
                "Q_D": str(q_d),
                "C_close": str(c_cl),
                "X_shedding": str(x_sh),
                "total_3RD": str(3 * rd),
            }
        )
    return rows


# =============================================================================
# RC-039: Manual §10 — Concentric Hydrogen Shell Wavelet Transitions
# =============================================================================


def eval_dec_hydrogen_shell_wavelet_step(inputs: dict[str, object]) -> dict[str, object]:
    """Step concentric shell transitions S_n -> S_m emitting outward wavelet packets (RC-039)."""
    tr_raw = inputs.get("transitions")
    require(isinstance(tr_raw, list) and len(tr_raw) >= 1, "transitions must be non-empty list")

    rows_out: list[dict[str, object]] = []
    for item in tr_raw:
        require(isinstance(item, list) and len(item) == 2, "transition must be [n, m]")
        n = require_exact_int(item[0], name="n")
        m = require_exact_int(item[1], name="m")
        require(n > m and m >= 1, f"require n > m >= 1, got {n}->{m}")
        dp = Fraction(1, m * m) - Fraction(1, n * n)
        m_base = m + 1
        dp_base = Fraction(1, m * m) - Fraction(1, m_base * m_base)
        r_series = dp / dp_base
        lam_ratio = Fraction(1, 1) / r_series
        series_name = "Lyman" if m == 1 else ("Balmer" if m == 2 else ("Paschen" if m == 3 else f"m{m}"))
        rows_out.append(
            {
                "n": n,
                "m": m,
                "series": series_name,
                "r_n_over_r1": n * n,
                "r_m_over_r1": m * m,
                "delta_P_hat": _pair(dp),
                "R_to_series_base": _pair(r_series),
                "wavelength_over_base": _pair(lam_ratio),
            }
        )

    out: dict[str, object] = {
        "transition_count": len(rows_out),
        "transitions": rows_out,
    }
    require_no_floats(out)
    return out


def build_hydrogen_transitions_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 9-row concentric shell wavelet D.E.C. CSV for Manual §10."""
    res = eval_dec_hydrogen_shell_wavelet_step(
        {"transitions": [[3, 2], [4, 2], [5, 2], [6, 2], [2, 1], [3, 1], [4, 1], [4, 3], [5, 3]]}
    )
    tr_list = res["transitions"]
    require(isinstance(tr_list, list), "transitions must be list")
    rows: list[dict[str, str]] = []
    for item in tr_list:
        require(isinstance(item, dict), "item must be dict")
        dp = _parse_pair(item["delta_P_hat"], name="delta_P_hat")
        rs = _parse_pair(item["R_to_series_base"], name="R_to_series_base")
        lr = _parse_pair(item["wavelength_over_base"], name="wavelength_over_base")
        rows.append(
            {
                "series": str(item["series"]),
                "transition": f"{item['n']}->{item['m']}",
                "n": str(item["n"]),
                "m": str(item["m"]),
                "r_n_over_r1": str(item["r_n_over_r1"]),
                "delta_P_hat": canonical_rational_str(dp),
                "R_series_exact": canonical_rational_str(rs),
                "R_series_dec6": format_rational_fixed(rs, 6),
                "lambda_over_base_exact": canonical_rational_str(lr),
            }
        )
    return rows


# =============================================================================
# RC-040: Manual §12 — Solar O0 Boundary Audit & Native Producer HOLD Gate
# =============================================================================


def eval_dec_solar_o0_boundary_audit(inputs: dict[str, object]) -> dict[str, object]:
    """Evaluate exact rational O0 solar residuals while enforcing producer HOLD gate (RC-040)."""
    recs_raw = inputs.get("records")
    require(isinstance(recs_raw, list) and len(recs_raw) == 3, "records must have 3 O0 rows")

    out_rows: list[dict[str, object]] = []
    for r in recs_raw:
        require(isinstance(r, dict), "solar record must be dict")
        rid = r.get("id")
        ao_s = r.get("ao")
        tg_s = r.get("target")
        require(
            isinstance(rid, str) and isinstance(ao_s, str) and isinstance(tg_s, str),
            "solar record fields must be strings",
        )
        ao = parse_printed_rational(ao_s, name="ao", allow_fraction_slash=False, allow_exponent=False)
        tg = parse_printed_rational(tg_s, name="target", allow_fraction_slash=False, allow_exponent=False)
        require(tg > 0, "solar target must be positive")
        resid = ao - tg
        ape = (abs(resid) * Fraction(100, 1)) / tg
        out_rows.append(
            {
                "id": rid,
                "ao_exact": _pair(ao),
                "target_exact": _pair(tg),
                "residual_exact": _pair(resid),
                "abs_percent_error_exact": _pair(ape),
                "abs_percent_error_7dp": format_rational_fixed(ape, 7),
            }
        )

    out: dict[str, object] = {
        "native_sadar_evaluated": 0,
        "producer_gate_status": "HOLD_MISSING_NATIVE_SOLAR_PRODUCER",
        "records": out_rows,
    }
    require_no_floats(out)
    return out


def build_solar_o0_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 3-row O0 solar boundary audit CSV for Manual §12."""
    res = eval_dec_solar_o0_boundary_audit(
        {
            "records": [
                {"id": "mercury_perihelion", "ao": "42.9799", "target": "42.98"},
                {"id": "solar_light_bending", "ao": "1.75001", "target": "1.75"},
                {"id": "solar_redshift", "ao": "0.00000211996", "target": "0.00000212"},
            ]
        }
    )
    recs = res["records"]
    require(isinstance(recs, list), "records must be list")
    scopes = {
        "mercury_perihelion": "B_Hg(orbital_return_shell)",
        "solar_light_bending": "B_bend(grazing_ray_chord)",
        "solar_redshift": "B_red(radial_climb_window)",
    }
    rows: list[dict[str, str]] = []
    for item in recs:
        require(isinstance(item, dict), "item must be dict")
        rid = str(item["id"])
        ao = _parse_pair(item["ao_exact"], name="ao")
        tg = _parse_pair(item["target_exact"], name="tg")
        rd = _parse_pair(item["residual_exact"], name="rd")
        ap = _parse_pair(item["abs_percent_error_exact"], name="ap")
        rows.append(
            {
                "record_id": rid,
                "boundary_scope": scopes[rid],
                "ao_exact": canonical_rational_str(ao),
                "target_exact": canonical_rational_str(tg),
                "residual_exact": canonical_rational_str(rd),
                "abs_pct_error_exact": canonical_rational_str(ap),
                "abs_pct_error_7dp": str(item["abs_percent_error_7dp"]),
                "native_producer_gate": "HOLD_MISSING_NATIVE_SOLAR_PRODUCER",
            }
        )
    return rows


# =============================================================================
# RC-041: Manual §13 — 20-Tick Q4 -> Z^3 Hinge-Saturation Run-Tumble Generator
# =============================================================================


def _octant_3d(x: int, y: int, z: int) -> int:
    b0 = 1 if x < 0 else 0
    b1 = 2 if y < 0 else 0
    b2 = 4 if z < 0 else 0
    return b0 | b1 | b2


def eval_dec_run_tumble_q4_stepper(inputs: dict[str, object]) -> dict[str, object]:
    """Generate 20-tick Q4->Z^3 run-tumble trace from 2-step hinge-saturation slide law (RC-041)."""
    ticks = require_exact_int(inputs.get("ticks"), name="ticks")
    sat_lim = require_exact_int(inputs.get("run_saturation_limit"), name="run_saturation_limit")
    beta_a = require_exact_int(inputs.get("beta_a"), name="beta_a")
    require(ticks == 20 and sat_lim == 2 and beta_a == 5, "canonical 20-tick run-tumble parameters required")

    # 8-leg 4D closed cycle: first 4 legs (+1,+1,-1,+1) on (e1,e2,e3,e4), next 4 legs flipped (-1,-1,+1,-1)
    base_legs: tuple[tuple[str, int, int], ...] = (
        ("e1", 0, 1),
        ("e2", 1, 1),
        ("e3", 2, -1),
        ("e4", 3, 1),
        ("e1", 0, -1),
        ("e2", 1, -1),
        ("e3", 2, 1),
        ("e4", 3, -1),
    )

    h = [0, 0, 0, 0]
    phase_counts = [0 for _ in range(beta_a)]
    octant_counts = [0 for _ in range(8)]
    sum_q3 = 0
    sum_q4 = 0
    closure_at_16 = 0

    for t in range(1, ticks + 1):
        leg_idx = ((t - 1) // sat_lim) % len(base_legs)
        in_leg = (t - 1) % sat_lim
        _ename, axis, sigma = base_legs[leg_idx]
        mode = "run" if (t == 1 or in_leg > 0) else "tumble"
        require(mode in ("run", "tumble"), "invalid mode")
        h[axis] += sigma
        x, y, z = h[0], h[1], h[2]
        q3 = x * x + y * y + z * z
        q4 = q3 + h[3] * h[3]
        theta = q3 % beta_a
        oct_code = _octant_3d(x, y, z)
        phase_counts[theta] += 1
        octant_counts[oct_code] += 1
        sum_q3 += q3
        sum_q4 += q4
        if t == 16 and h == [0, 0, 0, 0]:
            closure_at_16 = 1

    require(closure_at_16 == 1, "Q4 run-tumble walk must close to (0,0,0,0) at tick 16")
    out: dict[str, object] = {
        "active_ticks": ticks,
        "closure_at_tick_16": closure_at_16,
        "final_h4": list(h),
        "sum_Q3": sum_q3,
        "sum_Q4": sum_q4,
        "phase_counts": phase_counts,
        "octant_counts": octant_counts,
    }
    require_no_floats(out)
    return out


def build_run_tumble_dec_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 21-row Q4->Z^3 D.E.C. run-tumble walk CSV for Manual §13."""
    base_legs: tuple[tuple[str, int, int], ...] = (
        ("e1", 0, 1),
        ("e2", 1, 1),
        ("e3", 2, -1),
        ("e4", 3, 1),
        ("e1", 0, -1),
        ("e2", 1, -1),
        ("e3", 2, 1),
        ("e4", 3, -1),
    )
    h = [0, 0, 0, 0]
    rows: list[dict[str, str]] = [
        {
            "t": "0",
            "mode": "init",
            "edge": "-",
            "sigma": "0",
            "dwell_adm": "1",
            "h1": "0",
            "h2": "0",
            "h3": "0",
            "h4": "0",
            "Q3": "0",
            "Q4": "0",
            "theta": "0",
            "octant": "0",
        }
    ]
    for t in range(1, 21):
        leg_idx = ((t - 1) // 2) % len(base_legs)
        in_leg = (t - 1) % 2
        ename, axis, sigma = base_legs[leg_idx]
        mode = "run" if (t == 1 or in_leg > 0) else "tumble"
        dwell_adm = "0" if mode == "tumble" else "1"
        h[axis] += sigma
        x, y, z = h[0], h[1], h[2]
        q3 = x * x + y * y + z * z
        q4 = q3 + h[3] * h[3]
        theta = q3 % 5
        oct_code = _octant_3d(x, y, z)
        rows.append(
            {
                "t": str(t),
                "mode": mode,
                "edge": ename,
                "sigma": str(sigma),
                "dwell_adm": dwell_adm,
                "h1": str(h[0]),
                "h2": str(h[1]),
                "h3": str(h[2]),
                "h4": str(h[3]),
                "Q3": str(q3),
                "Q4": str(q4),
                "theta": str(theta),
                "octant": str(oct_code),
            }
        )
    return rows


# =============================================================================
# RC-042: Manual §14 — FRG Lens-Boundary Ray Walk with Active Chiral Flips
# =============================================================================


def eval_dec_lensing_ray_chiral_delta3(inputs: dict[str, object]) -> dict[str, object]:
    """Step FRG lens-boundary ray-packet shells with active chiral flips before B_ext (RC-042)."""
    shells_raw = inputs.get("shells")
    require(isinstance(shells_raw, list) and len(shells_raw) >= 1, "shells must be non-empty list")

    shell_out: list[dict[str, object]] = []
    chiral_flips_total = 0
    total_m = 0
    chi_state = 1  # starts as D_alpha (+1)
    for idx, sh in enumerate(shells_raw):
        require(isinstance(sh, dict), f"shells[{idx}] must be dict")
        k = require_exact_int(sh.get("k"), name="k")
        t0 = require_exact_int(sh.get("s_base"), name="s_base")
        c_x = require_exact_int(sh.get("c_cross"), name="c_cross")
        flip = require_exact_int(sh.get("chiral_flip"), name="chiral_flip")
        comp = require_exact_int(sh.get("comparator"), name="comparator")
        require(flip in (0, 1), "chiral_flip must be 0 or 1")
        if flip == 1:
            chi_state = -chi_state
            chiral_flips_total += 1
        tx = t0 + c_x
        require(tx - t0 == c_x, "FRG ring-gate identity violated")
        dz = tx - comp
        sgn = 1 if dz > 0 else (-1 if dz < 0 else 0)
        mag = abs(dz)
        total_m += mag
        shell_out.append(
            {
                "k": k,
                "T0": t0,
                "C_cross": c_x,
                "T_cross": tx,
                "post_chi": chi_state,
                "Delta_Z": dz,
                "delta3_sgn": sgn,
                "delta3_m": mag,
            }
        )

    out: dict[str, object] = {
        "shell_count": len(shell_out),
        "chiral_flips_total": chiral_flips_total,
        "final_chirality": chi_state,
        "delta3_total_m": total_m,
        "target_quarantined_before_freeze": 1,
        "shells": shell_out,
    }
    require_no_floats(out)
    return out


def build_lensing_ray_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 4-shell FRG chiral ray-packet D.E.C. CSV for Manual §14."""
    res = eval_dec_lensing_ray_chiral_delta3(
        {
            "shells": [
                {"k": 1, "s_base": 4, "c_cross": 3, "chiral_flip": 1, "comparator": 7},
                {"k": 2, "s_base": 6, "c_cross": 5, "chiral_flip": 1, "comparator": 10},
                {"k": 3, "s_base": 5, "c_cross": -2, "chiral_flip": 0, "comparator": 3},
                {"k": 4, "s_base": 8, "c_cross": 4, "chiral_flip": 1, "comparator": 11},
            ]
        }
    )
    sh_list = res["shells"]
    require(isinstance(sh_list, list), "shells must be list")
    comps = [7, 10, 3, 11]
    flips = [1, 1, 0, 1]
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(sh_list):
        require(isinstance(item, dict), "item must be dict")
        rows.append(
            {
                "shell_k": str(item["k"]),
                "T0_base": str(item["T0"]),
                "C_cross": str(item["C_cross"]),
                "T_cross": str(item["T_cross"]),
                "chiral_flip": str(flips[idx]),
                "post_chi": "+1" if item["post_chi"] == 1 else "-1",
                "O_comparator": str(comps[idx]),
                "Delta_Z": str(item["Delta_Z"]),
                "delta3_pair": f"({item['delta3_sgn']},{item['delta3_m']})",
            }
        )
    return rows


# =============================================================================
# RC-043: Manual App. A — Exact Rational Cycle-Shedding Recurrence
# =============================================================================


def eval_dec_cycle_shedding_exact_summary(inputs: dict[str, object]) -> dict[str, object]:
    """Step exact rational cycle-shedding recurrence P_t, X_t, O_t, R_t (RC-043)."""
    eta = _parse_pair(inputs.get("eta_ret"), name="eta_ret")
    gamma = _parse_pair(inputs.get("gamma_span"), name="gamma_span")
    lam = _parse_pair(inputs.get("lambda_reclose"), name="lambda_reclose")
    ticks_raw = inputs.get("ticks")
    require(isinstance(ticks_raw, list) and len(ticks_raw) >= 1, "ticks must be non-empty list")

    prev_p = Fraction(0, 1)
    sum_x = Fraction(0, 1)
    sum_o = Fraction(0, 1)
    sum_r = Fraction(0, 1)
    steps_out: list[dict[str, object]] = []
    for idx, tk in enumerate(ticks_raw):
        require(isinstance(tk, dict), f"ticks[{idx}] must be dict")
        lead = _parse_pair(tk.get("lead"), name="lead")
        lag = _parse_pair(tk.get("lag"), name="lag")
        comp = _parse_pair(tk.get("comp"), name="comp")
        span = abs(lead - lag)
        before = eta * prev_p + gamma * span
        raw_exc = before - comp
        x_t = raw_exc if raw_exc > 0 else Fraction(0, 1)
        p_t = before - x_t
        require(p_t <= comp, "post-clipping burden exceeded compatibility")
        r_t = lam * x_t
        o_t = (Fraction(1, 1) - lam) * x_t
        require(o_t + r_t == x_t, "shedding split failed exact conservation")
        prev_p = p_t
        sum_x += x_t
        sum_o += o_t
        sum_r += r_t
        steps_out.append(
            {
                "tick": idx,
                "span": _pair(span),
                "before_clip": _pair(before),
                "padar_burden": _pair(p_t),
                "shed_excess": _pair(x_t),
                "outward_O": _pair(o_t),
                "local_R": _pair(r_t),
            }
        )

    require(sum_o + sum_r == sum_x, "cumulative shedding conservation violated")
    out: dict[str, object] = {
        "tick_count": len(steps_out),
        "total_shed_X": _pair(sum_x),
        "total_outward_O": _pair(sum_o),
        "total_local_R": _pair(sum_r),
        "outward_share_on_shed": _pair(sum_o / sum_x) if sum_x > 0 else ["0", "1"],
        "local_share_on_shed": _pair(sum_r / sum_x) if sum_x > 0 else ["0", "1"],
        "steps": steps_out,
    }
    require_no_floats(out)
    return out


def build_cycle_shedding_exact_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 4-step exact rational cycle-shedding D.E.C. CSV for Manual App. A."""
    res = eval_dec_cycle_shedding_exact_summary(
        {
            "eta_ret": ["41", "50"],
            "gamma_span": ["11", "20"],
            "lambda_reclose": ["19", "50"],
            "ticks": [
                {"lead": ["21", "50"], "lag": ["107", "250"], "comp": ["14", "25"]},
                {"lead": ["39", "50"], "lag": ["1", "5"], "comp": ["1", "4"]},
                {"lead": ["4", "5"], "lag": ["1", "10"], "comp": ["1", "4"]},
                {"lead": ["9", "20"], "lag": ["2", "5"], "comp": ["3", "10"]},
            ],
        }
    )
    st_list = res["steps"]
    require(isinstance(st_list, list), "steps must be list")
    comps = ["14/25", "1/4", "1/4", "3/10"]
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(st_list):
        require(isinstance(item, dict), "item must be dict")
        sp = _parse_pair(item["span"], name="span")
        bf = _parse_pair(item["before_clip"], name="before")
        pb = _parse_pair(item["padar_burden"], name="padar")
        sx = _parse_pair(item["shed_excess"], name="shed")
        oo = _parse_pair(item["outward_O"], name="outward")
        lr = _parse_pair(item["local_R"], name="local")
        rows.append(
            {
                "tick": str(item["tick"]),
                "span_exact": canonical_rational_str(sp),
                "before_clip_exact": canonical_rational_str(bf),
                "C_compat_exact": comps[idx],
                "padar_P_exact": canonical_rational_str(pb),
                "shed_X_exact": canonical_rational_str(sx),
                "outward_O_exact": canonical_rational_str(oo),
                "local_R_exact": canonical_rational_str(lr),
            }
        )
    return rows


# =============================================================================
# RC-044: Manual App. C — 9-Point Z^3 Lag-1 Coordinate Phase-Cycle & Octant Walk
# =============================================================================


def eval_dec_coordinate_phase_3d_walk(inputs: dict[str, object]) -> dict[str, object]:
    """Step 9-point Z^3 trajectory lag-1 displacements, phase residues & octant delta_3 (RC-044)."""
    pts_raw = inputs.get("points")
    beta_a = require_exact_int(inputs.get("beta_a"), name="beta_a")
    require(isinstance(pts_raw, list) and len(pts_raw) >= 2 and beta_a > 0, "invalid 3D track inputs")

    pts: list[tuple[int, int, int]] = []
    for idx, p in enumerate(pts_raw):
        require(isinstance(p, list) and len(p) == 3, f"points[{idx}] must have 3 ints")
        pts.append(
            (
                require_exact_int(p[0], name="x"),
                require_exact_int(p[1], name="y"),
                require_exact_int(p[2], name="z"),
            )
        )

    n_steps = len(pts) - 1
    phase_counts = [0 for _ in range(beta_a)]
    octant_counts = [0 for _ in range(8)]
    q_vals: list[int] = []
    for i in range(n_steps):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        dz = pts[i + 1][2] - pts[i][2]
        q_i = dx * dx + dy * dy + dz * dz
        th = q_i % beta_a
        oc = _octant_3d(dx, dy, dz)
        q_vals.append(q_i)
        phase_counts[th] += 1
        octant_counts[oc] += 1

    # Integer-balanced octant comparator IntBalance(N, 8)
    base_q = n_steps // 8
    rem_q = n_steps % 8
    comp_oct = [base_q + (1 if q < rem_q else 0) for q in range(8)]
    dz_oct = [comp_oct[q] - octant_counts[q] for q in range(8)]
    require(sum(dz_oct) == 0, "octant delta_3 comparator failed count conservation")
    m_oct = sum(abs(x) for x in dz_oct)

    base_th = n_steps // beta_a
    rem_th = n_steps % beta_a
    comp_th = [base_th + (1 if th < rem_th else 0) for th in range(beta_a)]
    dz_th = [comp_th[th] - phase_counts[th] for th in range(beta_a)]
    require(sum(dz_th) == 0, "phase delta_3 comparator failed count conservation")
    m_th = sum(abs(x) for x in dz_th)

    out: dict[str, object] = {
        "step_count": n_steps,
        "Q_values": q_vals,
        "sum_Q": sum(q_vals),
        "R_Q_ratio": _pair(Fraction(sum(q_vals), n_steps)),
        "phase_counts": phase_counts,
        "phase_delta3_M": m_th,
        "octant_counts": octant_counts,
        "octant_delta3_M": m_oct,
    }
    require_no_floats(out)
    return out


def build_coordinate_phase_3d_csv_rows() -> list[dict[str, str]]:
    """Build deterministic 8-step Z^3 lag-1 D.E.C. displacement CSV for Manual App. C."""
    pts = [
        (0, 0, 0),
        (1, 1, 0),
        (2, 1, 1),
        (3, 2, 1),
        (2, 3, 2),
        (3, 4, 3),
        (4, 3, 4),
        (5, 4, 4),
        (6, 5, 5),
    ]
    rows: list[dict[str, str]] = []
    for i in range(len(pts) - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        dz = pts[i + 1][2] - pts[i][2]
        q_i = dx * dx + dy * dy + dz * dz
        th = q_i % 4
        oc = _octant_3d(dx, dy, dz)
        rows.append(
            {
                "step_i": str(i + 1),
                "from_xyz": f"({pts[i][0]},{pts[i][1]},{pts[i][2]})",
                "to_xyz": f"({pts[i + 1][0]},{pts[i + 1][1]},{pts[i + 1][2]})",
                "delta_xyz": f"({dx},{dy},{dz})",
                "Q_lag1": str(q_i),
                "theta_mod4": str(th),
                "octant_q": str(oc),
            }
        )
    return rows


# =============================================================================
# Deterministic CSV Serialization & Verification Hook
# =============================================================================


def _rows_to_csv_text(rows: list[dict[str, str]]) -> str:
    require(len(rows) > 0, "cannot serialize empty CSV rows")
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def expected_manual_dec_csv_map() -> dict[str, str]:
    """Return exact expected UTF-8 contents for all 12 new boundary_sadar CSV fixtures."""
    return {
        "manual/data/boundary_sadar/native_closure_wave_dec_walk.csv": _rows_to_csv_text(
            build_native_closure_wave_csv_rows()
        ),
        "manual/data/boundary_sadar/awareness_operativity_dec_walk.csv": _rows_to_csv_text(
            build_awareness_operativity_csv_rows()
        ),
        "manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv": _rows_to_csv_text(
            build_cell_measures_csv_rows()
        ),
        "manual/data/boundary_sadar/typed_map_joint_law_ledger.csv": _rows_to_csv_text(
            build_typed_maps_csv_rows()
        ),
        "manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv": _rows_to_csv_text(
            build_temporal_si_bridge_csv_rows()
        ),
        "manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv": _rows_to_csv_text(
            build_short_window_csv_rows()
        ),
        "manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv": _rows_to_csv_text(
            build_hydrogen_transitions_csv_rows()
        ),
        "manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv": _rows_to_csv_text(
            build_solar_o0_csv_rows()
        ),
        "manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv": _rows_to_csv_text(
            build_run_tumble_dec_csv_rows()
        ),
        "manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv": _rows_to_csv_text(
            build_lensing_ray_csv_rows()
        ),
        "manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv": _rows_to_csv_text(
            build_cycle_shedding_exact_csv_rows()
        ),
        "manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv": _rows_to_csv_text(
            build_coordinate_phase_3d_csv_rows()
        ),
    }


def verify_manual_dec_examples(root: Path) -> dict[str, int]:
    """Verify all 12 Manual D.E.C. CSV fixtures and cross-check against retained tracks."""
    exp_map = expected_manual_dec_csv_map()
    for rel, expected_txt in sorted(exp_map.items()):
        p = root / rel
        require(p.is_file(), f"missing Manual D.E.C. CSV fixture: {rel}")
        actual_txt = p.read_text(encoding="utf-8")
        require(actual_txt == expected_txt, f"Manual D.E.C. CSV drift in {rel}")

    # Cross-check that our Q4->Z^3 stepper reproduces all 21 rows of run_tumble_trace_20_ticks.csv!
    rt_gen = build_run_tumble_dec_csv_rows()
    with (root / "manual/data/run_tumble/run_tumble_trace_20_ticks.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        rt_orig = list(csv.DictReader(fh))
    require(len(rt_orig) == len(rt_gen), "run_tumble row count mismatch")
    for g_row, o_row in zip(rt_gen, rt_orig):
        for col in ("t", "mode", "edge", "sigma", "h1", "h2", "h3", "h4", "Q3", "Q4", "theta", "octant"):
            require(
                g_row[col] == o_row[col],
                f"Q4 stepper vs run_tumble_trace_20_ticks.csv mismatch at t={g_row['t']} col={col}",
            )

    return {"manual_dec_extra_csvs": len(exp_map), "run_tumble_stepper_rows_matched": len(rt_gen)}
