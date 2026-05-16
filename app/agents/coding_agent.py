from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import BaseAgent
from app.models import AgentResult, CodingOutput
from app.tools.coding_tools import python_syntax_check
from app.tools.document_tools import read_project_file


class CodingAgent(BaseAgent):
    name = "coding"

    async def run(self, query: str) -> AgentResult:
        async def execute() -> AgentResult:
            tools = [read_project_file, python_syntax_check]
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a senior coding agent. Generate Python/React code, review code "
                        "quality, and explain implementation tradeoffs. Use tools for project context "
                        "and syntax checks when relevant. Include empty arrays for code_blocks or "
                        "quality_notes when none are available.",
                    ),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad"),
                ],
            )
            agent = create_tool_calling_agent(self.llm, tools, prompt)
            executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
            raw = await executor.ainvoke({"input": query})
            structured_llm = self.llm.with_structured_output(CodingOutput)
            output = await structured_llm.ainvoke(
                f"Convert this coding result into structured output:\n{raw['output']}",
            )
            return AgentResult(
                agent=self.name,
                summary=output.explanation,
                output=output.model_dump(),
            )

        return await self.with_retry(execute)
