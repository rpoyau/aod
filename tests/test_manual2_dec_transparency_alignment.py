
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "manual-2" / "sections"
DEC = ROOT / "manual-2" / "data" / "dec"
MOL = ROOT / "manual-2" / "data" / "molecular"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_dec_shared_opening_is_structural_and_worked_applications_follow():
    main = read(ROOT / "manual-2" / "main.tex")
    assert "sections/00_scope.tex" in main
    assert "sections/00_dec_ledger.tex" in main
    assert main.index("sections/00_scope.tex") < main.index("sections/00_dec_ledger.tex")
    assert main.index("sections/00_dec_ledger.tex") < main.index("sections/03_gas_dec_trace_application.tex")
    assert main.index("sections/03_gas_dec_trace_application.tex") < main.index("sections/03_molecular_chain_worked_example.tex")
    section = read(ROOT / "shared" / "manual_intro_dec_ledger.tex")
    assert "Pen-and-Paper AFC Raw Execution and D.E.C. Ledger for Fusion Scales" in section
    assert "AFC runs raw" in section
    assert "The trace records the run" in section
    assert "D.E.C. is the manual ledger format for finite AFC edge execution" in section


def test_dec_row_schema_matches_raw_dec_trace_columns():
    raw_header = (MOL / "raw_dec_trace_molecular_chain.csv").read_text(encoding="utf-8").splitlines()[0].split(",")
    assert raw_header == [
        "tick", "B", "v", "e", "v_e", "sigma_e", "adm_e_B", "w_e_B", "P_e_B", "route_e_B"
    ]
    section = read(ROOT / "shared" / "manual_intro_dec_ledger.tex")
    for col in raw_header:
        escaped = col.replace("_", "\\_")
        assert f"\\texttt{{{escaped}}}" in section or col in section


def test_gas_pen_paper_demo_csv_has_two_exact_half_probability_rows():
    rows = read_csv(DEC / "manual2_dec_pen_paper_gas_trace.csv")
    assert [r["tick"] for r in rows] == ["6", "7"]
    assert {r["B"] for r in rows} == {"B_mol_005"}
    assert {r["P_num"] for r in rows} == {"1"}
    assert {r["P_den"] for r in rows} == {"2"}
    assert {r["P_exact"] for r in rows} == {"1/2"}
    assert {r["route_e_B"] for r in rows} == {"water_equivalent_route_unit"}
    assert {r["support_units"] for r in rows} == {"2"}
    assert {r["trace_id"] for r in rows} == {"trace_mol_005"}
    assert {r["motif_id"] for r in rows} == {"motif_mol_005"}
    assert {r["sadar_context_id"] for r in rows} == {"sadar_mol_005"}
    assert {r["freeze_row_id"] for r in rows} == {"chain_GAS_tripeptide_seed"}
    assert {r["delta3_status"] for r in rows} == {"zero_residual"}


def test_gas_worked_text_shows_trace_detector_sadar_freeze_and_audit_order():
    section = read(SEC / "03_gas_dec_trace_application.tex")
    for token in [
        "chain\\_GAS\\_tripeptide\\_seed", "tick", "6", "7", "$1/2$",
        "P_{\\mathrm{route}}=\\frac12+\\frac12=1", "mathrm{support\\_units}=2",
        "trace\\_mol\\_005", "motif\\_mol\\_005", "sadar\\_mol\\_005",
        "C}_8", "H}_{15}", "N}_3", "O}_5", "\\Delta_{\\mathrm{CHNOPS}}=(0,0,0,0,0,0)", "\\delta_3=0",
    ]:
        assert token in section
    assert section.index("raw\\_dec\\_trace\\_molecular\\_chain.csv") < section.index("read\\_only\\_trace\\_molecular\\_chain.csv")
    assert section.index("read\\_only\\_trace\\_molecular\\_chain.csv") < section.index("detected\\_chain\\_motifs.csv")
    assert section.index("detected\\_chain\\_motifs.csv") < section.index("sadar\\_detector\\_context.csv")
    assert section.index("sadar\\_detector\\_context.csv") < section.index("chain\\_formula\\_predictions.csv")
    assert section.index("chain\\_formula\\_predictions.csv") < section.index("molecular\\_chain\\_delta3\\_audit.csv")
    assert section.index("aod\\_contact\\_prediction\\_freeze.csv") < section.index("protein\\_contact\\_score.csv")


def test_dec_trace_chain_manifest_points_through_all_ledgers():
    rows = read_csv(DEC / "manual2_dec_trace_chain_manifest.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["chain_id"] == "chain_GAS_tripeptide_seed"
    for key in [
        "manual_demo_file", "raw_dec_file", "trace_file", "detector_file", "sadar_context_file",
        "freeze_file", "delta3_file", "contact_freeze_file", "score_file",
    ]:
        assert (ROOT / row[key]).exists(), key
    assert row["chain_status"] == "manual2_pen_paper_dec_trace_chain"


def test_dec_lane_is_manifested_and_target_lanes_remain_downstream():
    manifest = json.loads((ROOT / "manual-2" / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r16"
    assert "dec_pen_paper" in manifest["lanes"]
    dec = manifest["lanes"]["dec_pen_paper"]
    assert (ROOT / dec["gas_trace"]).exists()
    assert (ROOT / dec["trace_chain_manifest"]).exists()
    raw_text = (MOL / "raw_dec_trace_molecular_chain.csv").read_text(encoding="utf-8").lower()
    for forbidden in ["pubchem", "rdkit", "uniprot", "pdb", "alphafold", "target", "score"]:
        assert forbidden not in raw_text


def test_affirmative_status_headings_replace_defensive_no_claim_heading():
    joined = "\n".join(read(p) for p in SEC.glob("*.tex"))
    assert "No folding claim" not in joined
    assert "Folding status" in joined
    assert "Current score scope" in joined
