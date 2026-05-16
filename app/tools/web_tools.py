import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool


@tool
async def fetch_url(url: str) -> str:
    """Fetch and summarize readable text from a URL."""

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:6000]
