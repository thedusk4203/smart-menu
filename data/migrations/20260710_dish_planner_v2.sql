-- Dish Planner V2: chạy một lần trên database đã được tạo từ seed Phase A.
-- Giữ meal_plans/plan_data để UI vẫn đọc được schema_version=1; chỉ gỡ model
-- Meal Set và dựng lại candidate view ở cấp dish.
BEGIN;

DROP VIEW IF EXISTS v_meal_candidates;
DROP VIEW IF EXISTS v_meal_sets_full;
DROP VIEW IF EXISTS v_dishes_full;
DROP TABLE IF EXISTS meal_set_dishes;
DROP TABLE IF EXISTS meal_sets;
DROP TYPE IF EXISTS dish_role;

CREATE VIEW v_dishes_full AS
SELECT
    d.id, d.name, d.dish_type, d.cooking_method, d.tags, d.is_active,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.calories  / 100.0), 0) AS total_calories,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.protein_g / 100.0), 0) AS total_protein_g,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.carbs_g   / 100.0), 0) AS total_carbs_g,
    COALESCE(SUM(di.quantity * i.grams_per_unit * nf.fat_g     / 100.0), 0) AS total_fat_g,
    COALESCE(SUM(di.quantity * lp.price_per_default_unit), 0) AS estimated_cost,
    COUNT(di.id) AS ingredient_count,
    COUNT(nf.ingredient_id) AS nutrition_count,
    COUNT(lp.price_per_default_unit) AS priced_ingredient_count,
    COUNT(di.id) > 0 AND COUNT(nf.ingredient_id) = COUNT(di.id) AS has_complete_nutrition,
    COUNT(di.id) > 0 AND COUNT(lp.price_per_default_unit) = COUNT(di.id) AS has_complete_price,
    COUNT(di.id) > 0 AND COALESCE(BOOL_AND(i.is_active), FALSE) AS all_ingredients_active,
    COALESCE(JSONB_AGG(di.ingredient_id ORDER BY di.id) FILTER (WHERE di.id IS NOT NULL), '[]'::jsonb) AS ingredient_ids,
    COALESCE(JSONB_AGG(JSONB_BUILD_OBJECT(
        'ingredient_id', i.id, 'name', i.name, 'quantity', di.quantity, 'unit', di.unit,
        'estimated_cost', COALESCE(di.quantity * lp.price_per_default_unit, 0)
    ) ORDER BY di.id) FILTER (WHERE di.id IS NOT NULL), '[]'::jsonb) AS ingredients
FROM dishes d
LEFT JOIN dish_ingredients di ON di.dish_id = d.id
LEFT JOIN ingredients i ON i.id = di.ingredient_id
LEFT JOIN nutrition_facts nf ON nf.ingredient_id = di.ingredient_id
LEFT JOIN LATERAL (
    SELECT price_per_default_unit FROM price_snapshots ps
    WHERE ps.ingredient_id = di.ingredient_id ORDER BY ps.recorded_at DESC LIMIT 1
) lp ON TRUE
GROUP BY d.id;

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

COMMIT;
