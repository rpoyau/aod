#!/usr/bin/env python3
"""Declare the PDB measurement-lineage, availability, and limitation gate.

This Manual-II gate reclassifies the carried external PDB coordinate/contact
branch as a coordinate-model / derived-observable fixture and records the
measurement lineage needed before a measurement-space comparison can be
attempted.  It reads no target contact values, changes no AOD prediction row,
and computes no score.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
PAYLOAD = PROT / "external_pdb_payloads" / "1CRN.cif"
ATOM_EXTRACT = PROT / "pdb_external_atom_site_extract.csv"
VERSION = "v40.02r21.2"
RELEASE = "v40.02r21.2_measurement_lineage_consistency_quality_mask_materialization"
ACCESS_DATE = "2026-06-18"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    path = PROT / name
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def scalar_map(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("_"):
            continue
        try:
            parts = shlex.split(line, comments=False, posix=True)
        except ValueError:
            continue
        if len(parts) >= 2 and parts[0] not in out:
            out[parts[0]] = parts[1]
    return out


def val(m: dict[str, str], key: str, fallback: str = "unresolved") -> str:
    v = m.get(key, "")
    return fallback if v in {"", "?", "."} else v


def main() -> int:
    if not PAYLOAD.exists():
        raise FileNotFoundError(PAYLOAD)
    if not ATOM_EXTRACT.exists():
        raise FileNotFoundError(ATOM_EXTRACT)

    cif = scalar_map(PAYLOAD)
    coordinate_sha = sha(PAYLOAD)
    coordinate_bytes = PAYLOAD.stat().st_size

    experiment_fields = [
        "experiment_lineage_id","source_database","source_accession","archive_entry_version","experimental_method",
        "sample_conditions","crystal_conditions","space_group","unit_cell_a","unit_cell_b","unit_cell_c",
        "unit_cell_alpha","unit_cell_beta","unit_cell_gamma","wavelength_angstrom","resolution_low_angstrom",
        "archive_reported_resolution_high_angstrom","citation_reported_resolution_angstrom",
        "citation_resolution_relation_status","crystal_solvent_content_percent","matthews_coefficient",
        "coordinate_payload_path","coordinate_payload_sha256","coordinate_payload_byte_count",
        "coordinate_model_target_class","measurement_truth_status","archive_metadata_source","citation_metadata_source",
        "metadata_access_date","release_status",
    ]
    experiment_row = {
        "experiment_lineage_id": "pdb_measurement_lineage_1CRN_xray_v4002r211",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "archive_entry_version": "1.5",
        "experimental_method": val(cif, "_exptl.method", "X-RAY DIFFRACTION"),
        "sample_conditions": "unresolved_not_reported_in_current_coordinate_payload",
        "crystal_conditions": "unresolved_not_reported_in_current_coordinate_payload",
        "space_group": val(cif, "_symmetry.space_group_name_H-M", "P 1 21 1"),
        "unit_cell_a": val(cif, "_cell.length_a"),
        "unit_cell_b": val(cif, "_cell.length_b"),
        "unit_cell_c": val(cif, "_cell.length_c"),
        "unit_cell_alpha": val(cif, "_cell.angle_alpha"),
        "unit_cell_beta": val(cif, "_cell.angle_beta"),
        "unit_cell_gamma": val(cif, "_cell.angle_gamma"),
        "wavelength_angstrom": val(cif, "_diffrn_radiation_wavelength.wavelength"),
        "resolution_low_angstrom": val(cif, "_refine.ls_d_res_low"),
        "archive_reported_resolution_high_angstrom": val(cif, "_refine.ls_d_res_high", "1.50"),
        "citation_reported_resolution_angstrom": "0.945",
        "citation_resolution_relation_status": "reconciliation_pending",
        "crystal_solvent_content_percent": val(cif, "_exptl_crystal.density_percent_sol"),
        "matthews_coefficient": val(cif, "_exptl_crystal.density_Matthews"),
        "coordinate_payload_path": "manual-2/data/protein/external_pdb_payloads/1CRN.cif",
        "coordinate_payload_sha256": coordinate_sha,
        "coordinate_payload_byte_count": str(coordinate_bytes),
        "coordinate_model_target_class": "coordinate_model_observable_fixture",
        "measurement_truth_status": "coordinate_model_is_reconstruction_not_raw_experiment",
        "archive_metadata_source": "https://www.rcsb.org/structure/1CRN",
        "citation_metadata_source": "https://doi.org/10.1073/pnas.81.19.6014",
        "metadata_access_date": ACCESS_DATE,
        "release_status": RELEASE,
    }
    write_csv("pdb_external_experiment_lineage.csv", experiment_fields, [experiment_row])

    metadata_fields = [
        "measurement_lineage_id","stage_order","stage_name","operator_symbol","input_state","output_state","stage_role",
        "payload_or_schema_status","current_gate_status","target_value_read_status","release_status",
    ]
    metadata_rows = [
        ["pdb_measurement_lineage_1CRN_xray_v4002r211","1","physical_state","identity","X_physical","X_physical","declared physical specimen/state","registry_only","declared_no_target_values_read","not_read",RELEASE],
        ["pdb_measurement_lineage_1CRN_xray_v4002r211","2","measurement_operator","M_theta","X_physical","Y_raw","X-ray diffraction measurement operator","operator_family_registered_payload_schema_unresolved","not_frozen_in_this_gate","not_read",RELEASE],
        ["pdb_measurement_lineage_1CRN_xray_v4002r211","3","processing_operator","Q_psi","Y_raw","Y_processed","data reduction / processing operator","software_and_payload_schema_unresolved","not_frozen_in_this_gate","not_read",RELEASE],
        ["pdb_measurement_lineage_1CRN_xray_v4002r211","4","reconstruction_operator","R_phi","Y_processed","Xhat_model","refinement/reconstruction producing deposited coordinate model","coordinate_model_available_hash_locked","carried_coordinate_model_fixture","not_read",RELEASE],
        ["pdb_measurement_lineage_1CRN_xray_v4002r211","5","derived_observable_operator","D_eta","Xhat_model","O_derived","frozen coordinate-to-contact extraction policy","derived_contact_policy_available_quality_mask_required","policy_declared_no_new_score","not_read",RELEASE],
        ["pdb_measurement_lineage_1CRN_xray_v4002r211","6","independent_aod_lane","AOD_freeze","AOD_raw_trace","X_AOD_freeze","AOD motif/curling-curls/SADAR frozen packet","contact_pair_set","carried_forward_independent_lane","not_read",RELEASE],
    ]
    write_csv("pdb_external_measurement_metadata.csv", metadata_fields, [dict(zip(metadata_fields, r)) for r in metadata_rows])

    availability_fields = [
        "payload_registry_id","source_database","source_accession","payload_type","payload_availability","payload_path_or_probe_url",
        "local_payload_path","payload_sha256","payload_byte_count","probe_url","http_status","content_type","probe_bytes",
        "probe_sha256","probe_utc","archive_source","availability_probe_status","access_control_status","release_status",
    ]
    availability_rows = [
        ["1CRN_coordinate_model_mmcif","RCSB_PDB","1CRN","coordinate_model_mmcif","available_hash_locked","https://files.rcsb.org/download/1CRN.cif","manual-2/data/protein/external_pdb_payloads/1CRN.cif",coordinate_sha,str(coordinate_bytes),"https://files.rcsb.org/download/1CRN.cif","registered_from_local_payload","chemical/x-mmcif","69506",coordinate_sha,"2026-06-18T00:00:00Z","RCSB_PDB","local_byte_payload_registered","public_archive_reference",RELEASE],
        ["1CRN_validation_report_cif","RCSB_PDB","1CRN","validation_report_cif","available_not_locked","https://files.rcsb.org/download/1CRN-validation.cif.gz","","","","https://files.rcsb.org/download/1CRN-validation.cif.gz","not_probed_in_build_environment","unresolved","unresolved","unresolved","not_run","RCSB_PDB","archive_page_lists_validation_download_byte_lock_pending","public_archive_reference",RELEASE],
        ["1CRN_validation_report_xml","RCSB_PDB","1CRN","validation_report_xml","available_not_locked","https://files.rcsb.org/download/1CRN-validation.xml.gz","","","","https://files.rcsb.org/download/1CRN-validation.xml.gz","not_probed_in_build_environment","unresolved","unresolved","unresolved","not_run","RCSB_PDB","archive_page_lists_validation_download_byte_lock_pending","public_archive_reference",RELEASE],
        ["1CRN_structure_factors","RCSB_PDB","1CRN","reflection_payload_structure_factors","unresolved","https://files.rcsb.org/download/1CRN-sf.cif","","","","https://files.rcsb.org/download/1CRN-sf.cif","not_probed_in_build_environment","unresolved","unresolved","unresolved","not_run","RCSB_PDB","direct_archive_probe_required","public_archive_probe_required",RELEASE],
        ["1CRN_structure_factors_gz","RCSB_PDB","1CRN","processed_reflection_payload","unresolved","https://files.rcsb.org/download/1CRN-sf.cif.gz","","","","https://files.rcsb.org/download/1CRN-sf.cif.gz","not_probed_in_build_environment","unresolved","unresolved","unresolved","not_run","RCSB_PDB","direct_archive_probe_required","public_archive_probe_required",RELEASE],
        ["1CRN_map_coefficients","RCSB_PDB","1CRN","map_coefficients","unresolved","canonical_entry_specific_map_endpoint_to_be_probed","","","","canonical_entry_specific_map_endpoint_to_be_probed","not_probed_in_build_environment","unresolved","unresolved","unresolved","not_run","RCSB_PDB","direct_archive_probe_required","public_archive_probe_required",RELEASE],
        ["1CRN_raw_diffraction_images","external_raw_image_registry","1CRN","raw_diffraction_images","unresolved","external_registry_reference_not_declared","","","","external_registry_reference_not_declared","not_probed","unresolved","unresolved","unresolved","not_run","external_optional_registry","optional_external_registry_probe","external_registry_optional",RELEASE],
    ]
    write_csv("pdb_external_experimental_payload_availability.csv", availability_fields, [dict(zip(availability_fields, r)) for r in availability_rows])

    refinement_fields = [
        "refinement_card_id","source_database","source_accession","experimental_method","archive_entry_version",
        "archive_reported_resolution_high","archive_reported_resolution_low","citation_reported_resolution",
        "citation_resolution_relation_status","refinement_software","R_work","R_free","R_free_minus_R_work",
        "completeness","multiplicity","I_over_sigma","merging_statistics","validation_report_availability",
        "global_experiment_quality_state","coordinate_payload_sha256","coordinate_model_target_class",
        "measurement_payload_status","release_status",
    ]
    refinement_row = {
        "refinement_card_id": "pdb_refinement_validation_1CRN_v4002r211",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "experimental_method": "X-RAY DIFFRACTION",
        "archive_entry_version": "1.5",
        "archive_reported_resolution_high": "1.50",
        "archive_reported_resolution_low": val(cif, "_refine.ls_d_res_low"),
        "citation_reported_resolution": "0.945",
        "citation_resolution_relation_status": "reconciliation_pending",
        "refinement_software": "PROLSQ",
        "R_work": val(cif, "_refine.ls_R_factor_R_work"),
        "R_free": val(cif, "_refine.ls_R_factor_R_free"),
        "R_free_minus_R_work": "unresolved",
        "completeness": val(cif, "_refine.ls_percent_reflns_obs"),
        "multiplicity": val(cif, "_refine.ls_redundancy_reflns_obs"),
        "I_over_sigma": val(cif, "_refine.pdbx_ls_sigma_I"),
        "merging_statistics": "unresolved_not_in_current_coordinate_payload",
        "validation_report_availability": "available_not_locked",
        "global_experiment_quality_state": "partially_available_archive_metadata_validation_payload_not_ingested",
        "coordinate_payload_sha256": coordinate_sha,
        "coordinate_model_target_class": "coordinate_model_observable_fixture",
        "measurement_payload_status": "reflection_and_map_payload_availability_unresolved",
        "release_status": RELEASE,
    }
    write_csv("pdb_external_refinement_validation_metrics.csv", refinement_fields, [refinement_row])

    atom_rows = read_csv(ATOM_EXTRACT)
    local_fields = [
        "local_support_id","source_accession","coordinate_payload_sha256","chain_id","model_id","auth_seq_id","label_seq_id",
        "residue_name","occupancy","B_factor","alternate_location_status","missing_density_status","validation_outlier_status",
        "RSRZ","RSCC","RSRZ_status","RSCC_status","local_support_state","quality_mask_state","quality_mask_reason",
        "coordinate_use_status","target_contact_state_policy","release_status",
    ]
    local_rows: list[dict[str, str]] = []
    for r in atom_rows:
        alt = r.get("altloc_id", ".")
        alt_status = "no_alternate_location_on_selected_CA" if alt in {"", ".", "?"} else "alternate_location_present"
        local_rows.append({
            "local_support_id": f"1CRN_A_model1_local_support_label{int(r['label_seq_id']):04d}",
            "source_accession": "1CRN",
            "coordinate_payload_sha256": coordinate_sha,
            "chain_id": r["chain_id"],
            "model_id": r["model_id"],
            "auth_seq_id": r["auth_seq_id"],
            "label_seq_id": r["label_seq_id"],
            "residue_name": r["residue_name"],
            "occupancy": r["occupancy"],
            "B_factor": r["B_iso_or_equiv"],
            "alternate_location_status": alt_status,
            "missing_density_status": "not_assessed_without_validation_or_density_payload",
            "validation_outlier_status": "not_assessed_without_validation_report_ingest",
            "RSRZ": "",
            "RSCC": "",
            "RSRZ_status": "unavailable_validation_payload_not_ingested",
            "RSCC_status": "unavailable_validation_payload_not_ingested",
            "local_support_state": "quality_ambiguous",
            "quality_mask_state": "abstain",
            "quality_mask_reason": "local_model_to_data_support_metrics_not_ingested",
            "coordinate_use_status": "coordinate_model_fixture_available_target_use_requires_quality_mask",
            "target_contact_state_policy": "abstain_until_both_residues_quality_supported",
            "release_status": RELEASE,
        })
    write_csv("pdb_external_residue_quality_mask.csv", local_fields, local_rows)

    coordinate_policy_fields = [
        "coordinate_use_policy_id","source_accession","comparison_space","target_class","coordinate_model_role",
        "coordinate_model_is_raw_experiment","local_support_required","occupancy_semantics","B_factor_semantics",
        "RSRZ_RSCC_semantics","distance_uncertainty_rule","quality_state_domain","current_status","release_status",
    ]
    coordinate_policy_row = {
        "coordinate_use_policy_id": "pdb_coordinate_use_policy_1CRN_v4002r211",
        "source_accession": "1CRN",
        "comparison_space": "coordinate_model",
        "target_class": "coordinate_model_observable_fixture",
        "coordinate_model_role": "deposited_reconstruction_model_for_target_side_observable_extraction",
        "coordinate_model_is_raw_experiment": "false",
        "local_support_required": "true_before_quality_supported_target_decision",
        "occupancy_semantics": "model_occupancy_support_indicator_not_coordinate_standard_error",
        "B_factor_semantics": "displacement_or_disorder_support_indicator_not_coordinate_standard_error",
        "RSRZ_RSCC_semantics": "local_model_to_data_support_indicators_when_validation_payload_is_ingested",
        "distance_uncertainty_rule": "no_distance_interval_from_B_factor_or_occupancy_alone; separately_frozen_uncertainty_model_required",
        "quality_state_domain": "quality_supported|quality_ambiguous|quality_excluded",
        "current_status": "coordinate_model_fixture_active_local_validation_metrics_pending",
        "release_status": RELEASE,
    }
    write_csv("pdb_external_coordinate_use_policy.csv", coordinate_policy_fields, [coordinate_policy_row])

    observable_fields = [
        "observable_policy_id","source_accession","comparison_space","chain","model","assembly","atom_selector","altloc_rule",
        "occupancy_rule","distance_rule","minimum_sequence_separation","sequence_separation_rule","target_state_domain",
        "target_contact_1_rule","target_contact_0_rule","target_abstain_rule","quality_mask","threshold_proximity_policy",
        "uncertainty_interval_policy","aod_prediction_representation","measurement_space_xray_capability",
        "coordinate_model_capability","derived_contact_capability","target_value_read_status","score_status","release_status",
    ]
    observable_row = {
        "observable_policy_id": "pdb_contact_observable_policy_1CRN_A_CA_v4002r211",
        "source_accession": "1CRN",
        "comparison_space": "derived_observable",
        "chain": "A",
        "model": "1",
        "assembly": "asymmetric_unit_chain_A",
        "atom_selector": "CA",
        "altloc_rule": "primary_or_highest_occupancy_altloc",
        "occupancy_rule": "occupancy_recorded_as_support_indicator_not_uncertainty",
        "distance_rule": "euclidean_CA_distance_from_full_precision_coordinates",
        "minimum_sequence_separation": "3",
        "sequence_separation_rule": "abs(label_seq_id_j-label_seq_id_i) >= 3",
        "target_state_domain": "1|0|abstain",
        "target_contact_1_rule": "distance<=8.0A_and_both_residues_quality_supported",
        "target_contact_0_rule": "distance>8.0A_and_both_residues_quality_supported",
        "target_abstain_rule": "either_residue_quality_ambiguous_or_quality_excluded_or_missing_coordinate_or_unresolved_altloc_or_separately_frozen_uncertainty_model_marks_threshold_unresolved",
        "quality_mask": "pdb_external_residue_quality_mask.csv",
        "threshold_proximity_policy": "disabled_until_separately_frozen_uncertainty_model_exists",
        "uncertainty_interval_policy": "B_factor_occupancy_RSRZ_RSCC_are_not_interchangeable_coordinate_standard_errors",
        "aod_prediction_representation": "contact_pair_set",
        "measurement_space_xray_capability": "blocked_by_prediction_representation",
        "coordinate_model_capability": "unavailable_no_coordinate_generative_AOD_output",
        "derived_contact_capability": "available_subject_to_quality_mask",
        "target_value_read_status": "not_read_by_measurement_provenance_gate",
        "score_status": "policy_gate_only_no_new_score",
        "release_status": RELEASE,
    }
    write_csv("pdb_external_contact_observable_policy.csv", observable_fields, [observable_row])

    limitation_fields = [
        "limitation_id","source_accession","limitation_component","current_state","implication","resolution_or_gate",
        "comparison_space","release_status",
    ]
    limitation_rows = [
        ["lim_1CRN_coordinate_target_class","1CRN","coordinate_target_class","coordinate_model_observable_fixture","deposited_coordinates_are_a_reconstruction_model_not_raw_experimental_truth","measurement_lineage_required_for_stronger_claims","coordinate_model",RELEASE],
        ["lim_1CRN_resolution_reconciliation","1CRN","resolution_provenance","archive_1.50A_citation_0.945A_reconciliation_pending","do_not_collapse_values_or_call_contradiction","entry_history_experimental_payload_and_primary_literature_reconciliation_gate","registry",RELEASE],
        ["lim_1CRN_reflection_payload","1CRN","reflection_payload_availability","unresolved","measurement_space_operator_cannot_be_frozen_against_unknown_payload_schema","direct_archive_probe_required","measurement",RELEASE],
        ["lim_1CRN_local_support","1CRN","local_model_support","validation_payload_not_ingested_all_residues_quality_ambiguous","derived_contact_targets_require_abstention_mask","validation_payload_byte_lock_and_local_metric_ingest","derived_observable",RELEASE],
        ["lim_AOD_representation","1CRN","aod_prediction_representation","contact_pair_set","cannot_generate_Fcalc_or_density_without_coordinate_or_density_generative_output","measurement_space_xray_capability_blocked","measurement",RELEASE],
        ["lim_AOD_coordinate_model","1CRN","coordinate_model_capability","unavailable","no_coordinate_model_residual_RMSD_TMscore_GDT","coordinate_generative_AOD_output_required","coordinate_model",RELEASE],
        ["lim_AOD_derived_contact","1CRN","derived_contact_capability","available_subject_to_quality_mask","contact_reclosure_residual_may_be_defined_after_quality_mask_and_gate_freeze","quality_mask_and_abstention_gate_required","derived_observable",RELEASE],
        ["lim_measurement_operator","1CRN","measurement_operator_freeze","not_frozen","operator_freeze_follows_payload_availability_and_byte_lock","r22_then_r23","measurement",RELEASE],
    ]
    write_csv("pdb_external_target_limitation_budget.csv", limitation_fields, [dict(zip(limitation_fields, r)) for r in limitation_rows])

    matrix_fields = [
        "comparison_space","required_target_support","current_target_support","aod_representation_capability","result_that_may_be_reported",
        "current_gate_status","target_values_read_status","score_status","release_status",
    ]
    matrix_rows = [
        ["registry","accession_and_method_metadata","available","available","provenance_only","active_provenance_only","not_read","no_score",RELEASE],
        ["coordinate_model","coordinate_model_plus_refinement_and_validation_lineage","coordinate_model_hash_locked_refinement_and_local_validation_partial","unavailable_no_coordinate_generative_AOD_output","model_coordinate_comparison","blocked_by_AOD_prediction_representation","not_read","no_score",RELEASE],
        ["derived_observable","frozen_extraction_policy_and_local_quality_mask","contact_map_available_local_quality_mask_ambiguous","available_contact_pair_set","contact_or_reclosure_residual","available_after_quality_mask_freeze_no_new_score_in_this_gate","not_read","no_new_score",RELEASE],
        ["measurement","raw_or_processed_experimental_payload_and_frozen_forward_operator","payload_availability_unresolved","blocked_by_prediction_representation","reflection_map_or_restraint_residual","blocked_until_payload_byte_lock_and_operator_capability_freeze","not_read","no_score",RELEASE],
    ]
    write_csv("pdb_external_comparison_allowed_matrix.csv", matrix_fields, [dict(zip(matrix_fields, r)) for r in matrix_rows])

    branch_fields = [
        "branch_row_id","milestone_range","lane_role","target_class","experimental_measurement_truth_status","recomputation_status",
        "current_interpretation","release_status",
    ]
    branch_rows = [
        ["pdb_coordinate_branch_r11_r16","v40.02r11-v40.02r16","accession_coordinate_hash_residue_contact_boundary","coordinate_model_observable_fixture","not_raw_experimental_measurement_truth","not_required","target-side coordinate reconstruction and derived contact boundary",RELEASE],
        ["pdb_coordinate_branch_r17_r21","v40.02r17-v40.02r21","AOD_projection_alignment_state_gates","coordinate_model_observable_fixture","not_raw_experimental_measurement_truth","not_required","zero-coverage alignment and target-join quarantine over coordinate-derived boundary",RELEASE],
        ["pdb_manual_GAS_fixture_branch","v40.02r07-v40.02r10","manual_PDBx_mmcif_style_fixture","coordinate_model_observable_fixture","manual_fixture_not_experimental_truth","not_required","manual target-only contact residual machinery fixture",RELEASE],
    ]
    write_csv("pdb_external_coordinate_branch_classification.csv", branch_fields, [dict(zip(branch_fields, r)) for r in branch_rows])

    operator_fields = [
        "measurement_operator_family","method_status","data_contract_status","quality_semantics","current_branch_status","release_status",
    ]
    operator_rows = [
        ["xray_diffraction","implemented_for_provenance_and_capability_gate","experimental_payload_schema_pending_availability_probe","resolution_Rwork_Rfree_RSRZ_RSCC_method_specific","active_current_branch",RELEASE],
        ["cryo_em","registry_only_deferred","not_implemented","map_model_and_Qscore_semantics_deferred","deferred",RELEASE],
        ["solution_nmr","registry_only_deferred","not_implemented","chemical_shift_and_restraint_semantics_deferred","deferred",RELEASE],
        ["neutron_diffraction","registry_only_deferred","not_implemented","method_specific_semantics_deferred","deferred",RELEASE],
        ["integrative","registry_only_deferred","not_implemented","multi_source_restraint_semantics_deferred","deferred",RELEASE],
    ]
    write_csv("pdb_external_measurement_operator_family_registry.csv", operator_fields, [dict(zip(operator_fields, r)) for r in operator_rows])

    files = {
        "experiment_lineage": "manual-2/data/protein/pdb_external_experiment_lineage.csv",
        "measurement_metadata": "manual-2/data/protein/pdb_external_measurement_metadata.csv",
        "experimental_payload_availability": "manual-2/data/protein/pdb_external_experimental_payload_availability.csv",
        "refinement_validation_metrics": "manual-2/data/protein/pdb_external_refinement_validation_metrics.csv",
        "residue_quality_mask": "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
        "coordinate_use_policy": "manual-2/data/protein/pdb_external_coordinate_use_policy.csv",
        "contact_observable_policy": "manual-2/data/protein/pdb_external_contact_observable_policy.csv",
        "target_limitation_budget": "manual-2/data/protein/pdb_external_target_limitation_budget.csv",
        "comparison_allowed_matrix": "manual-2/data/protein/pdb_external_comparison_allowed_matrix.csv",
        "coordinate_branch_classification": "manual-2/data/protein/pdb_external_coordinate_branch_classification.csv",
        "measurement_operator_family_registry": "manual-2/data/protein/pdb_external_measurement_operator_family_registry.csv",
        "measurement_manifest": "manual-2/data/protein/pdb_external_measurement_manifest.json",
    }
    manifest = {
        "version_scope": VERSION,
        "lane": "pdb_measurement_provenance_availability_target_limitation_gate",
        "status": "measurement_lineage_declared; coordinate branch reclassified as coordinate_model_observable_fixture; reflection/map availability unresolved; no target values read; no score computed",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "archive_entry_version": "1.5",
        "experimental_method": "X-RAY DIFFRACTION",
        "archive_reported_resolution_high": "1.50",
        "citation_reported_resolution": "0.945",
        "citation_resolution_relation_status": "reconciliation_pending",
        "coordinate_payload_sha256": coordinate_sha,
        "coordinate_model_target_class": "coordinate_model_observable_fixture",
        "measurement_architecture": ["X_physical","M_theta","Y_raw","Q_psi","Y_processed","R_phi","Xhat_model","D_eta","O_derived"],
        "independent_aod_lane": "X_AOD_freeze",
        "aod_prediction_representation": "contact_pair_set",
        "measurement_space_xray_capability": "blocked_by_prediction_representation",
        "coordinate_model_capability": "unavailable",
        "derived_contact_capability": "available_subject_to_quality_mask",
        "reflection_payload_available": "unresolved",
        "processed_reflection_available": "unresolved",
        "availability_probe_status": "direct_archive_probe_required",
        "local_support_state_default": "quality_ambiguous",
        "target_contact_state_domain": ["1","0","abstain"],
        "target_value_read_status": "not_read_by_measurement_provenance_gate",
        "residual_status": "not_computed_in_v40.02r21.2",
        "score_status": "provenance_availability_limitation_gate_only_no_score",
        "next_milestones": [
            "v40.02r22A Validation Report Byte-Lock and Local-Support Ingest Gate",
            "v40.02r22B Reflection / Map Availability Probe and Byte-Lock Gate",
            "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
        ],
        "files": files,
        "file_sha256": {k: sha(ROOT / v) for k, v in files.items() if k != "measurement_manifest"},
        "deferred": [
            "reflection or map payload byte lock","measurement-operator freeze","target O_ij join","external residual score",
            "RMSD","TM-score","GDT","AlphaFold scoring","coordinate-level AOD prediction","released lambda_fold",
            "folding value-map release","biological-function claims",
        ],
    }
    (PROT / "pdb_external_measurement_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    from materialize_external_pdb_measurement_consistency_gate import main as materialize_consistency
    return materialize_consistency()


if __name__ == "__main__":
    raise SystemExit(main())
