import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from .models import Base
except Exception:
    # fallback for when modules are run directly (no package context)
    from models import Base

import dotenv
from dotenv import find_dotenv, load_dotenv

# Attempt to locate a .env file in this directory or parent directories and load it.
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)

# First try to load a .env file located next to this module (shopease/.env)
package_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(package_env):
    load_dotenv(package_env)
else:
    # fallback to any .env found in parent dirs
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)

# Now read DATABASE_URL from the environment
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = None
SessionLocal = None


def init_engine(url: str | None = None):
    global engine, SessionLocal
    if url is None:
        url = DATABASE_URL
    if not url:
        raise RuntimeError(
            "DATABASE_URL not set in environment and no URL provided.\n"
            "Make sure you have a .env file with DATABASE_URL or set the environment variable."
        )
    engine = create_engine(url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return engine


def create_schema():
    if engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine first.")
    Base.metadata.create_all(bind=engine)


def get_session():
    if SessionLocal is None:
        raise RuntimeError("SessionLocal not initialized. Call init_engine first.")
    return SessionLocal()
