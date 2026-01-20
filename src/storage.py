"""Storage layer. JSON now, database later."""

import json
from datetime import datetime, timezone
from .config import SNAPSHOTS_FILE, load_pages


def load_snapshots():
    """Load existing snapshots or return empty structure."""
    if not SNAPSHOTS_FILE.exists():
        return {"pages": {}}

    with open(SNAPSHOTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshots(snapshots):
    """Save snapshots to JSON file."""
    with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, indent=2, ensure_ascii=False)


def get_page_snapshot(page_id):
    """Get snapshot for a specific page."""
    snapshots = load_snapshots()
    return snapshots.get("pages", {}).get(page_id)


def save_page_snapshot(page_id, content, content_hash, diff=None, changed=False):
    """Save snapshot for a page, maintaining history."""
    snapshots = load_snapshots()
    config = load_pages()
    max_history = config.get("settings", {}).get("max_history_per_page", 50)
    now = datetime.now(timezone.utc).isoformat()

    if page_id not in snapshots["pages"]:
        snapshots["pages"][page_id] = {
            "last_checked": now,
            "last_changed": now if changed else None,
            "current_hash": content_hash,
            "current_content": content,
            "history": []
        }
    else:
        page_data = snapshots["pages"][page_id]
        page_data["last_checked"] = now

        if changed and diff:
            page_data["last_changed"] = now
            page_data["history"].insert(0, {
                "timestamp": now,
                "diff": diff,
                "previous_hash": page_data["current_hash"],
                "new_hash": content_hash
            })
            # Trim history
            page_data["history"] = page_data["history"][:max_history]

        page_data["current_hash"] = content_hash
        page_data["current_content"] = content

    save_snapshots(snapshots)


def get_last_no_changes_ts():
    """Gets the timestamp of the last 'no changes' notification."""
    snapshots = load_snapshots()
    return snapshots.get("meta", {}).get("last_no_changes_notification_ts")


def set_last_no_changes_ts():
    """Sets the timestamp for the last 'no changes' notification to now."""
    snapshots = load_snapshots()
    if "meta" not in snapshots:
        snapshots["meta"] = {}
    snapshots["meta"]["last_no_changes_notification_ts"] = datetime.now(timezone.utc).isoformat()
    save_snapshots(snapshots)
