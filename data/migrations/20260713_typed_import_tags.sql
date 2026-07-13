BEGIN;

ALTER TABLE ingredients
    ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE tag_catalog
    ADD COLUMN IF NOT EXISTS entity_type VARCHAR(20);

UPDATE tag_catalog SET entity_type = 'dish' WHERE entity_type IS NULL;

ALTER TABLE tag_catalog
    ALTER COLUMN entity_type SET DEFAULT 'dish',
    ALTER COLUMN entity_type SET NOT NULL;

ALTER TABLE tag_catalog DROP CONSTRAINT IF EXISTS uq_tag_catalog_name;
ALTER TABLE tag_catalog DROP CONSTRAINT IF EXISTS tag_catalog_name_key;
ALTER TABLE tag_catalog DROP CONSTRAINT IF EXISTS ck_tag_catalog_entity_type;
ALTER TABLE tag_catalog DROP CONSTRAINT IF EXISTS uq_tag_catalog_type_name;

ALTER TABLE tag_catalog
    ADD CONSTRAINT ck_tag_catalog_entity_type
        CHECK (entity_type IN ('ingredient', 'dish')),
    ADD CONSTRAINT uq_tag_catalog_type_name
        UNIQUE (entity_type, name);

CREATE INDEX IF NOT EXISTS idx_tag_catalog_type_active_name
    ON tag_catalog (entity_type, is_active, name);
CREATE UNIQUE INDEX IF NOT EXISTS uq_tag_catalog_type_normalized_name
    ON tag_catalog (entity_type, LOWER(BTRIM(name)));
CREATE INDEX IF NOT EXISTS idx_ingredients_tags
    ON ingredients USING GIN (tags);

INSERT INTO tag_catalog (entity_type, name)
SELECT 'dish', tag
FROM (
    SELECT jsonb_array_elements_text(tags) AS tag FROM meals
    UNION
    SELECT jsonb_array_elements_text(tags) AS tag FROM dishes
) source
WHERE btrim(tag) <> ''
ON CONFLICT (entity_type, name) DO UPDATE SET is_active = TRUE, updated_at = NOW();

INSERT INTO tag_catalog (entity_type, name)
SELECT 'ingredient', tag
FROM (
    SELECT DISTINCT jsonb_array_elements_text(tags) AS tag FROM ingredients
) source
WHERE btrim(tag) <> ''
ON CONFLICT (entity_type, name) DO NOTHING;

COMMIT;
