from crawler import crawl
from diff import has_changed
from storage import load_previous, save_snapshot

def main():
    print("Crawling URLs from urls.txt...")

    # 1. 새로운 크롤링 수행
    new_pages = crawl()
    if not new_pages:
        print("No URLs found in urls.txt. Add one URL per line.")
        return

    # 2. 기존 데이터 로드 (latest.json)
    old_pages = load_previous()

    # 3. 변경 사항 체크
    if has_changed(old_pages, new_pages):
        print("변경 사항이 감지되었습니다! 데이터를 갱신합니다.")
        # 내용이 바뀌었을 때만 저장
        save_snapshot(new_pages)
        print(f"Saved {len(new_pages)} page(s) to data/latest.json")
        
        # (옵션) 첫 페이지 내용 미리보기
        first = new_pages[0]
        preview = first.get("content", "")[:300]
        print(f"\n--- Preview ---\n{preview}\n...")
    else:
        # 내용이 같으면 저장하지 않고 종료
        print("변경된 내용이 없습니다. 새로운 파일을 생성하지 않습니다.")

if __name__ == "__main__":
    main()