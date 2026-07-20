BEGIN;

DO $$
BEGIN
    CREATE TYPE ingredient_purchase_mode AS ENUM ('regular', 'pantry', 'ignored');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE ingredients
    ADD COLUMN IF NOT EXISTS purchase_mode ingredient_purchase_mode NOT NULL DEFAULT 'regular',
    ADD COLUMN IF NOT EXISTS purchase_increment NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS room_shelf_life_days SMALLINT,
    ADD COLUMN IF NOT EXISTS fridge_shelf_life_days SMALLINT,
    ADD COLUMN IF NOT EXISTS freezer_shelf_life_days SMALLINT,
    ADD COLUMN IF NOT EXISTS shelf_life_source VARCHAR(255),
    ADD COLUMN IF NOT EXISTS shelf_life_reviewed_at DATE;

ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS ck_ingredient_purchase_increment;
ALTER TABLE ingredients ADD CONSTRAINT ck_ingredient_purchase_increment
    CHECK (purchase_increment IS NULL OR purchase_increment > 0);
ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS ck_ingredient_room_shelf_life;
ALTER TABLE ingredients ADD CONSTRAINT ck_ingredient_room_shelf_life
    CHECK (room_shelf_life_days IS NULL OR room_shelf_life_days BETWEEN 0 AND 3650);
ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS ck_ingredient_fridge_shelf_life;
ALTER TABLE ingredients ADD CONSTRAINT ck_ingredient_fridge_shelf_life
    CHECK (fridge_shelf_life_days IS NULL OR fridge_shelf_life_days BETWEEN 0 AND 3650);
ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS ck_ingredient_freezer_shelf_life;
ALTER TABLE ingredients ADD CONSTRAINT ck_ingredient_freezer_shelf_life
    CHECK (freezer_shelf_life_days IS NULL OR freezer_shelf_life_days BETWEEN 0 AND 3650);
ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS ck_ingredient_procurement_fields;
ALTER TABLE ingredients ADD CONSTRAINT ck_ingredient_procurement_fields CHECK (
    purchase_mode = 'regular'
    OR (
        purchase_increment IS NULL
        AND room_shelf_life_days IS NULL
        AND fridge_shelf_life_days IS NULL
        AND freezer_shelf_life_days IS NULL
        AND shelf_life_source IS NULL
        AND shelf_life_reviewed_at IS NULL
    )
);
ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS ck_ingredient_shelf_life_provenance;
ALTER TABLE ingredients ADD CONSTRAINT ck_ingredient_shelf_life_provenance CHECK (
    (
        room_shelf_life_days IS NULL
        AND fridge_shelf_life_days IS NULL
        AND freezer_shelf_life_days IS NULL
    )
    OR (NULLIF(BTRIM(shelf_life_source), '') IS NOT NULL AND shelf_life_reviewed_at IS NOT NULL)
);

ALTER TABLE dish_ingredients
    ADD COLUMN IF NOT EXISTS max_extra_quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS extra_step_quantity NUMERIC(10,2);
ALTER TABLE dish_ingredients DROP CONSTRAINT IF EXISTS ck_dish_ingredient_max_extra;
ALTER TABLE dish_ingredients ADD CONSTRAINT ck_dish_ingredient_max_extra
    CHECK (max_extra_quantity >= 0);
ALTER TABLE dish_ingredients DROP CONSTRAINT IF EXISTS ck_dish_ingredient_flex;
ALTER TABLE dish_ingredients ADD CONSTRAINT ck_dish_ingredient_flex CHECK (
    (max_extra_quantity = 0 AND extra_step_quantity IS NULL)
    OR (
        max_extra_quantity > 0
        AND extra_step_quantity > 0
        AND extra_step_quantity <= max_extra_quantity
        AND MOD(max_extra_quantity, extra_step_quantity) = 0
    )
);

ALTER TABLE shopping_lists
    ADD COLUMN IF NOT EXISTS item_key VARCHAR(160),
    ADD COLUMN IF NOT EXISTS item_kind VARCHAR(20) NOT NULL DEFAULT 'legacy',
    ADD COLUMN IF NOT EXISTS scheduled_day SMALLINT;
UPDATE shopping_lists
SET item_key = 'legacy:' || ingredient_id::text || ':' || unit
WHERE item_key IS NULL;
ALTER TABLE shopping_lists ALTER COLUMN item_key SET NOT NULL;
ALTER TABLE shopping_lists DROP CONSTRAINT IF EXISTS shopping_lists_meal_plan_id_ingredient_id_key;
ALTER TABLE shopping_lists DROP CONSTRAINT IF EXISTS ck_shopping_list_item_kind;
ALTER TABLE shopping_lists ADD CONSTRAINT ck_shopping_list_item_kind
    CHECK (item_kind IN ('legacy', 'purchase', 'pantry'));
ALTER TABLE shopping_lists DROP CONSTRAINT IF EXISTS ck_shopping_list_scheduled_day;
ALTER TABLE shopping_lists ADD CONSTRAINT ck_shopping_list_scheduled_day
    CHECK (scheduled_day IS NULL OR scheduled_day BETWEEN 1 AND 7);
CREATE UNIQUE INDEX IF NOT EXISTS uq_shopping_list_plan_item_key
    ON shopping_lists(meal_plan_id, item_key);

DROP VIEW IF EXISTS v_dish_candidates;
DROP VIEW IF EXISTS v_dishes_full;
DROP VIEW IF EXISTS v_ingredients_full;

CREATE VIEW v_ingredients_full AS
SELECT
    i.id, i.name, i.food_group, i.default_unit, i.grams_per_unit,
    i.purchase_mode, i.purchase_increment,
    i.room_shelf_life_days, i.fridge_shelf_life_days, i.freezer_shelf_life_days,
    i.shelf_life_source, i.shelf_life_reviewed_at, i.is_active,
    n.calories, n.protein_g, n.carbs_g, n.fat_g, n.fiber_g,
    p.price AS latest_price, p.unit AS price_unit,
    p.price_per_default_unit AS latest_price_per_unit,
    p.recorded_at AS price_recorded_at
FROM ingredients i
LEFT JOIN nutrition_facts n ON n.ingredient_id = i.id
LEFT JOIN LATERAL (
    SELECT price, unit, price_per_default_unit, recorded_at
    FROM price_snapshots ps
    WHERE ps.ingredient_id = i.id
    ORDER BY ps.recorded_at DESC
    LIMIT 1
) p ON TRUE;

CREATE VIEW v_dishes_full AS
SELECT
    d.id, d.name, d.dish_type, d.cooking_method, d.tags, d.is_active,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.calories  / 100.0), 0) AS total_calories,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.protein_g / 100.0), 0) AS total_protein_g,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.carbs_g   / 100.0), 0) AS total_carbs_g,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.fat_g     / 100.0), 0) AS total_fat_g,
    COALESCE(SUM(CASE WHEN i.purchase_mode = 'regular'
        THEN di.quantity * lp.price_per_default_unit ELSE 0 END), 0) AS estimated_cost,
    COUNT(di.id) AS ingredient_count,
    COUNT(nf.ingredient_id) AS nutrition_count,
    COUNT(lp.price_per_default_unit) FILTER (WHERE i.purchase_mode = 'regular') AS priced_ingredient_count,
    COUNT(di.id) > 0 AND COUNT(nf.ingredient_id) = COUNT(di.id) AS has_complete_nutrition,
    COUNT(di.id) > 0 AND BOOL_AND(
        i.purchase_mode <> 'regular' OR lp.price_per_default_unit IS NOT NULL
    ) AS has_complete_price,
    COUNT(di.id) > 0 AND BOOL_AND(
        i.purchase_mode <> 'regular'
        OR (i.purchase_increment IS NOT NULL AND lp.price_per_default_unit IS NOT NULL)
    ) AS has_complete_procurement,
    COUNT(di.id) > 0 AND COALESCE(BOOL_AND(i.is_active), FALSE) AS all_ingredients_active,
    COALESCE(JSONB_AGG(di.ingredient_id ORDER BY di.id)
        FILTER (WHERE di.id IS NOT NULL), '[]'::jsonb) AS ingredient_ids,
    COALESCE(JSONB_AGG(JSONB_BUILD_OBJECT(
        'ingredient_id', i.id,
        'name', i.name,
        'quantity', di.quantity,
        'unit', di.unit,
        'estimated_cost', CASE WHEN i.purchase_mode = 'regular'
            THEN COALESCE(di.quantity * lp.price_per_default_unit, 0) ELSE 0 END,
        'purchase_mode', i.purchase_mode,
        'purchase_increment', i.purchase_increment,
        'price_per_default_unit', lp.price_per_default_unit,
        'price_source', lp.source,
        'price_recorded_at', lp.recorded_at,
        'grams_per_unit', i.grams_per_unit,
        'calories_per_100g', nf.calories,
        'protein_g_per_100g', nf.protein_g,
        'carbs_g_per_100g', nf.carbs_g,
        'fat_g_per_100g', nf.fat_g,
        'room_shelf_life_days', i.room_shelf_life_days,
        'fridge_shelf_life_days', i.fridge_shelf_life_days,
        'freezer_shelf_life_days', i.freezer_shelf_life_days,
        'max_extra_quantity', di.max_extra_quantity,
        'extra_step_quantity', di.extra_step_quantity
    ) ORDER BY di.id) FILTER (WHERE di.id IS NOT NULL), '[]'::jsonb) AS ingredients
FROM dishes d
LEFT JOIN dish_ingredients di ON di.dish_id = d.id
LEFT JOIN ingredients i ON i.id = di.ingredient_id
LEFT JOIN nutrition_facts nf ON nf.ingredient_id = di.ingredient_id
LEFT JOIN LATERAL (
    SELECT price_per_default_unit, source, recorded_at
    FROM price_snapshots ps
    WHERE ps.ingredient_id = di.ingredient_id
    ORDER BY ps.recorded_at DESC
    LIMIT 1
) lp ON TRUE
GROUP BY d.id;

CREATE VIEW v_dish_candidates AS
SELECT
    id, name, dish_type, cooking_method, tags,
    total_calories, total_protein_g, total_carbs_g, total_fat_g, estimated_cost,
    ingredient_count, nutrition_count, priced_ingredient_count,
    all_ingredients_active, has_complete_nutrition, has_complete_price,
    has_complete_procurement, ingredient_ids, ingredients
FROM v_dishes_full
WHERE is_active = TRUE
  AND ingredient_count > 0
  AND all_ingredients_active = TRUE
  AND has_complete_nutrition = TRUE
  AND has_complete_price = TRUE
  AND total_calories > 0;

COMMIT;
