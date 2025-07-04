import asyncio
import httpx
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import platform
import os
import win32api

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

            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            content = "\n".join(
                [p.get_text() for p in paragraphs if p.get_text().strip()]
            )

            if not content.strip():
                logger.warning(
                    f"[BeautifulSoup] No meaningful content extracted from {url}"
                )
                return False, None

            return True, content

    except Exception as e:
        logger.error(f"[BeautifulSoup] Exception while fetching {url}: {e}")
        return False, None

def get_chrome_version_win(logger, default_version="137.0.7151.120"):
    potential_paths = [
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Google\\Chrome\\Application\\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google\\Chrome\\Application\\chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google\\Chrome\\Application\\chrome.exe"),
    ]

    for path in potential_paths:
        if os.path.exists(path):
            try:
                info = win32api.GetFileVersionInfo(path, "\\")
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
                return version
            except Exception as e:
                logger.warning(f"[Selenium] Failed to read version from {path}: {e}")
                continue

    logger.warning("[Selenium] Could not detect Chrome version. Using default.")
    return default_version

def fetch_with_selenium(url, logger):
    system = platform.system()
    options = uc.ChromeOptions()

    if system == "Linux":
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    version = get_chrome_version_win(logger)
    major_version = int(version.split('.')[0]) if version else 137

    driver = None
    try:
        driver = uc.Chrome(version_main=major_version, options=options)
        logger.info(f"[Selenium] Navigating to: {url}")
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
                    logger.warning(
                        f"[Selenium] Exception while quitting driver for {url}: {e}"
                    )