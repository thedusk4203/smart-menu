-- ============================================================
-- init_db.sql — CƠ SỞ DỮ LIỆU ỨNG DỤNG TẠO THỰC ĐƠN
-- Theo ngân sách & dinh dưỡng | Phụ trách: Nguyễn Văn Bình
-- PostgreSQL 16/18
-- ------------------------------------------------------------      
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

CREATE TYPE user_role AS ENUM ('user', 'data_editor', 'admin', 'super_admin');


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

-- Phân loại nội tại của dish. `side` được giữ trong enum cho dữ liệu catalogue
-- nhưng không tham gia Dish Planner V2.
CREATE TYPE dish_type AS ENUM (
    'staple',              -- Tinh bột (cơm, gạo lứt...)
    'savory',              -- Món mặn (thịt/cá/đậu kho, xào...)
    'soup',                -- Canh
    'vegetable_side',      -- Rau/món phụ
    'side',                -- Món phụ khác
    'breakfast'            -- Món ăn sáng gọn
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
    code            VARCHAR(64)     UNIQUE,
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
    -- Các món con trong một bữa/combo. Với lunch/dinner kiểu Việt thường là
    -- ["Cơm", "Món mặn", "Rau/Canh"], còn breakfast có thể chỉ 1-2 phần.
    components      JSONB           NOT NULL DEFAULT '[]'::jsonb,
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
-- dishes / dish_ingredients: planner ghép trực tiếp các dish trong lúc chạy.
-- ============================================================
CREATE TABLE dishes (
    id              SERIAL          PRIMARY KEY,
    code            VARCHAR(64)     UNIQUE,
    name            VARCHAR(255)    NOT NULL UNIQUE,
    dish_type       dish_type       NOT NULL,
    cooking_method  cooking_method,
    description     TEXT,
    instructions    TEXT,
    tags            JSONB           NOT NULL DEFAULT '[]'::jsonb,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE dishes IS 'Món con (đơn vị nấu): cơm, món mặn, canh, rau...; nguyên liệu ở dish_ingredients';

CREATE TRIGGER trg_dishes_updated_at
    BEFORE UPDATE ON dishes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE dish_ingredients (
    id              SERIAL          PRIMARY KEY,
    dish_id         INTEGER         NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    ingredient_id   INTEGER         NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
    quantity        NUMERIC(10,2)   NOT NULL CHECK (quantity > 0),
    unit            VARCHAR(20)     NOT NULL DEFAULT 'g',
    UNIQUE (dish_id, ingredient_id)
);
CREATE INDEX idx_dish_ingredients_ingredient ON dish_ingredients (ingredient_id);

-- ============================================================
-- BẢNG QUẢN TRỊ: audit log + import có preview/commit
-- ============================================================
CREATE TABLE audit_logs (
    id              BIGSERIAL       PRIMARY KEY,
    actor_user_id   INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action          VARCHAR(50)     NOT NULL,
    entity_type     VARCHAR(50)     NOT NULL,
    entity_id       INTEGER,
    before_data     JSONB,
    after_data      JSONB,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_logs_created_at ON audit_logs (created_at DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs (entity_type, entity_id);

CREATE TABLE llm_provider_configs (
    id                      BIGSERIAL       PRIMARY KEY,
    name                    VARCHAR(100)    NOT NULL,
    provider_type           VARCHAR(30)     NOT NULL
                                            CHECK (provider_type IN ('openai', 'deepseek', 'lmstudio', 'google', 'custom')),
    base_url                VARCHAR(500)    NOT NULL,
    model                   VARCHAR(200)    NOT NULL,
    encrypted_api_key       TEXT,
    api_key_suffix          VARCHAR(8),
    timeout_seconds         NUMERIC(6,2)    NOT NULL DEFAULT 60
                                            CHECK (timeout_seconds BETWEEN 1 AND 300),
    structured_output_mode  VARCHAR(20)     CHECK (structured_output_mode IN ('json_schema', 'json_object')),
    config_version          INTEGER         NOT NULL DEFAULT 1,
    tested_version          INTEGER,
    test_status             VARCHAR(20)     NOT NULL DEFAULT 'untested'
                                            CHECK (test_status IN ('untested', 'success', 'failed')),
    last_tested_at          TIMESTAMPTZ,
    last_test_error         TEXT,
    is_active               BOOLEAN         NOT NULL DEFAULT FALSE,
    created_by              INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by              INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uq_llm_provider_one_active
    ON llm_provider_configs ((is_active)) WHERE is_active = TRUE;

CREATE TABLE ai_request_logs (
    id                  BIGSERIAL       PRIMARY KEY,
    user_id             INTEGER         REFERENCES users(id) ON DELETE SET NULL,
    provider_config_id  BIGINT          REFERENCES llm_provider_configs(id) ON DELETE SET NULL,
    feature             VARCHAR(40)     NOT NULL,
    provider_type       VARCHAR(30)     NOT NULL,
    model               VARCHAR(200)    NOT NULL,
    request_data        JSONB           NOT NULL,
    response_data       JSONB,
    status              VARCHAR(20)     NOT NULL CHECK (status IN ('success', 'error')),
    latency_ms          INTEGER         NOT NULL DEFAULT 0,
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    total_tokens        INTEGER,
    error_message       TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ     NOT NULL DEFAULT (NOW() + INTERVAL '30 days')
);
CREATE INDEX idx_ai_request_logs_created_at ON ai_request_logs (created_at DESC);
CREATE INDEX idx_ai_request_logs_filters ON ai_request_logs (feature, status, user_id);

CREATE TABLE ai_conversations (
    id          BIGSERIAL       PRIMARY KEY,
    user_id     INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(80)     NOT NULL,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ai_conversations_user_updated
    ON ai_conversations (user_id, updated_at DESC, id DESC);

CREATE TABLE ai_conversation_turns (
    id                  BIGSERIAL       PRIMARY KEY,
    conversation_id     BIGINT          NOT NULL
                                        REFERENCES ai_conversations(id) ON DELETE CASCADE,
    turn_number         SMALLINT        NOT NULL CHECK (turn_number BETWEEN 1 AND 20),
    user_content        VARCHAR(4000)   NOT NULL,
    assistant_content   TEXT,
    status              VARCHAR(20)     NOT NULL DEFAULT 'pending'
                                        CHECK (status IN ('pending', 'completed', 'failed')),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (conversation_id, turn_number),
    CONSTRAINT ck_ai_conversation_completed_answer
        CHECK (status <> 'completed' OR NULLIF(BTRIM(assistant_content), '') IS NOT NULL)
);
CREATE INDEX idx_ai_conversation_turns_order
    ON ai_conversation_turns (conversation_id, turn_number);

CREATE TRIGGER trg_ai_conversations_updated_at
    BEFORE UPDATE ON ai_conversations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_ai_conversation_turns_updated_at
    BEFORE UPDATE ON ai_conversation_turns
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE import_jobs (
    id              BIGSERIAL       PRIMARY KEY,
    entity_type     VARCHAR(30)     NOT NULL,
    filename        VARCHAR(255)    NOT NULL,
    status          VARCHAR(30)     NOT NULL,
    payload         JSONB           NOT NULL DEFAULT '[]'::jsonb,
    errors          JSONB           NOT NULL DEFAULT '[]'::jsonb,
    warnings        JSONB           NOT NULL DEFAULT '[]'::jsonb,
    conflicts       JSONB           NOT NULL DEFAULT '[]'::jsonb,
    total_rows      INTEGER         NOT NULL DEFAULT 0,
    valid_rows      INTEGER         NOT NULL DEFAULT 0,
    error_count     INTEGER         NOT NULL DEFAULT 0,
    created_by      INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_import_jobs_created_at ON import_jobs (created_at DESC);


-- ============================================================
-- BẢNG 9: meal_plans — Thực đơn theo tuần
-- ============================================================
CREATE TABLE meal_plans (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL
                                    REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255)    NOT NULL DEFAULT 'Thực đơn',
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

CREATE TABLE shopping_list_shares (
    id UUID PRIMARY KEY,
    meal_plan_id INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uq_active_shopping_list_share ON shopping_list_shares(meal_plan_id) WHERE revoked_at IS NULL;


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
    m.components,
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

-- Dish aggregates. Completeness được tính theo TỪNG nguyên liệu, không suy ra
-- từ SUM (SUM có thể che mất một ingredient chưa có nutrition/giá).
CREATE VIEW v_dishes_full AS
SELECT
    d.id, d.name, d.dish_type, d.cooking_method, d.tags, d.is_active,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.calories  / 100.0), 0) AS total_calories,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.protein_g / 100.0), 0) AS total_protein_g,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.carbs_g   / 100.0), 0) AS total_carbs_g,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.fat_g     / 100.0), 0) AS total_fat_g,
    COALESCE(SUM(di.quantity * lp.price_per_default_unit), 0)               AS estimated_cost,
    COUNT(di.id)                                                            AS ingredient_count,
    COUNT(nf.ingredient_id)                                                 AS nutrition_count,
    COUNT(lp.price_per_default_unit)                                        AS priced_ingredient_count,
    COUNT(di.id) > 0 AND COUNT(nf.ingredient_id) = COUNT(di.id)             AS has_complete_nutrition,
    COUNT(di.id) > 0 AND COUNT(lp.price_per_default_unit) = COUNT(di.id)    AS has_complete_price,
    COUNT(di.id) > 0 AND COALESCE(BOOL_AND(i.is_active), FALSE)             AS all_ingredients_active,
    COALESCE(
        JSONB_AGG(di.ingredient_id ORDER BY di.id) FILTER (WHERE di.id IS NOT NULL),
        '[]'::jsonb
    ) AS ingredient_ids,
    COALESCE(
        JSONB_AGG(
            JSONB_BUILD_OBJECT(
                'ingredient_id', i.id,
                'name', i.name,
                'quantity', di.quantity,
                'unit', di.unit,
                'estimated_cost', COALESCE(di.quantity * lp.price_per_default_unit, 0)
            ) ORDER BY di.id
        ) FILTER (WHERE di.id IS NOT NULL),
        '[]'::jsonb
    ) AS ingredients
FROM dishes d
LEFT JOIN dish_ingredients di ON di.dish_id = d.id
LEFT JOIN ingredients     i  ON i.id = di.ingredient_id
LEFT JOIN nutrition_facts nf ON nf.ingredient_id = di.ingredient_id
LEFT JOIN LATERAL (
    SELECT price_per_default_unit FROM price_snapshots ps
    WHERE ps.ingredient_id = di.ingredient_id ORDER BY ps.recorded_at DESC LIMIT 1
) lp ON TRUE
GROUP BY d.id;
COMMENT ON VIEW v_dishes_full IS 'Dish totals + completeness theo từng ingredient.';

CREATE VIEW v_dish_candidates AS
SELECT
    id, name, dish_type, cooking_method, tags,
    total_calories, total_protein_g, total_carbs_g, total_fat_g, estimated_cost,
    ingredient_count, nutrition_count, priced_ingredient_count,
    all_ingredients_active, has_complete_nutrition, has_complete_price,
    ingredient_ids, ingredients
FROM v_dishes_full
WHERE is_active = TRUE
  AND ingredient_count > 0
  AND all_ingredients_active = TRUE
  AND has_complete_nutrition = TRUE
  AND has_complete_price = TRUE
  AND total_calories > 0
  AND estimated_cost > 0;
COMMENT ON VIEW v_dish_candidates IS 'Dish planner-ready: active, đủ recipe, nutrition, giá và ingredient active.';

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

-- Seed demo đủ rộng cho planner: ~40 nguyên liệu, 24 món (8 sáng / 8 trưa / 8 tối).
-- Số liệu dinh dưỡng và giá là ước lượng hợp lý cho demo; không dùng như dữ liệu y tế/chợ chính thức.
-- grams_per_unit: g->1, ml dầu->~0.92, ml sữa->~1.03, quả trứng->55, hộp sữa chua->100.
INSERT INTO ingredients (name, food_group, default_unit, grams_per_unit) VALUES
('Ức gà',              'protein',   'g',   1),
('Đùi gà',             'protein',   'g',   1),
('Thịt heo nạc',       'protein',   'g',   1),
('Thịt bò',            'protein',   'g',   1),
('Cá thu',             'protein',   'g',   1),
('Cá rô phi',          'protein',   'g',   1),
('Tôm',                'protein',   'g',   1),
('Trứng gà',           'protein',   'quả', 55),
('Đậu phụ',            'protein',   'g',   1),
('Đậu đen',            'protein',   'g',   1),
('Gạo trắng',          'grain',     'g',   1),
('Gạo lứt',            'grain',     'g',   1),
('Bún tươi',           'grain',     'g',   1),
('Mì gạo',             'grain',     'g',   1),
('Yến mạch',           'grain',     'g',   1),
('Khoai lang',         'grain',     'g',   1),
('Bánh mì',            'grain',     'g',   1),
('Nui',                'grain',     'g',   1),
('Cải ngọt',           'vegetable', 'g',   1),
('Rau muống',          'vegetable', 'g',   1),
('Bông cải xanh',      'vegetable', 'g',   1),
('Cà rốt',             'vegetable', 'g',   1),
('Bí đỏ',              'vegetable', 'g',   1),
('Cà chua',            'vegetable', 'g',   1),
('Dưa leo',            'vegetable', 'g',   1),
('Xà lách',            'vegetable', 'g',   1),
('Nấm rơm',            'vegetable', 'g',   1),
('Hành lá',            'vegetable', 'g',   1),
('Dầu ăn',             'fat',       'ml',  0.92),
('Dầu olive',          'fat',       'ml',  0.91),
('Sữa tươi',           'dairy',     'ml',  1.03),
('Sữa chua',           'dairy',     'hộp', 100),
('Chuối',              'fruit',     'g',   1),
('Táo',                'fruit',     'g',   1),
('Cam',                'fruit',     'g',   1),
('Đậu phộng',          'fat',       'g',   1),
('Nước mắm',           'other',     'ml',  1.2),
('Muối',               'other',     'g',   1),
('Đường',              'other',     'g',   1),
('Tỏi',                'other',     'g',   1),
('Gừng',               'other',     'g',   1),
('Cua đồng',           'protein',   'g',   1),
('Rau đay',            'vegetable', 'g',   1),
('Thịt ba chỉ',        'protein',   'g',   1),
('Nước dừa',           'other',     'ml',  1),
('Mồng tơi',           'vegetable', 'g',   1),
('Mướp',               'vegetable', 'g',   1);

INSERT INTO nutrition_facts (ingredient_id, calories, protein_g, carbs_g, fat_g, fiber_g)
SELECT i.id, v.calories, v.protein_g, v.carbs_g, v.fat_g, v.fiber_g
FROM (VALUES
('Ức gà',         165, 31.0,  0.0,   3.6,  0.0),
('Đùi gà',        209, 26.0,  0.0,  10.9,  0.0),
('Thịt heo nạc',  143, 21.0,  0.0,   5.0,  0.0),
('Thịt bò',       250, 26.0,  0.0,  15.0,  0.0),
('Cá thu',        205, 19.0,  0.0,  13.9,  0.0),
('Cá rô phi',     128, 26.0,  0.0,   2.7,  0.0),
('Tôm',            99, 24.0,  0.2,   0.3,  0.0),
('Trứng gà',      155, 13.0,  1.1,  11.0,  0.0),
('Đậu phụ',        76,  8.0,  1.9,   4.8,  0.3),
('Đậu đen',       132,  8.9, 23.7,   0.5,  8.7),
('Gạo trắng',     130,  2.7, 28.0,   0.3,  0.4),
('Gạo lứt',       111,  2.6, 23.0,   0.9,  1.8),
('Bún tươi',      110,  1.7, 25.7,   0.2,  0.5),
('Mì gạo',        109,  1.8, 24.9,   0.2,  0.9),
('Yến mạch',      389, 16.9, 66.3,   6.9, 10.6),
('Khoai lang',     86,  1.6, 20.1,   0.1,  3.0),
('Bánh mì',       265,  9.0, 49.0,   3.2,  2.7),
('Nui',           157,  5.8, 30.9,   0.9,  1.8),
('Cải ngọt',       13,  1.5,  2.2,   0.2,  1.2),
('Rau muống',      19,  2.6,  3.1,   0.2,  2.1),
('Bông cải xanh',  34,  2.8,  6.6,   0.4,  2.6),
('Cà rốt',         41,  0.9,  9.6,   0.2,  2.8),
('Bí đỏ',          26,  1.0,  6.5,   0.1,  0.5),
('Cà chua',        18,  0.9,  3.9,   0.2,  1.2),
('Dưa leo',        15,  0.7,  3.6,   0.1,  0.5),
('Xà lách',        15,  1.4,  2.9,   0.2,  1.3),
('Nấm rơm',        22,  3.1,  3.3,   0.3,  1.0),
('Hành lá',        32,  1.8,  7.3,   0.2,  2.6),
('Dầu ăn',        884,  0.0,  0.0, 100.0,  0.0),
('Dầu olive',     884,  0.0,  0.0, 100.0,  0.0),
('Sữa tươi',       61,  3.2,  4.8,   3.3,  0.0),
('Sữa chua',       59,  3.5,  4.7,   3.3,  0.0),
('Chuối',          89,  1.1, 22.8,   0.3,  2.6),
('Táo',            52,  0.3, 13.8,   0.2,  2.4),
('Cam',            47,  0.9, 11.8,   0.1,  2.4),
('Đậu phộng',     567, 25.8, 16.1,  49.2,  8.5),
('Nước mắm',       35,  5.0,  3.6,   0.0,  0.0),
('Muối',            0,  0.0,  0.0,   0.0,  0.0),
('Đường',         387,  0.0,100.0,   0.0,  0.0),
('Tỏi',           149,  6.4, 33.1,   0.5,  2.1),
('Gừng',           80,  1.8, 17.8,   0.8,  2.0),
('Cua đồng',       87, 12.3,  2.0,   3.3,  0.0),
('Rau đay',        34,  4.6,  5.8,   0.3,  1.5),
('Thịt ba chỉ',   518,  9.3,  0.0,  53.0,  0.0),
('Nước dừa',       19,  0.7,  3.7,   0.2,  1.1),
('Mồng tơi',       19,  1.8,  3.4,   0.3,  2.1),
('Mướp',           20,  1.2,  4.4,   0.2,  1.1)
) AS v(name, calories, protein_g, carbs_g, fat_g, fiber_g)
JOIN ingredients i ON i.name = v.name;

INSERT INTO price_snapshots (ingredient_id, price, unit, price_per_default_unit, source)
SELECT i.id, v.price, v.unit, v.price_per_default_unit, v.source
FROM (VALUES
('Ức gà',          90000, 'kg',    90,   'Chợ Nam Định'),
('Đùi gà',         65000, 'kg',    65,   'Chợ Nam Định'),
('Thịt heo nạc',  110000, 'kg',   110,   'Chợ Nam Định'),
('Thịt bò',       220000, 'kg',   220,   'Siêu thị'),
('Cá thu',        150000, 'kg',   150,   'Chợ Nam Định'),
('Cá rô phi',      60000, 'kg',    60,   'Chợ Nam Định'),
('Tôm',           180000, 'kg',   180,   'Chợ Nam Định'),
('Trứng gà',       35000, 'chục',3500,   'Siêu thị'),
('Đậu phụ',        30000, 'kg',    30,   'Chợ Nam Định'),
('Đậu đen',        45000, 'kg',    45,   'Siêu thị'),
('Gạo trắng',      22000, 'kg',    22,   'Siêu thị'),
('Gạo lứt',        35000, 'kg',    35,   'Siêu thị'),
('Bún tươi',       18000, 'kg',    18,   'Chợ Nam Định'),
('Mì gạo',         30000, 'kg',    30,   'Siêu thị'),
('Yến mạch',       90000, 'kg',    90,   'Siêu thị'),
('Khoai lang',     25000, 'kg',    25,   'Chợ Nam Định'),
('Bánh mì',        25000, 'kg',    25,   'Tiệm bánh'),
('Nui',            50000, 'kg',    50,   'Siêu thị'),
('Cải ngọt',       15000, 'kg',    15,   'Chợ Nam Định'),
('Rau muống',      12000, 'kg',    12,   'Chợ Nam Định'),
('Bông cải xanh',  45000, 'kg',    45,   'Siêu thị'),
('Cà rốt',         25000, 'kg',    25,   'Chợ Nam Định'),
('Bí đỏ',          18000, 'kg',    18,   'Chợ Nam Định'),
('Cà chua',        22000, 'kg',    22,   'Chợ Nam Định'),
('Dưa leo',        15000, 'kg',    15,   'Chợ Nam Định'),
('Xà lách',        30000, 'kg',    30,   'Siêu thị'),
('Nấm rơm',        70000, 'kg',    70,   'Chợ Nam Định'),
('Hành lá',        40000, 'kg',    40,   'Chợ Nam Định'),
('Dầu ăn',         45000, 'lít',   45,   'Siêu thị'),
('Dầu olive',     180000, 'lít',  180,   'Siêu thị'),
('Sữa tươi',       35000, 'lít',   35,   'Siêu thị'),
('Sữa chua',       30000, '4 hộp',7500,  'Siêu thị'),
('Chuối',          25000, 'kg',    25,   'Chợ Nam Định'),
('Táo',            60000, 'kg',    60,   'Siêu thị'),
('Cam',            35000, 'kg',    35,   'Chợ Nam Định'),
('Đậu phộng',      70000, 'kg',    70,   'Chợ Nam Định'),
('Nước mắm',       60000, 'lít',   60,   'Siêu thị'),
('Muối',           10000, 'kg',    10,   'Siêu thị'),
('Đường',          25000, 'kg',    25,   'Siêu thị'),
('Tỏi',            60000, 'kg',    60,   'Chợ Nam Định'),
('Gừng',           50000, 'kg',    50,   'Chợ Nam Định'),
('Cua đồng',      120000, 'kg',   120,   'Chợ Nam Định'),
('Rau đay',        12000, 'kg',    12,   'Chợ Nam Định'),
('Thịt ba chỉ',   130000, 'kg',   130,   'Chợ Nam Định'),
('Nước dừa',       15000, 'lít',   15,   'Chợ Nam Định'),
('Mồng tơi',       12000, 'kg',    12,   'Chợ Nam Định'),
('Mướp',           15000, 'kg',    15,   'Chợ Nam Định')
) AS v(name, price, unit, price_per_default_unit, source)
JOIN ingredients i ON i.name = v.name;

INSERT INTO meals (name, meal_type, cooking_method, description, servings, tags, components) VALUES
('Trứng chiên bánh mì',        'breakfast', 'stir_fry', 'Bữa sáng gọn gồm trứng chiên, bánh mì và dưa leo', 1, '["nhanh","rẻ","no lâu"]'::jsonb, '["Trứng chiên","Bánh mì","Dưa leo"]'::jsonb),
('Cháo yến mạch chuối',        'breakfast', 'boil',     'Yến mạch nấu sữa, chuối và đậu phộng', 1, '["healthy","no lâu"]'::jsonb, '["Cháo yến mạch sữa","Chuối","Đậu phộng"]'::jsonb),
('Bún trứng rau cải',          'breakfast', 'boil',     'Bún tươi ăn cùng trứng và cải ngọt', 1, '["nhanh","rẻ","nhiều rau"]'::jsonb, '["Bún tươi","Trứng luộc","Rau cải"]'::jsonb),
('Bánh mì trứng dưa leo',      'breakfast', 'boil',     'Bánh mì kẹp trứng luộc, dưa leo và xà lách', 1, '["nhanh","rẻ"]'::jsonb, '["Bánh mì","Trứng luộc","Dưa leo","Xà lách"]'::jsonb),
('Sữa chua yến mạch táo',      'breakfast', NULL,       'Sữa chua ăn cùng yến mạch và táo', 1, '["healthy","nhanh"]'::jsonb, '["Sữa chua","Yến mạch","Táo"]'::jsonb),
('Khoai lang trứng luộc',      'breakfast', 'boil',     'Khoai lang, trứng luộc và cam', 1, '["healthy","no lâu","rẻ"]'::jsonb, '["Khoai lang","Trứng luộc","Cam"]'::jsonb),
('Nui xào trứng',              'breakfast', 'stir_fry', 'Nui xào trứng, cà rốt và hành lá', 1, '["nhanh","rẻ"]'::jsonb, '["Nui xào trứng","Cà rốt","Hành lá"]'::jsonb),
('Cơm gạo lứt trứng',          'breakfast', 'stir_fry', 'Cơm gạo lứt ăn cùng trứng và cải ngọt', 1, '["healthy","no lâu"]'::jsonb, '["Cơm gạo lứt","Trứng xào","Cải ngọt"]'::jsonb),
('Bữa trưa gà luộc canh cải',  'lunch',     'boil',     'Mâm cơm trưa gồm cơm trắng, ức gà luộc, canh cải ngọt và nước mắm', 1, '["healthy","ít dầu","tăng cơ","giàu đạm"]'::jsonb, '["Cơm trắng","Ức gà luộc","Canh cải ngọt","Nước mắm"]'::jsonb),
('Bữa trưa gà xào bông cải',   'lunch',     'stir_fry', 'Mâm cơm trưa gồm cơm trắng, gà xào bông cải và cà rốt', 1, '["nhiều rau","giàu đạm"]'::jsonb, '["Cơm trắng","Gà xào bông cải","Cà rốt"]'::jsonb),
('Bữa trưa thịt nạc cà rốt',   'lunch',     'stir_fry', 'Mâm cơm trưa gồm cơm trắng, thịt nạc xào cà rốt và cà chua', 1, '["rẻ","no lâu"]'::jsonb, '["Cơm trắng","Thịt nạc xào cà rốt","Cà chua"]'::jsonb),
('Bữa trưa bún cá rau cải',    'lunch',     'boil',     'Bữa trưa nhẹ gồm bún cá rô phi, rau cải và hành lá', 1, '["healthy","ít dầu","giàu đạm"]'::jsonb, '["Bún cá rô phi","Rau cải","Hành lá"]'::jsonb),
('Bữa trưa bò xào rau muống',  'lunch',     'stir_fry', 'Mâm cơm trưa gồm cơm trắng, bò xào rau muống và tỏi', 1, '["giàu đạm","no lâu"]'::jsonb, '["Cơm trắng","Bò xào rau muống","Tỏi"]'::jsonb),
('Bữa trưa đậu phụ sốt cà',    'lunch',     'braise',   'Mâm cơm trưa gồm cơm trắng, đậu phụ sốt cà chua và hành lá', 1, '["rẻ","healthy","nhiều rau"]'::jsonb, '["Cơm trắng","Đậu phụ sốt cà chua","Hành lá"]'::jsonb),
('Bữa trưa tôm bí đỏ',         'lunch',     'stir_fry', 'Mâm cơm trưa gồm cơm trắng, tôm xào bí đỏ và hành lá', 1, '["giàu đạm","nhiều rau"]'::jsonb, '["Cơm trắng","Tôm xào bí đỏ","Hành lá"]'::jsonb),
('Bữa trưa cá thu cà chua',    'lunch',     'braise',   'Mâm cơm trưa gồm cơm trắng, cá thu kho cà chua và xà lách', 1, '["giàu đạm","no lâu"]'::jsonb, '["Cơm trắng","Cá thu kho cà chua","Xà lách"]'::jsonb),
('Bữa tối cá rô phi gạo lứt',  'dinner',    'steam',    'Mâm cơm tối gồm cơm gạo lứt, cá rô phi hấp và bông cải xanh', 1, '["healthy","ít dầu","giàu đạm"]'::jsonb, '["Cơm gạo lứt","Cá rô phi hấp","Bông cải xanh"]'::jsonb),
('Bữa tối canh bí thịt nạc',   'dinner',    'soup',     'Mâm cơm tối gồm cơm trắng, canh bí đỏ thịt nạc và hành lá', 1, '["rẻ","nhiều rau","no lâu"]'::jsonb, '["Cơm trắng","Canh bí đỏ thịt nạc","Hành lá"]'::jsonb),
('Bữa tối đậu phụ nấm rau',    'dinner',    'stir_fry', 'Mâm cơm tối gồm cơm gạo lứt, đậu phụ xào nấm và rau muống', 1, '["healthy","nhiều rau","rẻ"]'::jsonb, '["Cơm gạo lứt","Đậu phụ xào nấm","Rau muống"]'::jsonb),
('Bữa tối tôm bông cải',       'dinner',    'stir_fry', 'Mâm cơm tối gồm cơm trắng, tôm xào bông cải và tỏi', 1, '["giàu đạm","nhiều rau"]'::jsonb, '["Cơm trắng","Tôm xào bông cải","Tỏi"]'::jsonb),
('Bữa tối gà kho gừng',        'dinner',    'braise',   'Mâm cơm tối gồm cơm trắng, gà kho gừng và cà rốt', 1, '["no lâu","giàu đạm"]'::jsonb, '["Cơm trắng","Gà kho gừng","Cà rốt"]'::jsonb),
('Bữa tối bò rau cải',         'dinner',    'stir_fry', 'Mâm cơm tối gồm cơm trắng, bò xào cà rốt và cải ngọt', 1, '["giàu đạm","nhiều rau"]'::jsonb, '["Cơm trắng","Bò xào cà rốt","Cải ngọt"]'::jsonb),
('Bữa tối cá thu kho cà',      'dinner',    'braise',   'Mâm cơm tối gồm cơm trắng, cá thu kho cà chua và hành lá', 1, '["giàu đạm","no lâu"]'::jsonb, '["Cơm trắng","Cá thu kho cà chua","Hành lá"]'::jsonb),
('Bữa tối đậu đen trứng rau',  'dinner',    'boil',     'Mâm cơm tối gồm cơm gạo lứt, đậu đen, trứng và rau sống', 1, '["healthy","rẻ","no lâu"]'::jsonb, '["Cơm gạo lứt","Đậu đen","Trứng luộc","Rau sống"]'::jsonb);

INSERT INTO meal_ingredients (meal_id, ingredient_id, quantity, unit)
SELECT m.id, i.id, v.quantity, v.unit
FROM (VALUES
('Trứng chiên bánh mì',         'Trứng gà',       2,   'quả'),
('Trứng chiên bánh mì',         'Bánh mì',       80,   'g'),
('Trứng chiên bánh mì',         'Dưa leo',       50,   'g'),
('Trứng chiên bánh mì',         'Dầu ăn',         5,   'ml'),
('Trứng chiên bánh mì',         'Hành lá',        5,   'g'),
('Cháo yến mạch chuối',         'Yến mạch',      60,   'g'),
('Cháo yến mạch chuối',         'Sữa tươi',     200,   'ml'),
('Cháo yến mạch chuối',         'Chuối',        100,   'g'),
('Cháo yến mạch chuối',         'Đậu phộng',     10,   'g'),
('Bún trứng rau cải',           'Bún tươi',     180,   'g'),
('Bún trứng rau cải',           'Trứng gà',       1,   'quả'),
('Bún trứng rau cải',           'Cải ngọt',      80,   'g'),
('Bún trứng rau cải',           'Hành lá',        5,   'g'),
('Bún trứng rau cải',           'Nước mắm',       5,   'ml'),
('Bánh mì trứng dưa leo',       'Bánh mì',      100,   'g'),
('Bánh mì trứng dưa leo',       'Trứng gà',       1,   'quả'),
('Bánh mì trứng dưa leo',       'Dưa leo',       70,   'g'),
('Bánh mì trứng dưa leo',       'Xà lách',       30,   'g'),
('Sữa chua yến mạch táo',       'Sữa chua',       1,   'hộp'),
('Sữa chua yến mạch táo',       'Yến mạch',      40,   'g'),
('Sữa chua yến mạch táo',       'Táo',          120,   'g'),
('Khoai lang trứng luộc',       'Khoai lang',   220,   'g'),
('Khoai lang trứng luộc',       'Trứng gà',       2,   'quả'),
('Khoai lang trứng luộc',       'Cam',          100,   'g'),
('Nui xào trứng',               'Nui',          150,   'g'),
('Nui xào trứng',               'Trứng gà',       1,   'quả'),
('Nui xào trứng',               'Cà rốt',        50,   'g'),
('Nui xào trứng',               'Dầu ăn',         5,   'ml'),
('Nui xào trứng',               'Hành lá',        5,   'g'),
('Cơm gạo lứt trứng',           'Gạo lứt',      180,   'g'),
('Cơm gạo lứt trứng',           'Trứng gà',       1,   'quả'),
('Cơm gạo lứt trứng',           'Cải ngọt',      70,   'g'),
('Cơm gạo lứt trứng',           'Dầu ăn',         4,   'ml'),
('Bữa trưa gà luộc canh cải',   'Ức gà',        150,   'g'),
('Bữa trưa gà luộc canh cải',   'Gạo trắng',    200,   'g'),
('Bữa trưa gà luộc canh cải',   'Cải ngọt',     120,   'g'),
('Bữa trưa gà luộc canh cải',   'Nước mắm',       8,   'ml'),
('Bữa trưa gà xào bông cải',    'Đùi gà',       140,   'g'),
('Bữa trưa gà xào bông cải',    'Gạo trắng',    180,   'g'),
('Bữa trưa gà xào bông cải',    'Bông cải xanh',120,   'g'),
('Bữa trưa gà xào bông cải',    'Cà rốt',        50,   'g'),
('Bữa trưa gà xào bông cải',    'Dầu ăn',         8,   'ml'),
('Bữa trưa gà xào bông cải',    'Tỏi',            5,   'g'),
('Bữa trưa thịt nạc cà rốt',    'Thịt heo nạc', 130,   'g'),
('Bữa trưa thịt nạc cà rốt',    'Gạo trắng',    200,   'g'),
('Bữa trưa thịt nạc cà rốt',    'Cà rốt',       100,   'g'),
('Bữa trưa thịt nạc cà rốt',    'Cà chua',       60,   'g'),
('Bữa trưa thịt nạc cà rốt',    'Dầu ăn',         6,   'ml'),
('Bữa trưa bún cá rau cải',     'Cá rô phi',    150,   'g'),
('Bữa trưa bún cá rau cải',     'Bún tươi',     200,   'g'),
('Bữa trưa bún cá rau cải',     'Cải ngọt',     100,   'g'),
('Bữa trưa bún cá rau cải',     'Hành lá',        5,   'g'),
('Bữa trưa bún cá rau cải',     'Nước mắm',       8,   'ml'),
('Bữa trưa bò xào rau muống',   'Thịt bò',      120,   'g'),
('Bữa trưa bò xào rau muống',   'Gạo trắng',    200,   'g'),
('Bữa trưa bò xào rau muống',   'Rau muống',    120,   'g'),
('Bữa trưa bò xào rau muống',   'Dầu ăn',         8,   'ml'),
('Bữa trưa bò xào rau muống',   'Tỏi',            5,   'g'),
('Bữa trưa đậu phụ sốt cà',     'Đậu phụ',      180,   'g'),
('Bữa trưa đậu phụ sốt cà',     'Gạo trắng',    200,   'g'),
('Bữa trưa đậu phụ sốt cà',     'Cà chua',      120,   'g'),
('Bữa trưa đậu phụ sốt cà',     'Hành lá',        8,   'g'),
('Bữa trưa đậu phụ sốt cà',     'Dầu ăn',         6,   'ml'),
('Bữa trưa tôm bí đỏ',          'Tôm',          140,   'g'),
('Bữa trưa tôm bí đỏ',          'Gạo trắng',    190,   'g'),
('Bữa trưa tôm bí đỏ',          'Bí đỏ',        150,   'g'),
('Bữa trưa tôm bí đỏ',          'Hành lá',        5,   'g'),
('Bữa trưa tôm bí đỏ',          'Dầu ăn',         5,   'ml'),
('Bữa trưa cá thu cà chua',     'Cá thu',       130,   'g'),
('Bữa trưa cá thu cà chua',     'Gạo trắng',    190,   'g'),
('Bữa trưa cá thu cà chua',     'Cà chua',      120,   'g'),
('Bữa trưa cá thu cà chua',     'Xà lách',       50,   'g'),
('Bữa trưa cá thu cà chua',     'Dầu ăn',         5,   'ml'),
('Bữa tối cá rô phi gạo lứt',   'Cá rô phi',    150,   'g'),
('Bữa tối cá rô phi gạo lứt',   'Gạo lứt',      190,   'g'),
('Bữa tối cá rô phi gạo lứt',   'Bông cải xanh',100,   'g'),
('Bữa tối cá rô phi gạo lứt',   'Dầu olive',      5,   'ml'),
('Bữa tối canh bí thịt nạc',    'Thịt heo nạc', 120,   'g'),
('Bữa tối canh bí thịt nạc',    'Bí đỏ',        180,   'g'),
('Bữa tối canh bí thịt nạc',    'Gạo trắng',    180,   'g'),
('Bữa tối canh bí thịt nạc',    'Hành lá',        5,   'g'),
('Bữa tối canh bí thịt nạc',    'Nước mắm',       8,   'ml'),
('Bữa tối đậu phụ nấm rau',     'Đậu phụ',      180,   'g'),
('Bữa tối đậu phụ nấm rau',     'Nấm rơm',      120,   'g'),
('Bữa tối đậu phụ nấm rau',     'Rau muống',    100,   'g'),
('Bữa tối đậu phụ nấm rau',     'Gạo lứt',      170,   'g'),
('Bữa tối đậu phụ nấm rau',     'Dầu ăn',         6,   'ml'),
('Bữa tối đậu phụ nấm rau',     'Tỏi',            5,   'g'),
('Bữa tối tôm bông cải',        'Tôm',          130,   'g'),
('Bữa tối tôm bông cải',        'Bông cải xanh',130,   'g'),
('Bữa tối tôm bông cải',        'Gạo trắng',    180,   'g'),
('Bữa tối tôm bông cải',        'Dầu olive',      5,   'ml'),
('Bữa tối tôm bông cải',        'Tỏi',            5,   'g'),
('Bữa tối gà kho gừng',         'Đùi gà',       150,   'g'),
('Bữa tối gà kho gừng',         'Gạo trắng',    190,   'g'),
('Bữa tối gà kho gừng',         'Cà rốt',        80,   'g'),
('Bữa tối gà kho gừng',         'Nước mắm',      10,   'ml'),
('Bữa tối gà kho gừng',         'Đường',          5,   'g'),
('Bữa tối gà kho gừng',         'Tỏi',            5,   'g'),
('Bữa tối gà kho gừng',         'Gừng',           8,   'g'),
('Bữa tối bò rau cải',          'Thịt bò',      120,   'g'),
('Bữa tối bò rau cải',          'Cà rốt',       100,   'g'),
('Bữa tối bò rau cải',          'Cải ngọt',     100,   'g'),
('Bữa tối bò rau cải',          'Gạo trắng',    180,   'g'),
('Bữa tối bò rau cải',          'Dầu ăn',         6,   'ml'),
('Bữa tối bò rau cải',          'Tỏi',            5,   'g'),
('Bữa tối cá thu kho cà',       'Cá thu',       130,   'g'),
('Bữa tối cá thu kho cà',       'Cà chua',      140,   'g'),
('Bữa tối cá thu kho cà',       'Gạo trắng',    180,   'g'),
('Bữa tối cá thu kho cà',       'Hành lá',        5,   'g'),
('Bữa tối cá thu kho cà',       'Nước mắm',       8,   'ml'),
('Bữa tối cá thu kho cà',       'Đường',          4,   'g'),
('Bữa tối đậu đen trứng rau',   'Đậu đen',      120,   'g'),
('Bữa tối đậu đen trứng rau',   'Trứng gà',       1,   'quả'),
('Bữa tối đậu đen trứng rau',   'Gạo lứt',      160,   'g'),
('Bữa tối đậu đen trứng rau',   'Xà lách',       60,   'g'),
('Bữa tối đậu đen trứng rau',   'Cà chua',       60,   'g')
) AS v(meal_name, ingredient_name, quantity, unit)
JOIN meals m ON m.name = v.meal_name
JOIN ingredients i ON i.name = v.ingredient_name;

-- Ví dụ minh hoạ ràng buộc loại trừ: user demo không ăn đậu phộng.
-- Chỉ loại một món sáng, không làm mất nghiệm lunch/dinner của planner.
INSERT INTO user_excluded_ingredients (user_id, ingredient_id, reason)
SELECT 2, id, 'dislike'
FROM ingredients
WHERE name = 'Đậu phộng';


-- ============================================================
-- Seed Dish Planner V2: dishes + dish_ingredients.
-- ============================================================
INSERT INTO dishes (name, dish_type, cooking_method, description, tags) VALUES
('Cơm trắng',            'staple',         'boil',     'Cơm gạo trắng', '["cơ bản"]'::jsonb),
('Cơm gạo lứt',          'staple',         'boil',     'Cơm gạo lứt', '["healthy"]'::jsonb),
('Thịt kho tàu',         'savory',         'braise',   'Thịt ba chỉ kho trứng nước dừa', '["giàu đạm","đậm đà"]'::jsonb),
('Cá thu kho cà chua',   'savory',         'braise',   'Cá thu kho cà chua', '["giàu đạm"]'::jsonb),
('Gà kho gừng',          'savory',         'braise',   'Đùi gà kho gừng', '["giàu đạm"]'::jsonb),
('Đậu phụ sốt cà chua',  'savory',         'braise',   'Đậu phụ sốt cà chua', '["chay","rẻ"]'::jsonb),
('Tôm rim',              'savory',         'braise',   'Tôm rim mặn ngọt', '["giàu đạm"]'::jsonb),
('Thịt heo kho',         'savory',         'braise',   'Thịt heo nạc kho', '["giàu đạm"]'::jsonb),
('Bò xào hành',          'savory',         'stir_fry', 'Thịt bò xào hành', '["giàu đạm"]'::jsonb),
('Cá rô phi kho',        'savory',         'braise',   'Cá rô phi kho', '["giàu đạm","ít dầu"]'::jsonb),
('Trứng chiên',          'savory',         'stir_fry', 'Trứng gà chiên', '["nhanh","rẻ"]'::jsonb),
('Canh cua rau đay',     'soup',           'soup',     'Canh cua đồng rau đay mồng tơi mướp', '["mát","nhiều rau"]'::jsonb),
('Canh bí đỏ thịt nạc',  'soup',           'soup',     'Canh bí đỏ nấu thịt nạc', '["ngọt","nhiều rau"]'::jsonb),
('Canh cải ngọt',        'soup',           'soup',     'Canh cải ngọt', '["thanh","rẻ"]'::jsonb),
('Canh rau muống',       'soup',           'soup',     'Canh rau muống', '["thanh","rẻ"]'::jsonb),
('Canh mướp mồng tơi',   'soup',           'soup',     'Canh mướp nấu mồng tơi', '["mát","nhiều rau"]'::jsonb),
('Canh bí đỏ',           'soup',           'soup',     'Canh bí đỏ', '["chay","ngọt"]'::jsonb),
('Rau muống xào tỏi',    'vegetable_side', 'stir_fry', 'Rau muống xào tỏi', '["nhiều rau"]'::jsonb),
('Cải ngọt luộc',        'vegetable_side', 'boil',     'Cải ngọt luộc', '["ít dầu","thanh"]'::jsonb),
('Bông cải xào',         'vegetable_side', 'stir_fry', 'Bông cải xanh xào tỏi', '["nhiều rau"]'::jsonb),
('Cà rốt xào',           'vegetable_side', 'stir_fry', 'Cà rốt xào', '["nhiều rau"]'::jsonb),
('Rau đay luộc',         'vegetable_side', 'boil',     'Rau đay luộc', '["ít dầu","thanh"]'::jsonb),
('Mồng tơi xào tỏi',     'vegetable_side', 'stir_fry', 'Mồng tơi xào tỏi', '["nhiều rau"]'::jsonb),
('Xà lách trộn',         'vegetable_side', NULL,       'Xà lách trộn cà chua dưa leo', '["tươi"]'::jsonb),
('Bí đỏ hấp',            'vegetable_side', 'steam',    'Bí đỏ hấp', '["chay","ngọt"]'::jsonb),
('Trứng chiên bánh mì',  'breakfast',      'stir_fry', 'Trứng chiên ăn cùng bánh mì và dưa leo', '["nhanh","rẻ"]'::jsonb),
('Cháo yến mạch chuối',  'breakfast',      'boil',     'Yến mạch nấu sữa, chuối và đậu phộng', '["healthy"]'::jsonb),
('Bún trứng rau cải',    'breakfast',      'boil',     'Bún tươi ăn cùng trứng và cải ngọt', '["nhanh","nhiều rau"]'::jsonb),
('Bánh mì trứng dưa leo','breakfast',      'boil',     'Bánh mì kẹp trứng luộc, dưa leo, xà lách', '["nhanh","rẻ"]'::jsonb),
('Sữa chua yến mạch táo','breakfast',      NULL,       'Sữa chua ăn cùng yến mạch và táo', '["healthy","nhanh"]'::jsonb),
('Khoai lang trứng luộc','breakfast',      'boil',     'Khoai lang, trứng luộc và cam', '["healthy","no lâu"]'::jsonb),
('Nui xào trứng',        'breakfast',      'stir_fry', 'Nui xào trứng, cà rốt và hành lá', '["nhanh","rẻ"]'::jsonb),
('Cơm gạo lứt trứng',    'breakfast',      'stir_fry', 'Cơm gạo lứt ăn cùng trứng và cải ngọt', '["healthy"]'::jsonb);

INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, unit)
SELECT d.id, i.id, v.quantity, v.unit
FROM (VALUES
('Cơm trắng',            'Gạo trắng',     200, 'g'),
('Cơm gạo lứt',          'Gạo lứt',       180, 'g'),
('Thịt kho tàu',         'Thịt ba chỉ',   120, 'g'),
('Thịt kho tàu',         'Trứng gà',        1, 'quả'),
('Thịt kho tàu',         'Nước dừa',      100, 'ml'),
('Thịt kho tàu',         'Nước mắm',       10, 'ml'),
('Thịt kho tàu',         'Đường',           8, 'g'),
('Cá thu kho cà chua',   'Cá thu',        130, 'g'),
('Cá thu kho cà chua',   'Cà chua',       100, 'g'),
('Cá thu kho cà chua',   'Nước mắm',        8, 'ml'),
('Cá thu kho cà chua',   'Đường',           4, 'g'),
('Cá thu kho cà chua',   'Hành lá',         5, 'g'),
('Gà kho gừng',          'Đùi gà',        150, 'g'),
('Gà kho gừng',          'Gừng',            8, 'g'),
('Gà kho gừng',          'Nước mắm',       10, 'ml'),
('Gà kho gừng',          'Đường',           5, 'g'),
('Gà kho gừng',          'Tỏi',             5, 'g'),
('Đậu phụ sốt cà chua',  'Đậu phụ',       180, 'g'),
('Đậu phụ sốt cà chua',  'Cà chua',       120, 'g'),
('Đậu phụ sốt cà chua',  'Hành lá',         8, 'g'),
('Đậu phụ sốt cà chua',  'Dầu ăn',          6, 'ml'),
('Tôm rim',              'Tôm',           130, 'g'),
('Tôm rim',              'Tỏi',             5, 'g'),
('Tôm rim',              'Nước mắm',        6, 'ml'),
('Tôm rim',              'Đường',           4, 'g'),
('Thịt heo kho',         'Thịt heo nạc',  130, 'g'),
('Thịt heo kho',         'Nước mắm',        8, 'ml'),
('Thịt heo kho',         'Đường',           5, 'g'),
('Thịt heo kho',         'Hành lá',         5, 'g'),
('Bò xào hành',          'Thịt bò',       120, 'g'),
('Bò xào hành',          'Hành lá',        10, 'g'),
('Bò xào hành',          'Tỏi',             5, 'g'),
('Bò xào hành',          'Dầu ăn',          6, 'ml'),
('Cá rô phi kho',        'Cá rô phi',     150, 'g'),
('Cá rô phi kho',        'Nước mắm',        8, 'ml'),
('Cá rô phi kho',        'Đường',           4, 'g'),
('Cá rô phi kho',        'Hành lá',         5, 'g'),
('Trứng chiên',          'Trứng gà',        2, 'quả'),
('Trứng chiên',          'Dầu ăn',          5, 'ml'),
('Trứng chiên',          'Hành lá',         5, 'g'),
('Canh cua rau đay',     'Cua đồng',      100, 'g'),
('Canh cua rau đay',     'Rau đay',        80, 'g'),
('Canh cua rau đay',     'Mồng tơi',       40, 'g'),
('Canh cua rau đay',     'Mướp',           60, 'g'),
('Canh bí đỏ thịt nạc',  'Thịt heo nạc',   60, 'g'),
('Canh bí đỏ thịt nạc',  'Bí đỏ',         150, 'g'),
('Canh bí đỏ thịt nạc',  'Hành lá',         5, 'g'),
('Canh cải ngọt',        'Cải ngọt',      100, 'g'),
('Canh cải ngọt',        'Nước mắm',        5, 'ml'),
('Canh cải ngọt',        'Hành lá',         5, 'g'),
('Canh rau muống',       'Rau muống',     100, 'g'),
('Canh rau muống',       'Tỏi',             3, 'g'),
('Canh mướp mồng tơi',   'Mướp',          100, 'g'),
('Canh mướp mồng tơi',   'Mồng tơi',       60, 'g'),
('Canh bí đỏ',           'Bí đỏ',         150, 'g'),
('Canh bí đỏ',           'Hành lá',         5, 'g'),
('Rau muống xào tỏi',    'Rau muống',     120, 'g'),
('Rau muống xào tỏi',    'Tỏi',             5, 'g'),
('Rau muống xào tỏi',    'Dầu ăn',          6, 'ml'),
('Cải ngọt luộc',        'Cải ngọt',      120, 'g'),
('Bông cải xào',         'Bông cải xanh', 120, 'g'),
('Bông cải xào',         'Tỏi',             5, 'g'),
('Bông cải xào',         'Dầu ăn',          6, 'ml'),
('Cà rốt xào',           'Cà rốt',        100, 'g'),
('Cà rốt xào',           'Dầu ăn',          5, 'ml'),
('Rau đay luộc',         'Rau đay',       100, 'g'),
('Mồng tơi xào tỏi',     'Mồng tơi',      120, 'g'),
('Mồng tơi xào tỏi',     'Tỏi',             5, 'g'),
('Mồng tơi xào tỏi',     'Dầu ăn',          6, 'ml'),
('Xà lách trộn',         'Xà lách',        80, 'g'),
('Xà lách trộn',         'Cà chua',        50, 'g'),
('Xà lách trộn',         'Dưa leo',        50, 'g'),
('Bí đỏ hấp',            'Bí đỏ',         150, 'g'),
('Trứng chiên bánh mì',  'Trứng gà',        2, 'quả'),
('Trứng chiên bánh mì',  'Bánh mì',        80, 'g'),
('Trứng chiên bánh mì',  'Dưa leo',        50, 'g'),
('Trứng chiên bánh mì',  'Dầu ăn',          5, 'ml'),
('Trứng chiên bánh mì',  'Hành lá',         5, 'g'),
('Cháo yến mạch chuối',  'Yến mạch',       60, 'g'),
('Cháo yến mạch chuối',  'Sữa tươi',      200, 'ml'),
('Cháo yến mạch chuối',  'Chuối',         100, 'g'),
('Cháo yến mạch chuối',  'Đậu phộng',      10, 'g'),
('Bún trứng rau cải',    'Bún tươi',      180, 'g'),
('Bún trứng rau cải',    'Trứng gà',        1, 'quả'),
('Bún trứng rau cải',    'Cải ngọt',       80, 'g'),
('Bún trứng rau cải',    'Hành lá',         5, 'g'),
('Bún trứng rau cải',    'Nước mắm',        5, 'ml'),
('Bánh mì trứng dưa leo','Bánh mì',       100, 'g'),
('Bánh mì trứng dưa leo','Trứng gà',        1, 'quả'),
('Bánh mì trứng dưa leo','Dưa leo',        70, 'g'),
('Bánh mì trứng dưa leo','Xà lách',        30, 'g'),
('Sữa chua yến mạch táo','Sữa chua',        1, 'hộp'),
('Sữa chua yến mạch táo','Yến mạch',       40, 'g'),
('Sữa chua yến mạch táo','Táo',           120, 'g'),
('Khoai lang trứng luộc','Khoai lang',    220, 'g'),
('Khoai lang trứng luộc','Trứng gà',        2, 'quả'),
('Khoai lang trứng luộc','Cam',           100, 'g'),
('Nui xào trứng',        'Nui',           150, 'g'),
('Nui xào trứng',        'Trứng gà',        1, 'quả'),
('Nui xào trứng',        'Cà rốt',         50, 'g'),
('Nui xào trứng',        'Dầu ăn',          5, 'ml'),
('Nui xào trứng',        'Hành lá',         5, 'g'),
('Cơm gạo lứt trứng',    'Gạo lứt',       180, 'g'),
('Cơm gạo lứt trứng',    'Trứng gà',        1, 'quả'),
('Cơm gạo lứt trứng',    'Cải ngọt',       70, 'g'),
('Cơm gạo lứt trứng',    'Dầu ăn',          4, 'ml')
) AS v(dish_name, ingredient_name, quantity, unit)
JOIN dishes d ON d.name = v.dish_name
JOIN ingredients i ON i.name = v.ingredient_name;

-- Danh mục thẻ chuẩn tiếng Việt. Dữ liệu demo cũ dùng "healthy" được đổi
-- ngay khi khởi tạo để không tạo thêm giá trị tiếng Anh trong DB mới.
UPDATE meals SET tags = replace(tags::text, '"healthy"', '"lành mạnh"')::jsonb
WHERE tags::text LIKE '%"healthy"%';
UPDATE dishes SET tags = replace(tags::text, '"healthy"', '"lành mạnh"')::jsonb
WHERE tags::text LIKE '%"healthy"%';

CREATE TABLE tag_catalog (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO tag_catalog (name)
SELECT DISTINCT tag FROM (
    SELECT jsonb_array_elements_text(tags) AS tag FROM meals
    UNION SELECT jsonb_array_elements_text(tags) AS tag FROM dishes
) AS all_tags
WHERE btrim(tag) <> '';

COMMIT;
