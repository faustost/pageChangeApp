"""Core monitoring logic. Fetch, extract, diff."""

import hashlib
import re
import difflib
import requests
from bs4 import BeautifulSoup

# Reasonable timeout for requests
REQUEST_TIMEOUT = 30

# Elements that usually contain noise, not content
NOISE_TAGS = [
    "script", "style", "nav", "header", "footer", "aside",
    "noscript", "iframe", "svg", "form", "button", "input"
]

# Patterns to remove (timestamps, session IDs, etc.)
NOISE_PATTERNS = [
    r"\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}(:\d{2})?",  # datetime
    r"sessionid=[\w-]+",  # session IDs
    r"token=[\w-]+",  # tokens
    r"_=\d+",  # cache busters
]


def fetch_page(url):
    """Fetch page content. Returns HTML string or None on error."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_text(html, selector=None):
    """Extract meaningful text from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # If selector specified, focus on that element
    if selector:
        target = soup.select_one(selector)
        if target:
            soup = target

    # Remove noise elements
    for tag in NOISE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    # Get text, normalize whitespace
    text = soup.get_text(separator="\n", strip=True)

    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text)

    # Normalize whitespace: collapse multiple newlines, trim lines
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]  # Remove empty lines
    text = "\n".join(lines)

    return text


def compute_hash(content):
    """Compute hash of content for quick comparison."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def compute_diff(old_content, new_content, context_lines=2):
    """Compute a compact diff between old and new content."""
    if old_content is None:
        return "(first snapshot - no previous content)"

    old_lines = old_content.split("\n")
    new_lines = new_content.split("\n")

    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm="",
        n=context_lines
    ))

    if not diff:
        return None  # No difference

    # Skip the --- and +++ header lines, keep the rest
    diff_text = "\n".join(diff[2:])
    return diff_text


def check_page(page_config, previous_content=None):
    """
    Check a single page for changes.

    Returns:
        dict with keys: changed, content, hash, diff, error
    """
    url = page_config["url"]
    selector = page_config.get("selector")

    html = fetch_page(url)
    if html is None:
        return {"error": f"Failed to fetch {url}", "changed": False}

    content = extract_text(html, selector)
    content_hash = compute_hash(content)

    # First run - no previous content
    if previous_content is None:
        return {
            "changed": False,
            "content": content,
            "hash": content_hash,
            "diff": None,
            "first_run": True
        }

    # Compare
    previous_hash = compute_hash(previous_content)
    if content_hash == previous_hash:
        return {
            "changed": False,
            "content": content,
            "hash": content_hash,
            "diff": None
        }

    # Changed! Compute diff
    diff = compute_diff(previous_content, content)
    return {
        "changed": True,
        "content": content,
        "hash": content_hash,
        "diff": diff
    }
