from fastapi import FastAPI
from pydantic import BaseModel
from scripts.retrievers import retrieve_top_k, format_context
from .qa import answer_question

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    k: int = 5

@app.post("/query")
def query_api(request: QueryRequest):
    try:
        results = retrieve_top_k(request.query, request.k)
        context = format_context(results)
        answer = answer_question(context, request.query)
        return {"answer": answer}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
