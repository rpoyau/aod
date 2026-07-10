
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shared_intro_source_files_exist_and_manuals_include_them():
    assert (ROOT / "shared" / "manual_intro_scope_policy.tex").exists()
    assert (ROOT / "shared" / "manual_intro_dec_ledger.tex").exists()
    assert r"\input{../shared/manual_intro_scope_policy.tex}" in read("manual/sections/00_scope.tex")
    assert r"\input{../shared/manual_intro_dec_ledger.tex}" in read("manual/sections/00_dec_ledger.tex")
    assert r"\input{../shared/manual_intro_scope_policy.tex}" in read("manual-2/sections/00_scope.tex")
    assert r"\input{../shared/manual_intro_dec_ledger.tex}" in read("manual-2/sections/00_dec_ledger.tex")


def test_manual2_activates_manualii_branch_before_structural_opening():
    main = read("manual-2/main.tex")
    assert r"\def\AODManualII{1}" in main
    assert main.index(r"\def\AODManualII{1}") < main.index("sections/00_scope.tex")
    assert main.index("sections/00_scope.tex") < main.index("sections/00_dec_ledger.tex")
    assert main.index("sections/00_dec_ledger.tex") < main.index("sections/02_elementary_dec_worked_example.tex")


def test_builder_includes_shared_source_directory():
    builder = read("scripts/build_release_bundle.py")
    assert '"shared"' in builder
