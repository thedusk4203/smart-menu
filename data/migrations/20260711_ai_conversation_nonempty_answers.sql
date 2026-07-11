BEGIN;

UPDATE ai_conversation_turns
   SET status = 'failed', updated_at = NOW()
 WHERE status = 'completed'
   AND NULLIF(BTRIM(assistant_content), '') IS NULL;

ALTER TABLE ai_conversation_turns
    DROP CONSTRAINT IF EXISTS ai_conversation_turns_check;

ALTER TABLE ai_conversation_turns
    DROP CONSTRAINT IF EXISTS ai_conversation_turns_check2;

ALTER TABLE ai_conversation_turns
    DROP CONSTRAINT IF EXISTS ck_ai_conversation_completed_answer;

ALTER TABLE ai_conversation_turns
    ADD CONSTRAINT ck_ai_conversation_completed_answer
    CHECK (status <> 'completed' OR NULLIF(BTRIM(assistant_content), '') IS NOT NULL);

COMMIT;
