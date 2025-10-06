from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

from sync_drive import sync_from_drive, ensure_rclone_config
from load_pdfs import load_pdfs
from preprocessing import preprocess_documents
from retrievers import build_retrievers, get_retriever_for_query
from llm_model import get_llm
from unified_ask import ask_unified

# Move shared state into a dictionary
state = {}

class QueryInput(BaseModel):
    query: str

def create_app():
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

        # Store in app state or global var
        state["db"] = db
        state["bm25"] = bm25
        state["vec"] = vec
        state["hybrid"] = hybrid
        state["llm"] = llm

        print("Pipeline Ready")

    @app.post("/ask")
    async def ask_question(data: QueryInput):
        retr = get_retriever_for_query(data.query, state["db"], state["bm25"], state["hybrid"])
        result = ask_unified(data.query, state["llm"], retr)
        return {
            "answer": result.get("answer", ""),
            "sources": [doc.metadata.get("source", "unknown") for doc in result.get("context", [])]
        }

    @app.get("/")
    async def root():
        return {"status": "Running"}

    return app

app = create_app()