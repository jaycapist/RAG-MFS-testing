from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import time

def preprocess_documents(docs):
    print("Starting Split")
    split_start = time.perf_counter()
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

    print(f"Split Chunks: {time.perf_counter() - split_start:,.1f}s")
    embed_start = time.perf_counter()
    print("Starting Embeddings")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        encode_kwargs={"normalize_embeddings": True}
    )

    print(f"Embeddings: {time.perf_counter() - embed_start:,.1f}s")
    vector_start = time.perf_counter()
    print("Starting Vector Store")

    db = Chroma.from_documents(split_docs, embeddings)
    print(f"Vector Store: {time.perf_counter() - vector_start:,.1f}s")
    return db, split_docs