import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import close_all_sessions

os.environ["COLMENA_DB_PATH"] = "./data/db/colmena_test.db"

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


TEST_DB_FILE = Path(__file__).resolve().parents[1] / "data" / "db" / "colmena_test.db"


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database():
    yield
    close_all_sessions()
    engine.dispose()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()
