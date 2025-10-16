import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from .models import Base
except Exception:
    # fallback for when modules are run directly (no package context)
    from models import Base

import dotenv
dotenv.load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = None
SessionLocal = None


def init_engine(url: str | None = None):
    global engine, SessionLocal
    if url is None:
        url = DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL not set in environment and no URL provided")
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
