# Bảo mật, quyền và dữ liệu nhạy cảm

## Mục tiêu

Áp dụng thay đổi mà không làm suy yếu authentication, authorization, share token hoặc secret handling.

## Nguồn sự thật

- `backend/app/core/security.py`, `core/deps.py`, `core/config.py`, `ai/personalization.py` và identity/AI/shopping-list routers.
- `frontend/src/context/AuthContext.tsx`, route guards, `lib/apiClient.ts`, `.env.example` và `backend/.env.example`.

## Control matrix

| Control | Enforcement chính | Sai lầm cần tránh |
| --- | --- | --- |
| Password | Hash phía backend | Log/plaintext password |
| Access token | Decode token, account active | Tin role từ client/local storage |
| Google login | Backend verify ID token + verified Gmail | Tin credential frontend không verify |
| Role | `require_*` dependencies | Chỉ ẩn menu/button |
| Ownership | Router/use case kiểm owner resource | Lấy ID từ URL rồi query không check user |
| Provider secret | Encryption/config env | Trả API key hoặc encrypted blob cho UI |
| Public share | Token scope + expiry + revoke | Coi token như ID công khai vô hại |
| AI personalization | Consent + purpose mode + context/state role + RLS | Tin User ID/context từ request body |

## Role matrix

`user` chỉ dùng tài nguyên cá nhân. `data_editor` quản lý food data/quality/import/tag. `admin` là role legacy tương thích quyền `super_admin`; `super_admin` quản lý account và AI config/log. Khi thêm endpoint, chọn dependency hẹp nhất; không dùng `require_admin` nếu thao tác chỉ cần data editor, và không dùng data-editor dependency cho user administration.

## Share token và privacy

Shopping share hết hạn sau 7 ngày, scope dữ liệu theo ngày và có thể revoke. Người có token còn hiệu lực có thể xem/toggle purchased state nên token là capability nhạy cảm. Public PATCH một item và bulk PATCH đều build đúng `day/list_scope`, chỉ nhận ID trong visible set; bulk mismatch rollback và trả conflict. Không đưa token thật vào docs, log, screenshot, analytics hoặc error message.

## Logging/retention

AI request log và conversation history khác nhau. Provider secret/header được loại khỏi response/audit. Message chứa `[PERSONAL_CONTEXT]` được thay bằng marker redacted trước khi ghi log, nhưng không có redaction PII tổng quát cho User message, response hoặc payload khác. Conversation và request log có policy 30 ngày riêng; xóa conversation không xóa log tương ứng. Retention không thay thế quyền access, tối thiểu hóa dữ liệu hoặc encryption.

## AI consent và purpose limitation

- `general` không đọc profile và không cần consent.
- `meal_advice`/`health_reference` yêu cầu consent version hiện hành; notice đổi sẽ tắt personalization cho đến khi User đồng ý lại.
- Health mode yêu cầu profile tuổi từ 18 và chỉ là thông tin tham khảo.
- Context reader chỉ SELECT field allow-list; state writer chỉ ghi consent/history/log.
- Actor lấy từ token và được đẩy xuống RLS; client không được chọn User ID khác.
- Native web search chỉ được coi là grounded khi provider trả URL citation hợp lệ; citation không biến nội dung thành chẩn đoán y khoa.

Đường cleanup hiện mở primary engine; deployment tách AI state DB phải kiểm tra retention job thật sự dọn đúng database.

## Khi nào phải cập nhật tài liệu này

Cập nhật khi đổi auth token, Google policy, role, ownership, share behavior, CORS, env variable, encryption, retention hoặc logging/redaction.

## Kiểm tra mức độ hiểu

### Câu 1 (trắc nghiệm)

Frontend có thể là nguồn quyết định quyền cuối không?

A. Có  
B. Không, backend dependency/use case quyết định  
C. Chỉ với admin

### Câu 2 (trắc nghiệm)

Share token nên được xử lý như gì?

A. Chuỗi trang trí  
B. Capability nhạy cảm có scope/expiry  
C. User ID công khai

### Câu 3 (trắc nghiệm)

Google credential phải được verify ở đâu?

A. Chỉ browser  
B. Backend  
C. Database trigger

### Câu 4 (tình huống)

Bạn thêm endpoint xóa dish. Hãy nêu authorization/ownership/data integrity checks phải có.

### Câu 5 (tình huống)

Một issue yêu cầu hiển thị API key provider để “debug nhanh”. Hãy nêu cách hỗ trợ debug mà không lộ secret.

## Đáp án, giải thích và bằng chứng mong đợi

1. **B.** Client có thể bị sửa hoặc gọi API trực tiếp.
2. **B.** Ai có token hợp lệ có quyền trong phạm vi token.
3. **B.** Backend xác minh chữ ký/audience/email state.
4. Require data-editor role phù hợp, validate target/foreign references, thực hiện delete/deactivate theo contract, audit nếu áp dụng và trả status đúng.
5. Chỉ hiển thị trạng thái cấu hình/masked metadata và lỗi test đã rút gọn; đọc secret server-side từ encrypted config/env. Provider secret/header không được đưa vào response/log, nhưng prompt, context và response vẫn phải được coi là dữ liệu nhạy cảm.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
