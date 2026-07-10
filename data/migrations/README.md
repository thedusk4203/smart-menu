# Migrations thủ công

`init_db.sql` đã bao gồm toàn bộ schema admin cho database tạo mới. Với database
đã có sẵn, chạy migration theo thứ tự số trước khi khởi động backend mới:

```powershell
Get-Content .\data\migrations\002_admin.sql | docker exec -i smart-menu-db psql -U postgres -d DATN
Get-Content .\data\migrations\003_import_codes.sql | docker exec -i smart-menu-db psql -U postgres -d DATN
```

Các migration bổ sung role quản trị, audit/import job và mã duy nhất cho nguyên
liệu, món thành phần. Migration có thể chạy lại an toàn.
