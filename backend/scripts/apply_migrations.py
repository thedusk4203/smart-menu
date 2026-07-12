from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlmodel import Session

from app.core.database import engine


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "data" / "migrations"
MIGRATION_ORDER = (
    "002_admin.sql",
    "003_import_codes.sql",
    "20260710_dish_planner_v2.sql",
    "20260711_ai_provider_admin.sql",
    "20260711_ai_conversations.sql",
    "20260711_ai_conversation_nonempty_answers.sql",
    "20260711_google_gemini_provider.sql",
    "20260712_menu_names_tags_shares.sql",
    "20260712_ai_conversation_retention.sql",
)


def main() -> None:
    known = [MIGRATIONS_DIR / name for name in MIGRATION_ORDER]
    unknown = sorted(
        path for path in MIGRATIONS_DIR.glob("*.sql")
        if path.is_file() and path.name not in MIGRATION_ORDER
    )
    migration_files = [path for path in known if path.is_file()] + unknown
    with Session(engine) as session:
        session.execute(
            text(
                """CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )"""
            )
        )
        session.commit()
        applied = {
            row[0]
            for row in session.execute(text("SELECT version FROM schema_migrations"))
        }

    for path in migration_files:
        if path.name in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(sql)
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": path.name},
            )
        print(f"Applied {path.name}")


if __name__ == "__main__":
    main()
