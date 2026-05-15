# backend/tests/test_scraper.py
import pytest
import httpx
import respx
from app.services.scraper import fetch_article, fetch_articles_concurrent

HTML_CONTENT = """
<html><body>
<article>
<h1>台灣大哥大推出4G吃到飽方案</h1>
<p>台灣大哥大今日宣布推出全新4G吃到飽方案，月租費用為599元。</p>
<p>中華電信也提供類似方案，競爭激烈。</p>
</article>
</body></html>
"""

@pytest.mark.asyncio
@respx.mock
async def test_fetch_article_returns_text():
    respx.get("https://example.com/article").mock(
        return_value=httpx.Response(200, text=HTML_CONTENT, headers={"content-type": "text/html; charset=utf-8"})
    )
    result = await fetch_article("https://example.com/article")
    assert isinstance(result, str)
    assert "台灣大哥大" in result
    assert len(result) > 10

@pytest.mark.asyncio
@respx.mock
async def test_fetch_article_handles_timeout():
    respx.get("https://slow.example.com/").mock(side_effect=httpx.TimeoutException("timeout"))
    result = await fetch_article("https://slow.example.com/")
    assert result == ""

@pytest.mark.asyncio
@respx.mock
async def test_fetch_articles_concurrent_returns_list():
    urls = ["https://example1.com/", "https://example2.com/"]
    for url in urls:
        respx.get(url).mock(
            return_value=httpx.Response(200, text=HTML_CONTENT, headers={"content-type": "text/html; charset=utf-8"})
        )
    results = await fetch_articles_concurrent(urls)
    assert len(results) == 2
    assert all(isinstance(r, str) for r in results)
