import os
from pathlib import Path

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, close_all_sessions

os.environ["COLMENA_DB_PATH"] = "./data/db/colmena_test.db"

import app.models  # noqa: E402,F401  (registra todas las tablas para create_all)
from app.core.database import Base, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.routers.deps import get_current_user  # noqa: E402


TEST_DB_FILE = Path(__file__).resolve().parents[1] / "data" / "db" / "colmena_test.db"
TEST_USER_ID = "00000000-0000-0000-0000-0000000000aa"


def _override_current_user(db: Session = Depends(get_db)) -> User:
    """Sustituye la validacion de JWT por un usuario de prueba persistido."""
    user = db.get(User, TEST_USER_ID)
    if user is None:
        user = User(
            id=TEST_USER_ID,
            name="Usuario Test",
            username="test",
            email="test@colmena.local",
            status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


app.dependency_overrides[get_current_user] = _override_current_user


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
