BEGIN;

ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'data_editor';
ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'super_admin';

ALTER TABLE dishes ADD COLUMN IF NOT EXISTS instructions TEXT;

CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL       PRIMARY KEY,
    actor_user_id   INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action          VARCHAR(50)     NOT NULL,
    entity_type     VARCHAR(50)     NOT NULL,
    entity_id       INTEGER,
    before_data     JSONB,
    after_data      JSONB,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id);

CREATE TABLE IF NOT EXISTS import_jobs (
    id              BIGSERIAL       PRIMARY KEY,
    entity_type     VARCHAR(30)     NOT NULL,
    filename        VARCHAR(255)    NOT NULL,
    status          VARCHAR(30)     NOT NULL,
    payload         JSONB           NOT NULL DEFAULT '[]'::jsonb,
    errors          JSONB           NOT NULL DEFAULT '[]'::jsonb,
    warnings        JSONB           NOT NULL DEFAULT '[]'::jsonb,
    total_rows      INTEGER         NOT NULL DEFAULT 0,
    valid_rows      INTEGER         NOT NULL DEFAULT 0,
    error_count     INTEGER         NOT NULL DEFAULT 0,
    created_by      INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_import_jobs_created_at ON import_jobs (created_at DESC);

COMMIT;
