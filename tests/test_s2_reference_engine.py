"""Comprehensive Stage 2 (S2) reference engine test suite covering Gates G1-G7.

All tests are designed to execute identically under normal Python and ``python3 -O``.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from manual.engine import (
    BASE_COMMIT_BINDING,
    REPORT_SCHEMA,
    SECTOR_MAP,
    SECTOR_SPECS,
    VECTOR_SCHEMA,
    audit_source_tree,
    build_report,
    canonical_rational_pair,
    canonical_rational_str,
    exact_isclose,
    format_rational_fixed,
    loads_zero_float,
    parse_canonical_rational_pair,
    parse_exact_int,
    parse_printed_rational,
    registry_digest,
    require,
    require_exact_int,
    require_no_floats,
    round_rational_half_even,
    serialize_report,
    validate_report,
    validate_vector_record,
    verify_all_vectors,
    verify_data_coverage,
    verify_registry_completeness,
)
from manual.engine.cli import main as engine_main, validate_runtime_output_path
from manual.engine.sectors import tier1_adapters, tier2_exact, tier3_quarantine
from manual.engine.vectors import verify_single_vector

ROOT = Path(__file__).resolve().parents[1]

FAST_15_SECTORS: tuple[str, ...] = tuple(
    spec.sector_id for spec in SECTOR_SPECS if spec.sector_id != "temporal_anchor"
)


def _opt_flags() -> list[str]:
    return ["-O"] * sys.flags.optimize


def _run_cli(
    args: list[str],
    *,
    cwd: Path = ROOT,
    optimize: int | None = None,
) -> subprocess.CompletedProcess[str]:
    opt = sys.flags.optimize if optimize is None else optimize
    argv = [sys.executable, "-B", *(["-O"] * opt), "-m", "manual.engine", *args]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=300)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _copy_files(dest_root: Path, rel_paths: list[str] | tuple[str, ...]) -> None:
    for rel in rel_paths:
        src = ROOT / rel
        dst = dest_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _repin_temp_bindings(temp_root: Path, rel_path: str) -> None:
    cb_path = temp_root / "contracts/scientific/CANONICAL_BINDINGS.json"
    doc = json.loads(cb_path.read_text(encoding="utf-8"))
    doc["frozen_sha256"][rel_path] = hashlib.sha256((temp_root / rel_path).read_bytes()).hexdigest()
    cb_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Gate G1 — Coverage (16 Sectors + 17 manual/data Subdirs / 116 Files + Root)
# ---------------------------------------------------------------------------


def test_g1_registry_16_sectors_and_deterministic_digest():
    verify_registry_completeness()
    assert len(SECTOR_SPECS) == 16
    assert len(SECTOR_MAP) == 16
    tiers = [s.tier for s in SECTOR_SPECS]
    assert tiers.count("tier1_canonical_adapter") == 9
    assert tiers.count("tier2_exact_data_verifier") == 6
    assert tiers.count("tier3_provenance_guard") == 1
    d1 = registry_digest()
    d2 = registry_digest()
    assert len(d1) == 64 and d1 == d2

    proc = _run_cli(["--list-sectors"])
    assert proc.returncode == 0, proc.stderr
    listed = loads_zero_float(proc.stdout)
    assert isinstance(listed, dict)
    assert listed["sector_count"] == 16
    assert listed["registry_digest"] == d1


def test_g1_dual_data_coverage_17_subdirs_116_files_plus_root():
    cov = verify_data_coverage(ROOT)
    assert cov["status"] == "PASS"
    assert cov["manual_data_subdirs"] == 17
    assert cov["manual_data_files"] == 116
    assert cov["root_data_files"] == 2
    assert cov["uncovered_files"] == 0
    overlaps = cov["declared_data_overlaps"]
    assert "wavelet_shedding_simulation.csv" in overlaps
    assert "manual/data/derived/tau_ring_diagnostic.csv" in overlaps
    assert "manual/data/tau/aod_tau_fractal_ring_summary.csv" in overlaps
    assert "manual/data/sparc/NGC2403_rotmod.dat" in overlaps


def test_g1_uncovered_or_missing_manual_data_file_fails_closed(tmp_path: Path):
    shutil.copytree(ROOT / "manual/data", tmp_path / "manual/data")
    _copy_files(tmp_path, ["wavelet_shedding_simulation.csv", "cycle_shedding_summary.tex"])
    assert verify_data_coverage(tmp_path)["status"] == "PASS"

    # Extra uncovered file fails closed
    extra = tmp_path / "manual/data/dec/unbound_extra.csv"
    extra.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected 116 files"):
        verify_data_coverage(tmp_path)
    extra.unlink()

    # Missing required file fails closed
    (tmp_path / "manual/data/dec/dec_hinge_slide_example.csv").unlink()
    with pytest.raises(ValueError, match="expected 116 files"):
        verify_data_coverage(tmp_path)


def test_g1_cli_rejects_unknown_duplicate_conflicting_and_empty_flags():
    assert _run_cli(["--sector", "unknown_sector_xyz"]).returncode == 2
    assert _run_cli(["--sector", "dec_ledger", "--sector", "dec_ledger"]).returncode == 2
    assert _run_cli(["--verify-all", "--sector", "dec_ledger"]).returncode == 2
    assert _run_cli([]).returncode == 2


# ---------------------------------------------------------------------------
# Gate G2 — Execution, Subprocess Isolation, -O Propagation & Group-B Safety
# ---------------------------------------------------------------------------


def test_g2_15_fast_sectors_execute_with_orthogonal_status_and_diagnostics(tmp_path: Path):
    report_path = tmp_path / "fast15_report.json"
    diag_dir = tmp_path / "diag"
    args = ["--check-zero-float", "--verify-vectors", "--report", str(report_path), "--diagnostics-dir", str(diag_dir)]
    for sid in FAST_15_SECTORS:
        args.extend(["--sector", sid])

    proc = _run_cli(args)
    assert proc.returncode == 0, proc.stderr
    raw_text = report_path.read_text(encoding="utf-8")
    parsed = loads_zero_float(raw_text)
    assert isinstance(parsed, dict)
    validate_report(parsed)

    assert parsed["schema"] == REPORT_SCHEMA
    assert parsed["base_commit_binding"] == BASE_COMMIT_BINDING
    assert parsed["outcomes_summary"] == {"total_executed": 15, "PASS": 15, "FAIL": 0}
    assert parsed["scientific_status_summary"] == {
        "AUTHENTICATED_EXACT": 8,
        "CONFORMANT_DECLARED_FIXTURE": 2,
        "RETAINED_DATA_CONFORMANT": 4,
        "UNRESOLVED_PROVENANCE_QUARANTINED": 1,
    }
    assert parsed["zero_float_policy_audit"]["status"] == "PASS"
    assert parsed["vectors_verification"]["status"] == "PASS"
    assert parsed["vectors_verification"]["total_vectors"] == 30

    by_id = {sec["sector_id"]: sec for sec in parsed["sectors"]}
    pq = by_id["provenance_quarantine"]
    assert pq["check_outcome"] == "PASS"
    assert pq["scientific_status"] == "UNRESOLVED_PROVENANCE_QUARANTINED"
    assert pq["capability"] == "provenance_guard"

    # Temporal observation stripped absolute output path from canonical bytes
    to_sec = by_id["temporal_observation"]
    assert to_sec["exact_residuals_summary"]["absolute_output_path_stripped"] is True
    assert to_sec["exact_residuals_summary"]["canonical_output_relpath"] == "manual/data/temporal_observation/temporal.json"
    assert str(ROOT) not in raw_text

    # Diagnostics captured raw streams separately outside canonical report
    assert (diag_dir / "temporal_observation.stdout.txt").is_file()
    assert (diag_dir / "native_closure_wave.stdout.txt").is_file()


def test_g2_tier1_propagates_optimize_flag_and_blocks_bytecode(monkeypatch):
    recorded: list[tuple[list[str], dict[str, str]]] = []
    real_run = subprocess.run

    def spy_run(argv, *args, **kwargs):
        recorded.append((list(argv), dict(kwargs.get("env", {}))))
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(tier1_adapters.subprocess, "run", spy_run)
    res = tier1_adapters.run_tier1_sector(SECTOR_MAP["temporal_observation"], ROOT)
    assert res["check_outcome"] == "PASS"
    assert len(recorded) == 1
    argv, env = recorded[0]
    assert "-B" in argv
    assert env.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert argv.count("-O") == sys.flags.optimize

    # Explicitly prove -O propagation in a child python -O run
    probe = (
        "import sys, subprocess\n"
        "from pathlib import Path\n"
        "from manual.engine.registry import SECTOR_MAP\n"
        "from manual.engine.sectors import tier1_adapters\n"
        "seen = []\n"
        "real = subprocess.run\n"
        "def spy(argv, *a, **kw):\n"
        "    seen.append(list(argv))\n"
        "    return real(argv, *a, **kw)\n"
        "tier1_adapters.subprocess.run = spy\n"
        "tier1_adapters.run_tier1_sector(SECTOR_MAP['temporal_observation'], Path('.'))\n"
        "if seen[0].count('-O') != sys.flags.optimize or sys.flags.optimize < 1:\n"
        "    raise SystemExit(9)\n"
    )
    opt_proc = subprocess.run(
        [sys.executable, "-B", "-O", "-c", probe],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert opt_proc.returncode == 0, opt_proc.stderr


def test_g2_temporal_anchor_validator_and_negative_controls(monkeypatch):
    spec = SECTOR_MAP["temporal_anchor"]
    valid_stdout = json.dumps(
        {
            "full_archive_audit": "separate explicit operation",
            "generated_outputs": 6,
            "original_controls": {"A": "-5/29", "B": "-49/151"},
            "scientific_source_members_verified": True,
            "source_unchanged": True,
            "status": "PASS_ANCHOR_REPLAY",
        },
        sort_keys=True,
    ) + "\n"
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda argv, *a, **kw: subprocess.CompletedProcess(argv, 0, stdout=valid_stdout, stderr=""),
    )
    res = tier1_adapters.run_tier1_sector(spec, ROOT)
    assert res["check_outcome"] == "PASS"
    assert res["capability"] == "declared_fixture_replay"
    assert res["scientific_status"] == "AUTHENTICATED_EXACT"
    assert len(res["input_digests"]) == 39
    assert res["verified_counts"] == {
        "generated_outputs": 6,
        "anchor_cases": 4,
        "nested_replay_checks": 33,
        "scientific_source_members": 30,
    }

    bad_controls = json.dumps(
        {
            "full_archive_audit": "separate explicit operation",
            "generated_outputs": 6,
            "original_controls": {"A": "0", "B": "0"},
            "scientific_source_members_verified": True,
            "source_unchanged": True,
            "status": "PASS_ANCHOR_REPLAY",
        },
        sort_keys=True,
    ) + "\n"
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda argv, *a, **kw: subprocess.CompletedProcess(argv, 0, stdout=bad_controls, stderr=""),
    )
    with pytest.raises(ValueError, match="unexpected original_controls"):
        tier1_adapters.run_tier1_sector(spec, ROOT)


def test_g2_importing_engine_never_imports_group_b_or_manual_scripts():
    code = (
        "import sys, manual.engine\n"
        "import manual.engine.cli\n"
        "import manual.engine.sectors.tier1_adapters\n"
        "import manual.engine.sectors.tier2_exact\n"
        "import manual.engine.sectors.tier3_quarantine\n"
        "bad = [m for m in sys.modules if m.startswith(('manual.scripts', 'matplotlib', 'pandas', 'numpy', 'scipy', 'sympy', 'aod_' + 'dec'))]\n"
        "group_b = {'aod_3d_coordinate_phase_delta3', 'aod_brownian_3d_phase_delta3', 'aod_run_tumble_3d_trace',\n"
        "           'generate_cycle_shedding_fixture', 'generate_higgs_trace_figures', 'generate_k4_input_gate_figure',\n"
        "           'score_sparc_field_dynamics'}\n"
        "bad.extend(m for m in sys.modules if m in group_b)\n"
        "if bad: raise SystemExit('FORBIDDEN_LOADED:' + ','.join(sorted(bad)))\n"
    )
    proc = subprocess.run([sys.executable, "-B", *_opt_flags(), "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


# ---------------------------------------------------------------------------
# Gate G3 — Exactness, Typed Public Boundaries & Golden Vectors
# ---------------------------------------------------------------------------


def test_g3_zero_float_policy_audit_passes_on_live_engine():
    audit = audit_source_tree(ROOT / "manual/engine")
    assert audit["status"] == "PASS", audit
    assert audit["violation_count"] == 0
    assert audit["json_files_under_engine"] == 0
    assert audit["audited_python_files"] >= 12


def test_g3_typed_public_validators_reject_invalid_inputs_normal_and_O():
    with pytest.raises(ValueError, match="boom"):
        require(False, "boom")

    assert require_exact_int(0) == 0
    assert require_exact_int(-42) == -42
    for bad_int in (True, False, 0.1, 1.0, 1j, "1", None):
        with pytest.raises(TypeError):
            require_exact_int(bad_int)

    assert parse_exact_int("0") == 0
    assert parse_exact_int("-123") == -123
    assert parse_exact_int("+1", allow_leading_plus=True) == 1
    for bad_type in (True, False, 0.1, 1j, None):
        with pytest.raises(TypeError):
            parse_exact_int(bad_type)
    for bad_str in ("", " 1", "1 ", "+1", "01", "-0", "1.0", "NaN"):
        with pytest.raises(ValueError):
            parse_exact_int(bad_str)

    assert parse_printed_rational("0.45") == Fraction(9, 20)
    assert parse_printed_rational("-14/15") == Fraction(-14, 15)
    assert parse_printed_rational("3.5e-2", allow_exponent=True) == Fraction(7, 200)
    for bad_type in (0.1, 1.0, 1j, True, False, 5, Fraction(1, 2), None):
        with pytest.raises(TypeError):
            parse_printed_rational(bad_type)
    for bad_tok in ("", "NaN", "nan", "Inf", "-inf", "Infinity", "1/0", " 1/2", "1/2 ", "1.2.3", "1e-3"):
        with pytest.raises(ValueError):
            parse_printed_rational(bad_tok)

    assert canonical_rational_pair(0) == ("0", "1")
    assert canonical_rational_pair(Fraction(-4, 6)) == ("-2", "3")
    assert canonical_rational_str(Fraction(4, 2)) == "2"
    assert canonical_rational_str(Fraction(-3, 6)) == "-1/2"
    for bad_q in (True, 0.5, 1j, "1/2"):
        with pytest.raises(TypeError):
            canonical_rational_pair(bad_q)

    assert parse_canonical_rational_pair(["-2", "3"]) == Fraction(-2, 3)
    with pytest.raises(ValueError):
        parse_canonical_rational_pair(["2", "4"])
    with pytest.raises(ValueError):
        parse_canonical_rational_pair(["1", "0"])

    # Exact half-to-even rounding (pure integer arithmetic)
    assert round_rational_half_even(Fraction(5, 2), 0) == Fraction(2)
    assert round_rational_half_even(Fraction(7, 2), 0) == Fraction(4)
    assert round_rational_half_even(Fraction(-14, 15), 6) == Fraction(-933333, 1000000)
    assert format_rational_fixed(Fraction(-14, 15), 6) == "-0.933333"
    assert format_rational_fixed(Fraction(57, 100), 3) == "0.570"
    assert exact_isclose(Fraction(1, 1), Fraction(1, 1) + Fraction(1, 10**13), Fraction(1, 10**12))
    assert not exact_isclose(Fraction(1, 1), Fraction(1, 1) + Fraction(1, 10**6), Fraction(1, 10**12))


def test_g3_golden_vectors_all_30_pass_and_schema_valid_with_or_without_vectors():
    vec_summary = verify_all_vectors(ROOT)
    assert vec_summary["status"] == "PASS", vec_summary
    assert vec_summary["rational_core_count"] == 24
    assert vec_summary["symbolic_and_display_count"] == 6
    assert vec_summary["total_vectors"] == 30
    assert vec_summary["passed_vectors"] == 30
    assert vec_summary["failed_vectors"] == 0

    sec = tier2_exact.run_tier2_sector(SECTOR_MAP["dec_ledger"], ROOT)
    # Report schema passes BOTH without and with vectors_verification
    rep_without = build_report(
        [sec],
        data_coverage_audit={"status": "NOT_REQUESTED"},
        zero_float_policy_audit={"status": "NOT_REQUESTED"},
        vectors_verification=None,
    )
    validate_report(rep_without)
    assert "vectors_verification" not in rep_without

    rep_with = build_report(
        [sec],
        data_coverage_audit={"status": "NOT_REQUESTED"},
        zero_float_policy_audit={"status": "NOT_REQUESTED"},
        vectors_verification=vec_summary,
    )
    validate_report(rep_with)
    assert rep_with["vectors_verification"]["passed_vectors"] == 30

    # Non-circularity and oracle mismatch negative controls
    rc_lines = (ROOT / "manual/engine/vectors/rational_core.jsonl").read_text(encoding="utf-8").splitlines()
    rc24 = loads_zero_float(rc_lines[-1])
    assert isinstance(rc24, dict) and rc24["case_id"] == "RC-024"
    bad_basis = deepcopy(rc24)
    bad_basis["oracle_basis"] = "candidate_snapshot"
    with pytest.raises(ValueError, match="candidate_snapshot"):
        validate_vector_record(bad_basis)

    bad_val = deepcopy(rc24)
    bad_val["expected_outcome"]["exact_value"]["mean_shift"] = ["2", "999999"]
    with pytest.raises(ValueError, match="mismatch"):
        verify_single_vector(bad_val)


# ---------------------------------------------------------------------------
# Gate G4 — Reproducibility & Portability (Normal vs -O, Two Paths)
# ---------------------------------------------------------------------------


def test_g4_canonical_report_byte_identical_normal_vs_O_and_two_paths(tmp_path: Path):
    norm_out = tmp_path / "norm.json"
    opt_out = tmp_path / "opt.json"
    base_args = [
        "--check-zero-float",
        "--verify-vectors",
        "--sector", "temporal_observation",
        "--sector", "dec_ledger",
        "--sector", "higgs_trace",
        "--sector", "phase_delta3_3d",
        "--sector", "cycle_shedding",
        "--sector", "lensing_tallies",
        "--sector", "sparc_five_galaxy",
        "--sector", "provenance_quarantine",
    ]
    p_norm = _run_cli([*base_args, "--report", str(norm_out)], optimize=0)
    p_opt = _run_cli([*base_args, "--report", str(opt_out)], optimize=1)
    assert p_norm.returncode == 0, p_norm.stderr
    assert p_opt.returncode == 0, p_opt.stderr
    norm_bytes = norm_out.read_bytes()
    opt_bytes = opt_out.read_bytes()
    assert norm_bytes == opt_bytes

    # Execute from a second completely different directory path (non-Git copy)
    alt_root = tmp_path / "alt_checkout_location"
    alt_needed = set()
    for sid in ("temporal_observation", "dec_ledger", "higgs_trace", "phase_delta3_3d",
                "cycle_shedding", "lensing_tallies", "sparc_five_galaxy", "provenance_quarantine"):
        alt_needed.update(SECTOR_MAP[sid].input_paths)
    alt_needed.add("contracts/scientific/CANONICAL_BINDINGS.json")
    alt_needed.add("contracts/scientific/MAP_CONTRACT.json")
    alt_needed.add("contracts/scientific/ERROR_BUDGET.json")
    alt_needed.add("manual/__init__.py")
    _copy_files(alt_root, sorted(alt_needed))
    shutil.copytree(ROOT / "manual/engine", alt_root / "manual/engine")

    alt_out = tmp_path / "alt_norm.json"
    p_alt = _run_cli([*base_args, "--report", str(alt_out)], cwd=alt_root, optimize=0)
    assert p_alt.returncode == 0, p_alt.stderr
    assert alt_out.read_bytes() == norm_bytes

    # Negative controls on schema portability & non-conflation
    rep = loads_zero_float(norm_bytes.decode("utf-8"))
    assert isinstance(rep, dict)

    leaked_path = deepcopy(rep)
    leaked_path["sectors"][0]["exact_residuals_summary"]["leaked"] = "/home/user/repo/file.json"
    with pytest.raises(ValueError, match="absolute Unix path"):
        validate_report(leaked_path)

    leaked_ts = deepcopy(rep)
    leaked_ts["sectors"][0]["exact_residuals_summary"]["when"] = "2026-11-23T12:00:00Z"
    with pytest.raises(ValueError, match="timestamp"):
        validate_report(leaked_ts)

    leaked_key = deepcopy(rep)
    leaked_key["sectors"][0]["exact_residuals_summary"]["duration_s"] = 1
    with pytest.raises(ValueError, match="volatile report key"):
        validate_report(leaked_key)

    conflated = deepcopy(rep)
    for sec in conflated["sectors"]:
        if sec["sector_id"] == "provenance_quarantine":
            sec["scientific_status"] = "AUTHENTICATED_EXACT"
    with pytest.raises(ValueError, match="UNRESOLVED_PROVENANCE_QUARANTINED"):
        validate_report(conflated)


# ---------------------------------------------------------------------------
# Gate G5 — Negative Controls & Failure Behavior
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "snippet", "expected_rule"),
    [
        ("bad_float_lit.py", "X = 1.5\n", "float_or_complex_literal"),
        ("bad_complex_lit.py", "X = 1j\n", "float_or_complex_literal"),
        ("bad_float_call.py", "def f(x):\n    return float(x)\n", "forbidden_call"),
        ("bad_complex_call.py", "def f(x):\n    return complex(x, 0)\n", "forbidden_call"),
        ("bad_numpy.py", "import numpy as np\n", "forbidden_import"),
        ("bad_math.py", "import math\n", "forbidden_import"),
        ("bad_decimal.py", "from decimal import Decimal\n", "forbidden_import"),
        ("bad_scripts.py", "import manual.scripts.aod_awareness\n", "forbidden_import"),
        ("bad_sympy.py", "import sympy\n", "forbidden_sympy_import"),
        ("bad_assert.py", "def f(x):\n    assert x > 0\n", "bare_assert"),
        ("bad_exp_mod.py", "import " + "aod_" + "dec\n", "forbidden_import"),
        ("bad_exp_tok.py", "# legacy " + "aod-" + "dec note\n", "forbidden_experimental_token"),
    ],
)
def test_g5_ast_policy_rejects_injected_violations(tmp_path: Path, filename: str, snippet: str, expected_rule: str):
    eng_copy = tmp_path / "engine"
    shutil.copytree(ROOT / "manual/engine", eng_copy, ignore=shutil.ignore_patterns("__pycache__"))
    (eng_copy / filename).write_text(snippet, encoding="utf-8")
    audit = audit_source_tree(eng_copy)
    assert audit["status"] == "FAIL"
    rules = {v["rule"] for v in audit["violations"]}
    assert expected_rule in rules


def test_g5_ast_policy_rejects_json_under_engine_and_exp_token_in_readme(tmp_path: Path):
    eng_copy = tmp_path / "engine"
    shutil.copytree(ROOT / "manual/engine", eng_copy, ignore=shutil.ignore_patterns("__pycache__"))
    (eng_copy / "illegal_schema.json").write_text("{}\n", encoding="utf-8")
    readme = eng_copy / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n" + "aod_" + "dec\n", encoding="utf-8")
    audit = audit_source_tree(eng_copy)
    assert audit["status"] == "FAIL"
    rules = {v["rule"] for v in audit["violations"]}
    assert "forbidden_json_under_manual" in rules
    assert "forbidden_experimental_token" in rules


def test_g5_runtime_payload_guard_rejects_float_and_nonfinite():
    with pytest.raises(TypeError, match="forbidden float"):
        require_no_floats({"nested": [1, {"bad": 0.25}]})
    with pytest.raises(TypeError, match="forbidden complex"):
        require_no_floats({"nested": 1j})
    with pytest.raises(ValueError, match="JSON float"):
        loads_zero_float('{"val": 0.1}')
    with pytest.raises(ValueError, match="JSON float"):
        loads_zero_float('{"val": NaN}')


def test_g5_tier1_nonzero_stderr_empty_and_missing_file_fail_closed(monkeypatch, tmp_path: Path):
    spec = SECTOR_MAP["native_closure_wave"]

    # Nonzero return code
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a[0], 1, stdout="", stderr=""),
    )
    with pytest.raises(ValueError, match="exited with code 1"):
        tier1_adapters.run_tier1_sector(spec, ROOT)

    # Non-empty stderr
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, stdout="{}", stderr="warning"),
    )
    with pytest.raises(ValueError, match="unexpected stderr"):
        tier1_adapters.run_tier1_sector(spec, ROOT)

    # Vacuous empty result set
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(
            a[0], 0, stdout='{"results": [], "passed": 0, "total": 0}', stderr=""
        ),
    )
    with pytest.raises(ValueError, match="expected 83/83"):
        tier1_adapters.run_tier1_sector(spec, ROOT)

    # Missing input file fails closed through CLI (exit 1)
    bad_repo = tmp_path / "missing_repo"
    _copy_files(bad_repo, ["contracts/scientific/CANONICAL_BINDINGS.json"])
    report_out = tmp_path / "fail_report.json"
    rc = engine_main(["--repo-root", str(bad_repo), "--sector", "dec_ledger", "--report", str(report_out)])
    assert rc == 1
    rep = loads_zero_float(report_out.read_text(encoding="utf-8"))
    validate_report(rep)
    assert rep["outcomes_summary"] == {"total_executed": 1, "PASS": 0, "FAIL": 1}


def test_g5_frozen_csv_tamper_rejected(tmp_path: Path):
    spec = SECTOR_MAP["dec_ledger"]
    _copy_files(tmp_path, ["contracts/scientific/CANONICAL_BINDINGS.json", *spec.input_paths])
    target = tmp_path / "manual/data/dec/dec_one_node_ledger_example.csv"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen SHA-256 mismatch"):
        tier2_exact.run_tier2_sector(spec, tmp_path)


def test_g5_cycle_shedding_and_sparc_bound_violations_rejected(tmp_path: Path):
    # 1. Cycle shedding: perturb padar_burden on tick 10 by 1e-6 (> 1e-12 inherited bound)
    cs_root = tmp_path / "cs"
    cs_spec = SECTOR_MAP["cycle_shedding"]
    _copy_files(cs_root, ["contracts/scientific/CANONICAL_BINDINGS.json", *cs_spec.input_paths])
    csv_path = cs_root / "wavelet_shedding_simulation.csv"
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    cells = lines[11].split(",")
    cells[5] = "0.999999"
    lines[11] = ",".join(cells)
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exceeds inherited 1/10\\^12 bound"):
        tier2_exact.run_tier2_sector(cs_spec, cs_root)

    # 2. SPARC: perturb U_AO on row 0 by +1.0 (>= 1e-9 inherited check) and repin temp digest
    sp_root = tmp_path / "sparc"
    sp_spec = SECTOR_MAP["sparc_five_galaxy"]
    _copy_files(sp_root, ["contracts/scientific/CANONICAL_BINDINGS.json", *sp_spec.input_paths])
    bin_rel = "manual/data/derived/sparc_five_galaxy_per_bin.csv"
    bin_path = sp_root / bin_rel
    blines = bin_path.read_text(encoding="utf-8").splitlines()
    bcells = blines[1].split(",")
    bcells[21] = "300.06085"
    blines[1] = ",".join(bcells)
    bin_path.write_text("\n".join(blines) + "\n", encoding="utf-8")
    _repin_temp_bindings(sp_root, bin_rel)
    with pytest.raises(ValueError, match="inherited check"):
        tier2_exact.run_tier2_sector(sp_spec, sp_root)


def test_g5_tau_conflation_control_rejected(tmp_path: Path):
    # Direct unit negative control: conflating summary 1:2:10 with 9/20 fails
    with pytest.raises(ValueError, match="conflation breach"):
        tier3_quarantine.verify_tau_non_conflation(
            Fraction(9, 20),
            [Fraction(9, 20), Fraction(9, 20), Fraction(9, 20)],
        )
    # Direct unit negative control: overwriting diagnostic 1:2:10 with 23/50 fails
    with pytest.raises(ValueError, match="exact 9/20"):
        tier3_quarantine.verify_tau_non_conflation(
            Fraction(23, 50),
            [Fraction(23, 50), Fraction(23, 50), Fraction(23, 50)],
        )
    # Tampering with frozen tau file fails digest guard
    spec = SECTOR_MAP["provenance_quarantine"]
    _copy_files(tmp_path, ["contracts/scientific/CANONICAL_BINDINGS.json", *spec.input_paths])
    diag = tmp_path / "manual/data/derived/tau_ring_diagnostic.csv"
    diag.write_text(diag.read_text(encoding="utf-8").replace(",0.45,", ",0.46,"), encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        tier3_quarantine.run_tier3_sector(spec, tmp_path)


def test_g5_higgs_target_quarantine_breach_rejected(tmp_path: Path):
    spec = SECTOR_MAP["higgs_trace"]
    _copy_files(tmp_path, ["contracts/scientific/CANONICAL_BINDINGS.json", *spec.input_paths])
    rel = "manual/data/higgs/higgs_trace_internal_candidates_selection.csv"
    target = tmp_path / rel
    lines = target.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0] + ",mass_GeV"
    for i in range(1, len(lines)):
        lines[i] = lines[i] + ",125.09"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _repin_temp_bindings(tmp_path, rel)
    with pytest.raises(ValueError, match="target quarantine breach"):
        tier2_exact.run_tier2_sector(spec, tmp_path)


def test_g5_unsafe_report_and_diagnostics_paths_rejected():
    for unsafe in (
        ROOT / "manual/engine/leaked.json",
        ROOT / "manual/leaked.jsonl",
        ROOT / "tests/leaked.json",
        ROOT / "root_leaked.json",
    ):
        with pytest.raises(ValueError, match="distributable repository"):
            validate_runtime_output_path(unsafe, ROOT, flag_name="--report")
        proc = _run_cli(["--check-zero-float", "--report", str(unsafe)])
        assert proc.returncode == 2
        assert not unsafe.exists()

    unsafe_diag = ROOT / "manual/engine/diag_leak"
    proc_d = _run_cli(["--check-zero-float", "--diagnostics-dir", str(unsafe_diag)])
    assert proc_d.returncode == 2
    assert not unsafe_diag.exists()

    # Excluded _build/s2/ is explicitly allowed
    allowed = validate_runtime_output_path(ROOT / "_build/s2/allowed.json", ROOT, flag_name="--report")
    assert allowed == (ROOT / "_build/s2/allowed.json").resolve()


# ---------------------------------------------------------------------------
# Gate G6 — Distribution (Non-Git source.zip Round-Trip Inventory Proof)
# ---------------------------------------------------------------------------


def test_g6_source_zip_extraction_runs_engine_and_preserves_inventory(tmp_path: Path, monkeypatch):
    # Verify zero .json files anywhere under manual/engine/
    assert list((ROOT / "manual/engine").rglob("*.json")) == []

    builder = _load_module("s2_test_release_builder", ROOT / "scripts/build_release_bundle.py")
    ci_test = _load_module("s2_test_ci_release", ROOT / "tests/test_ci_release_builder.py")

    source_dir = builder.build_source_tree(tmp_path / "stage1")
    archive = tmp_path / "source.zip"
    builder.zip_dir(source_dir, archive)

    extracted = tmp_path / "extracted_non_git"
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            dst = extracted / info.filename
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(zf.read(info))
            dst.chmod((info.external_attr >> 16) & 0o777)

    assert not (extracted / ".git").exists()
    inv_before = ci_test.expected_source_inventory(extracted)

    # Run reference engine from the extracted non-Git archive, writing report OUTSIDE source tree
    ext_report = tmp_path / "external_report.json"
    args = [
        "--check-zero-float",
        "--verify-vectors",
        "--report", str(ext_report),
    ]
    for sid in ("native_closure_wave", "temporal_observation", "dec_ledger", "higgs_trace",
                "phase_delta3_3d", "cycle_shedding", "lensing_tallies", "sparc_five_galaxy",
                "provenance_quarantine"):
        args.extend(["--sector", sid])

    proc = _run_cli(args, cwd=extracted)
    assert proc.returncode == 0, proc.stderr
    parsed = loads_zero_float(ext_report.read_text(encoding="utf-8"))
    validate_report(parsed)
    assert parsed["outcomes_summary"] == {"total_executed": 9, "PASS": 9, "FAIL": 0}
    assert parsed["zero_float_policy_audit"]["status"] == "PASS"
    assert parsed["vectors_verification"]["status"] == "PASS"

    # Inventory before == after execution AND repackaging matches identically
    inv_after = ci_test.expected_source_inventory(extracted)
    assert inv_after == inv_before

    monkeypatch.setattr(builder, "ROOT", extracted)
    repacked = builder.build_source_tree(tmp_path / "stage2")
    archive2 = tmp_path / "source2.zip"
    builder.zip_dir(repacked, archive2)
    assert ci_test.archive_inventory(archive2) == inv_before


# ---------------------------------------------------------------------------
# Gate G7 — Preservation & Additive CI Workflow Integration
# ---------------------------------------------------------------------------


def test_g7_build_yml_s2_step_ordering_and_172_frozen_hashes_intact():
    workflow = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
    audit_cmd = "python3 scripts/audit_scientific_sources.py . --build-root latex"
    s2_step = "Verify S2 zero-float reference engine (normal and -O)"
    s2_norm = "python3 -B -m manual.engine --verify-all --check-zero-float --verify-vectors --report _build/s2/engine_norm.json"
    s2_opt = "python3 -B -O -m manual.engine --verify-all --check-zero-float --verify-vectors --report _build/s2/engine_opt.json"
    s2_cmp = "cmp _build/s2/engine_norm.json _build/s2/engine_opt.json"
    pytest_cmd = "pytest -q | tee tests.txt"
    bundle_cmd = "scripts/build_release_bundle.py --outdir dist"

    for snippet in (audit_cmd, s2_step, s2_norm, s2_opt, s2_cmp, pytest_cmd, bundle_cmd):
        assert snippet in workflow
    assert workflow.index(audit_cmd) < workflow.index(s2_step)
    assert workflow.index(s2_step) < workflow.index(pytest_cmd) < workflow.index(bundle_cmd)

    # All 172 pinned frozen_sha256 entries remain byte-identical
    cb = json.loads((ROOT / "contracts/scientific/CANONICAL_BINDINGS.json").read_text(encoding="utf-8"))
    frozen = cb["frozen_sha256"]
    assert len(frozen) == 172
    for rel, expected_sha in frozen.items():
        actual_sha = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"frozen file drifted: {rel}"
