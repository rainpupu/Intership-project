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
        if "recognition_records" not in tables:
            return

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
