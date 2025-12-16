-- ============================================================================
-- FIX: session_memories memory_type CHECK constraint
-- ============================================================================
--
-- Issue: Neon database has CHECK constraint that doesn't allow 'session_metadata'
-- Error: new row for relation "session_memories" violates check constraint
--        "session_memories_memory_type_check"
--
-- This script updates the constraint to allow all memory types used by the code:
-- - session_metadata (session info)
-- - message_user (user messages)
-- - message_assistant (assistant responses)
-- - message_system (system messages)
-- - context (project status updates)
-- - action (tasks and next actions)
-- - issue (bugs and problems)
-- - decision (technical decisions)
-- - log (development activities)
--
-- Run on: Neon database (via web SQL editor or psql)
-- Date: 2025-12-15
-- ============================================================================

-- Step 1: Check current constraint definition
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'session_memories'::regclass
  AND conname LIKE '%memory_type%';

-- Step 2: Drop existing constraint
ALTER TABLE session_memories
DROP CONSTRAINT IF EXISTS session_memories_memory_type_check;

-- Step 3: Add updated constraint with all allowed values
ALTER TABLE session_memories
ADD CONSTRAINT session_memories_memory_type_check
CHECK (memory_type IN (
    'session_metadata',      -- Session metadata (created_at, last_active, etc.)
    'message_user',          -- User messages in conversation
    'message_assistant',     -- Assistant responses
    'message_system',        -- System messages
    'context',               -- Project status updates
    'action',                -- Tasks and next actions
    'issue',                 -- Bugs and problems
    'decision',              -- Technical decisions
    'log'                    -- Development activities
));

-- Step 4: Verify constraint was updated
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'session_memories'::regclass
  AND conname LIKE '%memory_type%';

-- Step 5: Test insert (should succeed)
-- Uncomment to test:
-- INSERT INTO session_memories (session_id, user_id, memory_type, content, created_at)
-- VALUES (
--     'test_session_id',
--     'test_user_id',
--     'session_metadata',
--     '{"test": "data"}'::jsonb,
--     NOW()
-- );

-- Step 6: Clean up test row (if you ran the test)
-- DELETE FROM session_memories WHERE session_id = 'test_session_id';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
-- If no errors, the constraint has been successfully updated.
-- You can now save sessions using PostgresMemoryStorage without errors.
-- ============================================================================
