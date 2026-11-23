"""Deterministic canonical report builder and serializer (aod.manual.engine.report.v1).

Output bytes are deterministic across operating environments, checkouts, and
normal vs ``python3 -O`` execution: sorted keys, ASCII-safe UTF-8, LF endings,
zero timestamps/durations/absolute paths, and zero float/complex values.
"""
from __future__ import annotations

import json

from manual.engine.policy import require_no_floats
from manual.engine.registry import SECTOR_SPECS, registry_digest
from manual.engine.schema import (
    BASE_COMMIT_BINDING,
    ENGINE_VERSION,
    REPORT_SCHEMA,
    VALID_SCIENTIFIC_STATUSES,
    validate_report,
)

_CANONICAL_SECTOR_ORDER: dict[str, int] = {
    spec.sector_id: idx for idx, spec in enumerate(SECTOR_SPECS)
}


def build_report(
    sector_results: list[dict[str, object]],
    *,
    data_coverage_audit: dict[str, object],
    zero_float_policy_audit: dict[str, object],
    vectors_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    """Assemble and validate a canonical ``aod.manual.engine.report.v1`` dict."""
    ordered_sectors = sorted(
        sector_results,
        key=lambda rec: _CANONICAL_SECTOR_ORDER.get(str(rec.get("sector_id", "")), 999),
    )

    outcomes_summary = {
        "total_executed": len(ordered_sectors),
        "PASS": sum(1 for rec in ordered_sectors if rec.get("check_outcome") == "PASS"),
        "FAIL": sum(1 for rec in ordered_sectors if rec.get("check_outcome") == "FAIL"),
    }

    scientific_status_summary = {status: 0 for status in sorted(VALID_SCIENTIFIC_STATUSES)}
    for rec in ordered_sectors:
        if rec.get("check_outcome") == "PASS":
            status = str(rec["scientific_status"])
            if status in scientific_status_summary:
                scientific_status_summary[status] += 1

    payload: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "engine_version": ENGINE_VERSION,
        "base_commit_binding": BASE_COMMIT_BINDING,
        "registry_digest": registry_digest(),
        "sector_count": len(ordered_sectors),
        "data_coverage_audit": data_coverage_audit,
        "sectors": ordered_sectors,
        "outcomes_summary": outcomes_summary,
        "scientific_status_summary": scientific_status_summary,
        "zero_float_policy_audit": zero_float_policy_audit,
    }
    if vectors_verification is not None:
        payload["vectors_verification"] = vectors_verification

    require_no_floats(payload)
    validate_report(payload)
    return payload


def serialize_report(report_obj: dict[str, object]) -> str:
    """Validate and deterministically serialize a canonical report to UTF-8 JSON with LF."""
    validate_report(report_obj)
    return json.dumps(report_obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
