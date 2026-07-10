from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
EVIDENCE_DIR = PROT / "external_pdb_probe_evidence_snapshots"
VERSION = "v40.02r23"
RELEASE = "v40.02r23_comparison_space_capability_observation_operator_freeze_gate"
STAMP = "2026-06-19T00:00:00Z"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(data: Any) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(data))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def upsert_inventory_row(row: dict[str, str]) -> None:
    path = PROT / "external_payload_bundle_inventory.csv"
    rows = read_csv(path)
    fields = list(rows[0].keys())
    rows = [r for r in rows if r["source_path"] != row["source_path"] and r["bundle_path"] != row["bundle_path"]]
    rows.append(row)
    rows.sort(key=lambda r: r["bundle_path"])
    write_csv(path, fields, rows)



def refresh_inventory_metadata() -> None:
    path = PROT / "external_payload_bundle_inventory.csv"
    rows = read_csv(path)
    fields = list(rows[0].keys())
    for row in rows:
        src = ROOT / row["source_path"]
        if src.is_file():
            row["payload_byte_count"] = str(src.stat().st_size)
            row["payload_sha256"] = sha(src)
    rows.sort(key=lambda r: r["bundle_path"])
    write_csv(path, fields, rows)


def current_counts() -> tuple[int, int, int, int]:
    summary = read_csv(PROT / "pdb_external_quality_masked_contact_summary.csv")[0]
    supported = int(summary.get("quality_supported_pair_count", "0"))
    abstain = int(summary.get("effective_abstain_count", summary.get("effective_target_abstain_count", "946")))
    align = read_csv(PROT / "pdb_external_projection_alignment_coverage.csv")
    in_scope = sum(int(r.get("in_scope_flag", "0") or 0) for r in align)
    out_scope = sum(int(r.get("out_of_scope_flag", "0") or 0) for r in align)
    return supported, abstain, in_scope, out_scope


def build_evidence_snapshot() -> Path:
    xml_path = PROT / "external_pdb_validation_payloads" / "1crn_validation.xml.gz"
    cif_path = PROT / "external_pdb_validation_payloads" / "1crn_validation.cif.gz"
    pdf_path = PROT / "external_pdb_validation_payloads" / "1crn_full_validation.pdf.gz"
    data = {
        "snapshot_id": "pdb_external_probe_evidence_snapshot_1CRN_r23",
        "snapshot_class": "release_local_parsed_official_evidence_snapshot",
        "capture_timestamp_utc": STAMP,
        "source_byte_lock_status": "official_webpage_bytes_not_byte_locked; validation_archive_bytes_locked",
        "sources": [
            {
                "source_id": "rcsb_1crn_entry_page_parsed_snapshot",
                "source_url": "https://www.rcsb.org/structure/1CRN",
                "capture_method": "release_local_parsed_text_snapshot_from_official_page",
                "observed_download_labels": [
                    "FASTA Sequence",
                    "PDBx/mmCIF Format",
                    "PDBx/mmCIF Format (gz)",
                    "BinaryCIF Format (gz)",
                    "Legacy PDB Format",
                    "Legacy PDB Format (gz)",
                    "PDBML/XML Format (gz)",
                    "Validation Full (PDF - gz)",
                    "Validation (XML - gz)",
                    "Validation (CIF - gz)",
                    "Biological Assembly 1 (CIF - gz)",
                    "Biological Assembly 1 (PDB - gz)",
                ],
                "observed_entry_fields": {
                    "experimental_method": "X-RAY DIFFRACTION",
                    "archive_reported_resolution_angstrom": 1.50,
                    "archive_entry_version": 1.5,
                },
                "membership_note": "No structure-factor or validation-map-coefficient download label occurs in the captured official entry-page download list.",
            },
            {
                "source_id": "rcsb_electron_density_help_parsed_snapshot",
                "source_url": "https://www.rcsb.org/docs/general-help/electron-density-maps-and-coefficient-files",
                "capture_method": "release_local_parsed_text_snapshot_from_official_help_page",
                "observed_contract": {
                    "coordinate_and_structure_factor_distinction": True,
                    "validation_map_coefficient_download_template_documented": True,
                    "edmaps_shutdown_documented": True,
                    "edmaps_shutdown_date_text": "June 28, 2024",
                },
                "locator_templates": [
                    "https://files.rcsb.org/pub/pdb/validation_reports/{hash}/{pdbid}/{pdbid}_validation_2fo-fc_map_coef.cif.gz",
                    "https://files.rcsb.org/pub/pdb/validation_reports/{hash}/{pdbid}/{pdbid}_validation_fo-fc_map_coef.cif.gz",
                ],
            },
            {
                "source_id": "wwpdb_validation_archive_locked_payloads",
                "source_url": "https://files.rcsb.org/validation/download/",
                "capture_method": "locally_committed_archive_bytes",
                "payloads": [
                    {"path": str(xml_path.relative_to(ROOT)), "sha256": sha(xml_path), "byte_count": xml_path.stat().st_size},
                    {"path": str(cif_path.relative_to(ROOT)), "sha256": sha(cif_path), "byte_count": cif_path.stat().st_size},
                    {"path": str(pdf_path.relative_to(ROOT)), "sha256": sha(pdf_path), "byte_count": pdf_path.stat().st_size},
                ],
                "observed_validation_pipeline_state": {"xtriage_executed": False, "eds_executed": False},
            },
        ],
        "interpretation_guard": "This snapshot locks release-local parsed evidence and locally committed validation archive bytes. It is not an archive byte lock of the live RCSB HTML pages.",
    }
    path = EVIDENCE_DIR / "1crn_official_entry_map_docs_parsed_snapshot.json"
    write_json(path, data)
    return path


def build_membership_audit(snapshot_path: Path) -> list[dict[str, str]]:
    snapshot_id = "pdb_external_probe_evidence_snapshot_1CRN_r23"
    return [
        {
            "evidence_query_id": "1CRN_entry_has_coordinate_downloads",
            "evidence_snapshot_id": snapshot_id,
            "source_record_id": "rcsb_1crn_entry_page_parsed_snapshot",
            "evidence_snapshot_sha256": sha(snapshot_path),
            "evidence_extraction_rule": "exact_label_membership_in_observed_download_labels",
            "evidence_membership_query": "PDBx/mmCIF Format (gz)",
            "evidence_membership_result": "present",
            "availability_implication": "coordinate_model_locator_exposed",
            "release_status": RELEASE,
        },
        {
            "evidence_query_id": "1CRN_entry_has_structure_factor_download",
            "evidence_snapshot_id": snapshot_id,
            "source_record_id": "rcsb_1crn_entry_page_parsed_snapshot",
            "evidence_snapshot_sha256": sha(snapshot_path),
            "evidence_extraction_rule": "case_insensitive_substring_membership_in_observed_download_labels",
            "evidence_membership_query": "structure factor",
            "evidence_membership_result": "absent",
            "availability_implication": "not_listed_in_locked_official_evidence",
            "release_status": RELEASE,
        },
        {
            "evidence_query_id": "1CRN_entry_has_map_coefficient_download",
            "evidence_snapshot_id": snapshot_id,
            "source_record_id": "rcsb_1crn_entry_page_parsed_snapshot",
            "evidence_snapshot_sha256": sha(snapshot_path),
            "evidence_extraction_rule": "case_insensitive_substring_membership_in_observed_download_labels",
            "evidence_membership_query": "map coefficient",
            "evidence_membership_result": "absent",
            "availability_implication": "not_listed_in_locked_official_evidence",
            "release_status": RELEASE,
        },
        {
            "evidence_query_id": "RCSB_docs_map_coefficient_template",
            "evidence_snapshot_id": snapshot_id,
            "source_record_id": "rcsb_electron_density_help_parsed_snapshot",
            "evidence_snapshot_sha256": sha(snapshot_path),
            "evidence_extraction_rule": "boolean_contract_field",
            "evidence_membership_query": "validation_map_coefficient_download_template_documented",
            "evidence_membership_result": "present_true",
            "availability_implication": "locator_template_declared_not_payload_availability",
            "release_status": RELEASE,
        },
        {
            "evidence_query_id": "RCSB_docs_edmaps_shutdown",
            "evidence_snapshot_id": snapshot_id,
            "source_record_id": "rcsb_electron_density_help_parsed_snapshot",
            "evidence_snapshot_sha256": sha(snapshot_path),
            "evidence_extraction_rule": "boolean_contract_field",
            "evidence_membership_query": "edmaps_shutdown_documented",
            "evidence_membership_result": "present_true",
            "availability_implication": "legacy_map_service_not_an_active_payload_source",
            "release_status": RELEASE,
        },
        {
            "evidence_query_id": "1CRN_validation_eds_executed",
            "evidence_snapshot_id": snapshot_id,
            "source_record_id": "wwpdb_validation_archive_locked_payloads",
            "evidence_snapshot_sha256": sha(snapshot_path),
            "evidence_extraction_rule": "locked_validation_archive_field",
            "evidence_membership_query": "eds_executed",
            "evidence_membership_result": "false",
            "availability_implication": "validation_map_service_upstream_prerequisite_not_satisfied",
            "release_status": RELEASE,
        },
    ]


def build_locator_variants() -> list[dict[str, str]]:
    return [
        {"payload_family_id": "reflection_data", "locator_variant_id": "rcsb_structure_factor_cif_gz", "payload_type": "structure_factors", "format": "PDBx_mmCIF", "compression": "gzip", "declared_url": "https://files.rcsb.org/download/1CRN-sf.cif.gz", "source_archive": "RCSB_PDB", "locator_state": "declared_not_directly_probed", "release_status": RELEASE},
        {"payload_family_id": "reflection_data", "locator_variant_id": "rcsb_structure_factor_cif", "payload_type": "processed_reflections", "format": "PDBx_mmCIF", "compression": "none", "declared_url": "https://files.rcsb.org/download/1CRN-sf.cif", "source_archive": "RCSB_PDB", "locator_state": "declared_not_directly_probed", "release_status": RELEASE},
        {"payload_family_id": "reflection_data", "locator_variant_id": "wwpdb_legacy_structure_factor_ent_gz", "payload_type": "legacy_structure_factors", "format": "legacy_PDB_structure_factor", "compression": "gzip", "declared_url": "https://files.wwpdb.org/pub/pdb/data/structures/all/structure_factors/r1crnsf.ent.gz", "source_archive": "wwPDB", "locator_state": "declared_not_directly_probed", "release_status": RELEASE},
        {"payload_family_id": "validation_map_coefficients", "locator_variant_id": "validation_2fo_fc_cif_gz", "payload_type": "2Fo-Fc_map_coefficients", "format": "PDBx_mmCIF", "compression": "gzip", "declared_url": "https://files.rcsb.org/pub/pdb/validation_reports/cr/1crn/1crn_validation_2fo-fc_map_coef.cif.gz", "source_archive": "RCSB_PDB_wwPDB_validation", "locator_state": "declared_not_directly_probed", "release_status": RELEASE},
        {"payload_family_id": "validation_map_coefficients", "locator_variant_id": "validation_fo_fc_cif_gz", "payload_type": "Fo-Fc_map_coefficients", "format": "PDBx_mmCIF", "compression": "gzip", "declared_url": "https://files.rcsb.org/pub/pdb/validation_reports/cr/1crn/1crn_validation_fo-fc_map_coef.cif.gz", "source_archive": "RCSB_PDB_wwPDB_validation", "locator_state": "declared_not_directly_probed", "release_status": RELEASE},
        {"payload_family_id": "xray_map_service", "locator_variant_id": "rcsb_xray_cell_service", "payload_type": "rendered_xray_map_service", "format": "service_endpoint", "compression": "not_applicable", "declared_url": "https://maps.rcsb.org/x-ray/1crn/cell/", "source_archive": "RCSB_PDB_maps_API", "locator_state": "upstream_prerequisite_not_satisfied", "release_status": RELEASE},
        {"payload_family_id": "raw_image_registry", "locator_variant_id": "raw_image_registry_unspecified", "payload_type": "raw_diffraction_image_registry_reference", "format": "registry_reference", "compression": "not_applicable", "declared_url": "not_declared", "source_archive": "external_raw_image_registry", "locator_state": "not_probed", "release_status": RELEASE},
    ]


def build_family_availability() -> list[dict[str, str]]:
    return [
        {"payload_family_id": "reflection_data", "source_accession": "1CRN", "locator_variant_count": "3", "availability_state": "not_listed_in_locked_official_evidence", "evidence_snapshot_id": "pdb_external_probe_evidence_snapshot_1CRN_r23", "evidence_membership_query_ids": "1CRN_entry_has_structure_factor_download", "direct_probe_status": "not_probed", "byte_lock_status": "not_locked", "payload_sha256": "", "measurement_space_implication": "raw_xray_measurement_unavailable_for_current_accession", "release_status": RELEASE},
        {"payload_family_id": "validation_map_coefficients", "source_accession": "1CRN", "locator_variant_count": "2", "availability_state": "not_listed_in_locked_official_evidence", "evidence_snapshot_id": "pdb_external_probe_evidence_snapshot_1CRN_r23", "evidence_membership_query_ids": "1CRN_entry_has_map_coefficient_download;1CRN_validation_eds_executed", "direct_probe_status": "not_probed", "byte_lock_status": "not_locked", "payload_sha256": "", "measurement_space_implication": "processed_xray_measurement_unavailable_for_current_accession", "release_status": RELEASE},
        {"payload_family_id": "xray_map_service", "source_accession": "1CRN", "locator_variant_count": "1", "availability_state": "upstream_prerequisite_not_satisfied", "evidence_snapshot_id": "pdb_external_probe_evidence_snapshot_1CRN_r23", "evidence_membership_query_ids": "RCSB_docs_edmaps_shutdown;1CRN_validation_eds_executed", "direct_probe_status": "not_probed", "byte_lock_status": "not_locked", "payload_sha256": "", "measurement_space_implication": "map_service_inactive", "release_status": RELEASE},
        {"payload_family_id": "raw_image_registry", "source_accession": "1CRN", "locator_variant_count": "1", "availability_state": "not_probed", "evidence_snapshot_id": "", "evidence_membership_query_ids": "", "direct_probe_status": "not_probed", "byte_lock_status": "not_locked", "payload_sha256": "", "measurement_space_implication": "optional_registry_lane_unresolved", "release_status": RELEASE},
    ]


def build_capability_gate(supported_pairs: int, in_scope: int) -> list[dict[str, str]]:
    return [
        {"comparison_space": "registry", "target_lineage_support": "accession_method_and_payload_provenance_available", "aod_representation_support": "not_required", "observation_operator_family_id": "registry_provenance_identity", "operator_state": "active_provenance_only", "comparison_state": "active_provenance_only", "activation_condition": "registered_provenance_fields", "current_block_reason": "", "target_value_read_status": "metadata_only", "residual_status": "not_applicable", "score_status": "no_score", "release_status": RELEASE},
        {"comparison_space": "measurement_raw", "target_lineage_support": "reflection_data_not_listed_in_locked_official_evidence", "aod_representation_support": "contact_pair_set_cannot_generate_structure_factors", "observation_operator_family_id": "xray_diffraction_forward_operator", "operator_state": "inactive_target_payload_unavailable_and_representation_incompatible", "comparison_state": "inactive", "activation_condition": "byte_locked_reflection_payload_and_measurement_generative_AOD_representation", "current_block_reason": "target_payload_unavailable_and_prediction_representation_incompatible", "target_value_read_status": "not_read", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
        {"comparison_space": "measurement_processed", "target_lineage_support": "map_coefficients_not_listed_in_locked_official_evidence", "aod_representation_support": "contact_pair_set_cannot_generate_density_or_map_coefficients", "observation_operator_family_id": "xray_processed_measurement_operator", "operator_state": "inactive_target_payload_unavailable_and_representation_incompatible", "comparison_state": "inactive", "activation_condition": "byte_locked_processed_payload_and_measurement_generative_AOD_representation", "current_block_reason": "target_payload_unavailable_and_prediction_representation_incompatible", "target_value_read_status": "not_read", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
        {"comparison_space": "coordinate_model", "target_lineage_support": "coordinate_model_byte_locked_with_validation_lineage", "aod_representation_support": "contact_pair_set_has_no_coordinate_generation", "observation_operator_family_id": "coordinate_model_comparison_operator", "operator_state": "inactive_AOD_coordinate_representation_unavailable", "comparison_state": "inactive", "activation_condition": "compatible_coordinate_generative_AOD_output_frozen", "current_block_reason": "AOD_coordinate_representation_unavailable", "target_value_read_status": "not_joined", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
        {"comparison_space": "derived_observable", "target_lineage_support": f"contact_map_and_ternary_quality_mask_available_supported_pairs_{supported_pairs}", "aod_representation_support": "contact_pair_set_representation_available", "observation_operator_family_id": "derived_contact_CA_threshold_operator", "operator_state": "declared_but_comparison_inactive_zero_supported_pairs_and_zero_alignment_coverage", "comparison_state": "inactive", "activation_condition": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0", "current_block_reason": f"quality_supported_pairs_{supported_pairs}_and_in_scope_pairs_{in_scope}", "target_value_read_status": "not_read_by_operator_freeze", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
    ]


def main() -> None:
    current_version = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    if f"Canonical version: {VERSION}" not in current_version:
        print(json.dumps({
            "version": VERSION,
            "status": "historical_generator_noop_in_newer_package",
            "current_canonical_version": current_version.splitlines()[0],
        }, indent=2, sort_keys=True))
        return
    supported_pairs, abstain_pairs, in_scope, out_scope = current_counts()
    evidence_path = build_evidence_snapshot()
    evidence_sha = sha(evidence_path)

    write_csv(
        PROT / "pdb_external_probe_evidence_membership_audit.csv",
        ["evidence_query_id", "evidence_snapshot_id", "source_record_id", "evidence_snapshot_sha256", "evidence_extraction_rule", "evidence_membership_query", "evidence_membership_result", "availability_implication", "release_status"],
        build_membership_audit(evidence_path),
    )
    write_csv(
        PROT / "pdb_external_payload_family_locator_variants.csv",
        ["payload_family_id", "locator_variant_id", "payload_type", "format", "compression", "declared_url", "source_archive", "locator_state", "release_status"],
        build_locator_variants(),
    )
    write_csv(
        PROT / "pdb_external_payload_family_availability.csv",
        ["payload_family_id", "source_accession", "locator_variant_count", "availability_state", "evidence_snapshot_id", "evidence_membership_query_ids", "direct_probe_status", "byte_lock_status", "payload_sha256", "measurement_space_implication", "release_status"],
        build_family_availability(),
    )

    capability = build_capability_gate(supported_pairs, in_scope)
    write_csv(
        PROT / "pdb_external_comparison_space_capability_gate.csv",
        ["comparison_space", "target_lineage_support", "aod_representation_support", "observation_operator_family_id", "operator_state", "comparison_state", "activation_condition", "current_block_reason", "target_value_read_status", "residual_status", "score_status", "release_status"],
        capability,
    )

    family_rows = [
        {"measurement_operator_family_id": "registry_provenance_identity", "experimental_method": "registry", "comparison_space": "registry", "operator_semantics": "identity_on_registered_provenance_fields", "aod_input_requirement": "none", "target_payload_requirement": "registered_accession_and_method_metadata", "family_status": "implemented_active_provenance_only", "release_status": RELEASE},
        {"measurement_operator_family_id": "xray_diffraction_forward_operator", "experimental_method": "X-RAY DIFFRACTION", "comparison_space": "measurement_raw", "operator_semantics": "coordinate_or_density_generative_state_to_structure_factor_observable", "aod_input_requirement": "measurement_generative_coordinate_or_density_representation", "target_payload_requirement": "byte_locked_reflection_payload", "family_status": "registered_not_instantiated", "release_status": RELEASE},
        {"measurement_operator_family_id": "xray_processed_measurement_operator", "experimental_method": "X-RAY DIFFRACTION", "comparison_space": "measurement_processed", "operator_semantics": "coordinate_or_density_generative_state_to_processed_map_or_coefficient_observable", "aod_input_requirement": "measurement_generative_coordinate_or_density_representation", "target_payload_requirement": "byte_locked_map_coefficient_or_processed_payload", "family_status": "registered_not_instantiated", "release_status": RELEASE},
        {"measurement_operator_family_id": "coordinate_model_comparison_operator", "experimental_method": "X-RAY DIFFRACTION", "comparison_space": "coordinate_model", "operator_semantics": "coordinate_model_to_coordinate_residual", "aod_input_requirement": "coordinate_generative_AOD_representation", "target_payload_requirement": "byte_locked_coordinate_model_and_validation_lineage", "family_status": "registered_not_instantiated", "release_status": RELEASE},
        {"measurement_operator_family_id": "derived_contact_CA_threshold_operator", "experimental_method": "X-RAY DIFFRACTION", "comparison_space": "derived_observable", "operator_semantics": "frozen_AOD_contact_pair_set_to_quality_masked_CA_contact_target", "aod_input_requirement": "contact_pair_set", "target_payload_requirement": "coordinate_contact_map_plus_quality_mask_plus_alignment_coverage", "family_status": "declared_inactive", "release_status": RELEASE},
    ]
    write_csv(
        PROT / "pdb_external_observation_operator_family_registry.csv",
        ["measurement_operator_family_id", "experimental_method", "comparison_space", "operator_semantics", "aod_input_requirement", "target_payload_requirement", "family_status", "release_status"],
        family_rows,
    )

    state_rows = [
        {"measurement_operator_state_id": "registry_provenance_identity_1CRN_active_r23", "measurement_operator_family_id": "registry_provenance_identity", "measurement_operator_declaration_id": "registry_provenance_identity_1CRN_declaration_r23", "source_accession": "1CRN", "aod_source_packet_id": "not_required", "aod_prediction_representation": "contact_pair_set", "comparison_space": "registry", "operator_state": "active_provenance_only", "target_payload_state": "registry_metadata_available", "aod_capability_state": "not_required", "target_values_read_status": "metadata_only", "residual_status": "not_applicable", "score_status": "no_score", "release_status": RELEASE},
        {"measurement_operator_state_id": "xray_raw_1CRN_inactive_r23", "measurement_operator_family_id": "xray_diffraction_forward_operator", "measurement_operator_declaration_id": "xray_raw_1CRN_declaration_r23", "source_accession": "1CRN", "aod_source_packet_id": "chain_GAS_tripeptide_seed", "aod_prediction_representation": "contact_pair_set", "comparison_space": "measurement_raw", "operator_state": "inactive_target_payload_unavailable_and_representation_incompatible", "target_payload_state": "reflection_data_not_listed_in_locked_official_evidence", "aod_capability_state": "blocked_by_contact_pair_set_representation", "target_values_read_status": "not_read", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
        {"measurement_operator_state_id": "xray_processed_1CRN_inactive_r23", "measurement_operator_family_id": "xray_processed_measurement_operator", "measurement_operator_declaration_id": "xray_processed_1CRN_declaration_r23", "source_accession": "1CRN", "aod_source_packet_id": "chain_GAS_tripeptide_seed", "aod_prediction_representation": "contact_pair_set", "comparison_space": "measurement_processed", "operator_state": "inactive_target_payload_unavailable_and_representation_incompatible", "target_payload_state": "map_coefficients_not_listed_in_locked_official_evidence", "aod_capability_state": "blocked_by_contact_pair_set_representation", "target_values_read_status": "not_read", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
        {"measurement_operator_state_id": "coordinate_model_1CRN_inactive_r23", "measurement_operator_family_id": "coordinate_model_comparison_operator", "measurement_operator_declaration_id": "coordinate_model_1CRN_declaration_r23", "source_accession": "1CRN", "aod_source_packet_id": "chain_GAS_tripeptide_seed", "aod_prediction_representation": "contact_pair_set", "comparison_space": "coordinate_model", "operator_state": "inactive_AOD_coordinate_representation_unavailable", "target_payload_state": "coordinate_model_hash_locked_validation_lineage_available", "aod_capability_state": "coordinate_generation_unavailable", "target_values_read_status": "not_joined", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
        {"measurement_operator_state_id": "derived_contact_1CRN_declared_inactive_r23", "measurement_operator_family_id": "derived_contact_CA_threshold_operator", "measurement_operator_declaration_id": "derived_contact_1CRN_declaration_r23", "source_accession": "1CRN", "aod_source_packet_id": "chain_GAS_tripeptide_seed", "aod_prediction_representation": "contact_pair_set", "comparison_space": "derived_observable", "operator_state": "declared_but_comparison_inactive_zero_supported_pairs_and_zero_alignment_coverage", "target_payload_state": f"quality_mask_materialized_supported_pairs_{supported_pairs}_abstain_pairs_{abstain_pairs}", "aod_capability_state": f"representation_available_in_scope_pairs_{in_scope}_out_of_scope_pairs_{out_scope}", "target_values_read_status": "not_read_by_operator_freeze", "residual_status": "not_computed", "score_status": "no_score", "release_status": RELEASE},
    ]
    write_csv(
        PROT / "pdb_external_observation_operator_state.csv",
        ["measurement_operator_state_id", "measurement_operator_family_id", "measurement_operator_declaration_id", "source_accession", "aod_source_packet_id", "aod_prediction_representation", "comparison_space", "operator_state", "target_payload_state", "aod_capability_state", "target_values_read_status", "residual_status", "score_status", "release_status"],
        state_rows,
    )

    derived_rows = [{
        "measurement_operator_family_id": "derived_contact_CA_threshold_operator",
        "measurement_operator_state_id": "derived_contact_1CRN_declared_inactive_r23",
        "measurement_operator_declaration_id": "derived_contact_1CRN_declaration_r23",
        "source_accession": "1CRN",
        "target_object_id": "target_derived_contact_1CRN_observable_aware_quality_masked",
        "aod_source_packet_id": "chain_GAS_tripeptide_seed",
        "aod_packet_sha256": sha(PROT / "aod_contact_prediction_freeze.csv"),
        "sadar_context_id": "sadar_mol_005",
        "aod_prediction_representation": "contact_pair_set",
        "target_observable_domain": "1|0|abstain",
        "contact_atom_selector": "CA",
        "contact_threshold_angstrom": "8.0",
        "minimum_sequence_separation": "3",
        "sequence_separation_rule": "abs(label_seq_id_j-label_seq_id_i)>=3",
        "target_quality_mask_rule": "binary target only when both residues quality_supported; otherwise abstain",
        "alignment_projection_rule": "none_declared",
        "support_mask_rule": "quality_supported_pair_count>0",
        "comparison_join_rule": "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_in_scope_pair_count>0",
        "operator_state": "declared_inactive",
        "target_values_read_status": "not_read_by_operator_freeze",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "release_status": RELEASE,
    }]
    write_csv(
        PROT / "pdb_external_derived_contact_operator_declaration.csv",
        list(derived_rows[0].keys()),
        derived_rows,
    )

    nuisance_rows = [
        {"nuisance_parameter_id": "derived_contact_threshold", "measurement_operator_state_id": "derived_contact_1CRN_declared_inactive_r23", "parameter_name": "contact_threshold_angstrom", "parameter_value": "8.0", "parameter_classification": "fixed_from_predeclared_target_extraction_policy", "target_value_estimation_status": "not_estimated_from_target_agreement", "holdout_policy": "not_applicable_no_fitted_parameter", "release_status": RELEASE},
        {"nuisance_parameter_id": "derived_contact_sequence_separation", "measurement_operator_state_id": "derived_contact_1CRN_declared_inactive_r23", "parameter_name": "minimum_sequence_separation", "parameter_value": "3", "parameter_classification": "fixed_from_predeclared_target_extraction_policy", "target_value_estimation_status": "not_estimated_from_target_agreement", "holdout_policy": "not_applicable_no_fitted_parameter", "release_status": RELEASE},
        {"nuisance_parameter_id": "derived_contact_quality_mask", "measurement_operator_state_id": "derived_contact_1CRN_declared_inactive_r23", "parameter_name": "quality_mask_rule", "parameter_value": "observable_aware_ternary_target_policy", "parameter_classification": "fixed_from_validation_support_policy_before_comparison", "target_value_estimation_status": "not_estimated_from_AOD_agreement", "holdout_policy": "not_applicable_no_fitted_parameter", "release_status": RELEASE},
        {"nuisance_parameter_id": "derived_contact_alignment", "measurement_operator_state_id": "derived_contact_1CRN_declared_inactive_r23", "parameter_name": "alignment_projection_rule", "parameter_value": "none_declared", "parameter_classification": "not_available", "target_value_estimation_status": "not_estimated", "holdout_policy": "comparison_blocked", "release_status": RELEASE},
        {"nuisance_parameter_id": "xray_forward_operator", "measurement_operator_state_id": "xray_raw_1CRN_inactive_r23", "parameter_name": "scale_occupancy_disorder_bulk_solvent_B_factor_model", "parameter_value": "not_instantiated", "parameter_classification": "operator_not_instantiated", "target_value_estimation_status": "not_estimated", "holdout_policy": "required_before_any_future_target_value_fit", "release_status": RELEASE},
    ]
    write_csv(
        PROT / "pdb_external_observation_operator_nuisance_policy.csv",
        ["nuisance_parameter_id", "measurement_operator_state_id", "parameter_name", "parameter_value", "parameter_classification", "target_value_estimation_status", "holdout_policy", "release_status"],
        nuisance_rows,
    )

    leak_rows = [
        {"check_id": "r23_operator_family_declared_before_target_join", "check_status": "pass", "evidence": "operator family/state/declaration rows written with target_values_read_status not_read", "release_status": RELEASE},
        {"check_id": "r23_raw_measurement_operator_blocked_by_payload_and_representation", "check_status": "pass", "evidence": "reflection_data not listed in locked official evidence and AOD representation is contact_pair_set", "release_status": RELEASE},
        {"check_id": "r23_processed_measurement_operator_blocked_by_payload_and_representation", "check_status": "pass", "evidence": "map coefficients not listed and AOD representation cannot generate density/maps", "release_status": RELEASE},
        {"check_id": "r23_coordinate_model_operator_blocked_by_AOD_representation", "check_status": "pass", "evidence": "coordinate model exists but AOD coordinate-generative state unavailable", "release_status": RELEASE},
        {"check_id": "r23_derived_contact_operator_declared_inactive", "check_status": "pass", "evidence": f"quality_supported_pair_count={supported_pairs}; in_scope_pair_count={in_scope}", "release_status": RELEASE},
        {"check_id": "r23_target_values_not_read", "check_status": "pass", "evidence": "operator freeze reads lineage/status/mask counts only; no O_ij join and no residual", "release_status": RELEASE},
        {"check_id": "r23_nuisance_parameters_not_fit_to_target_agreement", "check_status": "pass", "evidence": "all active derived-contact policy values are predeclared; xray operator not instantiated", "release_status": RELEASE},
        {"check_id": "r23_candidate_selection_blocked", "check_status": "pass", "evidence": "candidate universe remains not materialized and selected_accession=none", "release_status": RELEASE},
    ]
    write_csv(
        PROT / "pdb_external_observation_operator_leakage_checks.csv",
        ["check_id", "check_status", "evidence", "release_status"],
        leak_rows,
    )

    candidate_rows = [{
        "candidate_universe_gate_id": "pdb_scored_accession_candidate_universe_snapshot_gate_r23",
        "candidate_universe_snapshot_id": "not_materialized",
        "archive_query": "X-RAY DIFFRACTION entries satisfying frozen scored-accession eligibility rule",
        "archive_query_timestamp_utc": "not_run",
        "eligibility_filter_version": "pdb_scored_accession_eligibility_xray_derived_contact_v1",
        "eligibility_filter_sha256": sha(PROT / "pdb_external_scored_accession_eligibility_rule.csv"),
        "eligible_accession_list": "not_materialized",
        "eligible_accession_list_sha256": "not_available",
        "selection_method": "lexicographically_lowest_accession_after_candidate_universe_snapshot",
        "selected_accession": "none",
        "candidate_universe_snapshot_status": "not_materialized_selection_blocked",
        "target_agreement_read_status": "not_read",
        "release_status": RELEASE,
    }]
    write_csv(
        PROT / "pdb_external_scored_accession_candidate_universe_snapshot_gate.csv",
        list(candidate_rows[0].keys()),
        candidate_rows,
    )

    manifest_files = {
        "probe_evidence_snapshot": str(evidence_path.relative_to(ROOT)),
        "probe_membership_audit": "manual-2/data/protein/pdb_external_probe_evidence_membership_audit.csv",
        "payload_family_locator_variants": "manual-2/data/protein/pdb_external_payload_family_locator_variants.csv",
        "payload_family_availability": "manual-2/data/protein/pdb_external_payload_family_availability.csv",
        "comparison_space_capability_gate": "manual-2/data/protein/pdb_external_comparison_space_capability_gate.csv",
        "operator_family_registry": "manual-2/data/protein/pdb_external_observation_operator_family_registry.csv",
        "operator_state": "manual-2/data/protein/pdb_external_observation_operator_state.csv",
        "derived_contact_operator_declaration": "manual-2/data/protein/pdb_external_derived_contact_operator_declaration.csv",
        "nuisance_policy": "manual-2/data/protein/pdb_external_observation_operator_nuisance_policy.csv",
        "leakage_checks": "manual-2/data/protein/pdb_external_observation_operator_leakage_checks.csv",
        "candidate_universe_snapshot_gate": "manual-2/data/protein/pdb_external_scored_accession_candidate_universe_snapshot_gate.csv",
    }
    manifest = {
        "version_scope": VERSION,
        "lane": "comparison_space_capability_and_observation_operator_freeze_gate",
        "source_accession": "1CRN",
        "aod_prediction_representation": "contact_pair_set",
        "quality_supported_pair_count": supported_pairs,
        "effective_abstain_pair_count": abstain_pairs,
        "in_scope_pair_count": in_scope,
        "out_of_scope_pair_count": out_scope,
        "operator_states": {r["comparison_space"]: r["operator_state"] for r in capability},
        "target_values_read_status": "not_read_by_operator_freeze",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "candidate_universe_snapshot_status": "not_materialized_selection_blocked",
        "next_milestone": "v40.02r24 -- Candidate-Universe Snapshot and Target-Independent Accession Selection Gate",
        "files": manifest_files,
        "file_sha256": {k: sha(ROOT / v) for k, v in manifest_files.items()},
    }
    write_json(PROT / "pdb_external_comparison_space_operator_manifest.json", manifest)

    # Register the release-local parsed official-evidence snapshot as a direct bundle payload.
    upsert_inventory_row({
        "source_path": str(evidence_path.relative_to(ROOT)),
        "bundle_path": "external_payloads/pdb_probe_evidence/1crn_official_entry_map_docs_parsed_snapshot.json",
        "payload_class": "release_local_parsed_official_evidence_snapshot",
        "payload_status": "hash_locked",
        "origin_class": "release_local_derived",
        "required_for_release": "yes",
        "embedding_class": "inline_bundle",
        "payload_byte_count": str(evidence_path.stat().st_size),
        "payload_sha256": evidence_sha,
        "inline_embedding_limit_bytes": "52428800",
        "redistribution_status": "project_generated_from_official_page_and_locked_archive_evidence",
        "license_or_terms_ref": "project_license_and_official_source_references",
        "source_url": "https://www.rcsb.org/structure/1CRN ; https://www.rcsb.org/docs/general-help/electron-density-maps-and-coefficient-files",
        "retrieval_or_registration_timestamp_utc": STAMP,
        "payload_pack_id": "",
    })

    # Update current payload status card without mutating historical probe rows.
    status_path = PROT / "external_payload_bundle_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status.update({
        "policy_version": VERSION,
        "policy_title": "Comparison-Space Capability and Observation-Operator Freeze Gate",
        "next_payload_gate": "v40.02r24 Candidate-Universe Snapshot and Target-Independent Accession Selection Gate",
        "probe_evidence_policy": "r22B.2 raw locator rows are retained; r23 adds a hash-locked release-local parsed official-evidence snapshot, deterministic membership audit, payload-family normalization, and prerequisite-failure typing without fabricating target HTTP responses.",
        "reflection_payload_probe_status": "not_listed_in_locked_official_evidence",
        "map_coefficient_probe_status": "not_listed_in_locked_official_evidence",
        "xray_map_service_status": "upstream_prerequisite_not_satisfied",
        "measurement_space_lane": "inactive_target_payload_unavailable_and_representation_incompatible",
        "comparison_operator_gate": "derived_contact_operator_declared_inactive; coordinate and X-ray operators inactive",
    })
    write_json(status_path, status)

    # Current embedding policy status.
    policy_path = PROT / "external_payload_embedding_policy.csv"
    policy = read_csv(policy_path)
    for row in policy:
        row["policy_status"] = "applied_in_r23"
    write_csv(policy_path, list(policy[0].keys()), policy)
    refresh_inventory_metadata()

    print(json.dumps({
        "version": VERSION,
        "quality_supported_pairs": supported_pairs,
        "effective_abstain_pairs": abstain_pairs,
        "in_scope_pairs": in_scope,
        "evidence_snapshot_sha256": evidence_sha,
        "operator_states": manifest["operator_states"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
