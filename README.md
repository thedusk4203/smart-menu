# Git Rule:
* Một commit chỉ nên giải quyết MỘT vấn đề duy nhất.
* Tạo nhánh riêng để làm việc. git checkout loại/tên user/tên tính năng VD: Đạt: git checkout -b feat/dat/ui-dashboard
* Commit comment rõ ràng, chi tiết.
* Không ai được đụng vào 'main'. Mọi thay đổi phải đi qua Pull Request (PR).
* Trước khi tạo PR gộp code vào main, người tạo PR bắt buộc phải pull code mới nhất từ main về nhánh của mình, tự giải quyết conflict (nếu có), test chạy mượt mà trên máy mình rồi hãy push lên và tạo PR.
* Khi cần sửa các file docker-compose.yml, main.py (Backend), router.tsx / App.tsx (Frontend), file .gitignore... thì nhắn vào nhóm trước.
* Không commit file .env (chứa mật khẩu DB, API Key DeepSeek). Nếu lỡ thì chạy (git rm -r --cached <tênfile>), commit lại, push lên.
* Không push code "rác" hoặc code chưa test.
* Xoá, merge nhầm bị conflict thì bỏ qua nhánh hiện tại và tạo nhánh mới

# Note:
    Các file hiện tại đều là file trống tạo sẵn để chuẩn cấu trúc thôi.