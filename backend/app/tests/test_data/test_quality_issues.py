from sqlalchemy import text

from app.modules.admin.use_cases import AdminService


def test_duplicate_name_quality_ignores_cross_entity_matches(db_session):
    cross_entity_record = db_session.execute(
        text(
            """WITH names AS (
                   SELECT 'ingredient'::text AS entity_type, id, name,
                          LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) AS normalized
                   FROM ingredients
                   UNION ALL
                   SELECT 'dish', id, name,
                          LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g'))
                   FROM dishes
               ), candidates AS (
                   SELECT *, COUNT(*) OVER (PARTITION BY entity_type, normalized) AS same_type_count,
                          COUNT(*) OVER (PARTITION BY normalized) AS all_type_count
                   FROM names
               )
               SELECT entity_type, id, name
               FROM candidates
               WHERE same_type_count = 1 AND all_type_count > 1
               LIMIT 1"""
        )
    ).first()

    if cross_entity_record is None:
        return

    result = AdminService(db_session).list_quality_issues(
        entity_type=None,
        severity=None,
        code="duplicate_name",
        search=cross_entity_record.name,
        limit=100,
        offset=0,
    )

    assert not any(
        issue["entity_type"] == cross_entity_record.entity_type
        and issue["entity_id"] == cross_entity_record.id
        for issue in result["items"]
    )


def test_dashboard_duplicate_count_is_scoped_by_entity_type(db_session):
    expected = db_session.execute(
        text(
            """SELECT COALESCE(SUM(group_size - 1), 0)
               FROM (
                   SELECT COUNT(*) AS group_size
                   FROM (
                       SELECT 'ingredient'::text AS entity_type,
                              LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) AS normalized
                       FROM ingredients
                       UNION ALL
                       SELECT 'dish', LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g'))
                       FROM dishes
                   ) names
                   GROUP BY entity_type, normalized
                   HAVING COUNT(*) > 1
               ) duplicate_groups"""
        )
    ).scalar_one()

    assert AdminService(db_session).dashboard()["duplicate_names"] == expected


def test_water_like_liquid_at_one_gram_per_ml_is_not_flagged(db_session):
    liquid = db_session.execute(
        text(
            """SELECT id, name
               FROM ingredients
               WHERE LOWER(BTRIM(default_unit)) = 'ml'
                 AND food_group::text NOT IN ('fat', 'dairy')
                 AND grams_per_unit = 1
               LIMIT 1"""
        )
    ).first()

    if liquid is None:
        return

    result = AdminService(db_session).list_quality_issues(
        entity_type="ingredient",
        severity="warning",
        code="missing_conversion",
        search=liquid.name,
        limit=100,
        offset=0,
    )

    assert not any(issue["entity_id"] == liquid.id for issue in result["items"])


def test_catalog_has_no_placeholder_conversions(db_session):
    result = AdminService(db_session).list_quality_issues(
        entity_type="ingredient",
        severity="warning",
        code="missing_conversion",
        search=None,
        limit=100,
        offset=0,
    )

    assert result["total"] == 0
