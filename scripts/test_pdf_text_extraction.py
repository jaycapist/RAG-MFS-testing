import fitz 
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        return text.strip()
    except Exception as e:
        return f"__ERROR__: {e}"

def test_pdf_extraction(pdf_dir="data/"):
    pdf_dir = Path(pdf_dir)
    pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
    print(f"Found {len(pdf_paths)} PDFs in '{pdf_dir.resolve()}'\n")

    for path in pdf_paths:
        result = extract_text_from_pdf(str(path))

        if result.startswith("__ERROR__"):
            print(f"{path.name} - Error: {result[10:]}")
        elif len(result) == 0:
            print(f"{path.name} - No text extracted")
        else:
            print(f"{path.name} - Extracted {len(result)} characters")
            print(f"    Preview: {result[:100]!r}")
        print("-" * 80)

if __name__ == "__main__":
    test_pdf_extraction("data/")
