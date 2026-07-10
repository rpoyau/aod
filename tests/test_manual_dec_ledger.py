
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def test_dec_ledger_section_placement_and_name():
    manual_main = read('manual/main.tex')
    assert r'\input{sections/00_dec_ledger.tex}' in manual_main
    assert manual_main.index(r'\input{sections/00_scope.tex}') < manual_main.index(r'\input{sections/00_dec_ledger.tex}') < manual_main.index(r'\input{sections/03_short_window_rcd_shedding_fixtures.tex}')
    sec = read('shared/manual_intro_dec_ledger.tex')
    assert r'\section{Pen-and-Paper AFC Raw Execution and D.E.C. Ledger}' in sec
    assert 'D.E.C. means Declared Edge Computation ledger' in sec
    assert 'manual ledger format used to expose one declared AFC edge computation' in sec
    assert 'AFC raw node' in sec
    assert 'D.E.C. ledger' in sec
    assert 'AFC runs raw. The trace records the run. A\\(\\Omega\\)D names detected motifs.' in sec


def test_dec_ledger_uses_duration_clipping_and_collision_support_not_ttl_or_higgs():
    sec = read('shared/manual_intro_dec_ledger.tex')
    assert 'duration-clipping' in sec
    assert 'collision-support trace status' in sec
    assert 'TTL cutoff' not in sec
    for term in ['Higgs', 'LHC', 'GeV', 'ATLAS', 'CMS']:
        assert term not in sec


def test_dec_exact_kernel_fractions_in_csv():
    path = ROOT / 'manual/data/dec/dec_one_node_ledger_example.csv'
    rows = list(csv.DictReader(path.open()))
    assert [r['neighbor'] for r in rows] == ['(1,0,0,0)','(0,1,0,0)','(0,0,1,0)','(0,0,0,1)']
    assert [r['probability_exact'] for r in rows] == ['1/8','1/8','1/2','1/4']
    assert [r['route'] for r in rows] == ['outgoing','returned','hinge','outgoing']


def test_dec_hinge_slide_fractions_and_route_labels():
    path = ROOT / 'manual/data/dec/dec_hinge_slide_example.csv'
    rows = list(csv.DictReader(path.open()))
    assert [r['probability_exact'] for r in rows] == ['3/7','3/7','1/7']
    assert [r['route'] for r in rows] == ['returned','returned','outgoing']
    assert 'return' not in [r['route'] for r in rows]
    assert 'out' not in [r['route'] for r in rows]


def test_dec_section_exact_arithmetic_statements():
    sec = read('shared/manual_intro_dec_ledger.tex')
    assert r'P^{\mathrm{iso}}(e_i;B)=\frac14' in sec
    assert r'w=(1,1,4,2)' in sec
    assert r'P^{\mathrm{ani}}=(1/8,1/8,1/2,1/4)' in sec
    assert r"w'((e_1,-1),(e_2,-1),(e_3,+1))=(3,3,1)" in sec
    assert r'P_{\mathrm{returned}}=3/7+3/7=6/7' in sec
    assert r'P_{\mathrm{outgoing}}=1/7' in sec
    assert r'p^D=C_3\rho^D_\omega=12' in sec
    assert r'\SADARop_B=p^D A_{12}=12(1/3)=4' in sec
    assert r'A_{21}=-1/3' in sec
    assert r'\SADARop_B=-4' in sec
    assert r'\Delta_{\mathrm{close}}=P^D-C_{\mathrm{close}}=3' in sec
    assert r'X_{\mathrm{shedding}}=\max(0,\Delta_{\mathrm{close}})=3' in sec


def test_dec_delta3_requires_comparator_language():
    sec = read('shared/manual_intro_dec_ledger.tex')
    assert 'Fixture-comparator rows form exact \\(\\delta_3\\) tallies.' in sec
    assert 'Fixture-comparator rows record exact \\(\\delta_3\\) residuals. Boundary-route rows record boundary values and route audits.' in sec
    assert 'Without a comparator' not in sec
    assert 'not an exact residual tally' not in sec


def test_tau_missing_burden_exact_ratio_csv_and_manual():
    path = ROOT / 'manual/data/dec/tau_missing_burden_exact_ratio_patch.csv'
    rows = list(csv.DictReader(path.open()))
    assert rows[0]['candidate'] == '1:2:9_yro'
    assert rows[0]['alias'] == 'Dimonnanyro'
    assert rows[0]['missing_num'] == '31'
    assert rows[0]['missing_den'] == '50'
    assert rows[0]['missing_frac_exact'] == '31/50'
    assert rows[0]['missing_fraction_display'] == '0.62'
    field_dyn = read('manual/sections/06_field_dynamics_applications.tex')
    assert r'\mathrm{miss}_\tau(1{:}2{:}9_{\mathrm{yro}})=\frac{31}{50}' in field_dyn
    assert r'\mathrm{missing\_fraction\_display}=0.62' in field_dyn


def test_dec_blocking_rule_and_bridge_sentence():
    sec = read('shared/manual_intro_dec_ledger.tex')
    assert r'\subsection{Blocking rule}' in sec
    assert 'Blocking is zero admissibility.' in sec
    assert 'not low probability' not in sec
    assert 'renormalized over branch-oriented continuations' in sec
    assert 'prior hinge-state row \\((e_3,0)\\) attempts same-resolution dwell' in sec
    assert r'\operatorname{adm}(e_3,0;B)=0' in sec
    assert 'not the edge slot \\(e_3\\) itself' in sec
    assert 'may re-enter only as an admitted branch state' in sec
    assert 'D.E.C. blocking and slide rules' in sec


def test_dec_audit_hooks_present():
    sec = read('shared/manual_intro_dec_ledger.tex')
    assert r'\subsection{D.E.C. audit invariants}' in sec
    assert r'\sum_e P(e;B)=1' in sec
    assert 'Zero admissibility gives zero probability' in sec
    assert r'\mathrm{Adm}^0_B(e,\sigma)=\varnothing' in sec
    assert r'\SADARop_B(C_{\bar e})=-\SADARop_B(C_e)' in sec
    assert 'decimal shown only as a display coordinate' in sec


def test_dec_kernel_text_has_no_orphan_so():
    sec = read('shared/manual_intro_dec_ledger.tex')
    assert '\nso\n' not in sec
    assert 'The anisotropic kernel is' in sec
