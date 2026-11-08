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
spec = importlib.util.spec_from_file_location('m3_compaction', ROOT/'scripts/audit_ontology_compaction.py')
compaction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compaction)


def check_m3(root):
    maps = {surface: audit.label_map(root, surface) for surface in ('main', 'manual')}
    eqs = {surface: audit.equations(root, surface) for surface in ('main', 'manual')}
    return compaction.audit_m3(root, maps, eqs)


def test_new_mathematics_is_active_without_replacing_canonical_obligations():
    result = audit.audit(ROOT)['compaction']
    assert (result['canonical_groups'], result['canonical_equations'],
            result['declared_dependencies']) == (44, 81, 72)
    assert result['m3'] == {'equations': 7, 'sources': 2}
    record = json.loads((ROOT/'contracts/scientific/M3_MATHEMATICAL_BINDINGS.json').read_text())
    assert sum(binding.get('surface', 'main') == 'main'
               for binding in record['equations'].values()) == 6
    assert record['equations']['eq:m3-disk-enclosure']['surface'] == 'manual'


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


@pytest.mark.parametrize('mutation', [
    'label-only', 'hidden', 'formula', 'wrong-document', 'wrong-path', 'duplicate',
])
def test_moved_disk_requires_one_active_manual_body(isolated, mutation):
    assert check_m3(isolated) == {'equations': 7, 'sources': 2}
    label = 'eq:m3-disk-enclosure'
    body = audit.equations(isolated, 'manual')[label]
    path = isolated/'manual/sections/01_m3_cells.tex'
    if mutation == 'label-only':
        replacement = r'\label{' + label + '}'
    elif mutation == 'hidden':
        replacement = r'\iffalse' + body + r'\fi'
    elif mutation == 'formula':
        replacement = body.replace(r'\frac{8}{n}', r'\frac{7}{n}')
        assert replacement != body
    else:
        replacement = body if mutation == 'duplicate' else ''
        destination = isolated/('manual/sections/02_m3_mapping_error.tex'
                               if mutation == 'wrong-path' else 'sections/07_cell_measures_mappings.tex')
        destination.write_text(destination.read_text() + '\n' + body + '\n')
    path.write_text(path.read_text().replace(body, replacement, 1))
    with pytest.raises(ValueError, match='M3 mathematical statement or owner changed ' + label):
        check_m3(isolated)


def test_unrendered_manual_example_cannot_satisfy_m3_owner(isolated):
    path = isolated/'manual/main.tex'
    text = path.read_text()
    changed = text.replace(r'\input{sections/01_m3_cells.tex}', '')
    assert changed != text
    path.write_text(changed)
    with pytest.raises(ValueError, match='M3 mathematical statement or owner changed eq:m3-disk-enclosure'):
        check_m3(isolated)


def test_staircase_anchor_must_move_with_its_manual_example(isolated):
    manual = isolated/'manual/sections/01_m3_cells.tex'
    label = r'\label{prop:m3-staircase}'
    assert label in manual.read_text()
    manual.write_text(manual.read_text().replace(label, '', 1))
    main = isolated/'sections/07_cell_measures_mappings.tex'
    main.write_text(main.read_text() + '\n' + label + '\n')
    with pytest.raises(ValueError, match='cell measure anchor owner changed prop:m3-staircase'):
        check_m3(isolated)


def test_m3_source_cannot_rebind_its_own_changed_mathematics(isolated):
    import hashlib
    path = isolated/'manual/sections/01_m3_cells.tex'
    path.write_text(path.read_text().replace(r'\frac{8}{n}', r'\frac{7}{n}'))
    contract = isolated/'contracts/scientific/M3_MATHEMATICAL_BINDINGS.json'
    record = json.loads(contract.read_text())
    record['sources']['manual/sections/01_m3_cells.tex'] = hashlib.sha256(path.read_bytes()).hexdigest()
    record['equations']['eq:m3-disk-enclosure']['formula'] = compaction._formula(
        audit.equations(isolated, 'manual')['eq:m3-disk-enclosure'])
    contract.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='scientific contract integrity changed'):
        check_m3(isolated)


def test_cell_contract_cannot_silently_reassign_the_example_to_main(isolated):
    path = isolated/'contracts/scientific/CELL_MEASURE_SPEC.json'
    record = json.loads(path.read_text())
    record['main_anchors'].append(record['manual_anchors'].pop())
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='scientific contract integrity changed CELL_MEASURE_SPEC.json'):
        check_m3(isolated)
