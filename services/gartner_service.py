import os
import requests
import math
import httpx
from bs4 import BeautifulSoup

GOOGLE_API_URL = 'https://www.googleapis.com/customsearch/v1'
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_ENV_KEY = os.getenv("GOOGLE_ENV_KEY")  # Programmable Search Engine ID

def fetch_news_page(start_index=1):
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_ENV_KEY,
        'q': 'Technology',
        'dateRestrict': 'w1',
        'sort': 'date',
        'start': start_index,
    }
    response = requests.get(GOOGLE_API_URL, params=params)
    return response.json()

def fetch_news():
    initial_response = fetch_news_page(1)

    if initial_response:
        total_results = int(initial_response['searchInformation']['totalResults'])
        print(f"🔎 Total results found: {total_results}")
        num_requests = min(math.ceil(total_results / 10), 10)
        all_items = []

        for i in range(num_requests):
            start = i * 10 + 1
            print(f"📄 Fetching page {i + 1} (start={start})")

            data = fetch_news_page(start)
            items = data.get('items', [])
            all_items.extend(items)

        articles = []
        for item in all_items:
            article_content = fetch_article_content(item['link'])
            print(f"📰 Processing article: {item['title']}")
            articles.append({
                'title': item['title'],
                'url': item['link'],
                'content': article_content
            })
        return articles
    else:
        print("❌ No results found.")
        return []

async def fetch_article_content(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = '\n'.join([para.get_text() for para in paragraphs])
            return content if content else "Content could not be retrieved"
    except Exception as e:
        return f"Error fetching content: {e}"
    
content = fetch_news()
print(content)