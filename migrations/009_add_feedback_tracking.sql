-- Migration 009: Add Feedback Tracking
-- Date: 2026-01-02
-- Description: Add feedback fields to knowledge_atoms and work_orders for user feedback loop

-- ============================================================================
-- Add feedback tracking to knowledge_atoms table
-- ============================================================================

-- Add success_rate column (calculated from positive/negative feedback)
ALTER TABLE knowledge_atoms
ADD COLUMN IF NOT EXISTS success_rate FLOAT DEFAULT NULL;

-- Add feedback counters
ALTER TABLE knowledge_atoms
ADD COLUMN IF NOT EXISTS feedback_positive_count INTEGER DEFAULT 0;

ALTER TABLE knowledge_atoms
ADD COLUMN IF NOT EXISTS feedback_negative_count INTEGER DEFAULT 0;

-- Add usage tracking
ALTER TABLE knowledge_atoms
ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;

-- Add constraint for valid success_rate (0.0-1.0 or NULL)
ALTER TABLE knowledge_atoms
DROP CONSTRAINT IF EXISTS valid_success_rate;

ALTER TABLE knowledge_atoms
ADD CONSTRAINT valid_success_rate CHECK (
    success_rate IS NULL OR (success_rate >= 0.0 AND success_rate <= 1.0)
);

-- Create index for filtering low-quality atoms (success_rate < 0.3)
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_success_rate
ON knowledge_atoms(success_rate)
WHERE success_rate IS NOT NULL;

-- ============================================================================
-- Add feedback tracking to work_orders table
-- ============================================================================

-- Add user feedback column (positive, negative, none)
DO $$ BEGIN
    CREATE TYPE FeedbackType AS ENUM ('positive', 'negative', 'none');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

ALTER TABLE work_orders
ADD COLUMN IF NOT EXISTS user_feedback FeedbackType DEFAULT 'none';

ALTER TABLE work_orders
ADD COLUMN IF NOT EXISTS feedback_at TIMESTAMPTZ;

-- Create index for filtering by feedback
CREATE INDEX IF NOT EXISTS idx_work_orders_feedback
ON work_orders(user_feedback)
WHERE user_feedback != 'none';

-- ============================================================================
-- Function to update atom success_rate when feedback is received
-- ============================================================================

CREATE OR REPLACE FUNCTION update_atom_success_rate(p_atom_id TEXT)
RETURNS VOID AS $$
DECLARE
    total_feedback INTEGER;
    positive_count INTEGER;
    new_success_rate FLOAT;
BEGIN
    -- Get feedback counts for this atom
    SELECT
        feedback_positive_count,
        feedback_positive_count + feedback_negative_count
    INTO positive_count, total_feedback
    FROM knowledge_atoms
    WHERE atom_id = p_atom_id;

    -- Calculate success_rate (only if we have at least 1 feedback)
    IF total_feedback > 0 THEN
        new_success_rate := positive_count::FLOAT / total_feedback::FLOAT;

        UPDATE knowledge_atoms
        SET success_rate = new_success_rate
        WHERE atom_id = p_atom_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON COLUMN knowledge_atoms.success_rate IS
'Calculated from user feedback: positive_count / (positive_count + negative_count). NULL if no feedback yet. Used to trigger research for low-quality atoms (<0.3).';

COMMENT ON COLUMN knowledge_atoms.feedback_positive_count IS
'Number of thumbs-up feedback received from users';

COMMENT ON COLUMN knowledge_atoms.feedback_negative_count IS
'Number of thumbs-down feedback received from users';

COMMENT ON COLUMN knowledge_atoms.usage_count IS
'Number of times this atom was shown to users (for calculating engagement rate)';

COMMENT ON COLUMN work_orders.user_feedback IS
'User feedback on the answer quality (positive/negative/none)';

COMMENT ON COLUMN work_orders.feedback_at IS
'Timestamp when user provided feedback';

-- ============================================================================
-- Example: How to use the feedback system
-- ============================================================================

/*
-- 1. User clicks thumbs up/down button
-- 2. Update work_order feedback
UPDATE work_orders
SET user_feedback = 'positive', feedback_at = NOW()
WHERE id = 'work_order_uuid';

-- 3. Increment atom feedback counter
UPDATE knowledge_atoms
SET feedback_positive_count = feedback_positive_count + 1
WHERE atom_id = 'allen_bradley:controllogix:motor-control';

-- 4. Recalculate success_rate
SELECT update_atom_success_rate('allen_bradley:controllogix:motor-control');

-- 5. Find low-quality atoms that need research
SELECT atom_id, title, success_rate, feedback_positive_count, feedback_negative_count
FROM knowledge_atoms
WHERE success_rate < 0.3
AND (feedback_positive_count + feedback_negative_count) >= 3  -- At least 3 feedback samples
ORDER BY success_rate ASC, usage_count DESC
LIMIT 10;
*/
