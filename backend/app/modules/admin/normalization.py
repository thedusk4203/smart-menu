from __future__ import annotations

import json
import re
from typing import Any


def row_dict(row) -> dict[str, Any]:
    return dict(row._mapping) if row is not None else {}


def json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def normalized_tags(value: Any) -> list[str]:
    raw_tags = value if isinstance(value, list) else str(value or "").split(",")
    tags: list[str] = []
    seen: set[str] = set()
    for raw_tag in raw_tags:
        tag = " ".join(str(raw_tag).split())
        if not tag:
            continue
        if len(tag) > 64:
            raise ValueError(f"Thẻ '{tag}' vượt quá 64 ký tự")
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            tags.append(tag)
    return tags


CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,63}$")


def normalized_code(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    code = str(value).strip().upper()
    if not CODE_PATTERN.fullmatch(code):
        raise ValueError("code chỉ gồm chữ in hoa, số, dấu chấm, gạch dưới hoặc gạch ngang")
    return code


def as_optional_id(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        result = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("id phải là số nguyên dương") from exc
    if result < 1:
        raise ValueError("id phải là số nguyên dương")
    return result


def enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def as_bool(value: Any, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().casefold() in {"1", "true", "yes", "y", "có", "co"}


def as_float(value: Any, field: str, row_number: int, *, default: float | None = None) -> float | None:
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} phải là số") from exc


def as_money(
    value: Any,
    field: str,
    row_number: int,
    *,
    default: float | None = None,
    max_fraction_digits: int = 0,
) -> float | None:
    """Đọc số tiền thô hoặc định dạng Việt Nam từ CSV/XLSX thành số chuẩn."""
    if value is None or str(value).strip() == "":
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
    else:
        raw = str(value).strip().replace("đ", "").replace("Đ", "")
        raw = re.sub(r"\s+", "", raw)
        if not raw or not re.fullmatch(r"[0-9.,]+", raw):
            raise ValueError(f"{field} phải là số tiền hợp lệ")
        fraction = ""
        if "," in raw:
            if raw.count(",") != 1:
                raise ValueError(f"{field} phải là số tiền hợp lệ")
            integer, fraction = raw.split(",")
            integer = integer.replace(".", "")
        elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw):
            integer = raw.replace(".", "")
        elif re.fullmatch(r"\d+", raw):
            integer = raw
        elif re.fullmatch(r"\d+\.\d+", raw):
            integer, fraction = raw.split(".")
        else:
            raise ValueError(f"{field} phải là số tiền hợp lệ")
        if not integer.isdigit() or (fraction and not fraction.isdigit()):
            raise ValueError(f"{field} phải là số tiền hợp lệ")
        if fraction and max_fraction_digits == 0:
            raise ValueError(f"{field} phải là số nguyên đồng")
        if len(fraction) > max_fraction_digits:
            raise ValueError(f"{field} chỉ được có tối đa {max_fraction_digits} số lẻ")
        result = float(f"{integer}.{fraction}" if fraction else integer)
    if result < 0:
        raise ValueError(f"{field} không được âm")
    if max_fraction_digits == 0 and not result.is_integer():
        raise ValueError(f"{field} phải là số nguyên đồng")
    return result

