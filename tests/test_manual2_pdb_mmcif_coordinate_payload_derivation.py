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


def test_v4002r07_coordinate_payload_files_exist_and_are_manifested():
    required = [
        "pdb_mmcif_coordinate_payload_registry.csv",
        "pdb_mmcif_atom_site_extract.csv",
        "pdb_mmcif_residue_coordinate_table.csv",
        "pdb_mmcif_contact_map_derived.csv",
        "pdb_mmcif_distance_matrix_derived.csv",
        "pdb_mmcif_contact_derivation_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    payload = PROT / "pdb_mmcif_payloads" / "manual_seed_GAS_pdbx_mmcif_payload_fixture.cif"
    assert payload.exists()
    manifest = json.loads((PROT / "pdb_mmcif_contact_derivation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r07"
    assert "target_coordinate_payload_ingest" in manifest["status"]
    assert "no_aod_vs_pdb_score" in manifest["status"]
    for rel in manifest["files"].values():
        if rel.endswith("/"):
            assert (ROOT / rel).is_dir(), rel
        else:
            assert (ROOT / rel).exists(), rel


def test_coordinate_payload_registry_is_target_only_and_not_scored():
    rows = read_csv(PROT / "pdb_mmcif_coordinate_payload_registry.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["payload_id"] == "manual_seed_GAS_pdbx_mmcif_payload_fixture"
    assert row["protein_id"] == "manual_seed_GAS"
    assert row["payload_sha256"]
    assert row["coordinate_payload_status"] == "committed_fixture_payload_not_external_pdb_validation"
    assert row["derived_contact_pairs"] == "1-3"
    assert row["derived_contact_count"] == "1"
    assert row["leakage_role"] == "target_only"
    assert row["prediction_premise_status"] == "forbidden_as_prediction_premise"
    assert row["score_status"] == "not_scored_in_v40.02r07"


def test_atom_site_and_residue_coordinate_extract_are_payload_only():
    atoms = read_csv(PROT / "pdb_mmcif_atom_site_extract.csv")
    residues = read_csv(PROT / "pdb_mmcif_residue_coordinate_table.csv")
    assert len(atoms) == 12
    assert len(residues) == 3
    assert {r["atom_name"] for r in atoms} >= {"N", "CA", "C", "CB"}
    assert {r["residue_name"] for r in residues} == {"GLY", "ALA", "SER"}
    gly = next(r for r in residues if r["residue_name"] == "GLY")
    assert gly["ca_coordinate_status"] == "present"
    assert gly["cb_coordinate_status"] == "missing_glycine_or_absent"
    assert {r["leakage_role"] for r in atoms + residues} == {"target_only"}
    assert {r["score_status"] for r in atoms + residues} == {"not_scored_in_v40.02r07"}


def test_contact_map_derivation_outputs_contact_rows_but_no_scores():
    contacts = read_csv(PROT / "pdb_mmcif_contact_map_derived.csv")
    distances = read_csv(PROT / "pdb_mmcif_distance_matrix_derived.csv")
    assert len(contacts) == 3
    assert len(distances) == 3
    pair13 = next(r for r in contacts if (r["residue_i"], r["residue_j"]) == ("1", "3"))
    assert pair13["ca_distance_angstrom"] == "7.6"
    assert pair13["derived_contact"] == "1"
    assert pair13["contact_scope_status"] == "in_scope"
    out_of_scope = [r for r in contacts if r["pair_separation"] == "1"]
    assert out_of_scope and {r["derived_contact"] for r in out_of_scope} == {"0"}
    assert {r["contact_map_hash"] for r in contacts} == {read_csv(PROT / "pdb_mmcif_coordinate_payload_registry.csv")[0]["contact_map_hash"]}
    assert {r["score_status"] for r in contacts + distances} == {"not_scored_in_v40.02r07"}
    header = " ".join(contacts[0].keys()).lower() + " " + " ".join(distances[0].keys()).lower()
    forbidden_score_columns = ["precision", "recall", "f1", "jaccard", "rmsd", "tm_score", "gdt"]
    assert not any(tok in header for tok in forbidden_score_columns)


def test_v4002r07_does_not_change_existing_prediction_or_score_rows():
    score = read_csv(PROT / "protein_contact_score.csv")
    assert len(score) == 1
    row = score[0]
    assert row["score_version"] == "v40.02r06"
    assert row["chain_id"] == "chain_GAS_tripeptide_seed"
    assert row["predicted_pairs"] == row["target_pairs"] == row["evaluation_pairs"] == "1-3"
    assert (row["tp"], row["fp"], row["fn"], row["tn"]) == ("1", "0", "0", "0")
    predictions = read_csv(PROT / "aod_contact_prediction_freeze.csv")
    assert {r["score_status"] for r in predictions} == {"not_scored_in_v40.02r05"}


def test_coordinate_payload_leakage_guards_are_active():
    guards = read_csv(PROT / "protein_target_leakage_guard.csv")
    ids = {r["guard_id"]: r for r in guards}
    assert "LEAK-PDB-PAYLOAD-001" in ids
    assert "LEAK-PDB-PAYLOAD-002" in ids
    assert ids["LEAK-PDB-PAYLOAD-001"]["forbidden_destination"] == "aod_contact_reclosure_prediction_freeze_inputs"
    assert ids["LEAK-PDB-PAYLOAD-002"]["allowed_role"] == "target_derivation_only_not_scored_in_v40.02r07"


def test_coordinate_derivation_generator_is_offline_and_reproducible():
    before = (PROT / "pdb_mmcif_contact_map_derived.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "derive_pdb_mmcif_contact_maps.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "pdb_mmcif_contact_map_derived.csv").read_text(encoding="utf-8")
    assert after == before


def test_roadmap_current_milestone_is_v4002r07_and_no_expanded_score_is_active():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "Scoped PDB Contact-Map Residual Pilot" in roadmap
    assert "v40.02r07 PDBx/mmCIF coordinate-payload derivation rows remain target-only and not scored" in roadmap
    assert "lambda_fold     = deferred_not_attached" in roadmap
