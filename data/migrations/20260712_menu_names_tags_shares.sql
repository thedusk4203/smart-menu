-- Menu names, Vietnamese tag catalogue and public shopping-list sharing.
BEGIN;

ALTER TABLE meal_plans ALTER COLUMN name SET DEFAULT 'Thực đơn';

UPDATE meals
SET tags = replace(tags::text, '"healthy"', '"lành mạnh"')::jsonb
WHERE tags::text LIKE '%"healthy"%';

UPDATE dishes
SET tags = replace(tags::text, '"healthy"', '"lành mạnh"')::jsonb
WHERE tags::text LIKE '%"healthy"%';

UPDATE meal_plans
SET plan_data = replace(plan_data::text, '"healthy"', '"lành mạnh"')::jsonb,
    name = CASE
      WHEN name IN ('Thực đơn tuần', 'Thực đơn của tôi')
      THEN 'Thực đơn ' || to_char(created_at AT TIME ZONE 'Asia/Ho_Chi_Minh', 'HH24:MI DD/MM/YYYY')
      ELSE name
    END;

CREATE TABLE IF NOT EXISTS tag_catalog (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tag_catalog_name UNIQUE (name)
);

INSERT INTO tag_catalog (name)
SELECT DISTINCT tag
FROM (
  SELECT jsonb_array_elements_text(tags) AS tag FROM meals
  UNION
  SELECT jsonb_array_elements_text(tags) AS tag FROM dishes
) tags
WHERE btrim(tag) <> ''
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS shopping_list_shares (
    id UUID PRIMARY KEY,
    meal_plan_id INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_shopping_list_share
    ON shopping_list_shares(meal_plan_id) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_shopping_list_shares_expiry ON shopping_list_shares(expires_at);

COMMIT;
