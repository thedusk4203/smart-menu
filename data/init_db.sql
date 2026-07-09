BEGIN;

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

CREATE TYPE user_role AS ENUM ('user', 'admin');

CREATE TYPE gender AS ENUM ('male', 'female');

CREATE TYPE activity_level AS ENUM (
    'sedentary',    
    'light',       
    'moderate',      
    'active'        
);

CREATE TYPE physical_goal AS ENUM (
    'maintain',           
    'lose_weight',         
    'gain_muscle',        
    'gain_weight'          
);

CREATE TYPE meal_type AS ENUM (
    'breakfast',           
    'lunch',             
    'dinner'              
);

CREATE TYPE cooking_method AS ENUM (
    'stir_fry',           
    'boil',               
    'soup',              
    'braise',           
);

CREATE TYPE food_group AS ENUM (
    'protein',            
    'vegetable',           
    'grain',              
    'dairy',               
    'fat',                 
    'fruit',               
    'other'                
);
CREATE TYPE exclusion_reason AS ENUM (
    'allergy',             
    'dislike'              
);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE users (
    id              SERIAL          PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    hashed_password VARCHAR(255)    NOT NULL,
    role            user_role       NOT NULL DEFAULT 'user',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE users IS 'TÃ i khoáº£n Ä‘Äƒng nháº­p, phÃ¢n quyá»n user/admin';

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

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
    meals_per_day   SMALLINT        NOT NULL DEFAULT 3 CHECK (meals_per_day BETWEEN 1 AND 5),
    daily_calorie_target  NUMERIC(7,1) CHECK (daily_calorie_target IS NULL OR daily_calorie_target > 0),
    daily_budget    NUMERIC(12,2)   CHECK (daily_budget IS NULL OR daily_budget >= 0),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE user_profiles IS 'ThÃ´ng tin thá»ƒ tráº¡ng, má»¥c tiÃªu, sá»‘ bá»¯a/ngÃ y vÃ  ngÃ¢n sÃ¡ch (theo ngÃ y) cá»§a ngÆ°á»i dÃ¹ng';

CREATE TRIGGER trg_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE ingredients (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL UNIQUE,
    food_group      food_group      NOT NULL,
    default_unit    VARCHAR(20)     NOT NULL DEFAULT 'g',  
    grams_per_unit  NUMERIC(10,4)   NOT NULL DEFAULT 1 CHECK (grams_per_unit > 0),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE ingredients IS 'Danh má»¥c nguyÃªn liá»‡u náº¥u Äƒn; grams_per_unit Ä‘á»ƒ quy Ä‘á»•i vá» gram cho tÃ­nh dinh dÆ°á»¡ng';

CREATE TRIGGER trg_ingredients_updated_at
    BEFORE UPDATE ON ingredients
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

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
COMMENT ON TABLE nutrition_facts IS 'ThÃ nh pháº§n dinh dÆ°á»¡ng trÃªn 100g nguyÃªn liá»‡u';

CREATE TABLE price_snapshots (
    id              SERIAL          PRIMARY KEY,
    ingredient_id   INTEGER         NOT NULL
                                    REFERENCES ingredients(id) ON DELETE CASCADE,
    price           NUMERIC(12,2)   NOT NULL CHECK (price >= 0),
    unit            VARCHAR(20)     NOT NULL DEFAULT 'kg',
    price_per_default_unit NUMERIC(14,4) CHECK (price_per_default_unit IS NULL OR price_per_default_unit >= 0),
    source          VARCHAR(255),                                 
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE price_snapshots IS 'CÃ¡c má»‘c giÃ¡ nguyÃªn liá»‡u theo thá»i gian; price_per_default_unit lÃ  giÃ¡ Ä‘Ã£ quy vá» Ä‘Æ¡n vá»‹ chuáº©n';

CREATE INDEX idx_price_ingredient_time
    ON price_snapshots (ingredient_id, recorded_at DESC);
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
COMMENT ON TABLE user_excluded_ingredients IS 'Danh sÃ¡ch nguyÃªn liá»‡u dá»‹ á»©ng/khÃ´ng Äƒn cá»§a tá»«ng user; planner loáº¡i má»i mÃ³n chá»©a cÃ¡c nguyÃªn liá»‡u nÃ y';

CREATE INDEX idx_excluded_user ON user_excluded_ingredients (user_id);

CREATE TABLE meals (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL,
    meal_type       meal_type       NOT NULL,
    cooking_method  cooking_method,
    description     TEXT,
    instructions    TEXT,
    servings        INTEGER         NOT NULL DEFAULT 1 CHECK (servings > 0),
    tags            JSONB           NOT NULL DEFAULT '[]'::jsonb,   
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE meals IS 'MÃ³n Äƒn, kÃ¨m nhÃ£n (tags) dáº¡ng JSONB Ä‘á»ƒ lá»c linh hoáº¡t';

CREATE INDEX idx_meals_tags ON meals USING GIN (tags);

CREATE TRIGGER trg_meals_updated_at
    BEFORE UPDATE ON meals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE meal_ingredients (
    id              SERIAL          PRIMARY KEY,
    meal_id         INTEGER         NOT NULL
                                    REFERENCES meals(id) ON DELETE CASCADE,
    ingredient_id   INTEGER         NOT NULL
                                    REFERENCES ingredients(id) ON DELETE RESTRICT,
    quantity        NUMERIC(10,2)   NOT NULL CHECK (quantity > 0),
    unit            VARCHAR(20)     NOT NULL DEFAULT 'g',
    UNIQUE (meal_id, ingredient_id)
);
COMMENT ON TABLE meal_ingredients IS 'Äá»‹nh lÆ°á»£ng nguyÃªn liá»‡u trong má»—i mÃ³n Äƒn (theo default_unit cá»§a nguyÃªn liá»‡u)';
CREATE INDEX idx_meal_ingredients_ingredient ON meal_ingredients (ingredient_id);

CREATE TABLE meal_plans (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL
                                    REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255)    NOT NULL DEFAULT 'Thá»±c Ä‘Æ¡n tuáº§n',
    start_date      DATE            NOT NULL,
    end_date        DATE,
    budget_limit    NUMERIC(12,2)   CHECK (budget_limit IS NULL OR budget_limit >= 0),  
    total_cost      NUMERIC(12,2)   NOT NULL DEFAULT 0 CHECK (total_cost >= 0),
    total_calories  NUMERIC(9,2)    NOT NULL DEFAULT 0 CHECK (total_calories >= 0),
    plan_data       JSONB           NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CHECK (end_date IS NULL OR end_date >= start_date)
);
COMMENT ON TABLE meal_plans IS 'Káº¿ hoáº¡ch thá»±c Ä‘Æ¡n cá»§a ngÆ°á»i dÃ¹ng; chi tiáº¿t lá»‹ch mÃ³n lÆ°u trong plan_data (JSONB); budget_limit theo tuáº§n';

CREATE INDEX idx_meal_plans_user ON meal_plans (user_id);
CREATE INDEX idx_meal_plans_data ON meal_plans USING GIN (plan_data);

CREATE TRIGGER trg_meal_plans_updated_at
    BEFORE UPDATE ON meal_plans
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

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
COMMENT ON TABLE shopping_lists IS 'Tá»•ng há»£p nguyÃªn liá»‡u cáº§n mua cho má»™t thá»±c Ä‘Æ¡n';
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
    p.price                  AS latest_price,            
    p.unit                   AS price_unit,
    p.price_per_default_unit AS latest_price_per_unit,   
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
COMMENT ON VIEW v_ingredients_full IS 'NguyÃªn liá»‡u kÃ¨m dinh dÆ°á»¡ng vÃ  giÃ¡ má»›i nháº¥t (gá»‘c + Ä‘Ã£ chuáº©n hoÃ¡)';
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
COMMENT ON VIEW v_meals_full IS 'MÃ³n Äƒn kÃ¨m tá»•ng dinh dÆ°á»¡ng (quy vá» gram) vÃ  chi phÃ­ Æ°á»›c tÃ­nh tá»« giÃ¡ má»›i nháº¥t';
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
COMMENT ON VIEW v_meal_plan_summary IS 'TÃ³m táº¯t thá»±c Ä‘Æ¡n + cá» vÆ°á»£t ngÃ¢n sÃ¡ch';

INSERT INTO users (email, hashed_password, role) VALUES
('admin@demo.com', '$2b$12$4hzAQtCbT.JRoxgOrmaDoObP3brV5B9VUWQaOBOTuo0po1nAFs09C', 'admin'),
('user@demo.com',  '$2b$12$4Na3jWlR4iZCJrESe6U2ceUn8LM/GHnG8V8mFw3S3/.M5Q2TUq8cW', 'user');

INSERT INTO user_profiles (user_id, full_name, gender, age, height_cm, weight_kg, activity_level, goal, meals_per_day, daily_calorie_target, daily_budget)
VALUES
(2, 'NgÆ°á»i dÃ¹ng Demo', 'male', 22, 170.0, 65.0, 'moderate', 'gain_muscle', 3, 2400, 80000);
INSERT INTO ingredients (name, food_group, default_unit, grams_per_unit) VALUES
('á»¨c gÃ ',        'protein',   'g',   1),
('Gáº¡o tráº¯ng',    'grain',     'g',   1),
('Cáº£i ngá»t',     'vegetable', 'g',   1),
('Trá»©ng gÃ ',     'protein',   'quáº£', 55),
('Dáº§u Äƒn',       'fat',       'ml',  0.92);

INSERT INTO nutrition_facts (ingredient_id, calories, protein_g, carbs_g, fat_g, fiber_g) VALUES
(1, 165, 31.0, 0.0,  3.6, 0.0),   
(2, 130, 2.7,  28.0, 0.3, 0.4),   
(3, 13,  1.5,  2.2,  0.2, 1.2), 
(4, 155, 13.0, 1.1,  11.0,0.0),   
(5, 884, 0.0,  0.0,  100.0,0.0);  
INSERT INTO price_snapshots (ingredient_id, price, unit, price_per_default_unit, source) VALUES
(1, 90000, 'kg',   90,   'Chá»£ Nam Äá»‹nh'),
(2, 22000, 'kg',   22,   'SiÃªu thá»‹'),
(3, 15000, 'kg',   15,   'Chá»£ Nam Äá»‹nh'),
(4, 35000, 'chá»¥c', 3500, 'SiÃªu thá»‹'),
(5, 45000, 'lÃ­t',  45,   'SiÃªu thá»‹');

INSERT INTO meals (name, meal_type, cooking_method, description, servings, tags) VALUES
('CÆ¡m á»©c gÃ  luá»™c rau', 'lunch', 'boil', 'á»¨c gÃ  luá»™c Äƒn kÃ¨m cÆ¡m vÃ  cáº£i ngá»t', 1, '["healthy","Ã­t dáº§u","tÄƒng cÆ¡"]'::jsonb),
('Trá»©ng chiÃªn',        'breakfast', 'stir_fry', 'Trá»©ng gÃ  chiÃªn dáº§u', 1, '["nhanh","ráº»"]'::jsonb);

INSERT INTO meal_ingredients (meal_id, ingredient_id, quantity, unit) VALUES
(1, 1, 150, 'g'),
(1, 2, 200, 'g'),
(1, 3, 100, 'g'),
(2, 4, 2,   'quáº£'),
(2, 5, 10,  'ml');
INSERT INTO user_excluded_ingredients (user_id, ingredient_id, reason) VALUES
(2, 5, 'dislike');

COMMIT;


