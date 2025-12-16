# Memory System Operations Runbook
**Version:** 1.0
**Last Updated:** 2025-12-15
**Owner:** DevOps Team

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Common Procedures](#common-procedures)
4. [Troubleshooting](#troubleshooting)
5. [Emergency Procedures](#emergency-procedures)
6. [Maintenance Tasks](#maintenance-tasks)
7. [Monitoring & Alerts](#monitoring--alerts)

---

## System Overview

### Architecture
```
Application Layer
      |
      v
PostgresMemoryStorage
      |
      v
DatabaseManager (Multi-Provider)
      |
      +-- Neon (Primary)
      +-- Supabase (Backup 1)
      +-- Railway (Backup 2)
```

### Components
- **PostgresMemoryStorage** - Memory API for agents
- **DatabaseManager** - Multi-provider connection manager
- **3 Providers** - Neon, Supabase, Railway (automatic failover)
- **Health Checks** - 60-second cached health status
- **Connection Pools** - psycopg pools (1-10 connections per provider)

### Key Tables
- `session_memories` - Session data and messages
- `knowledge_atoms` - Knowledge base (1,965 atoms)
- `settings` - Runtime configuration
- `research_staging`, `video_scripts`, `upload_jobs`, `agent_messages`

---

## Daily Operations

### Morning Checklist (5 minutes)
```bash
# 1. Check provider health
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
health = db.health_check_all()
for name, is_healthy in health.items():
    status = '[OK]' if is_healthy else '[DOWN]'
    print(f'{status} {name}')
"

# 2. Check knowledge atom count
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
result = db.execute_query('SELECT COUNT(*) FROM knowledge_atoms', fetch_mode='one')
print(f'Knowledge atoms: {result[0]}')
"

# 3. Check recent errors (if error_logs table exists)
# poetry run python scripts/ops/check_recent_errors.py

# 4. Verify backup exists from last night
ls -lh backups/  # Should see backup from previous day
```

### End of Day Checklist (3 minutes)
```bash
# 1. Trigger manual backup (if needed)
poetry run python scripts/ops/backup_database.py

# 2. Check failover events (if any occurred today)
# poetry run python scripts/ops/check_failover_log.py

# 3. Review slow queries (if logging enabled)
# poetry run python scripts/ops/analyze_slow_queries.py
```

---

## Common Procedures

### 1. Checking Provider Health

**When:** Before deployments, after incidents, during troubleshooting

**Command:**
```bash
poetry run python scripts/ops/verify_memory_deployment.py
```

**Expected Output:**
```
[TEST 1] Verifying imports...
[OK] All imports successful

[TEST 2] Testing DatabaseManager...
[INFO] Primary provider: neon
[INFO] Failover enabled: true
[OK] DatabaseManager initialized

[TEST 3] Testing provider health checks...
[OK] neon: healthy
[DOWN] supabase: unhealthy
[OK] Atleast one provider is healthy
```

**If Issues:**
- See [Troubleshooting](#troubleshooting) section

---

### 2. Switching Primary Provider

**When:** Primary provider is down or slow, planned maintenance

**Steps:**
```bash
# 1. Check which providers are healthy
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print(db.health_check_all())
"

# 2. Update .env to use healthy provider
# Edit .env:
DATABASE_PROVIDER=supabase  # or neon, railway

# 3. Restart application (if needed)
# The next database operation will use the new provider

# 4. Verify change
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print(f'Current primary: {db.primary_provider}')
"
```

---

### 3. Deploying Schema Changes

**When:** Database schema needs updating, new features added

**Steps:**
```bash
# 1. Backup all providers first!
poetry run python scripts/ops/backup_database.py --all-providers

# 2. Test schema change on Neon (test environment)
poetry run python scripts/deploy_multi_provider_schema.py --provider neon --dry-run

# 3. Apply to Neon
poetry run python scripts/deploy_multi_provider_schema.py --provider neon

# 4. Verify schema deployed correctly
poetry run python scripts/deploy_multi_provider_schema.py --verify

# 5. If OK, apply to Supabase
poetry run python scripts/deploy_multi_provider_schema.py --provider supabase

# 6. If OK, apply to Railway
poetry run python scripts/deploy_multi_provider_schema.py --provider railway

# 7. Final verification
poetry run python scripts/deploy_multi_provider_schema.py --verify
```

**Rollback Procedure (if schema breaks):**
```bash
# 1. Restore from backup
poetry run python scripts/ops/restore_database.py --provider neon --backup backups/neon-2025-12-15.sql

# 2. Verify restore worked
poetry run python scripts/ops/verify_memory_deployment.py

# 3. Investigate schema issue offline
```

---

### 4. Fixing Schema Constraint Issues

**When:** `session_memories_memory_type_check` constraint violation

**Steps:**
```bash
# 1. Check current constraint
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
db.set_provider('neon')
result = db.execute_query('''
    SELECT pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'session_memories'::regclass
    AND conname LIKE '%memory_type%'
''', fetch_mode='one')
print(result[0] if result else 'No constraint found')
"

# 2. Apply fix (dry-run first)
poetry run python scripts/ops/fix_schema_constraints.py --dry-run

# 3. Apply fix for real
poetry run python scripts/ops/fix_schema_constraints.py

# 4. Verify fix
poetry run python scripts/ops/verify_memory_deployment.py
```

---

### 5. Backing Up Database

**When:** Before deployments, daily automated backups, before risky operations

**Manual Backup:**
```bash
# Backup primary provider
poetry run python scripts/ops/backup_database.py

# Backup specific provider
poetry run python scripts/ops/backup_database.py --provider supabase

# Backup all providers
poetry run python scripts/ops/backup_database.py --all-providers
```

**Automated Backup (Cron):**
```bash
# Add to crontab (runs daily at 2am UTC)
0 2 * * * cd /path/to/agent-factory && poetry run python scripts/ops/backup_database.py --all-providers >> /var/log/agent-factory-backup.log 2>&1
```

**Verify Backup:**
```bash
# List recent backups
ls -lh backups/

# Test restore (dry-run)
poetry run python scripts/ops/restore_database.py --dry-run --backup backups/neon-2025-12-15.sql
```

---

### 6. Restoring from Backup

**When:** Data loss, corruption, rollback needed

**Steps:**
```bash
# 1. STOP ALL APPLICATIONS USING THE DATABASE
# This prevents writes during restore

# 2. Create pre-restore backup (just in case)
poetry run python scripts/ops/backup_database.py --provider neon

# 3. Restore from backup
poetry run python scripts/ops/restore_database.py --provider neon --backup backups/neon-2025-12-15.sql

# 4. Verify restore worked
poetry run python scripts/ops/verify_memory_deployment.py

# 5. Check data integrity
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
result = db.execute_query('SELECT COUNT(*) FROM session_memories', fetch_mode='one')
print(f'Sessions: {result[0]}')
"

# 6. RESTART APPLICATIONS
```

**Recovery Time Objective (RTO):** < 1 hour
**Recovery Point Objective (RPO):** < 24 hours (daily backups)

---

## Troubleshooting

### Issue: Provider Health Check Fails

**Symptoms:**
```
[DOWN] supabase: unhealthy
```

**Diagnosis Steps:**
```bash
# 1. Check if it's a DNS issue
ping db.mggqgrxwumnnujojndub.supabase.co

# 2. Check if it's a connectivity issue
psql "postgresql://postgres:[password]@db.mggqgrxwumnnujojndub.supabase.co:5432/postgres"

# 3. Check Supabase dashboard
# Go to: https://supabase.com/dashboard
# Verify project is active and not paused

# 4. Check firewall/network
# Ensure port 5432 outbound is allowed
```

**Resolution:**
- **If DNS fails:** Verify hostname in .env matches Supabase dashboard
- **If connection times out:** Check firewall, VPN, or network connectivity
- **If project paused:** Unpause in Supabase dashboard or switch to another provider
- **If permanent:** Update DATABASE_PROVIDER in .env to use healthy provider

---

### Issue: Schema Constraint Violation

**Symptoms:**
```
ERROR: new row for relation "session_memories" violates check constraint
```

**Diagnosis:**
```bash
# Check current constraint definition
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
result = db.execute_query('''
    SELECT pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'session_memories'::regclass
''', fetch_mode='all')
for row in result:
    print(row[0])
"
```

**Resolution:**
```bash
# Apply schema fix
poetry run python scripts/ops/fix_schema_constraints.py --provider neon

# Verify
poetry run python scripts/ops/verify_memory_deployment.py
```

---

### Issue: Connection Pool Exhausted

**Symptoms:**
```
WARNING: couldn't get a connection after 5.00 sec
```

**Diagnosis:**
```bash
# Check current pool settings (in database_manager.py)
# Default: min_size=1, max_size=10, timeout=5.0

# Check active connections
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
stats = db.get_provider_stats()
for name, info in stats.items():
    print(f'{name}: pool_active={info[\"pool_active\"]}')
"
```

**Resolution:**
```bash
# Option 1: Increase pool size (edit database_manager.py)
# Change max_size=10 to max_size=20

# Option 2: Increase timeout
# Change timeout=5.0 to timeout=10.0

# Option 3: Close idle connections
# Restart application to reset pools
```

---

### Issue: Failover Not Working

**Symptoms:**
```
ERROR: All database providers failed
```

**Diagnosis:**
```bash
# Check failover configuration
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print(f'Failover enabled: {db.failover_enabled}')
print(f'Failover order: {db.failover_order}')
print(f'Health: {db.health_check_all()}')
"
```

**Resolution:**
```bash
# 1. Verify at least one provider is healthy
# If all providers are down, investigate each provider

# 2. Check DATABASE_FAILOVER_ENABLED in .env
# Should be: DATABASE_FAILOVER_ENABLED=true

# 3. Verify failover order contains healthy providers
# DATABASE_FAILOVER_ORDER=neon,supabase,railway
```

---

## Emergency Procedures

### EMERGENCY: All Providers Down

**Impact:** Memory system completely unavailable, all operations failing

**Immediate Actions (first 5 minutes):**
```bash
# 1. Check if it's a code issue or infrastructure issue
poetry run python scripts/ops/verify_memory_deployment.py

# 2. Check each provider manually
ping db.mggqgrxwumnnujojndub.supabase.co
ping ep-bitter-shadow-ah70vrun-pooler.c-3.us-east-1.aws.neon.tech

# 3. Check provider dashboards
# - Supabase: https://supabase.com/dashboard
# - Neon: https://console.neon.tech
# - Railway: https://railway.app/dashboard

# 4. Switch to InMemoryStorage as temporary fallback
# Edit code to use: storage = InMemoryStorage()
# (data will be lost on restart, but system stays operational)
```

**Recovery Steps:**
```bash
# 1. Bring up at least one provider
# - Unpause project in dashboard
# - Fix DNS/connectivity issues
# - Restore from backup if needed

# 2. Verify provider is healthy
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print(db.health_check_all())
"

# 3. Switch back to PostgresMemoryStorage
# Revert code changes, restart application

# 4. Verify system operational
poetry run python scripts/ops/verify_memory_deployment.py
```

---

### EMERGENCY: Data Corruption Detected

**Impact:** Invalid data in database, queries failing

**Immediate Actions:**
```bash
# 1. STOP ALL WRITES IMMEDIATELY
# Stop application or disable write operations

# 2. Identify scope of corruption
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
# Check row counts, run validation queries
result = db.execute_query('SELECT COUNT(*) FROM session_memories WHERE content IS NULL', fetch_mode='one')
print(f'Null content rows: {result[0]}')
"

# 3. Restore from last known good backup
poetry run python scripts/ops/restore_database.py --backup backups/neon-2025-12-14.sql

# 4. Verify restore fixed corruption
poetry run python scripts/ops/verify_memory_deployment.py

# 5. RESTART APPLICATIONS
```

---

## Maintenance Tasks

### Weekly Tasks
- [ ] Review provider health metrics
- [ ] Check disk usage on all providers
- [ ] Verify backups are running and valid
- [ ] Review slow query logs (if enabled)
- [ ] Check for schema drift across providers

### Monthly Tasks
- [ ] Rotate database credentials
- [ ] Test disaster recovery (full restore)
- [ ] Review connection pool sizes
- [ ] Analyze query performance trends
- [ ] Update provider statistics

### Quarterly Tasks
- [ ] Load testing (find bottlenecks)
- [ ] Security audit (SQL injection, encryption)
- [ ] Capacity planning (project growth)
- [ ] Review and update runbook
- [ ] Provider cost analysis

---

## Monitoring & Alerts

### Health Monitoring Script
```bash
# Create cron job to check health every 5 minutes
*/5 * * * * cd /path/to/agent-factory && poetry run python scripts/ops/health_monitor.py >> /var/log/health-monitor.log 2>&1
```

### Alert Triggers
- **CRITICAL:** All providers down
- **WARNING:** Primary provider down (failover active)
- **WARNING:** Backup fails
- **INFO:** Provider recovered after being down

### Alert Channels
- Telegram (fast, mobile-friendly)
- Email (for full details)
- PagerDuty (for on-call rotation)

---

## Contacts & Escalation

| Role | Name | Contact | Escalation |
|------|------|---------|------------|
| Primary On-Call | TBD | telegram | Immediate |
| Secondary On-Call | TBD | email | After 15 min |
| Database Admin | TBD | phone | After 30 min |
| Engineering Lead | TBD | phone | For decisions |

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-15 | 1.0 | Initial runbook | Claude Code |

---

**END OF RUNBOOK**
