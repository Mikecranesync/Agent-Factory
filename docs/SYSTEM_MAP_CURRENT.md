# RIVET SYSTEM ARCHITECTURE

## Current System Map (What's Built)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   RIVET MVP                                      │
│                          Voice-First CMMS for Field Techs                        │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │  TELEGRAM   │
                                    │    USER     │
                                    │  (Mobile)   │
                                    └──────┬──────┘
                                           │
                                           │ Text / Photos
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TELEGRAM BOT LAYER                                  │
│                           VPS: 72.60.175.144                                     │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │    bot.py       │  │   handlers.py   │  │ rivet_pro_      │                  │
│  │                 │  │                 │  │ handlers.py     │                  │
│  │ • Webhook       │  │ • /start        │  │                 │                  │
│  │ • Message       │  │ • /help         │  │ • Equipment     │                  │
│  │   routing       │  │ • Basic cmds    │  │   queries       │                  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                    │                            │
│           └────────────────────┼────────────────────┘                            │
│                                │                                                 │
│                                ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │                    SESSION MANAGER                           │                │
│  │                                                              │                │
│  │  • User sessions          • Conversation state               │                │
│  │  • Context tracking       • Multi-turn memory                │                │
│  └──────────────────────────────┬───────────────────────────────┘                │
│                                 │                                                │
└─────────────────────────────────┼────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RIVET PRO CORE                                      │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ INTENT          │  │ CONFIDENCE      │  │ CONVERSATION    │                  │
│  │ DETECTOR        │  │ SCORER          │  │ MANAGER         │                  │
│  │                 │  │                 │  │                 │                  │
│  │ • Classify      │  │ • Score intent  │  │ • Multi-turn    │                  │
│  │   user intent   │  │   confidence    │  │   context       │                  │
│  │ • Route to      │  │ • Threshold     │  │ • History       │                  │
│  │   correct agent │  │   decisions     │  │   tracking      │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │                      SME AGENTS                              │                │
│  │                                                              │                │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │                │
│  │  │Electrical│ │Mechanical│ │Hydraulic │ │Pneumatic │        │                │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │        │                │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │                │
│  │                                                              │                │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │                │
│  │  │  Safety  │ │   PLC    │ │   VFD    │                     │                │
│  │  │  Agent   │ │  Agent   │ │  Agent   │                     │                │
│  │  └──────────┘ └──────────┘ └──────────┘                     │                │
│  └─────────────────────────────────────────────────────────────┘                │
│                                                                                  │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│    OCR PIPELINE     │ │   CLAUDE API    │ │   DATABASE          │
│                     │ │                 │ │                     │
│ ┌─────────────────┐ │ │ • claude-sonnet │ │ ┌─────────────────┐ │
│ │ Gemini Vision   │ │ │ • Responses     │ │ │ Neon PostgreSQL │ │
│ │ Provider        │ │ │ • Analysis      │ │ │                 │ │
│ └─────────────────┘ │ │                 │ │ │ • rivet_users   │ │
│ ┌─────────────────┐ │ │                 │ │ │ • Sessions      │ │
│ │ GPT-4O Vision   │ │ │                 │ │ │                 │ │
│ │ Provider        │ │ │                 │ │ └─────────────────┘ │
│ └─────────────────┘ │ │                 │ │                     │
│                     │ │                 │ │                     │
│ • Nameplate OCR     │ │                 │ │                     │
│ • Equipment ID      │ │                 │ │                     │
└─────────────────────┘ └─────────────────┘ └─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND                                     │
│                            (Phase 3 Complete)                                    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │                      API ROUTERS                             │                │
│  │                                                              │                │
│  │  /api/users/           /api/stripe/         /health          │                │
│  │  ├── provision         ├── checkout         └── DB status    │                │
│  │  ├── from-telegram     ├── webhook                           │                │
│  │  ├── link-telegram     ├── portal                            │                │
│  │  ├── {user_id}         └── cancel                            │                │
│  │  ├── by-email/{email}                                        │                │
│  │  ├── by-telegram/{id}                                        │                │
│  │  └── {user_id}/tier                                          │                │
│  └─────────────────────────────────────────────────────────────┘                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MONITORING & LOGGING                                   │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   LANGSMITH     │  │    WATCHDOG     │  │     REDIS       │                  │
│  │                 │  │                 │  │                 │                  │
│  │ • Trace routes  │  │ • Health checks │  │ • Session cache │                  │
│  │ • Performance   │  │ • Auto-restart  │  │ • Rate limiting │                  │
│  │ • Debug chains  │  │ • Alerts        │  │                 │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Current)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NEON POSTGRESQL                                        │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │                      rivet_users                             │                │
│  │                                                              │                │
│  │  id                 UUID PRIMARY KEY                         │                │
│  │  email              VARCHAR(255)                             │                │
│  │  telegram_id        BIGINT UNIQUE                            │                │
│  │  telegram_username  VARCHAR(255)                             │                │
│  │  stripe_customer_id VARCHAR(255)                             │                │
│  │  atlas_user_id      VARCHAR(255)                             │                │
│  │  tier               VARCHAR(50) DEFAULT 'beta'               │                │
│  │  created_at         TIMESTAMP                                │                │
│  │  updated_at         TIMESTAMP                                │                │
│  └─────────────────────────────────────────────────────────────┘                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure (Current)

```
agent_factory/
├── api/                          # FastAPI Backend
│   ├── main.py                   # App entry, health check
│   ├── config.py                 # Pydantic settings
│   └── routers/
│       ├── stripe.py             # Stripe endpoints ✅
│       ├── users.py              # User CRUD ✅
│       └── work_orders.py        # Work order stubs
│
├── integrations/
│   └── telegram/
│       ├── bot.py                # Main bot ✅
│       ├── handlers.py           # Base handlers ✅
│       ├── rivet_pro_handlers.py # Rivet handlers ✅
│       ├── session_manager.py    # Sessions ✅
│       ├── conversation_manager.py
│       └── ocr/
│           ├── pipeline.py       # OCR orchestration ✅
│           ├── gemini_provider.py # Gemini Vision ✅
│           └── gpt4o_provider.py  # GPT-4O Vision ✅
│
├── rivet_pro/
│   ├── intent_detector.py        # Intent classification ✅
│   ├── confidence_scorer.py      # Confidence scoring ✅
│   ├── database.py               # User DB methods ✅
│   ├── stripe_integration.py     # Stripe manager ✅
│   ├── feature_flags.py          # Tier features ✅
│   └── agents/                   # SME agents ✅
│
└── core/                         # Agent Factory core
    ├── agent_builder.py
    ├── llm_providers.py
    └── tool_registry.py
```
