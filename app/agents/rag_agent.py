from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models import AgentResult, RAGOutput, Source
from app.rag.vector_store import VectorStoreService


class RAGAgent(BaseAgent):
    name = "rag"

    def __init__(self, settings, vector_store: VectorStoreService | None = None) -> None:
        super().__init__(settings)
        self.vector_store = vector_store or VectorStoreService(settings)

    async def run(self, query: str) -> AgentResult:
        async def execute() -> AgentResult:
            documents = await self.vector_store.retrieve(query)
            context = "\n\n".join(
                f"Source: {doc.metadata.get('source', 'vector-store')}\n{doc.page_content}"
                for doc in documents
            )
            structured_llm = self.llm.with_structured_output(RAGOutput)
            output = await structured_llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are a RAG agent. Answer using only the provided context. "
                            "If the context is insufficient, say what is missing."
                        ),
                    ),
                    HumanMessage(content=f"Question: {query}\n\nContext:\n{context}"),
                ],
            )
            citations = [
                Source(
                    title=str(doc.metadata.get("title", "Retrieved chunk")),
                    uri=str(doc.metadata.get("source", "chroma")),
                    snippet=doc.page_content[:240],
                )
                for doc in documents
            ]
            if not output.citations:
                output.citations = citations
            return AgentResult(
                agent=self.name,
                summary=output.answer,
                output=output.model_dump(),
                sources=output.citations,
            )

        return await self.with_retry(execute)
