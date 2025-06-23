import os
import json
import requests
import math
import asyncio
from dotenv import load_dotenv
from services.llm_service import validate_article_url

load_dotenv()

GOOGLE_API_URL = "https://www.googleapis.com/customsearch/v1"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_ENV_KEYS = json.loads(os.getenv("GOOGLE_ENV_KEYS", "[]"))

def fetch_news_page(logger, cx, start_index=1, search_query=None):
    if search_query is None:
        # Use more specific queries that are likely to return articles
        search_queries = [
            '"latest technology news" "announces"',
            '"tech news" "launches" "2025"',
            '"technology company" "announces" "news"',
            '"releases" "update"',
            '"tech startup" "raises funding"',
            '"technology company" "partners" "announces"',
            '"startup" "funding" "news"',
            '"tech innovation" "announces" "breakthrough"',
            '"software" "announces" "release"',
            '"hardware" "announces" "launch"',
            '"cybersecurity" "announces" "news"',
            '"cloud computing" "announces" "update"',
            '"mobile" "announces" "app"',
            '"gaming" "announces" "release"',
            '"automotive" "technology" "announces"',
            '"biotechnology" "announces" "breakthrough"',
            '"quantum computing" "announces" "news"',
            '"blockchain" "announces" "update"',
            '"robotics" "announces" "innovation"',
            '"renewable energy" "technology" "announces"'
        ]
        search_query = search_queries[start_index % len(search_queries)]
    
    params = {
        "key": GOOGLE_API_KEY,
        "cx": cx,
        "q": search_query,
        "dateRestrict": "w1",
        "sort": "date",
        "start": start_index,
        "num": 10,
    }
    response = requests.get(GOOGLE_API_URL, params=params)
    logger.info(
        f"[Google API] Response from Google: {response.status_code}, using query: {search_query}"
    )
    return response.json()


async def fetch_google_api_top_stories(logger):
    if not GOOGLE_ENV_KEYS:
        logger.warning("No Google Custom Search keys provided.")
        return []

    metadata = []
    seen_urls = set()

    for cx in GOOGLE_ENV_KEYS:
        # Try multiple specific search queries to get better articles
        search_queries = [
            '"latest technology news" "announces"',
            '"tech news" "launches" "2025"',
            '"technology company" "announces" "news"',
            '"releases" "update"',
            '"tech startup" "raises funding"',
            '"technology company" "partners" "announces"',
            '"software" "announces" "release"',
            '"hardware" "announces" "launch"',
            '"cybersecurity" "announces" "news"',
            '"cloud computing" "announces" "update"'
        ]
        
        for query in search_queries:
            initial_response = fetch_news_page(logger, cx, 1, query)

            if not initial_response or "searchInformation" not in initial_response:
                logger.warning(f"[Google API] No results using engine id ({cx}) with query: {query}")
                continue

            total_results = int(
                initial_response["searchInformation"].get("totalResults", 0)
            )
            logger.info(
                f"[Google API] {total_results} results found using engine id ({cx}) with query: {query}"
            )

            items = initial_response.get("items", [])
            for item in items:
                url = item["link"]
                title = item["title"]
                
                # Skip if we've already seen this URL
                if url in seen_urls:
                    continue
                
                # Use LLM to validate if this is an actual article
                is_article, reason = await validate_article_url(url, title)
                
                if is_article:
                    metadata.append({
                        "title": title,
                        "url": url,
                        "source": "Google"
                    })
                    seen_urls.add(url)
                    logger.info(f"[Google API] Added article: {title}")
                else:
                    logger.info(f"[Google API] Filtered out non-article: {title} - {url} (Reason: {reason})")

            # Limit to first page per query to avoid rate limits
            if len(metadata) >= 20:  # Limit total articles
                break
        
        if len(metadata) >= 20:  # Limit total articles
            break

    logger.info(f"[Google API] Fetched metadata for {len(metadata)} articles after LLM validation.")
    return metadata
