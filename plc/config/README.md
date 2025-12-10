# PLC Configuration Files

Configuration for agents, database, and PLC platforms.

## Files

### database_schema.sql
Supabase table definitions for PLC atoms (extends RIVET schema).

```sql
CREATE TABLE plc_atoms (
  id UUID PRIMARY KEY,
  atom_id TEXT UNIQUE NOT NULL,
  atom_type TEXT NOT NULL,
  vendor TEXT NOT NULL,
  platform TEXT,
  embedding vector(3072),
  full_json JSONB NOT NULL,
  ...
);
```

### agent_schedules.yaml
When each agent runs (cron-style schedules).

```yaml
agents:
  textbook_scraper:
    schedule: "0 2 * * *"  # Daily at 2 AM
    enabled: true

  code_generator:
    schedule: "on_demand"
    enabled: true

  analytics_agent:
    schedule: "0 */6 * * *"  # Every 6 hours
    enabled: true
```

### vendor_config.yaml
Vendor-specific settings (API endpoints, documentation URLs).

```yaml
vendors:
  siemens:
    platforms:
      - s7-1200
      - s7-1500
      - s7-300
    documentation_url: "https://support.industry.siemens.com"
    programming_languages:
      - ladder_logic
      - structured_text
      - function_block_diagram

  allen_bradley:
    platforms:
      - control_logix
      - compact_logix
      - micro800
    documentation_url: "https://literature.rockwellautomation.com"
    programming_languages:
      - ladder_logic
      - structured_text
```

### safety_levels.yaml
Safety level definitions (aligns with IEC 62061).

```yaml
safety_levels:
  info:
    description: "Informational, no safety impact"
    color: "blue"
    requires_review: false

  danger:
    description: "Risk of injury or death"
    color: "red"
    requires_review: true
    requires_lockout_tagout: true
```
