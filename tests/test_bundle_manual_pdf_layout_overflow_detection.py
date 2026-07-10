from pathlib import Path
import subprocess, sys
import fitz

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools/validate_manual_pdf_layout.py"

def test_pdf_layout_validator_rejects_text_beyond_page_boundary(tmp_path):
    pdf = tmp_path / "overflow.pdf"
    doc = fitz.open()
    page = doc.new_page(width=300, height=300)
    page.insert_text((295, 100), "overflowing text beyond page", fontsize=12)
    doc.set_metadata({"creationDate": "D:19800101000000Z"})
    doc.save(pdf)
    result = subprocess.run([sys.executable, str(VALIDATOR), str(pdf), "--render-check"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "bounding box exceeds page boundary" in (result.stdout + result.stderr)
