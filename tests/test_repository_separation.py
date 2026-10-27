"""Current scientific specifications have a complete, explicit local inventory."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('separation_source_audit', ROOT / 'scripts/audit_scientific_sources.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture
def contract_root(tmp_path):
    shutil.copytree(ROOT / 'contracts', tmp_path / 'contracts')
    # Establish the positive result before each disposable mutation; no Git,
    # historical evidence, private project archive or external access is needed.
    assert len(audit.validate_contract_inventory(tmp_path)) == 5
    return tmp_path


def test_complete_current_scientific_inventory_is_local():
    records = audit.validate_contract_inventory(ROOT)
    assert set(records) == {
        'CANONICAL_BINDINGS.json', 'OWNERSHIP_AND_FIXTURES.json',
        'AWARENESS_ACTIVE_CAUSAL_SPEC.json', 'OPERATIVE_SELF_SCHEMA.json',
        'ROUND_TRIP_PHASE_FACTOR_SPEC.json',
    }


@pytest.mark.parametrize('schema', ['aod.scientific.future.v1', 'unrecognized.future-schema'])
def test_unregistered_contract_is_rejected_regardless_of_schema(contract_root, schema):
    path = contract_root / 'contracts/scientific/UNREGISTERED.json'
    path.write_text(json.dumps({'schema': schema, 'claim': 'unauthorized assertion'}))
    with pytest.raises(ValueError, match='Scientific contract inventory mismatch.*unregistered'):
        audit.validate_contract_inventory(contract_root)


def test_registered_name_requires_its_exact_specification_schema(contract_root):
    path = contract_root / 'contracts/scientific/AWARENESS_ACTIVE_CAUSAL_SPEC.json'
    record = json.loads(path.read_text())
    record['schema'] = 'unrecognized.future-schema'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='Scientific contract schema mismatch'):
        audit.validate_contract_inventory(contract_root)


def test_missing_contract_cannot_evade_completeness(contract_root):
    (contract_root / 'contracts/scientific/OPERATIVE_SELF_SCHEMA.json').unlink()
    with pytest.raises(ValueError, match='Scientific contract inventory mismatch.*missing'):
        audit.validate_contract_inventory(contract_root)


def test_run_report_is_not_an_active_scientific_specification(contract_root):
    # Protocol classification only: report content validation is separately
    # exercised against real CLI execution by test_m25_report_schema.py.
    report = {'schema': 'aod.fixture-run-report.v1', 'runner': 'manual/scripts/aod_awareness.py',
              'runner_output': {'source_sha256': '0' * 64, 'results': []}}
    (contract_root / 'transient-report.json').write_text(json.dumps(report))
    assert len(audit.validate_contract_inventory(contract_root)) == 5
    path = contract_root / 'contracts/scientific/AWARENESS_ACTIVE_CAUSAL_SPEC.json'
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='Scientific contract schema mismatch'):
        audit.validate_contract_inventory(contract_root)


@pytest.mark.parametrize('with_known_fields', [False, True])
def test_unknown_scientific_spec_outside_inventory_is_rejected(contract_root, with_known_fields):
    record = {'schema': 'unrecognized.future-schema'}
    if with_known_fields:
        record['source_anchors'] = ['eq:awareness-active']
    # Both the scientific filename and known binding fields identify an
    # unregistered authority, even if its schema is not on the allowlist.
    name = 'unknown.json' if with_known_fields else 'UNREGISTERED_SPEC.json'
    (contract_root / name).write_text(json.dumps(record))
    with pytest.raises(ValueError, match='Unregistered scientific specification'):
        audit.validate_contract_inventory(contract_root)


@pytest.mark.parametrize('suffix', ['_SPEC.json', '_SCHEMA.json'])
@pytest.mark.parametrize('record', [
    [{'schema': 'aod.scientific.unknown.v1', 'operative_source': 'unbound.py'}],
    'unrecognized specification', 1, True, None,
], ids=['list', 'string', 'number', 'boolean', 'null'])
def test_unregistered_scientific_filename_rejects_nonobject_json(contract_root, suffix, record):
    (contract_root / ('UNREGISTERED' + suffix)).write_text(json.dumps(record))
    with pytest.raises(ValueError, match='Unregistered scientific specification'):
        audit.validate_contract_inventory(contract_root)


def test_contract_symlink_is_not_local_authority(contract_root):
    path = contract_root / 'contracts/scientific/OPERATIVE_SELF_SCHEMA.json'
    content = path.read_bytes()
    target = contract_root / 'outside-copy.json'
    target.write_bytes(content)
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(ValueError, match='Scientific contracts cannot be symlinks'):
        audit.validate_contract_inventory(contract_root)
