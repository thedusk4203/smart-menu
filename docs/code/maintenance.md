# Quy trình bảo trì và thay đổi có kiểm soát

## Mục tiêu

Biến một yêu cầu thay đổi thành patch có scope rõ, contract nhất quán, migration/test/docs đầy đủ.

## Nguyên tắc

- Một thay đổi nghiệp vụ cần xác định owner module trước khi sửa UI hoặc SQL.
- Không bỏ layer để “đi nhanh”: page không query DB, router không chứa solver, AI không bypass checker.
- Backward compatibility phải được nêu rõ cho API/schema/migration; nếu không giữ được phải có migration/ADR và release note.
- Working tree có thể dirty; chỉ sửa file thuộc scope, không reset hoặc xóa thay đổi của người khác.

## Playbook theo loại thay đổi

| Thay đổi | Việc bắt buộc |
| --- | --- |
| Endpoint mới | Schema, router, role/ownership, use case/repository, factory, API docs đầy đủ, frontend wrapper/page nếu dùng, tests |
| Field/schema mới | Migration + baseline, validation/read-write, export/import/view/quality, TS type, API example, regression test |
| Planner rule | Domain/request, feasibility, solver, independent checker, reason/warning, snapshot, tests feasible/infeasible |
| AI task/provider | Port/client/logging/encryption, schema/grounding, fallback, SSE nếu stream, retention/security tests |
| Page mới | Route/guard/layout, API wrapper/type, UX state, responsive/a11y, API mapping và build |
| Admin import/data rule | Preview/commit boundary, role, audit/quality, conflict policy, template/export, migration/test |

## Docs synchronization gate

Trước PR, đối chiếu: bài Dusk liên quan, developer chapter, API domain/schema và ADR nếu quyết định có ảnh hưởng lâu dài. Khi evidence/count thay đổi, cập nhật baseline trong `code/README.md` và `testing.md`.

## Khi nào phải cập nhật tài liệu này

Cập nhật khi workflow branch/PR, layering, documentation gate, migration/release policy hoặc feature template thay đổi.

## Kiểm tra mức độ hiểu

### Câu 1 (trắc nghiệm)

Thêm field database bắt buộc chỉ cần sửa migration không?

A. Có  
B. Không, phải trace read/write/validation/view/import/frontend/test/docs  
C. Chỉ cần sửa screenshot

### Câu 2 (trắc nghiệm)

Planner rule mới cần test checker riêng vì sao?

A. Checker là defense độc lập với solver  
B. Để giảm số test  
C. Vì frontend không có TypeScript

### Câu 3 (trắc nghiệm)

Khi nào cần ADR?

A. Quyết định kiến trúc/chính sách có hệ quả lâu dài  
B. Sửa chính tả  
C. Đổi màu button

### Câu 4 (tình huống)

Bạn thêm endpoint Admin export mới. Hãy nêu docs/test/security artifacts phải thay đổi.

### Câu 5 (tình huống)

Một bug report nói UI ẩn nút nhưng API vẫn cho mutation. Hãy nêu fix boundary đúng và regression test.

## Đáp án, giải thích và bằng chứng mong đợi

1. **B.** Field sống qua nhiều layer và dữ liệu cũ.
2. **A.** Solver/AI output không tự chứng minh validity.
3. **A.** ADR ghi context/decision/consequence cho maintainer sau này.
4. Router role, service/repository/export format, API schema/docs/example, frontend consumer nếu có, audit/security/no sensitive fields, integration test và release documentation.
5. Thêm/check backend authorization/ownership ở dependency/use case/router; UI chỉ là bổ sung. Test gọi API trực tiếp bằng role thiếu quyền và mong đợi `403`/không mutation.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
