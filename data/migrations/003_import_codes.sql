BEGIN;

ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS code VARCHAR(64);
ALTER TABLE dishes ADD COLUMN IF NOT EXISTS code VARCHAR(64);
ALTER TABLE import_jobs ADD COLUMN IF NOT EXISTS conflicts JSONB NOT NULL DEFAULT '[]'::jsonb;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_ingredients_code') THEN
        ALTER TABLE ingredients ADD CONSTRAINT uq_ingredients_code UNIQUE (code);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dishes_code') THEN
        ALTER TABLE dishes ADD CONSTRAINT uq_dishes_code UNIQUE (code);
    END IF;
END $$;

COMMIT;
