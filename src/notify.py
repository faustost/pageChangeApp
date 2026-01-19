"""Notification handlers. Telegram now, more later."""

import requests
from .config import get_telegram_token, get_telegram_chat_id

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 4000  # Telegram limit is 4096, leave some buffer


def truncate_diff(diff, max_length=2000):
    """Truncate diff if too long, keeping it useful."""
    if not diff or len(diff) <= max_length:
        return diff

    return diff[:max_length] + "\n\n... (truncated)"


def format_telegram_message(page_name, page_url, diff, first_run=False):
    """Format a nice Telegram message."""
    if first_run:
        return (
            f"*New page added to monitor*\n\n"
            f"*{page_name}*\n"
            f"{page_url}\n\n"
            f"First snapshot saved. Will notify on changes."
        )

    truncated_diff = truncate_diff(diff)
    return (
        f"*Page changed!*\n\n"
        f"*{page_name}*\n"
        f"{page_url}\n\n"
        f"```\n{truncated_diff}\n```"
    )


def send_telegram(message):
    """Send a message via Telegram bot."""
    token = get_telegram_token()
    chat_id = get_telegram_chat_id()

    if not token or not chat_id:
        print("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        print(f"Would have sent:\n{message}\n")
        return False

    # Truncate if needed
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH] + "\n\n... (message truncated)"

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return False


def notify_change(page_name, page_url, diff, first_run=False):
    """Send notification about a page change."""
    message = format_telegram_message(page_name, page_url, diff, first_run)
    return send_telegram(message)


def format_failure_message(failed_pages):
    """Formats a message for page check failures."""
    page_list = "\n - ".join(failed_pages)
    return (
        f"⚠️ *Page Monitor Failure*\n\n"
        f"The following {len(failed_pages)} page(s) could not be checked due to errors:\n\n"
        f" - {page_list}"
    )


def notify_failure(failed_pages):
    """Sends a notification listing all pages that failed to be checked."""
    if not failed_pages:
        return
    message = format_failure_message(failed_pages)
    # Don't fail the whole run if the failure notification itself fails
    try:
        send_telegram(message)
    except Exception as e:
        print(f"CRITICAL: Failed to send failure notification: {e}")
