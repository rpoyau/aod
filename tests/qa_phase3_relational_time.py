"""Adversarial Phase 3 (P3-relational-time) QA & Handoff Verification Suite.

Covers all Phase 3 invariants across BND-P3-01, BND-P3-02, and BND-P3-03:
1. Main §4 relational-time clock-free audit (zero unbound `t` in
   `subsec:duon-tick-click` and `subsec:duon-continuity`, exact Typst bindings
   to `eq:complete-wave-state`, `eq:complete-coupling-state`,
   `eq:wave-update-trace`, `eq:coupling-trace`, exact 455 Main labels).
2. Independent exact rational oracle cross-checking BOTH Python S2
   (`eval_dec_temporal_si_bridge_bounds`) AND Rust S4
   (`aod-core --eval-op dec_temporal_si_bridge_bounds`) across an adversarial
   multi-case matrix — plus poisoned-`Fraction` proof and zero-hardcoded-ratio
   AST audit.
3. Adversarial error-class parity matrix (`TypeError` vs `ValueError`) between
   S2 Python and S4 Rust.
4. Cross-artifact parity from RC-037 engine -> 9-row CSV -> Figure 10 ->
   Manual §7 & Manual §2 (labels, verbatim equations, forbidden regressions,
   live CSV parity, Main citation resolution).
5. Frozen authority SHA-256 immutability checks.
6. End-to-end Typst PDF publication build (`--check-registry`) + 144 ppi
   `pdftoppm` render check of Main §4 and Manual Figure 10 with guaranteed
   `try/finally` cleanup of `_build/qa_p3_pub`.
7. Self-AST check verifying zero bare `assert` statements (`ast.Assert`),
   ensuring identical execution under normal and `-O` Python.
"""
from __future__ import annotations

import ast
import copy
import csv
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Any, Iterator

import pytest

import manual.engine.sectors.manual_dec_examples as dec_mod
from manual.engine.sectors.manual_dec_examples import (
    build_temporal_si_bridge_csv_rows,
    eval_dec_temporal_si_bridge_bounds,
)

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

PINNED_FROZEN_SHA256: dict[str, str] = {
    "manual/scripts/aod_temporal_observation.py": (
        "35c786adeac653ac9348424e915e3b0df98b8fc61ec7c6226bf82819540f7086"
    ),
    "manual/scripts/aod_temporal_anchor.py": (
        "0852fdcc8ee6c541d72a11cb0e67ade19851db458c9dadcba87a579a721d8266"
    ),
    "manual/data/temporal_observation/temporal.json": (
        "fbb2c38c1bb2ad7151a4d261ba975799a1aa2657716594f439d7d895dfc09554"
    ),
    "manual/data/experimental_comparison/experimental_input_comparison.json": (
        "4fb7bfdcbad9dde5e17ea7b659605347f6c923bbcc5397762fc8621cf94219ae"
    ),
}

CANONICAL_RC037_BASE: dict[str, Any] = {
    "compared_cuts": [2, 10, 18, 26],
    "ref_cuts": [2, 12, 22],
    "f_cs_hz": 9192631770,
    "cal_ref": 32,
    "field_a": [58, 48],
    "field_b": [151, 102],
}

MANUAL_S7_VERBATIM_EQUATIONS: tuple[tuple[str, str], ...] = (
    (
        "eq:manual-m3-cycle-bridge",
        '$ hat(C)_(upright("Cs")) = g_(theta) ( Gamma_R , omega ,cal(P),E,upright("preparation")), wide hat(T) = frac(hat(C)_(upright("Cs")), Delta nu_(upright("Cs"))). $ <eq:manual-m3-cycle-bridge>',
    ),
    (
        "eq:manual-m3-observed-advance",
        "$ A(W) = C(W) + phi.alt_1 - phi.alt_0 . $ <eq:manual-m3-observed-advance>",
    ),
    (
        "eq:manual-m3-accumulated-si",
        '$ frac(A, A_R) = frac(7, 17), wide T = frac(A_R, f_(upright("Cs"))) = frac(17, 2 f_(upright("Cs"))), wide macron(nu) = frac(A, T) = frac(7 f_(upright("Cs")), 17). $ <eq:manual-m3-accumulated-si>',
    ),
    (
        "eq:manual-m3-hydrogen-reduction",
        '$ nu_H = 284 nu_R + nu_S + nu_B + delta_(upright("UTC")) + delta_N + delta_W + delta_D + delta_Z . $ <eq:manual-m3-hydrogen-reduction>',
    ),
    (
        "eq:manual-m3-residual-dependence",
        '$ op("Var")(A - E) = op("Var")(A) + op("Var")(E) - 2 op("Cov")(A,E). $ <eq:manual-m3-residual-dependence>',
    ),
)

EXPECTED_MANUAL_S2_LABELS: frozenset[str] = frozenset(
    {
        "manual:m1-native-fixtures",
        "subsec:disoma-declaration",
        "fig:field-count",
        "fig:fractal-tesseract-beat-family",
        "manual:wavelet-continuation-fixtures",
        "manual:m1:dec-closure-walk",
        "fig:manual-native-closure-q4-walk",
        "tab:manual-native-closure-dec-walk",
    }
)

EXPECTED_MANUAL_S7_LABELS: frozenset[str] = frozenset(
    {
        "manual:m3-temporal",
        "eq:manual-m3-cycle-bridge",
        "tab:manual-m3-anchor-transfer",
        "manual:m3-metrology",
        "eq:manual-m3-observed-advance",
        "eq:manual-m3-accumulated-si",
        "eq:manual-m3-hydrogen-reduction",
        "eq:manual-m3-residual-dependence",
        "manual:m3-temporal:dec-si-bridge",
        "fig:manual-temporal-si-bridge-feynman",
        "tab:manual-temporal-dec-bridge",
    }
)


def _check(cond: bool, msg: str) -> None:
    """Non-strippable assertion helper active in both normal and -O Python."""
    if not cond:
        raise AssertionError(msg)


def _check_eq(actual: object, expected: object, label: str) -> None:
    """Non-strippable equality check with detailed mismatch diagnostics."""
    _check(actual == expected, f"{label}: actual={actual!r} != expected={expected!r}")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _assert_no_floats(obj: object, path: str = "$") -> None:
    _check(not isinstance(obj, float), f"forbidden float encountered at {path}: {obj!r}")
    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            _assert_no_floats(item, f"{path}[{idx}]")


def _tool_env() -> dict[str, str]:
    env = dict(os.environ)
    local_bin = str(Path.home() / ".local" / "bin")
    cur_path = env.get("PATH", "")
    parts = cur_path.split(os.pathsep) if cur_path else []
    if local_bin not in parts:
        env["PATH"] = f"{local_bin}{os.pathsep}{cur_path}" if cur_path else local_bin
    return env


@pytest.fixture(scope="module")
def aod_core_bin() -> Iterator[Path]:
    """Compile aod-core offline into an isolated temp target dir and clean up afterwards."""
    with tempfile.TemporaryDirectory(prefix="qa_p3_aod_core_") as tmp_dir:
        env = _tool_env()
        env["CARGO_TARGET_DIR"] = tmp_dir
        proc = subprocess.run(
            [
                "cargo",
                "build",
                "--manifest-path",
                str(REPO_ROOT / "crates" / "aod-core" / "Cargo.toml"),
                "--offline",
                "--locked",
                "--quiet",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        _check(
            proc.returncode == 0,
            f"cargo build for aod-core failed (rc={proc.returncode}): {proc.stderr}",
        )
        binary = Path(tmp_dir) / "debug" / "aod-core"
        _check(binary.is_file(), f"expected compiled aod-core binary at {binary}")
        yield binary


def _eval_s4(binary: Path, payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(binary),
            "--eval-op",
            "dec_temporal_si_bridge_bounds",
            "--input-stdin",
        ],
        cwd=str(REPO_ROOT),
        input=json.dumps(payload, separators=(",", ":")),
        capture_output=True,
        text=True,
        check=False,
    )


def _parse_rust_error_class(stderr: str) -> str | None:
    match = re.search(r"error \((TypeError|ValueError)\):", stderr)
    return match.group(1) if match else None


def _frac_pair(q: Fraction) -> list[str]:
    return [str(q.numerator), str(q.denominator)]


def _parse_oracle_rat(raw: object) -> Fraction:
    _check(isinstance(raw, list) and len(raw) == 2, f"oracle expected pair, got {raw!r}")
    a, b = raw[0], raw[1]
    if isinstance(a, str) and isinstance(b, str):
        return Fraction(int(a), int(b))
    _check(
        isinstance(a, int) and not isinstance(a, bool) and isinstance(b, int) and not isinstance(b, bool),
        f"oracle pair entries invalid: {raw!r}",
    )
    return Fraction(a, b)


def _independent_rc037_oracle(inputs: dict[str, Any]) -> dict[str, Any]:
    """Completely independent exact-rational oracle for RC-037 using fractions.Fraction."""
    c_cuts: list[int] = list(inputs["compared_cuts"])
    r_cuts: list[int] = list(inputs["ref_cuts"])
    f_cs_hz: int = int(inputs["f_cs_hz"])
    cal_ref: int = int(inputs["cal_ref"])
    na_cal, na_val = int(inputs["field_a"][0]), int(inputs["field_a"][1])
    nb_cal, nb_val = int(inputs["field_b"][0]), int(inputs["field_b"][1])

    win_lo, win_hi = (
        (int(inputs["window"][0]), int(inputs["window"][1]))
        if "window" in inputs
        else (0, 30)
    )
    compared_bias = (
        _parse_oracle_rat(inputs["compared_bias"])
        if "compared_bias" in inputs
        else Fraction(1, 4)
    )
    ref_bias = (
        _parse_oracle_rat(inputs["ref_bias"])
        if "ref_bias" in inputs
        else Fraction(-1, 4)
    )
    rcd_rd = int(inputs["rcd_rd"]) if "rcd_rd" in inputs else 3
    rcd_c_refs = list(inputs["rcd_c_reflections"]) if "rcd_c_reflections" in inputs else [1, 1]
    rcd_r_refs = list(inputs["rcd_r_reflections"]) if "rcd_r_reflections" in inputs else [2, 2]
    a_c = _parse_oracle_rat(inputs["a_c"]) if "a_c" in inputs else Fraction(1, 1)
    a_r = _parse_oracle_rat(inputs["a_r"]) if "a_r" in inputs else Fraction(1, 1)

    # 1. Half-open (win_lo, win_hi] filtering with anchor cuts[0] excluded
    n_c = sum(1 for k in c_cuts[1:] if win_lo < k <= win_hi)
    n_r = sum(1 for k in r_cuts[1:] if win_lo < k <= win_hi)
    _check(n_c > 0 and n_r > 0, f"oracle post-anchor counts must be positive: {n_c}, {n_r}")

    biz_cr = Fraction(n_c, n_r)
    biz_rc = Fraction(n_r, n_c)
    lag_fwd = Fraction(n_c - n_r, 1) + (compared_bias - ref_bias)
    lag_rev = -lag_fwd
    rcd_cr = rcd_rd + sum(rcd_c_refs)
    rcd_rc = rcd_rd + sum(rcd_r_refs)

    t_sec = Fraction(n_r, 1) * a_r / Fraction(f_cs_hz, 1)
    nu_bar = Fraction(n_c, 1) * a_c / t_sec

    pred_a = Fraction(cal_ref * na_val, na_cal)
    rel_a = (pred_a - cal_ref) / cal_ref
    pred_b = Fraction(cal_ref * nb_val, nb_cal)
    rel_b = (pred_b - cal_ref) / cal_ref

    # 2. Independent cut-by-cut causal simulation
    c_lo, c_hi = (
        (int(inputs["causal_window"][0]), int(inputs["causal_window"][1]))
        if "causal_window" in inputs
        else (0, 100)
    )
    outer_plus = set(
        inputs["causal_outer_plus"]
        if "causal_outer_plus" in inputs
        else [16, 32, 48, 64, 80, 96]
    )
    outer_minus = set(
        inputs["causal_outer_minus"]
        if "causal_outer_minus" in inputs
        else [15, 30, 45, 60, 75]
    )
    cut_i = int(inputs["intervention_cut"]) if "intervention_cut" in inputs else 40

    def _sim(apply_int: bool, disconnect: bool) -> tuple[list[tuple[int, int, bool, int, int, bool]], int, int]:
        cap = 2
        retained = True
        queued = False
        cp = 0
        cm = 0
        trace: list[tuple[int, int, bool, int, int, bool]] = []
        for k in range(c_lo, c_hi + 1):
            if queued:
                cap = 1
                queued = False
                if cap < 2:
                    retained = True if disconnect else False
            if k > c_lo:
                if k in outer_plus and retained:
                    cp += 1
                if k in outer_minus:
                    cm += 1
            q_here = apply_int and (k == cut_i)
            if q_here:
                queued = True
            trace.append((k, cap, retained, cp, cm, q_here))
        return trace, cp, cm

    base_tr, base_p, base_m = _sim(False, False)
    int_tr, int_p, int_m = _sim(True, False)
    disc_tr, disc_p, disc_m = _sim(True, True)

    _check_eq((disc_p, disc_m), (base_p, base_m), "oracle disconnected counts == baseline")

    prefix_through = None
    for rb, ri, rd in zip(base_tr, int_tr, disc_tr):
        if rb == ri == rd:
            prefix_through = rb[0]
        else:
            break
    first_div = None
    for rb, ri in zip(base_tr, int_tr):
        if rb[:5] != ri[:5]:
            first_div = rb[0]
            break
    _check_eq(prefix_through, cut_i - 1, "oracle common_prefix_through")
    _check_eq(first_div, cut_i + 1, "oracle first_divergent_cut")

    # 3. Independent observed-advance calculation
    oa_defaults: dict[str, dict[str, Any]] = {
        "compared": {"winding": 4, "phase_start": ["2", "3"], "phase_end": ["1", "6"]},
        "reference": {"winding": 8, "phase_start": ["1", "4"], "phase_end": ["3", "4"]},
        "split_left": {"winding": 2, "phase_start": ["2", "3"], "phase_end": ["5", "6"]},
        "split_right": {"winding": 2, "phase_start": ["5", "6"], "phase_end": ["1", "6"]},
        "signed_control": {"winding": 0, "phase_start": ["3", "4"], "phase_end": ["1", "4"]},
    }
    oa_in = dict(oa_defaults)
    if "observed_advance" in inputs:
        oa_in.update(inputs["observed_advance"])

    def _adv(entry: dict[str, Any]) -> Fraction:
        return Fraction(int(entry["winding"]), 1) + _parse_oracle_rat(entry["phase_end"]) - _parse_oracle_rat(entry["phase_start"])

    adv_c = _adv(oa_in["compared"])
    adv_r = _adv(oa_in["reference"])
    adv_split = _adv(oa_in["split_left"]) + _adv(oa_in["split_right"])
    adv_signed = _adv(oa_in["signed_control"])
    adv_clipped = adv_signed if adv_signed > 0 else Fraction(0, 1)
    _check_eq(adv_split, adv_c, "oracle observed advance split additivity")

    return {
        "delta_bip_compared": n_c,
        "delta_bip_ref": n_r,
        "biz_c_over_r": _frac_pair(biz_cr),
        "biz_r_over_c": _frac_pair(biz_rc),
        "lag_forward": _frac_pair(lag_fwd),
        "lag_reverse": _frac_pair(lag_rev),
        "T_seconds": _frac_pair(t_sec),
        "nu_bar_hz": _frac_pair(nu_bar),
        "transfer_A_pred": _frac_pair(pred_a),
        "transfer_A_rel_resid": _frac_pair(rel_a),
        "transfer_B_pred": _frac_pair(pred_b),
        "transfer_B_rel_resid": _frac_pair(rel_b),
        "intervention_ratio_before": _frac_pair(Fraction(base_p, base_m)),
        "intervention_ratio_after": _frac_pair(Fraction(int_p, int_m)),
        "window": [win_lo, win_hi],
        "rcd_c_given_r": rcd_cr,
        "rcd_r_given_c": rcd_rc,
        "intervention_common_prefix_through": prefix_through,
        "intervention_first_divergent_cut": first_div,
        "intervention_counts_before": [base_p, base_m],
        "intervention_counts_after": [int_p, int_m],
        "intervention_disconnect_rejected": True,
        "observed_advance_compared": _frac_pair(adv_c),
        "observed_advance_ref": _frac_pair(adv_r),
        "observed_advance_ratio": _frac_pair(adv_c / adv_r),
        "observed_advance_split_sum": _frac_pair(adv_split),
        "observed_advance_clipped": _frac_pair(adv_clipped),
        "observed_advance_signed": _frac_pair(adv_signed),
    }


def _extract_typst_subsection(text: str, start_heading_marker: str, next_heading_re: str) -> str:
    start_idx = text.find(start_heading_marker)
    _check(start_idx >= 0, f"missing heading marker {start_heading_marker!r}")
    rest = text[start_idx + len(start_heading_marker) :]
    match = re.search(next_heading_re, rest, flags=re.MULTILINE)
    end_idx = start_idx + len(start_heading_marker) + (match.start() if match else len(rest))
    return text[start_idx:end_idx]


def _extract_typst_labels(text: str) -> set[str]:
    """Extract all `<label>` declarations including `#aod-anchor(<...>)`."""
    return set(re.findall(r"<([a-zA-Z][a-zA-Z0-9:_-]*)>", text))


def _extract_main_refs(text: str) -> list[tuple[str, str]]:
    """Extract all `#mainequation/#mainsection/#mainappendix("main:...")` citations."""
    return re.findall(r'#(mainequation|mainsection|mainappendix)\("([^"]+)"\)', text)


def _strip_quoted_strings(expr: str) -> str:
    return re.sub(r'"[^"]*"', '""', expr)


# =============================================================================
# 1. Main §4 Relational-Time Clock-Free Audit & Exact 455 Main Labels
# =============================================================================


def test_main_section4_clock_free_tick_click_and_continuity() -> None:
    """Verify zero unbound `t` and exact state/trace bindings in Main §4 tail subsections."""
    path = REPO_ROOT / "typst" / "sections" / "06_wave_state_relational_time.typ"
    text = path.read_text(encoding="utf-8")

    tick_click = _extract_typst_subsection(
        text,
        "=== Tick/click <subsec:duon-tick-click>",
        r"^===?\s+",
    )
    continuity = _extract_typst_subsection(
        text,
        "=== Markovian and retained-history continuity <subsec:duon-continuity>",
        r"^==\s+",
    )

    required_eqrefs = (
        '#eqref("eq:complete-wave-state")',
        '#eqref("eq:complete-coupling-state")',
        '#eqref("eq:wave-update-trace")',
        '#eqref("eq:coupling-trace")',
    )

    for sub_name, sub_text in (("subsec:duon-tick-click", tick_click), ("subsec:duon-continuity", continuity)):
        for block in ("#aod-paragraph[Setup.]", "#aod-paragraph[Derivation.]", "#aod-paragraph[Falsification.]"):
            _check(block in sub_text, f"{sub_name} missing GM block {block}")
        for ref in required_eqrefs:
            _check(ref in sub_text, f"{sub_name} missing required Typst binding {ref}")

        # Zero new numbered equations inside compacted tail subsections
        numbered_eq_labels = re.findall(r"\$\s*<eq:[^>]+>", sub_text)
        _check(not numbered_eq_labels, f"{sub_name} unexpectedly declares numbered equations: {numbered_eq_labels}")

        # Audit every math span `$ ... $` for unbound background clock variable `t`
        math_spans = re.findall(r"\$([^$]+)\$", sub_text, flags=re.DOTALL)
        _check(len(math_spans) >= 6, f"{sub_name} expected >= 6 math spans, got {len(math_spans)}")
        for span in math_spans:
            cleaned = _strip_quoted_strings(span)
            # Standalone variable `t` not part of a Typst symbol (like `lt.eq`, `gt.eq`, `times`)
            _check(
                re.search(r"(?<![A-Za-z.])t(?![A-Za-z.])", cleaned) is None,
                f"{sub_name} contains unbound clock variable `t` in math span: ${span}$",
            )
            _check(
                re.search(r"_(?:t|\(\s*t\b)|\b[KXYSV]_t\b|\bbeta_t\b", cleaned) is None,
                f"{sub_name} contains clock-subscripted `t` in math span: ${span}$",
            )

        # Prose check for stray t-indexed symbols or `$t$`
        for forbidden_pat in (r"\$t\$", r"\b[KXYS]_t\b", r"\bbeta_t\b", r"\bt\s*\+\s*1\b", r"\bt\s*-\s*1\b"):
            _check(
                re.search(forbidden_pat, sub_text) is None,
                f"{sub_name} matched forbidden clock-t pattern {forbidden_pat}",
            )

    # Specific semantic bindings required by BND-P3-01
    for token in (
        "k in bb(Z)",
        "K_k := (S^W_(B,i,k) , S^(times)_(I,B,k) )",
        "X_k = E_B (K_k )",
        "Y_k",
        "beta_k",
        'Delta_(upright("lead/lag"), lt.eq k)',
        "cal(U)_B",
    ):
        _check(token in tick_click, f"subsec:duon-tick-click missing bound token {token!r}")

    for token in (
        'Pi_(upright("cut")) (S^W_(B,i,k) )',
        'cal(U)_B^(upright("M"))',
        "S^W_(B,i,k + 1) eq.not tilde(S)^W_(B,i,k + 1)",
        "(S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) ) eq.not (tilde(S)^W_(B,i,lt.eq k) , tilde(S)^(times)_(I,B,lt.eq k) )",
    ):
        _check(token in continuity, f"subsec:duon-continuity missing bound token {token!r}")


def test_main_registry_exact_455_labels_and_section4_bindings() -> None:
    """Verify Main registry preserves exact 455 labels, 198 numbered equations, and §4 entries."""
    reg_path = REPO_ROOT / "typst" / "lib" / "main_registry.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    entries = reg.get("entries")
    _check(isinstance(entries, dict), "main_registry.json entries must be a dict")
    _check_eq(reg.get("entry_count"), 455, "main_registry entry_count")
    _check_eq(len(entries), 455, "len(main_registry.entries)")

    eq_count = sum(1 for v in entries.values() if v.get("kind") in {"equation", "rg-equation"})
    _check_eq(eq_count, 198, "Main numbered equation count (equation + rg-equation)")

    expected_kinds = {
        "sec:wave-state-relational-time": "section",
        "subsec:duon-tick-click": "subsubsection",
        "subsec:duon-continuity": "subsubsection",
        "eq:complete-wave-state": "equation",
        "eq:complete-coupling-state": "equation",
        "eq:wave-update-trace": "equation",
        "eq:coupling-trace": "equation",
    }
    for label, kind in expected_kinds.items():
        _check(label in entries, f"Main label {label!r} missing from main_registry.json")
        _check_eq(entries[label].get("kind"), kind, f"kind of Main label {label}")


# =============================================================================
# 2. Independent Rational Oracle (S2 Python vs S4 Rust) & Poisoned-Fraction Proof
# =============================================================================


def _build_adversarial_valid_matrix() -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []

    def _case(name: str, overrides: dict[str, Any]) -> None:
        cfg = copy.deepcopy(CANONICAL_RC037_BASE)
        cfg.update(overrides)
        cases.append((name, cfg))

    _case("canonical_defaults_omitted", {})
    _case(
        "canonical_defaults_explicit",
        {
            "window": [0, 30],
            "compared_bias": ["1", "4"],
            "ref_bias": ["-1", "4"],
            "rcd_rd": 3,
            "rcd_c_reflections": [1, 1],
            "rcd_r_reflections": [2, 2],
            "a_c": ["1", "1"],
            "a_r": ["1", "1"],
            "causal_window": [0, 100],
            "causal_outer_plus": [16, 32, 48, 64, 80, 96],
            "causal_outer_minus": [15, 30, 45, 60, 75],
            "intervention_cut": 40,
            "observed_advance": {
                "compared": {"winding": 4, "phase_start": ["2", "3"], "phase_end": ["1", "6"]},
                "reference": {"winding": 8, "phase_start": ["1", "4"], "phase_end": ["3", "4"]},
                "split_left": {"winding": 2, "phase_start": ["2", "3"], "phase_end": ["5", "6"]},
                "split_right": {"winding": 2, "phase_start": ["5", "6"], "phase_end": ["1", "6"]},
                "signed_control": {"winding": 0, "phase_start": ["3", "4"], "phase_end": ["1", "4"]},
            },
        },
    )
    _case(
        "half_open_left_excluded_right_included",
        {
            "compared_cuts": [2, 10, 18, 26],
            "ref_cuts": [2, 12, 22, 30],
            "window": [2, 26],
        },
    )
    _case(
        "anchor_inside_minimum_two_closures_yields_count_one",
        {
            "compared_cuts": [5, 10],
            "ref_cuts": [1, 6, 10],
            "window": [0, 10],
        },
    )
    _case(
        "negative_cuts_and_window_equal_counts",
        {
            "compared_cuts": [-20, -15, -5, 10, 11],
            "ref_cuts": [-30, -10, 0, 10, 25],
            "window": [-20, 10],
            "compared_bias": ["-3", "5"],
            "ref_bias": ["2", "7"],
        },
    )
    _case(
        "asymmetric_biases_non_unit_gains_int_pairs",
        {
            "compared_bias": [-7, 12],
            "ref_bias": [5, 8],
            "a_c": [3, 7],
            "a_r": [5, 11],
            "rcd_rd": 7,
            "rcd_c_reflections": [2, 0, 5],
            "rcd_r_reflections": [1, 9],
        },
    )
    _case(
        "neutral_rcd_empty_and_extreme_transfer_val_zero_and_exact",
        {
            "rcd_rd": 11,
            "rcd_c_reflections": [],
            "rcd_r_reflections": [0, 4, 0, 9],
            "field_a": [10, 0],
            "field_b": [25, 25],
        },
    )
    _case(
        "shifted_intervention_cut_lands_on_outer_plus_event_32",
        {
            "intervention_cut": 32,
        },
    )
    _case(
        "shifted_intervention_cut_just_before_event_48",
        {
            "intervention_cut": 47,
        },
    )
    _case(
        "shifted_intervention_cut_lands_on_event_48",
        {
            "intervention_cut": 48,
        },
    )
    _case(
        "custom_causal_negative_window_zero_post_intervention_plus",
        {
            "causal_window": [-40, 60],
            "causal_outer_plus": [-40, 10, 20, 60, 70],
            "causal_outer_minus": [-40, -30, 0, 30, 60, 65],
            "intervention_cut": 5,
        },
    )
    _case(
        "custom_causal_all_plus_events_before_intervention_cut",
        {
            "causal_window": [0, 50],
            "causal_outer_plus": [5, 10],
            "causal_outer_minus": [10, 20, 30],
            "intervention_cut": 40,
        },
    )
    _case(
        "observed_advance_custom_splits_and_positive_signed_control",
        {
            "observed_advance": {
                "compared": {"winding": 3, "phase_start": ["1", "5"], "phase_end": ["4", "5"]},
                "reference": {"winding": 5, "phase_start": ["0", "1"], "phase_end": ["1", "2"]},
                "split_left": {"winding": 1, "phase_start": ["1", "5"], "phase_end": ["9", "10"]},
                "split_right": {"winding": 2, "phase_start": ["9", "10"], "phase_end": ["4", "5"]},
                "signed_control": {"winding": 0, "phase_start": ["1", "7"], "phase_end": ["5", "7"]},
            },
        },
    )
    _case(
        "observed_advance_negative_compared_and_zero_signed_control",
        {
            "observed_advance": {
                "compared": {"winding": 0, "phase_start": ["3", "4"], "phase_end": ["1", "4"]},
                "reference": {"winding": 1, "phase_start": ["0", "1"], "phase_end": ["1", "3"]},
                "split_left": {"winding": 0, "phase_start": ["3", "4"], "phase_end": ["1", "2"]},
                "split_right": {"winding": 0, "phase_start": ["1", "2"], "phase_end": ["1", "4"]},
                "signed_control": {"winding": 0, "phase_start": ["2", "3"], "phase_end": ["2", "3"]},
            },
        },
    )
    _case(
        "large_exact_integers_and_prime_gains",
        {
            "f_cs_hz": 91926317700000001,
            "cal_ref": 1000003,
            "field_a": [999983, 777773],
            "field_b": [131071, 65537],
            "a_c": ["1000003", "999983"],
            "a_r": ["77777", "131071"],
            "compared_bias": ["-1234567", "999983"],
            "ref_bias": ["7654321", "1000003"],
        },
    )
    _case(
        "observed_advance_int_pairs_partial_override",
        {
            "observed_advance": {
                "compared": {"winding": 4, "phase_start": [2, 3], "phase_end": [1, 6]},
                "reference": {"winding": 8, "phase_start": [1, 4], "phase_end": [3, 4]},
                "split_left": {"winding": 2, "phase_start": [2, 3], "phase_end": [5, 6]},
                "split_right": {"winding": 2, "phase_start": [5, 6], "phase_end": [1, 6]},
                "signed_control": {"winding": 0, "phase_start": [3, 4], "phase_end": [1, 4]},
            },
        },
    )
    return cases


def test_s2_and_s4_match_independent_oracle_across_adversarial_matrix(aod_core_bin: Path) -> None:
    """Cross-check S2 Python and S4 Rust against independent exact rational oracle."""
    matrix = _build_adversarial_valid_matrix()
    _check(len(matrix) >= 14, f"expected >= 14 adversarial matrix cases, got {len(matrix)}")

    for case_name, payload in matrix:
        expected = _independent_rc037_oracle(payload)
        s2_out = eval_dec_temporal_si_bridge_bounds(copy.deepcopy(payload))
        _assert_no_floats(s2_out, f"s2[{case_name}]")
        _check_eq(s2_out, expected, f"S2 vs independent oracle ({case_name})")

        proc = _eval_s4(aod_core_bin, payload)
        _check(
            proc.returncode == 0,
            f"S4 failed on valid case {case_name!r} (rc={proc.returncode}): {proc.stderr}",
        )
        s4_out = json.loads(proc.stdout)
        _assert_no_floats(s4_out, f"s4[{case_name}]")
        _check_eq(s4_out, expected, f"S4 vs independent oracle ({case_name})")
        _check_eq(s2_out, s4_out, f"S2 vs S4 parity ({case_name})")

        # Fundamental algebraic invariants verified directly on outputs
        biz_cr = _parse_oracle_rat(s2_out["biz_c_over_r"])
        biz_rc = _parse_oracle_rat(s2_out["biz_r_over_c"])
        _check_eq(biz_cr * biz_rc, Fraction(1, 1), f"cadence reciprocity ({case_name})")

        lag_f = _parse_oracle_rat(s2_out["lag_forward"])
        lag_r = _parse_oracle_rat(s2_out["lag_reverse"])
        _check_eq(lag_f + lag_r, Fraction(0, 1), f"lag antisymmetry ({case_name})")

        a_c = _parse_oracle_rat(payload["a_c"]) if "a_c" in payload else Fraction(1, 1)
        t_sec = _parse_oracle_rat(s2_out["T_seconds"])
        nu_bar = _parse_oracle_rat(s2_out["nu_bar_hz"])
        _check_eq(
            nu_bar * t_sec,
            Fraction(int(s2_out["delta_bip_compared"]), 1) * a_c,
            f"SI bridge identity nu_bar * T == N_c * a_c ({case_name})",
        )

        adv_c = _parse_oracle_rat(s2_out["observed_advance_compared"])
        adv_split = _parse_oracle_rat(s2_out["observed_advance_split_sum"])
        adv_signed = _parse_oracle_rat(s2_out["observed_advance_signed"])
        adv_clipped = _parse_oracle_rat(s2_out["observed_advance_clipped"])
        _check_eq(adv_split, adv_c, f"observed advance additivity ({case_name})")
        _check_eq(
            adv_clipped,
            adv_signed if adv_signed > 0 else Fraction(0, 1),
            f"observed advance clipping ({case_name})",
        )

        cut_i = int(payload.get("intervention_cut", 40))
        _check_eq(s2_out["intervention_common_prefix_through"], cut_i - 1, f"prefix_through ({case_name})")
        _check_eq(s2_out["intervention_first_divergent_cut"], cut_i + 1, f"first_divergent ({case_name})")
        _check(s2_out["intervention_disconnect_rejected"] is True, f"disconnect_rejected ({case_name})")


def test_rc037_poisoned_fraction_proof_and_ast_hygiene(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove RC-037 makes zero calls to Fraction and contains zero hardcoded intervention ratios."""
    import fractions as fractions_mod

    class _PoisonFraction:
        def __new__(cls, *args: object, **kwargs: object) -> object:
            raise RuntimeError("POISONED_FRACTION_INVOKED_IN_RC037")

    monkeypatch.setattr(dec_mod, "Fraction", _PoisonFraction)
    monkeypatch.setattr(fractions_mod, "Fraction", _PoisonFraction)

    canonical_res = eval_dec_temporal_si_bridge_bounds(copy.deepcopy(CANONICAL_RC037_BASE))
    _check_eq(canonical_res["biz_c_over_r"], ["3", "2"], "poisoned-Fraction canonical biz_c_over_r")
    _check_eq(canonical_res["intervention_ratio_before"], ["6", "5"], "poisoned-Fraction baseline ratio")
    _check_eq(canonical_res["intervention_ratio_after"], ["2", "5"], "poisoned-Fraction intervention ratio")

    perturbed = copy.deepcopy(CANONICAL_RC037_BASE)
    perturbed.update(
        {
            "window": [2, 26],
            "compared_bias": ["-5", "12"],
            "ref_bias": ["7", "8"],
            "a_c": ["3", "5"],
            "a_r": ["7", "11"],
            "intervention_cut": 48,
        }
    )
    perturbed_res = eval_dec_temporal_si_bridge_bounds(perturbed)
    _check_eq(perturbed_res["intervention_ratio_after"], ["3", "5"], "poisoned-Fraction shifted cut 48")

    csv_rows = build_temporal_si_bridge_csv_rows()
    _check_eq(len(csv_rows), 9, "poisoned-Fraction live CSV row count")

    # AST audit of RC-037 functions in manual_dec_examples.py
    src_path = REPO_ROOT / "manual" / "engine" / "sectors" / "manual_dec_examples.py"
    tree = ast.parse(src_path.read_text(encoding="utf-8"), filename=str(src_path))
    rc037_funcs = {
        "_parse_trit_pair",
        "_fmt_trit_pair",
        "_parse_strict_int_cuts",
        "_parse_int_window",
        "_count_post_anchor_in_half_open_window",
        "_parse_nonneg_int_list",
        "_step_cut40_causal_intervention",
        "_validate_causal_capacity_trace",
        "_parse_observed_advance_entry",
        "_eval_observed_advance_block",
        "eval_dec_temporal_si_bridge_bounds",
        "build_temporal_si_bridge_csv_rows",
    }
    found_funcs: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in rc037_funcs:
            found_funcs.add(node.name)
            for sub in ast.walk(node):
                _check(not isinstance(sub, ast.Assert), f"bare assert in {node.name}")
                if isinstance(sub, ast.Name):
                    _check(sub.id != "Fraction", f"forbidden Fraction symbol in {node.name}")
                if isinstance(sub, ast.Constant):
                    _check(not isinstance(sub.value, float), f"forbidden float literal in {node.name}")
                    if isinstance(sub.value, str):
                        _check(
                            sub.value not in {"6/5", "2/5", "3/2", "2/3", "768/29", "-5/29", "3264/151", "-49/151", "7/17", "-1/2"},
                            f"hardcoded computed numeric string {sub.value!r} in {node.name}",
                        )
    _check_eq(found_funcs, rc037_funcs, "RC-037 function set audited in AST")


# =============================================================================
# 3. Adversarial Error-Class Parity Matrix (S2 Python vs S4 Rust)
# =============================================================================


def _build_error_parity_matrix() -> list[tuple[str, dict[str, Any], type[Exception]]]:
    cases: list[tuple[str, dict[str, Any], type[Exception]]] = []

    def _err(name: str, overrides: dict[str, Any], exc_cls: type[Exception]) -> None:
        cfg = copy.deepcopy(CANONICAL_RC037_BASE)
        cfg.update(overrides)
        cases.append((name, cfg, exc_cls))

    # Explicit null across ALL optional top-level keys -> TypeError
    for opt_key in (
        "window",
        "compared_bias",
        "ref_bias",
        "rcd_rd",
        "rcd_c_reflections",
        "rcd_r_reflections",
        "a_c",
        "a_r",
        "causal_window",
        "causal_outer_plus",
        "causal_outer_minus",
        "intervention_cut",
        "observed_advance",
    ):
        _err(f"explicit_null_opt_{opt_key}", {opt_key: None}, TypeError)

    # Explicit null inside observed_advance subkeys & required keys -> TypeError
    _err("explicit_null_oa_compared", {"observed_advance": {"compared": None}}, TypeError)
    _err("explicit_null_oa_signed_control", {"observed_advance": {"signed_control": None}}, TypeError)
    _err("explicit_null_req_compared_cuts", {"compared_cuts": None}, TypeError)
    _err("explicit_null_req_f_cs_hz", {"f_cs_hz": None}, TypeError)
    _err("explicit_null_req_field_a", {"field_a": None}, TypeError)

    # Missing required key -> ValueError
    missing_fb = copy.deepcopy(CANONICAL_RC037_BASE)
    del missing_fb["field_b"]
    cases.append(("missing_required_field_b", missing_fb, ValueError))

    # Type-before-value precedence: [10, 5, "bad"] -> TypeError (not ValueError!)
    _err("type_before_monotonic_compared_cuts", {"compared_cuts": [10, 5, "bad"]}, TypeError)
    _err("type_before_monotonic_ref_cuts_bool", {"ref_cuts": [10, 5, True]}, TypeError)
    _err("type_before_monotonic_causal_outer_plus", {"causal_outer_plus": [50, 20, "bad"]}, TypeError)
    _err("type_before_monotonic_causal_outer_minus", {"causal_outer_minus": [40, 10, False]}, TypeError)

    # Bool & mixed-type rejections -> TypeError
    _err("bool_f_cs_hz", {"f_cs_hz": True}, TypeError)
    _err("bool_intervention_cut", {"intervention_cut": False}, TypeError)
    _err("bool_in_window", {"window": [False, 30]}, TypeError)
    _err("mixed_pair_compared_bias", {"compared_bias": ["1", 4]}, TypeError)
    _err("bool_pair_a_c", {"a_c": [True, 1]}, TypeError)
    _err("bad_str_in_rcd_c_reflections", {"rcd_c_reflections": [1, "bad"]}, TypeError)

    # Pair format & denominator errors -> ValueError
    _err("pair_wrong_len_a_r", {"a_r": ["1", "2", "3"]}, ValueError)
    _err("pair_zero_den_compared_bias", {"compared_bias": ["1", "0"]}, ValueError)
    _err("pair_neg_den_ref_bias", {"ref_bias": ["1", "-4"]}, ValueError)
    _err("pair_non_numeric_str", {"compared_bias": ["abc", "4"]}, ValueError)
    _err("pair_plus_sign_noncanonical", {"compared_bias": ["+1", "4"]}, ValueError)
    _err("pair_leading_zero_noncanonical", {"a_c": ["01", "4"]}, ValueError)
    _err("field_a_wrong_len_1", {"field_a": [58]}, ValueError)
    _err("field_b_wrong_len_3", {"field_b": [151, 102, 1]}, ValueError)
    _err("window_wrong_len_3", {"window": [0, 15, 30]}, ValueError)
    _err("oa_not_a_dict_list", {"observed_advance": []}, TypeError)
    _err(
        "oa_winding_str_type_error",
        {"observed_advance": {"signed_control": {"winding": "0", "phase_start": ["0", "1"], "phase_end": ["1", "2"]}}},
        TypeError,
    )
    _err(
        "oa_winding_bool_type_error",
        {"observed_advance": {"signed_control": {"winding": False, "phase_start": ["0", "1"], "phase_end": ["1", "2"]}}},
        TypeError,
    )
    _err(
        "oa_phase_start_mixed_pair_type_error",
        {"observed_advance": {"signed_control": {"winding": 0, "phase_start": [1, "4"], "phase_end": ["1", "2"]}}},
        TypeError,
    )

    # < 2 in-window closures, boundary exclusion, monotonicity, invalid windows -> ValueError
    _err("lt2_in_window_compared", {"window": [2, 15]}, ValueError)
    _err("lt2_in_window_anchor_outside_only_one_inside", {"compared_cuts": [0, 10], "window": [0, 30]}, ValueError)
    _err("lt2_in_window_ref_right_boundary", {"window": [2, 21]}, ValueError)
    _err("zero_in_window_left_open_at_26", {"window": [26, 40]}, ValueError)
    _err("non_strict_duplicate_cut", {"compared_cuts": [2, 10, 10, 26]}, ValueError)
    _err("decreasing_cuts", {"ref_cuts": [22, 12, 2]}, ValueError)
    _err("single_cut_len_lt_2", {"compared_cuts": [2]}, ValueError)
    _err("degenerate_window_eq", {"window": [30, 30]}, ValueError)
    _err("inverted_window_gt", {"window": [30, 0]}, ValueError)

    # Zero / negative gains & domain constraints -> ValueError
    _err("zero_gain_a_c", {"a_c": ["0", "1"]}, ValueError)
    _err("negative_gain_a_c", {"a_c": ["-1", "2"]}, ValueError)
    _err("zero_gain_a_r", {"a_r": ["0", "1"]}, ValueError)
    _err("negative_gain_a_r", {"a_r": ["-3", "5"]}, ValueError)
    _err("zero_f_cs_hz", {"f_cs_hz": 0}, ValueError)
    _err("negative_cal_ref", {"cal_ref": -1}, ValueError)
    _err("zero_field_a_cal", {"field_a": [0, 48]}, ValueError)
    _err("negative_field_b_val", {"field_b": [151, -1]}, ValueError)
    _err("zero_rcd_rd", {"rcd_rd": 0}, ValueError)
    _err("negative_rcd_c_reflection", {"rcd_c_reflections": [1, -1]}, ValueError)

    # Observed-advance domain & split continuity violations -> ValueError
    _err(
        "oa_phase_start_eq_one",
        {"observed_advance": {"signed_control": {"winding": 0, "phase_start": ["1", "1"], "phase_end": ["1", "4"]}}},
        ValueError,
    )
    _err(
        "oa_phase_end_gt_one",
        {"observed_advance": {"signed_control": {"winding": 0, "phase_start": ["0", "1"], "phase_end": ["5", "4"]}}},
        ValueError,
    )
    _err(
        "oa_phase_start_negative",
        {"observed_advance": {"signed_control": {"winding": 0, "phase_start": ["-1", "4"], "phase_end": ["1", "4"]}}},
        ValueError,
    )
    _err(
        "oa_negative_winding",
        {"observed_advance": {"signed_control": {"winding": -1, "phase_start": ["0", "1"], "phase_end": ["1", "2"]}}},
        ValueError,
    )
    _err(
        "oa_nonpositive_ref_advance_zero",
        {"observed_advance": {"reference": {"winding": 0, "phase_start": ["1", "2"], "phase_end": ["1", "2"]}}},
        ValueError,
    )
    _err(
        "oa_nonpositive_ref_advance_neg",
        {"observed_advance": {"reference": {"winding": 0, "phase_start": ["3", "4"], "phase_end": ["1", "4"]}}},
        ValueError,
    )
    _err(
        "oa_discontinuous_split_midpoint",
        {
            "observed_advance": {
                "split_left": {"winding": 2, "phase_start": ["2", "3"], "phase_end": ["1", "2"]},
                "split_right": {"winding": 2, "phase_start": ["5", "6"], "phase_end": ["1", "6"]},
            }
        },
        ValueError,
    )
    _err(
        "oa_mismatched_split_start",
        {
            "observed_advance": {
                "split_left": {"winding": 2, "phase_start": ["1", "3"], "phase_end": ["5", "6"]},
            }
        },
        ValueError,
    )
    _err(
        "oa_mismatched_split_end",
        {
            "observed_advance": {
                "split_right": {"winding": 2, "phase_start": ["5", "6"], "phase_end": ["1", "3"]},
            }
        },
        ValueError,
    )
    _err(
        "oa_mismatched_split_winding_sum",
        {
            "observed_advance": {
                "split_left": {"winding": 1, "phase_start": ["2", "3"], "phase_end": ["5", "6"]},
                "split_right": {"winding": 2, "phase_start": ["5", "6"], "phase_end": ["1", "6"]},
            }
        },
        ValueError,
    )
    _err("oa_unknown_key", {"observed_advance": {"bogus": {}}}, ValueError)
    _err(
        "oa_missing_entry_key",
        {"observed_advance": {"signed_control": {"winding": 0, "phase_start": ["0", "1"]}}},
        ValueError,
    )

    # Out-of-range intervention_cut & invalid causal window/schedules -> ValueError
    _err("intervention_cut_eq_lo", {"intervention_cut": 0}, ValueError)
    _err("intervention_cut_eq_hi", {"intervention_cut": 100}, ValueError)
    _err("intervention_cut_lt_lo", {"intervention_cut": -5}, ValueError)
    _err("intervention_cut_gt_hi", {"intervention_cut": 101}, ValueError)
    _err("causal_window_degenerate", {"causal_window": [50, 50]}, ValueError)
    _err("causal_window_inverted", {"causal_window": [100, 0]}, ValueError)
    _err("causal_window_exceeds_max_span", {"causal_window": [0, 100001]}, ValueError)
    _err("causal_outer_minus_only_at_lo_excluded", {"causal_outer_minus": [0]}, ValueError)
    _err("causal_outer_minus_above_hi", {"causal_outer_minus": [101]}, ValueError)
    _err("causal_outer_plus_empty", {"causal_outer_plus": []}, ValueError)
    _err("causal_outer_plus_duplicate", {"causal_outer_plus": [16, 16, 48]}, ValueError)

    return cases


def test_s2_and_s4_error_class_parity_matrix(aod_core_bin: Path) -> None:
    """Verify S2 Python and S4 Rust agree on exact TypeError vs ValueError across adversarial inputs."""
    matrix = _build_error_parity_matrix()
    _check(len(matrix) >= 60, f"expected >= 60 error parity cases, got {len(matrix)}")

    for case_name, payload, expected_cls in matrix:
        s2_raised: type[BaseException] | None = None
        s2_msg = ""
        try:
            eval_dec_temporal_si_bridge_bounds(copy.deepcopy(payload))
        except Exception as exc:  # noqa: BLE001
            s2_raised = type(exc)
            s2_msg = str(exc)

        _check(
            s2_raised is expected_cls,
            f"S2 error-class mismatch on {case_name!r}: expected {expected_cls.__name__}, "
            f"got {s2_raised.__name__ if s2_raised else 'NO_ERROR'} ({s2_msg})",
        )

        proc = _eval_s4(aod_core_bin, payload)
        _check(
            proc.returncode != 0,
            f"S4 unexpectedly succeeded on invalid case {case_name!r}; stdout={proc.stdout!r}",
        )
        rust_cls = _parse_rust_error_class(proc.stderr)
        _check(
            rust_cls == expected_cls.__name__,
            f"S4 error-class mismatch on {case_name!r}: expected {expected_cls.__name__}, "
            f"got {rust_cls!r} (stderr={proc.stderr!r})",
        )


# =============================================================================
# 4. Cross-Artifact Parity (Engine -> CSV -> Figure 10 -> Manual §7 & §2)
# =============================================================================


def test_rc037_engine_csv_and_vector_live_parity(aod_core_bin: Path) -> None:
    """Verify live RC-037 engine -> 9-row CSV -> rational_core.jsonl -> S4 exact parity."""
    csv_path = REPO_ROOT / "manual" / "data" / "boundary_sadar" / "temporal_si_bridge_dec_ledger.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        disk_cols = list(reader.fieldnames or [])
        disk_rows = list(reader)

    expected_cols = [
        "stage_id",
        "boundary_B",
        "lineage_pair",
        "delta_bip",
        "exact_quantity",
        "reverse_or_resid",
        "status_gate",
    ]
    _check_eq(disk_cols, expected_cols, "temporal_si_bridge_dec_ledger.csv columns")
    _check_eq(len(disk_rows), 9, "temporal_si_bridge_dec_ledger.csv row count")

    live_rows = build_temporal_si_bridge_csv_rows()
    _check_eq(disk_rows, live_rows, "disk CSV vs live build_temporal_si_bridge_csv_rows()")

    expected_stage_ids = [
        "T1_pair_closures",
        "T2_unwrapped_lag",
        "T3_cs133_bridge",
        "T4_transfer_field_A",
        "T5_transfer_field_B",
        "T6_cut40_intervention",
        "T7_directional_rcd",
        "T8_observed_advance_si",
        "T9_causal_disconnect_control",
    ]
    _check_eq([r["stage_id"] for r in disk_rows], expected_stage_ids, "CSV stage_id order")

    # Cross-check CSV values directly against S2 & S4 canonical outputs
    s2 = eval_dec_temporal_si_bridge_bounds(copy.deepcopy(CANONICAL_RC037_BASE))
    proc = _eval_s4(aod_core_bin, CANONICAL_RC037_BASE)
    _check(proc.returncode == 0, f"S4 canonical run failed: {proc.stderr}")
    s4 = json.loads(proc.stdout)
    _check_eq(s2, s4, "S2 vs S4 canonical output")

    def _pair_str(p: list[str]) -> str:
        return p[0] if p[1] == "1" else f"{p[0]}/{p[1]}"

    by_stage = {r["stage_id"]: r for r in disk_rows}
    _check_eq(by_stage["T1_pair_closures"]["boundary_B"], "B_pair(0,30]", "T1 boundary")
    _check_eq(by_stage["T1_pair_closures"]["exact_quantity"], _pair_str(s4["biz_c_over_r"]), "T1 exact_quantity")
    _check_eq(by_stage["T1_pair_closures"]["reverse_or_resid"], _pair_str(s4["biz_r_over_c"]), "T1 reverse")
    _check_eq(by_stage["T2_unwrapped_lag"]["exact_quantity"], _pair_str(s4["lag_forward"]), "T2 lag_forward")
    _check_eq(by_stage["T2_unwrapped_lag"]["reverse_or_resid"], _pair_str(s4["lag_reverse"]), "T2 lag_reverse")
    _check_eq(by_stage["T3_cs133_bridge"]["exact_quantity"], _pair_str(s4["T_seconds"]), "T3 T_seconds")
    _check_eq(by_stage["T3_cs133_bridge"]["reverse_or_resid"], _pair_str(s4["nu_bar_hz"]), "T3 nu_bar_hz")
    _check_eq(by_stage["T4_transfer_field_A"]["exact_quantity"], _pair_str(s4["transfer_A_pred"]), "T4 pred")
    _check_eq(by_stage["T4_transfer_field_A"]["reverse_or_resid"], _pair_str(s4["transfer_A_rel_resid"]), "T4 resid")
    _check_eq(by_stage["T5_transfer_field_B"]["exact_quantity"], _pair_str(s4["transfer_B_pred"]), "T5 pred")
    _check_eq(by_stage["T5_transfer_field_B"]["reverse_or_resid"], _pair_str(s4["transfer_B_rel_resid"]), "T5 resid")
    _check_eq(by_stage["T6_cut40_intervention"]["exact_quantity"], _pair_str(s4["intervention_ratio_before"]), "T6 before")
    _check_eq(by_stage["T6_cut40_intervention"]["reverse_or_resid"], _pair_str(s4["intervention_ratio_after"]), "T6 after")
    _check_eq(by_stage["T7_directional_rcd"]["exact_quantity"], str(s4["rcd_c_given_r"]), "T7 rcd_c|r")
    _check_eq(by_stage["T7_directional_rcd"]["reverse_or_resid"], str(s4["rcd_r_given_c"]), "T7 rcd_r|c")
    _check_eq(by_stage["T8_observed_advance_si"]["exact_quantity"], _pair_str(s4["observed_advance_ratio"]), "T8 ratio")
    _check_eq(by_stage["T8_observed_advance_si"]["reverse_or_resid"], _pair_str(s4["observed_advance_signed"]), "T8 signed")
    _check_eq(by_stage["T9_causal_disconnect_control"]["boundary_B"], "B_causal_hostile(prefix<=39)", "T9 prefix")
    _check_eq(by_stage["T9_causal_disconnect_control"]["exact_quantity"], _pair_str(s4["intervention_ratio_before"]), "T9 ratio")

    # Cross-check RC-037 vector & global 53-vector / 100 source_binding invariants
    vec_dir = REPO_ROOT / "manual" / "engine" / "vectors"
    rc_vectors = [
        json.loads(line)
        for line in (vec_dir / "rational_core.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sd_vectors = [
        json.loads(line)
        for line in (vec_dir / "symbolic_and_display.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _check_eq(len(rc_vectors), 45, "rational_core.jsonl vector count")
    _check_eq(len(sd_vectors), 8, "symbolic_and_display.jsonl vector count")
    all_vectors = rc_vectors + sd_vectors
    _check_eq(len(all_vectors), 53, "total golden vector count across JSONL suites")

    total_sb = sum(
        len([part for part in str(v.get("source_binding", "")).split(";") if part.strip()])
        for v in all_vectors
    )
    _check_eq(total_sb, 100, "total source_binding component count across all 53 vectors")

    rc037_matches = [v for v in rc_vectors if v.get("case_id") == "RC-037"]
    _check_eq(len(rc037_matches), 1, "unique RC-037 vector in rational_core.jsonl")
    rc037_vec = rc037_matches[0]
    _check_eq(rc037_vec.get("operation"), "dec_temporal_si_bridge_bounds", "RC-037 operation")
    expected_outcome = rc037_vec.get("expected_outcome")
    _check(isinstance(expected_outcome, dict), "RC-037 expected_outcome must be a dict")
    _check_eq(expected_outcome.get("status"), "OK", "RC-037 expected_outcome.status")
    vec_exact = expected_outcome.get("exact_value")
    _check(isinstance(vec_exact, dict), "RC-037 expected_outcome.exact_value must be a dict")
    _check_eq(len(vec_exact), 28, "RC-037 exact_value key count (14 legacy + 14 new)")

    vec_inputs = rc037_vec.get("inputs")
    _check(isinstance(vec_inputs, dict), "RC-037 inputs must be a dict")
    s2_from_vec = eval_dec_temporal_si_bridge_bounds(copy.deepcopy(vec_inputs))
    s4_vec_proc = _eval_s4(aod_core_bin, vec_inputs)
    _check(s4_vec_proc.returncode == 0, f"S4 failed on RC-037 vector inputs: {s4_vec_proc.stderr}")
    s4_from_vec = json.loads(s4_vec_proc.stdout)
    _check_eq(vec_exact, s2_from_vec, "RC-037 vector exact_value vs S2")
    _check_eq(vec_exact, s4_from_vec, "RC-037 vector exact_value vs S4")
    _check_eq(vec_exact, s2, "RC-037 vector exact_value vs canonical S2")

    # End-to-end Rust S4 golden-vector + zero-float/zero-unsafe/zero-dep crate policy check
    verify_proc = subprocess.run(
        [
            str(aod_core_bin),
            "--verify-vectors",
            "--check-zero-float",
            "--repo-root",
            str(REPO_ROOT),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    _check(
        verify_proc.returncode == 0,
        f"aod-core --verify-vectors --check-zero-float failed (rc={verify_proc.returncode}): "
        f"{verify_proc.stderr}\n{verify_proc.stdout}",
    )


def test_manual_typst_and_figure10_cross_artifact_invariants() -> None:
    """Audit Figure 10, Manual §7, and Manual §2 against all Phase 3 invariants."""
    reg = json.loads((REPO_ROOT / "typst" / "lib" / "main_registry.json").read_text(encoding="utf-8"))
    main_entries = set(reg["entries"].keys())

    fig10_path = REPO_ROOT / "typst" / "lib" / "figures" / "manual" / "temporal_si_bridge_feynman.typ"
    s7_path = REPO_ROOT / "typst" / "manual" / "sections" / "03_temporal_observation.typ"
    s2_path = REPO_ROOT / "typst" / "manual" / "sections" / "00_native_closure_wave_temporal_fixtures.typ"

    fig10 = fig10_path.read_text(encoding="utf-8")
    s7 = s7_path.read_text(encoding="utf-8")
    s2 = s2_path.read_text(encoding="utf-8")

    # Forbidden regressions across all three Typst files
    forbidden_patterns = (
        (r"\[\s*1\s*,\s*30\s*\]", "contradictory closed window [1, 30]"),
        (r"Held-out\s+obs\s*=\s*26", "incorrect held-out obs = 26"),
        (r"Held-out\s+obs\s*=\s*21", "incorrect held-out obs = 21"),
        (r"1[Ss]\s*[-–—]\s*2[Ss]", "erroneous Hydrogen 1S-2S chain"),
        (r"\bk\s*(?:<=|lt\.eq|≤)\s*40\b", "off-by-one prefix k <= 40"),
    )
    for fname, content in (
        ("temporal_si_bridge_feynman.typ", fig10),
        ("03_temporal_observation.typ", s7),
        ("00_native_closure_wave_temporal_fixtures.typ", s2),
    ):
        for pat, desc in forbidden_patterns:
            _check(
                re.search(pat, content) is None,
                f"{fname} contains forbidden regression ({desc}): matched /{pat}/",
            )

    # Figure 10 live CSV bindings (all 9 rows) & scientific anchors
    _check(
        'csv("/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv", row-type: dictionary)' in fig10,
        "temporal_si_bridge_feynman.typ must bind live to temporal_si_bridge_dec_ledger.csv",
    )
    for idx in range(9):
        _check(f"rows.at({idx})" in fig10, f"temporal_si_bridge_feynman.typ missing live row binding rows.at({idx})")
    for anchor in (
        "RC-037",
        "9,192,631,770",
        "1420.4 MHz",
        "Hellwig 1970",
        "21 cm",
        'N_(0,upright("val")) = 32',
        'B_(upright("pair"))(0, 30]',
        "k <= 39",
        "#r-trA.reverse_or_resid",
        "#r-trB.reverse_or_resid",
        "#r-rcd.exact_quantity",
        "#r-adv.exact_quantity",
        "#r-hos.exact_quantity",
    ):
        _check(anchor in fig10, f"temporal_si_bridge_feynman.typ missing required anchor {anchor!r}")

    # Manual §7: exact 11 labels, 5 verbatim equations, live CSV table, Figure 10 include, GM structure
    _check_eq(_extract_typst_labels(s7), EXPECTED_MANUAL_S7_LABELS, "Manual §7 exact 11 labels")
    for eq_label, verbatim in MANUAL_S7_VERBATIM_EQUATIONS:
        _check(verbatim in s7, f"Manual §7 verbatim equation {eq_label} altered or missing")
    _check(
        'csv("/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv", row-type: dictionary)' in s7,
        "Manual §7 <tab:manual-temporal-dec-bridge> must bind live to temporal_si_bridge_dec_ledger.csv",
    )
    _check(
        '#include "../../lib/figures/manual/temporal_si_bridge_feynman.typ"' in s7,
        "Manual §7 must include temporal_si_bridge_feynman.typ",
    )
    for phrase in (
        "(0, 30]",
        "k lt.eq 39",
        "--consumer-root",
        "RC-037",
        "1420.4",
        "#aod-paragraph[Setup",
        "#aod-paragraph[Derivation",
        "#aod-paragraph[Specialization",
        "#aod-paragraph[Falsification",
    ):
        _check(phrase in s7, f"Manual §7 missing required phrase {phrase!r}")

    # Manual §2: exact 8 labels, live CSV table, GM structure
    _check_eq(_extract_typst_labels(s2), EXPECTED_MANUAL_S2_LABELS, "Manual §2 exact 8 labels")
    _check(
        'csv("/manual/data/boundary_sadar/native_closure_wave_dec_walk.csv", row-type: dictionary)' in s2,
        "Manual §2 <tab:manual-native-closure-dec-walk> must bind live to native_closure_wave_dec_walk.csv",
    )
    for phrase in (
        "RC-033",
        "#aod-paragraph[Setup",
        "#aod-paragraph[Derivation",
        "#aod-paragraph[Specialization",
        "#aod-paragraph[Falsification",
    ):
        _check(phrase in s2, f"Manual §2 missing required phrase {phrase!r}")

    # Every #mainequation / #mainsection / #mainappendix citation in §2 and §7 must resolve in main_registry.json
    for fname, content in (("00_native_closure_wave_temporal_fixtures.typ", s2), ("03_temporal_observation.typ", s7)):
        refs = _extract_main_refs(content)
        _check(len(refs) > 0, f"{fname} expected nonzero Main cross-references")
        for macro, raw_target in refs:
            _check(raw_target.startswith("main:"), f"{fname} #{macro} target {raw_target!r} missing 'main:' prefix")
            key = raw_target[len("main:") :]
            _check(key in main_entries, f"{fname} #{macro}({raw_target!r}) unresolved in main_registry.json")


# =============================================================================
# 5. Frozen Authority SHA-256 Immutability Check
# =============================================================================


def test_frozen_temporal_authorities_sha256_immutable() -> None:
    """Verify SHA-256 digests of all 4 frozen temporal authorities match pinned values and manifests."""
    for rel_path, pinned_digest in PINNED_FROZEN_SHA256.items():
        full_path = REPO_ROOT / rel_path
        _check(full_path.is_file(), f"frozen authority missing: {rel_path}")
        actual = _sha256_file(full_path)
        _check_eq(actual, pinned_digest, f"frozen authority SHA-256 ({rel_path})")

    # Cross-check against internal repository manifests/provenance pins
    manifest_text = (REPO_ROOT / "typst" / "manifest.json").read_text(encoding="utf-8")
    for rel_path in (
        "manual/data/temporal_observation/temporal.json",
        "manual/data/experimental_comparison/experimental_input_comparison.json",
    ):
        _check(
            PINNED_FROZEN_SHA256[rel_path] in manifest_text,
            f"typst/manifest.json does not contain pinned digest for {rel_path}",
        )

    anchor_inputs_text = (REPO_ROOT / "manual" / "data" / "temporal_anchor" / "inputs.json").read_text(encoding="utf-8")
    for rel_path in (
        "manual/scripts/aod_temporal_observation.py",
        "manual/scripts/aod_temporal_anchor.py",
    ):
        _check(
            PINNED_FROZEN_SHA256[rel_path] in anchor_inputs_text,
            f"manual/data/temporal_anchor/inputs.json does not contain pinned digest for {rel_path}",
        )


# =============================================================================
# 6. End-to-End Typst PDF Build + 144 ppi pdftoppm Render Check
# =============================================================================


def _validate_png_144ppi(png_path: Path, label: str) -> None:
    _check(png_path.is_file(), f"{label}: rendered PNG missing at {png_path}")
    data = png_path.read_bytes()
    _check(len(data) > 10_000, f"{label}: PNG suspiciously small ({len(data)} bytes)")
    _check(data[:8] == b"\x89PNG\r\n\x1a\n", f"{label}: invalid PNG signature")
    _check(data[12:16] == b"IHDR", f"{label}: missing PNG IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    _check(
        width >= 1000 and height >= 1200,
        f"{label}: expected 144 ppi page dimensions >= 1000x1200, got {width}x{height}",
    )


def _extract_pdf_pages_text(pdf_path: Path) -> list[str]:
    proc = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        cwd=str(REPO_ROOT),
        env=_tool_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    _check(proc.returncode == 0, f"pdftotext failed on {pdf_path}: {proc.stderr}")
    pages = proc.stdout.split("\x0c")
    if pages and pages[-1] == "":
        pages.pop()
    _check(len(pages) > 0, f"pdftotext produced 0 pages for {pdf_path}")
    return pages


def test_end_to_end_typst_pdf_build_and_144ppi_png_render() -> None:
    """Build publication PDFs with --check-registry, verify text & 144 ppi PNG renders, then clean up."""
    build_root = REPO_ROOT / "_build"
    build_existed_before = build_root.exists()
    outdir = build_root / "qa_p3_pub"
    env = _tool_env()

    try:
        build_proc = subprocess.run(
            [
                sys.executable,
                "-B",
                str(REPO_ROOT / "scripts" / "build_publication.py"),
                "--outdir",
                str(outdir),
                "--check-registry",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        _check(
            build_proc.returncode == 0,
            f"build_publication.py --check-registry failed (rc={build_proc.returncode}):\n"
            f"STDOUT:\n{build_proc.stdout}\nSTDERR:\n{build_proc.stderr}",
        )

        main_pdf = outdir / "main.pdf"
        manual_pdf = outdir / "manual.pdf"
        for pdf_path in (main_pdf, manual_pdf):
            _check(pdf_path.is_file(), f"missing compiled PDF: {pdf_path}")
            head = pdf_path.read_bytes()[:5]
            _check_eq(head, b"%PDF-", f"PDF header ({pdf_path.name})")

        # Locate Main §4 tail page via main_registry.json and verify rendered text
        reg = json.loads((REPO_ROOT / "typst" / "lib" / "main_registry.json").read_text(encoding="utf-8"))
        tick_page = int(reg["entries"]["subsec:duon-tick-click"]["page"])
        cont_page = int(reg["entries"]["subsec:duon-continuity"]["page"])
        sec4_start_page = int(reg["entries"]["sec:wave-state-relational-time"]["page"])

        main_pages = _extract_pdf_pages_text(main_pdf)
        _check(1 <= sec4_start_page <= len(main_pages), f"Main §4 start page out of range: {sec4_start_page}")
        _check(1 <= tick_page <= len(main_pages), f"Tick/click page out of range: {tick_page}")
        _check(1 <= cont_page <= len(main_pages), f"Continuity page out of range: {cont_page}")

        _check("Tick/click" in main_pages[tick_page - 1], f"Main page {tick_page} missing 'Tick/click'")
        _check(
            "Markovian and retained-history continuity" in main_pages[cont_page - 1],
            f"Main page {cont_page} missing 'Markovian and retained-history continuity'",
        )

        # Locate Manual Figure 10 page dynamically and verify rendered PDF text
        manual_pages = _extract_pdf_pages_text(manual_pdf)
        fig10_pages = [
            idx + 1
            for idx, pg in enumerate(manual_pages)
            if "Figure 10" in pg and "RC-037" in pg and "temporal_si_bridge_dec_ledger.csv" in pg
        ]
        _check(len(fig10_pages) == 1, f"expected unique Figure 10 page in manual.pdf, found {fig10_pages}")
        fig10_page = fig10_pages[0]
        fig10_text = manual_pages[fig10_page - 1]

        for required_pdf_str in ("RC-037", "9,192,631,770", "1420.4 MHz", "Hellwig 1970", "5/29", "49/151", "32"):
            _check(
                required_pdf_str in fig10_text,
                f"Figure 10 rendered PDF page {fig10_page} missing {required_pdf_str!r}",
            )
        for forbidden_pdf_str in ("[1, 30]", "Held-out obs = 26", "Held-out obs = 21", "1S-2S", "1S–2S"):
            _check(
                forbidden_pdf_str not in fig10_text,
                f"Figure 10 rendered PDF page {fig10_page} contains forbidden string {forbidden_pdf_str!r}",
            )

        # Render Main §4 pages and Manual Figure 10 page at 144 ppi via pdftoppm
        png_dir = outdir / "png_144"
        png_dir.mkdir(parents=True, exist_ok=True)

        render_targets: list[tuple[str, Path, int]] = [
            ("main_sec4_start", main_pdf, sec4_start_page),
            ("main_sec4_tick", main_pdf, tick_page),
        ]
        if cont_page != tick_page:
            render_targets.append(("main_sec4_cont", main_pdf, cont_page))
        render_targets.append(("manual_fig10", manual_pdf, fig10_page))

        for tag, pdf_path, page_num in render_targets:
            prefix = png_dir / tag
            ppm = subprocess.run(
                [
                    "pdftoppm",
                    "-png",
                    "-r",
                    "144",
                    "-f",
                    str(page_num),
                    "-l",
                    str(page_num),
                    str(pdf_path),
                    str(prefix),
                ],
                cwd=str(REPO_ROOT),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            _check(
                ppm.returncode == 0,
                f"pdftoppm failed for {tag} page {page_num} (rc={ppm.returncode}): {ppm.stderr}",
            )
            matches = sorted(png_dir.glob(f"{tag}-*.png"))
            _check(len(matches) == 1, f"expected 1 PNG for {tag} page {page_num}, got {matches}")
            _validate_png_144ppi(matches[0], f"{tag}_p{page_num}")
    finally:
        shutil.rmtree(outdir, ignore_errors=True)
        if not build_existed_before and build_root.exists():
            try:
                build_root.rmdir()
            except OSError:
                pass


# =============================================================================
# 7. Self-AST Zero-Bare-Assert Check
# =============================================================================


def test_self_ast_zero_bare_asserts() -> None:
    """Verify zero bare `assert` statements (`ast.Assert`) in this QA test file."""
    self_path = Path(__file__).resolve()
    tree = ast.parse(self_path.read_text(encoding="utf-8"), filename=str(self_path))
    assert_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    _check(
        not assert_lines,
        f"{self_path.name} contains forbidden bare `assert` statements at lines: {assert_lines}",
    )
