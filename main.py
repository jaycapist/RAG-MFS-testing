from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

from sync_drive import sync_from_drive
from sync_drive import ensure_rclone_config
from load_pdfs import load_pdfs
from preprocessing import preprocess_documents
from retrievers import build_retrievers, get_retriever_for_query
from llm_model import get_llm
from unified_ask import ask_unified
from printers import print_sources

app = FastAPI()

print("Pipeline Starting")

@app.on_event("startup")
def startup_event():
    ensure_rclone_config()
    sync_from_drive()

docs = load_pdfs()
db, split_docs = preprocess_documents(docs)
bm25, vec, hybrid = build_retrievers(db, split_docs)
llm = get_llm()
print("Pipeline Ready")

class QueryInput(BaseModel):
    query: str

@app.post("/ask")
async def ask_question(data: QueryInput):
    query = data.query
    retr = get_retriever_for_query(query, db, bm25, hybrid)
    result = ask_unified(query, llm, retr)
    return {
        "answer": result.get("answer", ""),
        "sources": [doc.metadata.get("source", "unknown") for doc in result.get("context", [])]
    }

@app.get("/")
async def root():
    return {"status": "Running"}
