from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_data_editor


class TagWrite(BaseModel):
    name: str = Field(min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def normalize(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Tên thẻ không được để trống")
        return value


class TagActiveUpdate(BaseModel):
    is_active: bool


class TagResponse(BaseModel):
    id: int
    name: str
    is_active: bool


router = APIRouter(prefix="/api/tags", tags=["tags"])
admin_router = APIRouter(prefix="/api/admin/tags", tags=["admin-tags"])


def _row(row) -> TagResponse:
    return TagResponse(id=row.id, name=row.name, is_active=row.is_active)


@router.get("", response_model=list[TagResponse])
def active_tags(session: Session = Depends(get_session)):
    rows = session.execute(text("SELECT id, name, is_active FROM tag_catalog WHERE is_active=TRUE ORDER BY name"))
    return [_row(row) for row in rows]


@admin_router.get("", response_model=list[TagResponse])
def list_tags(
    search: str | None = Query(default=None),
    session: Session = Depends(get_session),
    _=Depends(require_data_editor),
):
    rows = session.execute(
        text("""SELECT id, name, is_active FROM tag_catalog
                WHERE :search IS NULL OR name ILIKE :pattern ORDER BY is_active DESC, name"""),
        {"search": search.strip() if search else None, "pattern": f"%{search.strip()}%" if search else None},
    )
    return [_row(row) for row in rows]


@admin_router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(data: TagWrite, session: Session = Depends(get_session), _=Depends(require_data_editor)):
    try:
        row = session.execute(
            text("INSERT INTO tag_catalog (name) VALUES (:name) RETURNING id, name, is_active"),
            {"name": data.name},
        ).first()
        session.commit()
        return _row(row)
    except Exception as exc:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Thẻ này đã tồn tại") from exc


@admin_router.put("/{tag_id}", response_model=TagResponse)
def rename_tag(tag_id: int, data: TagWrite, session: Session = Depends(get_session), _=Depends(require_data_editor)):
    old = session.execute(text("SELECT name FROM tag_catalog WHERE id=:id FOR UPDATE"), {"id": tag_id}).first()
    if old is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thẻ")
    if old.name != data.name:
        try:
            old_json, new_json = json.dumps(old.name, ensure_ascii=False), json.dumps(data.name, ensure_ascii=False)
            session.execute(text("UPDATE meals SET tags=replace(tags::text, :old, :new)::jsonb WHERE tags::text LIKE :pattern"), {"old": old_json, "new": new_json, "pattern": f"%{old_json}%"})
            session.execute(text("UPDATE dishes SET tags=replace(tags::text, :old, :new)::jsonb WHERE tags::text LIKE :pattern"), {"old": old_json, "new": new_json, "pattern": f"%{old_json}%"})
            session.execute(text("UPDATE meal_plans SET plan_data=replace(plan_data::text, :old, :new)::jsonb WHERE plan_data::text LIKE :pattern"), {"old": old_json, "new": new_json, "pattern": f"%{old_json}%"})
            row = session.execute(text("UPDATE tag_catalog SET name=:name, updated_at=NOW() WHERE id=:id RETURNING id,name,is_active"), {"id": tag_id, "name": data.name}).first()
            session.commit()
            return _row(row)
        except Exception as exc:
            session.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "Tên thẻ này đã tồn tại") from exc
    return TagResponse(id=tag_id, name=old.name, is_active=True)


@admin_router.patch("/{tag_id}/active", response_model=TagResponse)
def set_tag_active(tag_id: int, data: TagActiveUpdate, session: Session = Depends(get_session), _=Depends(require_data_editor)):
    row = session.execute(
        text("UPDATE tag_catalog SET is_active=:active, updated_at=NOW() WHERE id=:id RETURNING id,name,is_active"),
        {"id": tag_id, "active": data.is_active},
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thẻ")
    session.commit()
    return _row(row)
