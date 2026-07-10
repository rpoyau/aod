from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def rows(name: str) -> list[dict[str, str]]:
    with (PROT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r22a1_files_and_section_are_present() -> None:
    names = [
        "pdb_external_validation_snapshot_evidence_locators.csv",
        "pdb_external_validation_outlier_observable_policy.csv",
        "pdb_external_legacy_entry_policy.csv",
        "pdb_external_scored_accession_eligibility_rule.csv",
        "pdb_external_validation_snapshot_provenance_manifest.json",
    ]
    for name in names:
        assert (PROT / name).is_file(), name
    assert (ROOT / "manual-2/scripts/refine_external_pdb_validation_snapshot_provenance_policy.py").is_file()
    assert (ROOT / "manual-2/sections/24_validation_snapshot_provenance_observable_support_policy.tex").is_file()


def test_snapshot_evidence_locators_cover_every_audit_field() -> None:
    expected = {
        "$.source_report_generated_utc",
        "$.validation_pipeline.wwpdb_validation_pipeline",
        "$.validation_pipeline.molprobity",
        "$.validation_pipeline.xtriage",
        "$.validation_pipeline.eds",
        "$.validation_pipeline.percentile_statistics",
        "$.entry.experimental_method",
        "$.entry.reported_resolution_angstrom",
        "$.entry.chain_id",
        "$.entry.residue_count",
        "$.entry.atom_count",
        "$.entry.zero_occupancy_atom_count",
        "$.entry.alternate_conformation_residue_count",
        "$.entry.trace_residue_count",
        "$.entry.space_group",
        "$.entry.cell.a",
        "$.entry.cell.b",
        "$.entry.cell.c",
        "$.entry.cell.alpha",
        "$.entry.cell.beta",
        "$.entry.cell.gamma",
        "$.entry.refinement_program",
        "$.entry.r_work",
        "$.entry.r_free",
        "$.entry.completeness",
        "$.entry.rmerge",
        "$.entry.rsym",
        "$.entry.average_b_all_atoms_angstrom2",
        "$.entry.clash_count",
        "$.entry.symmetry_clash_count",
        "$.entry.ramachandran_outlier_count",
        "$.entry.sidechain_outlier_count",
        "$.entry.chain_break_count",
        "$.local_model_to_data.eds_status",
        "$.local_model_to_data.rsrz_available",
        "$.local_model_to_data.rscc_available",
        "$.local_model_to_data.missing_density_assessment_available",
        "$.geometry_outliers[0]",
        "$.geometry_outliers[1]",
        "$.geometry_outliers[2]",
        "$.geometry_outliers[3]",
    }
    r = rows("pdb_external_validation_snapshot_evidence_locators.csv")
    assert {x["snapshot_field_path"] for x in r} == expected
    assert len(r) == 41
    assert all(x["source_report_page"] for x in r)
    assert all(x["source_report_section"] for x in r)
    assert all(x["source_table_or_row"] for x in r)
    assert all(x["snapshot_sha256"] == sha(PROT / "external_pdb_validation_payloads/1crn_full_validation_report_parsed_snapshot.json") for x in r)
    assert all(x["source_machine_locator"] for x in r)
    assert {x["source_payload_lock_status"] for x in r} == {"archive_payload_byte_hash_locked"}
    assert {x["field_equivalence_status"] for x in r} == {"exact_after_declared_normalization"}


def test_observable_aware_outlier_policy_distinguishes_evidence_classes() -> None:
    by_type = {x["outlier_type"]: x for x in rows("pdb_external_validation_outlier_observable_policy.csv")}
    assert by_type["selected_atom_missing"]["support_action"] == "quality_excluded"
    assert by_type["selected_atom_altloc_unresolved"]["support_action"] == "quality_excluded"
    assert by_type["selected_atom_or_backbone_geometry_flag"]["support_action"] == "quality_ambiguous"
    assert by_type["sidechain_only_geometry_flag"]["support_action"] == "quality_ambiguous"
    assert by_type["missing_local_model_to_data_support"]["support_action"] == "quality_ambiguous"
    assert {x["atom_selector"] for x in by_type.values()} == {"CA"}
    assert {x["policy_freeze_status"] for x in by_type.values()} == {"frozen_before_r22A1_residue_state_rematerialization"}


def test_current_outliers_are_ambiguous_not_coordinate_exclusions() -> None:
    r = rows("pdb_external_validation_residue_outlier_ingest.csv")
    assert {x["label_seq_id"] for x in r} == {"7", "12", "14", "37"}
    assert {x["local_support_component_state"] for x in r} == {"quality_ambiguous"}
    selected = {x["label_seq_id"] for x in r if x["outlier_atom_scope"] == "selected_atom_or_backbone_geometry_flag"}
    sidechain = {x["label_seq_id"] for x in r if x["outlier_atom_scope"] == "sidechain_only_geometry_flag"}
    assert selected == {"7", "37"}
    assert sidechain == {"12", "14"}


def test_observable_aware_rematerialization_preserves_all_abstain_target() -> None:
    residue = rows("pdb_external_residue_quality_mask.csv")
    assert len(residue) == 46
    assert {x["local_support_state"] for x in residue} == {"quality_ambiguous"}
    pair = rows("pdb_external_quality_masked_contact_target.csv")
    assert len(pair) == 946
    assert {x["pair_support_state"] for x in pair} == {"quality_ambiguous"}
    assert {x["effective_target_state"] for x in pair} == {"abstain"}
    assert sum(x["coordinate_derived_contact_bit"] == "1" for x in pair) == 114
    assert sum(x["coordinate_derived_contact_bit"] == "0" for x in pair) == 832


def test_legacy_entry_and_scored_accession_selection_policy_are_frozen() -> None:
    legacy = rows("pdb_external_legacy_entry_policy.csv")[0]
    assert legacy["source_accession"] == "1CRN"
    assert legacy["lane_role"] == "measurement_lineage_coordinate_model_abstention_fixture"
    assert legacy["policy_status"] == "path_A_frozen_legacy_entry_not_first_quality_supported_score_target"
    assert legacy["target_agreement_read_status"] == "not_read_for_accession_policy_or_selection"

    eligibility = rows("pdb_external_scored_accession_eligibility_rule.csv")
    assert len(eligibility) == 12
    assert {x["criterion_status"] for x in eligibility} == {"frozen_before_accession_selection"}
    assert {x["target_agreement_read_status"] for x in eligibility} == {"not_read"}
    assert {x["accession_selection_status"] for x in eligibility} == {"rule_frozen_no_accession_selected_in_this_gate"}
    assert {x["accession_selection_method"] for x in eligibility} == {"lexicographically_lowest_accession_among_all_eligible_entries"}


def test_provenance_manifest_records_snapshot_not_archive_payload() -> None:
    d = json.loads((PROT / "pdb_external_validation_snapshot_provenance_manifest.json").read_text(encoding="utf-8"))
    assert d["version_scope"] == "v40.02r22B.1"
    assert d["locked_object_semantics"] == "release_local_parsed_validation_snapshot_not_original_archive_payload"
    assert d["archive_validation_payload_lock_status"] == "xml_cif_pdf_archive_payloads_byte_hash_locked"
    assert d["parse_equivalence_audit_status"] == "41_of_41_exact_after_declared_normalization"
    assert d["residue_counts"] == {"quality_supported": 0, "quality_ambiguous": 46, "quality_excluded": 0}
    assert d["pair_counts"] == {"quality_supported": 0, "quality_ambiguous": 946, "quality_excluded": 0}
    assert d["effective_target_counts"] == {"contact": 0, "noncontact": 0, "abstain": 946}
    assert d["target_join_status"] == "closed_zero_supported_pairs_no_alignment_no_prediction_emission_no_comparable_pairs"
    assert d["prediction_emitted_pair_count"] == 0
    assert d["comparable_pair_count"] == 0
    assert d["score_status"] == "no_score"
    for key, rel in d["files"].items():
        assert d["file_sha256"][key] == sha(ROOT / rel)


def test_manual_section_is_versionless_and_records_current_policy() -> None:
    text = (ROOT / "manual-2/sections/24_validation_snapshot_provenance_observable_support_policy.tex").read_text(encoding="utf-8")
    assert "release-local parsed validation snapshot" in text
    assert "selected-atom/backbone geometry flag" in text
    assert "side-chain-only geometry flag" in text
    assert "N_{\\rm residue}^{\\rm ambiguous}=46" in text
    assert "N_{\\rm pair}^{\\rm ambiguous}" not in text or "946" in text
    assert "v40.02" not in text


def test_r22a1_refinement_generator_is_offline_and_reproducible() -> None:
    tracked = [
        PROT / "pdb_external_validation_snapshot_evidence_locators.csv",
        PROT / "pdb_external_validation_outlier_observable_policy.csv",
        PROT / "pdb_external_legacy_entry_policy.csv",
        PROT / "pdb_external_scored_accession_eligibility_rule.csv",
        PROT / "pdb_external_validation_snapshot_provenance_manifest.json",
        PROT / "pdb_external_residue_quality_mask.csv",
        PROT / "pdb_external_quality_masked_contact_target.csv",
        PROT / "pdb_external_quality_masked_contact_summary.csv",
        PROT / "pdb_external_quality_mask_manifest.json",
        PROT / "pdb_external_validation_local_support_manifest.json",
        PROT / "pdb_external_measurement_manifest.json",
    ]
    before = {p.name: p.read_bytes() for p in tracked}
    script = ROOT / "manual-2/scripts/refine_external_pdb_validation_snapshot_provenance_policy.py"
    text = script.read_text(encoding="utf-8")
    assert "requests" not in text
    assert "urllib" not in text
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = {p.name: p.read_bytes() for p in tracked}
    assert after == before
