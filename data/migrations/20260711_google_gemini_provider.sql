BEGIN;

ALTER TABLE llm_provider_configs
    DROP CONSTRAINT IF EXISTS llm_provider_configs_provider_type_check;
ALTER TABLE llm_provider_configs
    ADD CONSTRAINT llm_provider_configs_provider_type_check
    CHECK (provider_type IN ('openai', 'deepseek', 'lmstudio', 'google', 'custom'));

COMMIT;
