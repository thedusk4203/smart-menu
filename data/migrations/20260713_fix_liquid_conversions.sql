-- Chuẩn hóa hệ số gram/ml còn giữ giá trị mặc định sau khi import catalog.
-- Theo quy ước dữ liệu demo đã ghi trong init_db.sql:
--   dầu ăn ~0,92 g/ml; sữa và sản phẩm sữa lỏng ~1,03 g/ml.
-- Chỉ sửa giá trị đúng bằng 1 để không ghi đè dữ liệu đã được biên tập.
BEGIN;

UPDATE ingredients
SET grams_per_unit = 0.92
WHERE LOWER(BTRIM(default_unit)) IN ('ml', 'milliliter', 'milliliters')
  AND food_group::text = 'fat'
  AND grams_per_unit = 1;

UPDATE ingredients
SET grams_per_unit = 1.03
WHERE LOWER(BTRIM(default_unit)) IN ('ml', 'milliliter', 'milliliters')
  AND food_group::text = 'dairy'
  AND grams_per_unit = 1;

COMMIT;
