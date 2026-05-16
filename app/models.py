from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentRoute(StrEnum):
    RESEARCH = "research"
    CODING = "coding"
    RAG = "rag"
    PLANNING = "planning"
    DIRECT = "direct"


class Source(BaseModel):
    title: str
    uri: str
    snippet: str = ""


class AgentResult(BaseModel):
    agent: str
    summary: str
    output: dict[str, Any] = Field(default_factory=dict)
    sources: list[Source] = Field(default_factory=list)


class SupervisorDecision(BaseModel):
    route: AgentRoute
    rationale: str
    rewritten_query: str


class ResearchOutput(BaseModel):
    answer: str
    key_findings: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)


class CodingOutput(BaseModel):
    explanation: str
    code_blocks: list[str] = Field(default_factory=list)
    quality_notes: list[str] = Field(default_factory=list)


class RAGOutput(BaseModel):
    answer: str
    citations: list[Source] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PlanOutput(BaseModel):
    objective: str
    steps: list[str]
    delegation: dict[str, str] = Field(default_factory=dict)
    risks: list[str] = Field(default_factory=list)


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
