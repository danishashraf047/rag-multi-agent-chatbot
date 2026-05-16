import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool


@tool
async def fetch_url(url: str) -> str:
    """Fetch and summarize readable text from a URL."""

    if not url.startswith(("http://", "https://")):
        return "Invalid URL. Provide a full URL beginning with http:// or https://."

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Unable to fetch URL due to a network or HTTP error: {exc}"

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:6000]


@tool
async def deployment_options_reference(topic: str) -> str:
    """Return built-in research notes for common FastAPI deployment tradeoffs."""

    return (
        f"Built-in deployment research notes for: {topic}\n"
        "FastAPI deployment options and tradeoffs:\n"
        "1. Uvicorn directly: simplest for local development and small internal services, "
        "but production setups usually need a process manager, reverse proxy, and restart policy.\n"
        "2. Gunicorn with Uvicorn workers: mature process management, multiple workers, graceful "
        "restarts, and better CPU utilization on a VM. It adds configuration complexity.\n"
        "3. Docker container: portable, repeatable builds and easy CI/CD integration. Requires image "
        "builds, registry management, container security updates, and external persistence.\n"
        "4. Managed container platforms such as Render, Fly.io, Railway, Cloud Run, Azure Container "
        "Apps, or AWS App Runner: fast deployment and autoscaling with less server maintenance. "
        "Tradeoffs include platform limits, cold starts, and provider-specific networking/secrets.\n"
        "5. Kubernetes: strong orchestration, scaling, rollouts, and service discovery for larger "
        "systems. It is operationally heavy for small apps.\n"
        "6. Traditional VM with Nginx/Caddy plus systemd: predictable and flexible, good for one or "
        "a few services. You own patching, monitoring, TLS, backups, and scaling.\n"
        "7. Serverless functions: useful for event-driven or bursty workloads, but less natural for "
        "long-lived streaming responses, WebSockets, and heavy model clients.\n"
        "Production recommendations: run behind HTTPS, keep secrets in environment or secret stores, "
        "add health checks, structured logs, request timeouts, graceful shutdown, persistent storage "
        "for ChromaDB, and external memory/storage when running more than one replica."
    )
