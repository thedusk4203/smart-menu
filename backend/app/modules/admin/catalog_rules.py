from __future__ import annotations

from app.shared.enums import UserRole


PRIVILEGED_ROLES = {UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value}

MISSING_CONVERSION_SQL = """i.grams_per_unit = 1
    AND LOWER(BTRIM(i.default_unit)) NOT IN ('g', 'gram', 'grams')
    AND (
        LOWER(BTRIM(i.default_unit)) NOT IN ('ml', 'milliliter', 'milliliters')
        OR i.food_group::text IN ('fat', 'dairy')
    )"""

MISSING_PURCHASE_RULE_SQL = """i.purchase_mode = 'regular'
    AND (i.purchase_increment IS NULL OR p.price_per_default_unit IS NULL)"""

MISSING_STORAGE_RULE_SQL = """i.purchase_mode = 'regular'
    AND i.room_shelf_life_days IS NULL
    AND i.fridge_shelf_life_days IS NULL
    AND i.freezer_shelf_life_days IS NULL"""
