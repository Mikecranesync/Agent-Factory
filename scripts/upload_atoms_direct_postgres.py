#!/usr/bin/env python3
"""
DIRECT POSTGRESQL UPLOAD - BYPASSES POST REST SCHEMA CACHE

Uploads atoms directly to PostgreSQL, avoiding Supabase PostgREST API.
This bypasses the PGRST204 schema cache issue.

Usage:
    poetry run python scripts/upload_atoms_direct_postgres.py
"""

import os
import sys
import json
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Load env
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("DIRECT POSTGRESQL UPLOAD - BYPASSING POSTGREST")
print("=" * 80)
print()

# ============================================================================
# STEP 1: LOAD ATOMS FROM LOCAL FILES
# ============================================================================

print("[1/3] LOADING ATOMS FROM LOCAL FILES...")
print()

atoms_dir = Path("data/atoms")
atom_files = list(atoms_dir.glob("**/*_specification_*.json"))

print(f"Found {len(atom_files)} atom files")

all_atoms = []
for atom_file in atom_files:
    try:
        with open(atom_file, 'r', encoding='utf-8') as f:
            atom = json.load(f)
            all_atoms.append(atom)
    except Exception as e:
        print(f"  ERROR loading {atom_file.name}: {e}")

print(f"\nLoaded {len(all_atoms)} atoms")

# ============================================================================
# STEP 2: CONNECT TO POSTGRESQL DIRECTLY
# ============================================================================

print(f"\n[2/3] CONNECTING TO POSTGRESQL DIRECTLY...")

# Try DATABASE_URL first
database_url = os.getenv("DATABASE_URL")
db_host = os.getenv("SUPABASE_DB_HOST")
db_port = os.getenv("SUPABASE_DB_PORT", "5432")
db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
db_user = os.getenv("SUPABASE_DB_USER", "postgres")
db_password = os.getenv("SUPABASE_DB_PASSWORD")

if database_url:
    # Parse connection string
    parsed = urllib.parse.urlparse(database_url)
    db_config = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip('/') or "postgres",
        "user": parsed.username or "postgres",
        "password": parsed.password
    }
elif db_host and db_password:
    # Use individual components
    db_config = {
        "host": db_host,
        "port": int(db_port),
        "database": db_name,
        "user": db_user,
        "password": db_password
    }
else:
    print("\nERROR: Database credentials not found in .env")
    print("Need either DATABASE_URL or SUPABASE_DB_HOST + SUPABASE_DB_PASSWORD")
    sys.exit(1)

try:
    conn = psycopg2.connect(**db_config)
    print(f"Connected to: {db_config['host']}")
except Exception as e:
    print(f"\nERROR connecting to PostgreSQL: {e}")
    sys.exit(1)

# ============================================================================
# STEP 3: UPLOAD ATOMS VIA DIRECT SQL
# ============================================================================

print(f"\n[3/3] UPLOADING {len(all_atoms)} ATOMS VIA DIRECT SQL...")
print()

# Prepare INSERT statement with ON CONFLICT (upsert)
insert_sql = """
INSERT INTO knowledge_atoms (
    id, atom_id, atom_type, title, summary, content,
    manufacturer, product, version, difficulty, safety_level,
    prerequisites, keywords, source_manual, source_page,
    embedding, metadata, created_at, updated_at
) VALUES %s
ON CONFLICT (atom_id) DO UPDATE SET
    title = EXCLUDED.title,
    summary = EXCLUDED.summary,
    content = EXCLUDED.content,
    keywords = EXCLUDED.keywords,
    embedding = EXCLUDED.embedding,
    updated_at = EXCLUDED.updated_at
"""

cursor = conn.cursor()

# Prepare data tuples
data_tuples = []
for atom in all_atoms:
    # Convert embedding list to PostgreSQL array string
    embedding = atom.get('embedding')
    if embedding:
        embedding_str = '{' + ','.join(map(str, embedding)) + '}'
    else:
        embedding_str = None

    # Convert arrays to PostgreSQL array strings
    prerequisites = atom.get('prerequisites', [])
    if prerequisites:
        prereqs_str = '{' + ','.join(f'"{p}"' for p in prerequisites) + '}'
    else:
        prereqs_str = '{}'

    keywords = atom.get('keywords', [])
    if keywords:
        keywords_str = '{' + ','.join(f'"{k}"' for k in keywords) + '}'
    else:
        keywords_str = '{}'

    # Convert metadata to JSON string
    metadata = atom.get('metadata', {})
    metadata_str = json.dumps(metadata) if metadata else '{}'

    data_tuple = (
        atom.get('id'),
        atom.get('atom_id'),
        atom.get('atom_type'),
        atom.get('title'),
        atom.get('summary'),
        atom.get('content'),
        atom.get('manufacturer'),
        atom.get('product'),
        atom.get('version'),
        atom.get('difficulty'),
        atom.get('safety_level'),
        prereqs_str,
        keywords_str,
        atom.get('source_manual'),
        atom.get('source_page'),
        embedding_str,
        metadata_str,
        atom.get('created_at'),
        atom.get('updated_at')
    )
    data_tuples.append(data_tuple)

# Execute batch insert
uploaded = 0
failed = 0
batch_size = 100

try:
    for i in range(0, len(data_tuples), batch_size):
        batch = data_tuples[i:i+batch_size]

        execute_values(cursor, insert_sql, batch)
        conn.commit()

        uploaded += len(batch)
        print(f"  Uploaded {uploaded}/{len(all_atoms)}...")

except Exception as e:
    print(f"\nERROR during upload: {e}")
    conn.rollback()
    failed = len(all_atoms) - uploaded

finally:
    cursor.close()
    conn.close()

print(f"\n{'=' * 80}")
print(f"UPLOAD COMPLETE")
print(f"{'=' * 80}")
print(f"\n  Uploaded: {uploaded}")
print(f"  Failed: {failed}")
print()

# ============================================================================
# VERIFICATION
# ============================================================================

print("=" * 80)
print("VERIFYING UPLOAD")
print("=" * 80)
print()

# Reconnect and count
conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM knowledge_atoms")
total_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM knowledge_atoms WHERE content IS NOT NULL")
with_content = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM knowledge_atoms WHERE embedding IS NOT NULL")
with_embedding = cursor.fetchone()[0]

cursor.close()
conn.close()

print(f"Total atoms in database: {total_count}")
print(f"Atoms with content: {with_content}")
print(f"Atoms with embeddings: {with_embedding}")
print()

if with_content == total_count and with_embedding == total_count:
    print("=" * 80)
    print("SUCCESS - ALL ATOMS UPLOADED WITH CONTENT AND EMBEDDINGS")
    print("=" * 80)
else:
    print("WARNING: Some atoms missing content or embeddings")

print()
