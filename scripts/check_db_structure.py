import psycopg2
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / '.env'
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('NEON_DB_URL='):
            neon_url = line.split('=', 1)[1].strip()
            break

conn = psycopg2.connect(neon_url)
cursor = conn.cursor()

# Check rivet_users columns
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'rivet_users'
    ORDER BY ordinal_position
""")

print('Columns in rivet_users table:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

cursor.close()
conn.close()
