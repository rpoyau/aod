import json
import subprocess
import sys
from pathlib import Path


def test_release_metadata_state_drives_surfaces_and_manual2_hash():
    state = json.loads(Path('governance/RELEASE_METADATA_STATE.json').read_text())
    version = state['candidate_version']
    manual2_hash = state['manual2_source_tree_hash']
    for rel in ['README.md','CANONICAL_VERSION.txt','RELEASE_READINESS.txt','MANUAL_I_ROADMAP.md','MANUAL_II_ROADMAP.md']:
        assert version in Path(rel).read_text()
    assert f'Manual-II source-tree hash: {manual2_hash}' in Path('CANONICAL_VERSION.txt').read_text()
    assert 'This package opens the v40.03r25.1 AUTHORING lane' not in Path('README.md').read_text()
    assert json.loads(Path('.zenodo.json').read_text())['version'] == version


def test_surface_synchronization_tool_passes_source_root():
    result = subprocess.run([sys.executable, 'tools/validate_surface_synchronization.py', '.'], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def _load_surface_validator_module():
    import importlib.util
    module_path = Path('tools/validate_surface_synchronization.py').resolve()
    spec = importlib.util.spec_from_file_location('surface_sync_validator_under_test', module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_phase_fixture(root: Path, phase: str, workflow_state: str):
    (root / 'cycle').mkdir(parents=True, exist_ok=True)
    (root / 'cycle/CYCLE_STATE.json').write_text(json.dumps({
        'active_phase': phase,
        'release': {'target_version': 'v40.04r03'}
    }), encoding='utf-8')
    (root / 'BUNDLE_WORKFLOW.md').write_text(
        '<!-- AOD_STATE_BEGIN -->\n'
        f'Current state: {workflow_state}.\n'
        'Candidate version: v40.04r03.\n'
        '<!-- AOD_STATE_END -->\n',
        encoding='utf-8'
    )


def test_phase_aware_workflow_surface_accepts_review_instance_and_authoring_source(tmp_path):
    module = _load_surface_validator_module()
    bundle = tmp_path / 'bundle'
    source = tmp_path / 'source'
    _write_phase_fixture(bundle, 'REVIEW', 'REVIEW')
    _write_phase_fixture(source, 'AUTHORING', 'AUTHORING')
    assert module.check_workflow_phase_surfaces(bundle, source) == []


def test_phase_aware_workflow_surface_requires_authoring_byte_identity(tmp_path):
    module = _load_surface_validator_module()
    bundle = tmp_path / 'bundle'
    source = tmp_path / 'source'
    _write_phase_fixture(bundle, 'AUTHORING', 'AUTHORING')
    _write_phase_fixture(source, 'AUTHORING', 'AUTHORING')
    (bundle / 'BUNDLE_WORKFLOW.md').write_text(
        (bundle / 'BUNDLE_WORKFLOW.md').read_text() + '\nextra instance text\n',
        encoding='utf-8'
    )
    errors = module.check_workflow_phase_surfaces(bundle, source)
    assert 'root/source duplicate mismatch: BUNDLE_WORKFLOW.md' in errors
