#!/usr/bin/env python3
"""MediDoc AI - Reset Development Database.

Recreates 'medidoc' database, enables pgvector, and creates all declarative schema tables.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ADMIN_URL = os.getenv("ADMIN_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
DEV_DB_NAME = os.getenv("POSTGRES_DB", "medidoc")
DEV_DB_URL = f"postgresql://postgres:postgres@localhost:5432/{DEV_DB_NAME}"


def reset_dev_database() -> None:
    """Terminate connections, drop and recreate medidoc database."""
    logger.info("Connecting to PostgreSQL admin interface to reset %s...", DEV_DB_NAME)
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{DEV_DB_NAME}' AND pid <> pg_backend_pid();
            """)
            cur.execute(f"DROP DATABASE IF EXISTS {DEV_DB_NAME};")
            cur.execute(f"CREATE DATABASE {DEV_DB_NAME};")
            logger.info("Database '%s' created.", DEV_DB_NAME)

    with psycopg.connect(DEV_DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            logger.info("Extension 'vector' enabled on '%s'.", DEV_DB_NAME)

    # Initialize SQLAlchemy declarative tables
    from backend.app.db.init_db import init_db
    init_db()
    logger.info("Database schema tables and indexes successfully initialized for '%s'.", DEV_DB_NAME)


if __name__ == "__main__":
    reset_dev_database()
