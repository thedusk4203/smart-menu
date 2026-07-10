from __future__ import annotations

import csv
import io

import pytest
from openpyxl import load_workbook

from app.modules.admin.use_cases import AdminService, _as_optional_id, _normalized_code


def test_import_code_is_normalized_and_rejects_unsafe_values():
    assert _normalized_code(" ing-001 ") == "ING-001"
    assert _normalized_code("") is None
    with pytest.raises(ValueError, match="code chỉ gồm"):
        _normalized_code("mã có khoảng trắng")


def test_optional_import_id_requires_positive_integer():
    assert _as_optional_id("12") == 12
    assert _as_optional_id("") is None
    with pytest.raises(ValueError, match="số nguyên dương"):
        _as_optional_id("0")


def test_ingredient_csv_template_exposes_identity_columns():
    service = AdminService(None)  # type: ignore[arg-type]

    content, media_type, filename = service.import_template("ingredients", "csv")
    headers = next(csv.reader(io.StringIO(content.decode("utf-8-sig"))))

    assert media_type.startswith("text/csv")
    assert filename.endswith(".csv")
    assert headers[:3] == ["id", "code", "name"]
    assert "price_per_default_unit" in headers


def test_dish_xlsx_template_includes_data_and_guide_sheets():
    service = AdminService(None)  # type: ignore[arg-type]

    content, media_type, filename = service.import_template("dishes", "xlsx")
    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    headers = next(workbook["Dữ liệu"].iter_rows(values_only=True))

    assert media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert filename.endswith(".xlsx")
    assert workbook.sheetnames == ["Dữ liệu", "Hướng dẫn"]
    assert list(headers[:3]) == ["id", "code", "name"]
    assert "ingredients_json" in headers
