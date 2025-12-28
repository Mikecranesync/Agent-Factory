import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['NEON_DB_URL'])
conn.autocommit = True
cursor = conn.cursor()

with open('migrations/public_launch/001_public_ready_schema.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    cursor.execute(sql)

cursor.close()
conn.close()
print('Migration complete')
