import sys

if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from dotenv import load_dotenv
from controllers import report_controller
from logger import get_logger

load_dotenv()

logger, log_file = get_logger()
logger.info("LLM-News API started")

app = FastAPI()

@app.get("/report")
async def get_report():
    logger.info("Received request for report generation")
    report = await report_controller.generate_tech_trends_report(logger)
    return report