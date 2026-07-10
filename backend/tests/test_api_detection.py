"""
检测 API 端点测试：任务列表查询、用户隔离、场景管理
"""
import pytest
from app.database.session import get_db, Base
from app.services.user_service import user_service
from app.entity.db_models import DetectionScene, DetectionTask
from main import app


def _register_and_login(client, db, username="detuser", email="det@test.com"):
    """注册并登录，返回 (Authorization headers, user)"""
    user = user_service.register(db, username, email, "Password123")
    login_resp = client.post("/api/auth/login", json={
        "username": username,
        "password": "Password123",
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user


class TestDetectionTasks:
    """检测任务列表查询测试"""

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

    def test_get_tasks_empty(self, client, db):
        """GET /api/detection/tasks 空列表"""
        headers, _ = _register_and_login(client, db)
        response = client.get("/api/detection/tasks", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_tasks_unauthorized(self, client):
        """未认证时获取任务列表返回 401"""
        response = client.get("/api/detection/tasks")
        assert response.status_code == 401


class TestDetectionUserIsolation:
    """检测任务用户隔离测试"""

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

    def test_user_cannot_see_others_tasks(self, client, db):
        """用户 A 看不到用户 B 的检测任务"""
        headers_a, user_a = _register_and_login(client, db, "userA", "a@test.com")
        headers_b, user_b = _register_and_login(client, db, "userB", "b@test.com")

        scene = DetectionScene(
            name="test_scene",
            display_name="测试场景",
            category="test",
            class_names=["obj"],
            created_by=user_a.id,
        )
        db.add(scene)
        db.commit()
        db.refresh(scene)

        task = DetectionTask(
            user_id=user_a.id,
            scene_id=scene.id,
            task_type="single",
            status="completed",
            total_images=1,
            total_objects=5,
        )
        db.add(task)
        db.commit()

        response = client.get("/api/detection/tasks", headers=headers_b)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 0

        response = client.get("/api/detection/tasks", headers=headers_a)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 1

    def test_user_cannot_access_others_results(self, client, db):
        """用户 B 不能获取用户 A 的检测结果"""
        headers_a, user_a = _register_and_login(client, db, "userA2", "a2@test.com")
        headers_b, _ = _register_and_login(client, db, "userB2", "b2@test.com")

        scene = DetectionScene(
            name="test_scene2",
            display_name="测试场景2",
            category="test",
            class_names=["obj"],
            created_by=user_a.id,
        )
        db.add(scene)
        db.commit()
        db.refresh(scene)

        task = DetectionTask(
            user_id=user_a.id,
            scene_id=scene.id,
            task_type="single",
            status="completed",
            total_images=1,
            total_objects=1,
        )
        db.add(task)
        db.commit()

        response = client.get(f"/api/detection/tasks/{task.id}/results", headers=headers_b)
        assert response.status_code == 404


class TestDetectionScenes:
    """检测场景管理测试"""

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

    def test_get_scenes_empty(self, client, db):
        """获取场景列表（初始为空）"""
        headers, _ = _register_and_login(client, db)
        response = client.get("/api/detection/scenes", headers=headers)
        assert response.status_code == 200

    def test_get_scenes_unauthorized(self, client):
        """未认证获取场景返回 401"""
        response = client.get("/api/detection/scenes")
        assert response.status_code == 401
