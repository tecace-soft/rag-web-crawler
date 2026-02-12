# import hashlib

# def fingerprint(text: str) -> str:
#     """텍스트의 고유 해시값을 생성합니다."""
#     return hashlib.sha256(text.encode("utf-8")).hexdigest()

# def has_changed(old: list[dict] | None, new: list[dict]) -> bool:
#     """
#     이전 데이터와 새 데이터를 비교하여 변경 여부를 반환합니다.
#     """
#     if not old:
#         return True # 기존 데이터가 없으면 무조건 새로운 것
    
#     # URL 기반으로 내용 매핑
#     old_by_url = {p["url"]: p.get("content", "") for p in old}
#     new_by_url = {p["url"]: p.get("content", "") for p in new}

#     # 1. URL 구성 자체가 달라졌는지 확인
#     if set(old_by_url.keys()) != set(new_by_url.keys()):
#         return True

#     # 2. 각 URL의 내용이 하나라도 바뀌었는지 해시값으로 비교
#     for url in new_by_url:
#         if fingerprint(old_by_url.get(url, "")) != fingerprint(new_by_url[url]):
#             return True
            
#     return False

# def has_changed(old: list[dict] | None, new: list[dict]) -> bool:
#     if not old: return True
    
#     # 각 URL별로 비교하지 않고, 모든 페이지의 텍스트를 하나로 합쳐서 비교합니다.
#     # 이렇게 하면 FAQ가 A페이지에서 B페이지로 옮겨가도 전체 내용이 같으면 "변경 없음"으로 뜹니다.
#     old_total = "".join([p.get("content", "") for p in old]).strip()
#     new_total = "".join([p.get("content", "") for p in new]).strip()

#     return fingerprint(old_total) != fingerprint(new_total)


import hashlib
import re

def normalize_text(text: str) -> str:
    """
    모든 공백, 줄바꿈, 특수문자를 제거하고 소문자로 통일하여 
    오직 '의미 있는 글자'만 남깁니다.
    """
    if not text:
        return ""
    # 1. XML 태그나 노이즈 패턴 제거 (이미 crawler에서 제거했겠지만 한 번 더 안전하게)
    text = re.sub(r"<\?xml.*?\?>", "", text)
    # 2. 공백, 줄바꿈, 탭 등 모든 화이트스페이스 제거
    text = re.sub(r"\s+", "", text)
    # 3. 소문자 변환
    return text.lower()

def has_changed(old: list[dict] | None, new: list[dict]) -> bool:
    if not old:
        return True

    # 1. 모든 페이지의 content를 하나의 거대한 텍스트 덩어리로 합칩니다.
    # URL 순서가 바뀌거나 내용이 이리저리 옮겨 다녀도 합계는 같습니다.
    old_corpus = "".join([p.get("content", "") for p in old])
    new_corpus = "".join([p.get("content", "") for p in new])

    # 2. 텍스트 정규화 (줄바꿈 하나 차이로 인한 해시 변경 방지)
    norm_old = normalize_text(old_corpus)
    norm_new = normalize_text(new_corpus)

    # 3. 정규화된 텍스트의 길이가 같고 내용이 같다면 변경 없음
    if len(norm_old) != len(norm_new):
        print(f"DEBUG: Length changed from {len(norm_old)} to {len(norm_new)}")
        return True
        
    return hashlib.sha256(norm_old.encode("utf-8")).hexdigest() != \
           hashlib.sha256(norm_new.encode("utf-8")).hexdigest()