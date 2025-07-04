import aiofiles
import random
import string
import locale
import datetime
import re
from pathlib import Path
from logger import logger


def clean_for_csv(text, delimiter):
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"[\u2028\u2029\x0b\x0c\x1c-\x1f]", " ", text)
    text = " ".join(text.split())
    text = text.replace(delimiter, "|")
    return text


def escape_csv_field(text):
    if any(char in text for char in ['"', ",", ";", "\n"]):
        return '"' + text.replace('"', '""') + '"'
    return text


async def write_report_to_csv(all_articles):
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}.csv"
    filepath = logs_dir / filename

    locale.setlocale(locale.LC_ALL, "")
    delimiter = locale.localeconv()["decimal_point"]
    delimiter = "," if delimiter != "," else ";"

    headers = [
        "Source",
        "Title",
        "Content",
        "Status",
        "Reason",
        "Retry",
        "MissingCategories",
        "Categories",
        "Insights",
        "Summary",
    ]

    async with aiofiles.open(filepath, mode="w", encoding="utf-8") as file:
        await file.write(delimiter.join(headers) + "\n")
        for entry in all_articles:
            try:
                logging_info = entry.get("logging", {})
                response_info = entry.get("response", {})
                metadata_info = entry.get("metadata", {})
                row = [
                    clean_for_csv(metadata_info.get("source", ""), delimiter),
                    clean_for_csv(metadata_info.get("title", ""), delimiter),
                    clean_for_csv(metadata_info.get("raw_content", ""), delimiter),
                    logging_info.get("status", ""),
                    logging_info.get("reason", ""),
                    str(logging_info.get("retry", "")),
                    clean_for_csv(
                        ", ".join(metadata_info.get("missing_categories", [])),
                        delimiter,
                    ),
                    clean_for_csv(
                        ", ".join(response_info.get("categories", [])), delimiter
                    ),
                    clean_for_csv(
                        ", ".join(response_info.get("insights", [])), delimiter
                    ),
                    clean_for_csv(response_info.get("summary", ""), delimiter),
                ]
                await file.write(
                    delimiter.join([escape_csv_field(cell) for cell in row]) + "\n"
                )
            except Exception as e:
                logger.error(f"[CSV Logger] Error writing row: {e}")

    logger.info(f"[LLM] CSV report written: {filepath}")
