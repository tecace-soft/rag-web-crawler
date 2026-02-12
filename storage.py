import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

LATEST = DATA_DIR / "latest.json"
PREVIOUS = DATA_DIR / "previous.json"

def load_previous() -> list[dict] | None:
    """기존에 저장된 최신 스냅샷(latest.json)을 로드합니다."""
    if LATEST.exists():
        try:
            data = json.loads(LATEST.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else None
        except Exception:
            return None
    return None

def save_snapshot(pages: list[dict]) -> None:
    """
    새로운 데이터를 latest.json에 저장합니다.
    기존 latest.json은 previous.json으로 백업됩니다.
    """
    if LATEST.exists():
        # 기존 파일을 백업으로 돌림
        LATEST.replace(PREVIOUS)

    LATEST.write_text(
        json.dumps(pages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )