"""Current scientific contracts cannot release unrelated conservation duties."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "contracts/scientific/CANONICAL_BINDINGS.json"
spec = importlib.util.spec_from_file_location(
    "m25_conservation_audit", ROOT / "scripts/audit_scientific_sources.py"
)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


@pytest.fixture(scope="module")
def source_template(tmp_path_factory):
    """Copy the scientific validation inputs, also from an unpacked source ZIP."""
    result = tmp_path_factory.mktemp("conservation-source")
    contract = json.loads((ROOT / CONTRACT).read_text())
    # This inventory is independent of Git and excludes generated build files.
    paths = set(contract["frozen_sha256"])
    for surface in ("main", "manual"):
        paths.update(audit.include_graph(ROOT, surface)[0])
    for folder, pattern in [("contracts/scientific", "*"), ("scripts", "*.py"),
                            ("tests", "*.py")]:
        paths.update(p.relative_to(ROOT).as_posix()
                     for p in (ROOT / folder).glob(pattern) if p.is_file())
    for relative in sorted(paths):
        destination = result / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    # Rejected mutants are meaningful only if their unchanged source passes.
    assert audit.audit(result)["compaction"]["canonical_equations"] == 81
    assert not (result / ".git").exists()
    return result


@pytest.fixture
def source(source_template, tmp_path):
    return Path(shutil.copytree(source_template, tmp_path / "source"))


def test_current_contract_preserves_canonical_and_supplemental_obligations(source):
    current = json.loads((source / CONTRACT).read_text())
    assert len(current["ownership"]) == 44
    assert len(current["formulas"]) == 81
    assert sum(len(r["depends_on"]) for r in current["ownership"]) == 72
    assert set(current["supplemental_formulas"]) == {
        "eq:hinge-saturation-weighted", "eq:temporal-sadar-burden",
        "eq:entropic-duon-current", "eq:hinge-positive-support",
        "eq:operative-source-removal",
    }
    # The independent contract digest binds the complete reviewed inventory.
    # Its size may change when authoring-only tests move out of this package.
    assert {"manual/scripts/aod_native_closure_wave.py",
            "manual/scripts/aod_awareness.py",
            "tests/test_native_closure_wave.py"} <= set(current["frozen_sha256"])
    for path, wanted in current["frozen_sha256"].items():
        assert hashlib.sha256((source / path).read_bytes()).hexdigest() == wanted


def test_unrelated_canonical_formula_mutation_is_rejected(source):
    label = "eq:odd-support-index"
    block = audit.equations(source)[label]
    changed = block.replace(r'2\ell+1', r'2\ell+3', 1)
    assert changed != block
    path = source / audit.label_map(source)[label]["path"]
    path.write_text(path.read_text().replace(block, changed, 1))
    with pytest.raises(ValueError, match="canonical mathematical statement changed " + label):
        audit.audit(source)


@pytest.mark.parametrize("path", [
    "manual/scripts/aod_native_closure_wave.py",
    "tests/test_native_closure_wave.py",
    "tests/test_active_scientific_sources.py",
])
def test_unrelated_protected_byte_mutation_is_rejected(source, path):
    target = source / path
    target.write_bytes(target.read_bytes() + b'\n# Unbound byte mutation.\n')
    with pytest.raises(ValueError, match="protected source changed"):
        audit.audit(source)


def test_current_binding_bytes_cannot_be_rewritten(source):
    path = source / CONTRACT
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match="scientific contract integrity changed"):
        audit.audit(source)


def test_unrelated_contract_field_cannot_be_rebound(source):
    path = source / CONTRACT
    contract = json.loads(path.read_text())
    del contract["frozen_sha256"]["manual/scripts/aod_native_closure_wave.py"]
    path.write_text(json.dumps(contract, indent=2) + "\n")
    with pytest.raises(ValueError, match="scientific contract integrity changed"):
        audit.audit(source)


def test_contract_cannot_authorize_its_own_source_mutation(source):
    target = source / "manual/scripts/aod_native_closure_wave.py"
    target.write_bytes(target.read_bytes() + b'\n# Unbound source mutation.\n')
    path = source / CONTRACT
    contract = json.loads(path.read_text())
    contract["frozen_sha256"][target.relative_to(source).as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(contract, indent=2) + "\n")
    with pytest.raises(ValueError, match="scientific contract integrity changed"):
        audit.audit(source)


def test_contract_cannot_authorize_its_own_formula_mutation(source):
    label = "eq:odd-support-index"
    block = audit.equations(source)[label]
    changed = block.replace(r'2\ell+1', r'2\ell+3', 1)
    path = source / audit.label_map(source)[label]["path"]
    path.write_text(path.read_text().replace(block, changed, 1))
    path = source / CONTRACT
    contract = json.loads(path.read_text())
    contract["formulas"][label] = contract["formulas"][label].replace(r'2\ell+1', r'2\ell+3', 1)
    path.write_text(json.dumps(contract, indent=2) + "\n")
    with pytest.raises(ValueError, match="scientific contract integrity changed"):
        audit.audit(source)


def test_supplemental_formula_removal_is_rejected(source):
    label = "eq:hinge-positive-support"
    block = audit.equations(source)[label]
    path = source / audit.label_map(source)[label]["path"]
    path.write_text(path.read_text().replace(block, r'\label{' + label + "}", 1))
    with pytest.raises(ValueError, match="supplemental mathematical statement or owner changed " + label):
        audit.audit(source)


def test_fixture_input_mutation_is_rejected(source):
    path = source / "manual/data/m2/awareness_cases.jsonl"
    rows = path.read_text().splitlines()
    row = json.loads(rows[0]);row["fixture_id"] += "-changed"
    rows[0] = json.dumps(row)
    path.write_text("\n".join(rows) + "\n")
    with pytest.raises(ValueError, match="immutable fixture file changed"):
        audit.audit(source)
