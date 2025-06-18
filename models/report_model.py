from pydantic import BaseModel
from typing import List

class ReportItem(BaseModel):
    categories: List[str]
    title: str
    summary: str
    insights: List[str]
    source: str

class ReportResponse(BaseModel):
    summaries: List[ReportItem]