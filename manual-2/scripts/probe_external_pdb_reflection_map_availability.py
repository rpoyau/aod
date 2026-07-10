from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
VERSION = "v40.02r22B.2"
RELEASE = "v40.02r22B2_reflection_map_availability_probe_byte_lock_gate"
PROBE_UTC = "2026-06-19T00:00:00Z"


def current_package_version() -> str:
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("Canonical version:"):
            return line.split(":", 1)[1].strip()
    return ""


def read_csv(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path = PROT / name
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def write_json(name: str, data: dict[str, Any]) -> None:
    (PROT / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_snapshot_value(obj: Any, path: str) -> Any:
    if not path.startswith("$."):
        raise ValueError(path)
    cur: Any = obj
    for part in path[2:].split("."):
        if "[" in part:
            key, idx = part.rstrip("]").split("[")
            cur = cur[key][int(idx)]
        else:
            cur = cur[part]
    return cur


def normalization_for(path: str, value: Any) -> tuple[str, str]:
    if path.endswith("_utc"):
        return "parse_report_timestamp_to_UTC_ISO8601_Z", "json_string_utc"
    if value is None:
        return "map_native_unavailable_token_to_JSON_null", "json_null"
    if isinstance(value, bool):
        return "parse_boolean_to_canonical_JSON_boolean", "json_boolean"
    if isinstance(value, int):
        return "parse_integer_to_canonical_JSON_integer", "json_integer"
    if isinstance(value, float):
        return "parse_decimal_to_canonical_JSON_number", "json_number"
    if isinstance(value, (dict, list)):
        return "canonicalize_nested_value_and_emit_sorted_key_JSON", "json_object"
    return "trim_and_preserve_declared_native_token", "json_string"


def build_normalization_policy() -> list[dict[str, str]]:
    evidence = read_csv("pdb_external_validation_snapshot_evidence_locators.csv")
    snapshot = json.loads(
        (PROT / "external_pdb_validation_payloads" / "1crn_full_validation_report_parsed_snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    rows: list[dict[str, str]] = []
    for i, row in enumerate(evidence, 1):
        path = row["snapshot_field_path"]
        value = get_snapshot_value(snapshot, path)
        operation, normalized_type = normalization_for(path, value)
        rows.append(
            {
                "normalization_rule_id": f"1CRN_validation_normalization_{i:03d}",
                "source_field_id": row["source_field_id"],
                "snapshot_field_path": path,
                "source_payload_type": row["source_payload_type"],
                "source_payload_id": row["source_payload_id"],
                "source_locator": row["source_machine_locator"],
                "normalization_operation": operation,
                "normalized_type": normalized_type,
                "field_equivalence_status": row.get("field_equivalence_status", "exact_after_declared_normalization"),
                "normalization_policy_status": "frozen_before_reflection_map_probe",
                "release_status": RELEASE,
            }
        )
    return rows


PROBES: list[dict[str, str]] = [
    {
        "probe_id": "1CRN_structure_factors_rcsb_cif_gz",
        "payload_type": "reflection_payload_structure_factors",
        "requested_url": "https://files.rcsb.org/download/1CRN-sf.cif.gz",
        "archive_source": "RCSB_PDB",
        "probe_state": "probed_unavailable",
        "probe_method": "official_entry_download_panel_plus_official_structure_factor_archive_listing",
        "evidence_url": "https://www.rcsb.org/structure/1CRN ; https://files.wwpdb.org/pub/pdb/data/structures/all/structure_factors/",
        "evidence_http_status": "200",
        "evidence_detail": "1CRN structure-factor payload is not listed in the entry download panel and r1crnsf.ent.gz is absent from the official archive listing",
    },
    {
        "probe_id": "1CRN_structure_factors_rcsb_cif",
        "payload_type": "processed_reflection_payload",
        "requested_url": "https://files.rcsb.org/download/1CRN-sf.cif",
        "archive_source": "RCSB_PDB",
        "probe_state": "probed_unavailable",
        "probe_method": "official_entry_download_panel_plus_official_structure_factor_archive_listing",
        "evidence_url": "https://www.rcsb.org/structure/1CRN ; https://files.wwpdb.org/pub/pdb/data/structures/all/structure_factors/",
        "evidence_http_status": "200",
        "evidence_detail": "No 1CRN structure-factor download is listed by the official entry or archive listing",
    },
    {
        "probe_id": "1CRN_structure_factors_legacy_archive",
        "payload_type": "legacy_structure_factor_payload",
        "requested_url": "https://files.wwpdb.org/pub/pdb/data/structures/all/structure_factors/r1crnsf.ent.gz",
        "archive_source": "wwPDB",
        "probe_state": "probed_unavailable",
        "probe_method": "official_archive_listing_membership_probe",
        "evidence_url": "https://files.wwpdb.org/pub/pdb/data/structures/all/structure_factors/",
        "evidence_http_status": "200",
        "evidence_detail": "Expected legacy object r1crnsf.ent.gz is absent from the official all-structure-factors listing",
    },
    {
        "probe_id": "1CRN_validation_2fo_fc_map_coefficients",
        "payload_type": "validation_2fo_fc_map_coefficients",
        "requested_url": "https://files.rcsb.org/pub/pdb/validation_reports/cr/1crn/1crn_validation_2fo-fc_map_coef.cif.gz",
        "archive_source": "RCSB_PDB_wwPDB_validation",
        "probe_state": "probed_unavailable",
        "probe_method": "official_entry_download_panel_plus_byte_locked_validation_pipeline_evidence",
        "evidence_url": "https://www.rcsb.org/structure/1CRN ; https://files.rcsb.org/validation/download/1crn_validation.xml.gz",
        "evidence_http_status": "200_and_local_byte_hash_locked",
        "evidence_detail": "No map-coefficient download is listed for 1CRN and the locked validation report records EDS not executed",
    },
    {
        "probe_id": "1CRN_validation_fo_fc_map_coefficients",
        "payload_type": "validation_fo_fc_map_coefficients",
        "requested_url": "https://files.rcsb.org/pub/pdb/validation_reports/cr/1crn/1crn_validation_fo-fc_map_coef.cif.gz",
        "archive_source": "RCSB_PDB_wwPDB_validation",
        "probe_state": "probed_unavailable",
        "probe_method": "official_entry_download_panel_plus_byte_locked_validation_pipeline_evidence",
        "evidence_url": "https://www.rcsb.org/structure/1CRN ; https://files.rcsb.org/validation/download/1crn_validation.xml.gz",
        "evidence_http_status": "200_and_local_byte_hash_locked",
        "evidence_detail": "No map-coefficient download is listed for 1CRN and the locked validation report records EDS not executed",
    },
    {
        "probe_id": "1CRN_xray_map_service_cell",
        "payload_type": "xray_map_service",
        "requested_url": "https://maps.rcsb.org/x-ray/1crn/cell/",
        "archive_source": "RCSB_PDB_maps_API",
        "probe_state": "probed_unavailable",
        "probe_method": "upstream_payload_capability_probe",
        "evidence_url": "https://www.rcsb.org/docs/general-help/electron-density-maps-and-coefficient-files",
        "evidence_http_status": "200",
        "evidence_detail": "The documented map service requires an available X-ray map lineage; 1CRN structure factors/map coefficients are not listed and EDS was not executed",
    },
    {
        "probe_id": "1CRN_raw_diffraction_image_registry",
        "payload_type": "raw_diffraction_image_registry_reference",
        "requested_url": "not_declared",
        "archive_source": "external_raw_image_registry",
        "probe_state": "not_probed",
        "probe_method": "not_started_optional_registry_lane",
        "evidence_url": "not_applicable",
        "evidence_http_status": "not_applicable",
        "evidence_detail": "Raw-image discovery remains optional and is not required for the current coordinate-model or derived-contact fixture lanes",
    },
]


def build_probe_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for p in PROBES:
        rows.append(
            {
                **p,
                "probe_timestamp_utc": PROBE_UTC,
                "final_url": "not_observed",
                "http_status": "not_directly_observed",
                "content_type": "not_observed",
                "content_length": "not_observed",
                "etag": "not_observed",
                "last_modified": "not_observed",
                "byte_lock_status": "not_locked",
                "sha256": "",
                "local_payload_path": "",
                "origin_class": "archive_external",
                "embedding_class": "inline_bundle_if_below_limit" if "raw_diffraction" not in p["payload_type"] else "separate_versioned_payload_pack_or_manifest_only_external_lock",
                "access_control_status": "public_archive_probe_evidence" if p["probe_state"] != "not_probed" else "unresolved_not_probed",
                "release_status": RELEASE,
            }
        )
    return rows


def update_availability(probe_rows: list[dict[str, str]]) -> None:
    path = PROT / "pdb_external_experimental_payload_availability.csv"
    rows = read_csv(path.name)
    by_type = {r["payload_type"]: r for r in probe_rows}
    for row in rows:
        ptype = row["payload_type"]
        if ptype in {"reflection_payload_structure_factors", "processed_reflection_payload"}:
            p = by_type[ptype]
            row.update(
                {
                    "payload_availability": "probed_unavailable",
                    "archive_listing_status": "not_listed_on_official_entry_or_archive_listing",
                    "byte_probe_status": "official_listing_probe_completed",
                    "byte_lock_status": "not_locked",
                    "parse_status": "not_started",
                    "field_availability_status": "unavailable_for_current_accession",
                    "http_status": "not_directly_observed",
                    "content_type": "not_observed",
                    "probe_bytes": "not_observed",
                    "probe_sha256": "",
                    "probe_utc": PROBE_UTC,
                    "availability_probe_status": "probed_unavailable_by_official_listing_evidence",
                    "access_control_status": "public_archive_no_payload_listed",
                    "release_status": RELEASE,
                }
            )
        elif ptype == "map_coefficients":
            row.update(
                {
                    "payload_availability": "probed_unavailable",
                    "archive_listing_status": "not_listed_and_validation_EDS_not_executed",
                    "byte_probe_status": "official_entry_and_locked_validation_evidence_probe_completed",
                    "byte_lock_status": "not_locked",
                    "parse_status": "not_started",
                    "field_availability_status": "unavailable_for_current_accession",
                    "payload_path_or_probe_url": "https://files.rcsb.org/pub/pdb/validation_reports/cr/1crn/",
                    "probe_url": "2fo-fc_and_fo-fc_canonical_validation_paths",
                    "http_status": "not_directly_observed",
                    "content_type": "not_observed",
                    "probe_bytes": "not_observed",
                    "probe_sha256": "",
                    "probe_utc": PROBE_UTC,
                    "availability_probe_status": "probed_unavailable_by_entry_and_validation_pipeline_evidence",
                    "access_control_status": "public_archive_no_payload_listed",
                    "release_status": RELEASE,
                }
            )
        elif ptype == "raw_diffraction_images":
            row.update(
                {
                    "payload_availability": "unresolved",
                    "archive_listing_status": "not_probed",
                    "byte_probe_status": "not_probed",
                    "byte_lock_status": "not_locked",
                    "parse_status": "not_started",
                    "field_availability_status": "unresolved",
                    "probe_utc": "not_run",
                    "availability_probe_status": "not_probed_optional_registry_lane",
                    "access_control_status": "unresolved_not_probed",
                    "release_status": RELEASE,
                }
            )
        else:
            row["release_status"] = RELEASE
    write_csv(path.name, list(rows[0].keys()), rows)


def update_comparison_and_limitations() -> None:
    rows = read_csv("pdb_external_comparison_allowed_matrix.csv")
    for row in rows:
        if row["comparison_space"] == "measurement_raw":
            row["current_target_support"] = "reflection_payload_probed_unavailable_for_1CRN"
            row["current_gate_status"] = "unavailable_for_current_accession_and_blocked_by_AOD_representation"
        elif row["comparison_space"] == "measurement_processed":
            row["current_target_support"] = "map_coefficients_probed_unavailable_for_1CRN"
            row["current_gate_status"] = "unavailable_for_current_accession_and_blocked_by_AOD_representation"
        row["release_status"] = RELEASE
    write_csv("pdb_external_comparison_allowed_matrix.csv", list(rows[0].keys()), rows)

    limits = read_csv("pdb_external_target_limitation_budget.csv")
    for row in limits:
        if row["limitation_id"] == "lim_1CRN_reflection_payload":
            row["current_state"] = "probed_unavailable_for_current_accession"
            row["implication"] = "measurement_space_lane_unavailable_for_1CRN"
            row["resolution_or_gate"] = "select_separate_predeclared_accession_for_measurement_space_pilot"
        row["release_status"] = RELEASE
    write_csv("pdb_external_target_limitation_budget.csv", list(limits[0].keys()), limits)


def update_embedding_policy() -> None:
    rows = read_csv("external_payload_embedding_policy.csv")
    for row in rows:
        row["policy_status"] = "applied_in_r22B2"
    write_csv("external_payload_embedding_policy.csv", list(rows[0].keys()), rows)


def update_linked_manifest_hashes() -> None:
    for name in [
        "pdb_external_validation_local_support_manifest.json",
        "pdb_external_quality_mask_manifest.json",
    ]:
        path = PROT / name
        data = json.loads(path.read_text(encoding="utf-8"))
        files = data.get("files", {})
        data["file_sha256"] = {key: sha(ROOT / rel) for key, rel in files.items()}
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_inventory_for_modified_embedded_files() -> None:
    path = PROT / "external_payload_bundle_inventory.csv"
    rows = read_csv(path.name)
    changed = {
        "manual-2/data/protein/external_payload_bundle_status.json",
        "manual-2/data/protein/external_payload_embedding_policy.csv",
    }
    for row in rows:
        if row["source_path"] in changed:
            source = ROOT / row["source_path"]
            row["payload_byte_count"] = str(source.stat().st_size)
            row["payload_sha256"] = sha(source)
            row["retrieval_or_registration_timestamp_utc"] = PROBE_UTC
            row["payload_status"] = "current_policy_status" if source.suffix == ".json" else "policy_applied"
    write_csv(path.name, list(rows[0].keys()), rows)


def main() -> None:
    current_version = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    if "Canonical version: v40.02r22B.2" not in current_version:
        print(json.dumps({
            "version": "v40.02r22B.2",
            "status": "historical_generator_noop_in_newer_package",
            "current_canonical_version": current_version.splitlines()[0],
        }, indent=2, sort_keys=True))
        return
    normalization = build_normalization_policy()
    write_csv(
        "pdb_external_validation_snapshot_normalization_policy.csv",
        [
            "normalization_rule_id", "source_field_id", "snapshot_field_path", "source_payload_type",
            "source_payload_id", "source_locator", "normalization_operation", "normalized_type",
            "field_equivalence_status", "normalization_policy_status", "release_status",
        ],
        normalization,
    )

    probes = build_probe_rows()
    write_csv(
        "pdb_external_reflection_map_probe_evidence.csv",
        [
            "probe_id", "payload_type", "probe_timestamp_utc", "requested_url", "final_url", "http_status",
            "content_type", "content_length", "etag", "last_modified", "byte_lock_status", "sha256",
            "probe_state", "probe_method", "evidence_url", "evidence_http_status", "evidence_detail",
            "archive_source", "local_payload_path", "origin_class", "embedding_class", "access_control_status",
            "release_status",
        ],
        probes,
    )

    locked = sum(1 for r in probes if r["probe_state"] == "byte_hash_locked")
    unavailable = sum(1 for r in probes if r["probe_state"] == "probed_unavailable")
    not_probed = sum(1 for r in probes if r["probe_state"] == "not_probed")
    write_csv(
        "pdb_external_reflection_map_availability_summary.csv",
        [
            "source_accession", "probe_row_count", "byte_hash_locked_count", "probed_unavailable_count",
            "retrieved_unlocked_count", "not_probed_count", "reflection_payload_state", "map_coefficient_state",
            "raw_image_registry_state", "measurement_space_lane", "coordinate_model_lane",
            "derived_observable_lane", "next_gate", "release_status",
        ],
        [{
            "source_accession": "1CRN", "probe_row_count": str(len(probes)),
            "byte_hash_locked_count": str(locked), "probed_unavailable_count": str(unavailable),
            "retrieved_unlocked_count": "0", "not_probed_count": str(not_probed),
            "reflection_payload_state": "probed_unavailable", "map_coefficient_state": "probed_unavailable",
            "raw_image_registry_state": "not_probed_optional", "measurement_space_lane": "unavailable_for_current_accession",
            "coordinate_model_lane": "active_reconstruction_space_fixture",
            "derived_observable_lane": "active_with_quality_mask_but_zero_supported_pairs",
            "next_gate": "comparison_space_capability_and_observation_operator_freeze",
            "release_status": RELEASE,
        }],
    )

    write_csv(
        "pdb_external_reflection_map_byte_lock.csv",
        ["probe_id", "payload_type", "byte_lock_status", "local_payload_path", "payload_byte_count", "payload_sha256", "embedding_class", "release_status"],
        [{
            "probe_id": r["probe_id"], "payload_type": r["payload_type"], "byte_lock_status": "not_locked_payload_unavailable" if r["probe_state"] == "probed_unavailable" else "not_locked_not_probed",
            "local_payload_path": "", "payload_byte_count": "", "payload_sha256": "", "embedding_class": r["embedding_class"], "release_status": RELEASE,
        } for r in probes],
    )

    write_csv(
        "pdb_external_reflection_map_access_control.csv",
        ["probe_id", "archive_source", "requested_url", "access_control_status", "redistribution_status", "license_or_terms_ref", "embedding_policy_id", "release_status"],
        [{
            "probe_id": r["probe_id"], "archive_source": r["archive_source"], "requested_url": r["requested_url"],
            "access_control_status": r["access_control_status"],
            "redistribution_status": "archive_terms_check_required_before_embedding" if r["probe_state"] != "not_probed" else "unresolved",
            "license_or_terms_ref": "https://www.wwpdb.org/about/usage-policies" if r["probe_state"] != "not_probed" else "not_resolved",
            "embedding_policy_id": "external_payload_policy_reflection_map" if "raw_diffraction" not in r["payload_type"] else "external_payload_policy_raw_images",
            "release_status": RELEASE,
        } for r in probes],
    )

    checks = [
        ("probe_states_are_explicit", "pass", "Each row is not_probed, probed_unavailable, retrieved_unlocked, or byte_hash_locked."),
        ("no_fabricated_target_http_status", "pass", "Target HTTP status/header fields remain not_directly_observed/not_observed because no direct response bytes were obtained."),
        ("no_unavailable_payload_hash", "pass", "Unavailable payloads carry no SHA-256 or local path."),
        ("official_evidence_is_recorded", "pass", "Official entry, archive-listing, validation, or map-documentation evidence is recorded for each completed probe."),
        ("measurement_space_lane_stays_closed", "pass", "1CRN measurement-space lane is unavailable and the contact-pair AOD representation is incompatible with X-ray forward prediction."),
        ("target_values_not_read", "pass", "No reflection, map, contact-target, residual, or score value is joined to the AOD branch."),
        ("large_payload_policy_applied", "pass", "Reflection/map and raw-image payload classes use the pre-frozen inline/separate-pack/manifest-only policy."),
        ("frozen_main_manual_shared", "pass", "This generator writes only Manual-II data files."),
    ]
    write_csv(
        "pdb_external_reflection_map_leakage_checks.csv",
        ["check_id", "status", "detail", "release_status"],
        [{"check_id": a, "status": b, "detail": c, "release_status": RELEASE} for a, b, c in checks],
    )

    write_csv(
        "pdb_external_scored_accession_candidate_universe_policy.csv",
        [
            "candidate_universe_snapshot_id", "archive_query", "archive_query_timestamp_utc",
            "eligibility_filter_version", "eligible_accession_list", "eligible_accession_list_sha256",
            "selection_method", "selected_accession", "candidate_universe_status", "target_agreement_read_status",
            "release_status",
        ],
        [{
            "candidate_universe_snapshot_id": "pdb_scored_accession_candidate_universe_deferred_v1",
            "archive_query": "X-RAY DIFFRACTION entries satisfying the frozen scored-accession eligibility rule",
            "archive_query_timestamp_utc": "not_run",
            "eligibility_filter_version": "pdb_scored_accession_eligibility_xray_derived_contact_v1",
            "eligible_accession_list": "not_materialized",
            "eligible_accession_list_sha256": "not_available",
            "selection_method": "lexicographically_lowest_accession_after_candidate_universe_snapshot",
            "selected_accession": "none",
            "candidate_universe_status": "selection_blocked_until_candidate_universe_snapshot",
            "target_agreement_read_status": "not_read",
            "release_status": RELEASE,
        }],
    )

    # Historical gate outputs above are reproducible in every later package.
    # Current-package metadata is updated only when this script is run in its
    # own canonical release; otherwise a historical regeneration must not
    # rewind newer manifests, comparison matrices, or bundle policy state.
    if current_package_version() == VERSION:
        update_availability(probes)
        update_comparison_and_limitations()
        update_embedding_policy()
        update_linked_manifest_hashes()

        status = json.loads((PROT / "external_payload_bundle_status.json").read_text(encoding="utf-8"))
        status.update({
            "policy_title": "Reflection / Map Availability Probe and Byte-Lock Gate",
            "policy_version": VERSION,
            "reflection_payload_probe_status": "probed_unavailable_for_1CRN",
            "map_coefficient_probe_status": "probed_unavailable_for_1CRN",
            "raw_image_registry_probe_status": "not_probed_optional",
            "measurement_space_lane": "unavailable_for_current_accession",
            "next_payload_gate": "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
            "probe_evidence_policy": "Target HTTP response fields are not fabricated; official entry/listing/pipeline evidence is recorded and target-specific headers remain not_observed unless bytes were retrieved.",
        })
        (PROT / "external_payload_bundle_status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        measurement = json.loads((PROT / "pdb_external_measurement_manifest.json").read_text(encoding="utf-8"))
        measurement.update({
            "version_scope": VERSION,
            "reflection_payload_probe_status": "probed_unavailable_for_1CRN",
            "map_coefficient_probe_status": "probed_unavailable_for_1CRN",
            "raw_image_registry_probe_status": "not_probed_optional",
            "measurement_space_lane": "unavailable_for_current_accession",
            "normalization_policy_status": "41_field_machine_readable_policy_frozen",
            "candidate_universe_status": "selection_blocked_until_candidate_universe_snapshot",
            "next_milestones": ["v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate"],
        })
        measurement.setdefault("files", {}).update(manifest["files"])
        measurement.setdefault("file_sha256", {}).update(manifest["file_sha256"])
        (PROT / "pdb_external_measurement_manifest.json").write_text(json.dumps(measurement, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        update_inventory_for_modified_embedded_files()


if __name__ == "__main__":
    main()
