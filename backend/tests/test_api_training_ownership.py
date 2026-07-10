"""
训练 API 所有权校验测试
确保用户只能访问自己的训练任务
"""

import pytest
from app.database.session import get_db
from main import app
from app.services.user_service import user_service
from app.entity.db_models import DetectionScene, TrainingTask
from app.core.security import create_access_token


class TestTrainingOwnership:
    """训练任务所有权校验测试"""

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

    def _create_scene(self, db, name, user_id):
        """创建检测场景"""
        scene = DetectionScene(
            name=name,
            display_name=f"场景 {name}",
            description="测试场景",
            category="agriculture",
            class_names=["class_a", "class_b"],
            is_active=True,
            created_by=user_id,
        )
        db.add(scene)
        db.flush()
        return scene

    def _create_training_task(self, db, user_id, scene_id, task_uuid):
        """创建训练任务"""
        task = TrainingTask(
            user_id=user_id,
            scene_id=scene_id,
            task_uuid=task_uuid,
            status="completed",
        )
        db.add(task)
        db.flush()
        return task

    def test_get_task_detail_by_owner(self, client, db):
        """任务所有者可以查看任务详情"""
        user, token = self._create_user_and_token(db, "owner", "owner@test.com")
        scene = self._create_scene(db, "owner_scene", user.id)
        task = self._create_training_task(db, user.id, scene.id, "owner-task-1")
        db.commit()

        response = client.get(
            f"/api/training/tasks/{task.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_get_task_detail_by_non_owner_returns_404(self, client, db):
        """非任务所有者查看详情返回 404"""
        user_a, token_a = self._create_user_and_token(db, "userOwnA", "ownA@test.com")
        user_b, token_b = self._create_user_and_token(db, "userOwnB", "ownB@test.com")
        scene = self._create_scene(db, "shared_scene", user_a.id)
        task = self._create_training_task(db, user_a.id, scene.id, "owner-only-1")
        db.commit()

        # 用户 B 尝试访问用户 A 的任务
        response = client.get(
            f"/api/training/tasks/{task.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

    def test_get_task_status_by_non_owner_returns_404(self, client, db):
        """非任务所有者查看状态返回 404"""
        user_a, token_a = self._create_user_and_token(db, "userStatA", "statA@test.com")
        user_b, token_b = self._create_user_and_token(db, "userStatB", "statB@test.com")
        scene = self._create_scene(db, "stat_scene", user_a.id)
        task = self._create_training_task(db, user_a.id, scene.id, "stat-only-1")
        db.commit()

        response = client.get(
            f"/api/training/tasks/{task.id}/status",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

    def test_get_task_metrics_by_non_owner_returns_404(self, client, db):
        """非任务所有者查看指标返回 404"""
        user_a, token_a = self._create_user_and_token(db, "userMetA", "metA@test.com")
        user_b, token_b = self._create_user_and_token(db, "userMetB", "metB@test.com")
        scene = self._create_scene(db, "met_scene", user_a.id)
        task = self._create_training_task(db, user_a.id, scene.id, "met-only-1")
        db.commit()

        response = client.get(
            f"/api/training/tasks/{task.id}/metrics",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

    def test_validate_model_by_non_owner_returns_404(self, client, db):
        """非任务所有者调用模型评估返回 404"""
        user_a, token_a = self._create_user_and_token(db, "userValA", "valA@test.com")
        user_b, token_b = self._create_user_and_token(db, "userValB", "valB@test.com")
        scene = self._create_scene(db, "val_scene", user_a.id)
        task = self._create_training_task(db, user_a.id, scene.id, "val-only-1")
        db.commit()

        response = client.post(
            f"/api/training/tasks/{task.id}/validate",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"img_size": 640, "batch_size": 16},
        )
        assert response.status_code == 404

    def test_training_requires_auth(self, client):
        """未认证时访问训练接口返回 401"""
        response = client.get("/api/training/tasks/1")
        assert response.status_code == 401

    def test_start_training_by_non_owner_returns_404(self, client, db):
        """非任务所有者启动训练返回 404"""
        user_a, token_a = self._create_user_and_token(db, "userStA", "stA@test.com")
        user_b, token_b = self._create_user_and_token(db, "userStB", "stB@test.com")
        scene = self._create_scene(db, "start_scene", user_a.id)
        task = self._create_training_task(db, user_a.id, scene.id, "start-only-1")
        db.commit()

        response = client.post(
            f"/api/training/tasks/{task.id}/start",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

    def test_pause_training_by_non_owner_returns_404(self, client, db):
        """非任务所有者暂停训练返回 404"""
        user_a, token_a = self._create_user_and_token(db, "userPsA", "psA@test.com")
        user_b, token_b = self._create_user_and_token(db, "userPsB", "psB@test.com")
        scene = self._create_scene(db, "pause_scene", user_a.id)
        task = self._create_training_task(db, user_a.id, scene.id, "pause-only-1")
        db.commit()

        response = client.post(
            f"/api/training/tasks/{task.id}/pause",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

    def test_cancel_training_by_non_owner_returns_404(self, client, db):
        """非任务所有者取消训练返回 404"""
        user_a, token_a = self._create_user_and_token(db, "userCnA", "cnA@test.com")
        user_b, token_b = self._create_user_and_token(db, "userCnB", "cnB@test.com")
        scene = self._create_scene(db, "cancel_scene", user_a.id)
        task = self._create_training_task(db, user_a.id, scene.id, "cancel-only-1")
        db.commit()

        response = client.post(
            f"/api/training/tasks/{task.id}/cancel",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404
