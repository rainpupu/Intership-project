"""
对话 API 端点测试：会话 CRUD、消息发送、权限校验
"""
import pytest
from app.database.session import get_db, Base
from app.services.user_service import user_service
from main import app


def _register_and_login(client, db, username="chatuser", email="chat@test.com"):
    """注册并登录，返回 Authorization headers"""
    user_service.register(db, username, email, "Password123")
    login_resp = client.post("/api/auth/login", json={
        "username": username,
        "password": "Password123",
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestChatSessionCRUD:
    """对话会话 CRUD 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        yield
        app.dependency_overrides.clear()

    def test_create_session(self, client, db):
        """POST /api/chat/sessions 创建会话"""
        headers = _register_and_login(client, db)
        response = client.post("/api/chat/sessions", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "session_id" in data
        assert "session_uuid" in data

    def test_create_session_with_title(self, client, db):
        """创建带标题的会话"""
        headers = _register_and_login(client, db)
        response = client.post(
            "/api/chat/sessions?title=测试会话",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "测试会话"

    def test_get_sessions(self, client, db):
        """GET /api/chat/sessions 获取会话列表"""
        headers = _register_and_login(client, db)
        client.post("/api/chat/sessions", headers=headers)
        client.post("/api/chat/sessions", headers=headers)
        response = client.get("/api/chat/sessions", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 2

    def test_delete_session(self, client, db):
        """DELETE /api/chat/sessions/{id} 删除会话"""
        headers = _register_and_login(client, db)
        create_res = client.post("/api/chat/sessions", headers=headers)
        session_id = create_res.json()["data"]["session_id"]
        response = client.delete(f"/api/chat/sessions/{session_id}", headers=headers)
        assert response.status_code == 200

    def test_delete_nonexistent_session(self, client, db):
        """删除不存在的会话返回 404"""
        headers = _register_and_login(client, db)
        response = client.delete("/api/chat/sessions/99999", headers=headers)
        assert response.status_code == 404


class TestChatMessages:
    """对话消息测试"""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        yield
        app.dependency_overrides.clear()

    def test_get_messages_empty(self, client, db):
        """获取空会话的消息列表"""
        headers = _register_and_login(client, db)
        create_res = client.post("/api/chat/sessions", headers=headers)
        session_id = create_res.json()["data"]["session_id"]
        response = client.get(f"/api/chat/sessions/{session_id}/messages", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["messages"] == [] or len(data["messages"]) == 0

    def test_get_messages_other_user_session(self, client, db):
        """访问其他用户的会话返回 404"""
        headers_a = _register_and_login(client, db, "userA", "a@test.com")
        create_res = client.post("/api/chat/sessions", headers=headers_a)
        session_id = create_res.json()["data"]["session_id"]
        headers_b = _register_and_login(client, db, "userB", "b@test.com")
        response = client.get(f"/api/chat/sessions/{session_id}/messages", headers=headers_b)
        assert response.status_code == 404


class TestChatAuth:
    """对话 API 认证测试"""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        yield
        app.dependency_overrides.clear()

    def test_create_session_unauthorized(self, client):
        """未认证时创建会话返回 401"""
        response = client.post("/api/chat/sessions")
        assert response.status_code == 401

    def test_get_sessions_unauthorized(self, client):
        """未认证时获取会话列表返回 401"""
        response = client.get("/api/chat/sessions")
        assert response.status_code == 401
