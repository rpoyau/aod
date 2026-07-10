import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOL = ROOT / "manual-2" / "data" / "molecular"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_molecular_chain_dec_files_exist_and_are_manifested():
    required = [
        "chain_word_spec.csv",
        "raw_dec_trace_molecular_chain.csv",
        "read_only_trace_molecular_chain.csv",
        "detected_chain_motifs.csv",
        "sadar_detector_context.csv",
        "chain_formula_predictions.csv",
        "chain_fission_audit.csv",
        "molecular_chain_delta3_audit.csv",
    ]
    for name in required:
        assert (MOL / name).exists(), name
    manifest = json.loads((MOL / "molecular_target_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r05"
    assert "chain_dec_fixture" in manifest["status"]
    for name in required:
        key = name.removesuffix(".csv")
        assert key in manifest["files"], key
        assert (ROOT / manifest["files"][key]).exists()


def test_chain_formula_predictions_close_exactly():
    rows = read_csv(MOL / "chain_formula_predictions.csv")
    assert len(rows) >= 5
    expected = {
        "chain_GA_peptide_seed": "C5H10N2O3",
        "chain_AMP_nucleotide_seed": "C10H14N5O7P",
        "chain_UMP_nucleotide_seed": "C9H13N2O9P",
        "chain_AU_dinucleotide_seed": "C19H25N7O15P2",
        "chain_GAS_tripeptide_seed": "C8H15N3O5",
    }
    by_id = {r["chain_id"]: r for r in rows}
    assert all(by_id[k]["frozen_formula"] == v for k, v in expected.items())
    for row in rows:
        assert row["frozen_formula"] == row["declared_check_formula"]
        assert row["formula_status"] == "closed_formula_freeze"
        assert row["sum_abs_Delta_CHNOPS"] == "0"
        for coord in ["C", "H", "N", "O", "P", "S"]:
            assert row[f"Delta_{coord}"] == "0"
        assert all(part.endswith(":0") for part in row["delta3_formula"].split(";"))


def test_raw_dec_chain_rows_have_neutral_headers_only():
    rows = read_csv(MOL / "raw_dec_trace_molecular_chain.csv")
    assert rows
    assert list(rows[0].keys()) == ["tick", "B", "v", "e", "v_e", "sigma_e", "adm_e_B", "w_e_B", "P_e_B", "route_e_B"]
    forbidden = [
        "pubchem", "rdkit", "uniprot", "pdb", "alphafold",
        "rna", "dna", "protein", "fold", "target", "score",
    ]
    header_text = " ".join(rows[0].keys()).lower()
    value_text = " ".join(" ".join(r.values()) for r in rows).lower()
    assert not any(tok in header_text for tok in forbidden)
    assert not any(tok in value_text for tok in forbidden)
    assert {r["route_e_B"] for r in rows} == {"water_equivalent_route_unit"}


def test_trace_detector_sadar_sequence_is_separated():
    traces = read_csv(MOL / "read_only_trace_molecular_chain.csv")
    motifs = read_csv(MOL / "detected_chain_motifs.csv")
    contexts = read_csv(MOL / "sadar_detector_context.csv")
    trace_ids = {r["trace_id"] for r in traces}
    assert trace_ids
    assert all(r["trace_id"] in trace_ids for r in motifs)
    assert {r["sadar_scalar_status"] for r in contexts} == {"detector_context_not_scalar_evaluated"}
    assert all(r["scalar_value"] == "" for r in contexts)
    assert {r["detector_status"] for r in motifs} == {"detected_after_raw_trace"}


def test_chain_fission_audits_recover_water_route_exactly():
    rows = read_csv(MOL / "chain_fission_audit.csv")
    assert rows
    assert {r["recovered_route_unit"] for r in rows} == {"H2O"}
    assert {r["audit_status"] for r in rows} == {"passed_exact_route_recovery"}
    for row in rows:
        assert row["sum_abs_Delta_CHNOPS"] == "0"
        assert row["delta3_status"] == "zero_residual"
        for coord in ["C", "H", "N", "O", "P", "S"]:
            assert row[f"Delta_{coord}"] == "0"


def test_molecular_chain_delta3_audit_is_zero_for_committed_rows():
    rows = read_csv(MOL / "molecular_chain_delta3_audit.csv")
    assert rows
    assert {r["delta3_status"] for r in rows} == {"zero_residual"}
    assert {r["audit_status"] for r in rows} == {"passed"}
    assert {r["Delta_Z"] for r in rows} == {"0"}
    assert {r["delta3_residue"] for r in rows} == {"0"}


def test_chain_dec_generator_is_offline_and_reproducible():
    before = (MOL / "chain_formula_predictions.csv").read_text(encoding="utf-8")
    script = ROOT / "manual-2" / "scripts" / "run_molecular_chain_fusion_dec.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    after = (MOL / "chain_formula_predictions.csv").read_text(encoding="utf-8")
    assert after == before


def test_roadmap_current_milestone_is_v4002r08_and_chain_dec_is_carried_forward():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Manual-II baseline milestone: v40.03r01" in roadmap
    assert "Molecular chain-D.E.C. rows from v40.02r03 are carried forward unchanged" in roadmap
    assert "source.zip contains the v40.03r01 carried baseline plus the active r08.1 authoring overlay" in roadmap
