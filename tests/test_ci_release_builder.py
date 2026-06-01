from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workflow_writes_tests_artifact_before_release_builder():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert "pytest -q | tee tests.txt" in workflow
    obsolete_audit_tool = "audit" + "_" + "pack"
    obsolete_verifier_log = "verifier" + ".log"
    assert obsolete_audit_tool not in workflow
    assert obsolete_verifier_log not in workflow
    assert "scripts/build_release_bundle.py --outdir dist --tests tests.txt --main main.pdf --manual manual.pdf" in workflow


def test_release_builder_uses_pytest_when_tests_artifact_is_missing():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    obsolete_audit_tool = "audit" + "_" + "pack"
    obsolete_verifier_log = "verifier" + ".log"
    assert "def resolve_required_artifact" not in script
    assert obsolete_verifier_log not in script
    assert obsolete_audit_tool not in script
    assert "tests_txt = (ROOT / args.tests).resolve()" in script
    assert "def ensure_tests_artifact" in script
    assert "ensure_tests_artifact(tests_txt)" in script
    assert "sys.executable" in script
    assert "pytest" in script
    assert "-q" in script


def test_ci_build_file_names_are_version_free():
    assert (ROOT / ".github" / "workflows" / "build.yml").exists()
    assert (ROOT / "scripts" / "build_release_bundle.py").exists()
    assert not any("v39" in p.name for p in (ROOT / "scripts").glob("*.py"))
