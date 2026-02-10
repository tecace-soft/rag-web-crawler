import json
from pathlib import Path

# Always use project-root data/ so latest.json is in one place
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

LATEST = DATA_DIR / "latest.json"
PREVIOUS = DATA_DIR / "previous.json"


def load_previous() -> list[dict] | None:
    """Load the previous snapshot: list of page results, or None if missing."""
    if PREVIOUS.exists():
        data = json.loads(PREVIOUS.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else None
    return None


def save_snapshot(pages: list[dict]) -> None:
    """
    Save all crawled pages into a single latest.json (and rotate previous).
    pages: list of { "url", "content", "chunks" } (and optionally "error").
    """
    if LATEST.exists():
        LATEST.replace(PREVIOUS)

    LATEST.write_text(
        json.dumps(pages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
