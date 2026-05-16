import os

from app.config.settings import Settings


def configure_tracing(settings: Settings) -> None:
    """Enable LangSmith tracing when configured."""

    if settings.langsmith_tracing:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        if settings.langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
