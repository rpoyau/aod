"""Tier-2 pure zero-float (int / Fraction) data verifiers for Sectors 10-15.

All arithmetic uses exclusively exact ``int`` and ``fractions.Fraction``.
Every frozen file pinned in ``contracts/scientific/CANONICAL_BINDINGS.json``
has its SHA-256 verified before arithmetic checks run.
"""
from __future__ import annotations

import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

from manual.engine.numeric import (
    canonical_rational_str,
    exact_isclose,
    format_rational_fixed,
    parse_exact_int,
    parse_printed_rational,
    require,
    round_rational_half_even,
)
from manual.engine.registry import SectorSpec

_CLOSURE_BAND_VALUES: dict[str, int] = {"C6": 18, "C8": 24, "C10": 27}
_HIGGS_QUARANTINE_SUBSTRINGS: tuple[str, ...] = ("gev", "mass", "prediction")

_SHEDDING_ETA = Fraction(41, 50)
_SHEDDING_GAMMA = Fraction(11, 20)
_SHEDDING_LAMBDA = Fraction(19, 50)
_SHEDDING_TOL = Fraction(1, 10**12)
_SHEDDING_FIELDS: tuple[str, ...] = (
    "tick",
    "lead",
    "lag",
    "span",
    "compatibility",
    "padar_burden",
    "shed_excess",
    "outward_shedding",
    "local_reclosure",
    "state",
)

_SPARC_GALAXY_ORDER: tuple[str, ...] = (
    "NGC2403",
    "NGC3198",
    "NGC6503",
    "NGC2841",
    "DDO154",
)
_SPARC_UPSILON_D = Fraction(1, 2)
_SPARC_UPSILON_B = Fraction(7, 10)
_SPARC_K_EXT_U = Fraction(8, 1)
_SPARC_INHERITED_TOL = Fraction(1, 10**9)

_BROWNIAN_OCTANT_PATTERNS: dict[int, str] = {
    0: "(+,+,+)",
    1: "(+,+,-)",
    2: "(+,-,+)",
    3: "(+,-,-)",
    4: "(-,+,+)",
    5: "(-,+,-)",
    6: "(-,-,+)",
    7: "(-,-,-)",
}

_LENSING_CLASSES: tuple[str, ...] = (
    "caustic_pair",
    "exoshedding_deflection",
    "open_loss_scatter",
    "weak_refraction",
    "straight",
    "hinge_slide",
    "chiral_flip",
)


def _load_frozen_bindings(repo_root: Path) -> dict[str, str]:
    path = repo_root / "contracts" / "scientific" / "CANONICAL_BINDINGS.json"
    require(path.is_file() and not path.is_symlink(), "CANONICAL_BINDINGS.json missing")
    doc = json.loads(path.read_text(encoding="utf-8"))
    frozen = doc.get("frozen_sha256")
    require(isinstance(frozen, dict) and len(frozen) == 172, "unexpected CANONICAL_BINDINGS frozen_sha256 map")
    return {str(k): str(v) for k, v in frozen.items()}


def _sha256_file(repo_root: Path, rel_path: str) -> str:
    rel = Path(rel_path)
    require(not rel.is_absolute() and ".." not in rel.parts, f"unsafe relative path: {rel_path}")
    target = repo_root / rel
    require(target.is_file() and not target.is_symlink(), f"missing or symlink input: {rel_path}")
    return hashlib.sha256(target.read_bytes()).hexdigest()


def _verify_input_digests(
    repo_root: Path,
    input_paths: tuple[str, ...],
    *,
    require_all_frozen: bool = True,
) -> dict[str, str]:
    frozen = _load_frozen_bindings(repo_root)
    digests: dict[str, str] = {}
    for rel in sorted(input_paths):
        actual = _sha256_file(repo_root, rel)
        if rel in frozen:
            require(
                actual == frozen[rel],
                f"frozen SHA-256 mismatch for {rel}: actual={actual}, pinned={frozen[rel]}",
            )
        elif require_all_frozen:
            raise ValueError(f"consumed Tier-2 file missing from CANONICAL_BINDINGS frozen_sha256: {rel}")
        digests[rel] = actual
    return digests


def _read_csv_exact(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require(reader.fieldnames is not None, f"CSV missing header: {path.name}")
        header = list(reader.fieldnames)
        rows: list[dict[str, str]] = []
        for idx, row in enumerate(reader):
            require(None not in row, f"extra CSV columns at row {idx} in {path.name}")
            require(
                all(val is not None for val in row.values()),
                f"missing CSV cell at row {idx} in {path.name}",
            )
            rows.append(dict(row))
    return header, rows


def _int_balance(n: int, k: int) -> list[int]:
    base, rem = divmod(n, k)
    return [base + (1 if idx < rem else 0) for idx in range(k)]


def _sign3(val: int) -> int:
    return 1 if val > 0 else (-1 if val < 0 else 0)


def _octant_brownian_msb_x(a: int, b: int, c: int) -> int:
    return (4 if a < 0 else 0) + (2 if b < 0 else 0) + (1 if c < 0 else 0)


def _octant_run_tumble_lsb_x(x: int, y: int, z: int) -> int:
    return (1 if x < 0 else 0) + (2 if y < 0 else 0) + (4 if z < 0 else 0)


def _parse_rotmod_exact(path: Path) -> list[tuple[Fraction, ...]]:
    rows: list[tuple[Fraction, ...]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        vals = tuple(
            parse_printed_rational(tok, name="rotmod", allow_fraction_slash=False)
            for tok in parts[:8]
        )
        rows.append(vals)
    return rows


# ---------------------------------------------------------------------------
# Sector 10: dec_ledger
# ---------------------------------------------------------------------------

def verify_dec_ledger(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Verify all 4 frozen D.E.C. fixture CSVs with zero exact residual."""
    root = Path(repo_root).resolve()
    digests = _verify_input_digests(root, spec.input_paths, require_all_frozen=True)

    # 1. dec_one_node_ledger_example.csv
    h1, r1 = _read_csv_exact(root / "manual/data/dec/dec_one_node_ledger_example.csv")
    require(len(h1) == 8 and len(r1) == 4, "dec_one_node_ledger_example.csv shape mismatch")
    state_to_route = {1: "outgoing", -1: "returned", 0: "hinge"}
    admissible_weights: list[int] = []
    neighbors_seen: set[tuple[int, int, int, int]] = set()
    for row in r1:
        adm = parse_exact_int(row["admissible"], name="admissible")
        wt = parse_exact_int(row["weight"], name="weight")
        st = parse_exact_int(row["state"], name="state", allow_leading_plus=True)
        require(adm in (0, 1) and wt >= 0, "invalid admissible/weight in one_node_ledger")
        require(st in state_to_route and row["route"] == state_to_route[st], "state/route mismatch in one_node_ledger")
        nbr_text = row["neighbor"].strip()
        require(nbr_text.startswith("(") and nbr_text.endswith(")"), f"invalid neighbor tuple: {nbr_text!r}")
        coords = tuple(parse_exact_int(tok, name="neighbor_coord") for tok in nbr_text[1:-1].split(","))
        require(
            len(coords) == 4 and all(c in (0, 1) for c in coords) and sum(coords) == 1,
            f"neighbor {coords} is not a Q4 basis vector (d_H == 1)",
        )
        neighbors_seen.add((coords[0], coords[1], coords[2], coords[3]))
        admissible_weights.append(adm * wt)
    require(len(neighbors_seen) == 4, "one_node_ledger neighbors must be 4 distinct Q4 basis vectors")
    z_one = sum(admissible_weights)
    require(z_one == 8, f"expected Z == 8, got {z_one}")
    probs_one: list[Fraction] = []
    for row, aw in zip(r1, admissible_weights):
        p_rec = parse_printed_rational(row["probability_exact"], name="probability_exact")
        p_exp = Fraction(aw, z_one)
        require(p_rec == p_exp, f"one_node probability mismatch: {p_rec} != {p_exp}")
        probs_one.append(p_rec)
    require(probs_one == [Fraction(1, 8), Fraction(1, 8), Fraction(1, 2), Fraction(1, 4)], "one_node probabilities mismatch")
    require(sum(probs_one, Fraction(0)) == Fraction(1), "one_node probabilities do not sum to 1")

    # 2. dec_hinge_slide_example.csv
    h2, r2 = _read_csv_exact(root / "manual/data/dec/dec_hinge_slide_example.csv")
    require(len(h2) == 5 and len(r2) == 3, "dec_hinge_slide_example.csv shape mismatch")
    slide_weights: list[Fraction] = []
    for row in r2:
        wn = parse_exact_int(row["weight_num"], name="weight_num")
        wd = parse_exact_int(row["weight_den"], name="weight_den")
        require(wd > 0 and wn >= 0, "invalid slide weight")
        require(
            row["route"] in {"returned", "outgoing"},
            f"invalid hinge-slide route spelling (shorthand forbidden): {row['route']!r}",
        )
        slide_weights.append(Fraction(wn, wd))
    z_slide = sum(slide_weights, Fraction(0))
    require(z_slide == Fraction(7), f"expected Z_slide == 7, got {z_slide}")
    p_ret = Fraction(0)
    p_out = Fraction(0)
    probs_slide: list[Fraction] = []
    for row, wt in zip(r2, slide_weights):
        p_rec = parse_printed_rational(row["probability_exact"], name="probability_exact")
        require(p_rec == wt / z_slide, f"hinge-slide probability mismatch: {p_rec} != {wt / z_slide}")
        probs_slide.append(p_rec)
        if row["route"] == "returned":
            p_ret += p_rec
        else:
            p_out += p_rec
    require(probs_slide == [Fraction(3, 7), Fraction(3, 7), Fraction(1, 7)], "hinge-slide probabilities mismatch")
    require(p_ret == Fraction(6, 7) and p_out == Fraction(1, 7), "hinge-slide route probability sums mismatch")

    # 3. field_tunnelling_hinge_slide_window_clip.csv
    h3, r3 = _read_csv_exact(root / "manual/data/dec/field_tunnelling_hinge_slide_window_clip.csv")
    require(len(h3) == 18 and len(r3) == 3, "field_tunnelling_hinge_slide_window_clip.csv shape mismatch")
    tunnel_rows = 0
    probs_tun: list[Fraction] = []
    for row in r3:
        require(parse_exact_int(row["direct_adm"], name="direct_adm") == 0, "direct_adm must be 0 on all rows")
        sw = Fraction(parse_exact_int(row["slide_weight_num"]), parse_exact_int(row["slide_weight_den"]))
        z_t = Fraction(parse_exact_int(row["Z_num"]), parse_exact_int(row["Z_den"]))
        p_t = Fraction(parse_exact_int(row["P_num"]), parse_exact_int(row["P_den"]))
        require(z_t == Fraction(7) and p_t == sw / z_t, "tunnelling normalization mismatch")
        probs_tun.append(p_t)
        is_tun = parse_exact_int(row["is_tunnel_branch"], name="is_tunnel_branch")
        require(is_tun in (0, 1), "is_tunnel_branch must be 0 or 1")
        if is_tun == 1:
            tunnel_rows += 1
            require(row["slide_branch"] == "e3:+1", f"unexpected tunnel branch: {row['slide_branch']!r}")
            rd_val = parse_exact_int(row["RD"], name="RD")
            omega_val = parse_exact_int(row["omega"], name="omega")
            c3_val = parse_exact_int(row["C3"], name="C3")
            rho_val = parse_exact_int(row["rhoD_omega"], name="rhoD_omega")
            pd_val = parse_exact_int(row["pD"], name="pD")
            tc = Fraction(
                parse_exact_int(row["tunnel_contribution_num"]),
                parse_exact_int(row["tunnel_contribution_den"]),
            )
            require(rd_val == 5 and omega_val == 2 and c3_val == 3, "tunnelling RD/omega/C3 mismatch")
            require(rho_val == min(rd_val, omega_val) == 2, "tunnelling rhoD_omega mismatch")
            require(pd_val == c3_val * rho_val == 6, "tunnelling pD mismatch")
            require(tc == p_t * pd_val == Fraction(6, 7), "tunnelling contribution mismatch")
    require(tunnel_rows == 1, f"expected unique tunnel row, found {tunnel_rows}")
    require(probs_tun == [Fraction(3, 7), Fraction(3, 7), Fraction(1, 7)], "tunnelling probabilities mismatch")

    # 4. tau_missing_burden_exact_ratio_patch.csv
    h4, r4 = _read_csv_exact(root / "manual/data/dec/tau_missing_burden_exact_ratio_patch.csv")
    require(len(h4) == 6 and len(r4) == 1, "tau_missing_burden_exact_ratio_patch.csv shape mismatch")
    patch = r4[0]
    require(patch["candidate"] == "1:2:9_yro" and patch["alias"] == "Dimonnanyro", "tau patch identity mismatch")
    ratio_num_den = Fraction(parse_exact_int(patch["missing_num"]), parse_exact_int(patch["missing_den"]))
    ratio_exact = parse_printed_rational(patch["missing_frac_exact"], name="missing_frac_exact")
    ratio_disp = parse_printed_rational(
        patch["missing_fraction_display"], name="missing_fraction_display", allow_fraction_slash=False
    )
    require(
        ratio_num_den == ratio_exact == ratio_disp == Fraction(31, 50),
        "tau missing burden patch must equal exact 31/50 == 0.62",
    )

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": digests,
        "verified_counts": {
            "one_node_rows": len(r1),
            "hinge_slide_rows": len(r2),
            "tunnelling_rows": len(r3),
            "tau_ratio_patch_rows": len(r4),
        },
        "exact_residuals_summary": {
            "max_exact_result_residual": "0",
            "field_roles": {
                "exact_input": ["admissible", "weight", "weight_num", "weight_den", "RD", "omega", "C3"],
                "exact_result": ["probability_exact", "Z", "rhoD_omega", "pD", "tunnel_contribution", "missing_frac_exact"],
            },
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Sector 11: higgs_trace
# ---------------------------------------------------------------------------

def verify_higgs_trace(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Verify Higgs trace selection, target quarantine, freeze map, and LHC rounded display."""
    root = Path(repo_root).resolve()
    digests = _verify_input_digests(root, spec.input_paths, require_all_frozen=True)

    formula_md = (root / "manual/data/higgs/higgs_trace_score_formula.md").read_text(encoding="utf-8")
    require("must not branch on candidate identity" in formula_md, "formula document lost non-branching rule")
    require("if candidate" not in formula_md.lower(), "candidate-override code found in formula doc")

    # 1. Internal candidates selection & target quarantine gate
    h_int, r_int = _read_csv_exact(root / "manual/data/higgs/higgs_trace_internal_candidates_selection.csv")
    require(len(r_int) == 8, f"expected 8 internal Higgs candidates, got {len(r_int)}")
    for col in h_int:
        low = col.lower()
        for forbidden in _HIGGS_QUARANTINE_SUBSTRINGS:
            require(
                forbidden not in low,
                f"Higgs target quarantine breach: column {col!r} contains forbidden token {forbidden!r}",
            )

    scored: list[tuple[Fraction, int, str]] = []
    max_pof_res = Fraction(0)
    for row in r_int:
        cand = row["candidate_K"]
        p = parse_exact_int(row["p"], name="p")
        q = parse_exact_int(row["q"], name="q")
        win_l = parse_exact_int(row["L_window"], name="L_window")
        c3 = parse_exact_int(row["C3_H_scoped"], name="C3_H_scoped")
        require(cand == f"{p}:{q}:{win_l}", f"candidate_K mismatch: {cand!r} vs {p}:{q}:{win_l}")

        pi_val = q**p + q
        rd_val = 2 * pi_val + 1
        rho_val = min(rd_val, win_l)
        pd_val = c3 * rho_val
        qd_val = c3 * max(0, rd_val - win_l)
        require(parse_exact_int(row["Pi_qp_plus_q"]) == pi_val, f"{cand}: Pi mismatch")
        require(parse_exact_int(row["RD_accessor"]) == rd_val, f"{cand}: RD mismatch")
        require(parse_exact_int(row["rhoD_omega"]) == rho_val, f"{cand}: rhoD_omega mismatch")
        require(parse_exact_int(row["PD_window_pressure"]) == pd_val, f"{cand}: PD mismatch")
        require(parse_exact_int(row["QD_pending_overhang"]) == qd_val, f"{cand}: QD mismatch")

        ca_label = row["lower_closure"]
        cb_label = row["upper_closure"]
        require(ca_label in _CLOSURE_BAND_VALUES and cb_label in _CLOSURE_BAND_VALUES, f"{cand}: unknown closure band")
        dl = pd_val - _CLOSURE_BAND_VALUES[ca_label]
        du = pd_val - _CLOSURE_BAND_VALUES[cb_label]
        require(parse_exact_int(row["delta_lower"]) == dl, f"{cand}: delta_lower mismatch")
        require(parse_exact_int(row["delta_upper"]) == du, f"{cand}: delta_upper mismatch")

        is_odd = 1 if win_l % 2 == 1 else 0
        is_saddle = 1 if (dl == 3 and du == -3) else 0
        q_band_ok = 1 if 100 <= qd_val <= 250 else 0
        require(parse_exact_int(row["is_yro_odd_window"]) == is_odd, f"{cand}: is_yro_odd_window mismatch")
        require(parse_exact_int(row["is_saddle_plus3_minus3"]) == is_saddle, f"{cand}: is_saddle mismatch")
        require(parse_exact_int(row["q_band_ok_100_250"]) == q_band_ok, f"{cand}: q_band_ok mismatch")

        d_saddle = abs(dl - 3) + abs(du + 3)
        d_q = 0 if 100 <= qd_val <= 250 else (100 - qd_val if qd_val < 100 else qd_val - 250)
        d_l = abs(win_l - 7)
        d_route = 0 if (win_l == 7 and dl == 3 and du == -3 and 100 <= qd_val <= 250) else 1
        s_h = Fraction(d_saddle, 12) + Fraction(d_q, 100) + Fraction(d_l, 2) + Fraction(d_route, 1)
        rec_sh = parse_printed_rational(row["S_H_trace_internal_selection"], name="S_H", allow_fraction_slash=False)
        require(rec_sh == s_h, f"{cand}: S_H mismatch: recorded={rec_sh}, exact={s_h}")

        pof_exact = Fraction(qd_val, pd_val + qd_val)
        pof_rec = parse_printed_rational(
            row["pending_overhang_fraction_display"], name="pending_overhang_fraction_display", allow_fraction_slash=False
        )
        require(
            pof_rec == round_rational_half_even(pof_exact, 6),
            f"{cand}: pending_overhang_fraction_display rounding mismatch",
        )
        pof_res = abs(pof_rec - pof_exact)
        if pof_res > max_pof_res:
            max_pof_res = pof_res

        rank = parse_exact_int(row["rank"], name="rank")
        scored.append((s_h, rank, cand))

    expected_scores = [
        Fraction(0),
        Fraction(79, 50),
        Fraction(9, 4),
        Fraction(12, 5),
        Fraction(289, 100),
        Fraction(3),
        Fraction(359, 100),
        Fraction(19, 4),
    ]
    require([s for s, _, _ in scored] == expected_scores, "Higgs S_H score sequence mismatch")
    require([rk for _, rk, _ in scored] == list(range(1, 9)), "Higgs rank sequence mismatch")
    min_score = min(s for s, _, _ in scored)
    winners = [cand for s, _, cand in scored if s == min_score]
    require(winners == ["3:3:7"], f"expected unique argmin 3:3:7, got {winners}")

    # 2. Freeze map
    _, r_map = _read_csv_exact(root / "manual/data/higgs/higgs_external_map_after_candidate_freeze.csv")
    require(len(r_map) == 4, f"expected 4 freeze map rows, got {len(r_map)}")
    e_h_mev = 61 * (2 ** (7 + 4))
    e_h_gev = Fraction(e_h_mev, 1000)
    require(e_h_mev == 124928 and e_h_gev == Fraction(15616, 125), "Higgs freeze formula mismatch")
    require(r_map[0]["quantity"] == "K_H_star" and r_map[0]["value"] == "3:3:7_yro", "K_H_star mismatch")
    require(parse_exact_int(r_map[1]["value"]) == e_h_mev and r_map[1]["unit"] == "MeV", "E_H_0 MeV mismatch")
    require(
        parse_printed_rational(r_map[2]["value"], allow_fraction_slash=False) == e_h_gev and r_map[2]["unit"] == "GeV",
        "E_H_0 GeV mismatch",
    )

    # 3. LHC comparison after freeze
    _, r_lhc = _read_csv_exact(root / "manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv")
    require(len(r_lhc) == 4, f"expected 4 LHC comparison rows, got {len(r_lhc)}")
    max_lhc_z_res = Fraction(0)
    max_lhc_ape_res = Fraction(0)
    cms_z_res: Fraction | None = None
    for row in r_lhc:
        mass = parse_printed_rational(row["mass_GeV"], name="mass_GeV", allow_fraction_slash=False)
        sigma = parse_printed_rational(row["sigma_GeV"], name="sigma_GeV", allow_fraction_slash=False)
        pred = parse_printed_rational(row["prediction_GeV"], name="prediction_GeV", allow_fraction_slash=False)
        delta_rec = parse_printed_rational(row["delta_GeV"], name="delta_GeV", allow_fraction_slash=False)
        ape_rec = parse_printed_rational(row["abs_percent_error"], name="abs_percent_error", allow_fraction_slash=False)
        z_rec = parse_printed_rational(row["z_score"], name="z_score", allow_fraction_slash=False)

        require(pred == e_h_gev, f"LHC prediction_GeV mismatch on {row['target_name']}")
        delta_exp = pred - mass
        require(delta_rec == delta_exp, f"LHC delta_GeV exact mismatch on {row['target_name']}")
        ape_exact = abs(delta_exp) * Fraction(100) / mass
        z_exact = delta_exp / sigma
        require(
            ape_rec == round_rational_half_even(ape_exact, 6),
            f"LHC abs_percent_error rounded_display mismatch on {row['target_name']}",
        )
        require(
            z_rec == round_rational_half_even(z_exact, 6),
            f"LHC z_score rounded_display mismatch on {row['target_name']}",
        )
        z_res = abs(z_rec - z_exact)
        ape_res = abs(ape_rec - ape_exact)
        if z_res > max_lhc_z_res:
            max_lhc_z_res = z_res
        if ape_res > max_lhc_ape_res:
            max_lhc_ape_res = ape_res
        if row["target_name"] == "CMS_H_to_4l_Run2_on_shell":
            cms_z_res = z_res
    require(cms_z_res == Fraction(1, 3000000), f"expected CMS z_score residual 1/3000000, got {cms_z_res}")

    # 4. yro aliases
    _, r_alias = _read_csv_exact(root / "manual/data/higgs/yro_aliases_and_renames.csv")
    require(len(r_alias) == 3, f"expected 3 yro alias rows, got {len(r_alias)}")
    alias_map = {row["row"]: row["alias"] for row in r_alias}
    require(
        alias_map == {
            "1:2:7_yro": "Dimonseptyro",
            "1:2:9_yro": "Dimonnanyro",
            "3:3:7_yro": "Tritrioseptyro",
        },
        f"yro alias map mismatch: {alias_map}",
    )

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": digests,
        "verified_counts": {
            "internal_candidates": len(r_int),
            "freeze_map_rows": len(r_map),
            "lhc_comparison_rows": len(r_lhc),
            "yro_alias_rows": len(r_alias),
        },
        "exact_residuals_summary": {
            "max_exact_result_residual": "0",
            "target_quarantine_enforced": True,
            "unique_argmin": "3:3:7",
            "E_H_0_GeV_exact": canonical_rational_str(e_h_gev),
            "cms_z_score_rounded_display_residual": canonical_rational_str(cms_z_res),
            "max_lhc_z_score_rounded_display_residual": canonical_rational_str(max_lhc_z_res),
            "max_lhc_abs_percent_error_rounded_display_residual": canonical_rational_str(max_lhc_ape_res),
            "max_pending_overhang_rounded_display_residual": canonical_rational_str(max_pof_res),
            "field_roles": {
                "exact_input": ["p", "q", "L_window", "C3_H_scoped", "mass_GeV", "sigma_GeV"],
                "exact_result": ["Pi_qp_plus_q", "RD_accessor", "rhoD_omega", "PD_window_pressure", "QD_pending_overhang", "delta_lower", "delta_upper", "S_H_trace_internal_selection", "prediction_GeV", "delta_GeV"],
                "rounded_display": ["pending_overhang_fraction_display", "abs_percent_error", "z_score"],
            },
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Sector 12: phase_delta3_3d
# ---------------------------------------------------------------------------

def verify_phase_delta3_3d(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Verify Brownian (MSB-x) and run-tumble (LSB-x) 3D phase-cycle delta_3 fixtures with zero residual."""
    root = Path(repo_root).resolve()
    digests = _verify_input_digests(root, spec.input_paths, require_all_frozen=True)

    # --- Brownian (MSB-x octant convention) ---
    _, b_track = _read_csv_exact(root / "manual/data/brownian/brownian_sample_track.csv")
    _, b_disp = _read_csv_exact(root / "manual/data/brownian/brownian_displacements.csv")
    _, b_qcnt = _read_csv_exact(root / "manual/data/brownian/displacement_q_counts.csv")
    _, b_phase = _read_csv_exact(root / "manual/data/brownian/phase_cycle_delta3.csv")
    _, b_oct = _read_csv_exact(root / "manual/data/brownian/octant_delta3.csv")
    _, b_ratios = _read_csv_exact(root / "manual/data/brownian/integer_motion_ratios.csv")

    require(len(b_track) == 9 and len(b_disp) == 8, "Brownian track/displacement row counts mismatch")
    pts = [
        (
            row["track_id"],
            parse_exact_int(row["t"]),
            parse_exact_int(row["x"]),
            parse_exact_int(row["y"]),
            parse_exact_int(row["z"]),
        )
        for row in b_track
    ]
    beta_a = 5
    q_counts: dict[int, int] = {}
    phase_counts = {theta: 0 for theta in range(beta_a)}
    oct_counts = {q: 0 for q in range(8)}
    sum_q = 0
    sum_x = 0
    sum_y = 0
    sum_z = 0
    for idx, row in enumerate(b_disp):
        tid0, t0, x0, y0, z0 = pts[idx]
        _, t1, x1, y1, z1 = pts[idx + 1]
        a, b_val, c = x1 - x0, y1 - y0, z1 - z0
        qval = a * a + b_val * b_val + c * c
        theta = qval % beta_a
        oct_id = _octant_brownian_msb_x(a, b_val, c)
        require(row["track_id"] == tid0 and parse_exact_int(row["i"]) == idx and parse_exact_int(row["lag_n"]) == 1, "Brownian index mismatch")
        require(
            (parse_exact_int(row["t0"]), parse_exact_int(row["t1"])) == (t0, t1)
            and (parse_exact_int(row["X0"]), parse_exact_int(row["Y0"]), parse_exact_int(row["Z0"])) == (x0, y0, z0)
            and (parse_exact_int(row["X1"]), parse_exact_int(row["Y1"]), parse_exact_int(row["Z1"])) == (x1, y1, z1),
            f"Brownian endpoints mismatch at i={idx}",
        )
        require(
            (parse_exact_int(row["a"]), parse_exact_int(row["b"]), parse_exact_int(row["c"])) == (a, b_val, c)
            and parse_exact_int(row["Q"]) == qval
            and parse_exact_int(row["theta"]) == theta
            and parse_exact_int(row["octant"]) == oct_id
            and row["octant_pattern"] == _BROWNIAN_OCTANT_PATTERNS[oct_id],
            f"Brownian displacement derived fields mismatch at i={idx}",
        )
        q_counts[qval] = q_counts.get(qval, 0) + 1
        phase_counts[theta] += 1
        oct_counts[oct_id] += 1
        sum_q += qval
        sum_x += a * a
        sum_y += b_val * b_val
        sum_z += c * c

    max_q = max(q_counts)
    require(len(b_qcnt) == max_q + 1, "Brownian displacement_q_counts length mismatch")
    for qv, row in enumerate(b_qcnt):
        require(
            parse_exact_int(row["lag_n"]) == 1
            and parse_exact_int(row["Q"]) == qv
            and parse_exact_int(row["observed_count"]) == q_counts.get(qv, 0),
            f"Brownian q_count mismatch at Q={qv}",
        )

    b_phase_comp = _int_balance(len(b_disp), beta_a)
    require(len(b_phase) == beta_a, "Brownian phase_cycle_delta3 row count mismatch")
    b_phase_dz_sum = 0
    for theta, row in enumerate(b_phase):
        obs = phase_counts[theta]
        comp = b_phase_comp[theta]
        dz = comp - obs
        b_phase_dz_sum += dz
        require(
            parse_exact_int(row["lag_n"]) == 1
            and parse_exact_int(row["beta_a"]) == beta_a
            and parse_exact_int(row["theta"]) == theta
            and parse_exact_int(row["observed_count"]) == obs
            and parse_exact_int(row["comparator_count"]) == comp
            and parse_exact_int(row["DeltaZ"]) == dz
            and parse_exact_int(row["s3"]) == _sign3(dz)
            and parse_exact_int(row["m"]) == abs(dz),
            f"Brownian phase_cycle_delta3 mismatch at theta={theta}",
        )
    require(b_phase_dz_sum == 0, "Brownian phase DeltaZ sum must be 0")

    b_oct_comp = _int_balance(len(b_disp), 8)
    require(len(b_oct) == 8, "Brownian octant_delta3 row count mismatch")
    b_oct_dz_sum = 0
    for q_id, row in enumerate(b_oct):
        obs = oct_counts[q_id]
        comp = b_oct_comp[q_id]
        dz = comp - obs
        b_oct_dz_sum += dz
        require(
            parse_exact_int(row["lag_n"]) == 1
            and parse_exact_int(row["octant"]) == q_id
            and row["sign_pattern"] == _BROWNIAN_OCTANT_PATTERNS[q_id]
            and parse_exact_int(row["observed_count"]) == obs
            and parse_exact_int(row["comparator_count"]) == comp
            and parse_exact_int(row["DeltaZ"]) == dz
            and parse_exact_int(row["s3"]) == _sign3(dz)
            and parse_exact_int(row["m"]) == abs(dz),
            f"Brownian octant_delta3 mismatch at octant={q_id}",
        )
    require(b_oct_dz_sum == 0, "Brownian octant DeltaZ sum must be 0")

    b_ratio_map = {row["ratio"]: (row["numerator"], parse_exact_int(row["denominator"])) for row in b_ratios}
    require(
        b_ratio_map
        == {
            "R_Q": (str(sum_q), len(b_disp)),
            "R_x": (str(sum_x), sum_q),
            "R_y": (str(sum_y), sum_q),
            "R_z": (str(sum_z), sum_q),
            "R_theta": (":".join(str(phase_counts[t]) for t in range(beta_a)), len(b_disp)),
            "R_oct": (":".join(str(oct_counts[q]) for q in range(8)), len(b_disp)),
        }
        and (sum_q, sum_x, sum_y, sum_z) == (20, 8, 7, 5),
        f"Brownian integer_motion_ratios mismatch: {b_ratio_map}",
    )

    # --- Run-tumble (LSB-x octant convention) ---
    _, rt_trace = _read_csv_exact(root / "manual/data/run_tumble/run_tumble_trace_20_ticks.csv")
    _, rt_phase = _read_csv_exact(root / "manual/data/run_tumble/run_tumble_phase_cycle_delta3.csv")
    _, rt_oct = _read_csv_exact(root / "manual/data/run_tumble/run_tumble_octant_delta3.csv")
    _, rt_ratios = _read_csv_exact(root / "manual/data/run_tumble/run_tumble_integer_motion_ratios.csv")
    rt_tex = (root / "manual/data/run_tumble/run_tumble_trace_table.tex").read_text(encoding="utf-8")

    require(len(rt_trace) == 21, f"expected 21 run_tumble trace rows, got {len(rt_trace)}")
    h_vec = [0, 0, 0, 0]
    rt_phase_counts = {theta: 0 for theta in range(beta_a)}
    rt_oct_counts = {q: 0 for q in range(8)}
    rt_sum_q3 = 0
    rt_sum_q4 = 0
    rt_sx = 0
    rt_sy = 0
    rt_sz = 0
    rt_sh4 = 0
    for idx, row in enumerate(rt_trace):
        t_val = parse_exact_int(row["t"], name="t")
        require(t_val == idx, f"run_tumble tick mismatch at {idx}")
        sigma = parse_exact_int(row["sigma"], name="sigma")
        edge = row["edge"]
        if idx == 0:
            require(row["mode"] == "init" and edge == "-" and sigma == 0, "run_tumble init row mismatch")
        else:
            require(row["mode"] in ("run", "tumble") and edge in ("e1", "e2", "e3", "e4") and sigma in (-1, 1), f"invalid step at t={idx}")
            h_vec[int(edge[1]) - 1] += sigma
        x, y, z = h_vec[0], h_vec[1], h_vec[2]
        q3 = x * x + y * y + z * z
        q4 = sum(v * v for v in h_vec)
        theta = q3 % beta_a
        oct_id = _octant_run_tumble_lsb_x(x, y, z)
        require(
            [parse_exact_int(row[k]) for k in ("h1", "h2", "h3", "h4")] == h_vec
            and (parse_exact_int(row["x"]), parse_exact_int(row["y"]), parse_exact_int(row["z"])) == (x, y, z)
            and parse_exact_int(row["Q3"]) == q3
            and parse_exact_int(row["Q4"]) == q4
            and parse_exact_int(row["theta"]) == theta
            and parse_exact_int(row["octant"]) == oct_id
            and parse_exact_int(row["beta_a"]) == beta_a,
            f"run_tumble derived state mismatch at t={idx}",
        )
        sigma_tex = "--" if idx == 0 else ("+1" if sigma > 0 else "-1")
        h_tex = "(" + ",".join(str(v) for v in h_vec) + ")"
        z_tex = f"({x},{y},{z})"
        tex_line = (
            f"{idx} & {row['mode']} & {edge} & {sigma_tex} & "
            f"\\texttt{{{h_tex}}} & \\texttt{{{z_tex}}} & "
            f"{q3} & {q4} & {theta} & {oct_id}\\\\"
        )
        require(tex_line in rt_tex, f"run_tumble_trace_table.tex missing exact row for t={idx}")
        if idx >= 1:
            rt_phase_counts[theta] += 1
            rt_oct_counts[oct_id] += 1
            rt_sum_q3 += q3
            rt_sum_q4 += q4
            rt_sx += x * x
            rt_sy += y * y
            rt_sz += z * z
            rt_sh4 += h_vec[3] * h_vec[3]

    rt_active_n = len(rt_trace) - 1
    rt_phase_comp = _int_balance(rt_active_n, beta_a)
    require(len(rt_phase) == beta_a, "run_tumble phase_cycle_delta3 length mismatch")
    rt_phase_dz_sum = 0
    for theta, row in enumerate(rt_phase):
        obs = rt_phase_counts[theta]
        comp = rt_phase_comp[theta]
        dz = comp - obs
        rt_phase_dz_sum += dz
        require(
            parse_exact_int(row["beta_a"]) == beta_a
            and parse_exact_int(row["theta"]) == theta
            and parse_exact_int(row["O"]) == obs
            and parse_exact_int(row["O_hat"]) == comp
            and parse_exact_int(row["DeltaZ"]) == dz
            and parse_exact_int(row["s3"]) == _sign3(dz)
            and parse_exact_int(row["m"]) == abs(dz),
            f"run_tumble phase_cycle_delta3 mismatch at theta={theta}",
        )
    require(rt_phase_dz_sum == 0, "run_tumble phase DeltaZ sum must be 0")

    rt_oct_comp = _int_balance(rt_active_n, 8)
    require(len(rt_oct) == 8, "run_tumble octant_delta3 length mismatch")
    rt_oct_dz_sum = 0
    for q_id, row in enumerate(rt_oct):
        obs = rt_oct_counts[q_id]
        comp = rt_oct_comp[q_id]
        dz = comp - obs
        rt_oct_dz_sum += dz
        require(
            parse_exact_int(row["octant"]) == q_id
            and parse_exact_int(row["O"]) == obs
            and parse_exact_int(row["O_hat"]) == comp
            and parse_exact_int(row["DeltaZ"]) == dz
            and parse_exact_int(row["s3"]) == _sign3(dz)
            and parse_exact_int(row["m"]) == abs(dz),
            f"run_tumble octant_delta3 mismatch at octant={q_id}",
        )
    require(rt_oct_dz_sum == 0, "run_tumble octant DeltaZ sum must be 0")

    rt_ratio_map = {
        row["ratio"]: (parse_exact_int(row["numerator"]), parse_exact_int(row["denominator"]))
        for row in rt_ratios
    }
    require(
        rt_ratio_map
        == {
            "R_Q3": (108, 20),
            "R_Q4": (138, 20),
            "R_x": (43, 108),
            "R_y": (35, 108),
            "R_z": (30, 108),
            "R_h4_audit": (30, 138),
        }
        and (rt_sum_q3, rt_sum_q4, rt_sx, rt_sy, rt_sz, rt_sh4) == (108, 138, 43, 35, 30, 30),
        f"run_tumble integer_motion_ratios mismatch: {rt_ratio_map}",
    )

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": digests,
        "verified_counts": {
            "brownian_track_points": len(b_track),
            "brownian_displacements": len(b_disp),
            "run_tumble_trace_rows": len(rt_trace),
            "run_tumble_active_ticks": rt_active_n,
        },
        "exact_residuals_summary": {
            "max_exact_result_residual": "0",
            "brownian_octant_convention": "MSB_x",
            "run_tumble_octant_convention": "LSB_x",
            "field_roles": {
                "exact_input": ["track_coords", "schedule_edge_sigma"],
                "exact_result": ["a", "b", "c", "Q", "Q3", "Q4", "theta", "octant", "DeltaZ", "s3", "m", "integer_motion_ratios"],
            },
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Sector 13: cycle_shedding
# ---------------------------------------------------------------------------

def verify_cycle_shedding(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Verify retained 90-row cycle-shedding CSV and summary TeX using exact Fraction arithmetic."""
    root = Path(repo_root).resolve()
    # Root shedding files are outside CANONICAL_BINDINGS frozen_sha256; hash and verify strictly.
    digests = _verify_input_digests(root, spec.input_paths, require_all_frozen=False)

    csv_path = root / "wavelet_shedding_simulation.csv"
    summary_path = root / "cycle_shedding_summary.tex"
    header, raw_rows = _read_csv_exact(csv_path)
    require(tuple(header) == _SHEDDING_FIELDS, f"unexpected cycle_shedding CSV header: {header}")
    require(len(raw_rows) == 90, f"expected 90 cycle_shedding rows, got {len(raw_rows)}")

    prev_burden = Fraction(0)
    max_abs_res = Fraction(0)
    nonzero_res_cells = 0
    derived_cols = ("span", "padar_burden", "shed_excess", "outward_shedding", "local_reclosure")
    max_col_res: dict[str, Fraction] = {c: Fraction(0) for c in derived_cols}

    max_span = Fraction(0)
    max_burden = Fraction(0)
    max_excess = Fraction(0)
    total_outward = Fraction(0)
    total_local = Fraction(0)

    for tick, row in enumerate(raw_rows):
        require(parse_exact_int(row["tick"], name="tick") == tick, f"tick order mismatch at row {tick}")
        require(row["state"] == "open", f"tick {tick}: retained fixture state must be 'open', got {row['state']!r}")

        lead = parse_printed_rational(row["lead"], name="lead", allow_fraction_slash=False)
        lag = parse_printed_rational(row["lag"], name="lag", allow_fraction_slash=False)
        comp = parse_printed_rational(row["compatibility"], name="compatibility", allow_fraction_slash=False)
        rec = {
            col: parse_printed_rational(row[col], name=col, allow_fraction_slash=False)
            for col in derived_cols
        }
        require(comp >= 0 and all(val >= 0 for val in rec.values()), f"tick {tick}: negative numeric value")

        span_exp = abs(lead - lag)
        before = _SHEDDING_ETA * prev_burden + _SHEDDING_GAMMA * span_exp
        exc_exp = max(Fraction(0), before - comp)
        bur_exp = before - exc_exp
        out_exp = (Fraction(1) - _SHEDDING_LAMBDA) * exc_exp
        loc_exp = _SHEDDING_LAMBDA * exc_exp

        expected_map = {
            "span": span_exp,
            "padar_burden": bur_exp,
            "shed_excess": exc_exp,
            "outward_shedding": out_exp,
            "local_reclosure": loc_exp,
        }
        for col, exp_val in expected_map.items():
            act_val = rec[col]
            require(
                exact_isclose(act_val, exp_val, _SHEDDING_TOL),
                f"tick {tick}: {col} exceeds inherited 1/10^12 bound (residual={abs(act_val - exp_val)})",
            )
            res = abs(act_val - exp_val)
            if res > 0:
                nonzero_res_cells += 1
            if res > max_col_res[col]:
                max_col_res[col] = res
            if res > max_abs_res:
                max_abs_res = res

        require(rec["padar_burden"] <= comp + _SHEDDING_TOL, f"tick {tick}: burden exceeds compatibility + tol")
        require(
            exact_isclose(rec["outward_shedding"] + rec["local_reclosure"], exc_exp, _SHEDDING_TOL),
            f"tick {tick}: outward + local != shed_excess within inherited bound",
        )

        if rec["span"] > max_span:
            max_span = rec["span"]
        if rec["padar_burden"] > max_burden:
            max_burden = rec["padar_burden"]
        if rec["shed_excess"] > max_excess:
            max_excess = rec["shed_excess"]
        total_outward += rec["outward_shedding"]
        total_local += rec["local_reclosure"]
        prev_burden = rec["padar_burden"]

    summary_text = summary_path.read_text(encoding="utf-8")
    expected_summary = {
        "Ticks": "90",
        "Maximum lead-lag span": format_rational_fixed(max_span, 3),
        "Maximum temporal SADAR burden": format_rational_fixed(max_burden, 3),
        "Maximum sheddic excess": format_rational_fixed(max_excess, 3),
        "Total exoshedding": format_rational_fixed(total_outward, 3),
        "Total local reclosure": format_rational_fixed(total_local, 3),
        "Sheddic path trigger ticks": "0",
        "First reclosure tick": "none",
    }
    for label, exp_str in expected_summary.items():
        found = re.findall(rf"(?m)^{re.escape(label)}\s*&\s*([^\\\n]+)\\\\\s*$", summary_text)
        require(
            [item.strip() for item in found] == [exp_str],
            f"cycle_shedding_summary.tex mismatch for {label!r}: found={found!r}, expected={[exp_str]!r}",
        )

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": digests,
        "verified_counts": {
            "simulation_rows": len(raw_rows),
            "open_state_rows": len(raw_rows),
            "summary_table_entries": len(expected_summary),
            "nonzero_legacy_float_cells": nonzero_res_cells,
        },
        "exact_residuals_summary": {
            "inherited_bound": canonical_rational_str(_SHEDDING_TOL),
            "max_abs_residual": canonical_rational_str(max_abs_res),
            "per_column_max_abs_residual": {
                col: canonical_rational_str(val) for col, val in sorted(max_col_res.items())
            },
            "nonzero_residual_cells_of_450": nonzero_res_cells,
            "summary_values_3dp": expected_summary,
            "field_roles": {
                "exact_input": ["tick", "lead", "lag", "compatibility"],
                "exact_result": ["state"],
                "retained_legacy_float_record": list(derived_cols),
                "rounded_display": ["cycle_shedding_summary.tex_3dp_metrics"],
            },
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Sector 14: lensing_tallies
# ---------------------------------------------------------------------------

def verify_lensing_tallies(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Verify all 12 frozen lensing files and SPARC-5 bin-count cross-checks in exact arithmetic."""
    root = Path(repo_root).resolve()
    digests = _verify_input_digests(root, spec.input_paths, require_all_frozen=True)

    # 1. k4_3d_timeflow_input_gate.csv
    _, r_k4 = _read_csv_exact(root / "manual/data/lensing/k4_3d_timeflow_input_gate.csv")
    require(len(r_k4) == 9, f"expected 9 K4 gate rows, got {len(r_k4)}")
    group_counts: dict[str, int] = {}
    quarantined_target_rows = 0
    for row in r_k4:
        grp = row["input_group"]
        group_counts[grp] = group_counts.get(grp, 0) + 1
        require(row["release_gate"] == "required before K4 release", f"K4 release gate mismatch: {row}")
        if grp == "lensing target side":
            require(row["source_status"] == "quarantined target side", "K4 lensing target side not quarantined")
            quarantined_target_rows += 1
    require(len(group_counts) == 6, f"expected 6 K4 input groups, got {len(group_counts)}")
    require(sorted(group_counts.values(), reverse=True) == [2, 2, 2, 1, 1, 1], f"unexpected K4 group counts: {group_counts}")
    require(quarantined_target_rows == 2, f"expected 2 quarantined K4 target rows, got {quarantined_target_rows}")

    # 2. Toy-1 tallies & verification checks
    _, r_t1 = _read_csv_exact(root / "manual/data/lensing/toy1_delta3_class_tallies.csv")
    _, r_t1c = _read_csv_exact(root / "manual/data/lensing/toy1_verification_checks.csv")
    require(len(r_t1) == 7 and len(r_t1c) == 11, "Toy-1 row counts mismatch")
    t1_sum_t = 0
    t1_sum_o = 0
    t1_sum_m = 0
    for row in r_t1:
        t_v = parse_exact_int(row["T_cross_predicted_tally"])
        o_v = parse_exact_int(row["O_fixture_tally"])
        dz = parse_exact_int(row["deltaZ"])
        s3 = parse_exact_int(row["s3"])
        m = parse_exact_int(row["m"])
        require(dz == t_v - o_v == 0 and s3 == 0 and m == 0, f"Toy-1 delta3 nonzero: {row}")
        t1_sum_t += t_v
        t1_sum_o += o_v
        t1_sum_m += m
    require(t1_sum_t == 18 and t1_sum_o == 18 and t1_sum_m == 0, "Toy-1 totals mismatch")
    require(all(row["passed"] == "True" for row in r_t1c), "Toy-1 verification checks not all True")

    # 3. SPARC-5 lensing class tallies & medium diagnostic summary cross-checked vs rotmod
    _, r_s5_cls = _read_csv_exact(root / "manual/data/lensing/sparc5_lensing_class_tallies.csv")
    _, r_s5_med = _read_csv_exact(root / "manual/data/lensing/sparc5_medium_diagnostic_summary.csv")
    require(len(r_s5_cls) == 5 and len(r_s5_med) == 5, "SPARC-5 lensing row counts mismatch")
    cls_by_gal = {row["galaxy"]: row for row in r_s5_cls}
    med_by_gal = {row["galaxy"]: row for row in r_s5_med}
    require(set(cls_by_gal.keys()) == set(med_by_gal.keys()) == set(_SPARC_GALAXY_ORDER), "SPARC-5 galaxy set mismatch")

    expected_events = {"NGC2403": 44, "NGC3198": 44, "NGC6503": 44, "NGC2841": 41, "DDO154": 46}
    for gal in _SPARC_GALAXY_ORDER:
        crow = cls_by_gal[gal]
        mrow = med_by_gal[gal]
        counts = {c: parse_exact_int(crow[c], name=f"{gal}.{c}") for c in _LENSING_CLASSES}
        total_events = sum(counts.values())
        require(total_events == parse_exact_int(mrow["events"]) == expected_events[gal], f"{gal}: events mismatch")
        require(parse_exact_int(mrow["caustic_bins_count"]) == counts["caustic_pair"], f"{gal}: caustic count mismatch")
        max_cnt = max(counts.values())
        top_classes = [c for c, v in counts.items() if v == max_cnt]
        require(top_classes == ["exoshedding_deflection"] and mrow["dominant_class"] == "exoshedding_deflection", f"{gal}: dominant class mismatch")
        rotmod_bins = len(_parse_rotmod_exact(root / f"manual/data/sparc/{gal}_rotmod.dat"))
        require(parse_exact_int(mrow["SPARC_bins_total"]) == rotmod_bins, f"{gal}: SPARC_bins_total != rotmod bin count")
        med_da = parse_printed_rational(mrow["median_abs_ΔAγ"], name="median_abs_ΔAγ", allow_fraction_slash=False)
        max_da = parse_printed_rational(mrow["max_abs_ΔAγ"], name="max_abs_ΔAγ", allow_fraction_slash=False)
        require(Fraction(0) < med_da <= max_da, f"{gal}: invalid ΔAγ ordering")

    # 4. SWELLS K0 target tallies
    _, r_k0 = _read_csv_exact(root / "manual/data/lensing/swells_k0_target_tallies_delta3_acquisition.csv")
    fam_sums: dict[str, int] = {}
    for row in r_k0:
        fam = row["target_family"]
        fam_sums[fam] = fam_sums.get(fam, 0) + parse_exact_int(row["O_observed_tally"])
    require(len(fam_sums) == 4 and all(total == 20 for total in fam_sums.values()), f"SWELLS K0 family sums != 20: {fam_sums}")

    # 5. SWELLS K1 thetaE scores & K1/K2/K3 comparison
    _, r_k1 = _read_csv_exact(root / "manual/data/lensing/swells_k1_thetaE_delta3_scores.csv")
    _, r_k123 = _read_csv_exact(root / "manual/data/lensing/swells_k1_k2_k3_delta3_comparison.csv")
    require(len(r_k1) == 3 and len(r_k123) == 3, "SWELLS K1/K123 row counts mismatch")
    k1_t_sum = 0
    k1_o_sum = 0
    k1_dzs: list[int] = []
    k1_ms: list[int] = []
    for row in r_k1:
        tv = parse_exact_int(row["T_cross_predicted_tally"])
        ov = parse_exact_int(row["O_observed_tally"])
        dz = parse_exact_int(row["deltaZ"])
        s3 = parse_exact_int(row["s3"])
        m = parse_exact_int(row["m"])
        require(dz == tv - ov and s3 == _sign3(dz) and m == abs(dz), f"SWELLS K1 row mismatch: {row}")
        k1_t_sum += tv
        k1_o_sum += ov
        k1_dzs.append(dz)
        k1_ms.append(m)
    require(k1_t_sum == 15 and k1_o_sum == 15, "SWELLS K1 totals != 15")
    require(k1_dzs == [0, 4, -4] and sum(k1_dzs) == 0 and sum(k1_ms) == 8, "SWELLS K1 deltaZ/m mismatch")

    k_runs = {row["run"]: row for row in r_k123}
    require(set(k_runs.keys()) == {"K1", "K2", "K3"}, "SWELLS run set mismatch")
    k1_m = parse_exact_int(k_runs["K1"]["thetaE_delta3_total_m"])
    k2_m = parse_exact_int(k_runs["K2"]["thetaE_delta3_total_m"])
    k3_m = parse_exact_int(k_runs["K3"]["thetaE_delta3_total_m"])
    require(k1_m == sum(k1_ms) == 8 and k1_m < k3_m < k2_m and (k3_m, k2_m) == (10, 18), "SWELLS K1/K2/K3 m ordering mismatch")
    # Rounded display match rates: 6/15*100=40, 6/15*100=40, 5/15*100=100/3 -> 33.3333
    expected_match_exact = {
        "K1": Fraction(6 * 100, 15),
        "K2": Fraction(6 * 100, 15),
        "K3": Fraction(5 * 100, 15),
    }
    max_match_res = Fraction(0)
    for run_id, exact_pct in expected_match_exact.items():
        rec_pct = parse_printed_rational(
            k_runs[run_id]["thetaE_system_match_rate_percent"],
            name=f"{run_id}.thetaE_system_match_rate_percent",
            allow_fraction_slash=False,
        )
        require(rec_pct == round_rational_half_even(exact_pct, 4), f"{run_id}: match rate rounded_display mismatch")
        res = abs(rec_pct - exact_pct)
        if res > max_match_res:
            max_match_res = res

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": digests,
        "verified_counts": {
            "k4_gate_rows": len(r_k4),
            "toy1_checks_passed": len(r_t1c),
            "sparc5_galaxies": len(r_s5_med),
            "swells_k0_families": len(fam_sums),
            "swells_k1_k2_k3_runs": len(r_k123),
        },
        "exact_residuals_summary": {
            "max_exact_result_residual": "0",
            "swells_k3_match_rate_rounded_display_residual": canonical_rational_str(max_match_res),
            "field_roles": {
                "exact_input": ["rotmod_bin_counts", "T_cross_predicted_tally", "O_observed_tally"],
                "exact_result": ["deltaZ", "s3", "m", "events", "caustic_bins_count", "thetaE_delta3_total_m"],
                "rounded_display": ["thetaE_system_match_rate_percent"],
                "retained_legacy_float_record": ["median_abs_ΔAγ", "max_abs_ΔAγ"],
            },
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Sector 15: sparc_five_galaxy
# ---------------------------------------------------------------------------

def verify_sparc_five_galaxy(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Verify SPARC five-galaxy exact per-bin, per-galaxy, and summary TeX tables."""
    root = Path(repo_root).resolve()
    digests = _verify_input_digests(root, spec.input_paths, require_all_frozen=True)

    rotmod_rows: list[tuple[str, tuple[Fraction, ...]]] = []
    for gal in _SPARC_GALAXY_ORDER:
        for vals in _parse_rotmod_exact(root / f"manual/data/sparc/{gal}_rotmod.dat"):
            rotmod_rows.append((gal, vals))
    require(len(rotmod_rows) == 209, f"expected 209 SPARC rotmod bins, got {len(rotmod_rows)}")

    _, bin_rows = _read_csv_exact(root / "manual/data/derived/sparc_five_galaxy_per_bin.csv")
    require(len(bin_rows) == 209, f"expected 209 per-bin CSV rows, got {len(bin_rows)}")

    input_cols = ("R", "Vobs", "errV", "Vgas", "Vdisk", "Vbul", "SBdisk", "SBbul")
    derived_cols = (
        "U_obs",
        "sigma_U",
        "U_gas",
        "U_disk",
        "U_bulge",
        "U_bar",
        "C_cap",
        "D_BF",
        "U_AO",
        "Delta_U",
        "z_U",
    )
    max_abs_res: dict[str, Fraction] = {c: Fraction(0) for c in derived_cols}
    max_rel_res: dict[str, Fraction] = {c: Fraction(0) for c in derived_cols}
    max_inherited_check = Fraction(0)
    max_vdisp_sq_res = Fraction(0)
    row0_sigma_u_res: Fraction | None = None

    exact_by_gal: dict[str, list[tuple[Fraction, Fraction, Fraction]]] = {g: [] for g in _SPARC_GALAXY_ORDER}

    for idx, (row, (gal, rot_vals)) in enumerate(zip(bin_rows, rotmod_rows)):
        require(row["galaxy"] == gal, f"SPARC bin row {idx} galaxy mismatch: {row['galaxy']} != {gal}")
        for col, expected_in in zip(input_cols, rot_vals):
            rec_in = parse_printed_rational(row[col], name=col, allow_fraction_slash=False)
            require(rec_in == expected_in, f"SPARC bin row {idx} exact_input mismatch on {col}")

        # Declaration constants exact
        require(parse_printed_rational(row["lambda_ret"], allow_fraction_slash=False) == Fraction(1), f"row {idx}: lambda_ret != 1")
        require(parse_printed_rational(row["density_index"], allow_fraction_slash=False) == Fraction(0), f"row {idx}: density_index != 0")
        require(parse_printed_rational(row["gas_star_index"], allow_fraction_slash=False) == Fraction(0), f"row {idx}: gas_star_index != 0")
        require(parse_printed_rational(row["bobbing_index"], allow_fraction_slash=False) == Fraction(0), f"row {idx}: bobbing_index != 0")

        r_val, v_obs, err_v, v_gas, v_disk, v_bul, _, _ = rot_vals
        u_obs = v_obs * v_obs
        sigma_u = Fraction(2) * v_obs * err_v
        u_gas = v_gas * v_gas
        u_disk = v_disk * v_disk
        u_bulge = v_bul * v_bul
        u_bar = u_gas + _SPARC_UPSILON_D * u_disk + _SPARC_UPSILON_B * u_bulge
        c_cap = r_val * (abs(v_gas) + abs(v_disk) + abs(v_bul))
        d_bf = c_cap
        u_ao = u_bar + _SPARC_K_EXT_U * d_bf
        delta_u = u_ao - u_obs
        require(sigma_u > 0, f"row {idx}: non-positive sigma_U")
        z_u = delta_u / sigma_u

        rec_u_bar = parse_printed_rational(row["U_bar"], name="U_bar", allow_fraction_slash=False)
        rec_d_bf = parse_printed_rational(row["D_BF"], name="D_BF", allow_fraction_slash=False)
        rec_u_ao = parse_printed_rational(row["U_AO"], name="U_AO", allow_fraction_slash=False)
        inherited_diff = abs(rec_u_ao - (rec_u_bar + _SPARC_K_EXT_U * rec_d_bf))
        require(
            inherited_diff < _SPARC_INHERITED_TOL,
            f"SPARC row {idx}: inherited check |U_AO - (U_bar + 8*D_BF)| = {inherited_diff} >= 1/10^9",
        )
        if inherited_diff > max_inherited_check:
            max_inherited_check = inherited_diff

        exact_map = {
            "U_obs": u_obs,
            "sigma_U": sigma_u,
            "U_gas": u_gas,
            "U_disk": u_disk,
            "U_bulge": u_bulge,
            "U_bar": u_bar,
            "C_cap": c_cap,
            "D_BF": d_bf,
            "U_AO": u_ao,
            "Delta_U": delta_u,
            "z_U": z_u,
        }
        for col, exp_val in exact_map.items():
            rec_val = parse_printed_rational(row[col], name=col, allow_fraction_slash=False)
            abs_r = abs(rec_val - exp_val)
            if abs_r > max_abs_res[col]:
                max_abs_res[col] = abs_r
            if exp_val != 0:
                rel_r = abs_r / abs(exp_val)
                if rel_r > max_rel_res[col]:
                    max_rel_res[col] = rel_r
            if idx == 0 and col == "sigma_U":
                row0_sigma_u_res = abs_r

        v_disp = parse_printed_rational(row["V_disp"], name="V_disp", allow_fraction_slash=False)
        require(v_disp >= 0, f"row {idx}: V_disp must be nonnegative")
        vdisp_sq_res = abs(v_disp * v_disp - u_ao)
        if vdisp_sq_res > max_vdisp_sq_res:
            max_vdisp_sq_res = vdisp_sq_res

        exact_by_gal[gal].append((u_obs, delta_u, z_u))

    require(
        row0_sigma_u_res == Fraction(1, 50000000000000),
        f"unexpected row-0 sigma_U legacy float residual: {row0_sigma_u_res}",
    )

    # Per-galaxy CSV and summary TeX table
    _, gal_rows = _read_csv_exact(root / "manual/data/derived/sparc_five_galaxy_per_galaxy.csv")
    require(len(gal_rows) == 5, f"expected 5 SPARC per-galaxy rows, got {len(gal_rows)}")
    summary_tex = (root / "manual/data/derived/sparc_summary_table.tex").read_text(encoding="utf-8")

    expected_n = {"DDO154": 12, "NGC2403": 73, "NGC2841": 50, "NGC3198": 43, "NGC6503": 31}
    per_gal_max_res: dict[str, Fraction] = {k: Fraction(0) for k in ("chi2_U", "MAE_U", "MSE_U", "MAPE_U")}
    for row in gal_rows:
        gal = row["galaxy"]
        require(gal in expected_n, f"unexpected SPARC galaxy: {gal!r}")
        pts = exact_by_gal[gal]
        n_bins = len(pts)
        require(parse_exact_int(row["N"], name="N") == n_bins == expected_n[gal], f"{gal}: N mismatch")

        chi2_ex = sum((z * z for _, _, z in pts), Fraction(0))
        mae_ex = sum((abs(du) for _, du, _ in pts), Fraction(0)) / Fraction(n_bins)
        mse_ex = sum((du * du for _, du, _ in pts), Fraction(0)) / Fraction(n_bins)
        valid = [(uo, du) for uo, du, _ in pts if uo > 0]
        mape_ex = sum((Fraction(100) * abs(du) / uo for uo, du in valid), Fraction(0)) / Fraction(len(valid))

        for mname, ex_v in (("chi2_U", chi2_ex), ("MAE_U", mae_ex), ("MSE_U", mse_ex), ("MAPE_U", mape_ex)):
            rec_v = parse_printed_rational(row[mname], name=f"{gal}.{mname}", allow_fraction_slash=False)
            diff = abs(rec_v - ex_v)
            if diff > per_gal_max_res[mname]:
                per_gal_max_res[mname] = diff

        expected_tex_line = (
            f"{gal} & G0 & obs-only & {n_bins} & "
            f"{format_rational_fixed(chi2_ex, 2)} & "
            f"{format_rational_fixed(mae_ex, 1)} & "
            f"{format_rational_fixed(mse_ex, 1)} & "
            f"{format_rational_fixed(mape_ex, 2)}\\\\"
        )
        require(
            expected_tex_line in summary_tex,
            f"sparc_summary_table.tex missing exact rounded line for {gal}: {expected_tex_line}",
        )

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": digests,
        "verified_counts": {
            "galaxies": len(gal_rows),
            "per_bin_rows": len(bin_rows),
            "summary_table_rows": len(gal_rows),
        },
        "exact_residuals_summary": {
            "inherited_U_AO_check_bound": canonical_rational_str(_SPARC_INHERITED_TOL),
            "max_inherited_U_AO_residual": canonical_rational_str(max_inherited_check),
            "row0_sigma_U_legacy_float_residual": canonical_rational_str(row0_sigma_u_res),
            "per_bin_max_abs_residual": {
                col: canonical_rational_str(val) for col, val in sorted(max_abs_res.items())
            },
            "per_bin_max_rel_residual": {
                col: canonical_rational_str(val) for col, val in sorted(max_rel_res.items())
            },
            "max_V_disp_squared_residual_vs_exact_U_AO": canonical_rational_str(max_vdisp_sq_res),
            "per_galaxy_max_abs_residual": {
                col: canonical_rational_str(val) for col, val in sorted(per_gal_max_res.items())
            },
            "field_roles": {
                "exact_input": list(input_cols),
                "exact_result": ["N", "lambda_ret", "density_index", "gas_star_index", "bobbing_index"],
                "retained_legacy_float_record": [*derived_cols, "V_disp", "chi2_U", "MAE_U", "MSE_U", "MAPE_U"],
                "rounded_display": ["sparc_summary_table.tex_(2,1,1,2)dp"],
            },
        },
        "error": None,
    }


_TIER2_HANDLERS = {
    "dec_ledger": verify_dec_ledger,
    "higgs_trace": verify_higgs_trace,
    "phase_delta3_3d": verify_phase_delta3_3d,
    "cycle_shedding": verify_cycle_shedding,
    "lensing_tallies": verify_lensing_tallies,
    "sparc_five_galaxy": verify_sparc_five_galaxy,
}


def run_tier2_sector(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Dispatch and execute one Tier-2 pure zero-float verifier."""
    require(spec.sector_id in _TIER2_HANDLERS, f"unregistered Tier-2 sector: {spec.sector_id}")
    result = _TIER2_HANDLERS[spec.sector_id](spec, repo_root)
    counts = result["verified_counts"]
    require(isinstance(counts, dict), "Tier-2 verified_counts must be a dict")
    for req_key, min_val in spec.required_outputs:
        actual = parse_exact_int(counts.get(req_key), name=f"{spec.sector_id}.{req_key}")
        require(actual >= min_val, f"vacuous Tier-2 output {spec.sector_id}.{req_key}: {actual} < {min_val}")
    return result
