r"""
========================================================================
 test_api.py — Script test tự động cho Smart Menu API (bản cơ bản)
------------------------------------------------------------------------
 Cách chạy:
   1) Mở 1 cửa sổ PowerShell, chạy server và ĐỂ YÊN:
        .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
   2) Mở cửa sổ PowerShell THỨ HAI, vào thư mục backend, chạy:
        python test_api.py
      (không cần kích hoạt venv — script chỉ dùng thư viện sẵn của Python)

 Script sẽ gọi lần lượt 5 nhóm API và in ra kết quả từng bước.
========================================================================
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# In tiếng Việt không lỗi font trên Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "http://127.0.0.1:8000"

_pass = 0
_fail = 0


def call(method, path, body=None, params=None):
    """Gửi 1 request, trả về (status_code, dữ liệu json)."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status, text = resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode("utf-8")
    except urllib.error.URLError:
        print("\n[X] KHÔNG kết nối được tới server.")
        print("    -> Hãy chắc chắn server đang chạy ở cửa sổ khác:")
        print("       .\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload\n")
        sys.exit(1)
    try:
        parsed = json.loads(text) if text else None
    except json.JSONDecodeError:
        parsed = text
    return status, parsed


def step(title, method, path, expect, body=None, params=None, show=None):
    """Chạy 1 bước test và in kết quả gọn gàng."""
    global _pass, _fail
    status, data = call(method, path, body=body, params=params)
    ok = status == expect
    mark = "[ OK ]" if ok else "[FAIL]"
    if ok:
        _pass += 1
    else:
        _fail += 1
    target = f"{method} {path}"
    if params:
        target += "?" + urllib.parse.urlencode(params)
    print(f"  {mark}  {target}")
    print(f"         mô tả : {title}")
    print(f"         kết quả: HTTP {status} (mong đợi {expect})")
    if show:
        try:
            print("         dữ liệu: " + show(data))
        except Exception:
            print(f"         dữ liệu: {data}")
    print()
    return data


def header(n, name):
    print("=" * 64)
    print(f" {n}. {name}")
    print("=" * 64)


def main():
    print("\n>>> Bắt đầu test Smart Menu API tại", BASE, "\n")

    # 0) HEALTH ---------------------------------------------------------
    header(0, "KIỂM TRA SERVER (health)")
    step("Server còn sống không", "GET", "/health", 200,
         show=lambda d: str(d))

    # 1) USERS ----------------------------------------------------------
    header(1, "API TÀI KHOẢN (users)")
    step("Lấy danh sách tài khoản", "GET", "/api/users", 200,
         show=lambda d: f"{len(d)} tài khoản: " + ", ".join(u["email"] for u in d))

    email = f"test_{int(time.time())}@demo.com"  # email duy nhất mỗi lần chạy
    new_user = step("Tạo tài khoản mới", "POST", "/api/users", 201,
                    body={"email": email, "password": "123456", "full_name": "Người Dùng Test"},
                    show=lambda d: f"id={d['id']}, email={d['email']}, role={d['role']}")
    uid = new_user["id"]

    step("Xem chi tiết tài khoản vừa tạo", "GET", f"/api/users/{uid}", 200,
         show=lambda d: f"id={d['id']}, is_active={d['is_active']}")
    step("Tạo trùng email -> phải báo lỗi 409", "POST", "/api/users", 409,
         body={"email": email, "password": "x"},
         show=lambda d: d.get("detail"))

    # 2) PROFILES -------------------------------------------------------
    header(2, "API HỒ SƠ NGƯỜI DÙNG (profiles)")
    step("Xem hồ sơ (tạo tự động khi đăng ký, đang rỗng)", "GET", f"/api/profiles/{uid}", 200,
         show=lambda d: f"họ tên={d['full_name']}, mục tiêu={d['goal']}, số bữa/ngày={d['meals_per_day']}")
    step("Cập nhật hồ sơ", "PUT", f"/api/profiles/{uid}", 200,
         body={"age": 23, "height_cm": 172, "weight_kg": 66, "gender": "male",
               "goal": "gain_muscle", "daily_budget": 85000, "meals_per_day": 3},
         show=lambda d: f"tuổi={d['age']}, cao={d['height_cm']}, nặng={d['weight_kg']}, ngân sách/ngày={d['daily_budget']}")
    step("Thêm nguyên liệu KHÔNG ăn (dầu ăn, id=5)", "POST", f"/api/profiles/{uid}/exclusions", 201,
         body={"ingredient_id": 5, "reason": "dislike"},
         show=lambda d: f"đã loại trừ nguyên liệu id={d['ingredient_id']} ({d['reason']})")
    step("Xem danh sách nguyên liệu loại trừ", "GET", f"/api/profiles/{uid}/exclusions", 200,
         show=lambda d: f"{len(d)} mục")

    # 3) INGREDIENTS ----------------------------------------------------
    header(3, "API NGUYÊN LIỆU (ingredients)")
    step("Lấy danh sách nguyên liệu (kèm dinh dưỡng + giá)", "GET", "/api/ingredients", 200,
         show=lambda d: f"{len(d)} nguyên liệu: " +
                        "; ".join(f"{x['name']}={x['calories']}kcal/100g, {x['latest_price_per_unit']}đ/{x['default_unit']}" for x in d[:3]) + " ...")
    step("Xem chi tiết nguyên liệu id=1 (Ức gà)", "GET", "/api/ingredients/1", 200,
         show=lambda d: f"{d['name']}: {d['calories']}kcal, {d['protein_g']}g đạm/100g")
    iname = f"Test_NL_{int(time.time())}"
    step("Tạo nguyên liệu mới (Đậu phụ)", "POST", "/api/ingredients", 201,
         body={"name": iname, "food_group": "protein", "grams_per_unit": 1,
               "nutrition": {"calories": 76, "protein_g": 8, "carbs_g": 1.9, "fat_g": 4.8}},
         show=lambda d: f"id={d['id']}, {d['name']}, {d['calories']}kcal")

    # 4) MEALS ----------------------------------------------------------
    header(4, "API MÓN ĂN (meals)")
    step("Lấy danh sách món (kèm tổng dinh dưỡng + chi phí)", "GET", "/api/meals", 200,
         show=lambda d: " | ".join(f"{m['name']}: {m['total_calories']:.0f}kcal, {m['estimated_cost']:.0f}đ" for m in d))
    step("Xem chi tiết món id=1 (kèm nguyên liệu)", "GET", "/api/meals/1", 200,
         show=lambda d: f"{d['name']} -> " + ", ".join(f"{i['name']} {i['quantity']:.0f}{i['unit']}" for i in d["ingredients"]))
    new_meal = step("Tạo món mới kèm nguyên liệu", "POST", "/api/meals", 201,
                    body={"name": "Cơm rang trứng", "meal_type": "lunch", "servings": 1, "tags": ["nhanh"],
                          "ingredients": [{"ingredient_id": 2, "quantity": 150, "unit": "g"},
                                          {"ingredient_id": 4, "quantity": 1, "unit": "quả"}]},
                    show=lambda d: f"id={d['id']}, {d['name']}: {d['total_calories']:.0f}kcal, {d['estimated_cost']:.0f}đ")

    # 5) MEAL PLANS -----------------------------------------------------
    header(5, "API LƯU THỰC ĐƠN (meal-plans)")
    new_plan = step("Lưu một thực đơn tuần", "POST", "/api/meal-plans", 201,
                    body={"user_id": uid, "name": "Thực đơn tuần 1",
                          "start_date": "2026-06-16", "end_date": "2026-06-22",
                          "budget_limit": 560000, "total_cost": 135000, "total_calories": 16800,
                          "plan_data": {"2026-06-16": {"breakfast": [2], "lunch": [1]}}},
                    show=lambda d: f"id={d['id']}, {d['name']}, {d['start_date']} -> {d['end_date']}")
    pid = new_plan["id"]
    step("Lấy danh sách thực đơn của user", "GET", "/api/meal-plans", 200,
         params={"user_id": uid},
         show=lambda d: f"{len(d)} thực đơn")
    step("Xem chi tiết thực đơn vừa lưu", "GET", f"/api/meal-plans/{pid}", 200,
         show=lambda d: f"{d['name']}, các ngày: {list(d['plan_data'].keys())}")
    step("Xoá thực đơn vừa lưu", "DELETE", f"/api/meal-plans/{pid}", 204)

    # TỔNG KẾT ----------------------------------------------------------
    print("=" * 64)
    total = _pass + _fail
    print(f" TỔNG KẾT: {_pass}/{total} bước ĐẠT" + (f", {_fail} bước LỖI" if _fail else " — tất cả OK!"))
    print("=" * 64)


if __name__ == "__main__":
    main()
