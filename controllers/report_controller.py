import os
import aiofiles
import random
import string
import locale
import asyncio
import datetime
import re
from pathlib import Path
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, RetryWithErrorOutputParser
from langchain_core.runnables import RunnableWithFallbacks
from langchain.callbacks.base import AsyncCallbackHandler
from services.google_api_service import fetch_google_api_top_stories
from services.hackernews_service import fetch_hackernews_top_stories
from logger_service import logger
from models.report_model import ReportResponse, ReportItem

CONCURRENCY_LIMIT = 3

class PromptAndResponseLogger(AsyncCallbackHandler):
    def __init__(self, logger):
        self.logger = logger
    async def on_llm_error(self, error, **kwargs):
        self.logger.error(f"LLM Error: {error}")

llm = ChatOpenAI(
    model_name="gpt-4o",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    callbacks=[PromptAndResponseLogger(logger)]
)

class ReportOutput(BaseModel):
    summary: str
    categories: list[str]
    insights: list[str]

combined_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
    You are a professional tech analyst. Perform 3 tasks:
    1. Interpret and summarize the content (never more than 15000 characters).
    2. Categorize into topics (only high-level and no abbreviations).
    3. Provide actionable insights (only actionable and specific insights).
    Output strictly as JSON:
    {{"summary": "<summary>", "categories": [], "insights": []}}
    If the content seems to be a protection wall, cookie banner, captcha, or similar, use category ["Error"], and fill summary with the error and leave insights empty.
    If insufficient content, use category ["Insufficient Content"], leave summary and insights empty.
    If other errors occur, use category ["Error"], and fill summary with the error and leave insights empty.
    """),
    ("human", """
    Article Content:
    {content}
    """)
])

base_parser = PydanticOutputParser(pydantic_object=ReportOutput)
retry_parser = RetryWithErrorOutputParser.from_llm(parser=base_parser, llm=llm)
base_pipeline = combined_prompt_template | llm | base_parser
combined_pipeline = RunnableWithFallbacks(
    runnable=base_pipeline,
    fallbacks=[combined_prompt_template | llm | retry_parser]
)

def clean_for_csv(text, delimiter):
    if not text:
        return ""
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'[\u2028\u2029\x0b\x0c\x1c-\x1f]', ' ', text)
    text = ' '.join(text.split())
    text = text.replace(delimiter, '|')
    return text

def escape_csv_field(text):
    if any(char in text for char in ['"', ',', ';', '\n']):
        return '"' + text.replace('"', '""') + '"'
    return text

async def write_report_to_csv(all_articles):
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}.csv"
    filepath = logs_dir / filename
    locale.setlocale(locale.LC_ALL, '')
    delimiter = locale.localeconv()['decimal_point']
    delimiter = ',' if delimiter != ',' else ';'

    headers = ["Status", "Reason", "Source", "Title", "Prompt", "Categories", "Insights", "Summary"]
    async with aiofiles.open(filepath, mode="w", encoding="utf-8") as file:
        await file.write(delimiter.join(headers) + "\n")
        for entry in all_articles:
            try:
                prompt_filled = combined_prompt_template.format_prompt(content=entry['content']).to_string()
            except Exception:
                prompt_filled = entry.get('prompt', '')
            prompt_cleaned = clean_for_csv(prompt_filled, delimiter)
            row = [
                entry['status'], entry['reason'],
                clean_for_csv(entry.get('source', ''), delimiter),
                clean_for_csv(entry.get('title', ''), delimiter),
                prompt_cleaned,
                clean_for_csv(", ".join(entry.get('categories', [])), delimiter),
                clean_for_csv(", ".join(entry.get('insights', [])), delimiter),
                clean_for_csv(entry.get('summary', ''), delimiter)
            ]
            await file.write(delimiter.join([escape_csv_field(cell) for cell in row]) + "\n")
    logger.info(f"[LLM] CSV report written: {filepath}")

async def process_article(article):
    content = await article['content'] if asyncio.iscoroutine(article['content']) else article['content']
    article['source'] = article.get('url', '')

    if not content or len(content.strip()) < 100:
        logger.warning(f"[LLM] Skipped (too short): {article['source']}")
        return {**article, 'categories': [], 'insights': [], 'summary': '', 'status': 'Rejected', 'reason': 'Too short'}

    try:
        result = await combined_pipeline.ainvoke({"content": content})
        if "Insufficient Content" in result.categories:
            logger.warning(f"[LLM] Rejected (Insufficient Content): {article['source']}")
            return {**article, 'categories': result.categories, 'insights': result.insights, 'summary': result.summary, 'status': 'Rejected', 'reason': 'Insufficient Content'}
        if "Error" in result.categories:
            logger.warning(f"[LLM] Rejected (Error in Model Response): {article['source']}")
            return {**article, 'categories': result.categories, 'insights': [], 'summary': result.summary, 'status': 'Rejected', 'reason': 'Error in Model Response'}
        logger.info(f"[LLM] Accepted: {article['source']}")
        return {**article, 'categories': result.categories, 'insights': result.insights, 'summary': result.summary, 'status': 'Accepted', 'reason': ''}
    except Exception as e:
        logger.error(f"[LLM] Error: {article.get('title', '')} - {e}")
        return {**article, 'categories': [], 'insights': [], 'summary': '', 'status': 'Error', 'reason': str(e)}

async def generate_tech_trends_report(logger):
    articles = await fetch_hackernews_top_stories(logger) + await fetch_google_api_top_stories(logger)
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def limited_process(article):
        async with semaphore:
            return await process_article(article)

    results = await asyncio.gather(*(limited_process(article) for article in articles))
    await write_report_to_csv(results)

    total = len(results)
    accepted = sum(1 for r in results if r['status'] == 'Accepted')
    rejected = sum(1 for r in results if r['status'] == 'Rejected')
    errors = sum(1 for r in results if r['status'] == 'Error')
    logger.info(f"[LLM] Summary: Total={total}, Accepted={accepted}, Rejected={rejected}, Errors={errors}")

    articles = [
        ReportItem(
            categories=entry['categories'], title=entry['title'], source=entry['source'],
            summary=entry['summary'], insights=entry['insights']
        ) for entry in results if entry['status'] == 'Accepted'
    ]
    return ReportResponse(articles=articles)