from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from controllers import report_controller
from logger import get_logger
from services import rag_service
from fastapi.responses import StreamingResponse

load_dotenv()

logger, log_file = get_logger()
logger.info("[Main] LLM-News API started")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Main] Initializing vectorstore.")
    rag_service.initialize_vectorstore(logger=logger)
    rag_service.index_articles_from_json(logger=logger)
    logger.info("[Main] Vectorstore ready.")
    yield
    logger.info("[Main] Shutting down application.")

app = FastAPI(lifespan=lifespan)

class RAGQuery(BaseModel):
    question: str

@app.get("/report")
async def get_report():
    logger.info("[Main] Received report request")
    report = await report_controller.generate_tech_trends_report(logger)
    return report

@app.post("/rag")
async def query_rag(request: RAGQuery):
    logger.info(f"[Main] Received RAG query: {request.question}")
    def token_stream():
        yield from rag_service.stream_query_articles(request.question, logger=logger)
    return StreamingResponse(token_stream(), media_type="text/plain")