from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

POST_INTRO_FILES = [
    ROOT / "manual-2" / "sections" / "02_elementary_dec_worked_example.tex",
    ROOT / "manual-2" / "sections" / "03_molecular_chain_worked_example.tex",
    ROOT / "manual-2" / "sections" / "04_chain_fission_worked_example.tex",
    ROOT / "manual-2" / "sections" / "05_pdb_contact_target_worked_example.tex",
    ROOT / "manual-2" / "sections" / "06_contact_residual_worked_example.tex",
    ROOT / "manual-2" / "sections" / "07_regenerating_csv_ledgers.tex",
    ROOT / "manual-2" / "sections" / "08_scoped_pdb_contact_residual_pilot.tex",
    ROOT / "manual-2" / "sections" / "09_multipair_scoped_contact_residual_pilot.tex",
    ROOT / "manual-2" / "sections" / "10_external_pdb_accession_scope_gate.tex",
]

FORBIDDEN = [
    "Using Section 1",
    "Using Section 2",
    "using Section 1",
    "using Section 2",
    "Using Sections 1",
    "using Sections 1",
    "using the shared D.E.C.",
    "Using the shared D.E.C.",
    "Manual II inherits Manual I",
]


def test_manual2_post_intro_sections_do_not_refer_reader_outward():
    text = "\n".join(p.read_text(encoding="utf-8") for p in POST_INTRO_FILES)
    for phrase in FORBIDDEN:
        assert phrase not in text


def test_regeneration_section_uses_direct_freeze_first_language():
    text = (ROOT / "manual-2" / "sections" / "07_regenerating_csv_ledgers.tex").read_text(encoding="utf-8")
    assert "freeze-first ledger order" in text
    assert "ordering in Section 1" not in text


def test_release_metadata_records_shared_source_freeze():
    readiness = (ROOT / "RELEASE_READINESS.txt").read_text(encoding="utf-8")
    assert "shared Section 1--2 source is carried forward unchanged" in readiness
    assert "Manual II Section 1--2 shared opening content is not modified" in readiness
