from crawler import crawl
from diff import has_changed
from storage import load_previous, save_snapshot


def main():
    print("Crawling URLs from urls.txt...")

    new_pages = crawl()
    if not new_pages:
        print("No URLs found in urls.txt. Add one URL per line.")
        return

    old_pages = load_previous()

    if has_changed(old_pages, new_pages):
        print("Content changed!")
        first = new_pages[0]
        preview = first.get("content", "")[:300]
        print(preview)
    else:
        print("No changes detected")

    save_snapshot(new_pages)
    print(f"Saved {len(new_pages)} page(s) to data/latest.json")


if __name__ == "__main__":
    main()
