#!/usr/bin/env python3
"""Verify database connection using DATABASE_URL from backend/.env. Run from backend: python scripts/check_db.py"""

import sys
from pathlib import Path

# Add backend to path so app.core.config is found
backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend))

def main():
    from app.core.config import get_settings
    from sqlalchemy import create_engine, text

    settings = get_settings()
    url = settings.database_url
    # Mask password in output
    if "@" in url and ":" in url:
        parts = url.split("@", 1)
        user_part = parts[0].rsplit("/", 1)[-1]
        if ":" in user_part:
            user = user_part.split(":")[0]
            url_display = url.replace(user_part, f"{user}:****", 1)
        else:
            url_display = url
    else:
        url_display = url

    print(f"Connecting to: {url_display}")
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("OK: Database connection successful.")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        print()
        print("Checks:")
        print("  1. PostgreSQL is running (e.g. pg_ctl status or service postgresql status)")
        print("  2. File backend/.env exists and contains DATABASE_URL=postgresql://user:password@host:port/dbname")
        print("  3. Database exists: createdb compliance_tracker")
        print("  4. User and password match your PostgreSQL setup")
        return 1

if __name__ == "__main__":
    sys.exit(main())
