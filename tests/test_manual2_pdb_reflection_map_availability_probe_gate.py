from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2/data/protein"


def rows(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_normalization_policy_covers_all_41_equivalence_fields() -> None:
    policy = rows("pdb_external_validation_snapshot_normalization_policy.csv")
    evidence = rows("pdb_external_validation_snapshot_evidence_locators.csv")
    audit = rows("pdb_external_validation_snapshot_field_equivalence_audit.csv")
    assert len(policy) == len(evidence) == len(audit) == 41
    assert len({r["normalization_rule_id"] for r in policy}) == 41
    assert {r["snapshot_field_path"] for r in policy} == {r["snapshot_field_path"] for r in audit}
    assert all(r["source_locator"] for r in policy)
    assert all(r["normalization_operation"] for r in policy)
    assert all(r["normalized_type"].startswith("json_") for r in policy)
    assert {r["field_equivalence_status"] for r in policy} == {"exact_after_declared_normalization"}


def test_probe_states_and_evidence_are_explicit_without_fabricated_http_results() -> None:
    p = rows("pdb_external_reflection_map_probe_evidence.csv")
    assert len(p) == 7
    assert {r["probe_state"] for r in p} == {"probed_unavailable", "not_probed"}
    assert sum(r["probe_state"] == "probed_unavailable" for r in p) == 6
    assert sum(r["probe_state"] == "not_probed" for r in p) == 1
    for r in p:
        assert r["probe_state"] in {"not_probed", "probed_unavailable", "retrieved_unlocked", "byte_hash_locked"}
        assert r["http_status"] == "not_directly_observed"
        assert r["content_type"] == "not_observed"
        assert r["content_length"] == "not_observed"
        assert r["etag"] == "not_observed"
        assert r["last_modified"] == "not_observed"
        assert r["byte_lock_status"] == "not_locked"
        assert r["sha256"] == ""
        assert r["local_payload_path"] == ""
        assert r["probe_method"]
        assert r["evidence_detail"]


def test_availability_summary_closes_measurement_space_for_1crn() -> None:
    s = rows("pdb_external_reflection_map_availability_summary.csv")[0]
    assert s["probe_row_count"] == "7"
    assert s["byte_hash_locked_count"] == "0"
    assert s["probed_unavailable_count"] == "6"
    assert s["not_probed_count"] == "1"
    assert s["reflection_payload_state"] == "probed_unavailable"
    assert s["map_coefficient_state"] == "probed_unavailable"
    assert s["measurement_space_lane"] == "unavailable_for_current_accession"
    assert s["coordinate_model_lane"] == "active_reconstruction_space_fixture"
    assert s["derived_observable_lane"] == "active_with_quality_mask_but_zero_supported_pairs"


def test_measurement_availability_and_comparison_matrix_are_updated() -> None:
    availability = {r["payload_type"]: r for r in rows("pdb_external_experimental_payload_availability.csv")}
    assert availability["reflection_payload_structure_factors"]["payload_availability"] == "probed_unavailable"
    assert availability["processed_reflection_payload"]["payload_availability"] == "probed_unavailable"
    assert availability["map_coefficients"]["payload_availability"] == "probed_unavailable"
    assert availability["raw_diffraction_images"]["availability_probe_status"] == "not_probed_optional_registry_lane"

    matrix = {r["comparison_space"]: r for r in rows("pdb_external_comparison_allowed_matrix.csv")}
    assert matrix["measurement_raw"]["current_target_support"] == "reflection_payload_probed_unavailable_for_1CRN"
    assert matrix["measurement_processed"]["current_target_support"] == "map_coefficients_probed_unavailable_for_1CRN"
    assert matrix["derived_observable"]["quality_supported_pair_count"] == "0"
    assert {r["score_status"] for r in matrix.values()} == {"no_score"}


def test_candidate_universe_snapshot_is_required_before_selection() -> None:
    r = rows("pdb_external_scored_accession_candidate_universe_policy.csv")[0]
    assert r["archive_query_timestamp_utc"] == "not_run"
    assert r["eligible_accession_list"] == "not_materialized"
    assert r["eligible_accession_list_sha256"] == "not_available"
    assert r["selected_accession"] == "none"
    assert r["candidate_universe_status"] == "selection_blocked_until_candidate_universe_snapshot"
    assert r["target_agreement_read_status"] == "not_read"


def test_large_payload_policy_is_applied_and_inventory_remains_authoritative() -> None:
    policy = rows("external_payload_embedding_policy.csv")
    assert {r["policy_status"] for r in policy} == {"applied_in_r24"}
    by_class = {r["payload_class"]: r for r in policy}
    assert by_class["reflection_or_map_payload"]["large_payload_action"] == "separate_versioned_payload_pack"
    assert "manifest_only" in by_class["raw_diffraction_images"]["large_payload_action"]
    status = json.loads((PROT / "external_payload_bundle_status.json").read_text(encoding="utf-8"))
    assert status["policy_version"] == "v40.03r01"
    assert status["inventory_authority"].endswith("external_payload_bundle_inventory.csv")
    assert status["measurement_space_lane"] == "inactive_target_payload_unavailable_and_representation_incompatible"


def test_probe_manifest_records_gate_only_and_no_score() -> None:
    d = json.loads((PROT / "pdb_external_reflection_map_probe_manifest.json").read_text(encoding="utf-8"))
    assert d["version_scope"] == "v40.02r22B.2"
    assert d["normalization_rule_count"] == 41
    assert d["probe_state_counts"] == {
        "not_probed": 1,
        "probed_unavailable": 6,
        "retrieved_unlocked": 0,
        "byte_hash_locked": 0,
    }
    assert d["measurement_space_lane"] == "unavailable_for_current_accession"
    assert d["target_value_read_status"] == "not_read_not_joined_to_AOD_prediction"
    assert d["residual_status"] == "not_computed"
    assert d["score_status"] == "no_score"
    assert d["candidate_universe_status"] == "selection_blocked_until_candidate_universe_snapshot"


def test_manual_section_is_versionless_and_gate_only() -> None:
    text = (ROOT / "manual-2/sections/26_reflection_map_availability_probe_byte_lock_gate.tex").read_text(encoding="utf-8")
    assert "Reflection and map availability probe / byte-lock gate" in text
    assert "not\\_directly\\_observed" in text
    assert "unavailable\\_for\\_current\\_accession" in text
    assert "candidate-universe snapshot" in text
    assert "v40.02" not in text


def test_r22b2_generator_is_offline_and_reproducible() -> None:
    tracked = [
        PROT / "pdb_external_validation_snapshot_normalization_policy.csv",
        PROT / "pdb_external_reflection_map_probe_evidence.csv",
        PROT / "pdb_external_reflection_map_availability_summary.csv",
        PROT / "pdb_external_reflection_map_byte_lock.csv",
        PROT / "pdb_external_reflection_map_access_control.csv",
        PROT / "pdb_external_reflection_map_leakage_checks.csv",
        PROT / "pdb_external_scored_accession_candidate_universe_policy.csv",
        PROT / "pdb_external_reflection_map_probe_manifest.json",
        PROT / "pdb_external_experimental_payload_availability.csv",
        PROT / "pdb_external_comparison_allowed_matrix.csv",
        PROT / "pdb_external_target_limitation_budget.csv",
        PROT / "external_payload_embedding_policy.csv",
        PROT / "external_payload_bundle_status.json",
        PROT / "external_payload_bundle_inventory.csv",
        PROT / "pdb_external_measurement_manifest.json",
    ]
    before = {p.name: p.read_bytes() for p in tracked}
    script = ROOT / "manual-2/scripts/probe_external_pdb_reflection_map_availability.py"
    text = script.read_text(encoding="utf-8")
    assert "requests" not in text
    assert "urllib" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = {p.name: p.read_bytes() for p in tracked}
    assert after == before
