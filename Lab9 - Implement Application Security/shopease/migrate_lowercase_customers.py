"""Rename mixed-case columns in customers table to lowercase identifiers.

This helps avoid PostgreSQL case-sensitivity issues where unquoted
identifiers are folded to lowercase (e.g., firstName becomes firstname).

Usage:
    python -m shopease.migrate_lowercase_customers
"""
from sqlalchemy import inspect, text
import os
from .db import init_engine


def run(database_url: str | None = None):
    engine = init_engine(database_url)
    inspector = inspect(engine)
    cols = inspector.get_columns('customers')
    to_rename = []
    for c in cols:
        name = c['name']
        lower = name.lower()
        if name != lower:
            to_rename.append((name, lower))

    if not to_rename:
        print('No mixed-case columns found in customers; nothing to do.')
        return

    with engine.connect() as conn:
        for orig, new in to_rename:
            # Use quoted original name to match exact case, rename to unquoted lower-case
            sql = f'ALTER TABLE customers RENAME COLUMN "{orig}" TO {new};'
            print('Running:', sql)
            conn.execute(text(sql))
        try:
            conn.commit()
        except Exception:
            pass

    print('Renamed columns:')
    for orig, new in to_rename:
        print(f' - "{orig}" -> {new}')


if __name__ == '__main__':
    run(os.environ.get('DATABASE_URL'))
