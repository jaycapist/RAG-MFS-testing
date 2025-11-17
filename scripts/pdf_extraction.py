import fitz
import io
import logging
import os
from pathlib import Path
from datetime import datetime

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("pdf_ocr_mvp")

def extract_pdf_pages(pdf_path):
    """Return [{'page': n, 'text': str}] using PyMuPDF only."""
    pages = []
    doc = fitz.open(str(pdf_path))
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""

        if not text.strip():
            blocks = page.get_text("blocks") or []
            block_text = "\n".join(b[4] for b in blocks if b[4].strip())
            if len(block_text) > len(text):
                text = block_text

        if len(text.strip()) < 32:
            words = page.get_text("words") or []
            word_text = " ".join(w[4] for w in words if w[4].strip())
            if len(word_text) > len(text):
                text = word_text

        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages


def tesseract_ocr_fallback(pdf_path, dpi=300):
    """Use Tesseract OCR on scanned PDF by converting pages to images."""
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:
        log.error(f"Tesseract OCR image conversion failed: {e}")
        return ""

    pages = []
    for i, image in enumerate(images):
        try:
            text = pytesseract.image_to_string(image)
        except Exception as e:
            log.warning(f"Tesseract OCR failed on page {i+1}: {e}")
            text = ""
        pages.append({"page": i + 1, "text": text})
    return pages


def extract_text_from_pdf(pdf_path, min_chars_for_ocr=200):
    """Extract text via local PyMuPDF, fallback to Tesseract OCR."""
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file() or pdf_file.stat().st_size == 0:
        log.warning(f"Skipping empty or invalid file: {pdf_path}")
        return "", [], False

    try:
        pages = extract_pdf_pages(pdf_path)
    except Exception as e:
        log.warning(f"Failed to extract text from {pdf_path}: {e}")
        return "", [], False

    all_text = "\n".join(p["text"] for p in pages).strip()

    if len(all_text) >= min_chars_for_ocr:
        return all_text, pages, False

    log.info(f"OCR fallback via Tesseract for {pdf_path} (had {len(all_text)} chars)")
    pages = tesseract_ocr_fallback(pdf_path)
    all_text = "\n".join(p["text"] for p in pages).strip()
    return all_text, pages, True if all_text else False


def test_pdf_extraction(pdf_dir="data/", min_chars_for_ocr=200):
    pdf_dir = Path(pdf_dir)
    pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
    print(f"\n[{datetime.now()}] Found {len(pdf_paths)} PDFs in '{pdf_dir.resolve()}'\n")

    for path in pdf_paths:
        text, pages, used_ocr = extract_text_from_pdf(str(path), min_chars_for_ocr=min_chars_for_ocr)
        total = len(text)
        empties = sum(1 for p in pages if not p["text"].strip())
        label = "TesseractOCR" if used_ocr else "Local"
        print(f"{path.name} | {label} | chars={total} | pages={len(pages)} | empty_pages={empties}")
        sample = next((p for p in pages if p["text"].strip()), None)
        if sample:
            print(f"  preview: {sample['text'][:140]!r}")
        else:
            print("  preview: <empty> (mark as needs_ocr)")
        print("-" * 80)


if __name__ == "__main__":
    test_pdf_extraction("data/", min_chars_for_ocr=200)
