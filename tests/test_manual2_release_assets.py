from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_release_builder_includes_manual2_as_first_class_asset():
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text(encoding="utf-8")
    assert '"manual-2"' in builder
    assert 'ap.add_argument("--manual2", default="manual-2.pdf")' in builder
    assert 'manual2_out = outdir / "manual-2.pdf"' in builder
    assert 'shutil.copy2(manual2_out, bundle_tmp / "manual-2.pdf")' in builder
    assert builder.index('"main.pdf"') < builder.index('"manual.pdf"') < builder.index('"manual-2.pdf"') < builder.index('"source.zip"')


def test_ci_builds_and_uploads_manual2_pdf():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    assert "Build Manual II Fractal Fusion Scales" in workflow
    assert "latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual-2/main.tex" in workflow
    assert "cp manual-2/main.pdf manual-2.pdf" in workflow
    assert "--manual2 manual-2.pdf" in workflow
    assert "dist/manual-2.pdf" in workflow
    assert "dist/MANUAL_II_ROADMAP.md" in workflow


def test_readme_and_zenodo_expose_fractal_fusion_scales():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert "Fractal Fusion Scales" in readme
    assert "manual-2.pdf" in readme
    assert "Fractal Fusion Scales" in zenodo["description"]
    assert "Manual II" in zenodo["description"]
    assert "manual-2.pdf" in zenodo.get("notes", "")
    assert any("RDKit" in r for r in zenodo["references"])


def test_reference_sync_script_uses_manual2_bib():
    script = (ROOT / "scripts" / "sync_zenodo_references.py").read_text(encoding="utf-8")
    assert 'ROOT / "manual-2" / "refs.bib"' in script
    assert "manual-2/refs.bib" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "manual-2/refs.bib" in (ROOT / "BUILD.md").read_text(encoding="utf-8")


def test_release_builder_includes_manual_ii_roadmap_asset():
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text(encoding="utf-8")
    assert "MANUAL_II_ROADMAP.md" in builder
    assert 'ap.add_argument("--roadmap", default="MANUAL_II_ROADMAP.md")' in builder
    assert 'roadmap_out = outdir / "MANUAL_II_ROADMAP.md"' in builder
    bundle_section = builder.split("bundle_order =", 1)[1]
    assert bundle_section.index('"manual-2.pdf"') < bundle_section.index('"MANUAL_II_ROADMAP.md"') < bundle_section.index('"source.zip"')
    assert 'bundle_versioned_zip = outdir / f"bundle-{version}.zip"' in builder
    assert "bundle.zip" in builder


def test_release_builder_includes_manual_artifact_baseline_manifest():
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    baseline = ROOT / "MANUAL_ARTIFACT_BASELINES_SHA256.txt"
    assert baseline.is_file()
    text = baseline.read_text(encoding="utf-8")
    assert "75bdaf7537abedb98ce27938afc25f37c2cc693be1ab43c23f7f4e1e7af482d9" in text
    assert "MANUAL_ARTIFACT_BASELINES_SHA256.txt" in builder
    assert "dist/MANUAL_ARTIFACT_BASELINES_SHA256.txt" in workflow
