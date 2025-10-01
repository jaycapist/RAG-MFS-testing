{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "7035c1fb",
   "metadata": {},
   "outputs": [],
   "source": [
    "from fastapi import FastAPI, Request\n",
    "from pydantic import BaseModel\n",
    "from dotenv import load_dotenv\n",
    "import os\n",
    "\n",
    "load_dotenv()\n",
    "\n",
    "from sync_drive import sync_pdfs_from_drive\n",
    "from load_pdfs import load_pdfs\n",
    "from preprocessing import preprocess_documents\n",
    "from retrievers import build_retrievers, get_retriever_for_query\n",
    "from llm_model import get_llm\n",
    "from unified_ask import ask_unified\n",
    "from printers import print_sources\n",
    "\n",
    "app = FastAPI()\n",
    "\n",
    "print(\"Pipeline Starting\")\n",
    "folder_id = \"0B5R6pTMzHSzVTWJoSDRVaFBTZnM\"\n",
    "sync_pdfs_from_drive(folder_id)\n",
    "\n",
    "docs = load_pdfs()\n",
    "db, split_docs = preprocess_documents(docs)\n",
    "bm25, vec, hybrid = build_retrievers(db, split_docs)\n",
    "llm = get_llm()\n",
    "print(\"Pipeline Ready\")\n",
    "\n",
    "class QueryInput(BaseModel):\n",
    "    query: str\n",
    "\n",
    "@app.post(\"/ask\")\n",
    "async def ask_question(data: QueryInput):\n",
    "    query = data.query\n",
    "    retr = get_retriever_for_query(query, db, bm25, hybrid)\n",
    "    result = ask_unified(query, llm, retr)\n",
    "    return {\n",
    "        \"answer\": result.get(\"answer\", \"\"),\n",
    "        \"sources\": [doc.metadata.get(\"source\", \"unknown\") for doc in result.get(\"context\", [])]\n",
    "    }\n",
    "\n",
    "@app.get(\"/\")\n",
    "async def root():\n",
    "    return {\"status\": \"Running\"}\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "rag_workshop_env",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.13"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
