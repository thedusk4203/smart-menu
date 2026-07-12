BEGIN;

CREATE INDEX IF NOT EXISTS idx_ai_conversations_retention
    ON ai_conversations (updated_at);

COMMIT;
