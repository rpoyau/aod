"""R07 typed ownership and semantic negative controls on disposable sources."""
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
    return out


def test_reviewed_ownership_preserves_formulas_and_operation_bindings():
    assert a.audit(ROOT)['compaction']['canonical_equations'] == 81
    record = json.loads((ROOT/'evidence/PR39_MAIN_MANUAL_RELOCATION_R07.json').read_text())
    rows = record['fixture_bindings']
    assert sum(r['current_construct']['surface'] == 'manual' for r in rows) == 23
    assert len(rows) == 47
    # Historical tags are not proxies for the actual executed models.
    by_id = {r['fixture_id']: r for r in rows}
    assert by_id['R04-NEW-041']['current_construct']['label'] == 'eq:fold-outer-closure'
    assert by_id['R04-NEW-042']['current_construct']['label'] == 'eq:retained-rebalancing'
    assert by_id['R04-NEW-043']['manual_model_equations'] == ['eq:awareness-response']
    assert 'eq:action-return-retention' not in by_id['R04-NEW-027']['manual_model_equations']


@pytest.mark.parametrize('mutation, reason', [
    ('unincluded-model', 'Manual example family not rendered'),
    ('label-without-body', 'canonical mathematical body absent'),
    ('renamed-copy-in-main', 'Main concept exclusion|relocated application body'),
    ('unrelated-fixture-binding', 'unreviewed relocation binding'),
    ('backward-dependency', 'Main depends on Manual'),
    ('altered-action-residual', 'canonical mathematical statement changed'),
], ids=['O01', 'O02', 'O03', 'O04', 'O05', 'O06'])
def test_semantic_ownership_mutations_are_rejected(tmp_path, mutation, reason):
    root = copy_source(tmp_path)
    if mutation == 'unincluded-model':
        p = root/'manual/main.tex'
        p.write_text(p.read_text().replace(r'\input{sections/00_awareness_fixtures.tex}', ''))
    elif mutation == 'label-without-body':
        body = a.equations(root, 'manual')['eq:action-return-retention']
        p = root/MANUAL
        p.write_text(p.read_text().replace(body, r'\label{eq:action-return-retention}'))
    elif mutation == 'renamed-copy-in-main':
        body = a.equations(root, 'manual')['eq:action-return-retention']
        body = body.replace('eq:action-return-retention', 'eq:renamed-relation')
        with (root/MAIN).open('a') as f:
            f.write('\nA signal binding and observed difference.\n' + body)
    elif mutation == 'unrelated-fixture-binding':
        p = root/'evidence/PR39_MAIN_MANUAL_RELOCATION_R07.json'; data = json.loads(p.read_text())
        data['fixture_bindings'][21]['current_construct'] = {
            'surface': 'main', 'path': 'sections/06_field.tex', 'label': 'eq:fourier-transform'}
        p.write_text(json.dumps(data))
    elif mutation == 'backward-dependency':
        p = root/'evidence/ONTOLOGY_COMPACTION_BINDINGS.json'; data = json.loads(p.read_text())
        next(r for r in data['ownership'] if r['concept'] == 'Retained carriage')['depends_on'].append('Awareness response and causal difference')
        p.write_text(json.dumps(data))
    else:
        p = root/MANUAL;p.write_text(p.read_text().replace('r_a=y-u', 'r_a=y+u'))
    with pytest.raises(ValueError, match=reason):
        a.audit(root)


def test_wrong_document_owner_is_rejected(tmp_path):
    root = copy_source(tmp_path)
    p = root/'evidence/ONTOLOGY_COMPACTION_BINDINGS.json';data = json.loads(p.read_text())
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
