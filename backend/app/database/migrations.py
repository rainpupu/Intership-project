from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine


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
