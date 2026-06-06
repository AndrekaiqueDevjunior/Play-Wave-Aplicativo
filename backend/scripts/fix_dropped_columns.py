#!/usr/bin/env python3
"""
Recreate columns that were dropped when enum types were dropped with CASCADE
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from core.database import engine

def recreate_dropped_columns():
    """Recreate all columns that depend on enum types"""
    conn = engine.connect()

    try:
        print("[*] Checking and recreating dropped columns...")

        # 1. audio_playlists.status
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='audio_playlists' AND column_name='status'
            )
        """))
        if not result.fetchone()[0]:
            print("  [*] Recreating audio_playlists.status...")
            conn.execute(text("""
                ALTER TABLE audio_playlists
                ADD COLUMN status audioplayliststatus DEFAULT 'active'
            """))
            print("  [+] audio_playlists.status recreated")

        # 2. audio_tracks.status
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='audio_tracks' AND column_name='status'
            )
        """))
        if not result.fetchone()[0]:
            print("  [*] Recreating audio_tracks.status...")
            conn.execute(text("""
                ALTER TABLE audio_tracks
                ADD COLUMN status audiotrackstatus DEFAULT 'active'
            """))
            print("  [+] audio_tracks.status recreated")

        # 3. audio_tracks.category
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='audio_tracks' AND column_name='category'
            )
        """))
        if not result.fetchone()[0]:
            print("  [*] Recreating audio_tracks.category...")
            conn.execute(text("""
                ALTER TABLE audio_tracks
                ADD COLUMN category audiotrackcategory DEFAULT 'music'
            """))
            print("  [+] audio_tracks.category recreated")

        conn.commit()

        # Verify
        print("\n[*] Verifying columns...")
        for table, col in [('audio_playlists', 'status'), ('audio_tracks', 'status'), ('audio_tracks', 'category')]:
            result = conn.execute(text(f"""
                SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL
            """))
            count = result.fetchone()[0]
            print(f"  [+] {table}.{col}: {count} rows with data")

        conn.close()
        print("\n[+] All columns recreated successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False

if __name__ == '__main__':
    success = recreate_dropped_columns()
    sys.exit(0 if success else 1)
