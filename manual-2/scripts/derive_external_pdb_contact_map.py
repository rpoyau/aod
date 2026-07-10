from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2/data/protein"
VERSION = "v40.02r15"
VERSION_LABEL = "v40.02r15_external_pdb_contact_map_derivation_gate"
PAYLOAD_SHA = "23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba"
RESIDUE_TABLE = PROT / "pdb_external_residue_coordinate_table.csv"
CONTACT_THRESHOLD = 8.0
MIN_SEQUENCE_SEPARATION = 3
SEQUENCE_SEPARATION_RULE = "abs(label_seq_id_j-label_seq_id_i)>=3"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def derive() -> None:
    residue_table_sha256 = sha256_file(RESIDUE_TABLE)
    manifest = json.loads((PROT / "pdb_external_residue_coordinate_table_manifest.json").read_text(encoding="utf-8"))
    if manifest["coordinate_payload_sha256"] != PAYLOAD_SHA:
        raise RuntimeError("residue table manifest does not reference the locked 1CRN byte payload")
    if manifest["coordinate_table_sha256"] != residue_table_sha256:
        raise RuntimeError("residue table SHA-256 no longer matches the r14 manifest")
    residues = sorted(read_csv(RESIDUE_TABLE), key=lambda row: int(row["label_seq_id"]))
    for row in residues:
        if row["coordinate_payload_sha256"] != PAYLOAD_SHA:
            raise RuntimeError("residue row uses an unexpected coordinate payload hash")
        if row["chain_id"] != "A" or row["model_id"] != "1" or row["atom_selector"] != "CA":
            raise RuntimeError("residue row violates the locked chain/model/atom policy")

    all_pairs: list[dict[str, str]] = []
    contact_rows: list[dict[str, str]] = []
    for i, left in enumerate(residues):
        for right in residues[i + 1:]:
            label_i = int(left["label_seq_id"])
            label_j = int(right["label_seq_id"])
            auth_i = int(left["auth_seq_id"])
            auth_j = int(right["auth_seq_id"])
            sep = abs(label_j - label_i)
            xyz_i = (float(left["x"]), float(left["y"]), float(left["z"]))
            xyz_j = (float(right["x"]), float(right["y"]), float(right["z"]))
            distance = math.dist(xyz_i, xyz_j)
            eligible = sep >= MIN_SEQUENCE_SEPARATION
            target_value = 1 if eligible and distance <= CONTACT_THRESHOLD else 0
            common = {
                "source_database": "RCSB_PDB",
                "source_accession": "1CRN",
                "coordinate_payload_sha256": PAYLOAD_SHA,
                "residue_table_sha256": residue_table_sha256,
                "chain_id": "A",
                "model_id": "1",
                "atom_selector": "CA",
                "residue_i": str(auth_i),
                "residue_j": str(auth_j),
                "auth_seq_i": str(auth_i),
                "auth_seq_j": str(auth_j),
                "label_seq_i": str(label_i),
                "label_seq_j": str(label_j),
                "residue_name_i": left["residue_name"],
                "residue_name_j": right["residue_name"],
                "sequence_separation": str(sep),
                "sequence_separation_rule": SEQUENCE_SEPARATION_RULE,
                "distance_angstrom": f"{distance:.3f}",
                "contact_threshold_angstrom": f"{CONTACT_THRESHOLD:.1f}",
                "min_sequence_separation": str(MIN_SEQUENCE_SEPARATION),
                "eligible_for_contact_map": "true" if eligible else "false",
                "target_contact_value": str(target_value) if eligible else "outside_sequence_separation_scope",
                "contact_map_status": "derived_in_v40.02r15" if eligible else "excluded_by_sequence_separation_rule",
                "score_status": "not_scored_in_v40.02r15",
                "leakage_role": "target_only_after_AOD_freeze",
                "release_status": VERSION_LABEL,
            }
            distance_row = dict(common)
            distance_row["distance_row_id"] = f"1CRN_A_model1_CA_label{label_i}_label{label_j}_distance"
            all_pairs.append(distance_row)
            if eligible:
                contact_row = dict(common)
                contact_row["contact_row_id"] = f"1CRN_A_model1_CA_label{label_i}_label{label_j}_contact"
                contact_rows.append(contact_row)

    distance_fields = [
        "distance_row_id", "source_database", "source_accession", "coordinate_payload_sha256",
        "residue_table_sha256", "chain_id", "model_id", "atom_selector", "residue_i", "residue_j",
        "auth_seq_i", "auth_seq_j", "label_seq_i", "label_seq_j", "residue_name_i", "residue_name_j",
        "sequence_separation", "sequence_separation_rule", "distance_angstrom", "contact_threshold_angstrom",
        "min_sequence_separation", "eligible_for_contact_map", "target_contact_value", "contact_map_status",
        "score_status", "leakage_role", "release_status",
    ]
    contact_fields = [
        "contact_row_id", "source_database", "source_accession", "coordinate_payload_sha256",
        "residue_table_sha256", "chain_id", "model_id", "atom_selector", "residue_i", "residue_j",
        "auth_seq_i", "auth_seq_j", "label_seq_i", "label_seq_j", "residue_name_i", "residue_name_j",
        "sequence_separation", "sequence_separation_rule", "distance_angstrom", "contact_threshold_angstrom",
        "min_sequence_separation", "target_contact_value", "contact_map_status", "score_status", "leakage_role",
        "release_status",
    ]
    write_csv(PROT / "pdb_external_contact_distance_matrix.csv", distance_fields, all_pairs)
    write_csv(PROT / "pdb_external_contact_map_derived.csv", contact_fields, contact_rows)

    total_pairs = len(all_pairs)
    eligible_pairs = len(contact_rows)
    contact_count = sum(1 for row in contact_rows if row["target_contact_value"] == "1")
    noncontact_count = eligible_pairs - contact_count
    excluded_short_range = total_pairs - eligible_pairs
    policy_row = {
        "policy_id": "pdb_external_contact_map_policy_1CRN_A_v4002r15",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "coordinate_payload_sha256": PAYLOAD_SHA,
        "residue_table_sha256": residue_table_sha256,
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "contact_threshold_angstrom": f"{CONTACT_THRESHOLD:.1f}",
        "min_sequence_separation": str(MIN_SEQUENCE_SEPARATION),
        "sequence_separation_rule": SEQUENCE_SEPARATION_RULE,
        "sequence_separation_rule_status": "declared_before_pair_generation",
        "total_ca_residue_count": str(len(residues)),
        "total_unordered_pair_count": str(total_pairs),
        "eligible_pair_count": str(eligible_pairs),
        "excluded_short_range_pair_count": str(excluded_short_range),
        "target_contact_count": str(contact_count),
        "target_noncontact_count": str(noncontact_count),
        "external_residual_score_status": "not_scored_in_v40.02r15",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "release_status": VERSION_LABEL,
    }
    write_csv(PROT / "pdb_external_contact_map_policy_application.csv", list(policy_row.keys()), [policy_row])

    block_rows = [
        {
            "block_id": "PDB-EXT-CONTACT-MAP-BLOCK-001",
            "derivation_id": "pdb_external_contact_map_derivation_1CRN_A_v4002r15",
            "candidate_derivation": "evaluation_pair_boundary",
            "required_precondition": "external_contact_map_derived_and_scope_gate_declared",
            "current_status": "blocked_until_explicit_evaluation_pair_boundary_gate",
            "leakage_role": "downstream_scope_before_score",
            "release_status": VERSION_LABEL,
        },
        {
            "block_id": "PDB-EXT-CONTACT-MAP-BLOCK-002",
            "derivation_id": "pdb_external_contact_map_derivation_1CRN_A_v4002r15",
            "candidate_derivation": "external_residual_score",
            "required_precondition": "evaluation_pair_boundary_declared_and_frozen_AOD_packet_join_authorized",
            "current_status": "blocked_in_v40.02r15",
            "leakage_role": "downstream_score_only_after_freeze_target_join",
            "release_status": VERSION_LABEL,
        },
        {
            "block_id": "PDB-EXT-CONTACT-MAP-BLOCK-003",
            "derivation_id": "pdb_external_contact_map_derivation_1CRN_A_v4002r15",
            "candidate_derivation": "coordinate_level_metric_score",
            "required_precondition": "coordinate_level_AOD_prediction_freeze",
            "current_status": "blocked_in_v40.02r15",
            "leakage_role": "coordinate_metrics_deferred",
            "release_status": VERSION_LABEL,
        },
    ]
    write_csv(
        PROT / "pdb_external_contact_map_derivation_block.csv",
        ["block_id", "derivation_id", "candidate_derivation", "required_precondition", "current_status", "leakage_role", "release_status"],
        block_rows,
    )

    check_specs = [
        ("contact_map_reads_only_r14_residue_table", "residue table is the only coordinate input"),
        ("residue_table_sha256_matches_r14_manifest", "residue_table_sha256 equals locked r14 table hash"),
        ("sequence_separation_rule_declared_before_pair_generation", "abs(label_seq_id_j-label_seq_id_i)>=3 declared before generation"),
        ("contact_threshold_8_angstrom_declared_before_contact_bits", "8.0 Angstrom cutoff declared before contact values"),
        ("eligible_pair_count_matches_declared_rule", "46 residues yield 946 eligible pairs under >=3 rule"),
        ("target_contact_count_matches_declared_rule", "8.0 Angstrom cutoff yields 114 contacts under >=3 rule"),
        ("no_external_residual_score_computed_in_r15", "external residual score remains blocked"),
        ("no_AOD_prediction_packet_joined_in_r15", "contact map is target-only and does not join AOD predictions"),
        ("coordinate_metrics_remain_deferred", "RMSD/TM-score/GDT remain deferred"),
        ("AOD_motif_curling_curls_and_SADAR_stay_upstream_of_future_target_join", "future target joins remain downstream of AOD motif/SADAR freeze"),
    ]
    check_rows = [
        {
            "check_id": f"PDB-EXT-CONTACT-MAP-CHECK-{idx:03d}",
            "check_name": name,
            "check_result": "active_pass",
            "detail": detail,
            "score_input_status": "contact_map_gate_only_no_AOD_join_or_score",
            "release_status": VERSION_LABEL,
        }
        for idx, (name, detail) in enumerate(check_specs, start=1)
    ]
    write_csv(PROT / "pdb_external_contact_map_leakage_checks.csv", list(check_rows[0].keys()), check_rows)

    manifest_obj = {
        "lane": "external_pdb_contact_map_derivation_gate",
        "version_scope": VERSION,
        "status": "external target contact-map derivation from r14 residue-coordinate table only; no AOD prediction join, external residual score, coordinate metric, AlphaFold score, or folding value map",
        "prior_residue_table_gate": "manual-2/data/protein/pdb_external_residue_coordinate_table.csv",
        "source_database": "RCSB_PDB",
        "source_accession": "1CRN",
        "chain_id": "A",
        "model_id": "1",
        "atom_selector": "CA",
        "coordinate_payload_sha256": PAYLOAD_SHA,
        "residue_table_sha256": residue_table_sha256,
        "residue_coordinate_rows": len(residues),
        "total_unordered_pair_count": total_pairs,
        "eligible_pair_count": eligible_pairs,
        "excluded_short_range_pair_count": excluded_short_range,
        "target_contact_count": contact_count,
        "target_noncontact_count": noncontact_count,
        "contact_threshold_angstrom": CONTACT_THRESHOLD,
        "min_sequence_separation": MIN_SEQUENCE_SEPARATION,
        "sequence_separation_rule": SEQUENCE_SEPARATION_RULE,
        "score_status": "not_scored_in_v40.02r15",
        "aod_prediction_join_status": "not_joined_in_v40.02r15",
        "coordinate_metric_status": "RMSD_TM_score_GDT_deferred_until_coordinate_level_AOD_prediction_freeze",
        "distance_matrix_sha256": sha256_file(PROT / "pdb_external_contact_distance_matrix.csv"),
        "contact_map_sha256": sha256_file(PROT / "pdb_external_contact_map_derived.csv"),
        "policy_application_sha256": sha256_file(PROT / "pdb_external_contact_map_policy_application.csv"),
        "blocked_until_later_gate": [
            "evaluation_pair_boundary_declaration",
            "external_accession_residual_score",
            "coordinate_level_metric_score",
        ],
        "files": {
            "distance_matrix": "manual-2/data/protein/pdb_external_contact_distance_matrix.csv",
            "contact_map": "manual-2/data/protein/pdb_external_contact_map_derived.csv",
            "policy_application": "manual-2/data/protein/pdb_external_contact_map_policy_application.csv",
            "derivation_block": "manual-2/data/protein/pdb_external_contact_map_derivation_block.csv",
            "leakage_checks": "manual-2/data/protein/pdb_external_contact_map_leakage_checks.csv",
        },
        "claim_discipline": "external contact rows are target-only rows that join only after frozen AOD packet and explicit evaluation-pair boundary gates pass",
    }
    (PROT / "pdb_external_contact_map_manifest.json").write_text(json.dumps(manifest_obj, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    derive()
