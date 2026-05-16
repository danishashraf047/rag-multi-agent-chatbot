from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models import AgentRoute, SupervisorDecision


class SupervisorAgent(BaseAgent):
    name = "supervisor"

    async def decide(self, user_input: str) -> SupervisorDecision:
        async def run() -> SupervisorDecision:
            structured_llm = self.llm.with_structured_output(SupervisorDecision)
            result = await structured_llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are a supervisor for a multi-agent AI system. "
                            "Classify the user request into exactly one route: "
                            "research for fact finding and web/document search, "
                            "coding for code generation/review/explanation, "
                            "rag for questions that should be answered from an indexed knowledge base, "
                            "planning for complex multi-step execution plans, "
                            "direct for simple conversation. Rewrite the query for the specialist."
                        ),
                    ),
                    HumanMessage(content=user_input),
                ],
            )
            return result

        decision = await self.with_retry(run)
        if decision.route not in set(AgentRoute):
            decision.route = AgentRoute.DIRECT
        return decision
