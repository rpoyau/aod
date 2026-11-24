"""CLI entry point and orchestration for the AOD Stage 2 zero-float reference engine.

Exit codes:
  0: all requested verifications passed
  1: one or more sector, policy, coverage, or golden-vector checks failed
  2: CLI argument error, unknown/duplicate sector, or unsafe runtime output path
"""
from __future__ import annotations

import argparse
import json
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
from manual.engine.report import (
    _ALLOWED_IN_REPO_OUTPUT_ROOTS,
    _path_within_lexical,
    _reject_pre_resolution_symlinks,
    atomic_write_safe_text,
    build_report,
    default_repo_root,
    serialize_report,
    validate_runtime_output_path,
)
from manual.engine.sectors.tier1_adapters import run_tier1_sector
from manual.engine.sectors.tier2_exact import run_tier2_sector
from manual.engine.sectors.tier3_quarantine import run_tier3_sector
from manual.engine.vectors import verify_all_vectors

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
        type=str,
        default=None,
        help="Write canonical report JSON to this path (must be outside distributable source dirs or under _build/).",
    )
    parser.add_argument(
        "--diagnostics-dir",
        type=str,
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
            for spec in selected_specs:
                if spec.tier == "tier1_canonical_adapter":
                    validate_runtime_output_path(
                        diagnostics_dir / f"{spec.sector_id}.stdout.txt",
                        repo_root,
                        flag_name="--diagnostics-dir child",
                        expect_dir=False,
                    )
                    validate_runtime_output_path(
                        diagnostics_dir / f"{spec.sector_id}.stderr.txt",
                        repo_root,
                        flag_name="--diagnostics-dir child",
                        expect_dir=False,
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
        try:
            atomic_write_safe_text(
                args.report, canonical_text, repo_root, flag_name="--report"
            )
        except ValueError as exc:
            sys.stderr.write(f"error: {exc}\n")
            return 2
    else:
        sys.stdout.write(canonical_text)

    failed = (
        report_obj["outcomes_summary"]["FAIL"] > 0
        or coverage_audit.get("status") == "FAIL"
        or zf_audit.get("status") == "FAIL"
        or (vectors_result is not None and vectors_result.get("status") == "FAIL")
    )
    if failed and report_path is not None:
        if coverage_audit.get("status") == "FAIL":
            detail = _sanitize_error(
                str(coverage_audit.get("error", "")), repo_root, diagnostics_dir=diagnostics_dir
            )
            sys.stderr.write(f"FAIL data_coverage: {detail}\n")
        if zf_audit.get("status") == "FAIL":
            raw_zf = zf_audit.get("error") or zf_audit.get("violations", [])[:3]
            detail = _sanitize_error(str(raw_zf), repo_root, diagnostics_dir=diagnostics_dir)
            sys.stderr.write(f"FAIL zero_float_policy: {detail}\n")
        if vectors_result is not None and vectors_result.get("status") == "FAIL":
            raw_vec = vectors_result.get("failures", [])[:3]
            detail = _sanitize_error(str(raw_vec), repo_root, diagnostics_dir=diagnostics_dir)
            sys.stderr.write(f"FAIL vectors: {detail}\n")
        for sec in report_obj["sectors"]:
            if isinstance(sec, dict) and sec.get("check_outcome") == "FAIL":
                detail = _sanitize_error(
                    str(sec.get("error", "")), repo_root, diagnostics_dir=diagnostics_dir
                )
                sys.stderr.write(f"FAIL sector={sec['sector_id']}: {detail}\n")
    return 1 if failed else 0
