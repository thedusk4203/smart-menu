BEGIN;

CREATE TABLE ai_conversations (
    id          BIGSERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(80) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ai_conversations_user_updated
    ON ai_conversations (user_id, updated_at DESC, id DESC);

CREATE TABLE ai_conversation_turns (
    id                  BIGSERIAL PRIMARY KEY,
    conversation_id     BIGINT NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    turn_number         SMALLINT NOT NULL CHECK (turn_number BETWEEN 1 AND 20),
    user_content        VARCHAR(4000) NOT NULL,
    assistant_content   TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'completed', 'failed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (conversation_id, turn_number),
    CHECK (status <> 'completed' OR assistant_content IS NOT NULL)
);
CREATE INDEX idx_ai_conversation_turns_order
    ON ai_conversation_turns (conversation_id, turn_number);

CREATE TRIGGER trg_ai_conversations_updated_at
    BEFORE UPDATE ON ai_conversations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_ai_conversation_turns_updated_at
    BEFORE UPDATE ON ai_conversation_turns
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
