from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workflow_writes_tests_artifact_before_release_builder():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert "python3 -m pytest -q | tee tests.txt" in workflow
    obsolete_audit_tool = "audit" + "_" + "pack"
    obsolete_verifier_log = "verifier" + ".log"
    assert obsolete_audit_tool not in workflow
    assert obsolete_verifier_log not in workflow
    assert "scripts/build_release_bundle.py --outdir dist --tests tests.txt --main main.pdf --manual manual.pdf" in workflow


def test_release_builder_requires_existing_tests_artifact():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    obsolete_audit_tool = "audit" + "_" + "pack"
    obsolete_verifier_log = "verifier" + ".log"
    assert "def resolve_required_artifact" not in script
    assert obsolete_verifier_log not in script
    assert obsolete_audit_tool not in script
    assert "tests_txt = (ROOT / args.tests).resolve()" in script
    assert "def require_tests_artifact" in script
    assert "require_tests_artifact(tests_txt)" in script
    assert "required test artifact missing or empty" in script
    assert "subprocess.run" not in script
    assert "-m pytest" not in script


def test_ci_build_file_names_are_version_free():
    assert (ROOT / ".github" / "workflows" / "build.yml").exists()
    assert (ROOT / "scripts" / "build_release_bundle.py").exists()
    assert not any("v39" in p.name for p in (ROOT / "scripts").glob("*.py"))



def test_workflow_has_no_legacy_verifier_or_audit_pack_steps():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert "Run verifier" not in workflow
    assert "verify_examples_sympy" not in workflow
    assert "audit_pack" not in workflow
    assert "python3 -m pytest -q | tee tests.txt" in workflow
    assert "test -s tests.txt" in workflow


def test_root_build_yml_mirrors_ci_workflow_when_present():
    root_workflow = ROOT / "build.yml"
    if root_workflow.exists():
        text = root_workflow.read_text()
        assert "Run verifier" not in text
        assert "audit_pack" not in text
        assert "verify_examples_sympy" not in text
        assert "python3 -m pytest -q | tee tests.txt" in text


def test_release_builder_includes_root_workflow_mirror():
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    assert "\"build.yml\"" in builder

def test_release_builder_legacy_bare_call_builds_source_clean_only():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    assert "def build_source_only" in script
    assert "source-clean.zip" in script
    assert "if len(sys.argv) == 1" in script
    assert "full release bundles still require" in script


def test_workflows_do_not_use_legacy_bare_builder_call():
    for rel in [Path(".github/workflows/build.yml"), Path("build.yml")]:
        text = (ROOT / rel).read_text()
        assert "python3 scripts/build_release_bundle.py\n" not in text
        assert "Run verifier" not in text
        assert "audit_pack" not in text
        assert "verify_examples_sympy" not in text
        assert "python3 -m pytest -q | tee tests.txt" in text
