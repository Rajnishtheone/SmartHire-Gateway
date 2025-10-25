from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_returns_token(api_client: TestClient):
    response = api_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["user"]["role"] == "admin"
    assert payload["user"]["name"] == "Administrator"


def test_login_rejects_invalid_credentials(api_client: TestClient):
    response = api_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_admin_can_manage_recruiters(api_client: TestClient):
    login_response = api_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = api_client.post(
        "/api/admin/users",
        json={"email": "newrecruiter@example.com", "password": "securepass", "name": "New Recruiter"},
        headers=headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "New Recruiter"

    list_response = api_client.get("/api/admin/users", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    emails = [item["email"] for item in items]
    assert "newrecruiter@example.com" in emails
    assert any(item["name"] == "New Recruiter" for item in items)

    delete_response = api_client.delete("/api/admin/users/newrecruiter@example.com", headers=headers)
    assert delete_response.status_code == 200
