from fastapi import FastAPI, BackgroundTasks
from crawler import crawl
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"status": "running", "message": "Crawler API is ready!"}

@app.get("/run-crawl")
def run_api_crawl(urls: str):
    # 1. URL 리스트 파싱
    target_urls = [u.strip() for u in urls.split(",") if u.strip()]
    
    try:
        results = crawl(target_urls)
        return {
            "status": "success",
            "url_count": len(results),
            "data": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)