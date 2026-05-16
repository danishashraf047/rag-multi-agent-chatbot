from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models import AgentResult, PlanOutput


class PlanningAgent(BaseAgent):
    name = "planning"

    async def run(self, query: str) -> AgentResult:
        async def execute() -> AgentResult:
            structured_llm = self.llm.with_structured_output(PlanOutput)
            output = await structured_llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are a planning agent. Break complex work into ordered subtasks. "
                            "Assign delegation items to one of these routes only: research, coding, "
                            "rag, planning, or direct. Include empty arrays if there are no risks or "
                            "delegation items."
                        ),
                    ),
                    HumanMessage(content=query),
                ],
            )
            return AgentResult(
                agent=self.name,
                summary=f"Plan for {output.objective}",
                output=output.model_dump(),
            )

        return await self.with_retry(execute)
