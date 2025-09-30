from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline

def get_llm():
    gen = pipeline(
        task="text2text-generation",
        model="google/flan-t5-base",
        max_new_tokens=512,
        temperature=0,
    )
    print("got LLM")
    return HuggingFacePipeline(pipeline=gen)