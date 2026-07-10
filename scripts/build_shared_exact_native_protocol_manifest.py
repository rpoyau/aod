#!/usr/bin/env python3
"""Validate and hash the shared native-exactness/D.E.C./projection protocol."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "shared" / "data" / "exact_native_protocol"
APPENDIX = ROOT / "shared" / "appendices" / "exact_native_dec_and_metric_projection_protocol.tex"
MANIFEST = DATA / "aod_shared_exactness_protocol_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate() -> None:
    kernel = rows("aod_dec_kernel_family_registry.csv")
    if len(kernel) != 1 or kernel[0]["kernel_family_id"] != "aod_dec_exact_kernel_v1":
        raise ValueError("exact D.E.C. kernel family row missing")
    if kernel[0]["terminal_rule"] != "if_Z_t_eq_0_no_division_record_terminal_blocked_or_pending":
        raise ValueError("terminal Z=0 rule missing")

    modes = [r["execution_mode"] for r in rows("aod_dec_execution_mode_registry.csv")]
    if modes != ["enumerate_all", "deterministic_selector", "sample_one"]:
        raise ValueError(f"unexpected execution modes: {modes}")

    join = rows("aod_branch_isolated_join_protocol.csv")
    orders = [int(r["stage_order"]) for r in join]
    if orders != list(range(1, 9)):
        raise ValueError(f"branch-isolated protocol order invalid: {orders}")
    if any(r["current_state"] not in {
        "protocol_declared", "contract_declared_not_instantiated",
        "closed_no_instantiated_projection", "closed_no_selected_scored_target",
        "closed_alignment_unavailable", "closed"
    } for r in join):
        raise ValueError("unexpected join current state")

    residual_ids = [r["component_id"] for r in rows("aod_typed_residual_registry.csv")]
    expected = ["E_calc", "Delta_oct", "E_oct", "E_proj", "I_Pi", "U_obs", "E_lineage", "E_scope", "E_emp", "E_rep"]
    if residual_ids != expected:
        raise ValueError(f"typed residual registry mismatch: {residual_ids}")

    migration = rows("aod_existing_prediction_migration_audit.csv")
    if not migration:
        raise ValueError("migration audit is empty")
    allowed = {
        "native_unchanged_report_unchanged",
        "native_unchanged_projection_retyped",
        "native_unchanged_target_support_changed",
        "native_unchanged_score_changed",
        "native_changed_DEC_defect_corrected",
        "comparison_now_abstains",
        "comparison_scope_changed",
    }
    for row in migration:
        if row["audit_disposition"] not in allowed:
            raise ValueError(f"bad migration disposition: {row['audit_disposition']}")
        if row["native_change_status"] == "unchanged" and row["old_native_packet_sha256"] != row["new_native_packet_sha256"]:
            raise ValueError(f"unchanged native row has changed hash: {row['lane_id']}")


def build() -> dict:
    validate()
    files = sorted(p for p in DATA.glob("*") if p.is_file() and p.name != MANIFEST.name)
    return {
        "protocol_id": "shared_native_exactness_dec_metric_projection_v1",
        "protocol_role": "cross_manual_exactness_and_comparison_contract",
        "shared_appendix_path": APPENDIX.relative_to(ROOT).as_posix(),
        "shared_appendix_sha256": sha256(APPENDIX),
        "manual_render_policy": "identical_shared_appendix_source_in_manual_I_and_manual_II",
        "main_note_policy": "frozen_unchanged",
        "manual_I_policy": "intentionally_revised_new_artifact_hash",
        "manual_II_policy": "shared_protocol_plus_application_specific_rows",
        "current_empirical_state": {
            "candidate_universe": "not_materialized",
            "selected_accession": "none",
            "target_value_read_status": "not_read",
            "comparison_join_state": "closed",
            "residual_status": "not_computed",
            "score_status": "no_score",
        },
        "files": {
            p.name: {
                "path": p.relative_to(ROOT).as_posix(),
                "sha256": sha256(p),
                "byte_count": p.stat().st_size,
            }
            for p in files
        },
    }


def main() -> int:
    manifest = build()
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(MANIFEST.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
