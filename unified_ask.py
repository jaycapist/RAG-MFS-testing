from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

def ask_unified(question, llm, retriever):
    RAG_PROMPT = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Use ONLY the provided context."),
        ("human", "Question: {input}\n\nContext:\n{context}")
    ])
    doc_chain = create_stuff_documents_chain(llm, RAG_PROMPT)
    rag_chain = create_retrieval_chain(retriever, doc_chain)
    return rag_chain.invoke({"input": question})