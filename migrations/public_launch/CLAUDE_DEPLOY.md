# RIVET CMMS - Public Launch Deployment

## Context
You are deploying the Rivet CMMS Telegram bot from personal-only to public multi-tenant mode. The bot token has already been created and added to `.env` as `PUBLIC_TELEGRAM_BOT_TOKEN`.

## Your Tasks

### 1. Verify the token exists
Read `.env` and confirm `PUBLIC_TELEGRAM_BOT_TOKEN` is set (don't print the full token, just confirm it exists and starts with a number).

### 2. Run the database migration
Execute the SQL migration against the Neon database:

```bash
psql $NEON_DB_URL -f migrations/public_launch/001_public_ready_schema.sql
```

If `psql` isn't available, use Python:
```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['NEON_DB_URL'])
conn.autocommit = True
cursor = conn.cursor()

with open('migrations/public_launch/001_public_ready_schema.sql', 'r') as f:
    sql = f.read()
    cursor.execute(sql)

cursor.close()
conn.close()
print('✓ Migration complete')
```

### 3. Verify admin registration
Confirm that Telegram ID `8445149012` is in the `admin_users` table as `super_admin`:

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['NEON_DB_URL'])
cursor = conn.cursor()
cursor.execute("SELECT telegram_id, username, role FROM admin_users WHERE telegram_id = 8445149012")
result = cursor.fetchone()
cursor.close()
conn.close()

if result:
    print(f"✓ Admin verified: {result}")
else:
    print("❌ Admin not found - check migration")
```

### 4. Verify tier_limits table
Check that the pricing tiers were created:

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['NEON_DB_URL'])
cursor = conn.cursor()
cursor.execute("SELECT tier, questions_per_month, price_monthly_usd FROM tier_limits ORDER BY price_monthly_usd")
rows = cursor.fetchall()
cursor.close()
conn.close()

print("Tier Limits:")
for row in rows:
    print(f"  {row[0]}: {row[1]} questions/mo @ ${row[2]}/mo")
```

### 5. Test the public_auth module
```python
import sys
sys.path.insert(0, '.')

from agent_factory.integrations.telegram.public_auth import auth

# Test admin check
is_admin = auth.is_admin(8445149012)
role = auth.get_admin_role(8445149012)

print(f"Admin check: {is_admin}")
print(f"Role: {role}")

if is_admin and role == 'super_admin':
    print("✓ Auth module working correctly")
else:
    print("❌ Auth module issue")
```

### 6. Test bot imports
Verify the public bot can import all dependencies:

```python
import sys
sys.path.insert(0, '.')

try:
    from agent_factory.integrations.telegram.public_auth import auth, admin_only, rate_limited
    print("✓ public_auth")
    
    from agent_factory.integrations.telegram.rivet_pro_handlers import RIVETProHandlers
    print("✓ rivet_pro_handlers")
    
    from agent_factory.integrations.telegram.tier0_handlers import TIER0Handlers
    print("✓ tier0_handlers")
    
    from agent_factory.integrations.telegram.print_handlers import add_machine_command
    print("✓ print_handlers")
    
    from agent_factory.integrations.telegram.manual_handlers import upload_manual_command
    print("✓ manual_handlers")
    
    print("\n✓ All imports successful - ready to launch!")
except ImportError as e:
    print(f"❌ Import error: {e}")
```

### 7. Create systemd service file for VPS (optional)
If deploying to VPS, create the service file:

```bash
cat > /tmp/rivet-public.service << 'EOF'
[Unit]
Description=Rivet CMMS Public Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rivet
EnvironmentFile=/opt/rivet/.env.production
ExecStart=/opt/rivet/venv/bin/python rivet_public_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at /tmp/rivet-public.service"
echo "To deploy: scp /tmp/rivet-public.service root@72.60.175.144:/etc/systemd/system/"
```

### 8. Summary
After completing all steps, print a summary:

```
═══════════════════════════════════════════════════════════════
RIVET CMMS - PUBLIC LAUNCH COMPLETE
═══════════════════════════════════════════════════════════════

Database:
  ✓ rate_limits table created
  ✓ usage_events table created  
  ✓ tier_limits configured (free/pro/enterprise)
  ✓ admin_users table with super_admin

Auth:
  ✓ public_auth middleware ready
  ✓ Admin commands protected
  ✓ Rate limiting enabled

To start locally:
  python rivet_public_bot.py

To deploy to VPS:
  scp rivet_public_bot.py root@72.60.175.144:/opt/rivet/
  scp agent_factory/integrations/telegram/public_auth.py root@72.60.175.144:/opt/rivet/agent_factory/integrations/telegram/
  ssh root@72.60.175.144 "cd /opt/rivet && python rivet_public_bot.py"

Bot URL: https://t.me/RivetCMMS_bot (or your bot username)
═══════════════════════════════════════════════════════════════
```

## Important Notes

- The working directory is: `C:\Users\hharp\OneDrive\Desktop\Agent Factory`
- Use Python for database operations if psql isn't available
- Don't print full tokens or passwords
- If any step fails, stop and report the error
- The bot token is already in `.env` as `PUBLIC_TELEGRAM_BOT_TOKEN`

## Success Criteria

All of these must be true:
1. Migration ran without errors
2. `admin_users` table has entry for 8445149012
3. `tier_limits` has free/pro/enterprise tiers
4. All Python imports succeed
5. `auth.is_admin(8445149012)` returns True
