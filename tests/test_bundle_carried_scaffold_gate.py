import json
import subprocess
import sys
from pathlib import Path


def test_carried_scaffold_lock_is_present_and_exact():
    lock = json.loads(Path('governance/CARRIED_SCAFFOLD_LOCK.json').read_text())
    assert lock['lock_id'] == 'AOD_CARRIED_SCAFFOLD_LOCK_v1'
    assert 'README.md' in lock['files']
    assert 'RELEASE_READINESS.txt' in lock['files']
    assert 'MANUAL_II_ROADMAP.md' in lock['files']
    assert 'External PDB Alignment Rule Freeze' in lock['files']['MANUAL_II_ROADMAP.md']
    assert 'shared Section 1--2 source is carried forward unchanged' in lock['files']['RELEASE_READINESS.txt']


def test_carried_scaffold_validator_passes():
    result = subprocess.run([sys.executable, 'tools/validate_carried_scaffolds.py', '.'], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
