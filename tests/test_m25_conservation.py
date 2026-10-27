"""M2.5 successors cannot release unrelated historical conservation duties."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "m25_conservation_audit", ROOT / "scripts/audit_scientific_sources.py"
)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


@pytest.fixture(scope="module")
def source_template(tmp_path_factory):
    """Copy the source inventory, including pending M2.5 evidence, without builds."""
    result = tmp_path_factory.mktemp("m25-conservation-source")
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    ).stdout.decode().split("\0")
    paths = {Path(name) for name in tracked if name}
    # These files may be untracked while the milestone's final commit is prepared.
    paths.update(p.relative_to(ROOT) for p in (ROOT / "evidence/m25").glob("*.json"))
    paths.update(p.relative_to(ROOT) for p in (ROOT / "tests").glob("test_m25*.py"))
    for relative in sorted(paths):
        destination = result / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    # A rejected mutant is useful only when its otherwise identical source passes.
    assert audit.audit(result)["compaction"]["canonical_equations"] == 81
    return result


@pytest.fixture
def source(source_template, tmp_path):
    return Path(shutil.copytree(source_template, tmp_path / "source"))


def test_m25_successor_advances_only_the_reviewed_formulas_and_test_bytes(source):
    baseline = json.loads(
        (source / "evidence/m25/ONTOLOGY_COMPACTION_BINDINGS.baseline.json").read_text()
    )
    current = json.loads((source / "evidence/ONTOLOGY_COMPACTION_BINDINGS.json").read_text())
    successor = json.loads((source / "evidence/m25/BINDING_SUCCESSOR.json").read_text())
    changed = {
        label for label, formula in baseline["formulas"].items()
        if current["formulas"][label] != formula
    }
    assert changed == {
        "eq:awareness-state-factorization", "eq:retained-rebalancing",
        "eq:awareness-active", "eq:awareness-operative-set", "eq:operative-self",
    }
    assert {k: v for k, v in current.items() if k != "formulas"} == {
        k: v for k, v in baseline.items() if k != "formulas"
    }
    for path, change in successor["test_changes"].items():
        assert hashlib.sha256(change["old"].encode()).hexdigest() == change["old_sha256"]
        assert hashlib.sha256(change["new"].encode()).hexdigest() == change["new_sha256"]
        assert (source / path).read_bytes() == change["new"].encode()
        assert change["frozen"] == (path in baseline["frozen_sha256"])


def test_unrelated_canonical_formula_mutation_is_rejected(source):
    label = "eq:odd-support-index"
    block = audit.equations(source)[label]
    changed = block.replace(r"2\ell+1", r"2\ell+3", 1)
    assert changed != block
    path = source / audit.label_map(source)[label]["path"]
    path.write_text(path.read_text().replace(block, changed, 1))
    with pytest.raises(ValueError, match="canonical mathematical statement changed " + label):
        audit.audit(source)


@pytest.mark.parametrize("path, message", [
    ("manual/scripts/aod_native_closure_wave.py", "protected engine, input, test or presentation changed"),
    ("tests/test_native_closure_wave.py", "protected engine, input, test or presentation changed"),
    ("tests/test_active_scientific_sources.py", "protected M2.5 test changed"),
])
def test_unrelated_protected_byte_mutation_is_rejected(source, path, message):
    target = source / path
    target.write_bytes(target.read_bytes() + b"\n# Unreviewed byte mutation.\n")
    with pytest.raises(ValueError, match=message):
        audit.audit(source)


def test_baseline_binding_bytes_cannot_be_rewritten(source):
    path = source / "evidence/m25/ONTOLOGY_COMPACTION_BINDINGS.baseline.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="M2.5 baseline binding changed"):
        audit.audit(source)


def test_unrelated_contract_field_cannot_be_rebound(source):
    path = source / "evidence/ONTOLOGY_COMPACTION_BINDINGS.json"
    contract = json.loads(path.read_text())
    # Attempt to release an unrelated engine from the frozen-file obligations.
    del contract["frozen_sha256"]["manual/scripts/aod_native_closure_wave.py"]
    path.write_text(json.dumps(contract, indent=2) + "\n")
    with pytest.raises(ValueError, match="unrelated M2.5 contract change"):
        audit.audit(source)


def test_successor_cannot_authorize_itself_after_an_unreviewed_change(source):
    path = source / "evidence/m25/BINDING_SUCCESSOR.json"
    successor = json.loads(path.read_text())
    successor["formula_changes"]["eq:operative-self"]["new"] += r"\quad 0=1"
    path.write_text(json.dumps(successor, indent=2) + "\n")
    with pytest.raises(ValueError, match="unreviewed M2.5 successor binding"):
        audit.audit(source)
