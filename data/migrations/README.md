# Database migrations

`data/init_db.sql` là baseline đầy đủ cho database mới. Database đang tồn tại
phải đi qua runner có registry tường minh; không chạy thủ công cả thư mục SQL.

## Quy trình an toàn

```powershell
cd backend
$env:UV_CACHE_DIR = ".uv-cache"
uv run python scripts/apply_migrations.py --plan
```

`--plan` chỉ đọc schema, kiểm checksum và in các migration đang chờ. Với
`20260720_v3_ledger_inventory.sql`, output còn hiển thị số plan V1/V2, shopping
item và share token sẽ bị xóa.

Sau khi backup PostgreSQL và kiểm output:

```powershell
uv run python scripts/apply_migrations.py --allow-destructive
```

Nếu không có migration phá dữ liệu, có thể chạy không cần cờ
`--allow-destructive`.

## Guardrail

- `MIGRATIONS` trong `backend/scripts/apply_migrations.py` là thứ tự duy nhất.
- File SQL đã được ghi vào `schema_migrations` là immutable; checksum đổi sẽ làm
  runner dừng.
- File SQL tự động chưa đăng ký hoặc file đăng ký bị thiếu đều làm runner dừng.
- Runner giữ PostgreSQL advisory lock để hai process không migrate đồng thời.
- `20260713_reset_food_catalog.sql` là script thủ công, không thuộc runner.
- Fresh database được nhận diện bằng marker baseline và không chạy lại migration
  lịch sử; `--plan` mô phỏng việc này mà không tạo bảng tracking.
