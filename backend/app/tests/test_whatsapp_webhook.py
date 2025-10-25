from __future__ import annotations

from fastapi.testclient import TestClient


def test_whatsapp_webhook_accepts_message(api_client: TestClient):
    response = api_client.post(
        "/api/whatsapp/webhook",
        data={
            "From": "whatsapp:+123456789",
            "Body": "Hello, this is John Doe. Email: john@example.com",
            "NumMedia": "0",
        },
    )
    assert response.status_code == 200
