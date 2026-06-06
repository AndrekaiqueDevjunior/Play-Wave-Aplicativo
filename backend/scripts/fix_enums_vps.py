#!/usr/bin/env python3
"""
Fix PostgreSQL enums to match Python code definitions
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from core.database import engine

def reset_enums():
    """Reset all enum types in PostgreSQL"""
    conn = engine.connect()

    print("Fixing enums in PostgreSQL...")

    try:
        # Test connection
        result = conn.execute(text("SELECT 1"))
        print("[+] Database connected")

        # audioplayliststatus
        print("\n[*] audioplayliststatus...")
        conn.execute(text("DROP TYPE IF EXISTS audioplayliststatus CASCADE"))
        conn.execute(text("CREATE TYPE audioplayliststatus AS ENUM ('active', 'inactive', 'archived')"))
        print("[+] audioplayliststatus created")

        # audiotrackstatus
        print("\n[*] audiotrackstatus...")
        conn.execute(text("DROP TYPE IF EXISTS audiotrackstatus CASCADE"))
        conn.execute(text("CREATE TYPE audiotrackstatus AS ENUM ('active', 'inactive', 'archived')"))
        print("[+] audiotrackstatus created")

        # audiotrackcategory
        print("\n[*] audiotrackcategory...")
        conn.execute(text("DROP TYPE IF EXISTS audiotrackcategory CASCADE"))
        conn.execute(text("CREATE TYPE audiotrackcategory AS ENUM ('music', 'jingle', 'ambient', 'announcement', 'other')"))
        print("[+] audiotrackcategory created")

        # devicecommandstatus
        print("\n[*] devicecommandstatus...")
        conn.execute(text("DROP TYPE IF EXISTS devicecommandstatus CASCADE"))
        conn.execute(text("CREATE TYPE devicecommandstatus AS ENUM ('PENDING', 'SENT', 'EXECUTED', 'FAILED', 'CANCELLED')"))
        print("[+] devicecommandstatus created")

        conn.commit()
        print("\n[+] All enums fixed successfully!")

        # Verify
        print("\nVerification:")
        for enum_name in ['audioplayliststatus', 'audiotrackstatus', 'audiotrackcategory', 'devicecommandstatus']:
            result = conn.execute(text(f"SELECT enum_range(NULL::{enum_name})"))
            values = result.fetchone()[0]
            print(f"  {enum_name}: {values}")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False

if __name__ == '__main__':
    success = reset_enums()
    sys.exit(0 if success else 1)
