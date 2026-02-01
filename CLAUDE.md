# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Page Change Monitor is a Python application that tracks changes to web pages and sends notifications via Telegram. It runs hourly on GitHub Actions but can also be executed locally.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (dry run - no notifications)
python main.py --dry-run

# Run with notifications
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=xxx python main.py
```

GitHub Actions runs automatically every hour and can be triggered manually from the Actions tab.

## Architecture

```
src/
├── config.py    # Environment + JSON configuration loading
├── monitor.py   # Core logic: fetch pages, parse HTML, compute diffs
├── notify.py    # Telegram Bot API notifications
└── storage.py   # JSON persistence for snapshots and history

data/
├── pages.json      # User-configured pages to monitor
└── snapshots.json  # Auto-generated: content hashes, history, diffs
```

**Data Flow:**
1. `main.py` orchestrates: loads pages → checks each → saves snapshots → sends notifications
2. `monitor.py` fetches with retry logic (3 retries, 5s delay, 60s timeout), strips HTML noise (scripts, styles, nav, dynamic content), hashes content (SHA256), and generates unified diffs
3. `storage.py` maintains history (up to 50 diffs per page) in `snapshots.json`
4. `notify.py` sends Telegram messages with rate limiting ("no changes" only once per 24h)

## Key Design Decisions

**HTML Noise Filtering:** The monitor removes DOM noise tags and filters dynamic patterns (timestamps, session IDs, tokens) to catch only meaningful changes. CSS selectors can focus monitoring on specific page regions.

**Git as Audit Trail:** GitHub Actions auto-commits `snapshots.json` changes with `[skip ci]`, creating version-controlled history of all detected changes.

**Retry Logic:** `MAX_RETRIES=3`, `RETRY_DELAY=5`, `REQUEST_TIMEOUT=60` handle transient network failures.

## Configuration

**Environment Variables:**
- `TELEGRAM_BOT_TOKEN` - Required for notifications
- `TELEGRAM_CHAT_ID` - Required for notifications

**pages.json structure:**
```json
{
  "pages": [{"id": "unique-id", "name": "Name", "url": "https://...", "selector": null}],
  "settings": {"max_history_per_page": 50}
}
```

## Limitations

- Only sees initial HTML, not JavaScript-rendered content
- Monitoring many pages hourly may trigger rate limits on target sites
