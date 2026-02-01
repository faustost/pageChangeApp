# Next Feature: Playwright for JavaScript-Rendered Pages

## The Problem

Some websites load content via JavaScript after the initial HTML loads. The current approach (`requests` + `BeautifulSoup`) only sees the initial HTML—like reading a book before the ink has dried.

Examples of JS-heavy sites:
- Single Page Applications (React, Vue, Angular)
- Sites with "Load More" buttons
- Dynamic government portals

## Effort Estimate

| Task | Complexity |
|------|------------|
| Add Playwright to the project | Low |
| Modify `monitor.py` to use Playwright | Medium |
| Update GitHub Actions workflow | Low |
| Testing & edge cases | Medium |

**Total: A few hours of focused work.**

---

## The Plan

### Step 1: Add Playwright Dependency

```bash
pip install playwright
playwright install chromium
```

Update `requirements.txt`:
```
requests>=2.28.0
beautifulsoup4>=4.11.0
playwright>=1.40.0
```

### Step 2: Add `js_render` Flag to Page Config

Modify `data/pages.json` to mark which pages need JavaScript:

```json
{
  "id": "some-spa-page",
  "name": "JavaScript Heavy Site",
  "url": "https://example.com/spa",
  "selector": null,
  "js_render": true   // <-- New flag, default false
}
```

This keeps the fast `requests` path for simple pages.

### Step 3: Create a Playwright Fetcher

Add to `monitor.py`:

```python
from playwright.sync_api import sync_playwright

def fetch_page_js(url, wait_seconds=3):
    """Fetch page with JavaScript rendering via headless browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(wait_seconds * 1000)  # Let JS execute
        html = page.content()
        browser.close()
        return html
```

### Step 4: Modify `fetch_page()` to Choose Strategy

```python
def fetch_page(url, js_render=False):
    """Fetch page content. Uses Playwright if js_render=True."""
    if js_render:
        return fetch_page_js(url)
    else:
        # Existing requests-based logic
        return fetch_page_requests(url)
```

### Step 5: Update `check_page()` Call

```python
def check_page(page_config, previous_content=None, previous_hash=None):
    url = page_config["url"]
    selector = page_config.get("selector")
    js_render = page_config.get("js_render", False)  # <-- New

    html = fetch_page(url, js_render=js_render)
    # ... rest unchanged
```

### Step 6: Update GitHub Actions Workflow

Playwright needs browser binaries installed:

```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    playwright install chromium --with-deps
```

The `--with-deps` flag installs system dependencies (fonts, libraries) that Chromium needs on Ubuntu.

---

## Trade-offs to Consider

| Aspect | requests | Playwright |
|--------|----------|------------|
| Speed | ~1-2 seconds | ~5-15 seconds |
| Memory | ~10 MB | ~200+ MB |
| GitHub Actions time | Minimal | Adds ~30s setup |
| Reliability | High | Slightly lower (browser can crash) |
| JS support | None | Full |

**Recommendation:** Keep both. Use `js_render: true` only for pages that need it.

---

## Edge Cases to Handle

1. **Timeout** - Some SPAs take forever to "settle". Add a `wait_for_selector` option:
   ```python
   page.wait_for_selector("#content-loaded", timeout=10000)
   ```

2. **Cookie banners / Popups** - May need to dismiss them:
   ```python
   page.click("button.accept-cookies", timeout=2000)
   ```

3. **Infinite scroll** - Page might never "finish" loading. The fixed wait time handles this.

4. **Browser crashes** - Wrap in try/except, fall back to error state.

---

## Testing Strategy

1. Find a known JS-heavy page (or create a test page on GitHub Pages)
2. Run with `--dry-run` to verify content is captured
3. Compare output between `js_render: false` and `js_render: true`
4. Test in GitHub Actions (the Ubuntu environment differs from Windows)

---

## When to Implement

**Now:** If you're missing changes on monitored pages that you can see in browser

**Later:** If current pages work fine with the simple approach

The beauty of the current architecture: this is an additive change. Nothing breaks, you just gain a new capability for pages that need it.

---

## Quick Validation Test

Before implementing, check if your current pages actually need this:

1. Open each monitored URL in browser
2. View Page Source (Ctrl+U)
3. Search for the content you're monitoring

If the content is in the source → `requests` works fine
If the content is NOT in the source → you need Playwright

---

*Created: January 2025*
*Status: Planned, not yet implemented*
