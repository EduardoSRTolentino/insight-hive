from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_list_and_get_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    name = f"Cliente {uuid4().hex[:8]}"
    created = client.post("/api/clients", json={"name": name}, headers=auth_headers)
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == name
    assert body["meetings_count"] == 0

    listing = client.get("/api/clients", headers=auth_headers)
    assert listing.status_code == 200
    assert any(item["id"] == body["id"] for item in listing.json())

    missing = client.get("/api/clients/999999", headers=auth_headers)
    assert missing.status_code == 404


def test_duplicate_name_conflict(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    name = f"Dup {uuid4().hex[:8]}"
    first = client.post("/api/clients", json={"name": name}, headers=auth_headers)
    assert first.status_code == 201
    other = client.post(
        "/api/clients",
        json={"name": f"Outro {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert other.status_code == 201
    patched = client.patch(
        f"/api/clients/{other.json()['id']}",
        json={"name": name},
        headers=auth_headers,
    )
    assert patched.status_code == 409
