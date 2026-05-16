from app.graph.workflow import MultiAgentWorkflow
from app.models import AgentResult, AgentRoute, PlanOutput


def test_route_from_state_without_constructing_workflow():
    route = MultiAgentWorkflow._route_from_state(
        object(),
        {"route": AgentRoute.RESEARCH},
    )
    assert route == AgentRoute.RESEARCH


def test_route_defaults_to_direct():
    route = MultiAgentWorkflow._route_from_state(object(), {})
    assert route == AgentRoute.DIRECT


def test_format_agent_result_includes_coding_blocks():
    result = AgentResult(
        agent="coding",
        summary="Here is the implementation.",
        output={
            "code_blocks": [
                "def add(a: int, b: int) -> int:\n    return a + b",
            ],
            "quality_notes": ["Uses type hints."],
        },
    )

    formatted = MultiAgentWorkflow._format_agent_result(result)

    assert "Here is the implementation." in formatted
    assert "```python" in formatted
    assert "def add" in formatted
    assert "Quality notes:" in formatted


def test_plan_output_schema_requires_every_property():
    schema = PlanOutput.model_json_schema()

    assert set(schema["required"]) == set(schema["properties"])
    assert schema["properties"]["delegation"]["type"] == "array"
