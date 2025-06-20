import asyncio
import httpx

HACKERNEWS_API_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HACKERNEWS_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

async def fetch_hackernews_top_stories(logger, limit=10):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(HACKERNEWS_API_URL, timeout=10)
            response.raise_for_status()

            top_story_ids = response.json()[:limit]
            logger.info(f"[Hacker News API] Total results found: {len(top_story_ids)}")

            tasks = [client.get(HACKERNEWS_ITEM_URL.format(story_id)) for story_id in top_story_ids]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            metadata = []

            for resp in responses:
                if isinstance(resp, Exception):
                    logger.error(f"[Hacker News API] Exception: {resp}")
                    continue

                json_data = resp.json()
                if 'url' in json_data:
                    metadata.append({
                        'title': json_data.get('title', 'No Title'),
                        'url': json_data['url'],
                        'source': 'HackerNews'
                    })

            logger.info(f"[Hacker News API] Fetched metadata for {len(metadata)} articles.")
            return metadata

    except Exception as e:
        logger.error(f"[Hacker News API] Failed: {e}")
        return []