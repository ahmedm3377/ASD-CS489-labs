"""Simple migration: add `role` column to customers table if missing.

Run this when DATABASE_URL is configured (reads .env next to package).

Usage:
    python -m shopease.migrate_add_role
"""
from sqlalchemy import text
from .db import init_engine
import os


def run(database_url: str | None = None):
    # initialize engine (init_engine will load .env if needed)
    engine = init_engine(database_url)

    add_column_sql = "ALTER TABLE customers ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'customer';"
    backfill_sql = "UPDATE customers SET role='customer' WHERE role IS NULL;"

    with engine.connect() as conn:
        print('Running:', add_column_sql)
        conn.execute(text(add_column_sql))
        print('Running:', backfill_sql)
        conn.execute(text(backfill_sql))
        # commit when using transactional engine
        try:
            conn.commit()
        except Exception:
            # some dialects auto-commit; ignore
            pass

    print('Migration complete: customers.role ensured.')


if __name__ == '__main__':
    db_url = os.environ.get('DATABASE_URL')
    run(db_url)
