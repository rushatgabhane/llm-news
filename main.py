import sys

if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from dotenv import load_dotenv
from controllers import report_controller

load_dotenv()

app = FastAPI()

@app.get("/report")
async def get_report():
    report = await report_controller.generate_tech_trends_report()
    return report
