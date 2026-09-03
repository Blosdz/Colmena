"""Login/registro standalone de Colmena (email + contraseña)."""

from app.core.database import SessionLocal
from app.services.auth_service import AuthService


def test_register_returns_token_and_persists_hash(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "Ana Ríos", "email": "ana@example.com", "password": "secreta123"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token"]
    assert body["user"]["email"] == "ana@example.com"
    assert body["user"]["appthesis_user_id"] is None

    # el token propio autoriza el resto de la API
    me = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200


def test_login_roundtrip_and_bad_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Bea", "email": "bea@example.com", "password": "clave-larga"},
    )
    ok = client.post(
        "/api/v1/auth/login", json={"email": "bea@example.com", "password": "clave-larga"}
    )
    assert ok.status_code == 200 and ok.json()["token"]

    bad = client.post(
        "/api/v1/auth/login", json={"email": "bea@example.com", "password": "otra"}
    )
    assert bad.status_code == 401


def test_duplicate_email_is_conflict(client):
    payload = {"name": "C", "email": "c@example.com", "password": "clave-larga"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_short_password_is_rejected(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "D", "email": "d@example.com", "password": "corta"},
    )
    assert resp.status_code == 422


def test_password_reset_flow(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Fede", "email": "fede@example.com", "password": "clave-vieja"},
    )
    req = client.post(
        "/api/v1/auth/password/reset-request", json={"email": "fede@example.com"}
    )
    assert req.status_code == 200
    reset_url = req.json()["reset_url"]
    assert reset_url and "token=" in reset_url  # expuesto en desarrollo
    token = reset_url.split("token=", 1)[1]

    done = client.post(
        "/api/v1/auth/password/reset", json={"token": token, "password": "clave-nueva-1"}
    )
    assert done.status_code == 200 and done.json()["token"]

    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "fede@example.com", "password": "clave-vieja"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "fede@example.com", "password": "clave-nueva-1"},
        ).status_code
        == 200
    )


def test_password_reset_unknown_email_still_ok(client):
    resp = client.post(
        "/api/v1/auth/password/reset-request", json={"email": "nadie@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["reset_url"] is None


def test_reset_token_is_not_a_session_token():
    db = SessionLocal()
    try:
        service = AuthService(db)
        service.register_local("Gil", "gil@example.com", "clave-larga")
        reset_token = service.request_password_reset("gil@example.com").split("token=", 1)[1]
        # un token de reset (typ=pwreset) nunca resuelve como sesión de Colmena
        assert service._resolve_local_token(reset_token) is None
    finally:
        db.close()


def test_resolve_current_user_accepts_own_jwt():
    db = SessionLocal()
    try:
        service = AuthService(db)
        user, token = service.register_local("Eva", "eva@example.com", "clave-larga")
        resolved = service.resolve_current_user(token)
        assert resolved.id == user.id
        # un token basura no resuelve como local (y sin AppThesis levanta 502/401, no lo colamos)
        assert service._resolve_local_token("no-es-un-jwt") is None
    finally:
        db.close()
