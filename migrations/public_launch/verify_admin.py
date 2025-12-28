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
    print(f"Admin verified: {result}")
else:
    print("Admin not found - check migration")
