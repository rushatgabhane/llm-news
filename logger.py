import logging
import os
import random
import string
from datetime import datetime, timedelta
import sys

if not os.path.exists("logs"):
    os.makedirs("logs")


def cleanup_old_logs():
    now = datetime.now()
    cutoff = now - timedelta(days=21)
    for filename in os.listdir("logs"):
        filepath = os.path.join("logs", filename)
        if os.path.isfile(filepath):
            try:
                timestamp_str = filename.split("_")[0]
                file_date = datetime.strptime(timestamp_str, "%Y-%m-%d")
                if file_date < cutoff:
                    os.remove(filepath)
                    print(f"Deleted old log file: {filename}")
            except Exception as e:
                print(f"Could not parse log filename {filename}: {e}")


cleanup_old_logs()


def generate_log_filename():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    random_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"logs/{timestamp}_{random_id}.log"


LOG_FILE = generate_log_filename()

logger = logging.getLogger("tech_trends_logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def sanitize_log_message(message: str) -> str:
    if not isinstance(message, str):
        message = str(message)
    return " ".join(message.replace("\n", " ").replace("\r", " ").split())


class SafeLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return sanitize_log_message(msg), kwargs


safe_logger = SafeLoggerAdapter(logger, {})


def get_logger():
    return safe_logger, LOG_FILE
