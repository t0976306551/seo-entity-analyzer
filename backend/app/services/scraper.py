# backend/app/services/scraper.py
import asyncio
import re
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-TW,zh;q=0.9",
}

async def fetch_article(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(url)

            if response.status_code != 200:
                return ""

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return ""

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:8000]

    except (httpx.TimeoutException, httpx.RequestError):
        return ""
    except Exception:
        return ""

async def fetch_articles_concurrent(urls: list[str]) -> list[str]:
    tasks = [fetch_article(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return list(results)
