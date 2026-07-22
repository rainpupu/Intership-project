"""测试配置文件"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
TEST_DB = PROJECT_ROOT / "tests" / ".test_cattrace.db"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))

if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

from app.database.session import Base, SessionLocal, engine  # noqa: E402
from app.entity.db_models import Cat, CatObservation  # noqa: E402


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _seed_agent_tool_data() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cats = [
            Cat(
                code="CAT-20240001",
                name="大橘",
                coat_color="橘白",
                age_stage="成年",
                gender="公",
                personality_tags=["亲人", "贪吃", "佛系"],
                adoption_status="待领养",
                last_seen_location="图书馆门口",
                last_seen_at=_dt("2026-07-13T15:30:00"),
                description="校园图书馆常驻猫咪，性格温和亲人，喜欢晒太阳。",
            ),
            Cat(
                code="CAT-20240002",
                name="芝麻",
                coat_color="玳瑁",
                age_stage="幼猫",
                gender="母",
                personality_tags=["胆小", "活泼", "好奇"],
                adoption_status="观察中",
                last_seen_location="食堂后灌木丛",
                last_seen_at=_dt("2026-07-14T08:00:00"),
                description="今年春天出生的小玳瑁，逐渐开始靠近人类。",
            ),
            Cat(
                code="CAT-20240003",
                name="奶茶",
                coat_color="乳白",
                age_stage="成年",
                gender="母",
                personality_tags=["优雅", "独立", "温和"],
                adoption_status="已领养",
                last_seen_location="学生宿舍",
                last_seen_at=_dt("2026-07-10T10:00:00"),
                description="优雅的乳白色猫咪，已经被学生领养。",
            ),
            Cat(
                code="CAT-20240004",
                name="黑仔",
                coat_color="纯黑",
                age_stage="成年",
                gender="公",
                personality_tags=["神秘", "独立", "夜间活跃"],
                adoption_status="待领养",
                last_seen_location="操场附近",
                last_seen_at=_dt("2026-07-08T21:00:00"),
                description="纯黑公猫，主要在夜间出没。",
            ),
            Cat(
                code="CAT-20240005",
                name="花花",
                coat_color="三花",
                age_stage="成年",
                gender="母",
                personality_tags=["粘人", "话多", "温柔"],
                adoption_status="待领养",
                last_seen_location="宿舍楼 C 区",
                last_seen_at=_dt("2026-07-12T18:45:00"),
                description="三花母猫，非常粘人，喜欢跟着人走。",
            ),
        ]
        db.add_all(cats)
        db.flush()

        db.add_all(
            [
                CatObservation(
                    cat_id=cats[0].id,
                    location="图书馆门口",
                    mood_status="放松",
                    health_status="健康良好",
                    observed_at=_dt("2026-07-13T15:30:00"),
                    description="主动靠近志愿者，进食正常。",
                ),
                CatObservation(
                    cat_id=cats[0].id,
                    location="图书馆西侧花坛",
                    mood_status="放松",
                    health_status="健康良好",
                    observed_at=_dt("2026-07-10T12:15:00"),
                    description="在花坛附近晒太阳。",
                ),
                CatObservation(
                    cat_id=cats[1].id,
                    location="食堂后灌木丛",
                    mood_status="紧张",
                    health_status="异常",
                    observed_at=_dt("2026-07-14T08:00:00"),
                    description="健康需关注，建议继续观察食欲。",
                ),
                CatObservation(
                    cat_id=cats[4].id,
                    location="宿舍楼 C 区",
                    mood_status="稳定",
                    health_status="健康良好",
                    observed_at=_dt("2026-07-12T18:45:00"),
                    description="正常活动。",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


_seed_agent_tool_data()
