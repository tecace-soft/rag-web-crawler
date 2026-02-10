import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString

# Path to URL list: one URL per line (blank lines and # comments ignored)
URLS_FILE = Path(__file__).resolve().parent.parent / "urls.txt"

# Minimum character length for a standalone text block to keep
MIN_LEN = 40
# Skip elements with these tag names (no text extracted from inside them)
SKIP_TAGS = {"script", "style", "noscript", "svg", "iframe"}
# Text that looks like UI/nav — skip blocks that are exactly or start with these
BLOCKLIST = {
    "Sign in", "Log in", "Contact", "Get started", "Learn more",
    "Privacy Policy", "Terms of Service", "Schedule a Demo", "Menu", "Close",
    "Cookie", "Accept", "Subscribe", "Submit", "Loading",
}
# Patterns that indicate noise (e.g. script content, long base64, SVG/XML)
NOISE_PATTERNS = [
    re.compile(r"^\s*(?:var|let|const|function|=>|\(function)\s", re.I),
    re.compile(r"^\s*\{[\s\S]*\"@"),
    re.compile(r"^[A-Za-z0-9+/=]{100,}"),  # long alphanumeric (e.g. base64)
    re.compile(r"<\?xml\s+version=", re.I),
    re.compile(r"^\s*xml\s+version=", re.I),
]


def _is_noise(text: str, allow_short: bool = False) -> bool:
    if not text:
        return True
    t = text.strip()
    if not allow_short and len(t) < MIN_LEN:
        return True
    if t in BLOCKLIST:
        return True
    for pat in NOISE_PATTERNS:
        if pat.search(text):
            return True
    return False


def _get_main_root(soup: BeautifulSoup):
    """Prefer main content area to avoid header/nav/footer."""
    main = soup.find("main") or soup.find(attrs={"data-main-content-parent": "true"})
    return main if main else soup.body or soup


def _extract_semantic_chunks(root) -> list[dict]:
    """
    Walk the tree and build chunks with optional heading context.
    Each chunk has 'heading' (or None) and 'text' for RAG-friendly retrieval.
    """
    chunks: list[dict] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush_chunk():
        nonlocal current_heading, current_lines
        text = "\n".join(current_lines).strip() if current_lines else (current_heading or "")
        if not text:
            return
        if current_lines:
            if _is_noise(text):
                current_lines = []
                return
        else:
            # Heading-only chunk (e.g. short section title)
            if _is_noise(text, allow_short=True):
                current_heading = None
                return
        had_body = bool(current_lines)
        chunks.append({
            "heading": current_heading,
            "text": text,
        })
        current_lines = []
        if not had_body and current_heading:
            current_heading = None

    def collect_text(elem):
        nonlocal current_heading, current_lines
        if elem.name in SKIP_TAGS:
            return
        if hasattr(elem, "name") and elem.name:
            if elem.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                flush_chunk()
                t = elem.get_text(separator=" ", strip=True)
                if t and not _is_noise(t):
                    current_heading = t
                return
            if elem.name in ("section", "article"):
                flush_chunk()
                for child in elem.children:
                    collect_text(child)
                flush_chunk()
                return
        # Leaf text or container: get direct text only for inline elements
        if isinstance(elem, NavigableString):
            text = elem.strip()
            if text:
                current_lines.append(text)
            return
        # For elements like <p>, <li>, <td>, get their full text as one block
        if elem.name in ("p", "li", "td", "th", "figcaption", "blockquote"):
            flush_chunk()
            t = elem.get_text(separator=" ", strip=True)
            if t and not _is_noise(t):
                current_lines.append(t)
            flush_chunk()
            return
        # Recurse into other containers
        for child in elem.children:
            collect_text(child)

    collect_text(root)
    flush_chunk()
    return chunks


def load_urls(path: Path | None = None) -> list[str]:
    """Load URLs from a text file (one per line). Blank lines and # comments are ignored."""
    p = path or URLS_FILE
    if not p.exists():
        return []
    urls = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def crawl_url(url: str) -> dict:
    """Crawl a single URL and return one page result: { url, content, chunks }."""
    res = requests.get(url, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    for tag in soup.find_all(SKIP_TAGS):
        tag.decompose()

    root = _get_main_root(soup)
    chunks = _extract_semantic_chunks(root)

    content_parts = []
    for c in chunks:
        if c["heading"]:
            content_parts.append(c["heading"])
        content_parts.append(c["text"])
    content = "\n\n".join(content_parts)

    return {
        "url": url,
        "content": content,
        "chunks": chunks,
    }


def crawl(urls_path: Path | None = None) -> list[dict]:
    """
    Load URLs from the urls file, crawl each, and return a list of page results.
    Each item is { "url", "content", "chunks" }. All are appended into one list for latest.json.
    """
    urls = load_urls(urls_path)
    if not urls:
        return []
    pages = []
    for url in urls:
        try:
            pages.append(crawl_url(url))
        except Exception as e:
            # Log and skip failed URLs so other pages still get saved
            pages.append({
                "url": url,
                "content": "",
                "chunks": [],
                "error": str(e),
            })
    return pages
