"""LangGraph Agent 图（Supervisor 多 Agent 协作模式）"""

import json
import threading
from typing import Annotated, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from typing_extensions import TypedDict

from app.core.config import settings
from app.services.agent_prompts import (
    SUPERVISOR_SYSTEM_PROMPT,
    CAT_STATUS_SYSTEM_PROMPT,
    CAT_QUERY_SYSTEM_PROMPT,
    ADOPTION_SYSTEM_PROMPT,
    KNOWLEDGE_QA_SYSTEM_PROMPT,
)
from app.services.agent_tools import (
    search_cats,
    get_cat_profile,
    get_cat_observations,
    get_recent_encounters,
    recommend_adoption_cats,
    get_attention_cats,
    query_knowledge_base,
)


# ======== 状态定义 ========

class AgentState(TypedDict):
    messages: Annotated[list, "对话消息列表"]
    next_agent: Annotated[str, "下一个处理的 Agent"]
    detection_results: Annotated[Optional[dict], "检测结果（预留）"]
    analysis_report: Annotated[Optional[str], "分析报告（预留）"]
    current_task: Annotated[Optional[str], "当前任务类型"]


# ======== LLM 缓存 ========

_llm_cache: Optional[ChatOpenAI] = None
_llm_lock = threading.Lock()


def get_llm() -> ChatOpenAI:
    global _llm_cache
    if _llm_cache is not None:
        return _llm_cache
    with _llm_lock:
        if _llm_cache is not None:
            return _llm_cache
        _llm_cache = ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
            streaming=True,
        )
    return _llm_cache


# ======== 工具分组 ========

STATUS_TOOLS = [get_attention_cats, get_cat_profile, get_cat_observations, get_recent_encounters]
QUERY_TOOLS = [search_cats, get_cat_profile, get_recent_encounters, get_cat_observations]
ADOPTION_TOOLS = [recommend_adoption_cats, get_cat_profile, get_cat_observations, query_knowledge_base]
KNOWLEDGE_TOOLS = [query_knowledge_base]


# ======== Agent 缓存 ========

_agent_cache: dict = {}
_agent_lock = threading.Lock()


def _get_cached_agent(agent_name: str, prompt: str, tools: list):
    key = agent_name
    if key not in _agent_cache:
        with _agent_lock:
            if key not in _agent_cache:
                llm = get_llm()
                _agent_cache[key] = create_react_agent(llm, tools, prompt=prompt)
    return _agent_cache[key]


# ======== Supervisor 节点 ========

async def supervisor_node(state: AgentState) -> dict:
    """使用结构化输出判断用户意图，决定分发给哪个 Agent。"""
    llm = get_llm()
    messages = state["messages"]
    prompt_messages = [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)] + messages

    response = await llm.ainvoke(prompt_messages)
    content = response.content.strip() if hasattr(response, "content") else str(response)

    # 解析 JSON 决策
    try:
        decision = json.loads(content)
        next_agent = decision.get("next_agent", "end")
    except json.JSONDecodeError:
        # 兜底：关键词匹配
        content_lower = content.lower()
        if any(kw in content_lower for kw in ["状态", "健康", "关注"]):
            next_agent = "cat_status_agent"
        elif any(kw in content_lower for kw in ["领养", "推荐"]):
            next_agent = "adoption_agent"
        elif any(kw in content_lower for kw in ["查询", "搜索", "档案"]):
            next_agent = "cat_query_agent"
        elif any(kw in content_lower for kw in ["怎么", "为什么", "什么"]):
            next_agent = "knowledge_qa_agent"
        else:
            next_agent = "end"

    valid_agents = {"cat_status_agent", "cat_query_agent", "adoption_agent", "knowledge_qa_agent", "end"}
    if next_agent not in valid_agents:
        next_agent = "end"

    return {"next_agent": next_agent}


# ======== 专业 Agent 节点 ========

async def _run_agent(state: AgentState, agent_name: str, system_prompt: str, tools: list) -> dict:
    agent = _get_cached_agent(agent_name, system_prompt, tools)
    messages = state["messages"]
    result = await agent.ainvoke({"messages": list(messages)})

    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    response_content = ai_messages[-1].content if ai_messages else "处理完成。"

    return {"messages": [AIMessage(content=response_content)]}


async def cat_status_agent_node(state: AgentState) -> dict:
    return await _run_agent(state, "cat_status", CAT_STATUS_SYSTEM_PROMPT, STATUS_TOOLS)


async def cat_query_agent_node(state: AgentState) -> dict:
    return await _run_agent(state, "cat_query", CAT_QUERY_SYSTEM_PROMPT, QUERY_TOOLS)


async def adoption_agent_node(state: AgentState) -> dict:
    return await _run_agent(state, "adoption", ADOPTION_SYSTEM_PROMPT, ADOPTION_TOOLS)


async def knowledge_qa_agent_node(state: AgentState) -> dict:
    return await _run_agent(state, "knowledge_qa", KNOWLEDGE_QA_SYSTEM_PROMPT, KNOWLEDGE_TOOLS)


# ======== 路由函数 ========

def route_to_agent(state: AgentState) -> str:
    next_agent = state.get("next_agent", "end")
    valid = {"cat_status_agent", "cat_query_agent", "adoption_agent", "knowledge_qa_agent", "end"}
    return next_agent if next_agent in valid else "end"


# ======== 图构建 ========

_graph_cache: Optional[any] = None
_graph_lock = threading.Lock()


def build_agent_graph():
    """构建 Supervisor 多 Agent 协作图。"""
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("cat_status_agent", cat_status_agent_node)
    graph.add_node("cat_query_agent", cat_query_agent_node)
    graph.add_node("adoption_agent", adoption_agent_node)
    graph.add_node("knowledge_qa_agent", knowledge_qa_agent_node)

    # 入口
    graph.set_entry_point("supervisor")

    # Supervisor 条件路由
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "cat_status_agent": "cat_status_agent",
            "cat_query_agent": "cat_query_agent",
            "adoption_agent": "adoption_agent",
            "knowledge_qa_agent": "knowledge_qa_agent",
            "end": END,
        },
    )

    # 各 Agent 完成后回到 Supervisor（用于多轮任务），或结束
    graph.add_edge("cat_status_agent", END)
    graph.add_edge("cat_query_agent", END)
    graph.add_edge("adoption_agent", END)
    graph.add_edge("knowledge_qa_agent", END)

    return graph.compile()


def get_agent_graph():
    global _graph_cache
    if _graph_cache is None:
        with _graph_lock:
            if _graph_cache is None:
                _graph_cache = build_agent_graph()
    return _graph_cache
