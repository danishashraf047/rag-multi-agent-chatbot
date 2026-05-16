from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import BaseAgent
from app.models import AgentResult, ResearchOutput, Source
from app.tools.document_tools import search_local_documents
from app.tools.web_tools import deployment_options_reference, fetch_url


class ResearchAgent(BaseAgent):
    name = "research"

    async def run(self, query: str) -> AgentResult:
        async def execute() -> AgentResult:
            tools = [search_local_documents, fetch_url, deployment_options_reference]
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a research agent. Use tools when useful, summarize findings, "
                        "and cite sources as title/uri/snippet when available. If web access is "
                        "unavailable, use local documents and built-in reference tools, then clearly "
                        "say that live web retrieval was unavailable.",
                    ),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad"),
                ],
            )
            agent = create_tool_calling_agent(self.llm, tools, prompt)
            executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
            raw = await executor.ainvoke({"input": query})
            structured_llm = self.llm.with_structured_output(ResearchOutput)
            output = await structured_llm.ainvoke(
                f"Convert this research result into structured output:\n{raw['output']}",
            )
            return AgentResult(
                agent=self.name,
                summary=output.answer,
                output=output.model_dump(),
                sources=output.sources,
            )

        return await self.with_retry(execute)
