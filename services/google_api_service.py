import os
import json
from urllib.parse import urlparse
import requests
import math
import asyncio
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_URL = 'https://www.googleapis.com/customsearch/v1'
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_ENV_KEYS = json.loads(os.getenv("GOOGLE_ENV_KEYS"))


def fetch_news_page(cx, start_index=1):
    params = {
        'key': GOOGLE_API_KEY,
        'cx': cx,
        'q': 'Technology',
        'dateRestrict': 'w1',
        'sort': 'date',
        'start': start_index,
    }
    response = requests.get(GOOGLE_API_URL, params=params)
    return response.json()


async def fetch_google_api_top_stories():
    articles = []

    for cx in GOOGLE_ENV_KEYS:
        print(f"🔄 Searching using cx: {cx}")
        initial_response = fetch_news_page(cx, 1)

        if not initial_response or 'searchInformation' not in initial_response:
            print(f"❌ No results or error for cx: {cx}")
            continue

        total_results = int(initial_response['searchInformation'].get('totalResults', 0))
        print(f"🔎 Total results found: {total_results}")
        num_requests = min(math.ceil(total_results / 10), 10)
        all_items = []

        for i in range(num_requests):
            start = i * 10 + 1
            print(f"📄 Fetching page {i + 1} (start={start}) for cx: {cx}")
            data = fetch_news_page(cx, start)
            current_items = data.get('items', [])
            all_items.extend(current_items)

        for item in all_items:
            article_content = await fetch_article_content(item['link'])
            articles.append({
                'title': item['title'],
                'url': item['link'],
                'content': article_content
            })

    return articles

def sync_fetch_article_content(url):
    import time

    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    profile_dir = os.path.expanduser("~/.config/selenium_profile")
    options.add_argument(f"--user-data-dir={profile_dir}")

    driver = None
    try:
        driver = uc.Chrome(options=options)
        driver.get(url)
        time.sleep(1)
        driver.implicitly_wait(1)

        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        content = "\n".join([p.text for p in paragraphs if p.text.strip()])
        return content if content else "No readable content found."

    except Exception as e:
        return f"Error scraping: {e}"

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


async def fetch_article_content(url):
    return await asyncio.to_thread(sync_fetch_article_content, url)