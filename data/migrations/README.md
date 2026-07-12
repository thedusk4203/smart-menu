# Database migrations

`data/init_db.sql` là schema đầy đủ cho database mới. Với database đang tồn tại,
chạy migration runner từ backend:

```powershell
cd backend
uv run python scripts/apply_migrations.py
```

Runner tạo bảng `schema_migrations`, áp dụng các file `.sql` theo thứ tự tên và
không chạy lại migration đã được ghi nhận. Sao lưu database trước khi chạy trên
môi trường demo có dữ liệu.
