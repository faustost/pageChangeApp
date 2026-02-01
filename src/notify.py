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


def truncate_message(message, max_length=MAX_MESSAGE_LENGTH):
    """Truncate message if too long."""
    if len(message) <= max_length:
        return message
    return message[:max_length] + "\n\n\\.\\.\\. \\(message truncated\\)"


def escape_markdown(text):
    """Escape special Markdown characters for Telegram."""
    if not text:
        return text
    # Characters that need escaping in Telegram Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_telegram_message(page_name, page_url, diff, first_run=False):
    """Format a nice Telegram message."""
    # Escape page name for Markdown, but keep URL as-is (will be escaped separately)
    safe_name = escape_markdown(page_name)

    if first_run:
        return (
            f"*New page added to monitor*\n\n"
            f"*{safe_name}*\n"
            f"{page_url}\n\n"
            f"First snapshot saved\\. Will notify on changes\\."
        )

    truncated_diff = truncate_diff(diff)
    # Don't escape diff content inside code block, but escape backticks
    safe_diff = truncated_diff.replace('`', "'") if truncated_diff else ""
    return (
        f"*Page changed\\!*\n\n"
        f"*{safe_name}*\n"
        f"{page_url}\n\n"
        f"```\n{safe_diff}\n```"
    )


def send_telegram(message, silent=False):
    """Send a message via Telegram bot."""
    token = get_telegram_token()
    chat_id = get_telegram_chat_id()

    if not token or not chat_id:
        print("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        print(f"Would have sent:\n{message}\n")
        return False

    # Truncate if needed
    message = truncate_message(message)

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
        "disable_notification": silent,
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
    # Audible notification for changes
    return send_telegram(message, silent=False)


def format_failure_message(failed_pages):
    """Formats a message for page check failures."""
    safe_pages = [escape_markdown(p) for p in failed_pages]
    page_list = "\n \\- ".join(safe_pages)
    return (
        f"⚠️ *Falha no Monitoramento*\n\n"
        f"Não foi possível verificar as seguintes {len(failed_pages)} página\\(s\\):\n\n"
        f" \\- {page_list}"
    )


def notify_failure(failed_pages):
    """Sends a notification listing all pages that failed to be checked."""
    if not failed_pages:
        return
    message = format_failure_message(failed_pages)
    try:
        # Silent notification for failures
        send_telegram(message, silent=True)
    except Exception as e:
        print(f"CRITICAL: Failed to send failure notification: {e}")


def notify_no_changes():
    """Envia uma notificação quando nenhuma alteração é encontrada."""
    message = (
        f"✅ *Monitoramento Concluído*\n\n"
        f"Todas as páginas foram verificadas e nenhuma nova alteração foi encontrada\\."
    )
    # Silent notification for no changes
    return send_telegram(message, silent=True)
