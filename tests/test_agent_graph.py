"""智能体图结构测试（不依赖 LLM API）"""

import pytest
from backend.app.services.agent_graph import (
    AgentState,
    build_agent_graph,
    route_to_agent,
)


class TestGraphStructure:
    """图结构测试"""

    def test_build_graph_succeeds(self):
        graph = build_agent_graph()
        assert graph is not None

    def test_graph_has_required_nodes(self):
        graph = build_agent_graph()
        nodes = graph.get_graph().nodes
        node_names = {n for n in nodes.keys() if n != "__start__" and n != "__end__"}
        expected = {"supervisor", "cat_status_agent", "cat_query_agent", "adoption_agent", "knowledge_qa_agent"}
        assert expected.issubset(node_names), f"Missing nodes: {expected - node_names}"


class TestRouting:
    """路由决策测试"""

    def test_route_to_agent_valid(self):
        state = AgentState(
            messages=[],
            next_agent="cat_query_agent",
            detection_results=None,
            analysis_report=None,
            current_task=None,
        )
        assert route_to_agent(state) == "cat_query_agent"

    def test_route_to_agent_invalid(self):
        state = AgentState(
            messages=[],
            next_agent="invalid_agent",
            detection_results=None,
            analysis_report=None,
            current_task=None,
        )
        assert route_to_agent(state) == "end"

    def test_route_to_agent_end(self):
        state = AgentState(
            messages=[],
            next_agent="end",
            detection_results=None,
            analysis_report=None,
            current_task=None,
        )
        assert route_to_agent(state) == "end"


class TestAgentState:
    """状态模型测试"""

    def test_state_fields(self):
        state = AgentState(
            messages=[],
            next_agent="supervisor",
            detection_results=None,
            analysis_report=None,
            current_task=None,
        )
        assert state["messages"] == []
        assert state["next_agent"] == "supervisor"
        assert state["detection_results"] is None
