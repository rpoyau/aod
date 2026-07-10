#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def resolve_pdf(path: Path) -> Path:
    return path / "manual-2.pdf" if path.is_dir() else path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_or_root", type=Path)
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--min-pages", type=int, default=1)
    ap.add_argument("--render-check", action="store_true", help="Render all pages with PyMuPDF at low resolution.")
    args = ap.parse_args()
    pdf = resolve_pdf(args.pdf_or_root)
    if not pdf.is_file():
        if args.allow_missing:
            print(json.dumps({"status": "skipped_missing_pdf", "pdf": str(pdf)}, sort_keys=True))
            return
        raise SystemExit(f"missing pdf: {pdf}")
    if pdf.stat().st_size <= 0:
        raise SystemExit("PDF is empty")

    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - environment guard
        raise SystemExit(f"pypdf unavailable: {exc}")

    reader = PdfReader(str(pdf))
    page_count = len(reader.pages)
    if page_count < args.min_pages:
        raise SystemExit(f"PDF page count too small: {page_count} < {args.min_pages}")
    meta = reader.metadata or {}
    creation = getattr(meta, "creation_date", None) or meta.get("/CreationDate")
    raw_creation = str(meta.get("/CreationDate", ""))
    if raw_creation and "19800101000000" not in raw_creation:
        raise SystemExit(f"non-deterministic CreationDate: {raw_creation}")

    rendered_pages = 0
    bbox_violations = []
    if args.render_check:
        try:
            import fitz  # PyMuPDF
        except Exception as exc:  # pragma: no cover - environment guard
            raise SystemExit(f"PyMuPDF unavailable for render check: {exc}")
        doc = fitz.open(str(pdf))
        if doc.page_count != page_count:
            raise SystemExit("page count mismatch between render and PDF readers")
        matrix = fitz.Matrix(0.35, 0.35)
        for page in doc:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            if pix.width <= 0 or pix.height <= 0:
                raise SystemExit(f"rendered page has invalid size: {page.number + 1}")
            page_rect = page.rect
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        x0, y0, x1, y1 = span.get("bbox", (0, 0, 0, 0))
                        if x0 < page_rect.x0 - 0.1 or y0 < page_rect.y0 - 0.1 or x1 > page_rect.x1 + 0.1 or y1 > page_rect.y1 + 0.1:
                            bbox_violations.append({"page": page.number + 1, "bbox": [x0, y0, x1, y1], "text": span.get("text", "")[:80]})
            rendered_pages += 1
        if bbox_violations:
            raise SystemExit("PDF text bounding box exceeds page boundary: " + json.dumps(bbox_violations[:10], sort_keys=True))

    print(json.dumps({
        "status": "passed",
        "validator": "manual_pdf_layout",
        "pdf": str(pdf),
        "byte_count": pdf.stat().st_size,
        "page_count": page_count,
        "creation_date": raw_creation,
        "rendered_pages": rendered_pages,
        "bbox_violations": bbox_violations,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
