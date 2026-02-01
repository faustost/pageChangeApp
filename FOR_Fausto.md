# FOR_Fausto.md - Page Change Monitor: The Complete Story

## What This Project Actually Does

Imagine you're waiting for important news on a website—maybe the results of a scholarship selection, or updates on a law being debated in Congress. You could obsessively refresh the page every hour like a nervous squirrel checking for acorns. Or... you could build a robot to do it for you.

That's exactly what this project is: **a tireless digital watchdog** that checks web pages every hour, remembers what they looked like, and pings you on Telegram the moment something changes.

You're currently monitoring:
- **PPGA UnB** - Graduate program selection results (the one that caught a change on Jan 29!)
- **MP 1318** - A legislative proposal in the Brazilian Congress
- **Eurasia Game** - Your own project page

---

## The Architecture: A Bird's Eye View

Think of this system like a night security guard making rounds:

```
┌─────────────────────────────────────────────────────────────────┐
│                     GITHUB ACTIONS (The Scheduler)              │
│                    Wakes up every hour, says "do your job"      │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        main.py (The Orchestrator)               │
│              Loads config, coordinates everyone, reports back   │
└─────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │  config.py  │     │ monitor.py  │     │  notify.py  │
   │   (Memory)  │     │  (The Eyes) │     │ (The Voice) │
   │             │     │             │     │             │
   │ Where are   │     │ Fetch page, │     │ Send Tele-  │
   │ the pages?  │     │ strip junk, │     │ gram alerts │
   │ What are    │     │ compute     │     │             │
   │ the creds?  │     │ differences │     │             │
   └─────────────┘     └─────────────┘     └─────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ storage.py  │
                       │ (The Diary) │
                       │             │
                       │ Remember    │
                       │ what we saw │
                       │ last time   │
                       └─────────────┘
```

---

## The Files: What Each One Does

### `main.py` - The Conductor

This is the entry point. Like a conductor in an orchestra, it doesn't play any instruments—it just tells everyone when to play and keeps things synchronized.

```python
# The main loop is elegantly simple:
for page in pages:
    previous = get_what_we_saw_last_time(page)
    current = check_the_page_now(page)

    if current != previous:
        save_the_new_version(current)
        send_telegram_alert("Hey! Something changed!")
```

Key insight: Notice the `--dry-run` flag. This is a **fantastic pattern** for any notification system. It lets you test the entire pipeline without actually bothering anyone. Use this pattern in every project that sends notifications.

### `src/config.py` - The Memory Keeper

The simplest module. It knows two things:
1. Where to find `pages.json` (what to monitor)
2. How to get Telegram credentials from environment variables

**Why environment variables for secrets?** Because you never, EVER put API tokens in code that goes to GitHub. Environment variables are the standard way to handle secrets—they exist only in the runtime environment, not in your codebase.

### `src/monitor.py` - The Real Brains

This is where the magic happens. Let me break down the clever bits:

**1. HTML Noise Filtering**

Web pages are noisy. They have scripts, styles, navigation menus, timestamps that change every second. If you compared raw HTML, you'd get false positives constantly.

```python
NOISE_TAGS = ["script", "style", "nav", "header", "footer", ...]
NOISE_PATTERNS = [r"\d{1,2}/\d{1,2}/\d{2,4}", ...]  # timestamps, sessions, etc.
```

The monitor surgically removes all this junk before comparing. It's like reading a newspaper and ignoring the ads, date, and page numbers—focusing only on the articles.

**2. Retry Logic**

Networks fail. Servers hiccup. The code handles this gracefully:

```python
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 60  # generous for slow servers
```

This is **defensive programming**. Assume things will break, and plan for it.

**3. Hash-Based Comparison**

Instead of comparing megabytes of text character-by-character, we compute a SHA256 hash (a 16-character fingerprint). If the fingerprints match, the content is identical. This is orders of magnitude faster.

### `src/storage.py` - The Historian

Every time a change is detected, we don't just save the new version—we save the **diff** (what changed) with a timestamp. This creates a complete audit trail.

```python
"history": [
    {"timestamp": "2025-01-29T...", "diff": "@@ -44,4 +44,5 @@\n+New line added"},
    {"timestamp": "2025-01-15T...", "diff": "..."},
    ...
]
```

Limit: 50 diffs per page. Old history eventually falls off, keeping storage manageable.

### `src/notify.py` - The Messenger

Sends Telegram messages. Simple in theory, surprisingly tricky in practice (more on this in Lessons Learned).

---

## The GitHub Actions Magic

Here's something beautiful: **your code runs for free, forever, without you touching it**.

```yaml
on:
  schedule:
    - cron: '0 * * * *'  # Every hour, on the hour
```

GitHub Actions is essentially a free computer in the cloud that wakes up, runs your code, and goes back to sleep. The workflow:

1. **Checkout** - Gets your code
2. **Setup Python** - Installs Python 3.11
3. **Install deps** - `pip install requests beautifulsoup4`
4. **Run monitor** - Executes `main.py` with Telegram secrets injected
5. **Commit changes** - Saves `snapshots.json` back to the repo

That last step is genius: **Git becomes your database's backup system**. Every change to snapshots.json is a Git commit. You can go back in time and see exactly what every page looked like, when.

The `[skip ci]` in commit messages prevents infinite loops—otherwise the commit would trigger another workflow run!

---

## Technologies Used & Why

| Technology | Why This One? |
|------------|---------------|
| **Python** | Perfect for scripting. Rich ecosystem, easy to read, fast to write. |
| **requests** | The standard HTTP library. Simple, reliable, everyone uses it. |
| **BeautifulSoup** | HTML parsing that doesn't make you cry. Forgiving, intuitive API. |
| **Telegram Bot API** | Free, instant, works on phone. Perfect for personal notifications. |
| **GitHub Actions** | Free CI/CD. No servers to manage. Just push code and forget. |
| **JSON** | Simple storage. Human-readable, no database to set up. |

### Why NOT a database?

For a personal project monitoring 3 pages? Overkill. JSON files work perfectly:
- Easy to inspect and debug
- Version controlled automatically
- Zero infrastructure to maintain

If you were monitoring 1000 pages? Then yes, SQLite or PostgreSQL.

---

## Lessons Learned (The Good Stuff)

### Lesson 1: Telegram's Markdown Parser is a Landmine

**The Bug:** On January 29th, the monitor detected a change on the PPGA page, but the Telegram notification failed with `400 Bad Request`.

**What Happened:** The page name contained "PPGA UnB - Processo Seletivo". That hyphen? Telegram's Markdown parser choked on it. Same with parentheses, periods, and a dozen other characters.

**The Fix:** We switched from `Markdown` to `MarkdownV2` and added proper escaping:

```python
def escape_markdown(text):
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
```

**The Lesson:** APIs that accept formatted text are minefields. Always:
1. Test with weird input (special characters, emojis, different languages)
2. Have a fallback (could send as plain text if Markdown fails)
3. Read the docs carefully—`MarkdownV2` has strict escaping rules

### Lesson 2: The Value of Dry Run

The `--dry-run` flag saves lives (and friendships). When testing:
- You don't spam yourself with test messages
- You can verify the entire pipeline works
- Others on your notification channel don't get confused

**Best Practice:** Every notification system should have a dry-run mode. Make it the default in development.

### Lesson 3: Content-Based Diffing vs. Hash Comparison

Early versions might have just compared hashes. But hashes only tell you *something* changed, not *what* changed.

The unified diff output:
```
@@ -44,4 +44,5 @@
 Edital PPGA 08/2025 - Resultado Provisório
+Edital PPGA 08/2025 - Resultado Final
```

This immediately tells you: one new line was added. Much more useful than "page changed!"

### Lesson 4: Noise Filtering is Non-Trivial

Many websites include:
- Timestamps that change every visit
- Session tokens in URLs
- Cache-buster parameters
- Dynamic ad content

Without filtering, you'd get false positives constantly. The `NOISE_PATTERNS` regex list handles common cases, but you may need to add more for specific sites.

### Lesson 5: Git as an Audit Trail

The `[skip ci]` commit pattern is elegant:
- Every change creates a commit
- You can `git log` to see change history
- You can `git diff` between any two commits
- It's free, requires no extra infrastructure

This pattern works for any data that changes over time and benefits from version history.

### Lesson 6: Retry Logic is Not Optional

Networks are unreliable. Servers have hiccups. The first request might fail for no good reason.

```python
MAX_RETRIES = 3
RETRY_DELAY = 5
```

This simple pattern—try, wait, retry—handles 99% of transient failures. Without it, you'd get false "page down" alerts during momentary network blips.

### Lesson 7: CSS Selectors for Precision

The `selector` field in page config is optional but powerful:

```json
{"selector": "#main-content"}
```

This tells the monitor to only watch a specific part of the page. Useful when:
- The header/footer changes frequently (news sites)
- You only care about one section
- The page has lots of dynamic content you want to ignore

---

## How Good Engineers Think

This project demonstrates several professional patterns:

1. **Separation of Concerns** - Each module does ONE thing. Config loads config. Monitor monitors. Notifier notifies. Easy to test, easy to modify.

2. **Defensive Programming** - Retry logic, timeout handling, graceful error messages. Assume things will break.

3. **Configuration over Code** - Pages are defined in JSON, not hardcoded. Adding a new page = editing JSON, not Python.

4. **Secrets Management** - Credentials in environment variables, never in code.

5. **Idempotency** - Running the script twice in a row produces the same result (no duplicate notifications).

6. **Observability** - Print statements at every step. When something fails at 3 AM, you need to know what happened.

---

## Potential Pitfalls to Avoid

1. **Rate Limiting** - If you monitor 100 pages every hour, target sites might block you. Consider adding delays between requests.

2. **JavaScript-Rendered Content** - This monitor only sees the initial HTML. Sites that load content via JavaScript (SPAs) won't work. For those, you'd need Selenium or Playwright.

3. **Telegram Rate Limits** - If many pages change at once, Telegram might throttle you. Consider batching notifications.

4. **Large Pages** - The entire page content is stored in `snapshots.json`. For very large pages, this file could grow unwieldy.

5. **Time Zones** - All timestamps are UTC. When debugging, remember to convert to your local time.

---

## Quick Reference: Adding a New Page

1. Edit `data/pages.json`:
```json
{
  "id": "unique-slug",
  "name": "Human Readable Name",
  "url": "https://example.com/page",
  "selector": null  // or "#specific-element"
}
```

2. Run locally to test:
```bash
python main.py --dry-run
```

3. Commit and push. GitHub Actions takes over from here.

---

## The Philosophy

This project embodies a powerful idea: **automate the boring stuff**.

Instead of manually checking websites, build a robot. Instead of running that robot manually, use free cloud infrastructure. Instead of managing a database, let Git handle versioning.

The result? A system that runs 24/7, costs nothing, requires no maintenance, and delivers value by alerting you exactly when you need to know something.

That's good engineering: **solve the problem, then get out of the way**.

---

*Last updated: January 2025*
*Fixed: Telegram MarkdownV2 escaping bug*
