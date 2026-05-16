from pathlib import Path

from langchain_core.tools import tool

from app.config.settings import get_settings


@tool
async def search_local_documents(query: str) -> str:
    """Search local .txt and .md documents for relevant lines."""

    settings = get_settings()
    docs_dir = settings.documents_dir
    if not docs_dir.exists():
        return "No local documents directory exists yet."

    terms = [term.lower() for term in query.split() if len(term) > 2]
    matches: list[str] = []
    for path in docs_dir.rglob("*"):
        if path.suffix.lower() not in {".txt", ".md"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            if any(term in lower for term in terms):
                matches.append(f"{path}:{line_no}: {line[:300]}")
            if len(matches) >= 12:
                return "\n".join(matches)

    return "\n".join(matches) if matches else "No local document matches found."


@tool
async def read_project_file(path: str) -> str:
    """Read a project file for code review or implementation context."""

    root = Path.cwd().resolve()
    target = (root / path).resolve()
    if root not in target.parents and target != root:
        return "Refusing to read files outside the project root."
    if not target.exists() or not target.is_file():
        return f"File not found: {path}"
    return target.read_text(encoding="utf-8", errors="ignore")[:8000]
