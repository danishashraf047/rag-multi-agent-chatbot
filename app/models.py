from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentRoute(StrEnum):
    RESEARCH = "research"
    CODING = "coding"
    RAG = "rag"
    PLANNING = "planning"
    DIRECT = "direct"


class Source(StrictBaseModel):
    title: str
    uri: str
    snippet: str


class AgentResult(BaseModel):
    agent: str
    summary: str
    output: dict[str, Any] = Field(default_factory=dict)
    sources: list[Source] = Field(default_factory=list)


class SupervisorDecision(StrictBaseModel):
    route: AgentRoute
    rationale: str
    rewritten_query: str


class ResearchOutput(StrictBaseModel):
    answer: str
    key_findings: list[str]
    sources: list[Source]


class CodingOutput(StrictBaseModel):
    explanation: str
    code_blocks: list[str]
    quality_notes: list[str]


class RAGOutput(StrictBaseModel):
    answer: str
    citations: list[Source]
    confidence: float = Field(ge=0.0, le=1.0)


class DelegationItem(StrictBaseModel):
    agent: AgentRoute
    task: str


class PlanOutput(StrictBaseModel):
    objective: str
    steps: list[str]
    delegation: list[DelegationItem]
    risks: list[str]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(default="default")
    stream: bool = False


class ChatResponse(BaseModel):
    session_id: str
    route: AgentRoute
    response: str
    agent_outputs: list[AgentResult] = Field(default_factory=list)
    error: str | None = None


class IngestRequest(BaseModel):
    paths: list[str] | None = None
    texts: list[str] | None = None
    metadatas: list[dict[str, Any]] | None = None


class IngestResponse(BaseModel):
    indexed_documents: int
    collection_name: str
