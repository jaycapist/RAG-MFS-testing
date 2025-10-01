from pathlib import Path
from tqdm import tqdm
from langchain.document_loaders import PyPDFLoader
import time, logging, warnings, contextlib, io
from helpers import add_year_metadata_consistent

def load_pdfs(pdf_dir="data/"):
    try:
        from pypdf.errors import PdfReadWarning
        warnings.filterwarnings("ignore", category=PdfReadWarning)
    except Exception:
        pass
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    pdf_dir = Path(pdf_dir)
    pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
    print(f"Scanning {len(pdf_paths)} PDFs in {pdf_dir.resolve()} ...")

    docs = []
    for p in tqdm(pdf_paths, desc="Loading PDFs", unit="file"):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                loader = PyPDFLoader(str(p))
                docs.extend(loader.load())
        except Exception as e:
            print(f":warning: Skipped {p.name}: {e}")

    add_year_metadata_consistent(docs)
    print("Added 'year' metadata.")
    return docs