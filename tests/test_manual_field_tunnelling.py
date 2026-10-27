
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def test_field_tunnelling_placement_and_scope():
    sec = read('manual/sections/00_dec_ledger.tex')
    assert 'Field tunnelling is a D0 exact internal fixture' in sec
    assert 'scalar tunnel contribution' in sec


def test_field_tunnelling_exact_arithmetic_in_manual():
    sec = read('manual/sections/00_dec_ledger.tex')
    assert r'\operatorname{adm}(e_0;B|t)=0' in sec
    assert r'\operatorname{Slide}_{\mu}(B|t)=\{s_1,\ldots,s_n\}' in sec
    assert r'Z_{\mathrm{slide}}(B|t)' in sec
    assert r'P_{\mathrm{slide}}(s_i;B|t)' in sec
    assert r's_{\mathrm{tunnel}}=(e_3,+1)' in sec
    assert r'P_{\mathrm{tunnel}}=1/7' in sec
    assert r'\rho^D_{\omega,s_{\mathrm{tunnel}}}=\min(5,2)=2' in sec
    assert r'p^D_{s_{\mathrm{tunnel}}}=3\cdot2=6' in sec
    assert r'T^D_{\mathrm{tunnel}}=(1/7)\cdot6=6/7' in sec
    assert 'The tunnel contribution is the window-clipped pressure carried by the slide-compatible outgoing successor.' in sec


def test_field_tunnelling_csv_exact_values():
    path = ROOT / 'manual/data/dec/field_tunnelling_hinge_slide_window_clip.csv'
    rows = list(csv.DictReader(path.open()))
    assert len(rows) == 3
    assert [r['slide_branch'] for r in rows] == ['e1:-1','e2:-1','e3:+1']
    assert [r['P_num'] + '/' + r['P_den'] for r in rows] == ['3/7','3/7','1/7']
    tunnel = [r for r in rows if r['is_tunnel_branch'] == '1'][0]
    assert tunnel['slide_branch'] == 'e3:+1'
    assert tunnel['direct_adm'] == '0'
    assert tunnel['P_num'] == '1' and tunnel['P_den'] == '7'
    assert tunnel['RD'] == '5'
    assert tunnel['omega'] == '2'
    assert tunnel['rhoD_omega'] == '2'
    assert tunnel['C3'] == '3'
    assert tunnel['pD'] == '6'
    assert tunnel['tunnel_contribution_num'] == '6'
    assert tunnel['tunnel_contribution_den'] == '7'


def test_registry_contains_field_tunnelling_row():
    reg = read('manual/sections/09_prediction_test_fixture_registry.tex')
    assert 'Field tunnelling hinge-slide fixture & D0 & integer fixture fields' in reg
    assert r'T^D_{\mathrm{tunnel}}' in reg
