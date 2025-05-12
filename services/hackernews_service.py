import asyncio
import httpx

HACKERNEWS_API_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HACKERNEWS_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

async def fetch_top_stories(limit=10):
    async with httpx.AsyncClient() as client:
        response = await client.get(HACKERNEWS_API_URL)
        top_story_ids = response.json()[:limit]
        tasks = [client.get(HACKERNEWS_ITEM_URL.format(story_id)) for story_id in top_story_ids]
        responses = await asyncio.gather(*tasks)
        articles = [resp.json().get('url') for resp in responses if 'url' in resp.json()]
    return articles
