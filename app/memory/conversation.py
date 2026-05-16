from collections import defaultdict, deque
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


@dataclass
class ConversationMemory:
    """Simple async-friendly process memory for recent conversation turns."""

    max_messages: int = 20
    _messages: dict[str, deque[BaseMessage]] = field(
        default_factory=lambda: defaultdict(deque),
    )

    async def load(self, session_id: str) -> list[BaseMessage]:
        return list(self._messages[session_id])

    async def append_user(self, session_id: str, content: str) -> None:
        await self._append(session_id, HumanMessage(content=content))

    async def append_ai(self, session_id: str, content: str) -> None:
        await self._append(session_id, AIMessage(content=content))

    async def _append(self, session_id: str, message: BaseMessage) -> None:
        queue = self._messages[session_id]
        queue.append(message)
        while len(queue) > self.max_messages:
            queue.popleft()
