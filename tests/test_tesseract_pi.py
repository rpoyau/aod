"""Zero-bare-assert verification suite for G6 4D tesseract-to-pi, B3 falsifiers, and cellular fold chain-map algebra.

All checks execute identically under normal Python and ``python3 -B -O`` (zero bare ``assert`` statements).
"""
from __future__ import annotations

import ast
import csv
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess

import pytest

from manual.engine.sectors import manual_dec_examples as mde
from manual.engine.ternary import TritRatio


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "manual" / "data" / "boundary_sadar" / "cell_measures_staircase_fold_dec.csv"
RC_JSONL_PATH = ROOT / "manual" / "engine" / "vectors" / "rational_core.jsonl"
CARGO_MANIFEST = ROOT / "crates" / "aod-core" / "Cargo.toml"


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _pair_to_frac(pair: object) -> Fraction:
    _check(isinstance(pair, list) and len(pair) == 2, f"expected [num, den] pair, got {pair!r}")
    return Fraction(int(pair[0]), int(pair[1]))


def test_zero_bare_asserts_and_zero_forbidden_imports() -> None:
    """AST self-check: zero bare assert nodes in this test and in manual_dec_examples.py."""
    for path in (Path(__file__).resolve(), Path(mde.__file__).resolve()):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        _check(not assert_lines, f"bare assert statements found in {path.name} at lines {assert_lines}")

    mde_tree = ast.parse(Path(mde.__file__).read_text(encoding="utf-8"), filename=mde.__file__)
    forbidden_mods = {"math", "cmath", "numpy", "scipy", "pandas", "matplotlib", "decimal", "importlib", "builtins"}
    for node in ast.walk(mde_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _check(alias.name.split(".")[0] not in forbidden_mods, f"forbidden import in manual_dec_examples: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            _check(node.module.split(".")[0] not in forbidden_mods, f"forbidden from-import in manual_dec_examples: {node.module}")


def test_q4_unit_cube_and_hand_derived_n1_n2_n4_oracles() -> None:
    """Verify Q4 81-cell boundary verification and hand-derived exact 4D oracles at n in {1, 2, 4}."""
    counts, bsq_zero = mde._verify_q4_unit_cube()
    _check(counts == [16, 32, 24, 8, 1], f"unexpected Q4 counts: {counts}")
    _check(bsq_zero == 1, f"expected boundary_sq_zero == 1, got {bsq_zero}")

    # Hand-derived single-orthant counts (N_in, N_out, N3_out)
    hand_oracles = {
        1: (0, 1, 1),
        2: (1, 15, 8),
        4: (32, 160, 51),
    }
    for n, expected in hand_oracles.items():
        got = mde._tesseract_4d_orthant_counts(n)
        _check(got == expected, f"orthant count mismatch at n={n}: got {got}, expected {expected}")

    res = mde.eval_dec_cell_measures_staircase_fold(
        {"edge_num": 3, "edge_den": 2, "levels": [1, 2, 4, 8, 16, 32], "machin_terms": 8}
    )
    t4_by_n = {row["n"]: row for row in res["tesseract_4d"]}

    # n = 1 hand oracle
    r1 = t4_by_n[1]
    _check(_pair_to_frac(r1["V4_minus"]) == Fraction(0), "n=1 V4_minus mismatch")
    _check(_pair_to_frac(r1["V4_plus"]) == Fraction(16), "n=1 V4_plus mismatch")
    _check(_pair_to_frac(r1["V4_width"]) == Fraction(16), "n=1 V4_width mismatch")
    _check(_pair_to_frac(r1["V3_plus"]) == Fraction(8), "n=1 V3_plus mismatch")
    _check(_pair_to_frac(r1["B3_staircase"]) == Fraction(64), "n=1 B3_staircase mismatch")
    _check(_pair_to_frac(r1["B3_stair_minus_4V4plus"]) == Fraction(0), "n=1 B3_stair_minus_4V4plus mismatch")
    _check(r1["B3_tesseract_box"] == 64, "n=1 B3_tesseract_box mismatch")
    _check(_pair_to_frac(r1["B3_box_minus_4V4plus"]) == Fraction(0), "n=1 B3_box_minus_4V4plus mismatch")
    _check(_pair_to_frac(r1["pi_sq_lower"]) == Fraction(0), "n=1 pi_sq_lower mismatch")
    _check(_pair_to_frac(r1["pi_sq_upper"]) == Fraction(32), "n=1 pi_sq_upper mismatch")
    _check(_pair_to_frac(r1["pi_4d_lower"]) == Fraction(0), "n=1 pi_4d_lower mismatch")
    _check(_pair_to_frac(r1["pi_4d_upper"]) == Fraction(6), "n=1 pi_4d_upper mismatch")
    _check(r1["pi_cross_lower"] is None and r1["pi_cross_upper"] is None, "n=1 pi_cross must be None")

    # n = 2 hand oracle
    r2 = t4_by_n[2]
    _check(_pair_to_frac(r2["V4_minus"]) == Fraction(1), "n=2 V4_minus mismatch")
    _check(_pair_to_frac(r2["V4_plus"]) == Fraction(15), "n=2 V4_plus mismatch")
    _check(_pair_to_frac(r2["V4_width"]) == Fraction(14), "n=2 V4_width mismatch")
    _check(_pair_to_frac(r2["V3_plus"]) == Fraction(8), "n=2 V3_plus mismatch")
    _check(_pair_to_frac(r2["B3_staircase"]) == Fraction(64), "n=2 B3_staircase mismatch")
    _check(_pair_to_frac(r2["B3_stair_minus_4V4plus"]) == Fraction(4), "n=2 B3_stair falsifier mismatch")
    _check(r2["B3_tesseract_box"] == 64, "n=2 B3_tesseract_box mismatch")
    _check(_pair_to_frac(r2["B3_box_minus_4V4plus"]) == Fraction(4), "n=2 B3_box falsifier mismatch")
    _check(_pair_to_frac(r2["pi_4d_lower"]) == Fraction(5, 4), "n=2 pi_4d_lower mismatch")
    _check(_pair_to_frac(r2["pi_4d_upper"]) == Fraction(11, 2), "n=2 pi_4d_upper mismatch")
    _check(_pair_to_frac(r2["pi_cross_lower"]) == Fraction(1, 2), "n=2 pi_cross_lower mismatch")
    _check(_pair_to_frac(r2["pi_cross_upper"]) == Fraction(30), "n=2 pi_cross_upper mismatch")

    # n = 4 hand oracle: B3_staircase = 51 != 64 = B3_tesseract_box!
    r4 = t4_by_n[4]
    _check(_pair_to_frac(r4["V4_minus"]) == Fraction(2), "n=4 V4_minus mismatch")
    _check(_pair_to_frac(r4["V4_plus"]) == Fraction(10), "n=4 V4_plus mismatch")
    _check(_pair_to_frac(r4["V4_width"]) == Fraction(8), "n=4 V4_width mismatch")
    _check(_pair_to_frac(r4["V3_plus"]) == Fraction(51, 8), "n=4 V3_plus mismatch")
    _check(_pair_to_frac(r4["B3_staircase"]) == Fraction(51), "n=4 B3_staircase must equal 51")
    _check(_pair_to_frac(r4["B3_stair_minus_4V4plus"]) == Fraction(11), "n=4 B3_stair falsifier mismatch")
    _check(r4["B3_tesseract_box"] == 64, "n=4 B3_tesseract_box must equal 64")
    _check(_pair_to_frac(r4["B3_box_minus_4V4plus"]) == Fraction(24), "n=4 B3_box falsifier mismatch")
    _check(_pair_to_frac(r4["pi_4d_lower"]) == Fraction(2), "n=4 pi_4d_lower mismatch")
    _check(_pair_to_frac(r4["pi_4d_upper"]) == Fraction(9, 2), "n=4 pi_4d_upper mismatch")
    _check(_pair_to_frac(r4["pi_cross_lower"]) == Fraction(16, 15), "n=4 pi_cross_lower mismatch")
    _check(_pair_to_frac(r4["pi_cross_upper"]) == Fraction(10), "n=4 pi_cross_upper mismatch")

    # n = 32 precision check
    r32 = t4_by_n[32]
    _check(_pair_to_frac(r32["pi_4d_lower"]) == Fraction(3047, 1024), "n=32 pi_4d_lower mismatch")
    _check(_pair_to_frac(r32["pi_4d_upper"]) == Fraction(3389, 1024), "n=32 pi_4d_upper mismatch")
    _check(_pair_to_frac(r32["B3_staircase"]) == Fraction(9179, 256), "n=32 B3_staircase mismatch")
    _check(res["axial_4d_gap_positive"] == 1, "axial_4d_gap_positive must equal 1")


def test_b_core_zero_machin_quarantine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove 4D B_core geometry & pi_4d integer-root enclosure never call Machin arctan."""

    def forbidden_arctan(*args: object, **kwargs: object) -> object:
        raise RuntimeError("Machin arctan leaked into B_core 4D geometry construction!")

    monkeypatch.setattr(mde, "_arctan_unit_enclosure", forbidden_arctan)

    disk_bounds = {
        1: (TritRatio.from_ints(0, 1), TritRatio.from_ints(4, 1)),
        2: (TritRatio.from_ints(1, 1), TritRatio.from_ints(4, 1)),
        4: (TritRatio.from_ints(2, 1), TritRatio.from_ints(15, 4)),
        8: (TritRatio.from_ints(41, 16), TritRatio.from_ints(7, 2)),
        16: (TritRatio.from_ints(183, 64), TritRatio.from_ints(107, 32)),
        32: (TritRatio.from_ints(385, 128), TritRatio.from_ints(833, 256)),
    }
    json_rows, _ = mde._compute_tesseract_4d_b_core([1, 2, 4, 8, 16, 32], disk_bounds)
    _check(len(json_rows) == 6, "expected 6 B_core 4D rows without Machin arctan")
    _check(_pair_to_frac(json_rows[-1]["pi_4d_lower"]) == Fraction(3047, 1024), "B_core pi_4d_lower mismatch")
    _check(_pair_to_frac(json_rows[-1]["pi_4d_upper"]) == Fraction(3389, 1024), "B_core pi_4d_upper mismatch")
    _check(
        _pair_to_frac(json_rows[2]["B3_staircase"]) != Fraction(json_rows[2]["B3_tesseract_box"]),
        "B3_staircase at n=4 (51) must remain distinct from B3_tesseract_box (64)",
    )


def test_b3_staircase_vs_box_falsifiers_all_levels() -> None:
    """Verify BOTH B3_staircase and B3_tesseract_box falsifiers across all 6 dyadic levels."""
    res = mde.eval_dec_cell_measures_staircase_fold(
        {"edge_num": 3, "edge_den": 2, "levels": [1, 2, 4, 8, 16, 32], "machin_terms": 8}
    )
    pi_lo = _pair_to_frac(res["pi_lower"])
    pi_hi = _pair_to_frac(res["pi_upper"])
    two_pi_sq_hi = 2 * pi_hi * pi_hi

    prev_b3_stair: Fraction | None = None
    for row in res["tesseract_4d"]:
        n = row["n"]
        v4_p = _pair_to_frac(row["V4_plus"])
        b3_s = _pair_to_frac(row["B3_staircase"])
        b3_s_diff = _pair_to_frac(row["B3_stair_minus_4V4plus"])
        b3_b = Fraction(row["B3_tesseract_box"])
        b3_b_diff = _pair_to_frac(row["B3_box_minus_4V4plus"])
        _check(b3_b == Fraction(64), f"B3_tesseract_box must equal 64 at n={n}")
        _check(b3_s_diff == b3_s - 4 * v4_p, f"B3_stair_minus_4V4plus identity broken at n={n}")
        _check(b3_b_diff == b3_b - 4 * v4_p, f"B3_box_minus_4V4plus identity broken at n={n}")
        _check(b3_s > two_pi_sq_hi, f"B3_staircase must exceed 2*pi^2 at n={n}")
        _check(b3_b > two_pi_sq_hi, f"B3_tesseract_box must exceed 2*pi^2 at n={n}")
        if n == 1:
            _check(b3_s_diff == 0 and b3_b_diff == 0, "at n=1 both differences equal 0")
        else:
            _check(b3_s_diff > 0, f"B3_stair falsifier must be > 0 at n={n}")
            _check(b3_b_diff > 0, f"B3_box falsifier must be > 0 at n={n}")
        if n >= 4:
            _check(b3_s < b3_b, f"for n>=4, B3_staircase ({b3_s}) must be strictly below bounding box 64")
        if prev_b3_stair is not None:
            _check(b3_s <= prev_b3_stair, f"B3_staircase must be nonincreasing at n={n}")
        prev_b3_stair = b3_s

    _check(Fraction(32, 3) * pi_lo - two_pi_sq_hi > 0, "asymptotic gap 32*pi/3 - 2*pi^2 must be positive")


def test_cellular_fold_chain_map_matrix_algebra_and_sign_flip_control() -> None:
    """Verify genuine matrix-derived cellular fold metrics and sign-flip commutation failure."""
    metrics = mde._eval_cellular_fold_chain_map()
    expected = {
        "fold_occupied_area": 2,
        "fold_image_area": 1,
        "fold_retained_multiplicity": 2,
        "fold_oriented_top_sum": 0,
        "fold_seam_cancelled": 1,
        "fold_surviving_boundary_edges": 3,
        "chain_map_commutes": 1,
    }
    _check(metrics == expected, f"fold chain-map metrics mismatch: got {metrics}, expected {expected}")

    # Hostile negative control: flipping orientation of Q_R violates B2_L * F2 == F1 * B2_K
    raised = False
    try:
        mde._eval_cellular_fold_chain_map(flip_right_face_sign=True, enforce_commutation=True)
    except ValueError as exc:
        raised = "B2_L * F2 != F1 * B2_K" in str(exc)
    _check(raised, "sign-flip negative control must raise ValueError on broken chain-map commutation")

    diag = mde._eval_cellular_fold_chain_map(flip_right_face_sign=True, enforce_commutation=False)
    _check(diag["chain_map_commutes"] == 0, f"expected chain_map_commutes=0 under sign flip, got {diag}")
    _check(diag["fold_oriented_top_sum"] == 2, f"expected fold_oriented_top_sum=2 under sign flip, got {diag}")


def test_csv_and_rc035_vector_and_rust_s4_parity() -> None:
    """Verify regenerated CSV (7 preserved 2D + 13 exact 4D columns), RC-035 JSONL, and Python==Rust parity."""
    csv_text = CSV_PATH.read_text(encoding="utf-8")
    expected_csv = mde._rows_to_csv_text(mde.build_cell_measures_csv_rows())
    _check(csv_text == expected_csv, "cell_measures_staircase_fold_dec.csv drifted from build_cell_measures_csv_rows()")

    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        expected_cols = [
            "n",
            "A_minus_exact",
            "A_plus_exact",
            "enclosure_width",
            "C_axial",
            "Cr_minus_2Aplus",
            "A_plus_dec6",
            "V4_minus_exact",
            "V4_plus_exact",
            "V4_width_exact",
            "B3_staircase_exact",
            "B3_stair_minus_4V4plus",
            "B3_tesseract_box",
            "B3_box_minus_4V4plus",
            "pi_4d_lower_exact",
            "pi_4d_upper_exact",
            "pi_4d_lower_dec6",
            "pi_4d_upper_dec6",
            "pi_cross_lower_exact",
            "pi_cross_upper_exact",
        ]
        _check(reader.fieldnames == expected_cols, f"CSV header mismatch: {reader.fieldnames}")
        rows = list(reader)
        _check(len(rows) == 6, f"expected 6 CSV rows, got {len(rows)}")
        _check(rows[0]["pi_cross_lower_exact"] == "null" and rows[0]["pi_cross_upper_exact"] == "null", "n=1 CSV pi_cross must be null")
        _check(rows[2]["B3_staircase_exact"] == "51" and rows[2]["B3_tesseract_box"] == "64", "n=4 CSV B3 values mismatch")

    rc035 = None
    for line in RC_JSONL_PATH.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("case_id") == "RC-035":
            rc035 = rec
            break
    if rc035 is None:
        raise AssertionError("RC-035 missing from rational_core.jsonl")
    py_out = mde.eval_dec_cell_measures_staircase_fold(rc035["inputs"])
    _check(py_out == rc035["expected_outcome"]["exact_value"], "Python S2 output differs from RC-035 golden vector")

    # Cross-language Rust S4 parity check
    env = {**os.environ, "CARGO_TARGET_DIR": str(ROOT / "_build" / "cargo-target")}
    proc = subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(CARGO_MANIFEST),
            "--offline",
            "--locked",
            "--",
            "--eval-op",
            "dec_cell_measures_staircase_fold",
            "--input-json",
            json.dumps(rc035["inputs"]),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    rs_out = json.loads(proc.stdout)
    _check(rs_out == py_out, "Python S2 != Rust S4 output on RC-035!")
