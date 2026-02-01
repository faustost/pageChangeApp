# Page Change Monitor

A simple app that monitors web pages for changes and notifies you via Telegram.

## Features

- Monitor multiple pages for content changes
- Smart text extraction (ignores ads, timestamps, navigation)
- Compact diff showing what changed
- Telegram notifications
- Runs free on GitHub Actions (hourly checks)
- JSON storage for snapshots and history

## Quick Start

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Start a chat with your new bot and send any message
5. Get your **chat ID** by visiting: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Look for `"chat":{"id":123456789}` in the response

### 2. Configure GitHub Secrets

In your GitHub repo, go to **Settings > Secrets and variables > Actions** and add:

- `TELEGRAM_BOT_TOKEN`: Your bot token from step 1
- `TELEGRAM_CHAT_ID`: Your chat ID from step 1

### 3. Configure Pages to Monitor

Edit `data/pages.json`:

```json
{
  "pages": [
    {
      "id": "my-page",
      "name": "My Important Page",
      "url": "https://example.com/page",
      "selector": null
    }
  ],
  "settings": {
    "max_history_per_page": 50
  }
}
```

- `id`: Unique identifier (used internally)
- `name`: Human-readable name (shown in notifications)
- `url`: Page URL to monitor
- `selector`: CSS selector to focus on (optional, `null` for whole page)

### 4. Enable GitHub Actions

The monitor runs automatically every hour. You can also trigger it manually:

1. Go to **Actions** tab in your repo
2. Select **Page Monitor** workflow
3. Click **Run workflow**

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with dry-run (no notifications)
python main.py --dry-run

# Run normally
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=xxx python main.py
```

### Running Tests

To run the automated test suite:

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run tests
python -m pytest tests
```

## Project Structure

```
pageChangeApp/
├── main.py              # Entry point
├── src/
│   ├── config.py        # Configuration loader
│   ├── storage.py       # JSON storage layer
│   ├── monitor.py       # Fetch, extract, diff logic
│   └── notify.py        # Telegram notifications
├── data/
│   ├── pages.json       # Pages to monitor (edit this)
│   └── snapshots.json   # Auto-generated snapshots
└── .github/
    └── workflows/
        └── monitor.yml  # Hourly cron job
```

## Future Enhancements

- [ ] Web UI to view history and manage pages
- [ ] CSS selectors for targeted monitoring
- [ ] Email notifications
- [ ] Webhook support
- [ ] Screenshot diff mode

## License

MIT
