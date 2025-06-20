# hackernews_service.py
import asyncio
import httpx
from services.scraper_service import fetch_article_content

HACKERNEWS_API_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HACKERNEWS_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

async def fetch_hackernews_top_stories(logger, limit=10):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(HACKERNEWS_API_URL, timeout=10)
            response.raise_for_status()  # Raise HTTPError if non-200

            top_story_ids = response.json()[:limit]
            logger.info(f"[Hacker News API] Total results found: {len(top_story_ids)}")

            tasks = [client.get(HACKERNEWS_ITEM_URL.format(story_id)) for story_id in top_story_ids]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            articles = []

            for resp in responses:
                if isinstance(resp, Exception):
                    logger.error(f"[Hacker News API] Exception {type(resp).__name__} {repr(resp)}")
                    continue

                json_data = resp.json()
                if 'url' in json_data:
                    method_used, article_content = await fetch_article_content(logger, json_data['url'])
                    if article_content:
                        articles.append({
                            'title': json_data.get('title', 'No Title'),
                            'url': json_data['url'],
                            'content': article_content,
                            'method': method_used
                        })

            logger.info(f"[Hacker News API] Finished fetching articles: {len(articles)} articles collected")
            return articles

    except Exception as e:
        logger.error(f"[Hacker News API] Failed to fetch top stories: {e}")
        return []