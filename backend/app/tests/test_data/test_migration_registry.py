from pathlib import Path

import pytest

from scripts.apply_migrations import (
    BASELINE_MIGRATIONS,
    MANUAL_SCRIPTS,
    MIGRATIONS,
    _simulated_baseline,
    migration_checksum,
    validate_registry,
)


def test_registry_contains_every_automatic_sql_migration() -> None:
    paths = validate_registry()

    assert [path.name for path in paths] == [spec.filename for spec in MIGRATIONS]
    assert not ({path.name for path in paths} & MANUAL_SCRIPTS)


def test_registry_rejects_unknown_migration(tmp_path: Path) -> None:
    for spec in MIGRATIONS:
        (tmp_path / spec.filename).write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "20990101_unregistered.sql").write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(RuntimeError, match="file chưa đăng ký"):
        validate_registry(tmp_path)


def test_checksum_changes_when_migration_content_changes(tmp_path: Path) -> None:
    path = tmp_path / "migration.sql"
    path.write_text("SELECT 1;", encoding="utf-8")
    first = migration_checksum(path)

    path.write_text("SELECT 2;", encoding="utf-8")

    assert migration_checksum(path) != first


def test_v3_cutover_is_explicitly_destructive() -> None:
    destructive = {spec.filename for spec in MIGRATIONS if spec.destructive}

    assert destructive == {"20260720_v3_ledger_inventory.sql"}


def test_plan_mode_simulates_baseline_without_writing(monkeypatch, tmp_path: Path) -> None:
    paths: dict[str, Path] = {}
    for version in BASELINE_MIGRATIONS:
        path = tmp_path / version
        path.write_text(version, encoding="utf-8")
        paths[version] = path
    monkeypatch.setattr("scripts.apply_migrations._has_full_baseline", lambda _connection: True)

    applied = _simulated_baseline(object(), {}, paths)

    assert tuple(applied) == BASELINE_MIGRATIONS
    assert all(applied[version] == migration_checksum(paths[version]) for version in applied)
