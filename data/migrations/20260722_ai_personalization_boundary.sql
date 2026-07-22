BEGIN;

CREATE TABLE IF NOT EXISTS user_ai_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    personalization_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    notice_version VARCHAR(40) NOT NULL,
    consented_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_consent_events (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    personalization_enabled BOOLEAN NOT NULL,
    notice_version VARCHAR(40) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_consent_events_user_created
    ON ai_consent_events (user_id, created_at DESC);

ALTER TABLE ai_conversations
    ADD COLUMN IF NOT EXISTS mode VARCHAR(24) NOT NULL DEFAULT 'general';
ALTER TABLE ai_conversations DROP CONSTRAINT IF EXISTS ck_ai_conversations_mode;
ALTER TABLE ai_conversations ADD CONSTRAINT ck_ai_conversations_mode
    CHECK (mode IN ('general', 'meal_advice', 'health_reference'));

ALTER TABLE ai_conversation_turns
    ADD COLUMN IF NOT EXISTS personalization_used BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS grounding_mode VARCHAR(24) NOT NULL DEFAULT 'none',
    ADD COLUMN IF NOT EXISTS citations JSONB NOT NULL DEFAULT '[]'::JSONB;
ALTER TABLE ai_conversation_turns DROP CONSTRAINT IF EXISTS ck_ai_turn_grounding_mode;
ALTER TABLE ai_conversation_turns ADD CONSTRAINT ck_ai_turn_grounding_mode
    CHECK (grounding_mode IN ('none', 'native_web_search', 'model_fallback'));

ALTER TABLE llm_provider_configs
    ADD COLUMN IF NOT EXISTS native_web_search_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS capability_checked_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='menuto_ai_context_reader') THEN
        CREATE ROLE menuto_ai_context_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='menuto_ai_state_writer') THEN
        CREATE ROLE menuto_ai_state_writer LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END $$;

ALTER ROLE menuto_ai_context_reader SET default_transaction_read_only = on;
DO $$
BEGIN
    EXECUTE format(
        'GRANT CONNECT ON DATABASE %%I TO menuto_ai_context_reader, menuto_ai_state_writer',
        current_database()
    );
END $$;
GRANT USAGE ON SCHEMA public TO menuto_ai_context_reader, menuto_ai_state_writer;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM menuto_ai_context_reader;
GRANT SELECT ON user_profiles, user_excluded_ingredients, ingredients,
    inventory_lots, tag_catalog, dish_ingredients, v_dish_candidates
    TO menuto_ai_context_reader;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM menuto_ai_state_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_ai_preferences, ai_consent_events,
    ai_conversations, ai_conversation_turns, ai_request_logs
    TO menuto_ai_state_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO menuto_ai_state_writer;

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_excluded_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_lots ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_ai_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_consent_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_conversation_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_request_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ai_context_profile_scope ON user_profiles;
CREATE POLICY ai_context_profile_scope ON user_profiles TO PUBLIC
    USING (current_user <> 'menuto_ai_context_reader'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER);
DROP POLICY IF EXISTS ai_context_exclusion_scope ON user_excluded_ingredients;
CREATE POLICY ai_context_exclusion_scope ON user_excluded_ingredients TO PUBLIC
    USING (current_user <> 'menuto_ai_context_reader'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER);
DROP POLICY IF EXISTS ai_context_inventory_scope ON inventory_lots;
CREATE POLICY ai_context_inventory_scope ON inventory_lots TO PUBLIC
    USING (current_user <> 'menuto_ai_context_reader'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER);

DROP POLICY IF EXISTS ai_state_preferences_scope ON user_ai_preferences;
CREATE POLICY ai_state_preferences_scope ON user_ai_preferences TO PUBLIC
    USING (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER)
    WITH CHECK (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER);
DROP POLICY IF EXISTS ai_state_consent_scope ON ai_consent_events;
CREATE POLICY ai_state_consent_scope ON ai_consent_events TO PUBLIC
    USING (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER)
    WITH CHECK (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER);
DROP POLICY IF EXISTS ai_state_conversation_scope ON ai_conversations;
CREATE POLICY ai_state_conversation_scope ON ai_conversations TO PUBLIC
    USING (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER)
    WITH CHECK (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER);
DROP POLICY IF EXISTS ai_state_turn_scope ON ai_conversation_turns;
CREATE POLICY ai_state_turn_scope ON ai_conversation_turns TO PUBLIC
    USING (current_user <> 'menuto_ai_state_writer' OR EXISTS (
        SELECT 1 FROM ai_conversations c WHERE c.id=conversation_id
          AND c.user_id=NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER
    ))
    WITH CHECK (current_user <> 'menuto_ai_state_writer' OR EXISTS (
        SELECT 1 FROM ai_conversations c WHERE c.id=conversation_id
          AND c.user_id=NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER
    ));
DROP POLICY IF EXISTS ai_state_log_scope ON ai_request_logs;
CREATE POLICY ai_state_log_scope ON ai_request_logs TO PUBLIC
    USING (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER)
    WITH CHECK (current_user <> 'menuto_ai_state_writer'
        OR user_id = NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER);

COMMIT;
