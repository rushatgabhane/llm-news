from services.hackernews_service import fetch_top_stories
from langchain.prompts import ChatPromptTemplate
from models.report_model import ReportResponse, ReportItem
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model_name="gpt-4.1-nano", openai_api_key=os.getenv("OPENAI_API_KEY"))
prompt_template = ChatPromptTemplate.from_template("Summarize the following tech article content in 2-3 sentences: {content}")

async def generate_tech_trends_report():
    articles = await fetch_top_stories()
    summaries = []

    for article in articles:
        try:
            summary = prompt_template | llm | str
            result = summary.invoke({"content": article['content']})
            report_item = ReportItem(title=article['title'], source=article['url'], summary=result)
            summaries.append(report_item)
        except Exception as e:
            summaries.append(ReportItem(title=article['title'], source=article['url'], summary=f"Error summarizing: {e}"))

    return ReportResponse(summaries=summaries)
