from __future__ import annotations

import json
import math
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from app.modules.admin.catalog_rules import (
    MISSING_CONVERSION_SQL,
    MISSING_PURCHASE_RULE_SQL,
    MISSING_STORAGE_RULE_SQL,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.modules.admin.import_service import AdminImportMixin
from app.modules.admin.user_service import AdminUserMixin
from app.modules.admin.schemas import (
    AdminDishWrite,
    AdminIngredientWrite,
)


from app.modules.admin.normalization import (
    enum_value as _enum_value,
    json_value as _json,
    normalized as _normalized,
    normalized_tags as _normalized_tags,
    row_dict as _row_dict,
)


class AdminService(AdminImportMixin, AdminUserMixin):
    """Ứng dụng quản trị tập trung cho dashboard, dữ liệu canonical và import.

    Các phép ghi dùng cùng một Session để công thức, giá và audit log được commit
    nguyên tử. Public read APIs vẫn nằm trong module domain hiện có.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def _validate_catalog_tags(self, tags: list[str], entity_type: str = "dish") -> None:
        names = _normalized_tags(tags)
        if not names:
            return
        rows = self.session.execute(
            text("""SELECT name FROM tag_catalog
                    WHERE entity_type=:entity_type AND is_active=TRUE AND name = ANY(:names)"""),
            {"entity_type": entity_type, "names": names},
        ).fetchall()
        found = {row.name for row in rows}
        missing = [name for name in names if name not in found]
        if missing:
            raise ValidationAppError("Thẻ chưa có trong danh mục hoặc đã ngừng dùng: " + ", ".join(missing))

    def _ensure_catalog_tags(self, tags: list[str], entity_type: str) -> None:
        for name in _normalized_tags(tags):
            existing = self.session.execute(
                text("""SELECT id FROM tag_catalog
                        WHERE entity_type=:entity_type AND LOWER(name)=LOWER(:name)
                        FOR UPDATE"""),
                {"entity_type": entity_type, "name": name},
            ).first()
            if existing:
                self.session.execute(
                    text("UPDATE tag_catalog SET is_active=TRUE, updated_at=NOW() WHERE id=:id"),
                    {"id": existing.id},
                )
            else:
                self.session.execute(
                    text("INSERT INTO tag_catalog (entity_type, name) VALUES (:entity_type, :name)"),
                    {"entity_type": entity_type, "name": name},
                )

    def _audit(
        self,
        actor_id: int,
        action: str,
        entity_type: str,
        entity_id: int | None,
        before: Any = None,
        after: Any = None,
    ) -> None:
        self.session.execute(
            text(
                """INSERT INTO audit_logs
                   (actor_user_id, action, entity_type, entity_id, before_data, after_data)
                   VALUES (:actor, :action, :etype, :eid,
                           CAST(:before AS jsonb), CAST(:after AS jsonb))"""
            ),
            {
                "actor": actor_id,
                "action": action,
                "etype": entity_type,
                "eid": entity_id,
                "before": _json(before) if before is not None else None,
                "after": _json(after) if after is not None else None,
            },
        )


    # ------------------------------------------------------------------ ingredients
    def _ingredient_from_db(self, ingredient_id: int) -> dict[str, Any]:
        row = self.session.execute(
            text(
                f"""SELECT i.id, i.name, i.food_group, i.default_unit, i.grams_per_unit,
                           i.purchase_mode, i.purchase_increment, i.room_shelf_life_days,
                           i.fridge_shelf_life_days, i.freezer_shelf_life_days,
                           i.shelf_life_source, i.shelf_life_reviewed_at,
                           i.tags, i.is_active, n.calories, n.protein_g, n.carbs_g, n.fat_g,
                          n.fiber_g, p.price AS latest_price, p.unit AS price_unit,
                          p.price_per_default_unit AS latest_price_per_unit,
                          p.source AS price_source, p.recorded_at AS price_recorded_at,
                          i.created_at, i.updated_at,
                           (i.purchase_mode = 'regular' AND (p.id IS NULL OR p.price_per_default_unit IS NULL)) AS missing_price,
                           (n.id IS NULL) AS missing_nutrition,
                           ({MISSING_CONVERSION_SQL}) AS missing_conversion,
                           ({MISSING_PURCHASE_RULE_SQL}) AS missing_purchase_rule,
                           ({MISSING_STORAGE_RULE_SQL}) AS missing_storage_rule,
                           CASE WHEN i.purchase_mode = 'regular' AND i.purchase_increment IS NOT NULL
                                     AND p.price_per_default_unit IS NOT NULL
                                THEN i.purchase_increment * p.price_per_default_unit END AS purchase_block_cost
                   FROM ingredients i
                   LEFT JOIN nutrition_facts n ON n.ingredient_id = i.id
                   LEFT JOIN LATERAL (
                       SELECT id, price, unit, price_per_default_unit, source, recorded_at
                       FROM price_snapshots WHERE ingredient_id = i.id
                       ORDER BY recorded_at DESC LIMIT 1
                   ) p ON TRUE
                   WHERE i.id = :id"""
            ),
            {"id": ingredient_id},
        ).first()
        if not row:
            raise NotFoundError("Không tìm thấy nguyên liệu")
        data = _row_dict(row)
        for key in (
            "grams_per_unit", "calories", "protein_g", "carbs_g", "fat_g",
            "fiber_g", "latest_price", "latest_price_per_unit", "purchase_increment",
            "purchase_block_cost",
        ):
            if data.get(key) is not None:
                data[key] = float(data[key])
        return data

    def list_ingredients(
        self,
        search: str | None,
        food_group: str | None,
        status: str | None,
        quality: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            where.append("i.name ILIKE :search")
            params["search"] = f"%{search.strip()}%"
        if food_group:
            where.append("i.food_group::text = :food_group")
            params["food_group"] = food_group
        if status == "active":
            where.append("i.is_active")
        elif status == "inactive":
            where.append("NOT i.is_active")
        if quality == "missing_price":
            where.append("i.purchase_mode = 'regular' AND (p.id IS NULL OR p.price_per_default_unit IS NULL)")
        elif quality == "missing_nutrition":
            where.append("n.id IS NULL")
        elif quality == "missing_conversion":
            where.append(MISSING_CONVERSION_SQL)
        elif quality == "missing_purchase_rule":
            where.append(MISSING_PURCHASE_RULE_SQL)
        elif quality == "missing_storage_rule":
            where.append(MISSING_STORAGE_RULE_SQL)
        clause = " AND ".join(where)
        joins = """LEFT JOIN nutrition_facts n ON n.ingredient_id = i.id
                   LEFT JOIN LATERAL (
                       SELECT id, price, unit, price_per_default_unit, source, recorded_at
                       FROM price_snapshots WHERE ingredient_id = i.id
                       ORDER BY recorded_at DESC LIMIT 1
                   ) p ON TRUE"""
        total = self.session.execute(
            text(f"SELECT COUNT(*) FROM ingredients i {joins} WHERE {clause}"), params
        ).scalar_one()
        rows = self.session.execute(
            text(
                f"""SELECT i.id, i.name, i.food_group, i.default_unit, i.grams_per_unit,
                           i.purchase_mode, i.purchase_increment, i.room_shelf_life_days,
                           i.fridge_shelf_life_days, i.freezer_shelf_life_days,
                           i.shelf_life_source, i.shelf_life_reviewed_at,
                           i.tags, i.is_active, n.calories, n.protein_g, n.carbs_g, n.fat_g,
                           n.fiber_g, p.price AS latest_price, p.unit AS price_unit,
                           p.price_per_default_unit AS latest_price_per_unit,
                           p.source AS price_source, p.recorded_at AS price_recorded_at,
                           i.created_at, i.updated_at,
                           (i.purchase_mode = 'regular' AND (p.id IS NULL OR p.price_per_default_unit IS NULL)) AS missing_price,
                           (n.id IS NULL) AS missing_nutrition,
                           ({MISSING_CONVERSION_SQL}) AS missing_conversion,
                           ({MISSING_PURCHASE_RULE_SQL}) AS missing_purchase_rule,
                           ({MISSING_STORAGE_RULE_SQL}) AS missing_storage_rule,
                           CASE WHEN i.purchase_mode = 'regular' AND i.purchase_increment IS NOT NULL
                                     AND p.price_per_default_unit IS NOT NULL
                                THEN i.purchase_increment * p.price_per_default_unit END AS purchase_block_cost
                    FROM ingredients i {joins} WHERE {clause}
                    ORDER BY i.updated_at DESC, i.name
                    LIMIT :limit OFFSET :offset"""
            ),
            params,
        ).fetchall()
        items = []
        for row in rows:
            data = _row_dict(row)
            for key in (
                "grams_per_unit", "calories", "protein_g", "carbs_g", "fat_g",
                "fiber_g", "latest_price", "latest_price_per_unit", "purchase_increment",
                "purchase_block_cost",
            ):
                if data.get(key) is not None:
                    data[key] = float(data[key])
            items.append(data)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def export_ingredients(
        self,
        output_format: str,
        search: str | None,
        food_group: str | None,
        status: str | None,
        quality: str | None,
    ) -> tuple[bytes, str, str]:
        where = ["1=1"]
        params: dict[str, Any] = {}
        if search:
            where.append("i.name ILIKE :search")
            params["search"] = f"%{search.strip()}%"
        if food_group:
            where.append("i.food_group::text = :food_group")
            params["food_group"] = food_group
        if status == "active":
            where.append("i.is_active")
        elif status == "inactive":
            where.append("NOT i.is_active")
        if quality == "missing_price":
            where.append("i.purchase_mode = 'regular' AND (p.id IS NULL OR p.price_per_default_unit IS NULL)")
        elif quality == "missing_nutrition":
            where.append("n.id IS NULL")
        elif quality == "missing_conversion":
            where.append(MISSING_CONVERSION_SQL)
        elif quality == "missing_purchase_rule":
            where.append(MISSING_PURCHASE_RULE_SQL)
        elif quality == "missing_storage_rule":
            where.append(MISSING_STORAGE_RULE_SQL)
        joins = """LEFT JOIN nutrition_facts n ON n.ingredient_id = i.id
                   LEFT JOIN LATERAL (
                       SELECT id, price, unit, price_per_default_unit, source, recorded_at
                       FROM price_snapshots WHERE ingredient_id = i.id
                       ORDER BY recorded_at DESC LIMIT 1
                   ) p ON TRUE"""
        rows = self.session.execute(
            text(
                f"""SELECT i.id, i.code, i.name, i.food_group, i.default_unit, i.grams_per_unit, i.tags,
                           i.purchase_mode, i.purchase_increment, i.room_shelf_life_days,
                           i.fridge_shelf_life_days, i.freezer_shelf_life_days,
                           i.shelf_life_source, i.shelf_life_reviewed_at,
                           n.calories, n.protein_g, n.carbs_g, n.fat_g, n.fiber_g,
                           p.price, p.unit AS price_unit, p.price_per_default_unit, p.source, i.is_active
                    FROM ingredients i {joins}
                    WHERE {' AND '.join(where)}
                    ORDER BY i.updated_at DESC, i.name"""
            ),
            params,
        ).fetchall()
        records = []
        for row in rows:
            data = _row_dict(row)
            records.append({
                "id": data["id"], "code": data["code"], "name": data["name"],
                "food_group": _enum_value(data["food_group"]), "default_unit": data["default_unit"],
                "grams_per_unit": float(data["grams_per_unit"]),
                "tags": ", ".join(str(tag).strip() for tag in (data.get("tags") or []) if str(tag).strip()),
                "calories": float(data["calories"]) if data["calories"] is not None else None,
                "protein_g": float(data["protein_g"]) if data["protein_g"] is not None else None,
                "carbs_g": float(data["carbs_g"]) if data["carbs_g"] is not None else None,
                "fat_g": float(data["fat_g"]) if data["fat_g"] is not None else None,
                "fiber_g": float(data["fiber_g"]) if data["fiber_g"] is not None else None,
                "price": float(data["price"]) if data["price"] is not None else None,
                "price_unit": data["price_unit"],
                "price_per_default_unit": float(data["price_per_default_unit"])
                if data["price_per_default_unit"] is not None else None,
                "source": data["source"], "is_active": data["is_active"],
                "purchase_mode": _enum_value(data["purchase_mode"]),
                "purchase_increment": float(data["purchase_increment"])
                if data["purchase_increment"] is not None else None,
                "room_shelf_life_days": data["room_shelf_life_days"],
                "fridge_shelf_life_days": data["fridge_shelf_life_days"],
                "freezer_shelf_life_days": data["freezer_shelf_life_days"],
                "shelf_life_source": data["shelf_life_source"],
                "shelf_life_reviewed_at": data["shelf_life_reviewed_at"],
            })
        return self._build_export_file("ingredients", output_format, records)

    def save_ingredient(
        self,
        data: AdminIngredientWrite,
        actor_id: int,
        ingredient_id: int | None = None,
    ) -> dict[str, Any]:
        duplicate = self.session.execute(
            text(
                """SELECT id FROM ingredients
                   WHERE LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) = :name
                     AND (:id IS NULL OR id <> :id)"""
            ),
            {"name": _normalized(data.name), "id": ingredient_id},
        ).first()
        if duplicate:
            raise ConflictError("Tên nguyên liệu đã tồn tại")
        before = self._ingredient_from_db(ingredient_id) if ingredient_id else None
        if before and before["default_unit"] != data.default_unit:
            referenced = self.session.execute(
                text(
                    """SELECT 1 FROM dish_ingredients WHERE ingredient_id = :id
                       UNION ALL SELECT 1 FROM meal_ingredients WHERE ingredient_id = :id
                       UNION ALL SELECT 1 FROM shopping_lists WHERE ingredient_id = :id
                       LIMIT 1"""
                ),
                {"id": ingredient_id},
            ).first()
            if referenced:
                raise ValidationAppError(
                    "Không thể đổi đơn vị chuẩn của nguyên liệu đã được công thức hoặc danh sách mua tham chiếu"
                )
        procurement = {
            "purchase_mode": data.purchase_mode,
            "purchase_increment": data.purchase_increment,
            "room_shelf_life_days": data.room_shelf_life_days,
            "fridge_shelf_life_days": data.fridge_shelf_life_days,
            "freezer_shelf_life_days": data.freezer_shelf_life_days,
            "shelf_life_source": data.shelf_life_source.strip() if data.shelf_life_source else None,
            "shelf_life_reviewed_at": data.shelf_life_reviewed_at,
        }
        if ingredient_id is None:
            row = self.session.execute(
                text(
                    """INSERT INTO ingredients
                       (name, food_group, default_unit, grams_per_unit, is_active,
                        purchase_mode, purchase_increment, room_shelf_life_days,
                        fridge_shelf_life_days, freezer_shelf_life_days,
                        shelf_life_source, shelf_life_reviewed_at)
                       VALUES (:name, CAST(:group AS food_group), :unit, :grams, :active,
                               CAST(:purchase_mode AS ingredient_purchase_mode), :purchase_increment,
                               :room_shelf_life_days, :fridge_shelf_life_days,
                               :freezer_shelf_life_days, :shelf_life_source,
                               :shelf_life_reviewed_at)
                       RETURNING id"""
                ),
                {
                    "name": data.name, "group": data.food_group.value,
                    "unit": data.default_unit, "grams": data.grams_per_unit,
                    "active": data.is_active, **procurement,
                },
            ).first()
            ingredient_id = row.id
            action = "create"
        else:
            self.session.execute(
                text(
                    """UPDATE ingredients SET name = :name,
                           food_group = CAST(:group AS food_group), default_unit = :unit,
                           grams_per_unit = :grams, is_active = :active,
                           purchase_mode = CAST(:purchase_mode AS ingredient_purchase_mode),
                           purchase_increment = :purchase_increment,
                           room_shelf_life_days = :room_shelf_life_days,
                           fridge_shelf_life_days = :fridge_shelf_life_days,
                           freezer_shelf_life_days = :freezer_shelf_life_days,
                           shelf_life_source = :shelf_life_source,
                           shelf_life_reviewed_at = :shelf_life_reviewed_at
                       WHERE id = :id"""
                ),
                {
                    "id": ingredient_id, "name": data.name, "group": data.food_group.value,
                    "unit": data.default_unit, "grams": data.grams_per_unit,
                    "active": data.is_active, **procurement,
                },
            )
            action = "update"
        if data.nutrition is not None:
            nutrition = data.nutrition.model_dump()
            self.session.execute(
                text(
                    """INSERT INTO nutrition_facts
                       (ingredient_id, calories, protein_g, carbs_g, fat_g, fiber_g)
                       VALUES (:ingredient_id, :calories, :protein_g, :carbs_g, :fat_g, :fiber_g)
                       ON CONFLICT (ingredient_id) DO UPDATE SET
                           calories = EXCLUDED.calories, protein_g = EXCLUDED.protein_g,
                           carbs_g = EXCLUDED.carbs_g, fat_g = EXCLUDED.fat_g,
                           fiber_g = EXCLUDED.fiber_g"""
                ),
                {"ingredient_id": ingredient_id, **nutrition},
            )
        if data.price is not None:
            price = data.price.model_dump()
            self.session.execute(
                text(
                    """INSERT INTO price_snapshots
                       (ingredient_id, price, unit, price_per_default_unit, source, recorded_at)
                       VALUES (:ingredient_id, :price, :unit, :price_per_default_unit,
                               :source, COALESCE(:recorded_at, NOW()))"""
                ),
                {"ingredient_id": ingredient_id, **price},
            )
        after = self._ingredient_from_db(ingredient_id)
        self._audit(actor_id, action, "ingredient", ingredient_id, before, after)
        self.session.commit()
        return after

    def set_ingredient_active(self, ingredient_id: int, active: bool, actor_id: int) -> dict[str, Any]:
        before = self._ingredient_from_db(ingredient_id)
        self.session.execute(
            text("UPDATE ingredients SET is_active = :active WHERE id = :id"),
            {"active": active, "id": ingredient_id},
        )
        after = self._ingredient_from_db(ingredient_id)
        self._audit(actor_id, "restore" if active else "deactivate", "ingredient", ingredient_id, before, after)
        self.session.commit()
        return after

    def delete_ingredient(self, ingredient_id: int, actor_id: int) -> None:
        before = self._ingredient_from_db(ingredient_id)
        references = self.session.execute(
            text(
                """SELECT 'công thức món' AS label FROM dish_ingredients WHERE ingredient_id = :id LIMIT 1
                   UNION ALL
                   SELECT 'món ăn' AS label FROM meal_ingredients WHERE ingredient_id = :id LIMIT 1
                   UNION ALL
                   SELECT 'danh sách đi chợ' AS label FROM shopping_lists WHERE ingredient_id = :id LIMIT 1"""
            ),
            {"id": ingredient_id},
        ).fetchall()
        if references:
            labels = ", ".join(row.label for row in references)
            raise ConflictError(f"Không thể xóa nguyên liệu vì đang được dùng trong: {labels}. Hãy gỡ liên kết hoặc ẩn nguyên liệu.")
        self.session.execute(text("DELETE FROM ingredients WHERE id = :id"), {"id": ingredient_id})
        self._audit(actor_id, "delete", "ingredient", ingredient_id, before, None)
        self.session.commit()

    # ------------------------------------------------------------------ dishes
    def _dish_base_query(self) -> str:
        return """SELECT d.id, d.name, d.dish_type, d.cooking_method, d.description,
                         d.instructions, d.tags, d.is_active,
                         COALESCE(v.total_calories, 0) AS total_calories,
                         COALESCE(v.total_protein_g, 0) AS total_protein_g,
                         COALESCE(v.total_carbs_g, 0) AS total_carbs_g,
                         COALESCE(v.total_fat_g, 0) AS total_fat_g,
                         COALESCE(v.estimated_cost, 0) AS estimated_cost,
                         COALESCE(v.ingredient_count, 0) AS ingredient_count,
                         (COALESCE(v.ingredient_count, 0) = 0) AS missing_recipe,
                          EXISTS (
                            SELECT 1 FROM dish_ingredients di JOIN ingredients i ON i.id = di.ingredient_id
                            WHERE di.dish_id = d.id AND NOT EXISTS (
                              SELECT 1 FROM price_snapshots p
                              WHERE p.ingredient_id = di.ingredient_id
                                AND p.price_per_default_unit IS NOT NULL
                            )
                            AND i.purchase_mode = 'regular'
                          ) AS missing_price,
                         EXISTS (
                           SELECT 1 FROM dish_ingredients di
                           LEFT JOIN nutrition_facts n ON n.ingredient_id = di.ingredient_id
                           WHERE di.dish_id = d.id AND n.id IS NULL
                         ) AS missing_nutrition,
                         d.created_at, d.updated_at
                  FROM dishes d LEFT JOIN v_dishes_full v ON v.id = d.id"""

    def _dish_from_db(self, dish_id: int, include_ingredients: bool = True) -> dict[str, Any]:
        row = self.session.execute(
            text(self._dish_base_query() + " WHERE d.id = :id"), {"id": dish_id}
        ).first()
        if not row:
            raise NotFoundError("Không tìm thấy món thành phần")
        data = _row_dict(row)
        for key in (
            "total_calories", "total_protein_g", "total_carbs_g",
            "total_fat_g", "estimated_cost",
        ):
            data[key] = float(data[key] or 0)
        data["ingredients"] = []
        if include_ingredients:
            rows = self.session.execute(
                text(
                    """SELECT di.ingredient_id, i.name, di.quantity, di.unit,
                              di.max_extra_quantity, di.extra_step_quantity,
                              NOT EXISTS (SELECT 1 FROM price_snapshots p
                                  WHERE p.ingredient_id = i.id
                                    AND p.price_per_default_unit IS NOT NULL)
                                  AND i.purchase_mode = 'regular' AS missing_price,
                              NOT EXISTS (SELECT 1 FROM nutrition_facts n
                                  WHERE n.ingredient_id = i.id) AS missing_nutrition
                       FROM dish_ingredients di JOIN ingredients i ON i.id = di.ingredient_id
                       WHERE di.dish_id = :id ORDER BY i.name"""
                ),
                {"id": dish_id},
            ).fetchall()
            data["ingredients"] = [
                {
                    **_row_dict(r),
                    "quantity": float(r.quantity),
                    "max_extra_quantity": float(r.max_extra_quantity),
                    "extra_step_quantity": float(r.extra_step_quantity)
                    if r.extra_step_quantity is not None else None,
                }
                for r in rows
            ]
        return data

    def list_dishes(
        self,
        search: str | None,
        dish_type: str | None,
        status: str | None,
        quality: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            where.append("d.name ILIKE :search")
            params["search"] = f"%{search.strip()}%"
        if dish_type:
            where.append("d.dish_type::text = :dtype")
            params["dtype"] = dish_type
        if status == "active":
            where.append("d.is_active")
        elif status == "inactive":
            where.append("NOT d.is_active")
        if quality == "missing_recipe":
            where.append("COALESCE(v.ingredient_count, 0) = 0")
        elif quality == "missing_price":
            where.append("EXISTS (SELECT 1 FROM dish_ingredients di JOIN ingredients i ON i.id = di.ingredient_id WHERE di.dish_id = d.id AND i.purchase_mode = 'regular' AND NOT EXISTS (SELECT 1 FROM price_snapshots p WHERE p.ingredient_id = di.ingredient_id AND p.price_per_default_unit IS NOT NULL))")
        elif quality == "missing_nutrition":
            where.append("EXISTS (SELECT 1 FROM dish_ingredients di LEFT JOIN nutrition_facts n ON n.ingredient_id = di.ingredient_id WHERE di.dish_id = d.id AND n.id IS NULL)")
        clause = " AND ".join(where)
        total = self.session.execute(
            text(f"SELECT COUNT(*) FROM dishes d LEFT JOIN v_dishes_full v ON v.id = d.id WHERE {clause}"),
            params,
        ).scalar_one()
        rows = self.session.execute(
            text(self._dish_base_query() + f" WHERE {clause} ORDER BY d.updated_at DESC, d.name LIMIT :limit OFFSET :offset"),
            params,
        ).fetchall()
        items = []
        for row in rows:
            data = _row_dict(row)
            for key in ("total_calories", "total_protein_g", "total_carbs_g", "total_fat_g", "estimated_cost"):
                data[key] = float(data[key] or 0)
            data["ingredients"] = []
            items.append(data)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def export_dishes(
        self,
        output_format: str,
        search: str | None,
        dish_type: str | None,
        status: str | None,
        quality: str | None,
    ) -> tuple[bytes, str, str]:
        where = ["1=1"]
        params: dict[str, Any] = {}
        if search:
            where.append("d.name ILIKE :search")
            params["search"] = f"%{search.strip()}%"
        if dish_type:
            where.append("d.dish_type::text = :dtype")
            params["dtype"] = dish_type
        if status == "active":
            where.append("d.is_active")
        elif status == "inactive":
            where.append("NOT d.is_active")
        if quality == "missing_recipe":
            where.append("NOT EXISTS (SELECT 1 FROM dish_ingredients di WHERE di.dish_id = d.id)")
        elif quality == "missing_price":
            where.append("EXISTS (SELECT 1 FROM dish_ingredients di JOIN ingredients i ON i.id = di.ingredient_id WHERE di.dish_id = d.id AND i.purchase_mode = 'regular' AND NOT EXISTS (SELECT 1 FROM price_snapshots p WHERE p.ingredient_id = di.ingredient_id AND p.price_per_default_unit IS NOT NULL))")
        elif quality == "missing_nutrition":
            where.append("EXISTS (SELECT 1 FROM dish_ingredients di LEFT JOIN nutrition_facts n ON n.ingredient_id = di.ingredient_id WHERE di.dish_id = d.id AND n.id IS NULL)")
        rows = self.session.execute(
            text(
                f"""SELECT d.id, d.code, d.name, d.dish_type, d.cooking_method, d.description,
                           d.instructions, d.tags, d.is_active,
                           COALESCE(
                               jsonb_agg(jsonb_build_object(
                                   'ingredient_id', di.ingredient_id, 'name', i.name,
                                    'quantity', di.quantity, 'unit', di.unit,
                                    'max_extra_quantity', di.max_extra_quantity,
                                    'extra_step_quantity', di.extra_step_quantity
                               ) ORDER BY i.name) FILTER (WHERE di.ingredient_id IS NOT NULL),
                               '[]'::jsonb
                           ) AS ingredients
                    FROM dishes d
                    LEFT JOIN dish_ingredients di ON di.dish_id = d.id
                    LEFT JOIN ingredients i ON i.id = di.ingredient_id
                    WHERE {' AND '.join(where)}
                    GROUP BY d.id
                    ORDER BY d.updated_at DESC, d.name"""
            ),
            params,
        ).fetchall()
        records = []
        for row in rows:
            data = _row_dict(row)
            ingredients = data.get("ingredients") or []
            if isinstance(ingredients, str):
                ingredients = json.loads(ingredients)
            tags = data.get("tags") or []
            if isinstance(tags, str):
                tags = json.loads(tags)
            records.append({
                "id": data["id"], "code": data["code"], "name": data["name"],
                "dish_type": _enum_value(data["dish_type"]),
                "cooking_method": _enum_value(data["cooking_method"]) if data["cooking_method"] else None,
                "description": data["description"], "instructions": data["instructions"],
                "tags": ", ".join(str(tag).strip() for tag in tags if str(tag).strip()),
                "ingredients_json": _json([
                    {
                        "ingredient_id": item["ingredient_id"], "name": item["name"],
                        "quantity": float(item["quantity"]), "unit": item["unit"],
                        "max_extra_quantity": float(item.get("max_extra_quantity") or 0),
                        "extra_step_quantity": float(item["extra_step_quantity"])
                        if item.get("extra_step_quantity") is not None else None,
                    }
                    for item in ingredients
                ]),
                "is_active": data["is_active"],
            })
        return self._build_export_file("dishes", output_format, records)

    def export_dish_flex_suggestions(self, output_format: str) -> tuple[bytes, str, str]:
        """Export complete, import-safe dish rows with conservative flex suggestions."""
        rows = self.session.execute(text(
            """SELECT d.id, d.code, d.name, d.dish_type, d.cooking_method,
                      d.description, d.instructions, d.tags, d.is_active,
                      COALESCE(jsonb_agg(jsonb_build_object(
                          'ingredient_id', di.ingredient_id, 'name', i.name,
                          'quantity', di.quantity, 'unit', di.unit,
                          'max_extra_quantity', di.max_extra_quantity,
                          'extra_step_quantity', di.extra_step_quantity,
                          'purchase_mode', i.purchase_mode,
                          'purchase_increment', i.purchase_increment,
                          'food_group', i.food_group
                      ) ORDER BY i.name) FILTER (WHERE di.ingredient_id IS NOT NULL), '[]'::jsonb)
                      AS ingredients
               FROM dishes d
               LEFT JOIN dish_ingredients di ON di.dish_id=d.id
               LEFT JOIN ingredients i ON i.id=di.ingredient_id
               GROUP BY d.id ORDER BY d.name"""
        )).fetchall()
        records: list[dict[str, Any]] = []
        for row in rows:
            data = _row_dict(row)
            ingredients = data.get("ingredients") or []
            if isinstance(ingredients, str):
                ingredients = json.loads(ingredients)
            changed = False
            exported_ingredients: list[dict[str, Any]] = []
            for item in ingredients:
                quantity = float(item["quantity"])
                maximum = float(item.get("max_extra_quantity") or 0)
                step = item.get("extra_step_quantity")
                eligible = (
                    maximum <= 0
                    and str(item.get("purchase_mode")) == "regular"
                    and str(item.get("unit") or "").casefold() in {"g", "ml"}
                    and str(item.get("food_group")) in {
                        "protein", "vegetable", "grain", "fruit", "dairy"
                    }
                    and quantity >= 20
                    and item.get("purchase_increment") is not None
                )
                if eligible:
                    suggested_step = 5.0 if quantity < 100 else 10.0
                    raw_max = min(
                        float(item["purchase_increment"]) * 0.20,
                        quantity * 0.25,
                    )
                    suggested_max = math.floor(raw_max / suggested_step) * suggested_step
                    if suggested_max >= suggested_step:
                        maximum = suggested_max
                        step = suggested_step
                        changed = True
                exported_ingredients.append({
                    "ingredient_id": item["ingredient_id"],
                    "name": item["name"],
                    "quantity": quantity,
                    "unit": item["unit"],
                    "max_extra_quantity": maximum,
                    "extra_step_quantity": float(step) if step is not None else None,
                })
            if not changed:
                continue
            tags = data.get("tags") or []
            if isinstance(tags, str):
                tags = json.loads(tags)
            records.append({
                "id": data["id"], "code": data["code"], "name": data["name"],
                "dish_type": _enum_value(data["dish_type"]),
                "cooking_method": _enum_value(data["cooking_method"])
                if data["cooking_method"] else None,
                "description": data["description"], "instructions": data["instructions"],
                "tags": ", ".join(str(tag).strip() for tag in tags if str(tag).strip()),
                "ingredients_json": _json(exported_ingredients),
                "is_active": data["is_active"],
            })
        content, media_type, filename = self._build_export_file(
            "dishes", output_format, records
        )
        return content, media_type, filename.replace("dishes-export", "dish-flex-suggestions")

    def save_dish(
        self,
        data: AdminDishWrite,
        actor_id: int,
        dish_id: int | None = None,
    ) -> dict[str, Any]:
        self._validate_catalog_tags(data.tags)
        ids = [i.ingredient_id for i in data.ingredients]
        if len(ids) != len(set(ids)):
            raise ValidationAppError("Mỗi nguyên liệu chỉ được xuất hiện một lần trong công thức")
        if data.is_active and not ids:
            raise ValidationAppError("Món đang hoạt động phải có ít nhất một nguyên liệu")
        duplicate = self.session.execute(
            text(
                """SELECT id FROM dishes
                   WHERE LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) = :name
                     AND (:id IS NULL OR id <> :id)"""
            ),
            {"name": _normalized(data.name), "id": dish_id},
        ).first()
        if duplicate:
            raise ConflictError("Tên món đã tồn tại")
        if ids:
            ingredient_rows = self.session.execute(
                text(
                    """SELECT i.id, i.default_unit, i.is_active, i.purchase_mode,
                              i.purchase_increment,
                              EXISTS (SELECT 1 FROM nutrition_facts n WHERE n.ingredient_id = i.id) AS has_nutrition,
                              EXISTS (SELECT 1 FROM price_snapshots p
                                      WHERE p.ingredient_id = i.id
                                        AND p.price_per_default_unit IS NOT NULL) AS has_price
                       FROM ingredients i WHERE i.id = ANY(:ids)"""
                ),
                {"ids": ids},
            ).fetchall()
            if len(ingredient_rows) != len(ids):
                raise ValidationAppError("Công thức chứa nguyên liệu không tồn tại")
            if data.is_active:
                by_id = {row.id: row for row in ingredient_rows}
                problems: list[str] = []
                for item in data.ingredients:
                    ingredient = by_id[item.ingredient_id]
                    if not ingredient.is_active:
                        problems.append(f"nguyên liệu id={item.ingredient_id} đang inactive")
                    if not ingredient.has_nutrition:
                        problems.append(f"nguyên liệu id={item.ingredient_id} thiếu dinh dưỡng")
                    if ingredient.purchase_mode == "regular" and not ingredient.has_price:
                        problems.append(f"nguyên liệu id={item.ingredient_id} thiếu giá chuẩn hoá")
                    if ingredient.purchase_mode == "regular" and ingredient.purchase_increment is None:
                        problems.append(f"nguyên liệu id={item.ingredient_id} thiếu bước mua")
                    if item.unit != ingredient.default_unit:
                        problems.append(
                            f"đơn vị '{item.unit}' của nguyên liệu id={item.ingredient_id} không khớp default_unit '{ingredient.default_unit}'"
                        )
                if problems:
                    raise ValidationAppError("Không thể kích hoạt dish: " + "; ".join(problems))
        before = self._dish_from_db(dish_id) if dish_id else None
        payload = {
            "name": data.name,
            "dtype": data.dish_type.value,
            "method": data.cooking_method.value if data.cooking_method else None,
            "description": data.description,
            "instructions": data.instructions,
            "tags": _json(data.tags),
            "active": data.is_active,
        }
        if dish_id is None:
            row = self.session.execute(
                text(
                    """INSERT INTO dishes
                       (name, dish_type, cooking_method, description, instructions, tags, is_active)
                       VALUES (:name, CAST(:dtype AS dish_type), CAST(:method AS cooking_method),
                               :description, :instructions, CAST(:tags AS jsonb), :active)
                       RETURNING id"""
                ),
                payload,
            ).first()
            dish_id = row.id
            action = "create"
        else:
            self.session.execute(
                text(
                    """UPDATE dishes SET name = :name, dish_type = CAST(:dtype AS dish_type),
                           cooking_method = CAST(:method AS cooking_method), description = :description,
                           instructions = :instructions, tags = CAST(:tags AS jsonb), is_active = :active
                       WHERE id = :id"""
                ),
                {**payload, "id": dish_id},
            )
            self.session.execute(text("DELETE FROM dish_ingredients WHERE dish_id = :id"), {"id": dish_id})
            action = "update"
        for item in data.ingredients:
            self.session.execute(
                text(
                    """INSERT INTO dish_ingredients
                       (dish_id, ingredient_id, quantity, unit, max_extra_quantity, extra_step_quantity)
                       VALUES (:dish_id, :ingredient_id, :quantity, :unit,
                               :max_extra_quantity, :extra_step_quantity)"""
                ),
                {"dish_id": dish_id, **item.model_dump()},
            )
        after = self._dish_from_db(dish_id)
        self._audit(actor_id, action, "dish", dish_id, before, after)
        self.session.commit()
        return after

    def set_dish_active(self, dish_id: int, active: bool, actor_id: int) -> dict[str, Any]:
        before = self._dish_from_db(dish_id)
        if active:
            ready = self.session.execute(
                text(
                    """SELECT ingredient_count, has_complete_nutrition, has_complete_procurement,
                               all_ingredients_active
                       FROM v_dishes_full WHERE id = :id"""
                ),
                {"id": dish_id},
            ).first()
            if not ready or not (
                ready.ingredient_count > 0
                and ready.has_complete_nutrition
                and ready.has_complete_procurement
                and ready.all_ingredients_active
            ):
                raise ValidationAppError(
                    "Không thể kích hoạt dish thiếu recipe, nutrition, procurement hoặc chứa nguyên liệu inactive"
                )
        self.session.execute(text("UPDATE dishes SET is_active = :active WHERE id = :id"), {"active": active, "id": dish_id})
        after = self._dish_from_db(dish_id)
        self._audit(actor_id, "restore" if active else "deactivate", "dish", dish_id, before, after)
        self.session.commit()
        return after

    def delete_dish(self, dish_id: int, actor_id: int) -> None:
        before = self._dish_from_db(dish_id)
        self.session.execute(text("DELETE FROM dishes WHERE id = :id"), {"id": dish_id})
        self._audit(actor_id, "delete", "dish", dish_id, before, None)
        self.session.commit()

    # ------------------------------------------------------------------ quality
    def _quality_cte(self) -> str:
        return f"""WITH issues AS (
            SELECT 'ingredient'::text entity_type, i.id entity_id, i.name entity_name,
                   'missing_price'::text code, 'error'::text severity,
                   'Thiếu giá chuẩn hóa'::text title,
                   'Chưa có giá quy đổi theo đơn vị mặc định.'::text detail, i.updated_at
            FROM ingredients i WHERE i.purchase_mode = 'regular' AND NOT EXISTS (
                SELECT 1 FROM price_snapshots p WHERE p.ingredient_id = i.id
                  AND p.price_per_default_unit IS NOT NULL
            )
            UNION ALL
            SELECT 'ingredient', i.id, i.name, 'missing_nutrition', 'error',
                   'Thiếu dinh dưỡng', 'Chưa có dữ liệu dinh dưỡng trên 100g.', i.updated_at
            FROM ingredients i WHERE NOT EXISTS (
                SELECT 1 FROM nutrition_facts n WHERE n.ingredient_id = i.id
            )
            UNION ALL
            SELECT 'ingredient', i.id, i.name, 'missing_conversion', 'warning',
                   'Cần kiểm tra quy đổi',
                   CASE
                       WHEN LOWER(BTRIM(i.default_unit)) IN ('ml', 'milliliter', 'milliliters')
                           THEN 'Dầu hoặc sữa đang dùng hệ số mặc định 1 g/ml; cần kiểm tra mật độ.'
                       ELSE 'Đơn vị không phải gram nhưng hệ số quy đổi đang bằng 1.'
                   END, i.updated_at
            FROM ingredients i WHERE {MISSING_CONVERSION_SQL}
            UNION ALL
            SELECT 'ingredient', i.id, i.name, 'missing_purchase_rule', 'error',
                   'Thiếu quy cách mua',
                   'Nguyên liệu thường cần giá chuẩn hóa và bước mua trước khi planner V3 sử dụng.',
                   i.updated_at
            FROM ingredients i
            LEFT JOIN LATERAL (
                SELECT price_per_default_unit FROM price_snapshots p
                WHERE p.ingredient_id = i.id ORDER BY recorded_at DESC LIMIT 1
            ) p ON TRUE
            WHERE {MISSING_PURCHASE_RULE_SQL}
            UNION ALL
            SELECT 'ingredient', i.id, i.name, 'missing_storage_rule', 'warning',
                   'Chưa xác minh bảo quản',
                   'Planner chỉ được mua và dùng nguyên liệu này trong cùng ngày.', i.updated_at
            FROM ingredients i WHERE {MISSING_STORAGE_RULE_SQL}
            UNION ALL
            SELECT 'dish', d.id, d.name, 'missing_recipe', 'error',
                   'Thiếu công thức', 'Món chưa có nguyên liệu trong công thức.', d.updated_at
            FROM dishes d WHERE NOT EXISTS (SELECT 1 FROM dish_ingredients di WHERE di.dish_id = d.id)
            UNION ALL
            SELECT 'dish', d.id, d.name, 'missing_price', 'error',
                   'Không tính được chi phí', 'Ít nhất một nguyên liệu trong món đang thiếu giá.', d.updated_at
            FROM dishes d WHERE EXISTS (
                SELECT 1 FROM dish_ingredients di JOIN ingredients i ON i.id = di.ingredient_id
                WHERE di.dish_id = d.id AND i.purchase_mode = 'regular'
                  AND NOT EXISTS (SELECT 1 FROM price_snapshots p
                      WHERE p.ingredient_id = di.ingredient_id
                        AND p.price_per_default_unit IS NOT NULL)
            )
            UNION ALL
            SELECT 'dish', d.id, d.name, 'missing_nutrition', 'error',
                   'Không tính đủ dinh dưỡng', 'Ít nhất một nguyên liệu trong món đang thiếu dinh dưỡng.', d.updated_at
            FROM dishes d WHERE EXISTS (
                SELECT 1 FROM dish_ingredients di
                LEFT JOIN nutrition_facts n ON n.ingredient_id = di.ingredient_id
                WHERE di.dish_id = d.id AND n.id IS NULL
            )
            UNION ALL
            SELECT src.entity_type, src.id, src.name, 'duplicate_name', 'warning',
                   'Tên có khả năng trùng', 'Tên chuẩn hóa trùng với một bản ghi khác.', src.updated_at
            FROM (
                SELECT 'ingredient'::text entity_type, id, name, updated_at,
                       LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) normalized FROM ingredients
                UNION ALL SELECT 'dish', id, name, updated_at,
                       LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) FROM dishes
            ) src JOIN (
                SELECT entity_type, normalized FROM (
                    SELECT 'ingredient'::text entity_type,
                           LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) normalized
                    FROM ingredients
                    UNION ALL
                    SELECT 'dish', LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g'))
                    FROM dishes
                ) all_names GROUP BY entity_type, normalized HAVING COUNT(*) > 1
            ) duplicates USING (entity_type, normalized)
        )"""

    def list_quality_issues(
        self,
        entity_type: str | None,
        severity: str | None,
        code: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if entity_type:
            where.append("entity_type = :entity_type")
            params["entity_type"] = entity_type
        if severity:
            where.append("severity = :severity")
            params["severity"] = severity
        if code:
            where.append("code = :code")
            params["code"] = code
        if search:
            where.append("entity_name ILIKE :search")
            params["search"] = f"%{search.strip()}%"
        clause = " AND ".join(where)
        cte = self._quality_cte()
        total = self.session.execute(text(cte + f" SELECT COUNT(*) FROM issues WHERE {clause}"), params).scalar_one()
        rows = self.session.execute(
            text(cte + f" SELECT * FROM issues WHERE {clause} ORDER BY CASE severity WHEN 'error' THEN 0 ELSE 1 END, updated_at DESC LIMIT :limit OFFSET :offset"),
            params,
        ).fetchall()
        return {"items": [_row_dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}

    # ------------------------------------------------------------------ imports
