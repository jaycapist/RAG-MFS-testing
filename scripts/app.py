from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from scripts.retrievers import retrieve, format_context
from scripts.qa import answer_question
from scripts.printer import format_answer_with_sources_json
from scripts.helpers import extract_filters

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

# API endpoint
@app.post("/query")
def query_api(request: QueryRequest):
    try:
        K = 15
        ALPHA = 0.30
        RETURN_ALL_CHUNKS = True

        metadata = extract_filters(request.query)

        results = retrieve(
            query=request.query,
            k=K,
            alpha=ALPHA,
            metadata=metadata,
            return_all_chunks=RETURN_ALL_CHUNKS
        )

        context = format_context(results)
        answer = answer_question(context, request.query)

        return format_answer_with_sources_json(answer, results)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}