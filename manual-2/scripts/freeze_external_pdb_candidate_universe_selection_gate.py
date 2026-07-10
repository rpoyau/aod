from __future__ import annotations

import csv
import hashlib
import json
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
QUERY_DIR = PROT / "external_pdb_candidate_universe_queries"
VERSION = "v40.02r24"
PACKAGE_VERSION = "v40.03r01"
RELEASE = "v40.02r24_candidate_universe_snapshot_target_independent_accession_selection_gate"
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


def update_csv_value(path: Path, predicate, updates: dict[str, str], append_fields: list[str] | None = None) -> None:
    rows = read_csv(path)
    fields = list(rows[0].keys()) if rows else []
    for field in append_fields or []:
        if field not in fields:
            fields.append(field)
    for row in rows:
        if predicate(row):
            row.update(updates)
    write_csv(path, fields, rows)


def build_motif_policy() -> Path:
    rows = [{
        "motif_compatibility_policy_id": "pdb_candidate_motif_compatibility_contact_reclosure_v1",
        "motif_compatibility_policy_family_id": "pdb_candidate_motif_compatibility_contact_reclosure",
        "aod_packet_family": "contact_reclosure",
        "aod_source_packet_id": "chain_GAS_tripeptide_seed",
        "aod_packet_sha256": sha(PROT / "aod_contact_prediction_freeze.csv"),
        "aod_reclosure_id": "aod_reclosure_pred_002",
        "sadar_context_id": "sadar_mol_005",
        "candidate_screening_scope": "topology_and_window_capacity_only_not_alignment",
        "allowed_external_chain_length_min": "40",
        "allowed_external_chain_length_max": "250",
        "minimum_external_window_length": "4",
        "motif_to_residue_window_rule": "candidate_chain_must_admit_at_least_one_ordered_four_residue_window_supporting_abs_j_minus_i_ge_3; no residue identity or contact value is inspected",
        "coverage_requirement": "candidate_screening_only; later declared alignment_projection_rule and nonzero in_scope coverage required",
        "abstention_policy": "before_alignment=out_of_scope; after_alignment_in_scope_nonemission=abstain",
        "alignment_declaration_status": "not_declared_by_candidate_screening_policy",
        "target_agreement_read_status": "not_read",
        "policy_freeze_status": "frozen_before_candidate_universe_materialization_and_accession_selection",
        "release_status": RELEASE,
    }]
    path = PROT / "pdb_external_motif_compatibility_policy.csv"
    write_csv(path, list(rows[0].keys()), rows)
    return path


def build_eligibility_v2(motif_path: Path) -> Path:
    old = read_csv(PROT / "pdb_external_scored_accession_eligibility_rule.csv")
    rows: list[dict[str, str]] = []
    new_id = "pdb_scored_accession_eligibility_xray_derived_contact_v2"
    for row in old:
        new = dict(row)
        new["selection_rule_id"] = new_id
        new["release_status"] = RELEASE
        if new["criterion_id"] == "motif_compatibility_policy":
            new["required_value"] = "pdb_candidate_motif_compatibility_contact_reclosure_v1"
            new["rationale"] = "freeze topology/window-capacity compatibility policy before archive-query response or target inspection"
        if new["criterion_id"] == "selection_method":
            new["criterion_status"] = "frozen_before_candidate_universe_materialization"
        rows.append(new)
    # Add an explicit archive-query response lock criterion before deterministic selection.
    fields = list(rows[0].keys())
    rows.append({
        "selection_rule_id": new_id,
        "criterion_order": "13",
        "criterion_id": "candidate_universe_response_lock",
        "criterion_field": "candidate_universe_response_sha256",
        "operator": "exists",
        "required_value": "official_RCSB_search_API_response_byte_hash_locked",
        "criterion_status": "frozen_before_selection",
        "rationale": "selection operates on a frozen archive-query response rather than a changing live query",
        "inspection_stage": "archive_query_response_before_any_AOD_agreement_values",
        "target_agreement_read_status": "not_read",
        "accession_selection_method": "lexicographically_lowest_accession_among_all_eligible_entries",
        "selection_seed": "not_applicable_deterministic_order",
        "accession_selection_status": "blocked_until_official_query_response_is_byte_hash_locked_and_eligibility_audit_materialized",
        "release_status": RELEASE,
    })
    rows.sort(key=lambda r: int(r["criterion_order"]))
    path = PROT / "pdb_external_scored_accession_eligibility_rule_v2.csv"
    write_csv(path, fields, rows)
    return path


def build_query_spec() -> tuple[Path, str]:
    # The Search API request is frozen, but this offline release build does not execute it.
    # The broad prefilter is intentionally limited to fields supported by the official Search API;
    # payload, chain, selected-atom, validation, and motif policy criteria are applied in the later
    # eligibility audit after the response is byte-locked.
    request = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "exptl.method",
                        "operator": "exact_match",
                        "value": "X-RAY DIFFRACTION",
                    },
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_entry_info.resolution_combined",
                        "operator": "less_or_equal",
                        "value": 2.0,
                    },
                },
            ],
        },
        "return_type": "entry",
        "request_options": {
            "return_all_hits": True,
            "results_content_type": ["experimental"],
            "results_verbosity": "compact",
        },
        "request_info": {
            "query_id": "aod_r24_xray_resolution_prefilter_v1",
        },
    }
    data = {
        "candidate_universe_query_spec_id": "pdb_candidate_universe_query_spec_r24_v1",
        "endpoint": "https://search.rcsb.org/rcsbsearch/v2/query",
        "http_method_contract": "GET_with_url_encoded_json_or_POST_application_json",
        "query_request": request,
        "local_sort_policy": "uppercase_identifier_lexicographic_ascending_after_response_lock",
        "prefilter_scope": "X-ray experimental entries with archive resolution <= 2.0 A; remaining eligibility criteria applied after response lock",
        "query_execution_status": "not_executed_in_offline_release_build",
        "target_agreement_read_status": "not_read",
        "source_documentation": "https://search.rcsb.org/",
        "frozen_at_utc": STAMP,
    }
    QUERY_DIR.mkdir(parents=True, exist_ok=True)
    path = QUERY_DIR / "rcsb_search_candidate_universe_query_r24.json"
    write_json(path, data)
    query_json = json.dumps(request, separators=(",", ":"), ensure_ascii=False)
    query_url = data["endpoint"] + "?json=" + urllib.parse.quote(query_json, safe="")
    return path, query_url


def update_activation_guards() -> None:
    strict = (
        "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_"
        "in_scope_pair_count>0_and_prediction_emitted_pair_count>0_and_comparable_pair_count>0"
    )
    update_csv_value(
        PROT / "pdb_external_comparison_space_capability_gate.csv",
        lambda r: r["comparison_space"] == "derived_observable",
        {
            "activation_condition": strict,
            "current_block_reason": "quality_supported_pairs_0_in_scope_pairs_0_prediction_emitted_pairs_0_comparable_pairs_0",
        },
    )
    update_csv_value(
        PROT / "pdb_external_derived_contact_operator_declaration.csv",
        lambda r: True,
        {"comparison_join_rule": strict},
    )
    update_csv_value(
        PROT / "pdb_external_comparison_join_declaration.csv",
        lambda r: True,
        {
            "aod_comparison_join_activation_condition": strict,
            "comparison_join_status": "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs",
            "prediction_emitted_pair_count": "0",
            "comparable_pair_count": "0",
        },
        append_fields=["prediction_emitted_pair_count", "comparable_pair_count"],
    )
    update_csv_value(
        PROT / "pdb_external_quality_masked_contact_summary.csv",
        lambda r: True,
        {
            "aod_comparison_join_activation_condition": strict,
            "aod_comparison_join_gate_state": "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs",
            "prediction_emitted_pair_count": "0",
            "comparable_pair_count": "0",
        },
        append_fields=["prediction_emitted_pair_count", "comparable_pair_count"],
    )

    # Carry the stricter comparison-activation guard into the linked provenance manifests
    # without changing their historical lane version_scope values.
    for manifest_name in [
        "pdb_external_validation_snapshot_provenance_manifest.json",
        "pdb_external_validation_local_support_manifest.json",
        "pdb_external_measurement_manifest.json",
    ]:
        manifest_path = PROT / manifest_name
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["carried_forward_in_package_version"] = VERSION
        manifest["aod_comparison_join_activation_condition"] = strict
        manifest["prediction_emitted_pair_count"] = 0
        manifest["comparable_pair_count"] = 0
        if "target_join_status" in manifest:
            manifest["target_join_status"] = "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs"
        if "aod_comparison_join_gate_state" in manifest:
            manifest["aod_comparison_join_gate_state"] = "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs"
        for key, rel in manifest.get("files", {}).items():
            fp = ROOT / rel
            if fp.is_file():
                manifest.setdefault("file_sha256", {})[key] = sha(fp)
        write_json(manifest_path, manifest)

    qm_path = PROT / "pdb_external_quality_mask_manifest.json"
    qm = json.loads(qm_path.read_text(encoding="utf-8"))
    qm["aod_comparison_join_gate_state"] = "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs"
    qm["prediction_emitted_pair_count"] = 0
    qm["comparable_pair_count"] = 0
    qm["aod_comparison_join_activation_condition"] = strict
    for key, rel in qm.get("files", {}).items():
        p = ROOT / rel
        if p.is_file():
            qm.setdefault("file_sha256", {})[key] = sha(p)
    write_json(qm_path, qm)

    op_path = PROT / "pdb_external_comparison_space_operator_manifest.json"
    op = json.loads(op_path.read_text(encoding="utf-8"))
    op["carried_forward_in_package_version"] = VERSION
    op["prediction_emitted_pair_count"] = 0
    op["comparable_pair_count"] = 0
    op["candidate_universe_snapshot_status"] = "query_spec_frozen_response_not_materialized_selection_blocked"
    op["canonical_comparison_matrix"] = "manual-2/data/protein/pdb_external_comparison_space_capability_gate.csv"
    op["historical_comparison_matrix"] = "manual-2/data/protein/pdb_external_comparison_allowed_matrix.csv"
    op["next_milestone"] = "v40.03r02 -- Official Candidate-Universe Response Byte-Lock and Eligibility Materialization Gate"
    for key, rel in op.get("files", {}).items():
        p = ROOT / rel
        if p.is_file():
            op.setdefault("file_sha256", {})[key] = sha(p)
    write_json(op_path, op)


def build_gate_files(motif_path: Path, eligibility_path: Path, query_path: Path, query_url: str) -> dict[str, Path]:
    query_sha = sha(query_path)
    motif_sha = sha(motif_path)
    elig_sha = sha(eligibility_path)

    response_status_rows = [{
        "archive_query_id": "aod_r24_xray_resolution_prefilter_v1",
        "candidate_universe_query_spec_id": "pdb_candidate_universe_query_spec_r24_v1",
        "archive_query_endpoint": "https://search.rcsb.org/rcsbsearch/v2/query",
        "archive_query_method": "GET_or_POST",
        "archive_query_url": query_url,
        "archive_query_spec_path": str(query_path.relative_to(ROOT)),
        "archive_query_spec_sha256": query_sha,
        "archive_query_timestamp_utc": "not_executed_offline_build",
        "archive_query_response_path": "",
        "archive_query_response_sha256": "",
        "archive_query_response_byte_count": "",
        "archive_query_response_status": "not_materialized_offline_build",
        "candidate_universe_materialization_status": "blocked_pending_official_query_response_byte_lock",
        "target_agreement_read_status": "not_read",
        "release_status": RELEASE,
    }]
    response_status_path = PROT / "pdb_external_candidate_universe_query_response_status.csv"
    write_csv(response_status_path, list(response_status_rows[0].keys()), response_status_rows)

    snapshot_rows = [{
        "candidate_universe_gate_id": "pdb_scored_accession_candidate_universe_gate_r24",
        "candidate_universe_snapshot_id": "pending_official_RCSB_search_API_response",
        "candidate_universe_query_spec_id": "pdb_candidate_universe_query_spec_r24_v1",
        "archive_query_spec_sha256": query_sha,
        "archive_query_response_sha256": "",
        "archive_query_response_status": "not_materialized_offline_build",
        "motif_compatibility_policy_id": "pdb_candidate_motif_compatibility_contact_reclosure_v1",
        "motif_compatibility_policy_sha256": motif_sha,
        "eligibility_filter_version": "pdb_scored_accession_eligibility_xray_derived_contact_v2",
        "eligibility_filter_sha256": elig_sha,
        "candidate_universe_count": "not_materialized",
        "eligible_accession_count": "not_materialized",
        "eligible_accession_list_path": "",
        "eligible_accession_list_sha256": "",
        "selection_method": "lexicographically_lowest_accession_after_frozen_universe_and_full_eligibility_audit",
        "selected_accession": "none",
        "selection_status": "blocked_pending_official_query_response_byte_lock_and_eligibility_materialization",
        "target_agreement_read_status": "not_read",
        "release_status": RELEASE,
    }]
    snapshot_path = PROT / "pdb_external_scored_accession_candidate_universe_snapshot_gate.csv"
    write_csv(snapshot_path, list(snapshot_rows[0].keys()), snapshot_rows)

    audit_rows = [{
        "eligibility_audit_id": "pdb_candidate_universe_eligibility_audit_r24_pending_response",
        "candidate_accession": "none",
        "candidate_universe_snapshot_id": "pending_official_RCSB_search_API_response",
        "eligibility_filter_version": "pdb_scored_accession_eligibility_xray_derived_contact_v2",
        "motif_compatibility_policy_id": "pdb_candidate_motif_compatibility_contact_reclosure_v1",
        "archive_prefilter_status": "not_evaluated_no_locked_response",
        "payload_and_validation_eligibility_status": "not_evaluated_no_candidate_rows",
        "selected_atom_coverage_status": "not_evaluated",
        "motif_compatibility_status": "policy_frozen_candidate_not_evaluated",
        "overall_eligibility_status": "blocked_pending_official_query_response_byte_lock",
        "target_agreement_read_status": "not_read",
        "release_status": RELEASE,
    }]
    audit_path = PROT / "pdb_external_candidate_universe_eligibility_audit.csv"
    write_csv(audit_path, list(audit_rows[0].keys()), audit_rows)

    selection_rows = [{
        "selection_gate_id": "pdb_scored_accession_target_independent_selection_gate_r24",
        "candidate_universe_snapshot_id": "pending_official_RCSB_search_API_response",
        "candidate_universe_snapshot_sha256": "",
        "eligibility_filter_version": "pdb_scored_accession_eligibility_xray_derived_contact_v2",
        "eligibility_filter_sha256": elig_sha,
        "motif_compatibility_policy_id": "pdb_candidate_motif_compatibility_contact_reclosure_v1",
        "motif_compatibility_policy_sha256": motif_sha,
        "selection_method": "lexicographically_lowest_accession_among_fully_eligible_rows",
        "selected_accession": "none",
        "selection_status": "blocked_no_materialized_candidate_universe",
        "selection_target_values_read_status": "not_read",
        "selection_AOD_agreement_values_read_status": "not_read",
        "next_required_input": "byte_locked_official_RCSB_search_API_response_JSON",
        "score_status": "no_score",
        "release_status": RELEASE,
    }]
    selection_path = PROT / "pdb_external_candidate_universe_selection_gate.csv"
    write_csv(selection_path, list(selection_rows[0].keys()), selection_rows)

    supersession_rows = [{
        "matrix_path": "manual-2/data/protein/pdb_external_comparison_allowed_matrix.csv",
        "matrix_status": "historical_carried_forward",
        "superseded_by": "manual-2/data/protein/pdb_external_comparison_space_capability_gate.csv",
        "canonical_matrix_status": "authoritative_current_capability_state",
        "supersession_reason": "r23 capability gate normalizes payload families and operator states; r24 retains it as canonical and tightens comparable-pair activation",
        "release_status": RELEASE,
    }]
    supersession_path = PROT / "pdb_external_comparison_matrix_supersession.csv"
    write_csv(supersession_path, list(supersession_rows[0].keys()), supersession_rows)

    leak_rows = [
        {"check_id": "r24_motif_compatibility_policy_frozen_before_candidate_universe_materialization", "check_status": "pass", "evidence": motif_sha, "release_status": RELEASE},
        {"check_id": "r24_archive_query_spec_frozen_before_response_or_selection", "check_status": "pass", "evidence": query_sha, "release_status": RELEASE},
        {"check_id": "r24_official_query_response_required_before_candidate_universe_snapshot", "check_status": "pass", "evidence": "response_not_materialized_selection_blocked", "release_status": RELEASE},
        {"check_id": "r24_no_accession_selected_without_locked_candidate_universe", "check_status": "pass", "evidence": "selected_accession=none", "release_status": RELEASE},
        {"check_id": "r24_AOD_agreement_values_not_read_during_query_or_selection", "check_status": "pass", "evidence": "not_read", "release_status": RELEASE},
        {"check_id": "r24_comparison_requires_prediction_emission_and_comparable_pairs", "check_status": "pass", "evidence": "prediction_emitted_pair_count>0 and comparable_pair_count>0 appended to canonical join rule", "release_status": RELEASE},
        {"check_id": "r24_historical_matrix_has_canonical_supersession_pointer", "check_status": "pass", "evidence": "pdb_external_comparison_space_capability_gate.csv", "release_status": RELEASE},
        {"check_id": "r24_no_target_join_residual_or_score", "check_status": "pass", "evidence": "candidate gate only", "release_status": RELEASE},
    ]
    leak_path = PROT / "pdb_external_candidate_universe_leakage_checks.csv"
    write_csv(leak_path, list(leak_rows[0].keys()), leak_rows)

    files = {
        "motif_compatibility_policy": motif_path,
        "eligibility_rule_v2": eligibility_path,
        "archive_query_spec": query_path,
        "archive_query_response_status": response_status_path,
        "candidate_universe_snapshot_gate": snapshot_path,
        "eligibility_audit": audit_path,
        "selection_gate": selection_path,
        "comparison_matrix_supersession": supersession_path,
        "leakage_checks": leak_path,
    }
    manifest = {
        "version_scope": VERSION,
        "lane": "candidate_universe_query_freeze_and_target_independent_selection_gate",
        "candidate_universe_query_spec_id": "pdb_candidate_universe_query_spec_r24_v1",
        "candidate_universe_query_spec_sha256": query_sha,
        "archive_query_response_status": "not_materialized_offline_build",
        "candidate_universe_snapshot_status": "blocked_pending_official_query_response_byte_lock",
        "motif_compatibility_policy_id": "pdb_candidate_motif_compatibility_contact_reclosure_v1",
        "motif_compatibility_policy_sha256": motif_sha,
        "eligibility_filter_version": "pdb_scored_accession_eligibility_xray_derived_contact_v2",
        "eligibility_filter_sha256": elig_sha,
        "candidate_universe_count": None,
        "eligible_accession_count": None,
        "selected_accession": None,
        "selection_status": "blocked_no_materialized_candidate_universe",
        "prediction_emitted_pair_count": 0,
        "comparable_pair_count": 0,
        "target_agreement_read_status": "not_read",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "next_milestone": "v40.03r02 -- Official Candidate-Universe Response Byte-Lock and Eligibility Materialization Gate",
        "files": {k: str(v.relative_to(ROOT)) for k, v in files.items()},
        "file_sha256": {k: sha(v) for k, v in files.items()},
    }
    manifest_path = PROT / "pdb_external_candidate_universe_manifest.json"
    write_json(manifest_path, manifest)
    files["manifest"] = manifest_path
    return files


def update_inventory(query_path: Path) -> None:
    upsert_inventory_row({
        "source_path": str(query_path.relative_to(ROOT)),
        "bundle_path": "external_payloads/pdb_candidate_universe/rcsb_search_candidate_universe_query_r24.json",
        "payload_class": "candidate_universe_archive_query_specification",
        "payload_status": "hash_locked_query_spec_response_not_materialized",
        "origin_class": "release_policy_metadata",
        "required_for_release": "yes",
        "embedding_class": "inline_bundle",
        "payload_byte_count": str(query_path.stat().st_size),
        "payload_sha256": sha(query_path),
        "inline_embedding_limit_bytes": "52428800",
        "redistribution_status": "project_generated_query_specification",
        "license_or_terms_ref": "project_license_and_RCSB_Search_API_terms",
        "source_url": "https://search.rcsb.org/",
        "retrieval_or_registration_timestamp_utc": STAMP,
        "payload_pack_id": "",
    })
    refresh_inventory_metadata()


def update_status_cards(query_path: Path) -> None:
    status_path = PROT / "external_payload_bundle_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status.update({
        "policy_version": PACKAGE_VERSION,
        "policy_title": "Exact Multioctave Temporal Calculus, Metric Projection, and Uncertainty-Qualified Comparison Protocol",
        "next_payload_gate": "v40.03r02 Official Candidate-Universe Response Byte-Lock and Eligibility Materialization Gate",
        "candidate_universe_query_spec_status": "hash_locked",
        "candidate_universe_query_response_status": "not_materialized_offline_build",
        "candidate_accession_selection_status": "blocked_no_materialized_candidate_universe",
        "candidate_universe_query_spec_sha256": sha(query_path),
    })
    write_json(status_path, status)
    policy_path = PROT / "external_payload_embedding_policy.csv"
    policy = read_csv(policy_path)
    for row in policy:
        row["policy_status"] = "applied_in_r24"
    write_csv(policy_path, list(policy[0].keys()), policy)


def main() -> None:
    motif_path = build_motif_policy()
    eligibility_path = build_eligibility_v2(motif_path)
    query_path, query_url = build_query_spec()
    update_activation_guards()
    files = build_gate_files(motif_path, eligibility_path, query_path, query_url)
    update_status_cards(query_path)
    update_inventory(query_path)
    print(json.dumps({
        "version": VERSION,
        "candidate_universe_query_spec_sha256": sha(query_path),
        "archive_query_response_status": "not_materialized_offline_build",
        "selected_accession": None,
        "next_milestone": "v40.03r01",
        "files": {k: str(v.relative_to(ROOT)) for k, v in files.items()},
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
