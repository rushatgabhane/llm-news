from fastapi import FastAPI

app = FastAPI()

from controllers import report_controller

@app.get("/report")
async def get_report():
    return report_controller.generate_tech_trends_report()

