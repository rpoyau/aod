"""Adversarial Role 6 QA & Handoff Verification Suite for Phase P2-tesseract-volume-pi.

Verifies whole-phase invariants across Python S2, Rust S4, aod_cell_measures,
Typst manuscript sections (§5 and §6), native Typst figure rendering, contracts,
digests, and byte-identical normal/-O and debug/release verification harnesses.

All checks use non-strippable ``_check(...)`` assertions so normal Python and
``python3 -B -O`` execute identical verification suites.
"""
from __future__ import annotations

import ast
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from types import ModuleType

import pytest

from manual.engine.sectors import manual_dec_examples as mde
from manual.engine.ternary import TritRatio


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "manual" / "data" / "boundary_sadar" / "cell_measures_staircase_fold_dec.csv"
CELLS_JSON_PATH = ROOT / "manual" / "data" / "cell_measures" / "cells_geometry.json"
CELLS_SCRIPT_PATH = ROOT / "manual" / "scripts" / "aod_cell_measures.py"
CELL_SPEC_PATH = ROOT / "contracts" / "scientific" / "CELL_MEASURE_SPEC.json"
CELL_BINDINGS_PATH = ROOT / "contracts" / "scientific" / "CELL_MAPPING_MATHEMATICAL_BINDINGS.json"
CANONICAL_BINDINGS_PATH = ROOT / "contracts" / "scientific" / "CANONICAL_BINDINGS.json"
RC_JSONL_PATH = ROOT / "manual" / "engine" / "vectors" / "rational_core.jsonl"
CARGO_MANIFEST = ROOT / "crates" / "aod-core" / "Cargo.toml"
RUST_LIB_PATH = ROOT / "crates" / "aod-core" / "src" / "lib.rs"
RUST_DEC_PATH = ROOT / "crates" / "aod-core" / "src" / "manual_dec_ops.rs"
TYPST_S5_PATH = ROOT / "typst" / "manual" / "sections" / "01_cell_measures.typ"
TYPST_S6_PATH = ROOT / "typst" / "manual" / "sections" / "02_mapping_error.typ"
TYPST_FIG_PATH = ROOT / "typst" / "lib" / "figures" / "manual" / "cell_staircase_fold_boundary.typ"
FIG_INVENTORY_PATH = ROOT / "typst" / "figure_inventory.json"
REP_LEDGER_PATH = ROOT / "typst" / "representation_change_ledger.json"
MAIN_REGISTRY_PATH = ROOT / "typst" / "lib" / "main_registry.json"


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _isqrt_floor(n: int) -> int:
    _check(isinstance(n, int) and not isinstance(n, bool) and n >= 0, f"bad isqrt input: {n!r}")
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) // 2)
    while True:
        nxt = (x + n // x) // 2
        if nxt >= x:
            break
        x = nxt
    _check(x * x <= n < (x + 1) * (x + 1), f"isqrt_floor invariant failed for {n}")
    return x


def _isqrt_ceil(n: int) -> int:
    fl = _isqrt_floor(n)
    return fl if fl * fl == n else fl + 1


def _pair_to_frac(val: object, *, name: str) -> Fraction:
    _check(isinstance(val, list) and len(val) == 2, f"{name}: expected [num, den], got {val!r}")
    num_s, den_s = val[0], val[1]
    _check(isinstance(num_s, str) and isinstance(den_s, str), f"{name}: non-string pair {val!r}")
    return Fraction(int(num_s), int(den_s))


def _load_aod_cell_measures() -> ModuleType:
    spec = importlib.util.spec_from_file_location("qa_aod_cell_measures", CELLS_SCRIPT_PATH)
    _check(spec is not None and spec.loader is not None, f"cannot load {CELLS_SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["qa_aod_cell_measures"] = mod
    spec.loader.exec_module(mod)
    return mod


def _cargo_env() -> dict[str, str]:
    return {
        **os.environ,
        "CARGO_TARGET_DIR": os.environ.get("CARGO_TARGET_DIR", str(ROOT / "_build" / "cargo-target")),
    }


def _run_rust_eval(op_name: str, inputs: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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
            op_name,
            "--input-json",
            json.dumps(inputs),
        ],
        cwd=ROOT,
        env=_cargo_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def _load_rc_vector(case_id: str) -> dict[str, object]:
    for line in RC_JSONL_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("case_id") == case_id:
            return rec
    raise AssertionError(f"vector {case_id} missing from {RC_JSONL_PATH}")


def _brute_force_4d_ball(n: int) -> dict[str, object]:
    """Completely independent from-scratch 4D microcell & neighbor-absence oracle."""
    n_sq = n * n
    outer_cells: set[tuple[int, int, int, int]] = set()
    inner_cells: set[tuple[int, int, int, int]] = set()

    for i in range(-n, n):
        mi = min(abs(i), abs(i + 1)) ** 2
        fi = max(abs(i), abs(i + 1)) ** 2
        for j in range(-n, n):
            mij = mi + min(abs(j), abs(j + 1)) ** 2
            fij = fi + max(abs(j), abs(j + 1)) ** 2
            for k in range(-n, n):
                mijk = mij + min(abs(k), abs(k + 1)) ** 2
                fijk = fij + max(abs(k), abs(k + 1)) ** 2
                for m in range(-n, n):
                    near = mijk + min(abs(m), abs(m + 1)) ** 2
                    far = fijk + max(abs(m), abs(m + 1)) ** 2
                    if near < n_sq:
                        outer_cells.add((i, j, k, m))
                    if far <= n_sq:
                        inner_cells.add((i, j, k, m))

    _check(inner_cells.issubset(outer_cells), f"inner 4-ball cells not subset of outer at n={n}")
    _check(len(inner_cells) % 16 == 0, f"inner 4-ball count not 16-orthant symmetric at n={n}")
    _check(len(outer_cells) % 16 == 0, f"outer 4-ball count not 16-orthant symmetric at n={n}")

    # Literal neighbor-absence count of exposed 3-faces in [-n, n)^4
    exposed_3faces = 0
    dirs = (
        (1, 0, 0, 0),
        (-1, 0, 0, 0),
        (0, 1, 0, 0),
        (0, -1, 0, 0),
        (0, 0, 1, 0),
        (0, 0, -1, 0),
        (0, 0, 0, 1),
        (0, 0, 0, -1),
    )
    for c in outer_cells:
        c0, c1, c2, c3 = c
        for d0, d1, d2, d3 in dirs:
            if (c0 + d0, c1 + d1, c2 + d2, c3 + d3) not in outer_cells:
                exposed_3faces += 1

    # Independent orthogonal projection check along each of the 4 axes
    proj_counts = [
        len({c[:axis] + c[axis + 1 :] for c in outer_cells})
        for axis in range(4)
    ]
    _check(len(set(proj_counts)) == 1, f"4D axis projections asymmetric at n={n}: {proj_counts}")
    _check(
        exposed_3faces == 2 * sum(proj_counts),
        f"exposed 3-faces {exposed_3faces} != 2*sum(projections)={2 * sum(proj_counts)} at n={n}",
    )
    _check(exposed_3faces % 64 == 0, f"exposed 3-faces not divisible by 64 at n={n}")

    # Verify inward diagonal shift injection (k_1-1, k_2-1, k_3-1, k_4-1) in positive orthant
    pos_outer = {c for c in outer_cells if c[0] >= 0 and c[1] >= 0 and c[2] >= 0 and c[3] >= 0}
    pos_inner = {c for c in inner_cells if c[0] >= 0 and c[1] >= 0 and c[2] >= 0 and c[3] >= 0}
    _check(len(pos_outer) * 16 == len(outer_cells), f"positive orthant outer mismatch at n={n}")
    _check(len(pos_inner) * 16 == len(inner_cells), f"positive orthant inner mismatch at n={n}")

    interior_shifted = 0
    for c0, c1, c2, c3 in pos_outer:
        if c0 >= 1 and c1 >= 1 and c2 >= 1 and c3 >= 1:
            shifted = (c0 - 1, c1 - 1, c2 - 1, c3 - 1)
            _check(
                shifted in pos_inner,
                f"inward diagonal shift (-1) failed for {(c0, c1, c2, c3)} at n={n}",
            )
            interior_shifted += 1
    _check(
        len(pos_outer) - len(pos_inner) <= len(pos_outer) - interior_shifted <= n**4 - (n - 1) ** 4 <= 4 * n**3,
        f"diagonal shift boundary shell bound violated at n={n}",
    )

    return {
        "N_in_orthant": len(pos_inner),
        "N_out_orthant": len(pos_outer),
        "N3_out_orthant": exposed_3faces // 64,
        "exposed_3face_count": exposed_3faces,
        "V4_minus": Fraction(len(inner_cells), n**4),
        "V4_plus": Fraction(len(outer_cells), n**4),
        "B3_staircase": Fraction(exposed_3faces, n**3),
    }


def _strip_rust_comments_and_strings(src: str) -> str:
    # Remove line comments, block comments, and double-quoted string literals
    no_strings = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    no_block = re.sub(r"/\*.*?\*/", "", no_strings, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", no_block)


def _extract_typst_table_cells(typst_src: str) -> list[list[str]]:
    """Extract the 6 data rows (10 cells each) from the single table(...) in 01_cell_measures.typ."""
    matches = list(re.finditer(r"\btable\s*\(", typst_src))
    _check(
        len(matches) == 1,
        f"01_cell_measures.typ must contain exactly ONE table(...) (zero duplicate 2D table), found {len(matches)}",
    )
    start = matches[0].start()
    tail = typst_src[start:]
    mid_idx = tail.find("midrule,")
    bot_idx = tail.find("bottomrule,")
    _check(mid_idx != -1 and bot_idx != -1 and mid_idx < bot_idx, "table midrule/bottomrule markers missing")
    body = tail[mid_idx + len("midrule,") : bot_idx]

    # Locate the end of table.header(...) before row content begins
    hdr_close = body.find("),")
    _check(hdr_close != -1, "could not locate end of table.header(...) in 01_cell_measures.typ")
    rows_block = body[hdr_close + 2 :]

    parsed_rows: list[list[str]] = []
    for raw_line in rows_block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        cells = re.findall(r"\[([^\]]+)\]", line)
        if cells:
            parsed_rows.append([c.strip() for c in cells])
    return parsed_rows


def _typst_cell_to_fraction(cell_text: str) -> Fraction:
    """Parse a Typst table cell like '51' or '$frac(3047, 1024)$' into exact Fraction."""
    if re.fullmatch(r"-?\d+", cell_text):
        return Fraction(int(cell_text), 1)
    m_frac = re.fullmatch(r"\$\s*frac\(\s*(-?\d+)\s*,\s*(\d+)\s*\)\s*\$", cell_text)
    if m_frac:
        return Fraction(int(m_frac.group(1)), int(m_frac.group(2)))
    m_slash = re.fullmatch(r"\$\s*(-?\d+)\s*slash\s*(\d+)\s*\$", cell_text)
    if m_slash:
        return Fraction(int(m_slash.group(1)), int(m_slash.group(2)))
    m_num = re.fullmatch(r"\$\s*(-?\d+)\s*\$", cell_text)
    if m_num:
        return Fraction(int(m_num.group(1)), 1)
    raise AssertionError(f"unexpected Typst numeric cell syntax: {cell_text!r}")


# =============================================================================
# 1. Global Invariants: Zero Bare Asserts, Zero Floats, std-only Zero-Unsafe Rust
# =============================================================================


def test_qa_zero_bare_asserts_zero_floats_and_rust_core_invariants() -> None:
    """Enforce zero bare asserts, zero floats in engine/Rust, and std-only #![forbid(unsafe_code)]."""
    assert_checked_files = (
        Path(__file__).resolve(),
        ROOT / "tests" / "test_tesseract_pi.py",
        Path(mde.__file__).resolve(),
        ROOT / "manual" / "engine" / "sectors" / "tier1_adapters.py",
    )
    for path in assert_checked_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        _check(not lines, f"bare assert statements in {path.relative_to(ROOT)} at lines {lines}")

    # Zero float literals, zero float() coercions, zero float/scientific imports in manual_dec_examples.py
    mde_path = Path(mde.__file__).resolve()
    mde_tree = ast.parse(mde_path.read_text(encoding="utf-8"), filename=str(mde_path))
    forbidden_mods = {"math", "cmath", "numpy", "scipy", "pandas", "matplotlib", "decimal", "statistics"}
    for node in ast.walk(mde_tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"float literal {node.value!r} in manual_dec_examples.py:{node.lineno}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float":
            raise AssertionError(f"float() call in manual_dec_examples.py:{node.lineno}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                _check(alias.name.split(".")[0] not in forbidden_mods, f"forbidden import {alias.name}")
        if isinstance(node, ast.ImportFrom) and node.module:
            _check(node.module.split(".")[0] not in forbidden_mods, f"forbidden from-import {node.module}")

    # Rust std-only, #![forbid(unsafe_code)], zero float types/literals in manual_dec_ops.rs
    lib_src = RUST_LIB_PATH.read_text(encoding="utf-8")
    _check("#![forbid(unsafe_code)]" in lib_src, "crates/aod-core/src/lib.rs missing #![forbid(unsafe_code)]")

    cargo_toml = CARGO_MANIFEST.read_text(encoding="utf-8")
    dep_match = re.search(r"(?m)^\[dependencies\]\s*\n(.*?)(?=^\[|\Z)", cargo_toml, flags=re.DOTALL)
    if dep_match:
        dep_lines = [
            ln.strip()
            for ln in dep_match.group(1).splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        _check(not dep_lines, f"crates/aod-core/Cargo.toml must have zero external dependencies, found {dep_lines}")

    rust_code = _strip_rust_comments_and_strings(RUST_DEC_PATH.read_text(encoding="utf-8"))
    _check(not re.search(r"\b(?:f32|f64)\b", rust_code), "float type f32/f64 found in manual_dec_ops.rs")
    _check(
        not re.search(r"(?<![A-Za-z0-9_.])\d+\.\d+(?![A-Za-z0-9_.])", rust_code),
        "float literal found in manual_dec_ops.rs",
    )


# =============================================================================
# 2. Independent 4D Brute-Force Oracle (Dyadic & Non-Dyadic) + Shift Proof
# =============================================================================


def test_qa_brute_force_4d_oracle_non_dyadic_and_shift_counterexample() -> None:
    """Cross-verify independent brute-force 4D enumeration against Python S2, Rust S4, and aod_cell_measures."""
    cells = _load_aod_cell_measures()

    # Check both dyadic (1, 2, 4) and adversarial non-dyadic (3) levels against literal 4D enumeration
    for n in (1, 2, 3, 4):
        bf = _brute_force_4d_ball(n)
        expected_triple = (bf["N_in_orthant"], bf["N_out_orthant"], bf["N3_out_orthant"])

        _check(
            mde._tesseract_4d_counts_route_a(n) == expected_triple,
            f"Python S2 Route A != brute-force at n={n}",
        )
        _check(
            mde._tesseract_4d_counts_route_b(n) == expected_triple,
            f"Python S2 Route B != brute-force at n={n}",
        )
        _check(
            mde._tesseract_4d_orthant_counts(n) == expected_triple,
            f"Python S2 orthant_counts != brute-force at n={n}",
        )
        _check(
            cells.tesseract_ball_counts(n) == expected_triple,
            f"aod_cell_measures Route A != brute-force at n={n}",
        )
        _check(
            cells.independent_tesseract_ball_counts(n) == expected_triple,
            f"aod_cell_measures Route B != brute-force at n={n}",
        )

        lvl = cells.tesseract_ball_level(n)
        _check(Fraction(lvl["V4_inner"]) == bf["V4_minus"], f"aod_cell_measures V4_inner mismatch at n={n}")
        _check(Fraction(lvl["V4_outer"]) == bf["V4_plus"], f"aod_cell_measures V4_outer mismatch at n={n}")
        _check(Fraction(lvl["B3_staircase"]) == bf["B3_staircase"], f"aod_cell_measures B3_staircase mismatch at n={n}")

    # Adversarial counterexample proving broken (+1) shift is NOT an injection into inner cells:
    # At n=2, cell (0,0,0,1) is outer (0+0+0+1=1 < 4), while shifted (+1) cell (1,1,1,2)
    # has max corner (2,2,2,3) with squared norm 4+4+4+9=21 > 4 (not inner, not even outer!).
    n_test = 2
    k_outer = (0, 0, 0, 1)
    _check(sum(c * c for c in k_outer) < n_test**2, "sanity: k_outer must be outer")
    broken_plus1 = tuple(c + 1 for c in k_outer)
    _check(
        sum((c + 1) ** 2 for c in broken_plus1) > n_test**2,
        "sanity: +1 shift must fail inner-ball inequality",
    )

    # Adversarial non-dyadic evaluation [1, 2, 3, 4, 5, 6] in BOTH Python S2 and Rust S4
    # proves neither implementation hardcodes a lookup table for {1, 2, 4, 8, 16, 32}.
    non_dyadic_inputs = {"edge_num": 5, "edge_den": 3, "levels": [1, 2, 3, 4, 5, 6], "machin_terms": 6}
    py_non_dyadic = mde.eval_dec_cell_measures_staircase_fold(non_dyadic_inputs)
    rs_proc = _run_rust_eval("dec_cell_measures_staircase_fold", non_dyadic_inputs)
    _check(rs_proc.returncode == 0, f"Rust S4 failed on non-dyadic levels: {rs_proc.stderr}")
    rs_non_dyadic = json.loads(rs_proc.stdout)
    _check(rs_non_dyadic == py_non_dyadic, "Python S2 != Rust S4 on non-dyadic levels [1,2,3,4,5,6]")

    # Verify non-dyadic n=3 exact hand oracle: N_out=54, N3_out=23, B3_staircase=1472/27 < 64
    t4_n3 = [r for r in py_non_dyadic["tesseract_4d"] if r["n"] == 3][0]
    _check(t4_n3["N_out_orthant"] == 54, f"unexpected n=3 N_out_orthant: {t4_n3['N_out_orthant']}")
    _check(t4_n3["N3_out_orthant"] == 23, f"unexpected n=3 N3_out_orthant: {t4_n3['N3_out_orthant']}")
    _check(_pair_to_frac(t4_n3["B3_staircase"], name="n3 B3") == Fraction(1472, 27), "n=3 B3_staircase != 1472/27")
    _check(_pair_to_frac(t4_n3["V4_plus"], name="n3 V4+") == Fraction(32, 3), "n=3 V4_plus != 32/3")
    _check(
        _pair_to_frac(t4_n3["B3_stair_minus_4V4plus"], name="n3 diff") == Fraction(320, 27),
        "n=3 B3_stair_minus_4V4plus != 320/27",
    )


# =============================================================================
# 3. Four-Way G6 Parity, Tightness, B3 Staircase vs 64, and Scope Discipline
# =============================================================================


def test_qa_g6_tesseract_pi_four_way_parity_and_invariants() -> None:
    """Verify exact parity across Python S2, Rust S4, aod_cell_measures, CSV, and RC-035."""
    cells = _load_aod_cell_measures()
    rc035 = _load_rc_vector("RC-035")
    inputs = rc035["inputs"]
    _check(isinstance(inputs, dict), "RC-035 inputs must be dict")

    py_out = mde.eval_dec_cell_measures_staircase_fold(inputs)
    _check(py_out == rc035["expected_outcome"]["exact_value"], "Python S2 != RC-035 expected_outcome")

    rs_proc = _run_rust_eval("dec_cell_measures_staircase_fold", inputs)
    _check(rs_proc.returncode == 0, f"Rust S4 failed on RC-035: {rs_proc.stderr}")
    rs_out = json.loads(rs_proc.stdout)
    _check(rs_out == py_out, "Rust S4 != Python S2 on RC-035")

    report = cells.build_report()
    report_raw = cells.report_bytes(report)
    _check(report_raw == CELLS_JSON_PATH.read_bytes(), "cells_geometry.json bytes mismatch")
    frozen_report = json.loads(CELLS_JSON_PATH.read_text(encoding="utf-8"))
    _check(
        json.loads(report_raw.decode("utf-8")) == frozen_report,
        "aod_cell_measures.build_report() drifted from cells_geometry.json",
    )

    # Scope & negative control checks
    _check(report["G6"]["status"] == "opened_declared_verification_model", "G6 status mismatch")
    _check(
        "not established" in report["G6"]["native_higher_cell_admission"],
        "G6 must explicitly deny native higher-cell admission",
    )
    _check(len(report["negative_controls"]) == 12, f"expected 12 negative controls, got {len(report['negative_controls'])}")
    _check(all(report["negative_controls"].values()), "one or more negative controls failed")
    for key in (
        "tesseract_4d_box_staircase_conflation",
        "tesseract_4d_fake_volume_enclosure",
        "tesseract_4d_refitted_refinement",
    ):
        _check(key in report["negative_controls"], f"missing 4D negative control {key}")

    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    _check(len(csv_rows) == 6, f"expected 6 CSV rows, got {len(csv_rows)}")

    pi_lo = _pair_to_frac(py_out["pi_lower"], name="pi_lower")
    pi_hi = _pair_to_frac(py_out["pi_upper"], name="pi_upper")
    _check(Fraction(314159265, 100000000) < pi_lo < pi_hi < Fraction(314159266, 100000000), "Machin pi bounds off")
    v4_ref_lo = (pi_lo * pi_lo) / 2
    v4_ref_hi = (pi_hi * pi_hi) / 2
    two_pi_sq_hi = 2 * pi_hi * pi_hi

    expected_b3_seq = [
        Fraction(64, 1),
        Fraction(64, 1),
        Fraction(51, 1),
        Fraction(341, 8),
        Fraction(2443, 64),
        Fraction(9179, 256),
    ]

    t4_rows = py_out["tesseract_4d"]
    st_rows = py_out["staircase"]
    g6_levels = report["G6"]["levels"]
    _check(len(t4_rows) == len(g6_levels) == len(csv_rows) == 6, "dyadic level count mismatch")

    prev: dict[str, Fraction | None] | None = None
    for idx, (t4, st, g6, crow) in enumerate(zip(t4_rows, st_rows, g6_levels, csv_rows)):
        n = t4["n"]
        _check(n == st["n"] == g6["n"] == int(crow["n"]) == (1 << idx), f"level alignment mismatch at idx={idx}")

        v4_m = _pair_to_frac(t4["V4_minus"], name=f"V4_minus[{n}]")
        v4_p = _pair_to_frac(t4["V4_plus"], name=f"V4_plus[{n}]")
        v4_w = _pair_to_frac(t4["V4_width"], name=f"V4_width[{n}]")
        v3_p = _pair_to_frac(t4["V3_plus"], name=f"V3_plus[{n}]")
        b3_s = _pair_to_frac(t4["B3_staircase"], name=f"B3_staircase[{n}]")
        b3_s_diff = _pair_to_frac(t4["B3_stair_minus_4V4plus"], name=f"B3_stair_diff[{n}]")
        b3_box = Fraction(t4["B3_tesseract_box"], 1)
        b3_box_diff = _pair_to_frac(t4["B3_box_minus_4V4plus"], name=f"B3_box_diff[{n}]")
        pi_sq_lo = _pair_to_frac(t4["pi_sq_lower"], name=f"pi_sq_lower[{n}]")
        pi_sq_hi = _pair_to_frac(t4["pi_sq_upper"], name=f"pi_sq_upper[{n}]")
        p4_lo = _pair_to_frac(t4["pi_4d_lower"], name=f"pi_4d_lower[{n}]")
        p4_hi = _pair_to_frac(t4["pi_4d_upper"], name=f"pi_4d_upper[{n}]")
        a2_m = _pair_to_frac(st["A_minus"], name=f"A_minus[{n}]")
        a2_p = _pair_to_frac(st["A_plus"], name=f"A_plus[{n}]")

        # Cross-surface exact parity: S2 == G6 (cells_geometry.json) == CSV
        _check(v4_m == Fraction(g6["V4_inner"]) == Fraction(crow["V4_minus_exact"]), f"V4_minus drift at n={n}")
        _check(v4_p == Fraction(g6["V4_outer"]) == Fraction(crow["V4_plus_exact"]), f"V4_plus drift at n={n}")
        _check(v4_w == Fraction(g6["V4_enclosure_width"]) == Fraction(crow["V4_width_exact"]), f"V4_width drift at n={n}")
        _check(v3_p == Fraction(g6["V3_outer"]), f"V3_plus drift at n={n}")
        _check(b3_s == Fraction(g6["B3_staircase"]) == Fraction(crow["B3_staircase_exact"]), f"B3_staircase drift at n={n}")
        _check(
            b3_s_diff == Fraction(g6["B3_stair_minus_4V4plus"]) == Fraction(crow["B3_stair_minus_4V4plus"]),
            f"B3_stair_minus_4V4plus drift at n={n}",
        )
        _check(b3_box == Fraction(64, 1) == Fraction(g6["B3_tesseract_box"]) == Fraction(crow["B3_tesseract_box"]), f"B3_box drift at n={n}")
        _check(
            b3_box_diff == Fraction(g6["B3_box_minus_4V4plus"]) == Fraction(crow["B3_box_minus_4V4plus"]),
            f"B3_box_minus_4V4plus drift at n={n}",
        )
        _check(p4_lo == Fraction(g6["pi_4d_lower"]) == Fraction(crow["pi_4d_lower_exact"]), f"pi_4d_lower drift at n={n}")
        _check(p4_hi == Fraction(g6["pi_4d_upper"]) == Fraction(crow["pi_4d_upper_exact"]), f"pi_4d_upper drift at n={n}")

        # Exact mathematical formulas & tight integer-root checks
        _check(v4_w == v4_p - v4_m, f"V4_width != V4_plus - V4_minus at n={n}")
        _check(v4_w <= Fraction(64, n), f"V4_width {v4_w} exceeds certified 64/n at n={n}")
        _check(v4_m <= v4_ref_lo < v4_ref_hi <= v4_p, f"V4 does not enclose pi^2/2 at n={n}")
        _check(pi_sq_lo == 2 * v4_m and pi_sq_hi == 2 * v4_p, f"pi_sq identity broken at n={n}")

        step = Fraction(1, n * n)
        _check(p4_lo * p4_lo <= pi_sq_lo < (p4_lo + step) ** 2, f"pi_4d_lower not tight isqrt_floor at n={n}")
        if p4_hi * p4_hi != pi_sq_hi:
            _check((p4_hi - step) ** 2 < pi_sq_hi <= p4_hi * p4_hi, f"pi_4d_upper not tight isqrt_ceil at n={n}")
        _check(p4_lo <= pi_lo < pi_hi <= p4_hi, f"pi_4d does not enclose pi at n={n}")

        # Cross-dimensional ratio pi_cross: None/null at n=1, valid enclosure for n>=2
        if n == 1:
            _check(t4["pi_cross_lower"] is None and t4["pi_cross_upper"] is None, "n=1 S2 pi_cross must be None")
            _check(g6["pi_cross_lower"] is None and g6["pi_cross_upper"] is None, "n=1 G6 pi_cross must be None")
            _check(crow["pi_cross_lower_exact"] == "null" and crow["pi_cross_upper_exact"] == "null", "n=1 CSV pi_cross must be null")
            pc_lo, pc_hi = None, None
        else:
            pc_lo = _pair_to_frac(t4["pi_cross_lower"], name=f"pi_cross_lower[{n}]")
            pc_hi = _pair_to_frac(t4["pi_cross_upper"], name=f"pi_cross_upper[{n}]")
            _check(pc_lo == Fraction(g6["pi_cross_lower"]) == Fraction(crow["pi_cross_lower_exact"]), f"pi_cross_lower drift at n={n}")
            _check(pc_hi == Fraction(g6["pi_cross_upper"]) == Fraction(crow["pi_cross_upper_exact"]), f"pi_cross_upper drift at n={n}")
            _check(pc_lo == (2 * v4_m) / a2_p and pc_hi == (2 * v4_p) / a2_m, f"pi_cross formula mismatch at n={n}")
            _check(pc_lo <= pi_lo < pi_hi <= pc_hi, f"pi_cross does not enclose pi at n={n}")

        # Exact exposed 4D staircase 3-boundary B3_staircase = 8 * V3_plus vs box 64
        _check(b3_s == 8 * v3_p == expected_b3_seq[idx], f"B3_staircase sequence mismatch at n={n}: got {b3_s}")
        _check(b3_s == Fraction(64 * t4["N3_out_orthant"], n**3), f"B3_staircase != 64*N3_out/n^3 at n={n}")
        _check(b3_s_diff == b3_s - 4 * v4_p, f"B3_stair_minus_4V4plus mismatch at n={n}")
        _check(b3_box_diff == b3_box - 4 * v4_p, f"B3_box_minus_4V4plus mismatch at n={n}")
        _check(b3_s > two_pi_sq_hi, f"B3_staircase must stay strictly above 2*pi^2 at n={n}")
        if n == 1:
            _check(b3_s_diff == 0 and b3_box_diff == 0, "at n=1 both B3-4V4+ differences must be 0")
        else:
            _check(b3_s_diff > 0 and b3_box_diff > 0, f"B3 falsifier must be strictly positive at n={n}")
        if n >= 4:
            _check(b3_s < b3_box, f"B3_staircase ({b3_s}) must be strictly distinct from 64 at n={n}")

        # Dyadic monotonicity across 1 -> 2 -> 4 -> 8 -> 16 -> 32
        if prev is not None:
            _check(prev["v4_m"] <= v4_m, f"V4_minus regressed at n={n}")
            _check(v4_p <= prev["v4_p"], f"V4_plus regressed at n={n}")
            _check(v4_w < prev["v4_w"], f"V4_width failed strict contraction at n={n}")
            _check(b3_s <= prev["b3_s"], f"B3_staircase increased at n={n}")
            _check(prev["p4_lo"] <= p4_lo, f"pi_4d_lower regressed at n={n}")
            _check(p4_hi <= prev["p4_hi"], f"pi_4d_upper regressed at n={n}")
            if prev["pc_lo"] is not None and pc_lo is not None and prev["pc_hi"] is not None and pc_hi is not None:
                _check(prev["pc_lo"] <= pc_lo and pc_hi <= prev["pc_hi"], f"pi_cross regressed at n={n}")

        prev = {
            "v4_m": v4_m,
            "v4_p": v4_p,
            "v4_w": v4_w,
            "b3_s": b3_s,
            "p4_lo": p4_lo,
            "p4_hi": p4_hi,
            "pc_lo": pc_lo,
            "pc_hi": pc_hi,
        }


# =============================================================================
# 4. Machin Arctan Quarantine from B_core (Runtime + Static AST / Rust Audit)
# =============================================================================


def test_qa_machin_arctan_quarantine_runtime_and_static(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove Machin arctan never leaks upstream into B_core in Python S2, Rust S4, or aod_cell_measures."""
    cells = _load_aod_cell_measures()

    # 1. Runtime quarantine in manual_dec_examples
    def _explode(*args: object, **kwargs: object) -> object:
        raise RuntimeError("FORBIDDEN: Machin arctan reference called inside B_core!")

    monkeypatch.setattr(mde, "_arctan_unit_enclosure", _explode)
    disk_bounds = {
        1: (TritRatio.from_ints(0, 1), TritRatio.from_ints(4, 1)),
        2: (TritRatio.from_ints(1, 1), TritRatio.from_ints(4, 1)),
        4: (TritRatio.from_ints(2, 1), TritRatio.from_ints(15, 4)),
        8: (TritRatio.from_ints(41, 16), TritRatio.from_ints(7, 2)),
        16: (TritRatio.from_ints(183, 64), TritRatio.from_ints(107, 32)),
        32: (TritRatio.from_ints(385, 128), TritRatio.from_ints(833, 256)),
    }
    q4_counts, bsq = mde._verify_q4_unit_cube()
    _check(q4_counts == [16, 32, 24, 8, 1] and bsq == 1, "Q4 B_core check failed under Machin lock")
    json_rows, _ = mde._compute_tesseract_4d_b_core([1, 2, 4, 8, 16, 32], disk_bounds)
    _check(len(json_rows) == 6, "B_core 4D computation failed under Machin lock")
    fold = mde._eval_cellular_fold_chain_map()
    _check(fold["chain_map_commutes"] == 1, "B_core fold check failed under Machin lock")

    # 2. Runtime quarantine in aod_cell_measures (lock every Machin / arctan / reference callable)
    patched_attrs: set[str] = set()
    for attr in dir(cells):
        if any(tok in attr.lower() for tok in ("arctan", "pi_reference", "compare_disk", "compare_tesseract")):
            if callable(getattr(cells, attr)):
                monkeypatch.setattr(cells, attr, _explode)
                patched_attrs.add(attr)
    _check(
        {"pi_reference_bounds", "compare_disk_reference", "compare_tesseract_reference"}.issubset(patched_attrs),
        f"expected reference callables missing on aod_cell_measures; patched={sorted(patched_attrs)}",
    )
    for n in (1, 2, 4, 8, 16, 32):
        lvl = cells.tesseract_ball_level(n)
        _check(lvl["n"] == n, f"aod_cell_measures B_core failed at n={n} under Machin lock")

    # 3. Static AST quarantine in manual_dec_examples.py
    mde_src = Path(mde.__file__).read_text(encoding="utf-8")
    mde_tree = ast.parse(mde_src, filename=str(mde.__file__))
    b_core_funcs = {
        "_cubical_boundary",
        "_verify_q4_unit_cube",
        "_complex_cells_by_dim",
        "_boundary_matrix",
        "_fold_cell_image",
        "_fold_matrix",
        "_eval_cellular_fold_chain_map",
        "_tesseract_4d_counts_route_a",
        "_tesseract_4d_counts_route_b",
        "_tesseract_4d_orthant_counts",
        "_compute_tesseract_4d_b_core",
    }
    funcs_by_name = {
        node.name: node for node in ast.walk(mde_tree) if isinstance(node, ast.FunctionDef)
    }
    for fname in b_core_funcs:
        _check(fname in funcs_by_name, f"missing B_core function {fname} in manual_dec_examples.py")
        for sub in ast.walk(funcs_by_name[fname]):
            if isinstance(sub, ast.Name):
                _check(
                    "arctan" not in sub.id.lower() and "machin" not in sub.id.lower(),
                    f"Machin/arctan token {sub.id!r} leaked into B_core function {fname}",
                )

    # Ordering check inside eval_dec_cell_measures_staircase_fold: B_core strictly precedes Machin
    eval_fn = funcs_by_name["eval_dec_cell_measures_staircase_fold"]
    call_lines: dict[str, list[int]] = {}
    for sub in ast.walk(eval_fn):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
            call_lines.setdefault(sub.func.id, []).append(sub.lineno)
    first_arctan = min(call_lines.get("_arctan_unit_enclosure", [10**9]))
    for core_call in ("_verify_q4_unit_cube", "_compute_tesseract_4d_b_core", "_eval_cellular_fold_chain_map"):
        _check(core_call in call_lines, f"{core_call} not called in eval_dec_cell_measures_staircase_fold")
        _check(
            max(call_lines[core_call]) < first_arctan,
            f"B_core call {core_call} appears after Machin _arctan_unit_enclosure",
        )

    # 4. Static quarantine in Rust manual_dec_ops.rs
    rust_src = RUST_DEC_PATH.read_text(encoding="utf-8")
    op_start = rust_src.find("pub fn op_dec_cell_measures_staircase_fold")
    _check(op_start != -1, "op_dec_cell_measures_staircase_fold missing in manual_dec_ops.rs")
    op_body = rust_src[op_start:]
    idx_q4 = op_body.find("verify_q4_unit_cube()")
    idx_t4 = op_body.find("tesseract_4d_orthant_counts(")
    idx_fold = op_body.find("eval_cellular_fold_chain_map(")
    idx_arctan = op_body.find("arctan_unit_enclosure(")
    _check(
        0 <= idx_q4 < idx_t4 < idx_fold < idx_arctan,
        "Rust op_dec_cell_measures_staircase_fold must run Q4 -> 4D B_core -> fold strictly before Machin arctan",
    )
    # Helper section between verify_q4_unit_cube and op_dec_cell_measures_staircase_fold must never call arctan
    helper_start = rust_src.find("pub fn verify_q4_unit_cube")
    _check(0 <= helper_start < op_start, "Rust B_core helper ordering unexpected")
    _check(
        "arctan_unit_enclosure" not in rust_src[helper_start:op_start],
        "Rust B_core 4D/fold helpers must not reference arctan_unit_enclosure",
    )

    # 5. Static AST quarantine in aod_cell_measures.py
    cm_tree = ast.parse(CELLS_SCRIPT_PATH.read_text(encoding="utf-8"), filename=str(CELLS_SCRIPT_PATH))
    cm_funcs = {node.name: node for node in ast.walk(cm_tree) if isinstance(node, ast.FunctionDef)}
    for fname in (
        "tesseract_ball_counts",
        "independent_tesseract_ball_counts",
        "tesseract_ball_tops",
        "tesseract_ball_level",
    ):
        _check(fname in cm_funcs, f"missing {fname} in aod_cell_measures.py")
        for sub in ast.walk(cm_funcs[fname]):
            if isinstance(sub, ast.Name):
                _check(
                    "arctan" not in sub.id.lower() and "pi_reference" not in sub.id.lower(),
                    f"reference token {sub.id!r} leaked into aod_cell_measures.{fname}",
                )


def test_qa_adversarial_invalid_inputs_rejected_python_and_rust() -> None:
    """Verify invalid / boundary-violating RC-035 inputs fail cleanly in BOTH Python S2 and Rust S4."""
    base = {"edge_num": 3, "edge_den": 2, "levels": [1, 2], "machin_terms": 4}
    bad_payloads = [
        {**base, "levels": []},
        {**base, "levels": [0]},
        {**base, "levels": [-2]},
        {**base, "edge_num": 0},
        {**base, "edge_den": 0},
        {**base, "machin_terms": 0},
    ]
    for payload in bad_payloads:
        py_rejected = False
        try:
            mde.eval_dec_cell_measures_staircase_fold(payload)
        except (ValueError, TypeError):
            py_rejected = True
        _check(py_rejected, f"Python S2 failed to reject invalid payload: {payload}")

        rs_proc = _run_rust_eval("dec_cell_measures_staircase_fold", payload)
        _check(rs_proc.returncode != 0, f"Rust S4 failed to reject invalid payload: {payload}")


# =============================================================================
# 5. Genuine Cellular Fold Chain-Map Algebra, Exhaustive Mutations & Anti-Hardcoding
# =============================================================================


def test_qa_cellular_fold_chain_map_matrices_mutations_and_anti_hardcoding() -> None:
    """Prove exact matrix chain-map identities, exhaustive mutation sensitivity, and zero hardcoded fold literals."""
    k0, k1, k2 = mde._complex_cells_by_dim((((0, 1), (0, 1)), ((1, 2), (0, 1))))
    l0, l1, l2 = mde._complex_cells_by_dim((((0, 1), (0, 1)),))
    _check((len(k0), len(k1), len(k2)) == (6, 7, 2), f"unexpected K_2 cell counts: {(len(k0), len(k1), len(k2))}")
    _check((len(l0), len(l1), len(l2)) == (4, 4, 1), f"unexpected L_2 cell counts: {(len(l0), len(l1), len(l2))}")

    b2_k = mde._boundary_matrix(k2, k1)
    b1_k = mde._boundary_matrix(k1, k0)
    b2_l = mde._boundary_matrix(l2, l1)
    b1_l = mde._boundary_matrix(l1, l0)
    f0 = mde._fold_matrix(k0, l0)
    f1 = mde._fold_matrix(k1, l1)
    f2 = mde._fold_matrix(k2, l2)

    # Exact chain complex & chain-map commutation identities
    _check(mde._mat_is_zero(mde._mat_mul(b1_k, b2_k)), "B1_K * B2_K != 0")
    _check(mde._mat_is_zero(mde._mat_mul(b1_l, b2_l)), "B1_L * B2_L != 0")
    _check(mde._mat_mul(b2_l, f2) == mde._mat_mul(f1, b2_k), "B2_L * F2 != F1 * B2_K")
    _check(mde._mat_mul(b1_l, f1) == mde._mat_mul(f0, b1_k), "B1_L * F1 != F0 * B1_K")
    _check(f2 == [[1, -1]], f"expected F2 == [[1, -1]], got {f2}")

    c_top = [1, 1]
    b_k = mde._mat_vec(b2_k, c_top)
    _check(mde._mat_vec(f2, c_top) == [0], "F2(Q_L + Q_R) must cancel to [0]")
    _check(all(v == 0 for v in mde._mat_vec(f1, b_k)), "F1(B2_K(Q_L + Q_R)) must vanish")

    # Exhaustive single-entry sign-flip mutation sensitivity:
    # 1. Flipping ANY nonzero entry of F2 must break B2_L * F2 == F1 * B2_K
    for r in range(len(f2)):
        for c in range(len(f2[0])):
            if f2[r][c] != 0:
                mut_f2 = [row[:] for row in f2]
                mut_f2[r][c] = -mut_f2[r][c]
                _check(
                    mde._mat_mul(b2_l, mut_f2) != mde._mat_mul(f1, b2_k),
                    f"mutating F2[{r}][{c}] failed to break B2_L * F2 == F1 * B2_K",
                )

    # 2. Flipping ANY nonzero entry of F1 must break degree-2 or degree-1 commutation
    for r in range(len(f1)):
        for c in range(len(f1[0])):
            if f1[r][c] != 0:
                mut_f1 = [row[:] for row in f1]
                mut_f1[r][c] = -mut_f1[r][c]
                comm2 = mde._mat_mul(b2_l, f2) == mde._mat_mul(mut_f1, b2_k)
                comm1 = mde._mat_mul(b1_l, mut_f1) == mde._mat_mul(f0, b1_k)
                _check(
                    not (comm2 and comm1),
                    f"mutating F1[{r}][{c}] failed to break chain-map commutation",
                )

    # 3. Flipping ANY nonzero entry of B2_K must break B1_K * B2_K == 0
    for r in range(len(b2_k)):
        for c in range(len(b2_k[0])):
            if b2_k[r][c] != 0:
                mut_b2 = [row[:] for row in b2_k]
                mut_b2[r][c] = -mut_b2[r][c]
                _check(
                    not mde._mat_is_zero(mde._mat_mul(b1_k, mut_b2)),
                    f"mutating B2_K[{r}][{c}] failed to break B1_K * B2_K == 0",
                )

    # Verify sign-flip control via _eval_cellular_fold_chain_map
    raised = False
    try:
        mde._eval_cellular_fold_chain_map(flip_right_face_sign=True, enforce_commutation=True)
    except ValueError:
        raised = True
    _check(raised, "flip_right_face_sign=True must raise ValueError when enforce_commutation=True")

    diag = mde._eval_cellular_fold_chain_map(flip_right_face_sign=True, enforce_commutation=False)
    _check(diag["chain_map_commutes"] == 0 and diag["fold_oriented_top_sum"] == 2, f"unexpected sign-flip diag: {diag}")

    # Anti-hardcoding AST audit in Python manual_dec_examples.py
    fold_keys = {
        "fold_occupied_area",
        "fold_image_area",
        "fold_retained_multiplicity",
        "fold_oriented_top_sum",
        "fold_seam_cancelled",
        "fold_surviving_boundary_edges",
        "chain_map_commutes",
    }
    mde_tree = ast.parse(Path(mde.__file__).read_text(encoding="utf-8"), filename=str(mde.__file__))
    funcs = {n.name: n for n in ast.walk(mde_tree) if isinstance(n, ast.FunctionDef)}
    eval_fn = funcs["eval_dec_cell_measures_staircase_fold"]
    found_keys: set[str] = set()
    for node in ast.walk(eval_fn):
        if isinstance(node, ast.Dict):
            for k_node, v_node in zip(node.keys, node.values):
                if isinstance(k_node, ast.Constant) and isinstance(k_node.value, str):
                    key = k_node.value
                    if key in fold_keys:
                        found_keys.add(key)
                        _check(
                            not isinstance(v_node, ast.Constant),
                            f"hardcoded literal for {key!r} in Python eval_dec_cell_measures_staircase_fold",
                        )
                        _check(
                            isinstance(v_node, ast.Subscript)
                            and isinstance(v_node.value, ast.Name)
                            and v_node.value.id == "fold_metrics",
                            f"{key!r} must be read from fold_metrics in eval_dec_cell_measures_staircase_fold",
                        )
                    elif key == "q4_cell_counts":
                        _check(
                            isinstance(v_node, ast.Name),
                            "q4_cell_counts must come from _verify_q4_unit_cube(), not a hardcoded list literal",
                        )
                    elif key == "boundary_sq_zero":
                        _check(
                            not isinstance(v_node, ast.Constant),
                            "boundary_sq_zero must come from _verify_q4_unit_cube(), not a hardcoded literal",
                        )
    _check(found_keys == fold_keys, f"missing fold keys in Python output dict: {fold_keys - found_keys}")

    fold_fn = funcs["_eval_cellular_fold_chain_map"]
    for node in ast.walk(fold_fn):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in fold_keys:
                    _check(
                        not isinstance(node.value, ast.Constant),
                        f"hardcoded literal assigned to {target.id} inside _eval_cellular_fold_chain_map",
                    )

    # Anti-hardcoding source audit in Rust crates/aod-core/src/manual_dec_ops.rs
    rust_src = RUST_DEC_PATH.read_text(encoding="utf-8")
    op_body = rust_src[rust_src.find("pub fn op_dec_cell_measures_staircase_fold") :]
    for key in sorted(fold_keys):
        _check(
            not re.search(rf'out\.insert\(\s*"{re.escape(key)}"\.to_string\(\)\s*,\s*int_json\(\s*-?\d+\s*\)', op_body),
            f"hardcoded integer literal for {key!r} in Rust op_dec_cell_measures_staircase_fold",
        )
        _check(
            re.search(rf'out\.insert\(\s*"{re.escape(key)}"\.to_string\(\)\s*,\s*int_json\(\s*fold\.{re.escape(key)}\s*\)', op_body)
            is not None,
            f"Rust op_dec_cell_measures_staircase_fold must populate {key!r} from fold.{key}",
        )
    _check(
        not re.search(r"vec!\s*\[\s*int_json\(\s*16\s*\)", op_body),
        "Rust op_dec_cell_measures_staircase_fold must not hardcode q4_cell_counts [16,32,24,8,1]",
    )
    _check(
        not re.search(r'out\.insert\(\s*"boundary_sq_zero"\.to_string\(\)\s*,\s*int_json\(\s*1\s*\)', op_body),
        "Rust op_dec_cell_measures_staircase_fold must not hardcode boundary_sq_zero = 1",
    )


# =============================================================================
# 6. Typst Manuscript Integrity (§5, §6) & Exact Table-to-CSV Parity
# =============================================================================


def test_qa_typst_manuscript_integrity_proof_and_csv_table_parity() -> None:
    """Verify Typst §5 and §6 structure, labels, zero TODO/TBD/FIXME, -1 shift proof, B3 vs 64, and table parity."""
    s5_src = TYPST_S5_PATH.read_text(encoding="utf-8")
    s6_src = TYPST_S6_PATH.read_text(encoding="utf-8")
    fig_src = TYPST_FIG_PATH.read_text(encoding="utf-8")

    # Zero TODO / TBD / FIXME markers across all 3 touched Typst files
    for label, src in (("01_cell_measures.typ", s5_src), ("02_mapping_error.typ", s6_src), ("cell_staircase_fold_boundary.typ", fig_src)):
        m = re.search(r"\b(?:TODO|TBD|FIXME)\b", src, flags=re.IGNORECASE)
        if m is not None:
            raise AssertionError(f"unresolved placeholder {m.group(0)!r} found in {label}")

    # Exactly ONE n=1..32 table in 01_cell_measures.typ (zero duplicate 2D table) & exact CSV parity
    table_rows = _extract_typst_table_cells(s5_src)
    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    _check(len(table_rows) == len(csv_rows) == 6, f"expected 6 Typst table rows, got {len(table_rows)}")

    col_keys = (
        "n",
        "A_minus_exact",
        "A_plus_exact",
        "Cr_minus_2Aplus",
        "V4_minus_exact",
        "V4_plus_exact",
        "pi_4d_lower_exact",
        "pi_4d_upper_exact",
        "B3_staircase_exact",
        "B3_stair_minus_4V4plus",
    )
    for row_idx, (t_cells, crow) in enumerate(zip(table_rows, csv_rows)):
        _check(
            len(t_cells) == len(col_keys),
            f"Typst table row {row_idx} expected {len(col_keys)} columns, got {len(t_cells)}: {t_cells}",
        )
        for col_idx, key in enumerate(col_keys):
            got = _typst_cell_to_fraction(t_cells[col_idx])
            expected = Fraction(crow[key])
            _check(
                got == expected,
                f"Typst table cell drift at row n={crow['n']} col {key}: Typst={t_cells[col_idx]!r} ({got}) != CSV={expected}",
            )

    # Inward diagonal shift (- 1) proof present, and broken (+ 1) shift ABSENT
    _check(
        "(k_1 - 1, k_2 - 1, k_3 - 1, k_4 - 1)" in s5_src,
        "01_cell_measures.typ missing inward diagonal shift (k_1 - 1, k_2 - 1, k_3 - 1, k_4 - 1)",
    )
    _check(
        "(k_1 + 1, k_2 + 1, k_3 + 1, k_4 + 1)" not in s5_src,
        "01_cell_measures.typ contains broken outward (+ 1) shift!",
    )
    _check(
        "n^4 - (n - 1)^4" in s5_src,
        "01_cell_measures.typ missing exact boundary-shell count n^4 - (n - 1)^4",
    )
    _check(
        "sum_(i = 1)^4 (m_i + 1)^2 = sum_(i = 1)^4 k_i^2 < n^2" in s5_src,
        "01_cell_measures.typ missing inward shift inner-ball inequality proof",
    )

    # Explicit distinction of B3_staircase vs bounding 4-cube 64
    _check('B_(3,upright("stair"),n)^(+)' in s5_src, "01_cell_measures.typ missing B3_staircase symbol")
    _check('B_(3,upright("box"))' in s5_src, "01_cell_measures.typ missing B3_box symbol")
    _check("32 pi" in s5_src and "eq.not 2 pi^2" in s5_src, "01_cell_measures.typ missing 32*pi/3 != 2*pi^2 limit")
    _check("strictly distinct" in s5_src and "64" in s5_src and "51" in s5_src, "01_cell_measures.typ must explicitly distinguish B3_staircase (51) from 64")
    _check(
        re.search(r'B_\(3,upright\("stair"\),n\)\^\(\+\)\s*=\s*64\b', s5_src) is None,
        "01_cell_measures.typ must never falsely equate B3_staircase(n) = 64 for general n",
    )

    # Defining labels intact across §5 and §6
    for lbl in (
        "<manual:m3-cells>",
        "<prop:m3-staircase>",
        "<eq:m3-disk-enclosure>",
        "<manual:m3-cells:dec-staircase-fold>",
        "<fig:manual-cell-staircase-fold>",
        "<tab:manual-cell-boundary-fold-ledger>",
    ):
        _check(lbl in s5_src, f"01_cell_measures.typ missing required defining label {lbl}")

    for lbl in (
        "<manual:m3-mapping-error>",
        "<eq:manual-m3-original-interval>",
        "<eq:manual-m3-original-product>",
        "<manual:m3-experimental-inputs>",
        "<manual:m3-maps:dec-joint-laws>",
        "<tab:manual-typed-map-joint-laws>",
    ):
        _check(lbl in s6_src, f"02_mapping_error.typ missing required defining label {lbl}")

    # GM authoring structure intact in both §5 and §6
    for fname, src in (("01_cell_measures.typ", s5_src), ("02_mapping_error.typ", s6_src)):
        for heading in ("Setup:", "Derivation:", "Specialization:", "Falsification:"):
            _check(heading in src, f"{fname} missing General Mechanics section marker {heading!r}")

    # Cross-check §6 table against RC-036 golden vector
    rc036 = _load_rc_vector("RC-036")["expected_outcome"]["exact_value"]
    for tok in (
        "T_interval_100",
        "F_near_cancel_100",
        "Rf_symmetric_2",
        "U_orig_recip_1000",
        "V_orig_prod_1000",
        f"frac({rc036['T_mean'][0]}, {rc036['T_mean'][1]})",
        f"frac({rc036['T_var'][0]}, {rc036['T_var'][1]})",
        f"frac({rc036['F_mean'][0]}, {rc036['F_mean'][1]})",
        f"frac({rc036['F_var_over_lin'][0]}, {rc036['F_var_over_lin'][1]})",
        f"frac({rc036['U_mean'][0]}, {rc036['U_mean'][1]})",
        f"frac({rc036['U_var'][0]}, {rc036['U_var'][1]})",
        f"frac({rc036['V_var_over_lin'][0]}, {rc036['V_var_over_lin'][1]})",
    ):
        _check(tok in s6_src, f"02_mapping_error.typ missing RC-036 exact entry {tok!r}")


# =============================================================================
# 7. Native Typst Figure: Zero Hardcoded Numeric Arrays + Clean PNG Render
# =============================================================================


def test_qa_figure_zero_hardcoded_arrays_and_typst_png_render(tmp_path: Path) -> None:
    """Verify cell_staircase_fold_boundary.typ is 100% CSV-driven and compiles cleanly to PNG."""
    fig_src = TYPST_FIG_PATH.read_text(encoding="utf-8")

    _check(
        'csv("/manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv", row-type: dictionary)' in fig_src,
        "figure must read cell_measures_staircase_fold_dec.csv dynamically",
    )

    # All plotted data arrays must be mapped from CSV rows, never hardcoded numeric tuples
    expected_series = (
        "ks",
        "ys-a-lo",
        "ys-a-hi",
        "ys-pi-lo",
        "ys-pi-hi",
        "ys-4v4-lo",
        "ys-4v4-hi",
        "ys-b3-stair",
        "ys-b3-box",
    )
    for var_name in expected_series:
        m = re.search(rf"#let\s+{re.escape(var_name)}\s*=\s*([^\n]+)", fig_src)
        _check(m is not None, f"figure missing data series definition #let {var_name} = ...")
        rhs = m.group(1).strip()
        _check("rows.map(" in rhs, f"figure series {var_name} must derive from rows.map(...), got: {rhs}")

    # Reject any hardcoded numeric tuple assigned to a data series variable (#let ys-... = (0.0, ...))
    _check(
        re.search(r"#let\s+(?:xs|ys|ks)[A-Za-z0-9_-]*\s*=\s*\(\s*\d", fig_src) is None,
        "hardcoded numeric array literal found in cell_staircase_fold_boundary.typ",
    )

    # Reject leaked hardcoded CSV fractions/numerators inside the figure source
    for forbidden_literal in ("385", "833", "3047", "3389", "72561", "89701", "9179", "57163", "183.0", "41.0"):
        _check(
            forbidden_literal not in fig_src,
            f"hardcoded CSV numeric value {forbidden_literal!r} leaked into cell_staircase_fold_boundary.typ",
        )

    # Compile figure cleanly into tmp_path via typst CLI (single-page PNG at 144 PPI)
    out_png = tmp_path / "cell_staircase_fold_boundary.png"
    proc = subprocess.run(
        [
            "typst",
            "compile",
            "--root",
            ".",
            "--format",
            "png",
            "--ppi",
            "144",
            str(TYPST_FIG_PATH.relative_to(ROOT)),
            str(out_png),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _check(proc.returncode == 0, f"typst compile failed (rc={proc.returncode}): {proc.stderr}")
    _check(out_png.is_file(), "typst compile produced no output PNG")
    png_bytes = out_png.read_bytes()
    _check(len(png_bytes) > 10_000, f"rendered PNG suspiciously small ({len(png_bytes)} bytes)")
    _check(png_bytes[:8] == b"\x89PNG\r\n\x1a\n", "rendered output is not a valid PNG")
    width_px, height_px = struct.unpack(">II", png_bytes[16:24])
    _check(width_px >= 600 and height_px >= 400, f"unexpected rendered PNG dimensions: {width_px}x{height_px}")


# =============================================================================
# 8. Whole-Phase Audits, Contract/Registry Digests & Byte-Identical Harnesses
# =============================================================================


def test_qa_audits_digest_parity_and_byte_identical_s2_s4_harnesses(tmp_path: Path) -> None:
    """Verify scientific audits, registry/contract digest parity, and normal/-O & debug/release byte-identity."""
    # 1. audit_scientific_sources.py
    audit_proc = subprocess.run(
        [sys.executable, "-B", "scripts/audit_scientific_sources.py", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _check(audit_proc.returncode == 0, f"audit_scientific_sources.py failed:\n{audit_proc.stdout}\n{audit_proc.stderr}")

    # 2. build_publication.py --check-registry & main_registry.json integrity
    reg_proc = subprocess.run(
        [sys.executable, "-B", "scripts/build_publication.py", "--check-registry"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _check(reg_proc.returncode == 0, f"build_publication.py --check-registry failed:\n{reg_proc.stdout}\n{reg_proc.stderr}")

    main_reg = json.loads(MAIN_REGISTRY_PATH.read_text(encoding="utf-8"))
    _check(
        re.fullmatch(r"[0-9a-f]{64}", str(main_reg.get("main_sources_sha256", ""))) is not None,
        "main_registry.json main_sources_sha256 invalid",
    )

    # 3. Direct SHA-256 parity across all phase-updated contracts, figure inventory & representation ledger
    cell_bindings = json.loads(CELL_BINDINGS_PATH.read_text(encoding="utf-8"))
    _check(
        cell_bindings["sources"]["typst/manual/sections/01_cell_measures.typ"] == _sha256_file(TYPST_S5_PATH),
        "CELL_MAPPING_MATHEMATICAL_BINDINGS.json digest mismatch for 01_cell_measures.typ",
    )

    canon_bindings = json.loads(CANONICAL_BINDINGS_PATH.read_text(encoding="utf-8"))
    csv_rel = "manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv"
    csv_sha = _sha256_file(CSV_PATH)
    # Locate csv_rel in canonical bindings (may be nested under a hashes/files section)
    canon_text = CANONICAL_BINDINGS_PATH.read_text(encoding="utf-8")
    _check(
        f'"{csv_rel}": "{csv_sha}"' in canon_text,
        f"CANONICAL_BINDINGS.json digest mismatch for {csv_rel}",
    )

    cells_doc = json.loads(CELLS_JSON_PATH.read_text(encoding="utf-8"))
    _check(cells_doc["spec_sha256"] == _sha256_file(CELL_SPEC_PATH), "cells_geometry.json spec_sha256 mismatch")
    _check(
        cells_doc["implementation_sha256"] == _sha256_file(CELLS_SCRIPT_PATH),
        "cells_geometry.json implementation_sha256 mismatch",
    )

    fig_inv = json.loads(FIG_INVENTORY_PATH.read_text(encoding="utf-8"))
    fig_entries = [
        e for e in fig_inv.get("figures", []) if e.get("label") == "fig:manual-cell-staircase-fold"
    ]
    _check(len(fig_entries) == 1, "fig:manual-cell-staircase-fold missing or duplicated in figure_inventory.json")
    fig_entry = fig_entries[0]
    _check(
        fig_entry["typst_component_sha256"] == _sha256_file(TYPST_FIG_PATH),
        "figure_inventory.json typst_component_sha256 mismatch",
    )
    _check(
        any(ds.get("path") == csv_rel and ds.get("sha256") == csv_sha for ds in fig_entry.get("data_sources", [])),
        "figure_inventory.json CSV sha256 mismatch",
    )

    rep_ledger_text = REP_LEDGER_PATH.read_text(encoding="utf-8")
    _check(_sha256_file(CELL_BINDINGS_PATH) in rep_ledger_text, "representation_change_ledger missing CELL_MAPPING digest")
    _check(_sha256_file(CANONICAL_BINDINGS_PATH) in rep_ledger_text, "representation_change_ledger missing CANONICAL_BINDINGS digest")
    _check(csv_sha in rep_ledger_text, "representation_change_ledger missing CSV digest")

    # 4. aod_cell_measures.py --check-data under normal and -O Python
    for flags in (["-B"], ["-B", "-O"]):
        cm_proc = subprocess.run(
            [sys.executable, *flags, "manual/scripts/aod_cell_measures.py", "--check-data"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        _check(cm_proc.returncode == 0, f"aod_cell_measures.py --check-data failed with {flags}: {cm_proc.stderr}")

    # 5. Python S2 normal == -O byte-identical report
    s2_norm = tmp_path / "s2_norm.json"
    s2_opt = tmp_path / "s2_opt.json"
    for flags, out_path in ((["-B"], s2_norm), (["-B", "-O"], s2_opt)):
        s2_proc = subprocess.run(
            [
                sys.executable,
                *flags,
                "-m",
                "manual.engine",
                "--sector",
                "boundary_sadar",
                "--sector",
                "cell_measures",
                "--check-zero-float",
                "--verify-vectors",
                "--report",
                str(out_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        _check(s2_proc.returncode == 0, f"S2 engine failed with {flags}: {s2_proc.stderr}")
    _check(s2_norm.read_bytes() == s2_opt.read_bytes(), "S2 normal vs -O reports are NOT byte-identical")

    # 6. Rust S4 debug == release byte-identical report
    s4_dbg = tmp_path / "s4_dbg.json"
    s4_rel = tmp_path / "s4_rel.json"
    for extra_args, out_path in (([], s4_dbg), (["--release"], s4_rel)):
        s4_proc = subprocess.run(
            [
                "cargo",
                "run",
                "--quiet",
                "--manifest-path",
                str(CARGO_MANIFEST),
                "--offline",
                "--locked",
                *extra_args,
                "--",
                "--verify-vectors",
                "--check-zero-float",
                "--report",
                str(out_path),
            ],
            cwd=ROOT,
            env=_cargo_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        _check(s4_proc.returncode == 0, f"S4 Rust core failed with {extra_args}: {s4_proc.stderr}")
    _check(s4_dbg.read_bytes() == s4_rel.read_bytes(), "S4 debug vs release reports are NOT byte-identical")
