"""
Clear conversation memory for fresh start

Usage:
    poetry run python scripts/clear_conversation_memory.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure UTF-8 for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from agent_factory.rivet_pro.database import RIVETProDatabase


def main():
    print("🧹 Clearing conversation memory...")
    print("="*60)

    # Connect to database
    print("🔌 Connecting to database...")
    db = RIVETProDatabase()
    print(f"✅ Connected to {db.provider.upper()}")

    try:
        # Clear conversation sessions
        cursor = db.conn.cursor()
        cursor.execute("TRUNCATE TABLE conversation_sessions RESTART IDENTITY CASCADE;")
        db.conn.commit()
        cursor.close()

        print("✅ Conversation sessions cleared")

        # Verify
        result = db._execute_one("SELECT COUNT(*) as count FROM conversation_sessions")
        count = result['count']
        print(f"📊 Current conversation count: {count}")

        if count == 0:
            print("\n✅ Memory cleared successfully - ready for fresh start!")
        else:
            print(f"\n⚠️ Warning: {count} conversations still exist")

    except Exception as e:
        print(f"❌ Error clearing memory: {e}")
        db.conn.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
