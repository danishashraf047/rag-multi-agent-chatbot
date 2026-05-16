from app.tools.web_tools import fetch_url


async def test_fetch_url_rejects_non_url_input():
    result = await fetch_url.ainvoke({"url": "FastAPI deployment options"})

    assert "Invalid URL" in result
