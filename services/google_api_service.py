import os
import json
import requests
import math
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_URL = 'https://www.googleapis.com/customsearch/v1'
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_ENV_KEYS = json.loads(os.getenv("GOOGLE_ENV_KEYS", "[]"))

def fetch_news_page(logger, cx, start_index=1):
    params = {
        'key': GOOGLE_API_KEY,
        'cx': cx,
        'q': 'Technology',
        'dateRestrict': 'w1',
        'sort': 'date',
        'start': start_index,
    }
    response = requests.get(GOOGLE_API_URL, params=params)
    logger.info(f"[Google API] Response from Google: {response.status_code}, using params: {params}")
    return response.json()

async def fetch_google_api_top_stories(logger):
    if not GOOGLE_ENV_KEYS:
        logger.warning("No Google Custom Search keys provided.")
        return []

    metadata = []

    for cx in GOOGLE_ENV_KEYS:
        initial_response = fetch_news_page(logger, cx, 1)

        if not initial_response or 'searchInformation' not in initial_response:
            logger.warning(f"[Google API] No results using engine id ({cx})!")
            continue

        total_results = int(initial_response['searchInformation'].get('totalResults', 0))
        logger.info(f"[Google API] {total_results} results found using engine id ({cx}).")

        items = initial_response.get('items', [])
        for item in items:
            metadata.append({
                'title': item['title'],
                'url': item['link'],
                'source': 'Google'
            })

        if total_results > 10:
            num_additional_requests = min(math.ceil((total_results - 10) / 10), 9)
            for i in range(num_additional_requests):
                start = (i + 1) * 10 + 1 
                data = fetch_news_page(logger, cx, start)
                current_items = data.get('items', [])
                for item in current_items:
                    metadata.append({
                        'title': item['title'],
                        'url': item['link'],
                        'source': 'Google'
                    })

    logger.info(f"[Google API] Fetched metadata for {len(metadata)} articles.")
    return metadata