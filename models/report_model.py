from pydantic import BaseModel
from typing import List

class ReportItem(BaseModel):
    title: str
    summary: str
    source: str

class ReportResponse(BaseModel):
    summaries: List[ReportItem]