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
    "20260713_typed_import_tags.sql",
)

MANUAL_SCRIPTS = {"20260713_reset_food_catalog.sql"}


def main() -> None:
    known = [MIGRATIONS_DIR / name for name in MIGRATION_ORDER]
    unknown = sorted(
        path for path in MIGRATIONS_DIR.glob("*.sql")
        if path.is_file() and path.name not in MIGRATION_ORDER and path.name not in MANUAL_SCRIPTS
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
        # Database được tạo từ init_db.sql đã chứa toàn bộ schema lịch sử nhưng
        # có thể chưa có bảng theo dõi migration. Khi các mốc cuối đã hiện diện,
        # ghi nhận baseline thay vì chạy lại các migration phá/tạo view cũ.
        baseline_markers = (
            "public.v_dish_candidates",
            "public.tag_catalog",
            "public.shopping_list_shares",
            "public.llm_provider_configs",
            "public.ai_conversations",
        )
        has_full_baseline = all(
            session.execute(text("SELECT to_regclass(:name)"), {"name": marker}).scalar_one() is not None
            for marker in baseline_markers
        )
        if has_full_baseline and "20260713_typed_import_tags.sql" not in applied:
            for version in MIGRATION_ORDER[:-1]:
                session.execute(
                    text("""INSERT INTO schema_migrations (version) VALUES (:version)
                            ON CONFLICT (version) DO NOTHING"""),
                    {"version": version},
                )
                applied.add(version)
            session.commit()

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
