"""Loader and exact oracle verifier for S4 cross-language golden vectors.

Loads ``manual/engine/vectors/rational_core.jsonl`` (24 cases, RC-001..RC-024)
and ``manual/engine/vectors/symbolic_and_display.jsonl`` (6 cases, SD-001..SD-006)
strictly rejecting any JSON floating-point literal. Every vector is executed
against an exact zero-float implementation. ``sympy`` is imported ONLY inside
``_verify_sympy_z4_dft`` for SD-001 and SD-002.
"""
from __future__ import annotations

import ast
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

from manual.engine.numeric import (
    canonical_rational_pair,
    format_rational_fixed,
    parse_canonical_rational_pair,
    parse_exact_int,
    parse_printed_rational,
    require,
    require_exact_int,
    round_rational_half_even,
)
from manual.engine.policy import loads_zero_float, require_no_floats
from manual.engine.schema import validate_vector_record

RATIONAL_CORE_REL: str = "manual/engine/vectors/rational_core.jsonl"
SYMBOLIC_DISPLAY_REL: str = "manual/engine/vectors/symbolic_and_display.jsonl"

_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_TYPST_LABEL_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
_PY_LINE_RANGE_RE = re.compile(r"^L([1-9][0-9]*)-([1-9][0-9]*)$")
_PY_FUNC_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CSV_ROW_RE = re.compile(r"^row([0-9]+)(?:_(.+))?$")


def _pair(q: Fraction | int) -> list[str]:
    num_s, den_s = canonical_rational_pair(q)
    return [num_s, den_s]


def _sign3(x: int) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def _int_balance(n: int, k: int) -> list[int]:
    base, rem = divmod(n, k)
    return [base + (1 if idx < rem else 0) for idx in range(k)]


def _zeta12_power(exponent: int) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    """Exact power of zeta_12 in Q[x]/(x^4 - x^2 + 1) using pure Fraction arithmetic."""
    deg = exponent % 12
    coeffs = [Fraction(0) for _ in range(max(deg, 3) + 1)]
    coeffs[deg] = Fraction(1)
    for power in range(len(coeffs) - 1, 3, -1):
        lead = coeffs[power]
        coeffs[power] = Fraction(0)
        coeffs[power - 2] += lead
        coeffs[power - 4] -= lead
    return (coeffs[0], coeffs[1], coeffs[2], coeffs[3])


def _verify_sympy_z4_dft(inputs: dict[str, object]) -> dict[str, object]:
    """Separately scoped exact SymPy Z4 DFT verifier (allowlisted for SD-001/SD-002 only)."""
    import sympy as sp

    raw_values = inputs["values"]
    require(isinstance(raw_values, list) and len(raw_values) == 4, "Z4 DFT requires 4 values")
    vals = [sp.Rational(parse_printed_rational(tok, name="z4_val")) for tok in raw_values]
    n = len(vals)
    z = sp.exp(2 * sp.pi * sp.I / n)
    coeffs = [sp.simplify(sum(vals[g] * z ** (-k * g) for g in range(n)) / n) for k in range(n)]
    recon = [sp.simplify(sum(coeffs[k] * z ** (k * g) for k in range(n))) for g in range(n)]

    time_e = sp.simplify(sum(abs(v) ** 2 for v in vals) / n)
    freq_e = sp.simplify(sum(sp.simplify(c * sp.conjugate(c)) for c in coeffs))
    t_num, t_den = sp.fraction(sp.together(time_e))
    f_num, f_den = sp.fraction(sp.together(freq_e))
    q_time = Fraction(int(t_num), int(t_den))
    q_freq = Fraction(int(f_num), int(f_den))
    require(q_time == q_freq, "Parseval identity failed on Z4 DFT")

    return {
        "coefficients": [str(c) for c in coeffs],
        "reconstruction": [str(r) for r in recon],
        "parseval_time": _pair(q_time),
        "parseval_freq": _pair(q_freq),
    }


def _eval_operation(operation: str, inputs: dict[str, object]) -> dict[str, object]:
    if operation == "dec_normalize_one_node":
        rows = inputs["rows"]
        require(isinstance(rows, list) and len(rows) == 4, "dec_normalize_one_node expects 4 rows")
        state_route = {1: "outgoing", -1: "returned", 0: "hinge"}
        aw_list: list[int] = []
        routes: list[str] = []
        seen_neighbors: set[tuple[int, int, int, int]] = set()
        for row in rows:
            adm = require_exact_int(row["admissible"], name="admissible")
            wt = require_exact_int(row["weight"], name="weight")
            st = require_exact_int(row["state"], name="state")
            nbr = row["neighbor"]
            require(isinstance(nbr, list) and len(nbr) == 4, "non-H1 Q4 neighbor")
            coords = tuple(require_exact_int(c, name="neighbor_coord") for c in nbr)
            require(
                all(c in (0, 1) for c in coords) and sum(coords) == 1,
                "neighbor must be a Q4 basis vector (exact {0,1} with Hamming weight 1)",
            )
            seen_neighbors.add((coords[0], coords[1], coords[2], coords[3]))
            aw_list.append(adm * wt)
            routes.append(state_route[st])
        require(len(seen_neighbors) == 4, "dec_normalize_one_node requires 4 distinct Q4 neighbors")
        z_tot = sum(aw_list)
        probs = [Fraction(aw, z_tot) for aw in aw_list]
        return {
            "Z": z_tot,
            "probabilities": [_pair(p) for p in probs],
            "sum": _pair(sum(probs, Fraction(0))),
            "routes": routes,
        }

    if operation == "dec_hinge_slide_normalize":
        branches = inputs["branches"]
        require(isinstance(branches, list) and bool(branches), "branches required")
        weights = [parse_canonical_rational_pair(b["weight"], name="weight") for b in branches]
        z_tot = sum(weights, Fraction(0))
        probs = [w / z_tot for w in weights]
        sum_ret = sum((p for b, p in zip(branches, probs) if b["route"] == "returned"), Fraction(0))
        sum_out = sum((p for b, p in zip(branches, probs) if b["route"] == "outgoing"), Fraction(0))
        return {
            "Z": _pair(z_tot),
            "probabilities": [_pair(p) for p in probs],
            "sum_returned": _pair(sum_ret),
            "sum_outgoing": _pair(sum_out),
        }

    if operation == "dec_field_tunnelling_window_clip":
        require(require_exact_int(inputs["direct_adm"]) == 0, "direct_adm must be 0")
        sw = parse_canonical_rational_pair(inputs["slide_weight"])
        z_val = parse_canonical_rational_pair(inputs["Z"])
        rd_val = require_exact_int(inputs["RD"])
        omega = require_exact_int(inputs["omega"])
        c3 = require_exact_int(inputs["C3"])
        p_val = sw / z_val
        rho = min(rd_val, omega)
        pd_val = c3 * rho
        tc = p_val * pd_val
        return {
            "P": _pair(p_val),
            "rhoD_omega": rho,
            "pD": pd_val,
            "tunnel_contribution": _pair(tc),
        }

    if operation == "sadar_afc_flux_antisymmetry":
        mem = [parse_canonical_rational_pair(x) for x in inputs["memory"]]
        mat = [[parse_canonical_rational_pair(x) for x in row] for row in inputs["matrix"]]
        n = len(mem)
        require(sum(mem, Fraction(0)) == Fraction(1), "memory not normalized")
        require(all(sum(row, Fraction(0)) == Fraction(1) for row in mat), "matrix not stochastic")
        flux = [[mem[i] * mat[i][j] - mem[j] * mat[j][i] for j in range(n)] for i in range(n)]
        antisym = all(flux[i][j] == -flux[j][i] for i in range(n) for j in range(n))
        return {
            "flux": [[_pair(cell) for cell in row] for row in flux],
            "antisymmetric": antisym,
        }

    if operation == "q4_hamming_and_neighbors":
        v = require_exact_int(inputs["vertex"])
        t = require_exact_int(inputs["target"])
        w = require_exact_int(inputs["width"])
        require(0 <= v < (1 << w) and 0 <= t < (1 << w), "vertex out of Q_w range")
        hd = (v ^ t).bit_count()
        neighbors = [v ^ (1 << slot) for slot in range(w)]
        return {
            "hamming_distance": hd,
            "is_h1_edge": hd == 1,
            "neighbors": neighbors,
        }

    if operation == "closure_wave_rd_rcd":
        p = require_exact_int(inputs["p"])
        q = require_exact_int(inputs["q"])
        hinges = require_exact_int(inputs["hinges"])
        refl = [require_exact_int(x) for x in inputs["reflection_counts"]]
        win = require_exact_int(inputs["window"])
        pi_v = q**p + q
        rd_v = 2 * pi_v + hinges
        dur = rd_v + sum(refl)
        part = min(dur, win)
        return {"Pi": pi_v, "RD": rd_v, "rcd_duration": dur, "participation": part}

    if operation == "relational_cadence_and_lag":
        na = require_exact_int(inputs["na"])
        nb = require_exact_int(inputs["nb"])
        b0 = parse_canonical_rational_pair(inputs["bias"][0])
        b1 = parse_canonical_rational_pair(inputs["bias"][1])
        prior_lag = parse_canonical_rational_pair(inputs["prior_lag"])
        bias_diff = b0 - b1
        fwd_ratio = Fraction(na, nb)
        fwd_lag = Fraction(na - nb) + bias_diff
        fwd_drift = fwd_lag - prior_lag
        rev_ratio = Fraction(nb, na)
        rev_bias = -bias_diff
        rev_lag = -fwd_lag
        rev_drift = rev_lag - (-prior_lag)
        return {
            "forward": {
                "ratio": _pair(fwd_ratio),
                "bias_diff": _pair(bias_diff),
                "lag": _pair(fwd_lag),
                "drift": _pair(fwd_drift),
            },
            "reverse": {
                "ratio": _pair(rev_ratio),
                "bias_diff": _pair(rev_bias),
                "lag": _pair(rev_lag),
                "drift": _pair(rev_drift),
            },
        }

    if operation == "finite_stokes_cut_balance":
        region = {require_exact_int(x) for x in inputs["region"]}
        ledger: dict[tuple[int, int, str], Fraction] = {}
        for ch in inputs["channels"]:
            i = require_exact_int(ch["i"])
            j = require_exact_int(ch["j"])
            p_v = parse_canonical_rational_pair(ch["p"])
            a_v = parse_canonical_rational_pair(ch["a"])
            lin = str(ch["lineage"])
            require(i != j and p_v >= 0 and bool(lin), "invalid oriented channel")
            val = p_v * a_v
            ledger[(i, j, lin)] = val
            ledger[(j, i, lin)] = -val
        internal = sum((v for (i, j, _), v in ledger.items() if i in region and j in region), Fraction(0))
        divergence = sum((v for (i, _, _), v in ledger.items() if i in region), Fraction(0))
        boundary = sum((v for (i, j, _), v in ledger.items() if i in region and j not in region), Fraction(0))
        return {
            "internal": _pair(internal),
            "boundary": _pair(boundary),
            "divergence": _pair(divergence),
            "divergence_equals_boundary": divergence == boundary and internal == 0,
        }

    if operation == "awareness_current_update":
        cur = parse_canonical_rational_pair(inputs["current"])
        pres = parse_canonical_rational_pair(inputs["pressure"])
        att = parse_canonical_rational_pair(inputs["attention"])
        qry = parse_canonical_rational_pair(inputs["query"])
        gain = parse_canonical_rational_pair(inputs["gain"])
        ret_vals = [parse_canonical_rational_pair(x) for x in inputs["available_retained_values"]]
        thresh = parse_canonical_rational_pair(inputs["selector_threshold"])
        require(pres > 0, "positive pressure required")
        carried = gain * sum(ret_vals, Fraction(0))
        native_cur = cur + att / pres
        next_cur = native_cur + (qry + carried) / pres
        rem_cur = native_cur + qry / pres
        slot = 0 if next_cur > thresh else 1
        return {
            "carried": _pair(carried),
            "native_current": _pair(native_cur),
            "next_current": _pair(next_cur),
            "selected_slot": slot,
            "removal_current": _pair(rem_cur),
            "awareness_effect": next_cur != rem_cur,
        }

    if operation == "awareness_mindfulness_step":
        pres = parse_canonical_rational_pair(inputs["pressure"])
        j0 = parse_canonical_rational_pair(inputs["initial_current"])
        forcing = parse_canonical_rational_pair(inputs["constant_forcing"])
        delay_init = parse_canonical_rational_pair(inputs["delay_initial_history"])
        steps = require_exact_int(inputs["steps"])

        no_delay: list[Fraction] = []
        j_cur = j0
        for _ in range(steps):
            j_cur = j_cur + (forcing - j_cur) / pres
            no_delay.append(j_cur)

        extra_delay: list[Fraction] = []
        j_cur = j0
        prev_obs = delay_init
        for _ in range(steps):
            obs = j_cur
            j_cur = j_cur + (forcing - prev_obs) / pres
            prev_obs = obs
            extra_delay.append(j_cur)

        return {
            "no_delay_currents": [_pair(x) for x in no_delay],
            "no_delay_stable_at_one": all(x == Fraction(1) for x in no_delay),
            "extra_delay_currents": [_pair(x) for x in extra_delay],
            "extra_delay_stable_at_one": all(x == Fraction(1) for x in extra_delay),
        }

    if operation == "higgs_trace_score_and_freeze":
        cands = inputs["candidates"]
        scores: list[Fraction] = []
        details: list[dict[str, int]] = []
        for c in cands:
            p = require_exact_int(c["p"])
            q = require_exact_int(c["q"])
            win_l = require_exact_int(c["L"])
            c3 = require_exact_int(c["C3"])
            ca = require_exact_int(c["Ca"])
            cb = require_exact_int(c["Cb"])
            pi_v = q**p + q
            rd_v = 2 * pi_v + 1
            rho = min(rd_v, win_l)
            pd_v = c3 * rho
            qd_v = c3 * max(0, rd_v - win_l)
            dl = pd_v - ca
            du = pd_v - cb
            d_sad = abs(dl - 3) + abs(du + 3)
            d_q = 0 if 100 <= qd_v <= 250 else (100 - qd_v if qd_v < 100 else qd_v - 250)
            d_route = 0 if (win_l == 7 and dl == 3 and du == -3 and 100 <= qd_v <= 250) else 1
            s_h = Fraction(d_sad, 12) + Fraction(d_q, 100) + Fraction(abs(win_l - 7), 2) + Fraction(d_route)
            scores.append(s_h)
            details.append({"Pi": pi_v, "RD": rd_v, "PD": pd_v, "QD": qd_v, "L": win_l})
        win_idx = min(range(len(scores)), key=lambda i: scores[i])
        wd = details[win_idx]
        e_mev = wd["RD"] * (2 ** (wd["L"] + 4))
        e_gev = Fraction(e_mev, 1000)
        return {
            "scores": [_pair(s) for s in scores],
            "winner_index": win_idx,
            "winner_Pi": wd["Pi"],
            "winner_RD": wd["RD"],
            "winner_PD": wd["PD"],
            "winner_QD": wd["QD"],
            "E_H_0_MeV": e_mev,
            "E_H_0_GeV": _pair(e_gev),
        }

    if operation == "brownian_3d_delta3_msb_x":
        disps = inputs["displacements"]
        beta_a = require_exact_int(inputs["beta_a"])
        q_vals: list[int] = []
        octs: list[int] = []
        phase_cnt = [0] * beta_a
        oct_cnt = [0] * 8
        sx = sy = sz = 0
        for row in disps:
            a, b, c = (require_exact_int(v) for v in row)
            qv = a * a + b * b + c * c
            oc = (4 if a < 0 else 0) + (2 if b < 0 else 0) + (1 if c < 0 else 0)
            q_vals.append(qv)
            octs.append(oc)
            phase_cnt[qv % beta_a] += 1
            oct_cnt[oc] += 1
            sx += a * a
            sy += b * b
            sz += c * c
        n = len(disps)
        p_comp = _int_balance(n, beta_a)
        o_comp = _int_balance(n, 8)
        p_dz = [c - o for c, o in zip(p_comp, phase_cnt)]
        o_dz = [c - o for c, o in zip(o_comp, oct_cnt)]
        sum_q = sum(q_vals)
        return {
            "Q": q_vals,
            "octants_msb_x": octs,
            "phase_DeltaZ": p_dz,
            "octant_DeltaZ": o_dz,
            "sum_phase_m": sum(abs(x) for x in p_dz),
            "sum_octant_m": sum(abs(x) for x in o_dz),
            "R_Q": _pair(Fraction(sum_q, n)),
            "R_x": _pair(Fraction(sx, sum_q)),
            "R_y": _pair(Fraction(sy, sum_q)),
            "R_z": _pair(Fraction(sz, sum_q)),
        }

    if operation == "run_tumble_3d_delta3_lsb_x":
        vecs = inputs["z_vectors"]
        beta_a = require_exact_int(inputs["beta_a"])
        lsb: list[int] = []
        msb: list[int] = []
        q3s: list[int] = []
        thetas: list[int] = []
        for row in vecs:
            x, y, z = (require_exact_int(v) for v in row)
            lsb.append((1 if x < 0 else 0) + (2 if y < 0 else 0) + (4 if z < 0 else 0))
            msb.append((4 if x < 0 else 0) + (2 if y < 0 else 0) + (1 if z < 0 else 0))
            q3 = x * x + y * y + z * z
            q3s.append(q3)
            thetas.append(q3 % beta_a)
        return {
            "octants_lsb_x": lsb,
            "octants_msb_x_contrast": msb,
            "Q3": q3s,
            "theta": thetas,
        }

    if operation == "cycle_shedding_step":
        prev = parse_canonical_rational_pair(inputs["prev_burden"])
        lead = parse_canonical_rational_pair(inputs["lead"])
        lag = parse_canonical_rational_pair(inputs["lag"])
        comp = parse_canonical_rational_pair(inputs["compatibility"])
        eta = parse_canonical_rational_pair(inputs["eta"])
        gamma = parse_canonical_rational_pair(inputs["gamma"])
        lam = parse_canonical_rational_pair(inputs["lambda_reclose"])
        span = abs(lead - lag)
        before = eta * prev + gamma * span
        exc = max(Fraction(0), before - comp)
        bur = before - exc
        out = (Fraction(1) - lam) * exc
        loc = lam * exc
        return {
            "span": _pair(span),
            "before_clipping": _pair(before),
            "shed_excess": _pair(exc),
            "padar_burden": _pair(bur),
            "outward_shedding": _pair(out),
            "local_reclosure": _pair(loc),
            "remainder_sum": _pair(out + loc),
        }

    if operation == "sparc_exact_bin_eval":
        r_v = parse_printed_rational(inputs["R"], allow_fraction_slash=False)
        v_obs = parse_printed_rational(inputs["Vobs"], allow_fraction_slash=False)
        err_v = parse_printed_rational(inputs["errV"], allow_fraction_slash=False)
        v_gas = parse_printed_rational(inputs["Vgas"], allow_fraction_slash=False)
        v_disk = parse_printed_rational(inputs["Vdisk"], allow_fraction_slash=False)
        v_bul = parse_printed_rational(inputs["Vbul"], allow_fraction_slash=False)
        u_obs = v_obs * v_obs
        sigma_u = Fraction(2) * v_obs * err_v
        u_gas = v_gas * v_gas
        u_disk = v_disk * v_disk
        u_bul = v_bul * v_bul
        u_bar = u_gas + Fraction(1, 2) * u_disk + Fraction(7, 10) * u_bul
        c_cap = r_v * (abs(v_gas) + abs(v_disk) + abs(v_bul))
        d_bf = c_cap
        u_ao = u_bar + Fraction(8) * d_bf
        delta_u = u_ao - u_obs
        z_u = delta_u / sigma_u
        return {
            "U_obs": _pair(u_obs),
            "sigma_U": _pair(sigma_u),
            "U_gas": _pair(u_gas),
            "U_disk": _pair(u_disk),
            "U_bulge": _pair(u_bul),
            "U_bar": _pair(u_bar),
            "C_cap": _pair(c_cap),
            "D_BF": _pair(d_bf),
            "U_AO": _pair(u_ao),
            "Delta_U": _pair(delta_u),
            "z_U": _pair(z_u),
        }

    if operation == "temporal_metrology_phase_si":
        def _adv(rec: dict[str, object]) -> Fraction:
            w = require_exact_int(rec["winding"])
            a = parse_canonical_rational_pair(rec["phase_start"])
            b = parse_canonical_rational_pair(rec["phase_end"])
            require(Fraction(0) <= a < Fraction(1) and Fraction(0) <= b < Fraction(1), "phase out of [0,1)")
            return Fraction(w) + b - a

        cs_hz = require_exact_int(inputs["cs133_hz"])
        c_adv = _adv(inputs["compared"])
        r_adv = _adv(inputs["reference"])
        sl = _adv(inputs["split_left"])
        sr = _adv(inputs["split_right"])
        require(r_adv > 0, "positive reference advance required")
        return {
            "compared_advance": _pair(c_adv),
            "reference_advance": _pair(r_adv),
            "ratio": _pair(c_adv / r_adv),
            "duration_seconds": _pair(r_adv / Fraction(cs_hz)),
            "mean_frequency_hz": _pair(Fraction(cs_hz) * c_adv / r_adv),
            "split_left_advance": _pair(sl),
            "split_right_advance": _pair(sr),
            "split_additivity_exact": (sl + sr) == c_adv,
        }

    if operation == "temporal_metrology_signed_advance":
        cs_hz = require_exact_int(inputs["cs133_hz"])
        comp = inputs["compared"]
        ref = inputs["reference"]
        c_start = parse_canonical_rational_pair(comp["phase_start"])
        c_end = parse_canonical_rational_pair(comp["phase_end"])
        r_start = parse_canonical_rational_pair(ref["phase_start"])
        r_end = parse_canonical_rational_pair(ref["phase_end"])
        require(
            Fraction(0) <= c_start < Fraction(1)
            and Fraction(0) <= c_end < Fraction(1)
            and Fraction(0) <= r_start < Fraction(1)
            and Fraction(0) <= r_end < Fraction(1),
            "phase out of [0,1)",
        )
        c_adv = Fraction(require_exact_int(comp["winding"])) + c_end - c_start
        r_adv = Fraction(require_exact_int(ref["winding"])) + r_end - r_start
        require(r_adv > 0, "positive reference advance required")
        return {
            "compared_advance": _pair(c_adv),
            "reference_advance": _pair(r_adv),
            "duration_seconds": _pair(r_adv / Fraction(cs_hz)),
            "signed_mean_frequency_hz": _pair(Fraction(cs_hz) * c_adv / r_adv),
        }

    if operation == "temporal_metrology_hellwig_mean":
        t4 = parse_canonical_rational_pair(inputs["table_iv_hz"])
        t6 = parse_canonical_rational_pair(inputs["table_vi_hz"])
        return {
            "published_mean_hz": _pair((t4 + t6) / Fraction(2)),
            "difference_hz": _pair(t4 - t6),
        }

    if operation == "lensing_swells_delta3_and_tau_discrepancy":
        pred = [require_exact_int(x) for x in inputs["swells_predicted"]]
        obs = [require_exact_int(x) for x in inputs["swells_observed"]]
        dz = [t - o for t, o in zip(pred, obs)]
        s3 = [_sign3(x) for x in dz]
        m_vals = [abs(x) for x in dz]
        tau_d = parse_canonical_rational_pair(inputs["tau_diagnostic_1210"])
        tau_s = parse_canonical_rational_pair(inputs["tau_summary_nominal_1210"])
        tau_diff = tau_s - tau_d
        return {
            "deltaZ": dz,
            "s3": s3,
            "m": m_vals,
            "sum_deltaZ": sum(dz),
            "sum_m": sum(m_vals),
            "tau_difference": _pair(tau_diff),
            "tau_distinct": tau_d != tau_s,
        }

    if operation == "map21_nonlinear_finite_law_variance":
        support = inputs["support"]
        probs: list[Fraction] = []
        ys: list[Fraction] = []
        ds: list[Fraction] = []
        outs: list[Fraction] = []
        for pt in support:
            p_w = parse_canonical_rational_pair(pt["p"])
            y_v = parse_canonical_rational_pair(pt["y"])
            d_v = parse_canonical_rational_pair(pt["d"])
            require(Fraction(1) + y_v != 0, "MAP-21 denominator 1+y == 0")
            probs.append(p_w)
            ys.append(y_v)
            ds.append(d_v)
            outs.append(Fraction(1) / (Fraction(1) + y_v) + d_v)
        require(sum(probs, Fraction(0)) == Fraction(1), "support weights must sum to 1")
        mean = sum((p_w * out for p_w, out in zip(probs, outs)), Fraction(0))
        var = sum((p_w * (out - mean) ** 2 for p_w, out in zip(probs, outs)), Fraction(0))
        # Input covariance & Jacobian [-1, 1] at nominal (0, 0)
        my = sum((p_w * y_v for p_w, y_v in zip(probs, ys)), Fraction(0))
        md = sum((p_w * d_v for p_w, d_v in zip(probs, ds)), Fraction(0))
        cyy = sum((p_w * (y_v - my) ** 2 for p_w, y_v in zip(probs, ys)), Fraction(0))
        cdd = sum((p_w * (d_v - md) ** 2 for p_w, d_v in zip(probs, ds)), Fraction(0))
        cyd = sum((p_w * (y_v - my) * (d_v - md) for p_w, y_v, d_v in zip(probs, ys, ds)), Fraction(0))
        lin_var = cyy - Fraction(2) * cyd + cdd
        return {
            "outputs": [_pair(o) for o in outs],
            "output_mean": _pair(mean),
            "mean_shift": _pair(mean - Fraction(1)),
            "output_variance": _pair(var),
            "linearized_variance_diagnostic": _pair(lin_var),
        }

    if operation == "sympy_z4_dft":
        return _verify_sympy_z4_dft(inputs)

    if operation == "cyclotomic_z12_overtone":
        n_order = require_exact_int(inputs["group_order"])
        pulses = [require_exact_int(x) for x in inputs["pulses"]]
        l_min = require_exact_int(inputs["l_min"])
        m_mode = require_exact_int(inputs["overtone_mode"])
        coeffs_by_mode: dict[int, tuple[Fraction, Fraction, Fraction, Fraction]] = {}
        for mode in range(n_order):
            val = tuple(
                sum((_zeta12_power(-mode * p)[j] for p in pulses), Fraction(0)) / Fraction(n_order)
                for j in range(4)
            )
            coeffs_by_mode[mode] = (val[0], val[1], val[2], val[3])
        v_hat_3 = coeffs_by_mode[m_mode][0]
        require(all(coeffs_by_mode[m][j] == 0 for m in range(n_order) for j in (1, 2, 3)), "unexpected non-rational cyclotomic part")
        nonzero = [m for m in range(n_order) if coeffs_by_mode[m][0] != 0]
        freq_e = sum((coeffs_by_mode[m][0] ** 2 for m in range(n_order)), Fraction(0))
        time_e = Fraction(len(pulses), n_order)
        require(freq_e == time_e, "Z12 Parseval mismatch")
        return {
            "v_hat_3": _pair(v_hat_3),
            "nonzero_modes": nonzero,
            "parseval_exact": _pair(freq_e),
            "overtone_exceeds_nyquist_bound": Fraction(m_mode) > Fraction(n_order, 2 * l_min),
        }

    if operation == "higgs_lhc_rounded_display":
        mass = parse_printed_rational(inputs["mass_GeV"], allow_fraction_slash=False)
        sigma = parse_printed_rational(inputs["sigma_GeV"], allow_fraction_slash=False)
        pred = parse_printed_rational(inputs["prediction_GeV"], allow_fraction_slash=False)
        dec = require_exact_int(inputs["decimals"])
        delta = pred - mass
        z_ex = delta / sigma
        z_rnd = round_rational_half_even(z_ex, dec)
        ape_ex = abs(delta) * Fraction(100) / mass
        ape_rnd = round_rational_half_even(ape_ex, dec)
        return {
            "delta_GeV": _pair(delta),
            "z_score_exact": _pair(z_ex),
            "z_score_rounded_6dp": format_rational_fixed(z_ex, dec),
            "z_score_rounding_residual": _pair(abs(z_rnd - z_ex)),
            "abs_percent_error_rounded_6dp": format_rational_fixed(ape_ex, dec),
            "abs_percent_error_rounding_residual": _pair(abs(ape_rnd - ape_ex)),
        }

    if operation == "printed_token_half_ulp_enclosure":
        tok = inputs["printed_token"]
        require(isinstance(tok, str) and "." in tok, "decimal printed_token required")
        dec_places = len(tok.split(".", 1)[1])
        val = parse_printed_rational(tok, allow_fraction_slash=False)
        half_ulp = Fraction(1, 2 * (10**dec_places))
        return {
            "decimal_places": dec_places,
            "value": _pair(val),
            "half_ulp_bound": _pair(half_ulp),
            "enclosure_lower": _pair(val - half_ulp),
            "enclosure_upper": _pair(val + half_ulp),
        }

    raise ValueError(f"unsupported vector operation: {operation!r}")


def _verify_reject_vector(operation: str, inputs: dict[str, object], expected_error_class: str) -> None:
    if operation == "typed_reject_float_operand":
        require(expected_error_class == "TypeError", "RC-021 expects TypeError")
        json_text = str(inputs["json_float_text"])
        rejected_json = False
        try:
            loads_zero_float(json_text)
        except ValueError:
            rejected_json = True
        require(rejected_json, "loads_zero_float failed to reject JSON float literal")

        # Synthesize runtime Python float via stdlib json.loads without float() or float literals.
        runtime_float = json.loads(str(inputs["decimal_token_for_runtime_float"]))
        for fn in (require_exact_int, parse_exact_int, parse_printed_rational, canonical_rational_pair, require_no_floats):
            caught = False
            try:
                fn(runtime_float)
            except TypeError:
                caught = True
            require(caught, f"{fn.__name__} failed to reject Python float with TypeError")
        return

    if operation == "typed_reject_bool_as_int":
        require(expected_error_class == "TypeError", "RC-022 expects TypeError")
        operand = inputs["bool_operand"]
        require(isinstance(operand, bool), "RC-022 requires JSON bool operand")
        for fn in (require_exact_int, parse_exact_int, canonical_rational_pair):
            caught = False
            try:
                fn(operand)
            except TypeError:
                caught = True
            require(caught, f"{fn.__name__} failed to reject bool with TypeError")
        return

    if operation == "typed_reject_nonfinite_and_malformed_tokens":
        require(expected_error_class == "ValueError", "RC-023 expects ValueError")
        tokens = inputs["bad_tokens"]
        require(isinstance(tokens, list) and bool(tokens), "RC-023 requires non-empty bad_tokens")
        for tok in tokens:
            caught = False
            try:
                parse_printed_rational(tok)
            except ValueError:
                caught = True
            require(caught, f"parse_printed_rational failed to reject malformed token {tok!r}")
        return

    raise ValueError(f"unsupported REJECT vector operation: {operation!r}")


def load_vector_file(path: Path) -> tuple[str, list[dict[str, object]]]:
    """Load and validate a zero-float JSONL golden vector file."""
    require(path.is_file() and not path.is_symlink(), f"vector file missing or symlink: {path.name}")
    raw_bytes = path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    records: list[dict[str, object]] = []
    for lineno, line in enumerate(raw_bytes.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parsed = loads_zero_float(line)
        require_no_floats(parsed, path=f"{path.name}:L{lineno}")
        validate_vector_record(parsed)
        require(isinstance(parsed, dict), f"line {lineno} in {path.name} must be a JSON object")
        records.append(parsed)
    return digest, records


def _exact_typed_equal(
    actual: object,
    expected: object,
    *,
    path: str = "$",
) -> tuple[bool, str]:
    """Recursively compare JSON-compatible values with strict runtime type equality.

    Requires ``type(actual) is type(expected)`` before any value comparison so
    Python's ``bool``/``int`` equality coercion (``True == 1``, ``False == 0``)
    is strictly rejected in both directions.
    """
    if type(actual) is not type(expected):
        return (
            False,
            f"type mismatch at {path}: actual={actual!r} ({type(actual).__name__}), "
            f"expected={expected!r} ({type(expected).__name__})",
        )
    if isinstance(actual, dict) and isinstance(expected, dict):
        for k in actual.keys():
            if type(k) is not str:
                return (
                    False,
                    f"non-string dict key at {path}: actual key={k!r} ({type(k).__name__})",
                )
        for k in expected.keys():
            if type(k) is not str:
                return (
                    False,
                    f"non-string dict key at {path}: expected key={k!r} ({type(k).__name__})",
                )
        actual_keys = set(actual.keys())
        expected_keys = set(expected.keys())
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            return (
                False,
                f"dict key mismatch at {path}: missing={missing!r}, extra={extra!r}",
            )
        for key in sorted(expected_keys):
            ok, detail = _exact_typed_equal(
                actual[key],
                expected[key],
                path=f"{path}.{key}",
            )
            if not ok:
                return (False, detail)
        return (True, "")
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return (
                False,
                f"list length mismatch at {path}: actual_len={len(actual)}, expected_len={len(expected)}",
            )
        for idx, (a_item, e_item) in enumerate(zip(actual, expected)):
            ok, detail = _exact_typed_equal(a_item, e_item, path=f"{path}[{idx}]")
            if not ok:
                return (False, detail)
        return (True, "")
    if actual is None or isinstance(actual, (bool, int, str)):
        if actual != expected:
            return (
                False,
                f"value mismatch at {path}: actual={actual!r} ({type(actual).__name__}), "
                f"expected={expected!r} ({type(expected).__name__})",
            )
        return (True, "")
    return (
        False,
        f"unsupported exact comparison type at {path}: {type(actual).__name__}",
    )


def _strip_typst_comments_and_strings(text: str) -> str:
    """Strip Typst line comments, nested block comments, and double-quoted strings."""
    out: list[str] = []
    i = 0
    n = len(text)
    block_depth = 0
    in_string = False
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if block_depth > 0:
            if ch == "/" and nxt == "*":
                block_depth += 1
                i += 2
            elif ch == "*" and nxt == "/":
                block_depth -= 1
                i += 2
            else:
                if ch == "\n":
                    out.append("\n")
                i += 1
            continue
        if in_string:
            if ch == "\\" and i + 1 < n:
                i += 2
            elif ch == '"':
                in_string = False
                i += 1
            else:
                if ch == "\n":
                    out.append("\n")
                i += 1
            continue
        if ch == "\\" and nxt in ('"', "\\", "/", "<", ">"):
            i += 2
            continue
        if ch == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            block_depth = 1
            i += 2
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def validate_source_binding(repo_root: Path, source_binding: str) -> None:
    """Validate every ``;``-separated ``path[#selector]`` component in ``source_binding``."""
    require(
        isinstance(source_binding, str) and bool(source_binding) and source_binding == source_binding.strip(),
        f"source_binding must be a non-empty trimmed string: {source_binding!r}",
    )
    root = Path(repo_root).resolve()

    for comp in source_binding.split(";"):
        require(
            bool(comp) and comp == comp.strip(),
            f"empty or whitespace-padded source_binding component in {source_binding!r}",
        )
        require(
            comp.count("#") <= 1,
            f"multiple '#' selectors forbidden in source_binding component: {comp!r}",
        )
        rel_path, has_hash, selector = comp.partition("#")
        require(bool(rel_path), f"missing relative path in source_binding component: {comp!r}")
        require("\\" not in rel_path, f"backslash forbidden in source_binding path: {rel_path!r}")
        require(
            not rel_path.startswith("/") and _WIN_DRIVE_RE.match(rel_path) is None,
            f"absolute path forbidden in source_binding: {rel_path!r}",
        )
        raw_parts = rel_path.split("/")
        require(
            all(part not in ("", ".", "..") for part in raw_parts),
            f"unsafe relative path segment in source_binding: {rel_path!r}",
        )
        if has_hash:
            require(bool(selector), f"empty selector after '#' in source_binding: {comp!r}")

        cur = root
        for part in raw_parts[:-1]:
            cur = cur / part
            require(not cur.is_symlink(), f"symlink parent forbidden in source_binding: {rel_path!r}")
            require(cur.is_dir(), f"source_binding parent directory missing: {rel_path!r}")
        target = cur / raw_parts[-1]
        require(not target.is_symlink(), f"symlink target forbidden in source_binding: {rel_path!r}")
        require(target.is_file(), f"source_binding target file missing: {rel_path!r}")
        try:
            target.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError(f"source_binding escapes repo_root: {rel_path!r}") from exc

        if not has_hash:
            continue

        suffix = target.suffix
        if suffix == ".typ":
            require(
                _TYPST_LABEL_RE.fullmatch(selector) is not None,
                f"invalid Typst label selector {selector!r} in {comp!r}",
            )
            stripped = _strip_typst_comments_and_strings(target.read_text(encoding="utf-8"))
            label_re = r"(?<!<)<" + re.escape(selector) + r">(?!>)"
            require(
                re.search(label_re, stripped) is not None,
                f"defining Typst label <{selector}> not found in {rel_path}",
            )
        elif suffix == ".py":
            text = target.read_text(encoding="utf-8")
            line_match = _PY_LINE_RANGE_RE.fullmatch(selector)
            if line_match is not None:
                start = int(line_match.group(1))
                end = int(line_match.group(2))
                line_count = len(text.splitlines())
                require(
                    1 <= start <= end <= line_count,
                    f"Python line range {selector!r} out of bounds for {rel_path} (1..{line_count})",
                )
            elif _PY_FUNC_NAME_RE.fullmatch(selector) is not None:
                try:
                    tree = ast.parse(text, filename=rel_path)
                except SyntaxError as exc:
                    raise ValueError(
                        f"failed to parse Python source_binding {rel_path}: {exc.msg}"
                    ) from exc
                top_funcs = {
                    node.name
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                require(
                    selector in top_funcs,
                    f"top-level function {selector!r} not found in {rel_path}",
                )
            else:
                raise ValueError(f"unsupported Python selector {selector!r} in {comp!r}")
        elif suffix == ".json":
            doc = loads_zero_float(target.read_text(encoding="utf-8"))
            segments = selector.split(".")
            require(
                all(bool(seg) for seg in segments),
                f"empty JSON key segment in selector {selector!r} for {rel_path}",
            )
            cur_obj: object = doc
            for seg in segments:
                require(
                    isinstance(cur_obj, dict) and seg in cur_obj,
                    f"JSON key path {selector!r} missing segment {seg!r} in {rel_path}",
                )
                cur_obj = cur_obj[seg]
        elif suffix == ".csv":
            with target.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            row_match = _CSV_ROW_RE.fullmatch(selector)
            if row_match is not None:
                idx = int(row_match.group(1))
                token = row_match.group(2)
                require(
                    0 <= idx < len(rows),
                    f"CSV row selector {selector!r} out of bounds for {rel_path} (rows={len(rows)})",
                )
                if token is not None:
                    require(
                        any(isinstance(val, str) and val == token for val in rows[idx].values()),
                        f"CSV row {idx} in {rel_path} does not contain token {token!r}",
                    )
            else:
                require(
                    any(
                        isinstance(val, str) and val == selector
                        for row in rows
                        for val in row.values()
                    ),
                    f"CSV cell token {selector!r} not found in {rel_path}",
                )
        else:
            raise ValueError(
                f"unsupported source_binding selector suffix {suffix!r} in {comp!r}"
            )


def verify_single_vector(
    record: dict[str, object],
    *,
    repo_root: Path | None = None,
) -> None:
    """Validate and execute one golden vector record against its exact oracle."""
    validate_vector_record(record)
    effective_root = (
        Path(__file__).resolve().parents[2]
        if repo_root is None
        else Path(repo_root).resolve()
    )
    operation = str(record["operation"])
    inputs = record["inputs"]
    require(isinstance(inputs, dict), "vector inputs must be a dict")
    expected = record["expected_outcome"]
    require(isinstance(expected, dict), "expected_outcome must be a dict")

    if expected["status"] == "REJECT":
        _verify_reject_vector(operation, inputs, str(expected["expected_error_class"]))
    else:
        actual = _eval_operation(operation, inputs)
        require_no_floats(actual, path=f"vector.{record['case_id']}")
        ok, detail = _exact_typed_equal(actual, expected["exact_value"])
        require(ok, f"vector {record['case_id']} ({operation}) mismatch: {detail}")

    validate_source_binding(effective_root, str(record["source_binding"]))


def verify_all_vectors(repo_root: Path) -> dict[str, object]:
    """Load and execute all 30 golden vectors (24 rational_core + 6 symbolic_and_display)."""
    root = Path(repo_root).resolve()
    rc_sha, rc_rows = load_vector_file(root / RATIONAL_CORE_REL)
    sd_sha, sd_rows = load_vector_file(root / SYMBOLIC_DISPLAY_REL)

    require(len(rc_rows) == 24, f"expected 24 rational_core vectors, got {len(rc_rows)}")
    require(len(sd_rows) == 6, f"expected 6 symbolic_and_display vectors, got {len(sd_rows)}")

    rc_ids = [str(r["case_id"]) for r in rc_rows]
    sd_ids = [str(r["case_id"]) for r in sd_rows]
    require(rc_ids == [f"RC-{i:03d}" for i in range(1, 25)], f"unexpected rational_core IDs: {rc_ids}")
    require(sd_ids == [f"SD-{i:03d}" for i in range(1, 7)], f"unexpected symbolic_and_display IDs: {sd_ids}")

    failures: list[dict[str, str]] = []
    passed = 0
    for rec in (*rc_rows, *sd_rows):
        cid = str(rec["case_id"])
        try:
            verify_single_vector(rec, repo_root=root)
            passed += 1
        except (ValueError, TypeError, KeyError, ZeroDivisionError, OSError) as exc:
            failures.append({"case_id": cid, "error": str(exc)})

    total = len(rc_rows) + len(sd_rows)
    return {
        "status": "PASS" if not failures else "FAIL",
        "rational_core_count": len(rc_rows),
        "symbolic_and_display_count": len(sd_rows),
        "total_vectors": total,
        "passed_vectors": passed,
        "failed_vectors": len(failures),
        "file_digests": {
            RATIONAL_CORE_REL: rc_sha,
            SYMBOLIC_DISPLAY_REL: sd_sha,
        },
        "failures": failures,
    }
