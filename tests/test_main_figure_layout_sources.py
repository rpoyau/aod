from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_fractal_tesseract_figure_regenerator_exists():
    script = ROOT / "scripts" / "generate_fractal_tesseract_q4_witness.py"
    assert script.exists()
    text = script.read_text(encoding="utf-8")
    assert "fractal_tesseract_q4_witness.jpg" in text
    assert "branch / hinge / branch support can cut again" in text
    assert "local witness of fractal tesseract support" in text
