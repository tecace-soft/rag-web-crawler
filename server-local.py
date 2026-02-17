from fastapi import FastAPI
from crawler import crawl
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Local Crawler API is running!"}

@app.get("/run-crawl")
def run_api_crawl(urls: str):
    target_urls = [u.strip() for u in urls.split(",") if u.strip()]
    try:
        # 업로드하신 crawler.py 로직 실행
        results = crawl(target_urls)
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)