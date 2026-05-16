import logging
import uuid
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.base import AgentError
from app.agents.coding_agent import CodingAgent
from app.agents.planner_agent import PlanningAgent
from app.agents.rag_agent import RAGAgent
from app.agents.research_agent import ResearchAgent
from app.agents.supervisor import SupervisorAgent
from app.config.settings import Settings
from app.graph.state import AgentState
from app.memory.conversation import ConversationMemory
from app.models import AgentResult, AgentRoute, ChatResponse


class MultiAgentWorkflow:
    """LangGraph workflow that shares state across all agents."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger("app.graph.workflow")
        self.memory = ConversationMemory()
        self.supervisor = SupervisorAgent(settings)
        self.research_agent = ResearchAgent(settings)
        self.coding_agent = CodingAgent(settings)
        self.rag_agent = RAGAgent(settings)
        self.planning_agent = PlanningAgent(settings)
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("load_memory", self._load_memory)
        builder.add_node("supervisor", self._supervisor)
        builder.add_node("research", self._research)
        builder.add_node("coding", self._coding)
        builder.add_node("rag", self._rag)
        builder.add_node("planning", self._planning)
        builder.add_node("direct", self._direct)
        builder.add_node("aggregate", self._aggregate)

        builder.set_entry_point("load_memory")
        builder.add_edge("load_memory", "supervisor")

        # LangGraph routing lives here: the supervisor writes `state["route"]`,
        # then conditional edges move the same shared state to exactly one
        # specialist node. Each specialist appends an AgentResult, and the
        # aggregate node combines those outputs into the final response.
        builder.add_conditional_edges(
            "supervisor",
            self._route_from_state,
            {
                AgentRoute.RESEARCH: "research",
                AgentRoute.CODING: "coding",
                AgentRoute.RAG: "rag",
                AgentRoute.PLANNING: "planning",
                AgentRoute.DIRECT: "direct",
            },
        )

        for node in ("research", "coding", "rag", "planning", "direct"):
            builder.add_edge(node, "aggregate")
        builder.add_edge("aggregate", END)
        return builder.compile(checkpointer=MemorySaver())

    async def ainvoke(self, message: str, session_id: str) -> ChatResponse:
        request_id = str(uuid.uuid4())
        initial_state: AgentState = {
            "request_id": request_id,
            "session_id": session_id,
            "user_input": message,
            "messages": [HumanMessage(content=message)],
            "agent_outputs": [],
            "metadata": {},
        }
        config = {"configurable": {"thread_id": session_id}}
        try:
            state = await self.graph.ainvoke(initial_state, config=config)
        except Exception as exc:
            self.logger.exception("workflow_failed", extra={"request_id": request_id})
            return ChatResponse(
                session_id=session_id,
                route=AgentRoute.DIRECT,
                response="I could not complete the request. Check server logs for details.",
                error=str(exc),
            )
        return ChatResponse(
            session_id=session_id,
            route=state.get("route", AgentRoute.DIRECT),
            response=state.get("final_response", ""),
            agent_outputs=state.get("agent_outputs", []),
            error=state.get("error"),
        )

    async def astream(self, message: str, session_id: str) -> AsyncIterator[dict]:
        request_id = str(uuid.uuid4())
        initial_state: AgentState = {
            "request_id": request_id,
            "session_id": session_id,
            "user_input": message,
            "messages": [HumanMessage(content=message)],
            "agent_outputs": [],
            "metadata": {},
        }
        config = {"configurable": {"thread_id": session_id}}
        async for update in self.graph.astream(initial_state, config=config, stream_mode="updates"):
            for node, payload in update.items():
                yield {"event": node, "data": self._jsonable(payload)}

    async def _load_memory(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        previous_messages = await self.memory.load(session_id)
        await self.memory.append_user(session_id, state["user_input"])
        return {"messages": previous_messages + state.get("messages", [])}

    async def _supervisor(self, state: AgentState) -> AgentState:
        decision = await self.supervisor.decide(state["user_input"])
        return {
            "route": decision.route,
            "rewritten_query": decision.rewritten_query,
            "metadata": {"supervisor_rationale": decision.rationale},
        }

    def _route_from_state(self, state: AgentState) -> AgentRoute:
        return state.get("route", AgentRoute.DIRECT)

    async def _research(self, state: AgentState) -> AgentState:
        return await self._run_specialist(state, self.research_agent.run)

    async def _coding(self, state: AgentState) -> AgentState:
        return await self._run_specialist(state, self.coding_agent.run)

    async def _rag(self, state: AgentState) -> AgentState:
        return await self._run_specialist(state, self.rag_agent.run)

    async def _planning(self, state: AgentState) -> AgentState:
        return await self._run_specialist(state, self.planning_agent.run)

    async def _direct(self, state: AgentState) -> AgentState:
        result = AgentResult(
            agent="direct",
            summary=state["rewritten_query"] or state["user_input"],
            output={"message": state["rewritten_query"] or state["user_input"]},
        )
        return {"agent_outputs": state.get("agent_outputs", []) + [result]}

    async def _run_specialist(self, state: AgentState, runner) -> AgentState:
        query = state.get("rewritten_query") or state["user_input"]
        try:
            result = await runner(query)
            return {"agent_outputs": state.get("agent_outputs", []) + [result]}
        except AgentError as exc:
            self.logger.exception("specialist_failed", extra={"route": state.get("route")})
            return {
                "error": str(exc),
                "agent_outputs": state.get("agent_outputs", []),
            }

    async def _aggregate(self, state: AgentState) -> AgentState:
        outputs = state.get("agent_outputs", [])
        if state.get("error") and not outputs:
            final = f"The {state.get('route', 'agent')} agent failed: {state['error']}"
        elif outputs:
            final = "\n\n".join(self._format_agent_result(result) for result in outputs)
        else:
            final = "I could not produce an answer."

        await self.memory.append_ai(state["session_id"], final)
        return {
            "final_response": final,
            "messages": [AIMessage(content=final)],
        }

    @staticmethod
    def _format_agent_result(result: AgentResult) -> str:
        output = result.output or {}
        parts = [result.summary]

        code_blocks = output.get("code_blocks") or []
        if code_blocks:
            parts.append(
                "\n\n".join(MultiAgentWorkflow._format_code_block(block) for block in code_blocks),
            )

        quality_notes = output.get("quality_notes") or []
        if quality_notes:
            notes = "\n".join(f"- {note}" for note in quality_notes)
            parts.append(f"Quality notes:\n{notes}")

        steps = output.get("steps") or []
        if steps and result.agent == "planning":
            plan = "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))
            parts.append(f"Execution plan:\n{plan}")

        key_findings = output.get("key_findings") or []
        if key_findings and result.agent == "research":
            findings = "\n".join(f"- {finding}" for finding in key_findings)
            parts.append(f"Key findings:\n{findings}")

        sources = result.sources or []
        if sources:
            source_lines = "\n".join(f"- {source.title}: {source.uri}" for source in sources)
            parts.append(f"Sources:\n{source_lines}")

        return "\n\n".join(part for part in parts if part)

    @staticmethod
    def _format_code_block(block: str) -> str:
        language = "python"
        stripped = block.strip()
        if stripped.startswith("```"):
            return stripped
        if "import React" in stripped or "export default" in stripped:
            language = "tsx"
        return f"```{language}\n{stripped}\n```"

    def _jsonable(self, payload):
        if isinstance(payload, dict):
            return {
                key: self._jsonable(value)
                for key, value in payload.items()
                if key != "messages"
            }
        if isinstance(payload, list):
            return [self._jsonable(item) for item in payload]
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        return payload
