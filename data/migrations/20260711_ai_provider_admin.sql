BEGIN;

CREATE TABLE IF NOT EXISTS llm_provider_configs (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    provider_type VARCHAR(30) NOT NULL CHECK (provider_type IN ('openai', 'deepseek', 'lmstudio', 'google', 'custom')),
    base_url VARCHAR(500) NOT NULL,
    model VARCHAR(200) NOT NULL,
    encrypted_api_key TEXT,
    api_key_suffix VARCHAR(8),
    timeout_seconds NUMERIC(6,2) NOT NULL DEFAULT 60 CHECK (timeout_seconds BETWEEN 1 AND 300),
    structured_output_mode VARCHAR(20) CHECK (structured_output_mode IN ('json_schema', 'json_object')),
    config_version INTEGER NOT NULL DEFAULT 1,
    tested_version INTEGER,
    test_status VARCHAR(20) NOT NULL DEFAULT 'untested' CHECK (test_status IN ('untested', 'success', 'failed')),
    last_tested_at TIMESTAMPTZ,
    last_test_error TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_provider_one_active
    ON llm_provider_configs ((is_active)) WHERE is_active = TRUE;

CREATE TABLE IF NOT EXISTS ai_request_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    provider_config_id BIGINT REFERENCES llm_provider_configs(id) ON DELETE SET NULL,
    feature VARCHAR(40) NOT NULL,
    provider_type VARCHAR(30) NOT NULL,
    model VARCHAR(200) NOT NULL,
    request_data JSONB NOT NULL,
    response_data JSONB,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error')),
    latency_ms INTEGER NOT NULL DEFAULT 0,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days')
);
CREATE INDEX IF NOT EXISTS idx_ai_request_logs_created_at ON ai_request_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_request_logs_filters ON ai_request_logs (feature, status, user_id);

COMMIT;
