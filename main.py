#!/usr/bin/env python3
"""
Page Change Monitor - Main entry point.

Usage:
    python main.py              # Check all pages
    python main.py --dry-run    # Check without notifications
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from src.config import load_pages
from src.storage import get_page_snapshot, save_page_snapshot, get_last_no_changes_ts, set_last_no_changes_ts
from src.monitor import check_page
from src.notify import notify_change, notify_failure, notify_no_changes


def run(dry_run=False):
    """Main monitoring loop."""
    config = load_pages()
    pages = config.get("pages", [])

    if not pages:
        print("No pages configured. Add pages to data/pages.json")
        return

    print(f"Checking {len(pages)} page(s)...")
    changes_found = 0
    failed_pages = []

    for page in pages:
        page_id = page["id"]
        page_name = page["name"]
        page_url = page["url"]

        print(f"\n[{page_id}] {page_name}")
        print(f"  URL: {page_url}")

        # Get previous snapshot
        snapshot = get_page_snapshot(page_id)
        previous_content = snapshot["current_content"] if snapshot else None

        # Check for changes
        result = check_page(page, previous_content)

        if result.get("error"):
            print(f"  ERROR: {result['error']}")
            failed_pages.append(page_name)
            continue

        first_run = result.get("first_run", False)
        changed = result["changed"]

        if first_run:
            print("  First snapshot saved.")
            save_page_snapshot(
                page_id,
                result["content"],
                result["hash"],
                changed=False
            )
            if not dry_run:
                notify_change(page_name, page_url, None, first_run=True)

        elif changed:
            changes_found += 1
            print("  CHANGED!")
            print(f"  Diff preview:\n{result['diff'][:500]}...")

            save_page_snapshot(
                page_id,
                result["content"],
                result["hash"],
                diff=result["diff"],
                changed=True
            )

            if not dry_run:
                notify_change(page_name, page_url, result["diff"])
            else:
                print("  (dry-run: notification skipped)")

        else:
            print("  No changes.")
            # Update last_checked timestamp
            save_page_snapshot(
                page_id,
                result["content"],
                result["hash"],
                changed=False
            )

    # Send notifications based on the outcome
    if not dry_run:
        if failed_pages:
            notify_failure(failed_pages)
        elif changes_found == 0 and pages:
            # Check if we should send the daily "no changes" notification
            last_ts_str = get_last_no_changes_ts()
            should_notify = True

            if last_ts_str:
                last_ts = datetime.fromisoformat(last_ts_str)
                # Ensure last_ts is timezone-aware (it should be, but be safe)
                if last_ts.tzinfo is None:
                    last_ts = last_ts.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                if now - last_ts < timedelta(hours=24):
                    should_notify = False
                    print("  (Skipping 'no changes' notification: < 24h since last one)")

            if should_notify:
                if notify_no_changes():
                    set_last_no_changes_ts()
                    print("  ('No changes' notification sent)")

    print(f"\nDone. {changes_found} change(s) found. {len(failed_pages)} failure(s).")
    return changes_found


def main():
    parser = argparse.ArgumentParser(description="Page Change Monitor")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check pages but don't send notifications"
    )
    args = parser.parse_args()

    try:
        run(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
