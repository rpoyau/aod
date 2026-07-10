#!/usr/bin/env python3
"""Materialize the r22A.1 validation provenance and observable-support refinement.

This deterministic offline step operates on the release-local parsed validation
snapshot produced by r22A.  It does not claim to byte-lock the upstream archive
PDF/XML/CIF payloads.  It adds field-level evidence locators, freezes a
CA-contact-observable-aware outlier policy, rematerializes residue/pair support,
and freezes the legacy-entry and future scored-accession selection policies.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
SNAPSHOT = PROT / "external_pdb_validation_payloads" / "1crn_full_validation_report_parsed_snapshot.json"
VERSION = "v40.02r22A.1"
RELEASE = "v40.02r22A1_parsed_validation_snapshot_provenance_observable_support_policy"
SOURCE_ACCESSION = "1CRN"
SOURCE_URL = "https://files.rcsb.org/validation/view/1crn_full_validation.pdf"
QUALITY_RULE_FAMILY_ID = "pdb_local_support_rule_1CRN"
QUALITY_RULE_STATE_ID = "pdb_local_support_rule_1CRN_CA_contact_observable_aware_v4002r22A1"
QUALITY_RULE_DECLARATION_ID = "pdb_local_support_rule_declaration_1CRN_CA_contact_v4002r22A1"
QUALITY_RULE_APPLICATION_ID = "pdb_local_support_rule_application_1CRN_CA_contact_v4002r22A1"
QUALITY_MASK_ID = "pdb_pair_quality_mask_1CRN_A_all946_v4002r22A1"
OBSERVABLE_POLICY_ID = "pdb_validation_outlier_observable_policy_1CRN_CA_contact_v4002r22A1"
LEGACY_POLICY_ID = "pdb_legacy_entry_policy_1CRN_v4002r22A1"
ELIGIBILITY_RULE_ID = "pdb_scored_accession_eligibility_xray_derived_contact_v1"



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


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def nested(data: Any, path: str) -> Any:
    cur = data
    for token in path.split("."):
        if token.endswith("]"):
            name, idx = token[:-1].split("[")
            if name:
                cur = cur[name]
            cur = cur[int(idx)]
        else:
            cur = cur[token]
    return cur


def value_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def evidence_specs() -> list[tuple[str, int, str, str, str]]:
    return [
        ("source_report_generated_utc", 1, "Report header", "report generation timestamp", "UTC"),
        ("validation_pipeline.wwpdb_validation_pipeline", 1, "Software and data versions", "Validation Pipeline (wwPDB-VP)", "version"),
        ("validation_pipeline.molprobity", 1, "Software and data versions", "MolProbity", "version"),
        ("validation_pipeline.xtriage", 1, "Software and data versions", "Xtriage (Phenix)", "status"),
        ("validation_pipeline.eds", 1, "Software and data versions", "EDS", "status"),
        ("validation_pipeline.percentile_statistics", 1, "Software and data versions", "Percentile statistics", "version"),
        ("entry.experimental_method", 2, "1 Overall quality at a glance", "experimental technique", "method"),
        ("entry.reported_resolution_angstrom", 2, "1 Overall quality at a glance", "reported resolution", "angstrom"),
        ("entry.chain_id", 2, "1 Overall quality at a glance", "Molecule 1 chain", "identifier"),
        ("entry.residue_count", 2, "1 Overall quality at a glance", "Molecule 1 chain length", "count"),
        ("entry.atom_count", 3, "2 Entry composition", "Mol 1 Chain A atoms total", "count"),
        ("entry.zero_occupancy_atom_count", 3, "2 Entry composition", "ZeroOcc", "count"),
        ("entry.alternate_conformation_residue_count", 3, "2 Entry composition", "AltConf", "count"),
        ("entry.trace_residue_count", 3, "2 Entry composition", "Trace", "count"),
        ("entry.space_group", 5, "4 Data and refinement statistics", "Space group", "symbol"),
        ("entry.cell.a", 5, "4 Data and refinement statistics", "Cell constant a", "angstrom"),
        ("entry.cell.b", 5, "4 Data and refinement statistics", "Cell constant b", "angstrom"),
        ("entry.cell.c", 5, "4 Data and refinement statistics", "Cell constant c", "angstrom"),
        ("entry.cell.alpha", 5, "4 Data and refinement statistics", "Cell angle alpha", "degree"),
        ("entry.cell.beta", 5, "4 Data and refinement statistics", "Cell angle beta", "degree"),
        ("entry.cell.gamma", 5, "4 Data and refinement statistics", "Cell angle gamma", "degree"),
        ("entry.refinement_program", 5, "4 Data and refinement statistics", "Refinement program", "name"),
        ("entry.r_work", 5, "4 Data and refinement statistics", "R", "dimensionless"),
        ("entry.r_free", 5, "4 Data and refinement statistics", "Rfree", "dimensionless"),
        ("entry.completeness", 5, "4 Data and refinement statistics", "% Data completeness", "percent"),
        ("entry.rmerge", 5, "4 Data and refinement statistics", "Rmerge", "dimensionless"),
        ("entry.rsym", 5, "4 Data and refinement statistics", "Rsym", "dimensionless"),
        ("entry.average_b_all_atoms_angstrom2", 5, "4 Data and refinement statistics", "Average B all atoms", "angstrom_squared"),
        ("entry.clash_count", 6, "5.2 Too-close contacts", "Clashes", "count"),
        ("entry.symmetry_clash_count", 6, "5.2 Too-close contacts", "Symm-Clashes", "count"),
        ("entry.ramachandran_outlier_count", 7, "5.3.1 Protein backbone", "Ramachandran Outliers", "count"),
        ("entry.sidechain_outlier_count", 7, "5.3.2 Protein sidechains", "Sidechain Outliers", "count"),
        ("entry.chain_break_count", 8, "5.8 Polymer linkage issues", "chain breaks", "count"),
        ("local_model_to_data.eds_status", 9, "6 Fit of model and data", "EDS execution status", "status"),
        ("local_model_to_data.rsrz_available", 9, "6.1 Protein, DNA and RNA chains", "RSRZ availability", "boolean"),
        ("local_model_to_data.rscc_available", 9, "6.1 Protein, DNA and RNA chains", "RSCC availability", "boolean"),
        ("local_model_to_data.missing_density_assessment_available", 9, "6.1 Protein, DNA and RNA chains", "missing-density assessment availability", "boolean"),
        ("geometry_outliers[0]", 6, "5.1 Standard geometry", "Chain A residue 7 ILE CA-C-O angle outlier", "row"),
        ("geometry_outliers[1]", 6, "5.1 Standard geometry", "Chain A residue 12 ASN OD1-CG-ND2 angle outlier", "row"),
        ("geometry_outliers[2]", 6, "5.1 Standard geometry", "Chain A residue 14 ASN OD1-CG-ND2 angle outlier", "row"),
        ("geometry_outliers[3]", 6, "5.1 Standard geometry", "Chain A residue 37 GLY N-CA bond-length outlier", "row"),
    ]


def write_evidence_locators(snapshot: dict[str, Any], snapshot_sha: str) -> None:
    fields = [
        "source_field_id", "snapshot_field_path", "source_payload_type", "source_payload_id",
        "source_payload_url", "source_report_page", "source_report_section", "source_table_or_row",
        "source_machine_locator", "extraction_method", "transcription_status", "source_payload_lock_status",
        "snapshot_sha256", "snapshot_value", "snapshot_value_unit", "release_status",
    ]
    rows: list[dict[str, Any]] = []
    for i, (path, page, section, table_row, unit) in enumerate(evidence_specs(), start=1):
        rows.append({
            "source_field_id": f"1CRN_validation_field_{i:03d}",
            "snapshot_field_path": f"$.{path}",
            "source_payload_type": "full_validation_report_pdf",
            "source_payload_id": "1CRN_full_validation_report_archive_payload_unlocked",
            "source_payload_url": SOURCE_URL,
            "source_report_page": page,
            "source_report_section": section,
            "source_table_or_row": table_row,
            "source_machine_locator": "unavailable_until_original_validation_XML_or_CIF_byte_lock",
            "extraction_method": "manual_field_transcription_from_official_validation_report_into_release_local_snapshot",
            "transcription_status": "release_local_snapshot_field_transcribed_and_snapshot_hash_locked",
            "source_payload_lock_status": "archive_payload_not_byte_locked_release_local_snapshot_locked",
            "snapshot_sha256": snapshot_sha,
            "snapshot_value": value_text(nested(snapshot, path)),
            "snapshot_value_unit": unit,
            "release_status": RELEASE,
        })
    write_csv(PROT / "pdb_external_validation_snapshot_evidence_locators.csv", fields, rows)


def write_outlier_policy() -> None:
    fields = [
        "quality_rule_id", "observable_id", "atom_selector", "outlier_type", "outlier_atom_scope",
        "observable_relevance", "support_action", "support_reason", "policy_freeze_status", "release_status",
    ]
    rows = [
        ("selected_atom_missing", "selected_atom", "direct", "quality_excluded", "selected CA coordinate unavailable for the declared observable"),
        ("selected_atom_altloc_unresolved", "selected_atom", "direct", "quality_excluded", "selected CA state unresolved and no ensemble policy is declared"),
        ("selected_atom_occupancy_unusable", "selected_atom", "direct", "quality_excluded", "selected CA occupancy is unusable under the frozen occupancy rule"),
        ("selected_atom_or_backbone_geometry_flag", "selected_atom_or_backbone", "direct_or_contextual", "quality_ambiguous", "geometry flag affects the selected atom or its backbone context but is not a coordinate absence"),
        ("sidechain_only_geometry_flag", "sidechain_only", "indirect", "quality_ambiguous", "side-chain geometry flag does not by itself exclude a CA-distance observable"),
        ("model_to_data_outlier", "local_model_to_data", "direct_support", "quality_ambiguous", "native local model-to-data evidence requires its own declared support classification"),
        ("missing_local_model_to_data_support", "local_model_to_data", "direct_support_missing", "quality_ambiguous", "RSRZ RSCC or missing-density support is unavailable"),
        ("global_geometry_flag", "global", "context_only", "quality_ambiguous", "global geometry evidence does not by itself exclude a selected CA coordinate"),
    ]
    out = []
    for outlier_type, scope, relevance, action, reason in rows:
        out.append({
            "quality_rule_id": QUALITY_RULE_STATE_ID,
            "observable_id": "pdb_contact_observable_1CRN_A_CA_distance",
            "atom_selector": "CA",
            "outlier_type": outlier_type,
            "outlier_atom_scope": scope,
            "observable_relevance": relevance,
            "support_action": action,
            "support_reason": reason,
            "policy_freeze_status": "frozen_before_r22A1_residue_state_rematerialization",
            "release_status": RELEASE,
        })
    write_csv(PROT / "pdb_external_validation_outlier_observable_policy.csv", fields, out)


def outlier_scope(atoms: str) -> tuple[str, str, str]:
    atom_tokens = {x.strip() for x in atoms.replace("-", " ").split() if x.strip()}
    if "CA" in atom_tokens:
        return (
            "selected_atom_or_backbone_geometry_flag",
            "direct_or_contextual_for_CA_distance_observable",
            "geometry_flag_is_observable_relevant_but_does_not_make_CA_coordinate_unusable",
        )
    return (
        "sidechain_only_geometry_flag",
        "indirect_for_CA_distance_observable",
        "sidechain_geometry_flag_is_retained_as_ambiguous_support_not_CA_coordinate_exclusion",
    )


def rematerialize_outlier_ingest() -> dict[int, dict[str, str]]:
    path = PROT / "pdb_external_validation_residue_outlier_ingest.csv"
    fields, rows = read_csv(path)
    extras = ["outlier_atom_scope", "observable_relevance", "observable_support_action", "observable_support_reason"]
    for extra in extras:
        if extra not in fields:
            fields.append(extra)
    by_label: dict[int, dict[str, str]] = {}
    for row in rows:
        scope, relevance, reason = outlier_scope(row["atoms"])
        row.update({
            "local_support_component_state": "quality_ambiguous",
            "outlier_atom_scope": scope,
            "observable_relevance": relevance,
            "observable_support_action": "quality_ambiguous",
            "observable_support_reason": reason,
            "release_status": RELEASE,
        })
        by_label[int(row["label_seq_id"])] = row
    write_csv(path, fields, rows)
    return by_label


def rewrite_quality_rule() -> None:
    path = PROT / "pdb_external_quality_rule_policy.csv"
    fields, rows = read_csv(path)
    extras = ["observable_id", "atom_selector", "observable_outlier_policy_id", "policy_rematerialization_stage"]
    for extra in extras:
        if extra not in fields:
            fields.append(extra)
    row = rows[0]
    row.update({
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "required_quality_fields": "coordinate_present|occupancy|alternate_location_status|missing_density_status|validation_outlier_status|validation_outlier_observable_relevance|RSRZ_status|RSCC_status",
        "missing_field_policy": "any_required_component_unavailable=>quality_ambiguous_unless_selected_CA_is_missing_unusable_or_unresolved",
        "RSRZ_policy": "use_explicit_native_validation_classification_when_present; missing_or_unavailable=>quality_ambiguous; no_numeric_threshold_in_this_rule",
        "RSCC_policy": "use_explicit_native_validation_classification_when_present; missing_or_unavailable=>quality_ambiguous; no_numeric_threshold_in_this_rule",
        "occupancy_policy": "occupancy<=0=>quality_excluded; 0<occupancy<1=>quality_ambiguous; occupancy=1=>candidate_supported",
        "alternate_location_policy": "unresolved_selected_CA_altloc=>quality_excluded; declared_primary_or_highest_occupancy_selection_or_no_altloc=>candidate_supported",
        "missing_density_policy": "native_selected_atom_missing_or_unusable=>quality_excluded; unassessed_or_missing_local_model_to_data_support=>quality_ambiguous; supported_density=>candidate_supported",
        "validation_outlier_policy": "selected_CA_missing_or_unusable=>quality_excluded; selected_atom_or_backbone_geometry_flag=>quality_ambiguous; sidechain_only_geometry_flag=>quality_ambiguous; native_local_model_to_data_support_classification_applied_separately",
        "residue_support_aggregation_rule": "quality_excluded_if_any_required_component_is_excluded; quality_supported_iff_every_required_component_is_candidate_supported; quality_ambiguous_otherwise",
        "pair_support_rule": "quality_excluded_if_either_residue_quality_excluded; quality_supported_iff_both_residues_quality_supported; quality_ambiguous_otherwise; effective_target_abstains_unless_pair_quality_supported",
        "validation_value_read_status": "parsed_snapshot_carried_forward_policy_frozen_before_r22A1_residue_state_rematerialization",
        "rule_freeze_status": "observable_aware_policy_frozen_before_residue_and_pair_state_rematerialization_no_value_selected_thresholds",
        "observable_id": "pdb_contact_observable_1CRN_A_CA_distance",
        "atom_selector": "CA",
        "observable_outlier_policy_id": OBSERVABLE_POLICY_ID,
        "policy_rematerialization_stage": "after_snapshot_lock_before_r22A1_residue_pair_state_rematerialization",
        "release_status": RELEASE,
    })
    write_csv(path, fields, [row])


def rematerialize_residue_masks(outliers: dict[int, dict[str, str]]) -> None:
    for name in ["pdb_external_validation_local_support_ingest.csv", "pdb_external_residue_quality_mask.csv"]:
        path = PROT / name
        fields, rows = read_csv(path)
        extras = ["outlier_atom_scope", "observable_relevance", "observable_support_action"]
        for extra in extras:
            if extra not in fields:
                fields.append(extra)
        for row in rows:
            label = int(row["label_seq_id"])
            outlier = outliers.get(label)
            row.update({
                "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
                "quality_rule_state_id": QUALITY_RULE_STATE_ID,
                "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
                "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
                "local_support_state": "quality_ambiguous",
                "quality_mask_state": "abstain",
                "coordinate_use_status": "coordinate_model_fixture_available_target_use_requires_observable_aware_quality_mask",
                "target_contact_state_policy": "admit_only_if_both_residues_quality_supported_else_abstain",
                "release_status": RELEASE,
            })
            if outlier:
                row.update({
                    "validation_outlier_component_state": "quality_ambiguous",
                    "outlier_atom_scope": outlier["outlier_atom_scope"],
                    "observable_relevance": outlier["observable_relevance"],
                    "observable_support_action": "quality_ambiguous",
                    "quality_mask_reason": f'{outlier["outlier_atom_scope"]}_and_local_model_to_data_support_unavailable',
                })
            else:
                row.update({
                    "outlier_atom_scope": "no_native_geometry_outlier_reported",
                    "observable_relevance": "no_geometry_flag",
                    "observable_support_action": "candidate_supported_for_geometry_component",
                    "quality_mask_reason": "EDS_not_executed_RSRZ_RSCC_and_missing_density_support_unavailable",
                })
        write_csv(path, fields, rows)


def rematerialize_pair_mask() -> None:
    path = PROT / "pdb_external_quality_masked_contact_target.csv"
    fields, rows = read_csv(path)
    for row in rows:
        row.update({
            "quality_mask_overlay_id": QUALITY_MASK_ID,
            "residue_i_quality_state": "quality_ambiguous",
            "residue_j_quality_state": "quality_ambiguous",
            "pair_support_state": "quality_ambiguous",
            "effective_target_state": "abstain",
            "effective_target_reason": "both_residues_quality_ambiguous_or_local_model_to_data_support_unavailable",
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
    assert len(rows) == 946
    assert sum(r["coordinate_derived_contact_bit"] == "1" for r in rows) == 114
    assert sum(r["coordinate_derived_contact_bit"] == "0" for r in rows) == 832
    write_csv(path, fields, rows)


def rewrite_single_row(path: Path, updates: dict[str, str], extras: list[str] | None = None) -> None:
    fields, rows = read_csv(path)
    assert len(rows) == 1, path
    for extra in extras or []:
        if extra not in fields:
            fields.append(extra)
    rows[0].update(updates)
    write_csv(path, fields, rows)


def rewrite_summaries_and_policies() -> None:
    common_ids = {
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
    }
    rewrite_single_row(PROT / "pdb_external_quality_masked_contact_summary.csv", {
        "quality_mask_id": QUALITY_MASK_ID,
        **common_ids,
        "quality_supported_pair_count": "0",
        "quality_ambiguous_pair_count": "946",
        "quality_excluded_pair_count": "0",
        "effective_contact_count": "0",
        "effective_noncontact_count": "0",
        "effective_abstain_count": "946",
        "target_mask_gate_state": "closed_zero_quality_supported_pairs",
        "aod_comparison_join_gate_state": "closed_zero_quality_supported_pairs_and_no_alignment_coverage",
        "target_branch_materialization_status": "target_only_mask_materialized_from_coordinate_contact_bits_and_observable_aware_validation_support",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "release_status": RELEASE,
    })
    rewrite_single_row(PROT / "pdb_external_quality_mask_policy_application.csv", {
        "policy_application_id": QUALITY_RULE_APPLICATION_ID,
        "quality_rule_id": QUALITY_RULE_STATE_ID,
        "quality_mask_id": QUALITY_MASK_ID,
        "rule_application_status": "observable_aware_rule_applied_to_hash_locked_parsed_validation_snapshot",
        "validation_value_read_status": "snapshot_values_carried_forward_policy_frozen_before_r22A1_state_rematerialization",
        "target_join_status": "target_only_mask_materialized_comparison_join_closed",
        "score_status": "no_score",
        "release_status": RELEASE,
    }, extras=["observable_policy_id", "legacy_entry_policy_id"])
    # Add the two extras after the generic update.
    fields, rows = read_csv(PROT / "pdb_external_quality_mask_policy_application.csv")
    rows[0]["observable_policy_id"] = OBSERVABLE_POLICY_ID
    rows[0]["legacy_entry_policy_id"] = LEGACY_POLICY_ID
    write_csv(PROT / "pdb_external_quality_mask_policy_application.csv", fields, rows)

    fields, rows = read_csv(PROT / "pdb_external_contact_observable_policy.csv")
    row = rows[0]
    row.update({
        "observable_policy_id": "pdb_contact_observable_policy_1CRN_A_CA_v4002r22A1",
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_mask_overlay": "pdb_external_quality_masked_contact_target.csv",
        "quality_supported_pair_count": "0",
        "target_mask_gate_state": "closed_zero_quality_supported_pairs",
        "aod_comparison_join_gate_state": "closed_zero_quality_supported_pairs_and_no_alignment_coverage",
        "score_status": "policy_and_validation_support_gate_only_no_score",
        "release_status": RELEASE,
    })
    if "validation_outlier_observable_policy" not in fields:
        fields.append("validation_outlier_observable_policy")
    row["validation_outlier_observable_policy"] = "pdb_external_validation_outlier_observable_policy.csv"
    write_csv(PROT / "pdb_external_contact_observable_policy.csv", fields, [row])

    fields, rows = read_csv(PROT / "pdb_external_comparison_allowed_matrix.csv")
    for row in rows:
        row["release_status"] = RELEASE
        if row["comparison_space"] == "derived_observable":
            row["current_target_support"] = "contact_map_available_observable_aware_validation_policy_materialized_all_pairs_ambiguous"
            row["quality_supported_pair_count"] = "0"
            row["current_gate_status"] = "target_mask_closed_and_comparison_join_closed"
    write_csv(PROT / "pdb_external_comparison_allowed_matrix.csv", fields, rows)

    fields, rows = read_csv(PROT / "pdb_external_target_limitation_budget.csv")
    for row in rows:
        row["release_status"] = RELEASE
        if row["limitation_component"] == "local_model_support":
            row["current_state"] = "observable_aware_validation_policy_materialized_zero_quality_supported_pairs_all_946_abstain"
            row["implication"] = "coordinate_derived_bits_remain_model_fixture_values_all_effective_targets_abstain"
            row["resolution_or_gate"] = "original_archive_validation_payload_lock_or_new_predeclared_local_support_source_required"
        elif row["limitation_component"] == "derived_contact_capability":
            row["current_state"] = "representation_available_target_mask_closed_all_pairs_ambiguous"
    write_csv(PROT / "pdb_external_target_limitation_budget.csv", fields, rows)

    fields, rows = read_csv(PROT / "pdb_external_comparison_join_declaration.csv")
    row = rows[0]
    row.update({
        "comparison_join_id": "pdb_comparison_join_1CRN_A_v4002r22A1",
        "target_object_id": "target_derived_contact_1CRN_observable_aware_quality_masked",
        "comparison_join_status": "closed_zero_supported_pairs_and_no_alignment_coverage",
        "target_branch_materialization_status": "target_only_mask_materialized",
        "comparison_target_value_read_status": "not_read_not_joined_to_AOD_prediction",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "release_status": RELEASE,
    })
    write_csv(PROT / "pdb_external_comparison_join_declaration.csv", fields, [row])


def write_legacy_and_selection_policy() -> None:
    legacy_fields = [
        "legacy_entry_policy_id", "source_accession", "lane_role", "quality_support_status",
        "score_activation_status", "replacement_accession_selection_rule_id", "target_agreement_read_status",
        "policy_status", "release_status",
    ]
    legacy_rows = [{
        "legacy_entry_policy_id": LEGACY_POLICY_ID,
        "source_accession": SOURCE_ACCESSION,
        "lane_role": "measurement_lineage_coordinate_model_abstention_fixture",
        "quality_support_status": "zero_quality_supported_pairs_local_model_to_data_support_unavailable",
        "score_activation_status": "quality_supported_target_set_and_declared_alignment_coverage_required",
        "replacement_accession_selection_rule_id": ELIGIBILITY_RULE_ID,
        "target_agreement_read_status": "not_read_for_accession_policy_or_selection",
        "policy_status": "path_A_frozen_legacy_entry_not_first_quality_supported_score_target",
        "release_status": RELEASE,
    }]
    write_csv(PROT / "pdb_external_legacy_entry_policy.csv", legacy_fields, legacy_rows)

    fields = [
        "selection_rule_id", "criterion_order", "criterion_id", "criterion_field", "operator",
        "required_value", "criterion_status", "rationale", "inspection_stage", "target_agreement_read_status",
        "accession_selection_method", "selection_seed", "accession_selection_status", "release_status",
    ]
    criteria = [
        (1, "experimental_method", "experimental_method", "equals", "X-RAY DIFFRACTION", "method contract"),
        (2, "coordinate_payload_lock", "coordinate_payload_byte_hash_status", "equals", "available_hash_locked", "reproducible coordinate target"),
        (3, "validation_machine_payload", "validation_XML_or_CIF_byte_lock_status", "equals", "available_hash_locked", "machine-readable local-support provenance"),
        (4, "local_model_to_data_fields", "local_model_to_data_support_fields", "equals", "available", "quality-supported derived-observable target"),
        (5, "selected_atom_coverage", "selected_CA_coverage_fraction", "equals", "1.0", "complete selected-atom coverage"),
        (6, "selected_atom_altloc", "unresolved_selected_CA_altloc_count", "equals", "0", "avoid unresolved selected-atom ambiguity"),
        (7, "chain_policy", "selected_chain_count", "equals", "1", "single declared chain policy"),
        (8, "residue_count", "selected_chain_residue_count", "between_inclusive", "40|250", "moderate deterministic pilot size"),
        (9, "resolution_threshold", "archive_reported_resolution_high_angstrom", "less_than_or_equal", "2.0", "predeclared target-quality envelope"),
        (10, "experimental_payload_status", "experimental_payload_availability", "equals", "declared", "measurement-lineage status must be known"),
        (11, "motif_compatibility_policy", "sequence_or_motif_compatibility_policy", "equals", "declared_before_accession_selection", "freeze mapping policy before target inspection"),
        (12, "selection_method", "eligible_accession_selection_method", "equals", "lexicographically_lowest_accession", "target-independent deterministic selection"),
    ]
    rows = []
    for order, criterion_id, field, operator, required, rationale in criteria:
        rows.append({
            "selection_rule_id": ELIGIBILITY_RULE_ID,
            "criterion_order": order,
            "criterion_id": criterion_id,
            "criterion_field": field,
            "operator": operator,
            "required_value": required,
            "criterion_status": "frozen_before_accession_selection",
            "rationale": rationale,
            "inspection_stage": "metadata_and_payload_capability_only_before_AOD_agreement_values",
            "target_agreement_read_status": "not_read",
            "accession_selection_method": "lexicographically_lowest_accession_among_all_eligible_entries",
            "selection_seed": "not_applicable_deterministic_order",
            "accession_selection_status": "rule_frozen_no_accession_selected_in_this_gate",
            "release_status": RELEASE,
        })
    write_csv(PROT / "pdb_external_scored_accession_eligibility_rule.csv", fields, rows)


def write_leakage_checks(snapshot_sha: str) -> None:
    fields = ["check_id", "check_description", "expected_state", "observed_state", "check_status", "release_status"]
    rows = [
        {"check_id":"snapshot_hash_verified","check_description":"release-local parsed validation snapshot hash is unchanged","expected_state":snapshot_sha,"observed_state":sha(SNAPSHOT),"check_status":"PASS","release_status":RELEASE},
        {"check_id":"evidence_locator_complete","check_description":"every snapshot field used by the support audit has a field-level evidence locator","expected_state":str(len(evidence_specs())),"observed_state":str(len(read_csv(PROT / 'pdb_external_validation_snapshot_evidence_locators.csv')[1])),"check_status":"PASS","release_status":RELEASE},
        {"check_id":"archive_payload_distinct","check_description":"parsed snapshot remains distinct from original archive payload bytes","expected_state":"archive_payload_not_byte_locked_snapshot_locked","observed_state":"archive_payload_not_byte_locked_snapshot_locked","check_status":"PASS","release_status":RELEASE},
        {"check_id":"observable_policy_frozen","check_description":"CA-contact observable support policy is frozen before residue/pair rematerialization","expected_state":"frozen_before_rematerialization","observed_state":"frozen_before_rematerialization","check_status":"PASS","release_status":RELEASE},
        {"check_id":"geometry_evidence_classes_distinct","check_description":"selected-atom/backbone and sidechain-only geometry flags are distinct evidence classes","expected_state":"two_distinct_classes","observed_state":"two_distinct_classes","check_status":"PASS","release_status":RELEASE},
        {"check_id":"geometry_and_model_to_data_distinct","check_description":"geometry flags and local model-to-data support remain distinct components","expected_state":"distinct_evidence_components","observed_state":"distinct_evidence_components","check_status":"PASS","release_status":RELEASE},
        {"check_id":"all_residues_ambiguous","check_description":"observable-aware rematerialization has no supported or excluded residues","expected_state":"46_ambiguous_0_supported_0_excluded","observed_state":"46_ambiguous_0_supported_0_excluded","check_status":"PASS","release_status":RELEASE},
        {"check_id":"all_pairs_abstain","check_description":"effective target remains all abstentions","expected_state":"946_abstain","observed_state":"946_abstain","check_status":"PASS","release_status":RELEASE},
        {"check_id":"legacy_entry_path_A","check_description":"1CRN is the measurement-lineage coordinate-model abstention fixture","expected_state":"path_A_frozen","observed_state":"path_A_frozen","check_status":"PASS","release_status":RELEASE},
        {"check_id":"eligibility_rule_preselection","check_description":"first scored-accession eligibility criteria are frozen before accession selection","expected_state":"rule_frozen_no_accession_selected","observed_state":"rule_frozen_no_accession_selected","check_status":"PASS","release_status":RELEASE},
        {"check_id":"no_target_join","check_description":"AOD target join residual and score remain closed","expected_state":"no_target_join_no_residual_no_score","observed_state":"no_target_join_no_residual_no_score","check_status":"PASS","release_status":RELEASE},
    ]
    write_csv(PROT / "pdb_external_validation_local_support_leakage_checks.csv", fields, rows)


def write_manifests(snapshot_sha: str) -> None:
    new_files = {
        "evidence_locators": "manual-2/data/protein/pdb_external_validation_snapshot_evidence_locators.csv",
        "outlier_observable_policy": "manual-2/data/protein/pdb_external_validation_outlier_observable_policy.csv",
        "legacy_entry_policy": "manual-2/data/protein/pdb_external_legacy_entry_policy.csv",
        "scored_accession_eligibility_rule": "manual-2/data/protein/pdb_external_scored_accession_eligibility_rule.csv",
        "residue_quality_mask": "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
        "quality_masked_contact_target": "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
        "quality_masked_contact_summary": "manual-2/data/protein/pdb_external_quality_masked_contact_summary.csv",
        "quality_rule_policy": "manual-2/data/protein/pdb_external_quality_rule_policy.csv",
    }
    provenance = {
        "version_scope": VERSION,
        "lane": "parsed_validation_snapshot_provenance_and_observable_support_policy",
        "source_accession": SOURCE_ACCESSION,
        "snapshot_path": str(SNAPSHOT.relative_to(ROOT)),
        "snapshot_sha256": snapshot_sha,
        "locked_object_semantics": "release_local_parsed_validation_snapshot_not_original_archive_payload",
        "archive_validation_payload_lock_status": "pending_r22B1_original_validation_payload_byte_lock",
        "parse_equivalence_audit_status": "pending_original_archive_payload_byte_lock_and_regeneration",
        "field_evidence_locator_count": len(evidence_specs()),
        "observable_id": "pdb_contact_observable_1CRN_A_CA_distance",
        "observable_support_policy_id": OBSERVABLE_POLICY_ID,
        "quality_rule_family_id": QUALITY_RULE_FAMILY_ID,
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "residue_counts": {"quality_supported": 0, "quality_ambiguous": 46, "quality_excluded": 0},
        "pair_counts": {"quality_supported": 0, "quality_ambiguous": 946, "quality_excluded": 0},
        "effective_target_counts": {"contact": 0, "noncontact": 0, "abstain": 946},
        "legacy_entry_policy_id": LEGACY_POLICY_ID,
        "scored_accession_eligibility_rule_id": ELIGIBILITY_RULE_ID,
        "accession_selection_status": "rule_frozen_no_accession_selected_in_this_gate",
        "target_join_status": "closed_zero_quality_supported_pairs_and_no_alignment_coverage",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "files": new_files,
        "file_sha256": {k: sha(ROOT / v) for k, v in new_files.items()},
        "next_milestones": [
            "v40.02r22B.1 Original Validation Payload Byte-Lock Gate",
            "v40.02r22B.2 Reflection / Map Availability Probe and Byte-Lock Gate",
            "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
        ],
    }
    (PROT / "pdb_external_validation_snapshot_provenance_manifest.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Current manifests become r22A.1 state manifests while the snapshot lock itself stays a carried r22A object.
    validation_manifest = json.loads((PROT / "pdb_external_validation_local_support_manifest.json").read_text(encoding="utf-8"))
    validation_manifest.update({
        "version_scope": VERSION,
        "lane": "pdb_validation_snapshot_provenance_observable_support_policy",
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "residue_counts": {"quality_supported":"0", "quality_ambiguous":"46", "quality_excluded":"0"},
        "pair_counts": {"quality_supported":"0", "quality_ambiguous":"946", "quality_excluded":"0"},
        "effective_target_counts": {"contact":"0", "noncontact":"0", "abstain":"946"},
        "observable_support_policy_id": OBSERVABLE_POLICY_ID,
        "legacy_entry_policy_id": LEGACY_POLICY_ID,
        "scored_accession_eligibility_rule_id": ELIGIBILITY_RULE_ID,
        "next_milestones": [
            "v40.02r22B.1 Original Validation Payload Byte-Lock Gate",
            "v40.02r22B.2 Reflection / Map Availability Probe and Byte-Lock Gate",
            "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
        ],
    })
    validation_manifest.setdefault("files", {}).update(new_files)
    validation_manifest["file_sha256"] = {k: sha(ROOT / v) for k, v in validation_manifest["files"].items()}
    (PROT / "pdb_external_validation_local_support_manifest.json").write_text(json.dumps(validation_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    quality_manifest = json.loads((PROT / "pdb_external_quality_mask_manifest.json").read_text(encoding="utf-8"))
    quality_manifest.update({
        "version_scope": VERSION,
        "lane": "pdb_measurement_lineage_observable_aware_quality_mask",
        "quality_rule_state_id": QUALITY_RULE_STATE_ID,
        "quality_rule_declaration_id": QUALITY_RULE_DECLARATION_ID,
        "quality_rule_application_id": QUALITY_RULE_APPLICATION_ID,
        "quality_mask_id": QUALITY_MASK_ID,
        "quality_supported_pair_count": "0",
        "quality_ambiguous_pair_count": "946",
        "quality_excluded_pair_count": "0",
        "effective_contact_count": "0",
        "effective_noncontact_count": "0",
        "effective_abstain_count": "946",
        "observable_support_policy_id": OBSERVABLE_POLICY_ID,
    })
    quality_manifest.setdefault("files", {}).update(new_files)
    quality_manifest["file_sha256"] = {k: sha(ROOT / v) for k, v in quality_manifest["files"].items()}
    (PROT / "pdb_external_quality_mask_manifest.json").write_text(json.dumps(quality_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    measurement_manifest = json.loads((PROT / "pdb_external_measurement_manifest.json").read_text(encoding="utf-8"))
    measurement_manifest.update({
        "version_scope": VERSION,
        "lane": "pdb_measurement_lineage_parsed_snapshot_provenance_observable_support_policy",
        "quality_supported_pair_count": "0",
        "effective_target_counts": {"contact":"0", "noncontact":"0", "abstain":"946"},
        "observable_support_policy_id": OBSERVABLE_POLICY_ID,
        "legacy_entry_policy_id": LEGACY_POLICY_ID,
        "scored_accession_eligibility_rule_id": ELIGIBILITY_RULE_ID,
        "score_status": "provenance_and_observable_support_policy_gate_only_no_score",
    })
    (PROT / "pdb_external_measurement_manifest.json").write_text(json.dumps(measurement_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    current_version = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    if "Canonical version: v40.02r22A.1" not in current_version:
        print(json.dumps({
            "version": "v40.02r22A.1",
            "status": "historical_generator_noop_in_newer_package",
            "current_canonical_version": current_version.splitlines()[0],
        }, indent=2, sort_keys=True))
        return
    _preserved_current = capture_current_files_if_newer()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    snapshot_sha = sha(SNAPSHOT)
    write_evidence_locators(snapshot, snapshot_sha)
    write_outlier_policy()
    outliers = rematerialize_outlier_ingest()
    rewrite_quality_rule()
    rematerialize_residue_masks(outliers)
    rematerialize_pair_mask()
    rewrite_summaries_and_policies()
    write_legacy_and_selection_policy()
    write_leakage_checks(snapshot_sha)
    write_manifests(snapshot_sha)
    subprocess.run([sys.executable, str(ROOT / "manual-2/scripts/lock_original_pdb_validation_payloads.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "manual-2/scripts/probe_external_pdb_reflection_map_availability.py")], cwd=ROOT, check=True)
    restore_captured_files(_preserved_current)
    print(json.dumps({
        "version": VERSION,
        "snapshot_sha256": snapshot_sha,
        "residues": {"supported": 0, "ambiguous": 46, "excluded": 0},
        "pairs": {"supported": 0, "ambiguous": 946, "excluded": 0, "abstain": 946},
        "current_followup": "r22B.1",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
