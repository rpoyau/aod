"""Comprehensive Stage 4 (S4) cross-language parity, policy, and packaging test suite.

Zero bare ``assert`` statements are used anywhere in this module: every check goes
through ``_check(...)`` so ``python3 -B -m pytest`` and ``python3 -B -O -m pytest``
execute identical verification logic.
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
import shutil
import subprocess
import sys
import tomllib
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from manual.engine.numeric import (
    canonical_rational_pair,
    exact_isclose,
    format_rational_fixed,
    parse_printed_rational,
)
from manual.engine.policy import loads_zero_float, require_no_floats
from manual.engine.vectors import (
    RATIONAL_CORE_REL,
    SYMBOLIC_DISPLAY_REL,
    _eval_operation,
    _verify_sympy_z4_dft,
    load_vector_file,
    verify_all_vectors,
)

CRATE_DIR = ROOT / "crates" / "aod-core"
RUST_REPORT_SCHEMA = "aod.s4.rust.report.v1"
FORBIDDEN_EXP_TOKEN_RE = re.compile(r"aod[-_]" + r"dec", re.IGNORECASE)
FORBIDDEN_FLOAT_TYPES = frozenset({"f16", "f32", "f64", "f128"})
FORBIDDEN_VOLATILE_KEYS = frozenset(
    {
        "timestamp",
        "created_at",
        "started_at",
        "finished_at",
        "duration",
        "duration_s",
        "elapsed",
        "elapsed_s",
        "wall_clock",
        "pid",
        "hostname",
        "executable",
        "stdout",
        "stderr",
        "temp_dir",
        "rustc_version",
        "target_triple",
        "profile",
        "debug",
        "build_mode",
    }
)
_ISO_TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_ABS_UNIX_RE = re.compile(
    r"(?:^/|(?<=[\s'\"(=:\[{,])/(?:(?:home|tmp|var|Users|root|opt|usr|etc|private|mnt|srv|proc|sys|workspace|github|app|runner|builds)(?:/|$)|[A-Za-z0-9._-]+/[A-Za-z0-9._-]+))"
)
_ABS_WIN_RE = re.compile(r"(?:^|[\s'\"(=:\[{,])[A-Za-z]:[\\/]")
_TEMP_MARKER_RE = re.compile(r"(?:pytest-of-|aod-anchor-scientific-replay-|/tmp/|\\Temp\\)")


def _check(condition: bool, message: object = "") -> None:
    """Non-strippable check helper identical under normal and ``-O`` Python."""
    if not condition:
        raise AssertionError(str(message) if message else "check failed")


def _rust_available() -> bool:
    return shutil.which("cargo") is not None and shutil.which("rustc") is not None


def _require_or_skip_rust() -> None:
    if not _rust_available():
        if os.environ.get("AOD_REQUIRE_RUST", "").strip() in {"1", "true", "TRUE", "yes"}:
            _check(False, "AOD_REQUIRE_RUST=1 set, but cargo/rustc are unavailable")
        pytest.skip("optional Rust toolchain (cargo/rustc) not installed")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_crate_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for entry in sorted(src.iterdir(), key=lambda p: p.name):
        if entry.name == "target":
            continue
        target = dst / entry.name
        if entry.is_dir():
            _copy_crate_tree(entry, target)
        elif entry.is_file():
            shutil.copy2(entry, target)


def _check_portable_json(value: object, *, path: str = "$") -> None:
    require_no_floats(value, path=path)
    if isinstance(value, dict):
        for k, v in value.items():
            _check(isinstance(k, str), f"non-string key at {path}")
            _check(k not in FORBIDDEN_VOLATILE_KEYS, f"volatile key {k!r} at {path}")
            _check_portable_json(k, path=f"{path}.<key:{k}>")
            _check_portable_json(v, path=f"{path}.{k}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _check_portable_json(item, path=f"{path}[{idx}]")
    elif isinstance(value, str):
        _check(_ISO_TS_RE.search(value) is None, f"timestamp leaked at {path}: {value!r}")
        _check(_ABS_UNIX_RE.search(value) is None, f"unix path leaked at {path}: {value!r}")
        _check(_ABS_WIN_RE.search(value) is None, f"win path leaked at {path}: {value!r}")
        _check(_TEMP_MARKER_RE.search(value) is None, f"temp marker leaked at {path}: {value!r}")


# ---------------------------------------------------------------------------
# Independent Python Rust-lexer & TOML/Cargo.lock policy mirror (no Rust needed)
# ---------------------------------------------------------------------------


def _py_lex_rust(src: str) -> tuple[list[tuple[str, str, int]], list[tuple[int, str]]]:
    """Independent Python Rust lexer returning (tokens, lex_errors)."""
    tokens: list[tuple[str, str, int]] = []
    errors: list[tuple[int, str]] = []
    n = len(src)
    pos = 0
    line = 1
    prev_can_tuple_index = False
    prev_is_tuple_dot = False

    def is_id_start(c: str) -> bool:
        return c.isascii() and (c.isalpha() or c == "_")

    def is_id_cont(c: str) -> bool:
        return c.isascii() and (c.isalnum() or c == "_")

    while pos < n:
        ch = src[pos]
        if ch in " \t\r\n":
            if ch == "\n":
                line += 1
            pos += 1
            continue

        # Line comment
        if src.startswith("//", pos):
            pos += 2
            while pos < n and src[pos] != "\n":
                pos += 1
            continue

        # Nested block comment
        if src.startswith("/*", pos):
            start_line = line
            pos += 2
            depth = 1
            while pos < n and depth > 0:
                if src[pos] == "\n":
                    line += 1
                    pos += 1
                elif src.startswith("/*", pos):
                    depth += 1
                    pos += 2
                elif src.startswith("*/", pos):
                    depth -= 1
                    pos += 2
                else:
                    pos += 1
            if depth != 0:
                errors.append((start_line, "unterminated block comment"))
            continue

        # Raw strings r#"..."#, br#"..."#, cr#"..."#
        raw_prefix = 0
        if ch == "r":
            raw_prefix = 1
        elif ch in ("b", "c") and pos + 1 < n and src[pos + 1] == "r":
            raw_prefix = 2
        if raw_prefix > 0:
            scan = pos + raw_prefix
            hashes = 0
            while scan < n and src[scan] == "#":
                hashes += 1
                scan += 1
            if scan < n and src[scan] == '"':
                start_line = line
                pos = scan + 1
                closing = '"' + ("#" * hashes)
                end_idx = src.find(closing, pos)
                if end_idx == -1:
                    errors.append((start_line, "unterminated raw string"))
                    break
                line += src[pos:end_idx].count("\n")
                pos = end_idx + len(closing)
                prev_can_tuple_index = False
                prev_is_tuple_dot = False
                continue

        # Raw identifier r#ident
        if ch == "r" and pos + 2 < n and src[pos + 1] == "#" and is_id_start(src[pos + 2]):
            tok_line = line
            pos += 2
            start = pos
            while pos < n and is_id_cont(src[pos]):
                pos += 1
            tokens.append(("RAW_IDENT", src[start:pos], tok_line))
            prev_can_tuple_index = True
            prev_is_tuple_dot = False
            continue

        # String / byte string / C string
        if ch == '"' or (ch in ("b", "c") and pos + 1 < n and src[pos + 1] == '"'):
            start_line = line
            if ch != '"':
                pos += 1
            pos += 1
            closed = False
            while pos < n:
                c = src[pos]
                if c == "\\":
                    if pos + 1 < n:
                        if src[pos + 1] == "\n":
                            line += 1
                        pos += 2
                    else:
                        pos += 1
                elif c == '"':
                    pos += 1
                    closed = True
                    break
                else:
                    if c == "\n":
                        line += 1
                    pos += 1
            if not closed:
                errors.append((start_line, "unterminated string literal"))
            prev_can_tuple_index = False
            prev_is_tuple_dot = False
            continue

        # Byte char literal b'...'
        if ch == "b" and pos + 1 < n and src[pos + 1] == "'":
            pos += 2
            while pos < n:
                if src[pos] == "\\":
                    pos = min(pos + 2, n)
                elif src[pos] == "'":
                    pos += 1
                    break
                else:
                    if src[pos] == "\n":
                        line += 1
                    pos += 1
            prev_can_tuple_index = False
            prev_is_tuple_dot = False
            continue

        # Char literal vs lifetime
        if ch == "'":
            if pos + 1 < n and src[pos + 1] == "\\":
                scan = pos + 2
                if scan < n:
                    scan += 1
                while scan < n and src[scan] not in ("'", "\n"):
                    scan += 1
                if scan < n and src[scan] == "'":
                    pos = scan + 1
                else:
                    pos += 1
            elif pos + 2 < n and src[pos + 1] not in ("'", "\n") and src[pos + 2] == "'":
                pos += 3
            else:
                pos += 1
                if pos < n and is_id_start(src[pos]):
                    while pos < n and is_id_cont(src[pos]):
                        pos += 1
            prev_can_tuple_index = False
            prev_is_tuple_dot = False
            continue

        # Identifier
        if is_id_start(ch):
            tok_line = line
            start = pos
            while pos < n and is_id_cont(src[pos]):
                pos += 1
            tokens.append(("IDENT", src[start:pos], tok_line))
            prev_can_tuple_index = True
            prev_is_tuple_dot = False
            continue

        # Numeric literal or tuple index
        if ch.isascii() and ch.isdigit():
            tok_line = line
            if prev_is_tuple_dot:
                start = pos
                while pos < n and src[pos].isascii() and src[pos].isdigit():
                    pos += 1
                if pos < n and src[pos] in "eEfF_":
                    pos = start
                else:
                    tokens.append(("TUPLE_IDX", src[start:pos], tok_line))
                    prev_can_tuple_index = True
                    prev_is_tuple_dot = False
                    continue

            start = pos
            if ch == "0" and pos + 1 < n and src[pos + 1] in "xXbBoO":
                radix = src[pos + 1].lower()
                pos += 2
                valid = "0123456789abcdefABCDEF_" if radix == "x" else ("01_" if radix == "b" else "01234567_")
                while pos < n and src[pos] in valid:
                    pos += 1
                suf_start = pos
                while pos < n and is_id_cont(src[pos]):
                    pos += 1
                suf = src[suf_start:pos].lstrip("_")
                kind = "FLOAT" if suf in FORBIDDEN_FLOAT_TYPES else "INT"
                tokens.append((kind, src[start:pos], tok_line))
            else:
                while pos < n and (src[pos] == "_" or (src[pos].isascii() and src[pos].isdigit())):
                    pos += 1
                is_float = False
                if pos < n and src[pos] == ".":
                    nxt = src[pos + 1] if pos + 1 < n else ""
                    if nxt == ".":
                        pass
                    elif nxt and is_id_start(nxt):
                        pass
                    elif nxt and nxt.isascii() and nxt.isdigit():
                        is_float = True
                        pos += 1
                        while pos < n and (src[pos] == "_" or (src[pos].isascii() and src[pos].isdigit())):
                            pos += 1
                    else:
                        is_float = True
                        pos += 1
                if pos < n and src[pos] in "eE":
                    is_float = True
                    pos += 1
                    if pos < n and src[pos] in "+-":
                        pos += 1
                    while pos < n and (src[pos] == "_" or (src[pos].isascii() and src[pos].isdigit())):
                        pos += 1
                suf_start = pos
                while pos < n and is_id_cont(src[pos]):
                    pos += 1
                suf = src[suf_start:pos].lstrip("_")
                if suf in FORBIDDEN_FLOAT_TYPES:
                    is_float = True
                tokens.append(("FLOAT" if is_float else "INT", src[start:pos], tok_line))
            prev_can_tuple_index = False
            prev_is_tuple_dot = False
            continue

        # Punctuation
        tok_line = line
        if src.startswith("..", pos):
            tokens.append(("DOTDOT", "..", tok_line))
            pos += 2
            prev_can_tuple_index = False
            prev_is_tuple_dot = False
        elif ch == ".":
            tokens.append(("DOT", ".", tok_line))
            pos += 1
            prev_is_tuple_dot = prev_can_tuple_index
            prev_can_tuple_index = False
        elif ch in "#![]()":
            tokens.append(("PUNCT", ch, tok_line))
            pos += 1
            prev_can_tuple_index = ch in ("]", ")")
            prev_is_tuple_dot = False
        else:
            tokens.append(("OTHER", ch, tok_line))
            pos += 1
            prev_can_tuple_index = False
            prev_is_tuple_dot = False

    return tokens, errors


def _py_has_leading_forbid_unsafe_code(tokens: list[tuple[str, str, int]]) -> bool:
    """Require `#![forbid(unsafe_code)]` strictly as a leading crate-level inner attribute."""
    target_seq = [
        ("PUNCT", "#"),
        ("PUNCT", "!"),
        ("PUNCT", "["),
        ("IDENT", "forbid"),
        ("PUNCT", "("),
        ("IDENT", "unsafe_code"),
        ("PUNCT", ")"),
        ("PUNCT", "]"),
    ]
    idx = 0
    n = len(tokens)
    while (
        idx + 2 < n
        and (tokens[idx][0], tokens[idx][1]) == ("PUNCT", "#")
        and (tokens[idx + 1][0], tokens[idx + 1][1]) == ("PUNCT", "!")
        and (tokens[idx + 2][0], tokens[idx + 2][1]) == ("PUNCT", "[")
    ):
        depth = 1
        scan = idx + 3
        while scan < n and depth > 0:
            if (tokens[scan][0], tokens[scan][1]) == ("PUNCT", "["):
                depth += 1
            elif (tokens[scan][0], tokens[scan][1]) == ("PUNCT", "]"):
                depth -= 1
            scan += 1
        if depth != 0:
            return False
        if [(k, v) for k, v, _ in tokens[idx:scan]] == target_seq:
            return True
        idx = scan
    return False


def _py_audit_cargo_toml_obj(rel: str, obj: object, path: tuple[str, ...], violations: list[dict[str, object]]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            sub_path = (*path, k)
            if k in {"patch", "replace", "workspace"}:
                violations.append({"file": rel, "line": 1, "rule": "forbidden_cargo_toml_section"})
            elif k in {"dependencies", "dev-dependencies", "build-dependencies"}:
                if not isinstance(v, dict) or len(v) > 0:
                    violations.append({"file": rel, "line": 1, "rule": "forbidden_dependency"})
            elif sub_path == ("package", "build") and v is not False:
                violations.append({"file": rel, "line": 1, "rule": "forbidden_build_script"})
            _py_audit_cargo_toml_obj(rel, v, sub_path, violations)
    elif isinstance(obj, list):
        for item in obj:
            _py_audit_cargo_toml_obj(rel, item, path, violations)


def _py_audit_crate_tree(crate_root: Path) -> list[dict[str, object]]:
    """Independent Python mirror of crates/aod-core/src/policy.rs using stdlib tomllib."""
    violations: list[dict[str, object]] = []
    if crate_root.is_symlink():
        violations.append({"file": ".", "line": 0, "rule": "forbidden_symlink"})
        return violations
    if not crate_root.is_dir():
        violations.append({"file": ".", "line": 0, "rule": "missing_crate_root"})
        return violations

    files: list[tuple[str, Path]] = []

    def walk(cur: Path, prefix: str) -> None:
        for entry in sorted(cur.iterdir(), key=lambda p: p.name):
            rel = f"{prefix}/{entry.name}" if prefix else entry.name
            if entry.is_symlink():
                violations.append({"file": rel, "line": 0, "rule": "forbidden_symlink"})
                continue
            if entry.is_dir():
                if not prefix and entry.name == "target":
                    continue
                walk(entry, rel)
            elif entry.is_file():
                files.append((rel, entry))

    walk(crate_root, "")

    seen_required = {"Cargo.toml": False, "Cargo.lock": False, "src/lib.rs": False, "src/main.rs": False}

    for rel, path in files:
        if rel in seen_required:
            seen_required[rel] = True
        if rel.endswith(".json"):
            violations.append({"file": rel, "line": 0, "rule": "forbidden_json_under_crate"})
            continue
        if rel == "build.rs" or rel.endswith("/build.rs"):
            violations.append({"file": rel, "line": 0, "rule": "forbidden_build_script"})

        text = path.read_text(encoding="utf-8")
        for lineno, raw_line in enumerate(text.splitlines(), start=1):
            if FORBIDDEN_EXP_TOKEN_RE.search(raw_line):
                violations.append({"file": rel, "line": lineno, "rule": "forbidden_experimental_token"})

        if rel == "Cargo.toml":
            try:
                doc = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                violations.append({"file": rel, "line": 1, "rule": "toml_parse_error"})
            else:
                _py_audit_cargo_toml_obj(rel, doc, (), violations)

        elif rel == "Cargo.lock":
            try:
                lock_doc = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                violations.append({"file": rel, "line": 1, "rule": "toml_parse_error"})
            else:
                extra_top = set(lock_doc.keys()) - {"version", "package"}
                if extra_top:
                    violations.append({"file": rel, "line": 1, "rule": "forbidden_lockfile_section"})
                pkgs = lock_doc.get("package")
                if not isinstance(pkgs, list) or len(pkgs) != 1 or not isinstance(pkgs[0], dict):
                    violations.append({"file": rel, "line": 1, "rule": "forbidden_lockfile_packages"})
                else:
                    pkg0 = pkgs[0]
                    if pkg0.get("name") != "aod-core":
                        violations.append({"file": rel, "line": 1, "rule": "forbidden_lockfile_package"})
                    for bad_key in ("dependencies", "source", "checksum"):
                        if bad_key in pkg0:
                            violations.append({"file": rel, "line": 1, "rule": "forbidden_lockfile_field"})
                    extra_pkg_keys = set(pkg0.keys()) - {"name", "version"}
                    if extra_pkg_keys:
                        violations.append({"file": rel, "line": 1, "rule": "forbidden_lockfile_field"})

        elif rel.endswith(".rs"):
            tokens, lex_errs = _py_lex_rust(text)
            for ln, _ in lex_errs:
                violations.append({"file": rel, "line": ln, "rule": "lex_error"})
            for kind, val, ln in tokens:
                if kind in ("IDENT", "RAW_IDENT"):
                    if val in FORBIDDEN_FLOAT_TYPES:
                        violations.append({"file": rel, "line": ln, "rule": "forbidden_float_type"})
                    elif val == "unsafe":
                        violations.append({"file": rel, "line": ln, "rule": "forbidden_unsafe"})
                    elif val == "extern":
                        violations.append({"file": rel, "line": ln, "rule": "forbidden_extern"})
                elif kind == "FLOAT":
                    violations.append({"file": rel, "line": ln, "rule": "forbidden_float_literal"})

            if rel in {"src/lib.rs", "src/main.rs"} or (rel.startswith("tests/") and rel.endswith(".rs")):
                if not _py_has_leading_forbid_unsafe_code(tokens):
                    violations.append({"file": rel, "line": 1, "rule": "missing_forbid_unsafe_code"})

    for req_file, present in seen_required.items():
        if not present:
            violations.append({"file": req_file, "line": 0, "rule": "missing_required_file"})

    return violations


# ---------------------------------------------------------------------------
# Session-scoped compiled debug + release Rust binaries (outside repo tree)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def rust_binaries(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    _require_or_skip_rust()
    target_dir = tmp_path_factory.mktemp("s4_cargo_target")
    lock_path = CRATE_DIR / "Cargo.lock"
    lock_before = _sha256_file(lock_path)
    env = {**os.environ, "CARGO_TARGET_DIR": str(target_dir)}

    for extra in ([], ["--release"]):
        proc = subprocess.run(
            [
                "cargo",
                "build",
                "--manifest-path",
                str(CRATE_DIR / "Cargo.toml"),
                "--offline",
                "--locked",
                *extra,
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        _check(proc.returncode == 0, f"cargo build {extra} failed:\n{proc.stderr}")

    _check(_sha256_file(lock_path) == lock_before, "Cargo.lock mutated during cargo build")
    _check(not (CRATE_DIR / "target").exists(), "crates/aod-core/target must never be created")
    return {
        "debug": target_dir / "debug" / "aod-core",
        "release": target_dir / "release" / "aod-core",
        "target_dir": target_dir,
    }


def _run_eval_op(bin_path: Path, op: str, inputs: dict[str, object], *, via_stdin: bool = True) -> dict[str, object]:
    payload = json.dumps(inputs, sort_keys=True)
    if via_stdin:
        proc = subprocess.run(
            [str(bin_path), "--eval-op", op, "--input-stdin"],
            input=payload,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    else:
        proc = subprocess.run(
            [str(bin_path), "--eval-op", op, "--input-json", payload],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    _check(proc.returncode == 0, f"--eval-op {op} failed (rc={proc.returncode}): {proc.stderr}")
    parsed = loads_zero_float(proc.stdout)
    require_no_floats(parsed, path=f"rust.{op}")
    _check(isinstance(parsed, dict), f"--eval-op {op} did not return a JSON object")
    return parsed


# ---------------------------------------------------------------------------
# Category 1: Hygiene, zero bare asserts, independent Python policy mirror
# ---------------------------------------------------------------------------


def test_s4_test_module_has_zero_bare_asserts_and_no_exp_tokens():
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(Path(__file__).name))
    assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    _check(len(assert_nodes) == 0, f"bare assert nodes forbidden in S4 tests: {len(assert_nodes)}")
    _check(FORBIDDEN_EXP_TOKEN_RE.search(src) is None, "forbidden experimental token in S4 test file")


def test_python_policy_mirror_passes_live_crate_without_rust():
    _check(CRATE_DIR.is_dir(), "crates/aod-core directory missing")
    _check(not (CRATE_DIR / "target").exists(), "crates/aod-core/target must not exist in source tree")
    violations = _py_audit_crate_tree(CRATE_DIR)
    _check(violations == [], f"Python policy mirror detected crate violations: {violations}")


def test_python_engine_is_completely_independent_of_rust():
    engine_dir = ROOT / "manual" / "engine"
    forbidden_refs = ("aod-core", "aod_core", "crates/aod-core", "cargo", "rustc")
    for py_file in sorted(engine_dir.rglob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        for token in forbidden_refs:
            _check(
                token not in text,
                f"manual/engine must remain 100% independent of Rust; found {token!r} in {py_file.name}",
            )


# ---------------------------------------------------------------------------
# Category 2: Offline/locked debug + release cargo test & Cargo.lock hygiene
# ---------------------------------------------------------------------------


def test_cargo_test_offline_locked_debug_and_release(rust_binaries: dict[str, Path]):
    lock_path = CRATE_DIR / "Cargo.lock"
    lock_before = _sha256_file(lock_path)
    env = {**os.environ, "CARGO_TARGET_DIR": str(rust_binaries["target_dir"])}

    for extra in ([], ["--release"]):
        proc = subprocess.run(
            [
                "cargo",
                "test",
                "--manifest-path",
                str(CRATE_DIR / "Cargo.toml"),
                "--offline",
                "--locked",
                *extra,
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        _check(proc.returncode == 0, f"cargo test {extra} failed:\n{proc.stdout}\n{proc.stderr}")

    _check(_sha256_file(lock_path) == lock_before, "Cargo.lock mutated during cargo test")
    _check(not (CRATE_DIR / "target").exists(), "crates/aod-core/target must never exist")


# ---------------------------------------------------------------------------
# Category 3: CLI byte-identical determinism & canonical report validation
# ---------------------------------------------------------------------------


def test_cli_debug_vs_release_byte_identical_report(rust_binaries: dict[str, Path], tmp_path: Path):
    rep_dbg = tmp_path / "debug_report.json"
    rep_rel = tmp_path / "release_report.json"
    for mode, out_path in (("debug", rep_dbg), ("release", rep_rel)):
        proc = subprocess.run(
            [
                str(rust_binaries[mode]),
                "--verify-vectors",
                "--check-zero-float",
                "--repo-root",
                str(ROOT),
                "--report",
                str(out_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        _check(proc.returncode == 0, f"{mode} CLI failed: {proc.stderr}")

    dbg_bytes = rep_dbg.read_bytes()
    rel_bytes = rep_rel.read_bytes()
    _check(dbg_bytes == rel_bytes, "debug and release canonical reports differ")
    _check(dbg_bytes.endswith(b"\n") and b"\r" not in dbg_bytes, "report must use LF line endings")

    parsed = loads_zero_float(dbg_bytes.decode("utf-8"))
    _check(isinstance(parsed, dict))
    _check_portable_json(parsed)
    _check(parsed["schema"] == RUST_REPORT_SCHEMA)
    _check(parsed["crate_name"] == "aod-core")
    _check(parsed["crate_version"] == "0.1.0")
    _check(parsed["overall_status"] == "PASS")

    vv = parsed["vectors_verification"]
    _check(isinstance(vv, dict))
    _check(vv["status"] == "PASS")
    _check(vv["rational_core_count"] == 24)
    _check(vv["symbolic_and_display_count"] == 6)
    _check(vv["total_vectors"] == 30)
    _check(vv["passed_vectors"] == 30)
    _check(vv["failed_vectors"] == 0)
    _check(vv["failures"] == [])

    py_vv = verify_all_vectors(ROOT)
    _check(vv["file_digests"] == py_vv["file_digests"], "Rust/Python vector SHA-256 digests differ")

    pa = parsed["policy_audit"]
    _check(isinstance(pa, dict))
    _check(pa["status"] == "PASS")
    _check(pa["violation_count"] == 0)
    _check(pa["violations"] == [])
    _check(pa["json_files_under_crate"] == 0)
    _check(pa["cargo_lock_packages"] == 1)

    # CLI utility flags and usage error exit code 2
    _check(subprocess.run([str(rust_binaries["debug"]), "--help"], capture_output=True).returncode == 0)
    _check(subprocess.run([str(rust_binaries["debug"]), "--version"], capture_output=True).returncode == 0)
    _check(subprocess.run([str(rust_binaries["debug"])], capture_output=True).returncode == 2)
    _check(subprocess.run([str(rust_binaries["debug"]), "--unknown-flag"], capture_output=True).returncode == 2)
    _check(
        subprocess.run(
            [str(rust_binaries["debug"]), "--verify-vectors", "--eval-op", "closure_wave_rd_rcd", "--input-json", "{}"],
            capture_output=True,
        ).returncode
        == 2
    )
    _check(
        subprocess.run(
            [str(rust_binaries["debug"]), "--eval-op", "closure_wave_rd_rcd"],
            capture_output=True,
        ).returncode
        == 2
    )


# ---------------------------------------------------------------------------
# Category 4: Direct --eval-op differential parity (27 golden + synthetic)
# ---------------------------------------------------------------------------


def test_differential_parity_all_27_positive_golden_vectors(rust_binaries: dict[str, Path]):
    _, rc_rows = load_vector_file(ROOT / RATIONAL_CORE_REL)
    _, sd_rows = load_vector_file(ROOT / SYMBOLIC_DISPLAY_REL)
    positive_count = 0

    for rec in (*rc_rows, *sd_rows):
        exp = rec["expected_outcome"]
        if exp["status"] != "OK":
            continue
        positive_count += 1
        op = str(rec["operation"])
        inputs = rec["inputs"]
        _check(isinstance(inputs, dict))

        py_out = _eval_operation(op, inputs)
        rust_out_dbg = _run_eval_op(rust_binaries["debug"], op, inputs, via_stdin=(positive_count % 2 == 0))
        rust_out_rel = _run_eval_op(rust_binaries["release"], op, inputs, via_stdin=True)

        _check(rust_out_dbg == py_out, f"{rec['case_id']} ({op}) debug mismatch vs Python")
        _check(rust_out_rel == py_out, f"{rec['case_id']} ({op}) release mismatch vs Python")
        _check(rust_out_dbg == exp["exact_value"], f"{rec['case_id']} ({op}) mismatch vs expected_value")

    _check(positive_count == 27, f"expected 27 positive golden vectors, ran {positive_count}")


def test_differential_beyond_i128_synthetic_vectors(rust_binaries: dict[str, Path]):
    big1 = "9" * 105
    big2 = "1" + "0" * 104
    scale40 = str(10**40)
    synthetic_cases = [
        (
            "temporal_metrology_hellwig_mean",
            {"table_iv_hz": [big1, "1"], "table_vi_hz": [big2, "1"]},
        ),
        (
            "closure_wave_rd_rcd",
            {"p": 120, "q": 3, "hinges": 1, "reflection_counts": [10**50, 7], "window": 10**60},
        ),
        (
            "relational_cadence_and_lag",
            {
                "na": 10**60 + 7,
                "nb": 10**60 + 3,
                "bias": [["1", str(10**50)], ["-1", str(10**50)]],
                "prior_lag": ["3", str(10**45)],
            },
        ),
        (
            "map21_nonlinear_finite_law_variance",
            {
                "support": [
                    {"p": ["1", "2"], "y": ["-1", scale40], "d": ["-1", scale40]},
                    {"p": ["1", "2"], "y": ["1", scale40], "d": ["1", scale40]},
                ]
            },
        ),
    ]
    for op, inputs in synthetic_cases:
        py_out = _eval_operation(op, inputs)
        rust_out = _run_eval_op(rust_binaries["release"], op, inputs)
        _check(rust_out == py_out, f"beyond-i128 differential mismatch on {op}")


def test_differential_90_tick_exact_cycle_shedding(rust_binaries: dict[str, Path]):
    csv_path = ROOT / "wavelet_shedding_simulation.csv"
    eta = Fraction(41, 50)
    gamma = Fraction(11, 20)
    lam = Fraction(19, 50)
    tol = Fraction(1, 10**12)

    tick_payloads: list[dict[str, str]] = []
    py_ticks_expected: list[dict[str, list[str]]] = []
    prev_exact = Fraction(0)
    max_span = Fraction(0)
    max_burden = Fraction(0)
    max_excess = Fraction(0)
    total_outward = Fraction(0)
    total_local = Fraction(0)

    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    _check(len(rows) == 90, f"expected 90 shedding rows, got {len(rows)}")

    for row in rows:
        lead = parse_printed_rational(row["lead"], allow_fraction_slash=False)
        lag = parse_printed_rational(row["lag"], allow_fraction_slash=False)
        comp = parse_printed_rational(row["compatibility"], allow_fraction_slash=False)
        tick_payloads.append({"lead": row["lead"], "lag": row["lag"], "compatibility": row["compatibility"]})

        span = abs(lead - lag)
        before = eta * prev_exact + gamma * span
        exc = max(Fraction(0), before - comp)
        bur = before - exc
        out_s = (Fraction(1) - lam) * exc
        loc_s = lam * exc
        prev_exact = bur

        if span > max_span:
            max_span = span
        if bur > max_burden:
            max_burden = bur
        if exc > max_excess:
            max_excess = exc
        total_outward += out_s
        total_local += loc_s

        # Verify chained exact rational stays close to retained CSV floats
        rec_bur = parse_printed_rational(row["padar_burden"], allow_fraction_slash=False)
        _check(exact_isclose(bur, rec_bur, tol), f"tick {row['tick']} exact burden diverged from CSV")

        py_ticks_expected.append(
            {
                "span": list(canonical_rational_pair(span)),
                "before_clipping": list(canonical_rational_pair(before)),
                "shed_excess": list(canonical_rational_pair(exc)),
                "padar_burden": list(canonical_rational_pair(bur)),
                "outward_shedding": list(canonical_rational_pair(out_s)),
                "local_reclosure": list(canonical_rational_pair(loc_s)),
                "remainder_sum": list(canonical_rational_pair(out_s + loc_s)),
            }
        )

    rust_trace = _run_eval_op(
        rust_binaries["release"],
        "cycle_shedding_trace",
        {
            "initial_burden": ["0", "1"],
            "eta": ["41", "50"],
            "gamma": ["11", "20"],
            "lambda_reclose": ["19", "50"],
            "ticks": tick_payloads,
        },
    )
    _check(rust_trace["ticks"] == py_ticks_expected, "90-tick exact cycle shedding trace mismatch vs Python Fraction")
    _check(rust_trace["final_burden"] == list(canonical_rational_pair(prev_exact)))
    _check(rust_trace["max_span"] == list(canonical_rational_pair(max_span)))
    _check(rust_trace["max_burden"] == list(canonical_rational_pair(max_burden)))
    _check(rust_trace["max_excess"] == list(canonical_rational_pair(max_excess)))
    _check(rust_trace["total_outward"] == list(canonical_rational_pair(total_outward)))
    _check(rust_trace["total_local"] == list(canonical_rational_pair(total_local)))

    # Confirm denominators grew far beyond i128 (~38 digits)
    max_den_len = max(len(t["padar_burden"][1]) for t in rust_trace["ticks"])
    _check(max_den_len > 40, f"expected >40-digit chained denominators, got {max_den_len}")


def test_differential_rounding_sparc_enclosures_sympy_z4_and_z12(rust_binaries: dict[str, Path]):
    bin_rel = rust_binaries["release"]

    # 1. Banker's rounding half-to-even ties & negative-zero prevention
    rounding_cases = [
        {"mass_GeV": "10.0", "sigma_GeV": "2.0", "prediction_GeV": "11.0", "decimals": 0},   # +0.5 -> 0
        {"mass_GeV": "10.0", "sigma_GeV": "2.0", "prediction_GeV": "13.0", "decimals": 0},   # +1.5 -> 2
        {"mass_GeV": "10.0", "sigma_GeV": "2.0", "prediction_GeV": "9.0", "decimals": 0},    # -0.5 -> 0 (not -0)
        {"mass_GeV": "10.0", "sigma_GeV": "2.0", "prediction_GeV": "7.0", "decimals": 0},    # -1.5 -> -2
        {"mass_GeV": "100.0", "sigma_GeV": "10000000.0", "prediction_GeV": "99.9", "decimals": 6},  # tiny negative -> 0.000000
    ]
    for inp in rounding_cases:
        py_out = _eval_operation("higgs_lhc_rounded_display", inp)
        rust_out = _run_eval_op(bin_rel, "higgs_lhc_rounded_display", inp)
        _check(rust_out == py_out, f"rounding mismatch on {inp}: {rust_out} != {py_out}")
        z_str = str(rust_out["z_score_rounded_6dp"])
        _check(re.fullmatch(r"-0(?:\.0+)?", z_str) is None, f"negative zero emitted: {z_str!r}")

    # 2. Negative SPARC Vgas/Vdisk/Vbul
    sparc_cases = [
        {"R": "1.93", "Vobs": "76.9", "errV": "10.3", "Vgas": "-0.05", "Vdisk": "83.17", "Vbul": "0.0"},
        {"R": "4.25", "Vobs": "112.4", "errV": "5.2", "Vgas": "-12.34", "Vdisk": "-45.67", "Vbul": "-8.9"},
    ]
    for inp in sparc_cases:
        _check(_run_eval_op(bin_rel, "sparc_exact_bin_eval", inp) == _eval_operation("sparc_exact_bin_eval", inp))

    # 3. Half-ULP enclosures
    for tok in ("0.0001234", "-12.500", "0.0", "125.040000"):
        inp = {"printed_token": tok}
        _check(
            _run_eval_op(bin_rel, "printed_token_half_ulp_enclosure", inp)
            == _eval_operation("printed_token_half_ulp_enclosure", inp)
        )

    # 4. Live SymPy Z4 DFT formatting parity across 10 diverse Gaussian rational combinations
    z4_cases = [
        ["1", "0", "-1", "0"],
        ["0", "1", "0", "-1"],
        ["1", "2", "3", "4"],
        ["1/2", "-3/4", "5/6", "-7/8"],
        ["-1", "-2", "-3", "-5"],
        ["1", "1", "0", "0"],
        ["0", "0", "0", "0"],
        ["1/3", "2/3", "-1/3", "0"],
        ["-5/7", "0", "5/7", "0"],
        ["0", "-3/5", "0", "3/5"],
    ]
    for vals in z4_cases:
        inp = {"values": vals}
        sympy_out = _verify_sympy_z4_dft(inp)
        rust_out = _run_eval_op(bin_rel, "sympy_z4_dft", inp)
        _check(rust_out == sympy_out, f"SymPy Z4 parity mismatch for {vals}: {rust_out} != {sympy_out}")

    # 5. Z12 cyclotomic variants
    z12_cases = [
        {"group_order": 12, "pulses": [0, 4, 8], "l_min": 4, "overtone_mode": 3},
        {"group_order": 12, "pulses": [0, 6], "l_min": 2, "overtone_mode": 2},
        {"group_order": 12, "pulses": [0, 3, 6, 9], "l_min": 3, "overtone_mode": 4},
        {"group_order": 12, "pulses": [0, 2, 4, 6, 8, 10], "l_min": 2, "overtone_mode": 0},
    ]
    for inp in z12_cases:
        _check(
            _run_eval_op(bin_rel, "cyclotomic_z12_overtone", inp)
            == _eval_operation("cyclotomic_z12_overtone", inp)
        )


# ---------------------------------------------------------------------------
# Category 5: Negative controls (JSON, vectors, --report safety, 11 policy probes)
# ---------------------------------------------------------------------------


def test_negative_controls_json_and_typed_boundaries(rust_binaries: dict[str, Path]):
    bin_dbg = rust_binaries["debug"]
    bad_payloads = [
        ("closure_wave_rd_rcd", '{"p": 0.1, "q": 3, "hinges": 1, "reflection_counts": [], "window": 10}'),
        ("closure_wave_rd_rcd", '{"p": 1e2, "q": 3, "hinges": 1, "reflection_counts": [], "window": 10}'),
        ("closure_wave_rd_rcd", '{"p": NaN, "q": 3, "hinges": 1, "reflection_counts": [], "window": 10}'),
        ("q4_hamming_and_neighbors", '{"vertex": true, "target": 1, "width": 4}'),
        ("printed_token_half_ulp_enclosure", '{"printed_token": "NaN"}'),
        ("printed_token_half_ulp_enclosure", '{"printed_token": "1/0"}'),
        ("printed_token_half_ulp_enclosure", '{"printed_token": " 0.5"}'),
        ("closure_wave_rd_rcd", '{"p": 3, "p": 4, "q": 3, "hinges": 1, "reflection_counts": [], "window": 10}'),
        ("closure_wave_rd_rcd", '{"p": 3} trailing'),
        ("closure_wave_rd_rcd", "[" * 65 + "]" * 65),
        ("closure_wave_rd_rcd", "[1, 2, 3]"),
    ]
    for op, raw in bad_payloads:
        proc = subprocess.run(
            [str(bin_dbg), "--eval-op", op, "--input-json", raw],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        _check(proc.returncode == 1, f"expected exit 1 for bad payload {raw!r}, got {proc.returncode}")


def test_negative_controls_tampered_vectors_and_sanitized_fail_report(
    rust_binaries: dict[str, Path], tmp_path: Path
):
    bin_dbg = rust_binaries["debug"]
    fake_repo = tmp_path / "fake_repo"
    vec_dir = fake_repo / "manual" / "engine" / "vectors"
    vec_dir.mkdir(parents=True)
    shutil.copy2(ROOT / RATIONAL_CORE_REL, vec_dir / "rational_core.jsonl")
    shutil.copy2(ROOT / SYMBOLIC_DISPLAY_REL, vec_dir / "symbolic_and_display.jsonl")

    # Tamper RC-001 expected Z from 8 to 9
    rc_path = vec_dir / "rational_core.jsonl"
    orig_lines = rc_path.read_text(encoding="utf-8").splitlines()
    tampered_0 = json.loads(orig_lines[0])
    tampered_0["expected_outcome"]["exact_value"]["Z"] = 9
    rc_path.write_text("\n".join([json.dumps(tampered_0), *orig_lines[1:]]) + "\n", encoding="utf-8")

    fail_report = tmp_path / "tampered_fail.json"
    proc = subprocess.run(
        [str(bin_dbg), "--verify-vectors", "--repo-root", str(fake_repo), "--report", str(fail_report)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    _check(proc.returncode == 1, f"expected exit 1 on tampered vector, got {proc.returncode}")
    parsed = loads_zero_float(fail_report.read_text(encoding="utf-8"))
    _check_portable_json(parsed)
    _check(parsed["overall_status"] == "FAIL")
    _check(parsed["vectors_verification"]["failed_vectors"] == 1)

    # Inject circular oracle_basis = candidate_snapshot -> loader rejects cleanly with sanitized report
    bad_basis = json.loads(orig_lines[0])
    bad_basis["oracle_basis"] = "candidate_snapshot"
    rc_path.write_text("\n".join([json.dumps(bad_basis), *orig_lines[1:]]) + "\n", encoding="utf-8")
    basis_report = tmp_path / "basis_fail.json"
    proc2 = subprocess.run(
        [str(bin_dbg), "--verify-vectors", "--repo-root", str(fake_repo), "--report", str(basis_report)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    _check(proc2.returncode == 1)
    parsed2 = loads_zero_float(basis_report.read_text(encoding="utf-8"))
    _check_portable_json(parsed2)
    _check(parsed2["overall_status"] == "FAIL")

    # Symlinked JSONL rejected cleanly
    real_rc = tmp_path / "real_rc.jsonl"
    shutil.copy2(ROOT / RATIONAL_CORE_REL, real_rc)
    rc_path.unlink()
    rc_path.symlink_to(real_rc)
    sym_report = tmp_path / "sym_fail.json"
    proc3 = subprocess.run(
        [str(bin_dbg), "--verify-vectors", "--repo-root", str(fake_repo), "--report", str(sym_report)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    _check(proc3.returncode == 1)
    _check_portable_json(loads_zero_float(sym_report.read_text(encoding="utf-8")))


def test_negative_controls_unsafe_report_paths_and_pre_resolution_symlinks(
    rust_binaries: dict[str, Path], tmp_path: Path
):
    bin_dbg = rust_binaries["debug"]
    fake_repo = tmp_path / "repo"
    (fake_repo / "manual" / "engine" / "vectors").mkdir(parents=True)
    shutil.copy2(ROOT / RATIONAL_CORE_REL, fake_repo / RATIONAL_CORE_REL)
    shutil.copy2(ROOT / SYMBOLIC_DISPLAY_REL, fake_repo / SYMBOLIC_DISPLAY_REL)
    (fake_repo / "_build").mkdir()
    outside = tmp_path / "outside_escape"
    outside.mkdir()
    # Pre-resolution symlink inside _build/ escaping outside repo!
    (fake_repo / "_build" / "escape").symlink_to(outside)
    # Direct symlink report target outside repo + trailing `/.` and `/` bypass probes
    direct_sym = tmp_path / "sym_target.json"
    real_sym_dest = outside / "real.json"
    direct_sym.symlink_to(real_sym_dest)
    sub_norm = tmp_path / "sub_norm"
    sub_norm.mkdir()
    # Existing directory collision
    existing_dir = tmp_path / "a_dir"
    existing_dir.mkdir()
    # Regular file used as parent
    file_parent = tmp_path / "file_parent"
    file_parent.write_text("x", encoding="utf-8")

    unsafe_targets = [
        str(fake_repo / "report.json"),
        str(fake_repo / "manual" / "report.json"),
        str(fake_repo / "crates" / "aod-core" / "report.json"),
        str(fake_repo / "typst" / "report.json"),
        str(fake_repo / "_build"),
        str(fake_repo / "_build" / "escape" / "report.json"),
        str(fake_repo / "_build" / ".." / "manual" / "report.json"),
        str(direct_sym),
        f"{direct_sym}/.",
        f"{direct_sym}/",
        f"{sub_norm}/../sym_target.json",
        str(existing_dir),
        f"{existing_dir}/",
        str(file_parent / "report.json"),
    ]
    for target in unsafe_targets:
        proc = subprocess.run(
            [str(bin_dbg), "--verify-vectors", "--repo-root", str(fake_repo), "--report", target],
            cwd=fake_repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
        _check(proc.returncode == 2, f"expected exit 2 for unsafe --report {target!r}, got {proc.returncode}")
    _check(not (outside / "report.json").exists(), "pre-resolution symlink escape wrote outside repo")
    _check(not real_sym_dest.exists(), "direct or trailing-dot symlink target was touched")
    _check(not (fake_repo / "crates").exists(), "unsafe --report created parent directory before validation")

    # Safe path under _build/sub/report.json MUST succeed!
    safe_in_repo = fake_repo / "_build" / "s4" / "ok_report.json"
    ok = subprocess.run(
        [str(bin_dbg), "--verify-vectors", "--repo-root", str(fake_repo), "--report", str(safe_in_repo)],
        cwd=fake_repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    _check(ok.returncode == 0, f"safe _build/s4 report failed: {ok.stderr}")
    _check(safe_in_repo.is_file())


def test_negative_controls_11_adversarial_policy_probes_and_false_positive_immunity(
    rust_binaries: dict[str, Path], tmp_path: Path
):
    bin_dbg = rust_binaries["debug"]

    def run_both_audits(crate_copy: Path) -> tuple[int, dict[str, object], list[dict[str, object]]]:
        proc = subprocess.run(
            [str(bin_dbg), "--check-zero-float", "--crate-root", str(crate_copy)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        rust_rep = loads_zero_float(proc.stdout)
        _check(isinstance(rust_rep, dict))
        _check_portable_json(rust_rep)
        py_viols = _py_audit_crate_tree(crate_copy)
        return proc.returncode, rust_rep, py_viols

    exp_tok = "aod" + "-" + "dec"

    def make_probe(name: str, mutate) -> None:
        copy_dir = tmp_path / f"probe_{name}"
        _copy_crate_tree(CRATE_DIR, copy_dir)
        mutate(copy_dir)
        rc, rust_rep, py_viols = run_both_audits(copy_dir)
        _check(rc == 1, f"Rust policy failed to reject probe {name}")
        _check(rust_rep["policy_audit"]["status"] == "FAIL", f"Rust policy status != FAIL on {name}")
        _check(len(py_viols) > 0, f"Python policy mirror failed to reject probe {name}")

    # 11 distinct adversarial mutation probes
    make_probe("01_float_type_f64", lambda d: (d / "src/p.rs").write_text("pub fn p(x: f64) {}\n"))
    make_probe("02_raw_ident_f32", lambda d: (d / "src/p.rs").write_text("pub fn p() { let r#f32 = 1; }\n"))
    make_probe("03_float_lit_decimal", lambda d: (d / "src/p.rs").write_text("pub fn p() { let _x = 0.5; }\n"))
    make_probe("04_float_lit_exp_suffix", lambda d: (d / "src/p.rs").write_text("pub fn p() { let _x = 1e5; let _y = 1_f64; }\n"))
    make_probe(
        "05_lifetime_then_float",
        lambda d: (d / "src/p.rs").write_text("pub fn p<'a>(s: &'a str) { let _x: f64 = 1.0; let _ = s; }\n"),
    )
    make_probe("06_unsafe_block", lambda d: (d / "src/p.rs").write_text("pub fn p() { unsafe {} }\n"))
    make_probe("07_extern_block", lambda d: (d / "src/p.rs").write_text('extern "C" { fn foo(); }\n'))
    make_probe(
        "08_commented_forbid_unsafe",
        lambda d: (d / "src/lib.rs").write_text(
            (d / "src/lib.rs").read_text().replace("#![forbid(unsafe_code)]", "// #![forbid(unsafe_code)]")
        ),
    )
    make_probe(
        "09_cargo_toml_dep",
        lambda d: (d / "Cargo.toml").write_text((d / "Cargo.toml").read_text() + '\nserde = "1.0"\n'),
    )
    make_probe(
        "10_cargo_lock_extra_pkg",
        lambda d: (d / "Cargo.lock").write_text(
            (d / "Cargo.lock").read_text() + '\n[[package]]\nname = "evil"\nversion = "0.1.0"\nsource = "registry"\n'
        ),
    )
    make_probe(
        "11_json_symlink_exp_token",
        lambda d: (
            (d / "stray.json").write_text("{}\n"),
            (d / "src/p.rs").write_text(f"// {exp_tok}\n"),
            (d / "src/sym.rs").symlink_to(d / "src/lib.rs"),
        ),
    )

    # Additional TOML 1.0 / Cargo.lock / build.rs / non-crate-root forbid / symlinked crate_root probes
    make_probe(
        "12_toml_target_inline_dep",
        lambda d: (d / "Cargo.toml").write_text(
            (d / "Cargo.toml").read_text() + '\n[target.\'cfg(unix)\']\ndependencies = { serde = "1.0" }\n'
        ),
    )
    make_probe(
        "13_toml_top_level_dotted_dep",
        lambda d: (d / "Cargo.toml").write_text(
            'dependencies.serde = "1.0"\n' + (d / "Cargo.toml").read_text()
        ),
    )
    make_probe(
        "14_toml_quoted_dependencies_header",
        lambda d: (d / "Cargo.toml").write_text(
            (d / "Cargo.toml").read_text().replace("[dependencies]", '["dependencies"]\nserde = "1.0"')
        ),
    )
    make_probe(
        "15_toml_spaced_target_dep_header",
        lambda d: (d / "Cargo.toml").write_text(
            (d / "Cargo.toml").read_text() + "\n[target . 'cfg(unix)' . dependencies]\nserde = \"1.0\"\n"
        ),
    )
    make_probe(
        "16_toml_inline_workspace",
        lambda d: (d / "Cargo.toml").write_text(
            'workspace = { members = ["."] }\n' + (d / "Cargo.toml").read_text()
        ),
    )
    make_probe(
        "17_cargo_lock_patch_unused",
        lambda d: (d / "Cargo.lock").write_text(
            (d / "Cargo.lock").read_text() + '\n[[patch.unused]]\nname = "evil"\nversion = "0.1.0"\n'
        ),
    )
    make_probe(
        "18_cargo_lock_quoted_dependencies",
        lambda d: (d / "Cargo.lock").write_text(
            (d / "Cargo.lock").read_text() + '"dependencies" = ["foo"]\n'
        ),
    )
    make_probe(
        "19_forbidden_build_rs",
        lambda d: (d / "build.rs").write_text("fn main() {}\n"),
    )
    make_probe(
        "20_mod_decoy_forbid_unsafe",
        lambda d: (d / "src/lib.rs").write_text(
            (d / "src/lib.rs")
            .read_text()
            .replace("#![forbid(unsafe_code)]", "mod decoy { #![forbid(unsafe_code)] }")
        ),
    )

    # Symlinked crate_root itself must be rejected cleanly by both Rust CLI and Python mirror
    sym_crate_root = tmp_path / "symlinked_crate_root"
    sym_crate_root.symlink_to(CRATE_DIR)
    rc_sym, rep_sym, py_sym = run_both_audits(sym_crate_root)
    _check(rc_sym == 1, "Rust policy failed to reject symlinked crate_root")
    _check(rep_sym["policy_audit"]["status"] == "FAIL")
    _check(len(py_sym) > 0, "Python mirror failed to reject symlinked crate_root")

    # False-positive immunity check
    benign_dir = tmp_path / "benign_immunity"
    _copy_crate_tree(CRATE_DIR, benign_dir)
    (benign_dir / "src/benign.rs").write_text(
        '//! f64 1.0 unsafe extern\n'
        '/* nested /* f32 0.5 unsafe */ comment 1e5 */\n'
        "pub fn benign<'a>(s: &'a str, t: ((u32, u32), u32)) -> &'a str {\n"
        '    let _s1 = "f64 1.0 unsafe extern";\n'
        '    let _s2 = r#"f32 0.5 "unsafe" extern"#;\n'
        "    let _c1 = 'a';\n"
        "    let _c2 = '\\'';\n"
        "    let _hex = 0x1e5 + 0x1f32;\n"
        "    let _r1 = 0..10;\n"
        "    let _r2 = 0..=10;\n"
        "    let _pow = 10u32.pow(2);\n"
        "    let _p0 = t.0;\n"
        "    let _p01 = t.0.1;\n"
        "    let _p1 = t.1;\n"
        "    s\n"
        "}\n",
        encoding="utf-8",
    )
    rc, rust_rep, py_viols = run_both_audits(benign_dir)
    _check(rc == 0, f"Rust policy false positive on benign module: {rust_rep}")
    _check(rust_rep["policy_audit"]["status"] == "PASS")
    _check(py_viols == [], f"Python mirror false positive on benign module: {py_viols}")


# ---------------------------------------------------------------------------
# Category 6: Non-Git source.zip round-trip & cross-checkout byte-identical report
# ---------------------------------------------------------------------------


def test_source_zip_roundtrip_offline_cargo_and_byte_identical_report(
    rust_binaries: dict[str, Path], tmp_path: Path
):
    spec = importlib.util.spec_from_file_location("s4_rel_builder", ROOT / "scripts/build_release_bundle.py")
    _check(spec is not None and spec.loader is not None)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    stage = builder.build_source_tree(tmp_path / "stage")
    archive = tmp_path / "source.zip"
    builder.zip_dir(stage, archive)

    extracted = tmp_path / "extracted_no_git"
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = extracted / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(info))
            target.chmod((info.external_attr >> 16) & 0o777)

    ci_spec = importlib.util.spec_from_file_location("s4_ci_inv", ROOT / "tests/test_ci_release_builder.py")
    _check(ci_spec is not None and ci_spec.loader is not None)
    ci_mod = importlib.util.module_from_spec(ci_spec)
    ci_spec.loader.exec_module(ci_mod)

    _check(not (extracted / ".git").exists(), "extracted archive must be non-Git")
    _check((extracted / "crates/aod-core/Cargo.toml").is_file())
    _check((extracted / "crates/aod-core/Cargo.lock").is_file())

    inv_before = ci_mod.expected_source_inventory(extracted)
    all_files_before = {
        p.relative_to(extracted).as_posix(): _sha256_file(p)
        for p in sorted(extracted.rglob("*"))
        if p.is_file()
    }

    ext_target = tmp_path / "ext_cargo_target"
    env = {**os.environ, "CARGO_TARGET_DIR": str(ext_target)}
    test_proc = subprocess.run(
        [
            "cargo",
            "test",
            "--manifest-path",
            str(extracted / "crates/aod-core/Cargo.toml"),
            "--offline",
            "--locked",
        ],
        cwd=extracted,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    _check(test_proc.returncode == 0, f"extracted source.zip cargo test failed:\n{test_proc.stderr}")
    _check(not (extracted / "crates/aod-core/target").exists())

    live_report = tmp_path / "live_report.json"
    ext_report = tmp_path / "ext_report.json"

    p_live = subprocess.run(
        [
            str(rust_binaries["debug"]),
            "--verify-vectors",
            "--check-zero-float",
            "--repo-root",
            str(ROOT),
            "--report",
            str(live_report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    _check(p_live.returncode == 0, p_live.stderr)

    p_ext = subprocess.run(
        [
            str(ext_target / "debug" / "aod-core"),
            "--verify-vectors",
            "--check-zero-float",
            "--report",
            str(ext_report),
        ],
        cwd=extracted,
        capture_output=True,
        text=True,
        timeout=60,
    )
    _check(p_ext.returncode == 0, p_ext.stderr)
    _check(
        live_report.read_bytes() == ext_report.read_bytes(),
        "live checkout report and detached source.zip report must be byte-identical",
    )

    inv_after = ci_mod.expected_source_inventory(extracted)
    all_files_after = {
        p.relative_to(extracted).as_posix(): _sha256_file(p)
        for p in sorted(extracted.rglob("*"))
        if p.is_file()
    }
    _check(inv_after == inv_before, "extracted source.zip inventory mutated during offline Cargo + CLI execution")
    _check(all_files_after == all_files_before, "unexpected file added/modified in extracted source.zip")
    _check(not (extracted / "crates/aod-core/target").exists())
