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
