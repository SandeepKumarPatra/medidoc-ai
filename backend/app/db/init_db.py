"""Database initialization routines.

Ensures the PostgreSQL pgvector extension is enabled and initializes all declarative tables
and indexes defined in models.py.
"""

import logging
from sqlalchemy import Engine, text
from backend.app.db.models import Base
from backend.app.db.session import engine as default_engine

logger = logging.getLogger(__name__)


def init_db(engine: Engine | None = None) -> None:
    """Initialize the database schema and enable pgvector.

    Args:
        engine: Optional SQLAlchemy engine instance. Defaults to application default engine.
    """
    target_engine = engine or default_engine
    logger.info("Initializing database with engine: %s", target_engine.url.render_as_string(hide_password=True))

    with target_engine.connect() as conn:
        logger.info("Enabling pgvector extension if not already present...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    logger.info("Creating declarative tables and indexes...")
    Base.metadata.create_all(bind=target_engine)
    logger.info("Database schema initialized successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
