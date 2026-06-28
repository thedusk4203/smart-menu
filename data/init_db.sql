-- ============================================================
-- init_db.sql — CƠ SỞ DỮ LIỆU ỨNG DỤNG TẠO THỰC ĐƠN
-- Theo ngân sách & dinh dưỡng | Phụ trách: Nguyễn Văn Bình
-- PostgreSQL 16/18
-- ------------------------------------------------------------
-- CÁCH CHẠY: pgAdmin → Query Tool (gắn với DB của đồ án)
--            → Open File → chọn file này → F5.
-- Chạy lại nhiều lần đều được (mỗi lần tự xoá sạch rồi tạo lại).
--
-- !!! CẢNH BÁO: dòng DROP SCHEMA bên dưới XOÁ TOÀN BỘ mọi thứ
--     trong schema "public". Chỉ dùng khi DB này chỉ chứa đồ án.
--
-- Toàn bộ bọc trong 1 transaction: lỗi giữa chừng -> tự rollback.
-- ============================================================

BEGIN;

-- ============================================================
-- PHẦN 0: RESET
-- ============================================================
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;


-- ============================================================
-- PHẦN 1: KIỂU DỮ LIỆU ENUM
-- ============================================================

CREATE TYPE user_role AS ENUM ('user', 'admin');

-- LƯU Ý QUAN TRỌNG: gender / activity_level / physical_goal bên dưới được
-- CHỈNH KHỚP với app/shared/enums.py mà Đức đã viết cho module nutrition
-- (đã merge vào main), để ORM và bộ tính BMR/TDEE đọc/ghi đúng giá trị.
-- Hệ quả: gender hiện chỉ còn male/female (bỏ 'other'); physical_goal hiện
-- CHƯA có 'gain_weight' (tăng cân) dù SRS có đề cập — đây là khoảng trống
-- cần bàn với Đức để bổ sung vào FitnessGoal, lúc đó chỉ cần thêm 1 dòng
-- ALTER TYPE ... ADD VALUE ở đây là đủ, không phá vỡ gì khác.
CREATE TYPE gender AS ENUM ('male', 'female');

CREATE TYPE activity_level AS ENUM (
    'sedentary',    -- Ít vận động (làm việc văn phòng)
    'light',        -- Vận động nhẹ (đi bộ 1-3 ngày/tuần)
    'moderate',      -- Vận động vừa (tập 3-5 ngày/tuần)
    'active'        -- Vận động nhiều (tập 6-7 ngày/tuần)
);

CREATE TYPE physical_goal AS ENUM (
    'maintain',            -- Duy trì cân nặng
    'lose_weight',         -- Giảm cân
    'gain_muscle',         -- Tăng cơ / tăng protein
    'gain_weight'          -- Tăng cân (theo SRS; khớp FitnessGoal.GAIN_WEIGHT)
);
-- DB đã chạy trước đó (chưa drop/recreate): bổ sung giá trị mới bằng
--   ALTER TYPE physical_goal ADD VALUE 'gain_weight';
-- (ALTER TYPE ... ADD VALUE không chạy được bên trong transaction block của
--  pgAdmin Query Tool — chạy riêng lệnh này ngoài BEGIN/COMMIT.)

CREATE TYPE meal_type AS ENUM (
    'breakfast',           -- Bữa sáng
    'lunch',               -- Bữa trưa
    'dinner'               -- Bữa tối
);

CREATE TYPE cooking_method AS ENUM (
    'stir_fry',            -- Xào
    'boil',                -- Luộc
    'soup',                -- Canh
    'braise',              -- Kho
    'steam'                -- Hấp
);

CREATE TYPE food_group AS ENUM (
    'protein',             -- Thịt, cá, trứng, đậu
    'vegetable',           -- Rau củ quả
    'grain',               -- Tinh bột (gạo, bún, mì)
    'dairy',               -- Sữa và chế phẩm
    'fat',                 -- Dầu mỡ
    'fruit',               -- Trái cây
    'other'                -- Khác
);

-- [MỚI] Lý do loại trừ nguyên liệu khỏi thực đơn của 1 người dùng
CREATE TYPE exclusion_reason AS ENUM (
    'allergy',             -- Dị ứng (ràng buộc CỨNG, tuyệt đối không dùng)
    'dislike'              -- Không thích / không ăn (ràng buộc cứng theo yêu cầu user)
);


-- ============================================================
-- PHẦN 2: HÀM TỰ ĐỘNG CẬP NHẬT updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- BẢNG 1: users — Tài khoản người dùng
-- ============================================================
CREATE TABLE users (
    id              SERIAL          PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    hashed_password VARCHAR(255)    NOT NULL,
    role            user_role       NOT NULL DEFAULT 'user',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE users IS 'Tài khoản đăng nhập, phân quyền user/admin';

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- BẢNG 2: user_profiles — Hồ sơ dinh dưỡng (1-1 với users)
-- ============================================================
CREATE TABLE user_profiles (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL UNIQUE
                                    REFERENCES users(id) ON DELETE CASCADE,
    full_name       VARCHAR(255),
    gender          gender,
    age             INTEGER         CHECK (age IS NULL OR (age BETWEEN 1 AND 120)),
    height_cm       NUMERIC(5,1)    CHECK (height_cm IS NULL OR height_cm > 0),
    weight_kg       NUMERIC(5,1)    CHECK (weight_kg IS NULL OR weight_kg > 0),
    activity_level  activity_level  NOT NULL DEFAULT 'sedentary',
    goal            physical_goal   NOT NULL DEFAULT 'maintain',
    -- [MỚI] Số bữa ăn/ngày — input cho thuật toán lập thực đơn (SRS 1.2 / 1.6)
    meals_per_day   SMALLINT        NOT NULL DEFAULT 3 CHECK (meals_per_day BETWEEN 1 AND 5),
    daily_calorie_target  NUMERIC(7,1) CHECK (daily_calorie_target IS NULL OR daily_calorie_target > 0),
    -- LƯU Ý NGÂN SÁCH: cột này là ngân sách THEO NGÀY (đồng).
    -- Ngân sách tuần khi tạo thực đơn (meal_plans.budget_limit) suy ra = daily_budget * 7.
    -- (Chốt quy ước này với Đức — module tính chi phí tiêu thụ giá trị này.)
    daily_budget    NUMERIC(12,2)   CHECK (daily_budget IS NULL OR daily_budget >= 0),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE user_profiles IS 'Thông tin thể trạng, mục tiêu, số bữa/ngày và ngân sách (theo ngày) của người dùng';

CREATE TRIGGER trg_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- BẢNG 3: ingredients — Nguyên liệu
-- ============================================================
CREATE TABLE ingredients (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL UNIQUE,
    food_group      food_group      NOT NULL,
    default_unit    VARCHAR(20)     NOT NULL DEFAULT 'g',   -- đơn vị chuẩn dùng trong công thức (g, ml, quả...)
    -- [MỚI] Số GRAM ứng với 1 default_unit. Cho phép quy MỌI thứ về gram
    -- để khớp nutrition_facts (vốn tính trên 100g).
    --   g  -> 1     | ml (dầu) -> ~0.92 | quả (trứng) -> ~55 ...
    grams_per_unit  NUMERIC(10,4)   NOT NULL DEFAULT 1 CHECK (grams_per_unit > 0),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE ingredients IS 'Danh mục nguyên liệu nấu ăn; grams_per_unit để quy đổi về gram cho tính dinh dưỡng';

CREATE TRIGGER trg_ingredients_updated_at
    BEFORE UPDATE ON ingredients
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- BẢNG 4: nutrition_facts — Dinh dưỡng / 100g (1-1 với ingredients)
-- ============================================================
CREATE TABLE nutrition_facts (
    id              SERIAL          PRIMARY KEY,
    ingredient_id   INTEGER         NOT NULL UNIQUE
                                    REFERENCES ingredients(id) ON DELETE CASCADE,
    calories        NUMERIC(7,2)    NOT NULL DEFAULT 0 CHECK (calories >= 0),  -- kcal/100g
    protein_g       NUMERIC(6,2)    NOT NULL DEFAULT 0 CHECK (protein_g >= 0),
    carbs_g         NUMERIC(6,2)    NOT NULL DEFAULT 0 CHECK (carbs_g  >= 0),
    fat_g           NUMERIC(6,2)    NOT NULL DEFAULT 0 CHECK (fat_g    >= 0),
    fiber_g         NUMERIC(6,2)    NOT NULL DEFAULT 0 CHECK (fiber_g  >= 0)
);
COMMENT ON TABLE nutrition_facts IS 'Thành phần dinh dưỡng trên 100g nguyên liệu';


-- ============================================================
-- BẢNG 5: price_snapshots — Lịch sử giá nguyên liệu
-- ============================================================
CREATE TABLE price_snapshots (
    id              SERIAL          PRIMARY KEY,
    ingredient_id   INTEGER         NOT NULL
                                    REFERENCES ingredients(id) ON DELETE CASCADE,
    -- price + unit: giá GỐC quan sát được (giữ để truy vết: 90000đ/kg, 35000đ/chục...)
    price           NUMERIC(12,2)   NOT NULL CHECK (price >= 0),
    unit            VARCHAR(20)     NOT NULL DEFAULT 'kg',
    -- [MỚI] Giá đã CHUẨN HOÁ về 1 default_unit của nguyên liệu (đồng / default_unit).
    -- VD: gà 90000đ/kg -> 90 đồng/g ; trứng 35000đ/chục -> 3500 đồng/quả.
    -- Module tính chi phí của Đức dùng cột này: cost = quantity * price_per_default_unit.
    price_per_default_unit NUMERIC(14,4) CHECK (price_per_default_unit IS NULL OR price_per_default_unit >= 0),
    source          VARCHAR(255),                                  -- chợ / siêu thị / nguồn
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE price_snapshots IS 'Các mốc giá nguyên liệu theo thời gian; price_per_default_unit là giá đã quy về đơn vị chuẩn';

CREATE INDEX idx_price_ingredient_time
    ON price_snapshots (ingredient_id, recorded_at DESC);


-- ============================================================
-- BẢNG 6: user_excluded_ingredients — Nguyên liệu user dị ứng / không ăn
-- [MỚI] Phục vụ ràng buộc CỨNG của thuật toán (SRS 1.2, 1.6, 1.7)
-- ============================================================
CREATE TABLE user_excluded_ingredients (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL
                                    REFERENCES users(id) ON DELETE CASCADE,
    ingredient_id   INTEGER         NOT NULL
                                    REFERENCES ingredients(id) ON DELETE CASCADE,
    reason          exclusion_reason NOT NULL DEFAULT 'dislike',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, ingredient_id)
);
COMMENT ON TABLE user_excluded_ingredients IS 'Danh sách nguyên liệu dị ứng/không ăn của từng user; planner loại mọi món chứa các nguyên liệu này';

CREATE INDEX idx_excluded_user ON user_excluded_ingredients (user_id);


-- ============================================================
-- BẢNG 7: meals — Món ăn
-- ============================================================
CREATE TABLE meals (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL,
    meal_type       meal_type       NOT NULL,
    cooking_method  cooking_method,
    description     TEXT,
    instructions    TEXT,
    servings        INTEGER         NOT NULL DEFAULT 1 CHECK (servings > 0),
    tags            JSONB           NOT NULL DEFAULT '[]'::jsonb,   -- ["chay","ít dầu",...]
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE meals IS 'Món ăn, kèm nhãn (tags) dạng JSONB để lọc linh hoạt';

CREATE INDEX idx_meals_tags ON meals USING GIN (tags);

CREATE TRIGGER trg_meals_updated_at
    BEFORE UPDATE ON meals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- BẢNG 8: meal_ingredients — Món ↔ Nguyên liệu (nhiều-nhiều)
-- ============================================================
CREATE TABLE meal_ingredients (
    id              SERIAL          PRIMARY KEY,
    meal_id         INTEGER         NOT NULL
                                    REFERENCES meals(id) ON DELETE CASCADE,
    ingredient_id   INTEGER         NOT NULL
                                    REFERENCES ingredients(id) ON DELETE RESTRICT,
    -- quantity LUÔN ghi theo default_unit của nguyên liệu (g / ml / quả).
    quantity        NUMERIC(10,2)   NOT NULL CHECK (quantity > 0),
    unit            VARCHAR(20)     NOT NULL DEFAULT 'g',
    UNIQUE (meal_id, ingredient_id)
);
COMMENT ON TABLE meal_ingredients IS 'Định lượng nguyên liệu trong mỗi món ăn (theo default_unit của nguyên liệu)';

-- [MỚI] tra ngược "nguyên liệu này nằm trong những món nào"
CREATE INDEX idx_meal_ingredients_ingredient ON meal_ingredients (ingredient_id);


-- ============================================================
-- BẢNG 9: meal_plans — Thực đơn theo tuần
-- ============================================================
CREATE TABLE meal_plans (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL
                                    REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255)    NOT NULL DEFAULT 'Thực đơn tuần',
    start_date      DATE            NOT NULL,
    end_date        DATE,
    budget_limit    NUMERIC(12,2)   CHECK (budget_limit IS NULL OR budget_limit >= 0),  -- ngân sách CẢ TUẦN
    total_cost      NUMERIC(12,2)   NOT NULL DEFAULT 0 CHECK (total_cost >= 0),
    total_calories  NUMERIC(9,2)    NOT NULL DEFAULT 0 CHECK (total_calories >= 0),
    -- plan_data: lịch món theo ngày/bữa, dạng JSONB
    -- {"2026-06-10": {"breakfast": [meal_id], "lunch": [...], "dinner": [...]}}
    plan_data       JSONB           NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CHECK (end_date IS NULL OR end_date >= start_date)
);
COMMENT ON TABLE meal_plans IS 'Kế hoạch thực đơn của người dùng; chi tiết lịch món lưu trong plan_data (JSONB); budget_limit theo tuần';

CREATE INDEX idx_meal_plans_user ON meal_plans (user_id);
CREATE INDEX idx_meal_plans_data ON meal_plans USING GIN (plan_data);

CREATE TRIGGER trg_meal_plans_updated_at
    BEFORE UPDATE ON meal_plans
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- BẢNG 10: shopping_lists — Danh sách mua sắm (sinh từ meal_plan)
-- ============================================================
CREATE TABLE shopping_lists (
    id              SERIAL          PRIMARY KEY,
    meal_plan_id    INTEGER         NOT NULL
                                    REFERENCES meal_plans(id) ON DELETE CASCADE,
    ingredient_id   INTEGER         NOT NULL
                                    REFERENCES ingredients(id) ON DELETE RESTRICT,
    total_quantity  NUMERIC(12,2)   NOT NULL CHECK (total_quantity > 0),
    unit            VARCHAR(20)     NOT NULL DEFAULT 'g',
    estimated_cost  NUMERIC(12,2)   NOT NULL DEFAULT 0 CHECK (estimated_cost >= 0),
    is_purchased    BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (meal_plan_id, ingredient_id)
);
COMMENT ON TABLE shopping_lists IS 'Tổng hợp nguyên liệu cần mua cho một thực đơn';


-- ============================================================
-- PHẦN 3: VIEW HỖ TRỢ
-- ============================================================

-- v_ingredients_full: nguyên liệu + dinh dưỡng + giá mới nhất (đã chuẩn hoá)
CREATE VIEW v_ingredients_full AS
SELECT
    i.id,
    i.name,
    i.food_group,
    i.default_unit,
    i.grams_per_unit,
    i.is_active,
    n.calories,
    n.protein_g,
    n.carbs_g,
    n.fat_g,
    n.fiber_g,
    p.price                  AS latest_price,            -- giá gốc (để hiển thị)
    p.unit                   AS price_unit,
    p.price_per_default_unit AS latest_price_per_unit,   -- giá đã quy về default_unit (để tính chi phí)
    p.recorded_at            AS price_recorded_at
FROM ingredients i
LEFT JOIN nutrition_facts n ON n.ingredient_id = i.id
LEFT JOIN LATERAL (
    SELECT price, unit, price_per_default_unit, recorded_at
    FROM price_snapshots ps
    WHERE ps.ingredient_id = i.id
    ORDER BY ps.recorded_at DESC
    LIMIT 1
) p ON TRUE;
COMMENT ON VIEW v_ingredients_full IS 'Nguyên liệu kèm dinh dưỡng và giá mới nhất (gốc + đã chuẩn hoá)';

-- [MỚI] v_meals_full: món ăn + tổng dinh dưỡng & chi phí ước tính (tính từ nguyên liệu)
-- Dinh dưỡng quy về gram qua grams_per_unit; chi phí dùng giá đã chuẩn hoá.
CREATE VIEW v_meals_full AS
SELECT
    m.id,
    m.name,
    m.meal_type,
    m.cooking_method,
    m.servings,
    m.tags,
    m.is_active,
    COALESCE(SUM(mi.quantity * i.grams_per_unit * nf.calories  / 100.0), 0) AS total_calories,
    COALESCE(SUM(mi.quantity * i.grams_per_unit * nf.protein_g / 100.0), 0) AS total_protein_g,
    COALESCE(SUM(mi.quantity * i.grams_per_unit * nf.carbs_g   / 100.0), 0) AS total_carbs_g,
    COALESCE(SUM(mi.quantity * i.grams_per_unit * nf.fat_g     / 100.0), 0) AS total_fat_g,
    COALESCE(SUM(mi.quantity * lp.price_per_default_unit), 0)               AS estimated_cost
FROM meals m
LEFT JOIN meal_ingredients mi ON mi.meal_id = m.id
LEFT JOIN ingredients       i  ON i.id = mi.ingredient_id
LEFT JOIN nutrition_facts   nf ON nf.ingredient_id = mi.ingredient_id
LEFT JOIN LATERAL (
    SELECT price_per_default_unit
    FROM price_snapshots ps
    WHERE ps.ingredient_id = mi.ingredient_id
    ORDER BY ps.recorded_at DESC
    LIMIT 1
) lp ON TRUE
GROUP BY m.id;
COMMENT ON VIEW v_meals_full IS 'Món ăn kèm tổng dinh dưỡng (quy về gram) và chi phí ước tính từ giá mới nhất';

-- v_meal_plan_summary: tóm tắt thực đơn kèm email người tạo
CREATE VIEW v_meal_plan_summary AS
SELECT
    mp.id,
    mp.user_id,
    u.email          AS user_email,
    mp.name,
    mp.start_date,
    mp.end_date,
    mp.budget_limit,
    mp.total_cost,
    mp.total_calories,
    (mp.budget_limit IS NOT NULL AND mp.total_cost > mp.budget_limit) AS over_budget,
    mp.created_at
FROM meal_plans mp
JOIN users u ON u.id = mp.user_id;
COMMENT ON VIEW v_meal_plan_summary IS 'Tóm tắt thực đơn + cờ vượt ngân sách';


-- ============================================================
-- PHẦN 4: DỮ LIỆU MẪU (SEED) — tối thiểu để chạy/demo
-- 2 tài khoản demo: admin@demo.com / admin123, user@demo.com / user123
-- (Mật khẩu đã hash bằng bcrypt cost 12)
-- ============================================================

INSERT INTO users (email, hashed_password, role) VALUES
('admin@demo.com', '$2b$12$4hzAQtCbT.JRoxgOrmaDoObP3brV5B9VUWQaOBOTuo0po1nAFs09C', 'admin'),
('user@demo.com',  '$2b$12$4Na3jWlR4iZCJrESe6U2ceUn8LM/GHnG8V8mFw3S3/.M5Q2TUq8cW', 'user');

INSERT INTO user_profiles (user_id, full_name, gender, age, height_cm, weight_kg, activity_level, goal, meals_per_day, daily_calorie_target, daily_budget)
VALUES
(2, 'Người dùng Demo', 'male', 22, 170.0, 65.0, 'moderate', 'gain_muscle', 3, 2400, 80000);

-- Vài nguyên liệu mẫu (seed đầy đủ 20 nguyên liệu/10 món sẽ bổ sung ở bước sau).
-- grams_per_unit: g->1, ml dầu->0.92, quả trứng->55
INSERT INTO ingredients (name, food_group, default_unit, grams_per_unit) VALUES
('Ức gà',        'protein',   'g',   1),
('Gạo trắng',    'grain',     'g',   1),
('Cải ngọt',     'vegetable', 'g',   1),
('Trứng gà',     'protein',   'quả', 55),
('Dầu ăn',       'fat',       'ml',  0.92);

INSERT INTO nutrition_facts (ingredient_id, calories, protein_g, carbs_g, fat_g, fiber_g) VALUES
(1, 165, 31.0, 0.0,  3.6, 0.0),   -- Ức gà
(2, 130, 2.7,  28.0, 0.3, 0.4),   -- Gạo trắng (đã nấu)
(3, 13,  1.5,  2.2,  0.2, 1.2),   -- Cải ngọt
(4, 155, 13.0, 1.1,  11.0,0.0),   -- Trứng gà
(5, 884, 0.0,  0.0,  100.0,0.0);  -- Dầu ăn

-- price_per_default_unit: gà 90000/kg=90đ/g; gạo 22000/kg=22đ/g; cải 15000/kg=15đ/g;
--                          trứng 35000/chục=3500đ/quả; dầu 45000/lít=45đ/ml
INSERT INTO price_snapshots (ingredient_id, price, unit, price_per_default_unit, source) VALUES
(1, 90000, 'kg',   90,   'Chợ Nam Định'),
(2, 22000, 'kg',   22,   'Siêu thị'),
(3, 15000, 'kg',   15,   'Chợ Nam Định'),
(4, 35000, 'chục', 3500, 'Siêu thị'),
(5, 45000, 'lít',  45,   'Siêu thị');

INSERT INTO meals (name, meal_type, cooking_method, description, servings, tags) VALUES
('Cơm ức gà luộc rau', 'lunch', 'boil', 'Ức gà luộc ăn kèm cơm và cải ngọt', 1, '["healthy","ít dầu","tăng cơ"]'::jsonb),
('Trứng chiên',        'breakfast', 'stir_fry', 'Trứng gà chiên dầu', 1, '["nhanh","rẻ"]'::jsonb);

INSERT INTO meal_ingredients (meal_id, ingredient_id, quantity, unit) VALUES
(1, 1, 150, 'g'),
(1, 2, 200, 'g'),
(1, 3, 100, 'g'),
(2, 4, 2,   'quả'),
(2, 5, 10,  'ml');

-- Ví dụ minh hoạ ràng buộc loại trừ: user demo không ăn dầu (ưu tiên ít dầu)
INSERT INTO user_excluded_ingredients (user_id, ingredient_id, reason) VALUES
(2, 5, 'dislike');

COMMIT;
