"""Current typed ownership and semantic negative controls on disposable sources."""
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r07_sources', ROOT / 'scripts/audit_scientific_sources.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
MANUAL = 'manual/sections/00_awareness_fixtures.tex'
MAIN = 'sections/08_awareness_learning_mindfulness.tex'


def copy_source(tmp_path):
    out = tmp_path / 'source'
    shutil.copytree(ROOT, out, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', 'R07_DELIVERY'))
    assert a.audit(out)['compaction']['canonical_equations'] == 81
    return out


def test_reviewed_ownership_preserves_formulas_and_operation_bindings():
    assert a.audit(ROOT)['compaction']['canonical_equations'] == 81
    record = json.loads((ROOT/'contracts/scientific/OWNERSHIP_AND_FIXTURES.json').read_text())
    rows = record['fixture_bindings']
    assert sum(r['current_construct']['surface'] == 'manual' for r in rows) == 23
    assert len(rows) == 47
    # Historical tags are not proxies for the actual executed models.
    by_id = {r['fixture_id']: r for r in rows}
    assert by_id['R04-NEW-041']['current_construct']['label'] == 'eq:fold-outer-closure'
    assert by_id['R04-NEW-042']['current_construct']['label'] == 'eq:retained-rebalancing'
    assert by_id['R04-NEW-043']['manual_model_equations'] == ['eq:awareness-response']
    assert 'eq:action-return-retention' not in by_id['R04-NEW-027']['manual_model_equations']


def test_inherited_worked_equations_have_one_complete_manual_owner():
    record = json.loads((ROOT/'contracts/scientific/OWNERSHIP_AND_FIXTURES.json').read_text())
    owners = {binding['label']: binding for binding in record['anchor_owners']}
    main, manual = a.equations(ROOT), a.equations(ROOT, 'manual')
    for label in ('eq:sadar-rational-response', 'eq:double-colon-parse-example',
                  'app:rd:eq:three-four-rd'):
        assert owners[label]['surface'] == 'manual'
        assert owners[label]['equation'] is True
        assert label in manual and label not in main
    # Moving examples must not reclassify the symbolic constructions they use.
    for label in ('eq:causal-update', 'eq:fractal-tesseract-cycle-range',
                  'eq:beat-count', 'app:rd:eq:path-support',
                  'eq:single-hinge-symmetric-fixture'):
        assert label in main and label not in manual


@pytest.mark.parametrize('label,mutation,reason', [
    ('eq:sadar-rational-response', 'label-only', 'owned mathematical body absent'),
    ('eq:double-colon-parse-example', 'hidden', 'inactive or wrong typed owner'),
    ('app:rd:eq:three-four-rd', 'altered', 'owned mathematical statement changed'),
    ('eq:sadar-rational-response', 'duplicate', 'duplicate cross-document active owner'),
])
def test_relocated_inherited_examples_cannot_leave_empty_or_competing_owners(
        tmp_path, label, mutation, reason):
    root = copy_source(tmp_path)
    path = root/a.label_map(root, 'manual')[label]['path']
    body = a.equations(root, 'manual')[label]
    if mutation == 'label-only':
        replacement = r'\label{' + label + '}'
    elif mutation == 'hidden':
        replacement = r'\iffalse' + body + r'\fi'
    elif mutation == 'altered':
        replacement = body.replace('68', '69')
        assert replacement != body
    else:
        replacement = body
        main = root/'sections/06_field.tex'
        main.write_text(main.read_text() + '\n' + body + '\n')
    path.write_text(path.read_text().replace(body, replacement, 1))
    with pytest.raises(ValueError, match=reason):
        a.audit(root)


@pytest.mark.parametrize('mutation, reason', [
    ('unincluded-model', r'Manual example family not rendered|Active scientific source anchor ownership mismatch|^unresolved manual reference manual:m2-awareness-fixtures in manual/sections/09_prediction_test_fixture_registry\.tex$'),
    ('label-without-body', 'canonical mathematical body absent'),
    ('unrelated-fixture-binding', 'scientific contract integrity changed'),
    ('altered-action-residual', 'canonical mathematical statement changed'),
], ids=['O01', 'O02', 'O04', 'O06'])
def test_semantic_ownership_mutations_are_rejected(tmp_path, mutation, reason):
    root = copy_source(tmp_path)
    if mutation == 'unincluded-model':
        p = root/'manual/main.tex'
        p.write_text(p.read_text().replace(r'\input{sections/00_awareness_fixtures.tex}', ''))
    elif mutation == 'label-without-body':
        body = a.equations(root, 'manual')['eq:action-return-retention']
        p = root/MANUAL
        p.write_text(p.read_text().replace(body, r'\label{eq:action-return-retention}'))
    elif mutation == 'unrelated-fixture-binding':
        p = root/'contracts/scientific/OWNERSHIP_AND_FIXTURES.json'; data = json.loads(p.read_text())
        data['fixture_bindings'][21]['current_construct'] = {
            'surface': 'main', 'path': 'sections/06_field.tex', 'label': 'eq:fourier-transform'}
        p.write_text(json.dumps(data))
    else:
        p = root/MANUAL;p.write_text(p.read_text().replace('r_a=y-u', 'r_a=y+u'))
    with pytest.raises(ValueError, match=reason):
        a.audit(root)


def test_wrong_document_owner_is_rejected(tmp_path):
    root = copy_source(tmp_path)
    p = root/'contracts/scientific/CANONICAL_BINDINGS.json';data = json.loads(p.read_text())
    row = next(r for r in data['ownership'] if r['concept'] == 'Action return and learning')
    row.update(surface='main', path=MAIN)
    p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='missing active canonical anchor'):
        a.audit(root)


def test_conditionally_hidden_manual_model_cannot_satisfy_owner(tmp_path):
    root = copy_source(tmp_path)
    p = root/MANUAL;body = a.equations(root, 'manual')['eq:action-return-retention']
    p.write_text(p.read_text().replace(body, r'\iffalse' + body + r'\fi'))
    with pytest.raises(ValueError, match='unresolved manual reference|missing active canonical anchor'):
        a.audit(root)
