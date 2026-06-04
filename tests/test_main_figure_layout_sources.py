from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def test_null_four_edge_labels_are_offset_from_topology():
    script = read("scripts/generate_null_four_edge.py")
    assert "Keep labels outside the topology lanes" in script
    assert "(0.00,-0.55)" in script
    assert "(-0.47,0.02)" in script
    assert "fontsize=8.3" in script

def test_fractal_tesseract_figure_regenerator_exists():
    script = ROOT / "scripts" / "generate_fractal_tesseract_q4_witness.py"
    assert script.exists()
    text = script.read_text(encoding="utf-8")
    assert "fractal_tesseract_q4_witness.jpg" in text
    assert "branch / hinge / branch support can cut again" in text
    assert "local witness of fractal tesseract support" in text

def test_field_count_figure_uses_smaller_topology_nodes():
    script = read("scripts/generate_field_count_sadar_scope.py")
    assert "0.26, edgecolor=blue" in script
    assert "0.86, 0.86" in script

def test_curling_curl_arrow_labels_have_white_backing():
    script = read("scripts/generate_curl_support_figures.py")
    assert "bbox=dict(facecolor='white'" in script
