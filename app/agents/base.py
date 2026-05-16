import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from langchain_openai import ChatOpenAI

from app.config.settings import Settings

T = TypeVar("T")


class AgentError(RuntimeError):
    """Raised when an agent cannot complete its task."""


class BaseAgent:
    name = "base"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(f"app.agents.{self.name}")
        if not settings.openai_api_key:
            raise AgentError("OPENAI_API_KEY is required to run OpenAI agents.")
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            timeout=settings.request_timeout_seconds,
            max_retries=0,
            temperature=0.2,
            streaming=True,
        )

    async def with_retry(self, operation: Callable[[], Awaitable[T]]) -> T:
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                return await operation()
            except Exception as exc:
                last_error = exc
                self.logger.warning(
                    "agent_attempt_failed",
                    extra={"agent": self.name, "attempt": attempt + 1, "error": str(exc)},
                )
                if attempt < self.settings.max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
        raise AgentError(f"{self.name} failed: {last_error}") from last_error
