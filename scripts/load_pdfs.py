import fitz
from pathlib import Path
from tqdm import tqdm
from langchain_core.documents import Document
from helpers import add_year_metadata_consistent
from scripts.pdf_extraction import extract_text_from_pdf
import json
GDRIVE_MAP_PATH = "scripts/gdrive_map.json"

if Path(GDRIVE_MAP_PATH).exists():
    with open(GDRIVE_MAP_PATH) as f:
        gdrive_map = json.load(f)
else:
    gdrive_map = {}

def get_drive_link(filename):
    file_id = gdrive_map.get(filename)
    if file_id:
        return f"https://drive.google.com/file/d/{file_id}/view"
    return None
    
def load_pdfs(pdf_dir="data/"):
    pdf_dir = Path(pdf_dir)
    pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
    print(f"Scanning {len(pdf_paths)} PDFs in {pdf_dir.resolve()} ...")

    docs = []
    for path in tqdm(pdf_paths, desc="Loading PDFs", unit="file"):
        try:
            text, pages, used_ocr = extract_text_from_pdf(str(path))
            content = text.strip()
            if content:
                filename = path.name
                metadata = {
                    "source": filename,
                    "link": get_drive_link(filename)
                }
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                docs.append(doc)
            else:
                print(f"Skipped {path.name} (empty)")
        except Exception as e:
            print(f"Skipped {path.name}: {e}")

    add_year_metadata_consistent(docs)
    print(f"Added 'year' metadata to {len(docs)} documents.")
    return docs
