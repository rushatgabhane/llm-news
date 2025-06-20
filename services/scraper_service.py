import asyncio
import httpx
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os

async def fetch_article_content(logger, url, method="auto"):
    if method == "BeautifulSoup" or method == "auto":
        success, content = await fetch_with_httpx_bs(url, logger=logger)
        if success:
            logger.info(f"[Scraper] Scraped with BeautifulSoup from {url}")
            return "BeautifulSoup", content

    if method == "Selenium" or (method == "auto" and not success):
        success, content = await asyncio.to_thread(fetch_with_selenium, url, logger)
        if success:
            logger.info(f"[Scraper] Scraped with Selenium from {url}")
            return "Selenium", content

    logger.error(f"[Scraper] Failed scraping content from {url}")
    return None, None

async def fetch_with_httpx_bs(url, logger):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return False, None

            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = '\n'.join([p.get_text() for p in paragraphs if p.get_text().strip()])

            if not content.strip():
                logger.warning(f"[BeautifulSoup] No meaningful content extracted from {url}")
                return False, None

            return True, content

    except Exception as e:
        logger.error(f"[BeautifulSoup] Exception while fetching {url}: {e}")
        return False, None

def fetch_with_selenium(url, logger):
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
        driver.implicitly_wait(2)

        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        content = "\n".join([p.text for p in paragraphs if p.text.strip()])

        if not content.strip():
            logger.warning(f"[Selenium] No meaningful content extracted from {url}")
            return False, None

        return True, content

    except Exception as e:
        logger.error(f"[Selenium] Exception while fetching {url}: {e}")
        return False, None

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                if logger:
                    logger.warning(f"[Selenium] Exception while quitting driver for {url}: {e}")