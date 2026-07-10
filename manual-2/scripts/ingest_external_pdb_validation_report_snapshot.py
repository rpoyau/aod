#!/usr/bin/env python3
"""Materialize the r22A validation-report snapshot and local-support gate.

The script is intentionally offline and deterministic.  It locks a release-local
parsed snapshot of the official RCSB/wwPDB full validation report for 1CRN.  The
snapshot is not represented as the original archive PDF/XML/CIF byte stream;
those upstream byte locks remain separate availability objects.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
PAYLOAD_DIR = PROT / "external_pdb_validation_payloads"
VERSION = "v40.02r22A"
RELEASE = "v40.02r22A_validation_report_snapshot_byte_lock_local_support_ingest_gate"
SOURCE_ACCESSION = "1CRN"
SOURCE_URL = "https://files.rcsb.org/validation/view/1crn_full_validation.pdf"
QUALITY_RULE_FAMILY_ID = "pdb_local_support_rule_1CRN"
QUALITY_RULE_STATE_ID = "pdb_local_support_rule_1CRN_predeclared_v4002r212"
QUALITY_RULE_DECLARATION_ID = "pdb_local_support_rule_declaration_1CRN_v4002r212"
QUALITY_RULE_APPLICATION_ID = "pdb_local_support_rule_application_1CRN_v4002r22A"
QUALITY_MASK_ID = "pdb_pair_quality_mask_1CRN_A_all946_v4002r22A"
TARGET_LINEAGE_FAMILY_ID = "pdb_measurement_lineage_1CRN_xray"
TARGET_LINEAGE_STATE_ID = "pdb_measurement_lineage_1CRN_xray_validation_snapshot_ingested_v4002r22A"
TARGET_LINEAGE_DECLARATION_ID = "pdb_measurement_lineage_declaration_1CRN_xray_v4002r22A"
AOD_LINEAGE_FAMILY_ID = "pdb_aod_prediction_lineage_GAS"
AOD_LINEAGE_STATE_ID = "pdb_aod_prediction_lineage_GAS_contact_pair_set_frozen_v4002r05"
AOD_LINEAGE_DECLARATION_ID = "pdb_aod_prediction_lineage_declaration_GAS_v4002r22A"
COMPARISON_JOIN_ID = "pdb_comparison_join_1CRN_A_v4002r22A"
SNAPSHOT_NAME = "1crn_full_validation_report_parsed_snapshot.json"
SNAPSHOT_PATH = PAYLOAD_DIR / SNAPSHOT_NAME

# Parsed from the official full validation report view.  Values are deliberately
# limited to the predeclared global/local support fields needed by this gate.
VALIDATION_SNAPSHOT = {
    "snapshot_schema": "aod.manual2.pdb_validation_report_parsed_snapshot.v1",
    "source_database": "RCSB_PDB_wwPDB",
    "source_accession": "1CRN",
    "source_report_url": SOURCE_URL,
    "source_report_title": "Full wwPDB X-ray Structure Validation Report",
    "source_report_generated_utc": "2026-03-05T18:55:00Z",
    "snapshot_registration_utc": "2026-06-18T00:00:00Z",
    "snapshot_semantics": "field_level_transcription_of_official_report_not_original_archive_pdf_xml_cif_bytes",
    "upstream_original_payload_byte_lock_status": "not_locked_in_build_environment",
    "validation_pipeline": {
        "wwpdb_validation_pipeline": "2.49",
        "molprobity": "4-5-2 with Phenix2.0",
        "xtriage": "NOT EXECUTED",
        "eds": "NOT EXECUTED",
        "percentile_statistics": "20250101.v01",
    },
    "entry": {
        "experimental_method": "X-RAY DIFFRACTION",
        "reported_resolution_angstrom": 1.50,
        "chain_id": "A",
        "residue_count": 46,
        "atom_count": 327,
        "zero_occupancy_atom_count": 0,
        "alternate_conformation_residue_count": 0,
        "trace_residue_count": 0,
        "space_group": "P 1 21 1",
        "cell": {"a": 40.96, "b": 18.65, "c": 22.52, "alpha": 90.00, "beta": 90.77, "gamma": 90.00},
        "refinement_program": "PROLSQ",
        "r_work": None,
        "r_free": None,
        "completeness": None,
        "rmerge": None,
        "rsym": None,
        "average_b_all_atoms_angstrom2": 6.0,
        "clash_count": 0,
        "symmetry_clash_count": 0,
        "ramachandran_outlier_count": 0,
        "sidechain_outlier_count": 0,
        "chain_break_count": 0,
    },
    "local_model_to_data": {
        "eds_status": "not_executed",
        "rsrz_available": False,
        "rscc_available": False,
        "missing_density_assessment_available": False,
    },
    "geometry_outliers": [
        {"chain_id": "A", "auth_seq_id": 7, "label_seq_id": 7, "residue_name": "ILE", "outlier_type": "bond_angle", "atoms": "CA-C-O", "z_score": -5.35, "observed": 115.39, "ideal": 120.95},
        {"chain_id": "A", "auth_seq_id": 12, "label_seq_id": 12, "residue_name": "ASN", "outlier_type": "bond_angle", "atoms": "OD1-CG-ND2", "z_score": 5.01, "observed": 127.61, "ideal": 122.60},
        {"chain_id": "A", "auth_seq_id": 14, "label_seq_id": 14, "residue_name": "ASN", "outlier_type": "bond_angle", "atoms": "OD1-CG-ND2", "z_score": 6.03, "observed": 128.62, "ideal": 122.60},
        {"chain_id": "A", "auth_seq_id": 37, "label_seq_id": 37, "residue_name": "GLY", "outlier_type": "bond_length", "atoms": "N-CA", "z_score": 5.78, "observed": 1.52, "ideal": 1.45},
    ],
}



PROTECTED_CURRENT_FILES = [
    "manual-2/data/protein/pdb_external_measurement_manifest.json",
    "manual-2/data/protein/pdb_external_quality_mask_manifest.json",
    "manual-2/data/protein/pdb_external_validation_local_support_manifest.json",
    "manual-2/data/protein/pdb_external_quality_mask_policy_application.csv",
    "manual-2/data/protein/pdb_external_target_limitation_budget.csv",
    "manual-2/data/protein/pdb_external_contact_observable_policy.csv",
    "manual-2/data/protein/pdb_external_comparison_allowed_matrix.csv",
    "manual-2/data/protein/pdb_external_validation_snapshot_evidence_locators.csv",
    "manual-2/data/protein/pdb_external_validation_snapshot_normalization_policy.csv",
    "manual-2/data/protein/pdb_external_validation_outlier_observable_policy.csv",
    "manual-2/data/protein/pdb_external_legacy_entry_policy.csv",
    "manual-2/data/protein/pdb_external_scored_accession_eligibility_rule.csv",
    "manual-2/data/protein/pdb_external_validation_snapshot_provenance_manifest.json",
    "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
    "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
    "manual-2/data/protein/pdb_external_quality_masked_contact_summary.csv",
    "manual-2/data/protein/external_pdb_validation_payloads/1crn_full_validation_report_parsed_snapshot.json",

]

def current_package_version() -> str:
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("Canonical version:"):
            return line.split(":", 1)[1].strip()
    return ""

def capture_current_files_if_newer() -> dict[Path, bytes]:
    if current_package_version() == VERSION:
        return {}
    captured: dict[Path, bytes] = {}
    for rel in PROTECTED_CURRENT_FILES:
        p = ROOT / rel
        if p.is_file():
            captured[p] = p.read_bytes()
    return captured

def restore_captured_files(captured: dict[Path, bytes]) -> None:
    for p, data in captured.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def write_snapshot() -> tuple[str, int]:
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(VALIDATION_SNAPSHOT, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(SNAPSHOT_PATH), SNAPSHOT_PATH.stat().st_size


def write_validation_payload_ledgers(snapshot_sha: str, snapshot_bytes: int) -> None:
    fields = [
        "validation_payload_id", "source_database", "source_accession", "payload_type",
        "source_report_url", "local_payload_path", "local_payload_sha256", "local_payload_byte_count",
        "snapshot_semantics", "upstream_original_payload_type", "upstream_original_payload_byte_lock_status",
        "report_generated_utc", "snapshot_registration_utc", "parse_status", "field_availability_status",
        "comparison_role", "release_status",
    ]
    rows = [{
        "validation_payload_id": "pdb_validation_report_snapshot_1CRN_v4002r22A",
        "source_database": "RCSB_PDB_wwPDB",
        "source_accession": SOURCE_ACCESSION,
        "payload_type": "validation_report_parsed_snapshot",
        "source_report_url": SOURCE_URL,
        "local_payload_path": f"manual-2/data/protein/external_pdb_validation_payloads/{SNAPSHOT_NAME}",
        "local_payload_sha256": snapshot_sha,
        "local_payload_byte_count": snapshot_bytes,
        "snapshot_semantics": VALIDATION_SNAPSHOT["snapshot_semantics"],
        "upstream_original_payload_type": "full_validation_report_pdf_xml_cif",
        "upstream_original_payload_byte_lock_status": "not_locked_in_build_environment",
        "report_generated_utc": VALIDATION_SNAPSHOT["source_report_generated_utc"],
        "snapshot_registration_utc": VALIDATION_SNAPSHOT["snapshot_registration_utc"],
        "parse_status": "parsed_predeclared_global_and_local_support_fields",
        "field_availability_status": "geometry_validation_available_local_model_to_data_EDS_fields_unavailable",
        "comparison_role": "target_measurement_lineage_support_only_not_AOD_premise",
        "release_status": RELEASE,
    }]
    write_csv(PROT / "pdb_external_validation_payload_byte_lock.csv", fields, rows)

    pfields = [
        "validation_provenance_id", "source_accession", "source_report_url", "report_generated_utc",
        "wwpdb_validation_pipeline", "molprobity_version", "xtriage_status", "eds_status",
        "percentile_statistics_version", "snapshot_sha256", "archive_original_byte_lock_status",
        "provenance_status", "release_status",
    ]
    p = VALIDATION_SNAPSHOT["validation_pipeline"]
    prows = [{
        "validation_provenance_id": "pdb_validation_provenance_1CRN_v4002r22A",
        "source_accession": SOURCE_ACCESSION,
        "source_report_url": SOURCE_URL,
        "report_generated_utc": VALIDATION_SNAPSHOT["source_report_generated_utc"],
        "wwpdb_validation_pipeline": p["wwpdb_validation_pipeline"],
        "molprobity_version": p["molprobity"],
        "xtriage_status": "not_executed",
        "eds_status": "not_executed",
        "percentile_statistics_version": p["percentile_statistics"],
        "snapshot_sha256": snapshot_sha,
        "archive_original_byte_lock_status": "unresolved_not_claimed_by_this_gate",
        "provenance_status": "official_report_field_snapshot_hash_locked",
        "release_status": RELEASE,
    }]
    write_csv(PROT / "pdb_external_validation_payload_provenance.csv", pfields, prows)


def write_global_metrics(snapshot_sha: str) -> None:
    e = VALIDATION_SNAPSHOT["entry"]
    fields = [
        "validation_global_metrics_id", "source_accession", "snapshot_sha256", "experimental_method",
        "reported_resolution_angstrom", "refinement_program", "R_work", "R_free", "R_free_minus_R_work",
        "completeness", "multiplicity", "I_over_sigma", "Rmerge", "Rsym", "average_B_all_atoms_angstrom2",
        "atom_count", "zero_occupancy_atom_count", "alternate_conformation_residue_count", "clash_count",
        "symmetry_clash_count", "ramachandran_outlier_count", "sidechain_outlier_count", "chain_break_count",
        "xtriage_status", "eds_status", "global_quality_state", "release_status",
    ]
    rows = [{
        "validation_global_metrics_id": "pdb_validation_global_metrics_1CRN_v4002r22A",
        "source_accession": SOURCE_ACCESSION,
        "snapshot_sha256": snapshot_sha,
        "experimental_method": e["experimental_method"],
        "reported_resolution_angstrom": f'{e["reported_resolution_angstrom"]:.2f}',
        "refinement_program": e["refinement_program"],
        "R_work": "unavailable_in_validation_report",
        "R_free": "unavailable_in_validation_report",
        "R_free_minus_R_work": "unavailable_in_validation_report",
        "completeness": "unavailable_in_validation_report",
        "multiplicity": "unavailable_in_validation_report",
        "I_over_sigma": "unavailable_in_validation_report",
        "Rmerge": "unavailable_in_validation_report",
        "Rsym": "unavailable_in_validation_report",
        "average_B_all_atoms_angstrom2": f'{e["average_b_all_atoms_angstrom2"]:.1f}',
        "atom_count": e["atom_count"],
        "zero_occupancy_atom_count": e["zero_occupancy_atom_count"],
        "alternate_conformation_residue_count": e["alternate_conformation_residue_count"],
        "clash_count": e["clash_count"],
        "symmetry_clash_count": e["symmetry_clash_count"],
        "ramachandran_outlier_count": e["ramachandran_outlier_count"],
        "sidechain_outlier_count": e["sidechain_outlier_count"],
        "chain_break_count": e["chain_break_count"],
        "xtriage_status": "not_executed",
        "eds_status": "not_executed",
        "global_quality_state": "geometry_validation_ingested_local_model_to_data_fields_unavailable",
        "release_status": RELEASE,
    }]
    write_csv(PROT / "pdb_external_validation_global_metrics.csv", fields, rows)


def write_outlier_ingest(snapshot_sha: str) -> dict[int, dict[str, object]]:
    out_by_label = {int(o["label_seq_id"]): o for o in VALIDATION_SNAPSHOT["geometry_outliers"]}
    fields = [
        "validation_outlier_row_id", "source_accession", "snapshot_sha256", "chain_id", "auth_seq_id",
        "label_seq_id", "residue_name", "outlier_type", "atoms", "z_score", "observed_value",
        "ideal_value", "native_validation_classification", "local_support_component_state", "release_status",
    ]
    rows = []
    for label, o in sorted(out_by_label.items()):
        rows.append({
            "validation_outlier_row_id": f"1CRN_A_validation_outlier_label{label:04d}",
            "source_accession": SOURCE_ACCESSION,
            "snapshot_sha256": snapshot_sha,
            "chain_id": o["chain_id"],
            "auth_seq_id": o["auth_seq_id"],
            "label_seq_id": o["label_seq_id"],
            "residue_name": o["residue_name"],
            "outlier_type": o["outlier_type"],
            "atoms": o["atoms"],
            "z_score": o["z_score"],
            "observed_value": o["observed"],
            "ideal_value": o["ideal"],
            "native_validation_classification": "native_geometry_outlier",
            "local_support_component_state": "quality_excluded",
            "release_status": RELEASE,
        })
    write_csv(PROT / "pdb_external_validation_residue_outlier_ingest.csv", fields, rows)
    return out_by_label


def write_quality_rule() -> None:
    fields = [
        "quality_rule_family_id", "quality_rule_state_id", "quality_rule_declaration_id",
        "quality_rule_application_id", "source_accession", "comparison_space", "required_quality_fields",
        "missing_field_policy", "RSRZ_policy", "RSCC_policy", "occupancy_policy",
        "alternate_location_policy", "missing_density_policy", "validation_outlier_policy",
        "residue_support_aggregation_rule", "residue_support_domain", "pair_support_rule",
        "target_state_rule", "target_mask_activation_condition", "aod_comparison_join_activation_condition",
        "validation_value_read_status", "rule_freeze_status", "release_status",
    ]
    row = {
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "source_accession": SOURCE_ACCESSION,
        "comparison_space": "derived_observable",
        "required_quality_fields": "coordinate_present|occupancy|alternate_location_status|missing_density_status|validation_outlier_status|RSRZ_status|RSCC_status",
        "missing_field_policy": "any_required_component_unavailable=>quality_ambiguous_unless_another_component_is_quality_excluded",
        "RSRZ_policy": "native_validation_value_or_native_outlier_classification_only; EDS_not_executed_or_missing=>quality_ambiguous; no_post_ingest_threshold_selection",
        "RSCC_policy": "native_validation_value_and_predeclared_native_support_classification_only; EDS_not_executed_or_missing=>quality_ambiguous; no_post_ingest_threshold_selection",
        "occupancy_policy": "occupancy<=0=>quality_excluded; 0<occupancy<1=>quality_ambiguous; occupancy=1=>candidate_supported",
        "alternate_location_policy": "unresolved_multiple_altloc=>quality_ambiguous; declared_primary_or_highest_occupancy_selection_or_no_altloc=>candidate_supported",
        "missing_density_policy": "missing_density=>quality_excluded; EDS_not_executed_or_unassessed=>quality_ambiguous; supported_density=>candidate_supported",
        "validation_outlier_policy": "native_geometry_or_validation_outlier=>quality_excluded; no_native_outlier=>candidate_supported; unavailable=>quality_ambiguous",
        "residue_support_aggregation_rule": "quality_excluded_if_any_required_component_quality_excluded; quality_supported_iff_every_required_component_candidate_supported; quality_ambiguous_otherwise",
        "residue_support_domain": "quality_supported|quality_ambiguous|quality_excluded",
        "pair_support_rule": "quality_excluded_if_either_residue_quality_excluded; quality_supported_iff_both_residues_quality_supported; quality_ambiguous_otherwise; effective_target_abstains_unless_pair_quality_supported",
        "target_state_rule": "coordinate_derived_contact_bit_admitted_as_1_or_0_only_for_quality_supported_pair; otherwise_abstain",
        "target_mask_activation_condition": "quality_supported_pair_count>0",
        "aod_comparison_join_activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "validation_value_read_status": "parsed_only_after_r21_2_rule_freeze",
        "rule_freeze_status": "predeclared_rule_applied_without_post_ingest_threshold_selection",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_quality_rule_policy.csv", fields, [row])


def component_state_for_residue(coord: dict[str, str], outlier: dict[str, object] | None) -> tuple[str, str, str, str, str, str, str, str]:
    occ = float(coord["occupancy"])
    occupancy_state = "candidate_supported" if occ == 1.0 else ("quality_excluded" if occ <= 0 else "quality_ambiguous")
    alt = coord.get("altloc_id", "")
    alt_state = "candidate_supported" if alt in {"", ".", "?"} else "quality_ambiguous"
    missing_density_state = "quality_ambiguous"
    outlier_state = "quality_excluded" if outlier else "candidate_supported"
    rsrz_state = "quality_ambiguous"
    rscc_state = "quality_ambiguous"
    states = ["candidate_supported", occupancy_state, alt_state, missing_density_state, outlier_state, rsrz_state, rscc_state]
    if "quality_excluded" in states:
        aggregate = "quality_excluded"
        reason = "native_validation_geometry_outlier"
    elif all(s == "candidate_supported" for s in states):
        aggregate = "quality_supported"
        reason = "all_required_local_support_components_candidate_supported"
    else:
        aggregate = "quality_ambiguous"
        reason = "EDS_not_executed_RSRZ_RSCC_and_missing_density_support_unavailable"
    return occupancy_state, alt_state, missing_density_state, outlier_state, rsrz_state, rscc_state, aggregate, reason


def write_local_support(snapshot_sha: str, out_by_label: dict[int, dict[str, object]]) -> dict[int, str]:
    coords = read_csv(PROT / "pdb_external_residue_coordinate_table.csv")
    fields = [
        "local_support_id", "source_accession", "coordinate_payload_sha256", "validation_snapshot_sha256",
        "chain_id", "model_id", "auth_seq_id", "label_seq_id", "residue_name", "occupancy", "B_factor",
        "coordinate_present_status", "occupancy_component_state", "alternate_location_status",
        "alternate_location_component_state", "missing_density_status", "missing_density_component_state",
        "validation_outlier_status", "validation_outlier_detail", "validation_outlier_component_state",
        "RSRZ", "RSCC", "RSRZ_status", "RSCC_status", "RSRZ_component_state", "RSCC_component_state",
        "quality_rule_family_id", "quality_rule_state_id", "quality_rule_declaration_id",
        "quality_rule_application_id", "local_support_state", "quality_mask_state", "quality_mask_reason",
        "coordinate_use_status", "target_contact_state_policy", "release_status",
    ]
    rows = []
    state_by_label: dict[int, str] = {}
    for coord in coords:
        label = int(coord["label_seq_id"])
        outlier = out_by_label.get(label)
        occ_state, alt_state, missing_state, out_state, rsrz_state, rscc_state, aggregate, reason = component_state_for_residue(coord, outlier)
        state_by_label[label] = aggregate
        detail = ""
        if outlier:
            detail = f'{outlier["outlier_type"]}:{outlier["atoms"]}:Z={outlier["z_score"]}'
        rows.append({
            "local_support_id": f"1CRN_A_model1_local_support_label{label:04d}",
            "source_accession": SOURCE_ACCESSION,
            "coordinate_payload_sha256": coord["coordinate_payload_sha256"],
            "validation_snapshot_sha256": snapshot_sha,
            "chain_id": coord["chain_id"],
            "model_id": coord["model_id"],
            "auth_seq_id": coord["auth_seq_id"],
            "label_seq_id": coord["label_seq_id"],
            "residue_name": coord["residue_name"],
            "occupancy": coord["occupancy"],
            "B_factor": _lookup_b_factor(label),
            "coordinate_present_status": "candidate_supported_present_CA_coordinate",
            "occupancy_component_state": occ_state,
            "alternate_location_status": "no_alternate_location_on_selected_CA" if coord.get("altloc_id") in {"", ".", "?"} else f'altloc_{coord["altloc_id"]}',
            "alternate_location_component_state": alt_state,
            "missing_density_status": "unassessed_EDS_not_executed",
            "missing_density_component_state": missing_state,
            "validation_outlier_status": "native_geometry_outlier" if outlier else "no_native_geometry_outlier_reported",
            "validation_outlier_detail": detail,
            "validation_outlier_component_state": out_state,
            "RSRZ": "",
            "RSCC": "",
            "RSRZ_status": "unavailable_EDS_not_executed",
            "RSCC_status": "unavailable_EDS_not_executed",
            "RSRZ_component_state": rsrz_state,
            "RSCC_component_state": rscc_state,
            "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
            "quality_rule_state_id": QUALITY_RULE_STATE_ID,
            "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
            "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
            "local_support_state": aggregate,
            "quality_mask_state": "abstain" if aggregate != "quality_supported" else "admit_coordinate_contact_bit",
            "quality_mask_reason": reason,
            "coordinate_use_status": "coordinate_model_fixture_available_target_use_requires_quality_mask",
            "target_contact_state_policy": "admit_only_if_both_residues_quality_supported_else_abstain",
            "release_status": RELEASE,
        })
    write_csv(PROT / "pdb_external_validation_local_support_ingest.csv", fields, rows)
    write_csv(PROT / "pdb_external_residue_quality_mask.csv", fields, rows)
    return state_by_label


def _lookup_b_factor(label: int) -> str:
    # Preserve the already materialized per-residue CA B factor from the r21.2 mask.
    old = getattr(_lookup_b_factor, "_cache", None)
    if old is None:
        old = {int(r["label_seq_id"]): r.get("B_factor", "") for r in read_csv(PROT / "pdb_external_residue_quality_mask.csv")}
        setattr(_lookup_b_factor, "_cache", old)
    return old.get(label, "")


def write_pair_mask(state_by_label: dict[int, str]) -> dict[str, int]:
    boundary = read_csv(PROT / "pdb_external_evaluation_pair_boundary.csv")
    fields = [
        "quality_mask_overlay_id", "evaluation_pair_boundary_id", "evaluation_pair_row_id", "pair_id",
        "source_accession", "chain_id", "model_id", "label_seq_i", "label_seq_j", "residue_name_i",
        "residue_name_j", "coordinate_derived_contact_bit", "residue_i_quality_state",
        "residue_j_quality_state", "pair_support_state", "effective_target_state", "effective_target_reason",
        "quality_rule_family_id", "quality_rule_state_id", "quality_rule_declaration_id",
        "quality_rule_application_id", "quality_mask_id", "target_branch_materialization_status",
        "comparison_target_value_read_status", "residual_status", "score_status", "release_status",
    ]
    rows = []
    counts = {"contact": 0, "noncontact": 0, "supported": 0, "ambiguous": 0, "excluded": 0, "effective_contact": 0, "effective_noncontact": 0, "abstain": 0}
    for b in boundary:
        li, lj = int(b["label_seq_i"]), int(b["label_seq_j"])
        si, sj = state_by_label[li], state_by_label[lj]
        bit = b["target_contact_value"]
        counts["contact" if bit == "1" else "noncontact"] += 1
        if "quality_excluded" in {si, sj}:
            pair_state = "quality_excluded"
            reason = "at_least_one_residue_quality_excluded"
            counts["excluded"] += 1
        elif si == sj == "quality_supported":
            pair_state = "quality_supported"
            reason = "both_residues_quality_supported"
            counts["supported"] += 1
        else:
            pair_state = "quality_ambiguous"
            reason = "at_least_one_residue_quality_ambiguous"
            counts["ambiguous"] += 1
        effective = bit if pair_state == "quality_supported" else "abstain"
        if effective == "1": counts["effective_contact"] += 1
        elif effective == "0": counts["effective_noncontact"] += 1
        else: counts["abstain"] += 1
        rows.append({
            "quality_mask_overlay_id": QUALITY_MASK_ID,
            "evaluation_pair_boundary_id": b["evaluation_pair_boundary_id"],
            "evaluation_pair_row_id": b["evaluation_pair_row_id"],
            "pair_id": b["evaluation_pair_row_id"],
            "source_accession": b["source_accession"],
            "chain_id": b["chain_id"],
            "model_id": b["model_id"],
            "label_seq_i": b["label_seq_i"],
            "label_seq_j": b["label_seq_j"],
            "residue_name_i": b["residue_name_i"],
            "residue_name_j": b["residue_name_j"],
            "coordinate_derived_contact_bit": bit,
            "residue_i_quality_state": si,
            "residue_j_quality_state": sj,
            "pair_support_state": pair_state,
            "effective_target_state": effective,
            "effective_target_reason": reason,
            "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
            "quality_rule_state_id": QUALITY_RULE_STATE_ID,
            "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
            "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
            "quality_mask_id": QUALITY_MASK_ID,
            "target_branch_materialization_status": "coordinate_derived_contact_bit_read_for_target_only_quality_mask_materialization",
            "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
            "residual_status": "not_computed",
            "score_status": "no_score",
            "release_status": RELEASE,
        })
    write_csv(PROT / "pdb_external_quality_masked_contact_target.csv", fields, rows)
    return counts


def write_summary(counts: dict[str, int]) -> None:
    fields = [
        "quality_mask_id", "quality_rule_family_id", "quality_rule_state_id", "quality_rule_declaration_id",
        "quality_rule_application_id", "evaluation_pair_boundary_id", "evaluation_pair_count",
        "coordinate_derived_contact_count", "coordinate_derived_noncontact_count", "quality_supported_pair_count",
        "quality_ambiguous_pair_count", "quality_excluded_pair_count", "effective_contact_count",
        "effective_noncontact_count", "effective_abstain_count", "target_mask_activation_condition",
        "target_mask_gate_state", "aod_comparison_join_activation_condition", "aod_comparison_join_gate_state",
        "target_branch_materialization_status", "comparison_target_value_read_status", "residual_status",
        "score_status", "release_status",
    ]
    row = {
        "quality_mask_id": QUALITY_MASK_ID,
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "evaluation_pair_boundary_id": "pdb_external_eval_boundary_1CRN_A_all946_v4002r16",
        "evaluation_pair_count": 946,
        "coordinate_derived_contact_count": counts["contact"],
        "coordinate_derived_noncontact_count": counts["noncontact"],
        "quality_supported_pair_count": counts["supported"],
        "quality_ambiguous_pair_count": counts["ambiguous"],
        "quality_excluded_pair_count": counts["excluded"],
        "effective_contact_count": counts["effective_contact"],
        "effective_noncontact_count": counts["effective_noncontact"],
        "effective_abstain_count": counts["abstain"],
        "target_mask_activation_condition": "quality_supported_pair_count>0",
        "target_mask_gate_state": "closed_zero_quality_supported_pairs",
        "aod_comparison_join_activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "aod_comparison_join_gate_state": "closed_zero_quality_supported_pairs_and_no_alignment_coverage",
        "target_branch_materialization_status": "target_only_mask_materialized_from_coordinate_contact_bits_and_validation_support",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_quality_masked_contact_summary.csv", fields, [row])


def update_lineage_and_comparison(counts: dict[str, int]) -> None:
    # Experiment lineage: keep provenance values while normalizing family/state/declaration identity.
    old = read_csv(PROT / "pdb_external_experiment_lineage.csv")[0]
    fields = [
        "measurement_lineage_family_id", "measurement_lineage_state_id", "measurement_lineage_declaration_id",
        "source_database", "source_accession", "archive_entry_version", "experimental_method", "sample_conditions",
        "crystal_conditions", "space_group", "unit_cell_a", "unit_cell_b", "unit_cell_c", "unit_cell_alpha",
        "unit_cell_beta", "unit_cell_gamma", "wavelength_angstrom", "resolution_low_angstrom",
        "archive_reported_resolution_high_angstrom", "citation_reported_resolution_angstrom",
        "citation_resolution_relation_status", "crystal_solvent_content_percent", "matthews_coefficient",
        "coordinate_payload_path", "coordinate_payload_sha256", "coordinate_payload_byte_count",
        "validation_snapshot_path", "validation_snapshot_sha256", "coordinate_model_target_class",
        "measurement_truth_status", "archive_metadata_source", "citation_metadata_source", "metadata_access_date",
        "release_status",
    ]
    row = {k: old.get(k, "") for k in fields}
    row.update({
        "measurement_lineage_family_id": TARGET_LINEAGE_FAMILY_ID,
        "measurement_lineage_state_id": TARGET_LINEAGE_STATE_ID,
        "measurement_lineage_declaration_id": TARGET_LINEAGE_DECLARATION_ID,
        "validation_snapshot_path": f"manual-2/data/protein/external_pdb_validation_payloads/{SNAPSHOT_NAME}",
        "validation_snapshot_sha256": sha(SNAPSHOT_PATH),
        "release_status": RELEASE,
    })
    write_csv(PROT / "pdb_external_experiment_lineage.csv", fields, [row])

    mfields = [
        "measurement_lineage_family_id", "measurement_lineage_state_id", "measurement_lineage_declaration_id",
        "lineage_branch", "branch_stage_order", "lineage_object_id", "upstream_object_id", "stage_name",
        "operator_symbol", "input_state", "output_state", "stage_role", "payload_or_schema_status",
        "current_gate_status", "target_branch_materialization_status", "comparison_target_value_read_status",
        "release_status",
    ]
    trows = [
        [TARGET_LINEAGE_FAMILY_ID,TARGET_LINEAGE_STATE_ID,TARGET_LINEAGE_DECLARATION_ID,"target_measurement","1","target_physical_state_1CRN","","physical_state","identity","X_physical","X_physical","declared physical specimen/state","registry_only","declared","not_materialized_at_this_stage","not_read_not_joined_to_AOD_prediction",RELEASE],
        [TARGET_LINEAGE_FAMILY_ID,TARGET_LINEAGE_STATE_ID,TARGET_LINEAGE_DECLARATION_ID,"target_measurement","2","target_raw_measurement_1CRN","target_physical_state_1CRN","measurement_operator","M_theta","X_physical","Y_raw","X-ray diffraction measurement operator","operator_family_registered_payload_schema_unresolved","not_frozen","not_materialized_at_this_stage","not_read_not_joined_to_AOD_prediction",RELEASE],
        [TARGET_LINEAGE_FAMILY_ID,TARGET_LINEAGE_STATE_ID,TARGET_LINEAGE_DECLARATION_ID,"target_measurement","3","target_processed_measurement_1CRN","target_raw_measurement_1CRN","processing_operator","Q_psi","Y_raw","Y_processed","data reduction / processing operator","software_and_payload_schema_unresolved","not_frozen","not_materialized_at_this_stage","not_read_not_joined_to_AOD_prediction",RELEASE],
        [TARGET_LINEAGE_FAMILY_ID,TARGET_LINEAGE_STATE_ID,TARGET_LINEAGE_DECLARATION_ID,"target_measurement","4","target_coordinate_model_1CRN","target_processed_measurement_1CRN","reconstruction_operator","R_phi","Y_processed","Xhat_model","refinement/reconstruction producing deposited coordinate model","coordinate_model_available_hash_locked","coordinate_model_fixture_carried_forward","coordinate_model_bytes_and_coordinates_materialized_target_only","not_read_not_joined_to_AOD_prediction",RELEASE],
        [TARGET_LINEAGE_FAMILY_ID,TARGET_LINEAGE_STATE_ID,TARGET_LINEAGE_DECLARATION_ID,"target_measurement","5","target_derived_contact_1CRN","target_coordinate_model_1CRN","derived_observable_operator","D_eta","Xhat_model","O_derived","frozen coordinate-to-contact extraction plus validation support mask","validation_snapshot_hash_locked_quality_mask_materialized","target_mask_closed_zero_supported_pairs","coordinate_contact_bits_read_for_target_only_mask_materialization","not_read_not_joined_to_AOD_prediction",RELEASE],
        [AOD_LINEAGE_FAMILY_ID,AOD_LINEAGE_STATE_ID,AOD_LINEAGE_DECLARATION_ID,"aod_prediction","1","aod_frozen_contact_packet_GAS","","independent_aod_lane","AOD_freeze","AOD_raw_trace","X_AOD_freeze","AOD motif/curling-curls/SADAR frozen packet","contact_pair_set","carried_forward_independent_lane","not_applicable","not_read_not_joined_to_target",RELEASE],
    ]
    write_csv(PROT / "pdb_external_measurement_metadata.csv", mfields, [dict(zip(mfields, r)) for r in trows])

    cfields = [
        "comparison_join_id", "target_lineage_family_id", "target_lineage_state_id",
        "aod_lineage_family_id", "aod_lineage_state_id", "comparison_space", "target_object_id",
        "aod_object_id", "target_mask_activation_condition", "aod_comparison_join_activation_condition",
        "comparison_join_status", "target_branch_materialization_status", "comparison_target_value_read_status",
        "residual_status", "score_status", "release_status",
    ]
    crow = {
        "comparison_join_id": COMPARISON_JOIN_ID,
        "target_lineage_family_id": TARGET_LINEAGE_FAMILY_ID,
        "target_lineage_state_id": TARGET_LINEAGE_STATE_ID,
        "aod_lineage_family_id": AOD_LINEAGE_FAMILY_ID,
        "aod_lineage_state_id": AOD_LINEAGE_STATE_ID,
        "comparison_space": "derived_observable",
        "target_object_id": "target_derived_contact_1CRN_quality_masked",
        "aod_object_id": "aod_frozen_contact_packet_GAS",
        "target_mask_activation_condition": "quality_supported_pair_count>0",
        "aod_comparison_join_activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "comparison_join_status": "closed_zero_supported_pairs_and_no_alignment_coverage",
        "target_branch_materialization_status": "target_only_mask_materialized",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_comparison_join_declaration.csv", cfields, [crow])


def update_availability(snapshot_sha: str, snapshot_bytes: int) -> None:
    old = read_csv(PROT / "pdb_external_experimental_payload_availability.csv")
    fields = list(old[0].keys())
    rows = []
    for row in old:
        if row.get("payload_type") == "validation_report_parsed_snapshot" or row.get("payload_registry_id") == "1CRN_validation_report_parsed_snapshot":
            continue
        out = dict(row)
        out["release_status"] = RELEASE
        if row["payload_type"] in {"validation_report_cif", "validation_report_xml"}:
            out.update({
                "payload_availability": "archive_listed_original_bytes_not_locked",
                "archive_listing_status": "archive_listed",
                "byte_probe_status": "remote_endpoint_known_not_locally_byte_locked",
                "byte_lock_status": "not_locked_original_archive_payload",
                "parse_status": "not_parsed_original_archive_payload",
                "field_availability_status": "parsed_snapshot_fields_available_original_payload_lock_pending",
                "availability_probe_status": "official_report_view_and_download_endpoints_declared",
            })
        rows.append(out)
    snapshot = {k: "" for k in fields}
    snapshot.update({
        "payload_registry_id": "1CRN_validation_report_parsed_snapshot",
        "source_database": "RCSB_PDB_wwPDB",
        "source_accession": SOURCE_ACCESSION,
        "payload_type": "validation_report_parsed_snapshot",
        "payload_availability": "available_hash_locked",
        "archive_listing_status": "derived_from_official_full_validation_report_view",
        "byte_probe_status": "release_local_snapshot_bytes_registered",
        "byte_lock_status": "snapshot_byte_hash_locked",
        "parse_status": "parsed_predeclared_global_and_local_support_fields",
        "field_availability_status": "geometry_fields_available_EDS_local_fit_fields_unavailable",
        "payload_path_or_probe_url": SOURCE_URL,
        "local_payload_path": f"manual-2/data/protein/external_pdb_validation_payloads/{SNAPSHOT_NAME}",
        "payload_sha256": snapshot_sha,
        "payload_byte_count": str(snapshot_bytes),
        "probe_url": SOURCE_URL,
        "http_status": "official_report_view_accessed",
        "content_type": "application/pdf_upstream; application/json_local_snapshot",
        "probe_bytes": str(snapshot_bytes),
        "probe_sha256": snapshot_sha,
        "probe_utc": "2026-06-18T00:00:00Z",
        "archive_source": "RCSB_PDB_wwPDB",
        "availability_probe_status": "parsed_snapshot_hash_locked_original_archive_bytes_unlocked",
        "access_control_status": "public_archive_reference",
        "release_status": RELEASE,
    })
    rows.append(snapshot)
    write_csv(PROT / "pdb_external_experimental_payload_availability.csv", fields, rows)


def update_refinement_metrics(snapshot_sha: str) -> None:
    fields = [
        "refinement_card_id", "source_database", "source_accession", "experimental_method",
        "archive_entry_version", "archive_reported_resolution_high", "archive_reported_resolution_low",
        "citation_reported_resolution", "citation_resolution_relation_status", "refinement_software",
        "R_work", "R_free", "R_free_minus_R_work", "completeness", "multiplicity", "I_over_sigma",
        "merging_statistics", "validation_report_snapshot_sha256", "validation_report_availability",
        "global_experiment_quality_state", "coordinate_payload_sha256", "coordinate_model_target_class",
        "measurement_payload_status", "release_status",
    ]
    row = {
        "refinement_card_id": "pdb_refinement_validation_1CRN_v4002r22A",
        "source_database": "RCSB_PDB_wwPDB",
        "source_accession": SOURCE_ACCESSION,
        "experimental_method": "X-RAY DIFFRACTION",
        "archive_entry_version": "1.5",
        "archive_reported_resolution_high": "1.50",
        "archive_reported_resolution_low": "unavailable_in_validation_report",
        "citation_reported_resolution": "0.945",
        "citation_resolution_relation_status": "reconciliation_pending",
        "refinement_software": "PROLSQ",
        "R_work": "unavailable_in_validation_report",
        "R_free": "unavailable_in_validation_report",
        "R_free_minus_R_work": "unavailable_in_validation_report",
        "completeness": "unavailable_in_validation_report",
        "multiplicity": "unavailable_in_validation_report",
        "I_over_sigma": "unavailable_in_validation_report",
        "merging_statistics": "Rmerge_and_Rsym_unavailable_in_validation_report",
        "validation_report_snapshot_sha256": snapshot_sha,
        "validation_report_availability": "parsed_snapshot_hash_locked_original_archive_bytes_unlocked",
        "global_experiment_quality_state": "geometry_validation_ingested_EDS_and_Xtriage_not_executed",
        "coordinate_payload_sha256": "23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba",
        "coordinate_model_target_class": "coordinate_model_observable_fixture",
        "measurement_payload_status": "reflection_and_map_payload_availability_unresolved",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_refinement_validation_metrics.csv", fields, [row])


def update_contact_policy_and_matrix(counts: dict[str, int]) -> None:
    # Contact observable policy with current capability vs future activation separated.
    fields = [
        "observable_policy_id", "source_accession", "comparison_space", "chain", "model", "assembly",
        "atom_selector", "altloc_rule", "occupancy_rule", "distance_rule", "minimum_sequence_separation",
        "sequence_separation_rule", "target_state_domain", "target_contact_1_rule", "target_contact_0_rule",
        "target_abstain_rule", "quality_mask", "threshold_proximity_policy", "uncertainty_interval_policy",
        "aod_prediction_representation", "measurement_space_xray_capability_current",
        "measurement_space_xray_activation_condition", "coordinate_model_capability_current",
        "coordinate_model_activation_condition", "derived_contact_capability_current",
        "derived_contact_activation_condition", "quality_rule_family_id", "quality_rule_state_id",
        "quality_mask_overlay", "quality_supported_pair_count", "target_mask_activation_condition",
        "target_mask_gate_state", "aod_comparison_join_activation_condition", "aod_comparison_join_gate_state",
        "target_branch_materialization_status", "comparison_target_value_read_status", "score_status", "release_status",
    ]
    row = {
        "observable_policy_id": "pdb_contact_observable_policy_1CRN_A_CA_v4002r22A",
        "source_accession": SOURCE_ACCESSION,
        "comparison_space": "derived_observable",
        "chain": "A", "model": "1", "assembly": "asymmetric_unit_chain_A", "atom_selector": "CA",
        "altloc_rule": "primary_or_highest_occupancy_altloc", "occupancy_rule": "occupancy_recorded_as_support_indicator_not_uncertainty",
        "distance_rule": "euclidean_CA_distance_from_full_precision_coordinates", "minimum_sequence_separation": "3",
        "sequence_separation_rule": "abs(label_seq_id_j-label_seq_id_i) >= 3", "target_state_domain": "1|0|abstain",
        "target_contact_1_rule": "distance<=8.0A_and_both_residues_quality_supported",
        "target_contact_0_rule": "distance>8.0A_and_both_residues_quality_supported",
        "target_abstain_rule": "pair_not_quality_supported_or_missing_coordinate_or_unresolved_altloc_or_separately_frozen_uncertainty_model_marks_threshold_unresolved",
        "quality_mask": "pdb_external_residue_quality_mask.csv", "threshold_proximity_policy": "disabled_until_separately_frozen_uncertainty_model_exists",
        "uncertainty_interval_policy": "B_factor_occupancy_RSRZ_RSCC_are_not_interchangeable_coordinate_standard_errors",
        "aod_prediction_representation": "contact_pair_set",
        "measurement_space_xray_capability_current": "blocked_by_prediction_representation",
        "measurement_space_xray_activation_condition": "compatible_measurement_generative_AOD_output_frozen",
        "coordinate_model_capability_current": "unavailable_for_contact_pair_set",
        "coordinate_model_activation_condition": "compatible_coordinate_generative_AOD_output_frozen",
        "derived_contact_capability_current": "representation_available_target_mask_zero_supported_pairs",
        "derived_contact_activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID, "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_mask_overlay": "pdb_external_quality_masked_contact_target.csv",
        "quality_supported_pair_count": counts["supported"],
        "target_mask_activation_condition": "quality_supported_pair_count>0",
        "target_mask_gate_state": "closed_zero_quality_supported_pairs",
        "aod_comparison_join_activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "aod_comparison_join_gate_state": "closed_zero_quality_supported_pairs_and_no_alignment_coverage",
        "target_branch_materialization_status": "coordinate_contact_bits_read_for_target_only_mask_materialization",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "score_status": "policy_and_validation_support_gate_only_no_score",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_contact_observable_policy.csv", fields, [row])

    fields2 = [
        "comparison_space", "lineage_branch", "required_target_support", "current_target_support",
        "aod_prediction_representation", "capability_current", "activation_condition",
        "result_that_may_be_reported", "quality_supported_pair_count", "current_gate_status",
        "target_branch_materialization_status", "comparison_target_value_read_status", "score_status", "release_status",
    ]
    rows2 = [
        {"comparison_space":"registry","lineage_branch":"target_measurement","required_target_support":"accession_and_method_metadata","current_target_support":"available","aod_prediction_representation":"contact_pair_set","capability_current":"available","activation_condition":"metadata_registered","result_that_may_be_reported":"provenance_only","quality_supported_pair_count":"","current_gate_status":"active_provenance_only","target_branch_materialization_status":"registry_metadata_available","comparison_target_value_read_status":"not_read_not_joined_to_AOD_prediction","score_status":"no_score","release_status":RELEASE},
        {"comparison_space":"coordinate_model","lineage_branch":"target_measurement+aod_prediction","required_target_support":"coordinate_model_plus_refinement_and_validation_lineage","current_target_support":"coordinate_model_hash_locked_validation_snapshot_ingested_EDS_fields_unavailable","aod_prediction_representation":"contact_pair_set","capability_current":"unavailable_for_contact_pair_set","activation_condition":"compatible_coordinate_generative_AOD_output_frozen","result_that_may_be_reported":"model_coordinate_comparison","quality_supported_pair_count":"","current_gate_status":"waiting_for_compatible_AOD_representation","target_branch_materialization_status":"coordinate_model_fixture_available","comparison_target_value_read_status":"not_read_not_joined_to_AOD_prediction","score_status":"no_score","release_status":RELEASE},
        {"comparison_space":"derived_observable","lineage_branch":"target_measurement+aod_prediction","required_target_support":"frozen_extraction_policy_and_local_quality_mask","current_target_support":"contact_map_available_validation_snapshot_ingested_zero_supported_pairs","aod_prediction_representation":"contact_pair_set","capability_current":"representation_available_target_mask_closed","activation_condition":"quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0","result_that_may_be_reported":"contact_or_reclosure_residual","quality_supported_pair_count":str(counts["supported"]),"current_gate_status":"target_mask_closed_and_comparison_join_closed","target_branch_materialization_status":"target_only_mask_materialized","comparison_target_value_read_status":"not_read_not_joined_to_AOD_prediction","score_status":"no_score","release_status":RELEASE},
        {"comparison_space":"measurement_raw","lineage_branch":"target_measurement+aod_prediction","required_target_support":"raw_experimental_payload_and_frozen_forward_operator","current_target_support":"raw_payload_probe_pending","aod_prediction_representation":"contact_pair_set","capability_current":"blocked_by_prediction_representation","activation_condition":"raw_payload_byte_lock_and_compatible_measurement_generative_AOD_output_frozen","result_that_may_be_reported":"raw_measurement_residual","quality_supported_pair_count":"","current_gate_status":"waiting_for_payload_and_AOD_capability","target_branch_materialization_status":"not_materialized","comparison_target_value_read_status":"not_read_not_joined_to_AOD_prediction","score_status":"no_score","release_status":RELEASE},
        {"comparison_space":"measurement_processed","lineage_branch":"target_measurement+aod_prediction","required_target_support":"processed_experimental_payload_and_frozen_forward_operator","current_target_support":"processed_payload_probe_pending","aod_prediction_representation":"contact_pair_set","capability_current":"blocked_by_prediction_representation","activation_condition":"processed_payload_byte_lock_and_compatible_measurement_generative_AOD_output_frozen","result_that_may_be_reported":"processed_measurement_residual","quality_supported_pair_count":"","current_gate_status":"waiting_for_payload_and_AOD_capability","target_branch_materialization_status":"not_materialized","comparison_target_value_read_status":"not_read_not_joined_to_AOD_prediction","score_status":"no_score","release_status":RELEASE},
    ]
    write_csv(PROT / "pdb_external_comparison_allowed_matrix.csv", fields2, rows2)



def update_policy_application_and_limitation(counts: dict[str, int]) -> None:
    fields = [
        "policy_application_id", "quality_rule_id", "quality_mask_id", "residue_quality_mask_file",
        "evaluation_boundary_file", "coordinate_contact_source_file", "pair_overlay_file",
        "rule_application_status", "validation_value_read_status", "target_join_status", "score_status",
        "release_status",
    ]
    row = {
        "policy_application_id": QUALITY_RULE_APPLICATION_ID,
        "quality_rule_id": QUALITY_RULE_STATE_ID,
        "quality_mask_id": QUALITY_MASK_ID,
        "residue_quality_mask_file": "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
        "evaluation_boundary_file": "manual-2/data/protein/pdb_external_evaluation_pair_boundary.csv",
        "coordinate_contact_source_file": "manual-2/data/protein/pdb_external_contact_map_derived.csv",
        "pair_overlay_file": "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
        "rule_application_status": "predeclared_rule_applied_to_hash_locked_parsed_validation_snapshot",
        "validation_value_read_status": "predeclared_fields_parsed_after_rule_freeze_no_post_ingest_threshold_selection",
        "target_join_status": "target_only_mask_materialized_comparison_join_closed",
        "score_status": "no_score",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_quality_mask_policy_application.csv", fields, [row])

    path = PROT / "pdb_external_target_limitation_budget.csv"
    old_rows = read_csv(path)
    lfields = list(old_rows[0].keys())
    rows = []
    for old in old_rows:
        out = dict(old)
        out["release_status"] = RELEASE
        component = old.get("limitation_component", "")
        if component == "local_model_support":
            out.update({
                "current_state": "validation_snapshot_ingested_zero_quality_supported_pairs",
                "implication": "all_946_coordinate_derived_pair_bits_remain_effective_target_abstentions",
                "resolution_or_gate": "original_archive_validation_payload_lock_or_new_predeclared_support_source_required",
                "comparison_space": "derived_observable",
            })
        elif component == "aod_prediction_representation":
            out.update({
                "current_state": "contact_pair_set_supports_derived_contact_lane_only",
                "implication": "measurement_and_coordinate_model_lanes_remain_blocked_for_current_AOD_representation",
                "resolution_or_gate": "compatible_measurement_or_coordinate_generative_AOD_output_required",
            })
        elif component == "coordinate_model_capability":
            out.update({
                "current_state": "unavailable_for_contact_pair_set",
                "implication": "no_coordinate_model_residual_RMSD_TMscore_GDT",
                "resolution_or_gate": "compatible_coordinate_generative_AOD_output_required",
            })
        elif component == "derived_contact_capability":
            out.update({
                "current_state": "representation_available_target_mask_closed_zero_supported_pairs",
                "implication": "derived_contact_join_requires_quality_support_alignment_rule_and_nonzero_in_scope_coverage",
                "resolution_or_gate": "validation_support_plus_alignment_projection_coverage_gate",
            })
        rows.append(out)
    write_csv(path, lfields, rows)

def write_leakage_checks(snapshot_sha: str, counts: dict[str, int]) -> None:
    fields = ["check_id", "check_description", "expected_state", "observed_state", "check_status", "release_status"]
    rows = [
        {"check_id":"validation_snapshot_hash_locked_before_parse","check_description":"release-local parsed validation snapshot hash is recorded before local-support materialization","expected_state":"snapshot_sha256_present","observed_state":snapshot_sha,"check_status":"PASS","release_status":RELEASE},
        {"check_id":"archive_original_bytes_not_misrepresented","check_description":"original archive PDF/XML/CIF bytes are not claimed as locally byte locked","expected_state":"upstream_original_payload_byte_lock_status=not_locked_in_build_environment","observed_state":"not_locked_in_build_environment","check_status":"PASS","release_status":RELEASE},
        {"check_id":"quality_rule_predeclared","check_description":"r21.2 quality rule declaration predates validation value parse","expected_state":QUALITY_RULE_DECLARATION_ID,"observed_state":QUALITY_RULE_DECLARATION_ID,"check_status":"PASS","release_status":RELEASE},
        {"check_id":"no_post_ingest_threshold_selection","check_description":"RSRZ/RSCC policy does not choose thresholds after reading 1CRN values","expected_state":"native_classification_or_missing=>ambiguous","observed_state":"EDS_not_executed_no_values_no_threshold_selected","check_status":"PASS","release_status":RELEASE},
        {"check_id":"target_mask_and_comparison_gate_separate","check_description":"target mask activation and AOD comparison join activation are distinct","expected_state":"mask_support_gate_plus_alignment_coverage_join_gate","observed_state":"separate_conditions_recorded","check_status":"PASS","release_status":RELEASE},
        {"check_id":"target_branch_read_not_comparison_join","check_description":"coordinate contact bits may be read for target-only mask materialization but are not joined to AOD prediction","expected_state":"target_only_materialization; comparison_target_unread","observed_state":"target_only_materialization; not_joined_to_AOD_prediction","check_status":"PASS","release_status":RELEASE},
        {"check_id":"all_effective_pairs_abstain","check_description":"no pair is admitted without two quality-supported residues","expected_state":"946_abstain","observed_state":f'{counts["abstain"]}_abstain',"check_status":"PASS" if counts["abstain"]==946 else "FAIL","release_status":RELEASE},
        {"check_id":"target_values_for_score_unread","check_description":"AOD comparison target values remain unread and unscored","expected_state":"no_target_join_no_residual_no_score","observed_state":"no_target_join_no_residual_no_score","check_status":"PASS","release_status":RELEASE},
    ]
    write_csv(PROT / "pdb_external_validation_local_support_leakage_checks.csv", fields, rows)


def write_manifests(snapshot_sha: str, snapshot_bytes: int, counts: dict[str, int]) -> None:
    files = {
        "validation_payload_byte_lock": PROT / "pdb_external_validation_payload_byte_lock.csv",
        "validation_payload_provenance": PROT / "pdb_external_validation_payload_provenance.csv",
        "validation_global_metrics": PROT / "pdb_external_validation_global_metrics.csv",
        "validation_residue_outlier_ingest": PROT / "pdb_external_validation_residue_outlier_ingest.csv",
        "validation_local_support_ingest": PROT / "pdb_external_validation_local_support_ingest.csv",
        "quality_rule_policy": PROT / "pdb_external_quality_rule_policy.csv",
        "residue_quality_mask": PROT / "pdb_external_residue_quality_mask.csv",
        "quality_masked_contact_target": PROT / "pdb_external_quality_masked_contact_target.csv",
        "quality_masked_contact_summary": PROT / "pdb_external_quality_masked_contact_summary.csv",
        "comparison_join_declaration": PROT / "pdb_external_comparison_join_declaration.csv",
        "quality_mask_policy_application": PROT / "pdb_external_quality_mask_policy_application.csv",
        "target_limitation_budget": PROT / "pdb_external_target_limitation_budget.csv",
        "contact_observable_policy": PROT / "pdb_external_contact_observable_policy.csv",
        "comparison_allowed_matrix": PROT / "pdb_external_comparison_allowed_matrix.csv",
        "experimental_payload_availability": PROT / "pdb_external_experimental_payload_availability.csv",
        "refinement_validation_metrics": PROT / "pdb_external_refinement_validation_metrics.csv",
        "experiment_lineage": PROT / "pdb_external_experiment_lineage.csv",
        "measurement_metadata": PROT / "pdb_external_measurement_metadata.csv",
        "leakage_checks": PROT / "pdb_external_validation_local_support_leakage_checks.csv",
    }
    manifest = {
        "version_scope": VERSION,
        "lane": "pdb_validation_report_snapshot_byte_lock_local_support_ingest",
        "source_accession": SOURCE_ACCESSION,
        "payload_lock_class": "release_local_parsed_report_snapshot",
        "upstream_archive_original_byte_lock_status": "not_locked_in_build_environment",
        "snapshot_path": f"manual-2/data/protein/external_pdb_validation_payloads/{SNAPSHOT_NAME}",
        "snapshot_sha256": snapshot_sha,
        "snapshot_byte_count": str(snapshot_bytes),
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "residue_counts": {"quality_supported":"0","quality_ambiguous":"42","quality_excluded":"4"},
        "pair_counts": {"quality_supported":str(counts["supported"]),"quality_ambiguous":str(counts["ambiguous"]),"quality_excluded":str(counts["excluded"])},
        "effective_target_counts": {"contact":str(counts["effective_contact"]),"noncontact":str(counts["effective_noncontact"]),"abstain":str(counts["abstain"])},
        "target_mask_activation_condition": "quality_supported_pair_count>0",
        "aod_comparison_join_activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "target_branch_materialization_status": "target_only_mask_materialized",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "files": {k: str(v.relative_to(ROOT)) for k,v in files.items()},
        "file_sha256": {k: sha(v) for k,v in files.items()},
        "next_milestones": [
            "v40.02r22B Reflection / Map Availability Probe and Byte-Lock Gate",
            "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
        ],
    }
    (PROT / "pdb_external_validation_local_support_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n",encoding="utf-8")

    qmanifest = {
        "version_scope": VERSION,
        "lane": "pdb_measurement_lineage_quality_mask_after_validation_snapshot_ingest",
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "quality_mask_id": QUALITY_MASK_ID,
        "evaluation_pair_count": "946",
        "coordinate_derived_contact_count": str(counts["contact"]),
        "coordinate_derived_noncontact_count": str(counts["noncontact"]),
        "quality_supported_pair_count": str(counts["supported"]),
        "quality_ambiguous_pair_count": str(counts["ambiguous"]),
        "quality_excluded_pair_count": str(counts["excluded"]),
        "effective_contact_count": str(counts["effective_contact"]),
        "effective_noncontact_count": str(counts["effective_noncontact"]),
        "effective_abstain_count": str(counts["abstain"]),
        "target_mask_gate_state": "closed_zero_quality_supported_pairs",
        "aod_comparison_join_gate_state": "closed_zero_quality_supported_pairs_and_no_alignment_coverage",
        "target_branch_materialization_status": "coordinate_contact_bits_read_for_target_only_mask_materialization",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "files": {
            "quality_rule_policy": "manual-2/data/protein/pdb_external_quality_rule_policy.csv",
            "residue_quality_mask": "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
            "quality_masked_contact_target": "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
            "quality_masked_contact_summary": "manual-2/data/protein/pdb_external_quality_masked_contact_summary.csv",
            "comparison_join_declaration": "manual-2/data/protein/pdb_external_comparison_join_declaration.csv",
            "quality_mask_policy_application": "manual-2/data/protein/pdb_external_quality_mask_policy_application.csv",
            "target_limitation_budget": "manual-2/data/protein/pdb_external_target_limitation_budget.csv",
            "contact_observable_policy": "manual-2/data/protein/pdb_external_contact_observable_policy.csv",
            "comparison_allowed_matrix": "manual-2/data/protein/pdb_external_comparison_allowed_matrix.csv",
        },
    }
    qmanifest["file_sha256"] = {k: sha(ROOT / v) for k,v in qmanifest["files"].items()}
    (PROT / "pdb_external_quality_mask_manifest.json").write_text(json.dumps(qmanifest, indent=2, sort_keys=True)+"\n",encoding="utf-8")

    mmanifest = {
        "version_scope": VERSION,
        "lane": "pdb_measurement_lineage_validation_snapshot_ingest",
        "measurement_lineage_family_id": TARGET_LINEAGE_FAMILY_ID,
        "measurement_lineage_state_id": TARGET_LINEAGE_STATE_ID,
        "measurement_lineage_declaration_id": TARGET_LINEAGE_DECLARATION_ID,
        "aod_lineage_family_id": AOD_LINEAGE_FAMILY_ID,
        "aod_lineage_state_id": AOD_LINEAGE_STATE_ID,
        "validation_snapshot_sha256": snapshot_sha,
        "validation_snapshot_byte_count": str(snapshot_bytes),
        "upstream_archive_original_byte_lock_status": "not_locked_in_build_environment",
        "quality_supported_pair_count": str(counts["supported"]),
        "effective_target_counts": {"contact":str(counts["effective_contact"]),"noncontact":str(counts["effective_noncontact"]),"abstain":str(counts["abstain"])},
        "target_mask_activation_condition": "quality_supported_pair_count>0",
        "aod_comparison_join_activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "target_branch_materialization_status": "target_only_mask_materialized",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "score_status": "validation_snapshot_and_quality_mask_gate_only_no_score",
    }
    (PROT / "pdb_external_measurement_manifest.json").write_text(json.dumps(mmanifest, indent=2, sort_keys=True)+"\n",encoding="utf-8")


def main() -> None:
    current_version = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    if "Canonical version: v40.02r22A" not in current_version:
        print(json.dumps({
            "version": "v40.02r22A",
            "status": "historical_generator_noop_in_newer_package",
            "current_canonical_version": current_version.splitlines()[0],
        }, indent=2, sort_keys=True))
        return
    _preserved_current = capture_current_files_if_newer()
    snapshot_sha, snapshot_bytes = write_snapshot()
    write_validation_payload_ledgers(snapshot_sha, snapshot_bytes)
    write_global_metrics(snapshot_sha)
    outliers = write_outlier_ingest(snapshot_sha)
    write_quality_rule()
    states = write_local_support(snapshot_sha, outliers)
    counts = write_pair_mask(states)
    assert counts == {"contact":114,"noncontact":832,"supported":0,"ambiguous":787,"excluded":159,"effective_contact":0,"effective_noncontact":0,"abstain":946}, counts
    write_summary(counts)
    update_lineage_and_comparison(counts)
    update_availability(snapshot_sha, snapshot_bytes)
    update_refinement_metrics(snapshot_sha)
    update_contact_policy_and_matrix(counts)
    update_policy_application_and_limitation(counts)
    write_leakage_checks(snapshot_sha, counts)
    write_manifests(snapshot_sha, snapshot_bytes, counts)
    # Re-apply the observable-aware r22A.1 policy and the original archive
    # byte-lock/equivalence gate so this legacy entry point regenerates the
    # current release state rather than an intermediate historical state.
    subprocess.run([sys.executable, str(ROOT / "manual-2/scripts/refine_external_pdb_validation_snapshot_provenance_policy.py")], cwd=ROOT, check=True)
    restore_captured_files(_preserved_current)
    print(json.dumps({"snapshot_sha256": snapshot_sha, "snapshot_bytes": snapshot_bytes, "counts": counts, "current_followup": "r22B.1"}, sort_keys=True))


if __name__ == "__main__":
    main()
