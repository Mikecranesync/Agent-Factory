# Supabase + pgvector Testing Guide
## Complete Setup and Testing for Knowledge Atoms

**Cost:** $0/month (Free tier - 500MB database, perfect for development)

**Time to Complete:** 45-60 minutes total

---

## Part 1: Supabase Project Setup (15 minutes)

### Step 1.1: Create Supabase Account and Project (5 min)

1. **Go to Supabase**
   - Navigate to: https://supabase.com/dashboard
   - Click "Sign in" or "Start your project"
   - Sign in with GitHub (recommended) or email

2. **Create New Project**
   - Click "New project" button (green button)
   - Fill in details:
     - **Organization:** Select your organization (or create new)
     - **Project name:** `agent-factory-prod` (or any name you prefer)
     - **Database password:** Click "Generate a password" button
       - ⚠️ **CRITICAL:** Copy this password immediately and save it somewhere safe
       - You'll need this password for direct database access later
     - **Region:** Select closest to you:
       - US East (N. Virginia) - `us-east-1`
       - Europe (Frankfurt) - `eu-central-1`
       - Asia Pacific (Sydney) - `ap-southeast-2`
     - **Pricing plan:** Free tier (default)
   - Click "Create new project"
   - ⏱️ Wait 2-3 minutes while project provisions

3. **Verify Project Created**
   - You should see project dashboard
   - Green "Active" status indicator
   - Database, Auth, Storage tabs visible

---

### Step 1.2: Get API Credentials (3 min)

1. **Navigate to API Settings**
   - In left sidebar: Click "Settings" (gear icon)
   - Click "API" section

2. **Copy Project URL**
   - Look for "Project URL" section at top
   - Example: `https://abcdefghijklmnop.supabase.co`
   - Click copy button or manually copy entire URL
   - Save this - you'll need it for `.env` file

3. **Copy Service Role Key**
   - Scroll down to "Project API keys" section
   - ⚠️ **IMPORTANT:** You need the **`service_role`** key (NOT `anon public`)
   - Look for row labeled `service_role` with label "secret"
   - Click "Reveal" button to show key
   - Click copy button
   - Example key format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (very long)
   - Save this securely - treat it like a password

4. **Update .env File**
   - Open `.env` file in Agent Factory root directory
   - Add these lines (replace with your actual values):

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_actual_key_here

# OpenAI (for embeddings - should already be set)
OPENAI_API_KEY=sk-...
```

   - Save `.env` file

---

### Step 1.3: Enable pgvector Extension (2 min)

1. **Navigate to Extensions**
   - In left sidebar: Click "Database"
   - Click "Extensions" tab

2. **Search for pgvector**
   - In search box at top, type: `vector`
   - Should see extension named `vector` with description "vector data type and ivfflat and hnsw access methods"

3. **Enable Extension**
   - Click toggle switch to enable (should turn green)
   - Or click "Enable" button if present
   - Wait for confirmation (green checkmark appears)
   - ✅ Extension is now active

4. **Verify Extension Enabled**
   - Extension should show "Enabled" status with green indicator
   - Version should be displayed (e.g., `0.7.0` or similar)

---

### Step 1.4: Create knowledge_atoms Table (5 min)

1. **Navigate to SQL Editor**
   - In left sidebar: Click "SQL Editor"
   - Click "New query" button

2. **Get Table Creation SQL**
   - You have two options:

**Option A: Copy from config file (recommended)**
   - Open file: `agent_factory/vectordb/supabase_vector_config.py`
   - Find method `get_table_schema_sql()`
   - Copy entire SQL statement (starts with `CREATE EXTENSION IF NOT EXISTS vector;`)

**Option B: Use SQL below directly**

```sql
-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create knowledge_atoms table
CREATE TABLE IF NOT EXISTS knowledge_atoms (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Atom metadata (from Knowledge Atom Standard)
    atom_id TEXT UNIQUE NOT NULL,
    atom_type TEXT NOT NULL CHECK (atom_type IN (
        'error_code', 'component_spec', 'procedure',
        'troubleshooting_tip', 'safety_requirement',
        'wiring_diagram', 'maintenance_schedule'
    )),

    -- Core content
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    keywords TEXT[] NOT NULL,

    -- Context
    manufacturer TEXT,
    product_family TEXT,
    error_code TEXT,
    component_type TEXT,
    industry_vertical TEXT CHECK (industry_vertical IN (
        'hvac', 'manufacturing', 'pumping', 'power_generation',
        'water_treatment', 'food_beverage', 'mining', 'oil_gas',
        'aerospace', 'automotive', 'marine'
    )),

    -- Quality metrics
    source_tier TEXT CHECK (source_tier IN (
        'manufacturer_official', 'stack_overflow', 'official_forum',
        'reddit', 'blog', 'anecdotal'
    )),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    status TEXT CHECK (status IN ('draft', 'validated', 'published', 'archived')),
    severity TEXT CHECK (severity IN ('critical', 'high', 'medium', 'low')),

    -- Timestamps
    date_created TIMESTAMPTZ DEFAULT NOW(),
    date_modified TIMESTAMPTZ DEFAULT NOW(),

    -- Vector embedding (pgvector)
    embedding vector(3072),

    -- Full atom data (JSONB for flexibility)
    atom_data JSONB NOT NULL,

    -- Integrity hash
    integrity_hash TEXT,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast filtering (metadata)
CREATE INDEX IF NOT EXISTS idx_atoms_atom_type ON knowledge_atoms(atom_type);
CREATE INDEX IF NOT EXISTS idx_atoms_manufacturer ON knowledge_atoms(manufacturer);
CREATE INDEX IF NOT EXISTS idx_atoms_product_family ON knowledge_atoms(product_family);
CREATE INDEX IF NOT EXISTS idx_atoms_error_code ON knowledge_atoms(error_code);
CREATE INDEX IF NOT EXISTS idx_atoms_industry_vertical ON knowledge_atoms(industry_vertical);
CREATE INDEX IF NOT EXISTS idx_atoms_source_tier ON knowledge_atoms(source_tier);
CREATE INDEX IF NOT EXISTS idx_atoms_confidence_score ON knowledge_atoms(confidence_score);
CREATE INDEX IF NOT EXISTS idx_atoms_status ON knowledge_atoms(status);
CREATE INDEX IF NOT EXISTS idx_atoms_severity ON knowledge_atoms(severity);
CREATE INDEX IF NOT EXISTS idx_atoms_date_created ON knowledge_atoms(date_created DESC);

-- Vector similarity index (HNSW for fast approximate nearest neighbor search)
CREATE INDEX IF NOT EXISTS idx_atoms_embedding ON knowledge_atoms
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

3. **Run SQL**
   - Paste SQL into editor
   - Click "Run" button (green play icon) or press `Ctrl+Enter`
   - Wait for execution (usually 5-10 seconds)

4. **Verify Success**
   - Should see message: "Success. No rows returned"
   - If you see errors, check:
     - pgvector extension is enabled
     - No typos in SQL
     - SQL editor is connected (green dot at bottom)

5. **Verify Table Created**
   - In left sidebar: Click "Database" → "Tables"
   - Should see `knowledge_atoms` table in list
   - Click on table name to see structure
   - Should see ~25 columns (id, atom_id, name, description, embedding, etc.)

---

## Part 2: Install Dependencies and Test Connection (10 minutes)

### Step 2.1: Install Python Dependencies (5 min)

1. **Navigate to Worktree Directory**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\agent-factory-knowledge-atom"
```

2. **Install Dependencies**
```bash
poetry install
```

This will install:
- `supabase ^2.0.0` - Supabase Python client
- `openai ^1.26.0` - OpenAI API for embeddings
- `jsonschema ^4.25.0` - JSON Schema validation
- `python-dateutil ^2.9.0` - Date utilities

Expected output:
```
Installing dependencies from lock file
...
Installing supabase (2.x.x)
Installing openai (1.x.x)
...
```

⏱️ Takes 2-3 minutes depending on internet speed

---

### Step 2.2: Test Supabase Connection (5 min)

1. **Create Test Script**

Create file: `test_supabase_connection.py` in worktree root

```python
"""
Test Supabase connection and table setup.
Verifies environment variables and database connectivity.
"""

import os
from dotenv import load_dotenv
from agent_factory.vectordb.supabase_vector_client import SupabaseVectorClient

def test_connection():
    """Test Supabase connection."""

    print("="*70)
    print("SUPABASE CONNECTION TEST")
    print("="*70)

    # Load environment variables
    load_dotenv()

    # Check env vars
    print("\n[1] Checking environment variables...")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not supabase_url:
        print("❌ SUPABASE_URL not set in .env")
        return False
    else:
        print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")

    if not supabase_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY not set in .env")
        return False
    else:
        print(f"✅ SUPABASE_SERVICE_ROLE_KEY: {supabase_key[:20]}...")

    if not openai_key:
        print("❌ OPENAI_API_KEY not set in .env")
        return False
    else:
        print(f"✅ OPENAI_API_KEY: {openai_key[:20]}...")

    # Test connection
    print("\n[2] Connecting to Supabase...")
    try:
        client = SupabaseVectorClient()
        client.connect()
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

    # Test table info
    print("\n[3] Checking knowledge_atoms table...")
    try:
        info = client.get_table_info()
        print(f"✅ Table exists")
        print(f"   - Rows: {info['row_count']}")
        print(f"   - Size: {info['table_size_mb']:.2f} MB")
    except Exception as e:
        print(f"❌ Table check failed: {str(e)}")
        return False

    print("\n" + "="*70)
    print("ALL TESTS PASSED ✅")
    print("="*70)
    print("\nReady to insert Knowledge Atoms!")

    return True

if __name__ == "__main__":
    test_connection()
```

2. **Run Test**
```bash
poetry run python test_supabase_connection.py
```

**Expected Output:**
```
======================================================================
SUPABASE CONNECTION TEST
======================================================================

[1] Checking environment variables...
✅ SUPABASE_URL: https://abcdefg.supabase...
✅ SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiI...
✅ OPENAI_API_KEY: sk-proj-...

[2] Connecting to Supabase...
✅ Connected successfully

[3] Checking knowledge_atoms table...
✅ Table exists
   - Rows: 0
   - Size: 0.00 MB

======================================================================
ALL TESTS PASSED ✅
======================================================================

Ready to insert Knowledge Atoms!
```

---

## Part 3: Test Knowledge Atom Insertion (15 minutes)

### Step 3.1: Create Insertion Test Script (5 min)

Create file: `test_knowledge_atom_insertion.py`

```python
"""
Test Knowledge Atom insertion with full validation pipeline.
"""

from dotenv import load_dotenv
load_dotenv()

from agent_factory.models.knowledge_atom import (
    KnowledgeAtom,
    AtomType,
    Severity,
    SourceTier,
    AuthorReputation,
    AtomStatus,
    IndustryVertical,
    ComponentType,
    ManufacturerReference,
    ProductFamily,
    KnowledgeSource,
    Quality,
    ConfidenceComponents,
)
from agent_factory.vectordb.knowledge_atom_store import KnowledgeAtomStore
from datetime import datetime

def create_test_atom():
    """Create ABB VFD firmware error atom for testing."""

    return KnowledgeAtom.create(
        atom_type=AtomType.ERROR_CODE,
        name="Error F032: Firmware Version Mismatch",
        description=(
            "Occurs when the drive firmware version does not match the expected version "
            "for the control system. Common causes include incomplete firmware update, "
            "power loss during update process, or incorrect firmware file used. "
            "Resolution requires factory reset and reflashing with correct firmware version. "
            "Critical for ABB ACS880 series drives in HVAC applications."
        ),
        keywords=["F032", "firmware", "mismatch", "ABB", "ACS880", "version", "update"],
        severity=Severity.HIGH,

        # Manufacturer context
        manufacturers=[
            ManufacturerReference(
                name="ABB",
                url="https://new.abb.com"
            )
        ],
        product_families=[
            ProductFamily(
                name="ABB ACS880 Series",
                identifier="abb_acs880"
            )
        ],
        error_code="F032",
        component_types=[ComponentType.VFD],
        industry_verticals=[IndustryVertical.HVAC],
        protocols=["ethernet_ip", "modbus"],

        # Source provenance
        provider=KnowledgeSource(
            source_tier=SourceTier.MANUFACTURER_OFFICIAL,
            source_platform="abb_manual",
            url="https://library.abb.com/acs880-firmware-manual",
            date_published=datetime(2024, 1, 15),
            author="ABB Technical Documentation Team",
            author_reputation=AuthorReputation.MANUFACTURER_OFFICIAL
        ),

        # Quality metrics
        quality=Quality(
            confidence_score=0.95,
            confidence_components=ConfidenceComponents(
                source_tier_confidence=0.95,
                corroboration_confidence=0.95,
                recency_confidence=0.95,
                author_reputation_confidence=1.0
            ),
            corroboration_count=5,
            contradiction_count=0,
            citation_count=47
        ),

        status=AtomStatus.VALIDATED,
        resolution="Perform factory reset, then reflash firmware using correct version from ABB support portal"
    )

def test_insertion():
    """Test complete insertion workflow."""

    print("="*70)
    print("KNOWLEDGE ATOM INSERTION TEST")
    print("="*70)

    # Step 1: Create atom
    print("\n[Step 1] Creating test Knowledge Atom...")
    atom = create_test_atom()
    print(f"✅ Created: {atom.name}")
    print(f"   Atom ID: {atom.atom_id}")
    print(f"   Type: {atom.atom_type.value}")
    print(f"   Confidence: {atom.quality.confidence_score}")
    print(f"   Manufacturer: {atom.manufacturers[0].name}")

    # Step 2: Initialize store
    print("\n[Step 2] Initializing Knowledge Atom Store...")
    store = KnowledgeAtomStore()

    # Step 3: Connect to Supabase
    print("\n[Step 3] Connecting to Supabase...")
    store.connect()
    print("✅ Connected and table verified")

    # Step 4: Insert atom (runs 6-stage validation + embedding)
    print("\n[Step 4] Inserting atom...")
    print("   This will:")
    print("   - Run 6-stage validation pipeline")
    print("   - Generate embedding (OpenAI text-embedding-3-large)")
    print("   - Insert into PostgreSQL with pgvector")
    print()

    try:
        integrity_hash = store.insert(atom)
        print(f"\n✅ Insertion successful!")
        print(f"   Integrity hash: {integrity_hash[:32]}...")
    except Exception as e:
        print(f"\n❌ Insertion failed: {str(e)}")
        return False

    # Step 5: Verify insertion
    print("\n[Step 5] Verifying insertion...")
    retrieved = store.get_by_atom_id(atom.atom_id)

    if not retrieved:
        print("❌ Atom not found in database!")
        return False

    print("✅ Atom retrieved successfully")
    print(f"   Name: {retrieved['name']}")
    print(f"   Manufacturer: {retrieved['manufacturer']}")
    print(f"   Confidence: {retrieved['confidence_score']}")
    print(f"   Status: {retrieved['status']}")
    print(f"   Has embedding: {retrieved['embedding'] is not None}")
    print(f"   Embedding dimensions: {len(retrieved['embedding']) if retrieved['embedding'] else 0}")

    # Step 6: Get database stats
    print("\n[Step 6] Database statistics...")
    stats = store.get_stats()
    print(f"   Total atoms: {stats['total_atoms']}")
    print(f"   Table size: {stats['table_size_mb']:.4f} MB")
    print(f"   Index size: {stats['index_size_mb']:.4f} MB")

    print("\n" + "="*70)
    print("TEST PASSED ✅")
    print("="*70)

    return True

if __name__ == "__main__":
    success = test_insertion()
    exit(0 if success else 1)
```

---

### Step 3.2: Run Insertion Test (5 min)

```bash
poetry run python test_knowledge_atom_insertion.py
```

**Expected Output:**
```
======================================================================
KNOWLEDGE ATOM INSERTION TEST
======================================================================

[Step 1] Creating test Knowledge Atom...
✅ Created: Error F032: Firmware Version Mismatch
   Atom ID: urn:industrial-maintenance:atom:f8e7d6c5-b4a3-...
   Type: error_code
   Confidence: 0.95
   Manufacturer: ABB

[Step 2] Initializing Knowledge Atom Store...

[Step 3] Connecting to Supabase...
Connecting to Supabase...
Creating knowledge_atoms table (if not exists)...
  - Dimension: 3072
  - Index type: hnsw
  - Distance metric: cosine
[OK] Table 'knowledge_atoms' created successfully
[OK] Knowledge Atom Store ready
✅ Connected and table verified

[Step 4] Inserting atom...
   This will:
   - Run 6-stage validation pipeline
   - Generate embedding (OpenAI text-embedding-3-large)
   - Insert into PostgreSQL with pgvector

Validating atom: Error F032: Firmware Version Mismatch...
[OK] Validation passed (hash: a1b2c3d4e5f6...)
Generating embedding...
[OK] Embedding generated (3072 dimensions)
Inserting into knowledge_atoms...
[OK] Inserted atom: Error F032: Firmware Version Mismatch

✅ Insertion successful!
   Integrity hash: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6...

[Step 5] Verifying insertion...
✅ Atom retrieved successfully
   Name: Error F032: Firmware Version Mismatch
   Manufacturer: abb
   Confidence: 0.95
   Status: validated
   Has embedding: True
   Embedding dimensions: 3072

[Step 6] Database statistics...
   Total atoms: 1
   Table size: 0.0234 MB
   Index size: 0.0156 MB

======================================================================
TEST PASSED ✅
======================================================================
```

---

### Step 3.3: Verify in Supabase Dashboard (3 min)

1. **Go to Table Editor**
   - Supabase Dashboard → Database → Table Editor
   - Click `knowledge_atoms` table

2. **Verify Row Data**
   You should see 1 row with:
   - ✅ `id`: UUID (auto-generated)
   - ✅ `atom_id`: `urn:industrial-maintenance:atom:...`
   - ✅ `atom_type`: `error_code`
   - ✅ `name`: "Error F032: Firmware Version Mismatch"
   - ✅ `description`: Full text (200+ chars)
   - ✅ `keywords`: Array `["F032", "firmware", ...]`
   - ✅ `manufacturer`: `abb`
   - ✅ `product_family`: `abb_acs880`
   - ✅ `error_code`: `F032`
   - ✅ `confidence_score`: `0.95`
   - ✅ `status`: `validated`
   - ✅ `embedding`: Vector (3072 dimensions) - shown as `[0.123, -0.456, ...]`
   - ✅ `atom_data`: JSONB object (full atom structure)

3. **Check Embedding Vector**
   - Click on the `embedding` cell
   - Should show array like: `[0.00234, -0.01567, 0.00891, ...]`
   - Should have exactly 3072 numbers
   - Click outside to close

---

## Part 4: Test Semantic Search (15 minutes)

### Step 4.1: Insert More Test Atoms (5 min)

Create file: `insert_test_atoms.py`

```python
"""Insert multiple test atoms for semantic search testing."""

from dotenv import load_dotenv
load_dotenv()

from agent_factory.models.knowledge_atom import *
from agent_factory.vectordb.knowledge_atom_store import KnowledgeAtomStore
from datetime import datetime

def create_test_atoms():
    """Create 5 test atoms with different content."""

    atoms = []

    # Atom 1: ABB VFD firmware error (already inserted, but here for reference)
    atoms.append(KnowledgeAtom.create(
        atom_type=AtomType.ERROR_CODE,
        name="Error F032: Firmware Version Mismatch",
        description="VFD firmware version does not match expected version for control system.",
        keywords=["F032", "firmware", "ABB", "ACS880"],
        severity=Severity.HIGH,
        manufacturers=[ManufacturerReference(name="ABB", url="https://new.abb.com")],
        product_families=[ProductFamily(name="ABB ACS880 Series", identifier="abb_acs880")],
        error_code="F032",
        component_types=[ComponentType.VFD],
        industry_verticals=[IndustryVertical.HVAC],
        provider=KnowledgeSource(
            source_tier=SourceTier.MANUFACTURER_OFFICIAL,
            source_platform="abb_manual",
            url="https://library.abb.com",
            date_published=datetime(2024, 1, 15)
        ),
        quality=Quality(confidence_score=0.95),
        status=AtomStatus.VALIDATED
    ))

    # Atom 2: Siemens VFD overcurrent error
    atoms.append(KnowledgeAtom.create(
        atom_type=AtomType.ERROR_CODE,
        name="Error A0501: Overcurrent Protection Triggered",
        description="Drive detected overcurrent condition and shut down to protect motor and drive components.",
        keywords=["A0501", "overcurrent", "Siemens", "G120"],
        severity=Severity.CRITICAL,
        manufacturers=[ManufacturerReference(name="Siemens", url="https://www.siemens.com")],
        product_families=[ProductFamily(name="Siemens SINAMICS G120", identifier="siemens_g120")],
        error_code="A0501",
        component_types=[ComponentType.VFD],
        industry_verticals=[IndustryVertical.MANUFACTURING],
        provider=KnowledgeSource(
            source_tier=SourceTier.MANUFACTURER_OFFICIAL,
            source_platform="siemens_manual",
            url="https://support.industry.siemens.com",
            date_published=datetime(2024, 2, 1)
        ),
        quality=Quality(confidence_score=0.97),
        status=AtomStatus.VALIDATED
    ))

    # Atom 3: Generic HVAC maintenance procedure
    atoms.append(KnowledgeAtom.create(
        atom_type=AtomType.PROCEDURE,
        name="Quarterly HVAC Preventive Maintenance Checklist",
        description="Standard quarterly maintenance procedure for commercial HVAC systems including filter replacement, coil cleaning, and refrigerant level checks.",
        keywords=["HVAC", "maintenance", "preventive", "quarterly", "checklist"],
        severity=Severity.MEDIUM,
        manufacturers=[],
        component_types=[ComponentType.HVAC_UNIT],
        industry_verticals=[IndustryVertical.HVAC],
        provider=KnowledgeSource(
            source_tier=SourceTier.OFFICIAL_FORUM,
            source_platform="hvac_talk",
            url="https://hvac-talk.com",
            date_published=datetime(2024, 3, 15)
        ),
        quality=Quality(confidence_score=0.82),
        status=AtomStatus.VALIDATED
    ))

    # Atom 4: Pump cavitation troubleshooting
    atoms.append(KnowledgeAtom.create(
        atom_type=AtomType.TROUBLESHOOTING_TIP,
        name="Centrifugal Pump Cavitation: Causes and Solutions",
        description="Cavitation in centrifugal pumps causes noise, vibration, and reduced performance. Common causes: insufficient NPSH, air leaks in suction line, or excessive fluid temperature.",
        keywords=["pump", "cavitation", "NPSH", "centrifugal", "troubleshooting"],
        severity=Severity.HIGH,
        manufacturers=[],
        component_types=[ComponentType.PUMP],
        industry_verticals=[IndustryVertical.PUMPING, IndustryVertical.WATER_TREATMENT],
        provider=KnowledgeSource(
            source_tier=SourceTier.STACK_OVERFLOW,
            source_platform="engineering_stackexchange",
            url="https://engineering.stackexchange.com",
            date_published=datetime(2024, 4, 10)
        ),
        quality=Quality(confidence_score=0.88),
        status=AtomStatus.VALIDATED
    ))

    # Atom 5: Safety requirement for arc flash
    atoms.append(KnowledgeAtom.create(
        atom_type=AtomType.SAFETY_REQUIREMENT,
        name="NFPA 70E Arc Flash PPE Requirements",
        description="Personal protective equipment requirements for electrical work based on arc flash hazard categories. Category 2 requires minimum 8 cal/cm² rated arc-rated clothing.",
        keywords=["safety", "arc flash", "PPE", "NFPA", "electrical"],
        severity=Severity.CRITICAL,
        manufacturers=[],
        component_types=[],
        industry_verticals=[IndustryVertical.MANUFACTURING, IndustryVertical.POWER_GENERATION],
        provider=KnowledgeSource(
            source_tier=SourceTier.MANUFACTURER_OFFICIAL,
            source_platform="nfpa_standard",
            url="https://www.nfpa.org/70E",
            date_published=datetime(2024, 1, 1)
        ),
        quality=Quality(confidence_score=0.98),
        status=AtomStatus.VALIDATED
    ))

    return atoms

def insert_all():
    """Insert all test atoms."""

    print("Creating test atoms...")
    atoms = create_test_atoms()
    print(f"Created {len(atoms)} atoms")

    print("\nConnecting to Supabase...")
    store = KnowledgeAtomStore()
    store.connect()

    print("\nInserting atoms (this will take ~2 min for embeddings)...")
    hashes = store.batch_insert(atoms, skip_validation=False)

    successful = sum(1 for h in hashes if h is not None)
    print(f"\n✅ Inserted {successful}/{len(atoms)} atoms")

    stats = store.get_stats()
    print(f"\nDatabase stats:")
    print(f"  Total atoms: {stats['total_atoms']}")
    print(f"  Table size: {stats['table_size_mb']:.2f} MB")

if __name__ == "__main__":
    insert_all()
```

**Run it:**
```bash
poetry run python insert_test_atoms.py
```

This will take ~2-3 minutes (generating embeddings for 5 atoms).

---

### Step 4.2: Test Semantic Search (5 min)

Create file: `test_semantic_search.py`

```python
"""Test semantic search functionality."""

from dotenv import load_dotenv
load_dotenv()

from agent_factory.vectordb.knowledge_atom_store import KnowledgeAtomStore

def test_search():
    """Test various semantic search queries."""

    print("="*70)
    print("SEMANTIC SEARCH TEST")
    print("="*70)

    store = KnowledgeAtomStore()
    store.connect()

    # Test 1: Search for VFD firmware issues
    print("\n[Test 1] Search: 'VFD firmware problem'")
    print("-"*70)
    results = store.query(
        "VFD firmware problem",
        top_k=3,
        min_similarity=0.0
    )

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Similarity: {result['similarity']:.3f}")
        print(f"   Manufacturer: {result.get('manufacturer', 'N/A')}")
        print(f"   Type: {result['atom_type']}")

    # Test 2: Search with manufacturer filter
    print("\n\n[Test 2] Search: 'drive error' (ABB only)")
    print("-"*70)
    results = store.query(
        "drive error",
        top_k=3,
        filters={"manufacturer": "abb"},
        min_similarity=0.0
    )

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Similarity: {result['similarity']:.3f}")
        print(f"   Manufacturer: {result['manufacturer']}")

    # Test 3: Search for safety content
    print("\n\n[Test 3] Search: 'electrical safety requirements'")
    print("-"*70)
    results = store.query(
        "electrical safety requirements",
        top_k=3,
        min_similarity=0.0
    )

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Similarity: {result['similarity']:.3f}")
        print(f"   Type: {result['atom_type']}")

    # Test 4: High confidence only
    print("\n\n[Test 4] Search: 'pump issues' (confidence >= 0.85)")
    print("-"*70)
    results = store.query(
        "pump issues",
        top_k=3,
        filters={"confidence_score": {"gte": 0.85}},
        min_similarity=0.0
    )

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Similarity: {result['similarity']:.3f}")
        print(f"   Confidence: {result['confidence_score']}")

    print("\n" + "="*70)
    print("SEARCH TESTS COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_search()
```

**Run it:**
```bash
poetry run python test_semantic_search.py
```

**Expected Output:**
```
======================================================================
SEMANTIC SEARCH TEST
======================================================================

[Test 1] Search: 'VFD firmware problem'
----------------------------------------------------------------------

1. Error F032: Firmware Version Mismatch
   Similarity: 0.847
   Manufacturer: abb
   Type: error_code

2. Error A0501: Overcurrent Protection Triggered
   Similarity: 0.623
   Manufacturer: siemens
   Type: error_code

3. Quarterly HVAC Preventive Maintenance Checklist
   Similarity: 0.412
   Manufacturer: N/A
   Type: procedure


[Test 2] Search: 'drive error' (ABB only)
----------------------------------------------------------------------

1. Error F032: Firmware Version Mismatch
   Similarity: 0.789
   Manufacturer: abb


[Test 3] Search: 'electrical safety requirements'
----------------------------------------------------------------------

1. NFPA 70E Arc Flash PPE Requirements
   Similarity: 0.891
   Type: safety_requirement

2. Error A0501: Overcurrent Protection Triggered
   Similarity: 0.512
   Type: error_code


[Test 4] Search: 'pump issues' (confidence >= 0.85)
----------------------------------------------------------------------

1. Centrifugal Pump Cavitation: Causes and Solutions
   Similarity: 0.834
   Confidence: 0.88

2. Error A0501: Overcurrent Protection Triggered
   Similarity: 0.478
   Confidence: 0.97

======================================================================
SEARCH TESTS COMPLETE
======================================================================
```

---

## Part 5: Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: "OPENAI_API_KEY not set"
**Error:**
```
[WARN] OPENAI_API_KEY not set - embeddings will fail
```

**Solution:**
- Check `.env` file has `OPENAI_API_KEY=sk-...`
- Restart terminal/VS Code
- Run `poetry shell` then retry

---

#### Issue 2: "SupabaseConnectionError"
**Error:**
```
SupabaseConnectionError: Missing Supabase credentials
```

**Solution:**
- Verify `.env` has both `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Check URL format: `https://xxxxx.supabase.co` (must include https://)
- Verify service role key (starts with `eyJ...`, very long)

---

#### Issue 3: "relation 'knowledge_atoms' does not exist"
**Error:**
```
relation "knowledge_atoms" does not exist
```

**Solution:**
- Table wasn't created
- Go to Supabase → SQL Editor
- Run table creation SQL (Step 1.4)
- Verify in Database → Tables

---

#### Issue 4: "Extension 'vector' does not exist"
**Error:**
```
ERROR: type "vector" does not exist
```

**Solution:**
- pgvector extension not enabled
- Go to Supabase → Database → Extensions
- Enable `vector` extension
- Re-run table creation SQL

---

#### Issue 5: Slow Embedding Generation
**Symptom:**
Taking > 30 seconds per atom

**Causes:**
- OpenAI API rate limits (Free tier: 3 requests/min)
- Network latency

**Solutions:**
- Wait between insertions
- Upgrade OpenAI API tier
- Use `skip_validation=True` for testing (NOT production)

---

## Success Checklist

After completing all tests, verify:

- [ ] ✅ Supabase project created and active
- [ ] ✅ pgvector extension enabled
- [ ] ✅ knowledge_atoms table created with all columns
- [ ] ✅ HNSW vector index created
- [ ] ✅ Environment variables set in `.env`
- [ ] ✅ Dependencies installed (`poetry install`)
- [ ] ✅ Connection test passes
- [ ] ✅ Single atom insertion works
- [ ] ✅ 5+ test atoms inserted
- [ ] ✅ Semantic search returns relevant results
- [ ] ✅ Metadata filtering works (manufacturer, confidence)
- [ ] ✅ Database stats show correct counts

---

## Next Steps

Once all tests pass:

1. **Integrate with ABB Scraper**
   - Modify ABB scraper to output Knowledge Atoms
   - Insert scraped data into Supabase
   - Build RIVET diagnostic agent

2. **Create Control Panel**
   - GitHub Issue similar to Rivet Discovery (#32)
   - Mobile-friendly commands for overnight work

3. **Scale Testing**
   - Insert 100+ atoms
   - Benchmark query performance
   - Monitor database size

---

## Cost Tracking

**Current Usage (Free Tier):**
- Database: 5 atoms × ~0.02 MB = 0.1 MB (of 500 MB free)
- Embeddings: 5 atoms × $0.00013 = $0.00065
- **Total: $0/month** (well within free tier)

**Projected Usage (1,000 atoms):**
- Database: ~20 MB (still free tier)
- Embeddings (one-time): ~$0.13
- Queries: Free (no per-query cost)
- **Total: $0/month**

**Upgrade Trigger (10,000+ atoms):**
- Database: ~200 MB (still free tier)
- May want Pro tier ($25/month) for better performance
- Or stay on free tier if performance is acceptable

---

## Support

**Supabase Issues:**
- Dashboard: https://supabase.com/dashboard
- Docs: https://supabase.com/docs
- Community: https://github.com/supabase/supabase/discussions

**pgvector Issues:**
- Docs: https://supabase.com/docs/guides/database/extensions/pgvector
- Examples: https://github.com/supabase/supabase/tree/master/examples/ai

**Knowledge Atom Standard:**
- Spec: `knowledge-atom-standard-v1.0.md`
- Issues: Create GitHub issue in Agent Factory repo

---

**Testing Time:** 45-60 minutes total
**Cost:** $0/month (Free tier)
**Status:** ✅ Production-ready for development

Happy testing! 🚀
