import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M2 = ROOT / "manual-2"
MOL = M2 / "data" / "molecular"
PROT = M2 / "data" / "protein"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_molecular_target_scaffold_files_exist_and_are_manifested():
    manifest = json.loads((MOL / "molecular_target_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r05"
    assert "chain_dec_fixture" in manifest["status"]
    assert "no_external_score" in manifest["status"]
    for rel in manifest["files"].values():
        assert (ROOT / rel).exists(), rel


def test_component_vectors_are_explicit_chnops_columns():
    rows = read_csv(MOL / "component_vector_registry.csv")
    assert rows
    expected_cols = ["n_C", "n_H", "n_N", "n_O", "n_P", "n_S"]
    for col in expected_cols:
        assert col in rows[0]
    water = next(r for r in rows if r["component_id"] == "water")
    assert [int(water[c]) for c in expected_cols] == [0, 2, 0, 1, 0, 0]
    methane = next(r for r in rows if r["component_id"] == "methane")
    assert [int(methane[c]) for c in expected_cols] == [1, 4, 0, 0, 0, 0]


def test_route_and_control_units_are_declared_not_scored():
    route = read_csv(MOL / "route_unit_registry.csv")
    control = read_csv(MOL / "control_unit_registry.csv")
    links = read_csv(MOL / "link_rule_registry.csv")
    assert route[0]["route_unit_id"] == "water_equivalent_route_unit"
    assert route[0]["route_formula"] == "H2O"
    assert [int(route[0][c]) for c in ["n_C", "n_H", "n_N", "n_O", "n_P", "n_S"]] == [0, 2, 0, 1, 0, 0]
    assert control[0]["control_unit_id"] == "methane_carbon_saturation_control"
    assert control[0]["route_status"] == "not_a_default_chain_route"
    assert any(r["detector_status"] == "detector_active_in_v40.02r03" for r in links)
    assert not any("scored" in r["admissibility_status"] for r in links)


def test_target_packets_have_provenance_checksums_and_leakage_roles():
    packet_files = [
        MOL / "pubchem_compound_target_packets.csv",
        PROT / "uniprot_target_packets.csv",
        PROT / "pdb_structure_target_packets.csv",
        PROT / "alphafold_structure_target_packets.csv",
    ]
    required = {
        "target_packet_id", "lane", "source", "source_accession",
        "source_release_or_snapshot", "source_record_url_or_path",
        "acquisition_utc", "raw_sha256", "normalized_sha256",
        "normalizer_script", "normalizer_version", "license_or_terms_ref",
        "target_status", "leakage_role", "release_status",
    }
    for path in packet_files:
        rows = read_csv(path)
        assert rows, path
        assert required <= set(rows[0]), path
        ids = [r["target_packet_id"] for r in rows]
        assert len(ids) == len(set(ids))
        assert {r["leakage_role"] for r in rows} <= {"target_only", "comparison_only", "allowed_input"}
        assert all(r["raw_sha256"] and r["normalized_sha256"] for r in rows)


def test_protein_lane_is_target_scaffold_only_with_deferred_lambdas():
    manifest = json.loads((PROT / "protein_target_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r16"
    assert "normalization" in manifest["status"]
    assert "aod_prediction_freeze" in manifest["status"]
    assert "contact_residual_comparison" in manifest["status"]
    guards = read_csv(PROT / "protein_target_leakage_guard.csv")
    assert guards and all(g["guard_status"].startswith("active") for g in guards)
    lambdas = read_csv(PROT / "protein_value_map_quarantine.csv")
    assert {r["lambda_id"] for r in lambdas} == {
        "lambda_molecule", "lambda_formula", "lambda_graph",
        "lambda_chain", "lambda_fold", "lambda_bio",
    }
    assert all(r["status"] == "deferred_not_attached" for r in lambdas)
    assert all(r["active_value_map"] == "false" for r in lambdas)


def test_raw_dec_headers_do_not_contain_target_or_folding_tokens():
    forbidden = ["pubchem", "rdkit", "uniprot", "pdb", "alphafold", "rna", "dna", "protein", "fold"]
    for path in (M2 / "data").rglob("raw_dec_trace*.csv"):
        header = read_csv(path)[0].keys() if read_csv(path) else []
        joined = " ".join(header).lower()
        assert not any(tok in joined for tok in forbidden), path


def test_roadmap_is_bundled_source_file_for_current_milestone():
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "v40.02r05 AOD contact/reclosure prediction packets" in roadmap
    assert "v40.02r06 contact-map residual rows remain" in roadmap
    assert "lambda_fold     = deferred_not_attached" in roadmap
