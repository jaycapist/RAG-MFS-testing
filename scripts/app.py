from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Union
from fastapi.middleware.cors import CORSMiddleware

from retrievers import retrieve, format_context
from qa import answer_question
from printer import format_answer_with_sources_json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.hawaii.edu"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model
class QueryRequest(BaseModel):
    query: str
    k: int = 15
    alpha: float = 0.3
    metadata: Optional[Dict[str, Union[str, int]]] = None

    return_all_chunks: bool = True


# API endpoint
@app.post("/query")
def query_api(request: QueryRequest):
    try:
        # Retrieve docs
        results = retrieve(
            query=request.query,
            k=request.k,
            alpha=request.alpha,
            metadata=request.metadata,
            return_all_chunks=request.return_all_chunks
        )

        # LLM context
        context = format_context(results)

        # Answer
        answer = answer_question(context, request.query)
        return format_answer_with_sources_json(answer, results)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
