import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"
MOL = ROOT / "manual-2" / "data" / "molecular"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_aod_prediction_freeze_files_exist_and_are_manifested():
    required = [
        "aod_folding_prediction_model_registry.csv",
        "aod_contact_prediction_freeze.csv",
        "aod_reclosure_motif_predictions.csv",
        "aod_prediction_freeze_manifest.json",
    ]
    for name in required:
        assert (PROT / name).exists(), name
    manifest = json.loads((PROT / "aod_prediction_freeze_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r05"
    assert manifest["status"] == "prediction_freeze_no_target_comparison_no_contact_score"
    for key, rel in manifest["files"].items():
        assert (ROOT / rel).exists(), key
    assert manifest["next_milestone"] == "v40.02r06 -- Protein Contact-Map Residual / Folding Target Comparison"


def test_model_registry_allows_only_internal_chain_dec_inputs():
    rows = read_csv(PROT / "aod_folding_prediction_model_registry.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["version_scope"] == "v40.02r05"
    assert row["input_contract"] == "ChainWordSpec+ReadOnlyTrace+DetectedChainMotif+SADARContext"
    allowed = row["allowed_input_files"].split(";")
    assert allowed == [
        "manual-2/data/molecular/chain_word_spec.csv",
        "manual-2/data/molecular/read_only_trace_molecular_chain.csv",
        "manual-2/data/molecular/detected_chain_motifs.csv",
        "manual-2/data/molecular/sadar_detector_context.csv",
    ]
    assert all((ROOT / rel).exists() for rel in allowed)
    assert row["geometry_status"] == "not_full_3d_geometry_prediction"
    assert row["contact_score_status"] == "not_scored_in_v40.02r05"
    assert row["comparison_status"] == "not_compared_in_v40.02r05"
    assert row["freeze_status"] == "frozen_before_external_comparison"


def test_contact_prediction_freeze_has_expected_pairs_and_no_scores():
    rows = read_csv(PROT / "aod_contact_prediction_freeze.csv")
    assert rows
    pairs = {(r["chain_id"], r["residue_i"], r["residue_j"], r["pair_class"]) for r in rows}
    assert ("chain_GA_peptide_seed", "1", "2", "adjacent_route_support") in pairs
    assert ("chain_GAS_tripeptide_seed", "1", "3", "multi_link_reclosure_span") in pairs
    assert {r["comparison_input_used"] for r in rows} == {"false"}
    assert {r["leak_check_status"] for r in rows} == {"passed_no_external_comparison_input"}
    assert {r["score_status"] for r in rows} == {"not_scored_in_v40.02r05"}
    assert {r["predicted_contact"] for r in rows} == {"1"}


def test_prediction_packets_have_no_external_target_leakage_tokens():
    forbidden = [
        "pdb", "alphafold", "uniprot", "pubchem", "rdkit",
        "target_contact", "target_distance", "distance_matrix_payload",
        "secondary_structure", "confidence", "plddt", "pae", "rmsd",
        "tm_score", "gdt", "precision", "recall", "jaccard",
    ]
    for name in ["aod_contact_prediction_freeze.csv", "aod_reclosure_motif_predictions.csv"]:
        text = (PROT / name).read_text(encoding="utf-8").lower()
        assert not any(tok in text for tok in forbidden), name


def test_reclosure_predictions_point_to_detected_motifs_and_sadar_contexts():
    rows = read_csv(PROT / "aod_reclosure_motif_predictions.csv")
    motifs = {r["motif_id"] for r in read_csv(MOL / "detected_chain_motifs.csv")}
    contexts = {r["sadar_context_id"] for r in read_csv(MOL / "sadar_detector_context.csv")}
    assert rows
    assert all(r["motif_id"] in motifs for r in rows)
    assert all(r["sadar_context_id"] in contexts for r in rows)
    assert {r["scalar_status"] for r in rows} == {"sadar_context_not_scalar_evaluated"}
    assert {r["score_status"] for r in rows} == {"not_scored_in_v40.02r05"}
    gas = next(r for r in rows if r["chain_id"] == "chain_GAS_tripeptide_seed")
    assert gas["predicted_reclosure_pairs"] == "1-2;2-3;1-3"


def test_target_leakage_guard_is_active_for_prediction_freeze():
    rows = read_csv(PROT / "protein_target_leakage_guard.csv")
    ids = {r["guard_id"] for r in rows}
    assert "LEAK-PRED-FREEZE-001" in ids
    assert "LEAK-PRED-FREEZE-002" in ids
    assert "LEAK-PRED-FREEZE-003" in ids
    assert all(r["guard_status"].startswith("active") for r in rows)
    assert any(r["forbidden_destination"] == "aod_contact_reclosure_prediction_freeze" for r in rows)


def test_prediction_freeze_does_not_activate_lambdas_or_scores():
    lambdas = read_csv(PROT / "protein_value_map_quarantine.csv")
    assert all(r["status"] == "deferred_not_attached" for r in lambdas)
    assert all(r["active_value_map"] == "false" for r in lambdas)
    assert all(r["status"] == "deferred_not_attached" for r in lambdas)
    assert all("v40.02r11" in r["release_status"] for r in lambdas)
    manifest = json.loads((PROT / "protein_target_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r16"
    assert "aod_prediction_freeze" in manifest["status"]
    assert "contact_residual_comparison" in manifest["status"]
    assert "aod_contact_prediction_freeze" in manifest["files"]


def test_prediction_freeze_generator_is_offline_and_reproducible():
    before = (PROT / "aod_contact_prediction_freeze.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "freeze_aod_contact_reclosure_predictions.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (PROT / "aod_contact_prediction_freeze.csv").read_text(encoding="utf-8")
    assert after == before


def test_roadmap_current_milestone_is_v4002r08_and_freeze_is_carried_forward():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "Scoped PDB Contact-Map Residual Pilot" in roadmap
    assert "v40.02r05 AOD contact/reclosure prediction packets" in roadmap
    assert "lambda_fold     = deferred_not_attached" in roadmap
