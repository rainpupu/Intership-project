"""
Dashboard API 测试：验证用户数据隔离
确保每个用户只能看到自己的数据
"""
import pytest
from app.database.session import get_db
from main import app
from app.services.user_service import user_service
from app.entity.db_models import DetectionTask, TrainingTask, ChatSession, DetectionScene
from app.core.security import create_access_token


class TestDashboardDataIsolation:
    """Dashboard 数据隔离测试"""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """每个测试前重置数据库并覆盖依赖"""
        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        yield
        app.dependency_overrides.clear()

    def _create_user_and_token(self, db, username, email):
        """创建用户并生成 token"""
        user = user_service.register(db, username, email, "Password123")
        token = create_access_token(data={"sub": str(user.id)})
        return user, token

    def _create_scene(self, db, name, display_name, user_id):
        """创建检测场景"""
        scene = DetectionScene(
            name=name,
            display_name=display_name,
            description=f"测试场景 {name}",
            category="agriculture",
            class_names=["class_a", "class_b"],
            is_active=True,
            created_by=user_id,
        )
        db.add(scene)
        db.flush()
        return scene

    def _create_detection_task(self, db, user_id, scene_id, task_type="single"):
        """创建检测任务"""
        task = DetectionTask(
            user_id=user_id,
            scene_id=scene_id,
            task_type=task_type,
            status="completed",
            total_objects=5,
        )
        db.add(task)
        db.flush()
        return task

    def _create_training_task(self, db, user_id, scene_id):
        """创建训练任务"""
        import uuid
        task = TrainingTask(
            user_id=user_id,
            scene_id=scene_id,
            task_uuid=str(uuid.uuid4()),
            status="completed",
        )
        db.add(task)
        db.flush()
        return task

    def test_dashboard_only_shows_user_data(self, client, db):
        """用户 A 的 Dashboard 不应包含用户 B 的数据"""
        # 创建两个用户
        user_a, token_a = self._create_user_and_token(db, "userA", "a@test.com")
        user_b, token_b = self._create_user_and_token(db, "userB", "b@test.com")

        # 创建共享场景
        scene = self._create_scene(db, "test_scene", "测试场景", user_a.id)

        # 用户 A 有 3 个检测任务
        for _ in range(3):
            self._create_detection_task(db, user_a.id, scene.id)

        # 用户 B 有 5 个检测任务
        for _ in range(5):
            self._create_detection_task(db, user_b.id, scene.id)

        # 用户 A 有 1 个训练任务
        self._create_training_task(db, user_a.id, scene.id)

        # 用户 B 有 2 个训练任务
        for _ in range(2):
            self._create_training_task(db, user_b.id, scene.id)

        db.commit()

        # 用户 A 查看 Dashboard
        response = client.get(
            "/api/dashboard/stats",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证只看到用户 A 的数据
        assert data["overview"]["total_detections"] == 3
        assert data["overview"]["total_training"] == 1

    def test_dashboard_user_b_only_sees_own_data(self, client, db):
        """用户 B 的 Dashboard 不应包含用户 A 的数据"""
        user_a, token_a = self._create_user_and_token(db, "userA2", "a2@test.com")
        user_b, token_b = self._create_user_and_token(db, "userB2", "b2@test.com")

        scene = self._create_scene(db, "test_scene2", "测试场景2", user_a.id)

        for _ in range(3):
            self._create_detection_task(db, user_a.id, scene.id)
        for _ in range(5):
            self._create_detection_task(db, user_b.id, scene.id)

        db.commit()

        # 用户 B 查看 Dashboard
        response = client.get(
            "/api/dashboard/stats",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证只看到用户 B 的数据
        assert data["overview"]["total_detections"] == 5

    def test_dashboard_requires_auth(self, client):
        """未认证时访问 Dashboard 返回 401"""
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 401

    def test_dashboard_recent_detections_user_scoped(self, client, db):
        """最近检测任务只展示当前用户的"""
        user_a, token_a = self._create_user_and_token(db, "userRA", "ra@test.com")
        user_b, token_b = self._create_user_and_token(db, "userRB", "rb@test.com")

        scene = self._create_scene(db, "recent_scene", "最近场景", user_a.id)

        # 用户 A 有 2 个检测
        for _ in range(2):
            self._create_detection_task(db, user_a.id, scene.id)

        # 用户 B 有 10 个检测
        for _ in range(10):
            self._create_detection_task(db, user_b.id, scene.id)

        db.commit()

        response = client.get(
            "/api/dashboard/stats",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["recent_detections"]) == 2
