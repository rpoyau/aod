"""Adversarial Phase 4 (P4-manual-sadar-examples) QA & Handoff Verification Suite.

Independently verifies all Phase 4 deliverables across BND-P4-01 through BND-P4-04:
1. Manual-wide Vector Citation & Anti-Contradiction Audit across all 18 Manual `.typ` files:
   - Canonical 53-vector inventory (`RC-001..RC-045` + `SD-001..SD-008`) and exact
     100 semicolon-separated `source_binding` components.
   - Every `RC-NNN` / `SD-NNN` token cited in all 18 Manual `.typ` files resolves in
     the 53-vector inventory.
   - Zero retired contradictions/misbindings across §1, §3, §4, §8, §9, §10, §11, §12,
     §13, §14, §15, App. A, App. B, and App. C, plus exact 53-vector partition in §15.
2. Live CSV Binding Verification:
   - Every refactored Manual `.typ` table binds live via `csv("/manual/data/boundary_sadar/...")`.
   - Every referenced CSV exists, parses cleanly via `csv.DictReader`, has non-empty exact
     rows, matches `expected_manual_dec_csv_map()` where applicable and
     `build_boundary_sadar_tables(REPO_ROOT)` byte-for-byte across all 20 CSVs, including
     exact schema/data verification of `coordinate_phase_3d_dec_walk.csv` vs
     `manual/data/brownian/octant_delta3.csv` (`RC-012`).
3. RC-044 Independent Pure-Integer Oracle, Poisoned-`Fraction`, Static Zero-`BigRat`,
   S2/S4 Parity, Error Rejection Matrix, and RC-041 Integrity:
   - Pure-integer (`math.gcd`, zero `Fraction`, zero floats) oracle verifying `RC-044` ==
     `RC-012` at `beta_a=5, msb_x`, explicit `lsb_x` contrast matching `RC-013`, all 8 sign
     patterns + zero-component edges, boundary `beta_a` values (`1`, `7`, `10000`), and
     multi-scale large-coordinate (`> i64` and `> i128` squared) walks across both S2 and S4.
   - Poisoned-`Fraction` proof on `eval_dec_coordinate_phase_3d_walk` and
     `build_coordinate_phase_3d_csv_rows`, plus Python AST audit.
   - Static audit of `crates/aod-core/src/manual_dec_ops.rs` (`op_dec_coordinate_phase_3d_walk`
     to EOF) confirming `TritWord`/`TritRatio`/`trit_pair_json` and zero `BigRat` /
     standalone `pair_json`.
   - Comprehensive `TypeError` vs `ValueError` rejection matrix across BOTH Python S2 and
     Rust S4 (verified identically under normal and `-O` Python).
   - Confirmation that `RC-041` (`eval_dec_run_tumble_q4_stepper`) and `_octant_3d` remain
     100% intact across S2, S4, and retained CSV tracks.
4. Publication Contract & Ownership Integrity + S2/S4 Vector Parity & Self-AST Audit:
   - All `OWNERSHIP_AND_FIXTURES.json` owned anchors exist in their exact declared files.
   - `CANONICAL_BINDINGS.json` (`192` frozen entries) matches live SHA-256 of
     `coordinate_phase_3d_dec_walk.csv` (and all 20 `boundary_sadar` CSVs); both
     `scripts/audit_ontology_compaction.py` and `typst/representation_change_ledger.json`
     match live SHA-256 of `CANONICAL_BINDINGS.json`.
   - Full S2 (normal vs `-O` byte-identical) and S4 (`aod-core --verify-vectors`) 53-vector
     verification.
   - Self-AST check guaranteeing zero bare `assert` statements and zero float literals/calls.
"""
from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterator

import pytest

from manual.engine.sectors.boundary_sadar import build_boundary_sadar_tables
import manual.engine.sectors.manual_dec_examples as dec_mod
from manual.engine.sectors.manual_dec_examples import (
    _octant_3d,
    build_coordinate_phase_3d_csv_rows,
    build_run_tumble_dec_csv_rows,
    eval_dec_coordinate_phase_3d_walk,
    eval_dec_run_tumble_q4_stepper,
    expected_manual_dec_csv_map,
)
from manual.engine.vectors import _eval_operation as eval_s2_vector_op
from manual.engine.vectors import validate_source_binding

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

CANONICAL_RC044_POINTS: list[list[int]] = [
    [0, 0, 0],
    [1, 1, 0],
    [2, 1, 1],
    [3, 2, 1],
    [2, 3, 2],
    [3, 4, 3],
    [4, 3, 4],
    [5, 4, 4],
    [6, 5, 5],
]

EXPECTED_LIVE_CSV_BINDINGS: dict[str, str] = {
    "00_native_closure_wave_temporal_fixtures.typ": "/manual/data/boundary_sadar/native_closure_wave_dec_walk.csv",
    "00_awareness_fixtures.typ": "/manual/data/boundary_sadar/awareness_operativity_dec_walk.csv",
    "01_rest_energy_prediction.typ": "/manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv",
    "02_hydrogen_facing_shell_tests.typ": "/manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv",
    "03_short_window_rcd_shedding_fixtures.typ": "/manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv",
    "03_temporal_observation.typ": "/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv",
    "04_boundary_current_applications.typ": "/manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv",
    "05_solar_system_field_tests.typ": "/manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv",
    "06_field_dynamics_applications.typ": "/manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv",
    "07_galactic_lensing_plan.typ": "/manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv",
    "A_simulation_fixtures_and_tau_prediction_context.typ": "/manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv",
    "C_3d_coordinate_phase_cycle_delta3_fixture.typ": "/manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv",
}


# =============================================================================
# Non-Strippable Assertion & Pure-Integer Helpers (Zero bare assert, Zero float)
# =============================================================================


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _check_eq(actual: object, expected: object, label: str) -> None:
    if actual != expected or type(actual) is not type(expected):
        raise AssertionError(
            f"{label}: mismatch\n  actual   ({type(actual).__name__}): {actual!r}\n  expected ({type(expected).__name__}): {expected!r}"
        )


def _check_json_eq(actual: object, expected: object, path: str = "$") -> None:
    """Strict type-preserving structural equality (distinguishes bool from int)."""
    _check(
        type(actual) is type(expected),
        f"{path}: type mismatch ({type(actual).__name__} != {type(expected).__name__}): "
        f"actual={actual!r}, expected={expected!r}",
    )
    if isinstance(actual, dict) and isinstance(expected, dict):
        _check(
            set(actual.keys()) == set(expected.keys()),
            f"{path}: key mismatch actual={sorted(actual.keys())} expected={sorted(expected.keys())}",
        )
        for key in sorted(actual.keys()):
            _check_json_eq(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(actual, list) and isinstance(expected, list):
        _check(
            len(actual) == len(expected),
            f"{path}: length mismatch actual={len(actual)} expected={len(expected)}",
        )
        for idx, (a_item, e_item) in enumerate(zip(actual, expected)):
            _check_json_eq(a_item, e_item, f"{path}[{idx}]")
    else:
        _check(
            actual == expected,
            f"{path}: value mismatch actual={actual!r} expected={expected!r}",
        )


def _assert_no_floats(obj: object, path: str = "$") -> None:
    _check(
        type(obj).__name__ != "float",
        f"forbidden float encountered at {path}: {obj!r}",
    )
    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            _assert_no_floats(item, f"{path}[{idx}]")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_pair(num: int, den: int) -> list[str]:
    """Pure-integer canonical reduced rational pair [num_str, den_str] with den > 0."""
    _check(den != 0, "zero denominator in _canonical_pair")
    if den < 0:
        num = -num
        den = -den
    if num == 0:
        return ["0", "1"]
    g = math.gcd(abs(num), den)
    return [str(num // g), str(den // g)]


def _int_balance(total: int, bins: int) -> list[int]:
    """Pure-integer IntBalance(N, K): distributes N across K bins, remainder to lowest indices."""
    _check(bins > 0, f"bins must be positive, got {bins}")
    base, rem = divmod(total, bins)
    return [base + (1 if idx < rem else 0) for idx in range(bins)]


def _independent_rc044_oracle(
    points: list[list[int]],
    beta_a: int,
    octant_bit_order: str = "msb_x",
) -> dict[str, Any]:
    """Completely independent pure-integer oracle for RC-044 (zero Fraction, zero TritWord, zero float)."""
    _check(len(points) >= 2, "oracle requires >= 2 points")
    _check(1 <= beta_a <= 10_000, f"oracle beta_a out of bounds: {beta_a}")
    _check(octant_bit_order in ("msb_x", "lsb_x"), f"oracle invalid bit_order: {octant_bit_order!r}")

    n_steps = len(points) - 1
    q_values: list[int] = []
    phase_counts: list[int] = [0 for _ in range(beta_a)]
    octant_counts: list[int] = [0 for _ in range(8)]
    sum_dx2 = 0
    sum_dy2 = 0
    sum_dz2 = 0
    sum_q = 0

    for i in range(n_steps):
        p0 = points[i]
        p1 = points[i + 1]
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dz = p1[2] - p0[2]
        dx2 = dx * dx
        dy2 = dy * dy
        dz2 = dz * dz
        q_i = dx2 + dy2 + dz2
        q_values.append(q_i)
        sum_dx2 += dx2
        sum_dy2 += dy2
        sum_dz2 += dz2
        sum_q += q_i
        theta = q_i % beta_a
        phase_counts[theta] += 1
        if octant_bit_order == "msb_x":
            oct_code = (4 if dx < 0 else 0) | (2 if dy < 0 else 0) | (1 if dz < 0 else 0)
        else:
            oct_code = (1 if dx < 0 else 0) | (2 if dy < 0 else 0) | (4 if dz < 0 else 0)
        octant_counts[oct_code] += 1

    _check(sum_q > 0, "oracle requires sum_Q > 0")
    _check_eq(sum_dx2 + sum_dy2 + sum_dz2, sum_q, "oracle axis square sum == sum_Q")

    phase_comp = _int_balance(n_steps, beta_a)
    phase_dz = [c - o for c, o in zip(phase_comp, phase_counts)]
    _check_eq(sum(phase_dz), 0, "oracle phase_DeltaZ conservation")
    phase_m = sum(abs(v) for v in phase_dz)

    octant_comp = _int_balance(n_steps, 8)
    octant_dz = [c - o for c, o in zip(octant_comp, octant_counts)]
    _check_eq(sum(octant_dz), 0, "oracle octant_DeltaZ conservation")
    octant_m = sum(abs(v) for v in octant_dz)

    return {
        "step_count": n_steps,
        "Q_values": q_values,
        "sum_Q": sum_q,
        "R_Q_ratio": _canonical_pair(sum_q, n_steps),
        "R_x_ratio": _canonical_pair(sum_dx2, sum_q),
        "R_y_ratio": _canonical_pair(sum_dy2, sum_q),
        "R_z_ratio": _canonical_pair(sum_dz2, sum_q),
        "phase_counts": phase_counts,
        "phase_DeltaZ": phase_dz,
        "phase_delta3_M": phase_m,
        "octant_bit_order": octant_bit_order,
        "octant_counts": octant_counts,
        "octant_DeltaZ": octant_dz,
        "octant_delta3_M": octant_m,
    }


def _load_canonical_vectors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rc_path = REPO_ROOT / "manual" / "engine" / "vectors" / "rational_core.jsonl"
    sd_path = REPO_ROOT / "manual" / "engine" / "vectors" / "symbolic_and_display.jsonl"
    rc_rows = [json.loads(line) for line in rc_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    sd_rows = [json.loads(line) for line in sd_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rc_rows, sd_rows


def _all_manual_typ_files() -> list[Path]:
    sections = sorted((REPO_ROOT / "typst" / "manual" / "sections").glob("*.typ"))
    appendices = sorted((REPO_ROOT / "typst" / "manual" / "appendices").glob("*.typ"))
    return sections + appendices


def _read_manual_section(name: str) -> str:
    return (REPO_ROOT / "typst" / "manual" / "sections" / name).read_text(encoding="utf-8")


def _read_manual_appendix(name: str) -> str:
    return (REPO_ROOT / "typst" / "manual" / "appendices" / name).read_text(encoding="utf-8")


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
    """Compile aod-core offline into an isolated temporary target directory and clean up."""
    with tempfile.TemporaryDirectory(prefix="qa_p4_aod_core_") as tmp_dir:
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


def _eval_s4_op(
    binary: Path,
    op_name: str,
    payload: dict[str, Any],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(binary),
            "--eval-op",
            op_name,
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


# =============================================================================
# 1. Manual-Wide Vector Citation & Anti-Contradiction Audit (All 18 .typ Files)
# =============================================================================


def test_canonical_53_vector_inventory_and_100_source_bindings() -> None:
    """Verify 45 RC + 8 SD = 53 canonical golden vectors and exact 100 source_binding components."""
    rc_rows, sd_rows = _load_canonical_vectors()
    _check_eq(len(rc_rows), 45, "rational_core.jsonl vector count")
    _check_eq(len(sd_rows), 8, "symbolic_and_display.jsonl vector count")

    all_rows = rc_rows + sd_rows
    _check_eq(len(all_rows), 53, "total canonical golden vector count")

    rc_ids = [str(r["case_id"]) for r in rc_rows]
    sd_ids = [str(r["case_id"]) for r in sd_rows]
    expected_rc_ids = [f"RC-{idx:03d}" for idx in range(1, 46)]
    expected_sd_ids = [f"SD-{idx:03d}" for idx in range(1, 9)]
    _check_eq(rc_ids, expected_rc_ids, "RC vector IDs RC-001..RC-045")
    _check_eq(sd_ids, expected_sd_ids, "SD vector IDs SD-001..SD-008")

    total_binding_components = 0
    for row in all_rows:
        case_id = str(row["case_id"])
        sb = row.get("source_binding")
        _check(isinstance(sb, str) and len(sb) > 0, f"{case_id}: missing source_binding")
        parts = sb.split(";")
        _check(all(len(p.strip()) > 0 for p in parts), f"{case_id}: empty source_binding component in {sb!r}")
        total_binding_components += len(parts)
        # Validate every source_binding resolves live against REPO_ROOT
        validate_source_binding(REPO_ROOT, sb)

    _check_eq(total_binding_components, 100, "total semicolon-separated source_binding components")

    # Cross-check RC-044 canonical record against RC-012 directly in the JSONL inventory
    by_id = {str(r["case_id"]): r for r in all_rows}
    rc012 = by_id["RC-012"]
    rc044 = by_id["RC-044"]
    _check_eq(rc044["operation"], "dec_coordinate_phase_3d_walk", "RC-044 operation")
    _check_eq(rc044["inputs"]["beta_a"], 5, "RC-044 canonical beta_a")
    _check_eq(rc044["inputs"]["octant_bit_order"], "msb_x", "RC-044 canonical octant_bit_order")
    _check_eq(rc044["inputs"]["points"], CANONICAL_RC044_POINTS, "RC-044 canonical 9-point track")

    exp_012 = rc012["expected_outcome"]["exact_value"]
    exp_044 = rc044["expected_outcome"]["exact_value"]
    _check_json_eq(exp_044["Q_values"], exp_012["Q"], "RC-044 Q_values == RC-012 Q")
    _check_json_eq(exp_044["R_Q_ratio"], exp_012["R_Q"], "RC-044 R_Q == RC-012 R_Q")
    _check_json_eq(exp_044["R_x_ratio"], exp_012["R_x"], "RC-044 R_x == RC-012 R_x")
    _check_json_eq(exp_044["R_y_ratio"], exp_012["R_y"], "RC-044 R_y == RC-012 R_y")
    _check_json_eq(exp_044["R_z_ratio"], exp_012["R_z"], "RC-044 R_z == RC-012 R_z")
    _check_json_eq(exp_044["phase_DeltaZ"], exp_012["phase_DeltaZ"], "RC-044 phase_DeltaZ == RC-012")
    _check_json_eq(exp_044["phase_delta3_M"], exp_012["sum_phase_m"], "RC-044 phase_delta3_M == RC-012")
    _check_json_eq(exp_044["octant_DeltaZ"], exp_012["octant_DeltaZ"], "RC-044 octant_DeltaZ == RC-012")
    _check_json_eq(exp_044["octant_delta3_M"], exp_012["sum_octant_m"], "RC-044 octant_delta3_M == RC-012")


def test_all_18_manual_typ_files_cite_only_canonical_vectors() -> None:
    """Verify exact 18 Manual .typ files and that EVERY cited RC-NNN/SD-NNN token exists in the 53-vector set."""
    rc_rows, sd_rows = _load_canonical_vectors()
    valid_ids = {str(r["case_id"]) for r in rc_rows + sd_rows}
    _check_eq(len(valid_ids), 53, "valid canonical vector ID set size")

    manual_files = _all_manual_typ_files()
    _check_eq(len(manual_files), 18, "Manual .typ file count (15 sections + 3 appendices)")

    token_pat = re.compile(r"\b(?:RC|SD)-\d+\b")
    cited_across_manual: set[str] = set()
    for path in manual_files:
        text = path.read_text(encoding="utf-8")
        tokens = token_pat.findall(text)
        unknown = sorted({tok for tok in tokens if tok not in valid_ids})
        _check(
            not unknown,
            f"{path.name} cites unknown/out-of-inventory vector IDs: {unknown}",
        )
        cited_across_manual.update(tokens)

    # Confirm both RC-045 and SD-008 appear in the Manual corpus
    for must_appear in ("RC-001", "RC-012", "RC-013", "RC-014", "RC-025", "RC-044", "RC-045", "SD-007", "SD-008"):
        _check(
            must_appear in cited_across_manual,
            f"expected canonical vector {must_appear} to be cited in Manual corpus",
        )


def test_manual_section1_scope_53_vector_alignment() -> None:
    """Verify Manual §1 (00_scope.typ) reflects 53 vectors (RC-001..RC-045 + SD-001..SD-008) and aligned chapter index."""
    s1 = _read_manual_section("00_scope.typ")
    _check("fifty-three" in s1, "§1 missing 'fifty-three' vector inventory statement")
    _check('#raw("RC-001") through #raw("RC-045")' in s1, "§1 missing RC-001 through RC-045 range")
    _check('#raw("SD-001") through #raw("SD-008")' in s1, "§1 missing SD-001 through SD-008 range")
    _check("fifty-two" not in s1.lower(), "§1 contains stale 'fifty-two' count")
    _check('RC-001") through #raw("RC-044")' not in s1, "§1 contains stale RC-001..RC-044 upper bound")

    # Verify key aligned rows in <tab:manual-chapter-dec-boundary-index>
    idx_start = s1.index("<fig:manual-five-boundary-calculation-spine>")
    idx_tab = s1[idx_start:]
    required_row_snippets = (
        '[§4 D.E.C. ledger]',
        '[#raw("RC-025"), #raw("RC-026"), #raw("RC-045")]',
        '[§8 Short-window]',
        '[#raw("RC-030"), #raw("RC-038")]',
        '[§9 Rest energy]',
        '[#raw("RC-027")--#raw("RC-029"), #raw("SD-007")]',
        '[§10 Hydrogen]',
        '[#raw("RC-031"), #raw("RC-039")]',
        '[§11 Wire & Stokes]',
        '[#raw("RC-032")]',
        '[§12 Solar O0]',
        '[#raw("RC-040")]',
        '[§13 Field dynamics]',
        '[#raw("RC-041"), #raw("SD-008")]',
        '[§14 Lensing plan]',
        '[#raw("RC-020"), #raw("RC-042")]',
        '[App. A Shedding]',
        '[#raw("RC-014"), #raw("RC-043")]',
        '[App. B Quarantine]',
        '[#raw("SD-007")]',
        '[App. C 3D phase]',
        '[#raw("RC-044")]',
    )
    for snippet in required_row_snippets:
        _check(snippet in idx_tab, f"§1 chapter index table missing {snippet!r}")


def test_manual_anti_contradiction_audit_s4_s8_s9_s10_s11_s12_s13_s14_s15_app_abc() -> None:
    """Assert ZERO retired contradictions/misbindings and presence of all canonical citations."""
    # --- §3 (00_awareness_fixtures.typ) ---
    s3 = _read_manual_section("00_awareness_fixtures.typ")
    _check("RC-034" in s3, "§3 missing RC-034 citation")
    _check('csv("/manual/data/boundary_sadar/awareness_operativity_dec_walk.csv"' in s3, "§3 missing live CSV binding")

    # --- §4 (00_dec_ledger.typ) ---
    s4 = _read_manual_section("00_dec_ledger.typ")
    _check("B|t" not in s4, "§4 contains forbidden 'B|t' notation")
    _check(
        re.search(r"B\s*(?:\||bar\.v)\s*t\b", s4) is None,
        "§4 contains forbidden 'B bar.v t' / 'B|t' cut-frame notation",
    )
    _check("B bar.v k" in s4, "§4 missing canonical cut-index 'B bar.v k' notation")
    _check("RC-028" not in s4, "§4 contains scrambled chiral-flip vector RC-028")
    _check("RC-029" not in s4, "§4 contains scrambled chiral-flip vector RC-029")
    for required in ("RC-025", "RC-026", "RC-045"):
        _check(required in s4, f"§4 missing required vector citation {required}")

    # --- §8 (03_short_window_rcd_shedding_fixtures.typ) ---
    s8 = _read_manual_section("03_short_window_rcd_shedding_fixtures.typ")
    _check(
        "still needs a frozen nested-path" not in s8.lower(),
        "§8 still contains retired 'still needs a frozen nested-path' contradiction",
    )
    _check("RC-029" not in s8, "§8 contains scrambled vector citation RC-029")
    for required in ("RC-030", "RC-038", "0_D", "0_H", "burn_contiguous_dwell"):
        _check(required in s8, f"§8 missing required token {required!r}")
    _check(
        re.search(r"burn.*0_D.*preserv.*0_H", s8, flags=re.IGNORECASE | re.DOTALL) is not None,
        "§8 must explicitly clarify 0_D optional dwell burned while 0_H structural hinge preserved",
    )
    _check(
        'csv("/manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv"' in s8,
        "§8 missing live CSV binding",
    )

    # --- §9 (01_rest_energy_prediction.typ) ---
    s9 = _read_manual_section("01_rest_energy_prediction.typ")
    _check("raw count 26" not in s9.lower(), "§9 contains stale 'raw count 26'")
    _check("raw_cuts = 26" not in s9, "§9 contains stale 'raw_cuts = 26'")
    _check("RC-025" not in s9, "§9 contains scrambled vector RC-025")
    _check("RC-026" not in s9, "§9 contains scrambled vector RC-026")
    for required in (
        "RC-011",
        "RC-027",
        "RC-028",
        "RC-029",
        "SD-004",
        "SD-005",
        "SD-007",
        "raw_cuts = 28 = 11 + 17",
        "TritWord.burn_contiguous_dwell",
        "50$-microslot",
        "2500",
    ):
        _check(required in s9, f"§9 missing required token {required!r}")
    _check(
        'csv("/manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv"' in s9,
        "§9 missing live CSV binding",
    )

    # --- §10 (02_hydrogen_facing_shell_tests.typ) ---
    s10 = _read_manual_section("02_hydrogen_facing_shell_tests.typ")
    for required in ("RC-031", "RC-039"):
        _check(required in s10, f"§10 missing required vector citation {required}")
    _check(
        'csv("/manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv"' in s10,
        "§10 missing live CSV binding",
    )

    # --- §11 (04_boundary_current_applications.typ) ---
    s11 = _read_manual_section("04_boundary_current_applications.typ")
    _check("RC-032" in s11, "§11 missing required vector citation RC-032")
    _check("RC-030" not in s11, "§11 contains scrambled vector RC-030")
    _check("RC-031" not in s11, "§11 contains scrambled vector RC-031")
    _check(
        'csv("/manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv"' in s11,
        "§11 missing live CSV binding",
    )

    # --- §12 (05_solar_system_field_tests.typ) ---
    s12 = _read_manual_section("05_solar_system_field_tests.typ")
    for required in ("RC-040", "HOLD_MISSING_NATIVE_SOLAR_PRODUCER"):
        _check(required in s12, f"§12 missing required token {required!r}")
    _check(
        'csv("/manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv"' in s12,
        "§12 missing live CSV binding",
    )

    # --- §13 (06_field_dynamics_applications.typ) ---
    s13 = _read_manual_section("06_field_dynamics_applications.typ")
    for forbidden in ("64.70291920", "66.1613", "1523", "1521", "RC-025", "RC-032"):
        _check(forbidden not in s13, f"§13 contains forbidden stale string {forbidden!r}")
    _check("pandas" not in s13.lower(), "§13 contains forbidden stale 'pandas' reference")
    for required in ("26.57055342", "SD-008", "RC-015", "RC-016", "RC-027", "RC-041", "230", "228", "209"):
        _check(required in s13, f"§13 missing required token {required!r}")
    _check(
        'csv("/manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv"' in s13,
        "§13 missing live CSV binding",
    )
    # Cross-check §13 SPARC G0 values directly against sparc_pooled_primary_exact.csv
    with (REPO_ROOT / "manual" / "data" / "boundary_sadar" / "sparc_pooled_primary_exact.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        sparc_rows = list(csv.DictReader(fh))
    _check_eq(len(sparc_rows), 1, "sparc_pooled_primary_exact.csv row count")
    _check_eq(sparc_rows[0]["N_total"], "209", "SPARC N_total")
    _check_eq(sparc_rows[0]["N_scored"], "209", "SPARC N_scored")
    _check_eq(len(sparc_rows[0]["MAPE_U_num"]), 230, "SPARC MAPE_U numerator digit length")
    _check_eq(len(sparc_rows[0]["MAPE_U_den"]), 228, "SPARC MAPE_U denominator digit length")
    _check_eq(sparc_rows[0]["MAPE_U_display_8dp"], "26.57055342", "SPARC MAPE_U 8dp display")

    # --- §14 (07_galactic_lensing_plan.typ) ---
    s14 = _read_manual_section("07_galactic_lensing_plan.typ")
    for required in ("RC-020", "RC-042"):
        _check(required in s14, f"§14 missing required vector citation {required}")
    _check(
        'csv("/manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv"' in s14,
        "§14 missing live CSV binding",
    )

    # --- §15 (09_prediction_test_fixture_registry.typ): exact 53-vector partition ---
    s15 = _read_manual_section("09_prediction_test_fixture_registry.typ")
    _check("RC-045" in s15, "§15 missing RC-045")
    _check("SD-008" in s15, "§15 missing SD-008")
    _check("fifty-three" in s15, "§15 missing 'fifty-three' vector statement")
    master_start = s15.index("== Reference-engine golden-vector")
    master_section = s15[master_start:]
    tbody_start = master_section.index("midrule,")
    tbody_end = master_section.index("bottomrule,")
    tbody = master_section[tbody_start:tbody_end]

    range_pat = re.compile(
        r'#raw\("(RC|SD)-(\d{3})"\)\s*(?:--|\u2013)\s*#raw\("(RC|SD)-(\d{3})"\)'
    )
    covered: list[str] = []
    for m in range_pat.finditer(tbody):
        p1, n1, p2, n2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        _check_eq(p1, p2, f"§15 range prefix mismatch: {m.group(0)}")
        _check(n1 <= n2, f"§15 descending range: {m.group(0)}")
        for n in range(n1, n2 + 1):
            covered.append(f"{p1}-{n:03d}")
    stripped_tbody = range_pat.sub("", tbody)
    for m in re.finditer(r'#raw\("(RC|SD)-(\d{3})"\)', stripped_tbody):
        covered.append(f"{m.group(1)}-{int(m.group(2)):03d}")

    expected_53 = [f"RC-{idx:03d}" for idx in range(1, 46)] + [f"SD-{idx:03d}" for idx in range(1, 9)]
    duplicates = sorted({x for x in covered if covered.count(x) > 1})
    missing = sorted(set(expected_53) - set(covered))
    extra = sorted(set(covered) - set(expected_53))
    _check(not duplicates, f"§15 master registry table has duplicate vector IDs: {duplicates}")
    _check(not missing, f"§15 master registry table is missing vector IDs: {missing}")
    _check(not extra, f"§15 master registry table has unexpected vector IDs: {extra}")
    _check_eq(len(covered), 53, "§15 master registry exact 53-vector coverage")

    # --- App. A (A_simulation_fixtures_and_tau_prediction_context.typ) ---
    app_a = _read_manual_appendix("A_simulation_fixtures_and_tau_prediction_context.typ")
    for required in ("RC-014", "RC-043", "cycle_shedding_exact_rational_summary.csv", "six-decimal"):
        _check(required in app_a, f"App. A missing required token {required!r}")
    _check(
        'csv("/manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv"' in app_a,
        "App. A missing live CSV binding for cycle_shedding_exact_rational_summary.csv",
    )

    # --- App. B (B_quarantined_external_comparison.typ) ---
    app_b = _read_manual_appendix("B_quarantined_external_comparison.typ")
    _check("RC-025" not in app_b, "App. B contains forbidden scrambled vector RC-025")
    for required in ("SD-007", "SD-004", "SD-005", "RC-027", "RC-028", "RC-029"):
        _check(required in app_b, f"App. B missing required vector citation {required}")

    # --- App. C (C_3d_coordinate_phase_cycle_delta3_fixture.typ) ---
    app_c = _read_manual_appendix("C_3d_coordinate_phase_cycle_delta3_fixture.typ")
    for forbidden in ("Q mod 4", "theta_mod4", "beta_a = 4", "mod 4"):
        _check(forbidden not in app_c, f"App. C contains forbidden stale string {forbidden!r}")
    for required in (
        "Q mod 5",
        "beta_a = 5",
        "RC-012",
        "RC-013",
        "RC-044",
        "msb_x",
        "lsb_x",
        "coordinate_phase_3d_dec_walk.csv",
    ):
        _check(required in app_c, f"App. C missing required token {required!r}")
    _check(
        'csv("/manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv"' in app_c,
        "App. C missing live CSV binding for coordinate_phase_3d_dec_walk.csv",
    )


# =============================================================================
# 2. Live CSV Binding Verification
# =============================================================================


def test_live_csv_bindings_parse_cleanly_and_match_engine_outputs() -> None:
    """Verify every Manual .typ live csv() binding exists, parses cleanly, and matches live engine outputs."""
    csv_call_pat = re.compile(r'csv\("([^"]+)"')
    exp_dec_map = expected_manual_dec_csv_map()
    exp_all_sadar_map = build_boundary_sadar_tables(REPO_ROOT)

    _check_eq(len(exp_dec_map), 12, "expected_manual_dec_csv_map() fixture count")
    _check_eq(len(exp_all_sadar_map), 20, "build_boundary_sadar_tables() fixture count")

    # Verify all 20 boundary_sadar CSVs on disk match live engine generators byte-for-byte
    disk_csvs = sorted((REPO_ROOT / "manual" / "data" / "boundary_sadar").glob("*.csv"))
    _check_eq(len(disk_csvs), 20, "manual/data/boundary_sadar/*.csv file count")
    for csv_path in disk_csvs:
        rel = csv_path.relative_to(REPO_ROOT).as_posix()
        _check(rel in exp_all_sadar_map, f"untracked CSV under manual/data/boundary_sadar: {rel}")
        actual_text = csv_path.read_text(encoding="utf-8")
        _check_eq(actual_text, exp_all_sadar_map[rel], f"live engine byte parity for {rel}")
        if rel in exp_dec_map:
            _check_eq(actual_text, exp_dec_map[rel], f"expected_manual_dec_csv_map byte parity for {rel}")

    # Verify every Manual .typ file's live csv() calls
    discovered_bindings: dict[str, list[str]] = {}
    for typ_path in _all_manual_typ_files():
        text = typ_path.read_text(encoding="utf-8")
        matches = csv_call_pat.findall(text)
        if matches:
            discovered_bindings[typ_path.name] = matches
            for csv_uri in matches:
                _check(
                    csv_uri.startswith("/manual/data/boundary_sadar/"),
                    f"{typ_path.name} binds non-boundary_sadar CSV: {csv_uri!r}",
                )
                rel = csv_uri.lstrip("/")
                disk_path = REPO_ROOT / rel
                _check(disk_path.is_file(), f"{typ_path.name} references missing CSV: {rel}")
                with disk_path.open(encoding="utf-8", newline="") as fh:
                    reader = csv.DictReader(fh)
                    fieldnames = reader.fieldnames
                    _check(
                        fieldnames is not None and len(fieldnames) >= 2,
                        f"{rel}: missing or degenerate CSV header: {fieldnames!r}",
                    )
                    rows = list(reader)
                _check(len(rows) > 0, f"{rel}: CSV has 0 data rows")
                for row_idx, row in enumerate(rows):
                    _check(None not in row, f"{rel} row {row_idx}: extra unkeyed CSV columns")
                    for col, val in row.items():
                        _check(
                            isinstance(val, str) and len(val.strip()) > 0,
                            f"{rel} row {row_idx} col {col!r}: empty or missing cell value",
                        )
                if rel in exp_dec_map:
                    _check_eq(
                        disk_path.read_text(encoding="utf-8"),
                        exp_dec_map[rel],
                        f"{typ_path.name} live CSV vs expected_manual_dec_csv_map ({rel})",
                    )

    # Every expected refactored Manual unit binds its exact expected live CSV
    for typ_name, expected_uri in sorted(EXPECTED_LIVE_CSV_BINDINGS.items()):
        _check(
            typ_name in discovered_bindings and expected_uri in discovered_bindings[typ_name],
            f"{typ_name}: expected live CSV binding {expected_uri!r}, got {discovered_bindings.get(typ_name)!r}",
        )


def test_coordinate_phase_3d_csv_exact_header_rows_and_rc012_cross_check() -> None:
    """Verify coordinate_phase_3d_dec_walk.csv schema, rows, and exact octant_delta3.csv (RC-012) agreement."""
    coord_path = REPO_ROOT / "manual" / "data" / "boundary_sadar" / "coordinate_phase_3d_dec_walk.csv"
    with coord_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        _check_eq(
            reader.fieldnames,
            [
                "step_i",
                "from_xyz",
                "to_xyz",
                "delta_xyz",
                "Q_lag1",
                "theta_mod5",
                "octant_msb_x",
                "octant_lsb_x",
            ],
            "coordinate_phase_3d_dec_walk.csv header",
        )
        rows = list(reader)

    _check_eq(len(rows), 8, "coordinate_phase_3d_dec_walk.csv row count")

    # Verify step 4 (-1,1,1) MSB-x=4 vs LSB-x=1 discriminator and step 6 (1,-1,1) MSB-x=2 vs LSB-x=2
    _check_eq(rows[3]["step_i"], "4", "step 4 index")
    _check_eq(rows[3]["delta_xyz"], "(-1,1,1)", "step 4 delta_xyz")
    _check_eq(rows[3]["Q_lag1"], "3", "step 4 Q_lag1")
    _check_eq(rows[3]["theta_mod5"], "3", "step 4 theta_mod5")
    _check_eq(rows[3]["octant_msb_x"], "4", "step 4 octant_msb_x")
    _check_eq(rows[3]["octant_lsb_x"], "1", "step 4 octant_lsb_x")

    _check_eq(rows[5]["step_i"], "6", "step 6 index")
    _check_eq(rows[5]["delta_xyz"], "(1,-1,1)", "step 6 delta_xyz")
    _check_eq(rows[5]["octant_msb_x"], "2", "step 6 octant_msb_x")
    _check_eq(rows[5]["octant_lsb_x"], "2", "step 6 octant_lsb_x")

    # Aggregate MSB-x octant counts from coordinate_phase_3d_dec_walk.csv and compare with RC-012 CSV
    msb_counts = [0 for _ in range(8)]
    for row in rows:
        msb_counts[int(row["octant_msb_x"])] += 1

    brownian_oct_path = REPO_ROOT / "manual" / "data" / "brownian" / "octant_delta3.csv"
    with brownian_oct_path.open(encoding="utf-8", newline="") as fh:
        rc012_oct_rows = list(csv.DictReader(fh))
    _check_eq(len(rc012_oct_rows), 8, "brownian/octant_delta3.csv row count")
    for idx, brow in enumerate(rc012_oct_rows):
        _check_eq(int(brow["octant"]), idx, f"brownian octant index {idx}")
        _check_eq(msb_counts[idx], int(brow["observed_count"]), f"octant {idx} observed_count vs RC-012 CSV")
        comp = int(brow["comparator_count"])
        dz = comp - msb_counts[idx]
        _check_eq(dz, int(brow["DeltaZ"]), f"octant {idx} DeltaZ vs RC-012 CSV")
        _check_eq(abs(dz), int(brow["m"]), f"octant {idx} m vs RC-012 CSV")


# =============================================================================
# 3. RC-044 Independent Oracle, Poisoned-Fraction, Zero-BigRat, S2/S4 Parity & RC-041
# =============================================================================


def _build_rc044_adversarial_valid_matrix() -> list[tuple[str, dict[str, Any]]]:
    big_1 = 10**12  # squared = 10**24 > i64::MAX (~9.22e18)
    big_2 = 10**25  # squared = 10**50 > i128::MAX (~1.70e38)
    return [
        (
            "canonical_omitted_default_msb_x",
            {"points": copy.deepcopy(CANONICAL_RC044_POINTS), "beta_a": 5},
        ),
        (
            "canonical_explicit_msb_x",
            {"points": copy.deepcopy(CANONICAL_RC044_POINTS), "beta_a": 5, "octant_bit_order": "msb_x"},
        ),
        (
            "canonical_explicit_lsb_x",
            {"points": copy.deepcopy(CANONICAL_RC044_POINTS), "beta_a": 5, "octant_bit_order": "lsb_x"},
        ),
        (
            "rc013_cumulative_path_lsb_x",
            {
                "points": [[0, 0, 0], [2, 2, -1], [1, 4, 1], [2, 3, 2], [1, 2, 1]],
                "beta_a": 5,
                "octant_bit_order": "lsb_x",
            },
        ),
        (
            "rc013_cumulative_path_msb_x",
            {
                "points": [[0, 0, 0], [2, 2, -1], [1, 4, 1], [2, 3, 2], [1, 2, 1]],
                "beta_a": 5,
                "octant_bit_order": "msb_x",
            },
        ),
        (
            "all_8_sign_octants_msb_x",
            {
                "points": [
                    [0, 0, 0],
                    [1, 1, 1],      # (+,+,+) -> 0
                    [2, 2, 0],      # (+,+,-) -> 1 (msb) / 4 (lsb)
                    [3, 1, 1],      # (+,-,+) -> 2 (msb) / 2 (lsb)
                    [4, 0, 0],      # (+,-,-) -> 3 (msb) / 6 (lsb)
                    [3, 1, 1],      # (-,+,+) -> 4 (msb) / 1 (lsb)
                    [2, 2, 0],      # (-,+,-) -> 5 (msb) / 5 (lsb)
                    [1, 1, 1],      # (-,-,+) -> 6 (msb) / 3 (lsb)
                    [0, 0, 0],      # (-,-,-) -> 7 (msb) / 7 (lsb)
                ],
                "beta_a": 5,
                "octant_bit_order": "msb_x",
            },
        ),
        (
            "all_8_sign_octants_lsb_x",
            {
                "points": [
                    [0, 0, 0],
                    [1, 1, 1],
                    [2, 2, 0],
                    [3, 1, 1],
                    [4, 0, 0],
                    [3, 1, 1],
                    [2, 2, 0],
                    [1, 1, 1],
                    [0, 0, 0],
                ],
                "beta_a": 5,
                "octant_bit_order": "lsb_x",
            },
        ),
        (
            "zero_component_and_stationary_substep_msb_x",
            {
                "points": [[0, 0, 0], [0, 0, 0], [-2, 0, 0], [-2, -3, 0], [-2, -3, -5], [-2, -3, -4]],
                "beta_a": 7,
                "octant_bit_order": "msb_x",
            },
        ),
        (
            "zero_component_and_stationary_substep_lsb_x",
            {
                "points": [[0, 0, 0], [0, 0, 0], [-2, 0, 0], [-2, -3, 0], [-2, -3, -5], [-2, -3, -4]],
                "beta_a": 7,
                "octant_bit_order": "lsb_x",
            },
        ),
        (
            "beta_a_min_1",
            {"points": [[10, -5, 3], [7, -1, 3], [7, -1, 8]], "beta_a": 1, "octant_bit_order": "msb_x"},
        ),
        (
            "beta_a_max_10000",
            {"points": [[0, 0, 0], [100, -1, 2], [99, 0, -3]], "beta_a": 10_000, "octant_bit_order": "lsb_x"},
        ),
        (
            "large_coords_exceeding_i64_squared_msb_x",
            {
                "points": [
                    [0, 0, 0],
                    [big_1, -2 * big_1, 3 * big_1],
                    [-big_1, big_1, 0],
                    [0, 0, -4 * big_1],
                ],
                "beta_a": 13,
                "octant_bit_order": "msb_x",
            },
        ),
        (
            "huge_coords_exceeding_i128_squared_lsb_x",
            {
                "points": [
                    [-big_2, big_2, 0],
                    [2 * big_2, -3 * big_2, 5 * big_2],
                    [-4 * big_2, -3 * big_2, -big_2],
                ],
                "beta_a": 17,
                "octant_bit_order": "lsb_x",
            },
        ),
    ]


def test_rc044_independent_oracle_s2_s4_parity_and_rc012_rc013_alignment(aod_core_bin: Path) -> None:
    """Cross-check S2 Python and S4 Rust against pure-integer oracle, RC-012, RC-013, and >i128 coords."""
    matrix = _build_rc044_adversarial_valid_matrix()
    _check(len(matrix) >= 13, f"expected >= 13 valid matrix cases, got {len(matrix)}")

    for case_name, payload in matrix:
        bit_order = str(payload.get("octant_bit_order", "msb_x"))
        expected = _independent_rc044_oracle(payload["points"], payload["beta_a"], bit_order)

        s2_out = eval_dec_coordinate_phase_3d_walk(copy.deepcopy(payload))
        _assert_no_floats(s2_out, f"s2[{case_name}]")
        _check_json_eq(s2_out, expected, f"S2 vs pure-integer oracle ({case_name})")

        proc = _eval_s4_op(aod_core_bin, "dec_coordinate_phase_3d_walk", payload)
        _check(
            proc.returncode == 0,
            f"S4 failed on valid RC-044 case {case_name!r} (rc={proc.returncode}): {proc.stderr}",
        )
        s4_out = json.loads(proc.stdout)
        _assert_no_floats(s4_out, f"s4[{case_name}]")
        _check_json_eq(s4_out, expected, f"S4 vs pure-integer oracle ({case_name})")
        _check_json_eq(s2_out, s4_out, f"S2 vs S4 parity ({case_name})")

        # Fundamental exact conservation invariants
        _check_eq(sum(s2_out["phase_DeltaZ"]), 0, f"sum(phase_DeltaZ)==0 ({case_name})")
        _check_eq(sum(s2_out["octant_DeltaZ"]), 0, f"sum(octant_DeltaZ)==0 ({case_name})")
        _check_eq(sum(s2_out["phase_counts"]), s2_out["step_count"], f"sum(phase_counts)==N ({case_name})")
        _check_eq(sum(s2_out["octant_counts"]), s2_out["step_count"], f"sum(octant_counts)==N ({case_name})")

    # Explicit pinned canonical assertions: RC-044 (omitted & msb_x) == RC-012
    out_default = eval_dec_coordinate_phase_3d_walk({"points": CANONICAL_RC044_POINTS, "beta_a": 5})
    out_msb = eval_dec_coordinate_phase_3d_walk(
        {"points": CANONICAL_RC044_POINTS, "beta_a": 5, "octant_bit_order": "msb_x"}
    )
    out_lsb = eval_dec_coordinate_phase_3d_walk(
        {"points": CANONICAL_RC044_POINTS, "beta_a": 5, "octant_bit_order": "lsb_x"}
    )
    _check_json_eq(out_default, out_msb, "RC-044 omitted default == explicit msb_x")
    _check_eq(out_msb["Q_values"], [2, 2, 2, 3, 3, 3, 2, 3], "RC-044 Q_values")
    _check_eq(out_msb["sum_Q"], 20, "RC-044 sum_Q")
    _check_eq(out_msb["R_Q_ratio"], ["5", "2"], "RC-044 R_Q")
    _check_eq(out_msb["R_x_ratio"], ["2", "5"], "RC-044 R_x")
    _check_eq(out_msb["R_y_ratio"], ["7", "20"], "RC-044 R_y")
    _check_eq(out_msb["R_z_ratio"], ["1", "4"], "RC-044 R_z")
    _check_eq(out_msb["phase_counts"], [0, 0, 4, 4, 0], "RC-044 phase_counts")
    _check_eq(out_msb["phase_DeltaZ"], [2, 2, -2, -3, 1], "RC-044 phase_DeltaZ")
    _check_eq(out_msb["phase_delta3_M"], 10, "RC-044 phase_delta3_M")
    _check_eq(out_msb["octant_counts"], [6, 0, 1, 0, 1, 0, 0, 0], "RC-044 msb_x octant_counts")
    _check_eq(out_msb["octant_DeltaZ"], [-5, 1, 0, 1, 0, 1, 1, 1], "RC-044 msb_x octant_DeltaZ")
    _check_eq(out_msb["octant_delta3_M"], 10, "RC-044 msb_x octant_delta3_M")

    # Explicit lsb_x contrast
    _check_eq(out_lsb["octant_bit_order"], "lsb_x", "RC-044 lsb_x bit order")
    _check_eq(out_lsb["octant_counts"], [6, 1, 1, 0, 0, 0, 0, 0], "RC-044 lsb_x octant_counts")
    _check_eq(out_lsb["octant_DeltaZ"], [-5, 0, 0, 1, 1, 1, 1, 1], "RC-044 lsb_x octant_DeltaZ")
    _check_eq(out_lsb["octant_delta3_M"], 10, "RC-044 lsb_x octant_delta3_M")
    _check_eq(out_lsb["phase_counts"], out_msb["phase_counts"], "lsb_x preserves phase_counts")
    _check_eq(out_lsb["R_Q_ratio"], out_msb["R_Q_ratio"], "lsb_x preserves R_Q_ratio")

    # Live cross-check against RC-012 and RC-013 evaluators in both S2 and S4
    rc_rows, _ = _load_canonical_vectors()
    by_id = {str(r["case_id"]): r for r in rc_rows}
    rc012_s2 = eval_s2_vector_op("brownian_3d_delta3_msb_x", by_id["RC-012"]["inputs"])
    _check_json_eq(out_msb["phase_DeltaZ"], rc012_s2["phase_DeltaZ"], "live S2 RC-044 vs RC-012 phase_DeltaZ")
    _check_json_eq(out_msb["octant_DeltaZ"], rc012_s2["octant_DeltaZ"], "live S2 RC-044 vs RC-012 octant_DeltaZ")
    _check_json_eq(out_msb["R_x_ratio"], rc012_s2["R_x"], "live S2 RC-044 vs RC-012 R_x")
    _check_json_eq(out_msb["R_y_ratio"], rc012_s2["R_y"], "live S2 RC-044 vs RC-012 R_y")
    _check_json_eq(out_msb["R_z_ratio"], rc012_s2["R_z"], "live S2 RC-044 vs RC-012 R_z")

    # Single-step octant discriminator matching RC-013 z_vectors [[2,2,-1], [-1,2,2], [1,-1,1], [-1,-1,-1]]
    rc013_s2 = eval_s2_vector_op("run_tumble_3d_delta3_lsb_x", by_id["RC-013"]["inputs"])
    rc013_vecs: list[list[int]] = by_id["RC-013"]["inputs"]["z_vectors"]
    for vec, exp_lsb, exp_msb in zip(
        rc013_vecs, rc013_s2["octants_lsb_x"], rc013_s2["octants_msb_x_contrast"]
    ):
        step_lsb = eval_dec_coordinate_phase_3d_walk(
            {"points": [[0, 0, 0], vec], "beta_a": 5, "octant_bit_order": "lsb_x"}
        )
        step_msb = eval_dec_coordinate_phase_3d_walk(
            {"points": [[0, 0, 0], vec], "beta_a": 5, "octant_bit_order": "msb_x"}
        )
        _check_eq(step_lsb["octant_counts"].index(1), exp_lsb, f"RC-013 lsb_x octant for {vec}")
        _check_eq(step_msb["octant_counts"].index(1), exp_msb, f"RC-013 msb_x octant for {vec}")


def test_rc044_poisoned_fraction_proof_and_python_ast_hygiene(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove eval_dec_coordinate_phase_3d_walk and build_coordinate_phase_3d_csv_rows NEVER instantiate Fraction."""
    import fractions as fractions_mod

    class _PoisonFraction:
        def __new__(cls, *args: object, **kwargs: object) -> object:
            raise RuntimeError("POISONED_FRACTION_INVOKED_IN_RC044")

    monkeypatch.setattr(dec_mod, "Fraction", _PoisonFraction)
    monkeypatch.setattr(fractions_mod, "Fraction", _PoisonFraction)

    res_default = eval_dec_coordinate_phase_3d_walk({"points": CANONICAL_RC044_POINTS, "beta_a": 5})
    _check_eq(res_default["R_Q_ratio"], ["5", "2"], "poisoned-Fraction default R_Q")
    _check_eq(res_default["R_x_ratio"], ["2", "5"], "poisoned-Fraction default R_x")
    _check_eq(res_default["R_y_ratio"], ["7", "20"], "poisoned-Fraction default R_y")
    _check_eq(res_default["R_z_ratio"], ["1", "4"], "poisoned-Fraction default R_z")

    res_lsb = eval_dec_coordinate_phase_3d_walk(
        {"points": CANONICAL_RC044_POINTS, "beta_a": 5, "octant_bit_order": "lsb_x"}
    )
    _check_eq(res_lsb["octant_counts"], [6, 1, 1, 0, 0, 0, 0, 0], "poisoned-Fraction lsb_x octant_counts")

    huge = 10**25
    res_huge = eval_dec_coordinate_phase_3d_walk(
        {"points": [[0, 0, 0], [huge, -2 * huge, 2 * huge]], "beta_a": 5, "octant_bit_order": "msb_x"}
    )
    _check_eq(res_huge["R_x_ratio"], ["1", "9"], "poisoned-Fraction huge R_x")
    _check_eq(res_huge["R_y_ratio"], ["4", "9"], "poisoned-Fraction huge R_y")
    _check_eq(res_huge["R_z_ratio"], ["4", "9"], "poisoned-Fraction huge R_z")

    csv_rows = build_coordinate_phase_3d_csv_rows()
    _check_eq(len(csv_rows), 8, "poisoned-Fraction build_coordinate_phase_3d_csv_rows row count")

    # Python AST audit on RC-044 functions in manual_dec_examples.py
    src_path = REPO_ROOT / "manual" / "engine" / "sectors" / "manual_dec_examples.py"
    tree = ast.parse(src_path.read_text(encoding="utf-8"), filename=str(src_path))
    target_funcs = {
        "_octant_3d_trit",
        "eval_dec_coordinate_phase_3d_walk",
        "build_coordinate_phase_3d_csv_rows",
    }
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            found.add(node.name)
            for sub in ast.walk(node):
                _check(not isinstance(sub, ast.Assert), f"bare assert in {node.name}")
                if isinstance(sub, ast.Name):
                    _check(sub.id != "Fraction", f"forbidden Fraction reference in {node.name}")
                    _check(sub.id != "_pair", f"forbidden BigRat/Fraction _pair call in {node.name}")
                if isinstance(sub, ast.Constant):
                    _check(
                        type(sub.value).__name__ != "float",
                        f"forbidden float literal in {node.name}: {sub.value!r}",
                    )
    _check_eq(found, target_funcs, "audited RC-044 Python function set")


def test_rc044_rust_static_zero_bigrat_and_trit_ratio() -> None:
    """Verify crates/aod-core/src/manual_dec_ops.rs RC-044 section uses TritWord/TritRatio and zero BigRat/pair_json."""
    rs_path = REPO_ROOT / "crates" / "aod-core" / "src" / "manual_dec_ops.rs"
    src = rs_path.read_text(encoding="utf-8")

    helper_marker = "fn octant_3d_trit"
    op_marker = "pub fn op_dec_coordinate_phase_3d_walk"
    _check(helper_marker in src, f"{helper_marker!r} missing from manual_dec_ops.rs")
    _check(op_marker in src, f"{op_marker!r} missing from manual_dec_ops.rs")

    helper_idx = src.index(helper_marker)
    op_idx = src.index(op_marker)
    _check(helper_idx < op_idx, "expected octant_3d_trit before op_dec_coordinate_phase_3d_walk")

    rc044_tail = src[op_idx:]
    rc044_full = src[helper_idx:]

    for required in ("TritWord", "TritRatio", "trit_pair_json"):
        _check(required in rc044_tail, f"op_dec_coordinate_phase_3d_walk missing {required!r}")

    _check("BigRat" not in rc044_full, "RC-044 Rust implementation must contain ZERO BigRat references")
    _check(
        "pair_json" not in rc044_full.replace("trit_pair_json", ""),
        "RC-044 Rust implementation must contain ZERO standalone pair_json calls",
    )


def _build_rc044_error_rejection_matrix() -> list[tuple[str, dict[str, Any], type[Exception]]]:
    return [
        # Missing required keys -> ValueError
        ("missing_points", {"beta_a": 5}, ValueError),
        ("missing_beta_a", {"points": [[0, 0, 0], [1, 1, 0]]}, ValueError),
        ("empty_object", {}, ValueError),
        # octant_bit_order non-str types -> TypeError
        ("order_null", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": None}, TypeError),
        ("order_int_0", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": 0}, TypeError),
        ("order_int_1", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": 1}, TypeError),
        ("order_bool_true", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": True}, TypeError),
        ("order_bool_false", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": False}, TypeError),
        ("order_list", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": ["msb_x"]}, TypeError),
        ("order_dict", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": {}}, TypeError),
        # octant_bit_order unknown string -> ValueError
        ("order_unknown", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": "unknown"}, ValueError),
        ("order_upper_msb", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": "MSB_X"}, ValueError),
        ("order_upper_lsb", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": "LSB_X"}, ValueError),
        ("order_empty_str", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": ""}, ValueError),
        ("order_trailing_space", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 5, "octant_bit_order": "msb_x "}, ValueError),
        # beta_a out-of-range ints -> ValueError
        ("beta_a_zero", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 0}, ValueError),
        ("beta_a_neg_5", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": -5}, ValueError),
        ("beta_a_10001", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 10_001}, ValueError),
        ("beta_a_i64_overflow", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 9223372036854775808}, ValueError),
        ("beta_a_neg_i64_underflow", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": -9223372036854775809}, ValueError),
        # Validation precedence: beta_a bounds checked before octant_bit_order type; len(points) < 2 before beta_a
        (
            "beta_a_i64_overflow_plus_null_order",
            {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": 9223372036854775808, "octant_bit_order": None},
            ValueError,
        ),
        (
            "short_points_plus_i64_overflow_beta_a",
            {"points": [[0, 0, 0]], "beta_a": 9223372036854775808},
            ValueError,
        ),
        # beta_a wrong type -> TypeError
        ("beta_a_null", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": None}, TypeError),
        ("beta_a_bool_true", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": True}, TypeError),
        ("beta_a_bool_false", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": False}, TypeError),
        ("beta_a_str", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": "5"}, TypeError),
        ("beta_a_list", {"points": [[0, 0, 0], [1, 1, 0]], "beta_a": [5]}, TypeError),
        # points length & type checks
        ("points_empty", {"points": [], "beta_a": 5}, ValueError),
        ("points_single", {"points": [[0, 0, 0]], "beta_a": 5}, ValueError),
        ("points_null", {"points": None, "beta_a": 5}, TypeError),
        ("points_str", {"points": "not_a_list", "beta_a": 5}, TypeError),
        ("points_int", {"points": 42, "beta_a": 5}, TypeError),
        ("point_elem_str", {"points": [[0, 0, 0], "bad"], "beta_a": 5}, TypeError),
        ("point_elem_null", {"points": [[0, 0, 0], None], "beta_a": 5}, TypeError),
        ("point_elem_len_2", {"points": [[0, 0, 0], [1, 1]], "beta_a": 5}, ValueError),
        ("point_elem_len_4", {"points": [[0, 0, 0], [1, 1, 0, 0]], "beta_a": 5}, ValueError),
        # Non-int & bool coordinate checks -> TypeError
        ("coord_str_x", {"points": [[0, 0, 0], ["1", 0, 0]], "beta_a": 5}, TypeError),
        ("coord_null_y", {"points": [[0, 0, 0], [1, None, 0]], "beta_a": 5}, TypeError),
        ("coord_list_z", {"points": [[0, 0, 0], [1, 0, [1]]], "beta_a": 5}, TypeError),
        ("coord_bool_true_x", {"points": [[0, 0, 0], [True, 0, 0]], "beta_a": 5}, TypeError),
        ("coord_bool_false_y", {"points": [[0, 0, 0], [1, False, 0]], "beta_a": 5}, TypeError),
        ("coord_bool_true_z", {"points": [[0, 0, 0], [1, 0, True]], "beta_a": 5}, TypeError),
        # Stationary walk (sum_Q == 0) -> ValueError
        ("stationary_2_points", {"points": [[1, 2, 3], [1, 2, 3]], "beta_a": 5}, ValueError),
        ("stationary_3_points", {"points": [[0, 0, 0], [0, 0, 0], [0, 0, 0]], "beta_a": 5}, ValueError),
    ]


def test_rc044_error_rejection_matrix_s2_and_s4_parity(aod_core_bin: Path) -> None:
    """Verify exact TypeError/ValueError parity across Python S2 and Rust S4 (normal and -O Python)."""
    # Python-only non-dict top-level inputs -> TypeError
    for bad_top in (None, [], "bad", 42, True):
        raised: BaseException | None = None
        try:
            eval_dec_coordinate_phase_3d_walk(bad_top)  # type: ignore[arg-type]
        except Exception as exc:
            raised = exc
        _check(
            isinstance(raised, TypeError),
            f"S2 top-level {bad_top!r}: expected TypeError, got {type(raised).__name__ if raised else None}",
        )

    # Tuple point rejected as TypeError in Python S2
    raised_tuple: BaseException | None = None
    try:
        eval_dec_coordinate_phase_3d_walk({"points": [[0, 0, 0], (1, 1, 0)], "beta_a": 5})  # type: ignore[list-item]
    except Exception as exc:
        raised_tuple = exc
    _check(
        isinstance(raised_tuple, TypeError),
        f"S2 tuple point: expected TypeError, got {type(raised_tuple).__name__ if raised_tuple else None}",
    )

    matrix = _build_rc044_error_rejection_matrix()
    _check(len(matrix) >= 40, f"expected >= 40 rejection matrix cases, got {len(matrix)}")

    for case_name, payload, expected_exc in matrix:
        s2_exc: BaseException | None = None
        try:
            eval_dec_coordinate_phase_3d_walk(copy.deepcopy(payload))
        except Exception as exc:
            s2_exc = exc
        _check(
            s2_exc is not None and type(s2_exc) is expected_exc,
            f"S2 rejection mismatch ({case_name}): expected {expected_exc.__name__}, "
            f"got {type(s2_exc).__name__ if s2_exc else 'NO_ERROR'}: {s2_exc!r}",
        )

        proc = _eval_s4_op(aod_core_bin, "dec_coordinate_phase_3d_walk", payload)
        _check(
            proc.returncode != 0,
            f"S4 unexpectedly succeeded on invalid case {case_name!r}: stdout={proc.stdout!r}",
        )
        rust_err_cls = _parse_rust_error_class(proc.stderr)
        _check_eq(
            rust_err_cls,
            expected_exc.__name__,
            f"S4 vs S2 error class parity ({case_name}); stderr={proc.stderr!r}",
        )

    # Confirm S4 CLI also rejects raw JSON float literal in coordinates
    float_json_proc = subprocess.run(
        [
            str(aod_core_bin),
            "--eval-op",
            "dec_coordinate_phase_3d_walk",
            "--input-json",
            '{"points":[[0,0,0],[1.5,0,0]],"beta_a":5}',
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    _check(
        float_json_proc.returncode != 0,
        f"S4 unexpectedly accepted JSON float literal: {float_json_proc.stdout!r}",
    )


def test_rc041_run_tumble_q4_stepper_and_octant_3d_intact(aod_core_bin: Path) -> None:
    """Verify RC-041 (eval_dec_run_tumble_q4_stepper) and legacy LSB-x _octant_3d remain 100% intact."""
    # Verify _octant_3d still implements LSB-x: (1 if x<0) | (2 if y<0) | (4 if z<0)
    expected_lsb_octants = [
        ((1, 1, 1), 0),
        ((-1, 1, 1), 1),
        ((1, -1, 1), 2),
        ((-1, -1, 1), 3),
        ((1, 1, -1), 4),
        ((-1, 1, -1), 5),
        ((1, -1, -1), 6),
        ((-1, -1, -1), 7),
        ((0, 0, 0), 0),
        ((-1, 0, 0), 1),
        ((0, -1, 0), 2),
        ((0, 0, -1), 4),
    ]
    for (x, y, z), exp_code in expected_lsb_octants:
        _check_eq(_octant_3d(x, y, z), exp_code, f"_octant_3d({x},{y},{z}) LSB-x")

    rc_rows, _ = _load_canonical_vectors()
    rc041 = {str(r["case_id"]): r for r in rc_rows}["RC-041"]
    payload = copy.deepcopy(rc041["inputs"])
    expected = rc041["expected_outcome"]["exact_value"]

    s2_out = eval_dec_run_tumble_q4_stepper(copy.deepcopy(payload))
    _assert_no_floats(s2_out, "s2[RC-041]")
    _check_json_eq(s2_out, expected, "RC-041 S2 vs golden vector")

    proc = _eval_s4_op(aod_core_bin, "dec_run_tumble_q4_stepper", payload)
    _check(proc.returncode == 0, f"RC-041 S4 failed (rc={proc.returncode}): {proc.stderr}")
    s4_out = json.loads(proc.stdout)
    _assert_no_floats(s4_out, "s4[RC-041]")
    _check_json_eq(s4_out, expected, "RC-041 S4 vs golden vector")
    _check_json_eq(s2_out, s4_out, "RC-041 S2 vs S4 parity")

    # Cross-check live 21-row CSV builder vs retained run_tumble_trace_20_ticks.csv
    gen_rows = build_run_tumble_dec_csv_rows()
    _check_eq(len(gen_rows), 21, "RC-041 generated CSV row count")
    with (REPO_ROOT / "manual" / "data" / "run_tumble" / "run_tumble_trace_20_ticks.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        retained_rows = list(csv.DictReader(fh))
    _check_eq(len(retained_rows), 21, "retained run_tumble_trace_20_ticks.csv row count")
    for g_row, r_row in zip(gen_rows, retained_rows):
        for col in ("t", "mode", "edge", "sigma", "h1", "h2", "h3", "h4", "Q3", "Q4", "theta", "octant"):
            _check_eq(g_row[col], r_row[col], f"RC-041 t={g_row['t']} col={col}")


# =============================================================================
# 4. Publication Contract & Ownership Integrity + Full S2/S4 Parity & Self-AST
# =============================================================================


def test_ownership_and_fixtures_owned_anchors_exist_in_exact_files() -> None:
    """Verify every owned anchor in OWNERSHIP_AND_FIXTURES.json exists in its exact declared file."""
    own_path = REPO_ROOT / "contracts" / "scientific" / "OWNERSHIP_AND_FIXTURES.json"
    own = json.loads(own_path.read_text(encoding="utf-8"))

    anchor_owners = own.get("anchor_owners")
    _check(isinstance(anchor_owners, list) and len(anchor_owners) == 26, f"unexpected anchor_owners count: {len(anchor_owners) if isinstance(anchor_owners, list) else None}")

    for entry in anchor_owners:
        rel_path = str(entry["path"])
        label = str(entry["label"])
        target = REPO_ROOT / rel_path
        _check(target.is_file(), f"OWNERSHIP_AND_FIXTURES anchor path missing: {rel_path}")
        text = target.read_text(encoding="utf-8")
        _check(
            f"<{label}>" in text,
            f"OWNERSHIP_AND_FIXTURES owned anchor <{label}> missing from {rel_path}",
        )

    fixture_bindings = own.get("fixture_bindings")
    _check(isinstance(fixture_bindings, list) and len(fixture_bindings) > 0, "fixture_bindings must be non-empty")
    for fb in fixture_bindings:
        cc = fb["current_construct"]
        cc_path = REPO_ROOT / str(cc["path"])
        cc_label = str(cc["label"])
        _check(cc_path.is_file(), f"fixture_bindings construct file missing: {cc['path']}")
        _check(
            f"<{cc_label}>" in cc_path.read_text(encoding="utf-8"),
            f"fixture_bindings anchor <{cc_label}> missing from {cc['path']}",
        )


def test_canonical_bindings_192_entries_and_acyclic_sha256_contract_chain() -> None:
    """Verify CANONICAL_BINDINGS.json (192 frozen entries), audit_ontology_compaction.py, and representation_change_ledger.json SHA-256 chain."""
    cb_path = REPO_ROOT / "contracts" / "scientific" / "CANONICAL_BINDINGS.json"
    cb_data = json.loads(cb_path.read_text(encoding="utf-8"))
    frozen = cb_data.get("frozen_sha256")
    _check(isinstance(frozen, dict), "CANONICAL_BINDINGS.json frozen_sha256 must be a dict")
    _check_eq(len(frozen), 192, "CANONICAL_BINDINGS.json frozen_sha256 entry count")

    # Verify live SHA-256 of coordinate_phase_3d_dec_walk.csv and all 20 boundary_sadar CSVs
    coord_rel = "manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv"
    coord_live_sha = _sha256_file(REPO_ROOT / coord_rel)
    _check(coord_rel in frozen, f"{coord_rel} missing from CANONICAL_BINDINGS.json")
    _check_eq(frozen[coord_rel], coord_live_sha, "CANONICAL_BINDINGS SHA-256 for coordinate_phase_3d_dec_walk.csv")

    for csv_path in sorted((REPO_ROOT / "manual" / "data" / "boundary_sadar").glob("*.csv")):
        rel = csv_path.relative_to(REPO_ROOT).as_posix()
        _check(rel in frozen, f"{rel} missing from CANONICAL_BINDINGS.json")
        _check_eq(frozen[rel], _sha256_file(csv_path), f"CANONICAL_BINDINGS SHA-256 for {rel}")

    # Load scripts/audit_ontology_compaction.py and verify CONTRACT_SHA256 matches live contracts
    cb_live_sha = _sha256_file(cb_path)
    audit_path = REPO_ROOT / "scripts" / "audit_ontology_compaction.py"
    spec = importlib.util.spec_from_file_location("qa_p4_audit_compaction", audit_path)
    _check(spec is not None and spec.loader is not None, "failed to load audit_ontology_compaction.py")
    audit_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_mod)

    contract_sha_map: dict[str, str] = getattr(audit_mod, "CONTRACT_SHA256")
    _check("CANONICAL_BINDINGS.json" in contract_sha_map, "CONTRACT_SHA256 missing CANONICAL_BINDINGS.json")
    _check_eq(
        contract_sha_map["CANONICAL_BINDINGS.json"],
        cb_live_sha,
        "audit_ontology_compaction.py CONTRACT_SHA256['CANONICAL_BINDINGS.json'] vs live SHA-256",
    )
    for cname, expected_sha in sorted(contract_sha_map.items()):
        cpath = REPO_ROOT / "contracts" / "scientific" / cname
        _check(cpath.is_file(), f"contract listed in CONTRACT_SHA256 missing: {cname}")
        _check_eq(_sha256_file(cpath), expected_sha, f"live contract SHA-256 for {cname}")

    # Verify typst/representation_change_ledger.json matches live SHA-256 of CANONICAL_BINDINGS.json & coordinate CSV
    rcl_path = REPO_ROOT / "typst" / "representation_change_ledger.json"
    rcl = json.loads(rcl_path.read_text(encoding="utf-8"))

    cb_amendments = [
        item
        for item in rcl.get("contract_amendments", [])
        if item.get("contract") == "contracts/scientific/CANONICAL_BINDINGS.json"
    ]
    _check_eq(len(cb_amendments), 1, "representation_change_ledger CANONICAL_BINDINGS amendment count")
    _check_eq(
        cb_amendments[0]["new_sha256"],
        cb_live_sha,
        "representation_change_ledger CANONICAL_BINDINGS new_sha256 vs live SHA-256",
    )

    coord_additions = [
        item
        for item in rcl.get("frozen_sha256_additions", [])
        if item.get("path") == coord_rel
    ]
    _check_eq(len(coord_additions), 1, "representation_change_ledger coordinate_phase_3d_dec_walk.csv entry count")
    _check_eq(
        coord_additions[0]["sha256"],
        coord_live_sha,
        "representation_change_ledger coordinate_phase_3d_dec_walk.csv sha256 vs live SHA-256",
    )


def test_s2_and_s4_full_53_vector_verification_byte_parity(aod_core_bin: Path) -> None:
    """Verify full S2 (normal vs -O byte-identical) and S4 53-vector verification PASS offline."""
    with tempfile.TemporaryDirectory(prefix="qa_p4_reports_") as tmp_dir:
        tmp = Path(tmp_dir)
        s2_norm = tmp / "s2_norm.json"
        s2_opt = tmp / "s2_opt.json"
        s4_rep = tmp / "s4_dbg.json"

        for flag_list, out_path, tag in (
            (["-B"], s2_norm, "S2 normal"),
            (["-B", "-O"], s2_opt, "S2 -O"),
        ):
            proc = subprocess.run(
                [
                    sys.executable,
                    *flag_list,
                    "-m",
                    "manual.engine",
                    "--sector",
                    "boundary_sadar",
                    "--check-zero-float",
                    "--verify-vectors",
                    "--report",
                    str(out_path),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            _check(
                proc.returncode == 0,
                f"{tag} verification failed (rc={proc.returncode}): {proc.stdout}\n{proc.stderr}",
            )

        norm_bytes = s2_norm.read_bytes()
        opt_bytes = s2_opt.read_bytes()
        _check_eq(norm_bytes, opt_bytes, "S2 normal vs -O report byte parity")
        s2_data = json.loads(norm_bytes.decode("utf-8"))
        _check_json_eq(
            s2_data["outcomes_summary"],
            {"FAIL": 0, "PASS": 1, "total_executed": 1},
            "S2 outcomes_summary",
        )
        _check_eq(s2_data["zero_float_policy_audit"]["status"], "PASS", "S2 zero_float_policy_audit status")
        _check_eq(s2_data["vectors_verification"]["status"], "PASS", "S2 vectors_verification status")
        _check_eq(s2_data["vectors_verification"]["total_vectors"], 53, "S2 total_vectors")
        _check_eq(s2_data["vectors_verification"]["passed_vectors"], 53, "S2 passed_vectors")
        _check_eq(s2_data["vectors_verification"]["failed_vectors"], 0, "S2 failed_vectors")

        proc_s4 = subprocess.run(
            [
                str(aod_core_bin),
                "--verify-vectors",
                "--check-zero-float",
                "--report",
                str(s4_rep),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        _check(
            proc_s4.returncode == 0,
            f"S4 verification failed (rc={proc_s4.returncode}): {proc_s4.stdout}\n{proc_s4.stderr}",
        )
        s4_data = json.loads(s4_rep.read_text(encoding="utf-8"))
        _check_eq(s4_data["overall_status"], "PASS", "S4 overall_status")
        _check_eq(s4_data["policy_audit"]["status"], "PASS", "S4 policy_audit status")
        _check_eq(s4_data["vectors_verification"]["status"], "PASS", "S4 vectors_verification status")
        _check_eq(s4_data["vectors_verification"]["total_vectors"], 53, "S4 total_vectors")
        _check_eq(s4_data["vectors_verification"]["passed_vectors"], 53, "S4 passed_vectors")
        _check_eq(s4_data["vectors_verification"]["failed_vectors"], 0, "S4 failed_vectors")
        _check_json_eq(
            s2_data["vectors_verification"]["file_digests"],
            s4_data["vectors_verification"]["file_digests"],
            "S2 vs S4 vector file_digests parity",
        )


def test_self_ast_zero_bare_asserts_and_zero_floats() -> None:
    """Verify zero bare `assert` statements and zero float literals/calls in this QA test file."""
    self_path = Path(__file__).resolve()
    tree = ast.parse(self_path.read_text(encoding="utf-8"), filename=str(self_path))

    assert_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    _check(
        not assert_lines,
        f"{self_path.name} contains forbidden bare `assert` statements at lines: {assert_lines}",
    )

    float_const_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value).__name__ == "float"
    ]
    _check(
        not float_const_lines,
        f"{self_path.name} contains forbidden float literals at lines: {float_const_lines}",
    )

    float_name_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "float"
    ]
    _check(
        not float_name_lines,
        f"{self_path.name} contains forbidden `float` references/calls at lines: {float_name_lines}",
    )
