from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.database import engine


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "data" / "migrations"
ADVISORY_LOCK_ID = 7_214_202_607


@dataclass(frozen=True)
class MigrationSpec:
    filename: str
    destructive: bool = False


MIGRATIONS = (
    MigrationSpec("002_admin.sql"),
    MigrationSpec("003_import_codes.sql"),
    MigrationSpec("20260710_dish_planner_v2.sql"),
    MigrationSpec("20260711_ai_provider_admin.sql"),
    MigrationSpec("20260711_ai_conversations.sql"),
    MigrationSpec("20260711_ai_conversation_nonempty_answers.sql"),
    MigrationSpec("20260711_google_gemini_provider.sql"),
    MigrationSpec("20260712_menu_names_tags_shares.sql"),
    MigrationSpec("20260712_ai_conversation_retention.sql"),
    MigrationSpec("20260713_fix_liquid_conversions.sql"),
    MigrationSpec("20260713_typed_import_tags.sql"),
    MigrationSpec("20260718_ai_system_prompts.sql"),
    MigrationSpec("20260719_procurement_planner_v3.sql"),
    MigrationSpec("20260720_v3_ledger_inventory.sql", destructive=True),
    MigrationSpec("20260720_catalog_density_cleanup.sql"),
)

MANUAL_SCRIPTS = {"20260713_reset_food_catalog.sql"}
BASELINE_MIGRATIONS = tuple(spec.filename for spec in MIGRATIONS[:-1])
BASELINE_MARKERS = (
    "public.v_dish_candidates",
    "public.tag_catalog",
    "public.shopping_list_shares",
    "public.llm_provider_configs",
    "public.ai_conversations",
    "public.inventory_lots",
)


def migration_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_registry(migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    registered = {spec.filename for spec in MIGRATIONS}
    actual = {
        path.name
        for path in migrations_dir.glob("*.sql")
        if path.is_file() and path.name not in MANUAL_SCRIPTS
    }
    missing = sorted(registered - actual)
    unknown = sorted(actual - registered)
    if missing or unknown:
        details: list[str] = []
        if missing:
            details.append(f"thiếu file đã đăng ký: {', '.join(missing)}")
        if unknown:
            details.append(f"file chưa đăng ký: {', '.join(unknown)}")
        raise RuntimeError("Migration registry không hợp lệ: " + "; ".join(details))
    return [migrations_dir / spec.filename for spec in MIGRATIONS]


def _tracking_table_exists(connection: Connection) -> bool:
    return connection.execute(
        text("SELECT to_regclass('public.schema_migrations')")
    ).scalar_one() is not None


def _read_applied(connection: Connection) -> dict[str, str | None]:
    if not _tracking_table_exists(connection):
        return {}
    columns = {
        row[0]
        for row in connection.execute(
            text(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_schema='public' AND table_name='schema_migrations'"""
            )
        )
    }
    if "checksum" not in columns:
        return {
            str(row.version): None
            for row in connection.execute(text("SELECT version FROM schema_migrations"))
        }
    return {
        str(row.version): str(row.checksum) if row.checksum else None
        for row in connection.execute(
            text("SELECT version, checksum FROM schema_migrations")
        )
    }


def _has_full_baseline(connection: Connection) -> bool:
    return all(
        connection.execute(
            text("SELECT to_regclass(:name)"), {"name": marker}
        ).scalar_one()
        is not None
        for marker in BASELINE_MARKERS
    )


def _ensure_tracking_table(connection: Connection) -> None:
    connection.execute(
        text(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                checksum CHAR(64),
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )"""
        )
    )
    connection.execute(
        text("ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum CHAR(64)")
    )


def _verify_and_backfill_checksums(
    connection: Connection,
    applied: dict[str, str | None],
    paths: dict[str, Path],
) -> None:
    for version, stored_checksum in applied.items():
        path = paths.get(version)
        if path is None:
            raise RuntimeError(f"Migration đã áp dụng không còn trong registry: {version}")
        current_checksum = migration_checksum(path)
        if stored_checksum is not None and stored_checksum != current_checksum:
            raise RuntimeError(
                f"Migration đã áp dụng bị thay đổi: {version}. "
                "Không được sửa file migration lịch sử."
            )
        if stored_checksum is None:
            connection.execute(
                text(
                    "UPDATE schema_migrations SET checksum=:checksum "
                    "WHERE version=:version AND checksum IS NULL"
                ),
                {"version": version, "checksum": current_checksum},
            )


def _record_baseline(
    connection: Connection,
    applied: dict[str, str | None],
    paths: dict[str, Path],
) -> None:
    if applied or not _has_full_baseline(connection):
        return
    for version in BASELINE_MIGRATIONS:
        connection.execute(
            text(
                """INSERT INTO schema_migrations (version, checksum)
                   VALUES (:version, :checksum)
                   ON CONFLICT (version) DO NOTHING"""
            ),
            {"version": version, "checksum": migration_checksum(paths[version])},
        )
        applied[version] = migration_checksum(paths[version])


def _legacy_counts(connection: Connection) -> dict[str, int] | None:
    if connection.execute(text("SELECT to_regclass('public.meal_plans')")).scalar_one() is None:
        return None
    plans = int(
        connection.execute(
            text(
                """SELECT COUNT(*) FROM meal_plans
                   WHERE COALESCE((plan_data->>'schema_version')::integer, 1) < 3"""
            )
        ).scalar_one()
    )

    def dependent_count(table_name: str) -> int:
        if connection.execute(
            text("SELECT to_regclass(:name)"), {"name": f"public.{table_name}"}
        ).scalar_one() is None:
            return 0
        return int(
            connection.execute(
                text(
                    f"""SELECT COUNT(*) FROM {table_name}
                        WHERE meal_plan_id IN (
                            SELECT id FROM meal_plans
                            WHERE COALESCE((plan_data->>'schema_version')::integer, 1) < 3
                        )"""
                )
            ).scalar_one()
        )

    return {
        "plans": plans,
        "shopping_items": dependent_count("shopping_lists"),
        "shares": dependent_count("shopping_list_shares"),
    }


def _simulated_baseline(
    connection: Connection,
    applied: dict[str, str | None],
    paths: dict[str, Path],
) -> dict[str, str | None]:
    """Mô phỏng baseline trong --plan mà không tạo schema_migrations."""
    if applied or not _has_full_baseline(connection):
        return applied
    return {
        version: migration_checksum(paths[version])
        for version in BASELINE_MIGRATIONS
    }


def _print_plan(
    pending: list[MigrationSpec],
    connection: Connection,
) -> None:
    if not pending:
        print("Database đã ở phiên bản mới nhất.")
        return
    print("Migration đang chờ:")
    for spec in pending:
        suffix = " [PHÁ DỮ LIỆU]" if spec.destructive else ""
        print(f"- {spec.filename}{suffix}")
        if spec.destructive and spec.filename == "20260720_v3_ledger_inventory.sql":
            counts = _legacy_counts(connection)
            if counts is not None:
                print(
                    "  Sẽ xóa "
                    f"{counts['plans']} plan V1/V2, "
                    f"{counts['shopping_items']} shopping item, "
                    f"{counts['shares']} share token."
                )


def apply_pending(*, plan_only: bool = False, allow_destructive: bool = False) -> None:
    migration_paths = validate_registry()
    paths = {path.name: path for path in migration_paths}

    with engine.connect() as lock_connection:
        lock_connection.execute(
            text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": ADVISORY_LOCK_ID}
        )
        try:
            applied = _read_applied(lock_connection)
            if not plan_only:
                _ensure_tracking_table(lock_connection)
                lock_connection.commit()
                applied = _read_applied(lock_connection)
                _verify_and_backfill_checksums(lock_connection, applied, paths)
                _record_baseline(lock_connection, applied, paths)
                lock_connection.commit()
            else:
                applied = _simulated_baseline(lock_connection, applied, paths)
                for version, stored_checksum in applied.items():
                    path = paths.get(version)
                    if path is None:
                        raise RuntimeError(
                            f"Migration đã áp dụng không còn trong registry: {version}"
                        )
                    if stored_checksum and stored_checksum != migration_checksum(path):
                        raise RuntimeError(f"Migration đã áp dụng bị thay đổi: {version}")

            pending = [spec for spec in MIGRATIONS if spec.filename not in applied]
            _print_plan(pending, lock_connection)
            if plan_only or not pending:
                return
            destructive = [spec.filename for spec in pending if spec.destructive]
            if destructive and not allow_destructive:
                raise RuntimeError(
                    "Có migration phá dữ liệu đang chờ: "
                    f"{', '.join(destructive)}. "
                    "Hãy backup database, chạy --plan, rồi chạy lại với --allow-destructive."
                )

            for spec in pending:
                path = paths[spec.filename]
                sql = path.read_text(encoding="utf-8")
                with engine.connect().execution_options(
                    isolation_level="AUTOCOMMIT"
                ) as connection:
                    connection.exec_driver_sql(sql)
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            """INSERT INTO schema_migrations (version, checksum)
                               VALUES (:version, :checksum)"""
                        ),
                        {
                            "version": spec.filename,
                            "checksum": migration_checksum(path),
                        },
                    )
                print(f"Applied {spec.filename}")
        finally:
            lock_connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": ADVISORY_LOCK_ID}
            )
            lock_connection.commit()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Áp dụng SQL migration có kiểm soát.")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Chỉ hiển thị migration và tác động phá dữ liệu; không ghi database.",
    )
    parser.add_argument(
        "--allow-destructive",
        action="store_true",
        help="Cho phép chạy migration được đánh dấu phá dữ liệu sau khi đã backup.",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parse_args()
    apply_pending(plan_only=args.plan, allow_destructive=args.allow_destructive)


if __name__ == "__main__":
    main()
