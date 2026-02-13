import sys
from crawler import crawl
from diff import has_changed
from storage import load_previous, save_snapshot

def main():
    # 1. 인자 확인: 콤마로 구분된 URL 리스트가 들어왔는지 체크
    target_urls = None
    if len(sys.argv) > 1:
        raw_input = sys.argv[1].strip()
        if raw_input:
            # 콤마로 분리하여 리스트화
            target_urls = [u.strip() for u in raw_input.split(",") if u.strip()]
            print(f"Received URLs via command line: {target_urls}")

    if not target_urls:
        print("No command line arguments. Falling back to urls.txt...")

    # 2. 새로운 크롤링 수행 (crawl 함수에 URL 리스트 전달 가능하도록 수정 필요)
    try:
        new_pages = crawl(target_urls) # crawler.py의 crawl 함수가 리스트도 받게 수정됨
        if not new_pages:
            print("No pages crawled. Please check your URLs.")
            return
    except Exception as e:
        print(f"Crawling failed: {e}")
        sys.exit(1) # 에러 발생 시 종료 코드를 반환하여 GitHub Actions에 알림

    # 3. 기존 데이터 로드 및 변경 사항 체크
    old_pages = load_previous()

    # 3. 변경 사항 체크
    if has_changed(old_pages, new_pages):
        print("변경 사항이 감지되었습니다! 데이터를 갱신합니다.")
        # 내용이 바뀌었을 때만 저장
        save_snapshot(new_pages)
        print(f"Saved {len(new_pages)} page(s) to data/latest.json")
    else:
        print("변경된 내용이 없습니다.")

if __name__ == "__main__":
    main()