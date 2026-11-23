"""Comprehensive Stage 2 (S2) reference engine test suite covering Gates G1-G7.

Zero bare ``assert`` statements are used in this test module: every check goes
through ``_check(...)`` so ``python3 -B -O -m pytest`` genuinely executes every
assertion rather than silently stripping them.
"""
from __future__ import annotations

import ast
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


def _check(condition: bool, message: object = "") -> None:
    """Non-strippable check helper active identically under normal and ``-O`` Python."""
    if not condition:
        raise AssertionError(str(message) if message else "check failed")


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
    _check(spec is not None and spec.loader is not None, f"failed to load module spec from {path}")
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
    _check(len(SECTOR_SPECS) == 16)
    _check(len(SECTOR_MAP) == 16)
    tiers = [s.tier for s in SECTOR_SPECS]
    _check(tiers.count("tier1_canonical_adapter") == 9)
    _check(tiers.count("tier2_exact_data_verifier") == 6)
    _check(tiers.count("tier3_provenance_guard") == 1)
    d1 = registry_digest()
    d2 = registry_digest()
    _check(len(d1) == 64 and d1 == d2)

    proc = _run_cli(["--list-sectors"])
    _check(proc.returncode == 0, proc.stderr)
    listed = loads_zero_float(proc.stdout)
    _check(isinstance(listed, dict))
    _check(listed["sector_count"] == 16)
    _check(listed["registry_digest"] == d1)


def test_g1_dual_data_coverage_17_subdirs_116_files_plus_root():
    cov = verify_data_coverage(ROOT)
    _check(cov["status"] == "PASS")
    _check(cov["manual_data_subdirs"] == 17)
    _check(cov["manual_data_files"] == 116)
    _check(cov["root_data_files"] == 2)
    _check(cov["uncovered_files"] == 0)
    overlaps = cov["declared_data_overlaps"]
    _check("wavelet_shedding_simulation.csv" in overlaps)
    _check("manual/data/derived/tau_ring_diagnostic.csv" in overlaps)
    _check("manual/data/tau/aod_tau_fractal_ring_summary.csv" in overlaps)
    _check("manual/data/sparc/NGC2403_rotmod.dat" in overlaps)


def test_g1_uncovered_or_missing_manual_data_file_fails_closed(tmp_path: Path):
    shutil.copytree(ROOT / "manual/data", tmp_path / "manual/data")
    _copy_files(tmp_path, ["wavelet_shedding_simulation.csv", "cycle_shedding_summary.tex"])
    _check(verify_data_coverage(tmp_path)["status"] == "PASS")

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
    _check(_run_cli(["--sector", "unknown_sector_xyz"]).returncode == 2)
    _check(_run_cli(["--sector", "dec_ledger", "--sector", "dec_ledger"]).returncode == 2)
    _check(_run_cli(["--verify-all", "--sector", "dec_ledger"]).returncode == 2)
    _check(_run_cli([]).returncode == 2)


# ---------------------------------------------------------------------------
# Gate G2 — Execution, Subprocess Isolation, -O Propagation & Group-B Safety
# ---------------------------------------------------------------------------


def test_g2_15_fast_sectors_execute_with_orthogonal_status_and_diagnostics(tmp_path: Path):
    report_path = tmp_path / "fast15_report.json"
    diag_dir = tmp_path / "diag"
    args = [
        "--check-zero-float",
        "--verify-vectors",
        "--report",
        str(report_path),
        "--diagnostics-dir",
        str(diag_dir),
    ]
    for sid in FAST_15_SECTORS:
        args.extend(["--sector", sid])

    proc = _run_cli(args)
    _check(proc.returncode == 0, proc.stderr)
    raw_text = report_path.read_text(encoding="utf-8")
    parsed = loads_zero_float(raw_text)
    _check(isinstance(parsed, dict))
    validate_report(parsed)

    _check(parsed["schema"] == REPORT_SCHEMA)
    _check(parsed["base_commit_binding"] == BASE_COMMIT_BINDING)
    _check(parsed["outcomes_summary"] == {"total_executed": 15, "PASS": 15, "FAIL": 0})
    _check(
        parsed["scientific_status_summary"]
        == {
            "AUTHENTICATED_EXACT": 8,
            "CONFORMANT_DECLARED_FIXTURE": 2,
            "RETAINED_DATA_CONFORMANT": 4,
            "UNRESOLVED_PROVENANCE_QUARANTINED": 1,
        }
    )
    _check(parsed["zero_float_policy_audit"]["status"] == "PASS")
    _check(parsed["vectors_verification"]["status"] == "PASS")
    _check(parsed["vectors_verification"]["total_vectors"] == 30)

    by_id = {sec["sector_id"]: sec for sec in parsed["sectors"]}
    pq = by_id["provenance_quarantine"]
    _check(pq["check_outcome"] == "PASS")
    _check(pq["scientific_status"] == "UNRESOLVED_PROVENANCE_QUARANTINED")
    _check(pq["capability"] == "provenance_guard")

    # Temporal observation stripped absolute output path from canonical bytes
    to_sec = by_id["temporal_observation"]
    _check(to_sec["exact_residuals_summary"]["absolute_output_path_stripped"] is True)
    _check(
        to_sec["exact_residuals_summary"]["canonical_output_relpath"]
        == "manual/data/temporal_observation/temporal.json"
    )
    _check(str(ROOT) not in raw_text)

    # Diagnostics captured raw streams separately outside canonical report
    _check((diag_dir / "temporal_observation.stdout.txt").is_file())
    _check((diag_dir / "native_closure_wave.stdout.txt").is_file())


def test_g2_tier1_propagates_optimize_flag_and_blocks_bytecode(monkeypatch):
    recorded: list[tuple[list[str], dict[str, str]]] = []
    real_run = subprocess.run

    def spy_run(argv, *args, **kwargs):
        recorded.append((list(argv), dict(kwargs.get("env", {}))))
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(tier1_adapters.subprocess, "run", spy_run)
    res = tier1_adapters.run_tier1_sector(SECTOR_MAP["temporal_observation"], ROOT)
    _check(res["check_outcome"] == "PASS")
    _check(len(recorded) == 1)
    argv, env = recorded[0]
    _check("-B" in argv)
    _check(env.get("PYTHONDONTWRITEBYTECODE") == "1")
    _check(argv.count("-O") == sys.flags.optimize)

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
    _check(opt_proc.returncode == 0, opt_proc.stderr)


def test_g2_temporal_anchor_validator_and_negative_controls(monkeypatch):
    spec = SECTOR_MAP["temporal_anchor"]
    valid_stdout = (
        json.dumps(
            {
                "full_archive_audit": "separate explicit operation",
                "generated_outputs": 6,
                "original_controls": {"A": "-5/29", "B": "-49/151"},
                "scientific_source_members_verified": True,
                "source_unchanged": True,
                "status": "PASS_ANCHOR_REPLAY",
            },
            sort_keys=True,
        )
        + "\n"
    )
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda argv, *a, **kw: subprocess.CompletedProcess(argv, 0, stdout=valid_stdout, stderr=""),
    )
    res = tier1_adapters.run_tier1_sector(spec, ROOT)
    _check(res["check_outcome"] == "PASS")
    _check(res["capability"] == "declared_fixture_replay")
    _check(res["scientific_status"] == "AUTHENTICATED_EXACT")
    _check(len(res["input_digests"]) == 39)
    _check(
        res["verified_counts"]
        == {
            "generated_outputs": 6,
            "anchor_cases": 4,
            "nested_replay_checks": 33,
            "scientific_source_members": 30,
        }
    )

    bad_controls = (
        json.dumps(
            {
                "full_archive_audit": "separate explicit operation",
                "generated_outputs": 6,
                "original_controls": {"A": "0", "B": "0"},
                "scientific_source_members_verified": True,
                "source_unchanged": True,
                "status": "PASS_ANCHOR_REPLAY",
            },
            sort_keys=True,
        )
        + "\n"
    )
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda argv, *a, **kw: subprocess.CompletedProcess(argv, 0, stdout=bad_controls, stderr=""),
    )
    with pytest.raises(ValueError, match="unexpected original_controls"):
        tier1_adapters.run_tier1_sector(spec, ROOT)


def test_g2_temporal_anchor_cross_zlib_decompressed_verifier(monkeypatch, tmp_path: Path):
    import gzip

    # Build a fast, deterministic stub repo matching aod_temporal_anchor.py's contract
    stub_root = tmp_path / "stub_repo"
    scripts_dir = stub_root / "manual/scripts"
    data_dir = stub_root / "manual/data/temporal_anchor"
    cases_dir = data_dir / "cases"
    source_dir = data_dir / "source"
    scripts_dir.mkdir(parents=True)
    cases_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)

    for helper_name in ("aod_native_closure_wave.py", "aod_mapping_error.py", "aod_temporal_observation.py"):
        (scripts_dir / helper_name).write_text("VALUE = 1\n", encoding="utf-8")

    (source_dir / "member.txt").write_text("source_member\n", encoding="utf-8")
    (data_dir / "source_members.json").write_text(
        json.dumps({"members": {"member.txt": {"bytes": 14}}}) + "\n",
        encoding="utf-8",
    )

    inputs_bytes = b'{"schema":"aod.m3.anchor-input.v1"}\n'
    report_bytes = b'{"schema":"aod.m3.anchor-report.v1"}\n'
    case_payload = b'{"case":"baseline","seq":[' + b",".join(str(i).encode() for i in range(500)) + b"]}\n"

    # Persist with compresslevel=1 while stub products() emits compresslevel=9 (different raw DEFLATE bytes!)
    gz_lvl1 = gzip.compress(case_payload, compresslevel=1, mtime=0)
    gz_lvl9 = gzip.compress(case_payload, compresslevel=9, mtime=0)
    _check(gz_lvl1 != gz_lvl9, "test requires distinct gzip bitstreams for same decompressed payload")
    _check(gzip.decompress(gz_lvl1) == gzip.decompress(gz_lvl9) == case_payload)

    (data_dir / "inputs.json").write_bytes(inputs_bytes)
    (data_dir / "report.json").write_bytes(report_bytes)
    (cases_dir / "baseline.json.gz").write_bytes(gz_lvl1)

    stub_script = (
        "import gzip, hashlib, os, sys\n"
        "from pathlib import Path\n"
        "import aod_native_closure_wave as n\n"
        "import aod_mapping_error as m\n"
        "import aod_temporal_observation as t\n"
        "DATA = Path('manual/data/temporal_anchor')\n"
        "def require(cond, msg):\n"
        "    if not cond:\n"
        "        raise ValueError(msg)\n"
        "def sha(p):\n"
        "    return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
        "def products(root):\n"
        "    if os.environ.get('STUB_REQUIRE_OPT') == '1' and sys.flags.optimize < 1:\n"
        "        raise ValueError('optimize flag was not propagated')\n"
        "    if os.environ.get('STUB_MUTATE_BOUND') == '1':\n"
        "        p = Path(root) / DATA / 'source/member.txt'\n"
        "        p.write_text('mutated\\n', encoding='utf-8')\n"
        f"    payload = {case_payload!r}\n"
        "    return {\n"
        f"        'inputs.json': {inputs_bytes!r},\n"
        f"        'report.json': {report_bytes!r},\n"
        "        'cases/baseline.json.gz': gzip.compress(payload, compresslevel=9, mtime=0),\n"
        "    }\n"
    )
    (scripts_dir / "aod_temporal_anchor.py").write_text(stub_script, encoding="utf-8")

    def _run_cross_zlib(*, opt: int, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(extra_env or {})}
        return subprocess.run(
            [
                sys.executable,
                "-B",
                *(["-O"] * opt),
                "-c",
                tier1_adapters._CROSS_ZLIB_ANCHOR_VERIFY_CODE,
                str(stub_root),
            ],
            cwd=stub_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    # (a) Identical decompressed JSON with compresslevel=1 vs 9 PASSES in normal and -O (proving -O propagation)
    p_norm = _run_cross_zlib(opt=0)
    _check(p_norm.returncode == 0 and p_norm.stderr == "", f"rc={p_norm.returncode} stderr={p_norm.stderr}")
    p_opt = _run_cross_zlib(opt=1, extra_env={"STUB_REQUIRE_OPT": "1"})
    _check(p_opt.returncode == 0 and p_opt.stderr == "", f"rc={p_opt.returncode} stderr={p_opt.stderr}")
    _check(p_norm.stdout == p_opt.stdout)
    parsed = loads_zero_float(p_norm.stdout)
    _check(isinstance(parsed, dict) and parsed["status"] == "PASS_ANCHOR_REPLAY")
    _check(parsed["generated_outputs"] == 3)
    _check(parsed["original_controls"] == {"A": "-5/29", "B": "-49/151"})

    # Also verify run_tier1_sector dispatches cross-zlib child argv when _host_zlib_roundtrips_anchor_gz is False
    seen_argv: list[list[str]] = []
    valid_stdout = (
        json.dumps(
            {
                "full_archive_audit": "separate explicit operation",
                "generated_outputs": 6,
                "original_controls": {"A": "-5/29", "B": "-49/151"},
                "scientific_source_members_verified": True,
                "source_unchanged": True,
                "status": "PASS_ANCHOR_REPLAY",
            },
            sort_keys=True,
        )
        + "\n"
    )
    with monkeypatch.context() as mp:
        mp.setattr(tier1_adapters, "_host_zlib_roundtrips_anchor_gz", lambda _r: False)
        mp.setattr(
            tier1_adapters.subprocess,
            "run",
            lambda argv, *a, **kw: (
                seen_argv.append(list(argv)),
                subprocess.CompletedProcess(argv, 0, stdout=valid_stdout, stderr=""),
            )[1],
        )
        dispatched = tier1_adapters.run_tier1_sector(SECTOR_MAP["temporal_anchor"], ROOT)
    _check(dispatched["check_outcome"] == "PASS")
    _check(len(seen_argv) == 1 and "-c" in seen_argv[0] and seen_argv[0].count("-O") == sys.flags.optimize)
    _check(tier1_adapters._CROSS_ZLIB_ANCHOR_VERIFY_CODE in seen_argv[0])

    # (b) 1-byte difference inside decompressed cases/baseline.json.gz FAILS CLOSED
    bad_payload = case_payload[:-2] + b"9\n"
    (cases_dir / "baseline.json.gz").write_bytes(gzip.compress(bad_payload, compresslevel=1, mtime=0))
    p_bad_gz = _run_cross_zlib(opt=sys.flags.optimize)
    _check(p_bad_gz.returncode != 0)
    _check("persisted anchor decompressed payload differs" in p_bad_gz.stderr, p_bad_gz.stderr)
    (cases_dir / "baseline.json.gz").write_bytes(gz_lvl1)

    # (c) 1-byte difference in uncompressed report.json FAILS CLOSED
    (data_dir / "report.json").write_bytes(report_bytes[:-1] + b" \n")
    p_bad_rep = _run_cross_zlib(opt=sys.flags.optimize)
    _check(p_bad_rep.returncode != 0)
    _check("persisted anchor artifact differs" in p_bad_rep.stderr, p_bad_rep.stderr)
    (data_dir / "report.json").write_bytes(report_bytes)

    # (d) Bound-file mutation during replay FAILS CLOSED
    p_mut = _run_cross_zlib(opt=sys.flags.optimize, extra_env={"STUB_MUTATE_BOUND": "1"})
    _check(p_mut.returncode != 0)
    _check("anchor replay changed bound source or data" in p_mut.stderr, p_mut.stderr)


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
    _check(proc.returncode == 0, proc.stderr)


# ---------------------------------------------------------------------------
# Gate G3 — Exactness, Typed Public Boundaries, -O Enforcement & Golden Vectors
# ---------------------------------------------------------------------------


def test_g3_zero_float_policy_audit_passes_on_live_engine_and_zero_bare_asserts_in_tests():
    audit = audit_source_tree(ROOT / "manual/engine")
    _check(audit["status"] == "PASS", audit)
    _check(audit["violation_count"] == 0)
    _check(audit["json_files_under_engine"] == 0)
    _check(audit["audited_python_files"] >= 12)
    _check(audit["audited_jsonl_files"] == 2)

    # Confirm this test module itself has zero bare assert statements so -O never strips checks.
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
    bare_asserts = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    _check(not bare_asserts, f"bare assert lines found in test_s2_reference_engine.py: {bare_asserts}")


def test_g3_typed_public_validators_reject_invalid_inputs_normal_and_O():
    with pytest.raises(ValueError, match="boom"):
        require(False, "boom")

    _check(require_exact_int(0) == 0)
    _check(require_exact_int(-42) == -42)
    for bad_int in (True, False, 0.1, 1.0, 1j, "1", None):
        with pytest.raises(TypeError):
            require_exact_int(bad_int)

    _check(parse_exact_int("0") == 0)
    _check(parse_exact_int("-123") == -123)
    _check(parse_exact_int("+1", allow_leading_plus=True) == 1)
    for bad_type in (True, False, 0.1, 1j, None):
        with pytest.raises(TypeError):
            parse_exact_int(bad_type)
    for bad_str in ("", " 1", "1 ", "+1", "01", "-0", "1.0", "NaN"):
        with pytest.raises(ValueError):
            parse_exact_int(bad_str)

    _check(parse_printed_rational("0.45") == Fraction(9, 20))
    _check(parse_printed_rational("-14/15") == Fraction(-14, 15))
    _check(parse_printed_rational("3.5e-2", allow_exponent=True) == Fraction(7, 200))
    for bad_type in (0.1, 1.0, 1j, True, False, 5, Fraction(1, 2), None):
        with pytest.raises(TypeError):
            parse_printed_rational(bad_type)
    for bad_tok in ("", "NaN", "nan", "Inf", "-inf", "Infinity", "1/0", " 1/2", "1/2 ", "1.2.3", "1e-3"):
        with pytest.raises(ValueError):
            parse_printed_rational(bad_tok)

    _check(canonical_rational_pair(0) == ("0", "1"))
    _check(canonical_rational_pair(Fraction(-4, 6)) == ("-2", "3"))
    _check(canonical_rational_str(Fraction(4, 2)) == "2")
    _check(canonical_rational_str(Fraction(-3, 6)) == "-1/2")
    for bad_q in (True, 0.5, 1j, "1/2"):
        with pytest.raises(TypeError):
            canonical_rational_pair(bad_q)

    _check(parse_canonical_rational_pair(["-2", "3"]) == Fraction(-2, 3))
    with pytest.raises(ValueError):
        parse_canonical_rational_pair(["2", "4"])
    with pytest.raises(ValueError):
        parse_canonical_rational_pair(["1", "0"])

    # Exact half-to-even rounding (pure integer arithmetic)
    _check(round_rational_half_even(Fraction(5, 2), 0) == Fraction(2))
    _check(round_rational_half_even(Fraction(7, 2), 0) == Fraction(4))
    _check(round_rational_half_even(Fraction(-14, 15), 6) == Fraction(-933333, 1000000))
    _check(format_rational_fixed(Fraction(-14, 15), 6) == "-0.933333")
    _check(format_rational_fixed(Fraction(57, 100), 3) == "0.570")
    _check(exact_isclose(Fraction(1, 1), Fraction(1, 1) + Fraction(1, 10**13), Fraction(1, 10**12)))
    _check(not exact_isclose(Fraction(1, 1), Fraction(1, 1) + Fraction(1, 10**6), Fraction(1, 10**12)))


def test_g3_explicit_python_minus_O_subprocess_enforces_validators_and_g5_controls():
    probe = (
        "import sys\n"
        "from fractions import Fraction\n"
        "from manual.engine import (\n"
        "    canonical_rational_pair, exact_isclose, loads_zero_float,\n"
        "    parse_canonical_rational_pair, parse_exact_int, parse_printed_rational,\n"
        "    require, require_exact_int, require_no_floats, round_rational_half_even,\n"
        "    validate_report,\n"
        ")\n"
        "from manual.engine.sectors import tier3_quarantine\n"
        "if sys.flags.optimize < 1:\n"
        "    raise SystemExit('NOT_OPTIMIZED')\n"
        "def must_raise(exc_type, fn, *a, **kw):\n"
        "    try:\n"
        "        fn(*a, **kw)\n"
        "    except exc_type:\n"
        "        return\n"
        "    raise SystemExit(f'MISSED_{exc_type.__name__}:{fn.__name__}')\n"
        "must_raise(ValueError, require, False, 'fail')\n"
        "must_raise(TypeError, require_exact_int, True)\n"
        "must_raise(TypeError, require_exact_int, 0.1)\n"
        "must_raise(TypeError, parse_exact_int, False)\n"
        "must_raise(ValueError, parse_exact_int, '-0')\n"
        "must_raise(TypeError, parse_printed_rational, 0.1)\n"
        "must_raise(ValueError, parse_printed_rational, 'NaN')\n"
        "must_raise(ValueError, parse_printed_rational, '1/0')\n"
        "must_raise(TypeError, canonical_rational_pair, 0.5)\n"
        "must_raise(ValueError, parse_canonical_rational_pair, ['2', '4'])\n"
        "must_raise(ValueError, round_rational_half_even, Fraction(1, 2), -1)\n"
        "must_raise(ValueError, exact_isclose, Fraction(1), Fraction(1), Fraction(-1, 10))\n"
        "must_raise(TypeError, require_no_floats, {'a': [0.25]})\n"
        "must_raise(ValueError, loads_zero_float, '{\"x\": 0.1}')\n"
        "must_raise(ValueError, tier3_quarantine.verify_tau_non_conflation, Fraction(9, 20), [Fraction(9, 20)] * 3)\n"
        "must_raise(ValueError, validate_report, {'bad': True})\n"
    )
    proc = subprocess.run([sys.executable, "-B", "-O", "-c", probe], cwd=ROOT, capture_output=True, text=True)
    _check(proc.returncode == 0, f"stderr={proc.stderr} stdout={proc.stdout}")


def test_g3_golden_vectors_all_30_pass_and_schema_valid_with_or_without_vectors():
    vec_summary = verify_all_vectors(ROOT)
    _check(vec_summary["status"] == "PASS", vec_summary)
    _check(vec_summary["rational_core_count"] == 24)
    _check(vec_summary["symbolic_and_display_count"] == 6)
    _check(vec_summary["total_vectors"] == 30)
    _check(vec_summary["passed_vectors"] == 30)
    _check(vec_summary["failed_vectors"] == 0)

    sec = tier2_exact.run_tier2_sector(SECTOR_MAP["dec_ledger"], ROOT)
    # Report schema passes BOTH without and with vectors_verification
    rep_without = build_report(
        [sec],
        data_coverage_audit={"status": "NOT_REQUESTED"},
        zero_float_policy_audit={"status": "NOT_REQUESTED"},
        vectors_verification=None,
    )
    validate_report(rep_without)
    _check("vectors_verification" not in rep_without)

    rep_with = build_report(
        [sec],
        data_coverage_audit={"status": "NOT_REQUESTED"},
        zero_float_policy_audit={"status": "NOT_REQUESTED"},
        vectors_verification=vec_summary,
    )
    validate_report(rep_with)
    _check(rep_with["vectors_verification"]["passed_vectors"] == 30)

    # Non-circularity, 0-based RC-016 binding, hardened vector checks, and oracle mismatch controls
    rc_lines = (ROOT / "manual/engine/vectors/rational_core.jsonl").read_text(encoding="utf-8").splitlines()
    rc_by_id = {loads_zero_float(line)["case_id"]: loads_zero_float(line) for line in rc_lines if line.strip()}
    _check(rc_by_id["RC-015"]["source_binding"].endswith("#row0"))
    _check(rc_by_id["RC-016"]["source_binding"].endswith("#row78_NGC3198"))

    # Hardened dec_normalize_one_node rejects duplicate/non-binary Q4 neighbors
    bad_rc1 = deepcopy(rc_by_id["RC-001"])
    bad_rc1["inputs"]["rows"][1]["neighbor"] = [1, 0, 0, 0]
    with pytest.raises(ValueError, match="4 distinct Q4 neighbors"):
        verify_single_vector(bad_rc1)

    bad_rc1_neg = deepcopy(rc_by_id["RC-001"])
    bad_rc1_neg["inputs"]["rows"][0]["neighbor"] = [2, -1, 0, 0]
    with pytest.raises(ValueError, match="Q4 basis vector"):
        verify_single_vector(bad_rc1_neg)

    # Hardened temporal_metrology_signed_advance rejects phase >= 1
    bad_rc18 = deepcopy(rc_by_id["RC-018"])
    bad_rc18["inputs"]["compared"]["phase_start"] = ["5", "4"]
    with pytest.raises(ValueError, match="phase out of"):
        verify_single_vector(bad_rc18)

    rc24 = rc_by_id["RC-024"]
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
        "--sector",
        "temporal_observation",
        "--sector",
        "dec_ledger",
        "--sector",
        "higgs_trace",
        "--sector",
        "phase_delta3_3d",
        "--sector",
        "cycle_shedding",
        "--sector",
        "lensing_tallies",
        "--sector",
        "sparc_five_galaxy",
        "--sector",
        "provenance_quarantine",
    ]
    p_norm = _run_cli([*base_args, "--report", str(norm_out)], optimize=0)
    p_opt = _run_cli([*base_args, "--report", str(opt_out)], optimize=1)
    _check(p_norm.returncode == 0, p_norm.stderr)
    _check(p_opt.returncode == 0, p_opt.stderr)
    norm_bytes = norm_out.read_bytes()
    opt_bytes = opt_out.read_bytes()
    _check(norm_bytes == opt_bytes)

    # Execute from a second completely different directory path (non-Git copy)
    alt_root = tmp_path / "alt_checkout_location"
    alt_needed = set()
    for sid in (
        "temporal_observation",
        "dec_ledger",
        "higgs_trace",
        "phase_delta3_3d",
        "cycle_shedding",
        "lensing_tallies",
        "sparc_five_galaxy",
        "provenance_quarantine",
    ):
        alt_needed.update(SECTOR_MAP[sid].input_paths)
    alt_needed.add("contracts/scientific/CANONICAL_BINDINGS.json")
    alt_needed.add("contracts/scientific/MAP_CONTRACT.json")
    alt_needed.add("contracts/scientific/ERROR_BUDGET.json")
    alt_needed.add("manual/__init__.py")
    _copy_files(alt_root, sorted(alt_needed))
    shutil.copytree(ROOT / "manual/engine", alt_root / "manual/engine")

    alt_out = tmp_path / "alt_norm.json"
    p_alt = _run_cli([*base_args, "--report", str(alt_out)], cwd=alt_root, optimize=0)
    _check(p_alt.returncode == 0, p_alt.stderr)
    _check(alt_out.read_bytes() == norm_bytes)

    # Negative controls on schema portability, PASS rollup consistency, & non-conflation
    rep = loads_zero_float(norm_bytes.decode("utf-8"))
    _check(isinstance(rep, dict))

    for bad_path, match_text in (
        ("/home/user/repo/file.json", "absolute Unix path"),
        ("/workspace/aod/file.json", "absolute Unix path"),
        ("failed at /github/workspace/file.py", "absolute Unix path"),
        ("C:\\Users\\aod\\file.json", "absolute Windows path"),
        ("C:/Users/aod/file.json", "absolute Windows path"),
    ):
        leaked = deepcopy(rep)
        leaked["sectors"][0]["exact_residuals_summary"]["leaked"] = bad_path
        with pytest.raises(ValueError, match=match_text):
            validate_report(leaked)

    leaked_tuple = deepcopy(rep)
    leaked_tuple["sectors"][0]["exact_residuals_summary"]["leaked_t"] = ("/app/secret/file",)
    with pytest.raises(ValueError, match="absolute Unix path"):
        validate_report(leaked_tuple)

    leaked_ts = deepcopy(rep)
    leaked_ts["sectors"][0]["exact_residuals_summary"]["when"] = "2026-11-23T12:00:00Z"
    with pytest.raises(ValueError, match="timestamp"):
        validate_report(leaked_ts)

    leaked_key = deepcopy(rep)
    leaked_key["sectors"][0]["exact_residuals_summary"]["duration_s"] = 1
    with pytest.raises(ValueError, match="volatile report key"):
        validate_report(leaked_key)

    bad_zf_pass = deepcopy(rep)
    bad_zf_pass["zero_float_policy_audit"]["violation_count"] = 1
    with pytest.raises(ValueError, match="violation_count == 0"):
        validate_report(bad_zf_pass)

    bad_vec_pass = deepcopy(rep)
    bad_vec_pass["vectors_verification"]["failed_vectors"] = 1
    bad_vec_pass["vectors_verification"]["passed_vectors"] = 29
    with pytest.raises(ValueError, match="failed_vectors == 0"):
        validate_report(bad_vec_pass)

    bad_vec_empty = deepcopy(rep)
    bad_vec_empty["vectors_verification"].update(
        {
            "rational_core_count": 0,
            "symbolic_and_display_count": 0,
            "total_vectors": 0,
            "passed_vectors": 0,
            "failed_vectors": 0,
        }
    )
    with pytest.raises(ValueError, match="total_vectors > 0"):
        validate_report(bad_vec_empty)

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
        ("bad_float_alias.py", "f = float\nX = f('1')\n", "forbidden_reference"),
        ("bad_map_float.py", "def f(xs):\n    return list(map(float, xs))\n", "forbidden_reference"),
        ("bad_dunder_import.py", "m = __import__('math')\n", "forbidden_call"),
        ("bad_compile.py", "c = compile('1', '<x>', 'eval')\n", "forbidden_call"),
        ("bad_dunder_builtins.py", "b = __builtins__\n", "forbidden_reference"),
        ("bad_importlib.py", "import importlib\n", "forbidden_import"),
        ("bad_builtins_import.py", "import builtins\n", "forbidden_import"),
        ("bad_numpy.py", "import numpy as np\n", "forbidden_import"),
        ("bad_math.py", "import math\n", "forbidden_import"),
        ("bad_decimal.py", "from decimal import Decimal\n", "forbidden_import"),
        ("bad_scripts.py", "import manual.scripts.aod_awareness\n", "forbidden_import"),
        ("bad_rel_scripts_1.py", "from .. import scripts\n", "forbidden_import"),
        ("bad_rel_scripts_2.py", "from ..scripts import aod_awareness\n", "forbidden_import"),
        ("bad_sympy.py", "import sympy\n", "forbidden_sympy_import"),
        ("bad_int_div.py", "X = 1 / 2\n", "integer_true_division"),
        ("bad_neg_pow.py", "X = 2 ** -1\n", "negative_integer_exponent"),
        ("bad_aug_div.py", "def f(x):\n    x /= 2\n    return x\n", "integer_true_division"),
        ("bad_aug_pow.py", "def f(x):\n    x **= -1\n    return x\n", "negative_integer_exponent"),
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
    _check(audit["status"] == "FAIL", f"{filename} unexpectedly passed: {audit}")
    rules = {v["rule"] for v in audit["violations"]}
    _check(expected_rule in rules, f"expected {expected_rule} in {rules} for {filename}")


def test_g5_ast_policy_rejects_json_under_engine_and_tokens_in_readme_and_jsonl(tmp_path: Path):
    eng_copy = tmp_path / "engine"
    shutil.copytree(ROOT / "manual/engine", eng_copy, ignore=shutil.ignore_patterns("__pycache__"))
    (eng_copy / "illegal_schema.json").write_text("{}\n", encoding="utf-8")
    readme = eng_copy / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n" + "aod_" + "dec\n", encoding="utf-8")
    bad_jl = eng_copy / "vectors" / "bad_injected.jsonl"
    bad_jl.write_text('{"note": "' + "aod-" + 'dec", "val": 0.5}\n', encoding="utf-8")
    audit = audit_source_tree(eng_copy)
    _check(audit["status"] == "FAIL")
    rules = {v["rule"] for v in audit["violations"]}
    _check("forbidden_json_under_manual" in rules)
    _check("forbidden_experimental_token" in rules)
    _check("forbidden_json_float" in rules)
    jl_violations = [v for v in audit["violations"] if v["file"] == "vectors/bad_injected.jsonl"]
    _check({v["rule"] for v in jl_violations} == {"forbidden_experimental_token", "forbidden_json_float"})


def test_g5_runtime_payload_guard_rejects_float_and_nonfinite():
    with pytest.raises(TypeError, match="forbidden float"):
        require_no_floats({"nested": [1, {"bad": 0.25}]})
    with pytest.raises(TypeError, match="forbidden complex"):
        require_no_floats({"nested": 1j})
    with pytest.raises(ValueError, match="JSON float"):
        loads_zero_float('{"val": 0.1}')
    with pytest.raises(ValueError, match="JSON float"):
        loads_zero_float('{"val": NaN}')


def test_g5_tier1_nonzero_stderr_empty_timeout_mutation_and_missing_file_fail_closed(
    monkeypatch, tmp_path: Path
):
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

    # TimeoutExpired produces clean sanitized FAIL canonical report (exit 1, valid schema, no leaked paths)
    def raise_timeout(argv, *a, **kw):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=1)

    monkeypatch.setattr(tier1_adapters.subprocess, "run", raise_timeout)
    timeout_report = tmp_path / "timeout_report.json"
    rc_to = engine_main(["--sector", "native_closure_wave", "--report", str(timeout_report)])
    _check(rc_to == 1)
    to_raw = timeout_report.read_text(encoding="utf-8")
    to_rep = loads_zero_float(to_raw)
    validate_report(to_rep)
    _check(to_rep["outcomes_summary"] == {"total_executed": 1, "PASS": 0, "FAIL": 1})
    _check(str(ROOT) not in to_raw)
    _check(sys.executable not in to_raw)

    # Bound read-only input mutation during Tier-1 subprocess execution fails closed
    mut_repo = tmp_path / "mut_repo"
    to_spec = SECTOR_MAP["temporal_observation"]
    _copy_files(mut_repo, to_spec.input_paths)
    mut_target = mut_repo / "manual/data/temporal_observation/temporal.json"

    def mutating_run(argv, *a, **kw):
        mut_target.write_text(mut_target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        out_json = json.dumps(
            {
                "status": "reconstructed",
                "output": str(mut_target.resolve()),
                "atomic_prediction": "incomplete",
            }
        )
        return subprocess.CompletedProcess(argv, 0, stdout=out_json, stderr="")

    monkeypatch.setattr(tier1_adapters.subprocess, "run", mutating_run)
    with pytest.raises(ValueError, match="mutated bound read-only inputs"):
        tier1_adapters.run_tier1_sector(to_spec, mut_repo)

    # Missing input file fails closed through CLI (exit 1)
    bad_repo = tmp_path / "missing_repo"
    _copy_files(bad_repo, ["contracts/scientific/CANONICAL_BINDINGS.json"])
    report_out = tmp_path / "fail_report.json"
    rc = engine_main(["--repo-root", str(bad_repo), "--sector", "dec_ledger", "--report", str(report_out)])
    _check(rc == 1)
    rep = loads_zero_float(report_out.read_text(encoding="utf-8"))
    validate_report(rep)
    _check(rep["outcomes_summary"] == {"total_executed": 1, "PASS": 0, "FAIL": 1})


def test_g5_tier1_failure_and_stderr_observability_with_report_flag(
    monkeypatch, capsys, tmp_path: Path
):
    # 1. Non-zero Tier-1 subprocess exit includes sanitized stderr tail in report AND emits FAIL line to stderr
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda argv, *a, **kw: subprocess.CompletedProcess(
            argv,
            2,
            stdout="",
            stderr="Traceback (most recent call last):\nValueError: /home/secret/work/script.py failed with sentinel_err\n",
        ),
    )
    out_rc = tmp_path / "obs_rc_fail.json"
    rc1 = engine_main(["--sector", "native_closure_wave", "--report", str(out_rc)])
    captured1 = capsys.readouterr()
    _check(rc1 == 1)
    raw1 = out_rc.read_text(encoding="utf-8")
    rep1 = loads_zero_float(raw1)
    validate_report(rep1)
    _check(rep1["outcomes_summary"] == {"total_executed": 1, "PASS": 0, "FAIL": 1})
    sec_err1 = rep1["sectors"][0]["error"]
    _check("exited with code 2" in sec_err1 and "sentinel_err" in sec_err1, sec_err1)
    _check("/home/secret/work" not in raw1 and str(ROOT) not in raw1)
    _check("FAIL sector=native_closure_wave:" in captured1.err, captured1.err)
    _check("sentinel_err" in captured1.err, captured1.err)
    _check("/home/secret/work" not in captured1.err and str(ROOT) not in captured1.err)

    # 2. Zero exit with unexpected stderr includes sanitized first stderr line in report AND emits FAIL line to stderr
    monkeypatch.setattr(
        tier1_adapters.subprocess,
        "run",
        lambda argv, *a, **kw: subprocess.CompletedProcess(
            argv,
            0,
            stdout="{}",
            stderr="DeprecationWarning: legacy_warn at /tmp/leak_dir/mod.py\nsecond line\n",
        ),
    )
    out_se = tmp_path / "obs_stderr_fail.json"
    rc2 = engine_main(["--sector", "native_closure_wave", "--report", str(out_se)])
    captured2 = capsys.readouterr()
    _check(rc2 == 1)
    raw2 = out_se.read_text(encoding="utf-8")
    rep2 = loads_zero_float(raw2)
    validate_report(rep2)
    sec_err2 = rep2["sectors"][0]["error"]
    _check("unexpected stderr" in sec_err2 and "legacy_warn" in sec_err2, sec_err2)
    _check("/tmp/leak_dir" not in raw2 and str(ROOT) not in raw2)
    _check("FAIL sector=native_closure_wave:" in captured2.err, captured2.err)
    _check("legacy_warn" in captured2.err, captured2.err)
    _check("/tmp/leak_dir" not in captured2.err and str(ROOT) not in captured2.err)


def test_g5_frozen_csv_tamper_and_parent_symlinks_rejected(tmp_path: Path):
    spec = SECTOR_MAP["dec_ledger"]
    tamper_root = tmp_path / "tamper"
    _copy_files(tamper_root, ["contracts/scientific/CANONICAL_BINDINGS.json", *spec.input_paths])
    target = tamper_root / "manual/data/dec/dec_one_node_ledger_example.csv"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen SHA-256 mismatch"):
        tier2_exact.run_tier2_sector(spec, tamper_root)

    # Tier-2 parent directory symlink fails closed
    t2_sym = tmp_path / "t2_sym"
    real_dec = tmp_path / "outside_dec"
    shutil.copytree(ROOT / "manual/data/dec", real_dec)
    _copy_files(t2_sym, ["contracts/scientific/CANONICAL_BINDINGS.json"])
    (t2_sym / "manual/data").mkdir(parents=True)
    (t2_sym / "manual/data/dec").symlink_to(real_dec)
    with pytest.raises(ValueError, match="symlink parent forbidden"):
        tier2_exact.run_tier2_sector(spec, t2_sym)

    # Tier-3 parent directory symlink fails closed
    t3_sym = tmp_path / "t3_sym"
    t3_spec = SECTOR_MAP["provenance_quarantine"]
    _copy_files(t3_sym, ["contracts/scientific/CANONICAL_BINDINGS.json", *t3_spec.input_paths])
    real_tau = tmp_path / "outside_tau"
    shutil.move(str(t3_sym / "manual/data/tau"), str(real_tau))
    (t3_sym / "manual/data/tau").symlink_to(real_tau)
    with pytest.raises(ValueError, match="symlink parent forbidden"):
        tier3_quarantine.run_tier3_sector(t3_spec, t3_sym)


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


def test_g5_unsafe_report_diagnostics_symlink_traversal_crossroot_and_collisions_rejected(tmp_path: Path):
    for unsafe in (
        ROOT / "manual/engine/leaked.json",
        ROOT / "manual/leaked.jsonl",
        ROOT / "tests/leaked.json",
        ROOT / "root_leaked.json",
        ROOT / "_build/s2/../../manual/engine/dotdot_leaked.json",
    ):
        with pytest.raises(ValueError, match="distributable repository"):
            validate_runtime_output_path(unsafe, ROOT, flag_name="--report")
        proc = _run_cli(["--check-zero-float", "--report", str(unsafe)])
        _check(proc.returncode == 2, f"unsafe report path not rejected: {unsafe}")
        _check(not unsafe.resolve().exists())

    unsafe_diag = ROOT / "manual/engine/diag_leak"
    proc_d = _run_cli(["--check-zero-float", "--diagnostics-dir", str(unsafe_diag)])
    _check(proc_d.returncode == 2)
    _check(not unsafe_diag.exists())

    # Cross-root --repo-root leak into live checkout distributable tree is rejected (exit 2)
    other_repo = tmp_path / "other_repo"
    other_repo.mkdir()
    cross_leak = ROOT / "manual/engine/cross_root_leak.json"
    proc_cross = _run_cli(
        ["--repo-root", str(other_repo), "--check-zero-float", "--report", str(cross_leak)]
    )
    _check(proc_cross.returncode == 2, proc_cross.stderr)
    _check(not cross_leak.exists())

    # Pre-resolution symlink escape inside _build/ (and symlink target file) rejected with exit 2
    outside_dir = tmp_path / "outside_target"
    outside_dir.mkdir()
    (other_repo / "_build").mkdir()
    (other_repo / "_build/escape").symlink_to(outside_dir)
    sym_escape = other_repo / "_build/escape/escaped.json"
    with pytest.raises(ValueError, match="symlink"):
        validate_runtime_output_path(sym_escape, other_repo, flag_name="--report")
    proc_sym = _run_cli(["--repo-root", str(other_repo), "--check-zero-float", "--report", str(sym_escape)])
    _check(proc_sym.returncode == 2, proc_sym.stderr)
    _check(not (outside_dir / "escaped.json").exists())

    (other_repo / "_build/s2").mkdir()
    sym_file = other_repo / "_build/s2/link.json"
    sym_file.symlink_to(outside_dir / "real.json")
    proc_sym_file = _run_cli(
        ["--repo-root", str(other_repo), "--check-zero-float", "--report", str(sym_file)]
    )
    _check(proc_sym_file.returncode == 2, proc_sym_file.stderr)

    # Existing directory passed to --report and existing regular file passed to --diagnostics-dir -> exit 2
    existing_dir = tmp_path / "existing_dir"
    existing_dir.mkdir()
    proc_dir_col = _run_cli(["--check-zero-float", "--report", str(existing_dir)])
    _check(proc_dir_col.returncode == 2, proc_dir_col.stderr)

    existing_file = tmp_path / "existing_file.txt"
    existing_file.write_text("file\n", encoding="utf-8")
    proc_file_col = _run_cli(["--check-zero-float", "--diagnostics-dir", str(existing_file)])
    _check(proc_file_col.returncode == 2, proc_file_col.stderr)

    # Excluded _build/s2/ is explicitly allowed
    allowed = validate_runtime_output_path(ROOT / "_build/s2/allowed.json", ROOT, flag_name="--report")
    _check(allowed == (ROOT / "_build/s2/allowed.json").resolve())


# ---------------------------------------------------------------------------
# Gate G6 — Distribution (Non-Git source.zip Round-Trip Inventory Proof)
# ---------------------------------------------------------------------------


def test_g6_source_zip_extraction_runs_all_fast_15_and_coverage_preserves_inventory(
    tmp_path: Path, monkeypatch
):
    # Verify zero .json files anywhere under manual/engine/
    _check(list((ROOT / "manual/engine").rglob("*.json")) == [])

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

    _check(not (extracted / ".git").exists())
    inv_before = ci_test.expected_source_inventory(extracted)

    # Verify complete 17-subdir / 116-file + root data coverage on extracted non-Git archive
    ext_cov = verify_data_coverage(extracted)
    _check(ext_cov["status"] == "PASS")
    _check(ext_cov["manual_data_subdirs"] == 17)
    _check(ext_cov["manual_data_files"] == 116)
    _check(ext_cov["uncovered_files"] == 0)

    # Run all 15 fast sectors + AST audit + 30 golden vectors from extracted non-Git archive
    ext_report = tmp_path / "external_report.json"
    args = [
        "--check-zero-float",
        "--verify-vectors",
        "--report",
        str(ext_report),
    ]
    for sid in FAST_15_SECTORS:
        args.extend(["--sector", sid])

    proc = _run_cli(args, cwd=extracted)
    _check(proc.returncode == 0, proc.stderr)
    parsed = loads_zero_float(ext_report.read_text(encoding="utf-8"))
    validate_report(parsed)
    _check(parsed["outcomes_summary"] == {"total_executed": 15, "PASS": 15, "FAIL": 0})
    _check(
        parsed["scientific_status_summary"]
        == {
            "AUTHENTICATED_EXACT": 8,
            "CONFORMANT_DECLARED_FIXTURE": 2,
            "RETAINED_DATA_CONFORMANT": 4,
            "UNRESOLVED_PROVENANCE_QUARANTINED": 1,
        }
    )
    _check(parsed["zero_float_policy_audit"]["status"] == "PASS")
    _check(parsed["vectors_verification"]["status"] == "PASS")

    # Inventory before == after execution AND repackaging matches identically
    inv_after = ci_test.expected_source_inventory(extracted)
    _check(inv_after == inv_before)

    monkeypatch.setattr(builder, "ROOT", extracted)
    repacked = builder.build_source_tree(tmp_path / "stage2")
    archive2 = tmp_path / "source2.zip"
    builder.zip_dir(repacked, archive2)
    _check(ci_test.archive_inventory(archive2) == inv_before)


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
        _check(snippet in workflow, f"missing workflow snippet: {snippet}")
    _check(workflow.index(audit_cmd) < workflow.index(s2_step))
    _check(workflow.index(s2_step) < workflow.index(pytest_cmd) < workflow.index(bundle_cmd))

    # All 172 pinned frozen_sha256 entries remain byte-identical
    cb = loads_zero_float((ROOT / "contracts/scientific/CANONICAL_BINDINGS.json").read_text(encoding="utf-8"))
    _check(isinstance(cb, dict))
    frozen = cb["frozen_sha256"]
    _check(len(frozen) == 172)
    for rel, expected_sha in frozen.items():
        actual_sha = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        _check(actual_sha == expected_sha, f"frozen file drifted: {rel}")
