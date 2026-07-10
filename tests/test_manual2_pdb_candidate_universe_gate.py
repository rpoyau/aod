from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2/data/protein"
QUERY = PROT / "external_pdb_candidate_universe_queries/rcsb_search_candidate_universe_query_r24.json"


def rows(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r24_gate_files_and_manifest_exist() -> None:
    names = [
        "pdb_external_motif_compatibility_policy.csv",
        "pdb_external_scored_accession_eligibility_rule_v2.csv",
        "pdb_external_candidate_universe_query_response_status.csv",
        "pdb_external_scored_accession_candidate_universe_snapshot_gate.csv",
        "pdb_external_candidate_universe_eligibility_audit.csv",
        "pdb_external_candidate_universe_selection_gate.csv",
        "pdb_external_comparison_matrix_supersession.csv",
        "pdb_external_candidate_universe_leakage_checks.csv",
        "pdb_external_candidate_universe_manifest.json",
    ]
    assert QUERY.is_file()
    for name in names:
        assert (PROT / name).is_file(), name
    d = json.loads((PROT / "pdb_external_candidate_universe_manifest.json").read_text(encoding="utf-8"))
    assert d["version_scope"] == "v40.02r24"
    assert d["candidate_universe_query_spec_sha256"] == sha(QUERY)
    assert d["archive_query_response_status"] == "not_materialized_offline_build"
    assert d["candidate_universe_snapshot_status"] == "blocked_pending_official_query_response_byte_lock"
    assert d["selected_accession"] is None
    assert d["target_agreement_read_status"] == "not_read"
    assert d["residual_status"] == "not_computed"
    assert d["score_status"] == "no_score"


def test_motif_policy_is_frozen_before_universe_or_selection() -> None:
    r = rows("pdb_external_motif_compatibility_policy.csv")[0]
    assert r["motif_compatibility_policy_id"] == "pdb_candidate_motif_compatibility_contact_reclosure_v1"
    assert r["aod_packet_family"] == "contact_reclosure"
    assert r["aod_source_packet_id"] == "chain_GAS_tripeptide_seed"
    assert r["candidate_screening_scope"] == "topology_and_window_capacity_only_not_alignment"
    assert r["allowed_external_chain_length_min"] == "40"
    assert r["allowed_external_chain_length_max"] == "250"
    assert r["minimum_external_window_length"] == "4"
    assert "no residue identity or contact value is inspected" in r["motif_to_residue_window_rule"]
    assert r["target_agreement_read_status"] == "not_read"
    assert r["policy_freeze_status"] == "frozen_before_candidate_universe_materialization_and_accession_selection"


def test_archive_query_spec_is_hash_locked_but_response_is_not_invented() -> None:
    q = json.loads(QUERY.read_text(encoding="utf-8"))
    assert q["endpoint"] == "https://search.rcsb.org/rcsbsearch/v2/query"
    assert q["query_execution_status"] == "not_executed_in_offline_release_build"
    request = q["query_request"]
    assert request["return_type"] == "entry"
    assert request["request_options"]["return_all_hits"] is True
    nodes = request["query"]["nodes"]
    assert nodes[0]["parameters"]["attribute"] == "exptl.method"
    assert nodes[0]["parameters"]["value"] == "X-RAY DIFFRACTION"
    assert nodes[1]["parameters"]["attribute"] == "rcsb_entry_info.resolution_combined"
    assert nodes[1]["parameters"]["operator"] == "less_or_equal"
    assert nodes[1]["parameters"]["value"] == 2.0
    status = rows("pdb_external_candidate_universe_query_response_status.csv")[0]
    assert status["archive_query_spec_sha256"] == sha(QUERY)
    assert status["archive_query_response_path"] == ""
    assert status["archive_query_response_sha256"] == ""
    assert status["archive_query_response_status"] == "not_materialized_offline_build"
    assert status["candidate_universe_materialization_status"] == "blocked_pending_official_query_response_byte_lock"


def test_selection_is_target_independent_and_blocked_without_frozen_response() -> None:
    snap = rows("pdb_external_scored_accession_candidate_universe_snapshot_gate.csv")[0]
    sel = rows("pdb_external_candidate_universe_selection_gate.csv")[0]
    assert snap["candidate_universe_count"] == "not_materialized"
    assert snap["eligible_accession_count"] == "not_materialized"
    assert snap["selected_accession"] == "none"
    assert sel["selected_accession"] == "none"
    assert sel["selection_status"] == "blocked_no_materialized_candidate_universe"
    assert sel["selection_target_values_read_status"] == "not_read"
    assert sel["selection_AOD_agreement_values_read_status"] == "not_read"
    assert sel["next_required_input"] == "byte_locked_official_RCSB_search_API_response_JSON"


def test_canonical_matrix_supersedes_historical_matrix() -> None:
    r = rows("pdb_external_comparison_matrix_supersession.csv")[0]
    assert r["matrix_path"].endswith("pdb_external_comparison_allowed_matrix.csv")
    assert r["matrix_status"] == "historical_carried_forward"
    assert r["superseded_by"].endswith("pdb_external_comparison_space_capability_gate.csv")
    assert r["canonical_matrix_status"] == "authoritative_current_capability_state"
    m = json.loads((PROT / "pdb_external_comparison_space_operator_manifest.json").read_text(encoding="utf-8"))
    assert m["canonical_comparison_matrix"].endswith("pdb_external_comparison_space_capability_gate.csv")
    assert m["historical_comparison_matrix"].endswith("pdb_external_comparison_allowed_matrix.csv")


def test_comparison_activation_requires_prediction_emission_and_comparable_pairs() -> None:
    strict = (
        "quality_supported_pair_count>0_and_declared_alignment_projection_rule_and_"
        "in_scope_pair_count>0_and_prediction_emitted_pair_count>0_and_comparable_pair_count>0"
    )
    capability = {r["comparison_space"]: r for r in rows("pdb_external_comparison_space_capability_gate.csv")}
    assert capability["derived_observable"]["activation_condition"] == strict
    derived = rows("pdb_external_derived_contact_operator_declaration.csv")[0]
    assert derived["comparison_join_rule"] == strict
    join = rows("pdb_external_comparison_join_declaration.csv")[0]
    assert join["aod_comparison_join_activation_condition"] == strict
    assert join["prediction_emitted_pair_count"] == "0"
    assert join["comparable_pair_count"] == "0"
    summary = rows("pdb_external_quality_masked_contact_summary.csv")[0]
    assert summary["aod_comparison_join_activation_condition"] == strict
    assert summary["prediction_emitted_pair_count"] == "0"
    assert summary["comparable_pair_count"] == "0"


def test_query_spec_is_registered_in_external_payload_allowlist() -> None:
    inv = rows("external_payload_bundle_inventory.csv")
    hit = [r for r in inv if r["source_path"].endswith("rcsb_search_candidate_universe_query_r24.json")]
    assert len(hit) == 1
    r = hit[0]
    assert r["bundle_path"] == "external_payloads/pdb_candidate_universe/rcsb_search_candidate_universe_query_r24.json"
    assert r["origin_class"] == "release_policy_metadata"
    assert r["required_for_release"] == "yes"
    assert r["payload_sha256"] == sha(QUERY)


def test_r24_manual_section_is_versionless_and_gate_only() -> None:
    text = (ROOT / "manual-2/sections/28_candidate_universe_snapshot_selection_gate.tex").read_text(encoding="utf-8")
    assert "Candidate-universe snapshot and target-independent accession selection gate" in text
    assert "official archive response was not materialized" in text
    assert "selected\\_accession}=\\texttt{none}" in text
    assert "N_{\\mathrm{prediction\\ emitted}}>0" in text
    assert "N_{\\mathrm{comparable}}>0" in text
    assert "No target contact value and no AOD agreement value is read" in text
    assert "v40.02" not in text


def test_r24_generator_is_offline_and_reproducible() -> None:
    tracked = [
        PROT / "pdb_external_motif_compatibility_policy.csv",
        PROT / "pdb_external_scored_accession_eligibility_rule_v2.csv",
        QUERY,
        PROT / "pdb_external_candidate_universe_query_response_status.csv",
        PROT / "pdb_external_scored_accession_candidate_universe_snapshot_gate.csv",
        PROT / "pdb_external_candidate_universe_eligibility_audit.csv",
        PROT / "pdb_external_candidate_universe_selection_gate.csv",
        PROT / "pdb_external_comparison_matrix_supersession.csv",
        PROT / "pdb_external_candidate_universe_leakage_checks.csv",
        PROT / "pdb_external_candidate_universe_manifest.json",
        PROT / "pdb_external_comparison_space_capability_gate.csv",
        PROT / "pdb_external_derived_contact_operator_declaration.csv",
        PROT / "pdb_external_comparison_join_declaration.csv",
        PROT / "pdb_external_quality_masked_contact_summary.csv",
        PROT / "pdb_external_quality_mask_manifest.json",
        PROT / "pdb_external_comparison_space_operator_manifest.json",
        PROT / "external_payload_bundle_inventory.csv",
        PROT / "external_payload_bundle_status.json",
        PROT / "external_payload_embedding_policy.csv",
    ]
    before = {str(p): p.read_bytes() for p in tracked}
    script = ROOT / "manual-2/scripts/freeze_external_pdb_candidate_universe_selection_gate.py"
    source = script.read_text(encoding="utf-8")
    assert "requests" not in source
    assert "urllib.request" not in source
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = {str(p): p.read_bytes() for p in tracked}
    assert after == before
