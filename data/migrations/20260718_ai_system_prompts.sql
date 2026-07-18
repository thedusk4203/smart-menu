BEGIN;

CREATE TABLE IF NOT EXISTS ai_system_prompts (
    feature     VARCHAR(40)     PRIMARY KEY
                                CHECK (feature IN ('chat', 'parse_menu', 'explain_plan', 'suggest_swap')),
    content     TEXT            NOT NULL
                                CHECK (CHAR_LENGTH(BTRIM(content)) BETWEEN 1 AND 20000),
    updated_by  INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMIT;
