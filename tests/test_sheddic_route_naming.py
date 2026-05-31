from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def test_reclosure_split_uses_outward_remainder_not_exo_remainder():
    text = read('sections/06_field.tex')
    assert r'X_W^{\mathrm{out}}=(1-\lambda_{\mathrm{reclose}})X_{\mathrm{shedding}}' in text
    assert r'X_W^{\mathrm{exo}}=(1-\lambda_{\mathrm{reclose}})X_{\mathrm{shedding}}' not in text
    assert r'X_W^{\mathrm{out}}=X_{\mathrm{exo}}+X_{\mathrm{redir}}+X_{\mathrm{open}}' in text


def test_flip_class_uses_sheddic_route_not_bare_sheddic():
    text = read('manual/sections/06_field_dynamics_applications.tex')
    assert r'\mathrm{sheddic\_route}' in text
    assert r'\mathrm{early\_coupling},\mathrm{fizz},\mathrm{pending},\mathrm{sheddic}' not in text


def test_cycle_shedding_demo_uses_outward_remainder():
    text = read('appendices/D_cycle_shedding_demonstration.tex')
    assert 'outward remainder' in text
    assert 'O_t) exoshedding' not in text
