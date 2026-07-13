-- Reset toàn bộ dữ liệu thực phẩm và lịch sử thực đơn phụ thuộc.
-- Không xóa tài khoản, hồ sơ người dùng, cấu hình AI hoặc nhật ký quản trị.
BEGIN;

TRUNCATE TABLE
    shopping_list_shares,
    shopping_lists,
    meal_plans,
    dish_ingredients,
    dishes,
    meal_ingredients,
    meals,
    price_snapshots,
    nutrition_facts,
    ingredients,
    tag_catalog
RESTART IDENTITY CASCADE;

COMMIT;
