-- ═══════════════════════════════════════════════════════════════════════════
-- RIVET Pro - Schema Verification Queries
-- Run these queries to verify your Neon PostgreSQL deployment
-- ═══════════════════════════════════════════════════════════════════════════

-- Usage:
-- psql $NEON_DB_URL -f scripts/verify_schema.sql

\echo '─────────────────────────────────────────────────────────────────────────'
\echo '1. VERIFY TABLES EXIST'
\echo '─────────────────────────────────────────────────────────────────────────'

SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name LIKE 'rivet_%'
ORDER BY table_name;

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '2. VERIFY INDEXES EXIST'
\echo '─────────────────────────────────────────────────────────────────────────'

SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename LIKE 'rivet_%'
ORDER BY tablename, indexname;

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '3. VERIFY FUNCTIONS EXIST'
\echo '─────────────────────────────────────────────────────────────────────────'

SELECT
    routine_name,
    routine_type,
    data_type as return_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND (
    routine_name LIKE '%user%'
    OR routine_name LIKE '%lookup%'
    OR routine_name LIKE '%print%'
    OR routine_name LIKE '%subscription%'
  )
ORDER BY routine_name;

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '4. TEST FUNCTION: Create Test User'
\echo '─────────────────────────────────────────────────────────────────────────'

SELECT * FROM get_or_create_user(
    123456789,  -- test telegram_id
    'test_user',
    'Test User'
);

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '5. TEST FUNCTION: Check and Increment Lookup (First Call)'
\echo '─────────────────────────────────────────────────────────────────────────'

SELECT
    allowed,
    remaining,
    is_pro,
    message
FROM check_and_increment_lookup(123456789);

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '6. TEST FUNCTION: Check and Increment Lookup (Second Call)'
\echo '─────────────────────────────────────────────────────────────────────────'

SELECT
    allowed,
    remaining,
    is_pro,
    message
FROM check_and_increment_lookup(123456789);

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '7. TEST FUNCTION: Get User Status'
\echo '─────────────────────────────────────────────────────────────────────────'

SELECT
    telegram_id,
    tier,
    is_pro,
    lookup_count,
    lookups_remaining,
    total_lookups,
    subscription_status,
    days_until_reset
FROM get_user_status(123456789);

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '8. VERIFY FREE TIER LIMIT (Increment to 10)'
\echo '─────────────────────────────────────────────────────────────────────────'

-- Increment 8 more times to reach the limit
SELECT check_and_increment_lookup(123456789) FROM generate_series(1, 8);

\echo ''
\echo 'Now check status at limit:'
SELECT allowed, remaining, message FROM check_and_increment_lookup(123456789);

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '9. TEST PRO USER UPGRADE'
\echo '─────────────────────────────────────────────────────────────────────────'

-- Simulate Stripe subscription
SELECT update_subscription(
    123456789,              -- telegram_id
    'cus_test123',          -- stripe_customer_id
    'sub_test123',          -- stripe_subscription_id
    'active',               -- subscription_status
    TRUE                    -- is_pro
);

\echo ''
\echo 'Verify Pro status allows unlimited lookups:'
SELECT allowed, remaining, is_pro, message FROM check_and_increment_lookup(123456789);

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '10. TEST PRINT SESSION (Pro Feature)'
\echo '─────────────────────────────────────────────────────────────────────────'

-- Start a print session
SELECT * FROM start_print_session(
    123456789,
    'test_file_id_123',
    'test_schematic.pdf',
    'base64_encoded_pdf_data_here'
);

\echo ''
\echo 'Get active print session:'
SELECT
    session_id,
    pdf_name,
    message_count,
    is_active
FROM rivet_print_sessions
WHERE telegram_id = 123456789 AND is_active = TRUE;

\echo ''
\echo 'Add message to session:'
SELECT add_print_message(
    (SELECT id FROM rivet_print_sessions WHERE telegram_id = 123456789 AND is_active = TRUE LIMIT 1),
    'user',
    'What does wire W123 connect to?'
);

\echo ''
\echo 'End print session:'
SELECT * FROM end_print_session(123456789);

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '11. VIEW ALL TEST DATA'
\echo '─────────────────────────────────────────────────────────────────────────'

\echo ''
\echo 'Users created:'
SELECT telegram_id, telegram_username, tier, is_pro, lookup_count, total_lookups_all_time FROM rivet_users;

\echo ''
\echo 'Usage log entries:'
SELECT COUNT(*) as total_usage_entries FROM rivet_usage_log;

\echo ''
\echo 'Print sessions:'
SELECT id, telegram_id, pdf_name, message_count, is_active FROM rivet_print_sessions;

\echo ''
\echo '─────────────────────────────────────────────────────────────────────────'
\echo '12. CLEANUP TEST DATA'
\echo '─────────────────────────────────────────────────────────────────────────'

-- Uncomment to clean up test data:
-- DELETE FROM rivet_print_sessions WHERE telegram_id = 123456789;
-- DELETE FROM rivet_usage_log WHERE telegram_id = 123456789;
-- DELETE FROM rivet_users WHERE telegram_id = 123456789;

\echo ''
\echo '═════════════════════════════════════════════════════════════════════════'
\echo '✅ VERIFICATION COMPLETE'
\echo '═════════════════════════════════════════════════════════════════════════'
\echo ''
\echo 'If all queries executed successfully, your schema is ready for production!'
\echo ''
\echo 'Expected results:'
\echo '  - 4 tables created (rivet_users, rivet_usage_log, rivet_print_sessions, rivet_stripe_events)'
\echo '  - 8 functions working (user management, lookup tracking, print sessions)'
\echo '  - Free tier: 10 lookup limit enforced'
\echo '  - Pro tier: Unlimited lookups'
\echo '  - Print sessions: Only available for Pro users'
\echo ''
\echo 'Next step: Phase 2 - Create n8n workflows'
\echo ''
