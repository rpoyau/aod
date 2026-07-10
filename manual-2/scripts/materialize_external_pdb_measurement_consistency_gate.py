#!/usr/bin/env python3
"""Materialize r21.2 measurement-lineage consistency and quality-mask overlays.

This Manual-II-only step keeps the target measurement lineage and the frozen
AOD prediction lane structurally independent, refines payload-availability
states, freezes the local-support rule before validation values are parsed, and
materializes the pair-level ternary target mask.  It reads no downstream target
comparison values and computes no residual score.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r21.2"
RELEASE = "v40.02r21.2_measurement_lineage_consistency_quality_mask_materialization"
QUALITY_RULE_ID = "pdb_local_support_rule_1CRN_v4002r212"
QUALITY_MASK_ID = "pdb_pair_quality_mask_1CRN_A_all946_v4002r212"
COMPARISON_JOIN_ID = "pdb_comparison_join_1CRN_A_v4002r212"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def update_release_status(path: Path) -> None:
    rows = read_csv(path)
    if not rows:
        return
    fields = list(rows[0].keys())
    if "release_status" in fields:
        for row in rows:
            row["release_status"] = RELEASE
        write_csv(path, fields, rows)


def materialize_measurement_metadata() -> None:
    fields = [
        "measurement_lineage_id", "lineage_branch", "branch_stage_order",
        "lineage_object_id", "upstream_object_id", "stage_name",
        "operator_symbol", "input_state", "output_state", "stage_role",
        "payload_or_schema_status", "current_gate_status",
        "target_value_read_status", "release_status",
    ]
    target_id = "pdb_measurement_lineage_1CRN_xray_v4002r212"
    rows_raw = [
        [target_id,"target_measurement","1","target_physical_state_1CRN","","physical_state","identity","X_physical","X_physical","declared physical specimen/state","registry_only","declared_no_target_values_read","not_read",RELEASE],
        [target_id,"target_measurement","2","target_raw_measurement_1CRN","target_physical_state_1CRN","measurement_operator","M_theta","X_physical","Y_raw","X-ray diffraction measurement operator","operator_family_registered_payload_schema_unresolved","not_frozen_in_this_gate","not_read",RELEASE],
        [target_id,"target_measurement","3","target_processed_measurement_1CRN","target_raw_measurement_1CRN","processing_operator","Q_psi","Y_raw","Y_processed","data reduction / processing operator","software_and_payload_schema_unresolved","not_frozen_in_this_gate","not_read",RELEASE],
        [target_id,"target_measurement","4","target_coordinate_model_1CRN","target_processed_measurement_1CRN","reconstruction_operator","R_phi","Y_processed","Xhat_model","refinement/reconstruction producing deposited coordinate model","coordinate_model_available_hash_locked","carried_coordinate_model_fixture","not_read",RELEASE],
        [target_id,"target_measurement","5","target_derived_contact_1CRN","target_coordinate_model_1CRN","derived_observable_operator","D_eta","Xhat_model","O_derived","frozen coordinate-to-contact extraction policy","derived_contact_policy_available_quality_mask_required","quality_mask_frozen_zero_admitted_pairs","not_read",RELEASE],
        ["pdb_aod_prediction_lineage_GAS_v4002r212","aod_prediction","1","aod_frozen_contact_packet_GAS","","independent_aod_lane","AOD_freeze","AOD_raw_trace","X_AOD_freeze","AOD motif/curling-curls/SADAR frozen packet","contact_pair_set","carried_forward_independent_lane","not_read",RELEASE],
    ]
    write_csv(PROT / "pdb_external_measurement_metadata.csv", fields, [dict(zip(fields, r)) for r in rows_raw])


def materialize_comparison_join() -> None:
    fields = [
        "comparison_join_id", "target_lineage_id", "aod_lineage_id",
        "comparison_space", "target_object_id", "aod_object_id",
        "join_prerequisite", "comparison_join_status",
        "target_value_read_status", "residual_status", "score_status",
        "release_status",
    ]
    rows = [
        {
            "comparison_join_id": COMPARISON_JOIN_ID,
            "target_lineage_id": "pdb_measurement_lineage_1CRN_xray_v4002r212",
            "aod_lineage_id": "pdb_aod_prediction_lineage_GAS_v4002r212",
            "comparison_space": "derived_observable",
            "target_object_id": "target_derived_contact_1CRN",
            "aod_object_id": "aod_frozen_contact_packet_GAS",
            "join_prerequisite": "quality_supported_pair_count>0_and_declared_alignment_projection_rule",
            "comparison_join_status": "deferred_zero_supported_pairs_and_no_alignment",
            "target_value_read_status": "not_read",
            "residual_status": "not_computed",
            "score_status": "no_score",
            "release_status": RELEASE,
        }
    ]
    write_csv(PROT / "pdb_external_comparison_join_declaration.csv", fields, rows)


def materialize_payload_availability() -> None:
    old = {r["payload_type"]: r for r in read_csv(PROT / "pdb_external_experimental_payload_availability.csv")}
    fields = [
        "payload_registry_id","source_database","source_accession","payload_type",
        "payload_availability","archive_listing_status","byte_probe_status",
        "byte_lock_status","parse_status","field_availability_status",
        "payload_path_or_probe_url","local_payload_path","payload_sha256",
        "payload_byte_count","probe_url","http_status","content_type",
        "probe_bytes","probe_sha256","probe_utc","archive_source",
        "availability_probe_status","access_control_status","release_status",
    ]
    state_map = {
        "coordinate_model_mmcif": ("available_hash_locked","archive_listed","probe_confirmed_from_committed_local_payload","byte_hash_locked","parsed_coordinate_model","coordinate_model_fields_available"),
        "validation_report_cif": ("archive_listed_probe_pending","archive_listed","probe_pending","not_locked","not_started","local_validation_fields_unavailable"),
        "validation_report_xml": ("archive_listed_probe_pending","archive_listed","probe_pending","not_locked","not_started","local_validation_fields_unavailable"),
        "reflection_payload_structure_factors": ("endpoint_declared_probe_pending","candidate_endpoint_declared","probe_pending","not_locked","not_started","reflection_fields_unavailable"),
        "processed_reflection_payload": ("endpoint_declared_probe_pending","candidate_endpoint_declared","probe_pending","not_locked","not_started","reflection_fields_unavailable"),
        "map_coefficients": ("endpoint_declared_probe_pending","candidate_endpoint_declared","probe_pending","not_locked","not_started","map_fields_unavailable"),
        "raw_diffraction_images": ("external_registry_reference_pending","external_registry_not_declared","probe_pending","not_locked","not_started","raw_image_fields_unavailable"),
    }
    rows: list[dict[str, str]] = []
    for ptype, row in old.items():
        availability, listing, probe, lock, parse, field_state = state_map[ptype]
        out = {k: row.get(k, "") for k in fields}
        out.update({
            "payload_availability": availability,
            "archive_listing_status": listing,
            "byte_probe_status": probe,
            "byte_lock_status": lock,
            "parse_status": parse,
            "field_availability_status": field_state,
            "release_status": RELEASE,
        })
        rows.append(out)
    write_csv(PROT / "pdb_external_experimental_payload_availability.csv", fields, rows)


def materialize_quality_rule() -> None:
    fields = [
        "quality_rule_id","source_accession","comparison_space",
        "required_quality_fields","missing_field_policy","RSRZ_policy",
        "RSCC_policy","occupancy_policy","alternate_location_policy",
        "missing_density_policy","validation_outlier_policy",
        "residue_support_domain","pair_support_rule","target_state_rule",
        "validation_value_read_status","rule_freeze_status","release_status",
    ]
    row = {
        "quality_rule_id": QUALITY_RULE_ID,
        "source_accession": "1CRN",
        "comparison_space": "derived_observable",
        "required_quality_fields": "coordinate_present|occupancy|alternate_location_status|missing_density_status|validation_outlier_status|RSRZ_status|RSCC_status",
        "missing_field_policy": "any_required_local_validation_field_unavailable=>quality_ambiguous",
        "RSRZ_policy": "use_validation_report_native_outlier_classification_when_present; unavailable=>quality_ambiguous",
        "RSCC_policy": "record_native_value_and_support_status_when_present; unavailable=>quality_ambiguous",
        "occupancy_policy": "occupancy<=0=>quality_excluded; 0<occupancy<1=>quality_ambiguous; occupancy=1=>candidate_supported",
        "alternate_location_policy": "unresolved_multiple_altloc=>quality_ambiguous; declared_primary_or_highest_occupancy_selection=>candidate_supported",
        "missing_density_policy": "missing_density=>quality_excluded; unassessed=>quality_ambiguous; supported_density=>candidate_supported",
        "validation_outlier_policy": "native_validation_outlier=>quality_excluded; no_outlier=>candidate_supported; unavailable=>quality_ambiguous",
        "residue_support_domain": "quality_supported|quality_ambiguous|quality_excluded",
        "pair_support_rule": "quality_supported iff both residues quality_supported; otherwise pair target abstains",
        "target_state_rule": "coordinate_derived_contact_bit admitted as 1 or 0 only for quality_supported pair; otherwise abstain",
        "validation_value_read_status": "not_read_rule_frozen_before_validation_ingest",
        "rule_freeze_status": "frozen_before_validation_value_parse",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_quality_rule_policy.csv", fields, [row])


def update_residue_mask() -> dict[str, dict[str, str]]:
    rows = read_csv(PROT / "pdb_external_residue_quality_mask.csv")
    fields = list(rows[0].keys())
    if "quality_rule_id" not in fields:
        insert_at = fields.index("local_support_state")
        fields.insert(insert_at, "quality_rule_id")
    by_label: dict[str, dict[str, str]] = {}
    for row in rows:
        row["quality_rule_id"] = QUALITY_RULE_ID
        row["release_status"] = RELEASE
        by_label[row["label_seq_id"]] = row
    write_csv(PROT / "pdb_external_residue_quality_mask.csv", fields, rows)
    return by_label


def materialize_pair_overlay(residue_by_label: dict[str, dict[str, str]]) -> None:
    pairs = read_csv(PROT / "pdb_external_evaluation_pair_boundary.csv")
    fields = [
        "quality_mask_overlay_id","evaluation_pair_boundary_id",
        "evaluation_pair_row_id","pair_id","source_accession","chain_id",
        "model_id","label_seq_i","label_seq_j","residue_name_i",
        "residue_name_j","coordinate_derived_contact_bit",
        "residue_i_quality_state","residue_j_quality_state",
        "pair_support_state","effective_target_state",
        "effective_target_reason","quality_rule_id","quality_mask_id",
        "target_value_read_status","residual_status","score_status",
        "release_status",
    ]
    out_rows: list[dict[str, str]] = []
    coord_contact_count = 0
    for pair in pairs:
        i = residue_by_label[pair["label_seq_i"]]
        j = residue_by_label[pair["label_seq_j"]]
        bit = pair["target_contact_value"]
        coord_contact_count += int(bit)
        states = {i["local_support_state"], j["local_support_state"]}
        if states == {"quality_supported"}:
            pair_state = "quality_supported"
            effective = bit
            reason = "both_residues_quality_supported"
        elif "quality_excluded" in states:
            pair_state = "quality_excluded"
            effective = "abstain"
            reason = "at_least_one_residue_quality_excluded"
        else:
            pair_state = "quality_ambiguous"
            effective = "abstain"
            reason = "at_least_one_residue_quality_ambiguous"
        out_rows.append({
            "quality_mask_overlay_id": QUALITY_MASK_ID,
            "evaluation_pair_boundary_id": pair["evaluation_pair_boundary_id"],
            "evaluation_pair_row_id": pair["evaluation_pair_row_id"],
            "pair_id": pair["evaluation_pair_row_id"],
            "source_accession": pair["source_accession"],
            "chain_id": pair["chain_id"],
            "model_id": pair["model_id"],
            "label_seq_i": pair["label_seq_i"],
            "label_seq_j": pair["label_seq_j"],
            "residue_name_i": pair["residue_name_i"],
            "residue_name_j": pair["residue_name_j"],
            "coordinate_derived_contact_bit": bit,
            "residue_i_quality_state": i["local_support_state"],
            "residue_j_quality_state": j["local_support_state"],
            "pair_support_state": pair_state,
            "effective_target_state": effective,
            "effective_target_reason": reason,
            "quality_rule_id": QUALITY_RULE_ID,
            "quality_mask_id": QUALITY_MASK_ID,
            "target_value_read_status": "not_joined_to_AOD_prediction",
            "residual_status": "not_computed",
            "score_status": "no_score",
            "release_status": RELEASE,
        })
    write_csv(PROT / "pdb_external_quality_masked_contact_target.csv", fields, out_rows)

    total = len(out_rows)
    coord_noncontact_count = total - coord_contact_count
    supported = sum(r["pair_support_state"] == "quality_supported" for r in out_rows)
    effective_contacts = sum(r["effective_target_state"] == "1" for r in out_rows)
    effective_noncontacts = sum(r["effective_target_state"] == "0" for r in out_rows)
    effective_abstain = sum(r["effective_target_state"] == "abstain" for r in out_rows)
    summary_fields = [
        "quality_mask_id","quality_rule_id","evaluation_pair_boundary_id",
        "evaluation_pair_count","coordinate_derived_contact_count",
        "coordinate_derived_noncontact_count","quality_supported_pair_count",
        "effective_contact_count","effective_noncontact_count",
        "effective_abstain_count","derived_observable_activation_condition",
        "derived_observable_gate_state","target_value_read_status",
        "residual_status","score_status","release_status",
    ]
    summary_row = {
        "quality_mask_id": QUALITY_MASK_ID,
        "quality_rule_id": QUALITY_RULE_ID,
        "evaluation_pair_boundary_id": out_rows[0]["evaluation_pair_boundary_id"],
        "evaluation_pair_count": str(total),
        "coordinate_derived_contact_count": str(coord_contact_count),
        "coordinate_derived_noncontact_count": str(coord_noncontact_count),
        "quality_supported_pair_count": str(supported),
        "effective_contact_count": str(effective_contacts),
        "effective_noncontact_count": str(effective_noncontacts),
        "effective_abstain_count": str(effective_abstain),
        "derived_observable_activation_condition": "quality_supported_pair_count>0",
        "derived_observable_gate_state": "quality_mask_frozen_zero_admitted_pairs" if supported == 0 else "quality_mask_frozen_supported_pairs_available",
        "target_value_read_status": "not_joined_to_AOD_prediction",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_quality_masked_contact_summary.csv", summary_fields, [summary_row])

    application_fields = [
        "policy_application_id","quality_rule_id","quality_mask_id",
        "residue_quality_mask_file","evaluation_boundary_file",
        "coordinate_contact_source_file","pair_overlay_file",
        "rule_application_status","validation_value_read_status",
        "target_join_status","score_status","release_status",
    ]
    application_row = {
        "policy_application_id": "pdb_quality_mask_policy_application_1CRN_v4002r212",
        "quality_rule_id": QUALITY_RULE_ID,
        "quality_mask_id": QUALITY_MASK_ID,
        "residue_quality_mask_file": "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
        "evaluation_boundary_file": "manual-2/data/protein/pdb_external_evaluation_pair_boundary.csv",
        "coordinate_contact_source_file": "manual-2/data/protein/pdb_external_contact_map_derived.csv",
        "pair_overlay_file": "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
        "rule_application_status": "materialized_from_frozen_rule_and_current_residue_support_states",
        "validation_value_read_status": "not_read_beyond_carried_unavailable_statuses",
        "target_join_status": "not_joined_to_AOD_prediction",
        "score_status": "no_score",
        "release_status": RELEASE,
    }
    write_csv(PROT / "pdb_external_quality_mask_policy_application.csv", application_fields, [application_row])


def materialize_contact_policy() -> None:
    rows = read_csv(PROT / "pdb_external_contact_observable_policy.csv")
    row = rows[0]
    fields = list(row.keys())
    additions = [
        "quality_rule_id","quality_mask_overlay","quality_supported_pair_count",
        "derived_observable_activation_condition","derived_observable_gate_state",
    ]
    insert_at = fields.index("target_value_read_status")
    for name in reversed(additions):
        if name not in fields:
            fields.insert(insert_at, name)
    row.update({
        "quality_rule_id": QUALITY_RULE_ID,
        "quality_mask_overlay": "pdb_external_quality_masked_contact_target.csv",
        "quality_supported_pair_count": "0",
        "derived_observable_activation_condition": "quality_supported_pair_count>0",
        "derived_observable_gate_state": "quality_mask_frozen_zero_admitted_pairs",
        "measurement_space_xray_capability": "activates_with_coordinate_or_density_generative_AOD_output",
        "coordinate_model_capability": "activates_with_coordinate_generative_AOD_output",
        "derived_contact_capability": "available_contact_pair_set_subject_to_quality_supported_pair_count_positive",
        "target_value_read_status": "not_read_by_measurement_consistency_gate",
        "score_status": "policy_and_quality_mask_gate_only_no_score",
        "release_status": RELEASE,
    })
    write_csv(PROT / "pdb_external_contact_observable_policy.csv", fields, [row])


def materialize_comparison_matrix() -> None:
    fields = [
        "comparison_space","lineage_branch","required_target_support",
        "current_target_support","aod_representation_capability",
        "result_that_may_be_reported","activation_condition",
        "quality_supported_pair_count","current_gate_status",
        "target_values_read_status","score_status","release_status",
    ]
    raw = [
        ["registry","target_measurement","accession_and_method_metadata","available","available","provenance_only","metadata_registered","","active_provenance_only","not_read","no_score",RELEASE],
        ["coordinate_model","target_measurement","coordinate_model_plus_refinement_and_validation_lineage","coordinate_model_hash_locked_refinement_and_local_validation_partial","activates_with_coordinate_generative_AOD_output","model_coordinate_comparison","compatible_coordinate_generative_AOD_output_frozen","","waiting_for_compatible_AOD_representation","not_read","no_score",RELEASE],
        ["derived_observable","target_measurement+aod_prediction","frozen_extraction_policy_and_local_quality_mask","contact_map_available_quality_mask_frozen_zero_supported_pairs","available_contact_pair_set","contact_or_reclosure_residual","quality_supported_pair_count>0","0","quality_mask_frozen_zero_admitted_pairs","not_read","no_score",RELEASE],
        ["measurement_raw","target_measurement","raw_experimental_payload_and_frozen_forward_operator","raw_payload_probe_pending","activates_with_measurement-generative_AOD_output","raw_measurement_residual","raw_payload_byte_lock_and_compatible_operator_frozen","","waiting_for_payload_and_AOD_capability","not_read","no_score",RELEASE],
        ["measurement_processed","target_measurement","processed_experimental_payload_and_frozen_forward_operator","processed_payload_probe_pending","activates_with_measurement-generative_AOD_output","processed_measurement_residual","processed_payload_byte_lock_and_compatible_operator_frozen","","waiting_for_payload_and_AOD_capability","not_read","no_score",RELEASE],
    ]
    write_csv(PROT / "pdb_external_comparison_allowed_matrix.csv", fields, [dict(zip(fields, r)) for r in raw])


def materialize_limitation_budget() -> None:
    rows = read_csv(PROT / "pdb_external_target_limitation_budget.csv")
    for row in rows:
        comp = row["limitation_component"]
        if comp == "local_model_support":
            row["current_state"] = "quality_mask_frozen_zero_quality_supported_pairs"
            row["implication"] = "all_946_coordinate_derived_pair_bits_are_effective_target_abstentions"
            row["resolution_or_gate"] = "validation_payload_byte_lock_and_local_support_ingest"
        elif comp == "aod_prediction_representation":
            row["current_state"] = "contact_pair_set_supports_derived_contact_lane"
            row["implication"] = "measurement_and_coordinate_model_lanes_activate_with_richer_frozen_AOD_outputs"
            row["resolution_or_gate"] = "comparison_space_capability_and_observation_operator_freeze"
        elif comp == "derived_contact_capability":
            row["current_state"] = "quality_mask_frozen_zero_supported_pairs"
            row["implication"] = "derived_contact_residual_activates_when_quality_supported_pair_count_positive"
            row["resolution_or_gate"] = "validation_payload_ingest_and_pair_mask_regeneration"
        row["release_status"] = RELEASE
    write_csv(PROT / "pdb_external_target_limitation_budget.csv", list(rows[0].keys()), rows)


def materialize_quality_manifest() -> None:
    files = {
        "quality_rule_policy": "manual-2/data/protein/pdb_external_quality_rule_policy.csv",
        "residue_quality_mask": "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
        "quality_masked_contact_target": "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
        "quality_masked_contact_summary": "manual-2/data/protein/pdb_external_quality_masked_contact_summary.csv",
        "quality_mask_policy_application": "manual-2/data/protein/pdb_external_quality_mask_policy_application.csv",
        "comparison_join_declaration": "manual-2/data/protein/pdb_external_comparison_join_declaration.csv",
    }
    summary = read_csv(PROT / "pdb_external_quality_masked_contact_summary.csv")[0]
    manifest = {
        "version_scope": VERSION,
        "lane": "pdb_measurement_lineage_consistency_quality_mask_materialization",
        "status": "quality rule frozen before validation parse; target and AOD lineages separated; pair-level ternary mask materialized; no target join or score",
        "source_accession": "1CRN",
        "quality_rule_id": QUALITY_RULE_ID,
        "quality_mask_id": QUALITY_MASK_ID,
        "evaluation_pair_count": summary["evaluation_pair_count"],
        "coordinate_derived_contact_count": summary["coordinate_derived_contact_count"],
        "coordinate_derived_noncontact_count": summary["coordinate_derived_noncontact_count"],
        "quality_supported_pair_count": summary["quality_supported_pair_count"],
        "effective_contact_count": summary["effective_contact_count"],
        "effective_noncontact_count": summary["effective_noncontact_count"],
        "effective_abstain_count": summary["effective_abstain_count"],
        "derived_observable_gate_state": summary["derived_observable_gate_state"],
        "target_value_read_status": "not_joined_to_AOD_prediction",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "files": files,
        "file_sha256": {k: sha(ROOT / v) for k, v in files.items()},
        "next_milestones": [
            "v40.02r22A Validation Report Byte-Lock and Local-Support Ingest Gate",
            "v40.02r22B Reflection / Map Availability Probe and Byte-Lock Gate",
            "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
        ],
    }
    (PROT / "pdb_external_quality_mask_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def update_measurement_manifest() -> None:
    path = PROT / "pdb_external_measurement_manifest.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d.update({
        "version_scope": VERSION,
        "lane": "pdb_measurement_provenance_availability_target_limitation_and_quality_mask_gate",
        "status": "measurement lineage declared with independent target/AOD branches; payload states decomposed; quality rule frozen; pair-level ternary target mask materialized; no target join or score",
        "measurement_architecture": {
            "target_measurement_branch": ["X_physical","M_theta","Y_raw","Q_psi","Y_processed","R_phi","Xhat_model","D_eta","O_derived"],
            "aod_prediction_branch": ["AOD_raw_trace","AOD_freeze","X_AOD_freeze"],
            "comparison_join_id": COMPARISON_JOIN_ID,
        },
        "independent_aod_lane": "pdb_aod_prediction_lineage_GAS_v4002r212",
        "derived_contact_capability": "available_contact_pair_set_subject_to_quality_supported_pair_count_positive",
        "quality_rule_id": QUALITY_RULE_ID,
        "quality_mask_id": QUALITY_MASK_ID,
        "quality_supported_pair_count": "0",
        "effective_target_counts": {"contact": "0", "noncontact": "0", "abstain": "946"},
        "target_value_read_status": "not_joined_to_AOD_prediction",
        "residual_status": "not_computed_in_v40.02r21.2",
        "score_status": "measurement_consistency_quality_mask_gate_only_no_score",
        "next_milestones": [
            "v40.02r22A Validation Report Byte-Lock and Local-Support Ingest Gate",
            "v40.02r22B Reflection / Map Availability Probe and Byte-Lock Gate",
            "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
        ],
    })
    new_files = {
        "quality_rule_policy": "manual-2/data/protein/pdb_external_quality_rule_policy.csv",
        "quality_masked_contact_target": "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
        "quality_masked_contact_summary": "manual-2/data/protein/pdb_external_quality_masked_contact_summary.csv",
        "quality_mask_policy_application": "manual-2/data/protein/pdb_external_quality_mask_policy_application.csv",
        "quality_mask_manifest": "manual-2/data/protein/pdb_external_quality_mask_manifest.json",
        "comparison_join_declaration": "manual-2/data/protein/pdb_external_comparison_join_declaration.csv",
    }
    d.setdefault("files", {}).update(new_files)
    d["file_sha256"] = {k: sha(ROOT / v) for k, v in d["files"].items() if k != "measurement_manifest"}
    d["deferred"] = [
        "validation report byte lock and local-support ingest",
        "reflection or map payload byte lock",
        "comparison-space observation-operator freeze",
        "target O_ij join",
        "external residual score",
        "RMSD","TM-score","GDT","AlphaFold scoring",
        "coordinate-level AOD prediction","released lambda_fold",
        "folding value-map release","biological-function claims",
    ]
    path.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    materialize_measurement_metadata()
    materialize_comparison_join()
    materialize_payload_availability()
    materialize_quality_rule()
    residue_by_label = update_residue_mask()
    materialize_pair_overlay(residue_by_label)
    materialize_contact_policy()
    materialize_comparison_matrix()
    materialize_limitation_budget()
    for name in [
        "pdb_external_experiment_lineage.csv",
        "pdb_external_refinement_validation_metrics.csv",
        "pdb_external_coordinate_use_policy.csv",
        "pdb_external_coordinate_branch_classification.csv",
        "pdb_external_measurement_operator_family_registry.csv",
    ]:
        update_release_status(PROT / name)
    materialize_quality_manifest()
    update_measurement_manifest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
