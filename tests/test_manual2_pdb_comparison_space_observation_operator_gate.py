from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2/data/protein"


def rows(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r23_files_exist_and_manifest_is_current() -> None:
    names = [
        "pdb_external_probe_evidence_membership_audit.csv",
        "pdb_external_payload_family_locator_variants.csv",
        "pdb_external_payload_family_availability.csv",
        "pdb_external_comparison_space_capability_gate.csv",
        "pdb_external_observation_operator_family_registry.csv",
        "pdb_external_observation_operator_state.csv",
        "pdb_external_derived_contact_operator_declaration.csv",
        "pdb_external_observation_operator_nuisance_policy.csv",
        "pdb_external_observation_operator_leakage_checks.csv",
        "pdb_external_scored_accession_candidate_universe_snapshot_gate.csv",
        "pdb_external_comparison_space_operator_manifest.json",
    ]
    for name in names:
        assert (PROT / name).is_file(), name
    manifest = json.loads((PROT / "pdb_external_comparison_space_operator_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r23"
    assert manifest["target_values_read_status"] == "not_read_by_operator_freeze"
    assert manifest["residual_status"] == "not_computed"
    assert manifest["score_status"] == "no_score"


def test_probe_family_normalization_uses_refined_state_vocabulary() -> None:
    family = {r["payload_family_id"]: r for r in rows("pdb_external_payload_family_availability.csv")}
    assert set(family) == {"reflection_data", "validation_map_coefficients", "xray_map_service", "raw_image_registry"}
    assert family["reflection_data"]["availability_state"] == "not_listed_in_locked_official_evidence"
    assert family["validation_map_coefficients"]["availability_state"] == "not_listed_in_locked_official_evidence"
    assert family["xray_map_service"]["availability_state"] == "upstream_prerequisite_not_satisfied"
    assert family["raw_image_registry"]["availability_state"] == "not_probed"
    assert sum(int(r["locator_variant_count"]) for r in family.values()) == 7


def test_locator_variants_are_separate_from_payload_families() -> None:
    locators = rows("pdb_external_payload_family_locator_variants.csv")
    assert len(locators) == 7
    assert len({r["locator_variant_id"] for r in locators}) == 7
    assert {r["payload_family_id"] for r in locators} == {
        "reflection_data", "validation_map_coefficients", "xray_map_service", "raw_image_registry"
    }
    assert sum(r["payload_family_id"] == "reflection_data" for r in locators) == 3
    assert sum(r["payload_family_id"] == "validation_map_coefficients" for r in locators) == 2


def test_release_local_evidence_snapshot_is_hash_locked_and_honestly_typed() -> None:
    path = PROT / "external_pdb_probe_evidence_snapshots/1crn_official_entry_map_docs_parsed_snapshot.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["snapshot_class"] == "release_local_parsed_official_evidence_snapshot"
    assert "not_byte_locked" in data["source_byte_lock_status"]
    assert "not an archive byte lock" in data["interpretation_guard"]
    audit = rows("pdb_external_probe_evidence_membership_audit.csv")
    assert len(audit) == 6
    assert {r["evidence_snapshot_sha256"] for r in audit} == {sha(path)}
    by_id = {r["evidence_query_id"]: r for r in audit}
    assert by_id["1CRN_entry_has_structure_factor_download"]["evidence_membership_result"] == "absent"
    assert by_id["1CRN_entry_has_map_coefficient_download"]["evidence_membership_result"] == "absent"
    assert by_id["1CRN_validation_eds_executed"]["evidence_membership_result"] == "false"


def test_operator_states_match_current_capability() -> None:
    states = {r["comparison_space"]: r for r in rows("pdb_external_comparison_space_capability_gate.csv")}
    assert states["registry"]["operator_state"] == "active_provenance_only"
    assert states["measurement_raw"]["operator_state"] == "inactive_target_payload_unavailable_and_representation_incompatible"
    assert states["measurement_processed"]["operator_state"] == "inactive_target_payload_unavailable_and_representation_incompatible"
    assert states["coordinate_model"]["operator_state"] == "inactive_AOD_coordinate_representation_unavailable"
    assert states["derived_observable"]["operator_state"] == "declared_but_comparison_inactive_zero_supported_pairs_and_zero_alignment_coverage"
    assert {r["score_status"] for r in states.values()} == {"no_score"}


def test_derived_contact_operator_is_declared_without_target_read_or_score() -> None:
    d = rows("pdb_external_derived_contact_operator_declaration.csv")[0]
    assert d["aod_prediction_representation"] == "contact_pair_set"
    assert d["contact_atom_selector"] == "CA"
    assert d["contact_threshold_angstrom"] == "8.0"
    assert d["minimum_sequence_separation"] == "3"
    assert d["target_observable_domain"] == "1|0|abstain"
    assert d["alignment_projection_rule"] == "none_declared"
    assert d["operator_state"] == "declared_inactive"
    assert d["target_values_read_status"] == "not_read_by_operator_freeze"
    assert d["residual_status"] == "not_computed"
    assert d["score_status"] == "no_score"


def test_nuisance_policy_has_no_target_fitted_parameter() -> None:
    nuisance = rows("pdb_external_observation_operator_nuisance_policy.csv")
    assert nuisance
    assert all("estimated_on_work_subset" not in r["parameter_classification"] for r in nuisance)
    assert all(r["target_value_estimation_status"] in {"not_estimated_from_target_agreement", "not_estimated_from_AOD_agreement", "not_estimated"} for r in nuisance)
    xray = next(r for r in nuisance if r["nuisance_parameter_id"] == "xray_forward_operator")
    assert xray["parameter_value"] == "not_instantiated"
    assert xray["holdout_policy"] == "required_before_any_future_target_value_fit"


def test_candidate_selection_remains_blocked_without_snapshot() -> None:
    r = rows("pdb_external_scored_accession_candidate_universe_snapshot_gate.csv")[0]
    assert r["candidate_universe_snapshot_id"] == "pending_official_RCSB_search_API_response"
    assert r["candidate_universe_count"] == "not_materialized"
    assert r["eligible_accession_count"] == "not_materialized"
    assert r["eligible_accession_list_sha256"] == ""
    assert r["selected_accession"] == "none"
    assert r["selection_status"] == "blocked_pending_official_query_response_byte_lock_and_eligibility_materialization"
    assert r["target_agreement_read_status"] == "not_read"


def test_external_payload_inventory_authorizes_evidence_snapshot() -> None:
    inv = rows("external_payload_bundle_inventory.csv")
    hit = [r for r in inv if r["payload_class"] == "release_local_parsed_official_evidence_snapshot"]
    assert len(hit) == 1
    row = hit[0]
    src = ROOT / row["source_path"]
    assert src.is_file()
    assert row["bundle_path"] == "external_payloads/pdb_probe_evidence/1crn_official_entry_map_docs_parsed_snapshot.json"
    assert row["origin_class"] == "release_local_derived"
    assert row["embedding_class"] == "inline_bundle"
    assert row["payload_sha256"] == sha(src)
    assert row["payload_byte_count"] == str(src.stat().st_size)


def test_r23_section_is_versionless_and_gate_only() -> None:
    text = (ROOT / "manual-2/sections/27_comparison_space_capability_observation_operator_freeze_gate.tex").read_text(encoding="utf-8")
    assert "Comparison-space capability and observation-operator freeze gate" in text
    assert "not\\_listed\\_in\\_locked\\_official\\_evidence" in text
    assert "upstream\\_prerequisite\\_not\\_satisfied" in text
    assert "declared\\_but\\_comparison\\_inactive" in text
    assert "Target values are not read" in text
    assert "v40.02" not in text


def test_r23_generator_is_offline_and_reproducible() -> None:
    tracked = [
        PROT / "external_pdb_probe_evidence_snapshots/1crn_official_entry_map_docs_parsed_snapshot.json",
        PROT / "pdb_external_probe_evidence_membership_audit.csv",
        PROT / "pdb_external_payload_family_locator_variants.csv",
        PROT / "pdb_external_payload_family_availability.csv",
        PROT / "pdb_external_comparison_space_capability_gate.csv",
        PROT / "pdb_external_observation_operator_family_registry.csv",
        PROT / "pdb_external_observation_operator_state.csv",
        PROT / "pdb_external_derived_contact_operator_declaration.csv",
        PROT / "pdb_external_observation_operator_nuisance_policy.csv",
        PROT / "pdb_external_observation_operator_leakage_checks.csv",
        PROT / "pdb_external_scored_accession_candidate_universe_snapshot_gate.csv",
        PROT / "pdb_external_comparison_space_operator_manifest.json",
        PROT / "external_payload_bundle_inventory.csv",
        PROT / "external_payload_bundle_status.json",
        PROT / "external_payload_embedding_policy.csv",
    ]
    before = {str(p): p.read_bytes() for p in tracked}
    script = ROOT / "manual-2/scripts/freeze_external_pdb_comparison_space_observation_operator.py"
    source = script.read_text(encoding="utf-8")
    assert "requests" not in source
    assert "urllib" not in source
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = {str(p): p.read_bytes() for p in tracked}
    assert after == before
