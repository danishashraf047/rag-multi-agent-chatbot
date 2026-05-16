from app.graph.workflow import MultiAgentWorkflow
from app.models import AgentRoute


def test_route_from_state_without_constructing_workflow():
    route = MultiAgentWorkflow._route_from_state(
        object(),
        {"route": AgentRoute.RESEARCH},
    )
    assert route == AgentRoute.RESEARCH


def test_route_defaults_to_direct():
    route = MultiAgentWorkflow._route_from_state(object(), {})
    assert route == AgentRoute.DIRECT
