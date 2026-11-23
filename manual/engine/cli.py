"""CLI entry point and orchestration for the AOD Stage 2 zero-float reference engine.

Exit codes:
  0: all requested verifications passed
  1: one or more sector, policy, coverage, or golden-vector checks failed
  2: CLI argument error, unknown/duplicate sector, or unsafe runtime output path
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from manual.engine.policy import audit_source_tree
from manual.engine.registry import (
    SECTOR_MAP,
    SECTOR_SPECS,
    SectorSpec,
    registry_digest,
    verify_data_coverage,
    verify_registry_completeness,
)
from manual.engine.report import build_report, serialize_report
from manual.engine.sectors.tier1_adapters import run_tier1_sector
from manual.engine.sectors.tier2_exact import run_tier2_sector
from manual.engine.sectors.tier3_quarantine import run_tier3_sector
from manual.engine.vectors import verify_all_vectors

_ALLOWED_IN_REPO_OUTPUT_ROOTS: frozenset[str] = frozenset(
    {"_build", "build", "dist", "release"}
)

_SCRUB_ISO_TS_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)
_SCRUB_TEMP_RE = re.compile(
    r"(?:pytest-of-[^\s'\",)\]}]+|aod-anchor-scientific-replay-[^\s'\",)\]}]+|/tmp(?:/[^\s'\",)\]}]*)*|\\Temp\\[^\s'\",)\]}]*)"
)
_SCRUB_WIN_PATH_RE = re.compile(r"(?:^|(?<=[\s'\"(=:\[{,]))[A-Za-z]:[\\/][^\s'\",)\]}]*")
_SCRUB_UNIX_PATH_RE = re.compile(
    r"(?:^/[^\s'\",)\]}]*|(?<=[\s'\"(=:\[{,])/(?:(?:home|tmp|var|Users|root|opt|usr|etc|private|mnt|srv|proc|sys|workspace|github|app|runner|builds)(?:/[^\s'\",)\]}]*)*|[^\s'\",)\]}]+/[^\s'\",)\]}]+))"
)


def default_repo_root() -> Path:
    """Resolve the repository root containing ``manual/engine/``."""
    return Path(__file__).resolve().parents[2]


def _path_within_lexical(path: Path, root: Path) -> bool:
    norm_path = Path(os.path.normpath(str(path)))
    norm_root = Path(os.path.normpath(str(root)))
    try:
        norm_path.relative_to(norm_root)
        return True
    except ValueError:
        return False


def _reject_pre_resolution_symlinks(raw_path: Path, roots: tuple[Path, ...], *, flag_name: str) -> None:
    """Reject symlinks on the target itself or any lexical segment inside any guarded root."""
    lexical_abs = Path(raw_path) if Path(raw_path).is_absolute() else (Path.cwd() / raw_path)
    if os.path.islink(lexical_abs):
        raise ValueError(f"{flag_name} target must not be a symlink")

    # Walk every lexical prefix BEFORE calling .resolve() so symlinks like _build/escape -> /tmp
    # are caught before resolution can leave the repository tree.
    parts = lexical_abs.parts
    if parts:
        cur = Path(parts[0])
        for part in parts[1:]:
            if part == ".":
                continue
            if part == "..":
                cur = cur.parent
                continue
            cur = cur / part
            if os.path.islink(cur):
                cur_in_resolved_parent = cur.parent.resolve() / cur.name
                if any(
                    _path_within_lexical(cur, r) or _path_within_lexical(cur_in_resolved_parent, r)
                    for r in roots
                ):
                    raise ValueError(
                        f"{flag_name} must not traverse symlink {cur.name!r} inside repository"
                    )


def validate_runtime_output_path(
    raw_path: Path,
    repo_root: Path,
    *,
    flag_name: str,
    expect_dir: bool = False,
) -> Path:
    """Reject writing runtime outputs inside distributable repository source directories.

    Enforces pre-resolution symlink checks, checks both ``repo_root`` and ``default_repo_root()``,
    and rejects existing directory/file type collisions. Outputs are allowed ONLY outside both
    repository roots or inside an excluded top-level build directory (``_build/``, ``build/``,
    ``dist/``, ``release/``).
    """
    repo = Path(repo_root).resolve()
    def_repo = default_repo_root().resolve()
    guarded_roots = (repo,) if repo == def_repo else (repo, def_repo)

    _reject_pre_resolution_symlinks(Path(raw_path), guarded_roots, flag_name=flag_name)

    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    for guarded in guarded_roots:
        try:
            rel = candidate.relative_to(guarded)
        except ValueError:
            continue
        if not rel.parts or len(rel.parts) < 2 or rel.parts[0] not in _ALLOWED_IN_REPO_OUTPUT_ROOTS:
            raise ValueError(
                f"{flag_name} target {rel.as_posix()!r} is inside a distributable repository "
                f"directory; write outside the repository or under _build/ to prevent source.zip contamination"
            )
        if candidate.is_symlink() or any(
            (guarded / parent).is_symlink() for parent in rel.parents if parent != Path(".")
        ):
            raise ValueError(f"{flag_name} must not traverse symlinks inside repository")

    if expect_dir:
        if candidate.exists() and not candidate.is_dir():
            raise ValueError(f"{flag_name} target already exists as a non-directory file")
    else:
        if candidate.exists() and candidate.is_dir():
            raise ValueError(f"{flag_name} target already exists as a directory")

    for parent in candidate.parents:
        if parent.exists():
            if not parent.is_dir():
                raise ValueError(f"{flag_name} parent path exists as a non-directory file")
            break

    return candidate


def _sanitize_error(
    message: str,
    repo_root: Path,
    *,
    diagnostics_dir: Path | None = None,
) -> str:
    """Scrub host paths, executables, temp markers, and timestamps for portable FAIL reports."""
    sanitized = str(message)
    replacements: list[tuple[str, str]] = [
        (str(Path(repo_root).resolve()), "<REPO_ROOT>"),
        (str(Path(repo_root)), "<REPO_ROOT>"),
        (str(default_repo_root().resolve()), "<REPO_ROOT>"),
        (str(Path(sys.executable).resolve()), "<PYTHON>"),
        (str(sys.executable), "<PYTHON>"),
        (str(Path.cwd().resolve()), "<CWD>"),
        (str(Path(tempfile.gettempdir()).resolve()), "<TEMP_DIR>"),
        (tempfile.gettempdir(), "<TEMP_DIR>"),
    ]
    if diagnostics_dir is not None:
        replacements.append((str(Path(diagnostics_dir).resolve()), "<DIAGNOSTICS_DIR>"))
        replacements.append((str(diagnostics_dir), "<DIAGNOSTICS_DIR>"))

    # Replace longest non-trivial prefixes first so specific paths win over short parents.
    seen_src: set[str] = set()
    for src, dst in sorted(replacements, key=lambda pair: len(pair[0]), reverse=True):
        if not src or src in {"/", ".", "\\"} or src in seen_src:
            continue
        seen_src.add(src)
        sanitized = sanitized.replace(src, dst)

    sanitized = _SCRUB_TEMP_RE.sub("<TEMP_PATH>", sanitized)
    sanitized = _SCRUB_WIN_PATH_RE.sub("<HOST_PATH>", sanitized)
    sanitized = _SCRUB_UNIX_PATH_RE.sub("<HOST_PATH>", sanitized)
    sanitized = _SCRUB_ISO_TS_RE.sub("<TIMESTAMP>", sanitized)
    return sanitized.strip() or "verification error"


def execute_sector(
    spec: SectorSpec,
    repo_root: Path,
    *,
    diagnostics_dir: Path | None = None,
) -> dict[str, object]:
    """Run one sector and return a canonical sector record (PASS or FAIL)."""
    try:
        if spec.tier == "tier1_canonical_adapter":
            return run_tier1_sector(spec, repo_root, diagnostics_dir=diagnostics_dir)
        if spec.tier == "tier2_exact_data_verifier":
            return run_tier2_sector(spec, repo_root)
        if spec.tier == "tier3_provenance_guard":
            return run_tier3_sector(spec, repo_root)
        raise ValueError(f"unsupported tier: {spec.tier}")
    except (ValueError, TypeError, KeyError, OSError, ZeroDivisionError, subprocess.SubprocessError) as exc:
        return {
            "sector_id": spec.sector_id,
            "tier": spec.tier,
            "adapter_id": spec.adapter_id,
            "bound_source_operation": spec.bound_source_operation,
            "capability": spec.capability,
            "check_outcome": "FAIL",
            "scientific_status": spec.scientific_status,
            "retained_holds": list(spec.retained_holds),
            "input_digests": {},
            "verified_counts": {},
            "exact_residuals_summary": {},
            "error": _sanitize_error(str(exc), repo_root, diagnostics_dir=diagnostics_dir),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -B -m manual.engine",
        description="AOD Stage 2 audited zero-float reference engine.",
    )
    parser.add_argument(
        "--verify-all",
        action="store_true",
        help="Execute all 16 registered verification sectors and dual data-coverage audit.",
    )
    parser.add_argument(
        "--sector",
        action="append",
        default=[],
        metavar="SECTOR_ID",
        help="Execute one registered sector (repeatable; rejects unknown or duplicate IDs).",
    )
    parser.add_argument(
        "--list-sectors",
        action="store_true",
        help="List all 16 registered sectors with metadata as canonical JSON and exit 0.",
    )
    parser.add_argument(
        "--check-zero-float",
        action="store_true",
        help="Run static AST zero-float/bare-assert/import policy audit over manual/engine/.",
    )
    parser.add_argument(
        "--verify-vectors",
        action="store_true",
        help="Load and execute all 30 S4 golden vectors in manual/engine/vectors/*.jsonl.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write canonical report JSON to this path (must be outside distributable source dirs or under _build/).",
    )
    parser.add_argument(
        "--diagnostics-dir",
        type=Path,
        default=None,
        help="Optional directory to capture raw Tier-1 stdout/stderr (same path safety guard as --report).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repository root directory (defaults to checkout containing manual/engine/).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    verify_registry_completeness()

    repo_root = default_repo_root() if args.repo_root is None else Path(args.repo_root).resolve()

    if args.list_sectors:
        listing = {
            "registry_digest": registry_digest(),
            "sector_count": len(SECTOR_SPECS),
            "sectors": [spec.to_canonical_dict() for spec in SECTOR_SPECS],
        }
        sys.stdout.write(json.dumps(listing, sort_keys=True, indent=2, ensure_ascii=True) + "\n")
        return 0

    if args.verify_all and args.sector:
        sys.stderr.write("error: --verify-all cannot be combined with --sector\n")
        return 2

    selected_specs: list[SectorSpec] = []
    if args.verify_all:
        selected_specs = list(SECTOR_SPECS)
    elif args.sector:
        seen: set[str] = set()
        for sid in args.sector:
            if sid in seen:
                sys.stderr.write(f"error: duplicate --sector {sid!r}\n")
                return 2
            if sid not in SECTOR_MAP:
                sys.stderr.write(f"error: unknown --sector {sid!r}\n")
                return 2
            seen.add(sid)
            selected_specs.append(SECTOR_MAP[sid])

    if not selected_specs and not args.check_zero_float and not args.verify_vectors:
        sys.stderr.write(
            "error: specify at least one action (--verify-all, --sector, --list-sectors, "
            "--check-zero-float, or --verify-vectors)\n"
        )
        return 2

    report_path: Path | None = None
    diagnostics_dir: Path | None = None
    try:
        if args.report is not None:
            report_path = validate_runtime_output_path(
                args.report, repo_root, flag_name="--report", expect_dir=False
            )
        if args.diagnostics_dir is not None:
            diagnostics_dir = validate_runtime_output_path(
                args.diagnostics_dir, repo_root, flag_name="--diagnostics-dir", expect_dir=True
            )
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    # 1. Data coverage audit (executed when running --verify-all; optional otherwise)
    if args.verify_all:
        try:
            coverage_audit = verify_data_coverage(repo_root)
        except (ValueError, TypeError, OSError) as exc:
            coverage_audit = {
                "status": "FAIL",
                "error": _sanitize_error(str(exc), repo_root, diagnostics_dir=diagnostics_dir),
            }
    else:
        coverage_audit = {"status": "NOT_REQUESTED"}

    # 2. Static AST zero-float policy audit
    if args.check_zero_float:
        engine_root = repo_root / "manual" / "engine"
        try:
            zf_audit = audit_source_tree(engine_root)
        except (ValueError, OSError) as exc:
            zf_audit = {
                "status": "FAIL",
                "error": _sanitize_error(str(exc), repo_root, diagnostics_dir=diagnostics_dir),
            }
    else:
        zf_audit = {"status": "NOT_REQUESTED"}

    # 3. Golden vectors verification
    vectors_result: dict[str, object] | None = None
    if args.verify_vectors:
        try:
            vectors_result = verify_all_vectors(repo_root)
        except (ValueError, TypeError, OSError) as exc:
            vectors_result = {
                "status": "FAIL",
                "rational_core_count": 0,
                "symbolic_and_display_count": 0,
                "total_vectors": 0,
                "passed_vectors": 0,
                "failed_vectors": 0,
                "file_digests": {"error": "0" * 64},
                "failures": [
                    {
                        "case_id": "LOADER",
                        "error": _sanitize_error(str(exc), repo_root, diagnostics_dir=diagnostics_dir),
                    }
                ],
            }

    # 4. Execute selected sectors
    sector_results = [
        execute_sector(spec, repo_root, diagnostics_dir=diagnostics_dir)
        for spec in selected_specs
    ]

    report_obj = build_report(
        sector_results,
        data_coverage_audit=coverage_audit,
        zero_float_policy_audit=zf_audit,
        vectors_verification=vectors_result,
    )
    canonical_text = serialize_report(report_obj)

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(canonical_text, encoding="utf-8")
    else:
        sys.stdout.write(canonical_text)

    failed = (
        report_obj["outcomes_summary"]["FAIL"] > 0
        or coverage_audit.get("status") == "FAIL"
        or zf_audit.get("status") == "FAIL"
        or (vectors_result is not None and vectors_result.get("status") == "FAIL")
    )
    return 1 if failed else 0
