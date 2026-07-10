
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_manual2_rendered_body_does_not_expose_source_sharing_as_reader_dependency():
    post_intro = "\n".join(
        (ROOT / "manual-2" / "sections" / name).read_text(encoding="utf-8")
        for name in [
            "02_elementary_dec_worked_example.tex",
            "03_gas_dec_trace_application.tex",
            "03_molecular_chain_worked_example.tex",
            "04_chain_fission_worked_example.tex",
            "05_pdb_contact_target_worked_example.tex",
            "06_contact_residual_worked_example.tex",
            "08_scoped_pdb_contact_residual_pilot.tex",
            "07_regenerating_csv_ledgers.tex",
        ]
    )
    forbidden = [
        "Manual I and Manual II share",
        "Manual II inherits Manual I",
        "Using Section 1",
        "Using Section 2",
        "using Section 1",
        "using Section 2",
    ]
    for term in forbidden:
        assert term not in post_intro


def test_manual2_opening_wrappers_mirror_manual_wrapper_names():
    main = read("manual-2/main.tex")
    assert "sections/00_scope.tex" in main
    assert "sections/00_dec_ledger.tex" in main
    assert "01_shared_scope_policy" not in main
    assert "02_shared_afc_dec_ledger" not in main
    assert r"\input{../shared/manual_intro_scope_policy.tex}" in read("manual-2/sections/00_scope.tex")
    assert r"\input{../shared/manual_intro_dec_ledger.tex}" in read("manual-2/sections/00_dec_ledger.tex")


def test_manual_i_branch_still_uses_shared_wrappers():
    assert r"\input{../shared/manual_intro_scope_policy.tex}" in read("manual/sections/00_scope.tex")
    assert r"\input{../shared/manual_intro_dec_ledger.tex}" in read("manual/sections/00_dec_ledger.tex")
