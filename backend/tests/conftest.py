"""Pytest configuration and isolation fixtures for MediDoc AI.

Ensures test isolation:
- Creates a dedicated 'medidoc_test' database on the same PostgreSQL instance.
- Enables pgvector and creates all declarative schema tables and indexes.
- Overrides the FastAPI get_db dependency, settings, and db.session engine/SessionLocal.
- Seeds baseline SOP passages into medidoc_test so retrieval and QA tests execute reliably.
- Automatically drops 'medidoc_test' after test completion.
- GUARANTEE: The development database ('medidoc') is NEVER written to or modified by tests.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator

import psycopg
import pytest

TEST_DB_NAME = "medidoc_test"
ADMIN_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
TEST_DATABASE_URL = f"postgresql+psycopg://postgres:postgres@localhost:5432/{TEST_DB_NAME}"

# Explicitly set environment to prevent any test from hitting dev medidoc DB
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["POSTGRES_DB"] = TEST_DB_NAME

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.db.init_db import init_db
from backend.app.db.session import get_db
from backend.app.ingestion.service import ingest_document
from backend.app.main import app

logger = logging.getLogger(__name__)


def _drop_test_database() -> None:
    """Force terminate active connections and drop the test database."""
    try:
        with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid();
                """)
                cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME};")
    except Exception as exc:
        logger.warning("Error dropping test database %s: %s", TEST_DB_NAME, exc)


def _create_test_database() -> None:
    """Create the test database and enable pgvector extension."""
    _drop_test_database()
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {TEST_DB_NAME};")

    with psycopg.connect(
        f"postgresql://postgres:postgres@localhost:5432/{TEST_DB_NAME}",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Session-scoped fixture to set up an isolated test database and teardown afterwards."""
    # 1. Create separate test database
    _create_test_database()

    # 2. Configure test engine and session factory
    test_engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    # 3. Patch backend.app.db.session engine and SessionLocal
    from backend.app.db import session as db_session_module

    original_engine = db_session_module.engine
    original_session_local = db_session_module.SessionLocal
    db_session_module.engine = test_engine
    db_session_module.SessionLocal = TestSessionLocal

    # 4. Patch settings
    settings = get_settings()
    original_db_url = settings.database_url
    original_db_name = settings.postgres_db
    settings.database_url = TEST_DATABASE_URL
    settings.postgres_db = TEST_DB_NAME

    # 5. Initialize schema tables in test database
    init_db(test_engine)

    # 6. Override FastAPI get_db dependency for TestClient requests
    def override_get_db() -> Generator[Session, None, None]:
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 7. Seed baseline test SOPs into medidoc_test so retrieval tests pass
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "generated"
    with TestSessionLocal() as seed_session:
        for sop_name in ["sop_infection_control.pdf", "sop_discharge_process.pdf"]:
            sop_path = data_dir / sop_name
            if sop_path.exists():
                with open(sop_path, "rb") as f:
                    ingest_document(
                        db=seed_session,
                        source=f.read(),
                        filename=sop_name,
                        doc_type="sop",
                    )
        seed_session.commit()

    yield test_engine

    # Teardown: close test engine, clear overrides, and drop test database
    test_engine.dispose()
    app.dependency_overrides.pop(get_db, None)
    db_session_module.engine = original_engine
    db_session_module.SessionLocal = original_session_local
    settings.database_url = original_db_url
    settings.postgres_db = original_db_name
    _drop_test_database()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Yield a database session bound to the isolated test database."""
    from backend.app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    """Yield a FastAPI TestClient configured with test database dependencies."""
    return TestClient(app)
