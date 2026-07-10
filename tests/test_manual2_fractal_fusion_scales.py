import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL2 = ROOT / "manual-2"


def read_csv(rel):
    with (ROOT / rel).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def residual_is_zero(text: str) -> bool:
    return all(part.endswith(":0") for part in text.split(";"))


def test_manual2_manual_ii_tree_is_single_compacted_package():
    assert MANUAL2.exists()
    assert (MANUAL2 / "main.tex").exists()
    assert (MANUAL2 / "preamble.tex").exists()
    assert not (ROOT / "manual-3").exists()
    text = (MANUAL2 / "main.tex").read_text(encoding="utf-8")
    assert "Fractal Fusion Scales" in text
    assert "Up the Octaves" in text
    section_text = "\n".join(p.read_text(encoding="utf-8") for p in (MANUAL2 / "sections").glob("*.tex"))
    for phrase in [
        "boundary setup",
        "raw AFC/D.E.C.",
        "trace detection",
        "frozen rows",
        "observable maps",
        "error analysis",
    ]:
        assert phrase in section_text


def test_manual2_manifest_names_octave_lanes_and_protocol_order():
    manifest = json.loads((MANUAL2 / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["title"] == "Fractal Fusion Scales"
    assert manifest["subtitle"] == "Up the Octaves"
    assert set(manifest["lanes"]) == {"elementary", "molecular", "bio_chain", "protein", "dec_pen_paper", "ontology_to_dec_occurrence_overlay", "temporal"}
    protocol = manifest["protocol"]
    assert protocol.index("setup declared boundary/window/octave") < protocol.index("run raw AFC/D.E.C. substrate")
    assert protocol.index("trace-detect retained events") < protocol.index("freeze exact ladder rows or target packets")
    assert protocol.index("map to observables only after freeze") < protocol.index("report residuals and error ledger")


def test_element_registry_has_frozen_118_rows():
    rows = read_csv("manual-2/data/elementary/element_registry_118.csv")
    assert len(rows) == 118
    assert [int(r["Z"]) for r in rows] == list(range(1, 119))
    assert rows[0]["symbol"] == "H"
    assert rows[0]["name"] == "Hydrogen"
    assert rows[-1]["symbol"] == "Og"
    assert rows[-1]["name"] == "Oganesson"
    assert all(r["registry_status"] == "frozen_118_name_symbol_fixture" for r in rows)


def test_336_and_346_ladders_have_deterministic_retained_capacity_residuals():
    for rel, ratio, surplus_step in [
        ("manual-2/data/elementary/fusion_ladder_336.csv", "3:3:6", 0),
        ("manual-2/data/elementary/fusion_ladder_346.csv", "3:4:6", 1),
    ]:
        rows = read_csv(rel)
        assert len(rows) == 118
        for row in rows:
            z = int(row["element_Z"])
            depth = (z + 5) // 6
            assert row["declared_ratio"] == ratio
            assert int(row["ladder_depth"]) == depth
            assert int(row["retained_capacity_Z"]) == depth * 6
            assert int(row["residual_Z"]) == depth * 6 - z
            assert int(row["sheddic_surplus"]) == depth * surplus_step
            expected = "closed" if depth * 6 == z else "boundary_residual"
            assert row["admissibility_status"] == expected


def test_pubchem_and_stellar_lanes_are_comparison_lanes_only():
    pubchem = read_csv("manual-2/data/elementary/pubchem_element_map.csv")
    stellar = read_csv("manual-2/data/elementary/stellar_scaled_comparison.csv")
    assert len(pubchem) == 118
    assert len(stellar) == 118
    assert all(r["comparison_status"] == "lookup_fixture_no_network_fetch" for r in pubchem)
    assert all(r["map_status"] == "comparison_lane_not_core_calculus" for r in stellar)
    assert {r["residual_class"] for r in stellar} >= {"zero", "capacity_minus_Z"}


def test_molecular_formula_residual_rows_close_exactly():
    residuals = read_csv("manual-2/data/molecular/formula_residuals.csv")
    assert residuals
    for row in residuals:
        assert row["sum_abs_residual_CHONPS"] == "0"
        assert residual_is_zero(row["residual_CHONPS"])


def test_bio_chain_nucleotide_and_peptide_rows_close_exactly():
    for rel in [
        "manual-2/data/bio_chain/nucleotide_candidates.csv",
        "manual-2/data/bio_chain/dinucleotide_candidates.csv",
        "manual-2/data/bio_chain/rna_dna_chain_closures.csv",
        "manual-2/data/bio_chain/peptide_candidates.csv",
        "manual-2/data/bio_chain/protein_chain_candidates.csv",
    ]:
        rows = read_csv(rel)
        assert rows, rel
        for row in rows:
            assert residual_is_zero(row["residual_CHONPS"]), (rel, row)
            if "status" in row:
                assert row["status"] == "closed"


def test_rdkit_lane_is_downstream_and_optional():
    rows = read_csv("manual-2/data/bio_chain/rdkit_graph_descriptors.csv")
    assert rows
    statuses = {r["rdkit_status"] for r in rows}
    assert statuses <= {"computed_optional_graph_lane", "parse_failed", "rdkit_unavailable_offline_fixture"}
    assert "molecule_id" in rows[0]
    assert "canonical_smiles" in rows[0]
