from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.security import hash_password
from app.modules.admin.catalog_rules import MISSING_CONVERSION_SQL, PRIVILEGED_ROLES
from app.modules.admin.normalization import enum_value as _enum_value, row_dict as _row_dict
from app.modules.admin.schemas import AdminUserCreate
from app.shared.enums import UserRole


class AdminUserMixin:
    # ------------------------------------------------------------------ dashboard
    def dashboard(self) -> dict[str, Any]:
        row = self.session.execute(
            text(
                f"""SELECT
                    (SELECT COUNT(*) FROM users) AS users_total,
                    (SELECT COUNT(*) FROM users WHERE is_active) AS users_active,
                    (SELECT COUNT(*) FROM users WHERE NOT is_active) AS users_locked,
                    (SELECT COUNT(*) FROM ingredients) AS ingredients_total,
                    (SELECT COUNT(*) FROM ingredients WHERE is_active) AS ingredients_active,
                    (SELECT COUNT(*) FROM dishes) AS dishes_total,
                    (SELECT COUNT(*) FROM v_dish_candidates) AS planner_ready_dishes,
                    (SELECT COUNT(*) FROM v_dish_candidates WHERE dish_type = 'breakfast') AS breakfast_count,
                    (SELECT COUNT(*) FROM v_dish_candidates WHERE dish_type = 'staple') AS staple_count,
                    (SELECT COUNT(*) FROM v_dish_candidates WHERE dish_type = 'savory') AS savory_count,
                    (SELECT COUNT(*) FROM v_dish_candidates WHERE dish_type = 'vegetable_side') AS vegetable_count,
                    (SELECT COUNT(*) FROM v_dish_candidates WHERE dish_type = 'soup') AS soup_count,
                    (SELECT COUNT(*) FROM ingredients i WHERE NOT EXISTS (
                        SELECT 1 FROM price_snapshots p
                        WHERE p.ingredient_id = i.id AND p.price_per_default_unit IS NOT NULL
                    )) AS missing_price,
                    (SELECT COUNT(*) FROM ingredients i WHERE NOT EXISTS (
                        SELECT 1 FROM nutrition_facts n WHERE n.ingredient_id = i.id
                    )) AS missing_nutrition,
                    (SELECT COUNT(*) FROM ingredients i
                     WHERE {MISSING_CONVERSION_SQL}) AS missing_conversion,
                    (SELECT COUNT(*) FROM dishes d WHERE
                        NOT EXISTS (SELECT 1 FROM dish_ingredients di WHERE di.dish_id = d.id)
                        OR EXISTS (
                            SELECT 1 FROM dish_ingredients di
                            LEFT JOIN nutrition_facts n ON n.ingredient_id = di.ingredient_id
                            WHERE di.dish_id = d.id AND n.id IS NULL
                        )
                        OR EXISTS (
                            SELECT 1 FROM dish_ingredients di
                            WHERE di.dish_id = d.id AND NOT EXISTS (
                                SELECT 1 FROM price_snapshots p
                                WHERE p.ingredient_id = di.ingredient_id
                                  AND p.price_per_default_unit IS NOT NULL
                            )
                        )
                    ) AS incomplete_dishes,
                    (SELECT COALESCE(SUM(group_size - 1), 0) FROM (
                        SELECT COUNT(*) AS group_size FROM (
                            SELECT 'ingredient'::text AS entity_type,
                                   LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g')) AS n
                            FROM ingredients
                            UNION ALL
                            SELECT 'dish'::text,
                                   LOWER(REGEXP_REPLACE(BTRIM(name), '\\s+', ' ', 'g'))
                            FROM dishes
                        ) names GROUP BY entity_type, n HAVING COUNT(*) > 1
                    ) duplicate_groups) AS duplicate_names,
                    (SELECT MAX(created_at) FROM import_jobs) AS last_import_at"""
            )
        ).first()
        data = _row_dict(row)
        data["open_quality_issues"] = (
            data["missing_price"]
            + data["missing_nutrition"]
            + data["missing_conversion"]
            + data["incomplete_dishes"]
            + data["duplicate_names"]
        )
        return data

    # ------------------------------------------------------------------ users
    def list_users(
        self,
        search: str | None,
        role: str | None,
        is_active: bool | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            where.append("(u.email ILIKE :search OR p.full_name ILIKE :search)")
            params["search"] = f"%{search.strip()}%"
        if role:
            where.append("u.role::text = :role")
            params["role"] = role
        if is_active is not None:
            where.append("u.is_active = :active")
            params["active"] = is_active
        clause = " AND ".join(where)
        total = self.session.execute(
            text(
                f"""SELECT COUNT(*) FROM users u
                    LEFT JOIN user_profiles p ON p.user_id = u.id WHERE {clause}"""
            ),
            params,
        ).scalar_one()
        rows = self.session.execute(
            text(
                f"""SELECT u.id, u.email, p.full_name, u.role, u.is_active,
                           u.created_at, u.updated_at
                    FROM users u LEFT JOIN user_profiles p ON p.user_id = u.id
                    WHERE {clause}
                    ORDER BY u.created_at DESC, u.id DESC
                    LIMIT :limit OFFSET :offset"""
            ),
            params,
        ).fetchall()
        return {"items": [_row_dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}

    def get_user(self, user_id: int) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """SELECT u.id, u.email, p.full_name, u.role, u.is_active,
                          u.created_at, u.updated_at
                   FROM users u LEFT JOIN user_profiles p ON p.user_id = u.id
                   WHERE u.id = :id"""
            ),
            {"id": user_id},
        ).first()
        if not row:
            raise NotFoundError("Không tìm thấy người dùng")
        return _row_dict(row)

    def create_user(self, data: AdminUserCreate, actor_id: int) -> dict[str, Any]:
        if self.session.execute(text("SELECT 1 FROM users WHERE LOWER(email) = LOWER(:email)"), {"email": data.email}).first():
            raise ConflictError("Email đã được sử dụng")
        row = self.session.execute(
            text(
                """INSERT INTO users (email, hashed_password, role)
                   VALUES (:email, :password, CAST(:role AS user_role)) RETURNING id"""
            ),
            {"email": data.email, "password": hash_password(data.password), "role": data.role.value},
        ).first()
        user_id = row.id
        self.session.execute(
            text("INSERT INTO user_profiles (user_id, full_name) VALUES (:id, :name)"),
            {"id": user_id, "name": data.full_name},
        )
        after = self.get_user(user_id)
        self._audit(actor_id, "create", "user", user_id, after=after)
        self.session.commit()
        return after

    def update_user_role(self, user_id: int, role: UserRole, actor_id: int) -> dict[str, Any]:
        before = self.get_user(user_id)
        if user_id == actor_id and role.value != _enum_value(before["role"]):
            raise ValidationAppError("Bạn không thể tự thay đổi vai trò của chính mình")
        current_role = _enum_value(before["role"])
        if current_role in PRIVILEGED_ROLES and role.value not in PRIVILEGED_ROLES:
            count = self.session.execute(
                text("SELECT COUNT(*) FROM users WHERE role::text IN ('admin', 'super_admin') AND is_active")
            ).scalar_one()
            if count <= 1:
                raise ValidationAppError("Phải giữ lại ít nhất một quản trị viên hệ thống đang hoạt động")
        self.session.execute(
            text("UPDATE users SET role = CAST(:role AS user_role) WHERE id = :id"),
            {"role": role.value, "id": user_id},
        )
        after = self.get_user(user_id)
        self._audit(actor_id, "change_role", "user", user_id, before, after)
        self.session.commit()
        return after

    def update_user_status(self, user_id: int, is_active: bool, actor_id: int) -> dict[str, Any]:
        before = self.get_user(user_id)
        if user_id == actor_id and not is_active:
            raise ValidationAppError("Bạn không thể tự khóa tài khoản của chính mình")
        if _enum_value(before["role"]) in PRIVILEGED_ROLES and not is_active:
            count = self.session.execute(
                text("SELECT COUNT(*) FROM users WHERE role::text IN ('admin', 'super_admin') AND is_active")
            ).scalar_one()
            if count <= 1:
                raise ValidationAppError("Không thể khóa quản trị viên hệ thống cuối cùng")
        self.session.execute(
            text("UPDATE users SET is_active = :active WHERE id = :id"),
            {"active": is_active, "id": user_id},
        )
        after = self.get_user(user_id)
        self._audit(actor_id, "unlock" if is_active else "lock", "user", user_id, before, after)
        self.session.commit()
        return after

