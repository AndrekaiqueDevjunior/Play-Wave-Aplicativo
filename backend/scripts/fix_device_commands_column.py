#!/usr/bin/env python3
"""
Recreate device_commands.status column if it was dropped
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from core.database import engine

def fix_device_commands():
    """Recreate device_commands.status column"""
    conn = engine.connect()

    try:
        print("[*] Checking device_commands table...")

        # Check if column exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='device_commands' AND column_name='status'
            )
        """))

        col_exists = result.fetchone()[0]

        if col_exists:
            print("[+] device_commands.status column already exists")
        else:
            print("[*] device_commands.status column missing, recreating...")

            # Recreate column
            conn.execute(text("""
                ALTER TABLE device_commands
                ADD COLUMN status devicecommandstatus DEFAULT 'PENDING'
            """))

            # Set all existing records to EXECUTED if they have no status
            conn.execute(text("""
                UPDATE device_commands
                SET status = 'EXECUTED'
                WHERE status IS NULL
            """))

            conn.commit()
            print("[+] device_commands.status column recreated and populated")

        # Verify
        result = conn.execute(text("""
            SELECT COUNT(*) FROM device_commands WHERE status IS NOT NULL
        """))
        count = result.fetchone()[0]
        print(f"[+] device_commands rows with status: {count}")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False

if __name__ == '__main__':
    success = fix_device_commands()
    sys.exit(0 if success else 1)
