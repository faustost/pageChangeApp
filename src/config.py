"""Configuration loader. Simple is better than complex."""

import json
import os
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
PAGES_FILE = DATA_DIR / "pages.json"
SNAPSHOTS_FILE = DATA_DIR / "snapshots.json"


def load_pages():
    """Load pages configuration from JSON file."""
    with open(PAGES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_telegram_token():
    """Get Telegram bot token from environment."""
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def get_telegram_chat_id():
    """Get Telegram chat ID from environment or config."""
    env_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if env_chat_id:
        return env_chat_id

    config = load_pages()
    return config.get("settings", {}).get("telegram_chat_id", "")
