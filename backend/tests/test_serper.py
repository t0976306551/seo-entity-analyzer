# backend/tests/test_serper.py
import pytest
import httpx
import respx
from app.services.serper import search_google

MOCK_RESPONSE = {
    "organic": [
        {"link": "https://example1.com", "title": "文章1", "snippet": "摘要1"},
        {"link": "https://example2.com", "title": "文章2", "snippet": "摘要2"},
    ]
}

@pytest.mark.asyncio
@respx.mock
async def test_search_returns_list_of_urls():
    respx.post("https://google.serper.dev/search").mock(
        return_value=httpx.Response(200, json=MOCK_RESPONSE)
    )
    results = await search_google("4G吃到飽", api_key="test_key")
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["url"] == "https://example1.com"
    assert results[0]["title"] == "文章1"

@pytest.mark.asyncio
@respx.mock
async def test_search_limits_to_10_results():
    mock_data = {"organic": [{"link": f"https://example{i}.com", "title": f"文章{i}", "snippet": ""} for i in range(15)]}
    respx.post("https://google.serper.dev/search").mock(
        return_value=httpx.Response(200, json=mock_data)
    )
    results = await search_google("test", api_key="test_key")
    assert len(results) <= 10

@pytest.mark.asyncio
@respx.mock
async def test_search_handles_api_error():
    respx.post("https://google.serper.dev/search").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    with pytest.raises(Exception, match="Serper API error"):
        await search_google("test", api_key="bad_key")
