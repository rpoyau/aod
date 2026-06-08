from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def read_sources(*dirs):
    parts=[]
    for d in dirs:
        root=ROOT/d
        if root.exists():
            for p in root.rglob('*.tex'):
                parts.append(p.read_text())
    return '\n'.join(parts)


def test_yro_is_route_status_not_support_enclosure():
    main = read_sources('sections','appendices')
    assert r'\operatorname{Yro}_{L}(K;B)' in main
    assert 'odd-window unstable route-status suffix' in main
    assert 'recorded separately from support-enclosure names' in main
    forbidden = ['Pyro', r'\mathsf C_7', r'\mathsf C_9', r'C_7=\\mathrm', r'C_9=\\mathrm']
    for term in forbidden:
        assert term not in main
    assert r'\mathsf C_6' in main and r'\mathsf C_8' in main and r'\mathsf C_{10}' in main


def test_dimonnanyro_and_tau_yro_update():
    manual = read_sources('manual/sections','manual/appendices')
    assert 'Dimonnanyro' in manual
    assert 'DimonNanon' not in manual
    assert 'DimonNanon' not in (ROOT / 'manual/data/higgs/yro_aliases_and_renames.csv').read_text()
    assert r'1{:}2{:}9_{\mathrm{yro}}' in manual
    assert r'K_\tau^\star=1{:}2{:}9_{\mathrm{yro}}=\mathrm{Dimonnanyro}' in manual


def test_tritrioseptyro_arithmetic_and_saddle():
    manual = read_sources('manual/sections')
    assert 'Tritrioseptyro' in manual
    assert r'3{:}3{:}7_{\mathrm{yro}}' in manual
    for term in [r'\Pi=30', 'RD=61', r'\rho^D_\omega=7', r'P^D_H=21', r'Q^D_H=162']:
        assert term in manual
    assert r'P^D_H-C_6=+3' in manual
    assert r'P^D_H-C_8=-3' in manual
    assert r'C_{3,H}=3' in manual
    assert 'The trace places Tritrioseptyro on the' in manual


def test_higgs_internal_table_has_no_gev_and_external_map_is_after_freeze():
    path=ROOT/'manual/data/higgs/higgs_trace_internal_candidates_selection.csv'
    assert path.exists()
    header=path.read_text().splitlines()[0]
    assert 'GeV' not in header and 'mass' not in header.lower() and 'prediction' not in header.lower()
    rows=list(csv.DictReader(path.open()))
    assert rows[0]['candidate_K']=='3:3:7'
    assert rows[0]['S_H_trace_internal_selection']=='0.0'
    assert rows[0]['rank']=='1'
    ext=ROOT/'manual/data/higgs/higgs_external_map_after_candidate_freeze.csv'
    assert ext.exists()
    etext=ext.read_text()
    assert 'K_H_star,3:3:7_yro' in etext
    assert '124.928' in etext


def test_score_formula_has_no_candidate_identity_override():
    p=ROOT/'manual/data/higgs/higgs_trace_score_formula.md'
    assert p.exists()
    text=p.read_text()
    assert '(p,q,L)=(3,3,7)' in text  # appears only as the forbidden branch example text
    forbidden_code = ['if (p,q,L)==(3,3,7)', 'if (p, q, L) == (3, 3, 7)', 'candidate_K == "3:3:7"']
    for term in forbidden_code:
        assert term not in text
    assert r'\arg\min_K S_H(K)=3{:}3{:}7_{\rm yro}' in text


def test_higgs_terms_are_manual_only():
    main = read_sources('sections','appendices')
    for term in ['Higgs', 'LHC', 'GeV', 'ATLAS', 'CMS', 'Tritrioseptyro']:
        assert term not in main
    manual = read_sources('manual/sections','manual/appendices')
    for term in ['Higgs', 'LHC', 'GeV', 'ATLAS', 'CMS', 'Tritrioseptyro']:
        assert term in manual


def test_higgs_external_lhc_table_values():
    p=ROOT/'manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv'
    assert p.exists()
    rows=list(csv.DictReader(p.open()))
    assert len(rows)==4
    for r in rows:
        assert r['prediction_GeV']=='124.928'
    assert rows[0]['target_name']=='ATLAS_CMS_Run1_combined'
    assert rows[0]['z_score']=='-0.675'
    assert rows[0]['abs_percent_error']=='0.129507'


def test_higgs_clean_line_wording_and_next_layer():
    manual = read_sources('manual/sections')
    assert r'Tritrioseptyro is the \(3{:}3{:}7_{\mathrm{yro}}\) Higgs-support prediction candidate selected by the internal AFC trace' in manual
    assert 'Production-channel and decay-channel residual tables carry the next comparison layer' in manual
    assert 'absolute percent error' in manual
    assert 'This is a Higgs-support diagnostic candidate under a frozen external map. It is not an equivalence proof.' not in manual

def test_yro_clean_status_language():
    main = read_sources('sections','appendices')
    assert 'A yro suffix is audited as route status on a declared boundary/window' in main
    assert 'terminal split' in main
    assert 'does not introduce an odd support enclosure' not in main
