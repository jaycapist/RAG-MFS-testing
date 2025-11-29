import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini") # default
client = OpenAI()

RAG_PROMPT_TEMPLATE = """You are an expert assistant analyzing documents from the Mānoa Faculty Senate.

Use ONLY the context below to answer the user's question. Be as specific and accurate as possible.

If the context gives a partial answer, summarize what is available.
If the context gives no answer, say: "There was no relevant information found in the provided documents."

---
Context:
{context}
---
Question: {question}

Answer:
"""

def answer_question(context: str, question: str, model: str = MODEL, verbose: bool = False) -> str:
    prompt = RAG_PROMPT_TEMPLATE.format(
        context=context.strip(),
        question=question.strip()
    )

    if verbose:
        print("Prompt:\n", prompt)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You answer only using the provided context."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
