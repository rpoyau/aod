import subprocess
import sys
from pathlib import Path


def test_manual_pdf_layout_tool_is_available():
    tool = Path('tools/validate_manual_pdf_layout.py')
    assert tool.is_file()
    text = tool.read_text()
    assert 'manual_pdf_layout' in text
    assert 'page_count' in text


def test_manual_pdf_layout_tool_accepts_source_tree_missing_pdf_when_allowed(tmp_path: Path):
    result = subprocess.run([sys.executable, 'tools/validate_manual_pdf_layout.py', str(tmp_path), '--allow-missing'], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
