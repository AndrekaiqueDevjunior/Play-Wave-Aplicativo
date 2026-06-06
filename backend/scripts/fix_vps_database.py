#!/usr/bin/env python3
"""
VPS Database Fix Script
Resolve incompatibilidades entre schema do banco de dados e modelos Python

Uso: python3 fix_vps_database.py
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from core.database import engine
from core.models import User
from core.auth import get_password_hash

def fix_admin_password():
    """Reset admin password hash."""
    print("🔧 Fixing admin password hash...")
    try:
        db = sessionmaker(bind=engine)()
        user = db.query(User).filter(User.email == 'admin@playwave.com').first()
        if user:
            password = 'Playwave@123'
            user.password_hash = get_password_hash(password)
            db.commit()
            print(f"✓ Admin password reset to: {password}")
        else:
            print("✗ Admin user not found")
        db.close()
    except Exception as e:
        print(f"✗ Error fixing admin password: {e}")
        return False
    return True


def fix_device_commands_status():
    """Clean invalid device_commands status values."""
    print("🔧 Fixing device_commands status values...")
    try:
        conn = engine.connect()

        # Update invalid status values
        result = conn.execute(text(
            "UPDATE device_commands SET status = 'EXECUTED' WHERE status::text IN ('RECEIVED', 'EXECUTING')"
        ))
        updated = result.rowcount

        # Check remaining values
        result = conn.execute(text("SELECT DISTINCT status FROM device_commands"))
        statuses = [row[0] for row in result]

        print(f"✓ Updated {updated} device commands with invalid status")
        print(f"✓ Current status values: {statuses}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"✗ Error fixing device_commands: {e}")
        return False
    return True


def check_enum_values():
    """Verify enum values in database match code expectations."""
    print("🔧 Checking enum values...")

    enums_to_check = [
        ('audiotrackstatus', ['active', 'inactive', 'archived']),
        ('audioplayliststatus', ['active', 'inactive', 'archived']),
        ('devicecommandstatus', ['PENDING', 'SENT', 'EXECUTED', 'FAILED', 'CANCELLED']),
    ]

    try:
        conn = engine.connect()

        for enum_name, expected_values in enums_to_check:
            result = conn.execute(text(
                f"SELECT enum_range(NULL::{enum_name})"
            ))
            row = result.fetchone()
            if row:
                # Parse PostgreSQL array format: {val1,val2,val3}
                values_str = row[0]
                actual_values = values_str.strip('{}').split(',') if values_str else []

                if set(actual_values) == set(expected_values):
                    print(f"✓ {enum_name}: {actual_values}")
                else:
                    print(f"⚠ {enum_name}: expected {expected_values}, got {actual_values}")
            else:
                print(f"✗ {enum_name}: not found")

        conn.close()
    except Exception as e:
        print(f"✗ Error checking enums: {e}")
        return False
    return True


def main():
    """Run all fixes."""
    print("=" * 70)
    print("VPS Database Fix Script")
    print("=" * 70)
    print()

    all_ok = True

    all_ok = check_enum_values() and all_ok
    print()

    all_ok = fix_admin_password() and all_ok
    print()

    all_ok = fix_device_commands_status() and all_ok
    print()

    if all_ok:
        print("=" * 70)
        print("✓ All fixes completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Restart backend: docker compose -f docker-compose.production.yml restart backend")
        print("  2. Wait for health check: docker compose -f docker-compose.production.yml ps backend")
        print("  3. Test /health: curl http://localhost:8000/health")
        print("  4. Test /campaigns: curl -H 'Authorization: Bearer <token>' http://localhost:8000/campaigns/")
        return 0
    else:
        print("=" * 70)
        print("✗ Some fixes failed. Please check the output above.")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
