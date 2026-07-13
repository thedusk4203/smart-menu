from __future__ import annotations

from sqlalchemy import text

from app.modules.admin.use_cases import AdminService
from app.modules.tags.router import active_tags, list_tags


def test_import_tag_upsert_keeps_ingredient_and_dish_catalogs_separate(db_session):
    savepoint = db_session.begin_nested()
    try:
        service = AdminService(db_session)
        service._ensure_catalog_tags(["test-tag-dùng-chung"], "ingredient")
        service._ensure_catalog_tags(["test-tag-dùng-chung"], "dish")
        service._ensure_catalog_tags(["test-tag-dùng-chung"], "ingredient")
        rows = db_session.execute(
            text("""SELECT entity_type, name, is_active FROM tag_catalog
                    WHERE name='test-tag-dùng-chung' ORDER BY entity_type""")
        ).fetchall()

        assert [(row.entity_type, row.name, row.is_active) for row in rows] == [
            ("dish", "test-tag-dùng-chung", True),
            ("ingredient", "test-tag-dùng-chung", True),
        ]
    finally:
        savepoint.rollback()


def test_public_tags_only_return_dish_tags_and_admin_can_filter_by_type(db_session):
    public = active_tags(session=db_session)
    assert all(tag.entity_type == "dish" for tag in public)

    ingredient_tags = list_tags(
        search=None,
        entity_type="ingredient",
        session=db_session,
        _=None,
    )
    assert all(tag.entity_type == "ingredient" for tag in ingredient_tags)
