"""Integration tests for the FastAPI endpoints."""

import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from database_init import init_db
from main import app
from models.database import SessionLocal
from models.entities import User

init_db()
client = TestClient(app)

_TEST_USER = {
    "name": "Test User",
    "email": "testuser@psychshield.test",
    "password": "T3st!Secure#1",
}


def _register_and_login(user: dict = None) -> dict:
    """Register a user and return auth headers."""
    u = user or _TEST_USER
    client.post("/api/auth/register", json=u)
    resp = client.post(
        "/api/auth/login",
        json={"email": u["email"], "password": u["password"]},
    )
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _get_admin_headers() -> dict:
    """Register a user, promote to admin in DB, then login."""
    admin = {
        "name": "Admin",
        "email": f"admin-{uuid.uuid4().hex[:8]}@psychshield.test",
        "password": "Adm1n!Secure#",
    }
    client.post("/api/auth/register", json=admin)
    db = SessionLocal()
    row = db.query(User).filter(User.email == admin["email"]).first()
    row.role = "admin"
    db.commit()
    db.close()
    resp = client.post(
        "/api/auth/login",
        json={"email": admin["email"], "password": admin["password"]},
    )
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login():
    email = f"new-{uuid.uuid4().hex[:8]}@psychshield.test"
    resp = client.post(
        "/api/auth/register",
        json={"name": "New", "email": email, "password": "Str0ng!Pass#"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "analyst"

    resp2 = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Str0ng!Pass#"},
    )
    assert resp2.status_code == 200
    assert "token" in resp2.json()


def test_login_wrong_password():
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@test.com", "password": "Wr0ng!Pass#"},
    )
    assert response.status_code == 401


def test_register_weak_password_rejected():
    response = client.post(
        "/api/auth/register",
        json={"name": "Test", "email": "weak@test.com", "password": "abc"},
    )
    assert response.status_code == 422


def test_register_invalid_email_rejected():
    response = client.post(
        "/api/auth/register",
        json={"name": "Test", "email": "notanemail", "password": "Str0ng!Pass#"},
    )
    assert response.status_code == 422


def test_analyze_requires_auth():
    response = client.post("/api/analyze-email", json={"body": "test email"})
    assert response.status_code == 401


def test_analyze_email_with_auth():
    headers = _register_and_login()
    response = client.post(
        "/api/analyze-email",
        json={
            "body": "URGENT: Your account has been suspended. Click immediately: https://paypa1-login.com/verify",
            "sender": "alert@paypa1-login.com",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "riskScore" in data
    assert "riskTier" in data
    assert data["riskTier"] in ("High", "Medium", "Low")
    assert 0 <= data["riskScore"] <= 100


def test_analyze_body_too_large_rejected():
    headers = _register_and_login()
    response = client.post(
        "/api/analyze-email",
        json={"body": "x" * 60000},
        headers=headers,
    )
    assert response.status_code == 422


def test_emails_list_requires_auth():
    response = client.get("/api/emails")
    assert response.status_code == 401


def test_emails_list_with_auth():
    headers = _register_and_login()
    response = client.get("/api/emails", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analytics_accessible_to_analyst():
    headers = _register_and_login()
    response = client.get("/api/analytics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "totalAnalyzed" in data
    assert "detectionRateTrend" in data


def test_audit_log_requires_admin():
    headers = _register_and_login()
    response = client.get("/api/audit-log", headers=headers)
    assert response.status_code == 403


def test_audit_log_with_admin():
    headers = _get_admin_headers()
    response = client.get("/api/audit-log", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_model_metrics_requires_admin():
    headers = _register_and_login()
    response = client.get("/api/model-metrics", headers=headers)
    assert response.status_code == 403


def test_model_metrics_with_admin():
    headers = _get_admin_headers()
    response = client.get("/api/model-metrics", headers=headers)
    assert response.status_code == 200
    assert response.json()["accuracy"] > 0


def test_email_detail_not_found():
    headers = _register_and_login()
    response = client.get("/api/emails/nonexistent-id", headers=headers)
    assert response.status_code == 404
