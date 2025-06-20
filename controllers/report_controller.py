import asyncio
from services.google_api_service import fetch_google_api_top_stories
from services.hackernews_service import fetch_hackernews_top_stories
from services.llm_service import process_article
from services.csv_logger_service import write_report_to_csv
from models.report_model import ReportResponse, ReportItem
from logger import logger

CONCURRENCY_LIMIT = 3

async def generate_tech_trends_report(logger):
    hn_metadata = await fetch_hackernews_top_stories(logger)
    google_metadata = await fetch_google_api_top_stories(logger)

    combined_metadata = hn_metadata + google_metadata

    seen_urls = set()
    unique_articles = []
    for article in combined_metadata:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)

    logger.info(f"[Report] {len(unique_articles)} unique articles after deduplication.")

    from services.scraper_service import fetch_article_content
    articles_with_content = []
    for article in unique_articles:
        method, content = await fetch_article_content(logger, article['url'])
        if content:
            article['content'] = content
            article['method'] = method
            articles_with_content.append(article)

    CONCURRENCY_LIMIT = 3
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def limited_process(article):
        async with semaphore:
            return await process_article(article)

    results = await asyncio.gather(*(limited_process(article) for article in articles_with_content))

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