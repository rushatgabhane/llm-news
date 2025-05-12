from services.hackernews_service import fetch_top_stories
from langchain import OpenAI, LLMChain
from models.report_model import ReportResponse, ReportItem

llm = OpenAI(model_name="gpt-4o-mini")
summary_chain = LLMChain(llm=llm, prompt="Summarize the following tech article: {article}")

async def generate_tech_trends_report():
    articles = await fetch_top_stories()
    summaries = []

    for article in articles:
        try:
            summary = summary_chain.run(article=article['url'])
            report_item = ReportItem(title=article['title'], source=article['url'], summary=summary)
            summaries.append(report_item)
        except Exception as e:
            summaries.append(ReportItem(title=article['title'], source=article['url'], summary=f"Error summarizing: {e}"))

    return ReportResponse(summaries=summaries)