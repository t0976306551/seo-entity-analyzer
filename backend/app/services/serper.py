# backend/app/services/serper.py
import httpx
from app.config import settings

SERPER_URL = "https://google.serper.dev/search"

async def search_google(keyword: str, api_key: str | None = None) -> list[dict]:
    key = api_key or settings.serper_api_key
    headers = {
        "X-API-KEY": key,
        "Content-Type": "application/json",
    }
    payload = {"q": keyword, "gl": "tw", "hl": "zh-tw", "num": 10}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(SERPER_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Serper API error: {response.status_code} {response.text}")

    data = response.json()
    results = []
    for item in data.get("organic", [])[:10]:
        results.append({
            "url": item.get("link", ""),
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
        })
    return results
