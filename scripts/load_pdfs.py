import fitz
from pathlib import Path
from tqdm import tqdm
from langchain_core.documents import Document
from helpers import add_year_metadata_consistent

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)

def load_pdfs(pdf_dir="data/"):
    pdf_dir = Path(pdf_dir)
    pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
    print(f"Scanning {len(pdf_paths)} PDFs in {pdf_dir.resolve()} ...")

    docs = []
    for path in tqdm(pdf_paths, desc="Loading PDFs", unit="file"):
        try:
            content = extract_text_from_pdf(str(path)).strip()
            if content:
                doc = Document(
                    page_content=content,
                    metadata={"source": str(path)}
                )
                docs.append(doc)
            else:
                print(f"Skipped {path.name} (empty)")
        except Exception as e:
            print(f"Skipped {path.name}: {e}")

    add_year_metadata_consistent(docs)
    print(f"Added 'year' metadata to {len(docs)} documents.")
    return docs
