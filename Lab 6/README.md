Shopease CLI - SQLAlchemy + PostgreSQL

This project provides a small CLI application to create a PostgreSQL schema for the Shopease management system, seed sample data, and perform basic CRUD operations.

Setup
1. Create a PostgreSQL database and note the connection URL, for example:
   postgresql://user:password@localhost:5432/shopease
2. Install requirements:
   pip install -r requirements.txt
3. Set environment variable:
   setx DATABASE_URL "postgresql://user:password@localhost:5432/shopease"

Usage
From the project root run:
   python -m shopease.cli init-db
   python -m shopease.cli seed
   python -m shopease.cli list customers
   python -m shopease.cli create-customer --firstName John --lastName Doe --email john@example.com

Verification
1. Ensure PostgreSQL is running and DATABASE_URL is set.
2. Initialize schema: python -m shopease.cli init-db
3. Seed: python -m shopease.cli seed
4. List customers: python -m shopease.cli customers list

Files created
- `shopease/models.py` - SQLAlchemy ORM models mapping the ER diagram (tables, PKs, FKs, enums).
- `shopease/db.py` - engine/session management and create_schema helper.
- `shopease/seed.py` - inserts sample data into all tables.
- `shopease/cli.py` - Click-based CLI exposing init-db, seed, and basic CRUD for customers and tickets.

Notes
- The app uses the `DATABASE_URL` environment variable to connect to PostgreSQL. Set it before running commands.
- You can extend the CLI commands to add update/delete operations similarly.
