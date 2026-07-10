
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manual2_post_intro_elementary_row_uses_dec_boundary_form():
    s2 = (ROOT / "manual-2" / "sections" / "02_elementary_dec_worked_example.tex").read_text(encoding="utf-8")
    assert "B=B_{336}" in s2
    assert "D.E.C. row pair" in s2
    assert "A$\\Omega$D now names the detected retained-capacity motif" in s2
    assert "curling-curls specification" in s2
    assert "SADAR context" in s2
    assert "The PubChem/element lane is a downstream lookup" in s2


def test_manual2_post_intro_does_not_replace_shared_opening_with_new_primitives():
    post_intro_files = [
        "02_elementary_dec_worked_example.tex",
        "03_gas_dec_trace_application.tex",
        "03_molecular_chain_worked_example.tex",
        "04_chain_fission_worked_example.tex",
        "05_pdb_contact_target_worked_example.tex",
        "06_contact_residual_worked_example.tex",
    ]
    text = "\n".join((ROOT / "manual-2" / "sections" / name).read_text(encoding="utf-8") for name in post_intro_files)
    assert "S_{\\mathrm{FFS}}" not in text
    assert "R_{\\zeta}" not in text
    assert "F_K" not in text


def test_manual2_opening_shared_files_are_not_rewritten_by_alignment_patch():
    # The shared source is frozen by exact hash; its content may include the accepted
    # shared Manual-II branch, but post-intro Manual-II applications are the only
    # place where new wording should be added in this patch line.
    import hashlib
    expected = {
        "shared/manual_intro_scope_policy.tex": "351880d125057ec624c6a1d17fa6d32e5f41a3fb2c9b0c47046ef80860f0771b",
        "shared/manual_intro_dec_ledger.tex": "cef213f2666e75b21ae1a41afc36d0adc8c82d15f5487bf7af7a2f5ce041e626",
    }
    for rel, digest in expected.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
