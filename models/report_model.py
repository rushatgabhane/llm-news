from pydantic import BaseModel
from typing import List

class ReportItem(BaseModel):
    source: str
    title: str
    categories: List[str]
    insights: List[str]
    summary: str

class ReportResponse(BaseModel):
    items: List[ReportItem]