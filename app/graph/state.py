from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from app.models import AgentResult, AgentRoute


class AgentState(TypedDict, total=False):
    request_id: str
    session_id: str
    user_input: str
    rewritten_query: str
    route: AgentRoute
    messages: Annotated[list[BaseMessage], add_messages]
    agent_outputs: list[AgentResult]
    final_response: str
    error: str | None
    metadata: dict[str, Any]
