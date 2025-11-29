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


def ocr_fallback(pdf_path, dpi=300):
    """Use Tesseract OCR on scanned PDFs converted to images."""
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:
        log.error(f"Image conversion failed: {e}")
        return ""

    pages = []
    for i, image in enumerate(images):
        try:
            text = pytesseract.image_to_string(image)
        except Exception as e:
            log.warning(f"OCR failed on page {i+1}: {e}")
            text = ""
        pages.append({"page": i + 1, "text": text})
    return pages


def extract_text(pdf_path, min_chars_for_ocr=200):
    """Extract text, fallback to OCR."""
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file() or pdf_file.stat().st_size == 0:
        log.warning(f"Skipping empty or invalid file: {pdf_path}")
        return "", [], False

    try:
        pages = extract_pdf_pages(pdf_path)
    except Exception as e:
        log.warning(f"Failed to extract text : {pdf_path} : {e}")
        return "", [], False

    all_text = "\n".join(p["text"] for p in pages).strip()

    if len(all_text) >= min_chars_for_ocr:
        return all_text, pages, False

    log.info(f"OCR fallback: {pdf_path} (had {len(all_text)} chars)")
    pages = ocr_fallback(pdf_path)
    all_text = "\n".join(p["text"] for p in pages).strip()
    return all_text, pages, True if all_text else False
