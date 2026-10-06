"""Actual rendered authority, hierarchy and mathematical-scope controls."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compaction_source_audit", ROOT / "scripts/audit_scientific_sources.py")
a = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = a
spec.loader.exec_module(a)


def copy_source(tmp_path):
    # Tests mutate a disposable source copy; no tracked worktree is edited.
    result = tmp_path / "source"
    shutil.copytree(ROOT, result, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache'))
    return result


def test_rendered_compaction_authority_and_all_ordered_dependencies():
    result = a.audit(ROOT)['compaction']
    assert result['canonical_groups'] == 43
    assert result['canonical_equations'] == 81
    assert result['ordered_dependencies'] == 67
    assert result['refined_first_uses'] == 2
    assert result['manual_example_families'] == 9


def test_competing_field_definition_with_new_label_is_rejected(tmp_path):
    root = copy_source(tmp_path)
    path = root / 'sections/06_field.tex'
    with path.open('a') as stream:
        stream.write('\n\\begin{equation}F_{B,\\lambda}=(B,\\lambda,\\varnothing)'
                     '\\label{eq:competing-scoped-field}\\end{equation}\n')
    with pytest.raises(ValueError, match='competing or absent canonical binding'):
        a.audit(root)


def test_removing_the_sole_science_body_but_retaining_its_label_fails(tmp_path):
    root = copy_source(tmp_path)
    path = root / 'sections/05_curl_closure_duon_current.tex'
    text = path.read_text()
    block = a.equations(root)['eq:field-organization']
    path.write_text(text.replace(block, '\\label{eq:field-organization}', 1))
    with pytest.raises(ValueError, match='required equation absent|canonical mathematical body absent'):
        a.audit(root)


def test_unrendered_awareness_file_cannot_supply_canonical_science(tmp_path):
    root = copy_source(tmp_path)
    path = root / 'main.tex'
    path.write_text(path.read_text().replace('\\input{sections/08_awareness_learning_mindfulness.tex}', ''))
    with pytest.raises(ValueError, match='unresolved literal Main provenance|missing active canonical anchor'):
        a.audit(root)


def test_appendix_c_demotion_cannot_pass_navigation(tmp_path):
    root = copy_source(tmp_path)
    path = root / 'appendices/C_stochastic_crowning.tex'
    path.write_text(path.read_text().replace('\\section{', '\\subsection{', 1))
    with pytest.raises(ValueError, match='appendix is not a top-level section'):
        a.audit(root)


def test_manual_awareness_inclusion_is_an_active_coverage_obligation(tmp_path):
    root = copy_source(tmp_path)
    path = root / 'manual/main.tex'
    path.write_text(path.read_text().replace('\\input{sections/00_awareness_fixtures.tex}', ''))
    with pytest.raises(ValueError, match='Manual example family not rendered'):
        a.audit(root)


def test_first_declaration_cannot_follow_the_rd_consumer(tmp_path):
    root = copy_source(tmp_path)
    path = root / 'sections/05_curl_closure_duon_current.tex'
    text = path.read_text()
    # Move the actual constructor while leaving both labels present.
    start = text.index('\\subsection{Dion}')
    end = text.index('\\subsubsection{Branch/hinge/branch reflection duration}')
    early = text[start:end]
    path.write_text(text[:start] + text[end:] + '\n' + early)
    with pytest.raises(ValueError, match='substantive consumer precedes prerequisite'):
        a.audit(root)


def test_two_branch_roles_do_not_bound_general_channel_capacity():
    from fractions import Fraction as Q
    from math import log
    weights = (Q(3), Q(3), Q(1))
    projected = ((weights[0]+weights[1])/sum(weights), weights[2]/sum(weights))
    assert projected == (Q(6,7), Q(1,7))
    # The three-row bijective ternary channel preserves every input symbol.
    kernel = ((0,1,0), (0,0,1), (1,0,0))
    joint = [[Q(1,3)*entry for entry in row] for row in kernel]
    marginal = [sum(joint[i][j] for i in range(3)) for j in range(3)]
    information = sum(float(joint[i][j])*log(float(joint[i][j]/(Q(1,3)*marginal[j])),3)
                      for i in range(3) for j in range(3) if joint[i][j])
    assert information == pytest.approx(1)
    assert information > log(2,3)
    assert max(sum(bool(entry) for entry in row) for row in kernel) == 1


def test_canonical_contract_does_not_modify_inherited_engine_or_inputs():
    result = a.audit(ROOT)['compaction']
    assert result['frozen_files'] >= 150
    contract = json.loads((ROOT/'evidence/ONTOLOGY_COMPACTION_BINDINGS.json').read_text())
    assert 'manual/scripts/aod_awareness.py' in contract['frozen_sha256']
    assert 'manual/scripts/aod_native_closure_wave.py' in contract['frozen_sha256']
