**1) use this script to start the github actions process:
**
$headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "Bearer YOUR-API-KEY-TOKEN-GOES-HERE" # CHANGE HERE
    "X-GitHub-Api-Version" = "2022-11-28"
}

$body = @{
    event_type = "run-crawler"
    client_payload = @{
        urls = "YOUR-URLS-GO-HERE-SEPARATE-EACH-URL-WITH-COMMA" # CHANGE HERE
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.github.com/repos/tecace-soft/rag-web-crawler/dispatches" `
      -Method Post `
      -Headers $headers `
      -Body $body

Write-Host "크롤러에 URL 리스트를 보냈습니다!" -ForegroundColor Green


**2) output can be accessible from here:
**   
https://raw.githubusercontent.com/tecace-soft/rag-web-crawler/main/data/latest.json?v=1
NOTE: githubusercontent doesnt show the latest json file change right away, and it usually takes more than 5 mins due to CDN cache. adding "?v=1" to bypass this issue.
