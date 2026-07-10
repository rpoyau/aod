
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "manual-2" / "sections"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def included_sections() -> list[str]:
    main = read(ROOT / "manual-2" / "main.tex")
    lines = []
    for line in main.splitlines():
        if line.strip().startswith("\\input{sections/"):
            lines.append(line.strip())
    return lines


def test_manual2_structural_opening_matches_manual_opening_pattern():
    lines = included_sections()
    assert lines[0] == r"\input{sections/00_scope.tex}"
    assert lines[1] == r"\input{sections/00_dec_ledger.tex}"
    assert lines[2] == r"\input{sections/00_dec_report_coordinate_overlay.tex}"
    assert lines[3] == r"\input{sections/01_ontology_to_dec_occurrence_overlay.tex}"
    elementary = r"\input{sections/02_elementary_dec_worked_example.tex}"
    hydrogen = r"\input{sections/01_hydrogen_transition_sadar_lock_atlas.tex}"
    assert elementary in lines
    if hydrogen in lines:
        assert lines.index(hydrogen) == lines.index(r"\input{sections/01_ontology_to_dec_occurrence_overlay.tex}") + 1
        assert lines.index(hydrogen) < lines.index(elementary)
    else:
        assert elementary in lines[4]


def test_worked_rows_appear_before_dataset_inventory():
    order = "\n".join(included_sections())
    assert order.index("02_elementary_dec_worked_example") < order.index("A_dataset_inventory_manifests")
    assert order.index("06_contact_residual_worked_example") < order.index("A_dataset_inventory_manifests")
    assert order.index("07_regenerating_csv_ledgers") < order.index("A_dataset_inventory_manifests")


def test_manual2_contains_gas_dec_application_between_opening_and_formula_worked_row():
    order = "\n".join(included_sections())
    assert order.index("00_dec_ledger") < order.index("03_gas_dec_trace_application")
    assert order.index("03_gas_dec_trace_application") < order.index("03_molecular_chain_worked_example")
    text = read(SEC / "03_gas_dec_trace_application.tex")
    assert "B_{\\mathrm{mol},005}" in text
    assert "P_{\\mathrm{route}}=\\frac12+\\frac12=1" in text
    assert "\\mathrm{support\\_units}=2" in text
    assert "trace\\_mol\\_005" in text
    assert "motif\\_mol\\_005" in text
    assert "sadar\\_mol\\_005" in text


def test_manual2_contains_glycine_alanine_arithmetic():
    text = read(SEC / "03_molecular_chain_worked_example.tex")
    assert "\\mathbf n(\\mathrm{Gly})+\\mathbf n(\\mathrm{Ala})-\\mathbf n(H_2O)" in text
    assert "\\mathrm{Gly\\mbox{-}Ala}" in text
    assert "\\Delta_{\\mathrm{CHNOPS}}=(0,0,0,0,0,0)" in text
    assert "chain_formula_predictions.csv" in text


def test_manual2_contains_fission_audit_arithmetic():
    text = read(SEC / "04_chain_fission_worked_example.tex")
    assert "\\mathbf n(\\mathrm{Gly})+\\mathbf n(\\mathrm{Ala})" in text
    assert "\\mathbf n(\\mathrm{Gly\\mbox{-}Ala})+\\mathbf n(H_2O)" in text
    assert "chain_fission_audit.csv" in text


def test_manual2_contains_pdb_ca_distance_contact_arithmetic():
    text = read(SEC / "05_pdb_contact_target_worked_example.tex")
    assert "d_{1,3}=7.6" in text
    assert "d_{1,3}\\le 8.0" in text
    assert "|3-1|\\ge 2" in text
    assert "O_{1,3}=1" in text
    assert "pdb_mmcif_contact_map_derived.csv" in text


def test_manual2_contains_contact_residual_arithmetic():
    text = read(SEC / "06_contact_residual_worked_example.tex")
    assert "\\widehat O_{1,3}=1" in text
    assert "O_{1,3}=1" in text
    assert "=1-1=0" in text
    assert "TP=1" in text
    assert "protein_contact_score.csv" in text


def test_release_log_language_is_not_in_main_worked_body():
    section_names = [
        "02_elementary_dec_worked_example.tex",
        "03_gas_dec_trace_application.tex",
        "03_molecular_chain_worked_example.tex",
        "04_chain_fission_worked_example.tex",
        "05_pdb_contact_target_worked_example.tex",
        "06_contact_residual_worked_example.tex",
    ]
    main_body = "\n".join(read(SEC / name) for name in section_names)
    forbidden = [
        "release bundle contains",
        "Release assets",
        "Current milestone",
        "bundle-v",
        "SHA-256",
        "patch summary",
    ]
    for term in forbidden:
        assert term not in main_body


def test_roadmap_release_notes_live_in_appendix_or_external_file():
    main = read(ROOT / "manual-2" / "main.tex")
    assert "C_roadmap_release_pointer" in main
    appendix = read(SEC / "C_roadmap_release_pointer.tex")
    assert "MANUAL\\_II\\_ROADMAP.md" in appendix
    assert "patch-summary" in appendix
