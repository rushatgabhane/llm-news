import aiofiles
import os
import json
import datetime
from pathlib import Path


async def write_report_to_json(all_articles):
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    filepath = logs_dir / filename

    async with aiofiles.open(filepath, mode="w", encoding="utf-8") as file:
        await file.write(json.dumps(all_articles, ensure_ascii=False, indent=2))

    return filepath


def get_latest_json_file():
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    json_files = sorted(logs_dir.glob("*.json"), reverse=True)
    if not json_files:
        return None
    return json_files[0]
