import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_protein_folding_target_normalization_files_exist_and_are_manifested():
    required = [
        "protein_sequence_target_packets.csv",
        "pdb_mmcif_structure_targets.csv",
        "alphafold_structure_targets.csv",
        "protein_contact_map_targets.csv",
        "protein_distance_matrix_targets.csv",
        "protein_structure_target_limitations.csv",
        "protein_folding_target_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "protein_folding_target_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r04"
    assert "target_normalization_gate" in manifest["status"]
    assert "no_aod_prediction" in manifest["status"]
    for key, rel in manifest["files"].items():
        assert (ROOT / rel).exists(), key


def test_sequence_target_packets_have_hashes_and_leakage_roles():
    rows = read_csv(PROT / "protein_sequence_target_packets.csv")
    assert rows
    required = {
        "protein_id", "target_packet_id", "source", "source_accession",
        "sequence", "sequence_sha256", "residue_count", "sequence_status",
        "normalization_status", "leakage_role", "target_status", "release_status",
    }
    assert required <= set(rows[0])
    by_id = {r["protein_id"]: r for r in rows}
    assert by_id["manual_seed_GAS"]["sequence"] == "GAS"
    assert by_id["manual_seed_GAS"]["leakage_role"] == "allowed_input"
    assert by_id["uniprot_P69905_locator"]["leakage_role"] == "target_only"
    assert all(r["sequence_sha256"] for r in rows)


def test_pdb_and_alphafold_targets_are_locator_or_comparator_rows_not_premises():
    pdb = read_csv(PROT / "pdb_mmcif_structure_targets.csv")
    af = read_csv(PROT / "alphafold_structure_targets.csv")
    assert pdb and af
    assert {r["source"] for r in pdb} == {"RCSB_PDB"}
    assert {r["source"] for r in af} == {"AlphaFold_DB"}
    assert {r["leakage_role"] for r in pdb + af} == {"target_only"}
    assert all(r["ca_coordinate_status"] == "locator_only_no_coordinate_payload" for r in pdb + af)
    assert all(r["contact_map_hash"] and r["distance_matrix_hash"] for r in pdb + af)
    assert {r["target_limitation_class"] for r in af} == {"predicted_structure_comparator_not_ground_truth"}
    assert all(r["normalization_status"] != "aod_prediction" for r in pdb + af)


def test_contact_and_distance_targets_are_targets_not_scores():
    contacts = read_csv(PROT / "protein_contact_map_targets.csv")
    distances = read_csv(PROT / "protein_distance_matrix_targets.csv")
    assert contacts and distances
    contact_ids = {r["protein_id"] for r in contacts}
    distance_ids = {r["protein_id"] for r in distances}
    assert contact_ids == distance_ids
    assert "manual_seed_GAS" in contact_ids
    assert any(r["contact_map_status"] == "normalized_manual_fixture_contact_map" for r in contacts)
    assert any(r["contact_map_status"] == "predicted_structure_locator_only_no_coordinate_payload" for r in contacts)
    assert all(r["contact_threshold_angstrom"] == "8.0" for r in contacts)
    assert all(r["contact_map_hash"] for r in contacts)
    assert all(r["distance_matrix_hash"] for r in distances)
    score_tokens = ["precision", "recall", "f1", "jaccard", "rmsd", "tm_score", "gdt"]
    header_text = " ".join(contacts[0].keys()).lower() + " " + " ".join(distances[0].keys()).lower()
    assert not any(tok in header_text for tok in score_tokens)


def test_structure_limitations_forbid_target_leakage_and_scores():
    rows = read_csv(PROT / "protein_structure_target_limitations.csv")
    assert rows
    classes = {r["limitation_class"] for r in rows}
    assert "forbidden_as_prediction_premise" in classes
    assert "predicted_structure_comparator_not_ground_truth" in classes
    assert all(r["release_status"] == "v40.02r04_target_normalization_carried_forward" for r in rows)
    assert any("comparison_only_after_v40.02r05_prediction_freeze" in r["score_permission"] for r in rows)


def test_protein_target_manifest_promotes_current_gate_without_active_lambdas():
    manifest = json.loads((PROT / "protein_target_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r16"
    assert "folding_target_normalization" in manifest["status"]
    assert "contact_residual_comparison" in manifest["status"]
    assert "protein_contact_map_targets" in manifest["files"]
    lambdas = read_csv(PROT / "protein_value_map_quarantine.csv")
    assert all(r["status"] == "deferred_not_attached" for r in lambdas)
    assert all(r["active_value_map"] == "false" for r in lambdas)
    assert any(r["lambda_id"] == "lambda_fold" for r in lambdas)


def test_normalization_generator_is_offline_and_reproducible():
    before = (PROT / "protein_contact_map_targets.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "normalize_protein_folding_targets.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "protein_contact_map_targets.csv").read_text(encoding="utf-8")
    assert after == before


def test_roadmap_current_milestone_is_v4002r08_and_target_gate_is_carried_forward():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "Scoped PDB Contact-Map Residual Pilot" in roadmap
    assert "Protein target-normalization rows from v40.02r04" in roadmap
    assert "source.zip contains the v40.03r01 carried baseline plus the active r08.1 authoring overlay" in roadmap
