import re
import asyncio
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, NavigableString


URLS_FILE = Path(__file__).resolve().parent / "urls.txt"
MIN_LEN = 40
SKIP_TAGS = {"script", "style", "noscript", "svg", "iframe"}
BLOCKLIST = {"Sign in", "Log in", "Contact", "Get started", "Learn more", "Privacy Policy", "Terms of Service", "Schedule a Demo", "Menu", "Close", "Cookie", "Accept", "Subscribe", "Submit", "Loading"}
NOISE_PATTERNS = [
    re.compile(r"^\s*(?:var|let|const|function|=>|\(function)\s", re.I),
    re.compile(r"^\s*\{[\s\S]*\"@"),
    re.compile(r"^[A-Za-z0-9+/=]{100,}"),
    re.compile(r"<\?xml\s+version=", re.I),
    re.compile(r"^\s*xml\s+version=", re.I),
]

def _is_noise(text: str, allow_short: bool = False) -> bool:
    if not text: return True
    t = text.strip()
    if not allow_short and len(t) < MIN_LEN: return True
    if t in BLOCKLIST: return True
    for pat in NOISE_PATTERNS:
        if pat.search(text): return True
    return False

def _get_main_root(soup: BeautifulSoup):
    """Prefer main content area to avoid header/nav/footer."""
    # Wix FAQ 전용 컨테이너를 먼저 찾습니다.
    faq_root = soup.find(attrs={"data-testid": "faq-list"})
    if faq_root:
        return faq_root
        
    # FAQ가 없는 일반 페이지의 경우 본문을 찾습니다.
    main = soup.find("main") or soup.find(attrs={"data-main-content-parent": "true"}) or soup.find(id="SITE_PAGES_CONTAINER")
    return main if main else soup.body or soup

def _extract_semantic_chunks(root) -> list[dict]:
    chunks: list[dict] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush_chunk():
        nonlocal current_heading, current_lines
        text = "\n".join(current_lines).strip() if current_lines else (current_heading or "")
        if not text: return
        if current_lines:
            if _is_noise(text):
                current_lines = []
                return
        else:
            if _is_noise(text, allow_short=True):
                current_heading = None
                return
        had_body = bool(current_lines)
        chunks.append({"heading": current_heading, "text": text})
        current_lines = []
        if not had_body and current_heading: current_heading = None

    def collect_text(elem):
        nonlocal current_heading, current_lines
        if elem.name in SKIP_TAGS: return
        if hasattr(elem, "name") and elem.name:
            if elem.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                flush_chunk()
                t = elem.get_text(separator=" ", strip=True)
                if t and not _is_noise(t): current_heading = t
                return
            if elem.name in ("section", "article"):
                flush_chunk()
                for child in elem.children: collect_text(child)
                flush_chunk()
                return
        if isinstance(elem, NavigableString):
            text = elem.strip()
            if text: current_lines.append(text)
            return
        if elem.name in ("p", "li", "td", "th", "figcaption", "blockquote"):
            flush_chunk()
            t = elem.get_text(separator=" ", strip=True)
            if t and not _is_noise(t): current_lines.append(t)
            flush_chunk()
            return
        for child in elem.children: collect_text(child)

    collect_text(root)
    flush_chunk()
    return chunks

def crawl_url(url: str) -> dict:
    """Crawl a single URL and return integrated text content WITHOUT chunks."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)

            all_text_blocks = []
            tabs = page.locator('[role="tab"]')
            tab_count = tabs.count()

            if tab_count > 0:
                print(f"[{url}] {tab_count}개의 탭 발견. 순회 중...")
                for i in range(tab_count):
                    tabs.nth(i).click()
                    page.wait_for_timeout(1500) 
                    soup = BeautifulSoup(page.content(), "html.parser")
                    for tag in soup.find_all(SKIP_TAGS): tag.decompose()
                    root = _get_main_root(soup)
                    all_text_blocks.append(root.get_text(separator="\n", strip=True))
            else:
                soup = BeautifulSoup(page.content(), "html.parser")
                for tag in soup.find_all(SKIP_TAGS): tag.decompose()
                root = _get_main_root(soup)
                all_text_blocks.append(root.get_text(separator="\n", strip=True))

            # chunks 없이 url과 content만 반환
            return {
                "url": url,
                "content": "\n\n".join(all_text_blocks)
            }
        finally:
            browser.close()

# --- main.py에서 호출하는 핵심 함수 ---
def load_urls(path: Path | None = None) -> list[str]:
    p = path or URLS_FILE
    if not p.exists(): return []
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]

def crawl(urls_path: Path | None = None) -> list[dict]:
    """
    URL 리스트를 순회하며 중복된 텍스트 블록은 제외하고 수집합니다.
    하나의 URL이라도 실패하면 예외를 발생시켜 전체 프로세스를 중단합니다.
    """
    urls = load_urls(urls_path)
    if not urls:
        return []
        
    pages = []
    # 이미 수집된 텍스트 블록을 기억 (중복 FAQ 방지)
    global_seen_content = set()

    for url in urls:
        try:
            print(f"Processing: {url}")
            # crawl_url 내부에서 발생하는 Timeout 등 모든 에러를 catch하지 않고 둡니다.
            page_data = crawl_url(url)
            
            # 수집된 전체 텍스트를 줄 단위로 나눠서 중복 체크
            lines = page_data["content"].split("\n")
            unique_lines = []
            
            for line in lines:
                clean_line = line.strip()
                # 텍스트가 너무 짧지 않고, 이전에 본 적 없는 내용일 때만 추가
                if len(clean_line) > 20: 
                    if clean_line not in global_seen_content:
                        unique_lines.append(clean_line)
                        global_seen_content.add(clean_line)
                elif clean_line: # 짧은 텍스트는 그냥 포함 (중복 체크 제외)
                    unique_lines.append(clean_line)

            # 중복이 제거된 텍스트로 갱신
            page_data["content"] = "\n".join(unique_lines)
            
            # 유의미한 내용이 남은 경우만 추가
            if page_data["content"].strip():
                pages.append(page_data)
            
        except Exception as e:
            # 에러 발생 시 로그만 찍고 예외를 다시 던짐(raise) -> main.py에서 중단 처리
            print(f"❌ Critical error at {url}: {e}")
            raise e
            
    return pages