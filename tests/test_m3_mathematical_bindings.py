"""Additional M3 statements remain active and independently integrity-bound."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest
import sympy as s

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('m3_audit', ROOT/'scripts/audit_scientific_sources.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_new_mathematics_is_active_without_replacing_canonical_obligations():
    result = audit.audit(ROOT)['compaction']
    assert (result['canonical_groups'], result['canonical_equations'],
            result['declared_dependencies']) == (44, 81, 72)
    assert result['m3'] == {'equations': 7, 'sources': 1}


def test_shared_coefficient_identity_has_no_identifying_power():
    q, r = s.symbols('q r', positive=True)
    residual = (2*q*r)*r - 2*(q*r*r)
    assert s.simplify(residual) == 0
    assert s.diff(residual, q) == 0


def test_finite_law_mean_variance_and_legitimate_cancellation_symbolically():
    epsilon, x, a, b = s.symbols('epsilon x a b', positive=True)
    law = [(-epsilon, s.Rational(1, 4)), (0, s.Rational(1, 2)),
           (epsilon, s.Rational(1, 4))]
    mean = sum(p*v**2 for v,p in law)
    variance = s.expand(sum(p*(v**2-mean)**2 for v,p in law))
    assert s.simplify(mean-epsilon**2/2) == 0
    assert s.simplify(variance-epsilon**4/4) == 0
    assert s.diff(x*x, x).subs(x, 0) == 0
    assert s.simplify((a+x)-(b+x)) == a-b


def test_free_relative_gain_has_constructive_countermodels():
    nh,nc,gc,r = s.symbols('nh nc gc r', positive=True)
    gh = r*gc*nc/nh
    assert s.simplify(gh*nh/(gc*nc)) == r
    assert s.simplify((2*gh)*nh/(gc*nc)) == 2*r


@pytest.fixture
def isolated(tmp_path):
    return Path(shutil.copytree(ROOT, tmp_path/'source',
        ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache',
                                     '*.pdf','*.xdv','*.log','*.fls','*.fdb_latexmk')))


def test_mathematical_body_cannot_be_removed_behind_a_retained_label(isolated):
    p = isolated/'sections/07_cell_measures_mappings.tex'
    block = audit.equations(isolated)['eq:m3-composed-bound']
    p.write_text(p.read_text().replace(block, r'\label{eq:m3-composed-bound}', 1))
    with pytest.raises(ValueError, match='M3 mathematical statement or owner changed'):
        audit.audit(isolated)


def test_m3_contract_cannot_release_its_own_source_binding(isolated):
    p = isolated/'contracts/scientific/M3_MATHEMATICAL_BINDINGS.json'
    d = json.loads(p.read_text())
    d['sources'] = {}
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match='scientific contract integrity changed'):
        audit.audit(isolated)
