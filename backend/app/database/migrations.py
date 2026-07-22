from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.services.breed_name_service import normalize_breed_candidates, to_chinese_breed_name


def ensure_runtime_columns(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        tables = {
            row[0]
            for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        }
        if "recognition_records" in tables:
            existing_columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(recognition_records)")).fetchall()
            }
            if "health_status" not in existing_columns:
                connection.execute(text("ALTER TABLE recognition_records ADD COLUMN health_status VARCHAR(100)"))
            if "mood_status" not in existing_columns:
                connection.execute(text("ALTER TABLE recognition_records ADD COLUMN mood_status VARCHAR(100)"))
            if "observed_at" not in existing_columns:
                connection.execute(text("ALTER TABLE recognition_records ADD COLUMN observed_at DATETIME"))
            if "user_remark" not in existing_columns:
                connection.execute(text("ALTER TABLE recognition_records ADD COLUMN user_remark TEXT"))

        _normalize_breed_names(connection, tables)
        _cleanup_observation_descriptions(connection, tables)
        _backfill_observation_locations(connection, tables)


def _load_json(value):
    if value in (None, ""):
        return []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []


def _normalize_breed_names(connection, tables: set[str]) -> None:
    if "cats" in tables:
        rows = connection.execute(text("SELECT id, coat_color FROM cats")).fetchall()
        for row in rows:
            normalized = to_chinese_breed_name(row.coat_color)
            if normalized and normalized != row.coat_color:
                connection.execute(
                    text("UPDATE cats SET coat_color = :coat_color WHERE id = :id"),
                    {"coat_color": normalized, "id": row.id},
                )

    if "recognition_records" not in tables:
        return

    rows = connection.execute(text("SELECT id, cat_id, cat_name, candidates FROM recognition_records")).fetchall()
    for row in rows:
        candidates = normalize_breed_candidates(_load_json(row.candidates))
        updates = {"id": row.id}

        if candidates != _load_json(row.candidates):
            updates["candidates"] = json.dumps(candidates, ensure_ascii=False)

        normalized_cat_name = to_chinese_breed_name(row.cat_name)
        if row.cat_id and str(row.cat_id).startswith("breed-") and normalized_cat_name != row.cat_name:
            updates["cat_name"] = normalized_cat_name

        if len(updates) > 1:
            assignments = ", ".join(f"{key} = :{key}" for key in updates if key != "id")
            connection.execute(
                text(f"UPDATE recognition_records SET {assignments} WHERE id = :id"),
                updates,
            )


def _cleanup_observation_descriptions(connection, tables: set[str]) -> None:
    if "cat_observations" not in tables:
        return

    connection.execute(
        text(
            """
            UPDATE cat_observations
            SET description = NULL
            WHERE description LIKE '%demo%'
               OR description LIKE '%测试%'
               OR description LIKE '%展示%'
               OR description LIKE '%由识别流程%'
            """
        )
    )


def _backfill_observation_locations(connection, tables: set[str]) -> None:
    if "cat_observations" not in tables or "cats" not in tables:
        return

    connection.execute(
        text(
            """
            UPDATE cat_observations
            SET location = (
                SELECT cats.last_seen_location
                FROM cats
                WHERE cats.id = cat_observations.cat_id
            )
            WHERE (location IS NULL OR TRIM(location) = '' OR location = '用户上传')
              AND EXISTS (
                SELECT 1
                FROM cats
                WHERE cats.id = cat_observations.cat_id
                  AND cats.last_seen_location IS NOT NULL
                  AND TRIM(cats.last_seen_location) != ''
                  AND cats.last_seen_location != '用户上传'
              )
            """
        )
    )

    fallback_locations = {
        "橘子": "校门东侧长椅",
        "奶盖": "三号楼花坛",
        "小黑": "图书馆北门",
        "三花妹妹": "旧食堂后门",
        "狸花弟弟": "操场西南角",
        "白白": "研究生公寓门口",
    }
    for cat_name, location in fallback_locations.items():
        connection.execute(
            text(
                """
                UPDATE cat_observations
                SET location = :location
                WHERE (location IS NULL OR TRIM(location) = '' OR location = '用户上传')
                  AND cat_id IN (SELECT id FROM cats WHERE name = :cat_name)
                """
            ),
            {"location": location, "cat_name": cat_name},
        )
