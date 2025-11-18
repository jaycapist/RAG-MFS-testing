import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def answer_question(context, question):
    prompt = f"""Use the context below to answer the question.

Context:
{context}

Question: {question}
Answer:
"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def format_answer_with_sources(answer: str, docs, preview=150):
    print("\nResponse:")
    print(answer.strip())

    print("\nList of documents used:")
    seen = set()
    for d in docs:
        src = d.payload.get("source", "unknown")
        if src in seen:
            continue
        seen.add(src)

        link = d.payload.get("link", "<no link>")
        snippet = d.payload.get("text", "").replace("\n", " ").strip()[:preview]
        if not snippet:
            snippet = "(No visible content)"
        
        print(f"{src} {link}  # {snippet}...")
