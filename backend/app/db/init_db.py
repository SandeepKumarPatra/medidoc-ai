"""Database initialization routines.

Ensures the PostgreSQL pgvector extension is enabled and initializes all declarative tables
and indexes defined in models.py.
"""

import logging
from sqlalchemy import Engine, text
from backend.app.db.models import Base
from backend.app.db import session as db_session

logger = logging.getLogger(__name__)


def init_db(engine: Engine | None = None) -> None:
    """Initialize the database schema and enable pgvector.

    Args:
        engine: Optional SQLAlchemy engine instance. Defaults to application default engine.
    """
    target_engine = engine or db_session.engine
    logger.info("Initializing database with engine: %s", target_engine.url.render_as_string(hide_password=True))

    with target_engine.connect() as conn:
        logger.info("Enabling pgvector extension if not already present...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    logger.info("Creating declarative tables and indexes...")
    Base.metadata.create_all(bind=target_engine)

    # Ensure schema migrations/columns are present on existing tables
    with target_engine.connect() as conn:
        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_file_hash ON documents(file_hash);"))
        conn.commit()
    logger.info("Database schema initialized successfully.")


def drop_db(engine: Engine | None = None) -> None:
    """Drop all declarative tables and schema in the database.

    Args:
        engine: Optional SQLAlchemy engine instance. Defaults to application default engine.
    """
    target_engine = engine or db_session.engine
    logger.info("Dropping all database tables...")
    Base.metadata.drop_all(bind=target_engine)
    logger.info("All database tables dropped successfully.")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Initialize or recreate MediDoc AI database schema.")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all database tables",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate all database tables cleanly",
    )
    args = parser.parse_args()

    if args.recreate:
        drop_db()
        init_db()
    elif args.drop:
        drop_db()
    else:
        init_db()
