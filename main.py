from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

from controllers import report_controller

@app.get("/report")
async def get_report():
    report = await report_controller.generate_tech_trends_report()
    return report
