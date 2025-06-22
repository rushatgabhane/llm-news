from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from controllers import report_controller
from logger import get_logger
from services import rag_service, json_logger_service
from fastapi.responses import StreamingResponse, JSONResponse
import json
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

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
    return JSONResponse(content=report.model_dump())


@app.post("/rag")
async def query_rag(request: RAGQuery):
    logger.info(f"[Main] Received RAG query: {request.question}")

    def token_stream():
        yield from rag_service.stream_query_articles(request.question, logger=logger)

    return StreamingResponse(token_stream(), media_type="text/plain")


@app.get("/categories")
async def get_categories():
    latest_file = json_logger_service.get_latest_json_file()
    if not latest_file:
        return {"categories": []}
    with open(latest_file, "r", encoding="utf-8") as f:
        all_articles = json.load(f)
    categories = set()
    for entry in all_articles:
        status = entry.get("logging", {}).get("status", "")
        if status != "Rejected":
            cats = entry.get("response", {}).get("categories", [])
            categories.update(cats)
    return {"categories": sorted(categories)}


async def run_report_and_index():
    logger.info("[Scheduler] Running scheduled report and index job.")
    report = await report_controller.generate_tech_trends_report(logger)
    logger.info("[Scheduler] Report and index job complete.")


# On app startup, run the report and schedule weekly job
scheduler = BackgroundScheduler()


def start_scheduler():
    # Run once on startup (in background)
    loop = asyncio.get_event_loop()
    loop.create_task(run_report_and_index())

    # Schedule weekly job (every Monday at 00:00)
    scheduler.add_job(
        lambda: asyncio.run(run_report_and_index()),
        "cron",
        day_of_week="mon",
        hour=0,
        minute=0,
    )
    scheduler.start()


start_scheduler()
