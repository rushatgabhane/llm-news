import os
import faiss
import json
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from services import json_logger_service

embedding_model = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

vectorstore = None

def initialize_vectorstore(logger=None):
    global vectorstore
    dimension = 1536
    faiss_index = faiss.IndexFlatL2(dimension)
    docstore = InMemoryDocstore()
    index_to_docstore_id = {}
    vectorstore = FAISS(embedding_model, faiss_index, docstore, index_to_docstore_id)
    if logger:
        logger.info("[RAG] Initialized empty vectorstore.")

def split_documents(docs: List[Document], logger=None) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    chunks = splitter.split_documents(docs)
    if logger:
        logger.info(f"[RAG] Split into {len(chunks)} document chunks.")
    return chunks

def index_articles_from_json(logger=None):
    latest_file = json_logger_service.get_latest_json_file()
    if not latest_file:
        if logger:
            logger.warning("[RAG] No previous JSON report found.")
        return

    if logger:
        logger.info(f"[RAG] Loading vectorstore from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        all_articles = json.load(f)

    docs = []
    for entry in all_articles:
        metadata = entry.get("metadata", {})
        content = metadata.get("raw_content", "") or metadata.get("content", "")
        title = metadata.get("title", "")
        source = metadata.get("source", "")
        if content:
            doc = Document(page_content=content, metadata={"title": title, "source": source})
            docs.append(doc)

    if docs:
        docs = split_documents(docs, logger=logger)
        vectorstore.add_documents(docs)
        if logger:
            logger.info(f"[RAG] Indexed {len(docs)} chunks into vectorstore.")

def query_articles(question: str, top_k: int = 5, logger=None) -> str:
    global vectorstore
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    retrieved_docs = retriever.get_relevant_documents(question)

    if logger:
        logger.info(f"[RAG] Retrieved {len(retrieved_docs)} chunks for question: {question}")
        retrieved_sources = set()
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.metadata.get("source", "N/A")
            title = doc.metadata.get("title", "N/A")
            if source not in retrieved_sources:
                logger.info(f"[RAG] Source: {source} | Title: {title}")
                retrieved_sources.add(source)

    custom_prompt = PromptTemplate.from_template("""
You are an expert AI technology analyst.

Use the provided context to identify and summarize the latest AI trends. Combine information from multiple documents if necessary.

If no relevant information is found, say: "No relevant trends found."

Context:
{context}

Question:
{question}

Answer:
""")

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": custom_prompt}
    )

    result = qa_chain.invoke({"query": question})

    if logger:
        full_context = "\n\n".join([doc.page_content for doc in result["source_documents"]])
        logger.info(f"[RAG] Context provided to LLM (first 2000 chars): {full_context[:2000]}")

    return result["result"]