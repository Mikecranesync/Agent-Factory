# WORKSTREAM 1: BACKEND + API
# Tab 1 of 3
# Copy everything below this line into Claude Code CLI

You are WS-1 (Backend) in a 3-tab parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context reaches 80%, checkpoint and summarize

## YOUR IDENTITY
- Workstream: WS-1 (Backend + API)
- Branch: rivet-backend
- Focus: Atlas CMMS, FastAPI, User/Work Order APIs

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b rivet-backend
git push -u origin rivet-backend
```

## EXISTING CODE YOU'RE BUILDING ON
```
agent_factory/api/           # FastAPI app (already created)
├── main.py                  # App entry point
├── config.py                # Settings
└── routers/
    ├── stripe.py            # Stripe endpoints (DONE)
    ├── users.py             # User provisioning (needs DB)
    └── work_orders.py       # Work order CRUD (needs Atlas)

agent_factory/rivet_pro/
├── stripe_integration.py    # Stripe manager (exists)
├── database.py              # User DB (exists)
└── feature_flags.py         # Tier features (DONE)
```

## YOUR TASKS

### Phase 1: Atlas CMMS Setup (Day 1)

**Task 1.1: Research Atlas CMMS**
```bash
# Clone and explore Atlas
cd /tmp
git clone https://github.com/Grashjs/cmms.git atlas-cmms
ls atlas-cmms/
cat atlas-cmms/README.md
```
- Document API endpoints we need
- Note authentication method
- Check Docker deployment options

**Task 1.2: Create Atlas Client**
Create `/agent_factory/integrations/atlas/`:
```
atlas/
├── __init__.py
├── client.py           # AtlasClient class
├── models.py           # Work order, Asset, User models
└── config.py           # Connection settings
```

AtlasClient methods needed:
```python
class AtlasClient:
    async def create_work_order(self, data: WorkOrderCreate) -> WorkOrder
    async def get_work_order(self, wo_id: str) -> WorkOrder
    async def list_work_orders(self, user_id: str) -> List[WorkOrder]
    async def get_asset(self, asset_id: str) -> Asset
    async def search_assets(self, query: str) -> List[Asset]
    async def create_user(self, email: str, tier: str) -> User
```

**Task 1.3: Docker Compose for Atlas**
Create `/deploy/atlas/docker-compose.yml`:
- Atlas backend
- Atlas frontend (optional for MVP)
- PostgreSQL for Atlas
- Configure for VPS 72.60.175.144

### Phase 2: Connect APIs (Day 2)

**Task 2.1: Wire Up Work Order Endpoints**
Update `/agent_factory/api/routers/work_orders.py`:
- Replace TODO stubs with real AtlasClient calls
- Add error handling
- Add LangSmith logging

**Task 2.2: Wire Up User Provisioning**
Update `/agent_factory/api/routers/users.py`:
- `/api/users/from-telegram` - Create user when bot /start
- `/api/users/provision` - Create user from Stripe webhook
- Store user in both our DB and Atlas

**Task 2.3: Wire Up Asset Search**
For intent clarification ("which pump?"):
```python
@router.get("/api/assets")
async def search_assets(q: str) -> List[AssetSummary]:
    # Search Atlas for matching equipment
    # Return id, name, location for disambiguation
```

### Phase 3: Database Schema (Day 2-3)

**Task 3.1: User Table**
```sql
CREATE TABLE rivet_users (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    telegram_id BIGINT UNIQUE,
    telegram_username VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    atlas_user_id VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'beta',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Task 3.2: Add to Neon**
Use existing NEON_DB_URL connection.

### Phase 4: Health & Monitoring (Day 3)

**Task 4.1: Health Endpoints**
```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "atlas": await check_atlas(),
        "database": await check_db(),
        "stripe": await check_stripe()
    }
```

**Task 4.2: LangSmith Tracing**
Add tracing to all API calls using existing LangSmith setup.

## COMMIT PROTOCOL
After EACH task:
```bash
git add -A
git commit -m "WS-1: [component] description"
git push origin rivet-backend
```

## SUCCESS CRITERIA
- [ ] AtlasClient can create/read work orders
- [ ] User provisioning works (Telegram + Stripe paths)
- [ ] Asset search returns results
- [ ] Health endpoint shows all systems green
- [ ] API runs: `uvicorn agent_factory.api.main:app --port 8000`

## UPDATE STATUS
After each phase, update: `/sprint/STATUS_WS1.md`

## START NOW
Begin with Task 1.1 - Research Atlas CMMS API.
