from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workflow_writes_tests_artifact_before_release_builder():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert ": > tests.txt" in workflow
    assert "pytest -q | tee -a tests.txt" in workflow
    assert "verify_examples_sympy.py" in workflow
    assert "tee verifier.log | tee -a tests.txt" in workflow
    assert "scripts/build_release_bundle.py --outdir dist --tests tests.txt --main main.pdf --manual manual.pdf" in workflow


def test_release_builder_accepts_verifier_log_as_tests_fallback():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    assert "def resolve_required_artifact" in script
    assert '"verifier.log"' in script
    assert '"audit_pack/verifier.log"' in script
    assert "tests_txt = resolve_required_artifact" in script


def test_ci_build_file_names_are_version_free():
    assert (ROOT / ".github" / "workflows" / "build.yml").exists()
    assert (ROOT / "scripts" / "build_release_bundle.py").exists()
    assert not any("v39" in p.name for p in (ROOT / "scripts").glob("*.py"))
