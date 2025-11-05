from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from scripts.retrievers import retrieve, format_context  # use the improved retriever
from .qa import answer_question

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.hawaii.edu"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define incoming request model
class QueryRequest(BaseModel):
    query: str
    k: int = 5
    alpha: float = 0.5  # vector <---> BM25
    use_mmr: bool = False
    lambda_param: float = 0.5

@app.post("/query")
def query_api(request: QueryRequest):
    try:
        results = retrieve(
            query=request.query,
            k=request.k,
            alpha=request.alpha,
            use_mmr=request.use_mmr,
            lambda_param=request.lambda_param
        )
        context = format_context(results)
        answer = answer_question(context, request.query)
        return {
            "answer": answer,
            "documents": [r.payload.get("text", "") for r in results]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
