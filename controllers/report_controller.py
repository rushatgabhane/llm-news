import asyncio
from services.google_api_service import fetch_google_api_top_stories
from services.hackernews_service import fetch_hackernews_top_stories
from services.llm_service import process_article
from services.csv_logger_service import write_report_to_csv
from models.report_model import ReportResponse, ReportItem
from logger import logger

CONCURRENCY_LIMIT = 3

async def generate_tech_trends_report(logger):
    articles = await fetch_hackernews_top_stories(logger)
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def limited_process(article):
        async with semaphore:
            return await process_article(article)

    results = await asyncio.gather(*(limited_process(article) for article in articles))
    await write_report_to_csv(results)

    total = len(results)
    accepted = sum(1 for r in results if r['logging']['status'] == 'Accepted')
    rejected = sum(1 for r in results if r['logging']['status'] == 'Rejected')
    errors = sum(1 for r in results if r['logging']['status'] == 'Error')
    logger.info(f"[LLM] Summary: Total={total}, Accepted={accepted}, Rejected={rejected}, Errors={errors}")

    response = [
        ReportItem(
            categories=entry['response']['categories'],
            title=entry['metadata'].get('title', 'No Title'),
            source=entry['metadata'].get('source', ''),
            summary=entry['response']['summary'],
            insights=entry['response']['insights']
        )
        for entry in results if entry['logging']['status'] == 'Accepted'
    ]

    return ReportResponse(items=response)