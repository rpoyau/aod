"""Tier-3 provenance quarantine guard (Sector 16: ``provenance_quarantine``).

Verifies exact frozen digests, shapes, verbatim sub-table consistency, and the
exact ``9/20`` vs ``~23/50`` non-conflation predicate across all 9 quarantined
SPARC/Tau provenance files while keeping ``check_outcome: "PASS"`` strictly
orthogonal to ``scientific_status: "UNRESOLVED_PROVENANCE_QUARANTINED"``.
"""
from __future__ import annotations

import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from manual.engine.numeric import (
    canonical_rational_str,
    parse_exact_int,
    parse_printed_rational,
    require,
)
from manual.engine.registry import SectorSpec

# Pinned shapes and frozen SHA-256 digests from CANONICAL_BINDINGS.json:862,866,867,900-905
QUARANTINED_FILES: dict[str, tuple[int, int, str]] = {
    "manual/data/derived/sparc_declaration_controls.csv": (
        4,
        2,
        "e16ef11585c814112e6f19f4cbabee1b5442f6bd1981f9d3d9f70cc76f7afd12",
    ),
    "manual/data/derived/tau_declaration_controls.csv": (
        4,
        2,
        "d1769dd1161a4f12f0be0bd7916f89c708f429560ba2fedbb2ecfd7c24ea5cab",
    ),
    "manual/data/derived/tau_ring_diagnostic.csv": (
        4,
        6,
        "c15898ce88098fbe4086f45f43d9e7323c26d36a863fe2da52ea19edb84a15bd",
    ),
    "manual/data/tau/aod_tau_fractal_ring_baseline_compatible.csv": (
        12,
        20,
        "b6fdf97b8998381c81ce850278aebf7382fd9ece79f181a80db814e516a83d35",
    ),
    "manual/data/tau/aod_tau_fractal_ring_comparison.csv": (
        12,
        15,
        "cc022faec55a0dc1863cfa123f0b8a5d9599415b0cca62b6929ff9c8fff5b74a",
    ),
    "manual/data/tau/aod_tau_fractal_ring_primary_lane_audit.csv": (
        4,
        14,
        "f045f9bc16e71b8d9531c6fd39632fb1653f9483496b4d8079738b56799dfba8",
    ),
    "manual/data/tau/aod_tau_fractal_ring_summary.csv": (
        12,
        30,
        "7aceb1d12cf39bbabf0153d10ab35d0307be6be6c4258ea4231acd2fe05f066b",
    ),
    "manual/data/tau/aod_tau_fractal_ring_top_cells.csv": (
        240,
        9,
        "8baedf575d8c435f4f4a58c0c69a5c5af0c89e78c7ba2fec07fd316afb2440f2",
    ),
    "manual/data/tau/aod_tau_fractal_ring_verification.csv": (
        4,
        8,
        "aa5149ccc0a31189ba83d7126fed892b0f95161ef4d739329e0c3585a9a8ad01",
    ),
}

_SUMMARY_NOMINAL_TOL = Fraction(1, 10**12)


def _read_csv_checked(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require(reader.fieldnames is not None, f"CSV missing header: {path.name}")
        header = list(reader.fieldnames)
        rows: list[dict[str, str]] = []
        for idx, row in enumerate(reader):
            require(None not in row, f"extra columns in {path.name} row {idx}")
            require(all(v is not None for v in row.values()), f"missing cell in {path.name} row {idx}")
            rows.append(dict(row))
    return header, rows


def verify_tau_non_conflation(
    diag_missing_1210: Fraction,
    summary_missing_1210_values: list[Fraction],
) -> dict[str, object]:
    """Enforce exact non-conflation between ``9/20`` (diagnostic) and ``~23/50`` (summary)."""
    require(
        diag_missing_1210 == Fraction(9, 20),
        f"tau_ring_diagnostic 1:2:10 missing_fraction must be exact 9/20, got {diag_missing_1210}",
    )
    require(
        len(summary_missing_1210_values) == 3,
        f"expected 3 summary depth rows for 1:2:10, got {len(summary_missing_1210_values)}",
    )
    max_dev_from_23_50 = Fraction(0)
    for idx, val in enumerate(summary_missing_1210_values):
        require(
            val != Fraction(9, 20),
            f"conflation breach: summary 1:2:10 row {idx} equals 9/20 instead of ~23/50",
        )
        dev = abs(val - Fraction(23, 50))
        require(
            dev < _SUMMARY_NOMINAL_TOL,
            f"summary 1:2:10 row {idx} deviates from 23/50 by {dev} >= 1/10^12",
        )
        if dev > max_dev_from_23_50:
            max_dev_from_23_50 = dev
    nominal_diff = Fraction(23, 50) - Fraction(9, 20)
    require(nominal_diff == Fraction(1, 100) and nominal_diff != 0, "expected genuine 1/100 difference")
    return {
        "diagnostic_1210_exact": canonical_rational_str(diag_missing_1210),
        "summary_1210_nominal": "23/50",
        "genuine_rational_difference": canonical_rational_str(nominal_diff),
        "max_summary_deviation_from_23_50": canonical_rational_str(max_dev_from_23_50),
    }


def verify_provenance_quarantine(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Execute Tier-3 provenance quarantine guard across all 9 frozen files."""
    root = Path(repo_root).resolve()
    cb_path = root / "contracts" / "scientific" / "CANONICAL_BINDINGS.json"
    require(cb_path.is_file() and not cb_path.is_symlink(), "CANONICAL_BINDINGS.json missing")
    cb_frozen = json.loads(cb_path.read_text(encoding="utf-8"))["frozen_sha256"]

    require(
        set(spec.input_paths) == set(QUARANTINED_FILES.keys()),
        "Tier-3 registry input_paths mismatch against 9 quarantined files",
    )

    digests: dict[str, str] = {}
    parsed_tables: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for rel in sorted(QUARANTINED_FILES):
        exp_rows, exp_cols, exp_sha = QUARANTINED_FILES[rel]
        require(cb_frozen.get(rel) == exp_sha, f"CANONICAL_BINDINGS frozen_sha256 mismatch for {rel}")
        target = root / rel
        require(target.is_file() and not target.is_symlink(), f"quarantined file missing or symlink: {rel}")
        actual_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        require(actual_sha == exp_sha, f"quarantined file digest mismatch for {rel}: {actual_sha} != {exp_sha}")
        header, rows = _read_csv_checked(target)
        require(
            len(rows) == exp_rows and len(header) == exp_cols,
            f"shape mismatch for {rel}: got ({len(rows)}, {len(header)}), expected ({exp_rows}, {exp_cols})",
        )
        digests[rel] = actual_sha
        parsed_tables[rel] = (header, rows)

    # 1. tau_ring_diagnostic.csv winner & 1:2:10 non-conflation
    _, diag_rows = parsed_tables["manual/data/derived/tau_ring_diagnostic.csv"]
    diag_by_k = {row["K"]: row for row in diag_rows}
    require("1:2:9" in diag_by_k and "1:2:10" in diag_by_k, "tau_ring_diagnostic missing 1:2:9 or 1:2:10")
    scored_abs = [
        (abs(parse_printed_rational(row["S_tau_ring"], name="S_tau_ring", allow_fraction_slash=False)), row["K"])
        for row in diag_rows
    ]
    min_abs = min(val for val, _ in scored_abs)
    argmin_ks = [k for val, k in scored_abs if val == min_abs]
    require(argmin_ks == ["1:2:9"], f"expected argmin |S_tau_ring| == 1:2:9, got {argmin_ks}")
    require(diag_by_k["1:2:9"]["status"] == "winner", "1:2:9 status must be 'winner'")
    require(
        parse_printed_rational(diag_by_k["1:2:9"]["missing_fraction"], allow_fraction_slash=False)
        == Fraction(31, 50),
        "tau_ring_diagnostic 1:2:9 missing_fraction must be exact 31/50",
    )

    diag_1210 = parse_printed_rational(
        diag_by_k["1:2:10"]["missing_fraction"], name="diag_1210", allow_fraction_slash=False
    )

    # 2. aod_tau_fractal_ring_summary.csv 1:2:10 depth rows
    sum_hdr, sum_rows = parsed_tables["manual/data/tau/aod_tau_fractal_ring_summary.csv"]
    rows_1210 = [row for row in sum_rows if row["candidate"] == "1:2:10"]
    depths_1210 = {parse_exact_int(row["depth"], name="depth") for row in rows_1210}
    require(depths_1210 == {2, 3, 4}, f"expected depths {{2,3,4}} for 1:2:10, got {depths_1210}")
    sum_1210_vals = [
        parse_printed_rational(row["missing_fraction"], name="summary_1210", allow_fraction_slash=False)
        for row in rows_1210
    ]
    non_conflation = verify_tau_non_conflation(diag_1210, sum_1210_vals)

    # 3. Verbatim sub-table consistency: baseline_compatible, primary_lane_audit, verification
    base_hdr, base_rows = parsed_tables["manual/data/tau/aod_tau_fractal_ring_baseline_compatible.csv"]
    require(set(base_hdr) <= set(sum_hdr), "baseline_compatible columns not subset of summary")
    for idx, (brow, srow) in enumerate(zip(base_rows, sum_rows)):
        for col in base_hdr:
            require(
                brow[col] == srow[col],
                f"baseline_compatible row {idx} col {col!r} differs from summary",
            )

    pla_hdr, pla_rows = parsed_tables["manual/data/tau/aod_tau_fractal_ring_primary_lane_audit.csv"]
    sum_d3 = [row for row in sum_rows if parse_exact_int(row["depth"]) == 3]
    require(len(sum_d3) == 4 and set(pla_hdr) <= set(sum_hdr), "primary_lane_audit schema mismatch")
    for idx, (prow, srow) in enumerate(zip(pla_rows, sum_d3)):
        for col in pla_hdr:
            require(
                prow[col] == srow[col],
                f"primary_lane_audit row {idx} col {col!r} differs from summary depth=3",
            )

    _, ver_rows = parsed_tables["manual/data/tau/aod_tau_fractal_ring_verification.csv"]
    table_shape_map = {
        "baseline_compatible": (12, 20),
        "summary": (12, 30),
        "comparison": (12, 15),
        "top_cells": (240, 9),
    }
    seen_tables: set[str] = set()
    for vrow in ver_rows:
        tname = vrow["table"]
        require(tname in table_shape_map and tname not in seen_tables, f"unexpected verification table: {tname!r}")
        seen_tables.add(tname)
        exp_r, exp_c = table_shape_map[tname]
        require(
            parse_exact_int(vrow["rows_v2"]) == exp_r
            and parse_exact_int(vrow["rows_v3"]) == exp_r
            and parse_exact_int(vrow["cols_v2"]) == exp_c
            and parse_exact_int(vrow["cols_v3"]) == exp_c
            and vrow["columns_equal"] == "True"
            and vrow["string_cells_equal"] == "True",
            f"verification row shape/equality mismatch for {tname}",
        )
        max_nd = parse_printed_rational(
            vrow["max_numeric_delta"], name="max_numeric_delta", allow_fraction_slash=False, allow_exponent=True
        )
        require(max_nd >= 0, f"negative max_numeric_delta for {tname}")
    require(seen_tables == set(table_shape_map.keys()), "verification table coverage incomplete")

    # 4. Positive carried controls
    _, sparc_ctrl = parsed_tables["manual/data/derived/sparc_declaration_controls.csv"]
    for idx, row in enumerate(sparc_ctrl):
        val = parse_printed_rational(row["MAPE_U_percent"], name=f"sparc_ctrl[{idx}]", allow_fraction_slash=False)
        require(val > 0, f"sparc_declaration_controls row {idx} must be positive")

    _, tau_ctrl = parsed_tables["manual/data/derived/tau_declaration_controls.csv"]
    for idx, row in enumerate(tau_ctrl):
        val = parse_exact_int(row["winner_margin_percent"], name=f"tau_ctrl[{idx}]")
        require(val > 0, f"tau_declaration_controls row {idx} must be positive")

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": "provenance_guard",
        "check_outcome": "PASS",
        "scientific_status": "UNRESOLVED_PROVENANCE_QUARANTINED",
        "retained_holds": list(spec.retained_holds),
        "input_digests": digests,
        "verified_counts": {
            "quarantined_files_verified": len(QUARANTINED_FILES),
            "tau_1210_summary_depth_rows": len(rows_1210),
            "sparc_carried_controls": len(sparc_ctrl),
            "tau_carried_controls": len(tau_ctrl),
        },
        "exact_residuals_summary": {
            "non_conflation_audit": non_conflation,
            "subtable_verbatim_match": True,
            "tau_diagnostic_argmin": "1:2:9",
            "field_roles": {
                "unresolved_provenance_output": sorted(QUARANTINED_FILES.keys()),
            },
        },
        "error": None,
    }


def run_tier3_sector(spec: SectorSpec, repo_root: Path) -> dict[str, object]:
    """Dispatch and execute the Tier-3 provenance quarantine guard."""
    require(spec.sector_id == "provenance_quarantine", f"unknown Tier-3 sector: {spec.sector_id}")
    return verify_provenance_quarantine(spec, repo_root)
