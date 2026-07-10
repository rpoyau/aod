from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def rendered_manual2_inputs() -> str:
    names = [
        "manual-2/main.tex",
        "manual-2/sections/00_scope.tex",
        "manual-2/sections/00_dec_ledger.tex",
        "manual-2/sections/02_elementary_dec_worked_example.tex",
        "manual-2/sections/03_gas_dec_trace_application.tex",
        "manual-2/sections/03_molecular_chain_worked_example.tex",
        "manual-2/sections/04_chain_fission_worked_example.tex",
        "manual-2/sections/05_pdb_contact_target_worked_example.tex",
        "manual-2/sections/06_contact_residual_worked_example.tex",
        "manual-2/sections/08_scoped_pdb_contact_residual_pilot.tex",
        "manual-2/sections/09_multipair_scoped_contact_residual_pilot.tex",
        "manual-2/sections/10_external_pdb_accession_scope_gate.tex",
        "manual-2/sections/07_regenerating_csv_ledgers.tex",
        "manual-2/sections/A_dataset_inventory_manifests.tex",
        "manual-2/sections/B_value_map_quarantine.tex",
        "manual-2/sections/C_roadmap_release_pointer.tex",
    ]
    return "\n".join(read(name) for name in names)


def test_manual2_wrapper_keeps_shared_source_frozen_but_renders_versionless_status():
    wrapper = read("manual-2/sections/00_dec_ledger.tex")
    shared = read("shared/manual_intro_dec_ledger.tex")
    assert "Manual II v40.02r08.6" in shared
    assert "shared source file itself is not edited" in wrapper
    assert "Manual II is the compact worked-row rendering of the fusion-scale manual." in wrapper
    assert "Manual II v40" not in wrapper


def test_manual2_rendered_inputs_do_not_introduce_version_specific_pdf_body_text():
    text = rendered_manual2_inputs()
    forbidden = ["Manual II v40", "r09.1", "v40.02r08 scope", "The v40.02r08 scope"]
    for term in forbidden:
        assert term not in text
