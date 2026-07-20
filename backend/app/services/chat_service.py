"""对话服务：管理会话与流式消息"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

try:
    from langchain_core.messages import AIMessage, HumanMessage
except ModuleNotFoundError:  # pragma: no cover - optional agent dependency
    @dataclass
    class HumanMessage:
        content: str

    @dataclass
    class AIMessage:
        content: str


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return str(content)


def _extract_ai_content(payload: Any) -> str:
    if payload is None:
        return ""

    if isinstance(payload, AIMessage):
        return _content_to_text(payload.content)

    if isinstance(payload, dict):
        for key in ("chunk", "output"):
            text = _extract_ai_content(payload.get(key))
            if text:
                return text

        messages = payload.get("messages")
        if isinstance(messages, list):
            for message in reversed(messages):
                text = _extract_ai_content(message)
                if text:
                    return text

        for value in payload.values():
            text = _extract_ai_content(value)
            if text:
                return text

    if isinstance(payload, list):
        for item in reversed(payload):
            text = _extract_ai_content(item)
            if text:
                return text

    return ""


def _fallback_reply(user_message: str) -> str:
    text = user_message.strip()
    if any(word in text for word in ("你好", "您好", "hello", "Hello", "嗨")):
        return "你好，我是 CatTrace AI 助手。你可以问我校园猫档案、近期健康状态、领养建议，或者猫咪照护常识。"
    return "我暂时没有生成有效回复。你可以换一种说法，直接说明想查询猫咪档案、健康状态、领养建议或猫咪照护知识。"


def _sanitize_agent_response(content: str) -> str:
    text = content.strip()
    patterns = (
        r"^知识库中(?:暂未|暂无|没有|未)?(?:查询到|检索到|找到)?相关(?:内容|信息)[，,。；;：:\s]*(?:不过|但是|但)?",
        r"^平台知识库中(?:暂未|暂无|没有|未)?(?:查询到|检索到|找到)?相关(?:内容|信息)[，,。；;：:\s]*(?:不过|但是|但)?",
        r"^根据知识库(?:检索|查询)?(?:结果)?[，,。；;：:\s]*",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text, count=1)
    return text.strip() or content.strip()


@dataclass
class ChatSession:
    id: int
    user_id: int
    title: str
    messages: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ChatMessage:
    id: int
    session_id: int
    role: str  # user / assistant
    content: str
    created_at: float = field(default_factory=time.time)


class ChatService:
    """对话服务（内存版，联调后切换为数据库版）"""

    def __init__(self):
        self._sessions: dict[int, ChatSession] = {}
        self._messages: dict[int, list[ChatMessage]] = {}
        self._session_counter: int = 0
        self._message_counter: int = 0

    def create_session(self, user_id: int, title: str = "新对话") -> ChatSession:
        self._session_counter += 1
        session = ChatSession(
            id=self._session_counter,
            user_id=user_id,
            title=title,
        )
        self._sessions[session.id] = session
        self._messages[session.id] = []
        return session

    def get_session(self, session_id: int) -> ChatSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self, user_id: int) -> list[ChatSession]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    def delete_session(self, session_id: int) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._messages.pop(session_id, None)
            return True
        return False

    def get_messages(self, session_id: int) -> list[ChatMessage]:
        return self._messages.get(session_id, [])

    async def send_message_stream(
        self, session_id: int, user_message: str
    ) -> AsyncGenerator[str, None]:
        """发送消息并流式返回 Agent 响应（SSE 格式）。"""
        session = self._sessions.get(session_id)
        if not session:
            yield f"data: {json.dumps({'type': 'error', 'content': '会话不存在'}, ensure_ascii=False)}\n\n"
            return

        # 保存用户消息
        self._message_counter += 1
        user_msg = ChatMessage(
            id=self._message_counter,
            session_id=session_id,
            role="user",
            content=user_message,
        )
        self._messages[session_id].append(user_msg)
        session.messages.append(HumanMessage(content=user_message))

        # 构建历史消息（传给 Agent 图）
        history_messages = []
        for msg in self._messages[session_id]:
            if msg.role == "user":
                history_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                history_messages.append(AIMessage(content=msg.content))

        # 初始化状态
        initial_state = {
            "messages": history_messages,
            "next_agent": "",
            "detection_results": None,
            "analysis_report": None,
            "current_task": None,
        }

        try:
            from app.services.agent_graph import get_agent_graph
            graph = get_agent_graph()
        except ModuleNotFoundError as exc:
            message = f"智能体依赖未安装：{exc.name}。请根据 backend/pyproject.toml 安装 LangChain/LangGraph 相关依赖。"
            yield f"data: {json.dumps({'type': 'error', 'content': message}, ensure_ascii=False)}\n\n"
            return

        full_response = ""
        final_response = ""

        try:
            async for event in graph.astream_events(
                initial_state,
                config={"recursion_limit": 10},
                version="v2",
            ):
                event_kind = event["event"]

                # LLM token 流式输出
                if event_kind == "on_chat_model_stream":
                    # 跳过 Supervisor 的决策 JSON，不向前端推送
                    metadata = event.get("metadata", {})
                    if metadata.get("langgraph_node") == "supervisor":
                        continue
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        token = _content_to_text(chunk.content)
                        full_response += token
                        yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

                # 工具开始调用
                elif event_kind in {"on_chain_stream", "on_chain_end"}:
                    metadata = event.get("metadata", {})
                    if metadata.get("langgraph_node") == "supervisor":
                        continue
                    content = _extract_ai_content(event.get("data"))
                    if content:
                        final_response = _sanitize_agent_response(content)

                elif event_kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event["data"].get("input", {})
                    try:
                        safe_input = str(tool_input)
                    except Exception:
                        safe_input = "(无法序列化)"
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'input': safe_input}, ensure_ascii=False)}\n\n"

                # 工具调用完成
                elif event_kind == "on_tool_end":
                    tool_output = event["data"].get("output", "")
                    try:
                        safe_output = str(tool_output)[:500]
                    except Exception:
                        safe_output = "(无法序列化)"
                    yield f"data: {json.dumps({'type': 'tool_result', 'output': safe_output}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'处理出错：{str(e)}'}, ensure_ascii=False)}\n\n"
            return

        # 保存 AI 回复
        if not full_response and final_response:
            full_response = final_response
            yield f"data: {json.dumps({'type': 'token', 'content': final_response}, ensure_ascii=False)}\n\n"

        if not full_response:
            full_response = _fallback_reply(user_message)
            yield f"data: {json.dumps({'type': 'token', 'content': full_response}, ensure_ascii=False)}\n\n"

        if full_response:
            self._message_counter += 1
            ai_msg = ChatMessage(
                id=self._message_counter,
                session_id=session_id,
                role="assistant",
                content=full_response,
            )
            self._messages[session_id].append(ai_msg)
            session.messages.append(AIMessage(content=full_response))

        # 首次对话自动设置标题
        if len(self._messages[session_id]) <= 2 and len(user_message) > 0:
            session.title = user_message[:20] + ("..." if len(user_message) > 20 else "")

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"


# 全局实例
chat_service = ChatService()
