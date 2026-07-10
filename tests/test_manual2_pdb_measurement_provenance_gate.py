from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def rows(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_measurement_and_validation_gate_files_are_present() -> None:
    names = [
        "pdb_external_experiment_lineage.csv",
        "pdb_external_measurement_metadata.csv",
        "pdb_external_experimental_payload_availability.csv",
        "pdb_external_refinement_validation_metrics.csv",
        "pdb_external_residue_quality_mask.csv",
        "pdb_external_coordinate_use_policy.csv",
        "pdb_external_contact_observable_policy.csv",
        "pdb_external_target_limitation_budget.csv",
        "pdb_external_comparison_allowed_matrix.csv",
        "pdb_external_comparison_join_declaration.csv",
        "pdb_external_quality_rule_policy.csv",
        "pdb_external_quality_masked_contact_target.csv",
        "pdb_external_quality_masked_contact_summary.csv",
        "pdb_external_quality_mask_manifest.json",
        "pdb_external_measurement_manifest.json",
        "pdb_external_validation_payload_byte_lock.csv",
        "pdb_external_validation_payload_provenance.csv",
        "pdb_external_validation_global_metrics.csv",
        "pdb_external_validation_residue_outlier_ingest.csv",
        "pdb_external_validation_local_support_ingest.csv",
        "pdb_external_validation_local_support_leakage_checks.csv",
        "pdb_external_validation_local_support_manifest.json",
        "pdb_external_validation_snapshot_evidence_locators.csv",
        "pdb_external_validation_outlier_observable_policy.csv",
        "pdb_external_legacy_entry_policy.csv",
        "pdb_external_scored_accession_eligibility_rule.csv",
        "pdb_external_validation_snapshot_provenance_manifest.json",
    ]
    for name in names:
        assert (PROT / name).is_file(), name
    assert (PROT / "external_pdb_validation_payloads/1crn_full_validation_report_parsed_snapshot.json").is_file()
    assert (ROOT / "manual-2/scripts/ingest_external_pdb_validation_report_snapshot.py").is_file()
    assert (ROOT / "manual-2/sections/23_validation_report_local_support_ingest_gate.tex").is_file()
    assert (ROOT / "manual-2/sections/24_validation_snapshot_provenance_observable_support_policy.tex").is_file()
    assert (ROOT / "manual-2/scripts/refine_external_pdb_validation_snapshot_provenance_policy.py").is_file()
    main = (ROOT / "manual-2/main.tex").read_text(encoding="utf-8")
    assert "23_validation_report_local_support_ingest_gate" in main
    assert "24_validation_snapshot_provenance_observable_support_policy" in main


def test_coordinate_branch_remains_reconstruction_space_fixture() -> None:
    r = rows("pdb_external_coordinate_branch_classification.csv")
    assert len(r) >= 3
    assert {x["target_class"] for x in r} == {"coordinate_model_observable_fixture"}
    assert {x["recomputation_status"] for x in r} == {"not_required"}


def test_archive_and_citation_resolution_values_remain_separate() -> None:
    r = rows("pdb_external_experiment_lineage.csv")[0]
    assert r["source_accession"] == "1CRN"
    assert r["archive_entry_version"] == "1.5"
    assert r["archive_reported_resolution_high_angstrom"] in {"1.5", "1.50"}
    assert r["citation_reported_resolution_angstrom"] == "0.945"
    assert r["citation_resolution_relation_status"] == "reconciliation_pending"
    assert r["coordinate_payload_sha256"] == sha(PROT / "external_pdb_payloads/1CRN.cif")


def test_lineage_family_state_and_declaration_ids_are_consistent() -> None:
    exp = rows("pdb_external_experiment_lineage.csv")[0]
    assert exp["measurement_lineage_family_id"] == "pdb_measurement_lineage_1CRN_xray"
    meta = rows("pdb_external_measurement_metadata.csv")
    target = [x for x in meta if x["lineage_branch"] == "target_measurement"]
    aod = [x for x in meta if x["lineage_branch"] == "aod_prediction"]
    assert {x["measurement_lineage_family_id"] for x in target} == {exp["measurement_lineage_family_id"]}
    assert {x["measurement_lineage_state_id"] for x in target} == {exp["measurement_lineage_state_id"]}
    assert {x["measurement_lineage_declaration_id"] for x in target} == {exp["measurement_lineage_declaration_id"]}
    assert [int(x["branch_stage_order"]) for x in target] == [1, 2, 3, 4, 5]
    assert len(aod) == 1 and aod[0]["stage_name"] == "independent_aod_lane"


def test_validation_snapshot_hash_and_original_archive_payloads_are_locked() -> None:
    lock = rows("pdb_external_validation_payload_byte_lock.csv")[0]
    path = ROOT / lock["local_payload_path"]
    assert lock["local_payload_sha256"] == sha(path)
    assert int(lock["local_payload_byte_count"]) == path.stat().st_size
    assert lock["upstream_original_payload_byte_lock_status"] == "locked_r22B1_xml_cif_pdf"
    assert "archive_regenerated_snapshot" in lock["snapshot_semantics"]
    assert lock["parse_status"] == "archive_regenerated_41_of_41_audit_fields_equivalent"


def test_payload_availability_distinguishes_snapshot_from_archive_payloads() -> None:
    r = rows("pdb_external_experimental_payload_availability.csv")
    by_type = {x["payload_type"]: x for x in r}
    snap = by_type["validation_report_parsed_snapshot"]
    assert snap["byte_lock_status"] == "snapshot_byte_hash_locked"
    assert snap["parse_status"] in {"parsed_predeclared_global_and_local_support_fields", "archive_regenerated_41_of_41_fields_equivalent"}
    for ptype in ("validation_report_cif", "validation_report_xml", "validation_report_pdf"):
        assert by_type[ptype]["byte_lock_status"] == "archive_payload_byte_hash_locked"
        assert by_type[ptype]["payload_sha256"]
        assert int(by_type[ptype]["payload_byte_count"]) > 0


def test_quality_rule_is_predeclared_and_deterministic() -> None:
    row = rows("pdb_external_quality_rule_policy.csv")[0]
    assert row["quality_rule_state_id"].endswith("v4002r22A1")
    assert row["quality_rule_declaration_id"].endswith("v4002r22A1")
    assert "policy_frozen_before_r22A1_residue_state_rematerialization" in row["validation_value_read_status"]
    assert "quality_excluded_if_any_required_component_is_excluded" in row["residue_support_aggregation_rule"]
    assert "quality_supported_iff_every_required_component_is_candidate_supported" in row["residue_support_aggregation_rule"]
    assert "no_numeric_threshold_in_this_rule" in row["RSRZ_policy"]
    assert "no_numeric_threshold_in_this_rule" in row["RSCC_policy"]
    assert row["atom_selector"] == "CA"


def test_validation_outlier_ingest_records_observable_aware_geometry_classes() -> None:
    r = rows("pdb_external_validation_residue_outlier_ingest.csv")
    assert len(r) == 4
    assert {x["label_seq_id"] for x in r} == {"7", "12", "14", "37"}
    assert {x["local_support_component_state"] for x in r} == {"quality_ambiguous"}
    assert {x["outlier_atom_scope"] for x in r} == {
        "selected_atom_or_backbone_geometry_flag",
        "sidechain_only_geometry_flag",
    }


def test_local_support_materialization_has_46_ambiguous_residues() -> None:
    r = rows("pdb_external_residue_quality_mask.csv")
    assert len(r) == 46
    assert sum(x["local_support_state"] == "quality_excluded" for x in r) == 0
    assert sum(x["local_support_state"] == "quality_ambiguous" for x in r) == 46
    assert sum(x["local_support_state"] == "quality_supported" for x in r) == 0
    assert {x["RSRZ_status"] for x in r} == {"unavailable_EDS_not_executed"}
    assert {x["RSCC_status"] for x in r} == {"unavailable_EDS_not_executed"}
    assert {x["quality_mask_state"] for x in r} == {"abstain"}


def test_pair_level_quality_overlay_materializes_all_ambiguous_and_abstain_counts() -> None:
    r = rows("pdb_external_quality_masked_contact_target.csv")
    assert len(r) == 946
    assert sum(x["coordinate_derived_contact_bit"] == "1" for x in r) == 114
    assert sum(x["coordinate_derived_contact_bit"] == "0" for x in r) == 832
    assert sum(x["pair_support_state"] == "quality_excluded" for x in r) == 0
    assert sum(x["pair_support_state"] == "quality_ambiguous" for x in r) == 946
    assert sum(x["pair_support_state"] == "quality_supported" for x in r) == 0
    assert {x["effective_target_state"] for x in r} == {"abstain"}
    assert {x["comparison_target_value_read_status"] for x in r} == {"not_read_not_joined_to_AOD_prediction"}


def test_target_mask_gate_and_aod_join_gate_are_distinct() -> None:
    row = rows("pdb_external_quality_masked_contact_summary.csv")[0]
    assert row["quality_supported_pair_count"] == "0"
    assert row["quality_ambiguous_pair_count"] == "946"
    assert row["quality_excluded_pair_count"] == "0"
    assert row["effective_abstain_count"] == "946"
    assert row["target_mask_activation_condition"] == "quality_supported_pair_count>0"
    assert row["aod_comparison_join_activation_condition"] == (
        "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_"
        "in_scope_pair_count>0_and_prediction_emitted_pair_count>0_and_comparable_pair_count>0"
    )
    assert row["prediction_emitted_pair_count"] == "0"
    assert row["comparable_pair_count"] == "0"
    assert row["target_mask_gate_state"] == "closed_zero_quality_supported_pairs"
    assert row["aod_comparison_join_gate_state"] == "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs"


def test_quality_policy_application_and_limitation_budget_are_current() -> None:
    app = rows("pdb_external_quality_mask_policy_application.csv")[0]
    assert app["quality_rule_id"].endswith("v4002r22A1")
    assert app["rule_application_status"] == "observable_aware_rule_applied_to_hash_locked_parsed_validation_snapshot"
    assert app["target_join_status"] == "target_only_mask_materialized_comparison_join_closed"
    limits = {x["limitation_component"]: x for x in rows("pdb_external_target_limitation_budget.csv")}
    assert limits["local_model_support"]["current_state"] == "observable_aware_validation_policy_materialized_zero_quality_supported_pairs_all_946_abstain"
    assert "alignment_rule" in limits["derived_contact_capability"]["implication"]
    assert limits["coordinate_model_capability"]["current_state"] == "unavailable_for_contact_pair_set"


def test_comparison_join_distinguishes_target_materialization_from_comparison_read() -> None:
    row = rows("pdb_external_comparison_join_declaration.csv")[0]
    assert row["target_branch_materialization_status"] == "target_only_mask_materialized"
    assert row["comparison_target_value_read_status"] == "not_read_not_joined_to_AOD_prediction"
    assert row["residual_status"] == "not_computed"
    assert row["score_status"] == "no_score"


def test_capability_current_and_activation_conditions_are_separate() -> None:
    p = rows("pdb_external_contact_observable_policy.csv")[0]
    assert p["aod_prediction_representation"] == "contact_pair_set"
    assert p["measurement_space_xray_capability_current"] == "blocked_by_prediction_representation"
    assert p["measurement_space_xray_activation_condition"] == "compatible_measurement_generative_AOD_output_frozen"
    assert p["coordinate_model_capability_current"] == "unavailable_for_contact_pair_set"
    assert p["coordinate_model_activation_condition"] == "compatible_coordinate_generative_AOD_output_frozen"


def test_historical_comparison_matrix_is_superseded_by_canonical_capability_gate() -> None:
    by_space = {x["comparison_space"]: x for x in rows("pdb_external_comparison_allowed_matrix.csv")}
    assert set(by_space) == {"registry", "coordinate_model", "derived_observable", "measurement_raw", "measurement_processed"}
    assert by_space["derived_observable"]["quality_supported_pair_count"] == "0"
    assert all(x["score_status"] == "no_score" for x in by_space.values())
    supersession = rows("pdb_external_comparison_matrix_supersession.csv")[0]
    assert supersession["matrix_status"] == "historical_carried_forward"
    assert supersession["superseded_by"].endswith("pdb_external_comparison_space_capability_gate.csv")
    canonical = {x["comparison_space"]: x for x in rows("pdb_external_comparison_space_capability_gate.csv")}
    assert canonical["derived_observable"]["activation_condition"] == (
        "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_"
        "in_scope_pair_count>0_and_prediction_emitted_pair_count>0_and_comparable_pair_count>0"
    )


def test_b_factor_and_occupancy_are_not_used_as_coordinate_error() -> None:
    p = rows("pdb_external_coordinate_use_policy.csv")[0]
    assert "not_coordinate_standard_error" in p["occupancy_semantics"]
    assert "not_coordinate_standard_error" in p["B_factor_semantics"]
    assert p["distance_uncertainty_rule"].startswith("no_distance_interval_from_B_factor_or_occupancy_alone")


def test_manifests_record_r22a_no_score_state() -> None:
    d = json.loads((PROT / "pdb_external_measurement_manifest.json").read_text(encoding="utf-8"))
    assert d["version_scope"] == "v40.02r23"
    assert d["quality_supported_pair_count"] == "0"
    assert d["effective_target_counts"] == {"contact": "0", "noncontact": "0", "abstain": "946"}
    assert d["comparison_target_value_read_status"] == "not_read_not_joined_to_AOD_prediction"
    q = json.loads((PROT / "pdb_external_quality_mask_manifest.json").read_text(encoding="utf-8"))
    assert q["version_scope"] == "v40.02r22A.1"
    assert q["quality_ambiguous_pair_count"] == "946"
    assert q["quality_excluded_pair_count"] == "0"
    assert q["effective_abstain_count"] == "946"
    v = json.loads((PROT / "pdb_external_validation_local_support_manifest.json").read_text(encoding="utf-8"))
    assert v["version_scope"] == "v40.02r22B.1"
    assert v["upstream_archive_original_byte_lock_status"] == "locked_r22B1_xml_cif_pdf"


def test_manual_sections_are_versionless_and_record_two_gates() -> None:
    text21 = (ROOT / "manual-2/sections/21_pdb_measurement_provenance_limitation_gate.tex").read_text(encoding="utf-8")
    text22 = (ROOT / "manual-2/sections/22_measurement_lineage_consistency_quality_mask.tex").read_text(encoding="utf-8")
    text23 = (ROOT / "manual-2/sections/23_validation_report_local_support_ingest_gate.tex").read_text(encoding="utf-8")
    assert "X_{\\rm physical}" in text21
    assert "N_{\\rm abstain}^{\\rm effective}=946" in text22
    assert "N_{\\rm residue}^{\\rm excluded}=0" in text23
    text24 = (ROOT / "manual-2/sections/24_validation_snapshot_provenance_observable_support_policy.tex").read_text(encoding="utf-8")
    assert "declared alignment/projection rule" in text23
    assert "N_{\\rm residue}^{\\rm ambiguous}=46" in text24
    assert "v40.02" not in text21 + text22 + text23 + text24


def test_validation_ingest_generator_is_offline_and_reproducible() -> None:
    import subprocess
    import sys

    tracked = [
        PROT / "external_pdb_validation_payloads/1crn_full_validation_report_parsed_snapshot.json",
        PROT / "pdb_external_validation_payload_byte_lock.csv",
        PROT / "pdb_external_residue_quality_mask.csv",
        PROT / "pdb_external_quality_masked_contact_target.csv",
        PROT / "pdb_external_quality_masked_contact_summary.csv",
        PROT / "pdb_external_measurement_manifest.json",
        PROT / "pdb_external_quality_mask_manifest.json",
        PROT / "pdb_external_validation_local_support_manifest.json",
        PROT / "pdb_external_quality_mask_policy_application.csv",
        PROT / "pdb_external_target_limitation_budget.csv",
        PROT / "pdb_external_contact_observable_policy.csv",
        PROT / "pdb_external_comparison_allowed_matrix.csv",
        PROT / "pdb_external_validation_snapshot_evidence_locators.csv",
        PROT / "pdb_external_validation_outlier_observable_policy.csv",
        PROT / "pdb_external_legacy_entry_policy.csv",
        PROT / "pdb_external_scored_accession_eligibility_rule.csv",
        PROT / "pdb_external_validation_snapshot_provenance_manifest.json",
    ]
    before = {p.name: p.read_bytes() for p in tracked}
    script = ROOT / "manual-2/scripts/ingest_external_pdb_validation_report_snapshot.py"
    text = script.read_text(encoding="utf-8")
    assert "requests" not in text
    assert "urllib" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    refine = ROOT / "manual-2/scripts/refine_external_pdb_validation_snapshot_provenance_policy.py"
    refine_text = refine.read_text(encoding="utf-8")
    assert "requests" not in refine_text
    assert "urllib" not in refine_text
    result2 = subprocess.run([sys.executable, str(refine)], cwd=ROOT, capture_output=True, text=True)
    assert result2.returncode == 0, result2.stderr
    after = {p.name: p.read_bytes() for p in tracked}
    assert after == before
