from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlmodel import Session

from app.core.database import get_session
from app.modules.dishes.schemas import DishDetailResponse, DishSummaryResponse
from app.shared.enums import DishType


router = APIRouter(prefix="/api/dishes", tags=["dishes"])


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


def _summary(row: Any) -> dict[str, Any]:
    data = dict(row._mapping)
    return {
        "id": int(data["id"]),
        "name": str(data["name"]),
        "dish_type": str(data["dish_type"]),
        "cooking_method": str(data["cooking_method"]) if data["cooking_method"] else None,
        "tags": [str(tag) for tag in _json_value(data.get("tags"), [])],
        "total_calories": float(data.get("total_calories") or 0),
        "total_protein_g": float(data.get("total_protein_g") or 0),
        "total_carbs_g": float(data.get("total_carbs_g") or 0),
        "total_fat_g": float(data.get("total_fat_g") or 0),
        "estimated_cost": float(data.get("estimated_cost") or 0),
    }


_SUMMARY_SELECT = """
    SELECT id, name, dish_type, cooking_method, tags,
           total_calories, total_protein_g, total_carbs_g, total_fat_g,
           estimated_cost
    FROM v_dish_candidates
"""


@router.get("", response_model=list[DishSummaryResponse])
def list_dishes(
    search: str | None = None,
    dish_type: DishType | None = None,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    where = ["TRUE"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if search and search.strip():
        where.append("name ILIKE :search")
        params["search"] = f"%{search.strip()}%"
    if dish_type is not None:
        where.append("dish_type::text = :dish_type")
        params["dish_type"] = dish_type.value

    rows = session.execute(
        text(
            _SUMMARY_SELECT
            + f" WHERE {' AND '.join(where)} ORDER BY name, id LIMIT :limit OFFSET :offset"
        ),
        params,
    ).fetchall()
    return [_summary(row) for row in rows]


@router.get("/{dish_id}", response_model=DishDetailResponse)
def get_dish(dish_id: int, session: Session = Depends(get_session)):
    row = session.execute(
        text(
            """
            SELECT v.id, v.name, v.dish_type, v.cooking_method, v.tags,
                   v.total_calories, v.total_protein_g, v.total_carbs_g,
                   v.total_fat_g, v.estimated_cost, v.ingredients,
                   d.description, d.instructions
            FROM v_dish_candidates v
            JOIN dishes d ON d.id = v.id
            WHERE v.id = :id
            """
        ),
        {"id": dish_id},
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy món ăn hoặc món chưa đủ dữ liệu để sử dụng.",
        )

    data = dict(row._mapping)
    result = _summary(row)
    result.update(
        {
            "description": data.get("description"),
            "instructions": data.get("instructions"),
            "ingredients": [
                {
                    "ingredient_id": int(item["ingredient_id"]),
                    "name": str(item["name"]),
                    "quantity": float(item["quantity"]),
                    "unit": str(item["unit"]),
                    "estimated_cost": float(item.get("estimated_cost") or 0),
                }
                for item in _json_value(data.get("ingredients"), [])
            ],
        }
    )
    return result
